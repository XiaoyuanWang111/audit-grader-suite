"""Step 4 stress tests for the ToyOrders reward: metamorphic properties, fuzzing, content-free responses.

    python -B audit/stress.py                 # print the three tables
    python -B audit/stress.py --write         # also write audit/stress_results.json

Expected rewards come from the contract's formulas (audit/CONTRACT.md), never from either grader.
Fuzz counts depend on the generators below; they are counts, not rates.
"""

import json
import os
import random
import sys
from collections import Counter
from decimal import Decimal

sys.dont_write_bytecode = True
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (os.path.join(W, "case"), os.path.join(W, "audit")):
    if p not in sys.path:
        sys.path.insert(0, p)

import replacement_reward as rr  # noqa: E402
import reward as grader  # noqa: E402

FUZZ_SEED = 20261111


def load_orders():
    with open(os.path.join(W, "case", "orders.jsonl"), encoding="utf-8") as f:
        return [json.loads(l, parse_float=Decimal) for l in f if l.strip()]


ORDERS = load_orders()
REFS = {o["order_id"]: o["reference"] for o in ORDERS}

GRADERS = {
    "grader": lambda resp, ref: grader.reward(resp, ref),
    "replacement": lambda resp, ref: rr.reward(resp, ref, **rr.PROPOSED),
}


# ---------- serialization of a reference-correct answer ----------

def item_text(it, extra=""):
    return '{"sku": %s, "qty": %d%s}' % (json.dumps(it["sku"]), it["qty"], extra)


def answer_text(ref, pretty=False, customer=None, total=None, items=None, key_order=None, item_extra=""):
    customer = json.dumps(ref["customer"]) if customer is None else customer
    total = str(ref["total"]) if total is None else total
    items = ref["items"] if items is None else items
    fields = {"customer": customer, "date": json.dumps(ref["date"]),
              "items": None, "total": total}
    order = key_order or ["customer", "date", "items", "total"]
    if pretty:
        item_lines = ",\n".join("    " + item_text(it, item_extra) for it in items)
        fields["items"] = "[\n" + item_lines + "\n  ]"
        body = ",\n".join('  "%s": %s' % (k, fields[k]) for k in order)
        return "{\n" + body + "\n}"
    fields["items"] = "[" + ", ".join(item_text(it, item_extra) for it in items) + "]"
    return "{" + ", ".join('"%s": %s' % (k, fields[k]) for k in order) + "}"


SERIALIZATIONS = {
    "compact": lambda ref, **k: answer_text(ref, **k),
    "pretty": lambda ref, **k: answer_text(ref, pretty=True, **k),
    "fenced-json": lambda ref, **k: "```json\n" + answer_text(ref, **k) + "\n```",
    "fenced-plain-pretty": lambda ref, **k: "```\n" + answer_text(ref, pretty=True, **k) + "\n```",
}


def base_cases():
    for o in ORDERS:
        for sname, ser in SERIALIZATIONS.items():
            yield o["order_id"], sname, ser


def label_lines(text, label):
    return "\n".join(label(i) + line for i, line in enumerate(text.split("\n")))


def items_reward(n_ref, n_ans, matched):
    return (3 + matched / max(n_ref, n_ans)) / 4


# ---------- metamorphic properties: (name, kind, edit(ref, ser, sname) -> response or None, expected(ref)) ----------

def _first_word_customer(ref, wrap):
    first, _, rest = ref["customer"].partition(" ")
    return json.dumps(wrap(first) + (" " + rest if rest else ""))


PROPERTIES = [
    # Edits the contract ignores: the reward stays 1.0.
    ("trailing newline", "ignored", lambda ref, ser, s: ser(ref) + "\n", lambda ref: 1.0),
    ("whitespace at both ends", "ignored", lambda ref, ser, s: " \n\t " + ser(ref) + " \n ", lambda ref: 1.0),
    ("blank line between lines", "ignored", lambda ref, ser, s: ser(ref).replace("\n", "\n\n") if "\n" in ser(ref)
     else ser(ref).replace(", ", ",\n\n"), lambda ref: 1.0),
    ("top-level keys reordered", "ignored",
     lambda ref, ser, s: ser(ref, key_order=["total", "items", "date", "customer"]), lambda ref: 1.0),
    ("items reordered", "ignored", lambda ref, ser, s: ser(ref, items=list(reversed(ref["items"]))),
     lambda ref: 1.0),
    ("customer upper-cased", "ignored", lambda ref, ser, s: ser(ref, customer=json.dumps(ref["customer"].upper())),
     lambda ref: 1.0),
    ("customer padded with spaces", "ignored",
     lambda ref, ser, s: ser(ref, customer=json.dumps("  " + ref["customer"] + " ")), lambda ref: 1.0),
    ("total with an extra trailing zero", "ignored",
     lambda ref, ser, s: ser(ref, total=str(ref["total"]) + "0"), lambda ref: 1.0),
    ("total in exponent form", "ignored",
     lambda ref, ser, s: ser(ref, total="%se2" % (ref["total"] / 100)), lambda ref: 1.0),
    ("extra key inside each item", "ignored", lambda ref, ser, s: ser(ref, item_extra=', "note": "x"'),
     lambda ref: 1.0),
    ("CRLF line breaks, unfenced", "ignored",
     lambda ref, ser, s: ser(ref).replace("\n", "\r\n") if not s.startswith("fenced") else None, lambda ref: 1.0),
    # Edits the contract forbids: the reward must drop to the stated value.
    ("numbered label before each line", "forbidden",
     lambda ref, ser, s: label_lines(ser(ref), lambda i: "%d. " % (i + 1)), lambda ref: 0.0),
    ("bullet before each line", "forbidden", lambda ref, ser, s: label_lines(ser(ref), lambda i: "- "),
     lambda ref: 0.0),
    ("bold markup around the answer", "forbidden", lambda ref, ser, s: "**" + ser(ref) + "**", lambda ref: 0.0),
    ("HTML tag around the answer", "forbidden", lambda ref, ser, s: "<json>" + ser(ref) + "</json>",
     lambda ref: 0.0),
    ("bold markup around the customer's first word", "forbidden",
     lambda ref, ser, s: ser(ref, customer=_first_word_customer(ref, lambda w: "**" + w + "**")), lambda ref: 0.75),
    ("HTML tag around the customer's first word", "forbidden",
     lambda ref, ser, s: ser(ref, customer=_first_word_customer(ref, lambda w: "<b>" + w + "</b>")),
     lambda ref: 0.75),
    ("typographic quotes around the customer key", "forbidden",
     lambda ref, ser, s: ser(ref).replace('"customer"', "“customer”"), lambda ref: 0.0),
    ("typographic apostrophe inside the customer's first word", "forbidden",
     lambda ref, ser, s: ser(ref, customer=_first_word_customer(ref, lambda w: w[:2] + "’" + w[2:])),
     lambda ref: 0.75),
    ("full stop after the customer's last word", "forbidden",
     lambda ref, ser, s: ser(ref, customer=json.dumps(ref["customer"] + ".")), lambda ref: 0.75),
    ("full stop after the answer", "forbidden", lambda ref, ser, s: ser(ref) + ".", lambda ref: 0.0),
    ("trailing sentence", "forbidden", lambda ref, ser, s: ser(ref) + "\nAll fields were found in the email.",
     lambda ref: 0.0),
    ("leading sentence", "forbidden", lambda ref, ser, s: "Here is the JSON object:\n" + ser(ref), lambda ref: 0.0),
    ("answer wrapped in a list", "forbidden", lambda ref, ser, s: "[" + ser(ref) + "]" if not s.startswith("fenced")
     else None, lambda ref: 0.0),
    ("last item duplicated", "forbidden", lambda ref, ser, s: ser(ref, items=ref["items"] + ref["items"][-1:]),
     lambda ref: items_reward(len(ref["items"]), len(ref["items"]) + 1, len(ref["items"]))),
    ("extra shipping item", "forbidden",
     lambda ref, ser, s: ser(ref, items=ref["items"] + [{"sku": "SHIPPING", "qty": 1}]),
     lambda ref: items_reward(len(ref["items"]), len(ref["items"]) + 1, len(ref["items"]))),
]


def safe(fn, resp, ref):
    try:
        v = fn(resp, ref)
    except BaseException as e:  # noqa: BLE001
        return type(e).__name__
    return v


def run_properties():
    """Return {property: {"kind", "cases", grader_name: [violations]}}, after checking the base cases pass."""
    out = {}
    base_bad = {g: [] for g in GRADERS}
    for oid, sname, ser in base_cases():
        for g, fn in GRADERS.items():
            v = safe(fn, ser(REFS[oid]), REFS[oid])
            if v != 1.0:
                base_bad[g].append((oid, sname, v))
    out["(base responses)"] = {"kind": "base", "cases": 48, **base_bad}
    for name, kind, edit, expected in PROPERTIES:
        rec = {"kind": kind, "cases": 0, **{g: [] for g in GRADERS}}
        for oid, sname, ser in base_cases():
            ref = REFS[oid]
            resp = edit(ref, ser, sname)
            if resp is None:
                continue
            rec["cases"] += 1
            exp = expected(ref)
            for g, fn in GRADERS.items():
                v = safe(fn, resp, ref)
                if not isinstance(v, float) or abs(v - exp) > 1e-9:
                    rec[g].append({"order_id": oid, "serialization": sname, "expected": exp,
                                   "got": v if isinstance(v, str) else round(v, 4)})
        out[name] = rec
    return out


# ---------- fuzzing ----------

ALPHABET = list('{}[]":,.-+0123456789eE \n\t\r`jsonJSONtrufalNIfiy\\/abcxyz') + [" ", "’", "“",
                                                                                    "　", "﻿", "\x85"]


def gen_text(rng):
    return "".join(rng.choice(ALPHABET) for _ in range(rng.randint(0, 80)))


def gen_mutation(rng):
    oid, sname, ser = rng.choice(list(base_cases()))
    s = list(ser(REFS[oid]))
    for _ in range(rng.randint(1, 3)):
        op = rng.randrange(3)
        pos = rng.randrange(len(s) + 1)
        if op == 0:
            s.insert(pos, rng.choice(ALPHABET))
        elif op == 1 and s:
            del s[min(pos, len(s) - 1)]
        elif s:
            s[min(pos, len(s) - 1)] = rng.choice(ALPHABET)
    return oid, "".join(s)


def rand_number(rng):
    return rng.choice([
        lambda: str(rng.randint(-10, 200)),
        lambda: "%d.%02d" % (rng.randint(0, 200), rng.randint(0, 99)),
        lambda: "%de%d" % (rng.randint(1, 9), rng.randint(-400, 400)),
        lambda: "1e%d" % rng.randint(999990, 999999999),
        lambda: "-1e%d" % rng.randint(999990, 999999999),
        lambda: "1" + "0" * rng.randint(4290, 4400),
        lambda: "64.505" + "0" * rng.randint(20, 30) + "1",
        lambda: rng.choice(["NaN", "Infinity", "-Infinity"]),
    ])()


def rand_json(rng, depth=0):
    kinds = ["num", "str", "true", "false", "null"] + (["list", "obj"] if depth < 3 else [])
    k = rng.choice(kinds)
    if k == "num":
        return rand_number(rng)
    if k == "str":
        return json.dumps(rng.choice(["", "AB-100", "Maria Lopez", "2026-03-07", "x" * rng.randint(0, 5)]))
    if k in ("true", "false", "null"):
        return k
    if k == "list":
        return "[" + ", ".join(rand_json(rng, depth + 1) for _ in range(rng.randint(0, 3))) + "]"
    keys = ["customer", "date", "items", "total", "sku", "qty", "extra"]
    return "{" + ", ".join('"%s": %s' % (rng.choice(keys), rand_json(rng, depth + 1))
                           for _ in range(rng.randint(0, 4))) + "}"


def gen_json_value(rng):
    v = rand_json(rng)
    r = rng.random()
    if r < 0.2:
        v = v + rng.choice(["\nDone.", ".", "\n```", " {}"])
    elif r < 0.3:
        v = rng.choice(["1. ", "Answer: ", "```json\n"]) + v
    return v


def gen_order_object(rng):
    """An object with the four keys and random values, aimed at the field scorers."""
    oid = rng.choice(list(REFS))
    ref = REFS[oid]

    def item():
        it = rng.choice(ref["items"])
        return '{"sku": %s, "qty": %s}' % (rng.choice([json.dumps(it["sku"]), rand_json(rng, 2)]),
                                          rng.choice([str(it["qty"]), "%d.0" % it["qty"], rand_number(rng), "true"]))
    items = "[" + ", ".join(item() for _ in range(rng.randint(0, 6))) + "]"
    total = rng.choice([str(ref["total"]), rand_number(rng), json.dumps(str(ref["total"]))])
    text = answer_text(ref, items=[], total=total).replace('"items": []', '"items": ' + items)
    if rng.random() < 0.2:
        text = "[" * rng.randint(2000, 50000) + "]" * 0 + text
    return oid, text


def run_fuzz(n=2000, seed=FUZZ_SEED):
    rng = random.Random(seed)
    gens = {
        "random text": lambda: (rng.choice(list(REFS)), gen_text(rng)),
        "mutated correct answer": lambda: gen_mutation(rng),
        "random JSON value": lambda: (rng.choice(list(REFS)), gen_json_value(rng)),
        "random order object": lambda: gen_order_object(rng),
    }
    out = {}
    for gname, gen in gens.items():
        rec = {"inputs": n, **{g: Counter() for g in GRADERS}, "disagree_fixes_only": 0, "examples": {}}
        for _ in range(n):
            oid, resp = gen()
            ref = REFS[oid]
            for g, fn in GRADERS.items():
                v = safe(fn, resp, ref)
                if isinstance(v, str):
                    rec[g][v] += 1
                    rec["examples"].setdefault(f"{g}:{v}", {"order_id": oid, "response": resp[:200]})
                elif not isinstance(v, float) or not 0.0 <= v <= 1.0:
                    rec[g]["bad value"] += 1
            gv = safe(GRADERS["grader"], resp, ref)
            fv = safe(lambda a, b: rr.reward(a, b, **rr.FIXES_ONLY), resp, ref)
            if isinstance(gv, str) or abs(gv - fv) > 1e-9:
                rec["disagree_fixes_only"] += 1
        for g in GRADERS:
            rec[g] = dict(rec[g])
        out[gname] = rec
    return out


# ---------- content-free responses ----------

def content_free():
    tmpl = open(os.path.join(W, "case", "prompt_template.txt"), encoding="utf-8").read()
    o = ORDERS[0]
    cases = {
        "empty": "",
        "whitespace only": " \n\t\n ",
        "repeated word": "order " * 200,
        "repeated braces": "{}" * 100,
        "instructions restated (rendered prompt)": tmpl.replace("{email}", o["email"]),
        "instructions restated (template)": tmpl,
        "the email copied": o["email"],
        "empty object": "{}",
        "keys with empty values": '{"customer": "", "date": "", "items": [], "total": 0}',
        "schema placeholder": '{"customer": "<name>", "date": "YYYY-MM-DD", "items": [{"sku": "<code>", '
                              '"qty": 0}], "total": 0}',
        "null": "null",
        "empty list": "[]",
        "empty string literal": '""',
        "zero": "0",
    }
    out = {}
    for name, resp in cases.items():
        out[name] = {g: safe(fn, resp, o["reference"]) for g, fn in GRADERS.items()}
    return out


def main():
    props = run_properties()
    print("Metamorphic properties (violations / cases)")
    print(f"{'property':<58}{'kind':<10}{'grader':>10}{'replacement':>13}")
    for name, rec in props.items():
        print(f"{name:<58}{rec['kind']:<10}{len(rec['grader']):>5}/{rec['cases']:<4}"
              f"{len(rec['replacement']):>7}/{rec['cases']:<4}")
    fuzz = run_fuzz()
    print(f"\nFuzz (seed {FUZZ_SEED}, 2000 inputs per generator): exceptions by type")
    for gname, rec in fuzz.items():
        print(f"{gname:<26} grader={rec['grader']} replacement={rec['replacement']} "
              f"grader!=fixes_only:{rec['disagree_fixes_only']}")
    cf = content_free()
    print("\nContent-free responses (order o01)")
    for name, rec in cf.items():
        print(f"{name:<42} grader={rec['grader']} replacement={rec['replacement']}")
    if "--write" in sys.argv:
        with open(os.path.join(W, "audit", "stress_results.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump({"properties": props, "fuzz": fuzz, "content_free": cf}, f, indent=1, default=str)
            f.write("\n")


if __name__ == "__main__":
    main()
