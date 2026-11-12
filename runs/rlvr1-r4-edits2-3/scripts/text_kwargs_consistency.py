"""Data-only checks: does the requirement text in the prompt state the same values as kwargs?

Prints counting_composition's text, the keyword_specific_position and
nth_paragraph_first_word rows whose text order differs, and, for each id with
kwargs, how many rows' prompts contain the rendered sentence built from kwargs.
"""
import json
import collections
import re

PATH = "<W>/case/data/rlvr1_instruction_following.jsonl"
rows = []
with open(PATH, encoding="utf-8") as f:
    for line in f:
        rows.append(json.loads(line))

RENDER = {
    "keywords:keyword_specific_position": lambda kw: f"Include keyword {kw['keyword']} in the {kw['n']}-th sentence, as the {kw['m']}-th word of that sentence",
    "length_constraints:nth_paragraph_first_word": lambda kw: f"There should be {kw['num_paragraphs']} paragraphs. Paragraphs and only paragraphs are separated with each other by two new lines as if it was '\\n\\n' in python. Paragraph {kw['nth_paragraph']} must start with word {kw['first_word']}",
    "first_word:first_word_answer": lambda kw: f"The first word of your response should be the word {kw['first_word']}",
    "first_word:first_word_sent": lambda kw: f"The first word of each sentence should be the word {kw['first_word']}",
    "last_word:last_word_answer": lambda kw: f"The last word of your response should be the word {kw['last_word']}",
    "last_word:last_word_sent": lambda kw: f"The last word of each sentence, before punctuation, should be the word {kw['last_word']}",
    "keywords:frequency": lambda kw: f"In your response, the word {kw['keyword']} should appear {kw['relation']} {kw['frequency']} times",
    "keywords:word_count_different_numbers": lambda kw: f"In your response, the word {kw['keyword']} should appear {kw['frequency']} times",
    "keywords:word_once": lambda kw: f"Include keyword {kw['keyword']} in your response",
    "keywords:letter_frequency": lambda kw: f"In your response, the letter {kw['letter']} should appear {kw['let_relation']} {kw['let_frequency']} times",
    "letters:letter_counting2": lambda kw: f"In your response, the letter {kw['letter']} should appear {kw['let_relation']} {kw['let_frequency']} times",
    "letters:letter_counting": lambda kw: f"Answer with {kw['relation']} {kw['N']} letters",
    "length_constraints:number_words": lambda kw: f"Answer with {kw['relation']} {kw['num_words']} words",
    "length_constraints:number_sentences": lambda kw: f"Your response should contain {kw['relation']} {kw['num_sentences']} sentences",
    "length_constraints:number_paragraphs": lambda kw: f"There should be {kw['num_paragraphs']} paragraphs. Paragraphs are separated with the markdown divider: ***",
    "change_case:capital_word_frequency": lambda kw: f"In your response, words with all capital letters should appear {kw['capital_relation']} {kw['capital_frequency']} times",
    "count:lowercase_counting": lambda kw: f"In your response, all lowercase words should appear at most {kw['N']} times",
    "detectable_content:number_placeholders": lambda kw: f"The response must contain at least {kw['num_placeholders']} placeholders represented by square brackets",
    "detectable_content:postscript": lambda kw: f"At the end of your response, please explicitly add a postscript starting with {kw['postscript_marker']}",
    "detectable_format:multiple_sections": lambda kw: f"Your response must have {kw['num_sections']} sections. Mark the beginning of each section with {kw['section_spliter']} X",
    "detectable_format:number_bullet_lists": lambda kw: f"Your answer must contain exactly {kw['num_bullets']} bullet points",
    "detectable_format:number_highlighted_sections": lambda kw: f"Highlight at least {kw['num_highlights']} sections in your answer with markdown",
    "keywords:existence": lambda kw: f"Include keywords {kw['keywords']} in the response",
    "keywords:forbidden_words": lambda kw: f"Do not include keywords {kw['forbidden_words']} in the response",
    "copy:repeat_phrase": lambda kw: f"Repeat the phrase {kw['phrase']} exactly {kw['small_n']} times, transforming it slightly each time by replacing only one word in the center of the phrase",
    "startend:end_checker": lambda kw: f"Finish your response with this exact phrase {kw['end_phrase']}",
}

hit = collections.Counter()
miss = collections.defaultdict(list)
total = collections.Counter()
for i, r in enumerate(rows):
    c = r["prompt"][0]["content"]
    rec = json.loads(r["extra_info"]["nemotron_ultra"]["record_json"])
    for iid, kw in zip(rec["instruction_id_list"], rec["kwargs"]):
        if iid == "count:counting_composition":
            k = c.find("sentence")
            print("counting_composition row", i, kw)
            print("   ", repr(c[-700:]))
        if iid not in RENDER:
            continue
        total[iid] += 1
        try:
            s = RENDER[iid](kw)
        except Exception as e:
            miss[iid].append((i, "render error " + repr(e)))
            continue
        if s in c:
            hit[iid] += 1
        else:
            miss[iid].append((i, kw))

for iid in sorted(total):
    print(f"{iid}: text matches kwargs in {hit[iid]} of {total[iid]}")
    for i, kw in miss[iid][:4]:
        c = rows[i]["prompt"][0]["content"]
        key = {"keywords:keyword_specific_position": "Include keyword",
               "length_constraints:nth_paragraph_first_word": "There should be"}.get(iid)
        snippet = ""
        if key and key in c:
            j = c.find(key)
            snippet = c[j:j + 260]
        print("    row", i, kw, "|", repr(snippet))
