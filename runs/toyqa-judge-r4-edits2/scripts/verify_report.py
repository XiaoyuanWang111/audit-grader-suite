"""Run every `python -B ...` command that audit/AUDIT.md gives and check it prints what the report says.

Usage (from W):  python -B audit/scripts/verify_report.py
Every command found in AUDIT.md must have a check below, and every check must match a command in AUDIT.md.
"""
import json
import pathlib
import re
import shlex
import subprocess
import sys

W = pathlib.Path(__file__).resolve().parents[2]
OUT = "audit/tests/_out/"


def labels(path):
    return {json.loads(l)["id"]: json.loads(l) for l in (W / path).read_text(encoding="utf-8").splitlines() if l}


def row_tokens(stdout, model):
    return next(l.split() for l in stdout.splitlines() if l.startswith(model + " "))


CHECKS = {
    "python -B case/judge_pipeline.py --judge fake --responses audit/tests/data/f1_unclosed_think.jsonl --out audit/tests/_out/f1_grader.jsonl":
        lambda p: p.returncode == 0 and row_tokens(p.stdout, "m")[1:6] == ["0", "0", "1", "0", "0"]
        and labels(OUT + "f1_grader.jsonl")["f1"]["label"] == "not_attempted",
    "python -B case/reference/pipeline_ref.py case/questions.jsonl audit/tests/data/f1_unclosed_think.jsonl fake audit/tests/_out/f1_ref.jsonl":
        lambda p: p.returncode == 0 and labels(OUT + "f1_ref.jsonl")["f1"]["label"] == "extraction_failure",
    "python -B case/judge_pipeline.py --responses audit/tests/data/f1_stored.jsonl --out audit/tests/_out/f1_stored_grader.jsonl":
        lambda p: p.returncode == 0 and {k: v["label"] for k, v in labels(OUT + "f1_stored_grader.jsonl").items()}
        == {"a08": "not_attempted", "a20": "not_attempted", "a40": "not_attempted"},
    "python -B -c \"import sys, json; sys.path.insert(0, 'case'); import judge_pipeline as g; q = json.loads(open('case/questions.jsonl').readline()); print(repr(g.render_prompt(g.load_template(), q, 'Let me answer.\\nCanberra').split('<<<\\n')[1].split('\\n>>>')[0]))\"":
        lambda p: p.returncode == 0 and p.stdout.strip() == "'Let me answer.'",
    "python -B case/judge_pipeline.py --judge fake --responses audit/tests/data/f2_second_line.jsonl --out audit/tests/_out/f2_grader.jsonl":
        lambda p: p.returncode == 0 and labels(OUT + "f2_grader.jsonl")["f2"]["label"] == "incorrect",
    "python -B case/reference/pipeline_ref.py case/questions.jsonl audit/tests/data/f2_second_line.jsonl fake audit/tests/_out/f2_ref.jsonl":
        lambda p: p.returncode == 0 and labels(OUT + "f2_ref.jsonl")["f2"]["label"] == "correct",
    "python -B case/judge_pipeline.py --judge fake --responses audit/tests/data/empty_in_batch.jsonl":
        lambda p: p.returncode == 1 and p.stdout == "" and "IndexError: list index out of range" in p.stderr
        and "line 57" in p.stderr,
    "python -B case/reference/pipeline_ref.py case/questions.jsonl audit/tests/data/empty_in_batch.jsonl fake audit/tests/_out/empty_ref.jsonl":
        lambda p: p.returncode == 0 and [v["label"] for v in labels(OUT + "empty_ref.jsonl").values()]
        == ["correct", "not_attempted", "correct"],
    "python -B -c \"import sys; sys.path.insert(0, 'case'); import judge_pipeline as g; print(g.parse_grade('A liver is not skin. B'))\"":
        lambda p: p.returncode == 0 and p.stdout.strip() == "A",
    "python -B case/judge_pipeline.py --responses audit/tests/data/f4_a24.jsonl --out audit/tests/_out/f4_a24_grader.jsonl":
        lambda p: p.returncode == 0 and (labels(OUT + "f4_a24_grader.jsonl")["a24"]["label"],
                                         labels(OUT + "f4_a24_grader.jsonl")["a24"]["grade"]) == ("correct", "A"),
    "python -B case/reference/pipeline_ref.py case/questions.jsonl audit/tests/data/f4_a24.jsonl recorded audit/tests/_out/f4_a24_ref.jsonl":
        lambda p: p.returncode == 0 and labels(OUT + "f4_a24_ref.jsonl")["a24"]["label"] == "incorrect",
    "python -B case/judge_pipeline.py --responses audit/tests/data/f4_stored.jsonl --out audit/tests/_out/f4_stored_grader.jsonl":
        lambda p: p.returncode == 0 and {k: v["label"] for k, v in labels(OUT + "f4_stored_grader.jsonl").items()}
        == {"a09": "correct", "a16": "not_attempted", "a22": "not_attempted", "a24": "correct",
            "a32": "not_attempted", "a34": "incorrect", "a35": "incorrect"},
    "python -B case/judge_pipeline.py --responses audit/tests/data/unrecorded_prompt.jsonl":
        lambda p: p.returncode == 1 and p.stdout == "" and "LookupError: no recorded reply" in p.stderr,
    "python -B -m unittest discover -s audit/tests -t audit/tests":
        lambda p: p.returncode == 0 and "Ran 215 tests" in p.stderr and "OK (expected failures=34)" in p.stderr,
    "python -B audit/scripts/fuzz.py":
        lambda p: p.returncode == 0 and all(s in p.stdout for s in (
            "grader 1655, reference 0", "exceptions 633 {'IndexError': 633}", "replacement's 851",
            "reference: exceptions 0 ; prompt differs from the replacement's 98", "reading (a): 0 differ")),
    "python -B audit/scripts/panel.py":
        lambda p: p.returncode == 0 and all(s in p.stdout for s in (
            "G vs X: 10 of 48", "G vs R: 10 of 48", "R vs X: 0 of 48", "1 of 33 distinct prompts flip",
            "puffin-13b       accuracy [-41.7, +0.0]", "used but unrecorded 0",
            "{'G': 48, 'R': 48, 'X': 48, 'X_full': 46}")),
    "python -B audit/scripts/freeze_sample.py": None,  # rewrites the frozen files; checked through SHA256SUMS below
}


def report_commands():
    text = (W / "audit" / "AUDIT.md").read_text(encoding="utf-8")
    cmds = set(re.findall(r"`(python -B [^`]+)`", text))
    for block in re.findall(r"```text\n(.*?)\n```", text, re.S):
        cmds.update(l for l in block.splitlines() if l.startswith("python -B"))
    return cmds


def main():
    cmds = report_commands()
    missing = cmds - set(CHECKS)
    unused = set(CHECKS) - cmds
    ok = not missing and not unused
    for c in sorted(missing):
        print("NO CHECK for report command:", c)
    for c in sorted(unused):
        print("check without a report command:", c)
    for cmd, check in CHECKS.items():
        if check is None:
            continue
        args = shlex.split(cmd)
        args[0] = sys.executable
        p = subprocess.run(args, cwd=W, capture_output=True, text=True, encoding="utf-8",
                           env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
        good = bool(check(p))
        ok &= good
        print("OK  " if good else "FAIL", cmd[:110])
        if not good:
            print("   exit", p.returncode, "| stdout:", p.stdout[-300:], "| stderr:", p.stderr[-300:])
    sums = (W / "audit" / "frozen" / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
    import hashlib
    bad = [l for l in sums if hashlib.sha256((W / "audit" / "frozen" / l.split("  ", 1)[1]).read_bytes()).hexdigest()
           != l.split("  ", 1)[0]]
    print(("OK  " if not bad else "FAIL"), f"audit/frozen/SHA256SUMS: {len(sums) - len(bad)} of {len(sums)} files match")
    ok &= not bad
    print("ALL OK" if ok else "SOME CHECKS FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
