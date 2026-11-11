"""Run every fixture on grader A, grader B and the replacement; print the verdict table and mismatches.

Usage: python audit/scripts/run_fixtures.py [--all]
"""
import sys
from pathlib import Path

W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W / "audit" / "lib"))
sys.path.insert(0, str(W / "audit" / "tests"))

import contract_grader as cg  # noqa: E402
import graders_under_audit as gu  # noqa: E402
from fixtures import FIXTURES  # noqa: E402


def show(v):
    return {True: "pass", False: "fail", None: "-"}.get(v, "ERR") if not isinstance(v, str) else "ERR"


def main():
    show_all = "--all" in sys.argv
    problems = 0
    for f in FIXTURES:
        a = gu.check_a(f["check"], f["kwargs"], gu.extract_a(f["response"]))
        b = gu.check_b(f["check"], f["kwargs"], gu.extract_b(f["response"]))
        rr = cg.check(f["check"], f["kwargs"], f["response"], None, f["ctx"])
        flips = {}
        for d in f["flip"]:
            flips[d] = cg.check(f["check"], f["kwargs"], f["response"], {d: "B"}, f["ctx"])
        label = f["label"]
        a_ok = a is label
        b_ok = b is None or b is label
        r_ok = rr is label and all(v is (not label) for v in flips.values())
        expect_a = "A" in f["wrong"]
        expect_b = "B" in f["wrong"]
        flag = []
        if not r_ok:
            flag.append("REPLACEMENT")
        if a_ok == expect_a:
            flag.append("A-mark")
        if b_ok == expect_b and b is not None:
            flag.append("B-mark")
        if flag:
            problems += 1
        if flag or show_all:
            print(f"{f['id']:<28} {f['check']:<45} label={show(label)} A={show(a)} B={show(b)} R={show(rr)} "
                  f"flips={ {k: show(v) for k, v in flips.items()} } wrong={f['wrong']} {' '.join(flag)}")
            print("    response:", repr(f["response"])[:110], " A-raw:", a if isinstance(a, str) else "")
    print("fixtures:", len(FIXTURES), "rows needing attention:", problems)


if __name__ == "__main__":
    main()
