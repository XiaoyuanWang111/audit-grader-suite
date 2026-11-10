"""Step 4: property, metamorphic and loose-transform tests against the grader under audit.

Each case states the contract's expectation. Cases the grader violates carry
pytest.mark.xfail(strict=True) with the finding id, like the fixtures.
"""
import pytest

import ifb
import ifbench_contract as rep
from fixtures_data import ROWS

NL = chr(10)


def kw_of(key, iid):
    row = ROWS[key]
    return dict(row["kwargs"][row["instruction_id_list"].index(iid)]), row["prompt"]


def g(iid, key, text, mode="strict"):
    kw, prompt = kw_of(key, iid)
    v, err = ifb.verdict("grader", iid, kw, prompt, text, mode=mode)
    assert err is None, err
    return v


def p(iid, key, text):
    kw, prompt = kw_of(key, iid)
    return rep.check(iid, kw, prompt, text)


def case(id_, finding=""):
    return {"id": id_, "marks": [pytest.mark.xfail(strict=True, reason=finding)] if finding else []}


# ---- metamorphic: edits the contract ignores must not change the verdict
NBB = "Deism sees God as distant. This view has problems.\n* It ignores revelation.\n* It weakens prayer."
STAIRS1 = "Line one\n  Line two\n\n    Line three"
INVARIANT = [
    ("format:options", "100", "Maybe", "Maybe" + NL, case("options-trailing-newline", "F-options-whitespace")),
    ("format:no_bullets_bullets", "98", NBB, NBB + NL, case("nbb-trailing-newline", "F-nbb-blank-line")),
    ("format:line_indent", "74", STAIRS1, STAIRS1.replace(NL + NL, NL + NL + NL), case("indent-second-blank-line", "F-indent-blank-lines")),
    ("format:line_indent", "74", "Line one\n  Line two\n    Line three", "Line one\n\tLine two\n\t\tLine three",
     case("indent-tabs-for-spaces", "F-indent-tabs")),
    ("words:start_verb", "257", "Consider an empire of pain.", "**Consider** an empire of pain.", case("startverb-bold", "F-startverb-markup")),
    ("count:conjunctions", "7", "Cats and dogs play, but birds sing.", "Cats and dogs play, but birds sing. And fish swim.",
     case("conjunctions-repeat-and", "F-conj-surface-forms")),
    ("words:paragraph_last_first", "241", "Sets can be open sets\nOpen intervals stay open", "Sets can be open sets\n\nOpen intervals stay open",
     case("paragraph-blank-line")),
]


@pytest.mark.parametrize("iid,key,a,b", [pytest.param(*x[:4], id=x[4]["id"], marks=x[4]["marks"]) for x in INVARIANT])
def test_invariant_edit(iid, key, a, b):
    assert p(iid, key, a) == p(iid, key, b)  # the contract itself is invariant
    assert g(iid, key, a) == g(iid, key, b)


# ---- edits the contract forbids must turn a pass into a fail
KW_PASS = ("The door is blue. Bread and bread. Blue blue. Lamp lamp lamp lamp lamp. "
           "River river river river river river river.")
TPL = "My Answer: Suffering on a cosmic scale.\nMy Conclusion: It is a thought experiment.\nFuture Outlook: More research is needed."
SUB = "* Light drops\n  - Photosynthesis slows\n* Temperature falls\n  - Growth pauses"
FORBIDDEN = [
    ("count:keywords_multiple", "2", KW_PASS, KW_PASS + " A door.", case("keywords-extra-occurrence")),
    ("format:sub-bullets", "126", SUB, SUB.replace("* ", ""), case("subbullets-bullets-removed", "F-subbullets-none")),
    ("format:output_template", "292", TPL, NL.join(reversed(TPL.split(NL))), case("template-reordered", "F-template-presence-only")),
    ("ratio:sentence_words", "166", "Cats nap. Dogs run. Owls fly.", "Cats nap. Cats run. Cats fly.", case("sentwords-repeated-word", "F-sentwords-no-word-check")),
    ("format:no_whitespace", "298", "Piousegoists", "Pious egoists", case("nowhitespace-space")),
    ("count:punctuation", "36", "Wait?! The plan (draft [v2] {final}) is ready: it isn't \"done\" -- yet; it is well-known... sure, really! Is it? Yes.",
     "Wait?! The plan draft v2 final is ready: it is done, yet; it is known... sure, really! Is it? Yes.",
     case("punctuation-marks-removed", "F-punct-six-marks")),
]


@pytest.mark.parametrize("iid,key,good,bad", [pytest.param(*x[:4], id=x[4]["id"], marks=x[4]["marks"]) for x in FORBIDDEN])
def test_forbidden_edit(iid, key, good, bad):
    assert p(iid, key, good) and not p(iid, key, bad)
    assert g(iid, key, good) and not g(iid, key, bad)


# ---- loose transform (G4): a loose pass must not come from deleting text the instruction constrains
LOOSE = [
    ("format:sub-bullets", "126", "* Light drops\n* Temperature falls", False, case("loose-subbullets-asterisks", "F-loose-deletes-constrained")),
    ("words:start_verb", "257", "Here is my answer.\nConsider an empire of pain.", False, case("loose-startverb-first-line", "F-loose-deletes-constrained")),
    ("count:keywords_multiple", "2", KW_PASS + "\nRiver.", False, case("loose-keywords-last-line", "F-loose-deletes-constrained")),
    ("count:numbers", "17", "In 2020 the team had 15 players.\nThat was 3 years ago.", False, case("loose-numbers-last-line", "F-loose-deletes-constrained")),
    ("format:no_bullets_bullets", "98", NBB + "\nIn short, the view fails.", True, case("loose-nbb-closing-line")),
]


@pytest.mark.parametrize("iid,key,text,label", [pytest.param(*x[:4], id=x[4]["id"], marks=x[4]["marks"]) for x in LOOSE])
def test_loose(iid, key, text, label):
    assert p(iid, key, text) == label
    assert g(iid, key, text, mode="loose") == label
