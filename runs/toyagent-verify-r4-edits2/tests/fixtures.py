"""Labeled fixtures for check V (verifier verdict) and check S (reward and score), labeled from audit/CONTRACT.md.

Verifier fixture fields:
    name     short description
    files    sandbox state under /workspace (key ending in '/' with value None = directory)
    label    contract verdict under the proposed reading of every decision entry
    alt      {decision id: verdict under that entry's other reading}, for decision fixtures
    current  None when the current grader gets the label right; otherwise the finding or decision id(s)
             that explain its wrong verdict. These tests are expected failures (strict), so the change that
             fixes the grader must remove the mark.
Ids are computed from the state (harness.state_id), so they stay stable while the content does not change.
"""

INSTRUCTION = (
    b"The directory /workspace/logs holds the access logs of a web server: access.log, access.log.1 and "
    b"access.log.2.gz (gzip-compressed). Each line is one request, and the HTTP status code is the field right "
    b"after the quoted request.\n\nCount the requests in all three files whose status code is a server error (500 "
    b"to 599). Write the count as a decimal integer to /workspace/out/answer.txt.\n"
)


def A(content):
    """State with only /workspace/out/answer.txt."""
    return {"out/answer.txt": content}


VERIFIER = [
    # ---- passing controls
    dict(name="pass: 41 and LF", files=A(b"41\n"), label="pass"),
    dict(name="pass: 41, no newline", files=A(b"41"), label="pass"),
    dict(name="pass: 41 and CRLF", files=A(b"41\r\n"), label="pass"),
    dict(name="pass: spaces, tab, blank lines around 41", files=A(b"  41\t\n\n"), label="pass"),
    dict(name="pass: blank lines before 41", files=A(b"\n\n41\n"), label="pass"),
    dict(name="pass: unrelated files beside the answer", label="pass",
         files={"out/answer.txt": b"41\n", "answer.txt": b"37\n", "out/count.sh": b"zcat -f x | wc -l\n",
                "tmp/notes.txt": b"access.log: 20\n"}),
    dict(name="pass: leading zero 041", files=A(b"041\n"), label="pass", alt={"D-leading-zeros": "fail"}),
    dict(name="pass: 5000 leading zeros then 41", files=A(b"0" * 5000 + b"41\n"), label="pass",
         alt={"D-leading-zeros": "fail"}, current="D-leading-zeros"),
    # ---- failing controls the current grader gets right
    dict(name="fail: empty file", files=A(b""), label="fail"),
    dict(name="fail: whitespace only", files=A(b" \n\t\n"), label="fail"),
    dict(name="fail: 37 (gzip file skipped)", files=A(b"37\n"), label="fail"),
    dict(name="fail: 40 (awk $9 misses the quoted space)", files=A(b"40\n"), label="fail"),
    dict(name="fail: 36", files=A(b"36\n"), label="fail"),
    dict(name="fail: 44 (byte counts matched)", files=A(b"44\n"), label="fail"),
    dict(name="fail: 42", files=A(b"42\n"), label="fail"),
    dict(name="fail: 0", files=A(b"0\n"), label="fail"),
    dict(name="fail: -41", files=A(b"-41\n"), label="fail"),
    dict(name="fail: hexadecimal", files=A(b"0x29\n"), label="fail"),
    dict(name="fail: 41.0", files=A(b"41.0\n"), label="fail"),
    dict(name="fail: scientific", files=A(b"4.1e1\n"), label="fail"),
    dict(name="fail: underscore separator", files=A(b"4_1\n"), label="fail"),
    dict(name="fail: comma separator", files=A(b"4,1\n"), label="fail"),
    dict(name="fail: two lines of 41", files=A(b"41\n41\n"), label="fail"),
    dict(name="fail: words", files=A(b"forty-one\n"), label="fail"),
    dict(name="fail: text after the count", files=A(b"41 server errors\n"), label="fail",
         alt={"D-surrounding-text": "pass"}),
    dict(name="fail: text before the count", files=A(b"Total 5xx: 41\n"), label="fail",
         alt={"D-surrounding-text": "pass"}),
    dict(name="fail: plus sign", files=A(b"+41\n"), label="fail", alt={"D-plus-sign": "pass"}),
    dict(name="fail: full-width digits", files=A("４１\n".encode()), label="fail",
         alt={"D-nonascii-digits": "pass"}),
    dict(name="fail: Arabic-Indic digits", files=A("٤١\n".encode()), label="fail",
         alt={"D-nonascii-digits": "pass"}),
    dict(name="fail: UTF-8 BOM before 41", files=A(b"\xef\xbb\xbf41\n"), label="fail"),
    dict(name="fail: UTF-16 with BOM", files=A("41\n".encode("utf-16")), label="fail"),
    dict(name="fail: NUL after 41", files=A(b"41\x00\n"), label="fail"),
    dict(name="fail: invalid UTF-8 byte after 41", files=A(b"41\xff\n"), label="fail"),
    dict(name="fail: instruction restated", files=A(INSTRUCTION), label="fail"),
    dict(name="fail: 41 repeated 50 times", files=A(b"41\n" * 50), label="fail"),
    dict(name="fail: wrong count at /workspace/answer.txt", files={"answer.txt": b"37\n"}, label="fail"),
    # ---- the current grader gets these wrong
    dict(name="fail: empty sandbox", files={}, label="fail", current="F1"),
    dict(name="fail: empty out/ directory", files={"out/": None}, label="fail", current="F1"),
    dict(name="fail: notes only, no answer file", files={"tmp/notes.txt": b"access.log: 20\naccess.log.1: 17\n"},
         label="fail", current="F1"),
    dict(name="fail: answer written to tmp/answer.txt", files={"tmp/answer.txt": b"41\n"}, label="fail",
         current="F1"),
    dict(name="fail: out/answer.txt is a directory", files={"out/answer.txt/": None}, label="fail", current="F1"),
    dict(name="fail: correct count at /workspace/answer.txt", files={"answer.txt": b"41\n"}, label="fail",
         current="F2"),
    dict(name="fail: correct count at /workspace/answer.txt, empty out/", files={"out/": None, "answer.txt": b"41\n"},
         label="fail", current="F2"),
    # U+001C..U+001F are whitespace to Python's str.strip() but not under either reading of D-whitespace (ASCII
    # whitespace, or the Unicode White_Space property); only D-surrounding-text's other reading makes "pass" right.
    dict(name="fail: information separator U+001F after 41", files=A(b"41\x1f\n"), label="fail",
         alt={"D-surrounding-text": "pass", "D-whitespace": "fail"}, current="D-surrounding-text"),
    dict(name="fail: file separator U+001C before 41", files=A(b"\x1c41\n"), label="fail",
         alt={"D-surrounding-text": "pass", "D-whitespace": "fail"}, current="D-surrounding-text"),
    dict(name="fail: no-break space U+00A0 after 41", files=A("41 \n".encode()), label="fail",
         alt={"D-whitespace": "pass", "D-surrounding-text": "pass"}, current="D-whitespace|D-surrounding-text"),
    dict(name="fail: ideographic space U+3000 before 41", files=A("　41\n".encode()), label="fail",
         alt={"D-whitespace": "pass", "D-surrounding-text": "pass"}, current="D-whitespace|D-surrounding-text"),
    dict(name="fail: next line U+0085 after 41", files=A("41\u0085\n".encode()), label="fail",
         alt={"D-whitespace": "pass", "D-surrounding-text": "pass"}, current="D-whitespace|D-surrounding-text"),
]

# ---- check S: result.json records -> per-configuration (trials, passed, score)
_C = "agentx+test"


def R(code, status="completed", **extra):
    rec = {"trial_id": "x", "task": "count-server-errors", "config": _C, "agent_status": status,
           "agent_error": None, "agent_steps": 5, "verifier_exit_code": code, "verifier_output": ""}
    rec.update(extra)
    return rec


def R_missing_code():
    rec = R(0)
    del rec["verifier_exit_code"]
    return rec


SCORER = [
    dict(name="exit 0 passes", trials={"a": R(0)}, label={_C: (1, 1, 100.0)}),
    dict(name="exit 1 fails", trials={"a": R(1)}, label={_C: (1, 0, 0.0)}),
    dict(name="exit 2 fails", trials={"a": R(2)}, label={_C: (1, 0, 0.0)}),
    dict(name="exit 127 fails", trials={"a": R(127)}, label={_C: (1, 0, 0.0)}),
    dict(name="signal exit -9 fails", trials={"a": R(-9)}, label={_C: (1, 0, 0.0)}),
    dict(name="timeout with exit 0 passes", trials={"a": R(0, "timeout")}, label={_C: (1, 1, 100.0)}),
    dict(name="agent error with exit 1 fails", trials={"a": R(1, "error")}, label={_C: (1, 0, 0.0)}),
    dict(name="two configurations kept apart",
         trials={"a": R(0), "b": R(1, config="agentx+other")},
         label={_C: (1, 1, 100.0), "agentx+other": (1, 0, 0.0)}),
    dict(name="verifier did not run (null) fails", trials={"a": R(None, "error")}, label={_C: (1, 0, 0.0)},
         current="F3"),
    dict(name="verifier_exit_code field missing fails", trials={"a": R_missing_code()}, label={_C: (1, 0, 0.0)},
         current="F3"),
    dict(name="null stays in the denominator as a fail", trials={"a": R(0), "b": R(1), "c": R(None, "error")},
         label={_C: (3, 1, 33.3)}, current="F3"),
]
