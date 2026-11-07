"""Step 4: property tests, metamorphic tests, content-free responses and a seeded fuzzer.

Usage (from the audit run directory): python audit/scripts/stress.py [--fuzz N] [--seed S]
Writes audit/work/stress_summary.json and prints counts. A verdict is "pass", "fail" or "crash" (an exception escaped
the grader). The replacement runs with the proposed readings unless noted.
"""

import argparse
import collections
import json
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CASE = os.path.join(ROOT, "case")
WORK = os.path.join(ROOT, "audit", "work")
for p in (CASE, os.path.join(CASE, "reference"), HERE, os.path.join(ROOT, "audit", "tests")):
    sys.path.insert(0, p)

import contract_grader  # noqa: E402
import grade  # noqa: E402
import harness_ref  # noqa: E402
from fixtures import CORRECT  # noqa: E402

with open(os.path.join(CASE, "tasks.jsonl"), encoding="utf-8") as f:
    TASKS = {t["task_id"]: t for t in map(json.loads, filter(str.strip, f))}
with open(os.path.join(CASE, "tests.json"), encoding="utf-8") as f:
    TESTS = json.load(f)
with open(os.path.join(CASE, "responses.jsonl"), encoding="utf-8") as f:
    RESPONSES = [json.loads(l) for l in f if l.strip()]
with open(os.path.join(CASE, "prompt_template.txt"), encoding="utf-8") as f:
    TEMPLATE = f.read()
GRADERS = ("grader", "reference", "replacement")
PROPOSED = dict(contract_grader.PROPOSED)
FIXES_ONLY = dict(contract_grader.FIXES_ONLY)


def verdict(which, task_id, response, decisions=None):
    task, tests = TASKS[task_id], TESTS[task_id]
    try:
        if which == "grader":
            ok = grade.grade_response(task, tests, response)[0]
        elif which == "reference":
            ok = harness_ref.passes(harness_ref.code_of(response), task["entry_point"], tests)
        else:
            ok = contract_grader.grade_response(task, tests, response, decisions or PROPOSED)[0]
        return "pass" if ok else "fail"
    except Exception as exc:  # noqa: BLE001
        return "crash:" + type(exc).__name__


def all_verdicts(task_id, response):
    return {g: verdict(g, task_id, response) for g in GRADERS}


# ---------------------------------------------------------------- content-free responses

def content_free(task_id):
    prompt = TASKS[task_id]["prompt"]
    return {
        "empty": "",
        "whitespace": "  \n\n\t\n",
        "repeated_word": "the " * 200,
        "repeated_dash_6000": "-" * 6000,
        "refusal": "I'm sorry, but I can't help with that.",
        "restated_instructions": TEMPLATE.replace("{prompt}", prompt),
        "restated_signature_block": "```python\n" + prompt + "```\n",
        "stub_raise": "```python\n" + prompt + "    raise NotImplementedError\n```\n",
        "pass_only": "```python\npass\n```\n",
    }


# ---------------------------------------------------------------- edits of stored responses

FENCE_PY = re.compile(r"^```python[ \t]*$", re.MULTILINE)


def first_block_span(response):
    """(start, end) of the code of the first block, by the contract's rule; None when there is no block."""
    lines = response.split("\n")
    first = next((i for i, l in enumerate(lines) if contract_grader.FENCE_LINE.match(l)), None)
    if first is None:
        return None
    for j in range(first + 1, len(lines)):
        m = contract_grader.FENCE_LINE.match(lines[j])
        if m and m.group(1) == "":
            return first, j
    return None


def edit_code(response, fn):
    """Apply fn to the graded code (the first block, or the whole response when it has none)."""
    span = first_block_span(response)
    if span is None:
        return fn(response)
    lines = response.split("\n")
    first, j = span
    code = "\n".join(lines[first + 1:j])
    return "\n".join(lines[:first + 1] + fn(code).split("\n") + lines[j:])


def entry_def(code, name):
    return re.search(r"^def " + re.escape(name) + r"\(.*\):[ \t]*$", code, re.MULTILINE)


INVARIANT_EDITS = {
    "append_prose": lambda r, t: r + "\n\nThis runs in linear time.\n",
    "print_at_load": lambda r, t: edit_code(r, lambda c: "print('loading')\n" + c),
    "helper_named_main": lambda r, t: edit_code(r, lambda c: c + "\n\ndef main():\n    return None\n"),
    "fence_trailing_spaces": lambda r, t: FENCE_PY.sub("```python  ", r).replace("\n```\n", "\n```  \n"),
    "retag_py": lambda r, t: FENCE_PY.sub("```py", r),
    "retag_none": lambda r, t: FENCE_PY.sub("```", r),
}


def _raise_first(code, name):
    m = entry_def(code, name)
    if m is None:
        return code
    return code[:m.end()] + "\n    raise RuntimeError('edit')" + code[m.end():]


TUPLIFY = ("\n\ndef _tuplify(x):\n    return tuple(_tuplify(v) for v in x) if isinstance(x, list) else x\n")


def _tuple_returns(code, name):
    m = entry_def(code, name)
    if m is None:
        return code
    renamed = code.replace("def " + name + "(", "def _orig_" + name + "(", 1)
    renamed = re.sub(r"\b" + re.escape(name) + r"\(", "_orig_" + name + "(", renamed)
    return renamed + TUPLIFY + f"\n\ndef {name}(*args):\n    return _tuplify(_orig_{name}(*args))\n"


MUST_FAIL_EDITS = {
    "rename_entry_point": lambda r, t: edit_code(r, lambda c: c.replace("def " + TASKS[t]["entry_point"] + "(",
                                                                        "def " + TASKS[t]["entry_point"] + "_x(", 1)),
    "raise_at_entry": lambda r, t: edit_code(r, lambda c: _raise_first(c, TASKS[t]["entry_point"])),
    "import_os": lambda r, t: edit_code(r, lambda c: "import os\n" + c),
    "drop_closing_fence": lambda r, t: (r[:r.rindex("\n```")] + "\n") if first_block_span(r) else None,
    "tuple_results": lambda r, t: (edit_code(r, lambda c: _tuple_returns(c, TASKS[t]["entry_point"]))
                                   if t in ("t04", "t08", "t09") else None),
}


# ---------------------------------------------------------------- fuzzer

def fuzz_case(rng, task_id):
    name = TASKS[task_id]["entry_point"]
    good = CORRECT.get(task_id, "def " + name + "(*args):\n    return None\n")
    body = rng.choice([
        ("correct", good),
        ("wrong_name", good.replace("def " + name + "(", "def " + name + "2(", 1)),
        ("raises", "def " + name + "(*args):\n    raise KeyError('x')\n"),
        ("returns_none", "def " + name + "(*args):\n    return None\n"),
        ("prints", "print('hi')\n" + good),
        ("allowed_import", "import itertools\n" + good),
        ("banned_import", "import sys\n" + good),
        ("relative_import", "from . import math\n" + good),
        ("dynamic_import", "_m = __import__('math')\n" + good),
        ("deep_sum", good + "\nx = " + "+".join(["1"] * rng.choice([100, 2996, 2997, 5000])) + "\n"),
        ("dashes", "-" * rng.choice([100, 5964, 5965, 9000])),
        ("null_byte", good + "\n# \x00\n"),
        ("non_ascii", "# café ≤ 中文\n" + good),
        ("lone_surrogate", "# \ud800\n" + good),
        ("syntax_error", "def " + name + "(:\n    pass\n"),
        ("load_error", good + "\nraise ValueError('at load')\n"),
        ("main_guard", good + "\nif __name__ == '__main__':\n    raise SystemExit(3)\n"),
    ])
    fence = rng.choice([("python", "```python\n", "```\n"), ("py", "```py\n", "```\n"), ("bare", "```\n", "```\n"),
                        ("none", "", ""), ("unclosed", "```python\n", ""), ("indented", "  ```python\n", "  ```\n"),
                        ("four", "````python\n", "````\n"), ("trailing_ws", "```python \t\n", "``` \n")])
    prose_before = rng.choice(["", "Here is the function:\n\n", "Usage:\n\n```\n>>> " + name + "()\n```\n\n"])
    prose_after = rng.choice(["", "\nThis is efficient.\n"])
    response = prose_before + fence[1] + body[1] + ("" if body[1].endswith("\n") else "\n") + fence[2] + prose_after
    crlf = rng.random() < 0.15
    if crlf:
        response = response.replace("\n", "\r\n")
    return {"task_id": task_id, "body": body[0], "fence": fence[0], "prose_before": bool(prose_before),
            "crlf": crlf, "response": response}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fuzz", type=int, default=300)
    ap.add_argument("--seed", type=int, default=20261106)
    args = ap.parse_args()
    summary = {}

    # content-free responses: which tasks each one passes
    cf = collections.defaultdict(lambda: collections.defaultdict(list))
    for t in sorted(TASKS):
        for kind, response in content_free(t).items():
            for g, v in all_verdicts(t, response).items():
                cf[kind][g].append(f"{t}:{v}")
    summary["content_free"] = {k: {g: {"passes": [x.split(":")[0] for x in v if x.endswith(":pass")],
                                       "crashes": [x for x in v if ":crash" in x]} for g, v in d.items()}
                               for k, d in cf.items()}
    print("Content-free responses: tasks passed (of 10) and crashes, grader / reference / replacement")
    for k, d in summary["content_free"].items():
        print(f"  {k:<26} " + " / ".join(f"{len(d[g]['passes'])} pass, {len(d[g]['crashes'])} crash" for g in GRADERS))

    # metamorphic: invariant edits (stored responses that do not time out)
    base = {r["id"]: all_verdicts(r["task_id"], r["response"]) for r in RESPONSES}
    slow = {"c26", "c38"}  # the two stored responses that reach the time limit; edits keep them slow
    inv = collections.defaultdict(lambda: collections.defaultdict(list))
    applicable = collections.Counter()
    for r in RESPONSES:
        if r["id"] in slow:
            continue
        for name, edit in INVARIANT_EDITS.items():
            edited = edit(r["response"], r["task_id"])
            if edited == r["response"]:
                continue
            applicable[name] += 1
            for g, v in all_verdicts(r["task_id"], edited).items():
                if v != base[r["id"]][g]:
                    inv[name][g].append(f"{r['id']}:{base[r['id']][g]}->{v}")
    summary["invariant_edits"] = {n: {"applied": applicable[n], **{g: inv[n][g] for g in GRADERS}}
                                  for n in INVARIANT_EDITS}
    print("\nEdits the contract ignores (verdict changes, grader / reference / replacement):")
    for n, d in summary["invariant_edits"].items():
        print(f"  {n:<24} applied to {d['applied']:>2}: " + " / ".join(str(len(d[g])) for g in GRADERS)
              + "   " + "; ".join(f"{g}: {' '.join(d[g])}" for g in GRADERS if d[g]))

    # metamorphic: edits the contract forbids, applied to responses the replacement passes
    must = collections.defaultdict(lambda: collections.defaultdict(list))
    tried = collections.Counter()
    passing = [r for r in RESPONSES if base[r["id"]]["replacement"] == "pass"]
    for r in passing:
        for name, edit in MUST_FAIL_EDITS.items():
            edited = edit(r["response"], r["task_id"])
            if edited is None or edited == r["response"]:
                continue
            tried[name] += 1
            for g, v in all_verdicts(r["task_id"], edited).items():
                if v != "fail":
                    must[name][g].append(f"{r['id']}:{v}")
    summary["must_fail_edits"] = {n: {"applied": tried[n], **{g: must[n][g] for g in GRADERS}} for n in MUST_FAIL_EDITS}
    print(f"\nEdits the contract forbids, on the {len(passing)} responses the replacement passes "
          "(verdicts that are not fail, grader / reference / replacement):")
    for n, d in summary["must_fail_edits"].items():
        print(f"  {n:<20} applied to {d['applied']:>2}: " + " / ".join(str(len(d[g])) for g in GRADERS)
              + "   " + "; ".join(f"{g}: {' '.join(d[g])}" for g in GRADERS if d[g]))

    # fuzzer
    rng = random.Random(args.seed)
    cases = [fuzz_case(rng, rng.choice(sorted(TASKS))) for _ in range(args.fuzz)]
    crashes = collections.Counter()
    disagree = collections.Counter()
    disagree_ref = collections.Counter()
    examples = {}
    for i, c in enumerate(cases):
        v = all_verdicts(c["task_id"], c["response"])
        fixes = verdict("replacement", c["task_id"], c["response"], FIXES_ONLY)
        for g in GRADERS:
            if v[g].startswith("crash"):
                crashes[(g, v[g], c["body"])] += 1
                examples.setdefault(f"{g} {v[g]} {c['body']}", i)
        if v["grader"] != fixes:
            key = (v["grader"], fixes, c["body"], c["fence"], "crlf" if c["crlf"] else "lf",
                   "prose" if c["prose_before"] else "")
            disagree[key] += 1
        if v["reference"] != fixes:
            disagree_ref[(v["reference"], fixes, c["body"], c["fence"], "crlf" if c["crlf"] else "lf")] += 1
    summary["fuzz"] = {"seed": args.seed, "cases": len(cases),
                       "crashes": {" | ".join(k): n for k, n in sorted(crashes.items())},
                       "grader_vs_fixes_only": {" | ".join(k): n for k, n in sorted(disagree.items())},
                       "reference_vs_fixes_only": {" | ".join(k): n for k, n in sorted(disagree_ref.items())},
                       "crash_examples": examples}
    with open(os.path.join(WORK, "fuzz_cases.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        for i, c in enumerate(cases):
            f.write(json.dumps(dict(c, index=i)) + "\n")
    print(f"\nFuzz: {len(cases)} cases, seed {args.seed}")
    print("  crashes (grader | exception | body):")
    for k, n in sorted(crashes.items()):
        print(f"    {n:>3}  {' | '.join(k)}")
    print(f"  grader vs replacement fixes-only: {sum(disagree.values())} disagreements")
    for k, n in sorted(disagree.items(), key=lambda kv: -kv[1]):
        print(f"    {n:>3}  grader={k[0]} fixes={k[1]} body={k[2]} fence={k[3]} {k[4]} {k[5]}")
    print(f"  reference vs replacement fixes-only: {sum(disagree_ref.values())} disagreements")
    for k, n in sorted(disagree_ref.items(), key=lambda kv: -kv[1]):
        print(f"    {n:>3}  reference={k[0]} fixes={k[1]} body={k[2]} fence={k[3]} {k[4]}")
    with open(os.path.join(WORK, "stress_summary.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(summary, f, indent=1)


if __name__ == "__main__":
    main()
