"""Reproduce each finding's counterexample: print the graders' verdicts next to the contract's.

Usage (from <W>):
    NLTK_DATA=$PWD/case/deps/nltk_data PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python.exe audit/repro.py F1 [F2 ...]
    ... audit/repro.py all

Grader A: final_answer_text, then NVIDIA's checker built by Marin's build_instruction (the SkyRL reward).
Grader B: grade_judge._answer_text, then verifyit's check (the task-curation gate).
Contract: audit/lib/contract_grader.py with the proposed readings (audit/CONTRACTS.md).
"""
import random
import sys
from pathlib import Path

W = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(W / "audit" / "lib"))
import contract_grader as cg  # noqa: E402
import graders_under_audit as gu  # noqa: E402

# finding -> list of (check, kwargs, response, ctx)
CASES = {
    "F1": [("keywords:existence", {"keywords": ["art", "she"]}, "She started to finish the task.", {})],
    "F2": [("keywords:word_once", {"keyword": "beer"}, "Beer is good and beer is cheap.", {})],
    "F3": [("keywords:word_count_different_numbers", {"keyword": "refuse", "frequency": 1, "relation": "less than"}, "I refuse.", {})],
    "F4": [("copy:repeat_phrase", {"phrase": "All that glitters is not gold", "small_n": 3},
            "All that glitters is not gold\nAll that glitters is not gold\nAll that shines is not gold", {})],
    "F5": [("copy:repeat_phrase", {"phrase": "All that glitters is not gold", "small_n": 2},
            "All that glitters is not gold\nAll that glitters is not gold", {}),
           ("copy:repeat_phrase", {"phrase": "All that glitters is not gold", "small_n": 2},
            "All that shines is not gold\nAll that sparkles is not gold", {})],
    "F6": [("detectable_content:postscript", {"postscript_marker": "P.S."}, "I added a P.S. note at the end, see below.\n\nThat is all.", {})],
    "F7": [("detectable_format:constrained_response", None, "My answer is yes. My answer is no.", {})],
    "F8": [("detectable_format:multiple_sections", {"num_sections": 2, "section_spliter": "SECTION"},
            "SECTION 1\nThis part mentions SECTION 2 inline only.", {})],
    "F9": [("detectable_format:number_bullet_lists", {"num_bullets": 2}, "* Apples\n* Pears\n\n* * *\n\nDone.", {})],
    "F10": [("detectable_format:number_highlighted_sections", {"num_highlights": 2}, "Compute 5 * 3 * 2 and *done*.", {})],
    "F11": [("first_word:first_word_answer", {"first_word": "development"}, "development, as a concept, matters.", {})],
    "F12": [("keywords:keyword_specific_position", {"keyword": "village", "n": 2, "m": 3}, "We walked far. Indeed, the village slept.", {})],
    "F13": [("count:count_unique", None, "Apples, pears, plums.", {})],
    "F14": [("keywords:start_end", None, "- Hello world -", {}), ("keywords:start_end", None, "Hello world, I say hello.", {})],
    "F15": [("keywords:no_adjacent_consecutive", None, "Steps 1 2 now", {})],
    "F16": [("keywords:no_adjacent_consecutive", None, "A big dog", {}), ("keywords:no_adjacent_consecutive", None, "very very good", {})],
    "F17": [("keywords:palindrome", None, "Top results\n---\nNotes here", {})],
    "F18": [("language:response_language", {"language": "es"}, "12345 67890", {})],
    "F19": [("last_word:last_word_answer", {"last_word": "payment"}, "", {})],
    "F20": [("length_constraints:number_paragraphs", {"num_paragraphs": 2},
             "First paragraph has ***bold italic*** text.\n***\nSecond paragraph.", {})],
    "F21": [("length_constraints:number_paragraphs", {"num_paragraphs": 2}, "First paragraph.\n***\nSecond paragraph.", {}),
            ("length_constraints:number_paragraphs", {"num_paragraphs": 2}, "First paragraph.\n\nSecond paragraph.", {})],
    "F22": [("paragraphs:paragraphs", {}, "First.\n***\nSecond.\n***\nThird.", {}), ("paragraphs:paragraphs2", {}, "A.\n\nB.\n\nC.", {})],
    "F23": [("length_constraints:number_words", {"num_words": 3, "relation": "less than"}, "Don't stop.", {}),
            ("change_case:capital_word_frequency", {"capital_frequency": 2, "capital_relation": "less than"}, "I'm sure NASA is fine.", {})],
    "F24": [("length_constraints:number_words", {"num_words": 5, "relation": "at least"}, "Это очень хороший и полезный ответ.", {}),
            ("last_word:last_word_answer", {"last_word": "ask"}, "Feel free to ask 朋友", {})],
    "F25": [("letters:letter_counting", {"N": 3, "relation": "at least"}, "Да, конечно, это так.", {})],
    "F26": [("detectable_content:number_placeholders", {"num_placeholders": 2}, "Dear [], see you at [ ].", {})],
    "F27": [("detectable_format:bigram_wrapping", None, "<<I am>> <<at home>> today", {})],
    "F28": [("count:counting_composition", {"n_sent": 3, "n_words": 2},
             "Birds sing. Cats sleep. Dogs run.\n* * *\nRain falls. Wind blows. Trees sway.\n* * *\nKids play. Moms smile. Dads cook.", {}),
            ("count:counting_composition", {"n_sent": 3, "n_words": 2}, "Birds sing. Cats sleep. Dogs run.", {})],
    "F30": [("combination:two_responses", None, "One.\n*******\nTwo.", {})],
    "F31": [("count:lowercase_counting", {"N": 2}, "the the the end", {}), ("count:lowercase_counting", {"N": 2}, "ALL CAPS ONLY.", {})],
    "F32": [("detectable_format:square_brackets", None, "Hello [world] how are you", {})],
    "F33": [("detectable_format:sentence_hyphens", None, "I like tea.-You like coffee.-We both like cake.", {}),
            ("detectable_format:sentence_hyphens", None, "I-like-tea. You-like-coffee.", {})],
    "F34": [("startend:quotation", None, "'Hello there.'", {})],
    "F35": [("detectable_format:title", None, "<< >>\nRoses are red.", {})],
    "F36": [("length_constraints:number_sentences", {"num_sentences": 2, "relation": "less than"}, "Dr. Smith arrived.", {}),
            ("length_constraints:number_sentences", {"num_sentences": 2, "relation": "at least"}, 'He said "Stop." Then he left.', {})],
    "F37": [("count:lowercase_counting", {"N": 2}, "Он сказал да да да да.", {})],
    "F38": [("detectable_format:square_brackets", None, "[Hello]and[world]", {})],
    "F39": [("last_word:last_word_sent", {"last_word": "limit"}, "We use Node.js to set the limit.", {}),
            ("length_constraints:number_sentences", {"num_sentences": 3, "relation": "at least"}, "第一句。第二句。第三句。", {})],
    "F40": [("detectable_content:postscript", {"postscript_marker": "P.S."}, "Answer.\n\n**P.S.** Thanks.", {})],
}


def show(v):
    if v is None:
        return "not checked (judge)"
    if isinstance(v, str):
        return "EXCEPTION " + v[7:]
    return "pass" if v else "fail"


def run_check_case(fid, check, kw, text, ctx):
    a = gu.check_a(check, kw, gu.extract_a(text))
    b = gu.check_b(check, kw, gu.extract_b(text))
    r = cg.check(check, kw, text, None, ctx)
    print(f"{fid}  {check}  kwargs={kw}\n    response={text!r}\n    grader A: {show(a)}   grader B: {show(b)}   contract: {show(r)}")


def f29():
    rec = {"instruction_id_list": ["length_constraints:nth_paragraph_first_word"],
           "kwargs": [{"num_paragraphs": 2, "nth_paragraph": 3, "first_word": "fight"}]}
    text = "Fight one.\n\nFight two."
    verdicts = []
    for seed in range(6):
        random.seed(seed)
        verdicts.append(gu.reward_a(text, rec)[0])
    print(f"F29  length_constraints:nth_paragraph_first_word  kwargs={rec['kwargs'][0]}\n    response={text!r}\n"
          f"    grader A reward under random.seed(0..5): {verdicts}   grader B gate: {'pass' if gu.gate_b(text, rec)[0] else 'fail'}"
          f"   contract: fail (paragraph 3 of 2 cannot exist)")


def p1():
    no_comma = {"instruction_id_list": ["punctuation:no_comma"], "kwargs": [None]}
    raw = "Okay so the user wants an answer without commas so I will plan it step by step and then write"
    print(f"P1  thinking-model response cut inside its reasoning (no </think>), row punctuation:no_comma\n    raw={raw!r}\n"
          f"    grader A reward: {gu.reward_a(raw, no_comma)[0]}   grader B gate: {'pass' if gu.gate_b(raw, no_comma)[0] else 'fail'}"
          f"   contract: extraction failure, reward {cg.grade_row(no_comma, raw, '', True)[0]}")
    tag = {"instruction_id_list": ["keywords:existence"], "kwargs": [{"keywords": ["tag"]}]}
    raw = "Wrap the plan in a <think> tag before you answer."
    print(f"P1  non-reasoning answer that mentions <think>, row keywords:existence ['tag']\n    raw={raw!r}\n"
          f"    graded text A: {gu.extract_a(raw)!r}  B: {gu.extract_b(raw)!r}   grader A reward: {gu.reward_a(raw, tag)[0]}"
          f"   grader B gate: {'pass' if gu.gate_b(raw, tag)[0] else 'fail'}   contract reward: {cg.grade_row(tag, raw, '', False)[0]}")


def p2():
    import nltk

    from skyrl_gym.envs.nemotron_ultra import instruction_following as m

    calls = []
    real_find, real_download = nltk.data.find, nltk.download

    def missing(*a, **k):
        raise LookupError("missing")

    nltk.data.find, nltk.download = missing, (lambda *a, **k: calls.append(a) or True)
    ready, m._NLTK_READY = m._NLTK_READY, False
    try:
        m._ensure_nltk_data()
    finally:
        nltk.data.find, nltk.download, m._NLTK_READY = real_find, real_download, ready
    print(f"P2  grader A with punkt_tab missing (nltk.data.find and nltk.download stubbed, no network)\n"
          f"    nltk.download calls: {calls}")


def p5():
    text = "[" * 5000
    b = gu.check_b("detectable_format:json_format", None, text)
    a = gu.check_a("detectable_format:json_format", None, text)
    print(f"P5  detectable_format:json_format  response='[' * 5000\n    grader A: {show(a)}   grader B check: {show(b)}"
          f" (the gate's _passes counts it as a failed constraint)")


SPECIAL = {"F29": f29, "P1": p1, "P2": p2, "P5": p5}


def main(ids):
    if ids == ["all"]:
        ids = list(CASES) + list(SPECIAL)
    for fid in ids:
        if fid in SPECIAL:
            SPECIAL[fid]()
        else:
            for case in CASES[fid]:
                run_check_case(fid, *case)


if __name__ == "__main__":
    main(sys.argv[1:] or ["all"])
