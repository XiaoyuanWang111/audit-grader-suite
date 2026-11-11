# Contracts for the 47 instruction checks of the RLVR1 instruction-following rows

Written from the requirement text that the model sees in the user message (surveyed with `audit/scripts/survey_templates.py` and `audit/scripts/template_coverage.py`, data only), before reading any grader code. Every one of the 28,219 constraints carries its id's main template below with its kwargs filled in, except surface variation from the prose joiner (a dropped final period; see `D-ps-marker`). `{x}` marks a kwarg value. A reading marked **Proposed** is the contract's reading of a decision entry; the alternative is listed in the decision table at the end.

## 0. Common definitions

**Graded text.**
- Non-reasoning models (Qwen2.5-7B-Instruct, Qwen3-4B-Instruct-2507, OLMo-2-1124-7B-Instruct): the whole response as generated. These models have no reasoning channel; a literal `<think>` that such a model writes is part of its answer (`D-literal-think`).
- Reasoning model (Qwen3-4B-Thinking-2507, whose chat template opens `<think>` in the prompt): the text after the last `</think>`. A response without `</think>` is an extraction failure: it fails every check, and it is counted separately. Thinking text is never graded.
- A truncated response (`finish_reason` = `length`) is graded as written; truncation is counted separately.

**Row verdict.** The SkyRL reward is 1.0 iff every constraint of the row passes (binary). The task-curation gate must fail a row (reward 0.0, judge not called) iff at least one of its deterministic constraints fails; the four semantic ids (`count:count_unique`, `detectable_format:bigram_wrapping`, `language:response_language`, `letters:letter_counting`) are not gated and their contract applies to the SkyRL reward only.

**Word** (`D-word`). Proposed: a maximal run of Unicode letters, digits and combining marks, with internal apostrophes (`'`, `’`) and internal hyphens kept inside the word (`don't`, `well-known` are one word). Punctuation and markdown symbols around a word are not part of it. For CJK text without spaces, each run of non-space characters between separators is one word (word-level checks are rarely meaningful there).

**Word comparison** (`D-word-case`). Proposed: a required, forbidden or counted word matches a word of the response when the two are equal ignoring case; a word that only contains it (`options` for `option`, `action` for `act`) does not match (`D-keyword-match`).

**Sentence** (`D-sentence`). Proposed: sentences end at a run of `.`, `!`, `?` (or `。！？`) followed by whitespace or the end of the text, and at every line break; empty pieces and pieces without a letter or digit (markdown rules, bullets alone) are not sentences. Common abbreviations (`Mr.`, `Dr.`, `e.g.`, `i.e.`, `U.S.`, `etc.` before a lowercase word) do not end a sentence. A list item or heading on its own line is a sentence.

**Paragraph separated by two new lines / two line breaks** (`D-paragraph-split`). Proposed: paragraphs are the non-empty blocks between runs of one or more blank lines (a blank line may contain only whitespace); a single line break inside a block does not separate paragraphs. The number of paragraphs is the number of non-empty blocks.

**Markdown divider `***`** (`D-divider`). Proposed: a line whose only content (after stripping whitespace) is `***`. Paragraphs are the pieces between dividers; every piece must contain non-whitespace text.

**Letters.** A letter is a Unicode alphabetic character. "The letter x" is counted ignoring case (`x` and `X`) (`D-letter-case`).

**Empty graded text.** Every check is applied literally: an empty response passes a check that only forbids something (no commas) and fails a check that requires something. Step 4 lists these passes.

## 1. Contracts per check

### change_case:capital_word_frequency
Text: "In your response, words with all capital letters should appear {capital_relation} {capital_frequency} times." (relation `less than` or `at least`)
- A capital word is a word with at least one cased letter and no lowercase letter (`NASA`, `I`, `A`, `COVID-19`). Proposed: single-letter words such as `I` count (`D-capital-word`).
- Pass: count < N for `less than`; count ≥ N for `at least`.

### change_case:english_capital
Text: "Your entire response should be in English, and in all capital letters."
- Pass: the response is in English (`D-english`: proposed, a language identifier run on the whole graded text returns English, or the text is English to a reader if the identifier is unsure) and contains no lowercase letter (any script with case).
- Fail: any lowercase letter; a response in another language; an empty response.

### change_case:english_lowercase
Text: "Your entire response should be in English, and in all lowercase letters. No capital letters are allowed."
- Pass: in English (`D-english`) and no uppercase letter anywhere.
- Fail: any uppercase letter; another language; empty.

### combination:two_responses
Text: "Give two different responses. Responses and only responses should be separated by 6 asterisk symbols: ******."
- Pass: the graded text contains exactly one separator `******` (a run of exactly six asterisks, `D-two-responses-separator`), the parts before and after it both contain non-whitespace text, and the two parts differ after stripping whitespace.
- Fail: no separator, two or more separators, an empty part, identical parts.

### copy:repeat_phrase
Text: "Repeat the phrase {phrase} exactly {small_n} times, transforming it slightly each time by replacing only one word in the center of the phrase."
- A variant of the phrase is a word sequence with the phrase's number of words that differs from the phrase in exactly one word, compared ignoring case; the first and last words are unchanged. Proposed: the replaced word is any word other than the first and the last (`D-repeat-center`; the alternative requires the middle word, or one of the two middle words for an even length).
- Pass: the response contains exactly {small_n} variants. Proposed: an unchanged copy of the phrase is not a repetition and does not count, and it does not by itself fail the check (`D-repeat-exact-copy`).

### count:count_unique (semantic in task curation; SkyRL only)
Text: "Only use unique words in your response, no word should be repeated!"
- Pass: no word occurs twice, comparing words ignoring case. Fail: any repeated word.

### count:counting_composition (1 constraint)
Text: "Write 3 paragraphs, delimited by the markdown divider: * * *, with exactly {n_sent} sentences each, with exactly {n_words} words in each sentence."
- Pass: dividers (a line `* * *`; proposed to also accept `***`, `D-divider`) split the text into exactly 3 non-empty paragraphs; each has exactly {n_sent} sentences; each sentence has exactly {n_words} words.

### count:lowercase_counting
Text: "In your response, all lowercase words should appear at most {N} times."
- A lowercase word is a word with at least one cased letter and no uppercase letter. Proposed: occurrences are counted per exact lowercase form; `The` is not an occurrence of `the` (`D-lowercase-count`).
- Pass: every lowercase word occurs at most N times. Fail: some lowercase word occurs N+1 or more times.

### detectable_content:number_placeholders
Text: "The response must contain at least {num_placeholders} placeholders represented by square brackets, such as [address]."
- A placeholder is a span `[...]` with non-whitespace content and no bracket inside. Proposed: any such span counts, including a markdown link text or a citation like `[1]` (`D-placeholder`).
- Pass: at least N placeholders.

### detectable_content:postscript
Text: "At the end of your response, please explicitly add a postscript starting with {postscript_marker}" (`P.S.` or `P.P.S`; in 147 prose-joined constraints the model sees `P.S` without the final period).
- Pass: some line of the graded text starts, after optional whitespace and markdown emphasis (`*`, `_`, `#`), with the marker, case-sensitively. The postscript runs from that line to the end, so it is at the end by construction. A `P.P.S` line does not start with `P.S.`.
- Proposed (`D-ps-marker`): for marker `P.S.`, a line starting `P.S` followed by `:` or a space also passes when the prompt shows `P.S` without the period; for `P.P.S`, any character may follow.
- Fail: no line starts with the marker; the marker only appears mid-line.

### detectable_format:bigram_wrapping (semantic in task curation; SkyRL only)
Text: "Wrap every word bigram in double angular brackets, such as <<I am>> <<at home>> <<with my>> <<cute dog>>."
- Pass: every word of the graded text lies inside a `<<...>>` group, and every group holds exactly two words; proposed, a final group of one word is allowed when the number of words is odd (`D-bigram-odd`).

### detectable_format:constrained_response
Text: "Answer with one of the following options: ('My answer is yes.', 'My answer is no.', 'My answer is maybe.')"
- Proposed (`D-constrained-surround`): pass iff the graded text, stripped of surrounding whitespace, equals one of the three options exactly. Alternative: the text contains exactly one of the options, with other text allowed.

### detectable_format:json_format
Text: "Entire output should be wrapped in JSON format. You can use markdown ticks such as ```."
- Pass: after stripping whitespace and at most one enclosing code fence (``` with an optional language tag), the whole remaining text parses as one JSON value. Proposed: the value must be an object or an array (`D-json-value`). Text outside the fence fails.

### detectable_format:multiple_sections
Text: "Your response must have {num_sections} sections. Mark the beginning of each section with {section_spliter} X, such as:" followed by `{section_spliter} 1` / `[content of section 1]` / `{section_spliter} 2` / `[content of section 2]`.
- A section marker is a line that starts, after optional markdown (`#`, `*`, whitespace), with the splitter word and a number. Proposed: the splitter word is matched case-sensitively as given (`SECTION` or `Section`) (`D-sections-case`), and text before the first marker is allowed.
- Pass: exactly N markers. Fail: any other count; markers only mid-sentence do not count.

### detectable_format:number_bullet_lists
Text: "Your answer must contain exactly {num_bullets} bullet points. Use the markdown bullet points such as:" followed by `* This is point 1.` / `* This is point 2`.
- A bullet point is a line that starts, after optional indentation, with `*`, `-` or `+` followed by a space and text (`D-bullet-marker`: proposed, all three markdown markers count). A horizontal rule (`***`, `---`) or bold text (`**x**`) is not a bullet. Proposed: nested bullets count (`D-bullet-nested`). Numbered items are not bullet points.
- Pass: exactly N bullet points.

### detectable_format:number_highlighted_sections
Text: "Highlight at least {num_highlights} sections in your answer with markdown, i.e. *highlighted section*."
- A highlighted section is a markdown emphasis span with non-whitespace content on one line. Proposed: both `*text*` and `**text**` count, each span once (`D-highlight-markup`).
- Pass: at least N spans.

### detectable_format:sentence_hyphens
Text: "All sentences must be connected using hyphens, with no spaces between them."
- Pass: the stripped graded text has no line break, and wherever one sentence ends (terminal punctuation) and another follows, they are joined by `-` with no whitespace on either side. Proposed: a single sentence passes (`D-hyphens-single`).
- Fail: two sentences separated by whitespace; a joining hyphen with a space on either side; line breaks.

### detectable_format:square_brackets
Text: "Enclose every word in your response within square brackets."
- Proposed (`D-brackets-each`): every word is enclosed in its own `[...]` group: each group holds exactly one word, optionally with punctuation, and no word character appears outside a group. Alternative: every word lies inside some bracketed group, groups may hold several words.

### detectable_format:title
Text: "Your answer must contain a title, wrapped in double angular brackets, such as <<poem of joy>>."
- Pass: the graded text contains `<<...>>` with non-whitespace content and no line break inside. Position is free (`D-title-position`: proposed anywhere).

### first_word:first_word_answer
Text: "The first word of your response should be the word {first_word}."
- Pass: the first word of the graded text, ignoring leading whitespace, punctuation and markdown symbols, equals {first_word} ignoring case.

### first_word:first_word_sent
Text: "The first word of each sentence should be the word {first_word}."
- Pass: there is at least one sentence and every sentence's first word equals {first_word} ignoring case (`D-sentence`).

### keywords:existence
Text: "Include keywords {keywords} in the response." (a Python list of two words)
- Pass: every keyword occurs as a word, ignoring case (`D-keyword-match`).

### keywords:forbidden_words
Text: "Do not include keywords {forbidden_words} in the response."
- Pass: no forbidden word occurs as a word, ignoring case. Proposed (`D-keyword-match`): an inflected form (`options` for `option`) or a longer word containing it does not violate.

### keywords:frequency
Text: "In your response, the word {keyword} should appear {relation} {frequency} times."
- Count the occurrences of {keyword} as a word, ignoring case. Pass: count < N (`less than`) or ≥ N (`at least`).

### keywords:keyword_specific_position
Text: "Include keyword {keyword} in the {n}-th sentence, as the {m}-th word of that sentence."
- Pass: the response has at least {n} sentences, and the {m}-th word (1-based) of sentence {n} (1-based) equals {keyword} ignoring case and surrounding punctuation.

### keywords:letter_frequency
Text: "In your response, the letter {letter} should appear {let_relation} {let_frequency} times."
- Count the letter ignoring case. Pass: count < N (`less than`) or ≥ N (`at least`).

### keywords:no_adjacent_consecutive
Text: "No two adjacent words can start with consecutive letters of the alphabet."
- For each pair of adjacent words whose first characters are both Latin letters, compare the letters ignoring case. Proposed: letters are consecutive when they differ by one in either order (`b`,`c` and `c`,`b`) (`D-consecutive-order`); no wrap from `z` to `a`.
- Pass: no adjacent pair is consecutive.

### keywords:palindrome
Text: "Include a palindrome in your response."
- Proposed (`D-palindrome`): pass iff some word, or some run of consecutive words read without spaces and punctuation, of at least 3 letters reads the same backwards ignoring case (`did`, `level`, `never odd or even`). A one- or two-letter word (`a`, `I`, `oo`) does not count.

### keywords:start_end
Text: "Start and end your response with the same word (do not write anything after the last word, not even punctuation)."
- Pass: the graded text, after stripping whitespace, ends with a word character (no trailing punctuation or symbol), and its first word (ignoring leading punctuation and markdown) equals its last word ignoring case.

### keywords:word_count_different_numbers
Text: "In your response, the word {keyword} should appear {frequency} times." (the kwargs also hold `relation`, `at least` in 320 and `less than` in 206 constraints, which the text does not show)
- Proposed (`D-word-count-relation`): the count of {keyword} as a word, ignoring case, equals {frequency}. Alternative: at least {frequency}. No reading of the text gives "fewer than {frequency}", so a response with exactly {frequency} occurrences passes under every reading.

### keywords:word_once
Text: "Include keyword {keyword} in your response."
- Pass: {keyword} occurs at least once as a word, ignoring case.

### language:response_language (semantic in task curation; SkyRL only)
Text: "Your ENTIRE response should be in {Language} language, no other language is allowed." (30 languages, code in kwargs, name in text, mapping consistent in all 780 constraints)
- Proposed (`D-language-mixed`): pass iff the graded text is written in {Language}; names, numbers, code and technical terms in Latin script do not by themselves make it another language.

### last_word:last_word_answer
Text: "The last word of your response should be the word {last_word}."
- Pass: the last word of the graded text, ignoring trailing punctuation and markdown symbols, equals {last_word} ignoring case.

### last_word:last_word_sent
Text: "The last word of each sentence, before punctuation, should be the word {last_word}."
- Pass: there is at least one sentence, and the last word of every sentence equals {last_word} ignoring case.

### length_constraints:nth_paragraph_first_word
Text: "There should be {num_paragraphs} paragraphs. Paragraphs and only paragraphs are separated with each other by two new lines as if it was '\n\n' in python. Paragraph {nth_paragraph} must start with word {first_word}."
- Pass: exactly {num_paragraphs} paragraphs (`D-paragraph-split`), and the first word of paragraph {nth_paragraph}, ignoring leading punctuation and markdown symbols, equals {first_word} ignoring case.

### length_constraints:number_paragraphs
Text: "There should be {num_paragraphs} paragraphs. Paragraphs are separated with the markdown divider: ***"
- Pass: the dividers (`D-divider`) split the text into exactly N non-empty paragraphs (no divider when N = 1).

### length_constraints:number_sentences
Text: "Your response should contain {relation} {num_sentences} sentences."
- Pass: sentence count (`D-sentence`) < N or ≥ N.

### length_constraints:number_words
Text: "Answer with {relation} {num_words} words."
- Pass: word count (`D-word`) < N or ≥ N.

### letters:letter_counting (semantic in task curation; SkyRL only)
Text: "Answer with {relation} {N} letters." (N is 2 or 3)
- Proposed (`D-letter-counting`): count the alphabetic characters of the graded text; pass iff count < N or ≥ N.

### letters:letter_counting2
Text: identical to `keywords:letter_frequency`. Same contract.

### paragraphs:paragraphs
Text: "There should be 2 paragraphs. Paragraphs are separated with the markdown divider: ***" (kwargs empty)
- Pass: exactly 2 non-empty paragraphs separated by one divider (`D-divider`).

### paragraphs:paragraphs2
Text: "There should be 2 paragraphs. Paragraphs and only paragraphs are separated with each other by two line breaks." (kwargs empty)
- Pass: exactly 2 paragraphs (`D-paragraph-split`).

### punctuation:no_comma
Text: "In your entire response, refrain from the use of any commas."
- Proposed (`D-comma-chars`): fail on any comma character: `,` U+002C, `，` U+FF0C, `、` U+3001, `،` U+060C, `﹐` U+FE50, `﹑` U+FE51. Pass otherwise.

### punctuation:punctuation_dot
Text: "In your entire response, refrain from the use of . (i.e. dots) as punctuation and in general."
- Proposed (`D-dot-chars`): fail on `.` U+002E, `．` U+FF0E, `。` U+3002 and `…` U+2026. Pass otherwise. Dots inside numbers, URLs and abbreviations count ("and in general").

### punctuation:punctuation_exclamation
Text: "In your entire response, refrain from the use of ! (i.e. exclamation marks) as punctuation and in general."
- Proposed (`D-exclamation-chars`): fail on `!` U+0021, `！` U+FF01, `¡` U+00A1. Pass otherwise.

### startend:end_checker
Text: "Finish your response with this exact phrase {end_phrase}. No other words should follow this phrase."
- Proposed (`D-end-trailing`): pass iff the graded text, after stripping trailing whitespace, ends with {end_phrase} exactly (case-sensitive). Alternative: trailing non-word characters (markdown `**`, a closing quote) after the phrase are allowed, since only "words" are forbidden.

### startend:quotation
Text: "Wrap your entire response with double quotation marks."
- Pass: the stripped graded text is at least two characters long, starts with a double quotation mark and ends with one. Proposed (`D-quote-chars`): `"` or the curly pair `“`…`”` count.

## 2. Decision table

| Id | Question | Proposed reading (contract) | Alternative reading | Example: proposed / alternative verdict |
|---|---|---|---|---|
| D-literal-think | Is a literal `<think>` written by a non-reasoning model part of the graded text? | yes, whole response graded | strip from `<think>` to the end as an unclosed reasoning block | Qwen2.5 answer `Use <think> tags. Done`: graded in full / only `Use ` graded |
| D-word | What is a word? | runs of letters/digits/marks with internal `'` and `-` | whitespace-separated tokens | `well-known,` = 1 word `well-known` / token `well-known,` |
| D-word-case | Case in word comparisons | ignore case | exact case | first word `Development` for `development`: pass / fail |
| D-keyword-match | Does an inflection or a containing word match a keyword? | no, whole words only | substring match | forbidden `option`, response `options`: pass / fail |
| D-sentence | Sentence boundaries | terminal punctuation + space, every line break, abbreviations kept | terminal punctuation only (lines without punctuation merge) | `Title\nBody text.` = 2 sentences / 1 |
| D-paragraph-split | Paragraph separator for "two new lines" | one or more blank lines, empty blocks dropped | exactly `\n\n`, every piece counts | `a\n\n\n\nb` = 2 paragraphs / 3 pieces |
| D-divider | Form of the `***` divider | a line of exactly `***` | any `***` substring, or `* * *`/`---` too | `a ***b` inline: 1 paragraph / 2 |
| D-letter-case | Case in letter counts | ignore case | lowercase only | `Sss` has 3 / 2 `s` |
| D-capital-word | Do one-letter words like `I` count as capital words? | yes | no | `I am` has 1 / 0 capital words |
| D-english | How is "in English" decided? | language ID on the whole text, reader when unsure | every sentence must be English | mostly English with one Chinese name: pass / fail |
| D-two-responses-separator | Does a run of 7+ asterisks count as the separator? | no, exactly six | any run of 6+ | `a *******b`: fail / pass |
| D-repeat-center | Which word may be replaced? | any word but first and last | only the middle word(s) | phrase "Time flies when having fun", variant "Time flies when making fun" (4th of 5 words replaced): pass / fail |
| D-repeat-exact-copy | Does an unchanged copy count, or fail? | neither | counts as a repetition | phrase once unchanged + N variants: pass / fail |
| D-lowercase-count | Are `The` and `the` the same lowercase word? | no, exact lowercase form | yes | `the The the` with N=2: pass / fail |
| D-placeholder | Do links and citations count as placeholders? | yes, any `[x]` | only placeholder-like names | `[1]` counts / does not |
| D-ps-marker | `P.S` without period when the prompt shows `P.S` | passes | fails | `P.S: thanks` (prompt shows `P.S`): pass / fail |
| D-bigram-odd | Odd word count: final one-word group | allowed | not allowed | `<<a b>> <<c>>`: pass / fail |
| D-constrained-surround | Text around the option | not allowed | allowed if exactly one option appears | `My answer is yes. Because...`: fail / pass |
| D-json-value | Must the JSON be an object or array? | yes | any JSON value | `"hello"`: fail / pass |
| D-sections-case | Case of the splitter word | as given | ignore case | `Section 1` when asked `SECTION`: fail / pass |
| D-bullet-marker | Which bullet markers count | `*`, `-`, `+` | `*` only (as in the example) | `- a\n- b` for N=2: pass / fail |
| D-bullet-nested | Do nested bullets count | yes | top level only | 2 bullets + 1 nested for N=2: fail / pass |
| D-highlight-markup | Does bold `**x**` count as a highlight | yes | only `*x*` | `**A** **B**` for N=2: pass / fail |
| D-hyphens-single | Does a one-sentence response pass sentence_hyphens | yes | needs two or more sentences | `Hello world.`: pass / fail |
| D-brackets-each | One word per bracket group | yes | groups may hold several words | `[hello world]`: fail / pass |
| D-title-position | Title position | anywhere | first line | text then `<<T>>`: pass / fail |
| D-consecutive-order | Is `c` then `b` consecutive | yes, either order | ascending only | `cat bat`: fail / pass |
| D-palindrome | Minimum palindrome | 3+ letters, whole word or word run | any word incl. `a`, `I` | `I saw a cat`: fail / pass |
| D-word-count-relation | `word_count_different_numbers` count | exactly N | at least N | 3 occurrences for N=2: fail / pass |
| D-language-mixed | Latin-script names or code in a non-Latin-language answer | allowed | not allowed | Hindi text with `Python` code: pass / fail |
| D-letter-counting | "Answer with at least N letters" | alphabetic characters of the text | (none found) | – |
| D-comma-chars | Non-ASCII commas | count | ASCII only | `你好，世界`: fail / pass |
| D-dot-chars | Non-ASCII dots | count | ASCII only | `你好。`: fail / pass |
| D-exclamation-chars | Non-ASCII exclamation marks | count | ASCII only | `好！`: fail / pass |
| D-end-trailing | Non-word characters after the end phrase | not allowed | allowed | `Any other questions?**`: fail / pass |
| D-quote-chars | Curly quotes | count | ASCII only | `“text”`: pass / fail |
| D-empty | Empty graded text | literal (passes pure prohibitions) | fails every check | `""` on no_comma: pass / fail |
