# Contracts for the 47 instruction checks (RLVR1 instruction-following rows)

Version 2 (changes marked [v2]; reasons in audit/ISSUE.md, step 3 entry).

Written from the text the model sees (the instruction texts in the rows' prompts, collected by
`audit/scripts/explore_texts2.py` and `audit/scripts/text_coverage.py`) before any grader code
was read. Each check's instruction text is quoted as it appears in the prompts, with `{name}` for
the row's kwargs. Where the text allows two verdicts, the contract states the proposed reading
and names the decision entry `D-<topic>` (table at the end).

## General rules

**G1. Graded text.** For a response that contains `</think>`, the graded text is the text after
the last `</think>`. A response from a thinking configuration (the chat template opens the think
block in the prompt) with no `</think>` is an extraction failure: it fails every check and is
counted separately. A response from a non-thinking configuration is graded whole, except that a
`<think>…</think>` block at its start is removed; one that starts with `<think>` and never closes
it is an extraction failure (D-think-nonthinking). The model's reasoning is never graded.

**G2. Whitespace at the ends.** Leading and trailing whitespace of the graded text is ignored by
every check that refers to the start or the end of the response.

**G3. Words.** A word is a maximal run of Unicode letters, digits and combining marks; an
apostrophe (' or ’) or a hyphen between two such characters joins the run, so `don't` and
`well-known` are one word each (D-word). In scripts written without spaces (Han, kana, Thai) each
ideograph or kana counts as one word for word counts (D-word-cjk).

**G4. Keyword matching.** A given keyword matches a word of the response when they are equal
ignoring case (D-keyword-case). Only whole words match: `soundtrack` does not contain the word
`sound`, and inflected forms (`dogs` for `dog`) do not match (D-keyword-substring). A
multi-word keyword or phrase matches the same sequence of words.

**G5. Sentences.** A sentence ends at `.`, `!` or `?` (one or more, optionally followed by
closing quotes or brackets) that is followed by whitespace or the end of the text, except after
an abbreviation (`Mr.`, `e.g.`, `U.S.`) or inside a number (`3.14`). A line that ends without
terminal punctuation (a heading, a list item, a table row) also ends a sentence (D-sentence-lines).
Text without any terminal punctuation is one sentence. Markdown markers at the start of a line
(`#`, `*`, `-`, `1.`, `>`) are not words.

**G6. First and last word.** The first (last) word of a text is its first (last) word under G3.
Punctuation attached to a word is not part of it (`Development,` is the word `Development`).
Markdown markup and quotation marks before the first word or after the last word are ignored
(D-first-last-markup), except where a check says otherwise (`keywords:start_end`). [v2]

**G7. Relations.** `less than N`: count < N. `at least N`: count >= N. `at most N`:
count <= N. `exactly N`: count = N.

**G8. Truncated responses** (finish reason `length`) are graded as written; reports count them
separately.

**G9. Row reward (both pipelines' deterministic part).** A row's constraints are all required;
a binary reward is 1 only when every constraint passes. A checker that raises an error has not
shown that the constraint passes: the constraint fails, and the error is counted as a grading
failure separately from model accuracy.

## Contracts

### change_case:capital_word_frequency
Text: "In your response, words with all capital letters should appear {capital_relation} {capital_frequency} times."
Count the words (G3) that contain at least one cased letter and whose cased letters are all
uppercase. One-letter words such as `I` and `A` count (D-allcaps-short). Pass iff the count
satisfies the relation (G7).

### change_case:english_capital
Text: "Your entire response should be in English, and in all capital letters."
Pass iff the graded text contains no lowercase letter (any script with case; characters without
case such as digits, punctuation and CJK do not matter, D-case-scope) and its prose is in English
(proper nouns, code identifiers, numbers and quoted foreign terms allowed, D-english-mixed).
Fail if any lowercase letter appears, including in code, URLs and quotes (D-case-scope), or if the
prose is in another language.

### change_case:english_lowercase
Text: "Your entire response should be in English, and in all lowercase letters. No capital letters are allowed."
Pass iff the graded text contains no uppercase (or titlecase) letter and its prose is in English
(D-english-mixed, D-case-scope). Fail on any capital letter anywhere.

### combination:two_responses
Text: "Give two different responses. Responses and only responses should be separated by 6 asterisk symbols: ******."
Pass iff the graded text contains exactly one separator, a run of exactly six `*` (D-two-sep),
the parts before and after it both contain a word, and the two parts differ after trimming
whitespace (D-two-different: "different" means not identical). Fail with no separator, more than
one separator, an empty side, or two identical responses.

### copy:repeat_phrase
Text: "Repeat the phrase {phrase} exactly {small_n} times, transforming it slightly each time by replacing only one word in the center of the phrase."
A variant is a word sequence (G3/G4) with the same number of words as the phrase, equal to it
(ignoring case) except for exactly one word, which is not the first or the last word
(D-repeat-center) and is replaced by a different word. Pass iff the graded text contains exactly
{small_n} variants. Unchanged copies of the phrase neither count nor fail the check
(D-repeat-copies). Fail with fewer or more variants, or when every repetition changes no word, or
changes two words, or changes the first or last word.

### count:count_unique
Text: "Only use unique words in your response, no word should be repeated!"
Pass iff no word (G3) occurs more than once, comparing words ignoring case (D-unique-case).
Numbers are words. Fail if any word repeats.

### count:counting_composition
Text: "Write 3 paragraphs, delimited by the markdown divider: * * *, with exactly {n_sent} sentences each, with exactly {n_words} words in each sentence."
Pass iff the graded text, split at lines consisting of `* * *`, has exactly 3 non-empty
paragraphs, each with exactly {n_sent} sentences (G5), each sentence with exactly {n_words}
words (G3).

### count:lowercase_counting
Text: "In your response, all lowercase words should appear at most {N} times."
A lowercase word is a word (G3) whose cased letters are all lowercase and that has at least one.
Pass iff every distinct lowercase word occurs at most {N} times in its lowercase form
(D-lowercase-scope: per word, not the total number of lowercase words).

### detectable_content:number_placeholders
Text: "The response must contain at least {num_placeholders} placeholders represented by square brackets, such as [address]."
A placeholder is a `[`…`]` span on one line whose content is non-empty, has a non-space
character and contains no bracket. Any such span counts, including `[1]` and the text of a
markdown link (D-placeholder). Pass iff there are at least {num_placeholders}.

### detectable_content:postscript
Text: "At the end of your response, please explicitly add a postscript starting with {postscript_marker}"
(147 prompts show the marker `P.S.` without its final dot, as `P.S`.)
Pass iff a line of the graded text starts (after optional whitespace and markdown emphasis such
as `**`) with the marker, matched ignoring case (D-postscript-case) and with its final dot
optional (D-postscript-dot; where the prompt shows the marker without the dot, the dot is
optional under every reading) [v2],
and that postscript is the last part of the response: it is in the last blank-line-separated block
of the graded text (D-postscript-end). Fail with no marker at a line start, with the marker only
inside a sentence, or with the postscript followed by further body text.

### detectable_format:bigram_wrapping
Text: "Wrap every word bigram in double angular brackets, such as <<I am>> <<at home>> <<with my>> <<cute dog>>."
Pass iff every word (G3) of the graded text is inside a `<<`…`>>` group and every group holds
exactly two words, except that one group may hold a single word when the response has an odd
number of words (D-bigram-odd). Punctuation inside or outside the groups does not matter.

### detectable_format:constrained_response
Text: "Answer with one of the following options: ('My answer is yes.', 'My answer is no.', 'My answer is maybe.')"
Pass iff the graded text, trimmed, is exactly one of the three options (D-constrained-extra: no
other text). Fail with extra text, two options, or none.

### detectable_format:json_format
Text: "Entire output should be wrapped in JSON format. You can use markdown ticks such as ```."
Pass iff the graded text, trimmed, after removing at most one enclosing markdown code fence
(` ``` ` or ` ```json `), is one valid JSON text (any JSON value, D-json-scalar) with nothing
outside the fence. Fail if any text lies outside the JSON, or the JSON does not parse.

### detectable_format:multiple_sections
Text: "Your response must have {num_sections} sections. Mark the beginning of each section with {section_spliter} X, such as: {section_spliter} 1 [content of section 1] {section_spliter} 2 [content of section 2]"
A marker is a line that starts (after optional whitespace and markdown heading or emphasis
markup) with {section_spliter}, in the given case (D-sections-case), followed by a space and a
section number. Pass iff there are exactly {num_sections} markers, numbered 1 to
{num_sections} in order (D-sections-number), each followed by non-empty content. Text before the
first marker (a title) is allowed (D-sections-preamble).

### detectable_format:number_bullet_lists
Text: "Your answer must contain exactly {num_bullets} bullet points. Use the markdown bullet points such as: * This is point 1. * This is point 2"
A bullet point is a line that starts, after optional indentation, with `*`, `-` or `+`, a space
and text (D-bullet-markers); a horizontal rule (`***`, `---`) or a bold line (`**x**`) is not.
Nested bullets count (D-bullet-nested). Numbered items do not. Pass iff there are exactly
{num_bullets}.

### detectable_format:number_highlighted_sections
Text: "Highlight at least {num_highlights} sections in your answer with markdown, i.e. *highlighted section*."
A highlighted section is an emphasis span `*text*` or `**text**` on one line with non-space
content (D-highlight-bold: bold counts). Pass iff there are at least {num_highlights} spans.

### detectable_format:sentence_hyphens
Text: "All sentences must be connected using hyphens, with no spaces between them."
Pass iff every boundary between consecutive sentences (G5) is a single `-` with no whitespace on
either side, so the text reads `First sentence.-Second sentence.-Third.` A response with one
sentence passes (D-hyphens-single). Fail if any two sentences are separated by whitespace
(including a line break) or joined by a hyphen with a space.

### detectable_format:square_brackets
Text: "Enclose every word in your response within square brackets."
Pass iff every word (G3) of the graded text lies inside a `[`…`]` pair that contains exactly
that one word (D-brackets-per-word); punctuation inside or outside the brackets does not matter.
Fail if any word is outside brackets or two words share one pair.

### detectable_format:title
Text: "Your answer must contain a title, wrapped in double angular brackets, such as <<poem of joy>>."
Pass iff the graded text contains a `<<`…`>>` span on one line with non-space content, anywhere
(D-title-position). Fail without one, or with empty `<<>>`.

### first_word:first_word_answer
Text: "The first word of your response should be the word {first_word}."
Pass iff the first word of the graded text (G6) equals {first_word} ignoring case
(D-keyword-case, D-first-last-markup).

### first_word:first_word_sent
Text: "The first word of each sentence should be the word {first_word}."
Pass iff every sentence (G5) of the graded text starts with the word {first_word} (ignoring case
and leading markup). Fail if any sentence starts with another word.

### keywords:existence
Text: "Include keywords {keywords} in the response." (the list is shown as a Python list)
Pass iff every keyword occurs at least once as a whole word (G4).

### keywords:forbidden_words
Text: "Do not include keywords {forbidden_words} in the response."
Fail iff any listed keyword occurs as a whole word (G4); words that merely contain it pass.

### keywords:frequency
Text: "In your response, the word {keyword} should appear {relation} {frequency} times."
Pass iff the whole-word count (G4) satisfies the relation (G7).

### keywords:keyword_specific_position
Text: "Include keyword {keyword} in the {n}-th sentence, as the {m}-th word of that sentence."
Pass iff the graded text has at least {n} sentences (G5) and the {m}-th word (G3, 1-based) of
the {n}-th sentence equals {keyword} ignoring case.

### keywords:letter_frequency
Text: "In your response, the letter {letter} should appear {let_relation} {let_frequency} times."
Count the occurrences of the letter in the graded text, ignoring case (D-letter-case); accented
letters are other letters. Pass iff the count satisfies the relation.

### keywords:no_adjacent_consecutive
Text: "No two adjacent words can start with consecutive letters of the alphabet."
For each pair of adjacent words (G3), across punctuation and line breaks, take their first
letters ignoring case. Fail iff some pair's first letters are consecutive in a-z, in either order
(`a b` and `b a`, D-consecutive-order). Words that start with a digit or a non-Latin letter take
part in no pair.

### keywords:palindrome
Text: "Include a palindrome in your response."
Pass iff the graded text contains a word, or a sequence of whole words, whose letters and digits
(ignoring case, spaces and punctuation) read the same backwards and number at least 3
(D-palindrome-min). Single letters and two-letter words do not count.

### keywords:start_end
Text: "Start and end your response with the same word (do not write anything after the last word, not even punctuation)."
Pass iff the graded text (trimmed) ends with a word character, so nothing but whitespace follows
the last word, and its first word (leading punctuation or markup ignored, D-start-markup) equals
its last word ignoring case. A one-word response passes (D-start-end-single [v2]). Fail on any
trailing punctuation or markup, or different words.

### keywords:word_count_different_numbers
Text: "In your response, the word {keyword} should appear {frequency} times."
(The prompt shows no relation; the row's `relation` kwarg is not in the text.)
Pass iff the whole-word count (G4) equals {frequency} (D-appear-n-times: "appear N times" means
exactly N).

### keywords:word_once
Text: "Include keyword {keyword} in your response."
Pass iff {keyword} occurs at least once as a whole word (G4). Occurring more than once still
passes ("include").

### language:response_language
Text: "Your ENTIRE response should be in {Language} language, no other language is allowed."
Pass iff all prose of the graded text is in {Language}; numbers, code, URLs, proper nouns and
brand names are allowed (D-language-mixed). Fail if any sentence or phrase is in another language.

### last_word:last_word_answer
Text: "The last word of your response should be the word {last_word}."
Pass iff the last word of the graded text (G6) equals {last_word} ignoring case.

### last_word:last_word_sent
Text: "The last word of each sentence, before punctuation, should be the word {last_word}."
Pass iff every sentence (G5) ends, before its punctuation, with the word {last_word} ignoring case.

### length_constraints:nth_paragraph_first_word
Text: "There should be {num_paragraphs} paragraphs. Paragraphs and only paragraphs are separated with each other by two new lines as if it was '\n\n' in python. Paragraph {nth_paragraph} must start with word {first_word}."
Paragraphs are the non-empty parts of the graded text between separators; a separator is a run
of two or more line breaks with only whitespace between them (D-paragraph-blank). Pass iff there
are exactly {num_paragraphs} paragraphs and paragraph {nth_paragraph} starts with the word
{first_word} (G6, ignoring case). When {nth_paragraph} > {num_paragraphs} (77 constraints) no
response can pass.

### length_constraints:number_paragraphs
Text: "There should be {num_paragraphs} paragraphs. Paragraphs are separated with the markdown divider: ***"
A divider is a line consisting of `***` and optional surrounding whitespace (D-divider-line);
`* * *`, `---` and `****` are not dividers. Pass iff the graded text, split at dividers, has
exactly {num_paragraphs} parts, each with a word. With one paragraph, no divider may appear.

### length_constraints:number_sentences
Text: "Your response should contain {relation} {num_sentences} sentences."
Pass iff the number of sentences (G5) satisfies the relation (G7).

### length_constraints:number_words
Text: "Answer with {relation} {num_words} words."
Pass iff the number of words (G3, D-word-cjk) satisfies the relation (G7).

### letters:letter_counting
Text: "Answer with {relation} {N} letters."
Count the letters (Unicode alphabetic characters) in the graded text (D-letter-unit: letters,
not words). Pass iff the count satisfies the relation (G7).

### letters:letter_counting2
Text: "In your response, the letter {letter} should appear {let_relation} {let_frequency} times."
Same contract as keywords:letter_frequency.

### paragraphs:paragraphs
Text: "There should be 2 paragraphs. Paragraphs are separated with the markdown divider: ***"
Same contract as length_constraints:number_paragraphs with 2 paragraphs.

### paragraphs:paragraphs2
Text: "There should be 2 paragraphs. Paragraphs and only paragraphs are separated with each other by two line breaks."
Paragraphs as in nth_paragraph_first_word (D-paragraph-blank). Pass iff there are exactly 2.

### punctuation:no_comma
Text: "In your entire response, refrain from the use of any commas."
Fail iff the graded text contains a comma: `,` or another comma character (`，` U+FF0C, `、`
U+3001, `،` U+060C, D-comma-variants).

### punctuation:punctuation_dot
Text: "In your entire response, refrain from the use of . (i.e. dots) as punctuation and in general."
Fail iff the graded text contains `.` anywhere (numbers, URLs, abbreviations included), or the
dot characters `．` U+FF0E and `…` U+2026 (D-dot-variants; `。` U+3002 is a full stop, not a dot,
and does not fail).

### punctuation:punctuation_exclamation
Text: "In your entire response, refrain from the use of ! (i.e. exclamation marks) as punctuation and in general."
Fail iff the graded text contains `!` anywhere, or `！` U+FF01, `¡` U+00A1, `‼` U+203C
(D-exclamation-variants).

### startend:end_checker
Text: "Finish your response with this exact phrase {end_phrase}. No other words should follow this phrase."
Pass iff the graded text, trimmed, ends with {end_phrase} in its exact case (D-end-case [v2]),
preceded by a non-word character or the start of the text (so `Many other questions?` does not
end with `Any other questions?`), and nothing follows it except characters that are not letters
or digits, such as closing markdown emphasis or a closing quote (D-end-trailing). Fail if any
word follows the phrase or the phrase differs.

### startend:quotation
Text: "Wrap your entire response with double quotation marks."
Pass iff the graded text, trimmed, is at least two characters long, starts with a double
quotation mark and ends with one: `"…"` or `“…”` (D-quote-curly).

## Decision entries

Each entry names both readings and the proposed one (first, in bold). Examples become fixtures in
step 3.

| Entry | Proposed reading | Other reading | Example |
|---|---|---|---|
| D-think-nonthinking | **A non-thinking model's answer is graded whole; only a leading `<think>` block is reasoning** | Any `<think>` makes the answer an extraction failure, or `<think>` is just text | `Use the <think> tag like this.` |
| D-word | **`don't`, `well-known` are one word** | Split at `'` and `-` | `don't` = 1 vs 2 words |
| D-word-cjk | **each Han/kana character is a word** | a run without spaces is one word | `我爱你` = 3 vs 1 |
| D-keyword-case | **case-insensitive** | case-sensitive | keyword `limit`, text `Limit` |
| D-keyword-substring | **whole words only** | substring | forbidden `sound`, text `soundtrack` |
| D-sentence-lines | **a line without terminal punctuation is its own sentence** | only `.!?` end sentences | `# Title` then `Body text.` = 2 vs 1 |
| D-first-last-markup | **ignore markdown markup and quotes around the first/last word** [v2] | the first/last token must be the word itself | `**Development** is…` |
| D-allcaps-short | **one-letter `I`, `A` count as all-caps words** | only words of two or more letters | `I like NASA.` = 2 vs 1 |
| D-case-scope | **every cased letter counts, in code and URLs too** | code and URLs exempt | lowercase rule, `Use print()` vs `use PRINT` |
| D-english-mixed | **English prose with proper nouns, code or a quoted foreign word passes** | any non-English token fails | `THE WORD "BONJOUR" MEANS HELLO.` |
| D-two-sep | **exactly one run of exactly 6 `*`** | a run of 6 or more | `A\n*******\nB` |
| D-two-different | **different = not identical after trimming** | substantially different | `Yes.` / `Yes!` |
| D-repeat-center | **any word but the first and last** | only the middle word(s) | phrase of 6 words, 2nd word replaced |
| D-repeat-copies | **unchanged copies neither count nor fail** | they count toward N, or they fail | original quoted once plus N variants |
| D-unique-case | **`The` and `the` are the same word** | case-sensitive | `The cat saw the dog` |
| D-lowercase-scope | **each lowercase word at most N times** | total lowercase words at most N | N=2, `a b c` |
| D-placeholder | **any non-empty `[…]` counts** | only placeholder-like names | `[1]`, `[link](url)` |
| D-postscript-case [v2] | **marker matched ignoring case** | exact case | marker `P.S.`, text `p.s. …` |
| D-postscript-dot [v2] | **the marker's final dot is optional** | the dot is required (only where the prompt shows it) | marker `P.S.`, text `P.S: …` |
| D-postscript-end | **the postscript is in the last block** | the marker may appear anywhere at a line start | `P.S. …` then a further paragraph |
| D-bigram-odd | **one single-word group allowed when the word count is odd** | every group exactly two words | `<<I am>> <<home>>` |
| D-constrained-extra | **exactly one option, nothing else** | contains an option | `My answer is yes. Because…` |
| D-json-scalar | **any JSON value** | object or array only | `"hello"` |
| D-sections-case | **marker word in the given case** | case-insensitive | spliter `SECTION`, text `Section 1` |
| D-sections-number | **numbered 1..N in order** | any `SECTION` marker counts | `SECTION 1`, `SECTION 3` |
| D-sections-preamble | **a title before `SECTION 1` is allowed** | the response must start with the first marker | `Plan\nSECTION 1\n…` |
| D-bullet-markers | **`*`, `-`, `+` bullets count** | only `*` | `- a\n- b` |
| D-bullet-nested | **nested bullets count** | only top-level | `* a\n  * b` = 2 vs 1 |
| D-highlight-bold | **`**bold**` counts as a highlight** | only `*italic*` | `**Key**` |
| D-hyphens-single | **one sentence passes** | at least two sentences needed | `Hello world.` |
| D-brackets-per-word | **each word in its own brackets** | words anywhere inside brackets | `[Hello world]` |
| D-title-position | **a title anywhere** | first line only | `Intro text. <<Title>>` |
| D-palindrome-min | **at least 3 letters/digits** | any length, single letters count | `I saw a cat.` |
| D-consecutive-order | **both orders** | ascending only (`a` then `b`) | `big apple` (b, a) |
| D-start-markup | **leading markup or punctuation before the first word ignored** | the response must begin with the word | `"Hello there hello` |
| D-appear-n-times | **"appear N times" = exactly N** | at least N | N=2, word appears 3 times |
| D-letter-case | **letter counts ignore case** | case-sensitive | letter `p`, text `Paper` = 2 vs 1 |
| D-letter-unit | **letters = alphabetic characters** | words | `Hi` = 2 letters |
| D-language-mixed | **numbers, code, names allowed** | any foreign token fails | Spanish answer quoting `Python` |
| D-paragraph-blank | **two or more line breaks (blank-only lines) = one separator** | exactly `\n\n` | `A\n\n\nB` = 2 vs 3 parts |
| D-divider-line | **`***` on its own line** | `***` anywhere | `***bold italic***` |
| D-comma-variants | **full-width, ideographic, Arabic commas count** | only `,` | `你好，世界` |
| D-dot-variants | **`．` and `…` count; `。` does not** | only `.` | `Wait…` |
| D-exclamation-variants | **`！`, `¡`, `‼` count** | only `!` | `¡Hola` |
| D-end-trailing | **closing markup/quotes without letters may follow** | only whitespace | `**Any other questions?**` |
| D-quote-curly | **curly quotes accepted** | straight only | `“Hello”` |
| D-end-case [v2] | **the end phrase in its exact case** | case-insensitive | `any other questions?` |
| D-start-end-single [v2] | **a one-word response passes keywords:start_end** | two words needed | `Hello` |
