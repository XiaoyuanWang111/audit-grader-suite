"""Property and metamorphic tests for the ToyQA judge pipeline (step 4 of the audit).

Each property draws a fixed number of random cases from a seeded generator, so a run is reproducible. Oracle
properties compare an implementation with the contract oracle (the replacement) and run on the grader and the
reference only; metamorphic properties need no oracle and run on all three implementations. A failing property names
its shortest counterexample.

Run from the audit run's root:  python -I -m unittest discover -s audit/tests -v
"""

import random
import unittest

from toyqa_audit_lib import (GRADER, IMPLS, QUESTIONS, REFERENCE, ScriptedJudge, contract_parse, contract_prompt,
                             judges, xfail_strict)

N_CASES = 400
SEED = 20261106

LINE_BREAKS = ["\n", "\r\n", "\r", " ", "\x0b", "\x0c", "\x85"]
TEXT_CHARS = list("abcdefghijklmnopqrstuvwxyz ABCXYZ0123456789.,:;!?-'\"(){}*_") + ["é", "ü", "中", "\U0001F600"]
REPLY_TOKENS = ["A", "B", "C", "CORRECT", "INCORRECT", "NOT_ATTEMPTED", "Answer:", "Grade:", "The", "grade", "is",
                "**", "(", ")", ".", ":", " ", " ", "\n", "é", "1", "x", "Based", "on", "rubric", "A1", "_", "a", "b"]
NO_STANDALONE_PREFIXES = ["CORRECT ", "INCORRECT ", "NOT_ATTEMPTED ", "Based on that, ", "Answer: ", "ABC "]


def rand_text(rng, lo, hi, breaks=0.0):
    out = []
    for _ in range(rng.randint(lo, hi)):
        out.append(rng.choice(LINE_BREAKS) if rng.random() < breaks else rng.choice(TEXT_CHARS))
    return "".join(out).replace("<think>", "").replace("</think>", "")


def rand_graded_text(rng, breaks=0.03):
    """A non-empty stripped text, as extraction hands it to the renderer."""
    while True:
        text = rand_text(rng, 1, 420, breaks).strip()
        if text:
            return text


def rand_reply(rng):
    return "".join(rng.choice(REPLY_TOKENS) for _ in range(rng.randint(0, 8)))


def shortest(counterexamples):
    return min(counterexamples, key=lambda c: len(repr(c))) if counterexamples else None


class Properties(unittest.TestCase):
    pass


def prop_extract_ignores_closed_reasoning(impl, rng):
    """E1: a closed reasoning block before the answer does not change the graded text."""
    bad = []
    for _ in range(N_CASES):
        answer, reasoning = rand_text(rng, 0, 80, 0.05), rand_text(rng, 0, 80, 0.05)
        if impl.extract("<think>" + reasoning + "</think>" + answer) != impl.extract(answer):
            bad.append((reasoning, answer))
    return bad


def prop_extract_ignores_outer_whitespace(impl, rng):
    """E3: leading and trailing whitespace does not change the graded text."""
    bad = []
    for _ in range(N_CASES):
        answer = rand_text(rng, 0, 80, 0.05)
        padded = rng.choice(["", " ", "\n", "\t "]) + answer + rng.choice(["", " ", "\n\n", " \t"])
        if impl.extract(padded) != impl.extract(answer):
            bad.append(padded)
    return bad


def prop_unclosed_reasoning_is_extraction_failure(impl, rng):
    """E2, L1 (forbidden edit): dropping the closing marker turns the row into an extraction failure, never
    not_attempted, and the judge is not called."""
    bad = []
    for _ in range(N_CASES):
        reasoning, answer = rand_text(rng, 0, 80), rand_text(rng, 1, 40)
        q = QUESTIONS[rng.choice(sorted(QUESTIONS))]
        label, calls = impl.label(ScriptedJudge([]), q, "<think>" + reasoning + answer)
        if (label, calls) != ("extraction_failure", 0):
            bad.append(("<think>" + reasoning + answer, label))
    return bad


def prop_prompt_matches_contract(impl, rng):
    """R1-R4 (oracle): the prompt is the template filled with the first 300 characters of the whole graded text."""
    bad = []
    for _ in range(N_CASES):
        q = QUESTIONS[rng.choice(sorted(QUESTIONS))]
        text = rand_graded_text(rng)
        if impl.render(q, text) != contract_prompt(q, text):
            bad.append(text)
    return bad


def prop_prompt_depends_only_on_first_300(impl, rng):
    """R1: text after character 300 never reaches the judge."""
    bad = []
    for _ in range(N_CASES):
        q = QUESTIONS[rng.choice(sorted(QUESTIONS))]
        base = (rand_graded_text(rng) + "x" * 300)[:300]
        if impl.render(q, base) != impl.render(q, base + rand_text(rng, 1, 50, 0.1)):
            bad.append(base)
    return bad


def prop_prompt_sees_every_edit_in_first_300(impl, rng):
    """R1 (forbidden edit): changing one character among the first 300 changes the prompt."""
    bad = []
    for _ in range(N_CASES):
        q = QUESTIONS[rng.choice(sorted(QUESTIONS))]
        text = rand_graded_text(rng, breaks=0.05)
        i = rng.randrange(min(len(text), 300))
        if text[i] in "\r\n \x0b\x0c\x85":
            continue
        edited = text[:i] + ("Q" if text[i] != "Q" else "R") + text[i + 1:]
        if edited.strip() != edited:
            continue
        if impl.render(q, text) == impl.render(q, edited):
            bad.append((text, i))
    return bad


def prop_values_inserted_as_text(impl, rng):
    """R4: braces and placeholder names in a one-line graded text reach the prompt unchanged."""
    bad = []
    for _ in range(N_CASES):
        q = QUESTIONS[rng.choice(sorted(QUESTIONS))]
        text = rng.choice(["{target}", "{question}", "{}", "{0}", "{{", "}}"]) + rand_text(rng, 1, 40)
        text = text.strip()
        if ("<<<\n" + text[:300] + "\n>>>") not in impl.render(q, text):
            bad.append(text)
    return bad


def prop_parse_matches_contract(impl, rng):
    """P1-P2 (oracle)."""
    bad = []
    for _ in range(N_CASES):
        reply = rand_reply(rng)
        if impl.parse(reply) != contract_parse(reply):
            bad.append(reply)
    return bad


def prop_parse_takes_appended_letter(impl, rng):
    """P1 (metamorphic): a letter appended on its own line becomes the grade."""
    bad = []
    for _ in range(N_CASES):
        reply, letter = rand_reply(rng), rng.choice("ABC")
        if impl.parse(reply + "\n" + letter) != letter:
            bad.append((reply, letter))
    return bad


def prop_parse_ignores_prefix_without_standalone_letter(impl, rng):
    """P1 (metamorphic): a prefix with no standalone A, B or C does not change the grade."""
    bad = []
    for _ in range(N_CASES):
        reply = rand_reply(rng)
        prefix = rng.choice(NO_STANDALONE_PREFIXES)
        if impl.parse(prefix + reply) != impl.parse(" " + reply):
            bad.append((prefix, reply))
    return bad


def prop_parse_ignores_markup_around_letter(impl, rng):
    """P1 (metamorphic): markdown or punctuation around a lone letter keeps it."""
    bad = []
    for _ in range(N_CASES):
        letter = rng.choice("ABC")
        wrapped = rng.choice(["**{}**", "({})", "{}.", "Grade: {}", "{}\n", " {} "]).format(letter)
        if impl.parse(wrapped) != letter:
            bad.append(wrapped)
    return bad


def prop_scores_ignore_row_order(impl, rng):
    """G1-G5: the scores depend only on the multiset of labels."""
    bad = []
    labels_pool = ["correct", "incorrect", "not_attempted", "extraction_failure", "judge_error"]
    for _ in range(N_CASES // 4):
        labels = [rng.choice(labels_pool) for _ in range(12)]
        shuffled = labels[:]
        rng.shuffle(shuffled)
        if impl.scores(labels) != impl.scores(shuffled):
            bad.append(labels)
    return bad


def prop_not_attempted_rate_counts_only_grade_c(impl, rng):
    """G4 end to end: unclosed reasoning rows never raise the not-attempted rate (fake judge)."""
    bad = []
    qids = sorted(QUESTIONS)
    for _ in range(N_CASES // 8):
        labels, n_c = [], 0
        for qid in qids:
            q = QUESTIONS[qid]
            kind = rng.choice(["gold", "refusal", "unclosed"])
            response = {"gold": q["gold"], "refusal": "I don't know.", "unclosed": "<think>" + q["gold"]}[kind]
            n_c += kind == "refusal"
            labels.append(impl.label(judges.FakeJudge(), q, response)[0])
        if impl.scores(labels)["not_attempted_rate"] != round(100 * n_c / 12, 1):
            bad.append(labels)
    return bad


# (property, run on, xfail by implementation)
PROPERTIES = [
    (prop_extract_ignores_closed_reasoning, "all", {}),
    (prop_extract_ignores_outer_whitespace, "all", {}),
    (prop_unclosed_reasoning_is_extraction_failure, "all", {"grader": "F1"}),
    (prop_prompt_matches_contract, "oracle", {"grader": "F2"}),
    (prop_prompt_depends_only_on_first_300, "all", {}),
    (prop_prompt_sees_every_edit_in_first_300, "all", {"grader": "F2"}),
    (prop_values_inserted_as_text, "all", {}),
    (prop_parse_matches_contract, "oracle", {"grader": "F4"}),
    (prop_parse_takes_appended_letter, "all", {"grader": "F4"}),
    (prop_parse_ignores_prefix_without_standalone_letter, "all", {"grader": "F4"}),
    (prop_parse_ignores_markup_around_letter, "all", {}),
    (prop_scores_ignore_row_order, "all", {}),
    (prop_not_attempted_rate_counts_only_grade_c, "all", {"grader": "F1"}),
]


def _attach():
    for prop, scope, xfail in PROPERTIES:
        impls = IMPLS if scope == "all" else (GRADER, REFERENCE)
        for impl in impls:
            def test(self, prop=prop, impl=impl):
                bad = prop(impl, random.Random(f"{SEED}:{prop.__name__}"))
                self.assertEqual(len(bad), 0, f"{len(bad)} counterexamples; shortest: {shortest(bad)!r}")
            test.__doc__ = f"{prop.__name__} on {impl.name}: {prop.__doc__.splitlines()[0]}"
            if impl.name in xfail:
                test = xfail_strict(f"{xfail[impl.name]}: {prop.__name__}")(test)
            setattr(Properties, f"test_{impl.name}_{prop.__name__}", test)


_attach()

if __name__ == "__main__":
    unittest.main()
