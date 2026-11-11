"""Print the verdict of the grader under audit (and of the reference and the
replacement) on one input.

Usage (from W, with NLTK_DATA set as in case/TASK.md):
  python audit/scripts/verdict.py --fixture '<fixture id>'
  python audit/scripts/verdict.py --check <instruction id> --key <dataset key> --text '<response>' [--kw '{"n": 2}']
  python audit/scripts/verdict.py --panel <folder> <run> <key>

The grader verdict is the strict harness verdict (case/grader/IFBench/grader.py:
`response.strip()` and `check_following(response)`); the loose verdict uses
test_instruction_following_loose.
"""
import argparse
import json

import common
import ref_runner
import replacement

ap = argparse.ArgumentParser()
ap.add_argument("--fixture")
ap.add_argument("--check")
ap.add_argument("--key")
ap.add_argument("--text")
ap.add_argument("--kw", default="{}")
ap.add_argument("--panel", nargs=3)
a = ap.parse_args()

label = None
if a.fixture:
    from tests.fixtures_data import FIX
    f = next(x for x in FIX if x["id"] == a.fixture)
    check, key, text, over, label = f["check"], f["key"], f["response"], f["kw"], f["label"]
elif a.panel:
    folder, run, key = a.panel
    rec = json.loads((common.CASE / "panel" / folder / f"{run}.jsonl").read_text(encoding="utf-8").splitlines()[common.row_list().index(key)])
    text = rec["response"]
    rows = common.rows()
    for check in rows[key]["instruction_id_list"]:
        kw, prompt = common.kwargs_for(key, check)
        print(f"{check}: grader={common.grade_grader(check, kw, prompt, text)} loose={common.grade_grader_loose(check, kw, prompt, text)} "
              f"reference={ref_runner.grade_reference(check, kw, prompt, text)} replacement={replacement.grade(check, kw, prompt, text)}")
    raise SystemExit(0)
else:
    check, key, text, over = a.check, a.key, a.text, json.loads(a.kw)
kw, prompt = common.kwargs_for(key, check, over)
print("check:", check, "| key:", key, "| kwargs:", {k: v for k, v in kw.items() if v is not None and k != "reference_text"})
print("response:", ascii(text))
if label:
    print("contract label:", label)
def show(name, fn):
    try:
        v = fn(check, kw, prompt, text)
    except Exception as e:  # noqa: BLE001  (a checker exception is a finding; print it, do not stop)
        v = f"raised {type(e).__name__}: {e}"
    print(name, v)


show("grader (strict):", common.grade_grader)
show("grader (loose): ", common.grade_grader_loose)
show("reference:      ", ref_runner.grade_reference)
show("replacement:    ", replacement.grade)
