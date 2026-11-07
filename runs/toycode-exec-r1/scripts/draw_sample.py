"""Step 6.1 to 6.3: draw, freeze and render the blinded review sample (round 1). Reviews are not run here.

Usage (from the audit run directory): python audit/scripts/draw_sample.py
Reads the step-5 verdict files in audit/work/ and writes, under audit/frozen/:
  review_r1_cases.jsonl     the case list (opaque id, task, requirement, prompt, response), no source or verdicts
  review_r1_keys.jsonl      each case's source row, model, stratum and every grader's verdict (not for reviewers)
  review_r1_batch_A.md      cases in reviewer A's order
  review_r1_batch_B.md      cases in reviewer B's order
  review_r1_reviewer_prompt.md, print_case.py (the helper that prints a case's exact response)
Prints the population and sample size of each stratum and the sha256 of every file.
"""

import hashlib
import json
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CASE = os.path.join(ROOT, "case")
WORK = os.path.join(ROOT, "audit", "work")
FROZEN = os.path.join(ROOT, "audit", "frozen")
SEED = 20261106          # opaque ids and the agreement-stratum draw
ORDER_SEEDS = {"A": 1, "B": 2}
SAMPLE = {"disagree": None, "agree": None}  # None = every case of the stratum (the population is 40 verdicts)


def load(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def write_text(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


RULE = """\
The ToyCode grading rule (from the benchmark's README), which every case below is judged by:
1. Code extraction. The code is the content of the first fenced code block in the response. A fenced block is a line
   made of three backticks and an optional language tag (ASCII letters, digits, `_`, `+` or `-`, for example `python`
   or `py`), then the code lines, then the next line made of three backticks; spaces or tabs at the end of either fence
   line are allowed. If the response has no fenced block, the whole response is the code.
2. Import check. The code is parsed with Python's `ast` module. The task fails if the code does not parse, or if any
   `import` or `from ... import` statement names a module that is not on the prompt's list (modules are compared by
   the part of the name before the first dot; a relative import is not on the list).
3. Execution. The code runs in a fresh Python process (CPython 3.12) with a limit of 4 seconds of wall time for the
   whole task (loading the code and running every test). A task that reaches the limit fails.
4. Tests. Each test calls the task's function with a fresh copy of the test's arguments. A test with `expected`
   passes when the return value is equal (Python `==`) to the expected value as loaded from JSON, where JSON arrays
   load as lists and `null` as `None`. A test with `raises` passes when the call raises that built-in exception class
   or a subclass of it. Any other exception raised by the call fails the test, and so does a missing function.
5. A task passes when all of its tests pass.
The tests are hidden from the model."""

PREAMBLE = """\
How to read this file. Each case starts with a line `=== CASE <id> ===`. `CHECK` names the task, and `REQUIREMENT TO
JUDGE` gives the function's name and the task's stored tests, one JSON object per line, which are the reference
answer; the case passes only under the grading rule printed once below. The text between `<<<PROMPT BEGIN>>>` and
`<<<PROMPT END>>>` is the exact message the model received. The text between `<<<RESPONSE BEGIN>>>` and
`<<<RESPONSE END>>>` is the model's exact response; the markers sit on their own lines, so a blank line or space just
inside them is part of the response. To see the response byte for byte, or to run its code, use the helper named in
your instructions; it prints the response exactly.
"""


def main():
    tasks = {t["task_id"]: t for t in load(os.path.join(CASE, "tasks.jsonl"))}
    with open(os.path.join(CASE, "tests.json"), encoding="utf-8") as f:
        tests = json.load(f)
    with open(os.path.join(CASE, "prompt_template.txt"), encoding="utf-8") as f:
        template = f.read()
    responses = load(os.path.join(CASE, "responses.jsonl"))
    verdicts = {name: {r["id"]: r["verdict"] for r in load(os.path.join(WORK, f"panel_{name}.jsonl"))}
                for name in ("grader", "reference", "fixes_only", "proposed")}

    strata = {"disagree": [], "agree": []}
    for r in responses:
        strata["disagree" if verdicts["grader"][r["id"]] != verdicts["proposed"][r["id"]] else "agree"].append(r)
    rng = random.Random(SEED)
    chosen = []
    for name, rows in strata.items():
        n = len(rows) if SAMPLE[name] is None else SAMPLE[name]
        picked = rows if n == len(rows) else rng.sample(rows, n)
        chosen += [(name, r) for r in picked]
        print(f"stratum {name}: population {len(rows)}, sampled {len(picked)}")
    rng.shuffle(chosen)
    cases, keys = [], []
    for k, (stratum, r) in enumerate(chosen, start=1):
        cid = f"K{k:02d}"
        t = tasks[r["task_id"]]
        requirement = (f"Function `{t['entry_point']}`. The stored tests (hidden from the model), each a JSON object with "
                       f"`args` and either `expected` or `raises`:\n" + "\n".join(json.dumps(x) for x in tests[r["task_id"]]))
        cases.append({"case_id": cid, "check": f"ToyCode task {r['task_id']} ({t['entry_point']})",
                      "requirement": requirement, "prompt": template.replace("{prompt}", t["prompt"]),
                      "response": r["response"]})
        keys.append({"case_id": cid, "response_id": r["id"], "model": r["model"], "task_id": r["task_id"],
                     "stratum": stratum, **{f"verdict_{n}": verdicts[n][r["id"]] for n in verdicts}})

    os.makedirs(FROZEN, exist_ok=True)
    cases_path = os.path.join(FROZEN, "review_r1_cases.jsonl")
    keys_path = os.path.join(FROZEN, "review_r1_keys.jsonl")
    write_text(cases_path, "".join(json.dumps(c) + "\n" for c in cases))
    write_text(keys_path, "".join(json.dumps(k) + "\n" for k in keys))

    for reviewer, seed in ORDER_SEEDS.items():
        order = list(cases)
        random.Random(seed).shuffle(order)
        parts = [PREAMBLE, "\n" + RULE + "\n"]
        for c in order:
            parts.append(f"\n=== CASE {c['case_id']} ===\nCHECK: {c['check']}\nREQUIREMENT TO JUDGE:\n{c['requirement']}\n"
                         f"<<<PROMPT BEGIN>>>\n{c['prompt']}\n<<<PROMPT END>>>\n"
                         f"<<<RESPONSE BEGIN>>>\n{c['response']}\n<<<RESPONSE END>>>\n")
        write_text(os.path.join(FROZEN, f"review_r1_batch_{reviewer}.md"), "".join(parts))

    write_text(os.path.join(FROZEN, "print_case.py"), HELPER)
    write_text(os.path.join(FROZEN, "review_r1_reviewer_prompt.md"), REVIEWER_PROMPT)
    for name in sorted(os.listdir(FROZEN)):
        print(sha(os.path.join(FROZEN, name)), name)


HELPER = '''"""Print the exact response of one review case: python audit/frozen/print_case.py K07 [--code]

--code prints only the code that rule 1 of the grading rule extracts, ready to run with: ... --code > case.py
"""
import json
import os
import re
import sys

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "review_r1_cases.jsonl")
FENCE = re.compile(r"```([A-Za-z0-9_+\\-]*)[ \\t]*\\Z")


def extract(text):
    lines = text.split("\\n")
    first = next((i for i, l in enumerate(lines) if FENCE.match(l)), None)
    if first is not None:
        for j in range(first + 1, len(lines)):
            m = FENCE.match(lines[j])
            if m and m.group(1) == "":
                return "\\n".join(lines[first + 1:j]) + "\\n"
    return text


def main():
    case_id = sys.argv[1]
    with open(PATH, encoding="utf-8") as f:
        for line in f:
            c = json.loads(line)
            if c["case_id"] == case_id:
                text = extract(c["response"]) if "--code" in sys.argv[2:] else c["response"]
                sys.stdout.write(text)
                return
    sys.exit("no such case: " + case_id)


if __name__ == "__main__":
    main()
'''

REVIEWER_PROMPT = """\
You are an independent reviewer for ToyCode 1.0, a benchmark of Python function completions graded by running the code. Your labels will be compared with automatic graders that you will never see, so they must come only from your own reading of the requirement text.

Your batch file: audit/frozen/review_r1_batch_<A or B>.md
Write your results to: audit/frozen/review_r1_labels_<A or B>.jsonl

For every case in the batch, decide whether the RESPONSE satisfies the single REQUIREMENT TO JUDGE, the way a careful human grader would who reads the requirement literally.

Rules:
1. Judge only that one requirement. Ignore every other requirement in the prompt, and ignore whether the content is correct, useful or well written unless the requirement is about that. Judge against the reference answer as given: the stored tests and the grading rule at the top of the batch. Do not use your own knowledge of the facts. If the reference answer looks wrong, set verdict ambiguous and say why.
2. Go by the requirement's own words. If a phrase has more than one reasonable reading and the readings give different verdicts, set verdict "ambiguous", name the readings in the reason, and still give your "lean": the verdict under the reading you find most natural.
3. When the requirement involves counting, positions, ratios, overlap or ordering, compute it with code instead of estimating it. This helper prints the exact response of a case: python audit/frozen/print_case.py <case id> (add --code to print only the extracted code). If a case says its response is truncated, read the full text from the file it names.
4. Independence: read only your batch file, the helper above, and the full-response files your batch names. Do not open, list or search any other file or folder, and do not use the web. Do not look for or reimplement grader code; reason from the requirement text.
5. Quoting: never copy more than ten consecutive words of any prompt or response into your messages, printed output or reasons, and never reproduce song lyrics, poems or other published text from memory. Paraphrase or give counts instead. When a script prints text, print only short snippets or counts.
6. Write as you go: after judging each case, append its line to the output file, so that partial work is kept. One JSON object per line, in the batch's case order, with exactly these fields: "case_id", "verdict" ("pass", "fail" or "ambiguous"), "lean" ("pass" or "fail"), "confidence" ("high", "medium" or "low"), "reason" (at most 40 words: the deciding fact or the numbers you computed). Every case must appear exactly once. If the file already has lines from an earlier attempt, keep them and continue after the last case written.
7. When done, reply with one line: the number of cases written and the count of each verdict.
"""


if __name__ == "__main__":
    main()
