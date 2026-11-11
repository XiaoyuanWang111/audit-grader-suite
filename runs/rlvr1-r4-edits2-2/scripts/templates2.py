"""Second pass: search each constraint's instruction text with known templates (case-insensitive,
without trailing period), and print prompts where it is still not found.
Writes out/constraint_text_variants.txt."""
import collections
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "case", "data", "rlvr1_instruction_following.jsonl")

T = {
    "change_case:capital_word_frequency": "In your response, words with all capital letters should appear {capital_relation} {capital_frequency} times",
    "change_case:english_capital": "Your entire response should be in English, and in all capital letters",
    "change_case:english_lowercase": "Your entire response should be in English, and in all lowercase letters. No capital letters are allowed",
    "combination:two_responses": "Give two different responses. Responses and only responses should be separated by 6 asterisk symbols: ******",
    "copy:repeat_phrase": "Repeat the phrase {phrase} exactly {small_n} times, transforming it slightly each time by replacing only one word in the center of the phrase",
    "count:count_unique": "Only use unique words in your response, no word should be repeated!",
    "count:counting_composition": "Write 3 paragraphs, delimited by the markdown divider: * * *, with exactly {n_sent} sentences each, with exactly {n_words} words in each sentence",
    "count:lowercase_counting": "In your response, all lowercase words should appear at most {N} times",
    "detectable_content:number_placeholders": "The response must contain at least {num_placeholders} placeholders represented by square brackets, such as [address]",
    "detectable_content:postscript": "At the end of your response, please explicitly add a postscript starting with {postscript_marker}",
    "detectable_format:bigram_wrapping": "Wrap every word bigram in double angular brackets, such as <<I am>> <<at home>> <<with my>> <<cute dog>>",
    "detectable_format:constrained_response": "Answer with one of the following options: ('My answer is yes.', 'My answer is no.', 'My answer is maybe.')",
    "detectable_format:json_format": "Entire output should be wrapped in JSON format. You can use markdown ticks such as ```",
    "detectable_format:multiple_sections": "Your response must have {num_sections} sections. Mark the beginning of each section with {section_spliter} X, such as:\n{section_spliter} 1\n[content of section 1]\n{section_spliter} 2\n[content of section 2]",
    "detectable_format:number_bullet_lists": "Your answer must contain exactly {num_bullets} bullet points. Use the markdown bullet points such as:\n* This is point 1. \n* This is point 2",
    "detectable_format:number_highlighted_sections": "Highlight at least {num_highlights} sections in your answer with markdown, i.e. *highlighted section*",
    "detectable_format:sentence_hyphens": "All sentences must be connected using hyphens, with no spaces between them",
    "detectable_format:square_brackets": "Enclose every word in your response within square brackets",
    "detectable_format:title": "Your answer must contain a title, wrapped in double angular brackets, such as <<poem of joy>>",
    "first_word:first_word_answer": "The first word of your response should be the word {first_word}",
    "first_word:first_word_sent": "The first word of each sentence should be the word {first_word}",
    "keywords:existence": "Include keywords {keywords} in the response",
    "keywords:forbidden_words": "Do not include keywords {forbidden_words} in the response",
    "keywords:frequency": "In your response, the word {keyword} should appear {relation} {frequency} times",
    "keywords:keyword_specific_position": "Include keyword {keyword} in the {n}-th sentence, as the {m}-th word of that sentence",
    "keywords:letter_frequency": "In your response, the letter {letter} should appear {let_relation} {let_frequency} times",
    "keywords:no_adjacent_consecutive": "No two adjacent words can start with consecutive letters of the alphabet",
    "keywords:palindrome": "Include a palindrome in your response",
    "keywords:start_end": "Start and end your response with the same word (do not write anything after the last word, not even punctuation)",
    "keywords:word_count_different_numbers": "In your response, the word {keyword} should appear {frequency} times",
    "keywords:word_once": "Include keyword {keyword} in your response",
    "language:response_language": "Your ENTIRE response should be in ",
    "last_word:last_word_answer": "The last word of your response should be the word {last_word}",
    "last_word:last_word_sent": "The last word of each sentence, before punctuation, should be the word {last_word}",
    "length_constraints:nth_paragraph_first_word": "There should be {num_paragraphs} paragraphs. Paragraphs and only paragraphs are separated with each other by two new lines as if it was '\\n\\n' in python. Paragraph {nth_paragraph} must start with word {first_word}",
    "length_constraints:number_paragraphs": "There should be {num_paragraphs} paragraphs. Paragraphs are separated with the markdown divider: ***",
    "length_constraints:number_sentences": "Your response should contain {relation} {num_sentences} sentences",
    "length_constraints:number_words": "Answer with {relation} {num_words} words",
    "letters:letter_counting": "Answer with {relation} {N} letters",
    "letters:letter_counting2": "In your response, the letter {letter} should appear {let_relation} {let_frequency} times",
    "paragraphs:paragraphs": "There should be 2 paragraphs. Paragraphs are separated with the markdown divider: ***",
    "paragraphs:paragraphs2": "There should be 2 paragraphs. Paragraphs and only paragraphs are separated with each other by two line breaks",
    "punctuation:no_comma": "In your entire response, refrain from the use of any commas",
    "punctuation:punctuation_dot": "In your entire response, refrain from the use of . (i.e. dots) as punctuation and in general",
    "punctuation:punctuation_exclamation": "In your entire response, refrain from the use of ! (i.e. exclamation marks) as punctuation and in general",
    "startend:end_checker": "Finish your response with this exact phrase {end_phrase}. No other words should follow this phrase",
    "startend:quotation": "Wrap your entire response with double quotation marks",
}


def render(t, kw):
    out = t
    for k, v in (kw or {}).items():
        if v is None:
            continue
        out = out.replace("{" + k + "}", str(v))
    return out


nf = collections.defaultdict(list)
found = collections.Counter()
for line in open(DATA, encoding="utf-8"):
    row = json.loads(line)
    rec = json.loads(row["extra_info"]["nemotron_ultra"]["record_json"])
    p = rec["prompt"].lower()
    for iid, kw in zip(rec["instruction_id_list"], rec["kwargs"]):
        r = render(T[iid], kw).lower()
        if "{" in r and iid not in ("count:counting_composition",):
            print("unrendered", iid, r)
        if r in p or r.rstrip("!.") in p:
            found[iid] += 1
        else:
            nf[iid].append((row["extra_info"]["nemotron_ultra"]["uuid"], kw, rec["prompt"]))
for iid in sorted(T):
    print(iid, "found", found[iid], "not found", len(nf[iid]))
    for u, kw, p in nf[iid][:2]:
        # locate a fragment of the template
        frag = T[iid][:25].lower()
        i = p.lower().find(frag)
        print("   ", u, json.dumps(kw, ensure_ascii=False)[:120], "|", repr(p[max(0, i - 20):i + 260]) if i >= 0 else repr(p[-300:]))
