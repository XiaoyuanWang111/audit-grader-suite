"""Find each instruction's text in the prompts and print the distinct templates (kwargs masked)."""
import collections, json, re, sys
import pandas as pd
KEY = {
 "count:conjunctions": "coordinating conjunctions", "count:keywords_multiple": "Include keyword",
 "count:numbers": "numbers in the response", "count:person_names": "person names",
 "count:pronouns": "pronouns", "count:punctuation": "punctuation mark", "count:unique_word_count": "unique words",
 "count:word_count_range": "must contain between", "count:words_japanese": "in Japanese",
 "format:emoji": "emoji", "format:line_indent": "indent", "format:list": "list of items",
 "format:newline": "new line", "format:no_bullets_bullets": "bullet points denoted",
 "format:no_whitespace": "whitespace", "format:options": "following options", "format:output_template": "template",
 "format:parentheses": "parentheses", "format:quote_unquote": "quoted phrase", "format:quotes": "quotes within quotes",
 "format:sub-bullets": "sub-bullet", "format:thesis": "thesis statement", "format:title_case": "title case",
 "ratio:overlap": "overlap", "ratio:sentence_balance": "balanced", "ratio:sentence_type": "ratio of declarative",
 "ratio:sentence_words": "same number of characters", "ratio:stop_words": "stop words",
 "repeat:repeat_change": "Repeat the request", "repeat:repeat_simple": "Only output this sentence",
 "repeat:repeat_span": "Copy the span", "sentence:alliteration_increment": "alliterative",
 "sentence:increment": "more words than the previous", "sentence:keyword": "include keyword",
 "words:alphabet": "next letter of the alphabet", "words:consonants": "consonant cluster",
 "words:keywords_specific_position": "word of that sentence", "words:last_first": "last word of each sentence",
 "words:no_consecutive": "consecutive words", "words:odd_even_syllables": "syllables",
 "words:palindrome": "palindromes", "words:paragraph_last_first": "Each paragraph",
 "words:prime_lengths": "prime numbers", "words:repeats": "repeat any word", "words:start_verb": "start with a verb",
 "words:vowel": "types of vowels", "words:words_position": "second word",
}
df = pd.read_parquet("case/data/train-00000-of-00001.parquet")
tmpl = collections.defaultdict(collections.Counter)
missing = collections.defaultdict(list)
for _, row in df.iterrows():
    for iid, kw in zip(list(row["instruction_id_list"]), row["kwargs"]):
        if iid.startswith("custom:"):
            continue
        kw = {k: v for k, v in kw.items() if v is not None}
        p = row["prompt"]
        k = KEY[iid]
        i = p.lower().find(k.lower())
        if i < 0:
            missing[iid].append(row["key"]); continue
        # sentence-ish window: back to previous [.!?] + space or start; forward 2 boundaries
        start = max(p.rfind(". ", 0, i), p.rfind("? ", 0, i), p.rfind("! ", 0, i), p.rfind("\n", 0, i))
        start = 0 if start < 0 else start + 2
        m = list(re.finditer(r"[.!?](\s|$)", p[i:]))
        end = i + (m[0].end() if m else len(p) - i)
        s = p[start:end].strip()
        for kk, v in kw.items():
            if isinstance(v, float) and v.is_integer():
                v = int(v)
            vs = str(v)
            if kk in ("reference_text", "prompt_to_repeat"):
                continue
            if vs and len(vs) < 200:
                s = s.replace(vs, "{" + kk + "}")
        tmpl[iid][s] += 1
sel = sys.argv[1:]
for iid in sorted(tmpl):
    if sel and not any(iid.startswith(x) for x in sel):
        continue
    print(f"=== {iid}" + (f"  KEY NOT FOUND in keys {missing[iid]}" if missing[iid] else ""))
    for s, c in tmpl[iid].most_common():
        print(f"  [{c}] {s[:400]}")
for iid in missing:
    if iid not in tmpl:
        print("=== MISSING ENTIRELY", iid, missing[iid])
