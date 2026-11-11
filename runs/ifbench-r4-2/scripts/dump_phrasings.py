"""List every distinct phrasing of each instruction in the prompts (task text only)."""
import json
import re
from collections import defaultdict, Counter
from pathlib import Path

import pandas as pd

W = Path(__file__).resolve().parents[2]
df = pd.read_parquet(W / "case/data/train-00000-of-00001.parquet")

PAT = {
    "count:conjunctions": r"coordinating conjunctions",
    "count:keywords_multiple": r"Include keyword",
    "count:numbers": r"numbers in the response",
    "count:person_names": r"person names",
    "count:pronouns": r"pronouns",
    "count:punctuation": r"punctuation",
    "count:unique_word_count": r"unique words",
    "count:word_count_range": r"between \d+ and \d+ words",
    "count:words_japanese": r"Japanese",
    "format:emoji": r"emoji",
    "format:line_indent": r"stairs",
    "format:list": r"list of items",
    "format:newline": r"new line",
    "format:no_bullets_bullets": r"two sentences ending",
    "format:no_whitespace": r"whitespace",
    "format:options": r"following options",
    "format:output_template": r"exact template",
    "format:parentheses": r"Nest parentheses",
    "format:quote_unquote": r"quoted phrase",
    "format:quotes": r"quotes within quotes",
    "format:sub-bullets": r"sub-bullet",
    "format:thesis": r"thesis statement",
    "format:title_case": r"title case",
    "ratio:overlap": r"trigram overlap",
    "ratio:sentence_balance": r"ratio of sentence types",
    "ratio:sentence_type": r"ratio of declarative",
    "ratio:sentence_words": r"same number of characters",
    "ratio:stop_words": r"stop words",
    "repeat:repeat_change": r"Repeat the request",
    "repeat:repeat_simple": r"Only output this sentence",
    "repeat:repeat_span": r"Copy the span",
    "sentence:alliteration_increment": r"alliterative",
    "sentence:increment": r"more words than the previous",
    "sentence:keyword": r"must include keyword",
    "words:alphabet": r"next letter of the alphabet",
    "words:consonants": r"consonant cluster",
    "words:keywords_specific_position": r"Include keyword \S+ in the",
    "words:last_first": r"last word of each sentence",
    "words:no_consecutive": r"consecutive words",
    "words:odd_even_syllables": r"syllables",
    "words:palindrome": r"palindromes",
    "words:paragraph_last_first": r"Each paragraph",
    "words:prime_lengths": r"prime numbers",
    "words:repeats": r"repeat any word",
    "words:start_verb": r"start with a verb",
    "words:vowel": r"types of vowels",
    "words:words_position": r"second word",
}

out = []
variants = defaultdict(Counter)
for _, r in df.iterrows():
    p = r["prompt"]
    for iid, kw in zip(r["instruction_id_list"], r["kwargs"]):
        kw = {k: (v.tolist() if hasattr(v, "tolist") else v) for k, v in kw.items() if v is not None}
        if iid.startswith("custom:"):
            continue
        pat = PAT[iid]
        m = list(re.finditer(pat, p))
        if not m:
            out.append(f"NOMATCH {iid} key={r['key']}: head={p[:200]!r}")
            continue
        # sentence-ish window around the first match
        s = m[0].start()
        a = max(p.rfind(". ", 0, s), p.rfind("\n", 0, s), p.rfind("? ", 0, s))
        a = 0 if a < 0 else a + 1
        b_candidates = [x for x in (p.find(". ", m[0].end()), p.find("\n", m[0].end())) if x >= 0]
        b = min(b_candidates) + 1 if b_candidates else len(p)
        sent = p[a:b].strip()
        if len(sent) > 400:
            sent = sent[:400] + "..."
        norm = re.sub(r"\d+(\.\d+)?", "#", sent)
        variants[iid][norm] += 1

with open(W / "audit/out/instruction_phrasings.txt", "w", newline="\n", encoding="utf-8") as f:
    for line in out:
        f.write(line + "\n")
    for iid in sorted(variants):
        f.write(f"=== {iid}\n")
        for v, c in variants[iid].most_common():
            f.write(f"  [{c}] {v}\n")
print("done", len(out), "nomatch")
