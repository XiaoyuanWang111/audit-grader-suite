"""Write cases/toyjson-reward/orders.jsonl, prompt_template.txt and responses.jsonl. Private: part of the keys."""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CASE = os.path.join(HERE, "..", "..", "cases", "toyjson-reward")
FENCE = "```"

ORDERS = [
    (
        "o01",
        "Hi, this is Maria Lopez. I'd like to confirm my order from March 7, 2026: 2 x AB-100 (desk lamp) and "
        "1 x CD-220 (bulb pack). The total came to $64.50. Thanks!",
        {"customer": "Maria Lopez", "date": "2026-03-07", "items": [["AB-100", 2], ["CD-220", 1]], "total": "64.50"},
    ),
    (
        "o02",
        "Order placed on 2026-01-15 by Kenji Watanabe. Items: EF-310 (qty 3). Order total: $29.97.",
        {"customer": "Kenji Watanabe", "date": "2026-01-15", "items": [["EF-310", 3]], "total": "29.97"},
    ),
    (
        "o03",
        "Hello! Please ship my order (placed 4 February 2026) to the usual address. I ordered one GH-405 kettle "
        "and two IJ-500 mugs. Total paid: $47.00. Best, Priya Raman",
        {"customer": "Priya Raman", "date": "2026-02-04", "items": [["GH-405", 1], ["IJ-500", 2]], "total": "47.00"},
    ),
    (
        "o04",
        "From: Tom Becker. Date of order: 12/03/2026 (that is, 12 March). 4 x KL-610, 1 x MN-720. Total $112.80, "
        "shipping included.",
        {"customer": "Tom Becker", "date": "2026-03-12", "items": [["KL-610", 4], ["MN-720", 1]], "total": "112.80"},
    ),
    (
        "o05",
        "Hi, it's Aisha Bello. My order from April 1, 2026: 1 OP-830 backpack. It was $59.99 in total; the $5.00 "
        "shipping fee is included in that.",
        {"customer": "Aisha Bello", "date": "2026-04-01", "items": [["OP-830", 1]], "total": "59.99"},
    ),
    (
        "o06",
        "Order confirmation needed: customer Lars Nilsson, ordered 2026-02-28. Products: QR-940 x 2, ST-150 x 2, "
        "UV-260 x 1. Grand total: $88.25.",
        {
            "customer": "Lars Nilsson",
            "date": "2026-02-28",
            "items": [["QR-940", 2], ["ST-150", 2], ["UV-260", 1]],
            "total": "88.25",
        },
    ),
    (
        "o07",
        "Hello, Chen Wei here. On 9 January 2026 I bought 5 packs of WX-370 printer paper. Total: $42.50.",
        {"customer": "Chen Wei", "date": "2026-01-09", "items": [["WX-370", 5]], "total": "42.50"},
    ),
    (
        "o08",
        "This is Sofia Rossi. Order date: March 20, 2026. I ordered 1 x YZ-480 and 3 x AB-590. Total: $35.00.",
        {"customer": "Sofia Rossi", "date": "2026-03-20", "items": [["YZ-480", 1], ["AB-590", 3]], "total": "35.00"},
    ),
    (
        "o09",
        "Hi! Daniel Okafor here, order from 2026-04-11: 2 CD-605 cables and 2 EF-715 adapters. Total was $31.96. "
        "Could you add gift wrap? It was free.",
        {"customer": "Daniel Okafor", "date": "2026-04-11", "items": [["CD-605", 2], ["EF-715", 2]], "total": "31.96"},
    ),
    (
        "o10",
        "Order by Emma Schulz on 5 March 2026: one GH-825 umbrella. Total charged: $24.00.",
        {"customer": "Emma Schulz", "date": "2026-03-05", "items": [["GH-825", 1]], "total": "24.00"},
    ),
    (
        "o11",
        "Name: Rahul Mehta. Ordered: 2026-02-10. Lines: IJ-935 (2), KL-045 (1), MN-155 (1). Total: $73.40, which "
        "includes a $4.90 delivery charge.",
        {
            "customer": "Rahul Mehta",
            "date": "2026-02-10",
            "items": [["IJ-935", 2], ["KL-045", 1], ["MN-155", 1]],
            "total": "73.40",
        },
    ),
    (
        "o12",
        "Hi, I'm Grace Kim. I placed an order on April 3, 2026 for 3 x OP-265 notebooks. My total was $13.50.",
        {"customer": "Grace Kim", "date": "2026-04-03", "items": [["OP-265", 3]], "total": "13.50"},
    ),
]

PROMPT = """Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
{email}
"""


def obj(customer, date, items, total, extra=None, total_raw=None, qty_raw=None):
    """Serialize an answer object the way a policy would write it (compact or indented)."""
    parts = [f'"customer": {json.dumps(customer)}', f'"date": {json.dumps(date)}']
    its = []
    for i, (sku, qty) in enumerate(items):
        q = qty_raw[i] if qty_raw and i in qty_raw else json.dumps(qty)
        its.append(f'{{"sku": {json.dumps(sku)}, "qty": {q}}}')
    parts.append('"items": [' + ", ".join(its) + "]")
    parts.append(f'"total": {total_raw if total_raw is not None else total}')
    for k, v in (extra or {}).items():
        parts.append(f"{json.dumps(k)}: {json.dumps(v)}")
    return "{" + ", ".join(parts) + "}"


def ref(oid):
    return next(r for o, _, r in ORDERS if o == oid)


def correct(oid, **kw):
    r = ref(oid)
    return obj(r["customer"], r["date"], r["items"], r["total"], **kw)


def fenced(text):
    return FENCE + "json\n" + text + "\n" + FENCE


def pretty(text):
    return json.dumps(json.loads(text), indent=2)


R = {}
R["step-0000"] = {
    "o01": fenced(pretty(correct("o01"))),
    "o02": correct("o02") + "\n\nI extracted the customer name, the order date, the items and the total from the email.",
    "o03": obj("Priya Raman", "4 February 2026", ref("o03")["items"], "47.00"),
    "o04": obj("Tom Becker", "2026-12-03", ref("o04")["items"], "112.80"),
    "o05": fenced(pretty(correct("o05", extra={"shipping": 5.0}))),
    "o06": obj("Lars Nilsson", "2026-02-28", [["QR-940", 2], ["ST-150", 2]], "88.25"),
    "o07": fenced(pretty(correct("o07"))) + "\nLet me know if you need anything else.",
    "o08": obj("Sofia Rossi", "2026-03-20", ref("o08")["items"], None, total_raw='"35.00"'),
    "o09": fenced(correct("o09")),
    "o10": correct("o10") + "\nNote: the email does not say which color the umbrella is.",
    "o11": obj("Rahul Mehta", "2026-02-10", ref("o11")["items"] + [["DELIVERY", 1]], "73.40"),
    "o12": "{'customer': 'Grace Kim', 'date': '2026-04-03', 'items': [{'sku': 'OP-265', 'qty': 3}], 'total': 13.5}",
}
R["step-0200"] = {
    "o01": obj("Maria Lopez", "2026-03-07", ref("o01")["items"], "64.50", qty_raw={0: "2.0"}),
    "o02": correct("o02"),
    "o03": fenced(correct("o03")),
    "o04": correct("o04"),
    "o05": obj("Aisha Bello", "2026-04-01", [["OP-830", 1], ["SHIPPING", 1]], "59.99"),
    "o06": correct("o06"),
    "o07": obj("Wei Chen", "2026-01-09", ref("o07")["items"], "42.50"),
    "o08": correct("o08"),
    "o09": correct("o09", extra={"notes": "gift wrap requested"}),
    "o10": fenced(correct("o10")),
    "o11": correct("o11"),
    "o12": obj("Grace Kim", "2026-04-03", ref("o12")["items"], "13.50", qty_raw={0: "3.0"}),
}
R["step-0400"] = {
    "o01": correct("o01"),
    "o02": correct("o02"),
    "o03": correct("o03"),
    "o04": fenced(pretty(correct("o04"))),
    "o05": correct("o05"),
    "o06": correct("o06"),
    "o07": correct("o07"),
    "o08": obj("Sofia Rossi", "2026-03-20", ref("o08")["items"], "35"),
    "o09": correct("o09"),
    "o10": obj("Emma Schulz", "2026-03-05", ref("o10")["items"], "25.00"),
    "o11": correct("o11"),
    "o12": correct("o12") + "\nDone.",
}
R["step-0600"] = {
    "o01": obj("Maria Lopez", "2026-03-07", ref("o01")["items"] + [["CD-220", 1]], "64.50"),
    "o02": correct("o02") + "\nExtraction complete.",
    "o03": correct("o03"),
    "o04": obj("Tom Becker", "2026-03-12", ref("o04")["items"] + [["KL-610", 1]], "112.80"),
    "o05": correct("o05") + "\nAll fields were found in the email.",
    "o06": correct("o06"),
    "o07": correct("o07"),
    "o08": obj("Sofia Rossi", "2026-03-20", ref("o08")["items"] + [["YZ-480", 3], ["AB-590", 1]], "35.00"),
    "o09": correct("o09"),
    "o10": correct("o10") + "\nAll fields were found in the email.",
    "o11": correct("o11"),
    "o12": correct("o12"),
}


def main():
    os.makedirs(CASE, exist_ok=True)
    with open(os.path.join(CASE, "orders.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        for oid, email, r in ORDERS:
            reference = {
                "customer": r["customer"],
                "date": r["date"],
                "items": [{"sku": s, "qty": q} for s, q in r["items"]],
                "total": None,
            }
            line = json.dumps({"order_id": oid, "email": email, "reference": reference})
            f.write(line.replace('"total": null', '"total": ' + r["total"]) + "\n")
    with open(os.path.join(CASE, "prompt_template.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write(PROMPT)
    rows = []
    n = 0
    for oid, _, _ in ORDERS:
        for ckpt in ["step-0000", "step-0200", "step-0400", "step-0600"]:
            n += 1
            rows.append(
                {
                    "id": f"j{n:02d}",
                    "checkpoint": ckpt,
                    "order_id": oid,
                    "response": R[ckpt][oid],
                    "temperature": 1.0,
                    "max_tokens": 256,
                }
            )
    with open(os.path.join(CASE, "responses.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"wrote {len(ORDERS)} orders and {len(rows)} responses")


if __name__ == "__main__":
    main()
