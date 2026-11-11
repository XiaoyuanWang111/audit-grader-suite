"""Metamorphic and content-free cases: edits applied to a passing response of every task.

IGNORED edits must keep the verdict `pass`; FORBIDDEN edits must make it `fail` (labels from audit/CONTRACT.md).
t02 uses the normalized solution, so these cases are labeled under the stored tests (D-palindrome-normalization
reading B); the replacement is run with --palindrome normalized for them.
"""

import json
import os

from fixtures import SOL, fenced
import harness

TASKS = {}
with open(os.path.join(harness.CASE, "tasks.jsonl"), encoding="utf-8") as _f:
    for _line in _f:
        if _line.strip():
            _t = json.loads(_line)
            TASKS[_t["task_id"]] = _t
with open(os.path.join(harness.CASE, "prompt_template.txt"), encoding="utf-8") as _f:
    TEMPLATE = _f.read()

LIST_TASKS = {"t04", "t08", "t09"}   # tasks whose expected values are lists


def _after_def(task, code, line):
    ep = TASKS[task]["entry_point"]
    out = []
    for l in code.split("\n"):
        out.append(l)
        if l.startswith(f"def {ep}("):
            out.append(line)
    return "\n".join(out)


TUPLE_WRAP = (
    "\n\n_inner = {ep}\n\n"
    "def {ep}(*args):\n"
    "    r = _inner(*args)\n"
    "    if isinstance(r, list):\n"
    "        return tuple(tuple(x) if isinstance(x, list) else x for x in r)\n"
    "    return r\n"
)
PROXY_WRAP = (
    "\n\nclass _Proxy:\n"
    "    def __init__(self, v):\n"
    "        self.v = v\n"
    "    def __repr__(self):\n"
    "        return self.v if isinstance(self.v, str) else repr(self.v)\n"
    "\n_inner = {ep}\n\n"
    "def {ep}(*args):\n"
    "    return _Proxy(_inner(*args))\n"
)

IGNORED = {
    "I01-trailing-newline": lambda t, c: fenced(c) + "\n",
    "I02-blank-line-in-code": lambda t, c: fenced(c.replace(":\n", ":\n\n", 1)),
    "I03-fence-trailing-blanks": lambda t, c: "```python \t\n" + c + "\n```\t ",
    "I04-prose-around": lambda t, c: "Here is the function:\n\n" + fenced(c) + "\n\nIt runs in linear time.",
    "I05-tag-py": lambda t, c: fenced(c, "py"),
    "I06-tag-empty": lambda t, c: fenced(c, ""),
    "I07-tag-python3": lambda t, c: fenced(c, "python3"),
    "I08-tag-Python": lambda t, c: fenced(c, "Python"),
    "I09-bare-code": lambda t, c: c,
    "I10-comment-line": lambda t, c: fenced("# Solution\n" + c),
    "I11-top-level-print": lambda t, c: fenced(c + "\n\nprint(\"loaded\")"),
    "I12-print-in-function": lambda t, c: fenced(_after_def(t, c, "    print(\"debug\")")),
    "I13-non-ascii-comment": lambda t, c: fenced("# naïve — résumé ✓ 你好\n" + c),
    "I14-second-block-after": lambda t, c: fenced(c) + "\n\n" + fenced("print(\"example\")"),
    "I15-blank-line-after-fence": lambda t, c: "```python\n\n" + c + "\n```",
    "I16-typing-import": lambda t, c: fenced("from typing import List\n\n" + c),
    "I17-typographic-docstring": lambda t, c: fenced(_after_def(
        t, c, "    \"\"\"Uses “typographic quotes” and it’s fine.\"\"\"")),
    "I18-numbered-prose-before": lambda t, c: "1. Read the input.\n2. Compute the answer.\n\n" + fenced(c),
    "I19-markup-prose-before": lambda t, c: "**Solution** (in `Python`, <b>tested</b>):\n\n" + fenced(c),
}

FORBIDDEN = {
    "X01-import-os": lambda t, c: fenced("import os\n" + c),
    "X02-import-json-in-function": lambda t, c: fenced(_after_def(t, c, "    import json")),
    "X03-rename-function": lambda t, c: fenced(c.replace(f"def {TASKS[t]['entry_point']}(",
                                                         f"def {TASKS[t]['entry_point']}_impl(")),
    "X04-raise-first": lambda t, c: fenced(_after_def(t, c, "    raise RuntimeError(\"not implemented\")")),
    "X05-non-python-first-block": lambda t, c: fenced("pip install toycode", "bash") + "\n\n" + fenced(c),
    "X06-unclosed-fence": lambda t, c: "```python\n" + c + "\n",
    "X07-tuple-results": lambda t, c: fenced(c + TUPLE_WRAP.format(ep=TASKS[t]["entry_point"])),
    "X08-repr-proxy": lambda t, c: fenced(c + PROXY_WRAP.format(ep=TASKS[t]["entry_point"])),
    "X09-systemexit-in-call": lambda t, c: fenced(_after_def(t, c, "    raise SystemExit")),
    "X10-empty-block": lambda t, c: "```python\n```",
    "X11-empty-response": lambda t, c: "",
    "X12-restate-signature": lambda t, c: fenced(TASKS[t]["prompt"].rstrip("\n")),
    "X13-restate-rendered-prompt": lambda t, c: TEMPLATE.replace("{prompt}", TASKS[t]["prompt"]),
    "X14-repeated-word": lambda t, c: "a " * 300,
}


def label(edit, task):
    if edit in IGNORED:
        return "pass"
    if edit == "X07-tuple-results" and task not in LIST_TASKS:
        return "pass"   # the wrapper changes nothing when the result is not a list
    return "fail"


def cases():
    out = []
    for edit, fn in list(IGNORED.items()) + list(FORBIDDEN.items()):
        for task in sorted(TASKS):
            out.append({"id": f"{edit}|{task}", "edit": edit, "task": task,
                        "response": fn(task, SOL[task]), "label": label(edit, task)})
    return out


def grade_all():
    rows = [harness.row(c["id"], c["task"], c["response"], model="m") for c in cases()]
    from concurrent.futures import ThreadPoolExecutor
    jobs = {"grader": (), "reference": (), "replacement": ("--palindrome", "normalized")}
    with ThreadPoolExecutor(max_workers=3) as ex:
        futs = {k: ex.submit(harness.run, k, rows, sw) for k, sw in jobs.items()}
        return {k: f.result() for k, f in futs.items()}
