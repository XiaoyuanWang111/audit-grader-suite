"""Step 4 fuzzing: random responses for every (row, instruction), graded by
the grader (strict and loose harness), the reference (strict) and the
replacement. Counts exceptions per check. Seeded (random.Random(10060)).
Writes audit/work/fuzz.json; prints counts and one minimal example per error.

Usage: python audit/scripts/fuzz.py [N_PER_ROW]
"""
import collections
import json
import random
import sys

import common
import ref_runner
import replacement

N = int(sys.argv[1]) if len(sys.argv) > 1 else 40
rng = random.Random(10060)
POOL = (["the", "and", "Emma", "eagle", "bald", "Question", "My", "Answer:", "Zimbabwe", "level", "1990", "3.5",
         "1,000", "don't", "well-known", "日本", "\U0001F680", "❤️", "café"] +
        list(".,;:!?-*#\"'()[]{}/") + ["?!", "...", "—", "“", "”", "‘", "’", "<i>", "</i>",
                                         "<em>", "**", "_", "\t", "  ", "\n", "\n\n", "\n  ", "SEPARATOR", "!?!?",
                                         " ", "　", "a)", "c)", "Yes", "I know", ","])
SPECIAL = ["", " ", "\n", ".", "...", "*", "-", '"', "'", "\t\"\t", "?", "!?!", "<i></i>", "**", "\n\n\n", "a",
           "​", "#", "(", ")", "1.", "* -", "- *", '""', "''", "\"'\"", "\t", " ", "Question"]


def gen():
    if rng.random() < 0.15:
        return rng.choice(SPECIAL)
    k = rng.randint(1, 30)
    out = []
    for _ in range(k):
        tok = rng.choice(POOL)
        out.append(tok)
        out.append(rng.choice(["", " ", " ", " ", "\n"]))
    return "".join(out)


graders = {
    "grader_strict": common.grade_grader,
    "grader_loose": common.grade_grader_loose,
    "reference_strict": ref_runner.grade_reference,
    "replacement": replacement.grade,
}
rows = common.rows()
errors = collections.Counter()
calls = collections.Counter()
examples = {}
for key in common.row_list():
    r = rows[key]
    for check, kw in zip(r["instruction_id_list"], r["kwargs"]):
        cases = [gen() for _ in range(N)] + SPECIAL
        for resp in cases:
            for gn, g in graders.items():
                calls[gn] += 1
                try:
                    g(check, dict(kw), r["prompt"], resp)
                except Exception as e:  # noqa: BLE001
                    k = (gn, check, type(e).__name__ + ": " + str(e)[:60])
                    errors[k] += 1
                    if k not in examples or len(resp) < len(examples[k][1]):
                        examples[k] = (key, resp)
# Mutation fuzzing from the fixtures: reaches structured paths (CSV, MCQ, templates).
from tests.fixtures_data import FIX  # noqa: E402

MUT_TOKENS = ["", "\t", "\t\t", '"', '""', ",", ",,", "\n", "\n\n", " ", "*", "-", "?", "!", ".", "“", "'"]


def mutate(s):
    s = list(s)
    for _ in range(rng.randint(1, 4)):
        op = rng.random()
        i = rng.randrange(len(s) + 1)
        if op < 0.4 and s:
            del s[min(i, len(s) - 1)]
        elif op < 0.8:
            s.insert(i, rng.choice(MUT_TOKENS))
        elif s:
            j = rng.randrange(len(s))
            s[i:i] = s[j:j + rng.randint(1, 10)]
    return "".join(s)


for f in FIX:
    kw, prompt = common.kwargs_for(f["key"], f["check"], f["kw"])
    for _ in range(N):
        resp = mutate(f["response"])
        for gn, g in graders.items():
            calls[gn] += 1
            try:
                g(f["check"], dict(kw), prompt, resp)
            except Exception as e:  # noqa: BLE001
                k = (gn, f["check"], type(e).__name__ + ": " + str(e)[:60])
                errors[k] += 1
                if k not in examples or len(resp) < len(examples[k][1]):
                    examples[k] = (f["key"], resp)

out = [dict(grader=g, check=c, error=e, count=n, example_key=examples[(g, c, e)][0], example=examples[(g, c, e)][1])
       for (g, c, e), n in sorted(errors.items())]
(common.W / "audit" / "work" / "fuzz.json").write_text(json.dumps(dict(calls=calls, errors=out), indent=1, ensure_ascii=False),
                                                       encoding="utf-8", newline="\n")
print("calls per grader:", dict(calls))
for o in out:
    print(f"{o['grader']:<17} {o['check']:<34} {o['count']:>5}  {o['error']}  | key={o['example_key']} example={o['example']!r}")
