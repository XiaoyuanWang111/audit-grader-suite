"""Regression tests: the labeled sandbox fixtures (fixtures.py) against the verifier under audit and the replacement.

Run from the audit folder's parent:  python -I audit/tests/test_verifier_fixtures.py -v
(or with --table to print every verdict and write audit/results/fixtures_run.json).

The verifier runs as the evaluation runs it: `bash verify.sh` with WORKSPACE, TESTS_DIR and PYTHON set
(grader_runner.run_verify_sh). Tests the current grader fails are unittest.expectedFailure, the strict-xfail
equivalent here (pytest is not installed): an unexpected success fails the run.
"""

import concurrent.futures
import json
import os
import pathlib
import shutil
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent / "scripts")]

import fixtures as FX  # noqa: E402
import grader_runner as GR  # noqa: E402
import replacement_verifier as RV  # noqa: E402

SYMLINKS = GR.symlinks_available()
WORKERS = int(os.environ.get("AUDIT_WORKERS", "6"))
NON_ASCII = {"nbsp", "ideographic-space", "nel", "arabic-indic-digits", "fullwidth-digits", "utf8-bom", "utf16-bom",
             "invalid-utf8", "info-separator-1c", "nul-after", "instruction-restatement", "lf"}
_CACHE = {}


def _run_one(fx, utf8=True):
    root = GR.new_tmpdir("fx_")
    try:
        try:
            ws = GR.build_workspace(fx["state"], root)
        except GR.SymlinkUnavailable:
            return None
        python, path_prepend = None, None
        if fx["env"] == "fake-python3":
            fakebin = root / "fakebin"  # outside the workspace, as /usr/local/bin would be
            fakebin.mkdir()
            (fakebin / "python3").write_bytes(FX.FAKE_PYTHON3.encode())
            os.chmod(fakebin / "python3", 0o755)
            python, path_prepend = "python3", fakebin
        code, out = GR.run_verify_sh(ws, utf8=utf8, python=python, path_prepend=path_prepend)
        verdict, reason = RV.grade_workspace(str(ws))
        flips = {e: RV.grade_workspace(str(ws), sw=RV.switches_for([e]))[0] for e in RV.DECISIONS}
        return {"exit": code, "output": out, "grader": "pass" if code == 0 else "fail",
                "replacement": verdict, "replacement_reason": reason, "flips": flips}
    finally:
        shutil.rmtree(root, ignore_errors=True)


def results(utf8=True):
    if utf8 not in _CACHE:
        todo = FX.FIXTURES if utf8 else [fx for fx in FX.FIXTURES if fx["name"] in NON_ASCII]
        with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as ex:
            futs = {fx["id"]: ex.submit(_run_one, fx, utf8) for fx in todo}
            _CACHE[utf8] = {k: v.result() for k, v in futs.items()}
    return _CACHE[utf8]


def _get(fx, test):
    r = results()[fx["id"]]
    if r is None:
        test.skipTest("this host cannot create symbolic links")
    return r


class VerifierFixtures(unittest.TestCase):
    """The verifier under audit must give each fixture its contract label (proposed readings)."""


class ReplacementFixtures(unittest.TestCase):
    """The replacement must give each fixture its label, and each decision switch its alternative label."""


class DecisionClassification(unittest.TestCase):
    """Where the grader differs from a label because of a decision, it must match that entry's alternative label."""


class EncodingInvariance(unittest.TestCase):
    """The image's locale is not recorded; the verifier's verdict must not depend on Python's default encoding."""


def _make_grader_test(fx):
    def test(self):
        r = _get(fx, self)
        self.assertEqual(r["grader"], fx["label"], f"{fx['id']} exit={r['exit']} output={r['output']!r}")
    if fx["grader"]:
        test = unittest.expectedFailure(test)
    test.__doc__ = f"{fx['id']} {fx['name']}: label {fx['label']}; known grader difference: {fx['grader']}"
    return test


def _make_replacement_test(fx):
    def test(self):
        r = _get(fx, self)
        self.assertEqual(r["replacement"], fx["label"], f"{fx['id']}: {r['replacement_reason']}")
        for entry, alt_label in fx["alt"].items():
            self.assertEqual(r["flips"][entry], alt_label, f"{fx['id']} with {entry} flipped")
    test.__doc__ = f"{fx['id']} {fx['name']}"
    return test


def _make_decision_test(fx, entry):
    def test(self):
        r = _get(fx, self)
        self.assertEqual(r["grader"], fx["alt"][entry], f"{fx['id']}: grader should follow {entry} reading B")
    test.__doc__ = f"{fx['id']} {fx['name']}: grader verdict = {entry} reading B"
    return test


def _make_encoding_test(fx):
    def test(self):
        a = results(utf8=True)[fx["id"]]
        b = results(utf8=False)[fx["id"]]
        if a is None or b is None:
            self.skipTest("this host cannot create symbolic links")
        self.assertEqual(a["exit"], b["exit"], f"{fx['id']}: PYTHONUTF8=1 {a['exit']} vs default {b['exit']}")
    test.__doc__ = f"{fx['id']} {fx['name']}"
    return test


for _fx in FX.FIXTURES:
    _slug = _fx["name"].replace("-", "_")
    setattr(VerifierFixtures, f"test_{_slug}", _make_grader_test(_fx))
    setattr(ReplacementFixtures, f"test_{_slug}", _make_replacement_test(_fx))
    if _fx["grader"] and _fx["grader"].startswith("D-"):
        setattr(DecisionClassification, f"test_{_slug}", _make_decision_test(_fx, _fx["grader"]))
    if _fx["name"] in NON_ASCII:
        setattr(EncodingInvariance, f"test_{_slug}", _make_encoding_test(_fx))


def table():
    rows = []
    for fx in FX.FIXTURES:
        r = results()[fx["id"]]
        if r is None:
            rows.append({"id": fx["id"], "name": fx["name"], "label": fx["label"], "skipped": "no symlinks"})
            continue
        rows.append({"id": fx["id"], "name": fx["name"], "label": fx["label"], "alt": fx["alt"],
                     "known_grader_difference": fx["grader"], "grader": r["grader"], "exit": r["exit"],
                     "grader_output": r["output"][-300:], "replacement": r["replacement"],
                     "replacement_reason": r["replacement_reason"], "flips": r["flips"]})
    return rows


if __name__ == "__main__":
    if "--table" in sys.argv:
        rows = table()
        out = HERE.parent / "results" / "fixtures_run.json"
        out.parent.mkdir(exist_ok=True)
        out.write_text(json.dumps(rows, indent=1, ensure_ascii=True) + "\n", encoding="utf-8", newline="\n")
        for row in rows:
            if "skipped" in row:
                print(f"{row['id']} {row['name']:<36} SKIPPED ({row['skipped']})")
                continue
            mark = "" if row["grader"] == row["label"] else f"  <-- grader differs ({row['known_grader_difference']})"
            print(f"{row['id']} {row['name']:<36} label={row['label']:<4} grader={row['grader']:<4} "
                  f"exit={row['exit']} repl={row['replacement']:<4} out={row['grader_output'][:60]!r}{mark}")
    else:
        unittest.main()
