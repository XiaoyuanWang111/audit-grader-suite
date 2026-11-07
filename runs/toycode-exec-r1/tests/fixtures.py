"""Labeled fixtures for the ToyCode grader audit.

Each fixture's label comes from audit/CONTRACT.md alone, under the proposed reading of every decision entry. Fields:

- check: the contract stage (C-extract, C-import, C-exec, C-test, C-data)
- task_id: the task whose tests the response is graded on
- response: the full response text
- label: "pass" or "fail" under the contract (proposed readings)
- shows: "control", a finding id (F1...), or a decision entry (D-...); a decision fixture also has "readings",
  the label under each reading of that entry
- grader, reference: the verdict that case/grade.py and case/reference/harness_ref.py give today, "pass", "fail"
  or "crash" (an exception escapes); a value that differs from the label marks the test as an expected failure
- note: one line on what the fixture shows

The fixture id is the check plus the first 16 hex digits of sha256(task_id + "\\n" + response).
"""

import hashlib

CORRECT = {
    "t01": (
        "def second_largest(nums):\n"
        "    distinct = sorted(set(nums))\n"
        "    return distinct[-2] if len(distinct) >= 2 else None\n"
    ),
    "t03": (
        "import re\n"
        "\n"
        "def parse_duration(text):\n"
        "    m = re.fullmatch(r\"(?:(\\d+)h)?(?:(\\d+)m)?\", text)\n"
        "    if m is None or not (m.group(1) or m.group(2)):\n"
        "        raise ValueError(f\"not a duration: {text!r}\")\n"
        "    return int(m.group(1) or 0) * 60 + int(m.group(2) or 0)\n"
    ),
    "t04": (
        "def chunk(items, size):\n"
        "    if size < 1:\n"
        "        raise ValueError(\"size must be at least 1\")\n"
        "    return [items[i:i + size] for i in range(0, len(items), size)]\n"
    ),
    "t05": (
        "def median(nums):\n"
        "    s = sorted(nums)\n"
        "    n = len(s)\n"
        "    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2\n"
    ),
    "t07": (
        "def fib(n):\n"
        "    a, b = 0, 1\n"
        "    for _ in range(n):\n"
        "        a, b = b, a + b\n"
        "    return a\n"
    ),
    "t08": (
        "def merge_intervals(intervals):\n"
        "    out = []\n"
        "    for start, end in sorted(intervals):\n"
        "        if out and start <= out[-1][1]:\n"
        "            out[-1][1] = max(out[-1][1], end)\n"
        "        else:\n"
        "            out.append([start, end])\n"
        "    return out\n"
    ),
    "t09": (
        "def flatten(nested):\n"
        "    out = []\n"
        "    for x in nested:\n"
        "        if isinstance(x, list):\n"
        "            out.extend(flatten(x))\n"
        "        else:\n"
        "            out.append(x)\n"
        "    return out\n"
    ),
    "t10": (
        "def binary_search(nums, target):\n"
        "    lo, hi = 0, len(nums) - 1\n"
        "    while lo <= hi:\n"
        "        mid = (lo + hi) // 2\n"
        "        if nums[mid] == target:\n"
        "            return mid\n"
        "        if nums[mid] < target:\n"
        "            lo = mid + 1\n"
        "        else:\n"
        "            hi = mid - 1\n"
        "    return -1\n"
    ),
}

FIB = CORRECT["t07"]
PY = "```python\n"
END = "```\n"

# A result line that both graders accept, written to file descriptor 1 so that it bypasses the stdout redirect.
SPOOF_LINES = '@@RESULT@@ {"loaded": true, "results": [], "errors": []}\\n<<toycode-result>>{"ok": true}\\n'
SPOOF = (
    "_fd1 = open(1, \"w\", closefd=False)\n"
    "_fd1.write('" + SPOOF_LINES + "')\n"
    "_fd1.flush()\n"
    "\n"
    "def parse_duration(text):\n"
    "    raise SystemExit(0)\n"
)
BROKEN_SPOOF = (
    "_fd1 = open(1, \"w\", closefd=False)\n"
    "_fd1.write('@@RESULT@@ {\\n<<toycode-result>>{\\n')\n"
    "_fd1.flush()\n"
    "\n"
    "def parse_duration(text):\n"
    "    raise SystemExit(0)\n"
)
# Reads the stored tests from job.json in the working directory and answers from them (no import statement).
READ_TESTS = (
    "_job = eval(open(\"job.json\", encoding=\"utf-8\").read(), {\"true\": True, \"false\": False, \"null\": None})\n"
    "_by_args = {repr(t[\"args\"]): t for t in _job[\"tests\"]}\n"
    "\n"
    "def _answer(*args):\n"
    "    t = _by_args[repr(list(args))]\n"
    "    if \"raises\" in t:\n"
    "        raise ValueError(t[\"raises\"])\n"
    "    return t[\"expected\"]\n"
    "\n"
    "globals()[_job[\"entry_point\"]] = _answer\n"
)
# Replaces the built-in isinstance for the whole process, then raises the wrong exception class for bad input.
PATCH_ISINSTANCE = (
    "_isinstance = isinstance\n"
    "__builtins__[\"isinstance\"] = lambda obj, cls: True if cls is ValueError else _isinstance(obj, cls)\n"
    "\n"
    "def parse_duration(text):\n"
    "    import re\n"
    "    m = re.fullmatch(r\"(?:(\\d+)h)?(?:(\\d+)m)?\", text)\n"
    "    if m is None or not (m.group(1) or m.group(2)):\n"
    "        raise RuntimeError(\"not a duration\")\n"
    "    return int(m.group(1) or 0) * 60 + int(m.group(2) or 0)\n"
)

RAW = [
    # ---------------------------------------------------------------- C-extract
    dict(check="C-extract", task_id="t07", response=PY + FIB + END, label="pass", shows="control",
         grader="pass", reference="pass", note="python-tagged block"),
    dict(check="C-extract", task_id="t07", response="```py\n" + FIB + END, label="pass", shows="F3",
         grader="fail", reference="pass", note="tag py is a fence tag; the grader only opens a block on ```python"),
    dict(check="C-extract", task_id="t07", response="```\n" + FIB + END, label="pass", shows="F3",
         grader="fail", reference="pass", note="a fence without a tag"),
    dict(check="C-extract", task_id="t07", response="```python3\n" + FIB + END, label="pass", shows="F3",
         grader="fail", reference="pass", note="tag python3"),
    dict(check="C-extract", task_id="t07", response="```Python\n" + FIB + END, label="pass", shows="F3",
         grader="fail", reference="pass", note="tag Python"),
    dict(check="C-extract", task_id="t07", response="```python \t\n" + FIB + "```  \n", label="pass",
         shows="control", grader="pass", reference="pass", note="spaces and a tab after both fences"),
    dict(check="C-extract", task_id="t07", response=FIB, label="pass", shows="control",
         grader="pass", reference="pass", note="no fence: the whole response is the code"),
    dict(check="C-extract", task_id="t07",
         response="Usage:\n\n```\n>>> fib(10)\n55\n```\n\nCode:\n\n" + PY + FIB + END, label="fail", shows="F3",
         grader="pass", reference="fail",
         note="the first block is the usage example; the grader skips it and grades the second block"),
    dict(check="C-extract", task_id="t07", response=PY + FIB, label="fail", shows="control",
         grader="fail", reference="fail", note="unclosed fence: the whole response, backticks included, is the code"),
    dict(check="C-extract", task_id="t07",
         response="  ```python\n" + "".join("  " + l + "\n" for l in FIB.splitlines()) + "  ```\n",
         label="fail", shows="control", grader="fail", reference="fail", note="indented fences are not fences"),
    dict(check="C-extract", task_id="t07", response=(PY + FIB + END).replace("\n", "\r\n"), label="pass",
         shows="D-line-terminator", readings={"A": "pass", "B": "fail"}, grader="fail", reference="fail",
         note="CRLF line endings"),
    dict(check="C-extract", task_id="t07", response="````python\n" + FIB + "````\n", label="fail",
         shows="control", grader="fail", reference="fail", note="four backticks are not a fence"),
    dict(check="C-extract", task_id="t07",
         response=PY + "".join("    " + l + "\n" for l in FIB.splitlines()) + END, label="fail",
         shows="control", grader="fail", reference="fail", note="code indented inside the block is not dedented"),
    dict(check="C-extract", task_id="t07", response=PY + FIB + END + "\nExample:\n\n" + PY + "print(fib(10))\n" + END,
         label="pass", shows="control", grader="pass", reference="pass", note="a second block is ignored"),
    dict(check="C-extract", task_id="t07", response=PY + "print(fib(10))\n" + END + "\n" + PY + FIB + END,
         label="fail", shows="control", grader="fail", reference="fail",
         note="only the first block counts, and it calls an undefined fib"),
    # ---------------------------------------------------------------- C-import
    dict(check="C-import", task_id="t07", response=PY + "from typing import List\n\n" + FIB + END, label="pass",
         shows="control", grader="pass", reference="pass", note="allowed module"),
    dict(check="C-import", task_id="t07", response=PY + "import os\n\n" + FIB + END, label="fail",
         shows="control", grader="fail", reference="fail", note="module off the list"),
    dict(check="C-import", task_id="t07",
         response=PY + FIB.replace("    a, b = 0, 1\n", "    import os\n    a, b = 0, 1\n") + END, label="fail",
         shows="control", grader="fail", reference="fail", note="import inside the function body"),
    dict(check="C-import", task_id="t07",
         response=PY + FIB.replace("def fib(n):\n", "def fib(n):\n    \"\"\"\n    import os\n    \"\"\"\n") + END,
         label="pass", shows="control", grader="pass", reference="pass", note="import text inside a docstring"),
    dict(check="C-import", task_id="t07", response=PY + "from __future__ import annotations\n\n" + FIB + END,
         label="fail", shows="control", grader="fail", reference="fail", note="__future__ is not on the list"),
    dict(check="C-import", task_id="t07",
         response=PY + FIB.replace("    a, b = 0, 1\n", "    if n < 0:\n        from .math import sqrt\n    a, b = 0, 1\n")
         + END, label="fail", shows="F4", grader="pass", reference="pass",
         note="a relative import that names an allowed module, in a branch the tests never run"),
    dict(check="C-import", task_id="t07", response=PY + "import collections.abc\n\n" + FIB + END, label="pass",
         shows="control", grader="pass", reference="pass", note="dotted name of an allowed module"),
    dict(check="C-import", task_id="t07", response=PY + "import math, os\n\n" + FIB + END, label="fail",
         shows="control", grader="fail", reference="fail", note="second name in one import statement"),
    dict(check="C-import", task_id="t07", response=PY + "_os = __import__(\"os\")\n\n" + FIB + END, label="pass",
         shows="D-dynamic-import", readings={"A": "pass", "B": "fail"}, grader="pass", reference="pass",
         note="a call to __import__ is not an import statement"),
    dict(check="C-import", task_id="t07", response="-" * 5965, label="fail", shows="F5",
         grader="crash", reference="crash", note="5,965 dashes: ast.parse raises MemoryError, which the check does not catch"),
    dict(check="C-import", task_id="t07", response=PY + FIB + "\nx = " + "+".join(["1"] * 2997) + "\n" + END,
         label="fail", shows="F5", grader="crash", reference="crash",
         note="a 2,997-term sum: ast.parse raises RecursionError, which the check does not catch"),
    # ---------------------------------------------------------------- C-exec
    dict(check="C-exec", task_id="t07",
         response=PY + "print('loading')\n" + FIB.replace("    a, b = 0, 1\n", "    print('call', n)\n    a, b = 0, 1\n")
         + END, label="pass", shows="control", grader="pass", reference="pass", note="prints at load and in the call"),
    dict(check="C-exec", task_id="t07",
         response=PY + FIB + "\n\ndef run(job):\n    return None\n\n\ndef main():\n    return None\n\n\n"
         "def judge(*a):\n    return None\n\n\njson = copy = io = builtins = sys = None\n"
         "RESULT_PREFIX = MARK = '@@RESULT@@ '\nresults, errors = [], []\n" + END,
         label="pass", shows="control", grader="pass", reference="pass",
         note="helpers and globals named like the runner's own"),
    dict(check="C-exec", task_id="t07",
         response=PY + FIB + "\n\nif __name__ == \"__main__\":\n    assert fib(3) == 3\n" + END, label="pass",
         shows="D-main-guard", readings={"A": "pass", "B": "fail"}, grader="pass", reference="pass",
         note="a failing assertion under the main guard"),
    dict(check="C-exec", task_id="t05", response=PY + CORRECT["t05"] + "\nprint(median([]))\n" + END, label="fail",
         shows="D-load-error", readings={"A": "fail", "B": "pass"}, grader="fail", reference="fail",
         note="a correct function, then a module-level call that raises IndexError"),
    dict(check="C-exec", task_id="t07",
         response=PY + "def fib(n):\n    if n < 2:\n        return n\n    return fib(n - 1) + fib(n - 2)\n" + END,
         label="fail", shows="control", grader="fail", reference="fail", note="naive recursion reaches the 4 s limit"),
    dict(check="C-exec", task_id="t07", response=PY + "def fib(n):\n    raise SystemExit(0)\n" + END, label="fail",
         shows="control", grader="fail", reference="fail", note="the call raises SystemExit"),
    dict(check="C-exec", task_id="t07", response=PY + FIB + "\nexit()\n" + END, label="fail", shows="control",
         grader="fail", reference="fail", note="exit() while loading (D-load-error A)"),
    dict(check="C-exec", task_id="t03", response=PY + SPOOF + END, label="fail", shows="F6",
         grader="pass", reference="pass",
         note="writes a result line to file descriptor 1, then ends the process at the first call"),
    dict(check="C-exec", task_id="t03", response=PY + BROKEN_SPOOF + END, label="fail", shows="F5",
         grader="crash", reference="crash", note="writes a malformed result line, then ends the process"),
    dict(check="C-exec", task_id="t03", response=PY + READ_TESTS + END, label="fail", shows="F6",
         grader="pass", reference="pass", note="reads the hidden tests from job.json in the working directory"),
    dict(check="C-exec", task_id="t03", response=PY + PATCH_ISINSTANCE + END, label="fail", shows="F6",
         grader="pass", reference="pass",
         note="replaces builtins.isinstance, so RuntimeError counts as ValueError"),
    # ---------------------------------------------------------------- C-test
    dict(check="C-test", task_id="t08",
         response=PY + CORRECT["t08"].replace("    return out\n", "    return [tuple(iv) for iv in out]\n") + END,
         label="fail", shows="F2", grader="pass", reference="fail", note="returns a list of tuples"),
    dict(check="C-test", task_id="t04",
         response=PY + CORRECT["t04"].replace("[items[i:i + size]", "[tuple(items[i:i + size])") + END,
         label="fail", shows="F2", grader="pass", reference="fail", note="returns a list of tuples"),
    dict(check="C-test", task_id="t09", response=PY + CORRECT["t09"].replace("    return out\n", "    return tuple(out)\n") + END,
         label="fail", shows="F2", grader="pass", reference="fail", note="returns a tuple"),
    dict(check="C-test", task_id="t01", response=PY + "def second_largest(nums):\n    return sorted(set(nums))[-2]\n" + END,
         label="fail", shows="F1", grader="pass", reference="fail",
         note="IndexError on the two tests with fewer than two distinct values"),
    dict(check="C-test", task_id="t07", response=PY + FIB.replace("def fib(n):", "def fibonacci(n):") + END,
         label="fail", shows="F1", grader="pass", reference="fail", note="the function has another name"),
    dict(check="C-test", task_id="t05", response=PY + "def median(nums):\n    raise NotImplementedError\n" + END,
         label="fail", shows="F1", grader="pass", reference="fail", note="a stub that raises"),
    dict(check="C-test", task_id="t10", response="", label="fail", shows="F1", grader="pass", reference="fail",
         note="empty response"),
    dict(check="C-test", task_id="t03", response=PY + "def parse_duration(*args):\n    raise ValueError\n" + END,
         label="fail", shows="F1", grader="pass", reference="fail",
         note="always raises ValueError: the raises tests pass and the errors of the other tests are ignored"),
    dict(check="C-test", task_id="t03",
         response=PY + "class DurationError(ValueError):\n    pass\n\n\n" + CORRECT["t03"].replace(
             "raise ValueError(", "raise DurationError(") + END,
         label="pass", shows="control", grader="pass", reference="pass", note="raises a subclass of ValueError"),
    dict(check="C-test", task_id="t03", response=PY + CORRECT["t03"].replace("raise ValueError(", "raise Exception(") + END,
         label="fail", shows="control", grader="fail", reference="fail", note="raises Exception, not ValueError"),
    dict(check="C-test", task_id="t03",
         response=PY + "class ValueError(Exception):\n    pass\n\n\n" + CORRECT["t03"] + END,
         label="fail", shows="control", grader="fail", reference="fail",
         note="raises its own class named ValueError, which is not the built-in"),
    dict(check="C-test", task_id="t03",
         response=PY + CORRECT["t03"].replace("return int(m.group(1) or 0) * 60 + int(m.group(2) or 0)",
                                             "return float(int(m.group(1) or 0) * 60 + int(m.group(2) or 0))") + END,
         label="pass", shows="D-numeric-type", readings={"A": "pass", "B": "fail"}, grader="pass", reference="pass",
         note="returns 90.0 where the docstring says an int"),
    dict(check="C-test", task_id="t07",
         response=PY + "class _Any:\n    def __eq__(self, other):\n        return True\n\n\ndef fib(n):\n    return _Any()\n" + END,
         label="fail", shows="D-eq-object", readings={"A": "pass", "B": "fail"}, grader="fail", reference="pass",
         note="returns an object whose __eq__ is always True"),
    dict(check="C-test", task_id="t08",
         response=PY + "def merge_intervals(intervals):\n    intervals.sort()\n    out = []\n    for iv in intervals:\n"
         "        if out and iv[0] <= out[-1][1]:\n            out[-1][1] = max(out[-1][1], iv[1])\n"
         "        else:\n            out.append(iv)\n    return out\n" + END,
         label="pass", shows="control", grader="pass", reference="pass", note="sorts and changes its argument in place"),
    dict(check="C-test", task_id="t09",
         response=PY + "def flatten(nested):\n    for x in nested:\n        if isinstance(x, list):\n"
         "            yield from flatten(x)\n        else:\n            yield x\n" + END,
         label="fail", shows="control", grader="fail", reference="fail", note="returns a generator, not a list"),
    dict(check="C-test", task_id="t04", response=PY + CORRECT["t04"].replace("raise ValueError(", "raise SystemExit(") + END,
         label="fail", shows="control", grader="fail", reference="fail", note="raises SystemExit for size 0"),
    # ---------------------------------------------------------------- C-data
    dict(check="C-data", task_id="t02", response=PY + "def is_palindrome(s):\n    return s == s[::-1]\n" + END,
         label="pass", shows="D-palindrome-normalization", readings={"A": "pass", "B": "fail"}, grader="fail",
         reference="fail", note="literal reversal: test 4 expects True for a phrase that is not its own reverse"),
    dict(check="C-data", task_id="t02",
         response=PY + "def is_palindrome(s):\n    t = [c.lower() for c in s if c.isalnum()]\n    return t == t[::-1]\n" + END,
         label="fail", shows="D-palindrome-normalization", readings={"A": "fail", "B": "pass"}, grader="pass",
         reference="pass", note="ignores case and punctuation"),
]


def fixture_id(check, task_id, response):
    return check + ":" + hashlib.sha256((task_id + "\n" + response).encode("utf-8", "surrogatepass")).hexdigest()[:16]


FIXTURES = [dict(f, id=fixture_id(f["check"], f["task_id"], f["response"])) for f in RAW]
assert len({f["id"] for f in FIXTURES}) == len(FIXTURES), "duplicate fixture"
