"""Step 4: property and metamorphic tests over all twelve orders.

Each property starts from the fully correct answer of every order. Invariance properties
apply an edit that the contract ignores, so the reward must stay 1.0. Forbidden-edit
properties apply an edit that the contract penalizes, so the reward must become the stated
value. The grader's failing properties are strict expected failures, named by finding.
"""
import unittest

from fixtures import FIXTURES
from support import REFS, Raw, correct, dump, grader, replacement, run, verdict_ok, xfail_strict

ORDERS = sorted(REFS)


def _compact(text):
    return text.replace(", ", ",").replace(": ", ":")


def _total_forms(order_id):
    t = REFS[order_id]["total"]
    forms = [format(t, "f"), format(t.normalize(), "f"), "%sE+1" % format(t.scaleb(-1), "f"), format(t, "f") + "000"]
    if t == t.to_integral_value():
        forms.append(str(int(t)))
    return forms


def _with(order_id, **changes):
    obj = correct(order_id)
    obj.update(changes)
    return obj


def _n(order_id):
    return len(REFS[order_id]["items"])


# Each property: name -> (function(order_id) -> list of (response, expected reward), grader mark).
INVARIANT = {
    "key_order_reversed": (lambda o: [(dump(dict(reversed(list(correct(o).items())))), 1.0)], None),
    "items_reversed": (lambda o: [(dump(_with(o, items=list(reversed(correct(o)["items"])))), 1.0)], None),
    "pretty_printed": (lambda o: [(dump(correct(o), indent=2), 1.0)], None),
    "compact": (lambda o: [(_compact(dump(correct(o))), 1.0)], None),
    "fence_json": (lambda o: [("```json\n" + dump(correct(o)) + "\n```", 1.0)], None),
    "fence_bare": (lambda o: [("```\n" + dump(correct(o)) + "\n```", 1.0)], None),
    "fence_spaces_after_tag": (lambda o: [("```json  \n" + dump(correct(o)) + "\n```", 1.0)], None),
    "outer_whitespace": (lambda o: [("\n \t" + dump(correct(o)) + " \n\n", 1.0)], None),
    "customer_upper_and_padded": (lambda o: [(dump(_with(o, customer=" " + REFS[o]["customer"].upper() + " ")), 1.0)], None),
    "total_number_forms": (lambda o: [(dump(_with(o, total=Raw(f))), 1.0) for f in _total_forms(o)], None),
    "item_other_keys": (lambda o: [(dump(_with(o, items=[dict(i, name="x") for i in correct(o)["items"]])), 1.0)], None),
    "item_key_order": (lambda o: [(dump(_with(o, items=[{"qty": i["qty"], "sku": i["sku"]} for i in correct(o)["items"]])), 1.0)], None),
    "crlf_inside_json": (lambda o: [(dump(correct(o), indent=2).replace("\n", "\r\n"), 1.0)], None),
}

FORBIDDEN = {
    "text_after_object": (lambda o: [(dump(correct(o)) + "\nDone.", 0.0)], "F1"),
    "text_inside_fence_after_object": (lambda o: [("```json\n" + dump(correct(o)) + "\nDone.\n```", 0.0)], "F1"),
    "second_copy": (lambda o: [(dump(correct(o)) + "\n" + dump(correct(o)), 0.0)], "F1"),
    "text_before_object": (lambda o: [("Answer: " + dump(correct(o)), 0.0)], None),
    "wrapped_in_array": (lambda o: [("[" + dump(correct(o)) + "]", 0.0)], "F2"),
    "extra_wrong_item": (lambda o: [(dump(_with(o, items=correct(o)["items"] + [{"sku": "ZZ-999", "qty": 1}])),
                                     (3 + _n(o) / (_n(o) + 1)) / 4)], "F3"),
    "duplicated_item": (lambda o: [(dump(_with(o, items=correct(o)["items"] + correct(o)["items"][:1])),
                                    (3 + _n(o) / (_n(o) + 1)) / 4)], "F3"),
    "extra_top_level_key": (lambda o: [(dump(_with(o, notes="none")), 0.9)], None),
    "skus_lower_case": (lambda o: [(dump(_with(o, items=[{"sku": i["sku"].lower(), "qty": i["qty"]} for i in correct(o)["items"]])), 0.75)], None),
    "date_with_slashes": (lambda o: [(dump(_with(o, date=REFS[o]["date"].replace("-", "/"))), 0.75)], None),
    "first_qty_plus_one": (lambda o: [(dump(_with(o, items=[{"sku": i["sku"], "qty": i["qty"] + (k == 0)} for k, i in enumerate(correct(o)["items"])])),
                                       (3 + (_n(o) - 1) / _n(o)) / 4)], None),
    "total_off_by_one_cent": (lambda o: [(dump(_with(o, total=Raw(format(REFS[o]["total"] + REFS[o]["total"].__class__("0.01"), "f")))), 0.75)], None),
}


def _check(test, fn, prop):
    for order_id in ORDERS:
        for response, expected in prop(order_id):
            with test.subTest(order=order_id, response=response[:40]):
                outcome = run(fn, response, REFS[order_id])
                test.assertTrue(verdict_ok(outcome, expected), "%s: %r, expected %r" % (order_id, outcome, expected))


class GraderProperties(unittest.TestCase):
    """case/reward.py."""


class ReplacementProperties(unittest.TestCase):
    """audit/replacement/reward_contract.py with the proposed readings."""


def _make(fn, prop, mark):
    def test(self):
        _check(self, fn, prop)
    if mark:
        test = xfail_strict(mark)(test)
    return test


for _group in (INVARIANT, FORBIDDEN):
    for _name, (_prop, _mark) in _group.items():
        setattr(GraderProperties, "test_" + _name, _make(grader.reward, _prop, _mark))
        setattr(ReplacementProperties, "test_" + _name, _make(replacement.reward, _prop, None))


class Metamorphic(unittest.TestCase):
    """Relations between graded responses rather than fixed labels."""

    def _fence_relation(self, fn):
        # Fencing an unfenced response does not change the answer text, so not the reward.
        for f in FIXTURES:
            r = f["response"]
            if "`" in r or "\r" in r or len(r) > 10000:
                continue
            ref = REFS[f["order_id"]]
            plain, fenced = run(fn, r, ref), run(fn, "```json\n" + r.strip() + "\n```", ref)
            with self.subTest(fixture=f["id"]):
                self.assertEqual(plain, fenced)

    def test_grader_fence_invariance(self):
        self._fence_relation(grader.reward)

    def test_replacement_fence_invariance(self):
        self._fence_relation(replacement.reward)

    def test_replacement_never_raises_on_fixtures(self):
        for f in FIXTURES:
            for kw in ({}, replacement.OFFICIAL):
                status, value = run(replacement.reward, f["response"], REFS[f["order_id"]], **kw)
                self.assertEqual(status, "ok", f["id"])
                self.assertIs(type(value), float)
                self.assertTrue(0.0 <= value <= 1.0)


if __name__ == "__main__":
    unittest.main()
