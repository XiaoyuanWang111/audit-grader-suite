"""Write cases/toycode-exec/tasks.jsonl and tests.json. Private: part of the keys."""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CASE = os.path.join(HERE, "..", "..", "cases", "toycode-exec")

TASKS = [
    (
        "t01",
        "second_largest",
        'def second_largest(nums):\n    """Return the second largest distinct value in the list nums, or None if nums has fewer than two\n    distinct values."""\n',
    ),
    (
        "t02",
        "is_palindrome",
        'def is_palindrome(s):\n    """Return True if the string s reads the same forwards and backwards, and False otherwise."""\n',
    ),
    (
        "t03",
        "parse_duration",
        'def parse_duration(text):\n    """Parse a duration such as "1h30m", "45m" or "2h" and return the total number of minutes as an int.\n    The hours part, if present, comes first. Raise ValueError if text is not such a duration."""\n',
    ),
    (
        "t04",
        "chunk",
        'def chunk(items, size):\n    """Split the list items into consecutive chunks of length size and return them as a list of lists.\n    The last chunk may be shorter. Raise ValueError if size is less than 1."""\n',
    ),
    ("t05", "median", 'def median(nums):\n    """Return the median of the non-empty list of numbers nums."""\n'),
    (
        "t06",
        "run_length",
        'def run_length(s):\n    """Return the run-length encoding of the string s: each run of one repeated character becomes the\n    character followed by the length of the run, so "aaab" becomes "a3b1"."""\n',
    ),
    ("t07", "fib", 'def fib(n):\n    """Return the n-th Fibonacci number, where fib(0) == 0 and fib(1) == 1."""\n'),
    (
        "t08",
        "merge_intervals",
        'def merge_intervals(intervals):\n    """Merge the intervals in the list intervals, each a [start, end] list with start <= end. Intervals\n    that overlap or touch are merged. Return the merged intervals as a list of [start, end] lists,\n    sorted by start."""\n',
    ),
    (
        "t09",
        "flatten",
        'def flatten(nested):\n    """Return a flat list of the integers in nested, a list whose elements are integers or lists of the\n    same kind, in left-to-right order."""\n',
    ),
    (
        "t10",
        "binary_search",
        'def binary_search(nums, target):\n    """Return the index of target in nums, a sorted list of distinct integers, or -1 if target is not\n    in nums."""\n',
    ),
]

TESTS = {
    "t01": [
        {"args": [[3, 1, 2]], "expected": 2},
        {"args": [[5, 5, 4]], "expected": 4},
        {"args": [[7]], "expected": None},
        {"args": [[]], "expected": None},
        {"args": [[-1, -2, -3]], "expected": -2},
    ],
    "t02": [
        {"args": ["racecar"], "expected": True},
        {"args": ["hello"], "expected": False},
        {"args": [""], "expected": True},
        {"args": ["Was it a car or a cat I saw"], "expected": True},
        {"args": ["ab"], "expected": False},
    ],
    "t03": [
        {"args": ["1h30m"], "expected": 90},
        {"args": ["45m"], "expected": 45},
        {"args": ["2h"], "expected": 120},
        {"args": ["abc"], "raises": "ValueError"},
        {"args": [""], "raises": "ValueError"},
    ],
    "t04": [
        {"args": [[1, 2, 3, 4, 5], 2], "expected": [[1, 2], [3, 4], [5]]},
        {"args": [[], 3], "expected": []},
        {"args": [[1, 2], 5], "expected": [[1, 2]]},
        {"args": [[1], 0], "raises": "ValueError"},
    ],
    "t05": [
        {"args": [[3, 1, 2]], "expected": 2},
        {"args": [[4, 1, 3, 2]], "expected": 2.5},
        {"args": [[5]], "expected": 5},
        {"args": [[1, 1, 2, 2]], "expected": 1.5},
    ],
    "t06": [
        {"args": ["aaab"], "expected": "a3b1"},
        {"args": [""], "expected": ""},
        {"args": ["abc"], "expected": "a1b1c1"},
        {"args": ["zzzz"], "expected": "z4"},
    ],
    "t07": [
        {"args": [0], "expected": 0},
        {"args": [1], "expected": 1},
        {"args": [10], "expected": 55},
        {"args": [30], "expected": 832040},
        {"args": [80], "expected": 23416728348467685},
    ],
    "t08": [
        {"args": [[[1, 3], [2, 6], [8, 10]]], "expected": [[1, 6], [8, 10]]},
        {"args": [[[1, 4], [4, 5]]], "expected": [[1, 5]]},
        {"args": [[]], "expected": []},
        {"args": [[[5, 6], [1, 2]]], "expected": [[1, 2], [5, 6]]},
    ],
    "t09": [
        {"args": [[1, [2, [3, 4]], 5]], "expected": [1, 2, 3, 4, 5]},
        {"args": [[]], "expected": []},
        {"args": [[[[]]]], "expected": []},
        {"args": [[[1], [2, [3]]]], "expected": [1, 2, 3]},
    ],
    "t10": [
        {"args": [[1, 3, 5, 7], 5], "expected": 2},
        {"args": [[1, 3, 5, 7], 4], "expected": -1},
        {"args": [[], 1], "expected": -1},
        {"args": [[2], 2], "expected": 0},
        {"args": [[1, 3, 5, 7], 9], "expected": -1},
    ],
}


def main():
    with open(os.path.join(CASE, "tasks.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        for tid, entry, prompt in TASKS:
            f.write(json.dumps({"task_id": tid, "entry_point": entry, "prompt": prompt}) + "\n")
    with open(os.path.join(CASE, "tests.json"), "w", encoding="utf-8", newline="\n") as f:
        f.write("{\n")
        items = list(TESTS.items())
        for i, (tid, tests) in enumerate(items):
            f.write(f'  "{tid}": [\n')
            for j, t in enumerate(tests):
                f.write("    " + json.dumps(t) + ("," if j < len(tests) - 1 else "") + "\n")
            f.write("  ]" + ("," if i < len(items) - 1 else "") + "\n")
        f.write("}\n")
    with open(os.path.join(CASE, "tests.json"), encoding="utf-8") as f:
        json.load(f)
    print("wrote tasks.jsonl and tests.json")


if __name__ == "__main__":
    main()
