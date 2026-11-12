"""Step 5 analysis of audit/work/panel_verdicts.jsonl.

Writes audit/work/panel_summary.json and prints the tables used in AUDIT.md.
Each constraint-level disagreement between a grader and the replacement is attributed:
- "decision:<entry>" when flipping that one decision entry makes the replacement agree;
- "defect" when no single flip does.
"""
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

A = Path("<W>/audit")
CASE = A.parent / "case"
sys.path.insert(0, str(A / "lib"))

from contract_grader import DEFAULT_READINGS, ContractGrader  # noqa: E402
from relevance import relevant  # noqa: E402
import harness as h  # noqa: E402
from multiprocessing import Pool  # noqa: E402

_W = {}


def _init():
    sys.path.insert(0, str(A / "lib"))
    _W["rows"] = h.load_rows()


def _attr(task):
    """Decision entries (single, then pairs) whose non-proposed reading gives the grader's verdict."""
    iid, kw, text_raw, thinking, grader_verdict = task
    entries = relevant(iid)

    def verdict(flips):
        cg = ContractGrader({e: "B" if DEFAULT_READINGS[e] == "A" else "A" for e in flips})
        return cg.check(iid, kw, cg.extract(text_raw, thinking))

    singles = [e for e in entries if verdict([e]) == grader_verdict]
    if singles:
        return singles
    for i, a in enumerate(entries):
        for b in entries[i + 1:]:
            if verdict([a, b]) == grader_verdict:
                return [a + "+" + b]
    return []


def boot_ci(diffs, n_boot=2000, seed=0):
    """95% percentile bootstrap interval of the mean of paired row differences."""
    import numpy as np

    if not diffs:
        return (0.0, 0.0)
    rng = np.random.default_rng(seed)
    x = np.asarray(diffs, dtype=float)
    means = x[rng.integers(0, len(x), size=(n_boot, len(x)))].mean(axis=1)
    return (float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975)))



def main():
    rows = h.load_rows()
    recs = [json.loads(line) for line in open(A / "work" / "panel_verdicts.jsonl", encoding="utf-8")]
    raw = {}
    for path in sorted((CASE / "panel").glob("*/*.jsonl")):
        with open(path, encoding="utf-8") as f:
            for i, line in enumerate(f):
                raw[(path.parent.name, path.stem, i)] = json.loads(line)["raw_response"]
    summary = {}
    # ---------------------------------------------------------------- stored records per run
    runs = defaultdict(list)
    for r in recs:
        runs[(r["folder"], r["run"])].append(r)
    stored = {}
    for key, rs in sorted(runs.items()):
        stored["/".join(key)] = {
            "n": len(rs),
            "finish_length": sum(r["finish_reason"] == "length" for r in rs),
            "thinking": rs[0]["thinking"],
            "has_close": sum(r["has_close"] for r in rs),
            "has_open": sum(r["has_open"] for r in rs),
            "extraction_failure": sum(r["extraction_failure"] for r in rs),
            "extraction_failure_and_length": sum(r["extraction_failure"] and r["finish_reason"] == "length" for r in rs),
            "skyrl_text_empty": sum(r["skyrl_text_empty"] for r in rs),
            "graded_text_differs": sum(not r["same_text"] for r in rs),
            "skyrl_infra_error": sum(r["skyrl_infra"] for r in rs),
            "extraction_failure_skyrl_reward_1": sum(r["extraction_failure"] and r["skyrl_reward"] == 1.0 for r in rs),
            "extraction_failure_gate_pass": sum(r["extraction_failure"] and r["gate_pass"] for r in rs),
        }
    summary["stored"] = stored
    print("== stored records")
    for k, v in stored.items():
        print(k, v)

    # ---------------------------------------------------------------- scores per run
    scores = {}
    for key, rs in sorted(runs.items()):
        sky = [r["skyrl_reward"] for r in rs]
        repl = [float(all(r["repl"])) for r in rs]
        gate = [float(r["gate_pass"]) for r in rs]
        repl_gate = [float(all(v for v, gv in zip(r["repl"], r["gate"]) if gv is not None)) for r in rs]
        d_sky = [b - a for a, b in zip(sky, repl)]
        d_gate = [b - a for a, b in zip(gate, repl_gate)]
        false_rewards = sum(1 for r in rs if r["skyrl_reward"] == 1.0 and not all(r["repl"]))
        sky_rewards = sum(1 for r in rs if r["skyrl_reward"] == 1.0)
        false_gate = sum(1 for r, rg in zip(rs, repl_gate) if r["gate_pass"] and not rg)
        gate_passes = sum(1 for r in rs if r["gate_pass"])
        LANG = {"language:response_language", "change_case:english_capital", "change_case:english_lowercase"}
        repl_nolang = [float(all((bool(sv) if iid in LANG else rv) for iid, sv, rv in zip(r["ids"], r["skyrl"], r["repl"]))) for r in rs]
        d_nolang = [b_ - a_ for a_, b_ in zip(sky, repl_nolang)]
        scores["/".join(key) + "#nolang"] = {
            "replacement_nolang": sum(repl_nolang) / len(rs), "delta": sum(d_nolang) / len(rs), "ci": boot_ci(d_nolang),
            "false_rewards_nolang": sum(1 for r, rn in zip(rs, repl_nolang) if r["skyrl_reward"] == 1.0 and not rn),
        }
        scores["/".join(key)] = {
            "n": len(rs),
            "skyrl": sum(sky) / len(rs), "replacement": sum(repl) / len(rs),
            "delta_repl_minus_skyrl": sum(d_sky) / len(rs), "ci": boot_ci(d_sky),
            "rows_gained": sum(1 for d in d_sky if d > 0), "rows_lost": sum(1 for d in d_sky if d < 0),
            "gate": sum(gate) / len(rs), "replacement_gate_constraints": sum(repl_gate) / len(rs),
            "delta_gate": sum(d_gate) / len(rs), "ci_gate": boot_ci(d_gate),
            "skyrl_rewards": sky_rewards, "false_rewards": false_rewards,
            "gate_passes": gate_passes, "false_gate_passes": false_gate,
        }
    summary["scores"] = scores
    print("== scores")
    for k, v in scores.items():
        print(k, {kk: (round(vv, 4) if isinstance(vv, float) else vv) for kk, vv in v.items()})

    # ---------------------------------------------------------------- rerun
    g1 = {r["uuid"]: r for r in runs[("Qwen__Qwen3-4B-Instruct-2507", "greedy")]}
    g2 = {r["uuid"]: r for r in runs[("Qwen__Qwen3-4B-Instruct-2507", "greedy_repeat")]}
    same_raw = sum(1 for u in g1 if raw[(g1[u]["folder"], "greedy", g1[u]["i"])] == raw[(g2[u]["folder"], "greedy_repeat", g2[u]["i"])])
    rerun = {
        "rows": len(g1), "identical_responses": same_raw,
        "skyrl_changed_rows": sum(1 for u in g1 if g1[u]["skyrl_reward"] != g2[u]["skyrl_reward"]),
        "repl_changed_rows": sum(1 for u in g1 if all(g1[u]["repl"]) != all(g2[u]["repl"])),
        "gate_changed_rows": sum(1 for u in g1 if g1[u]["gate_pass"] != g2[u]["gate_pass"]),
        "skyrl_score_diff": (sum(g2[u]["skyrl_reward"] for u in g1) - sum(g1[u]["skyrl_reward"] for u in g1)) / len(g1),
        "repl_score_diff": (sum(all(g2[u]["repl"]) for u in g1) - sum(all(g1[u]["repl"]) for u in g1)) / len(g1),
        "gate_score_diff": (sum(g2[u]["gate_pass"] for u in g1) - sum(g1[u]["gate_pass"] for u in g1)) / len(g1),
    }
    summary["rerun"] = rerun
    print("== rerun", rerun)

    # ---------------------------------------------------------------- nth > num rows
    nth = [r for r in recs if r.get("nth_gt_num")]
    summary["nth_gt_num"] = {
        "responses": len(nth),
        "skyrl_reward_differs_between_seeds": sum(1 for r in nth if r["skyrl_reward"] != r["skyrl_reward_seed2"]),
        "skyrl_reward_1_seed1": sum(1 for r in nth if r["skyrl_reward"] == 1.0),
        "skyrl_reward_1_either_seed": sum(1 for r in nth if r["skyrl_reward"] == 1.0 or r["skyrl_reward_seed2"] == 1.0),
        "nth_constraint_pass_seed1": sum(1 for r in nth if r["skyrl"][r["ids"].index("length_constraints:nth_paragraph_first_word")]),
    }
    print("== nth>num", summary["nth_gt_num"])

    # ---------------------------------------------------------------- per check
    per = defaultdict(Counter)
    attr = defaultdict(Counter)
    examples = defaultdict(list)
    tasks, keys = [], []
    for r in recs:
        record = rows[r["uuid"]]
        for j, iid in enumerate(r["ids"]):
            s_, g, p = bool(r["skyrl"][j]), r["gate"][j], bool(r["repl"][j])
            c = per[iid]
            c["n"] += 1
            c["skyrl_pass"] += s_
            c["repl_pass"] += p
            c["skyrl_err"] += r["skyrl_err"][j] is not None
            if g is not None:
                c["gate_n"] += 1
                c["gate_pass"] += g
                c["gate_repl_pass"] += p
                if g != s_:
                    c["gate_vs_skyrl"] += 1
            for name, v in (("skyrl", s_), ("gate", g)):
                if v is None or v == p:
                    continue
                direction = "false_pass" if v else "false_fail"
                c[f"{name}_{direction}"] += 1
                if r["extraction_failure"]:
                    attr[(iid, name)]["extraction_failure"] += 1
                    continue
                tasks.append((iid, record["kwargs"][j], raw[(r["folder"], r["run"], r["i"])], r["thinking"], v))
                keys.append((iid, name, direction, r))
    with Pool(8, initializer=_init) as pool:
        results = pool.map(_attr, tasks, chunksize=16)
    for (iid, name, direction, r), explained in zip(keys, results):
        if explained:
            for e in explained:
                attr[(iid, name)]["decision:" + e] += 1
            attr[(iid, name)]["any_decision"] += 1
        else:
            attr[(iid, name)]["defect_" + direction] += 1
            r_flags = r.setdefault("defect", {})
            if len(examples[(iid, name, direction)]) < 8:
                examples[(iid, name, direction)].append({"folder": r["folder"], "run": r["run"], "i": r["i"], "uuid": r["uuid"]})
    summary["per_check"] = {k: dict(v) for k, v in sorted(per.items())}
    summary["attribution"] = {f"{k[0]}|{k[1]}": dict(v) for k, v in sorted(attr.items())}
    summary["defect_examples"] = {"|".join(k): v for k, v in examples.items()}
    print("== per check (constraint level)")
    for iid, c in sorted(per.items()):
        print(f"{iid:<46} n={c['n']:<5} sky={c['skyrl_pass']:<5} repl={c['repl_pass']:<5} gate={c.get('gate_pass', '-')!s:<5}/{c.get('gate_n', 0):<5}"
              f" skyFP={c['skyrl_false_pass']:<4} skyFF={c['skyrl_false_fail']:<4} gateFP={c['gate_false_pass']:<4} gateFF={c['gate_false_fail']:<4} gate!=sky={c['gate_vs_skyrl']:<4} err={c['skyrl_err']}")
    print("== attribution")
    for k, v in sorted(attr.items()):
        print(k, dict(v))
    (A / "work" / "panel_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
