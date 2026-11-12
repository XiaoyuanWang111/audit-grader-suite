"""Data-level checks on the rows: None kwargs, kwarg ranges, and rows whose constraints conflict.

Reads only case/data. Prints counts.
"""
import collections
import json
import os

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(W, "case", "data", "rlvr1_instruction_following.jsonl")

none_kw = collections.Counter()
kw_none_entire = collections.Counter()
nth_gt = 0
nth_examples = []
pairs = collections.Counter()
conflicts = collections.Counter()
conf_examples = collections.defaultdict(list)
dup_ids = 0
with open(DATA, encoding="utf-8") as f:
    for idx, line in enumerate(f):
        rec = json.loads(json.loads(line)["extra_info"]["nemotron_ultra"]["record_json"])
        ids = rec["instruction_id_list"]
        kws = rec["kwargs"]
        if len(set(ids)) != len(ids):
            dup_ids += 1
        d = {}
        for iid, kw in zip(ids, kws):
            if kw is None:
                kw_none_entire[iid] += 1
            else:
                for k, v in kw.items():
                    if v is None:
                        none_kw[(iid, k)] += 1
            d[iid] = kw or {}
        for a in ids:
            for b in ids:
                if a < b:
                    pairs[(a, b)] += 1
        if "length_constraints:nth_paragraph_first_word" in d:
            kw = d["length_constraints:nth_paragraph_first_word"]
            if kw.get("nth_paragraph", 0) > kw.get("num_paragraphs", 99):
                nth_gt += 1
                nth_examples.append((idx, kw))

        def add(name):
            conflicts[name] += 1
            if len(conf_examples[name]) < 2:
                conf_examples[name].append((idx, ids, kws))

        lang = d.get("language:response_language", {}).get("language")
        if "change_case:english_capital" in d and "change_case:english_lowercase" in d:
            add("english_capital+english_lowercase")
        if lang and lang != "en" and ("change_case:english_capital" in d or "change_case:english_lowercase" in d):
            add("non-English response_language + english_*case")
        lc = d.get("letters:letter_counting")
        if lc and lc.get("relation") == "less than":
            add(f"letter_counting less than {lc.get('N')} (any row)")
            others = [i for i in ids if i != "letters:letter_counting"]
            if others:
                add("letter_counting less than + other constraints")
        if "count:count_unique" in d and "copy:repeat_phrase" in d:
            add("count_unique+repeat_phrase")
        if "count:count_unique" in d:
            for k in ("keywords:frequency", "keywords:word_count_different_numbers"):
                if k in d and d[k].get("frequency", 0) >= 2 and (k == "keywords:word_count_different_numbers" or d[k].get("relation") == "at least"):
                    add("count_unique + keyword frequency>=2")
        if "paragraphs:paragraphs" in d and "length_constraints:number_paragraphs" in d and d["length_constraints:number_paragraphs"].get("num_paragraphs") != 2:
            add("paragraphs(2,***) + number_paragraphs!=2")
        if "detectable_format:square_brackets" in d and "startend:quotation" in d:
            add("square_brackets+quotation")
        if "first_word:first_word_answer" in d and "keywords:start_end" in d and "last_word:last_word_answer" in d:
            if d["first_word:first_word_answer"].get("first_word") != d["last_word:last_word_answer"].get("last_word"):
                add("start_end + first_word!=last_word")
        if "detectable_format:constrained_response" in d and len(ids) > 1:
            add("constrained_response + other constraints")
        if "change_case:english_lowercase" in d and "change_case:capital_word_frequency" in d:
            cw = d["change_case:capital_word_frequency"]
            if cw.get("capital_relation") == "at least" and cw.get("capital_frequency", 0) >= 1:
                add("english_lowercase + capital words at least >=1")
        if "change_case:english_capital" in d and "count:lowercase_counting" in d:
            add("english_capital + lowercase_counting (fine)")
        if "change_case:english_capital" in d and "change_case:capital_word_frequency" in d:
            cw = d["change_case:capital_word_frequency"]
            if cw.get("capital_relation") == "less than":
                add("english_capital + capital words less than (likely impossible)")
        if "punctuation:punctuation_dot" in d and "detectable_content:postscript" in d and d["detectable_content:postscript"].get("postscript_marker") == "P.S.":
            add("no dots + P.S. postscript")
        if "punctuation:no_comma" in d and "keywords:existence" in d:
            pass

print("dup ids in a row:", dup_ids)
print("kwargs None (whole):", dict(kw_none_entire))
print("kwargs with None values:", {f"{a}|{b}": v for (a, b), v in none_kw.items()})
print("nth_paragraph > num_paragraphs:", nth_gt, nth_examples[:3])
print("conflicts:")
for k, v in conflicts.most_common():
    print("  ", v, k)
    for ex in conf_examples[k]:
        print("      row", ex[0], ex[1], json.dumps(ex[2])[:200])
