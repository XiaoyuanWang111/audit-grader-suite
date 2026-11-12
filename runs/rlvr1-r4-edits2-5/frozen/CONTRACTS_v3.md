# Contracts for the 47 instruction checks of the RLVR1 instruction-following rows

Written from the requirement texts that the model sees in the 11,817 prompts of
`case/data/rlvr1_instruction_following.jsonl` (surveyed with
`audit/scripts/survey_data.py` and `audit/scripts/show_texts.py`), before any
grader code was read. Each check is one instruction id. Each prompt lists its
requirements in the order of `instruction_id_list`, as a numbered or bulleted
list or inline joined by commas and "and"; the requirement texts below are the
most common renderings, with the row's kwargs filled in.

## 0. Graded text, aggregation, shared definitions

- **Graded text.** The visible answer. For a reasoning model whose rendering
  opens a reasoning block (Qwen3 thinking), the graded text is everything after
  the last `</think>`; a response whose reasoning never closes is an extraction
  failure that fails every check and is counted separately. A non-reasoning
  model's whole response is its graded text. A separate reasoning field is
  never graded.
- **D-strip.** Leading and trailing whitespace of the graded text is not part
  of the answer (proposed). Other reading: it is significant (for example a
  trailing newline after a closing quotation mark).
- **D-empty** (added in v3). An empty graded text fails every check, because
  there is no response to follow the instruction (proposed). Other reading:
  each check is applied literally, so an empty text passes checks such as "no
  commas".
- **Row reward (SkyRL).** Binary: 1 when every constraint of the row passes,
  else 0. **Task-curation gate.** Every deterministic constraint must pass;
  any failure gives 0. A check that cannot be evaluated (an exception) is a
  grading failure, not a model failure; it must not silently count as pass.
- **D-word.** A word is a maximal run of letters or digits, where an internal
  apostrophe (' or ’) or hyphen joins two runs into one word (`don't`,
  `well-known` = one word) (proposed). Other reading: whitespace-separated
  tokens, or runs split at every apostrophe and hyphen. Markdown symbols,
  bullets and punctuation are never words, and neither are inline HTML
  formatting tags such as `<b>` (v3: stated explicitly for the markup edits of
  step 4).
- **D-sentence.** A sentence ends at `.`, `!`, `?` (or `…`, `。`, `！`, `？`)
  followed by whitespace or the end of the text; a line break that ends a block
  (heading, list item, line without end punctuation) also ends a sentence
  (proposed). Abbreviations (`e.g.`, `Dr.`), decimals (`3.5`) and list labels
  (`1.`) do not end a sentence. Other reading: only end punctuation ends a
  sentence, so a heading joins the next sentence.
- **D-keyword-match.** A keyword is found as a whole word, case-insensitively,
  without inflected forms (`fix` does not match `fixed` or `prefix`)
  (proposed). Other readings: case-sensitive; substring match.
- **Edge words.** The first or last word of a text, sentence or paragraph is a
  word in the sense of D-word, so punctuation and quotation marks next to it
  are not part of it (`Hello,` and `"Hello` have first word `Hello`), and it
  is compared case-insensitively.
- **D-edge-word** (narrowed in v2). Markdown symbols at the edge (`*`, `_`,
  `#`, backticks) are skipped too, so `**Hello**` has first word `Hello`
  (proposed). Other reading: a word wrapped in markup is not the plain word.
- **Relations.** "at least N" means count >= N; "less than N" means count < N;
  "at most N" means count <= N; "exactly N" and a bare "N times" mean count == N
  (see D-bare-count).

## 1. Checks

Each entry: requirement text; contract (pass condition; everything else fails);
decision entries specific to the check.

### change_case:capital_word_frequency
Text: "In your response, words with all capital letters should appear {at least|less than} {N} times."
Pass iff the number of words (D-word) that contain at least one uppercase
letter and no lowercase letter satisfies the relation with N (v3: "at least one
uppercase letter", so words of scripts without case, such as Chinese, do not
count). Each occurrence counts.
- D-capital-single-letter: one-letter words such as `I` and `A` count
  (proposed: they count; the text says words with all capital letters).

### change_case:english_capital
Text: "Your entire response should be in English, and in all capital letters."
Pass iff the response is in English and contains no lowercase letter (Unicode
category Ll) anywhere.
- D-english: "in English" is part of the requirement, so a response that is not
  in English fails even if it has no lowercase letters (proposed). Other
  reading: only the letter case is checked. (v3: under the proposed reading, a
  letter of a non-Latin script also makes the response not English; the
  replacement detects English with langdetect, seed 0, on the lowercased text.)

### change_case:english_lowercase
Text: "Your entire response should be in English, and in all lowercase letters. No capital letters are allowed."
Pass iff the response is in English and contains no uppercase or titlecase
letter (Lu, Lt) anywhere. D-english applies.

### combination:two_responses
Text: "Give two different responses. Responses and only responses should be separated by 6 asterisk symbols: ******."
Pass iff the response contains the separator `******` exactly once, the text
before and after it are both non-empty after stripping, and the two differ.
- D-two-responses-different: "different" means not identical after stripping
  whitespace (proposed) vs. substantively different content.
- D-asterisk-run: a run of seven or more asterisks, or a markdown divider
  `***`, is not the separator, and a `******` inside a longer run does not
  count (proposed).

### copy:repeat_phrase
Text: "Repeat the phrase {phrase} exactly {n} times, transforming it slightly each time by replacing only one word in the center of the phrase."
A repetition is a span of the response that matches the phrase word by word
(D-word, case-insensitive) with exactly one word replaced. Pass iff the
response holds exactly n repetitions and each replaced word is a center word
of the phrase.
- D-repeat-center: a center word is any word other than the first and the
  last (proposed) vs. only the middle word (two middle words for an even
  count).
- D-repeat-unchanged: an unchanged copy of the phrase (for example quoting the
  task) makes the response fail (proposed: it is a repetition that was not
  transformed) vs. it is ignored.
- D-repeat-distinct: the n transformed copies need not differ from one another
  (proposed) vs. "each time" requires different replacements.

### count:count_unique
Text: "Only use unique words in your response, no word should be repeated!"
Pass iff no word (D-word) occurs twice, comparing words case-insensitively.
- D-unique-case: `The` and `the` are the same word (proposed) vs. different.

### count:counting_composition
Text: "Write 3 paragraphs, delimited by the markdown divider: * * *, with exactly {n_sent} sentences each, with exactly {n_words} words in each sentence."
Pass iff the response splits at the divider `* * *` into exactly 3 non-empty
paragraphs, each with exactly n_sent sentences (D-sentence), each sentence with
exactly n_words words (D-word).

### count:lowercase_counting
Text: "In your response, all lowercase words should appear at most {N} times."
Pass iff every distinct lowercase word (a word whose letters are all
lowercase) occurs at most N times.
- D-lowercase-counting-scope: each lowercase word at most N times (proposed)
  vs. the total number of lowercase words at most N.

### detectable_content:number_placeholders
Text: "The response must contain at least {N} placeholders represented by square brackets, such as [address]."
Pass iff the response contains at least N placeholders: spans `[...]` with
non-whitespace content and no line break or nested bracket inside.
- D-placeholder-form: any such span counts, including `[1]` and the text part
  of a markdown link (proposed) vs. only word-like names such as `[name]`, or
  (v3) also blank spans such as `[ ]` and `[]`.

### detectable_content:postscript
Text: "At the end of your response, please explicitly add a postscript starting with {P.S.|P.P.S}"
Pass iff the last part of the response is a postscript: a line that starts
with the marker (optionally after markdown emphasis), followed by postscript
text, with nothing after the postscript except more of its text.
- D-postscript-marker: the marker matches with or without its final dot
  (`P.S`, `P.S.`; `P.P.S`, `P.P.S.`), case-sensitive (proposed). The inline
  prompts render `P.S.` as `P.S` (147 of 644 constraints), so the model sees
  both forms.
- D-postscript-case (added in v3): `P.s.` or `p.s.` does not match `P.S.`
  (proposed: case-sensitive) vs. it does.
- D-postscript-position: the postscript must be the final part of the response
  (proposed: "At the end of your response") vs. it may appear anywhere.
- D-postscript-pps: for marker `P.S.`, a postscript that starts with `P.P.S`
  does not satisfy it (proposed) vs. it does.

### detectable_format:bigram_wrapping
Text: "Wrap every word bigram in double angular brackets, such as <<I am>> <<at home>> <<with my>> <<cute dog>>."
Pass iff every word of the response lies inside a `<<...>>` group, each group
holds exactly two words, and text outside groups is only whitespace and
punctuation.
- D-bigram-odd: with an odd number of words, a final one-word group passes
  (proposed) vs. fails.

### detectable_format:constrained_response
Text: "Answer with one of the following options: ('My answer is yes.', 'My answer is no.', 'My answer is maybe.')"
Pass iff the stripped response is exactly one of the three options.
- D-constrained-extra: other text alongside one option fails (proposed) vs. the
  response passes when it contains exactly one of the options.

### detectable_format:json_format
Text: "Entire output should be wrapped in JSON format. You can use markdown ticks such as ```."
Pass iff the stripped response, after removing one optional enclosing code
fence (``` or ```json), parses as JSON, and nothing is outside the fence.
- D-json-scalar: a JSON object or array is required (proposed) vs. any JSON
  value, such as a bare string, passes.

### detectable_format:multiple_sections
Text: "Your response must have {N} sections. Mark the beginning of each section with {SECTION|Section} X, such as:\n{S} 1\n[content of section 1]\n{S} 2\n[content of section 2]"
A section marker is a line that starts with the splitter word and a number,
optionally inside markdown heading or emphasis marks. Pass iff the response has
exactly N section markers, each followed by non-empty content.
- D-sections-count: exactly N (proposed) vs. at least N.
- D-sections-case: the splitter must match the requirement's case (proposed)
  vs. any case.
- D-sections-preamble: text before the first marker is allowed (proposed) vs.
  the response must begin with the first marker.
- D-sections-numbering: the numbers need not run 1..N (proposed) vs. they must.

### detectable_format:number_bullet_lists
Text: "Your answer must contain exactly {N} bullet points. Use the markdown bullet points such as:\n* This is point 1. \n* This is point 2"
A bullet point is a line that starts, after optional indentation, with `* `
or `- ` and text. Pass iff the response has exactly N bullet points.
- D-bullet-dash: `-` bullets count (proposed: both are markdown bullet points)
  vs. only `*`.
- D-bullet-nested: indented bullets count as bullet points (proposed) vs. only
  top-level bullets.

### detectable_format:number_highlighted_sections
Text: "Highlight at least {N} sections in your answer with markdown, i.e. *highlighted section*."
A highlighted section is a markdown emphasis span `*text*` with non-whitespace
text. Pass iff the response has at least N of them.
- D-highlight-bold: a bold span `**text**` also counts (proposed) vs. only
  single-asterisk italics.

### detectable_format:sentence_hyphens
Text: "All sentences must be connected using hyphens, with no spaces between them."
Pass iff every boundary between two consecutive sentences (D-sentence, without
the line-break rule) is a single hyphen with no whitespace on either side, and
the response contains no line break between sentences. Hyphens and spaces
inside a sentence are allowed.
- D-hyphen-single: a response with one sentence passes (proposed: nothing to
  connect) vs. fails.
- D-hyphen-scope (added in v3): the hyphens connect sentences to each other
  (proposed) vs. every sentence joins its own words with hyphens and has no
  spaces at all.

### detectable_format:square_brackets
Text: "Enclose every word in your response within square brackets."
Pass iff every word (D-word) of the response lies inside a pair of square
brackets that holds exactly that one word, possibly with punctuation attached
inside or outside the brackets.
- D-brackets-one-word: each bracket pair holds one word (proposed) vs. a pair
  may hold several words.

### detectable_format:title
Text: "Your answer must contain a title, wrapped in double angular brackets, such as <<poem of joy>>."
Pass iff the response contains `<<...>>` with non-whitespace content on one
line.
- D-title-position: the title may be anywhere (proposed: "contain") vs. it must
  be the first line.

### first_word:first_word_answer
Text: "The first word of your response should be the word {w}."
Pass iff the first word of the response (D-edge-word) equals w.

### first_word:first_word_sent
Text: "The first word of each sentence should be the word {w}."
Pass iff the response has at least one sentence and the first word of every
sentence (D-sentence, D-edge-word) equals w.

### keywords:existence
Text: "Include keywords ['{k1}', '{k2}'] in the response."
Pass iff every keyword occurs (D-keyword-match).

### keywords:forbidden_words
Text: "Do not include keywords ['{k1}', '{k2}'] in the response."
Pass iff no keyword occurs (D-keyword-match).

### keywords:frequency
Text: "In your response, the word {w} should appear {at least|less than} {N} times."
Pass iff the number of occurrences of w (D-keyword-match) satisfies the
relation.

### keywords:keyword_specific_position
Text: "Include keyword {k} in the {n}-th sentence, as the {m}-th word of that sentence."
Pass iff the response has an n-th sentence (D-sentence) and its m-th word
(D-word, case-insensitive) is k.

### keywords:letter_frequency
Text: "In your response, the letter {l} should appear {at least|less than} {N} times."
Pass iff the number of occurrences of the letter, counting upper and lower
case, satisfies the relation.
- D-letter-case: both cases count (proposed) vs. only the case shown.

### keywords:no_adjacent_consecutive
Text: "No two adjacent words can start with consecutive letters of the alphabet."
Pass iff for every two adjacent words (D-word, across punctuation and line
breaks) whose first characters are letters a-z (case-insensitive), the two
first letters are not neighbours in the alphabet (a-b, b-c, ..., y-z), in
either order.
- D-consecutive-order: descending pairs (`b` then `a`) also violate (proposed)
  vs. only ascending pairs.

### keywords:palindrome
Text: "Include a palindrome in your response."
Pass iff some word or number (D-word, case-insensitive) of at least three
letters or digits reads the same backwards (`level`, `2002`; v3: numbers added,
since the usual definition of a palindrome includes numbers), or some phrase of
two or more words does after removing spaces and punctuation (at least five
letters, such as "top spot"). Symbols such as `-` or `---` are never words.
- D-palindrome-length: one- and two-letter words (`a`, `I`, `aa`) do not count
  (proposed) vs. any palindromic word counts.

### keywords:start_end
Text: "Start and end your response with the same word (do not write anything after the last word, not even punctuation)."
Pass iff the first word (D-edge-word) equals the last word, compared
case-insensitively, and the stripped response ends with the last word's final
letter or digit (no punctuation or markup after it).
- D-start-end-leading: punctuation or markup before the first word is allowed
  (proposed: the parenthesis restricts only the end).
- D-start-end-one-word (added in v3): a one-word response passes (proposed:
  its first and last word are the same word) vs. it needs two occurrences.

### keywords:word_count_different_numbers
Text: "In your response, the word {w} should appear {N} times."
Pass iff w occurs (D-keyword-match) exactly N times. The kwarg `relation` is
not shown to the model in 427 of 526 constraints (and the other 99 show the
words only through other requirements).
- D-bare-count: a bare "N times" means exactly N (proposed) vs. at least N. No
  reading allows "less than N".

### keywords:word_once
Text: "Include keyword {k} in your response."
Pass iff k occurs at least once (D-keyword-match). Nothing in the text limits
the number of occurrences.

### language:response_language
Text: "Your ENTIRE response should be in {Language} language, no other language is allowed."
Pass iff all natural-language text of the response is in the language; code,
numbers, URLs and proper names do not count against it.
- D-language-mixed: a response that is mostly in the language but includes a
  sentence in another language fails (proposed, "no other language") vs.
  passes when the main language is right.

### last_word:last_word_answer
Text: "The last word of your response should be the word {w}."
Pass iff the last word of the response (D-edge-word) equals w.

### last_word:last_word_sent
Text: "The last word of each sentence, before punctuation, should be the word {w}."
Pass iff the response has at least one sentence and the last word of every
sentence (D-sentence, D-edge-word) equals w.

### length_constraints:nth_paragraph_first_word
Text: "There should be {N} paragraphs. Paragraphs and only paragraphs are separated with each other by two new lines as if it was '\n\n' in python. Paragraph {i} must start with word {w}."
Paragraphs are the non-empty chunks between separators, a separator being two
or more consecutive line breaks (with only whitespace between them). Pass iff
there are exactly N paragraphs and paragraph i's first word (D-edge-word) is w.
- D-paragraph-blank-run: three or more line breaks form one separator
  (proposed) vs. they create an empty paragraph that breaks the count.

### length_constraints:number_paragraphs
Text: "There should be {N} paragraphs. Paragraphs are separated with the markdown divider: ***"
A divider is a line that is `***` (optionally surrounded by whitespace).
Paragraphs are the chunks between dividers. Pass iff there are exactly N
chunks and every chunk is non-empty.
- D-divider-edge: a divider at the very start or end of the response (an empty
  outer chunk) fails (proposed) vs. is ignored.
- D-divider-variants: `* * *` and `---` are not the divider (proposed).
- A `***` that is not alone on its line (inline, or bold-italic markup such as
  `***Note***`) is not a divider (v3: stated explicitly; a markdown divider is
  a line of its own).

### length_constraints:number_sentences
Text: "Your response should contain {at least|less than} {N} sentences."
Pass iff the sentence count (D-sentence) satisfies the relation.

### length_constraints:number_words
Text: "Answer with {at least|less than} {N} words."
Pass iff the word count (D-word) satisfies the relation.

### letters:letter_counting
Text: "Answer with {at least|less than} {N} letters." (N is 2 or 3)
Pass iff the number of letters (alphabetic characters, any script) in the
response satisfies the relation.
- D-letters-unit: letters are alphabetic characters (proposed) vs. "letters"
  read as words or as written characters of any kind.

### letters:letter_counting2
Text: identical to keywords:letter_frequency. Same contract and D-letter-case.

### paragraphs:paragraphs
Text: "There should be 2 paragraphs. Paragraphs are separated with the markdown divider: ***" (no kwargs; every one of the 576 prompts says 2)
Contract of length_constraints:number_paragraphs with N = 2.

### paragraphs:paragraphs2
Text: "There should be 2 paragraphs. Paragraphs and only paragraphs are separated with each other by two line breaks." (no kwargs; 740 of 744 constraints show 2, and the other 4 rows' texts also say 2 for this requirement)
Paragraphs as in nth_paragraph_first_word. Pass iff exactly 2 paragraphs.

### punctuation:no_comma
Text: "In your entire response, refrain from the use of any commas."
Pass iff the response contains no comma.
- D-comma-variants: every comma character counts (`,` `，` `、` `،`) (proposed)
  vs. only the ASCII comma.

### punctuation:punctuation_dot
Text: "In your entire response, refrain from the use of . (i.e. dots) as punctuation and in general."
Pass iff the response contains no `.` character (also inside numbers, URLs,
code and ellipses).
- D-dot-variants: other full stops and dots (`。` `．` `…`) also fail (proposed)
  vs. only `.`.

### punctuation:punctuation_exclamation
Text: "In your entire response, refrain from the use of ! (i.e. exclamation marks) as punctuation and in general."
Pass iff the response contains no `!` character.
- D-exclamation-variants: `！` and `¡` also fail (proposed) vs. only `!`.

### startend:end_checker
Text: "Finish your response with this exact phrase {phrase}. No other words should follow this phrase."
Pass iff the stripped response ends with the phrase, character for character.
- D-end-trailing-markup: markup or quotation marks after the phrase (`**`,
  `"`) make it fail (proposed: the phrase must finish the response) vs. only
  words are forbidden after it.
- D-end-case: the phrase is matched case-sensitively (proposed: "exact
  phrase") vs. case-insensitively.

### startend:quotation
Text: "Wrap your entire response with double quotation marks."
Pass iff the stripped response has at least two characters, starts with a
double quotation mark and ends with one.
- D-quotation-typographic: typographic marks (“ ”) count (proposed) vs. only
  `"`.

## 2. Data-level conditions (from the texts and kwargs)

- Rows 1994, 2473, 3581, 4428, 4916, 5239, 6179, 8970, 11293 (0-based file
  order) combine `length_constraints:number_paragraphs` with N = 1 or 3 (`***`
  dividers) and `paragraphs:paragraphs2` (2 paragraphs separated by blank
  lines). Under these contracts both can hold at once (for N = 1: two
  blank-line paragraphs and no `***`), so the rows are satisfiable; a grader
  that counts the two separators as one kind would make them unsatisfiable.
- The graders may only use what the text states; a kwarg that changes the
  verdict but is not shown to the model (the `relation` of
  `keywords:word_count_different_numbers`) breaks the contract when it
  disagrees with the text.
