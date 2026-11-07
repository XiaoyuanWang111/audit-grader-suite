"""Grade every fixture with the grader under audit and the replacement; print a table.

    python -I audit/scripts/probe_fixtures.py [--json OUT]
"""

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(os.path.dirname(HERE), "tests"), os.path.join(os.path.dirname(HERE), "replacement")]

import common  # noqa: E402
import fixtures  # noqa: E402
import replacement_scoring  # noqa: E402
import replacement_verifier as rv  # noqa: E402


def grade_verifier_fixture(fx, n):
    with tempfile.TemporaryDirectory(prefix="fx_") as ws:
        common.materialize(ws, fx["files"])
        code, out, err = common.run_verify(ws)
        rep, reason = rv.grade(ws, n)
        reads = []
        if fx["decision"]:
            for sw, lab in fx["decision"]["readings"]:
                reads.append((sw, lab, rv.grade(ws, n, sw)[0]))
    return {"grader": "pass" if code == 0 else "fail", "exit": code, "out": out,
            "traceback": "Traceback" in err, "replacement": rep, "reason": reason, "readings": reads}


def grade_scoring_fixture(fx):
    with tempfile.TemporaryDirectory(prefix="sx_") as td:
        for r in fx["records"]:
            os.makedirs(os.path.join(td, r["trial_id"]))
            with open(os.path.join(td, r["trial_id"], "result.json"), "w", encoding="utf-8", newline="\n") as f:
                json.dump(r, f)
        rows, out, err, code = common.run_scoring(td)
        rep = replacement_scoring.scores(replacement_scoring.load(td))
    return {"grader": rows, "replacement": rep, "exit": code}


def main(argv):
    common.require_pins("before probe")
    n = rv.count_server_errors()
    assert n == fixtures.N == 41
    fixtures.all_ids()
    results = {}
    print(f"{'id':<26} {'name':<30} {'label':<5} {'grader':<6} {'exit':>4} {'repl':<5}  grader output")
    for fx in fixtures.VERIFIER_FIXTURES:
        g = grade_verifier_fixture(fx, n)
        results[fx["id"]] = {"name": fx["name"], "label": fx["label"], **g}
        flag = "" if g["grader"] == fx["label"] else "  <-- grader differs"
        if g["replacement"] != fx["label"]:
            flag += "  <-- REPLACEMENT differs"
        for sw, lab, got in g["readings"]:
            if got != lab:
                flag += f"  <-- REPLACEMENT reading {sw} differs"
        print(f"{fx['id']:<26} {fx['name']:<30} {fx['label']:<5} {g['grader']:<6} {g['exit']:>4} {g['replacement']:<5}  {g['out'][:40]!r}{' +traceback' if g['traceback'] else ''}{flag}")
    for fx in fixtures.SCORING_FIXTURES:
        g = grade_scoring_fixture(fx)
        exp = {c: (t, p, round(100 * s, 1)) for c, (t, p, s) in fx["expected"].items()}
        rep = {c: (t, p, round(100 * s, 1)) for c, (t, p, s) in g["replacement"].items()}
        results[fx["id"]] = {"name": fx["name"], "expected": exp, "grader": g["grader"], "replacement": rep}
        flag = "" if g["grader"] == exp else "  <-- grader differs"
        if rep != exp:
            flag += "  <-- REPLACEMENT differs"
        print(f"{fx['id']:<26} {fx['name']:<30} expected {exp} grader {g['grader']}{flag}")
    common.require_pins("after probe")
    if argv and argv[0] == "--json":
        with open(argv[1], "w", encoding="utf-8", newline="\n") as f:
            json.dump(results, f, indent=1, default=str)


if __name__ == "__main__":
    main(sys.argv[1:])
