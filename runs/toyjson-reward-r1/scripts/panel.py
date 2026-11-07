"""Step 5: grade the stored rollouts (the panel) with every grader.

    python -I -B audit/scripts/panel.py

Graders: case/reward.py (the grader under audit), the replacement with the official readings
("fixes only": every difference from the grader is a defect fix), and the replacement with
the proposed readings. Checks the case-file pins before and after. Writes
audit/runs/panel_verdicts.jsonl (one row per rollout) and audit/runs/panel_summary.json, and
prints the summary tables as Markdown.
"""
import collections
import json
import pathlib
import random
import subprocess
import sys
from decimal import Decimal

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "audit" / "scripts"))

import patched_grader as P  # noqa: E402

G, R = P.G, P.R
BOOT = 10000
SEED = 20261107
CHECKS = ("customer", "date", "items", "total")


def pins_ok(when):
    res = subprocess.run([sys.executable, "-I", "-B", str(ROOT / "audit" / "scripts" / "pin_inputs.py"), "--check"],
                         capture_output=True, text=True)
    print("pin check %s: %s" % (when, res.stdout.strip()))
    if res.returncode:
        raise SystemExit("pin check failed")


def grader_checks(response, ref):
    """The grader's own per-check verdicts, from its own functions."""
    try:
        answer = G.parse_answer(response)
    except Exception as exc:
        return {"gate": "raises " + type(exc).__name__}
    if answer is None:
        return {"gate": False, "customer": 0.0, "date": 0.0, "items": 0.0, "total": 0.0, "extra_keys": 0}
    if not isinstance(answer, dict):
        return {"gate": "raises AttributeError (top-level %s)" % type(answer).__name__}
    out = {"gate": True}
    for name, fn in (("customer", G.customer_score), ("date", G.date_score), ("items", G.items_score), ("total", G.total_score)):
        try:
            out[name] = fn(answer.get(name), ref[name])
        except Exception as exc:
            out[name] = "raises " + type(exc).__name__
    out["extra_keys"] = sum(1 for k in answer if k not in G.FIELDS)
    return out


def features(text):
    s = text.strip()
    return {
        "fenced": s.startswith("```"),
        "ends_with_brace_or_fence": s.endswith("}") or s.endswith("```"),
        "has_cr": "\r" in text,
        "has_think": "<think>" in text or "</think>" in text,
        "chars": len(text),
    }


def boot_ci(diffs, rng):
    n = len(diffs)
    means = sorted(sum(diffs[rng.randrange(n)] for _ in range(n)) / n for _ in range(BOOT))
    return means[int(0.025 * BOOT)], means[int(0.975 * BOOT) - 1]


def boot_ci_strata(groups, rng):
    """Mean over all rows, resampling within each group (checkpoint)."""
    total = sum(len(g) for g in groups)
    means = []
    for _ in range(BOOT):
        s = 0.0
        for g in groups:
            s += sum(g[rng.randrange(len(g))] for _ in range(len(g)))
        means.append(s / total)
    means.sort()
    return means[int(0.025 * BOOT)], means[int(0.975 * BOOT) - 1]


def main():
    pins_ok("before")
    refs = {}
    for line in open(ROOT / "case" / "orders.jsonl", encoding="utf-8"):
        if line.strip():
            o = json.loads(line, parse_float=Decimal)
            refs[o["order_id"]] = o["reference"]
    rows = [json.loads(l) for l in open(ROOT / "case" / "responses.jsonl", encoding="utf-8") if l.strip()]
    heldout = set(json.load(open(ROOT / "audit" / "frozen" / "heldout_split.json"))["heldout"])

    out = []
    for r in rows:
        ref = refs[r["order_id"]]
        g = P.outcome(G.reward, r["response"], ref)
        nofix = P.outcome(P.reward, r["response"], ref)
        allfix = P.outcome(P.reward, r["response"], ref, fixes=P.ALL_FIXES)
        off = R.score(r["response"], ref, **R.OFFICIAL)
        prop = R.score(r["response"], ref)
        if not P.same(g, nofix) or not P.same(allfix, ("ok", off["reward"])):
            raise SystemExit("harness mismatch on %s" % r["id"])
        out.append({
            "id": r["id"], "checkpoint": r["checkpoint"], "order_id": r["order_id"], "heldout": r["id"] in heldout,
            "grader": g[1] if g[0] == "ok" else "raises " + g[1],
            "fixes_only": off["reward"], "proposed": prop["reward"],
            "grader_checks": grader_checks(r["response"], ref),
            "fixes_only_checks": {k: off[k] for k in ("gate",) + CHECKS + ("extra_keys",)},
            "proposed_checks": {k: prop[k] for k in ("gate",) + CHECKS + ("extra_keys",)},
            "findings": P.attribute(r["response"], ref),
            "decisions": [d for d, sw in (("D-fence-newline", "fence_newline"), ("D-inner-whitespace", "inner_whitespace"),
                                          ("D-qty-bool", "qty_bool"), ("D-qty-integral", "qty_integral"),
                                          ("D-total-boundary", "total_boundary"))
                          if abs(R.reward(r["response"], ref, **dict(R.OFFICIAL, **{sw: R.PROPOSED[sw]})) - off["reward"]) > 1e-9],
            "features": features(r["response"]),
        })
    with open(ROOT / "audit" / "runs" / "panel_verdicts.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for row in out:
            f.write(json.dumps(row) + "\n")

    rng = random.Random(SEED)
    ckpts = sorted({r["checkpoint"] for r in out})
    summary = {"rollouts": len(out), "bootstrap_resamples": BOOT, "bootstrap_seed": SEED, "per_checkpoint": {}, "overall": {}}
    by = collections.defaultdict(list)
    for row in out:
        by[row["checkpoint"]].append(row)

    def num(v):
        return v if isinstance(v, float) else None

    print("\n| Checkpoint | Rollouts | Scored | Grader mean | Fixes-only mean | Proposed mean | Fixes-only minus grader [95% CI] | Proposed minus grader [95% CI] | Full: grader / fixes-only / proposed |")
    print("|---|---|---|---|---|---|---|---|---|")
    diff_groups_off, diff_groups_prop = [], []
    for c in ckpts:
        rs = by[c]
        scored = [x for x in rs if num(x["grader"]) is not None]
        gm = sum(x["grader"] for x in scored) / len(scored)
        om = sum(x["fixes_only"] for x in rs) / len(rs)
        pm = sum(x["proposed"] for x in rs) / len(rs)
        d_off = [x["fixes_only"] - x["grader"] for x in scored]
        d_prop = [x["proposed"] - x["grader"] for x in scored]
        diff_groups_off.append(d_off)
        diff_groups_prop.append(d_prop)
        ci_off, ci_prop = boot_ci(d_off, rng), boot_ci(d_prop, rng)
        full = (sum(x["grader"] == 1.0 for x in scored), sum(x["fixes_only"] == 1.0 for x in rs), sum(x["proposed"] == 1.0 for x in rs))
        summary["per_checkpoint"][c] = {"rollouts": len(rs), "scored": len(scored), "grader_mean": gm, "fixes_only_mean": om,
                                        "proposed_mean": pm, "fixes_only_minus_grader": om - gm, "ci_fixes_only": ci_off,
                                        "proposed_minus_grader": pm - gm, "ci_proposed": ci_prop, "full": full,
                                        "disagree_fixes_only": sum(abs(x["fixes_only"] - x["grader"]) > 1e-9 for x in scored),
                                        "disagree_proposed": sum(abs(x["proposed"] - x["grader"]) > 1e-9 for x in scored)}
        print("| %s | %d | %d | %.3f | %.3f | %.3f | %+.3f [%+.3f, %+.3f] | %+.3f [%+.3f, %+.3f] | %d / %d / %d |" % (
            c, len(rs), len(scored), gm, om, pm, om - gm, ci_off[0], ci_off[1], pm - gm, ci_prop[0], ci_prop[1], *full))

    allg = [x["grader"] for x in out if num(x["grader"]) is not None]
    ov = summary["overall"]
    ov["scored_coverage"] = "%d/%d" % (len(allg), len(out))
    ov["grader_mean"] = sum(allg) / len(allg)
    ov["fixes_only_mean"] = sum(x["fixes_only"] for x in out) / len(out)
    ov["proposed_mean"] = sum(x["proposed"] for x in out) / len(out)
    ov["ci_fixes_only_minus_grader"] = boot_ci_strata(diff_groups_off, rng)
    ov["ci_proposed_minus_grader"] = boot_ci_strata(diff_groups_prop, rng)
    g_full = [x for x in out if x["grader"] == 1.0]
    ov["grader_full_rewards"] = len(g_full)
    ov["false_full_vs_fixes_only"] = sorted(x["id"] for x in g_full if x["fixes_only"] < 1.0)
    ov["false_full_vs_proposed"] = sorted(x["id"] for x in g_full if x["proposed"] < 1.0)
    ov["disagree_fixes_only"] = sorted(x["id"] for x in out if abs(x["fixes_only"] - x["grader"]) > 1e-9)
    ov["disagree_proposed"] = sorted(x["id"] for x in out if abs(x["proposed"] - x["grader"]) > 1e-9)
    excess = sum(max(0.0, x["grader"] - x["fixes_only"]) for x in out)
    ov["excess_reward_share_vs_fixes_only"] = excess / sum(allg)
    ov["rollouts_per_finding"] = dict(collections.Counter(k for x in out for k in x["findings"]))
    ov["rollouts_per_decision"] = dict(collections.Counter(k for x in out for k in x["decisions"]))
    ov["features"] = {k: sum(1 for x in out if x["features"][k]) for k in ("fenced", "ends_with_brace_or_fence", "has_cr", "has_think")}
    ov["max_chars"] = max(x["features"]["chars"] for x in out)

    print("\nPer-check pass rates over all 48 rollouts (items and extra_keys: means)")
    print("| Check | Grader | Fixes-only | Proposed |")
    print("|---|---|---|---|")
    rates = {}
    for k in ("gate",) + CHECKS + ("extra_keys",):
        vals = []
        for key in ("grader_checks", "fixes_only_checks", "proposed_checks"):
            v = [x[key][k] for x in out]
            vals.append(sum(float(t) for t in v) / len(v))
        rates[k] = vals
        print("| %s | %.3f | %.3f | %.3f |" % (k, *vals))
    ov["per_check"] = rates
    (ROOT / "audit" / "runs" / "panel_summary.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("\n" + json.dumps(ov, indent=1))
    print("\nDisagreements (grader vs fixes-only or proposed):")
    for x in out:
        if abs(x["fixes_only"] - x["grader"]) > 1e-9 or abs(x["proposed"] - x["grader"]) > 1e-9:
            print("  %s %s %s held_out=%s grader=%s fixes_only=%.4f proposed=%.4f findings=%s decisions=%s" % (
                x["id"], x["checkpoint"], x["order_id"], x["heldout"], x["grader"], x["fixes_only"], x["proposed"],
                x["findings"], x["decisions"]))
    pins_ok("after")


if __name__ == "__main__":
    main()
