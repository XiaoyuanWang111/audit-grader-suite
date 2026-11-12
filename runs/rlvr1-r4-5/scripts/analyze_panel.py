"""Step 5 analysis of audit/out/panel_A.jsonl + panel_B.jsonl. Writes audit/out/panel_summary.json."""
import collections
import hashlib
import json
import sys

import numpy as np

A = "<W>/audit"
W = "<W>"
RNG = np.random.default_rng(20261112)


def held_out(uuid):
    return int(hashlib.sha256(uuid.encode()).hexdigest(), 16) % 10 < 3


def load():
    rows = []
    for p in ("panel_A.jsonl", "panel_B.jsonl"):
        for line in open(f"{A}/out/{p}", encoding="utf-8"):
            rows.append(json.loads(line))
    return rows


def boot_diff(a, b, n=2000):
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    d = b - a
    idx = RNG.integers(0, len(d), size=(n, len(d)))
    m = d[idx].mean(axis=1)
    return float(d.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def row_rewards(r):
    nv = float(r["nv_outcome"] == "graded" and all(r["nv"]))
    vs = float(r["vs_status"] == "scored" and r["vs"] is not None and all(r["vs"]))
    vg = float(all(v for v in r["vg"] if v is not None))
    rr = float(all(r["r"]))
    rf = float(all(r["rf"]))
    return nv, vs, vg, rr, rf


def main():
    rows = load()
    data = {}
    for line in open(f"{W}/case/data/rlvr1_instruction_following.jsonl", encoding="utf-8"):
        row = json.loads(line)
        rec = json.loads(row["extra_info"]["nemotron_ultra"]["record_json"])
        data[rec["uuid"]] = (rec, row["prompt"][0]["content"])
    summary = {"runs": {}, "checks": {}, "decisions": {}}
    by_file = collections.defaultdict(list)
    for r in rows:
        by_file[r["file"]].append(r)

    for subset in ("all", "heldout"):
        for f, rs in sorted(by_file.items()):
            if subset == "heldout":
                rs = [r for r in rs if held_out(r["uuid"])]
            rw = np.array([row_rewards(r) for r in rs])
            nv, vs, vg, rr, rf = rw.T
            s = {
                "n": len(rs),
                "finish_length": sum(r["finish_reason"] == "length" for r in rs),
                "nv_score": nv.mean(), "vs_score": vs.mean(), "vg_gate_pass": vg.mean(),
                "r_score": rr.mean(), "rf_score": rf.mean(),
                "r_minus_nv": boot_diff(nv, rr), "rf_minus_nv": boot_diff(nv, rf), "vs_minus_nv": boot_diff(nv, vs),
                "nv_infra_rows": sum(r["nv_outcome"] != "graded" for r in rs),
                "vs_unscored_rows": sum(r["vs_status"] != "scored" for r in rs),
                "nv_action_empty": sum(r["nv_action_empty"] for r in rs),
                "r_extraction_failure": sum(r["r_extraction_failure"] for r in rs),
                "nv_reward1_on_extraction_failure": int(sum(1 for r, x in zip(rs, nv) if r["r_extraction_failure"] and x == 1)),
                "nv_false_reward_rows": int(((nv == 1) & (rr == 0)).sum()),
                "nv_false_reward_rows_fixes_only": int(((nv == 1) & (rf == 0)).sum()),
                "nv_reward1_rows": int((nv == 1).sum()),
                "vs_false_reward_rows": int(((vs == 1) & (rr == 0)).sum()),
                "vs_reward1_rows": int((vs == 1).sum()),
                "vg_false_gate_pass": int(sum(1 for r, x in zip(rs, vg) if x == 1 and not all(
                    rv for rv, gv in zip(r["r"], r["vg"]) if gv is not None))),
                "vg_gate_pass_rows": int((vg == 1).sum()),
                "vg_false_gate_reject": int(sum(1 for r, x in zip(rs, vg) if x == 0 and all(
                    rv for rv, gv in zip(r["r"], r["vg"]) if gv is not None))),
                "vg_gate_reject_rows": int((vg == 0).sum()),
                "length_nv_reward1": int(sum(1 for r, x in zip(rs, nv) if r["finish_reason"] == "length" and x == 1)),
            }
            summary["runs"].setdefault(subset, {})[f] = s

    # rerun: greedy vs greedy_repeat
    g1 = {r["uuid"]: row_rewards(r) for r in by_file["Qwen__Qwen3-4B-Instruct-2507/greedy.jsonl"]}
    g2 = {r["uuid"]: row_rewards(r) for r in by_file["Qwen__Qwen3-4B-Instruct-2507/greedy_repeat.jsonl"]}
    common = sorted(set(g1) & set(g2))
    rerun = {}
    for k, name in enumerate(["nv", "vs", "vg", "r", "rf"]):
        a = [g1[u][k] for u in common]
        b = [g2[u][k] for u in common]
        rerun[name] = {"changed_rows": int(sum(x != y for x, y in zip(a, b))), "diff": boot_diff(a, b)}
    same_text = 0
    t1 = {}
    for line in open(f"{W}/case/panel/Qwen__Qwen3-4B-Instruct-2507/greedy.jsonl", encoding="utf-8"):
        d = json.loads(line)
        t1[d["uuid"]] = d["raw_response"]
    for line in open(f"{W}/case/panel/Qwen__Qwen3-4B-Instruct-2507/greedy_repeat.jsonl", encoding="utf-8"):
        d = json.loads(line)
        same_text += t1.get(d["uuid"]) == d["raw_response"]
    rerun["identical_responses"] = same_text
    rerun["rows"] = len(common)
    summary["rerun"] = rerun

    # per check
    per = collections.defaultdict(collections.Counter)
    dec = collections.defaultdict(collections.Counter)
    examples = collections.defaultdict(list)
    for r in rows:
        rec, prompt = data[r["uuid"]]
        for j, iid in enumerate(r["ids"]):
            c = per[iid]
            nv = bool(r["nv"][j]) and not r["nv_err"][j]
            c["n"] += 1
            c["nv"] += nv
            c["nv_err"] += bool(r["nv_err"][j])
            if r["vs"] is not None:
                c["vs_n"] += 1
                c["vs"] += bool(r["vs"][j])
            if r["vg"][j] is not None:
                c["vg_n"] += 1
                c["vg"] += bool(r["vg"][j])
                c["vg_ne_r"] += bool(r["vg"][j]) != r["r"][j]
                c["vg_pass_r_fail"] += bool(r["vg"][j]) and not r["r"][j]
                c["vg_fail_r_pass"] += (not r["vg"][j]) and r["r"][j]
                c["vg_ne_nv"] += bool(r["vg"][j]) != nv
            c["r"] += r["r"][j]
            c["rf"] += r["rf"][j]
            if nv != r["r"][j]:
                c["nv_ne_r"] += 1
                c["nv_pass_r_fail"] += nv and not r["r"][j]
                c["nv_fail_r_pass"] += (not nv) and r["r"][j]
                if r["rf"][j] == nv:
                    c["nv_ne_r_decision"] += 1
                    flips = r["flips"].get(str(j), {})
                    hit = [d for d, v in flips.items() if v == nv]
                    for d in hit:
                        dec[d][iid] += 1
                    if not hit:
                        dec["(several entries together)"][iid] += 1
                else:
                    c["nv_ne_r_defect"] += 1
                    if len(examples[iid]) < 3 and held_out(r["uuid"]) is False:
                        examples[iid].append({"file": r["file"], "uuid": r["uuid"], "nv": nv, "r": r["r"][j]})
            if r["rf"][j] != nv:
                c["nv_ne_rf"] += 1
            if iid == "length_constraints:nth_paragraph_first_word":
                kw = rec["kwargs"][j]
                if kw["nth_paragraph"] > kw["num_paragraphs"]:
                    c["unsat_n"] += 1
                    c["unsat_nv_pass"] += nv
                    c["unsat_vs_pass"] += bool(r["vs"][j]) if r["vs"] is not None else 0
            if iid == "detectable_content:postscript":
                kw = rec["kwargs"][j]
                shown_no_dot = kw["postscript_marker"] == "P.S." and ("postscript starting with P.S." not in prompt)
                if shown_no_dot:
                    c["ps_nodot_n"] += 1
                    c["ps_nodot_nv_fail_r_pass"] += (not nv) and r["r"][j]
            if iid == "keywords:word_count_different_numbers":
                kw = rec["kwargs"][j]
                c["wcdn_" + kw["relation"].replace(" ", "_") + "_n"] += 1
                c["wcdn_" + kw["relation"].replace(" ", "_") + "_nv_ne_r"] += nv != r["r"][j]
    summary["checks"] = {k: dict(v) for k, v in sorted(per.items())}
    summary["decisions"] = {k: dict(v) for k, v in sorted(dec.items(), key=lambda kv: -sum(kv[1].values()))}
    summary["defect_examples"] = examples
    tot = collections.Counter()
    for v in per.values():
        tot.update(v)
    summary["totals"] = dict(tot)
    json.dump(summary, open(f"{A}/out/panel_summary.json", "w", encoding="utf-8"), indent=1, default=float)

    # print
    for subset in ("all", "heldout"):
        print(f"\n=== runs ({subset})")
        print(f"{'file':55s} {'n':>6s} {'NV':>6s} {'VS':>6s} {'R':>6s} {'RF':>6s} {'R-NV [95%]':>24s} {'RF-NV':>8s} gate  falseNV/NV1  len")
        for f, s in summary["runs"][subset].items():
            d = s["r_minus_nv"]
            print(f"{f:55s} {s['n']:6d} {100*s['nv_score']:6.1f} {100*s['vs_score']:6.1f} {100*s['r_score']:6.1f} {100*s['rf_score']:6.1f} "
                  f"{100*d[0]:+6.1f} [{100*d[1]:+5.1f},{100*d[2]:+5.1f}] {100*s['rf_minus_nv'][0]:+7.1f} {100*s['vg_gate_pass']:5.1f} "
                  f"{s['nv_false_reward_rows']}/{s['nv_reward1_rows']} ({s['nv_false_reward_rows_fixes_only']} fixes-only) {s['finish_length']} "
                  f"infraNV={s['nv_infra_rows']} unscoredVS={s['vs_unscored_rows']} emptyNV={s['nv_action_empty']} extrfail={s['r_extraction_failure']} nv1_on_extrfail={s['nv_reward1_on_extraction_failure']}")
    print("\nrerun", json.dumps(rerun))
    print("\n=== per check: n, NV%, VS%, VG%, R%, RF%, NV!=R (defect/decision), VG!=R, VG pass&R fail, VG fail&R pass")
    for k, c in summary["checks"].items():
        vgp = 100 * c.get("vg", 0) / c["vg_n"] if c.get("vg_n") else float("nan")
        vsp = 100 * c.get("vs", 0) / c["vs_n"] if c.get("vs_n") else float("nan")
        print(f"{k:46s} {c['n']:5d} {100*c['nv']/c['n']:5.1f} {vsp:5.1f} {vgp:5.1f} {100*c['r']/c['n']:5.1f} {100*c['rf']/c['n']:5.1f} "
              f"{c.get('nv_ne_r',0):5d} ({c.get('nv_ne_r_defect',0)}/{c.get('nv_ne_r_decision',0)}) {c.get('vg_ne_r',0):5d} {c.get('vg_pass_r_fail',0):5d} {c.get('vg_fail_r_pass',0):5d}"
              + (f" unsat n={c['unsat_n']} nv_pass={c['unsat_nv_pass']} vs_pass={c['unsat_vs_pass']}" if c.get("unsat_n") else "")
              + (f" ps_nodot n={c['ps_nodot_n']} nvfail_rpass={c['ps_nodot_nv_fail_r_pass']}" if c.get("ps_nodot_n") else "")
              + (f" err={c['nv_err']}" if c.get("nv_err") else ""))
    print("\n=== decisions behind NV!=R (NV matches the decision's other reading)")
    for d, v in summary["decisions"].items():
        print(f"{d:28s} {sum(v.values()):6d} {dict(v)}")
    # extra: VS unscored reasons, empty SkyRL actions, totals of false rewards
    vs_reasons = collections.Counter()
    empty_nv1 = 0
    empty_rows = 0
    for r in rows:
        if r["vs_status"] != "scored":
            det = r.get("vs_detail") or {}
            errs = det.get("instruction_errors") or [det.get("error_type")] if isinstance(det, dict) else [str(det)[:60]]
            for e in errs or []:
                if e:
                    vs_reasons[str(e)[:70]] += 1
        if r["nv_action_empty"]:
            empty_rows += 1
            empty_nv1 += r["nv_outcome"] == "graded" and all(r["nv"])
    agg = collections.Counter()
    for f, s in summary["runs"]["all"].items():
        for k in ("nv_false_reward_rows", "nv_false_reward_rows_fixes_only", "nv_reward1_rows", "vs_false_reward_rows",
                  "vs_reward1_rows", "vg_false_gate_pass", "vg_gate_pass_rows", "vg_false_gate_reject", "vg_gate_reject_rows", "n"):
            agg[k] += s[k]
    summary["extra"] = {"vs_unscored_reasons": dict(vs_reasons), "empty_action_rows": empty_rows,
                        "empty_action_nv_reward1": empty_nv1, "aggregate": dict(agg)}
    json.dump(summary, open(f"{A}/out/panel_summary.json", "w", encoding="utf-8"), indent=1, default=float)
    print("\nextra", json.dumps(summary["extra"], indent=0))
    t = summary["totals"]
    print("\ntotals", {k: t[k] for k in ("n", "nv", "r", "rf", "nv_ne_r", "nv_ne_r_defect", "nv_ne_r_decision", "vg_n", "vg_ne_r", "vg_pass_r_fail", "vg_fail_r_pass", "nv_pass_r_fail", "nv_fail_r_pass")})


if __name__ == "__main__":
    main()
