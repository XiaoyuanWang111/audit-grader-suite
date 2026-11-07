"""Step 4: fuzz the grader under audit, and check the replacement never raises.

    python -I -B audit/scripts/fuzz.py [--n 20000] [--seed 7]

Three generators, each drawn with random.Random(seed):
    mutate   a correct answer for a random order with 1 to 3 random edits (character edits,
             prefixes, suffixes, fences, field values replaced by random JSON values, item
             edits, extra keys)
    value    a random JSON value (any type, nested, with extreme numbers) as the whole answer,
             sometimes fenced
    text     random strings over a JSON-heavy alphabet
For every case: the grader's outcome (value or exception type), the replacement's outcome
under the official readings ("fixes only") and the proposed readings, and the findings whose
fix alone changes the grader's verdict. Two harness checks run on every case: the patched
grader with no fixes equals case/reward.py, and with every fix equals the replacement's
official readings. Counts depend on this generator's input distribution; they are counts,
not rates. Writes audit/runs/fuzz_summary.json and prints it.
"""
import argparse
import collections
import json
import pathlib
import random
import sys
from decimal import Decimal

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "audit" / "scripts"))

import patched_grader as P  # noqa: E402

G, R = P.G, P.R

REFS = {}
for line in open(ROOT / "case" / "orders.jsonl", encoding="utf-8"):
    if line.strip():
        row = json.loads(line, parse_float=Decimal)
        REFS[row["order_id"]] = row["reference"]
ORDERS = sorted(REFS)

WORDS = ["Hope this helps!", "Note: total includes shipping.", "}", "]", "```", "\n```", "Done", "{}", "0", "null",
         "```json", "<think>ok</think>", " ", "\n", "\t", " ", "\r\n", "Here is the JSON:", "x"]
EXTREME = ["1e1000000", "-1e1000000", "1e-1000000", "1E+999999", "NaN", "Infinity", "-Infinity", "0", "-0", "1e400",
           "123456789012345678901234567890.123456789", "64.50500000000000000000000000000001", "2.0", "2e0", "true",
           "false", "null", '""', "[]", "{}", "1" * 50]


def rand_value(rng, depth=0):
    kind = rng.choice(["str", "int", "num", "extreme", "bool", "null", "list", "dict"] if depth < 4 else
                      ["str", "int", "num", "extreme", "bool", "null"])
    if kind == "str":
        return json.dumps(rng.choice(["", "Maria Lopez", "AB-100", "2026-03-07", "64.50", "x" * rng.randint(1, 5), "ß", " a "]))
    if kind == "int":
        return str(rng.randint(-5, 200))
    if kind == "num":
        return "%d.%02d" % (rng.randint(0, 200), rng.randint(0, 99))
    if kind == "extreme":
        return rng.choice(EXTREME)
    if kind == "bool":
        return rng.choice(["true", "false"])
    if kind == "null":
        return "null"
    if kind == "list":
        return "[" + ", ".join(rand_value(rng, depth + 1) for _ in range(rng.randint(0, 3))) + "]"
    keys = ["customer", "date", "items", "total", "sku", "qty", "notes", "a"]
    return "{" + ", ".join("%s: %s" % (json.dumps(rng.choice(keys)), rand_value(rng, depth + 1)) for _ in range(rng.randint(0, 4))) + "}"


def correct_parts(order_id):
    ref = REFS[order_id]
    items = [[("sku", json.dumps(i["sku"])), ("qty", str(i["qty"]))] for i in ref["items"]]
    return [("customer", json.dumps(ref["customer"])), ("date", json.dumps(ref["date"])), ("items", items),
            ("total", format(ref["total"], "f"))]


def render(parts):
    out = []
    for key, value in parts:
        if key == "items" and isinstance(value, list):
            value = "[" + ", ".join(("{" + ", ".join("%s: %s" % (json.dumps(k), v) for k, v in item) + "}") if isinstance(item, list) else item
                                    for item in value) + "]"
        out.append("%s: %s" % (json.dumps(key), value))
    return "{" + ", ".join(out) + "}"


def gen_mutate(rng):
    order_id = rng.choice(ORDERS)
    parts = correct_parts(order_id)
    for _ in range(rng.randint(1, 3)):
        op = rng.choice(["field_value", "item_extra", "item_dup", "item_drop", "item_value", "extra_key", "late"])
        if op == "field_value":
            k = rng.randrange(len(parts))
            parts[k] = (parts[k][0], rand_value(rng))
        elif op in ("item_extra", "item_dup", "item_drop", "item_value"):
            idx = [k for k, (key, v) in enumerate(parts) if key == "items" and isinstance(v, list)]
            if not idx:
                continue
            items = parts[idx[0]][1]
            if op == "item_extra":
                items.append(rng.choice([[("sku", '"ZZ-999"'), ("qty", "1")], rand_value(rng, 2), '"gift wrap"']))
            elif op == "item_dup" and items:
                items.append(rng.choice(items))
            elif op == "item_drop" and items:
                items.pop(rng.randrange(len(items)))
            elif op == "item_value" and items and isinstance(items[0], list):
                j = rng.randrange(len(items[0]))
                items[0][j] = (items[0][j][0], rand_value(rng, 3))
        elif op == "extra_key":
            parts.append((rng.choice(["notes", "Customer", "currency", "items", "total"]), rand_value(rng, 2)))
    text = render(parts)
    for _ in range(rng.randint(0, 2)):
        op = rng.choice(["char", "prefix", "suffix", "fence", "fence", "ws"])
        if op == "char" and text:
            p = rng.randrange(len(text))
            text = text[:p] + rng.choice(["", "}", '"', ",", " ", "\n", "x", "]"]) + text[p + rng.choice([0, 1]):]
        elif op == "prefix":
            text = rng.choice(WORDS) + rng.choice(["", " ", "\n"]) + text
        elif op == "suffix":
            text = text + rng.choice(["", " ", "\n"]) + rng.choice(WORDS)
        elif op == "fence":
            text = rng.choice(["```json", "```", "```JSON", "```json\t", "```json  ", "``` json"]) + rng.choice(["\n", "\r\n"]) + text + rng.choice(["\n```", "\r\n```", "```", "\n```\n"])
        else:
            text = rng.choice(["", " ", "\n", "\t", " "]) + text + rng.choice(["", " ", "\n", "　"])
    return order_id, text


def gen_value(rng):
    order_id = rng.choice(ORDERS)
    text = rand_value(rng)
    if rng.random() < 0.3:
        text = "```json\n" + text + "\n```"
    if rng.random() < 0.3:
        text += rng.choice(WORDS)
    return order_id, text


ALPHABET = list('{}[]":,0123456789.-eE ntrufals\n\t`\\abcxyz') + ["true", "null", "NaN", "Infinity", "```json\n", "\n```"]


def gen_text(rng):
    return rng.choice(ORDERS), "".join(rng.choice(ALPHABET) for _ in range(rng.randint(0, 40)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    gens = {"mutate": gen_mutate, "value": gen_value, "text": gen_text}
    stats = {name: collections.Counter() for name in gens}
    examples = {}
    harness_errors = []
    for i in range(args.n):
        name = ("mutate", "mutate", "value", "text")[i % 4]
        order_id, response = gens[name](rng)
        ref = REFS[order_id]
        g = P.outcome(G.reward, response, ref)
        o = P.outcome(R.reward, response, ref, **R.OFFICIAL)
        p = P.outcome(R.reward, response, ref)
        nofix = P.outcome(P.reward, response, ref)
        allfix = P.outcome(P.reward, response, ref, fixes=P.ALL_FIXES)
        if not P.same(g, nofix) or not P.same(allfix, o):
            harness_errors.append((name, order_id, response[:200], g, nofix, allfix, o))
        s = stats[name]
        s["cases"] += 1
        if o[0] == "raises" or p[0] == "raises":
            s["replacement raises"] += 1
        if g[0] == "raises":
            s["grader raises " + g[1]] += 1
        elif not P.same(g, o):
            s["grader above fixes-only" if g[1] > o[1] else "grader below fixes-only"] += 1
            if g[1] == 1.0:
                s["grader full reward, fixes-only not full"] += 1
        if not P.same(g, o):
            for k in P.attribute(response, ref):
                s["changed by fix " + k] += 1
                examples.setdefault(k, (order_id, response[:160], g, o))
        if not P.same(o, p):
            s["official and proposed readings differ"] += 1
    summary = {"n": args.n, "seed": args.seed, "python": sys.version.split()[0],
               "per_generator": {k: dict(sorted(v.items())) for k, v in stats.items()},
               "harness_mismatches": len(harness_errors),
               "first_example_per_fix": {k: {"order_id": v[0], "response_start": v[1], "grader": v[2], "fixes_only": v[3]}
                                         for k, v in sorted(examples.items())}}
    (ROOT / "audit" / "runs" / "fuzz_summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n",
                                                               encoding="utf-8", newline="\n")
    print(json.dumps(summary, indent=1, ensure_ascii=False))
    for e in harness_errors[:5]:
        print("HARNESS MISMATCH", e)


if __name__ == "__main__":
    main()
