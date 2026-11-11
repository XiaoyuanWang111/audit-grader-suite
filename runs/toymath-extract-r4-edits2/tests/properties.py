"""Metamorphic edits for step 4.

Each edit maps (problem_id, reference string) to a response. `expect` is the
contract label under the proposed readings: "correct" for an edit the contract
ignores (applied to a passing response), "not_correct" for an edit it forbids.
`depends` names the decision entry whose other reading changes the expectation.
"""
from decimal import Decimal

REASONING = ["Step one works through the problem.", "The result follows from the given numbers."]


def _resp(lines, answer_line, sep="\n", tail=""):
    return sep.join(lines + [answer_line]) + tail


def _fmt(d):
    s = format(d, "f")
    return s


def _commas(ref):
    d = Decimal(ref)
    neg = d < 0
    s = format(abs(d), "f")
    ip, _, fp = s.partition(".")
    grouped = f"{int(ip):,}"
    return ("-" if neg else "") + grouped + ("." + fp if fp else "")


def _trailing_zero(ref):
    return ref + "0" if "." in ref else ref + ".0"


# (name, expect, depends, applies(ref) -> bool, build(ref) -> response)
EDITS = [
    # --- edits the contract ignores ---
    ("base", "correct", None, lambda r: True, lambda r: _resp(REASONING, f"Answer: {r}")),
    ("numbered-lines", "correct", None, lambda r: True,
     lambda r: _resp([f"{i}. {l}" for i, l in enumerate(REASONING, 1)], f"Answer: {r}")),
    ("bulleted-lines", "correct", None, lambda r: True,
     lambda r: _resp([f"- {l}" for l in REASONING], f"Answer: {r}")),
    ("bold-first-word", "correct", None, lambda r: True,
     lambda r: _resp(["**Step** one works through the problem.", REASONING[1]], f"Answer: {r}")),
    ("italic-html-word", "correct", None, lambda r: True,
     lambda r: _resp(["Step one works through the *problem*.", "The <b>result</b> follows from the given numbers."], f"Answer: {r}")),
    ("typographic-quotes-word", "correct", None, lambda r: True,
     lambda r: _resp(["Step one works through the \u201cproblem\u201d.", "The problem\u2019s result follows from the given numbers."], f"Answer: {r}")),
    ("punct-after-last-word", "correct", None, lambda r: True,
     lambda r: _resp(["Step one works through the problem!", "The result follows from the given numbers;"], f"Answer: {r}")),
    ("blank-lines", "correct", None, lambda r: True, lambda r: _resp(REASONING, f"Answer: {r}", sep="\n\n")),
    ("trailing-newline", "correct", None, lambda r: True, lambda r: _resp(REASONING, f"Answer: {r}", tail="\n")),
    ("crlf", "correct", None, lambda r: True, lambda r: _resp(REASONING, f"Answer: {r}", sep="\r\n", tail="\r\n")),
    ("indent-answer", "correct", None, lambda r: True, lambda r: _resp(REASONING, f"  Answer: {r}")),
    ("tab-answer", "correct", None, lambda r: True, lambda r: _resp(REASONING, f"\tAnswer: {r}")),
    ("no-space-after-colon", "correct", None, lambda r: True, lambda r: _resp(REASONING, f"Answer:{r}")),
    ("trailing-space", "correct", None, lambda r: True, lambda r: _resp(REASONING, f"Answer: {r}   ")),
    ("trailing-zero", "correct", None, lambda r: True, lambda r: _resp(REASONING, f"Answer: {_trailing_zero(r)}")),
    ("thousands-commas", "correct", None, lambda r: abs(Decimal(r)) >= 1000,
     lambda r: _resp(REASONING, f"Answer: {_commas(r)}")),
    ("lines-after-answer", "correct", None, lambda r: True,
     lambda r: _resp(REASONING, f"Answer: {r}", tail="\nHope this helps.\nCheck: 1 + 1 = 2.")),
    ("earlier-wrong-answer-line", "correct", None, lambda r: True,
     lambda r: _resp(REASONING + ["Answer: 999999"], f"Answer: {r}")),
    ("period-after-number", "correct", "D-surrounding-text", lambda r: True, lambda r: _resp(REASONING, f"Answer: {r}.")),
    ("exclaim-after-number", "correct", "D-surrounding-text", lambda r: True, lambda r: _resp(REASONING, f"Answer: {r}!")),
    ("bold-number", "correct", "D-surrounding-text", lambda r: True, lambda r: _resp(REASONING, f"Answer: **{r}**")),
    ("italic-number", "correct", "D-surrounding-text", lambda r: True, lambda r: _resp(REASONING, f"Answer: *{r}*")),
    ("html-number", "correct", "D-surrounding-text", lambda r: True, lambda r: _resp(REASONING, f"Answer: <b>{r}</b>")),
    ("typographic-quotes-number", "correct", "D-surrounding-text", lambda r: True,
     lambda r: _resp(REASONING, f"Answer: \u201c{r}\u201d")),
    ("unit-after-number", "correct", "D-surrounding-text", lambda r: True, lambda r: _resp(REASONING, f"Answer: {r} units")),
    ("nbsp-before-label", "correct", "D-leading-whitespace", lambda r: True, lambda r: _resp(REASONING, f"\u00a0Answer: {r}")),
    # --- edits the contract forbids (a passing response must stop passing) ---
    ("shift-plus-0.02", "not_correct", None, lambda r: True,
     lambda r: _resp(REASONING, f"Answer: {_fmt(Decimal(r) + Decimal('0.02'))}")),
    ("shift-plus-1", "not_correct", None, lambda r: True,
     lambda r: _resp(REASONING, f"Answer: {_fmt(Decimal(r) + 1)}")),
    ("negate", "not_correct", None, lambda r: Decimal(r) != 0,
     lambda r: _resp(REASONING, f"Answer: {_fmt(-Decimal(r))}")),
    ("unicode-minus", "not_correct", None, lambda r: Decimal(r) < 0,
     lambda r: _resp(REASONING, f"Answer: \u2212{r.lstrip('-')}")),
    ("lowercase-label", "not_correct", None, lambda r: True, lambda r: _resp(REASONING, f"answer: {r}")),
    ("bold-label", "not_correct", None, lambda r: True, lambda r: _resp(REASONING, f"**Answer:** {r}")),
    ("bullet-before-label", "not_correct", None, lambda r: True, lambda r: _resp(REASONING, f"- Answer: {r}")),
    ("numbered-before-label", "not_correct", None, lambda r: True, lambda r: _resp(REASONING, f"3. Answer: {r}")),
    ("label-mid-line", "not_correct", None, lambda r: True, lambda r: _resp(REASONING, f"So the Answer: {r}")),
    ("later-wrong-answer-line", "not_correct", None, lambda r: True,
     lambda r: _resp(REASONING, f"Answer: {r}", tail="\nAnswer: 999999")),
    ("answer-line-removed", "not_correct", None, lambda r: True, lambda r: "\n".join(REASONING + [f"The answer is {r}."])),
]


def cases(problems):
    """Yield (edit_name, expect, depends, problem_id, response)."""
    for name, expect, depends, applies, build in EDITS:
        for pid in sorted(problems):
            ref = problems[pid]["answer"]
            if applies(ref):
                yield name, expect, depends, pid, build(ref)
