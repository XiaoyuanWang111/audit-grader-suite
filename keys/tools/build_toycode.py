"""Write cases/toycode-exec/responses.jsonl (the stored panel). Private: part of the keys."""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "cases", "toycode-exec", "responses.jsonl")
MODELS = ["kite-7b", "lark-13b", "wren-34b", "finch-8b"]
FENCE = "```"


def block(code, before="", after=""):
    text = ""
    if before:
        text += before + "\n\n"
    text += FENCE + "python\n" + code.strip("\n") + "\n" + FENCE
    if after:
        text += "\n\n" + after
    return text


P = {}

P["t01"] = {
    "kite-7b": block(
        """
def second_largest(nums):
    distinct = sorted(set(nums), reverse=True)
    if len(distinct) < 2:
        return None
    return distinct[1]
""",
        after="Converting to a set removes duplicates before sorting.",
    ),
    "lark-13b": block(
        """
def second_largest(nums):
    return sorted(set(nums))[-2]
"""
    ),
    "wren-34b": block(
        """
def second_largest(nums):
    first = second = None
    for x in nums:
        if first is None or x > first:
            first, second = x, first
        elif x != first and (second is None or x > second):
            second = x
    return second
""",
        before="A single pass that tracks the two largest distinct values:",
    ),
    "finch-8b": block(
        """
def second_largest(nums):
    s = sorted(nums)
    if len(s) < 2:
        return None
    return s[-2]
"""
    ),
}

P["t02"] = {
    "kite-7b": block(
        """
def is_palindrome(s):
    cleaned = [c.lower() for c in s if c.isalnum()]
    return cleaned == cleaned[::-1]
"""
    ),
    "lark-13b": block(
        """
def is_palindrome(s):
    return s == s[::-1]
"""
    ),
    "wren-34b": block(
        """
import re

def is_palindrome(s):
    letters = re.sub(r"[^a-z0-9]", "", s.lower())
    return letters == letters[::-1]
""",
        before="Ignore case, spaces and punctuation, then compare the string with its reverse:",
    ),
    "finch-8b": block(
        """
def is_palindrome(s):
    s = s.lower()
    return s == s[::-1]
"""
    ),
}

P["t03"] = {
    "kite-7b": block(
        """
import re

def parse_duration(text):
    m = re.fullmatch(r"(?:(\\d+)h)?(?:(\\d+)m)?", text)
    if not text or m is None:
        raise ValueError(f"invalid duration: {text!r}")
    hours = int(m.group(1) or 0)
    minutes = int(m.group(2) or 0)
    return hours * 60 + minutes
"""
    ),
    "lark-13b": block(
        """
def parse_duration(text):
    total = 0
    number = ""
    for ch in text:
        if ch.isdigit():
            number += ch
        elif ch == "h":
            total += int(number) * 60
            number = ""
        elif ch == "m":
            total += int(number)
            number = ""
        else:
            raise ValueError(f"unexpected character {ch!r}")
    return total
"""
    ),
    "wren-34b": block(
        """
import re

_DURATION = re.compile(r"(?:(?P<h>\\d+)h)?(?:(?P<m>\\d+)m)?")


def parse_duration(text):
    match = _DURATION.fullmatch(text)
    if match is None or not (match.group("h") or match.group("m")):
        raise ValueError(f"not a duration: {text!r}")
    return int(match.group("h") or 0) * 60 + int(match.group("m") or 0)
"""
    ),
    "finch-8b": block(
        """
def parse_duration(text):
    if not text:
        raise Exception("empty duration")
    hours, minutes = 0, 0
    if "h" in text:
        h, text = text.split("h", 1)
        hours = int(h)
    if text.endswith("m"):
        minutes = int(text[:-1])
    elif text:
        raise Exception("bad duration")
    return hours * 60 + minutes
"""
    ),
}

P["t04"] = {
    "kite-7b": block(
        """
def chunk(items, size):
    if size < 1:
        raise ValueError("size must be at least 1")
    return [items[i:i + size] for i in range(0, len(items), size)]
"""
    ),
    "lark-13b": block(
        """
def chunk(items, size):
    return [items[i:i + size] for i in range(0, len(items), size)]
"""
    ),
    "wren-34b": block(
        """
def chunk(items, size):
    if size < 1:
        raise ValueError(f"size must be positive, got {size}")
    chunks = []
    for start in range(0, len(items), size):
        chunks.append(items[start:start + size])
    return chunks
"""
    ),
    "finch-8b": block(
        """
def chunk(items, size):
    if size < 1:
        raise ValueError("size must be positive")
    return [tuple(items[i:i + size]) for i in range(0, len(items), size)]
"""
    ),
}

P["t05"] = {
    "kite-7b": block(
        """
def median(nums):
    s = sorted(nums)
    return s[len(s) // 2]
"""
    ),
    "lark-13b": block(
        """
import statistics

def median(nums):
    return statistics.median(nums)
""",
        before="The standard library already has this:",
    ),
    "wren-34b": block(
        """
def median(nums):
    s = sorted(nums)
    n = len(s)
    return (s[(n - 1) // 2] + s[n // 2]) / 2
""",
        after="For odd n both indices point at the middle element, so one formula covers both cases.",
    ),
    "finch-8b": block(
        """
def median(nums):
    s = sorted(nums)
    mid = len(s) // 2
    if len(s) % 2 == 1:
        return s[mid]
    return (s[mid - 1] + s[mid]) // 2
"""
    ),
}

P["t06"] = {
    "kite-7b": block(
        """
from itertools import groupby

def run_length(s):
    return "".join(f"{ch}{len(list(group))}" for ch, group in groupby(s))
"""
    ),
    "lark-13b": block(
        """
def run_length(s):
    result = []
    prev = s[0]
    count = 1
    for ch in s[1:]:
        if ch == prev:
            count += 1
        else:
            result.append(prev + str(count))
            prev, count = ch, 1
    result.append(prev + str(count))
    return "".join(result)
"""
    ),
    "wren-34b": block(
        """
def run_length(s):
    if not s:
        return ""
    parts = []
    current, count = s[0], 1
    for ch in s[1:]:
        if ch == current:
            count += 1
        else:
            parts.append(f"{current}{count}")
            current, count = ch, 1
    parts.append(f"{current}{count}")
    return "".join(parts)
""",
        after="Example:\n\n" + FENCE + 'python\nprint(run_length("aaab"))  # a3b1\n' + FENCE,
    ),
    "finch-8b": block(
        """
def run_length(s):
    out = ""
    count = 1
    for i in range(1, len(s)):
        if s[i] == s[i - 1]:
            count += 1
        else:
            out += s[i - 1] + str(count)
            count = 1
    return out
"""
    ),
}

P["t07"] = {
    "kite-7b": block(
        """
from functools import lru_cache

@lru_cache(maxsize=None)
def fib(n):
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)
"""
    ),
    "lark-13b": block(
        """
def fib(n):
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)
"""
    ),
    "wren-34b": block(
        """
def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a
"""
    ),
    "finch-8b": block(
        """
def fib(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a
"""
    ),
}

P["t08"] = {
    "kite-7b": block(
        """
def merge_intervals(intervals):
    merged = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged
"""
    ),
    "lark-13b": block(
        """
def merge_intervals(intervals):
    merged = []
    for start, end in sorted(intervals):
        if merged and start < merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged
"""
    ),
    "wren-34b": block(
        """
def merge_intervals(intervals):
    result = []
    for start, end in sorted(intervals, key=lambda iv: iv[0]):
        if result and start <= result[-1][1]:
            result[-1] = (result[-1][0], max(result[-1][1], end))
        else:
            result.append((start, end))
    return result
""",
        before="Sort by start, then extend the last merged interval while the next one overlaps or touches it:",
    ),
    "finch-8b": block(
        """
def merge_intervals(intervals):
    intervals = sorted(intervals)
    out = []
    for iv in intervals:
        if out and iv[0] <= out[-1][1]:
            out[-1][1] = max(out[-1][1], iv[1])
        else:
            out.append(list(iv))
    return out
"""
    ),
}

P["t09"] = {
    "kite-7b": """def flatten(nested):
    flat = []
    for item in nested:
        if isinstance(item, list):
            flat.extend(flatten(item))
        else:
            flat.append(item)
    return flat
""",
    "lark-13b": block(
        """
def flatten(nested):
    out = []
    stack = [iter(nested)]
    while stack:
        for item in stack[-1]:
            if isinstance(item, list):
                stack.append(iter(item))
                break
            out.append(item)
        else:
            stack.pop()
    return out
"""
    ),
    "wren-34b": block(
        """
def flatten(nested):
    def walk(xs):
        for x in xs:
            if isinstance(x, list):
                yield from walk(x)
            else:
                yield x
    return list(walk(nested))
"""
    ),
    "finch-8b": block(
        """
def flatten(nested):
    out = []
    for x in nested:
        if isinstance(x, list):
            out.extend(x)
        else:
            out.append(x)
    return out
"""
    ),
}

P["t10"] = {
    "kite-7b": block(
        """
def binary_search(nums, target):
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target:
            return mid
        if nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
"""
    ),
    "lark-13b": block(
        """
def binary_search(nums, target):
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target:
            return mid
        if nums[mid] < target:
            lo = mid
        else:
            hi = mid
    return -1
"""
    ),
    "wren-34b": block(
        """
from bisect import bisect_left

def binary_search(nums, target):
    i = bisect_left(nums, target)
    if i < len(nums) and nums[i] == target:
        return i
    return -1
"""
    ),
    "finch-8b": block(
        """
def binary_search(nums, target):
    if target < nums[0] or target > nums[-1]:
        return -1
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target:
            return mid
        elif nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
"""
    ),
}


def main():
    rows = []
    n = 0
    for tid in sorted(P):
        for model in MODELS:
            n += 1
            rows.append(
                {
                    "id": f"c{n:02d}",
                    "model": model,
                    "task_id": tid,
                    "response": P[tid][model],
                    "finish_reason": "stop",
                    "max_tokens": 1024,
                    "temperature": 0.0,
                }
            )
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"wrote {len(rows)} responses to {os.path.normpath(OUT)}")


if __name__ == "__main__":
    main()
