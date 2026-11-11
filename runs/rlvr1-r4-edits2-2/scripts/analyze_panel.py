"""Step 5 analysis of audit/out/panel/*.jsonl. Writes audit/out/panel_summary.json and prints a text summary.

Terms:
- nvidia / verifyit / replacement: per-constraint verdicts.
- SkyRL reward: binary reward of grade_instruction_following on final_answer_text (an exception row is an
  INFRA_ERROR with reward 0.0; reported both ways).
- Gate: curation's deterministic gate (semantic constraints excluded). Replacement gate = replacement verdicts on
  the same non-semantic constraints. Replacement reward = all constraints (semantic ones by the replacement's
  approximations).
- A disagreement between a grader and the replacement is "decision-explained" when the non-proposed reading of one
  decision entry (repl_flips) gives the grader's verdict; otherwise it is a contract contradiction ("defect").
"""
import collections
import glob
import json
import os
import random
import sys

AUDIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, AUDIT)
from harness import SEMANTIC  # noqa: E402

HELD_OUT = {"Qwen__Qwen2.5-7B-Instruct/sample0", "allenai__OLMo-2-1124-7B-Instruct/sample0"}


def load():
    recs = []
    for path in sorted(glob.glob(os.path.join(AUDIT, "out", "panel", "*.jsonl"))):
        with open(path, encoding="utf-8") as f:
            recs.extend(json.loads(line) for line in f)
    return recs


def boot_ci(diffs, n=2000, seed=0):
    rng = random.Random(seed)
    k = len(diffs)
    means = []
    for _ in range(n):
        s = 0.0
        for _ in range(k):
            s += diffs[rng.randrange(k)]
        means.append(s / k)
    means.sort()
    return means[int(0.025 * n)], means[int(0.975 * n) - 1]


def main():
    recs = load()
    runs = sorted({r["run"] for r in recs})
    out = {"runs": {}, "checks": {}, "decisions": {}, "special": {}}

    # ---------------- per run scores
    for run in runs:
        rs = [r for r in recs if r["run"] == run]
        n = len(rs)
        sky = [r["skyrl_reward"] for r in rs]
        infra = sum(r["skyrl_infra"] for r in rs)
        gate = [float(r["gate_pass"]) for r in rs]
        repl_all = [float(all(r["replacement"])) for r in rs]
        repl_gate = [float(all(v for v, i in zip(r["replacement"], r["ids"]) if i not in SEMANTIC)) for r in rs]
        d_sky = [b - a for a, b in zip(sky, repl_all)]
        d_gate = [b - a for a, b in zip(gate, repl_gate)]
        sky_pass_wrong = sum(1 for r in rs if r["skyrl_reward"] == 1.0 and not all(r["replacement"]))
        gate_pass_wrong = sum(1 for r, g in zip(rs, repl_gate) if r["gate_pass"] and not g)

        def defect_pass(r, grader):
            """A false pass that no single decision reading explains, on some constraint of the row."""
            for i, iid in enumerate(r["ids"]):
                v = r[grader][i]
                if v is True and r["replacement"][i] is False:
                    if not any(fv is True for fv in r["repl_flips"].get(str(i), {}).values()):
                        return True
            return False
        sky_false_defect = sum(1 for r in rs if r["skyrl_reward"] == 1.0 and not all(r["replacement"]) and defect_pass(r, "nvidia"))
        gate_false_defect = sum(1 for r, g in zip(rs, repl_gate) if r["gate_pass"] and not g and defect_pass(r, "verifyit"))
        out["runs"][run] = {
            "n": n,
            "held_out": run in HELD_OUT,
            "finish_length": sum(r["finish_reason"] == "length" for r in rs),
            "skyrl_text_empty": sum(r["skyrl_text_empty"] for r in rs),
            "repl_extraction_failure": sum(r["repl_extraction_failure"] for r in rs),
            "unclosed_graded_nonempty": sum(1 for r in rs if r["repl_extraction_failure"] and not r["skyrl_text_empty"]),
            "unclosed_graded_empty": sum(1 for r in rs if r["repl_extraction_failure"] and r["skyrl_text_empty"]),
            "literal_think_nonreasoning": sum(1 for r in rs if not r["reasoning"] and r["raw_has_think_open"]),
            "skyrl_infra_rows": infra,
            "skyrl_score": sum(sky) / n,
            "skyrl_score_excl_infra": sum(s for s, r in zip(sky, rs) if not r["skyrl_infra"]) / max(1, n - infra),
            "gate_pass_rate": sum(gate) / n,
            "repl_score": sum(repl_all) / n,
            "repl_gate_rate": sum(repl_gate) / n,
            "skyrl_to_repl": sum(d_sky) / n,
            "skyrl_to_repl_ci": boot_ci(d_sky),
            "gate_to_repl": sum(d_gate) / n,
            "gate_to_repl_ci": boot_ci(d_gate),
            "skyrl_passes": int(sum(sky)),
            "skyrl_false_rewards": sky_pass_wrong,
            "skyrl_false_rewards_defect": sky_false_defect,
            "gate_passes": int(sum(gate)),
            "gate_false_passes": gate_pass_wrong,
            "gate_false_passes_defect": gate_false_defect,
            "rows_gained_repl_vs_skyrl": sum(1 for x in d_sky if x > 0),
            "rows_lost_repl_vs_skyrl": sum(1 for x in d_sky if x < 0),
        }

    # ---------------- rerun: greedy vs greedy_repeat
    g1 = {r["uuid"]: r for r in recs if r["run"].endswith("/greedy")}
    g2 = {r["uuid"]: r for r in recs if r["run"].endswith("/greedy_repeat")}
    common = sorted(set(g1) & set(g2))
    rer = {"rows": len(common)}
    for name, key in (("skyrl", lambda r: r["skyrl_reward"]), ("gate", lambda r: float(r["gate_pass"])),
                      ("replacement", lambda r: float(all(r["replacement"])))):
        a = [key(g1[u]) for u in common]
        b = [key(g2[u]) for u in common]
        rer[name + "_changed_rows"] = sum(1 for x, y in zip(a, b) if x != y)
        rer[name + "_score_diff"] = (sum(b) - sum(a)) / len(common)
    raw1, raw2 = {}, {}
    for name, store in (("greedy", raw1), ("greedy_repeat", raw2)):
        with open(os.path.join(os.path.dirname(AUDIT), "case", "panel", "Qwen__Qwen3-4B-Instruct-2507", name + ".jsonl"), encoding="utf-8") as f:
            for line in f:
                x = json.loads(line)
                store[x["uuid"]] = x["raw_response"]
    rer["identical_raw_responses"] = sum(1 for u in common if raw1[u] == raw2[u])
    out["rerun"] = rer

    # ---------------- per check
    checks = collections.defaultdict(lambda: collections.Counter())
    nv_err = collections.Counter()
    dec_moves = collections.Counter()
    for r in recs:
        split = "held" if r["run"] in HELD_OUT else "dev"
        flips = r["repl_flips"]
        for i, iid in enumerate(r["ids"]):
            c = checks[iid]
            rep = r["replacement"][i]
            nv = r["nvidia"][i]
            vi = r["verifyit"][i]
            c["n"] += 1
            c["repl_pass"] += rep
            c["nvidia_pass"] += nv
            if r["nvidia_err"][i]:
                c["nvidia_error"] += 1
                nv_err[(iid, r["nvidia_err"][i].split(":")[0])] += 1
            f = flips.get(str(i), {})
            for d in f:
                dec_moves[d] += 1
            for g, v in (("nvidia", nv), ("verifyit", vi)):
                if v is None:
                    continue
                c[g + "_graded"] += 1
                c[g + "_pass_n"] += v
                if v == rep:
                    continue
                explained = [d for d, fv in f.items() if fv == v]
                kind = "decision" if explained else "defect"
                c[f"{g}_{kind}"] += 1
                c[f"{g}_{kind}_{split}"] += 1
                c[f"{g}_{kind}_{'false_pass' if v else 'false_fail'}"] += 1
                for d in explained:
                    c[f"{g}_by_{d}"] += 1
            if vi is not None and nv != vi:
                c["nv_vs_vi_disagree"] += 1
    for iid, c in sorted(checks.items()):
        out["checks"][iid] = dict(c)
    out["nvidia_errors"] = {f"{k[0]} | {k[1]}": v for k, v in nv_err.items()}
    out["decision_moves"] = dict(dec_moves)

    # ---------------- totals (constraint level)
    tot = collections.Counter()
    for iid, c in checks.items():
        for k, v in c.items():
            tot[k] += v
    out["totals"] = dict(tot)

    # ---------------- special counters
    sp = collections.Counter()
    for r in recs:
        for i, (iid, kw) in enumerate(zip(r["ids"], r["kwargs"])):
            if iid == "length_constraints:nth_paragraph_first_word" and kw["nth_paragraph"] > kw["num_paragraphs"]:
                sp["N17_constraints"] += 1
                sp["N17_nvidia_pass"] += r["nvidia"][i]
                sp["N17_verifyit_pass"] += bool(r["verifyit"][i])
            if iid == "keywords:word_count_different_numbers":
                key = "B2_" + kw["relation"].replace(" ", "_")
                sp[key + "_n"] += 1
                sp[key + "_nvidia_ne_repl"] += r["nvidia"][i] != r["replacement"][i]
                sp[key + "_verifyit_ne_repl"] += r["verifyit"][i] != r["replacement"][i]
        if r["repl_extraction_failure"]:
            sp["P1P2_extraction_failures"] += 1
            sp["P1P2_skyrl_reward_1"] += r["skyrl_reward"] == 1.0
            sp["P1P2_gate_pass"] += r["gate_pass"]
            sp["P1P2_nvidia_constraint_passes"] += sum(r["nvidia"])
            sp["P1P2_constraints"] += len(r["ids"])
        if not r["reasoning"] and r["raw_has_think_open"]:
            sp["literal_think_rows"] += 1
            sp["literal_think_skyrl_empty"] += r["skyrl_text_empty"]
            sp["literal_think_skyrl_reward_1"] += r["skyrl_reward"] == 1.0
        if r["skyrl_text_empty"] and not r["repl_extraction_failure"]:
            sp["empty_answer_rows"] += 1
    out["special"] = dict(sp)

    path = os.path.join(AUDIT, "out", "panel_summary.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print(json.dumps({k: out[k] for k in ("runs", "rerun", "special", "totals", "nvidia_errors", "decision_moves")}, indent=1))


if __name__ == "__main__":
    main()
