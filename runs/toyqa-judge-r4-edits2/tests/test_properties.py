"""Property and metamorphic tests (skill step 4).

Run from W:  python -B -m unittest discover -s audit/tests -t audit/tests -v

- Rendering: for random graded texts, the judge must see the stripped graded text cut to 300 characters (C1, C2).
- Metamorphic edits that the contract ignores must not change the verdict; edits it forbids must change it.
  These run the whole deterministic pipeline with judges.FakeJudge, the case's deterministic stand-in, which
  applies the rubric's normalisation; it isolates the deterministic stages, not the deployed judge.
- Reply parsing: appending a standalone grade letter to any reply must make it the grade (C4, last letter).
The `failures_*` helpers return the failing inputs, so a test failure shows counterexamples.
"""
import os
import random
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "scripts"))

from common import Scripted, grader, judges, predicted_in, questions, reference, replacement, template  # noqa: E402

TPL, QS = template(), questions()
Q01 = QS["q01"]
SEED = 20261111
CHARS = list("abcXYZ Canberra.,:;!?*_-") + ["\n", "\r\n", "\t", "\u2028", "\u00a0", "{", "}", "\u00e9", "\U0001F600"]


def graded_of(which, response):
    """The predicted answer the judge sees, or the label when the response never reaches the judge."""
    j = Scripted("A")
    try:
        if which == "G":
            grader.grade_response(j, TPL, Q01, response)
        elif which == "R":
            reference.ToyQAGrader(j, TPL).label(Q01, response)
        else:
            replacement.grade_response(j, TPL, Q01, response)
    except Exception as e:  # noqa: BLE001
        return "EXC:" + type(e).__name__
    return predicted_in(j.calls[0][0]) if j.calls else None


def failures_render(which, n=400):
    rnd = random.Random(SEED)
    bad = []
    for _ in range(n):
        g = "".join(rnd.choice(CHARS) for _ in range(rnd.randint(0, 420)))
        if rnd.random() < 0.05:
            g = " \n " * rnd.randint(1, 3)  # whitespace only
        if graded_of(which, g) != g.strip()[:300]:
            bad.append(g)
    return bad


def label_of(which, response):
    j = judges.FakeJudge()
    try:
        if which == "G":
            return grader.grade_response(j, TPL, Q01, response)["label"]
        if which == "R":
            return reference.ToyQAGrader(j, TPL).label(Q01, response)
        return replacement.grade_response(j, TPL, Q01, response)["label"]
    except Exception as e:  # noqa: BLE001
        return "EXC:" + type(e).__name__


BASES = {
    "one line": "Canberra is the capital.",
    "two lines, answer first": "Canberra.\nIt is in the Australian Capital Territory.",
    "two lines": "The capital is\nCanberra.",
    "think": "<think>Not Sydney.</think>\nThe capital is\nCanberra.",
}


def _lines(f):
    def edit(text):
        head, sep, body = text.rpartition("</think>")
        return head + sep + ("\n" if sep else "") + "\n".join(f(i, l) for i, l in enumerate(body.strip().split("\n")))
    return edit


IGNORED_EDITS = {
    "numbered label": _lines(lambda i, l: f"{i + 1}. {l}"),
    "bullet": _lines(lambda i, l: f"- {l}"),
    "bold": lambda t: t.replace("Canberra", "**Canberra**"),
    "italics": lambda t: t.replace("Canberra", "*Canberra*"),
    "html tag": lambda t: t.replace("Canberra", "<b>Canberra</b>"),
    "typographic quotes": lambda t: t.replace("Canberra", "\u201cCanberra\u201d"),
    "typographic apostrophe": lambda t: t.replace("Canberra", "Australia\u2019s Canberra"),
    "punctuation after word": lambda t: t.replace("Canberra", "Canberra!"),
    "blank line between lines": _lines(lambda i, l: ("\n" if i else "") + l),
    "trailing newline": lambda t: t + "\n",
}
FORBIDDEN_EDITS = {  # name -> (edit, label the edited response must get)
    "drop </think>": (lambda t: t.replace("</think>", ""), "extraction_failure"),
    "wrong answer": (lambda t: t.replace("Canberra", "Sydney"), "incorrect"),
}


def failures_metamorphic(which):
    bad = []
    for bname, base in BASES.items():
        assert label_of("X", base) == "correct", bname
        for ename, edit in IGNORED_EDITS.items():
            got = label_of(which, edit(base))
            if got != "correct":
                bad.append((bname, ename, got))
        for ename, (edit, want) in FORBIDDEN_EDITS.items():
            if ename == "drop </think>" and "</think>" not in base:
                continue
            got = label_of(which, edit(base))
            if got != want:
                bad.append((bname, ename, got))
    return bad


PARSE_CHARS = list("ABCabc019 _.:*()") + ["\u00e9", "\uff21", "\n"]


def failures_parse(which, n=1000):
    rnd = random.Random(SEED + 1)
    parse = {"G": grader.parse_grade, "R": reference.ToyQAGrader.grade_of, "X": replacement.parse_grade}[which]
    bad = []
    for _ in range(n):
        s = "".join(rnd.choice(PARSE_CHARS) for _ in range(rnd.randint(0, 30)))
        letter = rnd.choice("ABC")
        if parse(s + " " + letter) != letter:
            bad.append(s + " " + letter)
    return bad


class TestRenderProperty(unittest.TestCase):
    def test_replacement(self):
        self.assertEqual(failures_render("X")[:3], [])

    def test_reference(self):
        self.assertEqual(failures_render("R")[:3], [])

    @unittest.expectedFailure  # F2 (first line only) and F3 (IndexError on empty graded text)
    def test_grader(self):
        self.assertEqual(failures_render("G")[:3], [])


class TestMetamorphic(unittest.TestCase):
    def test_replacement(self):
        self.assertEqual(failures_metamorphic("X"), [])

    def test_reference(self):
        self.assertEqual(failures_metamorphic("R"), [])

    @unittest.expectedFailure  # F2 on every multi-line edit, F1 on "drop </think>"
    def test_grader(self):
        self.assertEqual(failures_metamorphic("G"), [])


class TestParseProperty(unittest.TestCase):
    def test_replacement(self):
        self.assertEqual(failures_parse("X")[:3], [])

    def test_reference(self):
        self.assertEqual(failures_parse("R")[:3], [])

    @unittest.expectedFailure  # F4: first capital letter anywhere wins
    def test_grader(self):
        self.assertEqual(failures_parse("G")[:3], [])


if __name__ == "__main__":
    unittest.main()
