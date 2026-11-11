"""Fuzz every check of graders A and B and the replacement with random text (step 4).

Inputs mix random Unicode, markdown fragments, words, whitespace and a few pathological shapes
(deep JSON nesting, long runs). kwargs come from the data (up to 10 distinct per check). Fixed seed.
Counts exceptions per check and grader; an exception is a grading failure, not a model failure.
Writes audit/out/fuzz.json.
"""
import collections
import json
import random
import sys
from pathlib import Path

W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W / "audit" / "lib"))
import contract_grader as cg  # noqa: E402
import graders_under_audit as gu  # noqa: E402

FRAGMENTS = ["*", "**", "***", "* * *", "-", "---", "[", "]", "[]", "<<", ">>", "<<a b>>", "\n", "\n\n", "\n\n\n",
             "P.S.", "P.P.S", "SECTION 1", "Section 2", "```json", "```", "{", "}", "\"", "“", "”", ",", "，", ".", "!",
             "?", "…", "the", "The", "sale", "wholesale", "Hello", "hello", "I", "a", "1", "2", " ", "\t", "é", "你好",
             "Привет", "مرحبا", "My answer is yes.", "******", "#", "> ", "'", "don't", "e.g.", "Dr."]


def random_text(rng):
    shape = rng.random()
    if shape < 0.03:
        return ""
    if shape < 0.06:
        return " " * rng.randint(1, 5)
    if shape < 0.08:
        return "[" * rng.randint(1000, 5000)
    if shape < 0.10:
        return "".join(chr(rng.randint(0x20, 0x2FFF)) for _ in range(rng.randint(1, 200)))
    parts = [rng.choice(FRAGMENTS) for _ in range(rng.randint(1, 40))]
    sep = rng.choice(["", " ", "\n"])
    return sep.join(parts)


def main(n_per_check=400):
    rng = random.Random(20261111)
    rows = gu.load_rows()
    kwargs_by_check = collections.defaultdict(list)
    for row in rows:
        for iid, kw in zip(row["record"]["instruction_id_list"], row["record"]["kwargs"]):
            key = json.dumps(kw, sort_keys=True)
            if key not in {json.dumps(k, sort_keys=True) for k in kwargs_by_check[iid]} and len(kwargs_by_check[iid]) < 10:
                kwargs_by_check[iid].append(kw)
    counts = collections.defaultdict(collections.Counter)
    examples = {}
    for iid in sorted(kwargs_by_check):
        for i in range(n_per_check):
            kw = kwargs_by_check[iid][i % len(kwargs_by_check[iid])]
            text = random_text(rng)
            counts[iid]["inputs"] += 1
            a = gu.check_a(iid, kw, gu.extract_a(text))
            if isinstance(a, str):
                counts[iid]["A_exceptions"] += 1
                examples.setdefault((iid, "A", a.split(":")[1].strip()), (repr(text[:60]), a[:120]))
            b = gu.check_b(iid, kw, gu.extract_b(text))
            if isinstance(b, str):
                counts[iid]["B_exceptions"] += 1
                examples.setdefault((iid, "B", b.split(":")[1].strip()), (repr(text[:60]), b[:120]))
            try:
                cg.check(iid, kw, text)
            except Exception as error:  # noqa: BLE001
                counts[iid]["R_exceptions"] += 1
                examples.setdefault((iid, "R", type(error).__name__), (repr(text[:60]), repr(error)[:120]))
    total = collections.Counter()
    for iid, c in counts.items():
        total.update(c)
        if c["A_exceptions"] or c["B_exceptions"] or c["R_exceptions"]:
            print(f"{iid:<45} inputs={c['inputs']} A_exc={c['A_exceptions']} B_exc={c['B_exceptions']} R_exc={c['R_exceptions']}")
    print("total", dict(total))
    for (iid, g, kind), (text, err) in sorted(examples.items()):
        print("  example", g, iid, kind, text[:50], "->", err[:100])
    (W / "audit" / "out" / "fuzz.json").write_text(json.dumps(
        {"counts": {k: dict(v) for k, v in counts.items()}, "total": dict(total),
         "examples": [[k[0], k[1], k[2], v[0], v[1]] for k, v in sorted(examples.items())]}, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
