"""Labeled fixtures for the ToyOrders reward, written from audit/CONTRACT.md alone.

Each fixture: check, order_id, response, expected (the reward under the contract's proposed readings), and for a
decision-dependent fixture, decision = (entry id, reward under reading A, reward under reading B); reading A is the
proposed one. `grader` records what case/reward.py does with the fixture, filled in after running it:
    None          the grader returns the expected reward (control)
    "F<n>"        the grader is wrong under every reading: finding F<n> (the test is an expected failure)
    "reading-A"   decision fixture, the grader follows reading A
    "reading-B"   decision fixture, the grader follows reading B
`needs_int_limit` marks a fixture whose contract label holds only while the interpreter's integer-string limit
(sys.get_int_max_str_digits(), Python >= 3.11 and the 3.7.14/3.8.14/3.9.14/3.10.7 security releases; changed by
PYTHONINTMAXSTRDIGITS or -X int_max_str_digits) is on and below that many digits, so that Python's json module
refuses the integer (finding G1).
"""

import hashlib

# Order o01: Maria Lopez, 2026-03-07, AB-100 x2 and CD-220 x1, total 64.50.
ITEMS1 = '[{"sku": "AB-100", "qty": 2}, {"sku": "CD-220", "qty": 1}]'


def o1(customer='"Maria Lopez"', date='"2026-03-07"', items=ITEMS1, total="64.50", extra=""):
    return '{"customer": %s, "date": %s, "items": %s, "total": %s%s}' % (customer, date, items, total, extra)


V1 = o1()
V1_PRETTY = ('{\n  "customer": "Maria Lopez",\n  "date": "2026-03-07",\n  "items": [\n'
             '    {"sku": "AB-100", "qty": 2},\n    {"sku": "CD-220", "qty": 1}\n  ],\n  "total": 64.50\n}')
# Order o02: Kenji Watanabe, 2026-01-15, EF-310 x3, total 29.97.
V2 = '{"customer": "Kenji Watanabe", "date": "2026-01-15", "items": [{"sku": "EF-310", "qty": 3}], "total": 29.97}'
# Order o04: Tom Becker, 2026-03-12, KL-610 x4 and MN-720 x1, total 112.80.
V4_DUP = ('{"customer": "Tom Becker", "date": "2026-03-12", "items": [{"sku": "KL-610", "qty": 4}, '
          '{"sku": "MN-720", "qty": 1}, {"sku": "KL-610", "qty": 1}], "total": 112.80}')
# Order o10: Emma Schulz, 2026-03-05, GH-825 x1, total 24.00.
V10_INT = '{"customer": "Emma Schulz", "date": "2026-03-05", "items": [{"sku": "GH-825", "qty": 1}], "total": 24}'

F_ITEMS_2_OF_3 = (3 + 2 / 3) / 4  # all fields right except items 2/3
F_ITEMS_1_OF_2 = 3.5 / 4

FIXTURES = [
    # ---- C1 answer extraction ----
    dict(check="answer", order_id="o01", response=V1, expected=1.0),
    dict(check="answer", order_id="o01", response="```json\n" + V1 + "\n```", expected=1.0),
    dict(check="answer", order_id="o01", response="```\n" + V1 + "\n```", expected=1.0),
    dict(check="answer", order_id="o01", response="```json   \n" + V1_PRETTY + "\n```", expected=1.0),
    dict(check="answer", order_id="o01", response="\n\n  " + V1 + "  \n", expected=1.0),
    dict(check="answer", order_id="o01", response=V1_PRETTY.replace("\n", "\n\n"), expected=1.0),
    dict(check="answer", order_id="o01", response=V1_PRETTY.replace("\n", "\r\n"), expected=1.0),
    dict(check="answer", order_id="o01", response=o1(customer='"Wrong Name", "customer": "Maria Lopez"'),
         expected=1.0),
    dict(check="answer", order_id="o02", response=V2 + "\n\nI extracted the customer name, the date, the items and "
         "the total from the email.", expected=0.0),
    dict(check="answer", order_id="o01", response=V1 + ".", expected=0.0),
    dict(check="answer", order_id="o01", response=V1 + "\n```", expected=0.0),
    dict(check="answer", order_id="o01", response=V1 + "\n" + V1, expected=0.0),
    dict(check="answer", order_id="o01", response="```json\n" + V1 + "\nDone.\n```", expected=0.0),
    dict(check="answer", order_id="o01", response="```json\n" + V1 + "\n```\n\n```json\n" + V1 + "\n```",
         expected=0.0),
    dict(check="answer", order_id="o01", response="```json\n" + V1 + "\n```\nLet me know if you need anything else.",
         expected=0.0),
    dict(check="answer", order_id="o01", response="Here is the JSON:\n" + V1, expected=0.0),
    dict(check="answer", order_id="o01", response="```JSON\n" + V1 + "\n```", expected=0.0),
    dict(check="answer", order_id="o01", response="```python\n" + V1 + "\n```", expected=0.0),
    dict(check="answer", order_id="o01", response="``` json\n" + V1 + "\n```", expected=0.0),
    dict(check="answer", order_id="o01", response="```json\n" + V1 + "```", expected=0.0),
    dict(check="answer", order_id="o01", response="```json\n" + V1, expected=0.0),
    dict(check="answer", order_id="o01", response="[" + V1 + "]", expected=0.0),
    dict(check="answer", order_id="o01", response='"Maria Lopez"', expected=0.0),
    dict(check="answer", order_id="o01", response="1. " + V1, expected=0.0),
    dict(check="answer", order_id="o01", response="2 items: " + V1, expected=0.0),
    dict(check="answer", order_id="o01", response="true", expected=0.0),
    dict(check="answer", order_id="o01", response="null", expected=0.0),
    dict(check="answer", order_id="o01", response="", expected=0.0),
    dict(check="answer", order_id="o01", response="   \n\t ", expected=0.0),
    dict(check="answer", order_id="o01", response=V1.replace('"', "'"), expected=0.0),
    dict(check="answer", order_id="o01", response="[" * 100000 + "]" * 100000, expected=0.0),
    dict(check="answer", order_id="o01", response=o1(extra=', "n": 1' + "0" * 5000), expected=0.0,
         needs_int_limit=5001),
    dict(check="answer", order_id="o01", response="```json\t\n" + V1 + "\n```", expected=1.0,
         decision=("D-fence-tab", 1.0, 0.0)),
    dict(check="answer", order_id="o01", response="```json\r\n" + V1 + "\r\n```", expected=1.0,
         decision=("D-crlf", 1.0, 0.0)),
    dict(check="answer", order_id="o01", response=V1 + " ", expected=1.0, decision=("D-whitespace", 1.0, 0.0)),
    dict(check="answer", order_id="o01", response="　" + V1, expected=1.0, decision=("D-whitespace", 1.0, 0.0)),
    # ---- C2 customer ----
    dict(check="customer", order_id="o01", response=o1(customer='"maria lopez"'), expected=1.0),
    dict(check="customer", order_id="o01", response=o1(customer='"MARIA LOPEZ"'), expected=1.0),
    dict(check="customer", order_id="o01", response=o1(customer='"  Maria Lopez "'), expected=1.0),
    dict(check="customer", order_id="o01", response=o1(customer='"Lopez Maria"'), expected=0.75),
    dict(check="customer", order_id="o01", response=o1(customer='"Maria  Lopez"'), expected=0.75),
    dict(check="customer", order_id="o01", response=o1(customer='"Maria"'), expected=0.75),
    dict(check="customer", order_id="o01", response=o1(customer='"Maria Lopez."'), expected=0.75),
    dict(check="customer", order_id="o01", response=o1(customer='"**Maria** Lopez"'), expected=0.75),
    dict(check="customer", order_id="o01", response=o1(customer='["Maria Lopez"]'), expected=0.75),
    dict(check="customer", order_id="o01", response=o1(customer="null"), expected=0.75),
    dict(check="customer", order_id="o01",
         response='{"date": "2026-03-07", "items": %s, "total": 64.50}' % ITEMS1, expected=0.75),
    dict(check="customer", order_id="o01", response=o1(customer='"Maria Lopez\\u00a0"'), expected=1.0,
         decision=("D-whitespace", 1.0, 0.75)),
    # ---- C3 date ----
    dict(check="date", order_id="o01", response=o1(date='"2026-3-7"'), expected=0.75),
    dict(check="date", order_id="o01", response=o1(date='"March 7, 2026"'), expected=0.75),
    dict(check="date", order_id="o01", response=o1(date='"2026-03-07T00:00:00"'), expected=0.75),
    dict(check="date", order_id="o01", response=o1(date='" 2026-03-07"'), expected=0.75),
    dict(check="date", order_id="o01", response=o1(date="20260307"), expected=0.75),
    dict(check="date", order_id="o01", response=o1(date='"2026-07-03"'), expected=0.75),
    # ---- C4 items ----
    dict(check="items", order_id="o01",
         response=o1(items='[{"sku": "CD-220", "qty": 1}, {"sku": "AB-100", "qty": 2}]'), expected=1.0),
    dict(check="items", order_id="o01",
         response=o1(items='[{"qty": 2, "sku": "AB-100", "name": "desk lamp"}, {"sku": "CD-220", "qty": 1}]'),
         expected=1.0),
    dict(check="items", order_id="o01", response=o1(items='[{"sku": "AB-100", "qty": 2}]'), expected=F_ITEMS_1_OF_2),
    dict(check="items", order_id="o01",
         response=o1(items='[{"sku": "AB-100", "qty": 2}, {"sku": "CD-220", "qty": 1}, {"sku": "CD-220", "qty": 1}]'),
         expected=F_ITEMS_2_OF_3),
    dict(check="items", order_id="o01",
         response=o1(items='[{"sku": "AB-100", "qty": 2}, {"sku": "CD-220", "qty": 1}, {"sku": "SHIPPING", "qty": 1}]'),
         expected=F_ITEMS_2_OF_3),
    dict(check="items", order_id="o01",
         response=o1(items='[{"sku": "AB-100", "qty": 1}, {"sku": "AB-100", "qty": 2}, {"sku": "AB-100", "qty": 3}, '
                           '{"sku": "CD-220", "qty": 1}, {"sku": "CD-220", "qty": 2}, {"sku": "CD-220", "qty": 3}]'),
         expected=(3 + 2 / 6) / 4),
    dict(check="items", order_id="o01",
         response=o1(items='[{"sku": "AB-100", "qty": 2}, {"sku": "CD-220", "qty": 1}, "gift wrap"]'),
         expected=F_ITEMS_2_OF_3),
    dict(check="items", order_id="o04", response=V4_DUP, expected=F_ITEMS_2_OF_3),
    dict(check="items", order_id="o02", response=V2.replace('[{"sku": "EF-310", "qty": 3}]',
                                                            '[{"sku": "EF-310", "qty": 3}, {"sku": "EF-310", "qty": 3}]'),
         expected=F_ITEMS_1_OF_2),
    dict(check="items", order_id="o01", response=o1(items='[{"sku": "AB-100", "qty": 3}, {"sku": "CD-220", "qty": 1}]'),
         expected=F_ITEMS_1_OF_2),
    dict(check="items", order_id="o01",
         response=o1(items='[{"sku": "AB-100", "qty": "2"}, {"sku": "CD-220", "qty": 1}]'), expected=F_ITEMS_1_OF_2),
    dict(check="items", order_id="o01",
         response=o1(items='[{"sku": "ab-100", "qty": 2}, {"sku": "CD-220", "qty": 1}]'), expected=F_ITEMS_1_OF_2),
    dict(check="items", order_id="o01",
         response=o1(items='[{"sku": "AB-100 ", "qty": 2}, {"sku": "CD-220", "qty": 1}]'), expected=F_ITEMS_1_OF_2),
    dict(check="items", order_id="o01",
         response=o1(items='[{"sku": "AB-100", "qty": 2.5}, {"sku": "CD-220", "qty": 1}]'), expected=F_ITEMS_1_OF_2),
    dict(check="items", order_id="o01",
         response=o1(items='[{"sku": "AB-100", "qty": 1e999999999}, {"sku": "CD-220", "qty": 1}]'),
         expected=F_ITEMS_1_OF_2),
    dict(check="items", order_id="o01", response=o1(items='{"AB-100": 2, "CD-220": 1}'), expected=0.75),
    dict(check="items", order_id="o01", response=o1(items="[]"), expected=0.75),
    dict(check="items", order_id="o01",
         response=o1(items='[{"sku": "AB-100", "qty": 2.0}, {"sku": "CD-220", "qty": 1}]'), expected=F_ITEMS_1_OF_2,
         decision=("D-qty-decimal", F_ITEMS_1_OF_2, 1.0)),
    dict(check="items", order_id="o01",
         response=o1(items='[{"sku": "AB-100", "qty": 2e0}, {"sku": "CD-220", "qty": 1}]'), expected=F_ITEMS_1_OF_2,
         decision=("D-qty-decimal", F_ITEMS_1_OF_2, 1.0)),
    dict(check="items", order_id="o01",
         response=o1(items='[{"sku": "AB-100", "qty": 2}, {"sku": "CD-220", "qty": true}]'), expected=F_ITEMS_1_OF_2,
         decision=("D-qty-bool", F_ITEMS_1_OF_2, 1.0)),
    # ---- C5 total ----
    dict(check="total", order_id="o01", response=o1(total="64.5"), expected=1.0),
    dict(check="total", order_id="o01", response=o1(total="6.45e1"), expected=1.0),
    dict(check="total", order_id="o10", response=V10_INT, expected=1.0),
    dict(check="total", order_id="o01", response=o1(total="64.504"), expected=1.0),
    dict(check="total", order_id="o01", response=o1(total="64.506"), expected=0.75),
    dict(check="total", order_id="o01", response=o1(total="64.494"), expected=0.75),
    dict(check="total", order_id="o01", response=o1(total="64"), expected=0.75),
    dict(check="total", order_id="o01", response=o1(total='"64.50"'), expected=0.75),
    dict(check="total", order_id="o01", response=o1(total='"$64.50"'), expected=0.75),
    dict(check="total", order_id="o01", response=o1(total="true"), expected=0.75),
    dict(check="total", order_id="o01", response=o1(total="null"), expected=0.75),
    dict(check="total", order_id="o01", response=o1(total="64.505" + "0" * 27 + "1"), expected=0.75),
    dict(check="total", order_id="o01", response=o1(total="64.494" + "9" * 28), expected=0.75),
    dict(check="total", order_id="o01", response=o1(total="1e999999999"), expected=0.75),
    dict(check="total", order_id="o01", response=o1(total="-1e999999999"), expected=0.75),
    dict(check="total", order_id="o01", response=o1(total="64.505"), expected=1.0,
         decision=("D-total-boundary", 1.0, 0.75)),
    dict(check="total", order_id="o01", response=o1(total="64.495"), expected=1.0,
         decision=("D-total-boundary", 1.0, 0.75)),
    dict(check="total", order_id="o01", response=o1(total="NaN"), expected=0.75,
         decision=("D-json-constants", 0.75, 0.0)),
    dict(check="total", order_id="o01", response=o1(total="Infinity"), expected=0.75,
         decision=("D-json-constants", 0.75, 0.0)),
    # ---- C6 penalty ----
    dict(check="penalty", order_id="o01", response=o1(extra=', "shipping": 5.0'), expected=0.9),
    dict(check="penalty", order_id="o01", response=o1(extra=', "shipping": 5.0, "notes": "gift wrap"'), expected=0.8),
    dict(check="penalty", order_id="o01", response=o1(extra=', "notes": "a", "notes": "b"'), expected=0.9),
    dict(check="penalty", order_id="o01", response=o1(extra="".join(', "k%d": 0' % k for k in range(15))),
         expected=0.0),
    dict(check="penalty", order_id="o01", response=o1(customer='"Lopez"', extra=', "currency": "USD"'),
         expected=0.65),
    # ---- C7 aggregation ----
    dict(check="aggregation", order_id="o01", response="{}", expected=0.0),
    dict(check="aggregation", order_id="o01",
         response='{"customer": "", "date": "", "items": [], "total": 0}', expected=0.0),
    dict(check="aggregation", order_id="o01", response=o1(customer='"Maria Lopes"', date='"2026-03-08"'),
         expected=0.5),
    dict(check="aggregation", order_id="o01", response=o1(customer='"x"', date='"x"', items="[]", total="0"),
         expected=0.0),
]


def fixture_id(f):
    h = hashlib.sha256((f["order_id"] + "\x00" + f["response"]).encode("utf-8")).hexdigest()[:16]
    return f"{f['check']}:{h}"


# What case/reward.py does with each fixture, filled in after the first run (see the module docstring).
# Fixtures not listed are controls: the grader returns the contract's label.
GRADER = {
    # F1: text after the JSON object is ignored (bare answer, or inside a fenced block).
    "answer:df35ee4f5cf34daa": "F1", "answer:97e0fa751297a94a": "F1", "answer:f08d98d9938fc3ff": "F1",
    "answer:1f5e9e3d870b4d40": "F1", "answer:a6e5c970a7d0aa78": "F1", "answer:b9e76acbf8992c1f": "F1",
    # F2: the items score divides by the number of reference items only.
    "items:0e4f8a209d882667": "F2", "items:c9733e725e3950ef": "F2", "items:626b8a6960422a82": "F2",
    "items:97cb0e2adef03567": "F2", "items:aeac784e134a6387": "F2", "items:83bed4a666b94e20": "F2",
    # F3: AttributeError when the answer starts with a JSON value that is not an object.
    "answer:93751ec6a097e138": "F3", "answer:afea8378e051a56a": "F3", "answer:4197c7476f3f64d5": "F3",
    "answer:16890eccf7d17c20": "F3", "answer:396a15a5180f7fe2": "F3",
    # F4: json errors other than JSONDecodeError escape (RecursionError, ValueError for long integers).
    "answer:107b473745bd1dec": "F4", "answer:0300e40cc038df78": "F4",
    # F5: decimal.Overflow on a total with a huge exponent.
    "total:c197ae2ec197c446": "F5", "total:96c2adf2bb40dc08": "F5",
    # F6: the total's distance is rounded to 28 significant digits before the comparison.
    "total:e56a1cb3f525a70d": "F6", "total:98c2931995549f4e": "F6",
    # Decision fixtures.
    "answer:7ce335eb306b3203": "reading-A",  # D-fence-tab
    "answer:12d1c458b72de9ec": "reading-B",  # D-crlf
    "answer:e79904ef5e29e976": "reading-A",  # D-whitespace
    "answer:978017d532252365": "reading-A",  # D-whitespace
    "customer:44ae1f3195228d07": "reading-A",  # D-whitespace
    "items:2eff2dbf3a9f5f7b": "reading-B",  # D-qty-decimal
    "items:d06634d92ba01a40": "reading-B",  # D-qty-decimal
    "items:0b4650fd6483fc5b": "reading-A",  # D-qty-bool
    "total:9e173617b36d501d": "reading-A",  # D-total-boundary
    "total:0abdc1577d47d0fa": "reading-A",  # D-total-boundary
    "total:cf53ca1a4079c7d8": "reading-A",  # D-json-constants
    "total:1aa61bd040c6658f": "reading-A",  # D-json-constants
}

for _f in FIXTURES:
    _f["id"] = fixture_id(_f)
    _f.setdefault("decision", None)
    _f.setdefault("needs_int_limit", None)
    _f["grader"] = GRADER.get(_f["id"])
