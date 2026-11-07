"""Enumerate every combination of the file states that verify.sh branches on, and grade each one with the whole
verify.sh and with the replacement (step 4, in place of random fuzzing for the bash wrapper).

States: /workspace/out present or absent; out/answer.txt absent, "41\\n", "37\\n", empty, or a directory;
/workspace/answer.txt absent, "41\\n", "37\\n", or a directory. 24 states (out/answer.txt needs /workspace/out).

Usage: python -I audit/scripts/enumerate_states.py     Writes audit/results/enumerate_states.json.
"""

import collections
import concurrent.futures
import json
import os
import pathlib
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import grader_runner as GR  # noqa: E402
import replacement_verifier as RV  # noqa: E402

ANSWER = {"absent": None, "41": b"41\n", "37": b"37\n", "empty": b"", "dir": "dir"}
ROOT_ANSWER = {"absent": None, "41": b"41\n", "37": b"37\n", "dir": "dir"}


def entries(path, value):
    if value is None:
        return []
    if value == "dir":
        return [{"path": path, "kind": "dir"}]
    return [{"path": path, "kind": "file", "hex": value.hex()}]


def states():
    for out_dir in ("present", "absent"):
        for a in (ANSWER if out_dir == "present" else {"absent": None}):
            for r in ROOT_ANSWER:
                st = ([{"path": "out", "kind": "dir"}] if out_dir == "present" else [])
                st += entries("out/answer.txt", ANSWER[a]) + entries("answer.txt", ROOT_ANSWER[r])
                yield {"out_dir": out_dir, "out/answer.txt": a, "answer.txt": r}, st


def run(desc, st):
    root = GR.new_tmpdir("state_")
    try:
        ws = GR.build_workspace(st, root)
        code, out = GR.run_verify_sh(ws)
        verdict, reason = RV.grade_workspace(str(ws))
        return dict(desc, grader_exit=code, grader_output=out, grader="pass" if code == 0 else "fail",
                    replacement=verdict, replacement_reason=reason)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def main():
    with concurrent.futures.ThreadPoolExecutor(max_workers=int(os.environ.get("AUDIT_WORKERS", "6"))) as ex:
        rows = list(ex.map(lambda s: run(*s), list(states())))
    summary = collections.Counter()
    for r in rows:
        if r["grader"] == r["replacement"]:
            summary["agree"] += 1
        elif r["grader_output"] == "no answer file":
            summary["grader pass on 'no answer file' (F1)"] += 1
        elif r["out/answer.txt"] in ("absent", "dir") and r["answer.txt"] == "41":
            summary["grader pass from /workspace/answer.txt (F2)"] += 1
        else:
            summary["other disagreement"] += 1
    result = {"states": len(rows), "summary": dict(summary), "rows": rows}
    out = GR.AUDIT / "results" / "enumerate_states.json"
    out.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8", newline="\n")
    for r in rows:
        print(f"out={r['out_dir']:<7} out/answer.txt={r['out/answer.txt']:<6} answer.txt={r['answer.txt']:<6} "
              f"grader={r['grader']} ({r['grader_output'][:24]!r}) replacement={r['replacement']}")
    print(json.dumps(result["summary"]))


if __name__ == "__main__":
    main()
