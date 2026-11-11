# ToyCode blinded review, batch A

Each case below starts with a line `=== CASE <id> ===`. The REQUIREMENT TO JUDGE is the benchmark's grading rule followed by the task's stored tests, one JSON object per line. The PROMPT is the only message the model saw, between `<<<BEGIN PROMPT>>>` and `<<<END PROMPT>>>`. The RESPONSE is the model's complete reply, between `<<<BEGIN RESPONSE>>>` and `<<<END RESPONSE>>>`; the markers sit on their own lines, so any blank line or space just inside them belongs to the response. The exact response is also in responses/<id>.txt next to this file, and `python -B show_case.py <id>` prints it (add --repr to see every character escaped).

=== CASE TC131 ===

REQUIREMENT TO JUDGE:

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

Stored tests for `parse_duration` (hidden from the model):

{"args": ["1h30m"], "expected": 90}
{"args": ["45m"], "expected": 45}
{"args": ["2h"], "expected": 120}
{"args": ["abc"], "raises": "ValueError"}
{"args": [""], "raises": "ValueError"}

PROMPT:
<<<BEGIN PROMPT>>>
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def parse_duration(text):
    """Parse a duration such as "1h30m", "45m" or "2h" and return the total number of minutes as an int.
    The hours part, if present, comes first. Raise ValueError if text is not such a duration."""
<<<END PROMPT>>>

RESPONSE:
<<<BEGIN RESPONSE>>>
```python
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
```
<<<END RESPONSE>>>

=== CASE TC135 ===

REQUIREMENT TO JUDGE:

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

Stored tests for `chunk` (hidden from the model):

{"args": [[1, 2, 3, 4, 5], 2], "expected": [[1, 2], [3, 4], [5]]}
{"args": [[], 3], "expected": []}
{"args": [[1, 2], 5], "expected": [[1, 2]]}
{"args": [[1], 0], "raises": "ValueError"}

PROMPT:
<<<BEGIN PROMPT>>>
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def chunk(items, size):
    """Split the list items into consecutive chunks of length size and return them as a list of lists.
    The last chunk may be shorter. Raise ValueError if size is less than 1."""
<<<END PROMPT>>>

RESPONSE:
<<<BEGIN RESPONSE>>>
```python
def chunk(items, size):
    if size < 1:
        raise ValueError(f"size must be positive, got {size}")
    chunks = []
    for start in range(0, len(items), size):
        chunks.append(items[start:start + size])
    return chunks
```
<<<END RESPONSE>>>

=== CASE TC167 ===

REQUIREMENT TO JUDGE:

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

Stored tests for `fib` (hidden from the model):

{"args": [0], "expected": 0}
{"args": [1], "expected": 1}
{"args": [10], "expected": 55}
{"args": [30], "expected": 832040}
{"args": [80], "expected": 23416728348467685}

PROMPT:
<<<BEGIN PROMPT>>>
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def fib(n):
    """Return the n-th Fibonacci number, where fib(0) == 0 and fib(1) == 1."""
<<<END PROMPT>>>

RESPONSE:
<<<BEGIN RESPONSE>>>
```python
def fib(n):
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)
```
<<<END RESPONSE>>>

=== CASE TC226 ===

REQUIREMENT TO JUDGE:

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

Stored tests for `merge_intervals` (hidden from the model):

{"args": [[[1, 3], [2, 6], [8, 10]]], "expected": [[1, 6], [8, 10]]}
{"args": [[[1, 4], [4, 5]]], "expected": [[1, 5]]}
{"args": [[]], "expected": []}
{"args": [[[5, 6], [1, 2]]], "expected": [[1, 2], [5, 6]]}

PROMPT:
<<<BEGIN PROMPT>>>
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def merge_intervals(intervals):
    """Merge the intervals in the list intervals, each a [start, end] list with start <= end. Intervals
    that overlap or touch are merged. Return the merged intervals as a list of [start, end] lists,
    sorted by start."""
<<<END PROMPT>>>

RESPONSE:
<<<BEGIN RESPONSE>>>
```python
def merge_intervals(intervals):
    merged = []
    for start, end in sorted(intervals):
        if merged and start < merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged
```
<<<END RESPONSE>>>

=== CASE TC235 ===

REQUIREMENT TO JUDGE:

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

Stored tests for `run_length` (hidden from the model):

{"args": ["aaab"], "expected": "a3b1"}
{"args": [""], "expected": ""}
{"args": ["abc"], "expected": "a1b1c1"}
{"args": ["zzzz"], "expected": "z4"}

PROMPT:
<<<BEGIN PROMPT>>>
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def run_length(s):
    """Return the run-length encoding of the string s: each run of one repeated character becomes the
    character followed by the length of the run, so "aaab" becomes "a3b1"."""
<<<END PROMPT>>>

RESPONSE:
<<<BEGIN RESPONSE>>>
```python
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
```
<<<END RESPONSE>>>

=== CASE TC241 ===

REQUIREMENT TO JUDGE:

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

Stored tests for `fib` (hidden from the model):

{"args": [0], "expected": 0}
{"args": [1], "expected": 1}
{"args": [10], "expected": 55}
{"args": [30], "expected": 832040}
{"args": [80], "expected": 23416728348467685}

PROMPT:
<<<BEGIN PROMPT>>>
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def fib(n):
    """Return the n-th Fibonacci number, where fib(0) == 0 and fib(1) == 1."""
<<<END PROMPT>>>

RESPONSE:
<<<BEGIN RESPONSE>>>
```python
from functools import lru_cache

@lru_cache(maxsize=None)
def fib(n):
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)
```
<<<END RESPONSE>>>

=== CASE TC248 ===

REQUIREMENT TO JUDGE:

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

Stored tests for `median` (hidden from the model):

{"args": [[3, 1, 2]], "expected": 2}
{"args": [[4, 1, 3, 2]], "expected": 2.5}
{"args": [[5]], "expected": 5}
{"args": [[1, 1, 2, 2]], "expected": 1.5}

PROMPT:
<<<BEGIN PROMPT>>>
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def median(nums):
    """Return the median of the non-empty list of numbers nums."""
<<<END PROMPT>>>

RESPONSE:
<<<BEGIN RESPONSE>>>
```python
def median(nums):
    s = sorted(nums)
    return s[len(s) // 2]
```
<<<END RESPONSE>>>

=== CASE TC270 ===

REQUIREMENT TO JUDGE:

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

Stored tests for `chunk` (hidden from the model):

{"args": [[1, 2, 3, 4, 5], 2], "expected": [[1, 2], [3, 4], [5]]}
{"args": [[], 3], "expected": []}
{"args": [[1, 2], 5], "expected": [[1, 2]]}
{"args": [[1], 0], "raises": "ValueError"}

PROMPT:
<<<BEGIN PROMPT>>>
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def chunk(items, size):
    """Split the list items into consecutive chunks of length size and return them as a list of lists.
    The last chunk may be shorter. Raise ValueError if size is less than 1."""
<<<END PROMPT>>>

RESPONSE:
<<<BEGIN RESPONSE>>>
```python
def chunk(items, size):
    if size < 1:
        raise ValueError("size must be at least 1")
    return [items[i:i + size] for i in range(0, len(items), size)]
```
<<<END RESPONSE>>>

=== CASE TC291 ===

REQUIREMENT TO JUDGE:

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

Stored tests for `second_largest` (hidden from the model):

{"args": [[3, 1, 2]], "expected": 2}
{"args": [[5, 5, 4]], "expected": 4}
{"args": [[7]], "expected": null}
{"args": [[]], "expected": null}
{"args": [[-1, -2, -3]], "expected": -2}

PROMPT:
<<<BEGIN PROMPT>>>
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def second_largest(nums):
    """Return the second largest distinct value in the list nums, or None if nums has fewer than two
    distinct values."""
<<<END PROMPT>>>

RESPONSE:
<<<BEGIN RESPONSE>>>
```python
def second_largest(nums):
    distinct = sorted(set(nums), reverse=True)
    if len(distinct) < 2:
        return None
    return distinct[1]
```

Converting to a set removes duplicates before sorting.
<<<END RESPONSE>>>

=== CASE TC295 ===

REQUIREMENT TO JUDGE:

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

Stored tests for `is_palindrome` (hidden from the model):

{"args": ["racecar"], "expected": true}
{"args": ["hello"], "expected": false}
{"args": [""], "expected": true}
{"args": ["Was it a car or a cat I saw"], "expected": true}
{"args": ["ab"], "expected": false}

PROMPT:
<<<BEGIN PROMPT>>>
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def is_palindrome(s):
    """Return True if the string s reads the same forwards and backwards, and False otherwise."""
<<<END PROMPT>>>

RESPONSE:
<<<BEGIN RESPONSE>>>
Ignore case, spaces and punctuation, then compare the string with its reverse:

```python
import re

def is_palindrome(s):
    letters = re.sub(r"[^a-z0-9]", "", s.lower())
    return letters == letters[::-1]
```
<<<END RESPONSE>>>

=== CASE TC307 ===

REQUIREMENT TO JUDGE:

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

Stored tests for `flatten` (hidden from the model):

{"args": [[1, [2, [3, 4]], 5]], "expected": [1, 2, 3, 4, 5]}
{"args": [[]], "expected": []}
{"args": [[[[]]]], "expected": []}
{"args": [[[1], [2, [3]]]], "expected": [1, 2, 3]}

PROMPT:
<<<BEGIN PROMPT>>>
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def flatten(nested):
    """Return a flat list of the integers in nested, a list whose elements are integers or lists of the
    same kind, in left-to-right order."""
<<<END PROMPT>>>

RESPONSE:
<<<BEGIN RESPONSE>>>
```python
def flatten(nested):
    out = []
    for x in nested:
        if isinstance(x, list):
            out.extend(x)
        else:
            out.append(x)
    return out
```
<<<END RESPONSE>>>

=== CASE TC373 ===

REQUIREMENT TO JUDGE:

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

Stored tests for `flatten` (hidden from the model):

{"args": [[1, [2, [3, 4]], 5]], "expected": [1, 2, 3, 4, 5]}
{"args": [[]], "expected": []}
{"args": [[[[]]]], "expected": []}
{"args": [[[1], [2, [3]]]], "expected": [1, 2, 3]}

PROMPT:
<<<BEGIN PROMPT>>>
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def flatten(nested):
    """Return a flat list of the integers in nested, a list whose elements are integers or lists of the
    same kind, in left-to-right order."""
<<<END PROMPT>>>

RESPONSE:
<<<BEGIN RESPONSE>>>
def flatten(nested):
    flat = []
    for item in nested:
        if isinstance(item, list):
            flat.extend(flatten(item))
        else:
            flat.append(item)
    return flat

<<<END RESPONSE>>>

=== CASE TC375 ===

REQUIREMENT TO JUDGE:

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

Stored tests for `binary_search` (hidden from the model):

{"args": [[1, 3, 5, 7], 5], "expected": 2}
{"args": [[1, 3, 5, 7], 4], "expected": -1}
{"args": [[], 1], "expected": -1}
{"args": [[2], 2], "expected": 0}
{"args": [[1, 3, 5, 7], 9], "expected": -1}

PROMPT:
<<<BEGIN PROMPT>>>
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def binary_search(nums, target):
    """Return the index of target in nums, a sorted list of distinct integers, or -1 if target is not
    in nums."""
<<<END PROMPT>>>

RESPONSE:
<<<BEGIN RESPONSE>>>
```python
from bisect import bisect_left

def binary_search(nums, target):
    i = bisect_left(nums, target)
    if i < len(nums) and nums[i] == target:
        return i
    return -1
```
<<<END RESPONSE>>>

=== CASE TC393 ===

REQUIREMENT TO JUDGE:

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

Stored tests for `second_largest` (hidden from the model):

{"args": [[3, 1, 2]], "expected": 2}
{"args": [[5, 5, 4]], "expected": 4}
{"args": [[7]], "expected": null}
{"args": [[]], "expected": null}
{"args": [[-1, -2, -3]], "expected": -2}

PROMPT:
<<<BEGIN PROMPT>>>
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def second_largest(nums):
    """Return the second largest distinct value in the list nums, or None if nums has fewer than two
    distinct values."""
<<<END PROMPT>>>

RESPONSE:
<<<BEGIN RESPONSE>>>
```python
def second_largest(nums):
    return sorted(set(nums))[-2]
```
<<<END RESPONSE>>>

=== CASE TC440 ===

REQUIREMENT TO JUDGE:

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

Stored tests for `fib` (hidden from the model):

{"args": [0], "expected": 0}
{"args": [1], "expected": 1}
{"args": [10], "expected": 55}
{"args": [30], "expected": 832040}
{"args": [80], "expected": 23416728348467685}

PROMPT:
<<<BEGIN PROMPT>>>
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def fib(n):
    """Return the n-th Fibonacci number, where fib(0) == 0 and fib(1) == 1."""
<<<END PROMPT>>>

RESPONSE:
<<<BEGIN RESPONSE>>>
```python
def fib(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a
```
<<<END RESPONSE>>>

=== CASE TC463 ===

REQUIREMENT TO JUDGE:

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

Stored tests for `merge_intervals` (hidden from the model):

{"args": [[[1, 3], [2, 6], [8, 10]]], "expected": [[1, 6], [8, 10]]}
{"args": [[[1, 4], [4, 5]]], "expected": [[1, 5]]}
{"args": [[]], "expected": []}
{"args": [[[5, 6], [1, 2]]], "expected": [[1, 2], [5, 6]]}

PROMPT:
<<<BEGIN PROMPT>>>
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def merge_intervals(intervals):
    """Merge the intervals in the list intervals, each a [start, end] list with start <= end. Intervals
    that overlap or touch are merged. Return the merged intervals as a list of [start, end] lists,
    sorted by start."""
<<<END PROMPT>>>

RESPONSE:
<<<BEGIN RESPONSE>>>
Sort by start, then extend the last merged interval while the next one overlaps or touches it:

```python
def merge_intervals(intervals):
    result = []
    for start, end in sorted(intervals, key=lambda iv: iv[0]):
        if result and start <= result[-1][1]:
            result[-1] = (result[-1][0], max(result[-1][1], end))
        else:
            result.append((start, end))
    return result
```
<<<END RESPONSE>>>

=== CASE TC489 ===

REQUIREMENT TO JUDGE:

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

Stored tests for `binary_search` (hidden from the model):

{"args": [[1, 3, 5, 7], 5], "expected": 2}
{"args": [[1, 3, 5, 7], 4], "expected": -1}
{"args": [[], 1], "expected": -1}
{"args": [[2], 2], "expected": 0}
{"args": [[1, 3, 5, 7], 9], "expected": -1}

PROMPT:
<<<BEGIN PROMPT>>>
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def binary_search(nums, target):
    """Return the index of target in nums, a sorted list of distinct integers, or -1 if target is not
    in nums."""
<<<END PROMPT>>>

RESPONSE:
<<<BEGIN RESPONSE>>>
```python
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
```
<<<END RESPONSE>>>

=== CASE TC505 ===

REQUIREMENT TO JUDGE:

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

Stored tests for `merge_intervals` (hidden from the model):

{"args": [[[1, 3], [2, 6], [8, 10]]], "expected": [[1, 6], [8, 10]]}
{"args": [[[1, 4], [4, 5]]], "expected": [[1, 5]]}
{"args": [[]], "expected": []}
{"args": [[[5, 6], [1, 2]]], "expected": [[1, 2], [5, 6]]}

PROMPT:
<<<BEGIN PROMPT>>>
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def merge_intervals(intervals):
    """Merge the intervals in the list intervals, each a [start, end] list with start <= end. Intervals
    that overlap or touch are merged. Return the merged intervals as a list of [start, end] lists,
    sorted by start."""
<<<END PROMPT>>>

RESPONSE:
<<<BEGIN RESPONSE>>>
```python
def merge_intervals(intervals):
    merged = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged
```
<<<END RESPONSE>>>

=== CASE TC512 ===

REQUIREMENT TO JUDGE:

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

Stored tests for `chunk` (hidden from the model):

{"args": [[1, 2, 3, 4, 5], 2], "expected": [[1, 2], [3, 4], [5]]}
{"args": [[], 3], "expected": []}
{"args": [[1, 2], 5], "expected": [[1, 2]]}
{"args": [[1], 0], "raises": "ValueError"}

PROMPT:
<<<BEGIN PROMPT>>>
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def chunk(items, size):
    """Split the list items into consecutive chunks of length size and return them as a list of lists.
    The last chunk may be shorter. Raise ValueError if size is less than 1."""
<<<END PROMPT>>>

RESPONSE:
<<<BEGIN RESPONSE>>>
```python
def chunk(items, size):
    if size < 1:
        raise ValueError("size must be positive")
    return [tuple(items[i:i + size]) for i in range(0, len(items), size)]
```
<<<END RESPONSE>>>

=== CASE TC521 ===

REQUIREMENT TO JUDGE:

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

Stored tests for `is_palindrome` (hidden from the model):

{"args": ["racecar"], "expected": true}
{"args": ["hello"], "expected": false}
{"args": [""], "expected": true}
{"args": ["Was it a car or a cat I saw"], "expected": true}
{"args": ["ab"], "expected": false}

PROMPT:
<<<BEGIN PROMPT>>>
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def is_palindrome(s):
    """Return True if the string s reads the same forwards and backwards, and False otherwise."""
<<<END PROMPT>>>

RESPONSE:
<<<BEGIN RESPONSE>>>
```python
def is_palindrome(s):
    s = s.lower()
    return s == s[::-1]
```
<<<END RESPONSE>>>

=== CASE TC525 ===

REQUIREMENT TO JUDGE:

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

Stored tests for `parse_duration` (hidden from the model):

{"args": ["1h30m"], "expected": 90}
{"args": ["45m"], "expected": 45}
{"args": ["2h"], "expected": 120}
{"args": ["abc"], "raises": "ValueError"}
{"args": [""], "raises": "ValueError"}

PROMPT:
<<<BEGIN PROMPT>>>
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def parse_duration(text):
    """Parse a duration such as "1h30m", "45m" or "2h" and return the total number of minutes as an int.
    The hours part, if present, comes first. Raise ValueError if text is not such a duration."""
<<<END PROMPT>>>

RESPONSE:
<<<BEGIN RESPONSE>>>
```python
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
```
<<<END RESPONSE>>>

=== CASE TC560 ===

REQUIREMENT TO JUDGE:

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

Stored tests for `is_palindrome` (hidden from the model):

{"args": ["racecar"], "expected": true}
{"args": ["hello"], "expected": false}
{"args": [""], "expected": true}
{"args": ["Was it a car or a cat I saw"], "expected": true}
{"args": ["ab"], "expected": false}

PROMPT:
<<<BEGIN PROMPT>>>
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def is_palindrome(s):
    """Return True if the string s reads the same forwards and backwards, and False otherwise."""
<<<END PROMPT>>>

RESPONSE:
<<<BEGIN RESPONSE>>>
```python
def is_palindrome(s):
    cleaned = [c.lower() for c in s if c.isalnum()]
    return cleaned == cleaned[::-1]
```
<<<END RESPONSE>>>

=== CASE TC576 ===

REQUIREMENT TO JUDGE:

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

Stored tests for `binary_search` (hidden from the model):

{"args": [[1, 3, 5, 7], 5], "expected": 2}
{"args": [[1, 3, 5, 7], 4], "expected": -1}
{"args": [[], 1], "expected": -1}
{"args": [[2], 2], "expected": 0}
{"args": [[1, 3, 5, 7], 9], "expected": -1}

PROMPT:
<<<BEGIN PROMPT>>>
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def binary_search(nums, target):
    """Return the index of target in nums, a sorted list of distinct integers, or -1 if target is not
    in nums."""
<<<END PROMPT>>>

RESPONSE:
<<<BEGIN RESPONSE>>>
```python
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
```
<<<END RESPONSE>>>

=== CASE TC583 ===

REQUIREMENT TO JUDGE:

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

Stored tests for `binary_search` (hidden from the model):

{"args": [[1, 3, 5, 7], 5], "expected": 2}
{"args": [[1, 3, 5, 7], 4], "expected": -1}
{"args": [[], 1], "expected": -1}
{"args": [[2], 2], "expected": 0}
{"args": [[1, 3, 5, 7], 9], "expected": -1}

PROMPT:
<<<BEGIN PROMPT>>>
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def binary_search(nums, target):
    """Return the index of target in nums, a sorted list of distinct integers, or -1 if target is not
    in nums."""
<<<END PROMPT>>>

RESPONSE:
<<<BEGIN RESPONSE>>>
```python
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
```
<<<END RESPONSE>>>

=== CASE TC602 ===

REQUIREMENT TO JUDGE:

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

Stored tests for `merge_intervals` (hidden from the model):

{"args": [[[1, 3], [2, 6], [8, 10]]], "expected": [[1, 6], [8, 10]]}
{"args": [[[1, 4], [4, 5]]], "expected": [[1, 5]]}
{"args": [[]], "expected": []}
{"args": [[[5, 6], [1, 2]]], "expected": [[1, 2], [5, 6]]}

PROMPT:
<<<BEGIN PROMPT>>>
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def merge_intervals(intervals):
    """Merge the intervals in the list intervals, each a [start, end] list with start <= end. Intervals
    that overlap or touch are merged. Return the merged intervals as a list of [start, end] lists,
    sorted by start."""
<<<END PROMPT>>>

RESPONSE:
<<<BEGIN RESPONSE>>>
```python
def merge_intervals(intervals):
    intervals = sorted(intervals)
    out = []
    for iv in intervals:
        if out and iv[0] <= out[-1][1]:
            out[-1][1] = max(out[-1][1], iv[1])
        else:
            out.append(list(iv))
    return out
```
<<<END RESPONSE>>>

=== CASE TC718 ===

REQUIREMENT TO JUDGE:

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

Stored tests for `chunk` (hidden from the model):

{"args": [[1, 2, 3, 4, 5], 2], "expected": [[1, 2], [3, 4], [5]]}
{"args": [[], 3], "expected": []}
{"args": [[1, 2], 5], "expected": [[1, 2]]}
{"args": [[1], 0], "raises": "ValueError"}

PROMPT:
<<<BEGIN PROMPT>>>
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def chunk(items, size):
    """Split the list items into consecutive chunks of length size and return them as a list of lists.
    The last chunk may be shorter. Raise ValueError if size is less than 1."""
<<<END PROMPT>>>

RESPONSE:
<<<BEGIN RESPONSE>>>
```python
def chunk(items, size):
    return [items[i:i + size] for i in range(0, len(items), size)]
```
<<<END RESPONSE>>>

=== CASE TC753 ===

REQUIREMENT TO JUDGE:

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

Stored tests for `flatten` (hidden from the model):

{"args": [[1, [2, [3, 4]], 5]], "expected": [1, 2, 3, 4, 5]}
{"args": [[]], "expected": []}
{"args": [[[[]]]], "expected": []}
{"args": [[[1], [2, [3]]]], "expected": [1, 2, 3]}

PROMPT:
<<<BEGIN PROMPT>>>
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def flatten(nested):
    """Return a flat list of the integers in nested, a list whose elements are integers or lists of the
    same kind, in left-to-right order."""
<<<END PROMPT>>>

RESPONSE:
<<<BEGIN RESPONSE>>>
```python
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
```
<<<END RESPONSE>>>

=== CASE TC785 ===

REQUIREMENT TO JUDGE:

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

Stored tests for `second_largest` (hidden from the model):

{"args": [[3, 1, 2]], "expected": 2}
{"args": [[5, 5, 4]], "expected": 4}
{"args": [[7]], "expected": null}
{"args": [[]], "expected": null}
{"args": [[-1, -2, -3]], "expected": -2}

PROMPT:
<<<BEGIN PROMPT>>>
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def second_largest(nums):
    """Return the second largest distinct value in the list nums, or None if nums has fewer than two
    distinct values."""
<<<END PROMPT>>>

RESPONSE:
<<<BEGIN RESPONSE>>>
A single pass that tracks the two largest distinct values:

```python
def second_largest(nums):
    first = second = None
    for x in nums:
        if first is None or x > first:
            first, second = x, first
        elif x != first and (second is None or x > second):
            second = x
    return second
```
<<<END RESPONSE>>>

=== CASE TC802 ===

REQUIREMENT TO JUDGE:

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

Stored tests for `run_length` (hidden from the model):

{"args": ["aaab"], "expected": "a3b1"}
{"args": [""], "expected": ""}
{"args": ["abc"], "expected": "a1b1c1"}
{"args": ["zzzz"], "expected": "z4"}

PROMPT:
<<<BEGIN PROMPT>>>
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def run_length(s):
    """Return the run-length encoding of the string s: each run of one repeated character becomes the
    character followed by the length of the run, so "aaab" becomes "a3b1"."""
<<<END PROMPT>>>

RESPONSE:
<<<BEGIN RESPONSE>>>
```python
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
```

Example:

```python
print(run_length("aaab"))  # a3b1
```
<<<END RESPONSE>>>

=== CASE TC813 ===

REQUIREMENT TO JUDGE:

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

Stored tests for `is_palindrome` (hidden from the model):

{"args": ["racecar"], "expected": true}
{"args": ["hello"], "expected": false}
{"args": [""], "expected": true}
{"args": ["Was it a car or a cat I saw"], "expected": true}
{"args": ["ab"], "expected": false}

PROMPT:
<<<BEGIN PROMPT>>>
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def is_palindrome(s):
    """Return True if the string s reads the same forwards and backwards, and False otherwise."""
<<<END PROMPT>>>

RESPONSE:
<<<BEGIN RESPONSE>>>
```python
def is_palindrome(s):
    return s == s[::-1]
```
<<<END RESPONSE>>>

=== CASE TC818 ===

REQUIREMENT TO JUDGE:

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

Stored tests for `parse_duration` (hidden from the model):

{"args": ["1h30m"], "expected": 90}
{"args": ["45m"], "expected": 45}
{"args": ["2h"], "expected": 120}
{"args": ["abc"], "raises": "ValueError"}
{"args": [""], "raises": "ValueError"}

PROMPT:
<<<BEGIN PROMPT>>>
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def parse_duration(text):
    """Parse a duration such as "1h30m", "45m" or "2h" and return the total number of minutes as an int.
    The hours part, if present, comes first. Raise ValueError if text is not such a duration."""
<<<END PROMPT>>>

RESPONSE:
<<<BEGIN RESPONSE>>>
```python
import re

_DURATION = re.compile(r"(?:(?P<h>\d+)h)?(?:(?P<m>\d+)m)?")


def parse_duration(text):
    match = _DURATION.fullmatch(text)
    if match is None or not (match.group("h") or match.group("m")):
        raise ValueError(f"not a duration: {text!r}")
    return int(match.group("h") or 0) * 60 + int(match.group("m") or 0)
```
<<<END RESPONSE>>>

=== CASE TC828 ===

REQUIREMENT TO JUDGE:

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

Stored tests for `second_largest` (hidden from the model):

{"args": [[3, 1, 2]], "expected": 2}
{"args": [[5, 5, 4]], "expected": 4}
{"args": [[7]], "expected": null}
{"args": [[]], "expected": null}
{"args": [[-1, -2, -3]], "expected": -2}

PROMPT:
<<<BEGIN PROMPT>>>
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def second_largest(nums):
    """Return the second largest distinct value in the list nums, or None if nums has fewer than two
    distinct values."""
<<<END PROMPT>>>

RESPONSE:
<<<BEGIN RESPONSE>>>
```python
def second_largest(nums):
    s = sorted(nums)
    if len(s) < 2:
        return None
    return s[-2]
```
<<<END RESPONSE>>>

=== CASE TC832 ===

REQUIREMENT TO JUDGE:

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

Stored tests for `fib` (hidden from the model):

{"args": [0], "expected": 0}
{"args": [1], "expected": 1}
{"args": [10], "expected": 55}
{"args": [30], "expected": 832040}
{"args": [80], "expected": 23416728348467685}

PROMPT:
<<<BEGIN PROMPT>>>
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def fib(n):
    """Return the n-th Fibonacci number, where fib(0) == 0 and fib(1) == 1."""
<<<END PROMPT>>>

RESPONSE:
<<<BEGIN RESPONSE>>>
```python
def fib(n):
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a
```
<<<END RESPONSE>>>

=== CASE TC833 ===

REQUIREMENT TO JUDGE:

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

Stored tests for `parse_duration` (hidden from the model):

{"args": ["1h30m"], "expected": 90}
{"args": ["45m"], "expected": 45}
{"args": ["2h"], "expected": 120}
{"args": ["abc"], "raises": "ValueError"}
{"args": [""], "raises": "ValueError"}

PROMPT:
<<<BEGIN PROMPT>>>
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def parse_duration(text):
    """Parse a duration such as "1h30m", "45m" or "2h" and return the total number of minutes as an int.
    The hours part, if present, comes first. Raise ValueError if text is not such a duration."""
<<<END PROMPT>>>

RESPONSE:
<<<BEGIN RESPONSE>>>
```python
import re

def parse_duration(text):
    m = re.fullmatch(r"(?:(\d+)h)?(?:(\d+)m)?", text)
    if not text or m is None:
        raise ValueError(f"invalid duration: {text!r}")
    hours = int(m.group(1) or 0)
    minutes = int(m.group(2) or 0)
    return hours * 60 + minutes
```
<<<END RESPONSE>>>

=== CASE TC841 ===

REQUIREMENT TO JUDGE:

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

Stored tests for `median` (hidden from the model):

{"args": [[3, 1, 2]], "expected": 2}
{"args": [[4, 1, 3, 2]], "expected": 2.5}
{"args": [[5]], "expected": 5}
{"args": [[1, 1, 2, 2]], "expected": 1.5}

PROMPT:
<<<BEGIN PROMPT>>>
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def median(nums):
    """Return the median of the non-empty list of numbers nums."""
<<<END PROMPT>>>

RESPONSE:
<<<BEGIN RESPONSE>>>
The standard library already has this:

```python
import statistics

def median(nums):
    return statistics.median(nums)
```
<<<END RESPONSE>>>

=== CASE TC850 ===

REQUIREMENT TO JUDGE:

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

Stored tests for `flatten` (hidden from the model):

{"args": [[1, [2, [3, 4]], 5]], "expected": [1, 2, 3, 4, 5]}
{"args": [[]], "expected": []}
{"args": [[[[]]]], "expected": []}
{"args": [[[1], [2, [3]]]], "expected": [1, 2, 3]}

PROMPT:
<<<BEGIN PROMPT>>>
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def flatten(nested):
    """Return a flat list of the integers in nested, a list whose elements are integers or lists of the
    same kind, in left-to-right order."""
<<<END PROMPT>>>

RESPONSE:
<<<BEGIN RESPONSE>>>
```python
def flatten(nested):
    def walk(xs):
        for x in xs:
            if isinstance(x, list):
                yield from walk(x)
            else:
                yield x
    return list(walk(nested))
```
<<<END RESPONSE>>>

=== CASE TC900 ===

REQUIREMENT TO JUDGE:

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

Stored tests for `run_length` (hidden from the model):

{"args": ["aaab"], "expected": "a3b1"}
{"args": [""], "expected": ""}
{"args": ["abc"], "expected": "a1b1c1"}
{"args": ["zzzz"], "expected": "z4"}

PROMPT:
<<<BEGIN PROMPT>>>
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def run_length(s):
    """Return the run-length encoding of the string s: each run of one repeated character becomes the
    character followed by the length of the run, so "aaab" becomes "a3b1"."""
<<<END PROMPT>>>

RESPONSE:
<<<BEGIN RESPONSE>>>
```python
from itertools import groupby

def run_length(s):
    return "".join(f"{ch}{len(list(group))}" for ch, group in groupby(s))
```
<<<END RESPONSE>>>

=== CASE TC910 ===

REQUIREMENT TO JUDGE:

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

Stored tests for `median` (hidden from the model):

{"args": [[3, 1, 2]], "expected": 2}
{"args": [[4, 1, 3, 2]], "expected": 2.5}
{"args": [[5]], "expected": 5}
{"args": [[1, 1, 2, 2]], "expected": 1.5}

PROMPT:
<<<BEGIN PROMPT>>>
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def median(nums):
    """Return the median of the non-empty list of numbers nums."""
<<<END PROMPT>>>

RESPONSE:
<<<BEGIN RESPONSE>>>
```python
def median(nums):
    s = sorted(nums)
    mid = len(s) // 2
    if len(s) % 2 == 1:
        return s[mid]
    return (s[mid - 1] + s[mid]) // 2
```
<<<END RESPONSE>>>

=== CASE TC948 ===

REQUIREMENT TO JUDGE:

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

Stored tests for `median` (hidden from the model):

{"args": [[3, 1, 2]], "expected": 2}
{"args": [[4, 1, 3, 2]], "expected": 2.5}
{"args": [[5]], "expected": 5}
{"args": [[1, 1, 2, 2]], "expected": 1.5}

PROMPT:
<<<BEGIN PROMPT>>>
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def median(nums):
    """Return the median of the non-empty list of numbers nums."""
<<<END PROMPT>>>

RESPONSE:
<<<BEGIN RESPONSE>>>
```python
def median(nums):
    s = sorted(nums)
    n = len(s)
    return (s[(n - 1) // 2] + s[n // 2]) / 2
```

For odd n both indices point at the middle element, so one formula covers both cases.
<<<END RESPONSE>>>

=== CASE TC982 ===

REQUIREMENT TO JUDGE:

1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example
   `python` or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of
   either fence line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process, with the same interpreter as the grader, and a limit of 4
   seconds of wall time for the whole task (loading the code and running every test). A task that reaches the limit
   fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from `tests.json`, where JSON
   arrays load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception
   class or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass. A model's score is the percentage of the 10 tasks it passes.

Stored tests for `run_length` (hidden from the model):

{"args": ["aaab"], "expected": "a3b1"}
{"args": [""], "expected": ""}
{"args": ["abc"], "expected": "a1b1c1"}
{"args": ["zzzz"], "expected": "z4"}

PROMPT:
<<<BEGIN PROMPT>>>
Complete the Python function below. Reply with one Python code block that contains the complete function definition. You may define helper functions. You may import only these standard-library modules: math, itertools, collections, functools, re, heapq, bisect, string, typing.

def run_length(s):
    """Return the run-length encoding of the string s: each run of one repeated character becomes the
    character followed by the length of the run, so "aaab" becomes "a3b1"."""
<<<END PROMPT>>>

RESPONSE:
<<<BEGIN RESPONSE>>>
```python
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
```
<<<END RESPONSE>>>
