"""Step 5: grade the stored panel (case/responses.jsonl) with all three graders.

Run from W:  python -B audit/scripts/panel.py {dev|holdout|all} [--show]

dev      = the 24 responses not in audit/frozen/holdout_ids.txt
holdout  = the 24 held-out responses
all      = all 48

The grader and the reference run through their command lines on the subset
file; the replacement runs in-process, at the proposed readings and at each
single alternative reading. Writes audit/panel/<subset>_*.jsonl and prints:
stored-record counts, per-response verdicts, disagreements, per-problem pass
rates, scored coverage, and each model's score under each grader.
--show prints the full text of every response where the graders disagree.
"""
import json
import pathlib
import sys
from collections import Counter

sys.dont_write_bytecode = True
W = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W / "audit" / "tests"))

import harness  # noqa: E402

PANEL = W / "audit" / "panel"


def load_subset(which):
    rows = harness.read_jsonl(W / "case" / "responses.jsonl")
    held = set((W / "audit" / "frozen" / "holdout_ids.txt").read_text(encoding="utf-8").split())
    if which == "dev":
        return [r for r in rows if r["id"] not in held]
    if which == "holdout":
        return [r for r in rows if r["id"] in held]
    return rows


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "dev"
    show = "--show" in sys.argv
    rows = load_subset(which)
    problems = harness.read_jsonl(harness.PROBLEMS)
    refs = {p["problem_id"]: p["answer"] for p in problems}
    PANEL.mkdir(parents=True, exist_ok=True)
    sub = PANEL / f"{which}_responses.jsonl"
    harness.write_jsonl(sub, rows)

    rc, so, se, g = harness.run_grader(sub, PANEL / f"{which}_grader.jsonl")
    assert g is not None, se
    rc2, so2, se2, r = harness.run_reference(sub, PANEL / f"{which}_reference.jsonl")
    assert r is not None, se2
    m = harness.replacement
    p_rows, notes = m.grade(problems, rows)
    harness.write_jsonl(PANEL / f"{which}_replacement.jsonl", p_rows)

    # Stored-record counts.
    print(f"subset {which}: {len(rows)} responses")
    print("finish_reason:", dict(Counter(x["finish_reason"] for x in rows)))
    print("per model:", dict(Counter(x["model"] for x in rows)))
    pairs = Counter((x["model"], x["problem_id"]) for x in rows)
    print("duplicate (model, problem) pairs:", sum(1 for v in pairs.values() if v > 1),
          "| unknown problem ids:", sum(1 for x in rows if x["problem_id"] not in refs))
    print("responses containing '<think>' or '</think>':",
          sum(1 for x in rows if "<think>" in x["response"] or "</think>" in x["response"]))
    print("responses with an answer line (proposed reading):",
          sum(1 for x in rows if m.answer_rest(x["response"]) is not None))
    print("grader stdout:\n" + so)
    print("reference stdout:\n" + so2)

    # Per-response table.
    table = []
    for x, gv, rv, pv in zip(rows, g, r, p_rows):
        assert gv["id"] == rv["id"] == pv["id"] == x["id"]
        alts = {}
        for k, vals in m.CHOICES.items():
            for v in vals:
                if v != m.DEFAULTS[k]:
                    alts[f"{k}={v}"] = m.verdict(x["response"], refs[x["problem_id"]], {k: v})[0]
        table.append({"id": x["id"], "model": x["model"], "problem_id": x["problem_id"],
                      "finish_reason": x["finish_reason"],
                      "grader": gv["verdict"], "grader_extracted": gv["extracted"],
                      "reference": rv["verdict"], "reference_answer": rv["answer"],
                      "replacement": pv["verdict"], "replacement_extracted": pv["extracted"],
                      "alternatives": alts})
    harness.write_jsonl(PANEL / f"{which}_table.jsonl", table)

    b = harness.binary
    print(f"{'id':<5}{'model':<11}{'pid':<5}{'finish':<8}{'grader':<22}{'reference':<22}{'replacement':<22}alt readings that change the replacement")
    for t in table:
        changed = [k for k, v in t["alternatives"].items() if b(v) != b(t["replacement"])]
        flag = "" if b(t["grader"]) == b(t["reference"]) == b(t["replacement"]) else "  <-- disagree"
        print(f"{t['id']:<5}{t['model']:<11}{t['problem_id']:<5}{t['finish_reason']:<8}"
              f"{t['grader'] + '(' + str(t['grader_extracted']) + ')':<22}"
              f"{t['reference'] + '(' + str(t['reference_answer']) + ')':<22}"
              f"{t['replacement'] + '(' + str(t['replacement_extracted']) + ')':<22}{','.join(changed) or '-'}{flag}")

    # Disagreements at the score level.
    def dis(a, c):
        return [t["id"] for t in table if b(t[a]) != b(t[c])]
    print("score-level disagreements: grader vs replacement", dis("grader", "replacement"),
          "| grader vs reference", dis("grader", "reference"),
          "| reference vs replacement", dis("reference", "replacement"))
    print("label-level disagreements grader vs replacement:",
          [t["id"] for t in table if t["grader"] != t["replacement"]])

    # Per-problem pass rates.
    print("per-problem correct counts (grader / reference / replacement), out of models present:")
    for pid in sorted(refs):
        ts = [t for t in table if t["problem_id"] == pid]
        if ts:
            print(f"  {pid}: {sum(b(t['grader']) == 'correct' for t in ts)} / "
                  f"{sum(b(t['reference']) == 'correct' for t in ts)} / "
                  f"{sum(b(t['replacement']) == 'correct' for t in ts)} of {len(ts)}")

    # Scores: each grader's own score, and correct/12 for comparison.
    print("model scores: grader as printed | grader correct/12 | reference | replacement | replacement - grader")
    models = sorted({t["model"] for t in table})
    gt = {}
    for line in so.splitlines()[1:]:
        parts = line.split()
        if len(parts) == 5:
            gt[parts[0]] = float(parts[4])
    for mod in models:
        ts = [t for t in table if t["model"] == mod]
        gc = sum(b(t["grader"]) == "correct" for t in ts)
        rcnt = sum(b(t["reference"]) == "correct" for t in ts)
        pc = sum(b(t["replacement"]) == "correct" for t in ts)
        print(f"  {mod:<10} {gt.get(mod, float('nan')):6.1f} | {100 * gc / 12:6.1f} | {100 * rcnt / 12:6.1f} | "
              f"{100 * pc / 12:6.1f} | {100 * pc / 12 - gt.get(mod, float('nan')):+6.1f}")
    expected = len(models) * 12
    print(f"scored coverage: grader {len(g)}/{expected}, reference {len(r)}/{expected}, "
          f"replacement {sum(1 for x in p_rows if x['scored'])}/{expected} "
          f"(subset holds {len(rows)} of the models' 12-problem sets)")
    for n in notes:
        print("replacement note:", n)

    if show:
        dis_ids = {t["id"] for t in table
                   if len({b(t["grader"]), b(t["reference"]), b(t["replacement"])}) > 1}
        for x in rows:
            if x["id"] in dis_ids:
                print(f"\n===== {x['id']} {x['model']} {x['problem_id']} ref={refs[x['problem_id']]} finish={x['finish_reason']}")
                print(ascii(x["response"]))


if __name__ == "__main__":
    main()
