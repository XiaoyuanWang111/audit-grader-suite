"""Regenerate the fuzz inputs (same seed and generators as fuzz_verifier.py) and
check that every defect input (the grader passes, every combination of
readings fails) contains one of U+001C..U+001F.

    python -I audit/scripts/check_fuzz_defects.py
"""

import contextlib
import io
import itertools
import os
import random
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(os.path.dirname(HERE), "replacement")]

import common  # noqa: E402
import fuzz_verifier as fz  # noqa: E402
import replacement_verifier as rv  # noqa: E402

SEPARATORS = set("\x1c\x1d\x1e\x1f")


def main():
    common.require_pins("before defect check")
    check_main = common.load_check_answer_main()
    expected = os.path.join(common.TESTS_DIR, "expected.json")
    names = sorted(rv.CHOICES)
    combos = [dict(zip(names, v)) for v in itertools.product(*(rv.CHOICES[k] for k in names))]
    rng = random.Random(fz.SEED)
    defects = with_sep = 0
    others = []
    with tempfile.TemporaryDirectory(prefix="fd_") as ws:
        os.makedirs(os.path.join(ws, "out"))
        path = os.path.join(ws, "out", "answer.txt")
        for _gname, gen in fz.GENERATORS.items():
            for _ in range(fz.PER_GENERATOR):
                data = gen(rng)
                with open(path, "wb") as f:
                    f.write(data)
                try:
                    with contextlib.redirect_stdout(io.StringIO()):
                        g = "pass" if check_main(["check_answer.py", path, expected]) == 0 else "fail"
                except Exception:
                    g = "fail"
                if g != "pass" or rv.grade(ws, 41)[0] == "pass":
                    continue
                if any(rv.grade(ws, 41, cb)[0] == "pass" for cb in combos):
                    continue
                defects += 1
                if SEPARATORS & set(data.decode("utf-8", "replace")):
                    with_sep += 1
                else:
                    others.append(data)
    common.require_pins("after defect check")
    print(f"defect inputs {defects}; containing U+001C..U+001F {with_sep}; others {others[:5]}")


if __name__ == "__main__":
    main()
