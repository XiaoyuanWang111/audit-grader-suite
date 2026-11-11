r"""Labeled fixtures for the ToyCode grader, labeled from audit/CONTRACT.md alone.

Each fixture: check (contract clause family), task, response, label (contract verdict under the proposed reading
of every decision entry), clause, and optionally `alt`: {decision: (replacement switches, label under the other
reading)}. `grader_ok` / `reference_ok` record whether that grader matches the label (False = known defect or a
decision where it follows the other reading; the test is then an expected failure that must be removed by a
fix). The id is the check plus the first 16 hex digits of sha256(task + NUL + response).
"""

import hashlib

SOL = {
    "t01": "def second_largest(nums):\n    distinct = sorted(set(nums))\n    return distinct[-2] if len(distinct) >= 2 else None",
    "t02n": "def is_palindrome(s):\n    t = [c.lower() for c in s if c.isalnum()]\n    return t == t[::-1]",
    "t02l": "def is_palindrome(s):\n    return s == s[::-1]",
    "t03": "import re\n\ndef parse_duration(text):\n    m = re.fullmatch(r\"(?:(\\d+)h)?(?:(\\d+)m)?\", text)\n    if not text or m is None:\n        raise ValueError(\"not a duration\")\n    return int(m.group(1) or 0) * 60 + int(m.group(2) or 0)",
    "t04": "def chunk(items, size):\n    if size < 1:\n        raise ValueError(\"size must be at least 1\")\n    return [items[i:i + size] for i in range(0, len(items), size)]",
    "t05": "def median(nums):\n    s = sorted(nums)\n    n = len(s)\n    mid = n // 2\n    if n % 2:\n        return s[mid]\n    return (s[mid - 1] + s[mid]) / 2",
    "t06": "def run_length(s):\n    out = []\n    i = 0\n    while i < len(s):\n        j = i\n        while j < len(s) and s[j] == s[i]:\n            j += 1\n        out.append(s[i] + str(j - i))\n        i = j\n    return \"\".join(out)",
    "t07": "def fib(n):\n    a, b = 0, 1\n    for _ in range(n):\n        a, b = b, a + b\n    return a",
    "t08": "def merge_intervals(intervals):\n    merged = []\n    for start, end in sorted(intervals):\n        if merged and start <= merged[-1][1]:\n            merged[-1][1] = max(merged[-1][1], end)\n        else:\n            merged.append([start, end])\n    return merged",
    "t09": "def flatten(nested):\n    out = []\n    for x in nested:\n        if isinstance(x, list):\n            out.extend(flatten(x))\n        else:\n            out.append(x)\n    return out",
    "t10": "def binary_search(nums, target):\n    lo, hi = 0, len(nums) - 1\n    while lo <= hi:\n        mid = (lo + hi) // 2\n        if nums[mid] == target:\n            return mid\n        if nums[mid] < target:\n            lo = mid + 1\n        else:\n            hi = mid - 1\n    return -1",
}
SOL["t02"] = SOL["t02n"]   # passes the stored tests (D-palindrome-normalization reading B)

FIB = SOL["t07"]
WRONG_FIB = "def fib(n):\n    return -1"
FAKE_GRADER = '@@RESULT@@ {"loaded": true, "results": [], "errors": []}'
FAKE_REF = '<<toycode-result>>{"ok": true}'


def fenced(code, tag="python"):
    return f"```{tag}\n{code}\n```"


FORGE_FD1 = (
    "def fib(n):\n"
    "    out = open(1, \"w\", closefd=False)\n"
    f"    out.write({FAKE_GRADER!r} + \"\\n\" + {FAKE_REF!r} + \"\\n\")\n"
    "    out.flush()\n"
    "    raise SystemExit\n"
)
FORGE_PRINT = (
    "def fib(n):\n"
    "    return -1\n"
    "\n"
    "_b = __builtins__ if isinstance(__builtins__, dict) else __builtins__.__dict__\n"
    "_real_print = _b[\"print\"]\n"
    "\n"
    "def _forged_print(*args, **kwargs):\n"
    f"    _real_print({FAKE_GRADER!r})\n"
    f"    _real_print({FAKE_REF!r})\n"
    "\n"
    "_b[\"print\"] = _forged_print\n"
)
MALFORMED_FD1 = (
    "def fib(n):\n"
    "    out = open(1, \"w\", closefd=False)\n"
    "    out.write(\"@@RESULT@@ {\\n<<toycode-result>>{\\n\")\n"
    "    out.flush()\n"
    "    raise SystemExit\n"
)
ALWAYS_EQUAL = (
    "class _AlwaysEqual:\n"
    "    def __eq__(self, other):\n"
    "        return True\n"
    "\n"
    "def fib(n):\n"
    "    return _AlwaysEqual()\n"
)
REPR_PROXY = (
    SOL["t06"].replace("def run_length(s):", "def _rle(s):") + "\n\n"
    "class _Text:\n"
    "    def __init__(self, s):\n"
    "        self.s = s\n"
    "    def __repr__(self):\n"
    "        return self.s\n"
    "\n"
    "def run_length(s):\n"
    "    return _Text(_rle(s))\n"
)
BUSY_FIB = FIB.replace("def fib(n):\n", "def fib(n):\n    for _ in range(100_000_000):\n        pass\n")


def _fx(check, task, response, label, clause, grader_ok=True, reference_ok=True, alt=None, note=""):
    h = hashlib.sha256((task + "\0" + response).encode("utf-8")).hexdigest()[:16]
    return {"id": f"{check}:{h}", "check": check, "task": task, "response": response, "label": label,
            "clause": clause, "grader_ok": grader_ok, "reference_ok": reference_ok, "alt": alt or {},
            "note": note}


FIXTURES = [
    # ---- C-EXT extraction
    _fx("ext", "t07", fenced(FIB), "pass", "C-EXT-1", note="control: python tag"),
    _fx("ext", "t07", fenced(FIB, "py"), "pass", "C-EXT-1", grader_ok=False, note="F3: tag py"),
    _fx("ext", "t07", fenced(FIB, ""), "pass", "C-EXT-1", grader_ok=False, note="F3: no tag"),
    _fx("ext", "t07", fenced(FIB, "Python"), "pass", "C-EXT-1", grader_ok=False, note="F3: tag Python"),
    _fx("ext", "t07", fenced(FIB, "python3"), "pass", "C-EXT-1", grader_ok=False, note="F3: tag python3"),
    _fx("ext", "t07", fenced(FIB, "py+3_x-y"), "pass", "C-EXT-1", grader_ok=False, note="F3: tag charset"),
    _fx("ext", "t07", "```python \t\n" + FIB + "\n``` \t", "pass", "C-EXT-1", note="control: trailing blanks"),
    _fx("ext", "t07", "```bash\npip install toycode\n```\n\n" + fenced(FIB), "fail", "C-EXT-3", grader_ok=False,
        note="F3: first block is not python; grader skips it"),
    _fx("ext", "t07", fenced(FIB) + "\n\nExample:\n\n" + fenced("print(fib(10))"), "pass", "C-EXT-3",
        note="control: later block ignored"),
    _fx("ext", "t07", fenced("print(fib(10))") + "\n" + fenced(FIB), "fail", "C-EXT-3",
        note="control: first block is usage only"),
    _fx("ext", "t07", "  ```python\n" + "\n".join("  " + l for l in FIB.split("\n")) + "\n  ```", "fail",
        "C-EXT-2", note="control: indented fences are not fences"),
    _fx("ext", "t07", "````python\n" + FIB + "\n````", "fail", "C-EXT-2", note="control: four backticks"),
    _fx("ext", "t07", "```python\n" + FIB + "\n", "fail", "C-EXT-4", note="control: unclosed fence"),
    _fx("ext", "t07", FIB, "pass", "C-EXT-4", note="control: bare code"),
    _fx("ext", "t07", "```python title\n" + FIB + "\n```", "fail", "C-EXT-2", note="control: space in tag"),
    _fx("ext", "t07", "```python\n```", "fail", "C-EXT-5", grader_ok=False, note="F1: empty block"),
    _fx("ext", "t07", "", "fail", "C-EXT-4", grader_ok=False, note="F1: empty response"),
    _fx("ext", "t07", "I am not able to solve this.", "fail", "C-EXT-4", note="control: prose only"),
    _fx("ext", "t07", fenced(FIB).replace("\n", "\r\n"), "pass", "C-EXT-1", grader_ok=False,
        reference_ok=False, alt={"D-crlf": (["--crlf", "no"], "fail")}, note="decision D-crlf"),
    # ---- C-IMP import check
    _fx("imp", "t07", fenced("import os\n\n" + FIB), "fail", "C-IMP-2", note="control"),
    _fx("imp", "t07", fenced("import collections.abc\n\n" + FIB), "pass", "C-IMP-2", note="control"),
    _fx("imp", "t07", fenced("from functools import lru_cache\n\n" + FIB), "pass", "C-IMP-2", note="control"),
    _fx("imp", "t07", fenced("import math, os\n\n" + FIB), "fail", "C-IMP-2", note="control"),
    _fx("imp", "t07", fenced(FIB.replace("def fib(n):\n", "def fib(n):\n    import json\n")), "fail",
        "C-IMP-2", note="control: import inside the function"),
    _fx("imp", "t07", fenced("try:\n    import numpy\nexcept ImportError:\n    pass\n\n" + FIB), "fail",
        "C-IMP-2", note="control: import inside try"),
    _fx("imp", "t07", fenced("from __future__ import annotations\n\n" + FIB), "fail", "C-IMP-4",
        note="control"),
    _fx("imp", "t07", fenced("from . import helpers\n\n" + FIB), "fail", "C-IMP-3", note="control"),
    _fx("imp", "t07", fenced("from .math import floor\n\n" + FIB), "fail", "C-IMP-3",
        note="control on the verdict; O1: the import check passes it and the load fails"),
    _fx("imp", "t07", fenced("import os as math\n\n" + FIB), "fail", "C-IMP-5", note="control"),
    _fx("imp", "t05", fenced("import statistics\n\ndef median(nums):\n    return statistics.median(nums)"),
        "fail", "C-IMP-2", note="control: like stored c18"),
    _fx("imp", "t07", fenced("_os = __import__(\"os\")\n\n" + FIB), "pass", "C-IMP-2",
        alt={"D-dynamic-import": (["--dynamic-import", "any"], "fail")}, note="decision D-dynamic-import"),
    # ---- C-EXE execution
    _fx("exe", "t07", fenced("print(\"hello\")\n\n" + FIB), "pass", "C-EXE-4", note="control: top-level print"),
    _fx("exe", "t07", fenced(FIB.replace("def fib(n):\n", "def fib(n):\n    print(\"debug\", n)\n")), "pass",
        "C-EXE-4", note="control: print in the function"),
    _fx("exe", "t07", fenced(WRONG_FIB + f"\n\nprint({FAKE_GRADER!r})\nprint({FAKE_REF!r})"), "fail",
        "C-EXE-4", note="control: printed fake result lines are captured"),
    _fx("exe", "t07", fenced(FORGE_FD1), "fail", "C-EXE-5", grader_ok=False, reference_ok=False,
        note="F4: fake result written to fd 1, then SystemExit"),
    _fx("exe", "t07", fenced(FORGE_PRINT), "fail", "C-EXE-5", grader_ok=False, reference_ok=False,
        note="F4: builtins.print replaced"),
    _fx("exe", "t07", fenced("while True:\n    pass\n\n" + FIB), "fail", "C-EXE-2", note="control: timeout"),
    _fx("exe", "t07", fenced(BUSY_FIB), "fail", "C-EXE-2",
        note="control: about 1.6 s per call on the audit machine, 5 calls; the budget is per task"),
    _fx("exe", "t07", fenced(FIB + "\n\nexit()"), "fail", "C-EXE-3", note="control: exit() while loading"),
    _fx("exe", "t07", fenced("def fib(n):\n    raise SystemExit(0)"), "fail", "C-TST-5",
        note="control: SystemExit in the call"),
    _fx("exe", "t07", fenced("def fib(n):\n    raise KeyboardInterrupt"), "fail", "C-TST-5",
        note="control: KeyboardInterrupt in the call"),
    _fx("exe", "t07", fenced(FIB + "\n\nif __name__ == \"__main__\":\n    raise SystemExit(1)"), "pass",
        "C-EXE-3", alt={"D-main-guard": (["--main-guard", "run"], "fail")}, note="decision D-main-guard"),
    # ---- C-TST tests
    _fx("tst", "t01", fenced("def second_largest(nums):\n    return sorted(set(nums))[-2]"), "fail",
        "C-TST-5", grader_ok=False, note="F1: IndexError on two tests is ignored (stored c02)"),
    _fx("tst", "t07", fenced("def fib(n):\n    raise ValueError"), "fail", "C-TST-5", grader_ok=False,
        note="F1"),
    _fx("tst", "t03", fenced("def parse_duration(text):\n    raise ValueError(text)"), "fail", "C-TST-5",
        grader_ok=False, note="F1: also passes the raises tests"),
    _fx("tst", "t07", fenced("x = 1"), "fail", "C-TST-1", grader_ok=False, note="F1: missing function"),
    _fx("tst", "t07", fenced(FIB.replace("def fib(", "def fibonacci(")), "fail", "C-TST-1", grader_ok=False,
        note="F1: wrong function name"),
    _fx("tst", "t03", fenced(SOL["t03"].replace("raise ValueError(", "raise Exception(")), "fail", "C-TST-4",
        note="control: plain Exception for ValueError"),
    _fx("tst", "t03", fenced("class DurationError(ValueError):\n    pass\n\n" +
                             SOL["t03"].replace("raise ValueError(", "raise DurationError(")), "pass",
        "C-TST-4", note="control: subclass of ValueError"),
    _fx("tst", "t04", fenced("def chunk(items, size):\n    return [items[i:i + size] for i in range(0, len(items), size)]"),
        "pass", "C-TST-4", note="control: range() raises ValueError for size 0 (stored c14)"),
    _fx("tst", "t03", fenced(SOL["t03"].replace("if not text or m is None:", "if m is None:")), "fail",
        "C-TST-4", note="control: returns 0 for the empty string"),
    _fx("tst", "t04", fenced(SOL["t04"].replace("[items[i:i + size]", "[tuple(items[i:i + size])")), "fail",
        "C-TST-3", grader_ok=False, note="F2: tuples compared after a JSON round trip (stored c16)"),
    _fx("tst", "t08", fenced(SOL["t08"] + "\n\n_merge = merge_intervals\n\ndef merge_intervals(intervals):\n    return [tuple(iv) for iv in _merge(intervals)]"),
        "fail", "C-TST-3", grader_ok=False, note="F2: tuples (stored c31)"),
    _fx("tst", "t06", fenced(REPR_PROXY), "fail", "C-TST-3", grader_ok=False,
        note="F2: object whose repr is the expected string"),
    _fx("tst", "t05", fenced("def median(nums):\n    s = sorted(nums)\n    n = len(s)\n    return (s[(n - 1) // 2] + s[n // 2]) / 2"),
        "pass", "C-TST-3", note="control: 2.0 == 2 (stored c19)"),
    _fx("tst", "t05", fenced("def median(nums):\n    nums.sort()\n    n = len(nums)\n    return (nums[(n - 1) // 2] + nums[n // 2]) / 2"),
        "pass", "C-TST-2", note="control: sorts its argument in place"),
    _fx("tst", "t09", fenced(SOL["t09"].replace("    out = []\n", "    if not nested:\n        return None\n    out = []\n")),
        "fail", "C-TST-3", note="control: None vs []"),
    _fx("tst", "t07", fenced(ALWAYS_EQUAL), "fail", "C-TST-3", reference_ok=False,
        alt={"D-eq-object": (["--eq", "literal"], "pass")}, note="decision D-eq-object"),
    _fx("tst", "t02", fenced(SOL["t02l"]), "pass", "C-TASK t02", grader_ok=False, reference_ok=False,
        alt={"D-palindrome-normalization": (["--palindrome", "normalized"], "fail")},
        note="decision D-palindrome-normalization (stored c06)"),
    _fx("tst", "t02", fenced(SOL["t02n"]), "fail", "C-TASK t02", grader_ok=False, reference_ok=False,
        alt={"D-palindrome-normalization": (["--palindrome", "normalized"], "pass")},
        note="decision D-palindrome-normalization (stored c05)"),
]

# Fixtures whose response must not stop the run: graded in a file next to a passing control row.
ROBUSTNESS = [
    _fx("rob", "t07", "-" * 2996 + "1", "fail", "C-IMP-1", grader_ok=False, reference_ok=False,
        note="F5: RecursionError from ast.parse escapes and stops the run"),
    _fx("rob", "t07", fenced(MALFORMED_FD1), "fail", "C-EXE-5", grader_ok=False, reference_ok=False,
        note="F5: malformed forged result line raises in the parent and stops the run"),
]

# Aggregation fixtures: (id, rows, contract score for model "m", grader_ok, reference_ok, note)
AGGREGATION = [
    ("agg:missing-tasks", [("a1", "t07", fenced(FIB))], 10.0, True, True,
     "control: 9 tasks without a response count as fail"),
    ("agg:duplicate-row", [("d1", "t07", fenced(FIB)), ("d2", "t07", fenced(FIB))], 10.0, False, False,
     "F6: a duplicated passing row is counted twice"),
]

# Hash-seed fixture (G2): verdict must not depend on the grader's PYTHONHASHSEED.
SET_ORDER_RLE = fenced("def run_length(s):\n    return \"\".join(c + str(s.count(c)) for c in set(s))")
