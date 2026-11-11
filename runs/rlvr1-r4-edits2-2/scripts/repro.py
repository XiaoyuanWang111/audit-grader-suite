"""Reproduce a finding: print each counterexample's exact input and every grader's verdict.

From the case folder, with NLTK_DATA and PYTHONDONTWRITEBYTECODE set as case/TASK.md shows:
  ../.venv/Scripts/python.exe ../audit/scripts/repro.py N1        (one finding)
  ../.venv/Scripts/python.exe ../audit/scripts/repro.py all       (every finding)

Constraint findings print: check, kwargs, response (repr), contract label, then the SkyRL verdict
(final_answer_text + NVIDIA check_following, with any exception) and the curation gate verdict (verifyit check;
"judged" for the four semantic constraints, which have no deterministic check). Pipeline findings print the row reward.
"""
import json
import os
import random
import sys

AUDIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, AUDIT)
import harness  # noqa: E402
import replacement as R  # noqa: E402

PH = "Live each day to the fullest"
C = {
    "N1": [("copy:repeat_phrase", {"phrase": PH, "small_n": 3}, "Live each day to the fullest. Live each day to the fullest. Live each hour to the fullest.", False),
           ("copy:repeat_phrase", {"phrase": PH, "small_n": 2}, "**Live** each moment to the fullest. Live each hour to the fullest.", True)],
    "N2": [("count:count_unique", None, "Hello, world, friend.", True)],
    "N3": [("count:counting_composition", {"n_sent": 3, "n_words": 2}, "Dogs bark. Cats purr. Birds sing.\n* * *\nFish swim. Bees buzz. Cows moo.\n* * *\nKids play. Moms cook. Dads work.", True)],
    "N4": [("detectable_content:postscript", {"postscript_marker": "P.S."}, "Thanks, as the P.S. says, for reading.", False),
           ("detectable_content:postscript", {"postscript_marker": "P.S."}, "Thanks.\n\nP.P.S. See you soon.", False)],
    "N5": [("detectable_format:constrained_response", None, "My answer is yes. My answer is no.", False)],
    "N6": [("detectable_format:multiple_sections", {"num_sections": 2, "section_spliter": "SECTION"}, "SECTION 1\nA text.\nSECTION 2\nB text.\nSECTION 3\nC text.", False)],
    "N7": [("detectable_format:number_bullet_lists", {"num_bullets": 3}, "* one\n* two\n* three\n\n---\n\nDone.", True),
           ("detectable_format:number_bullet_lists", {"num_bullets": 3}, "*Note*: intro\n* one\n* two\n* three", True)],
    "N8": [("detectable_format:number_highlighted_sections", {"num_highlights": 3}, "* **Alpha**: one\n* **Beta**: two", False)],
    "N9": [("detectable_format:sentence_hyphens", None, "Tea is well-known.-Coffee is too.", True)],
    "N10": [("detectable_format:square_brackets", None, "[I], [like] [tea].", True)],
    "N11": [("first_word:first_word_answer", {"first_word": "development"}, "**Development** matters.", True),
            ("first_word:first_word_answer", {"first_word": "development"}, "Development, as a field, matters.", True),
            ("first_word:first_word_sent", {"first_word": "tea"}, "Tea, I think, is warm. Tea is calm.", True),
            ("length_constraints:nth_paragraph_first_word", {"num_paragraphs": 2, "nth_paragraph": 1, "first_word": "fuel"}, "Fuel: costly.\n\nPrices rise.", True),
            ("last_word:last_word_answer", {"last_word": "expression"}, "It remains a mystery in modern history—expression.", True)],
    "N12": [("keywords:keyword_specific_position", {"keyword": "tea", "n": 2, "m": 3}, "I like coffee. Yes, drink tea daily.", True)],
    "N13": [("keywords:no_adjacent_consecutive", None, "Step 1 2 done.", True),
            ("keywords:no_adjacent_consecutive", None, '"A" big dog.', False)],
    "N14": [("keywords:palindrome", None, "This - that.", False),
            ("keywords:palindrome", None, "Level up now.", True)],
    "N15": [("change_case:english_capital", None, "HELLO WORLD", True),
            ("change_case:english_capital", None, "PROFESIÓN DEL SUSTENTADOR PRINCIPAL DE LA FAMILIA; TRABAJA COMO CUIDADORA DE MAYORES A DOMICILIO.", False),
            ("language:response_language", {"language": "ta"}, "12345", False)],
    "N18": [("length_constraints:number_sentences", {"num_sentences": 3, "relation": "at least"}, "我喜欢茶。你喜欢咖啡。他喜欢水。", True)],
    "B1": [("keywords:word_once", {"keyword": "beer"}, "Beer is good and beer is cold.", True)],
    "B2": [("keywords:word_count_different_numbers", {"keyword": "box", "frequency": 2, "relation": "less than"}, "A box and a box.", True),
           ("keywords:word_count_different_numbers", {"keyword": "box", "frequency": 2, "relation": "less than"}, "No containers here.", False)],
    "B3": [("combination:two_responses", None, "Tea is warm.\n*******\nCoffee is strong.", False)],
    "B4": [("detectable_content:number_placeholders", {"num_placeholders": 2}, "Dear [name], see [] and [ ].", False)],
    "B5": [("detectable_format:json_format", None, '{"a": NaN}', False)],
    "B6": [("detectable_format:number_bullet_lists", {"num_bullets": 3}, "* one\n* two\n* three\n\n* * *\n\nEnd.", True)],
    "B7": [("detectable_content:postscript", {"postscript_marker": "P.P.S"}, "The two limits are equal.\n\nP.P.S.", False)],
    "V1": [("change_case:english_capital", None, "ПРИВЕТ МИР, КАК ТВОИ ДЕЛА СЕГОДНЯ?", False),
           ("change_case:english_lowercase", None, "bonjour je suis très content de vous voir aujourd'hui mon ami", False)],
    "V2": [("copy:repeat_phrase", {"phrase": PH, "small_n": 2}, "Live each moment to the fullest. Live each hour to the fullest.", True),
           ("copy:repeat_phrase", {"phrase": PH, "small_n": 2}, "Live each day to the fullest. Live each day to the fullest.", False)],
    "V3": [("count:counting_composition", {"n_sent": 3, "n_words": 2}, "Dogs bark loudly. Cats purr softly. Birds sing sweetly.", False)],
    "V4": [("count:lowercase_counting", {"N": 2}, "the cat and the dog and the bird", False),
           ("count:lowercase_counting", {"N": 2}, "Hello World", True)],
    "V5": [("detectable_content:postscript", {"postscript_marker": "P.S."}, "Thanks.\n\n**P.S.** See you soon.", True)],
    "V6": [("detectable_format:json_format", None, '```JSON\n{"a": 1}\n```', True)],
    "V7": [("detectable_format:multiple_sections", {"num_sections": 2, "section_spliter": "SECTION"}, "SECTION 1\nAs SECTION 2 below shows, tea.\nSECTION 2\nB text.", True)],
    "V8": [("detectable_format:number_highlighted_sections", {"num_highlights": 1}, "Text.\n\n* * *\n\nMore.", False)],
    "V9": [("detectable_format:sentence_hyphens", None, "I like tea.-You like coffee.-We both like water.", True)],
    "V10": [("detectable_format:square_brackets", None, "[I] like tea", False)],
    "V11": [("keywords:no_adjacent_consecutive", None, "A big dog.", False),
            ("keywords:no_adjacent_consecutive", None, "The the cat.", True),
            ("keywords:no_adjacent_consecutive", None, "вот где дом", False)],
    "V12": [("keywords:start_end", None, "Hello there my friend hello.", False)],
    "V13": [("length_constraints:number_paragraphs", {"num_paragraphs": 3}, "One.\n***\nTwo.\n***\nThree.", True),
            ("length_constraints:number_paragraphs", {"num_paragraphs": 3}, "One.\n\nTwo.\n\nThree.", False)],
    "V14": [("paragraphs:paragraphs", None, "One.\n***\nTwo.\n***\nThree.", False),
            ("paragraphs:paragraphs2", None, "One.\n***\nTwo.", False)],
    "V15": [("startend:quotation", None, "'Hello there.'", False)],
    "V16": [("length_constraints:number_words", {"num_words": 5, "relation": "at least"}, "Это очень хороший ответ сегодня.", True),
            ("first_word:first_word_answer", {"first_word": "development"}, "- Development matters.", True)],
    "V17": [("keywords:palindrome", None, "A man, a plan, a canal: Panama.", True)],
    "V18": [("length_constraints:number_sentences", {"num_sentences": 3, "relation": "at least"}, "我喜欢茶。你喜欢咖啡。他喜欢水。", True)],
}
TRUNC = "Okay the user wants an answer without any commas so I should plan the reply first and then"
NO_COMMA = {"instruction_id_list": ["punctuation:no_comma"], "kwargs": [None]}


def show(check, kwargs, response, label):
    harness.setup()
    sky_text = harness.final_answer_text(response)
    nv, err = harness.skyrl_constraint(check, kwargs, sky_text)
    if check in harness.SEMANTIC:
        vi = "judged (no gate check)"
    else:
        vi = harness.verifyit_constraint(check, kwargs, harness.curation_answer_text(response))[0]
    re_ = R.check(check, kwargs, R.graded_text(response, False))
    print(f"  check={check} kwargs={json.dumps(kwargs, ensure_ascii=False)}")
    print(f"  response={response!r}")
    print(f"  contract={'pass' if label else 'fail'} | SkyRL/NVIDIA={'pass' if nv else 'fail'}{' (exception: ' + err + ')' if err else ''}"
          f" | curation/verifyit={vi if isinstance(vi, str) else ('pass' if vi else 'fail')} | replacement={'pass' if re_ else 'fail'}")


def pipeline(fid):
    harness.setup()
    if fid == "P1":
        print("  Qwen3 thinking response cut off inside its reasoning (the chat template opened <think>, so no marker):")
        print(f"  raw={TRUNC!r}  row constraints={NO_COMMA}")
        print(f"  contract: extraction failure, reward 0 | SkyRL reward={harness.skyrl_row(TRUNC, NO_COMMA)['reward']}"
              f" | curation gate={'pass' if harness.verifyit_row(TRUNC, NO_COMMA)['gate_pass'] else 'fail'}")
    elif fid == "P2":
        raw = "<think>I will avoid commas and"
        print(f"  raw={raw!r}  row constraints={NO_COMMA}")
        print(f"  graded text SkyRL={harness.final_answer_text(raw)!r}")
        print(f"  contract: extraction failure, reward 0 | SkyRL reward={harness.skyrl_row(raw, NO_COMMA)['reward']}"
              f" | curation gate={'pass' if harness.verifyit_row(raw, NO_COMMA)['gate_pass'] else 'fail'}")
    elif fid in ("N16", "P3"):
        rec = {"instruction_id_list": ["last_word:last_word_answer"], "kwargs": [{"last_word": "end"}]}
        r = harness.skyrl_row("", rec)
        print(f"  raw='' row constraints={rec}")
        print(f"  SkyRL reward={r['reward']} errors={r['errors']} -> NemotronTaskSession returns Outcome.INFRA_ERROR")
    elif fid == "N17":
        rec = {"instruction_id_list": ["length_constraints:nth_paragraph_first_word"],
               "kwargs": [{"first_word": "fuel", "nth_paragraph": 3, "num_paragraphs": 2}]}
        raw = "Fuel is costly.\n\nFuel prices rise."
        rewards = []
        for seed in range(20):
            random.seed(seed)
            rewards.append(harness.skyrl_row(raw, rec)["reward"])
        print(f"  raw={raw!r} row constraints={rec}")
        print(f"  contract: fail (paragraph 3 of 2 cannot exist) | SkyRL rewards over random seeds 0-19: {rewards}")


def main():
    which = sys.argv[1]
    ids = list(C) + ["N16", "N17", "P1", "P2"] if which == "all" else [which]
    for fid in ids:
        print(f"== {fid}")
        if fid in C:
            for ex in C[fid]:
                show(*ex)
        else:
            pipeline(fid)


if __name__ == "__main__":
    main()
