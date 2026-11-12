# Contracts for the 47 instruction types of the RLVR1 instruction-following rows

Written from the text that the model sees (the user prompt of each row), before reading any
grader code. The instruction texts below were extracted from the prompts by
`audit/scripts/instruction_texts.py` and checked against every row by
`audit/scripts/template_presence.py` (every constraint's text, kwargs filled in, is in its row's
prompt; inline layouts drop the final period and join items with ", " and " and ").

Each contract gives PASS and FAIL conditions. Where the text allows two verdicts, the contract
names a decision entry `D-<topic>` (table at the end) and follows its proposed reading.

## 0. Common definitions

**G1. Graded text.** The graded text is the visible answer.
- A model without a reasoning mode: the whole response.
- A reasoning model (here Qwen3-4B-Thinking-2507, whose chat template opens `<think>` in the
  prompt, so the stored response holds only the closing `</think>`): the text after the last
  `</think>`. A response with no `</think>` is an **extraction failure**: every check fails and
  the row's reward is 0; the report counts these separately. A separate reasoning field is
  never graded.
- `D-think-markup`: a non-reasoning model's response that itself contains a `<think>...</think>`
  span. Proposed: grade the whole response (it is visible text); alternative: strip the span
  (Change 4: an unclosed `<think>` span runs to the end of the response).

**G2. Whitespace.** Leading and trailing whitespace of the graded text is not part of the answer
(invisible); position checks (first word, last word, start, end, quotes, exact options, JSON) use
the stripped text. Invisible formatting is otherwise kept (paragraph checks look at newlines).

**G3. Word.** `D-word`: proposed: a word is a maximal run of Unicode letters, digits and
combining marks, where an internal apostrophe (`'` or `’`) or an internal hyphen joins two
runs into one word ("don't", "well-known" are one word each); markdown symbols, punctuation and
numbers-only runs follow the same rule (a run of digits is a word). Alternative: a word is a
whitespace-separated token that contains at least one letter or digit.

**G4. Word comparison.** Comparing a word with a target word (first word, last word, keyword
position, start/end) ignores letter case and the punctuation or markdown around the word
("**Development**:" is the word development). Not a decision: a careful reader sees the same
word.

**G5. Keyword occurrence.** `D-keyword-boundary`: proposed: keyword k occurs where its letters
appear case-insensitively with no letter, digit or underscore immediately before or after
(hyphens and apostrophes are boundaries, so "fix-it" and "fix's" contain fix, "fixes" and
"prefix" do not). Alternative: any case-insensitive substring ("prefix" contains fix).

**G6. Sentence.** `D-sentence`: proposed: a sentence ends at `.`, `!` or `?` (one or more,
with any closing quote or bracket) followed by whitespace or the end of the text, except after a
common abbreviation (Mr., Mrs., Ms., Dr., St., vs., etc., e.g., i.e., No.) or a single-letter
initial or a list number such as "1."; a line break that ends a non-empty line also ends a
sentence (a heading or a list item without final punctuation is one sentence); a span with no
word is not a sentence. Alternative readings: line breaks do not end sentences (a heading runs
into the next sentence), or a standard sentence tokenizer's output.

**G7. Relations.** "at least N" means count >= N; "less than N" means count < N; "at most N"
means count <= N; "exactly N" and plain "N times" mean count == N (see `D-appear-n-times`).

**G8. Row reward.**
- SkyRL reward (binary mode, the default): 1.0 iff every constraint of the row passes, else 0.0.
- Task-curation gate: reward 0.0 iff some constraint outside the four judged ids
  (`count:count_unique`, `detectable_format:bigram_wrapping`, `language:response_language`,
  `letters:letter_counting`) fails; otherwise the LLM judge decides. The audit grades the gate.
- A check that raises an exception has produced no verdict: a grading failure, counted apart
  from the model's accuracy.

## 1. Contracts, one per instruction id

Text in quotes is the instruction as the model sees it, with kwargs in braces.

### change_case:capital_word_frequency
"In your response, words with all capital letters should appear {capital_relation}
{capital_frequency} times."
PASS iff the number of word occurrences (G3) whose letters are all uppercase (at least one
letter, no lowercase letter) satisfies the relation (G7). Each occurrence counts.
`D-capital-single-letter`: proposed: one-letter words such as "I" and "A" count;
alternative: only words of two or more letters.

### change_case:english_capital
"Your entire response should be in English, and in all capital letters."
PASS iff (a) the graded text has no lowercase letter (any cased script) and (b) it is in
English. FAIL if either part fails. `D-english-part`: proposed: (b) is part of the check;
alternative: only the letter case is checked.

### change_case:english_lowercase
"Your entire response should be in English, and in all lowercase letters. No capital letters
are allowed."
PASS iff the graded text has no uppercase letter (any cased script) and is in English.
`D-english-part` as above.

### combination:two_responses
"Give two different responses. Responses and only responses should be separated by 6 asterisk
symbols: ******."
(Change 8: `D-two-responses-edge`: proposed: a separator at the very start or end is an extra
separator and fails; alternative: it is ignored.)
PASS iff the graded text contains the separator `******` exactly once, no longer run of
asterisks is used as the separator, both sides are non-empty after stripping, and the two sides
differ (after whitespace normalisation). FAIL if the separator is missing, used more than once,
or one side is empty or a copy of the other.

### copy:repeat_phrase
"Repeat the phrase {phrase} exactly {small_n} times, transforming it slightly each time by
replacing only one word in the center of the phrase."
PASS iff the number of transformed repetitions equals small_n, where a transformed repetition
is a span of the response with the phrase's word count whose words equal the phrase's words
(case-insensitive, punctuation ignored) except exactly one word that is neither the first nor
the last. `D-repeat-original`: proposed: an unchanged copy of the phrase is not a repetition
(and fails the "transforming it each time" requirement); alternative: unchanged copies count
toward small_n. `D-repeat-center`: proposed: any word other than the first and the last;
alternative: only the middle word (or one of the two middle words).

### count:count_unique
"Only use unique words in your response, no word should be repeated!"
PASS iff no word (G3) occurs twice, comparing case-insensitively. `D-unique-case`: proposed:
"The" and "the" are the same word; alternative: case-sensitive.

### count:counting_composition (1 row)
"Write 3 paragraphs, delimited by the markdown divider: * * *, with exactly {n_sent} sentences
each, with exactly {n_words} words in each sentence."
PASS iff the text splits at divider lines into exactly 3 non-empty paragraphs, each with exactly
n_sent sentences (G6), each of exactly n_words words (G3). `D-divider-form`: proposed: a line
that is a markdown thematic break made of asterisks (`***` or `* * *`) is the divider;
alternative: only the literal `* * *` (resp. `***`).

### count:lowercase_counting
"In your response, all lowercase words should appear at most {N} times."
PASS iff every word written in lowercase occurs, in lowercase, at most N times. (Change 10: a word
written in lowercase has at least one lowercase letter and no uppercase letter; words of
caseless scripts such as Han or Gurmukhi are not lowercase words.)
`D-lowercase-count`: proposed: count only the lowercase-written occurrences of each word;
alternative: once a word appears in lowercase, count all its occurrences case-insensitively.
`D-lowercase-scope` (Change 2): proposed: "at most N times" applies to each lowercase word;
alternative: the response holds at most N lowercase words in total.

### detectable_content:number_placeholders
"The response must contain at least {num_placeholders} placeholders represented by square
brackets, such as [address]."
PASS iff the number of bracketed spans `[text]` with non-blank text on one line, not nested, is
at least N. `D-placeholder-kind`: proposed: every such span counts (including a markdown link
text or a citation number); alternative: only spans that read as fill-in placeholders.

### detectable_content:postscript
"At the end of your response, please explicitly add a postscript starting with
{postscript_marker}" (marker `P.S.` or `P.P.S`; inline layouts show `P.S` without the dot).
PASS iff a line of the graded text starts (after optional markdown emphasis or heading marks)
with the marker, compared case-insensitively, with or without a final dot, followed by a space,
colon, dot, dash or end of line, and that postscript is the last part of the response (nothing
follows it but its own text). A `P.P.S` line does not satisfy marker `P.S.`, and a `P.S.` line
does not satisfy `P.P.S`. `D-postscript-end`: proposed: the postscript must be the final part
of the response; alternative: a postscript anywhere in the response passes.
`D-postscript-case`: proposed: case-insensitive marker (`p.s.` counts); alternative:
case-sensitive.

### detectable_format:bigram_wrapping
"Wrap every word bigram in double angular brackets, such as <<I am>> <<at home>> <<with my>>
<<cute dog>>."
PASS iff every word of the graded text is inside a `<<...>>` group, and every group holds
exactly two words, except that the last group may hold one word when the word count is odd.
Punctuation may sit inside or outside the groups. `D-bigram-odd`: proposed: a final single-word
group is allowed; alternative: never.

### detectable_format:constrained_response
"Answer with one of the following options: ('My answer is yes.', 'My answer is no.', 'My
answer is maybe.')"
`D-constrained-exact`: proposed: PASS iff the graded text contains exactly one of the three
options (the other text is allowed) and no second option; alternative: PASS iff the graded text,
stripped (markdown emphasis removed), is exactly one option.

### detectable_format:json_format
"Entire output should be wrapped in JSON format. You can use markdown ticks such as ```."
PASS iff the stripped graded text, after removing one optional enclosing markdown code fence
(```` ``` ```` or ```` ```json ````), parses as JSON. FAIL if any text lies outside the JSON (or
outside the fence). `D-json-toplevel`: proposed: any JSON value; alternative: only an object or
an array.

### detectable_format:multiple_sections
"Your response must have {num_sections} sections. Mark the beginning of each section with
{section_spliter} X, such as: {section_spliter} 1 [content of section 1] {section_spliter} 2
[content of section 2]"
PASS iff the graded text has exactly N section-marker lines, each starting (after optional
markdown heading or emphasis) with the spliter word and a section number, and each section has
content. `D-sections-numbering`: proposed: X is any number or label (numbering not checked);
alternative: X must run 1..N. `D-sections-preamble`: proposed: text before the first marker is
allowed; alternative: it makes an extra, unmarked section and fails. `D-sections-case`:
proposed: the spliter word must match as given (SECTION vs Section), case-insensitively;
alternative: exact case. A mention of "Section 2" inside a sentence is not a marker. (Change 6:
a marker may also follow an opening quote mark, or follow a sentence's end and close its line,
as in "...the end. SECTION 2" followed by a line break.)

### detectable_format:number_bullet_lists
"Your answer must contain exactly {num_bullets} bullet points. Use the markdown bullet points
such as: * This is point 1. * This is point 2"
PASS iff the number of markdown bullet items (lines starting, after indentation, with `*`, `-`
or `+` followed by a space) equals N. Numbered items, horizontal rules (`***`, `---`) and lines
starting with `**bold**` are not bullet points. `D-bullet-marker`: proposed: `-` and `+` items
count; alternative: only `*` items. `D-bullet-nested`: proposed: nested items count as bullet
points; alternative: only top-level items.

### detectable_format:number_highlighted_sections
"Highlight at least {num_highlights} sections in your answer with markdown, i.e. *highlighted
section*."
PASS iff the number of markdown-emphasised spans with non-blank text is at least N.
`D-highlight-bold`: proposed: italic `*text*` and bold `**text**` both count; alternative:
only single-asterisk `*text*`. A bullet marker `* ` is not a highlight.

### detectable_format:sentence_hyphens
"All sentences must be connected using hyphens, with no spaces between them."
PASS iff the graded text has no whitespace between consecutive sentences and every boundary
between consecutive sentences is a hyphen `-` (e.g. "One.-Two.-Three."). Spaces inside a
sentence are allowed. A single sentence passes. FAIL if two sentences are separated by a space
or a line break, or joined with " - " (spaces around the hyphen). `D-hyphen-dash`: proposed:
only `-` (and U+2010/U+2011) is a hyphen; alternative: en and em dashes also count.

### detectable_format:square_brackets
"Enclose every word in your response within square brackets."
(Change 10: words are read with the brackets removed, so `[J][u][s][t]` is the word Just split
over four pairs and fails.)
PASS iff every word (G3) is inside a pair of square brackets that encloses only that word
(punctuation may sit inside or outside the brackets). `D-bracket-group`: proposed: each word
in its own pair; alternative: a bracket pair may hold several words (even the whole response).

### detectable_format:title
"Your answer must contain a title, wrapped in double angular brackets, such as <<poem of
joy>>."
PASS iff the graded text contains `<<t>>` where t is non-blank text without a line break.
`D-title-position`: proposed: anywhere; alternative: the title must open the response.

### first_word:first_word_answer
"The first word of your response should be the word {first_word}."
PASS iff the first word (G3) of the graded text equals first_word (G4).

### first_word:first_word_sent
"The first word of each sentence should be the word {first_word}."
PASS iff the graded text has at least one sentence (G6) and the first word of every sentence
equals first_word (G4).

### keywords:existence
"Include keywords {keywords} in the response." (keywords shown as a Python list)
PASS iff every keyword occurs (G5).

### keywords:forbidden_words
"Do not include keywords {forbidden_words} in the response."
PASS iff no forbidden word occurs (G5).

### keywords:frequency
"In your response, the word {keyword} should appear {relation} {frequency} times."
PASS iff the number of occurrences (G5) satisfies the relation (G7).

### keywords:keyword_specific_position
"Include keyword {keyword} in the {n}-th sentence, as the {m}-th word of that sentence."
PASS iff the graded text has at least n sentences (G6) and the m-th word (G3) of sentence n
equals keyword (G4).

### keywords:letter_frequency
"In your response, the letter {letter} should appear {let_relation} {let_frequency} times."
PASS iff the number of occurrences of the letter satisfies the relation.
`D-letter-case`: proposed: case-insensitive ("R" counts for r); alternative: case-sensitive.

### keywords:no_adjacent_consecutive
"No two adjacent words can start with consecutive letters of the alphabet."
PASS iff for no two adjacent words (G3; adjacency ignores punctuation and line breaks) the first
letters, lowercased, are neighbours in the Latin alphabet a-z. Words whose first character is
not a Latin letter never form such a pair. `D-consecutive-script` (Change 7): proposed: only the
Latin alphabet a-z; alternative: letters of any alphabet that are neighbours in Unicode order
(Cyrillic в then г). `D-consecutive-order`: proposed: both orders count
("big apple": b then a is a pair); alternative: only ascending order (a then b).

### keywords:palindrome
"Include a palindrome in your response."
PASS iff some word (G3) of at least 3 letters or digits reads the same reversed
(case-insensitive), or some span of two or more consecutive words whose letters (at least 7)
read the same reversed. `D-palindrome-length`: proposed: words of 3 or more characters;
alternative: any word of 2 or more (or any length, so "a" counts).

### keywords:start_end
"Start and end your response with the same word (do not write anything after the last word, not
even punctuation)."
PASS iff the first and last words (G3, G4) are equal and the stripped graded text ends with the
last word's final letter or digit (no punctuation, markdown or quote after it). Leading
markdown or punctuation before the first word is allowed. `D-start-end-one-word` (Change 3):
proposed: a one-word response passes; alternative: it fails (two occurrences are needed).

### keywords:word_count_different_numbers
"In your response, the word {keyword} should appear {frequency} times." (the row's kwargs
also hold a `relation` that the text does not show)
PASS iff the number of occurrences (G5) equals frequency. `D-appear-n-times`: proposed:
exactly N; alternative: at least N. A hidden relation that the model cannot see ("less than")
is not part of the contract.

### keywords:word_once
"Include keyword {keyword} in your response."
PASS iff the keyword occurs (G5) at least once. (The text says nothing about how many times.)

### language:response_language
"Your ENTIRE response should be in {Language} language, no other language is allowed."
(Change 9: under the proposed reading, a paragraph of ten or more letters written mostly in
another script fails the whole response; this also applies to "in English" in the change_case
contracts.)
PASS iff the response's prose is written in the named language. Proper names, code, numbers,
URLs and quoted terms in other scripts do not by themselves make it fail.
`D-language-mixed`: proposed: a response predominantly in the language with a few foreign
technical terms or names passes; alternative: any foreign word fails.

### last_word:last_word_answer
"The last word of your response should be the word {last_word}."
PASS iff the last word (G3) of the graded text equals last_word (G4); punctuation, markdown or
quotes after it are allowed.

### last_word:last_word_sent
"The last word of each sentence, before punctuation, should be the word {last_word}."
PASS iff the graded text has at least one sentence (G6) and the last word of every sentence
equals last_word (G4).

### length_constraints:nth_paragraph_first_word
"There should be {num_paragraphs} paragraphs. Paragraphs and only paragraphs are separated with
each other by two new lines as if it was '\n\n' in python. Paragraph {nth_paragraph} must start
with word {first_word}."
PASS iff the stripped graded text, split at blank lines (two or more consecutive newlines,
whitespace-only lines included), has exactly num_paragraphs non-empty paragraphs and paragraph
nth_paragraph's first word equals first_word (G4). A row whose nth_paragraph exceeds
num_paragraphs cannot pass. `D-blank-run`: proposed: three or more newlines are one separator;
alternative: only exactly two newlines separate (a longer run makes an empty paragraph).

### length_constraints:number_paragraphs
"There should be {num_paragraphs} paragraphs. Paragraphs are separated with the markdown
divider: ***"
PASS iff the graded text, split at divider lines, has exactly num_paragraphs non-empty
paragraphs. `D-divider-form` (see counting_composition): proposed (Change 5): a `***` or
`* * *` that is not markdown emphasis, wherever it stands (on its own line, or at the end or
start of a paragraph's line); alternative: only a line that is exactly `***`.
(Change 1, see the log in ISSUE.md: the alternative is a line that is exactly `***`; a `***`
inside a line, such as bold italic `***word***`, is never a divider.)
`D-divider-empty`: proposed: empty parts (a divider at the start or end, or two in a row) are
not paragraphs and make the response fail ("paragraphs are separated" by dividers);
alternative: empty parts are ignored.

### length_constraints:number_sentences
"Your response should contain {relation} {num_sentences} sentences."
PASS iff the number of sentences (G6) satisfies the relation.

### length_constraints:number_words
"Answer with {relation} {num_words} words."
PASS iff the number of words (G3) satisfies the relation.

### letters:letter_counting
"Answer with {relation} {N} letters." (N is 2 or 3)
PASS iff the number of letters (Unicode alphabetic characters) in the graded text satisfies
the relation. `D-letters-unit`: proposed: letters are alphabetic characters; alternative:
"letters" means words (a mis-generated "words" instruction).

### letters:letter_counting2
"In your response, the letter {letter} should appear {let_relation} {let_frequency} times."
Same contract as keywords:letter_frequency (`D-letter-case`).

### paragraphs:paragraphs
"There should be 2 paragraphs. Paragraphs are separated with the markdown divider: ***"
Same contract as length_constraints:number_paragraphs with num_paragraphs = 2.

### paragraphs:paragraphs2
"There should be 2 paragraphs. Paragraphs and only paragraphs are separated with each other by
two line breaks."
PASS iff the stripped graded text, split at blank lines, has exactly 2 non-empty paragraphs.
Single line breaks inside a paragraph are allowed. `D-blank-run` applies.

### punctuation:no_comma
"In your entire response, refrain from the use of any commas."
PASS iff the graded text has no comma. `D-comma-chars`: proposed: every comma character counts
(U+002C, fullwidth U+FF0C, ideographic U+3001, Arabic U+060C, small U+FE50); alternative: only
the ASCII comma.

### punctuation:punctuation_dot
"In your entire response, refrain from the use of . (i.e. dots) as punctuation and in general."
PASS iff the graded text has no `.` anywhere ("and in general": decimals, URLs, ellipses
included). `D-dot-chars`: proposed: the ideographic full stop U+3002, fullwidth U+FF0E and the
ellipsis character U+2026 also count; alternative: only U+002E.

### punctuation:punctuation_exclamation
"In your entire response, refrain from the use of ! (i.e. exclamation marks) as punctuation and
in general."
PASS iff the graded text has no `!`. `D-excl-chars`: proposed: fullwidth U+FF01, U+00A1, U+203C,
U+2049, U+2757 and U+2755 also count; alternative: only U+0021.

### startend:end_checker
"Finish your response with this exact phrase {end_phrase}. No other words should follow this
phrase."
PASS iff the stripped graded text ends with end_phrase exactly, or ends with end_phrase followed
only by characters that are not letters or digits (closing markdown or quotes).
`D-end-trailing`: proposed: such trailing non-word characters are allowed ("no other words");
alternative: nothing may follow. `D-end-case`: proposed: the phrase is matched exactly
(case-sensitive: "exact phrase"); alternative: case-insensitive (matters with the lowercase or
capital-letters constraints in the same row).

### startend:quotation
"Wrap your entire response with double quotation marks."
PASS iff the stripped graded text has at least two characters, starts with a double quotation
mark and ends with a double quotation mark. `D-quote-chars`: proposed: the ASCII `"` and the
curly `“` (open) and `”` (close) count; guillemets do not; alternative: only ASCII `"`.

## 2. Decision table (proposed reading first)

| Entry | Proposed reading | Alternative reading |
|---|---|---|
| D-think-markup | grade a non-reasoning model's `<think>` span as text | strip it |
| D-word | runs of letters/digits, internal ' and - join | whitespace tokens with a letter or digit |
| D-keyword-boundary | whole word, hyphen/apostrophe are boundaries | substring |
| D-sentence | punctuation + space, line breaks, abbreviations kept | no line-break boundary / tokenizer |
| D-appear-n-times | "N times" = exactly N | at least N |
| D-capital-single-letter | "I", "A" count as capital words | only 2+ letters |
| D-english-part | "in English" is checked | only case is checked |
| D-repeat-original | unchanged copy does not count | counts |
| D-repeat-center | any non-edge word | only the middle word |
| D-unique-case | case-insensitive | case-sensitive |
| D-divider-form | `***`, `* * *` lines | literal string only |
| D-divider-empty | empty part fails | ignored |
| D-lowercase-count | lowercase-written occurrences only | all occurrences |
| D-placeholder-kind | any `[text]` | fill-in placeholders only |
| D-postscript-end | postscript last | anywhere |
| D-postscript-case | case-insensitive marker | case-sensitive |
| D-bigram-odd | final single-word group allowed | not allowed |
| D-constrained-exact | contains exactly one option | is exactly one option |
| D-json-toplevel | any JSON value | object or array |
| D-sections-numbering | label not checked | 1..N |
| D-sections-preamble | preamble allowed | not allowed |
| D-sections-case | case-insensitive spliter | exact case |
| D-bullet-marker | `*`, `-`, `+` | `*` only |
| D-bullet-nested | nested items count | top level only |
| D-highlight-bold | `*x*` and `**x**` | `*x*` only |
| D-hyphen-dash | `-` (U+2010, U+2011) | also en/em dash |
| D-bracket-group | one word per pair | several words per pair |
| D-title-position | anywhere | at the start |
| D-letter-case | case-insensitive | case-sensitive |
| D-consecutive-order | both orders | ascending only |
| D-palindrome-length | 3+ characters | 2+ or any |
| D-language-mixed | predominantly in the language | no foreign word |
| D-blank-run | 2+ newlines = one separator | exactly two |
| D-letters-unit | alphabetic characters | words |
| D-comma-chars | all comma characters | ASCII only |
| D-dot-chars | `.`, `。`, `．`, `…` | ASCII only |
| D-excl-chars | all exclamation characters | ASCII only |
| D-end-trailing | trailing non-word characters allowed | nothing may follow |
| D-end-case | case-sensitive | case-insensitive |
| D-quote-chars | `"` and `“ ”` | ASCII only |
| D-lowercase-scope (Change 2) | per lowercase word | total lowercase words |
| D-start-end-one-word (Change 3) | one-word response passes | fails |
| D-consecutive-script (Change 7) | Latin a-z only | any alphabet |
| D-two-responses-edge (Change 8) | leading or trailing separator fails | ignored |
