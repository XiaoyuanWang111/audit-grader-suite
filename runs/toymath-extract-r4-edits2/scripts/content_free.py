"""Grade content-free responses on all 12 problems with all three graders (step 4).

Run from W:  python -B audit/scripts/content_free.py
Prints, per content-free response, the problems on which each grader says `correct`.
"""
import pathlib
import sys

sys.dont_write_bytecode = True
W = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W / "audit" / "tests"))

import fixtures  # noqa: E402
import harness  # noqa: E402

KINDS = {
    "empty": lambda pid: "",
    "whitespace": lambda pid: " \n\t\n ",
    "repeated-text": lambda pid: "I will think about this carefully. " * 40,
    "prompt-restated": lambda pid: fixtures.rendered_prompt(pid),
    "problem-restated": lambda pid: fixtures.PROBLEMS[pid]["problem"],
    "answer-template": lambda pid: "Answer: <number>",
    "label-only": lambda pid: "Answer:",
}


def main():
    items = []
    for kind, build in KINDS.items():
        for pid in sorted(fixtures.PROBLEMS):
            items.append({"id": f"{kind}|{pid}", "problem_id": pid, "response": build(pid), "kind": kind})
    res = harness.grade_all(items, "content_free")
    print(f"{'response':<18}{'grader labels':<26}{'reference labels':<26}{'replacement labels':<26}passes (correct)")
    for kind in KINDS:
        rows = [it for it in items if it["kind"] == kind]
        line = f"{kind:<18}"
        passes = []
        for g in ("grader", "reference", "replacement"):
            labs = sorted({res[it['id']][g] for it in rows})
            line += f"{'/'.join(labs):<26}"
            passes += [f"{g}:{it['problem_id']}" for it in rows if res[it["id"]][g] == "correct"]
        print(line + (", ".join(passes) or "none"))


if __name__ == "__main__":
    main()
