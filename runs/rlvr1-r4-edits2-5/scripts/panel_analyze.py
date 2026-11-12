"""Step 5 analysis of audit/work/panel_verdicts.jsonl.

Writes audit/work/panel_summary.json and prints the tables used in AUDIT.md: stored-record counts,
per-run scores of grader A, grader B's gate and the replacement with paired bootstrap intervals,
the greedy rerun difference, per-check pass rates and disagreements (each classified as finding or
decision by fixture_lib.explain), false rewards of grader A, and the held-out split.
"""
from __future__ import annotations

import collections
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
W = HERE.parents[1]
sys.path.insert(0, str(HERE))
import fixture_lib as fl  # noqa: E402
import graders as g  # noqa: E402

VERDICTS = W / "audit" / "work" / "panel_verdicts.jsonl"
OUT = W / "audit" / "work" / "panel_summary.json"
DATA = W / "case" / "data" / "rlvr1_instruction_following.jsonl"
PANEL = W / "case" / "panel"
DEV_N = 300
SEED = 20261112


def load_raw():
    raw = {}
    for path in sorted(PANEL.glob("*/*.jsonl")):
        key = f"{path.parent.name}/{path.name}"
        for n, line in enumerate(path.open(encoding="utf-8")):
            raw[(key, n)] = json.loads(line)["raw_response"]
    return raw


def load_kwargs():
    out = {}
    for idx, line in enumerate(DATA.open(encoding="utf-8")):
        rec = json.loads(json.loads(line)["extra_info"]["nemotron_ultra"]["record_json"])
        out[idx] = rec["kwargs"]
    return out


def boot(diffs, rng, reps=1000):
    if not diffs:
        return (0.0, 0.0)
    n = len(diffs)
    means = sorted(sum(diffs[rng.randrange(n)] for _ in range(n)) / n for _ in range(reps))
    return (means[int(0.025 * reps)], means[int(0.975 * reps) - 1])


def main():
    rng = random.Random(SEED)
    recs = [json.loads(line) for line in VERDICTS.open(encoding="utf-8")]
    raw = load_raw()
    kwargs = load_kwargs()
    cache = {}

    def classify(rec, idx, observed):
        iid = rec["ids"][idx]
        kw = kwargs[rec["row"]][idx]
        text = raw[(rec["file"], rec["n"])]
        key = (iid, json.dumps(kw, sort_keys=True), hash(text), rec["reasoning"], observed)
        if key not in cache:
            if rec["extraction_failure"]:
                cache[key] = ("extraction", [])
            else:
                readings = fl.explain(iid, kw, text, observed, rec["reasoning"])
                cache[key] = ("decision", readings) if readings else ("finding", [])
        return cache[key]

    # 1. stored records
    stored = collections.defaultdict(collections.Counter)
    for r in recs:
        s = stored[r["file"]]
        s["responses"] += 1
        s["finish_length"] += r["finish"] == "length"
        s["extraction_failure"] += r["extraction_failure"]
        s["literal_marker_non_reasoning"] += r["literal_marker"]
        s["A_text_empty"] += r["a_text_empty"]
        s["A_infra_error"] += r["A_infra"]
        s["closed_but_length"] += r["reasoning"] and not r["extraction_failure"] and r["finish"] == "length"

    # 2. per run scores
    runs = {}
    for file in sorted(stored):
        rows = [r for r in recs if r["file"] == file]
        a = [r["A_reward"] for r in rows]
        rr = [float(all(r["R"])) for r in rows]
        gate_rows = [r for r in rows if r["B_has_gate"]]
        b = [float(r["B_gate"]) for r in gate_rows]
        rg = [float(all(v for v, bv in zip(r["R"], r["B"]) if bv is not None)) for r in gate_rows]
        d = [x - y for x, y in zip(rr, a)]
        dg = [x - y for x, y in zip(rg, b)]
        runs[file] = {
            "rows": len(rows),
            "A_score": sum(a) / len(a), "R_score": sum(rr) / len(rr),
            "R_minus_A": sum(d) / len(d), "R_minus_A_ci": boot(d, rng),
            "A_coverage": 1 - sum(r["A_infra"] for r in rows) / len(rows),
            "B_gate_rows": len(gate_rows), "B_gate_pass": sum(b) / len(b), "R_gate_pass": sum(rg) / len(rg),
            "Rgate_minus_B": sum(dg) / len(dg), "Rgate_minus_B_ci": boot(dg, rng),
            "A_passes": sum(a), "A_false_rewards": sum(1 for r in rows if r["A_reward"] == 1.0 and not all(r["R"])),
            "A_missed_rewards": sum(1 for r in rows if r["A_reward"] == 0.0 and all(r["R"])),
            "B_false_gate_passes": sum(1 for r in gate_rows if r["B_gate"] and not all(v for v, bv in zip(r["R"], r["B"]) if bv is not None)),
            "B_false_gate_fails": sum(1 for r in gate_rows if not r["B_gate"] and all(v for v, bv in zip(r["R"], r["B"]) if bv is not None)),
        }

    # 3. rerun difference (greedy vs greedy_repeat)
    g1 = {r["uuid"]: r for r in recs if r["file"].endswith("/greedy.jsonl")}
    g2 = {r["uuid"]: r for r in recs if r["file"].endswith("/greedy_repeat.jsonl")}
    common = sorted(set(g1) & set(g2))
    rerun = {
        "rows": len(common),
        "identical_text": sum(1 for u in common if raw[(g1[u]["file"], g1[u]["n"])] == raw[(g2[u]["file"], g2[u]["n"])]),
        "A_row_changes": sum(1 for u in common if g1[u]["A_reward"] != g2[u]["A_reward"]),
        "A_score_diff": (sum(g2[u]["A_reward"] for u in common) - sum(g1[u]["A_reward"] for u in common)) / len(common),
        "R_row_changes": sum(1 for u in common if all(g1[u]["R"]) != all(g2[u]["R"])),
        "R_score_diff": (sum(all(g2[u]["R"]) for u in common) - sum(all(g1[u]["R"]) for u in common)) / len(common),
        "B_row_changes": sum(1 for u in common if g1[u]["B_gate"] != g2[u]["B_gate"]),
    }

    # 4. per check, with classification of disagreements
    per_check = collections.defaultdict(collections.Counter)
    readings_count = collections.defaultdict(collections.Counter)
    false_reward_cause = collections.Counter()
    heldout = collections.Counter()
    fixes = collections.defaultdict(lambda: collections.Counter())
    for r in recs:
        held = r["n"] >= DEV_N
        a_false_reward = r["A_reward"] == 1.0 and not all(r["R"])
        causes = set()
        # "fixes only": take the contract's verdict where the grader's disagreement is a finding,
        # an extraction failure or a grading failure, and keep the grader's verdict on decisions.
        fixed_a, fixed_b = [], []
        for i, iid in enumerate(r["ids"]):
            av, rv, bv = r["A"][i] and not r["A_err"][i], r["R"][i], r["B"][i]
            if r["A_err"][i]:
                fixed_a.append(rv)
            elif av != rv:
                fixed_a.append(av if classify(r, i, av)[0] == "decision" else rv)
            else:
                fixed_a.append(av)
            if bv is not None:
                fixed_b.append(bv if bv == rv or classify(r, i, bv)[0] == "decision" else rv)
        f = fixes[r["file"]]
        f["rows"] += 1
        f["A"] += r["A_reward"]
        f["A_fixed"] += all(fixed_a)
        if r["B_has_gate"]:
            f["B_rows"] += 1
            f["B"] += r["B_gate"]
            f["B_fixed"] += all(fixed_b)
        for i, iid in enumerate(r["ids"]):
            c = per_check[iid]
            c["n"] += 1
            av, rv, bv = r["A"][i] and not r["A_err"][i], r["R"][i], r["B"][i]
            c["A_pass"] += av
            c["R_pass"] += rv
            c["A_error"] += bool(r["A_err"][i])
            if bv is not None:
                c["B_n"] += 1
                c["B_pass"] += bv
                c["B_R_n"] += 1
                c["R_pass_on_B"] += rv
                if bv != rv:
                    c["B_disagree"] += 1
                    cls, rd = classify(r, i, bv)
                    c["B_" + cls] += 1
                    c["B_false_pass" if bv else "B_false_fail"] += 1
                    for x in rd:
                        readings_count["B"][x] += 1
                    if held:
                        heldout["B_disagree"] += 1
                        heldout["B_" + cls] += 1
                if av != bv:
                    c["A_B_disagree"] += 1
            if r["A_err"][i]:
                c["A_disagree"] += 1
                c["A_grading_failure"] += 1
                causes.add("grading_failure")
                continue
            if av != rv:
                c["A_disagree"] += 1
                cls, rd = classify(r, i, av)
                c["A_" + cls] += 1
                c["A_false_pass" if av else "A_false_fail"] += 1
                for x in rd:
                    readings_count["A"][x] += 1
                if held:
                    heldout["A_disagree"] += 1
                    heldout["A_" + cls] += 1
                if av and not rv:
                    causes.add(cls)
        if held:
            heldout["constraints"] += len(r["ids"])
            heldout["rows"] += 1
            heldout["A_passes"] += r["A_reward"] == 1.0
            heldout["A_false_rewards"] += a_false_reward
        if a_false_reward:
            if "extraction" in causes:
                false_reward_cause["extraction failure"] += 1
            elif "finding" in causes:
                false_reward_cause["at least one finding"] += 1
            else:
                false_reward_cause["decisions only"] += 1

    total_a_pass = sum(1 for r in recs if r["A_reward"] == 1.0)
    total_false = sum(false_reward_cause.values())
    summary = {
        "stored": {k: dict(v) for k, v in stored.items()},
        "runs": runs,
        "rerun": rerun,
        "per_check": {k: dict(v) for k, v in sorted(per_check.items())},
        "readings": {k: dict(v.most_common()) for k, v in readings_count.items()},
        "false_rewards": {"A_passes": total_a_pass, "A_false_rewards": total_false,
                          "share": total_false / total_a_pass if total_a_pass else 0.0,
                          "by_cause": dict(false_reward_cause)},
        "heldout": dict(heldout),
        "dev_n": DEV_N,
        "fixes_only": {k: {"A": v["A"] / v["rows"], "A_fixed": v["A_fixed"] / v["rows"],
                           "B_gate": v["B"] / v["B_rows"], "B_gate_fixed": v["B_fixed"] / v["B_rows"]}
                       for k, v in fixes.items()},
    }
    OUT.write_text(json.dumps(summary, indent=1), encoding="utf-8", newline="\n")
    print(json.dumps({"stored": summary["stored"], "rerun": rerun, "false_rewards": summary["false_rewards"],
                      "heldout": summary["heldout"]}, indent=1))
    for f, v in runs.items():
        print(f, {k: (round(x, 4) if isinstance(x, float) else (tuple(round(y, 4) for y in x) if isinstance(x, tuple) else x)) for k, x in v.items()})


if __name__ == "__main__":
    main()
