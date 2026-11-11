"""Aggregate audit/out/panel_verdicts.jsonl into the step 5 tables. Writes audit/out/panel_report.json
and prints the tables used in audit/AUDIT.md.

Graders: A = SkyRL reward (NVIDIA checkers), session reward (an instruction error gives 0.0 and an
INFRA_ERROR outcome); B = task-curation gate (deterministic constraints only; a gate pass sends the
row to the LLM judge, which is outside this case); R = replacement grader, proposed readings.
"""
import collections
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W / "audit" / "scripts"))
from classify_fixtures import RULES  # noqa: E402

IN = W / "audit" / "out" / "panel_verdicts.jsonl"
OUT = W / "audit" / "out" / "panel_report.json"


def held_out(uuid):
    return hashlib.sha256(uuid.encode("utf-8")).hexdigest()[0] in "012"


def boot_ci(diffs, n=2000, seed=0):
    diffs = np.asarray(diffs, dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(diffs), size=(n, len(diffs)))
    means = diffs[idx].mean(axis=1)
    return float(diffs.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


MULTI = {("A", "first_word:first_word_sent"): "F11/F39", ("A", "keywords:keyword_specific_position"): "F12/F39"}


def finding_for(grader, c, kw):
    if grader == "A" and c["id"] == "keywords:word_once":
        return "F2" if c["R"] else "F1"  # R passes: >= 1 whole-word occurrence, so A failed on a count of 2+ or on decoys
    if grader == "A" and c["id"] == "length_constraints:nth_paragraph_first_word":
        return "F29" if kw["nth_paragraph"] > kw["num_paragraphs"] else "unassigned"
    return MULTI.get((grader, c["id"])) or RULES.get((grader, c["id"]), "unassigned")


def main():
    recs = [json.loads(line) for line in IN.open(encoding="utf-8")]
    sys.path.insert(0, str(W / "audit" / "lib"))
    import graders_under_audit as gu
    kwargs_of = {r["uuid"]: r["record"]["kwargs"] for r in gu.load_rows()}
    report = {}

    # 1. overview per run
    runs = collections.OrderedDict()
    for r in recs:
        runs.setdefault(r["file"], []).append(r)
    overview = {}
    print("== Panel overview")
    for f, rs in runs.items():
        o = {
            "responses": len(rs),
            "truncated": sum(r["finish"] == "length" for r in rs),
            "R_extraction_failed": sum(r["r_extraction_failed"] for r in rs),
            "extraction_differs_A": sum(r["extraction_differs_A"] for r in rs),
            "extraction_differs_B": sum(r["extraction_differs_B"] for r in rs),
            "A_infra_error_rows": sum(r["A_infra_error"] for r in rs),
            "constraints": sum(len(r["cons"]) for r in rs),
            "A_constraint_errors": sum(c["A_err"] is not None for r in rs for c in r["cons"]),
            "B_constraint_errors": sum(c["B_err"] for r in rs for c in r["cons"]),
            "B_deterministic_constraints": sum(c["B"] is not None for r in rs for c in r["cons"]),
        }
        overview[f] = o
        print(f"  {f:<60} {o}")
    report["overview"] = overview

    # 2. scores per run, paired changes
    print("== Scores per run (mean reward, %); change = R minus grader, paired bootstrap 95% CI")
    scores = {}
    for f, rs in runs.items():
        a = [r["A_session_reward"] for r in rs]
        b = [1.0 if r["B_gate"] else 0.0 for r in rs]
        rr = [r["R_reward"] for r in rs]
        dA = boot_ci([x - y for x, y in zip(rr, a)])
        dB = boot_ci([x - y for x, y in zip(rr, b)])
        s = {"A": 100 * np.mean(a), "B_gate_pass": 100 * np.mean(b), "R": 100 * np.mean(rr),
             "R_minus_A": [100 * v for v in dA], "R_minus_B": [100 * v for v in dB],
             "A_rows_gained_by_R": sum(1 for x, y in zip(rr, a) if x > y), "A_rows_lost_by_R": sum(1 for x, y in zip(rr, a) if x < y)}
        scores[f] = s
        print(f"  {f:<60} A={s['A']:.1f} B_gate={s['B_gate_pass']:.1f} R={s['R']:.1f} "
              f"R-A={s['R_minus_A'][0]:+.1f} [{s['R_minus_A'][1]:+.1f},{s['R_minus_A'][2]:+.1f}] "
              f"R-B={s['R_minus_B'][0]:+.1f} [{s['R_minus_B'][1]:+.1f},{s['R_minus_B'][2]:+.1f}] "
              f"(R gains {s['A_rows_gained_by_R']}, loses {s['A_rows_lost_by_R']} rows vs A)")
    report["scores"] = scores

    # 3. rerun: greedy vs greedy_repeat
    g1 = {r["uuid"]: r for r in runs.get("Qwen__Qwen3-4B-Instruct-2507/greedy.jsonl", [])}
    g2 = {r["uuid"]: r for r in runs.get("Qwen__Qwen3-4B-Instruct-2507/greedy_repeat.jsonl", [])}
    common = sorted(set(g1) & set(g2))
    rerun = {"rows": len(common)}
    for key, name in (("A_session_reward", "A"), ("R_reward", "R")):
        x = [g1[u][key] for u in common]
        y = [g2[u][key] for u in common]
        rerun[name] = {"run1": 100 * np.mean(x), "run2": 100 * np.mean(y), "changed_rows": sum(a != b for a, b in zip(x, y)),
                       "diff": [100 * v for v in boot_ci([b - a for a, b in zip(x, y)])]}
    xb = [1.0 if g1[u]["B_gate"] else 0.0 for u in common]
    yb = [1.0 if g2[u]["B_gate"] else 0.0 for u in common]
    rerun["B"] = {"run1": 100 * np.mean(xb), "run2": 100 * np.mean(yb), "changed_rows": sum(a != b for a, b in zip(xb, yb)),
                  "diff": [100 * v for v in boot_ci([b - a for a, b in zip(xb, yb)])]}
    rerun["identical_text"] = sum(1 for u in common if True)
    print("== Rerun (greedy vs greedy_repeat, same rows)", json.dumps(rerun))
    report["rerun"] = rerun

    # 4. per check, disagreements and their attribution
    per = collections.defaultdict(lambda: collections.Counter())
    finding_counts = collections.defaultdict(collections.Counter)
    decision_counts = collections.defaultdict(collections.Counter)
    for r in recs:
        ext = {"A": r["extraction_differs_A"], "B": r["extraction_differs_B"]}
        for ci, c in enumerate(r["cons"]):
            p = per[c["id"]]
            p["n"] += 1
            p["A_pass"] += c["A"] is True
            p["R_pass"] += c["R"] is True
            if c["B"] is not None:
                p["B_n"] += 1
                p["B_pass"] += c["B"] is True
                p["A_ne_B"] += c["A"] is not c["B"]
            for g in ("A", "B"):
                gv = c[g]
                if gv is None or gv is c["R"]:
                    continue
                p[g + "_ne_R"] += 1
                if ext[g]:
                    kind = "P1"
                elif c.get(g + "_explained"):
                    kind = "decision"
                    for d in c[g + "_explained"]:
                        decision_counts[g][d] += 1
                elif c.get(g + "_explained_all_used"):
                    kind = "decision"
                    decision_counts[g]["several entries together"] += 1
                else:
                    kind = finding_for(g, c, kwargs_of[r["uuid"]][ci])
                    if g == "A" and c["A_err"] is not None:
                        kind = "F19" if c["id"] == "last_word:last_word_answer" else "A-exception"
                p[g + "_" + ("decision" if kind == "decision" else "finding")] += 1
                finding_counts[kind][g] += 1
                finding_counts[kind][g + ":" + c["id"]] += 1
    print("== Per check: verdicts, pass % (A, B, R), disagreements with R (decision-explained / finding)")
    total_v = sum(p["n"] for p in per.values())
    for iid, p in sorted(per.items()):
        bpass = f"{100 * p['B_pass'] / p['B_n']:5.1f}" if p["B_n"] else "  -  "
        print(f"  {iid:<45} n={p['n']:5d} A={100 * p['A_pass'] / p['n']:5.1f} B={bpass} R={100 * p['R_pass'] / p['n']:5.1f} "
              f"A!=R={p['A_ne_R']:4d} (dec {p['A_decision']:4d}, def {p['A_finding']:4d})  "
              f"B!=R={p['B_ne_R']:4d} (dec {p['B_decision']:4d}, def {p['B_finding']:4d})  A!=B={p['A_ne_B']:4d}")
    report["per_check"] = {k: dict(v) for k, v in per.items()}
    print("== Disagreements with R by cause (constraint verdicts); total verdicts", total_v)
    for kind, c in sorted(finding_counts.items(), key=lambda kv: -(kv[1]["A"] + kv[1]["B"])):
        detail = {k: v for k, v in c.items() if ":" in k}
        print(f"  {kind:<12} A={c['A']:5d} B={c['B']:5d}  {detail}")
    report["by_cause"] = {k: dict(v) for k, v in finding_counts.items()}
    print("== Decision entries that explain a grader/R disagreement (single entry, reading B reproduces the grader)")
    for g in ("A", "B"):
        print("  ", g, dict(decision_counts[g].most_common()))
    report["decision_explains"] = {g: dict(v) for g, v in decision_counts.items()}

    # 5. effect of each decision entry on R (constraint verdicts and row rewards that flip under reading B)
    eff = collections.defaultdict(collections.Counter)
    for r in recs:
        row_flip = collections.Counter()
        for c in r["cons"]:
            for d in c.get("flips", {}):
                eff[d]["verdicts"] += 1
                row_flip[d] += 1
        for d in row_flip:
            # a row reward flips when this constraint is the only failure (R 1 -> 0) or the row passes otherwise
            others_pass = lambda cc: all(x["R"] for x in r["cons"] if x is not cc)  # noqa: E731
            for c in r["cons"]:
                if d in c.get("flips", {}) and others_pass(c) and not r["r_extraction_failed"]:
                    eff[d]["rows"] += 1
                    break
    print("== Effect of each decision entry's reading B on R (constraint verdicts, row rewards that flip)")
    for d, c in sorted(eff.items(), key=lambda kv: -kv[1]["verdicts"]):
        print(f"  {d:<24} verdicts={c['verdicts']:5d} rows={c['rows']:5d}")
    report["decision_effect"] = {k: dict(v) for k, v in eff.items()}

    # 6. false rewards (A session reward 1 that R fails) and lost rewards
    fr = collections.Counter()
    for r in recs:
        if r["A_session_reward"] == 1.0:
            fr["A_passes"] += 1
            if r["R_reward"] == 0.0:
                fr["false"] += 1
                if r["extraction_differs_A"]:
                    fr["false_extraction"] += 1
                else:
                    bad = [c for c in r["cons"] if c["A"] is True and c["R"] is False]
                    if all(c.get("A_explained") or c.get("A_explained_all_used") for c in bad):
                        fr["false_decision_only"] += 1
                    else:
                        fr["false_finding"] += 1
                if held_out(r["uuid"]):
                    fr["false_heldout"] += 1
            if held_out(r["uuid"]):
                fr["A_passes_heldout"] += 1
        elif r["R_reward"] == 1.0:
            fr["lost"] += 1
        if r["B_gate"]:
            fr["B_passes"] += 1
            if r["R_reward"] == 0.0:
                fr["B_false_pass"] += 1
                if not r["extraction_differs_B"]:
                    bad = [c for c in r["cons"] if c["B"] is True and c["R"] is False]
                    if bad and not all(c.get("B_explained") or c.get("B_explained_all_used") for c in bad):
                        fr["B_false_pass_finding"] += 1
        elif r["R_reward"] == 1.0:
            fr["B_lost"] += 1
    print("== False rewards (A session reward 1.0, R 0.0)", dict(fr))
    report["false_rewards"] = dict(fr)

    # 7. reference comparison: A vs B on deterministic constraints, who is right per R
    ab = collections.Counter()
    for r in recs:
        for c in r["cons"]:
            if c["B"] is None or c["A"] is c["B"]:
                continue
            ab["disagree"] += 1
            if c["R"] is c["A"]:
                ab["B_wrong_" + ("decision" if c.get("B_explained") or c.get("B_explained_all_used") else ("P1" if r["extraction_differs_B"] else "defect"))] += 1
            else:
                ab["A_wrong_" + ("decision" if c.get("A_explained") or c.get("A_explained_all_used") else ("P1" if r["extraction_differs_A"] else "defect"))] += 1
    print("== Reference comparison (A vs B on deterministic constraints)", dict(ab))
    report["reference_comparison"] = dict(ab)
    OUT.write_text(json.dumps(report, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
