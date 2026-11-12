# Contracts for the 47 instruction checks of the RLVR1 instruction-following rows

Written from the requirement text that the model sees in the prompts of
`case/data/rlvr1_instruction_following.jsonl` (templates collected by
`audit/scripts/instruction_texts.py` and checked against kwargs by
`audit/scripts/text_kwargs_consistency.py`), before any grader code was read.
Each contract states when a response passes and when it fails. Where the text
allows two verdicts, the contract names a decision entry `D-<topic>` (table at
the end) and follows its proposed reading.

## G. Definitions shared by all checks

- G1. Graded text. The model's visible answer. For a reasoning model, the text
  after the last end-of-reasoning marker (`</think>` for Qwen3); a separate
  reasoning field is never graded. A response whose reasoning never closes is
  an extraction failure: it fails every check and is counted separately.
  Leading and trailing whitespace of the graded text is never itself a
  violation, except where a contract says so.
- G2. Word. A maximal run of letters and digits (any script), which may
  contain an internal apostrophe (`'` or `’`) or an internal hyphen. Markup
  and punctuation around it (`*`, `_`, `#`, backticks, quotation marks,
  brackets, `.,;:!?`) are not part of the word (D-markup-transparent). Whether
  a hyphenated compound is one word or two: D-word-hyphen (proposed: one).
  How to count words in scripts written without spaces (Chinese, Japanese,
  Thai): D-word-unspaced (proposed: each run of such characters between
  spaces or punctuation is one word; this only matters for counting checks).
- G3. Sentence. A sentence ends at `.`, `!`, `?`, `…` or their full-width and
  CJK forms (`。！？`), followed by whitespace, a closing quote or bracket, or
  the end of the text. Abbreviations (`e.g.`, `Dr.`, `U.S.`) and decimal
  numbers do not end a sentence. A heading, a list item or a line without
  final punctuation ends at its line break (D-sentence-lines, proposed: yes).
- G4. Word comparison. Comparing a response word with a word the text names
  (first word, last word, keyword) ignores letter case and surrounding markup
  and punctuation (D-word-case, proposed: case-insensitive). Inflected forms
  (`cats` for `cat`) are different words. A keyword counts only as a whole
  word, never inside a longer word (D-keyword-boundary, proposed: whole word).
- G5. Letters. "The letter x" counts both cases of x (D-letter-case, proposed:
  case-insensitive).
- G6. Relations. "less than N": count < N. "at least N": count >= N. "at most
  N": count <= N. "exactly N" or a bare "N times": count = N.
- G7. Paragraph split by blank lines. A separator is a run of two or more line
  breaks, possibly with spaces or tabs between them (a blank line); leading
  and trailing whitespace of the response is ignored (D-paragraph-blank-lines,
  proposed: any blank-line run is one separator).
- G8. Paragraph split by the markdown divider `***`. A divider is a line whose
  only non-space content is `***` (D-divider-line, proposed: a line on its
  own; `***` inside a line, such as `***bold italic***`, is not a divider).
  The pieces between dividers are the paragraphs; each must contain text
  (an empty piece, as from a divider at the very start or end, fails the
  count) (D-divider-empty, proposed: an empty piece is a defect, not
  ignored).

## C. One contract per check

### change_case:capital_word_frequency
Text: "In your response, words with all capital letters should appear {relation} {N} times."
- Count the words (G2) that contain at least one letter with case and whose
  cased letters are all upper case (`NASA`, `AI`, `COVID-19`). Single-letter
  words such as `I` and `A` count (D-capital-single, proposed: they count).
- Pass when the count satisfies the relation (G6); fail otherwise.

### change_case:english_capital
Text: "Your entire response should be in English, and in all capital letters."
- Pass: the response is English text (D-english, proposed: the prose is
  English; names, numbers, code and quoted foreign terms are allowed) and
  contains no lower-case letter of any script.
- Fail: any lower-case letter; prose in another language; an empty response
  (D-empty-english, proposed: an empty response is not "in English" and fails).

### change_case:english_lowercase
Text: "Your entire response should be in English, and in all lowercase letters. No capital letters are allowed."
- Pass: English (D-english) and no upper-case or title-case letter of any
  script.
- Fail: any capital letter; prose in another language; an empty response
  (D-empty-english).

### combination:two_responses
Text: "Give two different responses. Responses and only responses should be separated by 6 asterisk symbols: ******."
- Pass: the response contains exactly one separator, a run of exactly six
  asterisks `******` (D-two-separator, proposed: a run of six, not five or
  seven), and splitting at it gives two parts that each contain text and that
  differ from each other after whitespace normalization.
- Fail: zero or two or more separators; an empty part; two identical parts.

### copy:repeat_phrase
Text: "Repeat the phrase {phrase} exactly {small_n} times, transforming it slightly each time by replacing only one word in the center of the phrase."
- A transformed repetition is a word sequence in the response with the same
  number of words as the phrase that differs from the phrase in exactly one
  word, and that word is not the first or the last word of the phrase
  (D-repeat-center, proposed: any word other than the first and last; the
  other reading allows only the middle word). Word comparison as in G4.
- Pass: the response contains exactly `small_n` transformed repetitions and
  no unchanged copy of the phrase (D-repeat-original, proposed: an unchanged
  copy is a repetition that was not transformed, so it fails).
- Fail: fewer or more transformed repetitions; a repetition that changes two
  or more words, or the first or last word; an unchanged copy.

### count:count_unique
Text: "Only use unique words in your response, no word should be repeated!"
- Pass: no word (G2) occurs twice, comparing words case-insensitively
  (D-unique-case, proposed: `The` and `the` are the same word).
- Fail: any word occurring twice. An empty response passes vacuously.

### count:counting_composition
Text: "Write 3 paragraphs, delimited by the markdown divider: * * *, with exactly {n_sent} sentences each, with exactly {n_words} words in each sentence."
- Pass: splitting at divider lines `* * *` (G8 with this divider; `***`
  accepted too, D-divider-line) gives exactly 3 non-empty paragraphs, each
  with exactly `n_sent` sentences (G3), each sentence with exactly `n_words`
  words (G2).
- Fail otherwise.

### count:lowercase_counting
Text: "In your response, all lowercase words should appear at most {N} times."
- A lower-case word is a word (G2) whose cased letters are all lower case.
- Pass: every distinct lower-case word occurs at most N times
  (D-lowercase-counting, proposed: per distinct word; the other reading caps
  the total number of lower-case words at N).
- Fail: some lower-case word occurs more than N times.

### detectable_content:number_placeholders
Text: "The response must contain at least {N} placeholders represented by square brackets, such as [address]."
- A placeholder is a span `[text]` with non-empty text and no bracket inside
  (D-placeholder, proposed: any such span counts, including the text of a
  markdown link; `[]` does not).
- Pass: at least N placeholders. Fail: fewer.

### detectable_content:postscript
Text: "At the end of your response, please explicitly add a postscript starting with {marker}" (marker `P.S.` or `P.P.S`; in 147 rows the prompt shows `P.S.` as `P.S`).
- A postscript is a line that starts with the marker as the prompt shows it,
  after optional markup such as `**` (D-markup-transparent).
- Pass: the response has a postscript, and it is the last block of the
  response: no blank-line-separated block of other text follows it
  (D-postscript-end, proposed: the postscript must be at the end).
- Letter case of the marker: D-postscript-case (proposed: `p.s.` counts as
  `P.S.`).
- Fail: no line starting with the marker; the marker only inside a line; a
  postscript followed by another block of the answer.

### detectable_format:bigram_wrapping
Text: "Wrap every word bigram in double angular brackets, such as <<I am>> <<at home>> <<with my>> <<cute dog>>."
- Pass: every word of the response lies inside a `<<...>>` group, and each
  group holds exactly two words; an answer with an odd number of words may end
  with one group of one word (D-bigram-odd, proposed: allowed).
- Fail: a word outside every group; a group with three or more words.

### detectable_format:constrained_response
Text: "Answer with one of the following options: ('My answer is yes.', 'My answer is no.', 'My answer is maybe.')"
- Pass: the response contains exactly one of the three option sentences
  (exact wording; case-sensitive) and none of the other two
  (D-constrained-extra, proposed: other text around the option is allowed; the
  other reading requires the response to be the option alone).
- Fail: no option; two or more different options.

### detectable_format:json_format
Text: "Entire output should be wrapped in JSON format. You can use markdown ticks such as ```."
- Pass: the whole response, after stripping whitespace and removing one
  optional enclosing markdown code fence (```` ``` ```` or ```` ```json ````),
  parses as one JSON value (D-json-scalar, proposed: any JSON value).
- Fail: text outside the JSON or the fence; invalid JSON; two JSON values.

### detectable_format:multiple_sections
Text: "Your response must have {N} sections. Mark the beginning of each section with {spliter} X, such as: {spliter} 1 [content of section 1] {spliter} 2 [content of section 2]" (spliter `SECTION` or `Section`).
- A section header is a line that starts, after optional markdown heading or
  emphasis marks, with the spliter word followed by a space and a section
  number (D-section-case, proposed: the spliter word in any letter case; and
  D-section-markup, proposed: `## SECTION 1` and `**SECTION 1**` count).
- Pass: exactly N section headers, each followed by content. Text before the
  first header (a title) does not count as a section (D-section-preamble,
  proposed: allowed).
- Fail: more or fewer headers; the spliter word used mid-sentence does not
  count as a header.

### detectable_format:number_bullet_lists
Text: "Your answer must contain exactly {N} bullet points. Use the markdown bullet points such as: * This is point 1. * This is point 2"
- A bullet point is a line that starts, after optional indentation, with a
  markdown bullet marker `*`, `-` or `+` followed by a space
  (D-bullet-markers, proposed: all three markers; and D-bullet-nested,
  proposed: nested bullets count too). `**bold**` at a line start and
  numbered items (`1.`) are not bullet points. A horizontal rule (`***`,
  `---`) is not a bullet point.
- Pass: exactly N bullet points. Fail: any other number.

### detectable_format:number_highlighted_sections
Text: "Highlight at least {N} sections in your answer with markdown, i.e. *highlighted section*."
- A highlighted section is a markdown emphasis span `*text*` with non-empty
  text; `**text**` counts too (D-highlight-bold, proposed: bold counts).
- Pass: at least N highlighted sections. Fail: fewer. `**` with nothing
  between and a lone `*` bullet marker are not highlights.

### detectable_format:sentence_hyphens
Text: "All sentences must be connected using hyphens, with no spaces between them."
- Pass: consecutive sentences (G3) are joined by a hyphen with no whitespace
  on either side (`One.-Two.-Three.`); words inside a sentence keep their
  spaces. A one-sentence response passes (D-hyphen-single, proposed: passes).
- Fail: two consecutive sentences separated by whitespace (space or line
  break) instead of a hyphen, or by a hyphen with a space next to it.

### detectable_format:square_brackets
Text: "Enclose every word in your response within square brackets."
- Pass: every word (G2) is enclosed in its own pair of square brackets
  (`[Hello] [world].`); punctuation outside the brackets is allowed
  (D-bracket-group, proposed: one word per pair; the other reading also
  accepts `[Hello world]`).
- Fail: a word outside brackets.

### detectable_format:title
Text: "Your answer must contain a title, wrapped in double angular brackets, such as <<poem of joy>>."
- Pass: the response contains `<<text>>` on one line with non-blank text
  (anywhere; D-title-position, proposed: anywhere).
- Fail: no such span; `<<>>` or `<< >>`.

### first_word:first_word_answer
Text: "The first word of your response should be the word {w}."
- Pass: the first word (G2) of the response equals w (G4: case and leading
  markup or punctuation ignored).
- Fail: any other first word; an empty response.

### first_word:first_word_sent
Text: "The first word of each sentence should be the word {w}."
- Pass: every sentence (G3) starts with the word w (G4). Fail: some sentence
  starting with another word; an empty response (D-empty-each, proposed: a
  response with no sentence fails).

### keywords:existence
Text: "Include keywords ['k1', 'k2', ...] in the response."
- Pass: every keyword occurs at least once as a whole word (G4). Fail: a
  keyword missing, or present only inside a longer word.

### keywords:forbidden_words
Text: "Do not include keywords ['k1', 'k2', ...] in the response."
- Pass: no keyword occurs as a whole word (G4). A keyword inside a longer word
  (`wheel` in `wheelchair`) does not count (D-keyword-boundary).
- Fail: any keyword present as a word, in any letter case.

### keywords:frequency
Text: "In your response, the word {k} should appear {relation} {N} times."
- Count whole-word occurrences of k (G4). Pass when the count satisfies the
  relation (G6).

### keywords:keyword_specific_position
Text: "Include keyword {k} in the {n}-th sentence, as the {m}-th word of that sentence."
- Pass: the response has at least n sentences (G3), and the m-th word (G2,
  1-based) of the n-th sentence equals k (G4). Fail otherwise.

### keywords:letter_frequency
Text: "In your response, the letter {l} should appear {relation} {N} times."
- Count occurrences of the letter l in either case (G5). Pass when the count
  satisfies the relation (G6).

### keywords:no_adjacent_consecutive
Text: "No two adjacent words can start with consecutive letters of the alphabet."
- For each pair of adjacent words (G2, across punctuation and line breaks),
  take their first letters, case-insensitively, in the Latin alphabet a-z.
- Fail: some pair whose first letters are consecutive, in either order (`a`
  then `b`, or `b` then `a`) (D-consecutive-order, proposed: either order).
  Words that start with a digit or a non-Latin letter never form such a pair.
- Pass otherwise.

### keywords:palindrome
Text: "Include a palindrome in your response."
- Pass: the response contains a word (G2) of at least three letters that
  reads the same backwards, case-insensitively (`level`, `noon`, `did`), or a
  phrase of whole words that does, ignoring spaces and punctuation
  (D-palindrome-length, proposed: at least three letters; the other readings
  accept two letters or a single letter).
- Fail: no such word or phrase.

### keywords:start_end
Text: "Start and end your response with the same word (do not write anything after the last word, not even punctuation)."
- Pass: the first word and the last word (G2) are the same word (G4), and
  nothing but whitespace follows the last word (D-start-end-trailing,
  proposed: trailing whitespace allowed; trailing punctuation or markup such
  as `.` or `**` fails). Leading markup or punctuation before the first word
  is allowed (D-markup-transparent).
- Fail: different words; any non-whitespace character after the last word; an
  empty response.

### keywords:word_count_different_numbers
Text: "In your response, the word {k} should appear {N} times." (no relation in the text in all 526 rows; the kwargs carry one)
- Pass: k occurs exactly N times as a whole word (G4, G6 bare "N times").
- Fail: any other count.

### keywords:word_once
Text: "Include keyword {k} in your response."
- Pass: k occurs at least once as a whole word (G4). Fail: k absent.

### language:response_language
Text: "Your ENTIRE response should be in {Language} language, no other language is allowed."
- Pass: the whole response is written in that language; numbers, names,
  code and unavoidable technical terms are not "another language" (D-english
  applies in the same way).
- Fail: prose in another language, including a mix; an empty response.

### last_word:last_word_answer
Text: "The last word of your response should be the word {w}."
- Pass: the last word (G2) equals w (G4: trailing punctuation and markup
  ignored). Fail otherwise, and on an empty response.

### last_word:last_word_sent
Text: "The last word of each sentence, before punctuation, should be the word {w}."
- Pass: every sentence (G3) ends with the word w (G4). Fail: some sentence
  ending with another word; an empty response (D-empty-each).

### length_constraints:nth_paragraph_first_word
Text: "There should be {num_paragraphs} paragraphs. Paragraphs and only paragraphs are separated with each other by two new lines as if it was '\n\n' in python. Paragraph {i} must start with word {w}."
- Pass: splitting at blank lines (G7) gives exactly num_paragraphs non-empty
  paragraphs, and the first word (G2, G4) of paragraph i is w.
- Fail: another paragraph count; another first word of paragraph i.

### length_constraints:number_paragraphs
Text: "There should be {N} paragraphs. Paragraphs are separated with the markdown divider: ***"
- Pass: splitting at divider lines (G8) gives exactly N non-empty paragraphs.
  For N = 1, a response with no divider passes.
- Fail: another count; an empty piece.

### length_constraints:number_sentences
Text: "Your response should contain {relation} {N} sentences."
- Count sentences (G3). Pass when the count satisfies the relation (G6).

### length_constraints:number_words
Text: "Answer with {relation} {N} words."
- Count words (G2). Pass when the count satisfies the relation (G6).

### letters:letter_counting
Text: "Answer with {relation} {N} letters." (N is 2 or 3)
- Count the letters (alphabetic characters of any script) in the response
  (D-letter-def, proposed: any script). Pass when the count satisfies the
  relation (G6).

### letters:letter_counting2
Text: identical to keywords:letter_frequency: "In your response, the letter {l} should appear {relation} {N} times."
- Same contract as keywords:letter_frequency.

### paragraphs:paragraphs
Text: "There should be 2 paragraphs. Paragraphs are separated with the markdown divider: ***"
- Same contract as length_constraints:number_paragraphs with N = 2.

### paragraphs:paragraphs2
Text: "There should be 2 paragraphs. Paragraphs and only paragraphs are separated with each other by two line breaks."
- Pass: splitting at blank lines (G7) gives exactly 2 non-empty paragraphs.
  Single line breaks inside a paragraph are allowed.
- Fail: one paragraph, three or more paragraphs.

### punctuation:no_comma
Text: "In your entire response, refrain from the use of any commas."
- Fail: any comma character: `,` and its other forms `，` (full width), `、`
  (ideographic), `،` (Arabic), `﹐` (D-comma-unicode, proposed: all forms
  count). Pass otherwise, including an empty response.

### punctuation:punctuation_dot
Text: "In your entire response, refrain from the use of . (i.e. dots) as punctuation and in general."
- Fail: any `.` anywhere (sentence end, number, URL, abbreviation), its full
  width form `．`, or the ellipsis character `…` (D-dot-unicode, proposed:
  these count; the ideographic full stop `。` is not a dot). Pass otherwise.

### punctuation:punctuation_exclamation
Text: "In your entire response, refrain from the use of ! (i.e. exclamation marks) as punctuation and in general."
- Fail: any exclamation mark: `!`, `！`, `¡`, `‼` (D-exclamation-unicode,
  proposed: all forms count). Pass otherwise.

### startend:end_checker
Text: "Finish your response with this exact phrase {phrase}. No other words should follow this phrase."
- Pass: the response, after removing trailing whitespace, ends with the exact
  phrase (D-end-case, proposed: exact letter case; D-end-trailing, proposed:
  nothing but whitespace may follow, so trailing markup or punctuation such
  as `**` or `.` fails; D-markup-transparent does not apply here).
- Fail: the phrase absent, changed, or followed by anything other than
  whitespace.

### startend:quotation
Text: "Wrap your entire response with double quotation marks."
- Pass: the response, after stripping surrounding whitespace, starts with a
  double quotation mark and ends with one, and is longer than the two marks:
  `"..."` or typographic `“...”` (D-quotation-typographic, proposed: both).
- Fail: a missing opening or closing mark; single quotation marks.

## D. Decision entries (proposed readings)

| Entry | Question | Proposed | Other reading |
|---|---|---|---|
| D-markup-transparent | Does markdown or punctuation around a word change it? | No: `**Hello**` has first word Hello | Markup is part of the text |
| D-word-hyphen | Is `well-known` one word? | One word | Two words |
| D-word-unspaced | How are words counted in unspaced scripts? | A run between spaces/punctuation is one word | Each character is a word |
| D-sentence-lines | Does a line break end a sentence without final punctuation (headings, list items)? | Yes | Only `.!?` end sentences |
| D-word-case | Are named words compared case-insensitively? | Yes | Exact case |
| D-keyword-boundary | Does a keyword count inside a longer word? | No, whole words only | Substring counts |
| D-letter-case | Does "the letter m" count `M`? | Yes | Lower case only |
| D-paragraph-blank-lines | Is a run of 3+ line breaks one separator? | Yes | Only exactly `\n\n` |
| D-divider-line | Must `***` stand on its own line to divide? | Yes | Any `***` divides |
| D-divider-empty | Does an empty piece (divider at start or end) count against N? | Yes, it fails | Empty pieces are ignored |
| D-capital-single | Do `I` and `A` count as all-capital words? | Yes | Only words of 2+ letters |
| D-english | How much non-English text is allowed in "entirely English"? | Names, numbers, code only | Any amount of foreign words |
| D-empty-english | Does an empty response satisfy "entire response in English, capitals/lowercase"? | No | Yes, vacuously |
| D-two-separator | Must the separator be exactly six asterisks? | Exactly six | Six or more |
| D-repeat-center | Which word may be replaced in repeat_phrase? | Any but the first and last | The middle word only |
| D-repeat-original | Does an unchanged copy count as a repetition? | It is an untransformed repetition: fail | Ignored |
| D-unique-case | Are `The` and `the` the same word for count_unique? | Yes | No |
| D-lowercase-counting | "all lowercase words should appear at most N times": per word or total? | Per distinct word | Total lower-case words <= N |
| D-placeholder | Does any `[text]`, including link text, count as a placeholder? | Yes | Only placeholder-like names |
| D-postscript-end | Must the postscript be the last block? | Yes | Anywhere |
| D-postscript-case | Does `p.s.` count as `P.S.`? | Yes | Exact case |
| D-bigram-odd | May an odd final word stand alone in `<<...>>`? | Yes | No |
| D-constrained-extra | May other text surround the chosen option? | Yes | The option alone |
| D-json-scalar | Does a bare JSON scalar count as JSON format? | Yes | Object or array only |
| D-section-case | Does `Section 1` mark a section when the spliter is `SECTION`? | Yes | Exact case |
| D-section-markup | Do `## SECTION 1` and `**SECTION 1**` count? | Yes | Plain line start only |
| D-section-preamble | Is text before the first header allowed? | Yes | No |
| D-bullet-markers | Do `-` and `+` bullets count? | Yes | Only `*` |
| D-bullet-nested | Do nested bullets count? | Yes | Top level only |
| D-highlight-bold | Does `**bold**` count as a highlight? | Yes | Only `*italic*` |
| D-hyphen-single | Does a one-sentence response satisfy sentence_hyphens? | Yes | No |
| D-bracket-group | Does `[Hello world]` enclose both words? | No | Yes |
| D-title-position | Must the title come first? | No, anywhere | First line |
| D-empty-each | Does a response with no sentence satisfy "each sentence"? | No | Yes, vacuously |
| D-consecutive-order | Are `b` then `a` consecutive letters? | Yes, either order | Only ascending |
| D-palindrome-length | Minimum palindrome length | 3 letters | 2 letters, or 1 |
| D-start-end-trailing | What may follow the last word? | Whitespace only | Nothing at all |
| D-letter-def | Which characters are letters in letter_counting? | Letters of any script | Latin a-z only |
| D-comma-unicode | Do `，`, `、`, `،` count as commas? | Yes | Only `,` |
| D-dot-unicode | Do `．` and `…` count as dots? | Yes (`。` does not) | Only `.` |
| D-exclamation-unicode | Do `！`, `¡`, `‼` count? | Yes | Only `!` |
| D-end-case | Is the end phrase case-sensitive? | Yes (exact) | Case-insensitive |
| D-end-trailing | May punctuation or markup follow the end phrase? | No | Non-word characters may |
| D-quotation-typographic | Do `“ ”` count as double quotation marks? | Yes | Only `"` |
