# Contracts for the 47 instruction ids of RLVR1 instruction following

Written from the instruction texts that the model sees in the prompts
(`audit/scripts/instruction_texts.py` locates the text of all 28,219
constraints; every one matches the template below), before any grader code was
read. Each contract states pass and fail conditions. `{x}` is a kwarg value as
the prompt shows it. A decision entry `D-<topic>` marks a term that the text
leaves open; the contract follows the proposed reading (A) and the decision
table at the end gives both readings.

## 0. Common definitions

- **Graded text.** The whole visible answer. For a reasoning model, the text
  after the last `</think>`; never a separate reasoning field. A response whose
  reasoning never closes (Qwen3-4B-Thinking-2507: no `</think>` in the raw
  response, because the chat template opens `<think>` in the prompt) is an
  extraction failure: it fails every constraint, and the report counts these
  responses separately.
- **Outer whitespace** (D-outer-whitespace): leading and trailing whitespace of
  the graded text is ignored by every check.
- **Empty graded text** (D-empty): a constraint that only forbids something
  (a character, a word, more than N of something) passes; a constraint that
  requires something fails. Content-free passes are reported separately.
- **Word** (D-word): a maximal run of letters, digits and combining marks,
  where an apostrophe or a hyphen between two such runs stays inside the word
  (`don't`, `well-known` are one word each). Each CJK ideograph, kana or hangul
  syllable outside a space-separated run counts as one word. Punctuation-only
  and markup-only tokens (`-`, `**`, `#`, `1.` minus the digit) are not words;
  a number is a word.
- **Sentence** (D-sentence): a span that ends at terminal punctuation
  (`.`, `!`, `?`, `…`, `。`, `！`, `？`) followed by whitespace, a closing
  quote/bracket or the end of the text, not counting abbreviations
  (`e.g.`, `Dr.`, `U.S.`), decimal points or list numbers (`1.`). A non-empty
  line that ends without terminal punctuation (a heading, a list item, a title)
  is also a sentence. A sentence contains at least one word.
- **Keyword match** (D-keyword-match): case-insensitive, whole word (the
  keyword is not preceded or followed by a letter or digit), exact form (no
  inflections).
- **Relations**: `at least N` means count >= N; `less than N` means count < N;
  `at most N` means count <= N; `exactly N` means count == N.
- **Letter**: a Unicode alphabetic character. "The letter t" counts `t` and
  `T` (D-letter-case).

## 1. Contracts

### change_case:capital_word_frequency
Text: "In your response, words with all capital letters should appear {at least|less than} {N} times."
Count the words (D-word) that contain at least one letter and whose letters are
all uppercase, including one-letter words such as `I` and `A`
(D-capital-word). Every occurrence counts. Pass iff count {relation} N.

### change_case:english_capital
Text: "Your entire response should be in English, and in all capital letters."
Pass iff (a) the natural-language text is English (D-english), and (b) no
character of the graded text is a lowercase letter (any script). Fail on any
lowercase letter, including inside code, URLs or names. Empty text fails (a).

### change_case:english_lowercase
Text: "Your entire response should be in English, and in all lowercase letters. No capital letters are allowed."
Pass iff (a) the text is English (D-english), and (b) no character is an
uppercase or titlecase letter (any script). Fail on any capital letter,
including `I`, names, acronyms, code. Empty text fails (a).

### combination:two_responses
Text: "Give two different responses. Responses and only responses should be separated by 6 asterisk symbols: ******"
Pass iff the graded text contains exactly one run of exactly six asterisks
`******` (a run of 7 or more asterisks is not the separator, and other
asterisk runs such as `**bold**` are not separators), the parts before and
after it are both non-empty after stripping whitespace, and the two parts are
not identical after stripping whitespace (D-two-responses-different).

### copy:repeat_phrase
Text: "Repeat the phrase {phrase} exactly {n} times, transforming it slightly each time by replacing only one word in the center of the phrase."
Phrases have 5 or 6 words. A transformed repetition is a word sequence of the
phrase's length (D-word; compared case-insensitively, punctuation ignored)
that equals the phrase except at exactly one center position, where it has a
different word. Center (D-repeat-center): for odd length L the word at
position (L+1)/2; for even length L either of positions L/2 and L/2+1.
Pass iff the response contains exactly n transformed repetitions and no
verbatim copy of the phrase (D-repeat-original).

### count:count_unique
Text: "Only use unique words in your response, no word should be repeated!"
Pass iff no word (D-word) occurs twice, comparing words case-insensitively
(D-unique-case). Empty text passes (D-empty).

### count:counting_composition
Text: "Write {P} paragraphs, delimited by the markdown divider: * * *, with exactly {n_sent} sentences each, with exactly {n_words} words in each sentence." (one row; P = 3 in the text, and no kwarg carries P)
Pass iff the text splits at divider lines `* * *` into exactly P non-empty
paragraphs, every paragraph has exactly n_sent sentences (D-sentence), and every
sentence has exactly n_words words (D-word).

### count:lowercase_counting
Text: "In your response, all lowercase words should appear at most {N} times."
A lowercase word is a word (D-word) with at least one letter and no uppercase
letter. Pass iff each distinct lowercase word occurs at most N times
(D-lowercase-counting-scope; occurrences with capitals, such as `The` for
`the`, do not count).

### detectable_content:number_placeholders
Text: "The response must contain at least {N} placeholders represented by square brackets, such as [address]."
A placeholder is a span `[...]` with at least one non-space character and no
bracket or line break inside, and not immediately followed by `(` (the text of
a markdown link) (D-placeholder). Every occurrence counts. Pass iff count >= N.

### detectable_content:postscript
Text: "At the end of your response, please explicitly add a postscript starting with {marker}" (kwarg `P.S.` or `P.P.S`; 186 prompts show `P.S.` as `P.S` because the trailing period was dropped when the requirements were joined)
Pass iff a line of the graded text begins, after optional whitespace and
markdown emphasis (`*`, `_`), with the marker, where the marker's final period
is optional and a colon may follow (D-postscript-marker, D-postscript-position).
Letters match case-sensitively. `P.P.S` does not satisfy `P.S.`, and `P.S.`
does not satisfy `P.P.S`.

### detectable_format:bigram_wrapping
Text: "Wrap every word bigram in double angular brackets, such as <<I am>> <<at home>> <<with my>> <<cute dog>>."
Pass iff the graded text contains at least one `<<...>>` unit, every word
(D-word) lies inside a `<<...>>` unit, and every unit contains exactly two
words (D-bigram: a final one-word unit fails). Punctuation may appear inside or
outside units.

### detectable_format:constrained_response
Text: "Answer with one of the following options: ('My answer is yes.', 'My answer is no.', 'My answer is maybe.')"
Pass iff the stripped graded text is exactly one of the three option strings
(D-constrained). Fail on extra text, a missing period, or two options.

### detectable_format:json_format
Text: "Entire output should be wrapped in JSON format. You can use markdown ticks such as ```."
Strip whitespace; if the text starts with a code fence (```` ``` ```` or
```` ```json ````) and ends with ```` ``` ````, remove that one fence. Pass iff
what remains parses as a JSON object or array (D-json). Text outside the fence
fails.

### detectable_format:multiple_sections
Text: "Your response must have {n} sections. Mark the beginning of each section with {SPLITTER} X, such as:\n{SPLITTER} 1\n[content of section 1]\n{SPLITTER} 2\n[content of section 2]" (SPLITTER is `SECTION` or `Section`)
A section marker is a line that begins, after optional whitespace and markdown
heading or emphasis characters (`#`, `*`, `_`), with SPLITTER exactly as given
(D-sections-case) followed by a space and a number. Pass iff there are exactly
n markers, numbered 1 to n in order (D-sections-numbering). Text before the
first marker is allowed (D-sections-preamble).

### detectable_format:number_bullet_lists
Text: "Your answer must contain exactly {n} bullet points. Use the markdown bullet points such as:\n* This is point 1. \n* This is point 2"
A bullet point is a line that starts, after optional indentation, with `*`,
`-` or `+`, a space, and non-empty text (D-bullets). Nested bullets count.
Numbered items, horizontal rules (`***`, `---`, `* * *`) and lines starting
with bold `**` are not bullets. Pass iff the count is exactly n.

### detectable_format:number_highlighted_sections
Text: "Highlight at least {N} sections in your answer with markdown, i.e. *highlighted section*."
A highlighted section is a markdown emphasis span on one line, `*text*` or
`**text**` (D-highlight), with non-space text inside. Each span counts once.
Pass iff count >= N.

### detectable_format:sentence_hyphens
Text: "All sentences must be connected using hyphens, with no spaces between them."
Split the graded text into sentences (D-sentence). Pass iff every two
consecutive sentences are joined by a hyphen `-` with no whitespace (spaces or
line breaks) between the first sentence's end, the hyphen and the next
sentence. A one-sentence response passes (D-hyphens-single). Spaces inside a
sentence are allowed.

### detectable_format:square_brackets
Text: "Enclose every word in your response within square brackets."
Pass iff every word (D-word) is enclosed in its own pair of square brackets,
`[word]` (D-square-brackets); punctuation may sit inside or outside the
brackets. Fail if any word is outside brackets or a bracket holds two words.

### detectable_format:title
Text: "Your answer must contain a title, wrapped in double angular brackets, such as <<poem of joy>>."
Pass iff the text contains a span `<<...>>` with non-space text on one line,
anywhere (D-title).

### first_word:first_word_answer
Text: "The first word of your response should be the word {w}."
The first word (D-word) of the graded text, skipping leading whitespace,
markdown and punctuation, equals w case-insensitively (D-first-last-word).

### first_word:first_word_sent
Text: "The first word of each sentence should be the word {w}."
Pass iff every sentence (D-sentence) starts with the word w (first word
case-insensitively, after leading markup and punctuation).

### keywords:existence
Text: "Include keywords {list} in the response."
Pass iff every keyword of the list occurs (D-keyword-match).

### keywords:forbidden_words
Text: "Do not include keywords {list} in the response."
Pass iff no keyword of the list occurs (D-keyword-match).

### keywords:frequency
Text: "In your response, the word {k} should appear {at least|less than} {N} times."
Count occurrences of k (D-keyword-match). Pass iff count {relation} N.

### keywords:keyword_specific_position
Text: "Include keyword {k} in the {n}-th sentence, as the {m}-th word of that sentence."
Pass iff the graded text has at least n sentences (D-sentence) and the m-th
word (D-word) of the n-th sentence equals k case-insensitively.

### keywords:letter_frequency
Text: "In your response, the letter {l} should appear {at least|less than} {N} times."
Count occurrences of l and its uppercase form (D-letter-case). Pass iff count
{relation} N.

### keywords:no_adjacent_consecutive
Text: "No two adjacent words can start with consecutive letters of the alphabet."
For every two adjacent words (D-word), take their first characters,
lowercased; if both are letters a-z and they are neighbours in the alphabet in
either order (D-consecutive-order), fail. Otherwise pass.

### keywords:palindrome
Text: "Include a palindrome in your response."
Pass iff the text contains a word of at least 3 letters that reads the same
backwards (case-insensitive), or a phrase of several words that does once
spaces and punctuation are removed, with at least 3 letters (D-palindrome).

### keywords:start_end
Text: "Start and end your response with the same word (do not write anything after the last word, not even punctuation)."
Pass iff the first word and the last word (D-word) are equal
case-insensitively (D-start-end-case), and the stripped graded text ends with
the last character of the last word (nothing after it, not even punctuation
or markdown). Leading markup or punctuation before the first word is allowed.

### keywords:word_count_different_numbers
Text: "In your response, the word {k} should appear {N} times." (the kwargs also hold a `relation`, `at least` in 320 and `less than` in 206 constraints, that the text does not show)
Count occurrences of k (D-keyword-match). Pass iff count == N (D-count-exact).
No reading of the text allows `less than N`.

### keywords:word_once
Text: "Include keyword {k} in your response."
Pass iff k occurs at least once (D-keyword-match). More occurrences pass.

### language:response_language
Text: "Your ENTIRE response should be in {Language} language, no other language is allowed."
Pass iff the natural-language text of the response is in the named language
(D-language): names, code, numbers and URLs do not count against it; a
sentence or more in another language fails.

### last_word:last_word_answer
Text: "The last word of your response should be the word {w}."
The last word (D-word) of the graded text, ignoring trailing whitespace,
punctuation and markdown, equals w case-insensitively (D-first-last-word).

### last_word:last_word_sent
Text: "The last word of each sentence, before punctuation, should be the word {w}."
Pass iff every sentence (D-sentence) ends with the word w (last word,
case-insensitive, before its punctuation).

### length_constraints:nth_paragraph_first_word
Text: "There should be {P} paragraphs. Paragraphs and only paragraphs are separated with each other by two new lines as if it was '\n\n' in python. Paragraph {i} must start with word {w}."
Paragraphs are the non-empty blocks separated by blank lines
(D-paragraph-blank). Pass iff there are exactly P paragraphs, i <= P, and the
first word of paragraph i (after leading markup and punctuation) equals w
case-insensitively. When i > P (77 of the 515 constraints), no response can
pass.

### length_constraints:number_paragraphs
Text: "There should be {P} paragraphs. Paragraphs are separated with the markdown divider: ***"
A divider is a line whose only content is `***` (D-divider). Pass iff the
text splits at dividers into exactly P parts and every part has non-space text.

### length_constraints:number_sentences
Text: "Your response should contain {at least|less than} {N} sentences."
Count sentences (D-sentence). Pass iff count {relation} N.

### length_constraints:number_words
Text: "Answer with {at least|less than} {N} words."
Count words (D-word). Pass iff count {relation} N.

### letters:letter_counting
Text: "Answer with {at least|less than} {N} letters." (N is 2 or 3)
Count letters (Unicode alphabetic characters, any script; D-letters-count).
Pass iff count {relation} N.

### letters:letter_counting2
Same text and contract as keywords:letter_frequency.

### paragraphs:paragraphs
Text: "There should be 2 paragraphs. Paragraphs are separated with the markdown divider: ***" (no kwargs; every prompt shows 2)
Same contract as length_constraints:number_paragraphs with P = 2.

### paragraphs:paragraphs2
Text: "There should be 2 paragraphs. Paragraphs and only paragraphs are separated with each other by two line breaks" (no kwargs; every prompt shows 2)
Pass iff the text has exactly 2 non-empty blocks separated by blank lines
(D-paragraph-blank). Single line breaks inside a paragraph are allowed.

### punctuation:no_comma
Text: "In your entire response, refrain from the use of any commas."
Pass iff the text contains no comma character: `,` U+002C, `，` U+FF0C, `、`
U+3001, `،` U+060C, `﹐` U+FE50, `﹑` U+FE51 (D-comma-chars).

### punctuation:punctuation_dot
Text: "In your entire response, refrain from the use of . (i.e. dots) as punctuation and in general."
Pass iff the text contains no dot: `.` U+002E, `．` U+FF0E, `。` U+3002, `…`
U+2026 (D-dot-chars). "In general" covers decimals, URLs, file names and
abbreviations.

### punctuation:punctuation_exclamation
Text: "In your entire response, refrain from the use of ! (i.e. exclamation marks) as punctuation and in general."
Pass iff the text contains no exclamation mark: `!` U+0021, `！` U+FF01, `¡`
U+00A1, `‼` U+203C, `❗` U+2757, `❕` U+2755 (D-exclamation-chars). "In
general" covers code such as `!=`.

### startend:end_checker
Text: "Finish your response with this exact phrase {phrase}. No other words should follow this phrase." (phrases: "Is there anything else I can help with?", "Any other questions?")
Pass iff the stripped text contains the exact phrase (case-sensitive, with its
`?`) and nothing after its last occurrence other than whitespace,
punctuation, quotes and markdown characters (D-end-phrase).

### startend:quotation
Text: "Wrap your entire response with double quotation marks."
Pass iff the stripped text has at least 2 characters, starts with `"` or `“`
and ends with `"` or `”` (D-quotation).

## 2. Decision table

| Entry | Question | Reading A (proposed) | Reading B | Example: A / B |
|---|---|---|---|---|
| D-outer-whitespace | Is leading/trailing whitespace part of the response? | No: stripped before every check | Yes | end_checker `…help with?\n`: pass / fail |
| D-empty | Does empty text pass a prohibition? | Yes; requirements fail | Every constraint fails | no_comma on `""`: pass / fail |
| D-word | What is a word? | Letter/digit runs with inner `'`/`-`; one CJK char = one word; punctuation-only tokens are not words | Whitespace-separated tokens | `Hi - there **` words: 2 / 4 |
| D-sentence | What ends a sentence? | Terminal punctuation (not abbreviations, decimals, list numbers), or the end of a line without one | Terminal punctuation only | `Title\nOne sentence.`: 2 / 1 sentences |
| D-keyword-match | How does a keyword match? | Case-insensitive whole word | Case-insensitive substring | forbidden `art` in `start`: pass / fail |
| D-letter-case | Does "the letter t" count `T`? | Yes | No | `Tt`, at least 2: pass / fail |
| D-capital-word | Do one-letter words (`I`, `A`) count as all-capital words? | Yes | No (two or more letters) | `I am`, at least 1: pass / fail |
| D-english | What makes a response "in English"? | Its natural-language text is English; names, code, numbers do not count | Every word is English | `THE CAPITAL IS 北京 (BEIJING).`: pass / fail |
| D-two-responses-different | What makes two responses "different"? | Not identical after stripping whitespace | Different in content (a judgment) | `Yes.\n******\nYes!`: pass / fail |
| D-repeat-center | Which word is "in the center"? | The middle word (odd length) or either middle word (even) | Any word but the first and last | 6-word phrase, 5th word replaced: fail / pass |
| D-repeat-original | Does a verbatim copy of the phrase fail? | Yes, it is an untransformed repetition | No, it is ignored | intro quoting the phrase + n variants: fail / pass |
| D-unique-case | Are `The` and `the` the same word? | Yes | No | `The cat saw the dog`: fail / pass |
| D-lowercase-counting-scope | "All lowercase words should appear at most N times": per word or in total? | Each lowercase word at most N times | At most N lowercase words in all | N=2, `the cat and the dog`: pass / fail |
| D-placeholder | What is a placeholder? | Non-empty `[...]` on one line, not a markdown link's text | Any `[...]`, including `[]` and link text | `[x](http://a)`, at least 1: fail / pass |
| D-postscript-marker | Must the marker match the kwarg exactly? | Final period optional, colon allowed, case-sensitive | Exact kwarg string (`P.S.`) | `P.S: thanks` for `P.S.`: pass / fail |
| D-postscript-position | Where must the marker be? | At the start of a line (after markup) | Anywhere | `see my P.S. below`: fail / pass |
| D-bigram | Can an odd last word stand alone in `<<...>>`? | No: every unit has exactly two words | Yes, one single-word unit at the end | `<<I am>> <<here>>`: fail / pass |
| D-constrained | May other text surround the option? | No: the response is exactly one option | Yes, if exactly one option appears | `My answer is yes. Because…`: fail / pass |
| D-json | Is a JSON scalar "JSON format"? | No: object or array | Any JSON value | `"hello"`: fail / pass |
| D-sections-case | Must the splitter's case match? | Yes | No | `Section 1` for `SECTION`: fail / pass |
| D-sections-numbering | Must X run 1..n in order? | Yes | No, any X | `SECTION 1`, `SECTION 3` for n=2: fail / pass |
| D-sections-preamble | Is text before the first marker allowed? | Yes | No | `Intro\nSECTION 1 …`: pass / fail |
| D-bullets | Which lines are bullet points? | `*`, `-`, `+` bullets, nested ones included | Only `*` bullets, as in the example | `- a\n- b`, exactly 2: pass / fail |
| D-highlight | Does bold `**x**` count as a highlight? | Yes | No, only `*x*` | `**Intro**`, at least 1: pass / fail |
| D-hyphens-single | Does a one-sentence response pass? | Yes | No | `Hello there.`: pass / fail |
| D-square-brackets | One word per bracket pair? | Yes | No: every word inside some pair | `[Hello world]`: fail / pass |
| D-title | Where may the title be? | Anywhere | At the start | `Text\n<<T>>`: pass / fail |
| D-first-last-word | Are case and leading/trailing markup ignored? | Yes | No | `**Development** is…` for `development`: pass / fail |
| D-palindrome | Do one- or two-letter words count? | No: at least 3 letters | Yes | `I am here`: fail / pass |
| D-consecutive-order | Are `b`,`a` consecutive letters? | Yes, either order | Only `a` then `b` | `big apple`: fail / pass |
| D-start-end-case | Must the two words match in case? | No | Yes | `Hello world hello`: pass / fail |
| D-count-exact | "Should appear N times": exactly or at least? | Exactly N | At least N | N+1 occurrences: fail / pass |
| D-language | How strict is "no other language"? | Names, code, numbers allowed | No foreign word at all | Korean text with `iPhone`: pass / fail |
| D-divider | Which dividers separate paragraphs? | A line that is exactly `***` | Any markdown thematic break (`---`, `* * *`, `****`) | `a\n---\nb`, 2 paragraphs: fail / pass |
| D-paragraph-blank | Is a blank-line run of 3+ newlines one separator? | Yes; whitespace-only lines are blank | No: only `\n\n` separates | `a\n\n\nb`, 2 paragraphs: pass / fail |
| D-comma-chars | Which characters are commas? | `,` `，` `、` `،` `﹐` `﹑` | `,` only | `你好，世界`: fail / pass |
| D-dot-chars | Which characters are dots? | `.` `．` `。` `…` | `.` only | `你好。`: fail / pass |
| D-exclamation-chars | Which characters are exclamation marks? | `!` `！` `¡` `‼` `❗` `❕` | `!` only | `你好！`: fail / pass |
| D-end-phrase | May punctuation or markup follow the phrase? | Yes, no words | Nothing but whitespace | `**Any other questions?**`: pass / fail |
| D-quotation | Do curly quotes count? | Yes | No, only `"` | `“Hi”`: pass / fail |
| D-letters-count | Which characters are letters? | Unicode alphabetic | ASCII a-z, A-Z | `Да`, at least 2: pass / fail |

## 3. Contract changes after the hash was recorded

Each change is dated and gives its reason. The hash recorded in `audit/ISSUE.md` covers sections 0 to 2
as first written.

- C1, 2026-11-12T09:48:23Z, D-word clarified. (a) Comparisons of a word with a given word (first/last
  word, keyword position, start/end, palindrome) use the word without attached punctuation or markup under
  both readings; reading B of D-word (whitespace tokens) governs counting only. (b) A number with an
  internal `.` or `,` (`3.5`, `1,000`) is one word. (c) Han and kana characters count one word each;
  Hangul, which separates words with spaces, forms words like Latin script. Reason: while writing
  fixtures it was clear that no reading of "the first word should be the word X" includes a trailing comma,
  and the first wording of D-word left Korean unclear.
- C2, 2026-11-12T09:48:23Z, new entry D-postscript-case. Reading A (proposed): the marker's letters match
  case-insensitively (`p.s.` counts for `P.S.`). Reading B: case-sensitive. Reason: the text does not fix
  the marker's case, and the first contract chose case-sensitive without a decision entry. The postscript
  contract now follows reading A.
- C3, 2026-11-12T09:48:23Z, new entry D-start-end-leading. Reading A (proposed): markup or punctuation
  before the first word is allowed (`**Hello** … hello`). Reading B: the response must begin with the word
  itself. Reason: the first contract allowed leading markup without a decision entry.
- C4, 2026-11-12T09:48:23Z, D-empty clarified: a requirement on every item of a kind ("every word",
  "each sentence", "no two adjacent words", "no word repeated", "all lowercase words at most N times")
  counts as a prohibition and passes on empty text under reading A; `bigram_wrapping` needs at least one
  wrapped unit.

| Entry | Question | Reading A (proposed) | Reading B | Example: A / B |
|---|---|---|---|---|
| D-postscript-case | Must the marker's case match? | No | Yes | `p.s. thanks` for `P.S.`: pass / fail |
| D-start-end-leading | May markup or punctuation precede the first word? | Yes | No | `**Hello** world hello`: pass / fail |
- C5, 2026-11-12T09:56:48Z, new entry D-start-end-single. Reading A (proposed): a one-word response starts
  and ends with the same word, so it passes. Reading B: the check needs at least two words. Reason: fuzzing
  produced one-word responses, and the text does not settle them.
- C6, 2026-11-12T09:56:48Z, new entry D-end-phrase-case. Reading A (proposed): "this exact phrase" is
  case-sensitive. Reading B: case is ignored. Reason: fuzzing produced the phrase in capitals; rows that
  also require all capital or all lowercase letters make the case question matter, and a careful reader
  could take "exact" to be about the words only.
- C7, 2026-11-12T09:56:48Z, D-empty extended: for the "every item" checks of C4 (not the punctuation
  checks), a response with no word at all (only punctuation or symbols) is treated like empty text.
  Reason: fuzzing produced symbol-only responses, on which the vacuous pass of reading A and the fail of
  reading B differ in the same way as on empty text.
- C8, 2026-11-12T09:56:48Z, multiple_sections: the space between SPLITTER and the number is optional
  (`SECTION1` is a marker). Reason: the spacing is not what the instruction asks about; fuzzing showed the
  first contract made it decisive.

| Entry | Question | Reading A (proposed) | Reading B | Example: A / B |
|---|---|---|---|---|
| D-start-end-single | Does a one-word response pass start_end? | Yes | No | `Hello`: pass / fail |
| D-end-phrase-case | Is "this exact phrase" case-sensitive? | Yes | No | `… ANY OTHER QUESTIONS?`: fail / pass |
- C9, 2026-11-12T10:07:09Z, D-first-last-word split into D-first-last-case (are the words compared
  case-insensitively? A: yes, B: no) and D-first-last-markup (are markup and punctuation around the word
  ignored? A: yes, B: no). The proposed readings are unchanged. Reason: grader A ignores case but not
  attached punctuation, so one switch could not express its reading; seen on panel responses outside the
  held-out set.
- C10, 2026-11-12T10:07:09Z, sentence_hyphens: a hyphen with whitespace on either side, an en or em
  dash, or a line break between clauses is a connector that breaks the rule (it is not a bare hyphen, or
  it has whitespace), even when the clauses carry no end punctuation. Reason: panel responses (outside
  the held-out set) replace periods with ` - ` or `—`; the first contract saw such a text as one sentence
  and passed it.
- C11, 2026-11-12T10:07:09Z, new entry D-separator-edge. Reading A (proposed): a divider (`***`) or the
  `******` separator before the first or after the last part is ignored. Reading B: it creates an empty
  part, which fails. Reason: panel responses (outside the held-out set) end with a stray divider or
  separator; the text does not settle it.
- C12, 2026-11-12T10:07:09Z, new entry D-divider-inline. Reading A (proposed): `***` with whitespace on
  both sides inside a line also separates paragraphs. Reading B: only a line that is the divider counts.
  Reason: panel responses (outside the held-out set) put ` *** ` between two sentences.
- C13, 2026-11-12T10:07:09Z, palindrome: a palindrome phrase of several words needs at least 5 letters
  and a word of 2 or more letters. Reason: panel responses in Chinese produced three single-character
  "words" that read the same backwards by chance.
- C14, 2026-11-12T10:07:09Z, multiple_sections: any punctuation (not only markdown) may precede the
  marker on its line. Reason: a panel response (outside the held-out set) opens with a quotation mark
  before `SECTION 1`.
- Replacement fix (not a contract change), 2026-11-12T10:07:09Z: reading B of D-paragraph-blank now
  splits literally at `\n\n`, as its contract text says, instead of rejecting whitespace-only lines.

| Entry | Question | Reading A (proposed) | Reading B | Example: A / B |
|---|---|---|---|---|
| D-first-last-case | Is the word compared case-insensitively? | Yes | No | `Development is…` for `development`: pass / fail |
| D-first-last-markup | Are markup and punctuation around the word ignored? | Yes | No | `**development** is…`: pass / fail |
| D-separator-edge | Does a divider or separator at the very start or end count? | No, it is ignored | Yes, it makes an empty part | `***\n\nOne paragraph.`, 1 paragraph: pass / fail |
| D-divider-inline | Does ` *** ` inside a line separate paragraphs? | Yes | No, only a divider line | `One. *** Two.`, 2 paragraphs: pass / fail |

D-first-last-word is retired (replaced by the two entries above). The contract has 48 decision entries.
