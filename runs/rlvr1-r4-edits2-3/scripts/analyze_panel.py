"""Step 5 analysis of audit/panel/verdicts.jsonl. Writes audit/panel/summary.json and prints tables.

Graders: skyrl (NVIDIA checkers after final_answer_text), tc (verifyit gate; judged constraints
have no deterministic verdict), rep (replacement, proposed readings; an extraction failure fails
every constraint). Row-level scores are binary (all constraints pass). Because the task-curation
reward also depends on the LLM judge, the comparable task-curation number is the gate: all
deterministic constraints pass. Intervals: 95% paired bootstrap over responses (2,000 resamples,
seed 0). Held-out: first hex digit of sha256(uuid) even (fixed in audit/ISSUE.md before analysis).
"""

import collections
import hashlib
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIT = os.path.dirname(HERE)
PATH = os.path.join(AUDIT, "panel", "verdicts.jsonl")
SEMANTIC = {"count:count_unique", "detectable_format:bigram_wrapping", "language:response_language",
            "letters:letter_counting"}


def held_out(uuid):
    return int(hashlib.sha256(uuid.encode()).hexdigest()[0], 16) % 2 == 0


def boot(diffs, n=2000, seed=0):
    rng = random.Random(seed)
    m = len(diffs)
    if m == 0:
        return (0.0, 0.0)
    stats = []
    for _ in range(n):
        s = 0.0
        for _ in range(m):
            s += diffs[rng.randrange(m)]
        stats.append(s / m)
    stats.sort()
    return (stats[int(0.025 * n)], stats[int(0.975 * n) - 1])


def config_name(r):
    return f"{r['folder']}/{r['run']}"


def main():
    recs = [json.loads(line) for line in open(PATH, encoding="utf-8")]
    out = {"responses": len(recs)}

    # A. stored-record counts
    A = collections.defaultdict(collections.Counter)
    for r in recs:
        c = A[config_name(r)]
        c["responses"] += 1
        c["truncated (finish_reason length)"] += r["finish_reason"] == "length"
        if r["reasoning_model"]:
            c["reasoning never closed (no </think>)"] += not r["has_close_think"]
        c["literal <think> in the text"] += r["has_open_think"]
        c["SkyRL graded text empty"] += r["skyrl"]["action_empty"]
        c["task-curation candidate empty"] += r["tc"]["candidate_empty"]
        c["SkyRL checker exception (row INFRA_ERROR, reward 0)"] += r["skyrl"]["infra"]
        c["contract extraction failure"] += r["rep"]["extraction_failure"]
    out["stored_records"] = {k: dict(v) for k, v in A.items()}

    # B. scores per config
    def row_scores(r):
        det = [i for i, iid in enumerate(r["ids"]) if iid not in SEMANTIC]
        rep = r["rep"]["results"]
        sky = r["skyrl"]["results"]
        return {
            "skyrl": r["skyrl"]["reward"],
            "rep": float(all(rep)),
            "tc_gate": float(r["tc"]["gate"]),
            "rep_gate": float(all(rep[i] for i in det)),
            "skyrl_gate": float(all(sky[i] for i in det) and not r["skyrl"]["infra"]),
        }

    B = {}
    for subset in ("all", "held_out"):
        groups = collections.defaultdict(list)
        for r in recs:
            if subset == "held_out" and not held_out(r["uuid"]):
                continue
            groups[config_name(r)].append(row_scores(r))
        res = {}
        for cfg, rows in sorted(groups.items()):
            n = len(rows)
            mean = {k: sum(x[k] for x in rows) / n for k in rows[0]}
            d1 = [x["rep"] - x["skyrl"] for x in rows]
            d2 = [x["rep_gate"] - x["tc_gate"] for x in rows]
            d3 = [x["tc_gate"] - x["skyrl_gate"] for x in rows]
            res[cfg] = {
                "n": n,
                **{k: round(100 * v, 2) for k, v in mean.items()},
                "rep_minus_skyrl": round(100 * sum(d1) / n, 2),
                "rep_minus_skyrl_ci": [round(100 * x, 2) for x in boot(d1)],
                "rep_gate_minus_tc_gate": round(100 * sum(d2) / n, 2),
                "rep_gate_minus_tc_gate_ci": [round(100 * x, 2) for x in boot(d2)],
                "tc_gate_minus_skyrl_gate": round(100 * sum(d3) / n, 2),
                "tc_gate_minus_skyrl_gate_ci": [round(100 * x, 2) for x in boot(d3)],
            }
        B[subset] = res
    out["scores"] = B

    # C. per-check verdicts and disagreements
    C = collections.defaultdict(collections.Counter)
    examples = {}
    for r in recs:
        if r["rep"]["extraction_failure"]:
            continue
        for i, iid in enumerate(r["ids"]):
            c = C[iid]
            rep = r["rep"]["results"][i]
            sky = r["skyrl"]["results"][i] and not r["skyrl"]["errors"][i]
            tc = r["tc"]["results"][i]
            explained_vs = lambda g: bool(r["flips"][i]) or r["rep"]["all_other"][i] == g
            c["n"] += 1
            c["rep_pass"] += rep
            c["skyrl_pass"] += sky
            if r["skyrl"]["errors"][i]:
                c["skyrl_exception"] += 1
            if sky != rep:
                kind = "skyrl_false_pass" if sky else "skyrl_false_fail"
                c[kind] += 1
                explained = explained_vs(sky)
                c[kind + ("_decision" if explained else "_defect")] += 1
                examples.setdefault((iid, kind, explained), (r["folder"], r["run"], r["uuid"]))
            if tc is not None:
                c["tc_n"] += 1
                c["tc_pass"] += tc
                if tc != rep:
                    kind = "tc_false_pass" if tc else "tc_false_fail"
                    c[kind] += 1
                    explained = explained_vs(tc)
                    c[kind + ("_decision" if explained else "_defect")] += 1
                    examples.setdefault((iid, kind, explained), (r["folder"], r["run"], r["uuid"]))
                if tc != sky:
                    c["tc_vs_skyrl_disagree"] += 1
                    if tc == rep:
                        c["ref_comparison: reference wrong" + (" (decision)" if explained_vs(sky) else " (defect)")] += 1
                    elif sky == rep:
                        c["ref_comparison: verifyit wrong" + (" (decision)" if explained_vs(tc) else " (defect)")] += 1
    out["per_check"] = {k: dict(v) for k, v in sorted(C.items())}
    out["examples"] = {f"{k[0]} | {k[1]} | {'decision' if k[2] else 'defect'}": v for k, v in examples.items()}

    # D. false rewards
    D = {}
    for subset in ("all", "held_out"):
        res = {}
        groups = collections.defaultdict(list)
        for r in recs:
            if subset == "held_out" and not held_out(r["uuid"]):
                continue
            groups[config_name(r)].append(r)
        for cfg, rs in sorted(groups.items()):
            c = collections.Counter()
            for r in rs:
                sc = row_scores(r)
                if sc["skyrl"] == 1.0:
                    c["skyrl_passes"] += 1
                    if sc["rep"] == 0.0:
                        c["skyrl_false_rewards"] += 1
                        if r["rep"]["extraction_failure"]:
                            c["fr: reasoning never closed"] += 1
                        elif r["skyrl"]["action_empty"]:
                            c["fr: graded text empty after extraction"] += 1
                        else:
                            wrong = [i for i, (a, b) in enumerate(zip(r["skyrl"]["results"], r["rep"]["results"])) if a != b]
                            if all(r["flips"][i] or r["rep"]["all_other"][i] == r["skyrl"]["results"][i] for i in wrong):
                                c["fr: decisions only"] += 1
                            else:
                                c["fr: checker defect"] += 1
                if sc["tc_gate"] == 1.0:
                    c["tc_gate_passes"] += 1
                    if sc["rep_gate"] == 0.0:
                        c["tc_gate_false_passes"] += 1
                        if r["rep"]["extraction_failure"]:
                            c["tc_fp: reasoning never closed"] += 1
                        elif r["tc"]["candidate_empty"]:
                            c["tc_fp: candidate empty after extraction"] += 1
                if sc["rep"] == 1.0 and sc["skyrl"] == 0.0:
                    c["skyrl_false_zero"] += 1
                if sc["rep_gate"] == 1.0 and sc["tc_gate"] == 0.0:
                    c["tc_gate_false_fail"] += 1
            c["skyrl_false_reward_share_of_passes_pct"] = round(100 * c["skyrl_false_rewards"] / max(1, c["skyrl_passes"]), 1)
            c["tc_gate_false_pass_share_pct"] = round(100 * c["tc_gate_false_passes"] / max(1, c["tc_gate_passes"]), 1)
            res[cfg] = dict(c)
        tot = collections.Counter()
        for v in res.values():
            for k, x in v.items():
                if not k.endswith("_pct"):
                    tot[k] += x
        tot["skyrl_false_reward_share_of_passes_pct"] = round(100 * tot["skyrl_false_rewards"] / max(1, tot["skyrl_passes"]), 1)
        tot["tc_gate_false_pass_share_pct"] = round(100 * tot["tc_gate_false_passes"] / max(1, tot["tc_gate_passes"]), 1)
        res["TOTAL"] = dict(tot)
        D[subset] = res
    out["false_rewards"] = D

    # E. greedy rerun
    g = {r["uuid"]: r for r in recs if r["folder"] == "Qwen__Qwen3-4B-Instruct-2507" and r["run"] == "greedy"}
    g2 = {r["uuid"]: r for r in recs if r["folder"] == "Qwen__Qwen3-4B-Instruct-2507" and r["run"] == "greedy_repeat"}
    common = sorted(set(g) & set(g2))
    E = collections.Counter()
    for u in common:
        a, b = g[u], g2[u]
        E["rows"] += 1
        E["identical_response"] += a["raw_sha256"] == b["raw_sha256"]
        for k in ("skyrl", "rep", "tc_gate"):
            sa, sb = row_scores(a)[k], row_scores(b)[k]
            E[k + "_verdict_changed"] += sa != sb
            E[k + "_sum_a"] += sa
            E[k + "_sum_b"] += sb
    E2 = dict(E)
    for k in ("skyrl", "rep", "tc_gate"):
        E2[k + "_score_diff_pts"] = round(100 * (E[k + "_sum_b"] - E[k + "_sum_a"]) / max(1, E["rows"]), 2)
    out["rerun"] = E2

    # F. decision effects (single flips, constraint verdicts and row scores)
    F = collections.defaultdict(collections.Counter)
    for r in recs:
        if r["rep"]["extraction_failure"]:
            continue
        base = r["rep"]["results"]
        names = {n for fl in r["flips"] for n in fl}
        for n in names:
            new = [(not v) if n in fl else v for v, fl in zip(base, r["flips"])]
            F[n]["constraint_verdicts_flipped"] += sum(1 for fl in r["flips"] if n in fl)
            delta = float(all(new)) - float(all(base))
            F[n]["rows_score_up"] += delta > 0
            F[n]["rows_score_down"] += delta < 0
            F[n]["agrees_with_skyrl_after_flip"] += sum(
                1 for i, fl in enumerate(r["flips"]) if n in fl and new[i] == (r["skyrl"]["results"][i] and not r["skyrl"]["errors"][i]))
            F[n]["agrees_with_tc_after_flip"] += sum(
                1 for i, fl in enumerate(r["flips"]) if n in fl and r["tc"]["results"][i] is not None and new[i] == r["tc"]["results"][i])
    out["decision_effects"] = {k: dict(v) for k, v in sorted(F.items(), key=lambda kv: -kv[1]["constraint_verdicts_flipped"])}

    with open(os.path.join(AUDIT, "panel", "summary.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=1)

    # print
    print("== stored records")
    for cfg, c in out["stored_records"].items():
        print(f"  {cfg}: {c}")
    for subset in ("all", "held_out"):
        print(f"== scores ({subset}), row-level binary, percent")
        for cfg, v in B[subset].items():
            print(f"  {cfg:52s} n={v['n']:5d} skyrl={v['skyrl']:6.2f} rep={v['rep']:6.2f} d={v['rep_minus_skyrl']:+6.2f} "
                  f"{v['rep_minus_skyrl_ci']} | tc_gate={v['tc_gate']:6.2f} rep_gate={v['rep_gate']:6.2f} "
                  f"d={v['rep_gate_minus_tc_gate']:+6.2f} {v['rep_gate_minus_tc_gate_ci']} | skyrl_gate={v['skyrl_gate']:6.2f}")
    print("== false rewards")
    for subset in ("all", "held_out"):
        print("  ", subset, D[subset]["TOTAL"])
        if subset == "all":
            for cfg, v in D[subset].items():
                print("     ", cfg, v)
    print("== rerun", out["rerun"])
    print("== per check (n, pass% skyrl/tc/rep, skyrl FP/FN [defect], tc FP/FN [defect])")
    for iid, c in out["per_check"].items():
        n = c["n"]
        tcn = c.get("tc_n", 0)
        print(f"  {iid:46s} n={n:5d} sky={100*c['skyrl_pass']/n:5.1f} tc={(100*c.get('tc_pass',0)/tcn) if tcn else float('nan'):5.1f} "
              f"rep={100*c['rep_pass']/n:5.1f} | skyFP={c.get('skyrl_false_pass',0):4d}[{c.get('skyrl_false_pass_defect',0):4d}] "
              f"skyFN={c.get('skyrl_false_fail',0):4d}[{c.get('skyrl_false_fail_defect',0):4d}] | "
              f"tcFP={c.get('tc_false_pass',0):4d}[{c.get('tc_false_pass_defect',0):4d}] tcFN={c.get('tc_false_fail',0):4d}[{c.get('tc_false_fail_defect',0):4d}] "
              f"exc={c.get('skyrl_exception',0)}")
    print("== decision effects (top)")
    for k, v in list(out["decision_effects"].items())[:45]:
        print(f"  {k:28s} {v}")


if __name__ == "__main__":
    main()
