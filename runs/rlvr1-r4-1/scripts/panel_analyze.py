"""Step 5 analysis of audit/out/panel_verdicts.jsonl.

Prints and writes audit/out/panel_summary.json:
- per run: responses, truncations, extraction status, SkyRL score, gate pass rate, contract score
  (replacement, proposed readings), the paired difference SkyRL - contract with a 95% bootstrap
  interval, and the same on the held-out half;
- per check: pass rates per grader and disagreement counts with the replacement, each disagreement
  classified as extraction, decision (an alternative reading of one entry gives the grader's
  verdict; entries named) or finding;
- false rewards: SkyRL passes that the contract contradicts, and the part that no single
  alternative reading explains;
- gate: false gate passes and false gate failures;
- rerun: greedy vs greedy_repeat;
- the RNG dependence of the 77 impossible nth_paragraph constraints.
"""
import collections
import dataclasses
import hashlib
import json
import pathlib
import random
import sys

import numpy as np

W = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W / "audit"))
sys.path.insert(0, str(W / "audit" / "scripts"))
import harness  # noqa: E402
import replacement as rp  # noqa: E402
from classify_fixtures import SWITCHES  # noqa: E402

V = W / "audit" / "out" / "panel_verdicts.jsonl"
PANEL = W / "case" / "panel"


def singles():
    for name, (entry, alt) in SWITCHES.items():
        if name == "word_mode":
            yield entry, dataclasses.replace(rp.PROPOSED, word_mode="whitespace")
            yield entry, dataclasses.replace(rp.PROPOSED, word_mode="split")
        elif name != "literal_think":
            yield entry, dataclasses.replace(rp.PROPOSED, **{name: alt})


SINGLES = list(singles())


def boot_diff(a, b, n=2000, seed=0):
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = a - b
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(d), size=(n, len(d)))
    m = d[idx].mean(axis=1)
    return float(d.mean()), float(np.quantile(m, 0.025)), float(np.quantile(m, 0.975))


def main():
    recs = [json.loads(l) for l in V.open(encoding="utf-8")]
    raw = {}
    for folder in {r["folder"] for r in recs}:
        for p in (PANEL / folder).glob("*.jsonl"):
            for line in p.open(encoding="utf-8"):
                x = json.loads(line)
                raw[(folder, p.stem, x["uuid"])] = x["raw_response"]
    prompts = {harness.record_of(r)["uuid"]: r["prompt"][0]["content"] for r in harness.load_rows()}

    # ---- classify every constraint-level disagreement once per (response, constraint, grader)
    cls_cache = {}

    def classify(rec, i, grader_verdict, grader):
        key = (rec["folder"], rec["run"], rec["uuid"], i, grader)
        if key in cls_cache:
            return cls_cache[key]
        reasoning = rec["folder"].endswith("__thinking")
        rtext = raw[(rec["folder"], rec["run"], rec["uuid"])]
        ctext = rp.graded_text(rtext, reasoning)
        gtext = harness.final_answer_text(rtext)
        iid, kw = rec["ids"][i], rec["kwargs"][i]
        if (ctext or "") != gtext and rec["repl_on_grader_text"][i] == grader_verdict:
            out = ("extraction", [])
        else:
            ents = []
            for entry, r in SINGLES:
                try:
                    v = rp.check_constraint(iid, kw, ctext, r, prompt=prompts[rec["uuid"]])
                except Exception:  # noqa: BLE001
                    continue
                if v == grader_verdict:
                    ents.append(entry)
            out = ("decision", sorted(set(ents))) if ents else ("finding", [])
        cls_cache[key] = out
        return out

    per_check = collections.defaultdict(lambda: collections.Counter())
    decision_counts = {"skyrl": collections.Counter(), "gate": collections.Counter()}
    finding_examples = collections.defaultdict(list)
    runs = collections.OrderedDict()
    false_reward = collections.Counter()
    gate_stats = collections.Counter()
    for rec in recs:
        key = f"{rec['folder']}/{rec['run']}"
        runs.setdefault(key, []).append(rec)
        resp_finding = False
        resp_contra = False
        for i, iid in enumerate(rec["ids"]):
            s, g, c = rec["skyrl"][i], rec["gate"][i], rec["repl"][i]
            pc = per_check[iid]
            pc["n"] += 1
            pc["skyrl_pass"] += s
            pc["repl_pass"] += c
            if g is not None:
                pc["gate_n"] += 1
                pc["gate_pass"] += g
                pc["gate_vs_skyrl_disagree"] += g != s
                if g != s:
                    pc["gate_vs_skyrl_repl_sides_with_" + ("gate" if c == g else "skyrl")] += 1
            if rec["skyrl_err"][i]:
                pc["skyrl_error"] += 1
            for grader, gv in (("skyrl", s), ("gate", g)):
                if gv is None or gv == c:
                    continue
                kind, ents = classify(rec, i, gv, grader)
                direction = "false_pass" if gv else "false_fail"
                pc[f"{grader}_{direction}"] += 1
                pc[f"{grader}_{direction}_{kind}"] += 1
                for e in ents:
                    decision_counts[grader][e] += 1
                if kind == "finding" and len(finding_examples[(grader, iid, direction)]) < 5:
                    finding_examples[(grader, iid, direction)].append(f"{key}:{rec['uuid']}")
                if grader == "skyrl" and gv and not c:
                    resp_contra = True
                    if kind in ("finding", "extraction"):
                        resp_finding = True
        for i, iid in enumerate(rec["ids"]):
            s, o = rec["skyrl"][i], rec["off_sk"][i]
            per_check[iid]["fo_skyrl_false_pass"] += s and not o
            per_check[iid]["fo_skyrl_false_fail"] += (not s) and o
            g, ov = rec["gate"][i], rec["off_vi"][i]
            if g is not None:
                per_check[iid]["fo_gate_false_pass"] += g and not ov
                per_check[iid]["fo_gate_false_fail"] += (not g) and ov
        if rec["skyrl_reward"] == 1.0:
            false_reward["skyrl_pass_fo"] += 1
            false_reward["fixes_only_contradicted"] += rec["off_sk_reward"] == 0.0
            false_reward[f"fixes_only_contradicted_{'heldout' if rec['heldout'] else 'dev'}"] += rec["off_sk_reward"] == 0.0
        offv = [v for v in rec["off_vi"] if v is not None]
        gate_stats["fo_false_gate_pass"] += rec["gate_pass"] and not all(offv)
        gate_stats["fo_false_gate_fail"] += (not rec["gate_pass"]) and all(offv)
        if rec["skyrl_reward"] == 1.0:
            false_reward["skyrl_pass"] += 1
            if rec["repl_reward"] == 0.0:
                false_reward["contradicted"] += 1
                if resp_finding:
                    false_reward["contradicted_by_finding_or_extraction"] += 1
            false_reward[f"pass_{'heldout' if rec['heldout'] else 'dev'}"] += 1
            if rec["repl_reward"] == 0.0:
                false_reward[f"contradicted_{'heldout' if rec['heldout'] else 'dev'}"] += 1
        # gate vs contract on deterministic constraints
        det = [(g, c) for g, c in zip(rec["gate"], rec["repl"]) if g is not None]
        c_gate = all(c for _, c in det)
        gate_stats["n"] += 1
        gate_stats["gate_pass"] += rec["gate_pass"]
        gate_stats["contract_gate_pass"] += c_gate
        gate_stats["false_gate_pass"] += rec["gate_pass"] and not c_gate
        gate_stats["false_gate_fail"] += (not rec["gate_pass"]) and c_gate

    run_rows = []
    for key, rs in runs.items():
        sk = [r["skyrl_reward"] for r in rs]
        cr = [r["repl_reward"] for r in rs]
        gp = [float(r["gate_pass"]) for r in rs]
        cg = [float(all(c for g, c in zip(r["gate"], r["repl"]) if g is not None)) for r in rs]
        d, lo, hi = boot_diff(sk, cr)
        dg, glo, ghi = boot_diff(gp, cg)
        ho = [r for r in rs if r["heldout"]]
        dh, hlo, hhi = boot_diff([r["skyrl_reward"] for r in ho], [r["repl_reward"] for r in ho])
        ext = collections.Counter(r["extraction"] for r in rs)
        fo = [r["off_sk_reward"] for r in rs]
        dfo = boot_diff(sk, fo)
        dfo_h = boot_diff([r["skyrl_reward"] for r in ho], [r["off_sk_reward"] for r in ho])
        gfo = [float(all(v for v in r["off_vi"] if v is not None)) for r in rs]
        dgfo = boot_diff(gp, gfo)
        run_rows.append({
            "fixes_only_score": float(np.mean(fo)), "skyrl_minus_fixes_only": list(dfo),
            "skyrl_minus_fixes_only_heldout": list(dfo_h),
            "gate_fixes_only_pass": float(np.mean(gfo)), "gate_minus_fixes_only": list(dgfo),
            "skyrl_vs_fixes_only_row_disagree": sum(a != b for a, b in zip(sk, fo)),
            "run": key, "n": len(rs), "truncated": sum(r["finish"] == "length" for r in rs),
            "extraction": dict(ext), "graded_empty": sum(r["graded_empty"] for r in rs),
            "skyrl_score": float(np.mean(sk)), "contract_score": float(np.mean(cr)),
            "skyrl_minus_contract": [d, lo, hi], "skyrl_minus_contract_heldout": [dh, hlo, hhi],
            "gate_pass": float(np.mean(gp)), "contract_gate_pass": float(np.mean(cg)),
            "gate_minus_contract": [dg, glo, ghi],
            "skyrl_error_responses": sum(any(e for e in r["skyrl_err"]) for r in rs),
            "skyrl_reward1_on_unclosed": sum(r["skyrl_reward"] == 1.0 for r in rs if r["extraction"] == "unclosed"),
            "gate_pass_on_unclosed": sum(r["gate_pass"] for r in rs if r["extraction"] == "unclosed"),
            "skyrl_reward1_on_marker": sum(r["skyrl_reward"] == 1.0 for r in rs if r["extraction"] == "marker_in_answer"),
            "skyrl_score_truncated": float(np.mean([r["skyrl_reward"] for r in rs if r["finish"] == "length"] or [0])),
        })

    # rerun: greedy vs greedy_repeat
    g1 = {r["uuid"]: r for r in runs["Qwen__Qwen3-4B-Instruct-2507/greedy"]}
    g2 = {r["uuid"]: r for r in runs["Qwen__Qwen3-4B-Instruct-2507/greedy_repeat"]}
    common = sorted(set(g1) & set(g2))
    same_text = sum(raw[("Qwen__Qwen3-4B-Instruct-2507", "greedy", u)] == raw[("Qwen__Qwen3-4B-Instruct-2507", "greedy_repeat", u)] for u in common)
    rerun = {
        "rows": len(common), "identical_responses": same_text,
        "skyrl_flips": sum(g1[u]["skyrl_reward"] != g2[u]["skyrl_reward"] for u in common),
        "contract_flips": sum(g1[u]["repl_reward"] != g2[u]["repl_reward"] for u in common),
        "skyrl_repeat_minus_greedy": boot_diff([g2[u]["skyrl_reward"] for u in common], [g1[u]["skyrl_reward"] for u in common]),
        "contract_repeat_minus_greedy": boot_diff([g2[u]["repl_reward"] for u in common], [g1[u]["repl_reward"] for u in common]),
    }

    # RNG dependence of impossible nth_paragraph constraints
    rng_resp = 0
    rng_vary = 0
    rng_ever_pass = 0
    for rec in recs:
        for i, iid in enumerate(rec["ids"]):
            kw = rec["kwargs"][i]
            if iid == "length_constraints:nth_paragraph_first_word" and kw["nth_paragraph"] > kw["num_paragraphs"]:
                rng_resp += 1
                text = harness.final_answer_text(raw[(rec["folder"], rec["run"], rec["uuid"])])
                vs = set()
                for seed in range(20):
                    random.seed(seed)
                    vs.add(harness.skyrl_check(iid, kw, text))
                rng_vary += len(vs) > 1
                rng_ever_pass += True in vs

    summary = {
        "runs": run_rows, "per_check": {k: dict(v) for k, v in sorted(per_check.items())},
        "decision_counts": {g: dict(c.most_common()) for g, c in decision_counts.items()},
        "false_reward": dict(false_reward), "gate": dict(gate_stats), "rerun": rerun,
        "nth_rng": {"responses": rng_resp, "verdict_varies_over_20_seeds": rng_vary, "passes_for_some_seed": rng_ever_pass},
        "finding_examples": {f"{g}|{i}|{d}": v for (g, i, d), v in finding_examples.items()},
    }
    (W / "audit" / "out" / "panel_summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")

    print("== runs")
    for r in run_rows:
        print(json.dumps(r))
    print("== false rewards", dict(false_reward))
    print("== gate", dict(gate_stats))
    print("== rerun", rerun)
    print("== nth rng", summary["nth_rng"])
    print("== per check (skyrl false_pass/false_fail by class; gate likewise)")
    for iid, c in sorted(per_check.items()):
        print(f"{iid}: n={c['n']} skyrl={c['skyrl_pass']} repl={c['repl_pass']} gate={c.get('gate_pass','-')}/{c.get('gate_n','-')}"
              f" | SK FP f={c['skyrl_false_pass_finding']} d={c['skyrl_false_pass_decision']} x={c['skyrl_false_pass_extraction']}"
              f" FF f={c['skyrl_false_fail_finding']} d={c['skyrl_false_fail_decision']} x={c['skyrl_false_fail_extraction']}"
              f" | GT FP f={c['gate_false_pass_finding']} d={c['gate_false_pass_decision']} x={c['gate_false_pass_extraction']}"
              f" FF f={c['gate_false_fail_finding']} d={c['gate_false_fail_decision']} x={c['gate_false_fail_extraction']}"
              f" | err={c['skyrl_error']}"
              f" | FIXES-ONLY SK FP={c['fo_skyrl_false_pass']} FF={c['fo_skyrl_false_fail']}"
              f" GT FP={c['fo_gate_false_pass']} FF={c['fo_gate_false_fail']}")
    print("== decision counts", json.dumps(summary["decision_counts"]))


if __name__ == "__main__":
    main()
