"""Labeled fixtures for the ToyOps count-server-errors verifier (check `answer-file`, contract C1).

Each fixture is a sandbox state: the files the agent leaves under /workspace (the read-only logs are not part of
it). `label` is the verdict under the contract's proposed readings, written from audit/CONTRACT.md alone. `alt`
gives the label under the alternative reading of each decision entry whose reading changes it.

`grader` records how the current verifier (verify.sh + check_answer.py, manifest hashes) is known to differ, from the
first run of these fixtures on 2026-11-07:
- "F<n>" or "G<n>": the grader's verdict is wrong and no reading of the text makes it right (a finding;
  G marks the grading environment rather than the verifier code).
- "D-<entry>": the grader's verdict differs from `label` but matches the alternative reading of that entry.
Tests whose grader verdict differs from `label` are expected failures, so the change that fixes the grader (or
the maintainers' choice of the other reading) must update this file.

A fixture's id is its check name plus the first 16 hex digits of the sha256 of its canonical JSON (state and
environment), so ids stay stable when names or notes change.
"""

import hashlib
import json
import pathlib

CHECK = "answer-file"
INSTRUCTION = (pathlib.Path(__file__).resolve().parents[2] / "case" / "task" / "instruction.md").read_bytes()


def f(path, data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return {"path": path, "kind": "file", "hex": data.hex()}


def d(path):
    return {"path": path, "kind": "dir"}


def link(path, target):
    return {"path": path, "kind": "symlink", "target": target}


OUT_DIR = d("out")  # the harness creates /workspace/out empty; the agent may remove it


def ans(data):
    return [OUT_DIR, f("out/answer.txt", data)]


FIXTURES = [
    # ---- pass controls (unambiguous) ----
    dict(name="lf", state=ans("41\n"), label="pass", note="the count and a final newline"),
    dict(name="no-newline", state=ans("41"), label="pass", note="no final newline (trial t04)"),
    dict(name="crlf", state=ans("41\r\n"), label="pass", note="CRLF ending; CR is whitespace under every reading"),
    dict(name="many-newlines", state=ans("41\n\n\n"), label="pass", note="several final newlines"),
    dict(name="leading-whitespace", state=ans("\n \t41 \n"), label="pass", note="whitespace at both ends"),
    dict(name="vt-ff", state=ans("\x0b41\x0c\n"), label="pass",
         note="VT and FF: whitespace under both readings of D-whitespace"),
    dict(name="extra-files", state=ans("41\n") + [f("out/count.sh", "zcat -f /workspace/logs/access.log* | wc -l\n"),
                                                   f("tmp/notes.txt", "draft: 40\n")],
         label="pass", note="other files the agent left do not matter"),
    dict(name="both-paths-out-right", state=ans("41\n") + [f("answer.txt", "37\n")], label="pass",
         note="out/answer.txt is the answer; /workspace/answer.txt is ignored"),

    # ---- missing answer file (README rule 1: fails) ----
    dict(name="missing-out-empty", state=[OUT_DIR], label="fail", grader="F1",
         note="the agent wrote nothing; /workspace/out is empty (trial t21)"),
    dict(name="missing-no-out-dir", state=[], label="fail", grader="F1", note="/workspace/out removed, nothing written"),
    dict(name="missing-notes-only", state=[OUT_DIR, f("tmp/notes.txt", "access.log: 20\naccess.log.1: 17\n")],
         label="fail", grader="F1", note="partial notes, no answer file (trial t14)"),
    dict(name="answer-is-directory", state=[OUT_DIR, d("out/answer.txt")], label="fail", grader="F1",
         note="a directory at the answer path is not an answer file"),
    dict(name="dangling-symlink", state=[OUT_DIR, link("out/answer.txt", "../tmp/nowhere.txt")], label="fail",
         grader="F1", needs_symlink=True, note="a link to nothing is a missing answer"),

    # ---- answer at another path (README rule 1 names /workspace/out/answer.txt) ----
    dict(name="wrong-path-right-value", state=[OUT_DIR, f("answer.txt", "41\n")], label="fail", grader="F2",
         note="answer written to /workspace/answer.txt (trials t12, t35)"),
    dict(name="wrong-path-wrong-value", state=[OUT_DIR, f("answer.txt", "37\n")], label="fail",
         note="answer at the wrong path with a wrong value (trial t23)"),
    dict(name="both-paths-out-wrong", state=ans("37\n") + [f("answer.txt", "41\n")], label="fail",
         note="a wrong out/answer.txt is not rescued by /workspace/answer.txt"),
    dict(name="dir-at-answer-path-and-root-answer", state=[OUT_DIR, d("out/answer.txt"), f("answer.txt", "41\n")],
         label="fail", grader="F2", note="out/answer.txt is a directory; /workspace/answer.txt holds 41"),

    # ---- empty or not the count (unambiguous fails) ----
    dict(name="empty", state=ans(""), label="fail", note="0 bytes (trial t26)"),
    dict(name="whitespace-only", state=ans(" \n\t\n"), label="fail", note="whitespace only"),
    dict(name="value-40", state=ans("40\n"), label="fail", note="the 9th-field miscount (t07, t27)"),
    dict(name="value-37", state=ans("37\n"), label="fail", note=".gz skipped (t11 and others)"),
    dict(name="value-45", state=ans("45\n"), label="fail", note="size field counted (t24, t31)"),
    dict(name="value-42", state=ans("42\n"), label="fail", note="off by one"),
    dict(name="value-0", state=ans("0\n"), label="fail", note="t33"),
    dict(name="negative", state=ans("-41\n"), label="fail", note="a negative number is not the count"),
    dict(name="hex", state=ans("0x29\n"), label="fail", note="hexadecimal"),
    dict(name="float", state=ans("41.0\n"), label="fail", note="decimal fraction notation"),
    dict(name="exponent", state=ans("4.1e1\n"), label="fail", note="exponent notation"),
    dict(name="underscore", state=ans("4_1\n"), label="fail", note="digit separator"),
    dict(name="comma", state=ans("4,1\n"), label="fail", note="digit separator"),
    dict(name="inner-space", state=ans("4 1\n"), label="fail", note="inner whitespace"),
    dict(name="two-lines", state=ans("41\n41\n"), label="fail", note="two integers"),
    dict(name="words-only", state=ans("forty-one\n"), label="fail", note="words, not a decimal integer"),
    dict(name="nul-after", state=ans("41\x00"), label="fail", note="NUL is not whitespace"),
    dict(name="nul-inside", state=ans("4\x001\n"), label="fail", note="NUL inside the digits"),
    dict(name="info-separator-1c", state=ans("41\x1c"), label="fail", grader="F4",
         note="U+001C is whitespace under neither reading (not POSIX [:space:], not Unicode White_Space)"),
    dict(name="info-separator-1f-leading", state=ans("\x1f41\n"), label="fail", grader="F4",
         note="U+001F before the digits"),
    dict(name="invalid-utf8", state=ans(b"41\xff\n"), label="fail", note="a byte that is not text"),
    dict(name="huge-wrong-number", state=ans("1" * 5000 + "\n"), label="fail",
         note="5,000 digits; verdict fail, see test_no_exception for the exception"),

    # ---- content-free responses (step 4) ----
    dict(name="instruction-restatement", state=ans(INSTRUCTION), label="fail",
         note="the instruction text copied into the answer file"),
    dict(name="repeated-count-one-line", state=ans("41 41 41\n"), label="fail", note="repeated text"),
    dict(name="repeated-count-lines", state=ans("41\n" * 100), label="fail", note="the count on 100 lines"),

    # ---- decision entries ----
    dict(name="leading-zero", state=ans("041\n"), label="pass", alt={"D-leading-zeros": "fail"}),
    dict(name="leading-zeros-5001-digits", state=ans("0" * 4999 + "41\n"), label="pass",
         alt={"D-leading-zeros": "fail"}, grader="D-leading-zeros",
         note="the grader fails it through an exception (F5), which reading B happens to match"),
    dict(name="plus-sign", state=ans("+41\n"), label="pass", alt={"D-plus-sign": "fail"}, grader="D-plus-sign"),
    dict(name="nbsp", state=ans("41 \n"), label="fail",
         alt={"D-whitespace": "pass", "D-surrounding-text": "pass"}, grader="D-whitespace"),
    dict(name="ideographic-space", state=ans("　41\n"), label="fail",
         alt={"D-whitespace": "pass", "D-surrounding-text": "pass"}, grader="D-whitespace"),
    dict(name="nel", state=ans("41\u0085"), label="fail", alt={"D-whitespace": "pass"}, grader="D-whitespace"),
    dict(name="arabic-indic-digits", state=ans("٤١\n"), label="fail", alt={"D-digits": "pass"}),
    dict(name="fullwidth-digits", state=ans("４１\n"), label="fail", alt={"D-digits": "pass"}),
    dict(name="words-after", state=ans("41 server errors\n"), label="fail", alt={"D-surrounding-text": "pass"},
         note="trial t09"),
    dict(name="words-before", state=ans("Total 5xx: 41\n"), label="fail", alt={"D-surrounding-text": "pass"},
         note="trial t17"),
    dict(name="label-colon", state=ans("count: 41\n"), label="fail", alt={"D-surrounding-text": "pass"}),
    dict(name="utf8-bom", state=ans(b"\xef\xbb\xbf41\n"), label="fail",
         alt={"D-bom": "pass", "D-surrounding-text": "pass"}),
    dict(name="utf16-bom", state=ans("41\n".encode("utf-16")), label="fail", alt={"D-bom": "pass"}),
    dict(name="symlink-in-workspace", state=[OUT_DIR, f("tmp/real.txt", "41\n"),
                                             link("out/answer.txt", "../tmp/real.txt")],
         label="pass", alt={"D-symlink": "fail"}, needs_symlink=True),
    dict(name="symlink-to-expected-json", state=[OUT_DIR, link("out/answer.txt", "{TESTS_DIR}/expected.json")],
         label="fail", alt={"D-surrounding-text": "pass"}, needs_symlink=True,
         note="a link to the grader's own key; under D-surrounding-text B its one integer is 41"),

    # ---- the verifier's environment (contract C1: it must not run what the agent wrote) ----
    dict(name="python3-shadowed-on-path", state=ans("37\n"), label="fail", grader="G1", env="fake-python3",
         note="a python3 that the agent left first on PATH (outside /workspace) prints 'correct' and exits 0"),
]

for fx in FIXTURES:
    fx.setdefault("check", CHECK)
    fx.setdefault("alt", {})
    fx.setdefault("grader", None)
    fx.setdefault("needs_symlink", False)
    fx.setdefault("env", None)
    fx.setdefault("note", "")
    canon = json.dumps({"check": fx["check"], "state": fx["state"], "env": fx["env"]}, sort_keys=True)
    fx["id"] = f"{fx['check']}:{hashlib.sha256(canon.encode()).hexdigest()[:16]}"

ids = [fx["id"] for fx in FIXTURES]
assert len(set(ids)) == len(ids), "duplicate fixture state"
names = [fx["name"] for fx in FIXTURES]
assert len(set(names)) == len(names), "duplicate fixture name"

FAKE_PYTHON3 = "#!/bin/sh\necho correct\nexit 0\n"
