"""Step 5: grade the stored panel (case/responses.jsonl) with the recorded judge replies.

Usage (from W):  python -B audit/scripts/panel.py
Writes audit/panel/labels.jsonl and audit/panel/summary.json, prints the tables.

Graders: G = case/judge_pipeline.py (under audit), R = case/reference/pipeline_ref.py, X = the replacement with the
proposed readings, X_full = the replacement with D-judge-window reading (b). A prompt that the stored run did not
send has no recorded reply; it is reported as `no_reply` (a coverage gap of this offline run, not a judge error).
"""
import hashlib
import json
import sys
from collections import Counter

sys.path.insert(0, __import__("os").path.dirname(__file__))
from common import (AUDIT, CASE, grader, judges, questions, reference_grade, replacement,  # noqa: E402
                    responses, template)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def run(fn):
    try:
        return fn()
    except LookupError:
        return "no_reply"
    except Exception as e:  # noqa: BLE001
        return "exception:" + type(e).__name__


def main():
    for name in ("judge_pipeline.py", "judges.py", "judge_replies.jsonl", "judge_template.txt", "questions.jsonl",
                 "responses.jsonl", "reference/pipeline_ref.py"):
        print("pin", sha((CASE / name).read_bytes())[:16], name)
    qs, tpl = questions(), template()
    rec = judges.RecordedJudge(CASE / "judge_replies.jsonl")
    recorded_prompts = {k[0] for k in rec.replies}
    used_prompts = set()
    rows = []
    for r in responses():
        q, resp = qs[r["question_id"]], r["response"]
        g = run(lambda: grader.grade_response(rec, tpl, q, resp))
        x = run(lambda: replacement.grade_response(rec, tpl, q, resp, {"judge_exception": "raise"}))
        xf = run(lambda: replacement.grade_response(rec, tpl, q, resp,
                                                   {"judge_exception": "raise", "judge_window": "full"}))
        ref = run(lambda: reference_grade(rec, q, resp))
        row = {"id": r["id"], "model": r["model"], "question_id": r["question_id"],
               "finish_reason": r["finish_reason"]}
        row["G"] = g["label"] if isinstance(g, dict) else g
        row["G_calls"] = g["judge_calls"] if isinstance(g, dict) else None
        row["X"] = x["label"] if isinstance(x, dict) else x
        row["X_calls"] = x["judge_calls"] if isinstance(x, dict) else None
        row["X_full"] = xf["label"] if isinstance(xf, dict) else xf
        row["R"] = ref[0] if isinstance(ref, tuple) else ref
        gt = replacement.extract_graded_text(resp)
        row["graded_len"] = None if gt is None else len(gt)
        row["graded_lines"] = None if gt is None else len(gt.splitlines())
        if isinstance(g, dict) and g["prompt_sha256"]:
            p = g["prompt_sha256"]
            used_prompts.add(p)
            row["prompt_sha256"] = p
            r1, r2 = rec.replies[(p, 1)], rec.replies[(p, 2)]
            row["reply1"], row["reply2"] = r1, r2
            row["call1_grade_contract"] = replacement.parse_grade(r1)
            row["call2_grade_contract"] = replacement.parse_grade(r2)
            row["call1_grade_G"] = grader.parse_grade(r1)
        if isinstance(x, dict) and x["prompt_sha256"]:
            row["X_prompt_same_as_G"] = x["prompt_sha256"] == row.get("prompt_sha256")
        rows.append(row)

    out_dir = AUDIT / "panel"
    out_dir.mkdir(exist_ok=True)
    with open(out_dir / "labels.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    n_q = len(qs)
    def table(key):
        return replacement.aggregate([{"model": r["model"], "label": r[key]} for r in rows], n_q)

    tables = {k: table(k) for k in ("G", "R", "X", "X_full")}
    print("\nlabel counts")
    for k in tables:
        print(f"  {k:7}", dict(Counter(r[k] for r in rows)))
    print("\nper model: accuracy / cga / F / not_att_% / extr_fail / judge_err")
    for m in sorted(tables["G"]):
        for k in tables:
            t = tables[k][m]
            print(f"  {m:16} {k:7} {t['accuracy']:6.1f} {t['correct_given_attempted']:6.1f} {t['f_score']:6.1f} "
                  f"{t['not_attempted_rate']:6.1f} {t['extraction_failure']:3d} {t['judge_error']:3d}")
    print("\nscore change, G minus X (points): accuracy, cga, F, not_att_%")
    for m in sorted(tables["G"]):
        a, b = tables["G"][m], tables["X"][m]
        print(f"  {m:16} " + " ".join(f"{a[k] - b[k]:+6.1f}" for k in
                                      ("accuracy", "correct_given_attempted", "f_score", "not_attempted_rate")))
    print("\ndisagreements")
    for k1, k2 in (("G", "X"), ("G", "R"), ("R", "X"), ("X", "X_full")):
        d = [r for r in rows if r[k1] != r[k2]]
        print(f"  {k1} vs {k2}: {len(d)} of {len(rows)}")
        for r in d:
            print(f"    {r['id']} {r['model']:16} {r['question_id']} {k1}={r[k1]} {k2}={r[k2]}")
    judged = [r for r in rows if "prompt_sha256" in r]
    flips = [r for r in judged if r["call1_grade_contract"] != r["call2_grade_contract"]]
    distinct = {r["prompt_sha256"]: r for r in judged}
    dflips = [r for r in distinct.values() if r["call1_grade_contract"] != r["call2_grade_contract"]]
    print(f"\njudge repeat (call 1 vs call 2, contract parser): {len(flips)} of {len(judged)} judged responses, "
          f"{len(dflips)} of {len(distinct)} distinct prompts differ")
    for r in dflips:
        print(f"    {r['id']} {r['question_id']} call1={r['reply1']!r} call2={r['reply2']!r}")
    print(f"\nprompts: recorded {len(recorded_prompts)}, used by G {len(used_prompts)}, "
          f"recorded but unused {len(recorded_prompts - used_prompts)}, used but unrecorded "
          f"{len(used_prompts - recorded_prompts)}")
    over = [r for r in rows if r["graded_len"] and r["graded_len"] > 300]
    multi = [r for r in rows if r["graded_lines"] and r["graded_lines"] > 1]
    print(f"graded texts over 300 chars: {[(r['id'], r['graded_len']) for r in over]}")
    print(f"graded texts with more than one line: {[r['id'] for r in multi]}")
    print(f"finish_reason length: {[(r['id'], r['G'], r['X']) for r in rows if r['finish_reason'] == 'length']}")
    cov = {k: sum(1 for r in rows if r[k] in replacement.LABELS) for k in tables}
    print(f"scored coverage (rows with a label, of {len(rows)}): {cov}")
    # Judge repeat as a rerun: the replacement with the recorded call-2 reply used as call 1 (and call 1 as retry).
    def swapped(prompt, call):
        return rec(prompt, 3 - call)

    x2 = {r["id"]: replacement.grade_response(swapped, tpl, qs[r["question_id"]], r["response"])["label"]
          for r in responses()}
    both = [r for r in judged if r["call1_grade_contract"] and r["call2_grade_contract"]]
    both_d = {r["prompt_sha256"]: r for r in both}
    flip_both = [r for r in both_d.values() if r["call1_grade_contract"] != r["call2_grade_contract"]]
    print(f"\njudge repeat where both calls give a grade: {len(flip_both)} of {len(both_d)} distinct prompts flip "
          f"({sum(1 for r in both if r['call1_grade_contract'] != r['call2_grade_contract'])} of {len(both)} "
          f"responses)")

    def exact(labels):
        c = Counter(labels)
        acc = c["correct"] / n_q
        att = c["correct"] + c["incorrect"]
        cga = c["correct"] / att if att else 0.0
        f = 2 * acc * cga / (acc + cga) if acc + cga else 0.0
        return {"accuracy": 100 * acc, "cga": 100 * cga, "f": 100 * f, "na": 100 * c["not_attempted"] / n_q}

    models = sorted(tables["G"])
    by = {m: [r for r in rows if r["model"] == m] for m in models}
    print("\nexact score changes in points (accuracy, cga, F, not_att_%):")
    print("  model            G-X                          G-R                          X(call2 first)-X")
    deltas = {}
    for m in models:
        e = {k: exact([r[k] for r in by[m]]) for k in ("G", "R", "X")}
        e["X2"] = exact([x2[r["id"]] for r in by[m]])
        d = {pair: {k: e[pair[0]][k] - e[pair[1]][k] for k in e["G"]}
             for pair in (("G", "X"), ("G", "R"), ("X2", "X"))}
        deltas[m] = {f"{a}-{b}": v for (a, b), v in d.items()}
        print(f"  {m:16} " + "   ".join(" ".join(f"{v:+6.1f}" for v in d[p].values())
                                         for p in (("G", "X"), ("G", "R"), ("X2", "X"))))

    rnd = __import__("random").Random(20261111)
    print("\npaired bootstrap over the 12 questions (10,000 resamples, seed 20261111), G minus X, 95% interval:")
    boot = {}
    for m in models:
        rs = by[m]
        out = {"accuracy": [], "f": []}
        for _ in range(10000):
            s = [rs[rnd.randrange(len(rs))] for _ in rs]
            a, b = exact([r["G"] for r in s]), exact([r["X"] for r in s])
            out["accuracy"].append(a["accuracy"] - b["accuracy"])
            out["f"].append(a["f"] - b["f"])
        boot[m] = {}
        for k, v in out.items():
            v.sort()
            boot[m][k] = (v[249], v[9749])
        print(f"  {m:16} accuracy [{boot[m]['accuracy'][0]:+.1f}, {boot[m]['accuracy'][1]:+.1f}]   "
              f"F [{boot[m]['f'][0]:+.1f}, {boot[m]['f'][1]:+.1f}]")
    for name, key in (("G", "G"), ("X", "X")):
        order = sorted(models, key=lambda m: -exact([r[key] for r in by[m]])["f"])
        print(f"ranking by F under {name}: {order}")

    summary = {"tables": tables, "coverage": cov, "n_rows": len(rows), "n_judged": len(judged),
               "flips_responses": len(flips), "flips_prompts": len(dflips), "distinct_prompts": len(distinct),
               "flip_both_prompts": len(flip_both), "both_graded_prompts": len(both_d), "deltas": deltas,
               "bootstrap_G_minus_X": boot}
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
