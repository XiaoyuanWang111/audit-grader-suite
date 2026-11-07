"""Labeled fixtures for the ToyOrders reward, labeled from audit/CONTRACT.md alone.

Each fixture has:
    check      the contract check it targets (answer, customer, date, items, total,
               extra_keys, reward, content_free)
    kind       pass, fail or near-miss (a fail that differs from a pass by one small edit)
    order_id   the order whose reference grades it
    response   the exact response text
    expected   the reward under the contract's proposed readings
    readings   for a decision fixture: {decision id: {reading: reward}}
    grader     None when case/reward.py should agree with `expected`; otherwise the finding or
               decision id that explains its verdict (these tests are strict expected failures)
    id         check name plus the first 12 hex digits of sha256(check, order_id, response)

The labels were written by hand from the contract; no grader computed them.
"""
import hashlib
import sys

from support import DELETE, Pairs, Raw, correct, correct_text, dump

C01 = correct_text("o01")
C10_TOTAL = '{"total":24}'  # o10's total alone: 0.25 when the gate passes
R_2_3 = (3 + 2 / 3) / 4  # all fields right, items 2 of 3

# Python 3.11+ (and the 3.10.7, 3.9.14, 3.8.14 security releases) limit int parsing to 4,300 digits.
INT_DIGIT_LIMIT = hasattr(sys, "get_int_max_str_digits")


def _items(*pairs):
    return [{"sku": s, "qty": q} for s, q in pairs]


def _o01(**changes):
    return correct_text("o01", **changes)


RAW_FIXTURES = [
    # ---- answer: extraction and parse gate -----------------------------------------------
    dict(check="answer", kind="pass", order_id="o01", response=C01, expected=1.0),
    dict(check="answer", kind="pass", order_id="o01", response="```json\n" + C01 + "\n```", expected=1.0),
    dict(check="answer", kind="pass", order_id="o01", response="```\n" + C01 + "\n```", expected=1.0),
    dict(check="answer", kind="pass", order_id="o01", response="```json   \n" + C01 + "\n```", expected=1.0),
    dict(check="answer", kind="pass", order_id="o01", response="\n\n  " + C01 + "  \n\t", expected=1.0),
    dict(check="answer", kind="pass", order_id="o01", response="```json\n\n" + C01 + "\n\n```", expected=1.0),
    dict(check="answer", kind="pass", order_id="o01", response=dump(correct("o01"), indent=2), expected=1.0),
    dict(check="answer", kind="pass", order_id="o01",
         response=dump(correct("o01"), indent=2).replace("\n", "\r\n"), expected=1.0,
         note="CRLF line breaks inside unfenced JSON are JSON whitespace"),
    dict(check="answer", kind="near-miss", order_id="o01", response=C01 + "\nHope this helps!", expected=0.0, grader="F1"),
    dict(check="answer", kind="near-miss", order_id="o01",
         response="```json\n" + C01 + "\nNote: shipping is included.\n```", expected=0.0, grader="F1"),
    dict(check="answer", kind="fail", order_id="o01", response=C01 + "\n" + C01, expected=0.0, grader="F1"),
    dict(check="answer", kind="fail", order_id="o01",
         response="```json\n" + C01 + "\n```\n```json\n" + C01 + "\n```", expected=0.0, grader="F1"),
    dict(check="answer", kind="near-miss", order_id="o01", response=C01 + "}", expected=0.0, grader="F1"),
    dict(check="answer", kind="fail", order_id="o10", response=C10_TOTAL + "x", expected=0.0, grader="F1",
         note="smallest F1 reproducer: the grader gives 0.25"),
    dict(check="answer", kind="fail", order_id="o01", response="Here is the JSON: " + C01, expected=0.0),
    dict(check="answer", kind="fail", order_id="o01", response="Sure!\n```json\n" + C01 + "\n```", expected=0.0),
    dict(check="answer", kind="fail", order_id="o01", response="```json\n" + C01 + "\n```\nHope this helps!", expected=0.0),
    dict(check="answer", kind="fail", order_id="o01", response="[" + C01 + "]", expected=0.0, grader="F2"),
    dict(check="answer", kind="fail", order_id="o01", response="2 items: AB-100 and CD-220, total $64.50", expected=0.0, grader="F2"),
    dict(check="answer", kind="fail", order_id="o01", response='"Maria Lopez"', expected=0.0, grader="F2"),
    dict(check="answer", kind="fail", order_id="o01", response="true", expected=0.0, grader="F2"),
    dict(check="answer", kind="fail", order_id="o01", response="NaN", expected=0.0, grader="F2"),
    dict(check="answer", kind="fail", order_id="o01", response="0", expected=0.0, grader="F2",
         note="smallest F2 reproducer: the grader raises AttributeError"),
    dict(check="answer", kind="fail", order_id="o01", response="null", expected=0.0),
    dict(check="answer", kind="fail", order_id="o01", response="", expected=0.0),
    dict(check="answer", kind="fail", order_id="o01", response=" \n\t ", expected=0.0),
    dict(check="answer", kind="fail", order_id="o01", response="```json " + C01 + "```", expected=0.0),
    dict(check="answer", kind="near-miss", order_id="o01", response="```json\n" + C01 + "```", expected=0.0),
    dict(check="answer", kind="near-miss", order_id="o01", response="```JSON\n" + C01 + "\n```", expected=0.0),
    dict(check="answer", kind="fail", order_id="o01", response="```javascript\n" + C01 + "\n```", expected=0.0),
    dict(check="answer", kind="fail", order_id="o01", response="``` json\n" + C01 + "\n```", expected=0.0),
    dict(check="answer", kind="fail", order_id="o01", response="~~~json\n" + C01 + "\n~~~", expected=0.0),
    dict(check="answer", kind="fail", order_id="o01", response="````json\n" + C01 + "\n````", expected=0.0),
    dict(check="answer", kind="near-miss", order_id="o01", response="```json\t\n" + C01 + "\n```", expected=0.0, grader="F7"),
    dict(check="answer", kind="fail", order_id="o10", response="```json\t\n" + C10_TOTAL + "\n```", expected=0.0, grader="F7",
         note="smallest F7 reproducer: the grader gives 0.25"),
    dict(check="answer", kind="near-miss", order_id="o01", response=C01[:-1] + ", }", expected=0.0),
    dict(check="answer", kind="near-miss", order_id="o01", response=C01.replace("Maria Lopez", "Maria\tLopez"), expected=0.0,
         note="a raw tab inside a JSON string is invalid JSON to Python's json module"),
    dict(check="answer", kind="fail", order_id="o01", response=C01.replace('"', "'"), expected=0.0),
    dict(check="answer", kind="fail", order_id="o01", response="<think>The email is from Maria.</think>\n" + C01, expected=0.0),
    dict(check="answer", kind="fail", order_id="o01", response='{"a": ' + "[" * 100000 + "]" * 100000 + "}", expected=0.0,
         grader="F5", note="deep nesting; on CPython 3.12.10 the grader raises from a depth of 2,997"),
    dict(check="answer", kind="fail", order_id="o01", response='{"total": ' + "1" * 4301 + "}", expected=0.0,
         grader="F5" if INT_DIGIT_LIMIT else None, note="4,301-digit integer; raises only where the int digit limit exists"),
    dict(check="answer", kind="fail", order_id="o01", response='{"a": 1,}', expected=0.0),

    # ---- customer ------------------------------------------------------------------------
    dict(check="customer", kind="pass", order_id="o01", response=_o01(customer="maria lopez"), expected=1.0),
    dict(check="customer", kind="pass", order_id="o01", response=_o01(customer="  MARIA LOPEZ "), expected=1.0),
    dict(check="customer", kind="pass", order_id="o06", response=correct_text("o06", customer="Lars Nilßon"), expected=1.0,
         note="str.casefold maps the sharp s to ss, so the stated comparison accepts it"),
    dict(check="customer", kind="near-miss", order_id="o01", response=_o01(customer="Maria  Lopez"), expected=0.75),
    dict(check="customer", kind="fail", order_id="o01", response=_o01(customer="Maria"), expected=0.75),
    dict(check="customer", kind="fail", order_id="o01", response=_o01(customer=["Maria", "Lopez"]), expected=0.75),
    dict(check="customer", kind="fail", order_id="o01", response=_o01(customer=None), expected=0.75),
    dict(check="customer", kind="fail", order_id="o01", response=_o01(customer=DELETE), expected=0.75),
    dict(check="customer", kind="fail", order_id="o01",
         response=dump({"Customer": "Maria Lopez", **{k: v for k, v in correct("o01").items() if k != "customer"}}),
         expected=0.65, note="Customer is an extra key and customer is missing"),

    # ---- date ----------------------------------------------------------------------------
    dict(check="date", kind="near-miss", order_id="o01", response=_o01(date=" 2026-03-07"), expected=0.75),
    dict(check="date", kind="fail", order_id="o01", response=_o01(date="2026-3-7"), expected=0.75),
    dict(check="date", kind="fail", order_id="o01", response=_o01(date="2026/03/07"), expected=0.75),
    dict(check="date", kind="fail", order_id="o04", response=correct_text("o04", date="2026-12-03"), expected=0.75),
    dict(check="date", kind="fail", order_id="o01", response=_o01(date=20260307), expected=0.75),

    # ---- items ---------------------------------------------------------------------------
    dict(check="items", kind="pass", order_id="o01", response=_o01(items=_items(("CD-220", 1), ("AB-100", 2))), expected=1.0),
    dict(check="items", kind="pass", order_id="o01",
         response=_o01(items=[{"sku": "AB-100", "qty": 2, "name": "desk lamp"}, {"sku": "CD-220", "qty": 1, "name": "bulb pack"}]),
         expected=1.0),
    dict(check="items", kind="pass", order_id="o01", response=_o01(items=[{"qty": 2, "sku": "AB-100"}, {"qty": 1, "sku": "CD-220"}]),
         expected=1.0),
    dict(check="items", kind="near-miss", order_id="o01", response=_o01(items=_items(("AB-100", 3), ("CD-220", 1))), expected=0.875),
    dict(check="items", kind="near-miss", order_id="o01", response=_o01(items=_items(("ab-100", 2), ("CD-220", 1))), expected=0.875),
    dict(check="items", kind="near-miss", order_id="o01", response=_o01(items=_items(("AB-100", "2"), ("CD-220", 1))), expected=0.875),
    dict(check="items", kind="fail", order_id="o01", response=_o01(items={"AB-100": 2, "CD-220": 1}), expected=0.75),
    dict(check="items", kind="fail", order_id="o01", response=_o01(items=[]), expected=0.75),
    dict(check="items", kind="near-miss", order_id="o01", response=_o01(items=_items(("AB-100", 2), ("CD-220", 1), ("ZZ-999", 5))),
         expected=R_2_3, grader="F3"),
    dict(check="items", kind="near-miss", order_id="o01", response=_o01(items=_items(("AB-100", 2), ("AB-100", 2), ("CD-220", 1))),
         expected=R_2_3, grader="F3"),
    dict(check="items", kind="near-miss", order_id="o01", response=_o01(items=_items(("AB-100", 2), ("CD-220", 1)) + ["gift wrap"]),
         expected=R_2_3, grader="F3"),
    dict(check="items", kind="near-miss", order_id="o01",
         response=_o01(items=_items(("AB-100", 2), ("CD-220", 1)) + [{"note": "gift wrap"}]), expected=R_2_3, grader="F3"),
    dict(check="items", kind="fail", order_id="o02",
         response=correct_text("o02", items=_items(*[("EF-310", q) for q in range(1, 6)])), expected=0.8, grader="F3",
         note="hedging over quantities: the grader gives the full reward"),
    dict(check="items", kind="fail", order_id="o02", response='{"items":[{"sku":"EF-310","qty":3},0]}', expected=0.125, grader="F3",
         note="smallest F3 reproducer: the grader gives 0.25"),
    dict(check="items", kind="fail", order_id="o01", response=_o01(items=_items(("AB-100", 2), ("AB-100", 2))), expected=0.875),
    dict(check="items", kind="near-miss", order_id="o01", response=_o01(items=[{"sku": "AB-100", "qty": 2}, {"sku": "CD-220", "qty": True}]),
         expected=0.875, readings={"D-qty-bool": {"reject": 0.875, "accept": 1.0}}),
    dict(check="items", kind="near-miss", order_id="o01", response=_o01(items=[{"sku": "AB-100", "qty": Raw("2.0")}, {"sku": "CD-220", "qty": 1}]),
         expected=0.875, readings={"D-qty-integral": {"type": 0.875, "value": 1.0}}, grader="D-qty-integral"),
    dict(check="items", kind="near-miss", order_id="o01", response=_o01(items=[{"sku": "AB-100", "qty": Raw("2e0")}, {"sku": "CD-220", "qty": 1}]),
         expected=0.875, readings={"D-qty-integral": {"type": 0.875, "value": 1.0}}, grader="D-qty-integral"),
    dict(check="items", kind="fail", order_id="o01", response=_o01(items=[{"sku": "AB-100", "qty": Raw("2.5")}, {"sku": "CD-220", "qty": 1}]),
         expected=0.875),
    dict(check="items", kind="fail", order_id="o10", response='{"items":[{"sku":"GH-825","qty":true}]}', expected=0.0,
         readings={"D-qty-bool": {"reject": 0.0, "accept": 0.25}}),
    dict(check="items", kind="fail", order_id="o02", response='{"items":[{"sku":"EF-310","qty":3.0}]}', expected=0.0,
         readings={"D-qty-integral": {"type": 0.0, "value": 0.25}}, grader="D-qty-integral"),

    # ---- total ---------------------------------------------------------------------------
    dict(check="total", kind="pass", order_id="o03", response=correct_text("o03", total=Raw("47")), expected=1.0),
    dict(check="total", kind="pass", order_id="o01", response=_o01(total=Raw("6.45e1")), expected=1.0),
    dict(check="total", kind="pass", order_id="o01", response=_o01(total=Raw("64.504")), expected=1.0),
    dict(check="total", kind="pass", order_id="o01", response=_o01(total=Raw("64.5000")), expected=1.0),
    dict(check="total", kind="near-miss", order_id="o01", response=_o01(total=Raw("64.505")), expected=1.0,
         readings={"D-total-boundary": {"inclusive": 1.0, "exclusive": 0.75}}),
    dict(check="total", kind="near-miss", order_id="o01", response=_o01(total=Raw("64.495")), expected=1.0,
         readings={"D-total-boundary": {"inclusive": 1.0, "exclusive": 0.75}}),
    dict(check="total", kind="near-miss", order_id="o01", response=_o01(total=Raw("64.5051")), expected=0.75),
    dict(check="total", kind="fail", order_id="o01", response=_o01(total="64.50"), expected=0.75),
    dict(check="total", kind="fail", order_id="o01", response=_o01(total="$64.50"), expected=0.75),
    dict(check="total", kind="fail", order_id="o01", response=_o01(total=True), expected=0.75),
    dict(check="total", kind="fail", order_id="o01", response=_o01(total=Raw("NaN")), expected=0.75),
    dict(check="total", kind="fail", order_id="o01", response=_o01(total=Raw("Infinity")), expected=0.75),
    dict(check="total", kind="fail", order_id="o01", response=_o01(total=Raw("1e1000000")), expected=0.75, grader="F4"),
    dict(check="total", kind="fail", order_id="o01", response='{"total":1e1000000}', expected=0.0, grader="F4",
         note="smallest F4 reproducer: the grader raises decimal.Overflow"),
    dict(check="total", kind="fail", order_id="o01", response=_o01(total=Raw("1e-1000000")), expected=0.75),
    dict(check="total", kind="near-miss", order_id="o01", response=_o01(total=Raw("64.5050000000000000000000000000001")),
         expected=0.75, grader="F6"),
    dict(check="total", kind="near-miss", order_id="o01", response='{"total":64.4949999999999999999999999999999}', expected=0.0,
         grader="F6", note="smallest F6 reproducer: the grader gives 0.25"),
    dict(check="total", kind="fail", order_id="o05", response=correct_text("o05", total=Raw("54.99")), expected=0.75),

    # ---- extra_keys ----------------------------------------------------------------------
    dict(check="extra_keys", kind="near-miss", order_id="o01", response=dump({**correct("o01"), "notes": ""}), expected=0.9),
    dict(check="extra_keys", kind="near-miss", order_id="o01",
         response=dump(Pairs(list(correct("o01").items()) + [("notes", 1), ("notes", 2)])), expected=0.9),
    dict(check="extra_keys", kind="pass", order_id="o01",
         response=dump(Pairs([("customer", "Maria")] + list(correct("o01").items()))), expected=1.0,
         note="a repeated key keeps its last value"),
    dict(check="extra_keys", kind="fail", order_id="o01",
         response=dump({**correct("o01"), **{"k%d" % i: i for i in range(11)}}), expected=0.0),
    dict(check="extra_keys", kind="fail", order_id="o01",
         response=dump({**{k: v for k, v in correct("o01").items() if k != "total"}, "Total": Raw("64.50")}), expected=0.65),

    # ---- reward: aggregation -------------------------------------------------------------
    dict(check="reward", kind="fail", order_id="o01", response='{"customer": "Maria Lopez", "date": "2026-03-07"}', expected=0.5),
    dict(check="reward", kind="fail", order_id="o01", response='{"a": 1, "b": 2, "c": 3, "d": 4, "e": 5}', expected=0.0),
    dict(check="reward", kind="near-miss", order_id="o06",
         response=correct_text("o06", items=_items(("QR-940", 2), ("ST-150", 2), ("UV-260", 2))), expected=R_2_3),
    dict(check="reward", kind="fail", order_id="o01", response="{}", expected=0.0),

    # ---- decision fixtures: line breaks and whitespace in the fence -------------------------
    dict(check="answer", kind="near-miss", order_id="o01", response="```json\r\n" + C01 + "\r\n```", expected=1.0,
         readings={"D-fence-newline": {"universal": 1.0, "lf": 0.0}}, grader="D-fence-newline"),
    dict(check="answer", kind="near-miss", order_id="o10", response="```json\r\n" + C10_TOTAL + "\r\n```", expected=0.25,
         readings={"D-fence-newline": {"universal": 0.25, "lf": 0.0}}, grader="D-fence-newline"),
    dict(check="answer", kind="near-miss", order_id="o01", response="```json\n " + C01 + "\n```", expected=1.0,
         readings={"D-inner-whitespace": {"strip": 1.0, "json": 0.0}}),

    # ---- content-free responses (step 4) ---------------------------------------------------
    dict(check="content_free", kind="fail", order_id="o01", response="PROMPT:o01", expected=0.0,
         note="the rendered prompt itself, restating the instructions"),
    dict(check="content_free", kind="fail", order_id="o01", response='{"customer": "", "date": "", "items": [], "total": 0}', expected=0.0),
    dict(check="content_free", kind="fail", order_id="o01",
         response=dump({"customer": "the customer's full name, as written in the email", "date": "YYYY-MM-DD",
                        "items": [{"sku": "the product code, a string", "qty": 0}], "total": 0}), expected=0.0),
    dict(check="content_free", kind="fail", order_id="o01", response=(C01 + "\n") * 3, expected=0.0, grader="F1",
         note="the correct answer repeated three times"),
    dict(check="content_free", kind="fail", order_id="o01", response="EMAIL:o01", expected=0.0, note="the email echoed back"),
    dict(check="content_free", kind="fail", order_id="o01",
         response="Read the order email below and reply with a JSON object that has exactly these keys: customer, date, items, total.",
         expected=0.0),
]

# Fully correct answers for every order: pass controls for all twelve references.
for _oid in ("o%02d" % i for i in range(1, 13)):
    RAW_FIXTURES.append(dict(check="reward", kind="pass", order_id=_oid, response=correct_text(_oid), expected=1.0))


def _expand(response, order_id):
    """PROMPT:<id> and EMAIL:<id> stand for the rendered prompt and the email of an order."""
    import json
    from support import ROOT
    if response.startswith(("PROMPT:", "EMAIL:")):
        kind, oid = response.split(":", 1)
        rows = {json.loads(l)["order_id"]: json.loads(l) for l in open(ROOT / "case" / "orders.jsonl", encoding="utf-8") if l.strip()}
        if kind == "EMAIL":
            return rows[oid]["email"]
        template = (ROOT / "case" / "prompt_template.txt").read_text(encoding="utf-8")
        return template.replace("{email}", rows[oid]["email"])
    return response


def fixture_id(check, order_id, response):
    digest = hashlib.sha256("\0".join((check, order_id, response)).encode("utf-8", "surrogatepass")).hexdigest()
    return "%s:%s" % (check, digest[:12])


def build():
    out = []
    for raw in RAW_FIXTURES:
        f = dict(raw)
        f["response"] = _expand(f["response"], f["order_id"])
        f.setdefault("readings", None)
        f.setdefault("grader", None)
        f.setdefault("note", "")
        f["id"] = fixture_id(f["check"], f["order_id"], f["response"])
        out.append(f)
    ids = [f["id"] for f in out]
    assert len(ids) == len(set(ids)), "duplicate fixture"
    return out


FIXTURES = build()
