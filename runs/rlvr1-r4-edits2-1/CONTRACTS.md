# Contracts for the 47 instruction checks of the RLVR1 instruction-following rows

Written from the instruction texts that the model sees (extracted from the prompts by
`audit/scripts/extract_templates.py`; placeholders in braces are the row's kwargs) before any grader
code was read. Each contract gives the pass condition; a response that does not meet it fails.
`D-<topic>` names a decision entry: the text allows two verdicts, and the contract states the proposed
reading. Decision entries are listed at the end with both readings and an example of each.

## 0. Common definitions

- **Graded text (G).** The model's visible answer. For a reasoning model, G is the text after the last
  `</think>`; a separate reasoning field is never graded. A response that opens reasoning and never closes
  it (`<think>` without a later `</think>`, or, for a template that opens `<think>` in the prompt, no
  `</think>` at all) is an extraction failure: it fails every check and is counted separately. For a
  non-reasoning model, G is the whole generated text. Proposed (D-surrounding-whitespace): leading and
  trailing whitespace of G is ignored by every check.
- **Empty response.** Proposed (D-empty-response): a G that is empty or whitespace-only fails every check.
- **Word.** A maximal run of letters and digits (any script), with internal apostrophes (`'` or `’`)
  kept inside the word (D-word-apostrophe) and internal hyphens joining one word (D-word-hyphen).
  Markdown markup (`*`, `_`, `` ` ``, `#`, `>`), quotation marks, brackets and punctuation next to a word
  are not part of it.
- **Word comparison.** Comparing a word with a given word (first word, last word, keyword, start/end) is
  case-insensitive (D-word-case) and whole-word: a keyword does not match inside a longer word
  (D-keyword-substring), and an inflected form (`gardens` for `garden`) is not the word (D-keyword-inflection).
  A multi-word keyword matches the same words in sequence.
- **Sentence.** A sentence ends at a run of `.`, `!` or `?` (or `。！？`) followed by whitespace or the end
  of G, and also at a line break (D-sentence-linebreak). A period inside a number (`3.5`) or a common
  abbreviation (`e.g.`, `Dr.`, `U.S.`) does not end a sentence (D-sentence-abbreviation). A sentence must
  contain at least one word; lines of only markup (`***`, `---`) are not sentences.
- **Paragraph (blank-line form).** Paragraphs are the non-empty pieces of G between blank lines (one or
  more lines containing only whitespace); a single line break does not separate paragraphs.
- **Relations.** "less than N" means count < N; "at least N" means count >= N; "at most N" means count <= N;
  "exactly N" means count = N.

## 1. Contracts

Each heading is the instruction id, then the instruction text as the model sees it.

### change_case:capital_word_frequency
"In your response, words with all capital letters should appear {capital_relation} {capital_frequency} times."
Pass: the number of word occurrences in G whose letters are all uppercase (at least one letter, no lowercase
letter) satisfies the relation. Every occurrence counts. One-letter words such as `I` and `A` count
(D-allcaps-short-words). A word with digits counts if its letters are uppercase (`COVID19`).

### change_case:english_capital
"Your entire response should be in English, and in all capital letters."
Pass: G contains no lowercase letter (in any script) and its natural-language text is English (proper
nouns, numbers, code identifiers and quoted foreign names do not make it non-English; D-english-detection).

### change_case:english_lowercase
"Your entire response should be in English, and in all lowercase letters. No capital letters are allowed."
Pass: G contains no uppercase letter (in any script) and is English as above.

### combination:two_responses
"Give two different responses. Responses and only responses should be separated by 6 asterisk symbols: ******."
Pass: G contains exactly one run of exactly six asterisks `******` used as the separator (a longer run of
asterisks is not the separator), the text before and the text after it are both non-empty after trimming
whitespace, and the two parts differ after trimming whitespace (D-two-responses-different). No other
six-asterisk run occurs.

### copy:repeat_phrase
"Repeat the phrase {phrase} exactly {small_n} times, transforming it slightly each time by replacing only one word in the center of the phrase."
Pass: G contains exactly `small_n` occurrences of transformed copies of the phrase, where a transformed copy
is the phrase with exactly one word other than its first and last word replaced by one different word
(D-repeat-center), compared case-insensitively, and G contains no verbatim copy of the phrase
(D-repeat-verbatim). The copies need not differ from each other.

### count:count_unique
"Only use unique words in your response, no word should be repeated!"
Pass: no word occurs twice in G, compared case-insensitively (D-word-case).

### count:counting_composition
"Write {3} paragraphs, delimited by the markdown divider: * * *, with exactly {n_sent} sentences each, with exactly {n_words} words in each sentence."
Pass: G split at lines that are the divider `* * *` gives exactly 3 non-empty paragraphs; each has exactly
`n_sent` sentences; each sentence has exactly `n_words` words.

### count:lowercase_counting
"In your response, all lowercase words should appear at most {N} times."
Pass: every distinct word written in all-lowercase letters occurs at most N times in G, counting only its
all-lowercase occurrences (D-lowercase-counting-scope: per word, not the total number of lowercase words).

### detectable_content:number_placeholders
"The response must contain at least {num_placeholders} placeholders represented by square brackets, such as [address]."
Pass: G contains at least `num_placeholders` occurrences of `[text]`, where text is non-empty, not only
whitespace, and contains no bracket or line break (D-placeholder-content). Markdown link text `[x](url)` and
citation marks `[1]` count as bracketed spans under this reading.

### detectable_content:postscript
"At the end of your response, please explicitly add a postscript starting with {postscript_marker}"
Pass: some line of G starts (after optional markdown emphasis or heading marks, D-markup-around-marker) with
the marker as written (`P.S.` or `P.P.S`, case-sensitive; `P.P.S.` starts with `P.P.S`), and that
postscript is the last part of G: no line after it starts a non-postscript part (D-postscript-position;
the postscript may span several lines up to the end).

### detectable_format:bigram_wrapping
"Wrap every word bigram in double angular brackets, such as <<I am>> <<at home>> <<with my>> <<cute dog>>."
Pass: every word of G is inside a `<<...>>` group, and every group holds exactly two words; punctuation
and whitespace may sit between groups. With an odd number of words, one group may hold the single last
word (D-bigram-odd).

### detectable_format:constrained_response
"Answer with one of the following options: ('My answer is yes.', 'My answer is no.', 'My answer is maybe.')"
Pass: G (trimmed) is exactly one of the three options (D-constrained-exact). A G that contains two different
options fails under every reading.

### detectable_format:json_format
"Entire output should be wrapped in JSON format. You can use markdown ticks such as ```."
Pass: G (trimmed), after removing one optional enclosing markdown code fence (```` ``` ```` or
```` ```json ````), parses as JSON, and the value is an object or an array (D-json-scalar). Text outside the
fence fails.

### detectable_format:multiple_sections
"Your response must have {num_sections} sections. Mark the beginning of each section with {section_spliter} X, such as:\n{section_spliter} 1\n[content of section 1]\n{section_spliter} 2\n[content of section 2]"
Pass: G has exactly `num_sections` marker lines, each starting (after optional markdown heading or emphasis
marks, D-markup-around-marker) with the splitter word exactly as given (case-sensitive,
D-section-marker-case) followed by a space and the section number; the numbers are 1..N in order
(D-section-numbering); each section has non-empty content. Text before the first marker is allowed and is
not a section (D-section-preamble).

### detectable_format:number_bullet_lists
"Your answer must contain exactly {num_bullets} bullet points. Use the markdown bullet points such as:\n* This is point 1. \n* This is point 2"
Pass: G has exactly `num_bullets` bullet lines. A bullet line starts, after optional indentation, with `*`,
`-` or `+` followed by a space and text (D-bullet-markers); indented sub-bullets count (D-bullet-nesting).
A line starting with `**` (bold), an italic span `*x*`, a horizontal rule (`***`, `---`) or a numbered label
(`1.`) is not a bullet line.

### detectable_format:number_highlighted_sections
"Highlight at least {num_highlights} sections in your answer with markdown, i.e. *highlighted section*."
Pass: G contains at least `num_highlights` highlighted spans: `*text*` with single asterisks and non-empty,
non-whitespace text on one line. A bold span `**text**` also counts once (D-highlight-bold).

### detectable_format:sentence_hyphens
"All sentences must be connected using hyphens, with no spaces between them."
Pass: between every two consecutive sentences of G there is a hyphen `-` with no whitespace on either side
of it (`First one.-Second one.-Third.`); no whitespace or line break separates two sentences. A G with one
sentence passes (D-sentence-hyphens-single).

### detectable_format:square_brackets
"Enclose every word in your response within square brackets."
Pass: every word of G is enclosed in its own pair of square brackets, `[word]`; punctuation may sit outside
the brackets (D-square-brackets-grouping).

### detectable_format:title
"Your answer must contain a title, wrapped in double angular brackets, such as <<poem of joy>>."
Pass: G contains at least one `<<text>>` with non-empty, non-whitespace text on one line, at any position
(D-title-position).

### first_word:first_word_answer
"The first word of your response should be the word {first_word}."
Pass: the first word of G equals `first_word` (word comparison rules; leading markup or quotation marks are
not part of the word).

### first_word:first_word_sent
"The first word of each sentence should be the word {first_word}."
Pass: G has at least one sentence, and the first word of every sentence equals `first_word`.

### keywords:existence
"Include keywords {keywords} in the response."
Pass: every keyword of the list occurs in G (word comparison rules).

### keywords:forbidden_words
"Do not include keywords {forbidden_words} in the response."
Pass: no keyword of the list occurs in G (word comparison rules; `lawyer` does not contain the keyword
`law`, D-keyword-substring).

### keywords:frequency
"In your response, the word {keyword} should appear {relation} {frequency} times."
Pass: the number of occurrences of `keyword` in G (word comparison rules) satisfies the relation.

### keywords:keyword_specific_position
"Include keyword {keyword} in the {n}-th sentence, as the {m}-th word of that sentence."
Pass: G has at least n sentences, and the m-th word of the n-th sentence equals `keyword`.

### keywords:letter_frequency
"In your response, the letter {letter} should appear {let_relation} {let_frequency} times."
Pass: the number of occurrences of the letter in G, counting both cases (D-letter-case) and not counting
accented forms (`é` is not `e`), satisfies the relation.

### keywords:no_adjacent_consecutive
"No two adjacent words can start with consecutive letters of the alphabet."
Pass: for every two adjacent words of G (adjacent in the word sequence, across punctuation and line breaks,
D-adjacent-scope), whose first characters are both Latin letters a-z, the first letters (case-insensitive)
are not neighbours in the alphabet, in either order (`b`,`c` and `c`,`b` both violate; D-consecutive-order).

### keywords:palindrome
"Include a palindrome in your response."
Pass: G contains a word of at least three letters that reads the same backward, case-insensitively
(`level`, `Anna`), or a multi-word palindrome ignoring spaces and punctuation (D-palindrome-length: one- and
two-letter words do not count).

### keywords:start_end
"Start and end your response with the same word (do not write anything after the last word, not even punctuation)."
Pass: the first word and the last word of G are the same word (case-insensitive), G has at least two words
(D-start-end-single), and the last character of G (trimmed) is the last character of that word: no
punctuation or markup follows it. Leading markup before the first word is allowed (D-markup-around-word).

### keywords:word_count_different_numbers
"In your response, the word {keyword} should appear {frequency} times."
Pass: `keyword` occurs exactly `frequency` times in G (word comparison rules; D-wcdn-relation: "should appear
N times" read as exactly N). The row's `relation` kwarg is not in the text the model sees.

### keywords:word_once
"Include keyword {keyword} in your response."
Pass: `keyword` occurs at least once in G (word comparison rules). Occurring more than once still passes.

### language:response_language
"Your ENTIRE response should be in {language name} language, no other language is allowed."
Pass: the natural-language text of G is in the named language; proper nouns, numbers, code and quoted
names in other scripts do not make it fail (D-english-detection applies the same way).

### last_word:last_word_answer
"The last word of your response should be the word {last_word}."
Pass: the last word of G equals `last_word` (trailing punctuation and markup are not part of the word).

### last_word:last_word_sent
"The last word of each sentence, before punctuation, should be the word {last_word}."
Pass: G has at least one sentence, and the last word of every sentence equals `last_word`.

### length_constraints:nth_paragraph_first_word
"There should be {num_paragraphs} paragraphs. Paragraphs and only paragraphs are separated with each other by two new lines as if it was '\n\n' in python. Paragraph {nth_paragraph} must start with word {first_word}."
Pass: G has exactly `num_paragraphs` paragraphs (blank-line form), and the first word of paragraph
`nth_paragraph` equals `first_word`. When `nth_paragraph` > `num_paragraphs`, no response can pass.

### length_constraints:number_paragraphs
"There should be {num_paragraphs} paragraphs. Paragraphs are separated with the markdown divider: ***"
Pass: G split at divider lines (a line that is `***` after trimming whitespace, D-divider-line) gives exactly
`num_paragraphs` pieces, each non-empty after trimming (an empty piece fails, D-paragraph-empty-piece).

### length_constraints:number_sentences
"Your response should contain {relation} {num_sentences} sentences."
Pass: the number of sentences in G satisfies the relation.

### length_constraints:number_words
"Answer with {relation} {num_words} words."
Pass: the number of words in G satisfies the relation.

### letters:letter_counting
"Answer with {relation} {N} letters."
Pass: the number of letters (alphabetic characters, any script) in G satisfies the relation
(D-letter-counting-unit: letters are characters, not words).

### letters:letter_counting2
"In your response, the letter {letter} should appear {let_relation} {let_frequency} times."
Same contract as keywords:letter_frequency.

### paragraphs:paragraphs
"There should be 2 paragraphs. Paragraphs are separated with the markdown divider: ***"
Same contract as length_constraints:number_paragraphs with 2 paragraphs.

### paragraphs:paragraphs2
"There should be 2 paragraphs. Paragraphs and only paragraphs are separated with each other by two line breaks."
Pass: G has exactly 2 paragraphs (blank-line form).

### punctuation:no_comma
"In your entire response, refrain from the use of any commas."
Pass: G contains no comma character: `,` and its other forms `，` (full-width), `、` (ideographic), `،`
(Arabic) (D-comma-variants).

### punctuation:punctuation_dot
"In your entire response, refrain from the use of . (i.e. dots) as punctuation and in general."
Pass: G contains no `.` anywhere (in numbers, URLs, ellipses and abbreviations too), and no other full-stop
form `．` `。` or ellipsis character `…` (D-dot-variants).

### punctuation:punctuation_exclamation
"In your entire response, refrain from the use of ! (i.e. exclamation marks) as punctuation and in general."
Pass: G contains no `!`, and no other exclamation form `！` `¡` `‼` (D-exclamation-variants).

### startend:end_checker
"Finish your response with this exact phrase {end_phrase}. No other words should follow this phrase."
Pass: G (trimmed) ends with the phrase exactly as written (case-sensitive); nothing but whitespace follows
it (D-end-trailing-nonwords: markup or punctuation after the phrase fails).

### startend:quotation
"Wrap your entire response with double quotation marks."
Pass: G (trimmed) is at least two characters long, starts with a double quotation mark and ends with one;
`"` and the typographic pair `“ ”` count (D-typographic-quotes).

## 2. Decision entries (proposed reading first)

| Entry | Proposed reading (example) | Other reading (example) |
|---|---|---|
| D-surrounding-whitespace | leading/trailing whitespace of G is ignored (`"x"\n` passes quotation) | whitespace counts as content (`"x"\n` fails) |
| D-empty-response | empty G fails every check | literal: empty G passes negative checks (no commas, forbidden words, at most N, less than N) |
| D-word-apostrophe | `don't` is one word | `don` and `t` are two words |
| D-word-hyphen | `well-known` is one word | two words |
| D-word-case | `Peace` equals `peace` | case must match |
| D-keyword-substring | keyword `law` not in `lawyer` | substring match: `lawyer` contains `law` |
| D-keyword-inflection | `gardens` is not `garden` | inflected forms count |
| D-sentence-linebreak | a line break ends a sentence (a heading line is a sentence) | only `.!?` end sentences |
| D-sentence-abbreviation | `Dr.` and `3.5` do not end a sentence | every `.` + space ends one |
| D-allcaps-short-words | `I` and `A` count as all-capital words | one-letter words do not count |
| D-english-detection | proper nouns, code and numbers allowed inside English text | any non-English token fails |
| D-two-responses-different | parts must differ after trimming | any two parts, even identical |
| D-repeat-center | any word but the first and last may be replaced | only the middle word(s) |
| D-repeat-verbatim | a verbatim copy fails | verbatim copies are ignored |
| D-lowercase-counting-scope | each lowercase word at most N times | total lowercase words at most N |
| D-placeholder-content | any non-empty `[text]` counts, including `[1]` | only placeholder-like names (`[address]`) |
| D-markup-around-marker | `**P.S.**`, `## SECTION 1` count as markers | marker must be the first characters of the line |
| D-postscript-position | postscript is the final part | marker anywhere |
| D-bigram-odd | a final single-word group is allowed for odd counts | every group exactly two words |
| D-constrained-exact | G is exactly one option | G contains one option among other text |
| D-json-scalar | object or array only | any JSON value (`"hi"`, `3`) |
| D-section-marker-case | `SECTION` and `Section` are different markers | case-insensitive |
| D-section-numbering | numbers 1..N in order | any numbers |
| D-section-preamble | text before SECTION 1 is allowed | a preamble counts as an extra section or fails |
| D-bullet-markers | `*`, `-`, `+` bullets count | only `*` |
| D-bullet-nesting | indented sub-bullets count | only top-level bullets count |
| D-highlight-bold | `**bold**` counts once | only single-asterisk `*x*` |
| D-sentence-hyphens-single | one sentence passes | at least two sentences needed |
| D-square-brackets-grouping | each word in its own brackets | one pair around many words is enough |
| D-title-position | `<<title>>` anywhere | must be the first line |
| D-letter-case | `S` counts as letter `s` | case-sensitive |
| D-adjacent-scope | adjacency crosses punctuation and line breaks | only words in the same sentence/clause |
| D-consecutive-order | `c b` violates as `b c` does | only ascending pairs violate |
| D-palindrome-length | at least three letters | any palindrome word, `a`, `I`, `aa` |
| D-start-end-single | at least two words | a one-word G starts and ends with the same word |
| D-markup-around-word | leading `**`/quotes before the first word ignored | any character before the first word fails |
| D-wcdn-relation | "should appear N times" = exactly N | at least N |
| D-divider-line | `***` divider must be on its own line | `***` anywhere splits |
| D-paragraph-empty-piece | empty pieces fail | empty pieces are ignored |
| D-letter-counting-unit | letters = alphabetic characters | letters = words |
| D-comma-variants | `，`, `、`, `،` are commas | only ASCII `,` |
| D-dot-variants | `．`, `。`, `…` are dots | only ASCII `.` |
| D-exclamation-variants | `！`, `¡`, `‼` are exclamation marks | only ASCII `!` |
| D-end-trailing-nonwords | nothing but whitespace after the phrase | punctuation/markup (not words) may follow |
| D-typographic-quotes | `“ ”` count | only ASCII `"` |

## 3. Contract changes after v1 (each with its reason)

C1 (2026-11-11T09:58Z). startend:end_checker, D-end-trailing-nonwords: the proposal becomes the literal
reading, "non-word characters (closing quotation marks, punctuation, markup) may follow the phrase; no word
may". Reason: the text says "No other words should follow this phrase", and 20 rows combine it with
startend:quotation ("Wrap your entire response with double quotation marks"), which the v1 proposal made
unsatisfiable. The other reading (only whitespace may follow) stays in the table.

C2 (2026-11-11T09:58Z). New decision entries for terms v1 left undefined, found while reading code; the
contract's existing wording is the proposal:
| Entry | Proposed reading (example) | Other reading (example) |
|---|---|---|
| D-postscript-case | marker case as written (`p.s.` does not start a `P.S.` postscript) | case-insensitive |
| D-end-case | "exact phrase" is case-sensitive (`any other questions?` fails) | case-insensitive |
| D-palindrome-case | case-insensitive (`Level` is a palindrome) | case-sensitive |
| D-blank-line-whitespace | a line of only spaces is a blank line between paragraphs | only `\n\n` exactly separates |
| D-paragraph-separator-count | three or more newlines still separate two paragraphs | more than two newlines make an empty paragraph or break the rule |
| D-sentence-hyphens-spaces | spaces inside a sentence are allowed; none between sentences | no spaces anywhere (words joined by hyphens) |
| D-letter-script | letters of any script count for letters:letter_counting | only Latin a-z |
| D-adjacent-alphabet | only Latin a-z first letters are checked | consecutive letters of any alphabet (Cyrillic а,б) |

C3 (2026-11-11T10:18Z, prompted by the panel; the replacement was changed accordingly). Panel cases showed
four terms the v1 text left undefined; the contract's existing wording is the proposal:
| Entry | Proposed reading (example) | Other reading (example) |
|---|---|---|
| D-postscript-line-start | the marker starts a line (`Main text.\nP.S. note`) | the marker may follow text on its line (`Main text. P.S. note`) |
| D-section-line-start | a section marker starts a line | a marker may stand mid-line (`SECTION 1 intro. SECTION 2 end.`) |
| D-two-responses-extra-separator | separators only between the two responses (`******` before the first one fails) | a leading or trailing separator is ignored |
| D-sentence-hyphens-dash | a dash with a space beside it (`It rains - we stay in`) joins sentences with a space and fails | only terminal punctuation marks sentences, so that text is one sentence and passes |
Clarifications of the v1 wording, not new readings: a CJK full stop (`。！？`) ends a sentence even without a
following space (section 0 already lists them); markdown emphasis after terminal punctuation (`done.*`)
still ends the sentence; quotation marks before a marker (`"SECTION 1`, as when the whole response is
quoted) count as markup for D-markup-around-marker.
