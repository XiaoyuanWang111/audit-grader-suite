"""Print every fixture's label and the verdicts of the grader, the reference and the replacement (proposed readings).

Usage (from the audit run directory): python audit/scripts/fixture_table.py [--json audit/work/fixture_table.json]
A recorded verdict (the fixture's "grader" or "reference" field) that differs from today's run is flagged with "!".
"""

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "tests"))

import contract_grader  # noqa: E402
import test_fixtures as tf  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    args = ap.parse_args()
    rows = []
    for f in tf.FIXTURES:
        g = tf.verdict("grader", f)
        r = tf.verdict("reference", f)
        x = tf.verdict("replacement", f, dict(contract_grader.PROPOSED))
        rows.append({"id": f["id"], "shows": f["shows"], "task_id": f["task_id"], "label": f["label"],
                     "grader": g, "reference": r, "replacement": x, "note": f["note"]})
        flag = "".join(["!" if g != f["grader"] else " ", "!" if r != f["reference"] else " ",
                        "!" if x != f["label"] else " "])
        print(f"{flag} {f['id']:<28} {f['shows']:<27} {f['label']:<5} grader={g:<6} ref={r:<6} repl={x:<6} {f['note']}")
    if args.json:
        with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(rows, fh, indent=1)
    wrong = {k: sum(row[k] != row["label"] for row in rows) for k in ("grader", "reference", "replacement")}
    print("fixtures", len(rows), "verdicts that differ from the label:", wrong)


if __name__ == "__main__":
    main()
