"""Print every fixture whose label a grader contradicts (discovery run, step 3).

Run from W:  python -B audit/scripts/discover.py
"""
import pathlib
import sys

sys.dont_write_bytecode = True
W = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W / "audit" / "tests"))

import fixtures  # noqa: E402
import harness  # noqa: E402


def main():
    res = harness.grade_all(fixtures.FIXTURES, "discover")
    n = {"grader": 0, "reference": 0, "replacement": 0}
    for f in fixtures.FIXTURES:
        v = res[f["id"]]
        marks = []
        if v["grader"] != f["label"]:
            n["grader"] += 1
            marks.append(f"GRADER={v['grader']}({v['grader_extracted']})")
        if harness.binary(v["reference"]) != harness.binary(f["label"]):
            n["reference"] += 1
            marks.append(f"REF={v['reference']}({v['reference_answer']})")
        if v["replacement"] != f["label"]:
            n["replacement"] += 1
            marks.append(f"REPL={v['replacement']}")
        if marks:
            print(f"{f['name']:<28} {f['kind']:<9} {','.join(f['tags']):<40} label={f['label']:<10} " + " ".join(marks))
    print(f"{len(fixtures.FIXTURES)} fixtures; mismatches: {n}")


if __name__ == "__main__":
    main()
