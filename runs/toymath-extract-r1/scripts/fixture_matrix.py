"""Run every fixture through grade.py, the reference and the replacement, and classify each verdict.

Usage: python -I audit/scripts/fixture_matrix.py      (writes audit/out/fixture_matrix.json)

Each verdict is classified against the fixture's contract label:
  pass       the verdict equals the label (proposed readings)
  decision   it equals the label under reading (b) of a decision entry the fixture names
  label      it differs from the label only between incorrect and no_answer (the score is the same)
  finding    none of these
It also checks the replacement against the hand labels: under (a) and under each entry's (b) switch alone, it
must give fixture["alt"].get(entry, fixture["label"]).
"""
import collections
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "audit", "tests"))
sys.path.insert(0, os.path.join(ROOT, "audit", "scripts"))

import fixtures  # noqa: E402
import graders  # noqa: E402
import grade_contract  # noqa: E402


def classify(verdict, fx):
    if verdict == fx["label"]:
        return "pass", []
    entries = [d for d, lab in sorted(fx["alt"].items()) if lab == verdict]
    if entries:
        return "decision", entries
    if {verdict, fx["label"]} == {"incorrect", "no_answer"}:
        return "label", []
    return "finding", []


def main():
    fxs = fixtures.FIXTURES
    rows = graders.as_rows(fxs)
    g, g_out, g_rc = graders.run_grade_py(rows)
    r, r_out, r_rc = graders.run_reference(rows)
    rep = graders.run_replacement(rows)
    assert g is not None and r is not None, (g_out, r_out)
    self_check = []
    for entry in grade_contract.ENTRY.values():
        sw = grade_contract.switches_for([entry])
        got = graders.run_replacement(rows, sw)
        for fx in fxs:
            want = fx["alt"].get(entry, fx["label"])
            if got[fx["id"]][1] != want:
                self_check.append((fx["id"], entry, want, got[fx["id"]]))
    for fx in fxs:
        if rep[fx["id"]][1] != fx["label"]:
            self_check.append((fx["id"], "(a)", fx["label"], rep[fx["id"]]))
    matrix = []
    for fx in fxs:
        entry = {"id": fx["id"], "family": fx["family"], "problem_id": fx["problem_id"], "label": fx["label"],
                 "alt": fx["alt"], "note": fx["note"], "response_ascii": ascii(fx["response"])[:120]}
        for name, res in (("grade_py", g), ("reference", r), ("replacement", rep)):
            extracted, verdict = res[fx["id"]]
            kind, entries = classify(verdict, fx)
            entry[name] = {"extracted": None if extracted is None else str(extracted)[:40], "verdict": verdict,
                           "class": kind, "entries": entries}
        matrix.append(entry)
    with open(os.path.join(ROOT, "audit", "out", "fixture_matrix.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"fixtures": len(fxs), "replacement_self_check_failures": self_check, "matrix": matrix}, f,
                  indent=1, ensure_ascii=True)
        f.write("\n")
    print("fixtures:", len(fxs), "| grade.py exit", g_rc, "| reference exit", r_rc)
    print("replacement self-check failures:", len(self_check))
    for item in self_check:
        print("  ", item)
    for name in ("grade_py", "reference", "replacement"):
        c = collections.Counter(e[name]["class"] for e in matrix)
        print("%-12s %s" % (name, dict(sorted(c.items()))))
    for name in ("grade_py", "reference"):
        print("--- %s: every verdict that is not a pass" % name)
        for e in matrix:
            v = e[name]
            if v["class"] != "pass":
                print("  %-9s %-25s %s label=%s got=%s extracted=%s %s | %s" % (
                    v["class"], e["id"], e["problem_id"], e["label"], v["verdict"], v["extracted"],
                    ",".join(v["entries"]), e["response_ascii"][:70]))


if __name__ == "__main__":
    main()
