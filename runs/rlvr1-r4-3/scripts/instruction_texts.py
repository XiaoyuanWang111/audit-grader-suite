"""Locate each constraint's instruction text in its prompt (data only, no grader code).

For every constraint of every row, search the prompt for the instruction text of
its id with the regexes below (written from the prompts), and compare the
numbers and words the text shows with the constraint's kwargs.

Usage: python instruction_texts.py [--show-unmatched N] [--json OUT]
"""
import collections
import json
import re
import sys

DATA = "<W>/case/data/rlvr1_instruction_following.jsonl"

REL = r"(?P<rel>at least|less than|at most|more than|exactly|fewer than)"
T = {
    "change_case:capital_word_frequency": r"[Ii]n your response, words with all capital letters should appear " + REL + r" (?P<n>\d+) times",
    "change_case:english_capital": r"[Yy]our entire response should be in English, and in all capital letters",
    "change_case:english_lowercase": r"[Yy]our entire response should be in English, and in all lowercase letters\. No capital letters are allowed",
    "combination:two_responses": r"[Gg]ive two different responses\. Responses and only responses should be separated by 6 asterisk symbols: \*\*\*\*\*\*",
    "copy:repeat_phrase": r"[Rr]epeat the phrase (?P<phrase>.+?) exactly (?P<n>\d+) times, transforming it slightly each time by replacing only one word in the center of the phrase",
    "count:count_unique": r"[Oo]nly use unique words in your response, no word should be repeated!",
    "count:counting_composition": r"[Ww]rite (?P<p>\d+) paragraphs, delimited by the markdown divider: \* \* \*, with exactly (?P<s>\d+) sentences each, with exactly (?P<w>\d+) words in each sentence",
    "count:lowercase_counting": r"[Ii]n your response, all lowercase words should appear at most (?P<n>\d+) times",
    "detectable_content:number_placeholders": r"[Tt]he response must contain at least (?P<n>\d+) placeholders represented by square brackets, such as \[address\]",
    "detectable_content:postscript": r"[Aa]t the end of your response, please explicitly add a postscript starting with (?P<m>[^\s,]+?)(?=[\s,]|$)",
    "detectable_format:bigram_wrapping": r"[Ww]rap every word bigram in double angular brackets, such as <<I am>> <<at home>> <<with my>> <<cute dog>>",
    "detectable_format:constrained_response": r"[Aa]nswer with one of the following options: (?P<opts>\(.*?\))",
    "detectable_format:json_format": r"[Ee]ntire output should be wrapped in JSON format\. You can use markdown ticks such as ```",
    "detectable_format:multiple_sections": r"[Yy]our response must have (?P<n>\d+) sections\. Mark the beginning of each section with (?P<sp>.+?) X, such as:",
    "detectable_format:number_bullet_lists": r"[Yy]our answer must contain exactly (?P<n>\d+) bullet points\. Use the markdown bullet points such as:",
    "detectable_format:number_highlighted_sections": r"[Hh]ighlight at least (?P<n>\d+) sections in your answer with markdown, i\.e\. \*highlighted section\*",
    "detectable_format:sentence_hyphens": r"[Aa]ll sentences must be connected using hyphens, with no spaces between them",
    "detectable_format:square_brackets": r"[Ee]nclose every word in your response within square brackets",
    "detectable_format:title": r"[Yy]our answer must contain a title, wrapped in double angular brackets, such as <<poem of joy>>",
    "first_word:first_word_answer": r"[Tt]he first word of your response should be the word (?P<w>[^\s.,]+)",
    "first_word:first_word_sent": r"[Tt]he first word of each sentence should be the word (?P<w>[^\s.,]+)",
    "keywords:existence": r"[Ii]nclude keywords (?P<kw>\[.*?\]) in the response",
    "keywords:forbidden_words": r"[Dd]o not include keywords (?P<kw>\[.*?\]) in the response",
    "keywords:frequency": r"[Ii]n your response, the word (?P<k>\S+) should appear " + REL + r" (?P<n>\d+) times",
    "keywords:keyword_specific_position": r"[Ii]nclude keyword (?P<k>\S+) in the (?P<n>\d+)-th sentence, as the (?P<m>\d+)-th word of that sentence",
    "keywords:letter_frequency": r"[Ii]n your response, the letter (?P<l>\S+) should appear " + REL + r" (?P<n>\d+) times",
    "keywords:no_adjacent_consecutive": r"[Nn]o two adjacent words can start with consecutive letters of the alphabet",
    "keywords:palindrome": r"[Ii]nclude a palindrome in your response",
    "keywords:start_end": r"[Ss]tart and end your response with the same word \(do not write anything after the last word, not even punctuation\)",
    "keywords:word_count_different_numbers": r"[Ii]n your response, the word (?P<k>\S+) should appear (?P<n>\d+) times",
    "keywords:word_once": r"[Ii]nclude keyword (?P<k>\S+) in your response",
    "language:response_language": r"[Yy]our ENTIRE response should be in (?P<lang>[\w ]+?) language, no other language is allowed",
    "last_word:last_word_answer": r"[Tt]he last word of your response should be the word (?P<w>[^\s.,]+)",
    "last_word:last_word_sent": r"[Tt]he last word of each sentence, before punctuation, should be the word (?P<w>[^\s.,]+)",
    "length_constraints:nth_paragraph_first_word": r"[Tt]here should be (?P<np>\d+) paragraphs\. Paragraphs and only paragraphs are separated with each other by two new lines as if it was '\\n\\n' in python\. Paragraph (?P<n>\d+) must start with word (?P<w>[^\s.,]+)",
    "length_constraints:number_paragraphs": r"[Tt]here should be (?P<n>\d+) paragraphs\. Paragraphs are separated with the markdown divider: \*\*\*",
    "length_constraints:number_sentences": r"[Yy]our response should contain " + REL + r" (?P<n>\d+) sentences",
    "length_constraints:number_words": r"[Aa]nswer with " + REL + r" (?P<n>\d+) words",
    "letters:letter_counting": r"[Aa]nswer with " + REL + r" (?P<n>\d+) letters",
    "letters:letter_counting2": r"[Ii]n your response, the letter (?P<l>\S+) should appear " + REL + r" (?P<n>\d+) times",
    "paragraphs:paragraphs": r"[Tt]here should be (?P<n>\d+) paragraphs\. Paragraphs are separated with the markdown divider: \*\*\*",
    "paragraphs:paragraphs2": r"[Tt]here should be (?P<n>\d+) paragraphs\. Paragraphs and only paragraphs are separated with each other by two line breaks",
    "punctuation:no_comma": r"[Ii]n your entire response, refrain from the use of any commas",
    "punctuation:punctuation_dot": r"[Ii]n your entire response, refrain from the use of \. \(i\.e\. dots\) as punctuation and in general",
    "punctuation:punctuation_exclamation": r"[Ii]n your entire response, refrain from the use of ! \(i\.e\. exclamation marks\) as punctuation and in general",
    "startend:end_checker": r"[Ff]inish your response with this exact phrase (?P<p>.+?)\. No other words should follow this phrase",
    "startend:quotation": r"[Ww]rap your entire response with double quotation marks",
}

LANG = {
    "en": "English", "es": "Spanish", "fr": "French", "de": "German", "it": "Italian", "pt": "Portuguese",
    "ru": "Russian", "ar": "Arabic", "hi": "Hindi", "bn": "Bengali", "ur": "Urdu", "pa": "Punjabi",
    "ta": "Tamil", "te": "Telugu", "ml": "Malayalam", "kn": "Kannada", "gu": "Gujarati", "mr": "Marathi",
    "ne": "Nepali", "ko": "Korean", "ja": "Japanese", "zh": "Chinese", "vi": "Vietnamese", "th": "Thai",
    "fi": "Finnish", "sv": "Swedish", "bg": "Bulgarian", "uk": "Ukrainian", "fa": "Persian", "tr": "Turkish",
    "pl": "Polish", "nl": "Dutch", "el": "Greek", "he": "Hebrew", "id": "Indonesian", "sw": "Swahili",
    "cs": "Czech", "ro": "Romanian", "hu": "Hungarian", "da": "Danish", "no": "Norwegian",
}

# kwarg -> regex group, per id, for the comparison of text and kwargs
KWMAP = {
    "change_case:capital_word_frequency": {"capital_relation": "rel", "capital_frequency": "n"},
    "copy:repeat_phrase": {"phrase": "phrase", "small_n": "n"},
    "count:counting_composition": {"n_sent": "s", "n_words": "w"},
    "count:lowercase_counting": {"N": "n"},
    "detectable_content:number_placeholders": {"num_placeholders": "n"},
    "detectable_content:postscript": {"postscript_marker": "m"},
    "detectable_format:multiple_sections": {"num_sections": "n", "section_spliter": "sp"},
    "detectable_format:number_bullet_lists": {"num_bullets": "n"},
    "detectable_format:number_highlighted_sections": {"num_highlights": "n"},
    "first_word:first_word_answer": {"first_word": "w"},
    "first_word:first_word_sent": {"first_word": "w"},
    "keywords:existence": {"keywords": "kw"},
    "keywords:forbidden_words": {"forbidden_words": "kw"},
    "keywords:frequency": {"keyword": "k", "relation": "rel", "frequency": "n"},
    "keywords:keyword_specific_position": {"keyword": "k", "n": "n", "m": "m"},
    "keywords:letter_frequency": {"letter": "l", "let_relation": "rel", "let_frequency": "n"},
    "keywords:word_count_different_numbers": {"keyword": "k", "frequency": "n"},
    "keywords:word_once": {"keyword": "k"},
    "last_word:last_word_answer": {"last_word": "w"},
    "last_word:last_word_sent": {"last_word": "w"},
    "length_constraints:nth_paragraph_first_word": {"num_paragraphs": "np", "nth_paragraph": "n", "first_word": "w"},
    "length_constraints:number_paragraphs": {"num_paragraphs": "n"},
    "length_constraints:number_sentences": {"relation": "rel", "num_sentences": "n"},
    "length_constraints:number_words": {"relation": "rel", "num_words": "n"},
    "letters:letter_counting": {"relation": "rel", "N": "n"},
    "letters:letter_counting2": {"letter": "l", "let_relation": "rel", "let_frequency": "n"},
    "startend:end_checker": {"end_phrase": "p"},
}


def norm(v):
    if isinstance(v, list):
        return str(v)
    return str(v)


def main():
    show = 0
    out = None
    args = sys.argv[1:]
    if "--show-unmatched" in args:
        show = int(args[args.index("--show-unmatched") + 1])
    if "--json" in args:
        out = args[args.index("--json") + 1]
    total = collections.Counter()
    matched = collections.Counter()
    mismatch = collections.defaultdict(collections.Counter)
    examples = collections.defaultdict(list)
    unmatched_examples = collections.defaultdict(list)
    records = []
    with open(DATA, encoding="utf-8") as f:
        for i, line in enumerate(f):
            row = json.loads(line)
            rec = json.loads(row["extra_info"]["nemotron_ultra"]["record_json"])
            p = rec["prompt"]
            for j, (iid, kw) in enumerate(zip(rec["instruction_id_list"], rec["kwargs"])):
                total[iid] += 1
                kw = {k: v for k, v in (kw or {}).items() if v is not None}
                ms = list(re.finditer(T[iid], p))
                entry = {"row": i, "uuid": rec["uuid"], "j": j, "id": iid, "kwargs": kw, "found": len(ms)}
                if not ms:
                    if len(unmatched_examples[iid]) < show:
                        unmatched_examples[iid].append((i, kw))
                    records.append(entry)
                    continue
                matched[iid] += 1
                # choose the match that best agrees with kwargs
                best = None
                for m in ms:
                    g = m.groupdict()
                    diffs = []
                    for k, grp in KWMAP.get(iid, {}).items():
                        if k not in kw:
                            diffs.append((k, "missing-kwarg", g.get(grp)))
                            continue
                        if grp not in g or g[grp] is None:
                            continue
                        if norm(kw[k]) != g[grp]:
                            diffs.append((k, norm(kw[k]), g[grp]))
                    if best is None or len(diffs) < len(best[1]):
                        best = (m, diffs)
                m, diffs = best
                entry["text"] = m.group(0)
                entry["diffs"] = diffs
                if iid == "language:response_language":
                    lang = kw.get("language")
                    if LANG.get(lang) != m.group("lang"):
                        diffs.append(("language", lang, m.group("lang")))
                for d in diffs:
                    mismatch[iid][(d[0], d[1] == "missing-kwarg")] += 1
                    if len(examples[iid]) < 4:
                        examples[iid].append((i, d))
                if iid in ("paragraphs:paragraphs", "paragraphs:paragraphs2"):
                    mismatch[iid][("text n=" + m.group("n"), False)] += 1
                if iid == "keywords:word_count_different_numbers":
                    mismatch[iid][("relation=" + str(kw.get("relation")), False)] += 1
                records.append(entry)
    for iid in sorted(total):
        print(f"{iid:48s} {matched[iid]:5d}/{total[iid]:5d} {dict(mismatch[iid])}")
        for e in examples[iid]:
            print("     e.g.", e)
        for e in unmatched_examples[iid]:
            print("     unmatched", e)
    if out:
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
