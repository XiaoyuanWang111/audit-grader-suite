"""Labeled fixtures for the count-server-errors verifier and scoring script.

Every label comes from audit/CONTRACT.md alone. A verifier fixture is a sandbox
state: a map from a path under /workspace to its bytes (None = an empty
directory). A decision fixture also gives its label under each reading of the
decision entries it involves; its main label is the proposed reading's.

Fixture id: check name + the first 16 hex digits of the sha256 of the
fixture's canonical JSON (check, files or records, and readings).
"""

import hashlib
import json

N = 41


def _fid(check, payload):
    canon = json.dumps({"check": check, **payload}, sort_keys=True, ensure_ascii=True)
    return f"{check}:{hashlib.sha256(canon.encode('ascii')).hexdigest()[:16]}"


def A(name, files, label, kind, decision=None):
    """Verifier fixture. decision = {"switches": {...}, "readings": [(switches, label), ...]}"""
    enc = {k: (None if v is None else v.hex()) for k, v in files.items()}
    payload = {"files": enc}
    if decision:
        payload["readings"] = [[sorted(sw.items()), lab] for sw, lab in decision["readings"]]
    return {"id": _fid("answer", payload), "name": name, "files": files, "label": label,
            "kind": kind, "decision": decision}


def ans(b):
    return {"out/answer.txt": b}


def readings(entry_switch, values_labels):
    return {"entries": [entry_switch[0]],
            "readings": [({entry_switch[1]: v}, lab) for v, lab in values_labels]}


VERIFIER_FIXTURES = [
    # Pass: the trimmed content is 41.
    A("plain-no-newline", ans(b"41"), "pass", "pass"),
    A("final-newline", ans(b"41\n"), "pass", "pass"),
    A("spaces-around", ans(b" 41 \n"), "pass", "pass"),
    A("tab-crlf", ans(b"\t41\r\n"), "pass", "pass"),
    A("blank-lines-around", ans(b"\n\n41\n\n"), "pass", "pass"),
    A("crlf", ans(b"41\r\n"), "pass", "pass"),
    A("formfeed-vtab", ans(b"\f41\v"), "pass", "pass"),
    A("other-files-ignored", {"out/answer.txt": b"41\n", "answer.txt": b"37\n",
                              "tmp/count.py": b"print(37)\n", "out/count.sh": b"echo 37\n",
                              "out/notes.txt": b"40\n"}, "pass", "pass"),
    # Fail: no answer file at /workspace/out/answer.txt.
    A("empty-workspace", {}, "fail", "missing"),
    A("only-tmp-notes", {"tmp/notes.txt": b"access.log: 20\naccess.log.1: 17\n"}, "fail", "missing"),
    A("empty-out-dir", {"out": None}, "fail", "missing"),
    A("wrong-path-root-41", {"answer.txt": b"41\n"}, "fail", "missing"),
    A("wrong-path-root-37", {"answer.txt": b"37\n"}, "fail", "missing"),
    A("answer-is-directory", {"out/answer.txt": None}, "fail", "missing"),
    A("answer-is-directory-root-41", {"out/answer.txt": None, "answer.txt": b"41\n"}, "fail", "missing"),
    A("no-extension", {"out/answer": b"41\n"}, "fail", "missing"),
    A("double-extension", {"out/answer.txt.txt": b"41\n"}, "fail", "missing"),
    A("tmp-answer", {"tmp/answer.txt": b"41\n"}, "fail", "missing"),
    # Fail: empty content.
    A("empty-file", ans(b""), "fail", "empty"),
    A("whitespace-only", ans(b"\n \t\n"), "fail", "empty"),
    # Fail: another integer (near misses from the log traps first).
    A("count-40-field9", ans(b"40\n"), "fail", "wrong-count"),
    A("count-45-grep", ans(b"45\n"), "fail", "wrong-count"),
    A("count-37-no-gz", ans(b"37\n"), "fail", "wrong-count"),
    A("count-36-both", ans(b"36\n"), "fail", "wrong-count"),
    A("count-20-one-file", ans(b"20\n"), "fail", "wrong-count"),
    A("count-0", ans(b"0\n"), "fail", "wrong-count"),
    A("count-minus-41", ans(b"-41\n"), "fail", "wrong-count"),
    A("count-42", ans(b"42\n"), "fail", "wrong-count"),
    A("count-410", ans(b"410\n"), "fail", "wrong-count"),
    A("count-4", ans(b"4\n"), "fail", "wrong-count"),
    # Fail: other text in the content.
    A("text-suffix", ans(b"41 server errors\n"), "fail", "other-text"),
    A("text-prefix", ans(b"Total 5xx: 41\n"), "fail", "other-text"),
    A("json-object", ans(b'{"count": 41}\n'), "fail", "other-text"),
    A("repeated-41", ans(b"41\n41\n"), "fail", "other-text"),
    A("inner-space", ans(b"4 1\n"), "fail", "other-text"),
    A("words", ans(b"forty-one\n"), "fail", "other-text"),
    A("key-value", ans(b"count=41"), "fail", "other-text"),
    A("two-counts", ans(b"41\n37\n"), "fail", "other-text"),
    A("sentence", ans(b"The count is 41.\n"), "fail", "other-text"),
    A("instruction-restated", ans(b"Count the requests in all three files whose status code is a server error (500 to 599).\n"), "fail", "other-text"),
    # Fail: not an integer numeral.
    A("decimal-point", ans(b"41.0\n"), "fail", "not-integer"),
    A("exponent", ans(b"4.1e1\n"), "fail", "not-integer"),
    A("hex", ans(b"0x29\n"), "fail", "not-integer"),
    A("underscore", ans(b"4_1\n"), "fail", "not-integer"),
    A("trailing-comma", ans(b"41,\n"), "fail", "not-integer"),
    A("trailing-dot", ans(b"41.\n"), "fail", "not-integer"),
    # Fail: control characters that are whitespace under neither reading of D-whitespace-set.
    A("info-sep-1c-after", ans(b"41\x1c\n"), "fail", "control"),
    A("info-sep-1f-before", ans(b"\x1f41"), "fail", "control"),
    A("info-sep-1e-1d", ans(b"\x1e41\x1d"), "fail", "control"),
    A("nul-after", ans(b"41\x00"), "fail", "control"),
    A("invalid-utf8", ans(b"41\xff\n"), "fail", "control"),
    # Fail: more than 4,300 digits, value not 41.
    A("long-number", ans(b"1" * 4301 + b"\n"), "fail", "wrong-count"),
]

# Decision fixtures: label under the proposed reading, plus every reading.
_D = [
    ("leading-zero", ans(b"041\n"), "pass", ("D-leading-zeros", "leading_zeros"), [("allow", "pass"), ("reject", "fail")]),
    ("two-leading-zeros", ans(b"0041"), "pass", ("D-leading-zeros", "leading_zeros"), [("allow", "pass"), ("reject", "fail")]),
    ("zeros-past-int-limit", ans(b"0" * 4299 + b"41\n"), "pass", ("D-leading-zeros", "leading_zeros"), [("allow", "pass"), ("reject", "fail")]),
    ("plus-sign", ans(b"+41\n"), "pass", ("D-plus-sign", "plus_sign"), [("allow", "pass"), ("reject", "fail")]),
    ("arabic-indic-digits", ans("٤١\n".encode("utf-8")), "fail", ("D-digit-script", "digit_script"), [("ascii", "fail"), ("unicode", "pass")]),
    ("fullwidth-digits", ans("４１\n".encode("utf-8")), "fail", ("D-digit-script", "digit_script"), [("ascii", "fail"), ("unicode", "pass")]),
    ("nbsp-after", ans("41 \n".encode("utf-8")), "fail", ("D-whitespace-set", "whitespace_set"), [("ascii", "fail"), ("unicode", "pass")]),
    ("ideographic-space-before", ans("　41".encode("utf-8")), "fail", ("D-whitespace-set", "whitespace_set"), [("ascii", "fail"), ("unicode", "pass")]),
    ("line-separator-after", ans("41 ".encode("utf-8")), "fail", ("D-whitespace-set", "whitespace_set"), [("ascii", "fail"), ("unicode", "pass")]),
    ("nel-after", ans("41\u0085".encode("utf-8")), "fail", ("D-whitespace-set", "whitespace_set"), [("ascii", "fail"), ("unicode", "pass")]),
    ("utf8-bom", ans(b"\xef\xbb\xbf41\n"), "fail", ("D-encoding", "encoding"), [("utf8", "fail"), ("bom", "pass")]),
    ("utf16le-bom", ans(b"\xff\xfe4\x001\x00\n\x00"), "fail", ("D-encoding", "encoding"), [("utf8", "fail"), ("bom", "pass")]),
]
for name, files, label, (entry, switch), vl in _D:
    VERIFIER_FIXTURES.append(A(name, files, label, "decision", readings((entry, switch), vl)))

# A fixture that two entries decide together.
VERIFIER_FIXTURES.append(A(
    "plus-sign-and-leading-zero", ans(b"+041\n"), "pass", "decision",
    {"entries": ["D-plus-sign", "D-leading-zeros"],
     "readings": [({"plus_sign": "allow", "leading_zeros": "allow"}, "pass"),
                  ({"plus_sign": "allow", "leading_zeros": "reject"}, "fail"),
                  ({"plus_sign": "reject", "leading_zeros": "allow"}, "fail"),
                  ({"plus_sign": "reject", "leading_zeros": "reject"}, "fail")]}))


def S(name, records, expected, kind):
    """Scoring fixture: records = list of result.json dicts (a missing key is left out).
    expected = {config: (trials, passes, mean reward)} from the contract."""
    return {"id": _fid("score", {"records": records}), "name": name, "records": records,
            "expected": expected, "kind": kind}


def rec(tid, config, code="__absent__", status="completed", output=""):
    r = {"trial_id": tid, "task": "count-server-errors", "config": config,
         "agent_status": status, "agent_error": None, "agent_steps": 5, "verifier_output": output}
    if code != "__absent__":
        r["verifier_exit_code"] = code
    return r


SCORING_FIXTURES = [
    S("exit-0", [rec("x1", "c", 0)], {"c": (1, 1, 1.0)}, "reward"),
    S("exit-1", [rec("x1", "c", 1)], {"c": (1, 0, 0.0)}, "reward"),
    S("exit-2", [rec("x1", "c", 2)], {"c": (1, 0, 0.0)}, "reward"),
    S("exit-127", [rec("x1", "c", 127)], {"c": (1, 0, 0.0)}, "reward"),
    S("exit-137", [rec("x1", "c", 137)], {"c": (1, 0, 0.0)}, "reward"),
    S("exit-minus-9", [rec("x1", "c", -9)], {"c": (1, 0, 0.0)}, "reward"),
    S("exit-null", [rec("x1", "c", None, status="error", output=None)], {"c": (1, 0, 0.0)}, "reward"),
    S("exit-absent", [rec("x1", "c")], {"c": (1, 0, 0.0)}, "reward"),
    S("exit-false", [rec("x1", "c", False)], {"c": (1, 0, 0.0)}, "reward"),
    S("exit-string-0", [rec("x1", "c", "0")], {"c": (1, 0, 0.0)}, "reward"),
    S("agent-error-exit-0", [rec("x1", "c", 0, status="error")], {"c": (1, 1, 1.0)}, "reward"),
    S("agent-timeout-exit-0", [rec("x1", "c", 0, status="timeout")], {"c": (1, 1, 1.0)}, "reward"),
    S("output-correct-exit-1", [rec("x1", "c", 1, output="correct")], {"c": (1, 0, 0.0)}, "reward"),
    S("output-no-answer-exit-0", [rec("x1", "c", 0, output="no answer file")], {"c": (1, 1, 1.0)}, "reward"),
    S("denominator-with-null", [rec("x1", "c", 0), rec("x2", "c", None, status="error", output=None),
                                rec("x3", "c", 1)], {"c": (3, 1, 1 / 3)}, "score"),
    S("denominator-errors-timeouts", [rec("x1", "c", 0), rec("x2", "c", 0, status="timeout"),
                                      rec("x3", "c", 3, status="error")], {"c": (3, 2, 2 / 3)}, "score"),
    S("two-configs", [rec("x1", "a", 0), rec("x2", "a", 1), rec("x3", "b", 0), rec("x4", "b", 0)],
      {"a": (2, 1, 0.5), "b": (2, 2, 1.0)}, "score"),
]


def all_ids():
    ids = [f["id"] for f in VERIFIER_FIXTURES] + [f["id"] for f in SCORING_FIXTURES]
    assert len(ids) == len(set(ids)), "fixture id collision"
    return ids
