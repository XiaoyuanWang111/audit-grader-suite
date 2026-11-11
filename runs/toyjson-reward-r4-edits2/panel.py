"""Step 5: grade the 48 stored rollouts with case/reward.py and the replacement (fixes_only and proposed modes).

    python -B audit/panel.py           # print the summary
    python -B audit/panel.py --write   # also write audit/panel/verdicts.jsonl and audit/panel/summary.json

No responses are generated (no compute in this exercise): the stored rollouts are the panel.
"""

import json
import os
import random
import sys
from collections import defaultdict
from decimal import Decimal

sys.dont_write_bytecode = True
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (os.path.join(W, "case"), os.path.join(W, "audit")):
    if p not in sys.path:
        sys.path.insert(0, p)

import classify  # noqa: E402
import replacement_reward as rr  # noqa: E402
import reward as grader  # noqa: E402

BOOT_SEED = 20261111
BOOT_N = 10000
DECISION_SWITCH = {"D-whitespace": "whitespace", "D-fence-tab": "fence_tab", "D-crlf": "crlf",
                   "D-json-constants": "json_constants", "D-qty-decimal": "qty_decimal", "D-qty-bool": "qty_bool",
                   "D-total-boundary": "total_inclusive"}


def load(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l, parse_float=Decimal) for l in f if l.strip()]


def grader_breakdown(resp, ref):
    """The grader's own per-check scores, from its functions."""
    try:
        ans = grader.parse_answer(resp)
        if not isinstance(ans, dict):
            return {"answer": 0, "customer": 0, "date": 0, "items": 0.0, "total": 0, "extra_keys": 0}
        return {"answer": 1,
                "customer": int(grader.customer_score(ans.get("customer"), ref["customer"])),
                "date": int(grader.date_score(ans.get("date"), ref["date"])),
                "items": grader.items_score(ans.get("items"), ref["items"]),
                "total": int(grader.total_score(ans.get("total"), ref["total"])),
                "extra_keys": sum(1 for k in ans if k not in grader.FIELDS)}
    except BaseException as e:  # noqa: BLE001
        return {"error": type(e).__name__}


def safe(fn, *a, **k):
    try:
        return fn(*a, **k)
    except BaseException as e:  # noqa: BLE001
        return type(e).__name__


def decisions_involved(resp, ref):
    """Decision entries whose switch alone moves fixes_only to a different reward."""
    base = rr.reward(resp, ref, **rr.FIXES_ONLY)
    out = []
    for d, sw in DECISION_SWITCH.items():
        if rr.FIXES_ONLY[sw] != rr.PROPOSED[sw]:
            v = rr.reward(resp, ref, **{**rr.FIXES_ONLY, sw: rr.PROPOSED[sw]})
            if abs(v - base) > 1e-9:
                out.append(d)
    return out


def boot_ci(diffs, rng):
    n = len(diffs)
    means = sorted(sum(diffs[rng.randrange(n)] for _ in range(n)) / n for _ in range(BOOT_N))
    return means[int(0.025 * BOOT_N)], means[int(0.975 * BOOT_N) - 1]


def main():
    refs = {o["order_id"]: o["reference"] for o in load(os.path.join(W, "case", "orders.jsonl"))}
    rows = load(os.path.join(W, "case", "responses.jsonl"))
    out = []
    for r in rows:
        ref = refs[r["order_id"]]
        resp = r["response"]
        g = safe(grader.reward, resp, ref)
        g2 = safe(grader.reward, resp, ref)
        fx = rr.reward(resp, ref, **rr.FIXES_ONLY)
        pr = rr.reward(resp, ref, **rr.PROPOSED)
        out.append({
            "id": r["id"], "checkpoint": r["checkpoint"], "order_id": r["order_id"],
            "grader": g, "grader_rerun_identical": g == g2, "fixes_only": fx, "proposed": pr,
            "findings": list(classify.explain(resp, ref) or ["UNEXPLAINED"]) if g != fx else [],
            "decisions": decisions_involved(resp, ref) if abs(fx - pr) > 1e-9 else [],
            "grader_checks": grader_breakdown(resp, ref),
            "proposed_checks": rr.breakdown(resp, ref, "proposed"),
            "record": {"fenced": resp.strip().startswith("```"),
                       "ends_with_brace_or_fence": resp.strip().endswith(("}", "```")),
                       "think_marker": "<think>" in resp or "</think>" in resp,
                       "chars": len(resp)},
        })

    by_ck = defaultdict(list)
    for o in out:
        by_ck[o["checkpoint"]].append(o)
    rng = random.Random(BOOT_SEED)
    summary = {"checkpoints": {}, "overall": {}}

    def stats(group):
        n = len(group)
        g_ok = [o for o in group if isinstance(o["grader"], float)]
        res = {"rollouts": n, "scored_coverage_grader": len(g_ok) / n, "scored_coverage_replacement": 1.0}
        for k in ("grader", "fixes_only", "proposed"):
            vals = [o[k] for o in group if isinstance(o[k], float)]
            res[f"mean_{k}"] = sum(vals) / len(vals)
            res[f"full_{k}"] = sum(v == 1.0 for v in vals)
        for k in ("fixes_only", "proposed"):
            diffs = [o["grader"] - o[k] for o in g_ok]
            lo, hi = boot_ci(diffs, rng)
            res[f"grader_minus_{k}"] = {"mean": sum(diffs) / len(diffs), "ci95": [lo, hi],
                                        "rollouts_differing": sum(abs(d) > 1e-9 for d in diffs)}
        checks = {}
        for name in ("answer", "customer", "date", "items", "total"):
            gv = [o["grader_checks"].get(name) for o in group]
            pv = [o["proposed_checks"][name] for o in group]
            full = (lambda v: v == 1 or v == 1.0 or v == "1")
            checks[name] = {"grader_full": sum(full(v) for v in gv), "proposed_full": sum(full(v) for v in pv)}
        checks["no_extra_keys"] = {"grader_full": sum(o["grader_checks"].get("extra_keys") == 0 for o in group),
                                   "proposed_full": sum(o["proposed_checks"]["extra_keys"] == 0 for o in group)}
        res["checks_full_count"] = checks
        return res

    for ck in sorted(by_ck):
        summary["checkpoints"][ck] = stats(by_ck[ck])
    summary["overall"] = stats(out)

    def false_rewards(k):
        over = [o for o in out if isinstance(o["grader"], float) and o["grader"] > o[k] + 1e-9]
        full = [o for o in out if o["grader"] == 1.0]
        return {"rollouts_rewarded_above_contract": len(over), "ids": [o["id"] for o in over],
                "excess_reward_total": round(sum(o["grader"] - o[k] for o in over), 4),
                "grader_full_rewards": len(full),
                "grader_full_rewards_not_full_under_contract": sum(o[k] < 1.0 for o in full),
                "share_of_grader_reward_mass_contradicted": round(
                    sum(o["grader"] - o[k] for o in over) / sum(o["grader"] for o in out if isinstance(o["grader"], float)), 4),
                "rollouts_rewarded_below_contract": [o["id"] for o in out
                                                     if isinstance(o["grader"], float) and o["grader"] < o[k] - 1e-9]}
    summary["false_rewards_vs_fixes_only"] = false_rewards("fixes_only")
    summary["false_rewards_vs_proposed"] = false_rewards("proposed")
    attrib = defaultdict(list)
    for o in out:
        for f in o["findings"]:
            attrib[f].append(o["id"])
        for d in o["decisions"]:
            attrib[d].append(o["id"])
    summary["attribution"] = dict(attrib)
    summary["records"] = {"fenced": sum(o["record"]["fenced"] for o in out),
                          "ends_with_brace_or_fence": sum(o["record"]["ends_with_brace_or_fence"] for o in out),
                          "think_marker": sum(o["record"]["think_marker"] for o in out),
                          "grader_rerun_identical": sum(o["grader_rerun_identical"] for o in out),
                          "max_chars": max(o["record"]["chars"] for o in out)}

    print(f"{'checkpoint':<12}{'n':>3}{'grader':>8}{'fixes':>8}{'prop':>8}{'full g/f/p':>12}  "
          f"{'grader-fixes [95% CI]':<26}{'grader-proposed [95% CI]':<26}")
    for ck, s in list(summary["checkpoints"].items()) + [("all", summary["overall"])]:
        a, b = s["grader_minus_fixes_only"], s["grader_minus_proposed"]
        print(f"{ck:<12}{s['rollouts']:>3}{s['mean_grader']:>8.3f}{s['mean_fixes_only']:>8.3f}{s['mean_proposed']:>8.3f}"
              f"{s['full_grader']:>5}/{s['full_fixes_only']}/{s['full_proposed']:<4}  "
              f"{a['mean']:+.3f} [{a['ci95'][0]:+.3f}, {a['ci95'][1]:+.3f}]{'':<5}"
              f"{b['mean']:+.3f} [{b['ci95'][0]:+.3f}, {b['ci95'][1]:+.3f}]")
    print("\nchecks at full score, grader / proposed (overall):",
          {k: f"{v['grader_full']}/{v['proposed_full']}" for k, v in summary["overall"]["checks_full_count"].items()})
    print("false rewards vs fixes_only:", json.dumps(summary["false_rewards_vs_fixes_only"]))
    print("false rewards vs proposed:  ", json.dumps(summary["false_rewards_vs_proposed"]))
    print("attribution:", json.dumps(summary["attribution"]))
    print("records:", summary["records"])
    if "--write" in sys.argv:
        os.makedirs(os.path.join(W, "audit", "panel"), exist_ok=True)
        with open(os.path.join(W, "audit", "panel", "verdicts.jsonl"), "w", encoding="utf-8", newline="\n") as f:
            for o in out:
                f.write(json.dumps(o, default=str) + "\n")
        with open(os.path.join(W, "audit", "panel", "summary.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(summary, f, indent=1, default=str)
            f.write("\n")


if __name__ == "__main__":
    main()
