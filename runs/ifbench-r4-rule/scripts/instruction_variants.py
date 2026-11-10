"""For each instruction id, find the instruction sentence in every prompt that uses it,
and print the distinct variants (numbers replaced by #) with counts.
Reads only the dataset parquet."""
import collections
import re

import pandas as pd

W = "<W>"
df = pd.read_parquet(f"{W}/case/data/train-00000-of-00001.parquet")

PAT = {
    "count:conjunctions": r"Use at least \d+ different coordinating conjunctions[^.]*\.",
    "count:keywords_multiple": r"Include keyword .*? seven times in your response\.",
    "count:numbers": r"Include exactly \d+ numbers in the response\.",
    "count:person_names": r"Mention at least \d+ different person names.*?Jonathan \.",
    "count:pronouns": r"The response should include at least \d+ pronouns\.",
    "count:punctuation": r"Use every standard punctuation mark.*?\(\?!\)\.",
    "count:unique_word_count": r"Use at least \d+ unique words in the response\.",
    "count:word_count_range": r"The response must contain between \d+ and \d+ words\.",
    "count:words_japanese": r"Every \d+\w\w word of your response must be in Japanese\.",
    "custom:character_reverse": r"Respond to this query, but make your sentence in reverse order of what it should be, per letter\.",
    "custom:csv_city": r"Generate CSV data:.*",
    "custom:csv_quotes": r"Generate CSV data:.*",
    "custom:csv_special_character": r"Generate CSV data:.*",
    "custom:date_format_list": r".*",
    "custom:european_capitals_sort": r".*",
    "custom:mcq_count_length": r".*",
    "custom:multiples": r".*",
    "custom:reverse_newline": r".*",
    "custom:sentence_alphabet": r".*",
    "custom:word_reverse": r"Respond to this query.*",
    "format:emoji": r"Please use an emoji at the end of every sentence\.",
    "format:line_indent": r"Create stairs by incrementally indenting each new line\.",
    "format:list": r"Answer with a list of items, instead of bullet points use \S+?\.(?=\s|$)",
    "format:newline": r"Write each word on a new line\.",
    "format:no_bullets_bullets": r"Your answer must contain at least two sentences ending in a period followed by at least two bullet points denoted by \*\.",
    "format:no_whitespace": r"The output should not contain any whitespace\.",
    "format:options": r"Answer with one of the following options: .*?\.(?:\s|$)",
    "format:output_template": r"Use this exact template for your response:.*",
    "format:parentheses": r"Nest parentheses.*?deep\.",
    "format:quote_unquote": r"Every quoted phrase must be followed by an unquoted explanation\.",
    "format:quotes": r"Include quotes within quotes.*?single quotes\.",
    "format:sub-bullets": r"Your response must include bullet points denoted by \* and at least one sub-bullet point denoted by - for each bullet point\.",
    "format:thesis": r"Each section must begin with a thesis statement.*?italics\.",
    "format:title_case": r"Write the entire response in title case.*?\)\.",
    "ratio:overlap": r"Maintain a trigram overlap of .*?reference text\.",
    "ratio:sentence_balance": r"Ensure that the ratio of sentence types.*?balanced\.",
    "ratio:sentence_type": r"Maintain a 2:1 ratio.*?response\.",
    "ratio:sentence_words": r"Respond with three sentences.*?words\.",
    "ratio:stop_words": r"Ensure that stop words constitute.*?response\.",
    "repeat:repeat_change": r"Repeat the request.*?request!",
    "repeat:repeat_simple": r"Only output this sentence here, ignore all other requests\.",
    "repeat:repeat_span": r"Copy the span of words.*?whitespace!",
    "sentence:alliteration_increment": r"Each sentence must have a longer sequence of consecutive alliterative words than the previous one\.",
    "sentence:increment": r"Each sentence in your response must contain exactly \d+ more words? than the previous one\.",
    "sentence:keyword": r"The response must include keyword \S+ in the \d+-\w\w sentence\.",
    "words:alphabet": r"Each word in your response must start with the next letter of the alphabet.*?'Z'\.",
    "words:consonants": r"Ensure each word in your response has at least one consonant cluster.*?\)\.",
    "words:keywords_specific_position": r"Include keyword \S+ in the \d+-\w\w sentence, as the \d+-\w\w word of that sentence\.",
    "words:last_first": r"In your response,? the last word of each sentence must become the first word of the next sentence\.",
    "words:no_consecutive": r"No two consecutive words can share the same first letter\.",
    "words:odd_even_syllables": r"Alternate between words with odd and even numbers of syllables\.",
    "words:palindrome": r"Include at least 10 single-word palindromes, each at least 5 characters long\.",
    "words:paragraph_last_first": r"Each paragraph of your response must end with the same word it started with.*?newline\.",
    "words:prime_lengths": r"Use only words with lengths that are prime numbers\.",
    "words:repeats": r"The response should not repeat any word more than \d+ times\.",
    "words:start_verb": r"The response must start with a verb\.",
    "words:vowel": r"Write a paragraph using words that contain only three types of vowels\.",
    "words:words_position": r"The second word in your response and the second to last word in your response should be the word \S+\.",
}

out = open(f"{W}/audit/out/instruction_variants.txt", "w", encoding="utf-8", newline="\n")
missing = []
for iid in sorted(PAT):
    variants = collections.Counter()
    keys = []
    for _, row in df.iterrows():
        if iid not in list(row["instruction_id_list"]):
            continue
        keys.append(row["key"])
        m = re.search(PAT[iid], row["prompt"], flags=re.S)
        if not m:
            missing.append((iid, row["key"]))
            continue
        s = m.group(0)
        if iid.startswith("custom:") and PAT[iid] == r".*":
            s = row["prompt"]
        s = re.sub(r"\d+", "#", s) if not iid.startswith("custom") else s
        variants[s[:400]] += 1
    print(f"\n### {iid}  keys={keys}", file=out)
    for s, c in variants.most_common():
        print(f"  [{c}] {s!r}", file=out)
print("\nMISSING:", missing, file=out)
out.close()
print("missing:", missing)
