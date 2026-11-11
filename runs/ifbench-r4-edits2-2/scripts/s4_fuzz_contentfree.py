"""Step 4: fuzzing and content-free responses.

Fuzz: for every one of the 344 instruction instances in the dataset (real kwargs and prompt),
grade FUZZ_N generated strings with the grader, the reference and the replacement, through
their harness functions, and count exceptions per check. Generated strings mix random
Unicode, words with punctuation and markup, CSV-like lines with empty fields, nested
brackets and quotes, numbered lists and unclosed think tags (seeded, deterministic).

Content-free: grade the empty string, whitespace, repeated text, the prompt itself and the
prompt's last sentence (a restatement of the instruction) for every instance; list the
checks they pass under each grader.

Writes audit/work/fuzz.json and audit/work/contentfree.json.
"""
import json
import os
import random
import sys
from collections import Counter, defaultdict

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(W, "audit", "lib"))
import graders as G  # noqa: E402
import pyarrow.parquet as pq  # noqa: E402

FUZZ_N = int(os.environ.get("FUZZ_N", "60"))
rows = pq.read_table(os.path.join(W, "case", "data", "train-00000-of-00001.parquet")).to_pylist()
inst = []
for r in rows:
    for iid, kw in zip(r["instruction_id_list"], r["kwargs"]):
        inst.append((r["key"], iid, {k: v for k, v in kw.items() if v is not None}, r["prompt"]))

rng = random.Random(10060)
VOCAB = ["the", "and", "Emma", "door", "level", "radar", "1999", "3.14", "**bold**", "*", "-", "—",
         "“quote”", "'single'", "\"double\"", "(", ")", "[", "]", "{", "}", "<i>", "</i>", "<em>",
         "!?", "?!", "...", "…", ";", ":", ",", ".", "!", "?", "\U0001F600", "\U0001F1FA\U0001F1F8",
         "すし", "寿司", "My Answer:", "My Conclusion:", "Future Outlook:", "Question 1:",
         "A)", "B)", "Zimbabwe", "Zambia", "Reykjavik", "1796-04-12", "14", "21", "\t", "\n", "\n\n", "  ",
         "<think>", "</think>", "​", " ", "don't", "don’t", "Imagine", "eagle", "elgae dlab"]


def gen():
    k = rng.randrange(8)
    if k == 0:
        return "".join(chr(rng.choice([rng.randrange(32, 127), rng.randrange(0x80, 0x3000),
                                       rng.randrange(0x1F300, 0x1FAFF)])) for _ in range(rng.randrange(1, 80)))
    if k == 1:
        return " ".join(rng.choice(VOCAB) for _ in range(rng.randrange(1, 60)))
    if k == 2:  # CSV-like with empty fields and quotes
        delim = rng.choice([",", "\t"])
        lines = []
        for _ in range(rng.randrange(1, 18)):
            fields = [rng.choice(["", '""', '"x"', "y", '"a,b"', " ", '"', "1"]) for _ in range(rng.randrange(1, 7))]
            lines.append(delim.join(fields))
        return rng.choice(["", "StudentID\tSubject\tGrade\tSemester\tScore\n",
                           "ProductID,Category,Brand,Price,Stock\n", "ID,Country,City,Year,Count\n"]) + "\n".join(lines)
    if k == 3:  # brackets and quotes
        return "".join(rng.choice("()[]{}\"'“”‘’ ab") for _ in range(rng.randrange(1, 60)))
    if k == 4:  # numbered list
        return "\n".join(f"{i}. " + " ".join(rng.choice(VOCAB) for _ in range(rng.randrange(0, 8)))
                         for i in range(1, rng.randrange(2, 12)))
    if k == 5:  # punctuation only
        return "".join(rng.choice(".,!?;:-—*#") for _ in range(rng.randrange(1, 12)))
    if k == 6:  # unclosed think
        return "<think>" + " ".join(rng.choice(VOCAB) for _ in range(rng.randrange(1, 30)))
    return rng.choice(["a", ".", "-", "*", "1", "。", "\U0001F600", "x\n\ny", " \n.", "?!"])


def run(fn, iid, kw, resp, prompt):
    try:
        return "pass" if fn(iid, kw, resp, prompt=prompt) else "fail", None
    except Exception as e:  # noqa: BLE001
        return "exc", f"{type(e).__name__}: {str(e)[:80]}"


WHO = {"grader": G.grade_grader, "reference": G.grade_reference, "replacement": G.grade_replacement}

fuzz_exc = {w: Counter() for w in WHO}
fuzz_examples = {w: {} for w in WHO}
fuzz_total = 0
for key, iid, kw, prompt in inst:
    for _ in range(FUZZ_N):
        resp = gen()
        fuzz_total += 1
        for w, fn in WHO.items():
            v, err = run(fn, iid, kw, resp, prompt)
            if v == "exc":
                fuzz_exc[w][iid] += 1
                fuzz_examples[w].setdefault(iid, {"key": key, "response": resp, "error": err})
json.dump({"n_per_instance": FUZZ_N, "total": fuzz_total, "exceptions": {w: dict(c) for w, c in fuzz_exc.items()},
           "examples": fuzz_examples}, open(os.path.join(W, "audit", "work", "fuzz.json"), "w", encoding="utf-8"),
          indent=1, ensure_ascii=False)
print(f"fuzz: {fuzz_total} generated responses x 3 graders")
for w in WHO:
    print(f"  {w}: {sum(fuzz_exc[w].values())} exceptions: {dict(fuzz_exc[w])}")
    for iid, ex in fuzz_examples[w].items():
        print(f"     e.g. {iid} key={ex['key']} {ex['error']} response={ex['response'][:60]!r}")


def last_sentence(p):
    parts = [x for x in p.replace("\n", " ").split(". ") if x.strip()]
    return (parts[-1].strip() + ("" if parts[-1].strip().endswith(".") else ".")) if parts else p


CF = {
    "empty": lambda p: "",
    "whitespace": lambda p: "   \n  ",
    "repeated_word": lambda p: " ".join(["word"] * 60),
    "repeated_sentence": lambda p: " ".join(["This is a sentence."] * 20),
    "prompt_restated": lambda p: p,
    "instruction_restated": last_sentence,
}
cf = {w: defaultdict(list) for w in WHO}
for key, iid, kw, prompt in inst:
    for name, mk in CF.items():
        resp = mk(prompt)
        for w, fn in WHO.items():
            v, err = run(fn, iid, kw, resp, prompt)
            if v == "pass":
                cf[w][name].append(f"{iid} (key {key})")
            elif v == "exc":
                cf[w][name].append(f"EXC {iid} (key {key}) {err}")
json.dump({w: dict(d) for w, d in cf.items()}, open(os.path.join(W, "audit", "work", "contentfree.json"), "w",
                                                   encoding="utf-8"), indent=1, ensure_ascii=False)
for w in WHO:
    print(f"content-free passes, {w}:")
    for name in CF:
        lst = cf[w].get(name, [])
        print(f"  {name:22s} {len(lst):3d} of {len(inst)}  checks: {sorted(set(x.split(' (')[0] for x in lst))}")
