"""Reproduce each finding's counterexample.

usage (from audit/):  ../.venv/Scripts/python.exe repro.py F1      (or: repro.py all)

Each line prints: finding, grader, instruction id, the grader's verdict, and the contract label.
"skyrl" = SkyRL reward (final_answer_text + grade_instruction_following, NVIDIA's checkers);
"gate" = task-curation gate (grade_judge._answer_text + verifyit's ifeval check), "judged" when
the constraint goes to the LLM judge instead.
"""
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "lib"))
import harness as h  # noqa: E402

LT, AT = "less than", "at least"
# id -> list of (graders to show, instruction id, kwargs, response, contract label, thinking)
CASES = {
    "F1": [("skyrl", "keywords:existence", {"keywords": ["art", "home"]}, "We start at home.", "fail")],
    "F2": [("skyrl,gate", "keywords:word_once", {"keyword": "river"}, "The river flows into another river.", "pass")],
    "F3": [("skyrl,gate", "keywords:word_count_different_numbers", {"keyword": "tree", "relation": LT, "frequency": 2}, "A tree and a tree.", "pass"),
           ("skyrl,gate", "keywords:word_count_different_numbers", {"keyword": "tree", "relation": LT, "frequency": 2}, "Nothing here.", "fail")],
    "F4": [("skyrl", "copy:repeat_phrase", {"phrase": "Laughter is the best medicine", "small_n": 2}, "Laughter is the best medicine. Laughter is our best medicine.", "fail")],
    "F5": [("skyrl", "copy:repeat_phrase", {"phrase": "Don't judge a book by cover", "small_n": 2}, "Don’t judge the book by cover. Don’t judge one book by cover.", "pass")],
    "F6": [("gate", "copy:repeat_phrase", {"phrase": "Laughter is the best medicine", "small_n": 2}, "Laughter is our best medicine. Laughter is my best medicine.", "pass"),
           ("gate", "copy:repeat_phrase", {"phrase": "Laughter is the best medicine", "small_n": 2}, "Laughter is the best medicine. Laughter is the best medicine.", "fail")],
    "F7": [("skyrl", "count:count_unique", {}, "Apples, pears, plums.", "pass")],
    "F8": [("skyrl", "count:counting_composition", {"n_sent": 3, "n_words": 2}, "Birds sing. Cats sleep. Dogs bark.\n* * *\nFish swim. Bees buzz. Cows moo.\n* * *\nKids play. Moms cook. Dads read.", "pass")],
    "F9": [("gate", "count:counting_composition", {"n_sent": 3, "n_words": 2}, "Birds sing. Cats sleep. Dogs bark. Fish swim. Bees buzz. Cows moo. Kids play. Moms cook. Dads read.", "fail")],
    "F10": [("gate", "count:lowercase_counting", {"N": 2}, "the the the end", "fail"),
            ("gate", "count:lowercase_counting", {"N": 2}, "I AM OK.", "pass")],
    "F11": [("gate", "keywords:no_adjacent_consecutive", {}, "A big dog.", "fail"),
            ("gate", "keywords:no_adjacent_consecutive", {}, "The the end.", "pass")],
    "F12": [("gate", "change_case:english_capital", {}, "LE TEMPS EST TRÈS BEAU AUJOURD'HUI ET NOUS ALLONS AU PARC AVEC NOS AMIS.", "fail")],
    "F13": [("gate", "detectable_format:square_brackets", {}, "[The] sun is bright.", "fail")],
    "F14": [("gate", "detectable_format:sentence_hyphens", {}, "Well-known. Fine-tuned.", "fail")],
    "F15": [("skyrl", "detectable_format:sentence_hyphens", {}, "The well-known poet arrived.-We listened.", "pass")],
    "F16": [("gate", "length_constraints:number_paragraphs", {"num_paragraphs": 2}, "First paragraph.\n***\nSecond paragraph.", "pass")],
    "F17": [("gate", "paragraphs:paragraphs2", {}, "First part.\n\nSecond part.\n\nThird part.", "fail"),
            ("gate", "paragraphs:paragraphs", {}, "First part.\n\nSecond part.", "fail")],
    "F18": [("skyrl", "length_constraints:number_paragraphs", {"num_paragraphs": 2}, "***Note*** first part.\n***\nSecond part.", "pass")],
    "F19": [("skyrl", "detectable_format:multiple_sections", {"num_sections": 2, "section_spliter": "SECTION"}, "SECTION 1\nA text.\nSECTION 2\nB text.\nSECTION 3\nC text.", "fail")],
    "F20": [("skyrl,gate", "detectable_format:multiple_sections", {"num_sections": 2, "section_spliter": "SECTION"}, "SECTION 1\nSee SECTION 2 below for details.", "fail")],
    "F21": [("skyrl", "detectable_format:number_bullet_lists", {"num_bullets": 2}, "* Apples\n* Pears\n---\nThat is all.", "pass")],
    "F22": [("skyrl,gate", "detectable_format:number_bullet_lists", {"num_bullets": 2}, "* Apples\n* Pears\n* * *\nDone.", "pass")],
    "F23": [("skyrl,gate", "detectable_format:number_highlighted_sections", {"num_highlights": 2}, "Compute 2 * 3 * 4 and *done*.", "fail")],
    "F24": [("skyrl", "detectable_format:constrained_response", {}, "My answer is yes. My answer is no.", "fail")],
    "F25": [("skyrl,gate", "detectable_format:json_format", {}, "NaN", "fail")],
    "F26": [("gate", "detectable_format:json_format", {}, '```JSON\n{"a": 1}\n```', "pass")],
    "F27": [("skyrl", "detectable_content:number_placeholders", {"num_placeholders": 2}, "Dear [], meet me at [].", "fail"),
            ("skyrl,gate", "detectable_content:number_placeholders", {"num_placeholders": 2}, "Dear [ ], meet me at [ ].", "fail")],
    "F28": [("skyrl", "detectable_content:postscript", {"postscript_marker": "P.S."}, "Remember to read the P.S. section of the letter.\n\nThanks.", "fail"),
            ("skyrl", "detectable_content:postscript", {"postscript_marker": "P.S."}, "Here is my answer.\n\nP.P.S. One more note.", "fail")],
    "F29": [("gate", "detectable_content:postscript", {"postscript_marker": "P.S."}, "Here is my answer.\n\n**P.S.** Thanks for asking.", "pass")],
    "F30": [("gate", "detectable_format:title", {}, "<< >>\nThe rain falls softly.", "fail")],
    "F31": [("skyrl", "startend:end_checker", {"end_phrase": "Any other questions?"}, "Here is the plan. Many other questions?", "fail"),
            ("gate", "startend:end_checker", {"end_phrase": "Is there anything else I can help with?"}, "SectionIs there anything else I can help with?", "fail")],
    "F32": [("gate", "startend:quotation", {}, "'Hello there.'", "fail")],
    "F33": [("skyrl,gate", "combination:two_responses", {}, "A cat.\n*******\nA dog.", "fail")],
    "F34": [("skyrl", "first_word:first_word_answer", {"first_word": "development"}, "Development, in short, matters.", "pass"),
            ("skyrl", "length_constraints:nth_paragraph_first_word", {"num_paragraphs": 2, "nth_paragraph": 2, "first_word": "rain"}, "Clouds gathered.\n\n**Rain** fell all night.", "pass")],
    "F35": [("skyrl", "keywords:start_end", {}, "! !", "fail")],
    "F36": [("skyrl", "keywords:palindrome", {}, "* Apples\n* Pears", "fail"),
            ("skyrl", "keywords:palindrome", {}, "Paddle the kayak.", "pass")],
    "F37": [("skyrl", "keywords:no_adjacent_consecutive", {}, '"apple" "banana" were eaten.', "fail")],
    "F38": [("skyrl", "keywords:keyword_specific_position", {"keyword": "river", "n": 2, "m": 3}, "We walked far. Then, the river appeared.", "pass")],
    "F39": [("skyrl", "detectable_format:square_brackets", {}, "[The] [sun] [is] [bright].", "pass")],
    "F40": [("skyrl", "detectable_format:bigram_wrapping", {}, "<<I am>> <<at home>> today", "fail")],
    "F41": [("skyrl", "language:response_language", {"language": "fr"}, "12345", "fail")],
    "F42": [("gate", "length_constraints:number_words", {"relation": AT, "num_words": 3}, "Мы пошли домой сегодня.", "pass"),
            ("gate", "first_word:first_word_answer", {"first_word": "rain"}, "- Rain falls softly today.\n- Clouds gather.", "pass")],
    "F43": [("gate", "length_constraints:number_sentences", {"relation": AT, "num_sentences": 2}, "We met Dr. Smith today.", "fail")],
    "F44": [("gate", "keywords:start_end", {}, "Hello there my friend hello.", "fail")],
    "F45": [("skyrl", "last_word:last_word_answer", {"last_word": "language"}, "We speak one language —", "pass")],
    "F46": [("skyrl", "count:lowercase_counting", {"N": 2}, "мы мы мы идём", "fail")],
    "F47": [("skyrl", "change_case:english_capital", {}, "SCHOOL OF REALISM", "pass"),
            ("skyrl", "language:response_language", {"language": "fr"}, "Le temps est très beau aujourd'hui et nous allons au parc.\nWe play with our friends all day long in the park.", "fail")],
    "F48": [("skyrl,gate", "length_constraints:number_sentences", {"relation": AT, "num_sentences": 3}, "今天下雨了。我们待在家里。我们看书。", "pass")],
    "G1": [("skyrl,gate", "keywords:word_once", {"keyword": "river"}, "The user wants the word river once, so I will plan a short answer about a", "fail", True)],
}


def verdict(grader, iid, kw, response):
    if grader == "skyrl":
        random.seed(0)
        passed, error = h.skyrl_check(iid, kw, h.skyrl_text(response))
        return ("pass" if passed else "fail") + (f" (exception {error})" if error else "")
    g = h.gate_check(iid, kw, h.gate_text(response))
    return "judged" if g is None else ("pass" if g else "fail")


def run(fid):
    if fid in CASES:
        for case in CASES[fid]:
            graders, iid, kw, response, label = case[:5]
            thinking = len(case) > 5 and case[5]
            for g in graders.split(","):
                note = "  [raw thinking-mode response, no </think>: contract = extraction failure]" if thinking else ""
                print(f"{fid} {g:<5} {iid:<45} grader={verdict(g, iid, kw, response):<5} contract={label}{note}")
    elif fid == "G2":
        record = {"instruction_id_list": ["last_word:last_word_answer"], "kwargs": [{"last_word": "limit"}]}
        row = h.skyrl_row(record, "")
        print(f"G2 skyrl last_word:last_word_answer on an empty answer: errors={row['errors']} infra_error={row['infra_error']} reward={row['reward']}")
    elif fid == "G3":
        kw = {"num_paragraphs": 2, "nth_paragraph": 3, "first_word": "rain"}
        seen = Counter()
        for seed in range(40):
            random.seed(seed)
            seen[h.skyrl_check("length_constraints:nth_paragraph_first_word", kw, "Rain fell.\n\nRain stopped.")[0]] += 1
        print(f"G3 skyrl nth_paragraph_first_word {kw} 'Rain fell.\\n\\nRain stopped.' over 40 seeds: pass={seen[True]} fail={seen[False]} contract=fail")
    elif fid == "G4":
        src = (h.CASE / "reference/skyrl_gym/envs/nemotron_ultra/instruction_following.py").read_text(encoding="utf-8")
        line = next(i + 1 for i, l in enumerate(src.splitlines()) if "nltk.download(" in l)
        print(f"G4 instruction_following.py line {line}: {src.splitlines()[line - 1].strip()}")
    elif fid == "G5":
        routes = Counter()
        with open(h.CASE / "data/rlvr1_instruction_following.jsonl", encoding="utf-8") as f:
            for l in f:
                routes[json.loads(l)["extra_info"]["nemotron_ultra"]["route"]] += 1
        src = (h.CASE / "reference/skyrl_gym/nemotron_tasks.py").read_text(encoding="utf-8").splitlines()
        line = next(i + 1 for i, l in enumerate(src) if 'ultra["route"] != "task_session"' in l)
        print(f"G5 data routes={dict(routes)}; nemotron_tasks.py line {line}: {src[line - 1].strip()} -> {src[line].strip()}")
    else:
        raise SystemExit(f"unknown finding {fid}")


if __name__ == "__main__":
    ids = list(CASES) + ["G2", "G3", "G4", "G5"] if sys.argv[1] == "all" else sys.argv[1:]
    ids = sorted(ids, key=lambda x: (x[0], int(re.sub(r"\D", "", x))))
    for fid in ids:
        run(fid)
