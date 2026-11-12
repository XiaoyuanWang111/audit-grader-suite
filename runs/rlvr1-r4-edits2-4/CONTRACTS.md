# Contracts for the 47 instruction checks of RLVR1 instruction following

Written from the instruction text that the model sees (the prompts of
`case/data/rlvr1_instruction_following.jsonl`, templates collected by
`audit/scripts/instruction_texts.py` into `audit/work/instruction_texts.json`),
before reading any grader code. `{x}` is a kwargs value. A decision entry
`D-<topic>` marks a point where the text allows two verdicts; the contract
states the proposed reading, and the decision table at the end gives both
readings and an example of each.

## 0. Graded text and shared terms

- **Graded text G.** For a response generated with thinking (Qwen3 thinking,
  whose chat template opens `<think>` in the prompt), G is the text after the
  last `</think>`. A thinking response without `</think>` is an extraction
  failure: it fails every check and is counted separately. For a response
  generated without thinking, G is the whole response. Leading and trailing
  whitespace of G is ignored by every check (it is not "anything written").
- **Empty G.** An empty G (or whitespace only) fails every check
  (`D-empty-response`).
- **Row verdict.** A row passes when every one of its constraints passes
  (both pipelines; task curation's gate covers only the non-semantic
  constraints, so the gate verdict is compared with the contract over those).
- **Word.** A maximal run of letters, digits and combining marks, where an
  internal apostrophe (`'` or `’`) or hyphen between two such characters
  joins the run (`well-known`, `don't` are one word each) (`D-word-units`).
  Markup (`*`, `_`, `#`, backticks, `<`, `>`, `[`, `]`), quotation marks and
  punctuation are never part of a word. Numbers are words. Scripts written
  without spaces (CJK) have no agreed word unit (`D-word-cjk`, open).
- **Word equality.** Two words are the same word when they are equal ignoring
  case (`D-word-case`); an inflected form (`cats` for `cat`) is a different
  word (`D-keyword-inflection`). A word that merely contains the keyword as a
  substring of a different word (`start` for `art`, `lawyer` for `law`,
  `category` for `cat`) is never the keyword.
- **Sentence.** A sentence is a maximal span of text ending at `.`, `!` or `?`
  (one or more, optionally followed by closing quotes or brackets) that is
  followed by whitespace or the end of G, or ending at a line break that ends
  a non-empty line (a heading or a list item without final punctuation is its
  own sentence) (`D-sentence-split`). A period in an abbreviation (`e.g.`,
  `Dr.`), a decimal number (`3.5`) or a list label (`1.`) does not end a
  sentence. A sentence must contain at least one word.
- **Paragraph (blank-line form).** Blocks of G separated by one or more blank
  lines (a run of two or more line breaks, where the lines between may hold
  whitespace only); empty blocks are not paragraphs (`D-paragraph-blank-lines`).
- **Paragraph (divider form).** Parts of G separated by lines that consist of
  the markdown divider `***` only (`D-divider-form`); every part must be
  non-empty (`D-divider-edges`); blank lines inside a part do not split it
  (`D-divider-blank-lines`).
- **Relations.** `less than N` means count < N; `at least N` means count >= N.

## 1. Per-check contracts

### change_case:capital_word_frequency
Text: "In your response, words with all capital letters should appear {capital_relation} {capital_frequency} times."
Count the word occurrences (not distinct words) in G whose cased letters are
all uppercase and that contain at least one letter; one-letter words such as
`I` and `A` count (`D-capital-word`). Pass iff the count meets the relation.

### change_case:english_capital
Text: "Your entire response should be in English, and in all capital letters."
Pass iff G contains no lowercase letter (of any cased script) and G is written
in English (`D-language-mixed`: names, numbers, code and short quoted terms in
another language are allowed).

### change_case:english_lowercase
Text: "Your entire response should be in English, and in all lowercase letters. No capital letters are allowed."
Pass iff G contains no uppercase or titlecase letter and G is written in
English (as above).

### combination:two_responses
Text: "Give two different responses. Responses and only responses should be separated by 6 asterisk symbols: ******."
Pass iff G contains exactly one separator, a run of exactly six `*` (not part
of a longer run of `*`), and the two parts it splits G into are each
non-empty and differ after stripping surrounding whitespace
(`D-two-different`).

### copy:repeat_phrase
Text: "Repeat the phrase {phrase} exactly {small_n} times, transforming it slightly each time by replacing only one word in the center of the phrase."
A variant is the phrase with exactly one word replaced by one different word,
where the replaced word is a middle word: the 3rd of 5 words, the 3rd or 4th
of 6 words (`D-repeat-center`); all other words unchanged (case-insensitive,
ignoring punctuation). Pass iff G contains exactly {small_n} variants.
Whether an unchanged copy of the phrase may also appear is `D-repeat-original`
(proposed: an unchanged copy counts as a repetition that was not transformed,
so the response fails).

### count:count_unique
Text: "Only use unique words in your response, no word should be repeated!"
Pass iff no word occurs twice in G, comparing words case-insensitively.

### count:counting_composition
Text: "Write 3 paragraphs, delimited by the markdown divider: * * *, with exactly 3 sentences each, with exactly 2 words in each sentence." (kwargs n_sent 3, n_words 2; one constraint in the data)
Pass iff G splits on divider lines (`* * *`, `D-divider-form`) into exactly 3
non-empty paragraphs, each with exactly {n_sent} sentences, each with exactly
{n_words} words.

### count:lowercase_counting
Text: "In your response, all lowercase words should appear at most {N} times."
Pass iff every word written in lowercase occurs at most {N} times in
lowercase form (`D-lowercase-count`; capitalized occurrences are not
lowercase words).

### detectable_content:number_placeholders
Text: "The response must contain at least {num_placeholders} placeholders represented by square brackets, such as [address]."
A placeholder is a span `[text]` with non-empty, non-whitespace text and no
nested brackets (`D-placeholder`). Pass iff G has at least
{num_placeholders} placeholders.

### detectable_content:postscript
Text: "At the end of your response, please explicitly add a postscript starting with {postscript_marker}"
Pass iff the last paragraph (blank-line form) of G starts, after optional
markup (`*`, `_`, `#`) and whitespace, with the marker exactly as given
(case-sensitive, `D-postscript-case`), and the marker is a whole token (`P.S.`
does not match the start of `P.P.S.`); the postscript is the end of the
response (`D-postscript-position`).

### detectable_format:bigram_wrapping
Text: "Wrap every word bigram in double angular brackets, such as <<I am>> <<at home>> <<with my>> <<cute dog>>."
Pass iff every word of G lies inside a `<<...>>` group, and every group holds
exactly two words, except that with an odd word count one group may hold one
word (`D-bigram-odd`). Punctuation may sit inside or outside groups.

### detectable_format:constrained_response
Text: "Answer with one of the following options: ('My answer is yes.', 'My answer is no.', 'My answer is maybe.')"
Pass iff G contains exactly one of the three option sentences (other text
allowed, `D-constrained-extra`) and no second, different option.

### detectable_format:json_format
Text: "Entire output should be wrapped in JSON format. You can use markdown ticks such as ```."
Pass iff G, after removing one optional surrounding markdown fence
(```` ``` ```` or ```` ```json ````), parses as a JSON object or array
(`D-json-value`), with nothing else before or after.

### detectable_format:multiple_sections
Text: "Your response must have {num_sections} sections. Mark the beginning of each section with {section_spliter} X, such as: {section_spliter} 1 [content of section 1] {section_spliter} 2 [content of section 2]"
A section marker is a line that starts, after optional markdown heading or
emphasis markup, with the splitter word (case-insensitive, `D-section-case`)
followed by a space and a label X (a number or word). A mention inside a
sentence (`as described in Section 2`) is not a marker. Pass iff G has
exactly {num_sections} markers, each followed by non-empty content, and no
non-empty text before the first marker other than a title line
(`D-sections-preamble`).

### detectable_format:number_bullet_lists
Text: "Your answer must contain exactly {num_bullets} bullet points. Use the markdown bullet points such as: * This is point 1. * This is point 2"
A bullet point is a line that starts, after optional indentation, with `*`,
`-` or `+` followed by a space and text (`D-bullet-markers`: proposed counts
all three markers and nested bullets). A line starting with `**bold**` or
`*italic*` is not a bullet; a numbered item is not a bullet. Pass iff the
count equals {num_bullets}.

### detectable_format:number_highlighted_sections
Text: "Highlight at least {num_highlights} sections in your answer with markdown, i.e. *highlighted section*."
A highlight is an emphasis span `*text*` or `**text**` (`D-highlight-bold`)
with non-empty, non-whitespace text on one line. A bullet marker `* ` at the
start of a line is not part of a highlight. Pass iff G has at least
{num_highlights} highlights.

### detectable_format:sentence_hyphens
Text: "All sentences must be connected using hyphens, with no spaces between them."
Pass iff every boundary between consecutive sentences is a single hyphen `-`
with no whitespace on either side, and G contains no other sentence boundary
(no space or line break between sentences). A G of one sentence passes
(`D-hyphens-single`).

### detectable_format:square_brackets
Text: "Enclose every word in your response within square brackets."
Pass iff every word of G is enclosed in its own pair of square brackets
`[word]` (`D-brackets-each`); punctuation may be inside or outside the
brackets.

### detectable_format:title
Text: "Your answer must contain a title, wrapped in double angular brackets, such as <<poem of joy>>."
Pass iff G contains `<<text>>` with non-empty, non-whitespace text on one
line, anywhere in G (`D-title-position`).

### first_word:first_word_answer
Text: "The first word of your response should be the word {first_word}."
Pass iff the first word of G (markup and punctuation before it ignored)
equals {first_word} (`D-word-case`).

### first_word:first_word_sent
Text: "The first word of each sentence should be the word {first_word}."
Pass iff G has at least one sentence and the first word of every sentence
equals {first_word}.

### keywords:existence
Text: "Include keywords ['{k1}', '{k2}'] in the response."
Pass iff every keyword occurs in G as a word (word equality above).

### keywords:forbidden_words
Text: "Do not include keywords ['{k1}', '{k2}'] in the response."
Pass iff no keyword occurs in G as a word. A different word that contains a
keyword as a substring does not violate the constraint.

### keywords:frequency
Text: "In your response, the word {keyword} should appear {relation} {frequency} times."
Pass iff the number of occurrences of {keyword} as a word meets the relation.

### keywords:keyword_specific_position
Text: "Include keyword {keyword} in the {n}-th sentence, as the {m}-th word of that sentence."
Pass iff G has an {n}-th sentence (sentence rules above) and its {m}-th word
equals {keyword}.

### keywords:letter_frequency
Text: "In your response, the letter {letter} should appear {let_relation} {let_frequency} times."
Count the occurrences of {letter} in G, ignoring case (`D-letter-case`). Pass
iff the count meets the relation.

### keywords:no_adjacent_consecutive
Text: "No two adjacent words can start with consecutive letters of the alphabet."
For each pair of adjacent words in G (adjacent in the word sequence, across
punctuation and line breaks), take their first characters, ignoring case.
Pass iff no pair consists of two Latin letters that are neighbours in the
alphabet, in either order (`D-consecutive-order`).

### keywords:palindrome
Text: "Include a palindrome in your response."
Pass iff G contains a word of at least 3 letters that reads the same
backwards ignoring case, or a phrase of several words that does so ignoring
case, spaces and punctuation (`D-palindrome-unit`, `D-palindrome-length`).

### keywords:start_end
Text: "Start and end your response with the same word (do not write anything after the last word, not even punctuation)."
Pass iff the first word of G (markup before it ignored) equals the last word
of G, and the last non-whitespace character of G is the last character of
that word.

### keywords:word_count_different_numbers
Text: "In your response, the word {keyword} should appear {frequency} times." (the kwargs also hold a `relation` that the text does not show)
Pass iff {keyword} occurs as a word exactly {frequency} times
(`D-word-count-exact`). The hidden relation is not part of the text; a
verdict that applies `less than {frequency}` contradicts every reading.

### keywords:word_once
Text: "Include keyword {keyword} in your response."
Pass iff {keyword} occurs as a word at least once (the text sets no upper
bound).

### language:response_language
Text: "Your ENTIRE response should be in {Language} language, no other language is allowed."
Pass iff G is written in the language with ISO code {language}
(`D-language-mixed`).

### last_word:last_word_answer
Text: "The last word of your response should be the word {last_word}."
Pass iff the last word of G (punctuation and markup after it ignored) equals
{last_word}.

### last_word:last_word_sent
Text: "The last word of each sentence, before punctuation, should be the word {last_word}."
Pass iff G has at least one sentence and the last word of every sentence
equals {last_word}.

### length_constraints:nth_paragraph_first_word
Text: "There should be {num_paragraphs} paragraphs. Paragraphs and only paragraphs are separated with each other by two new lines as if it was '\n\n' in python. Paragraph {nth_paragraph} must start with word {first_word}."
Pass iff G has exactly {num_paragraphs} paragraphs (blank-line form) and the
first word of paragraph {nth_paragraph} (markup before it ignored) equals
{first_word}.

### length_constraints:number_paragraphs
Text: "There should be {num_paragraphs} paragraphs. Paragraphs are separated with the markdown divider: ***"
Pass iff G has exactly {num_paragraphs} paragraphs (divider form).

### length_constraints:number_sentences
Text: "Your response should contain {relation} {num_sentences} sentences."
Pass iff the number of sentences in G meets the relation.

### length_constraints:number_words
Text: "Answer with {relation} {num_words} words."
Pass iff the number of words in G meets the relation.

### letters:letter_counting
Text: "Answer with {relation} {N} letters."
Pass iff the number of letter characters in G meets the relation.

### letters:letter_counting2
Text: same as keywords:letter_frequency. Same contract.

### paragraphs:paragraphs
Text: "There should be 2 paragraphs. Paragraphs are separated with the markdown divider: ***"
Pass iff G has exactly 2 paragraphs (divider form).

### paragraphs:paragraphs2
Text: "There should be 2 paragraphs. Paragraphs and only paragraphs are separated with each other by two line breaks."
Pass iff G has exactly 2 paragraphs (blank-line form).

### punctuation:no_comma
Text: "In your entire response, refrain from the use of any commas."
Pass iff G contains no comma character: `,` U+002C, `，` U+FF0C, `、` U+3001,
`،` U+060C, `﹐` U+FE50 (`D-comma-chars`).

### punctuation:punctuation_dot
Text: "In your entire response, refrain from the use of . (i.e. dots) as punctuation and in general."
Pass iff G contains no dot: `.` U+002E, `．` U+FF0E, `。` U+3002, `…` U+2026
(`D-dot-chars`). Dots in numbers, URLs and abbreviations count ("and in
general").

### punctuation:punctuation_exclamation
Text: "In your entire response, refrain from the use of ! (i.e. exclamation marks) as punctuation and in general."
Pass iff G contains no exclamation mark: `!` U+0021, `！` U+FF01, `¡` U+00A1,
`‼` U+203C, `❗` U+2757, `❕` U+2755 (`D-exclamation-chars`).

### startend:end_checker
Text: "Finish your response with this exact phrase {end_phrase}. No other words should follow this phrase."
Pass iff G, after trailing whitespace is stripped, ends with {end_phrase}
exactly (case and punctuation as given), optionally followed by closing
markup only (`*`, `_`, quotation marks) (`D-end-markup`).

### startend:quotation
Text: "Wrap your entire response with double quotation marks."
Pass iff G starts with a double quotation mark and ends with one: `"` ... `"`
or `“` ... `”` (`D-quote-chars`), and G is longer than the two marks.

## 2. Decision table

| Entry | Reading A | Reading B | Example: A / B verdicts | Proposed |
|---|---|---|---|---|
| D-empty-response | empty G fails every check | empty G passes checks that only forbid things (no comma, lowercase, ...) | `""` on no_comma: fail / pass | A |
| D-word-units | hyphenated compounds and contractions are one word | split at `-` and `'` | `well-known don't` = 2 / 4 words | A |
| D-word-cjk | each CJK character is a word | each whitespace-delimited run is a word | `我喜欢猫` = 4 / 1 words | open (no proposal) |
| D-word-case | keyword, first/last-word and start/end comparisons ignore case | exact case | first_word `development`, G `Development is ...`: pass / fail | A |
| D-keyword-inflection | only the exact word form counts | inflected forms count | keyword `cat`, G `Two cats.`: fail / pass | A |
| D-sentence-split | a line end also ends a sentence (headings, list items) | only `.`, `!`, `?` end a sentence | `Title\nOne. Two.` = 3 / 2 sentences | A |
| D-capital-word | one-letter capitals (`I`, `A`) count as all-capital words | only words of 2+ letters count | `I am OK` = 2 / 1 | A |
| D-language-mixed | the response is in the language, with names, numbers and code allowed | every token must be in the language | English answer naming `Wikipédia`: pass / fail | A |
| D-two-different | parts differ after stripping whitespace | parts must differ in substance | `Yes ****** Yes.`: pass / fail | A |
| D-repeat-center | only a middle word may change (3rd of 5; 3rd or 4th of 6) | any word but the first and last may change | `Every dog has a silver lining`: fail / pass | A |
| D-repeat-original | an unchanged copy breaks "transforming it each time" | unchanged copies are ignored | 2 variants + 1 exact copy, small_n 2: fail / pass | A |
| D-lowercase-count | only lowercase occurrences count | case-insensitive occurrences count | N 2, `The the the`: pass / fail | A |
| D-placeholder | any non-empty `[text]` counts | only fill-in slots count (`[name]`, not `[1]` or link text) | `[1]` cites: count / not | A |
| D-postscript-case | marker case as given | case-insensitive | `p.s. hi` for `P.S.`: fail / pass | A |
| D-postscript-position | the postscript is the last paragraph | a postscript anywhere | `P.S. hi\n\nMore text.`: fail / pass | A |
| D-bigram-odd | an odd word count may end with a one-word group | every group must have exactly two words | `<<I am>> <<here>>`: pass / fail | A |
| D-constrained-extra | other text may accompany one option | G is exactly one option | `My answer is yes. Because ...`: pass / fail | A |
| D-json-value | only an object or array | any JSON value | `"hello"`: fail / pass | A |
| D-section-case | splitter matched ignoring case | exact case | `Section 1` for `SECTION`: pass / fail | A |
| D-sections-preamble | a title line may precede the first marker, other text may not | any text may precede the first marker | intro paragraph then 2 markers (n 2): fail / pass | A |
| D-bullet-markers | `*`, `-`, `+` bullets and nested bullets count | only top-level `*` bullets count | `- a\n- b` for 2: pass / fail | A |
| D-highlight-bold | `**bold**` counts as a highlight | only single-asterisk `*italic*` | `**a** **b**` for 2: pass / fail | A |
| D-hyphens-single | a single sentence fails (nothing is connected) | a single sentence passes vacuously | `Hello there.`: fail / pass | B (vacuous pass; the text forbids only unconnected sentences) |
| D-brackets-each | each word in its own brackets | one pair around the whole response | `[Hello world]`: fail / pass | A |
| D-title-position | the title may be anywhere | the title must open the response | `Intro.\n<<T>>`: pass / fail | A |
| D-consecutive-order | neighbours in either order | only ascending order (`a` then `b`) | `boy ate`: fail / pass | A |
| D-palindrome-unit | a whole word or whole phrase | any palindromic letter run inside a word | `never` (contains `eve`): fail / pass | A |
| D-palindrome-length | at least 3 letters | any length (`a`, `I`, `oo`) | `I am here`: fail / pass | A |
| D-word-count-exact | exactly {frequency} times | at least {frequency} times | frequency 2, word appears 3 times: fail / pass | A |
| D-paragraph-blank-lines | any run of 2+ line breaks is one separator | only exactly `\n\n`; `\n\n\n` makes an empty paragraph | `a\n\n\nb` for 2 paragraphs: pass / fail | A |
| D-divider-form | divider is a line holding exactly the given form (`***`; `* * *` for counting_composition) | any markdown thematic break (`***`, `* * *`, `---`) | `a\n---\nb` for 2: fail / pass | A |
| D-divider-edges | every part must be non-empty (no divider at the start or end) | empty edge parts are ignored | `a\n***\nb\n***` for 2: fail / pass | A |
| D-divider-blank-lines | blank lines inside a part do not split it | blank lines also split paragraphs | `a\n\nb\n***\nc` for 2: pass / fail | A |
| D-letter-case | letter count ignores case | exact case | letter `a`, G `A a`: 2 / 1 | A |
| D-comma-chars | all comma characters | ASCII `,` only | `你好，世界` on no_comma: fail / pass | A |
| D-dot-chars | `.`, `．`, `。`, `…` | ASCII `.` only | `你好。` on punctuation_dot: fail / pass | A |
| D-exclamation-chars | `!`, `！`, `¡`, `‼`, `❗`, `❕` | ASCII `!` only | `好！` on punctuation_exclamation: fail / pass | A |
| D-end-markup | closing markup after the phrase allowed | nothing may follow the phrase | `**Any other questions?**`: pass / fail | A |
| D-quote-chars | `"` or the typographic pair `“ ”` | ASCII `"` only | `“Hi”`: pass / fail | A |
