# Contracts for the 47 instruction checks of the RLVR1 instruction-following rows

Written from the instruction text that the model sees in each row's prompt, before any grader code was read. The instruction text of each id was taken from the prompts (audit/scripts/show_instr.py) and checked against every constraint's kwargs (audit/scripts/template_check.py: all 28,219 constraints match their template; see "Rendering notes"). Sources: `case/TASK.md` (how each pipeline forms a reward) and `case/data/rlvr1_instruction_following.jsonl`.

Each contract gives the pass and fail conditions. Where the text allows two verdicts, the contract states the proposed reading and names a decision entry `D-<topic>`, listed at the end with both readings, an example of each and the proposal.

## 1. Graded text

- G1. Non-reasoning model: the graded text is the whole response the model generated.
- G2. Reasoning model (Qwen3 thinking): the graded text is the text after the last `</think>`. The reasoning field is never graded. A response with no `</think>` is an extraction failure: it fails every check of its row, and the report counts these responses separately.
- G3. A response cut by the token limit is graded as written (the cut text is the model's answer); the report counts truncated responses separately.
- G4. Leading and trailing whitespace of the graded text is not part of the answer (`D-outer-whitespace`, proposed: ignored). Whitespace inside the text counts where a check depends on it (paragraph breaks, hyphen joins).

## 2. Reward contracts

- R1 (grader A, SkyRL binary reward). Reward 1.0 if and only if the graded text passes every constraint of the row; 0.0 otherwise. A constraint whose check raises is a grading failure: it must not pass, and it must be reported apart from model failures; one exception must not stop grading of other rows.
- R2 (grader B, task-curation gate). The gate must fail (reward 0.0, judge not called) if and only if the graded text fails at least one deterministic (non-semantic) constraint of the row. The semantic constraints (`count:count_unique`, `detectable_format:bigram_wrapping`, `language:response_language`, `letters:letter_counting`) go to the judge, outside this audit; their contracts below apply to grader A only.
- R3. A row's verdict cannot depend on the order of its constraints, on the process, or on the run (no randomness).

## 3. Shared definitions

- Word: a maximal run of letters, digits, apostrophes and hyphens that contains at least one letter or digit, with leading and trailing apostrophes and hyphens removed. Punctuation and markdown symbols (`* _ # > \` " [ ] ( ) < >`) are not part of a word (`D-word`). For text without spaces between words (Chinese, Japanese, Thai), word counts are not defined by the text (`D-word-cjk`, proposed: each CJK ideograph or kana run segment counts as one word per character; such responses are rare in instructions that count words).
- Keyword occurrence: a word equal to the keyword, compared case-insensitively. A longer word that contains the keyword (`beers`, `beerhall`, `swordfish` for `sword`) is not an occurrence; a hyphen or apostrophe compound part is not an occurrence either (`beer-garden`; `D-keyword-match`, proposed: whole word only). Multi-word keywords do not occur in this data (every keyword is one lowercase word, see Rendering notes).
- Sentence: a maximal span of text that ends with `.`, `!` or `?` (one or more, optionally followed by closing quotes or brackets) followed by whitespace or the end of the text, or that ends at a line break that ends a line without such punctuation (a heading, a list item, a title line), or at the end of the text. Decimal points, abbreviation dots (`e.g.`, `Mr.`) and dots inside URLs do not end a sentence (`D-sentence`, proposed: as stated; the alternative ignores line breaks and splits only at `.!?`).
- First word of a text: the first word after skipping whitespace, punctuation and markdown symbols. Last word: the last word before trailing whitespace, punctuation and markdown symbols (`D-edge-markup`, proposed: skipped). Word comparisons are case-insensitive (`D-word-case`, proposed: case-insensitive).
- Relations: "at least N" means count >= N; "less than N" means count < N; "at most N" means count <= N; "exactly N" or a bare "N times" means count == N.

## 4. Contracts per check

Instruction text as rendered, with `{}` for kwargs.

### change_case

- `change_case:capital_word_frequency` — "In your response, words with all capital letters should appear {at least|less than} {N} times." Count the words that contain at least one cased letter and no lowercase letter (`HELLO`, `USA`, `COVID-19`, `I`, `A`). Pass iff the count meets the relation. Single-letter words such as `I` and `A` count (`D-allcaps-single`, proposed: they count, since they are words in all capital letters).
- `change_case:english_capital` — "Your entire response should be in English, and in all capital letters." Fail if the graded text contains any lowercase letter (any script that has case). Fail if the text is not English (`D-english`, proposed: the prose is English; code, numbers, URLs and proper names are allowed; a response in another language fails even when it has no lowercase letters).
- `change_case:english_lowercase` — "Your entire response should be in English, and in all lowercase letters. No capital letters are allowed." Fail if the graded text contains any uppercase or titlecase letter; fail if not English (`D-english`).

### combination

- `combination:two_responses` — "Give two different responses. Responses and only responses should be separated by 6 asterisk symbols: ******." The separator is a run of exactly six `*` (a run of seven or more is not it). Pass iff the separator occurs exactly once, both parts are non-empty after trimming whitespace, and the two parts differ after trimming whitespace. The separator need not be on its own line.

### copy

- `copy:repeat_phrase` — "Repeat the phrase {phrase} exactly {small_n} times, transforming it slightly each time by replacing only one word in the center of the phrase." A variant is a word sequence in the graded text with the phrase's word count that equals the phrase, compared case-insensitively word by word, at every position but one, where the word differs; that position must be in the center of the phrase (`D-repeat-center`, proposed: the middle word of a 5-word phrase, either middle word of a 6-word phrase). Pass iff the graded text contains exactly `small_n` variants. The original phrase may also appear (for example quoted in an introduction) and does not count as a repetition (`D-repeat-original`, proposed: allowed and not counted). Variants need not differ from each other.

### count

- `count:count_unique` — "Only use unique words in your response, no word should be repeated!" Fail iff some word occurs twice, compared case-insensitively (`D-word-case`). Grader A only.
- `count:counting_composition` — "Write 3 paragraphs, delimited by the markdown divider: * * *, with exactly {n_sent} sentences each, with exactly {n_words} words in each sentence." Pass iff the text, split at lines that consist of the divider `* * *`, has exactly 3 non-empty paragraphs, each with exactly `n_sent` sentences of exactly `n_words` words. One row.
- `count:lowercase_counting` — "In your response, all lowercase words should appear at most {N} times." A lowercase word is a word with at least one letter and no uppercase letter. Pass iff each distinct lowercase word occurs at most N times (`D-lowercase-counting`, proposed: per word; the other reading caps the total number of lowercase words at N).

### detectable_content

- `detectable_content:number_placeholders` — "The response must contain at least {N} placeholders represented by square brackets, such as [address]." A placeholder is `[` + text with at least one non-space character and no `[`, `]` or line break + `]`. Pass iff the count >= N. A markdown link's `[text]` also has the shape of a placeholder and counts (`D-placeholder-link`, proposed: counts, as the text defines placeholders by their brackets).
- `detectable_content:postscript` — "At the end of your response, please explicitly add a postscript starting with {P.S.|P.P.S}." Pass iff a line of the graded text starts with the marker (after optional whitespace and markdown emphasis or heading symbols), and that postscript is at the end: no line after the marker line belongs to the main answer (`D-postscript-end`, proposed: the marker line is in the last block of the text, where blocks are separated by blank lines; the alternative accepts the marker on any line). The marker is matched case-sensitively; when the marker is `P.S.`, `P.S` followed by `.` is required unless the prompt shows `P.S` without the dot (see Rendering notes; `D-postscript-dot`, proposed: the text the model saw decides). `P.P.S` matches `P.P.S` and `P.P.S.`.

### detectable_format

- `detectable_format:bigram_wrapping` — "Wrap every word bigram in double angular brackets, such as <<I am>> <<at home>> <<with my>> <<cute dog>>." Pass iff every word is inside a `<<...>>` group and every group holds exactly two words; punctuation outside groups is allowed. With an odd number of words, one final group of one word is allowed (`D-bigram-odd`, proposed: allowed). Grader A only.
- `detectable_format:constrained_response` — "Answer with one of the following options: ('My answer is yes.', 'My answer is no.', 'My answer is maybe.')" Pass iff the graded text contains exactly one of the three option strings, and nothing else beyond whitespace (`D-constrained-exact`, proposed: the whole graded text is one option; the other reading allows extra text around exactly one option).
- `detectable_format:json_format` — "Entire output should be wrapped in JSON format. You can use markdown ticks such as ```." Pass iff the graded text, trimmed, either parses as JSON, or is one fenced code block (opening fence with an optional language tag such as `json`, closing fence) whose content parses as JSON. Text outside the fence fails. A JSON scalar (a bare string or number) passes (`D-json-scalar`, proposed: only an object or array passes; "wrapped in JSON format" asks for a JSON structure).
- `detectable_format:multiple_sections` — "Your response must have {N} sections. Mark the beginning of each section with {SECTION|Section} X, such as: ..." A section marker is a line that starts (after optional markdown heading or emphasis symbols) with the given word followed by a space and a number. Pass iff there are exactly N markers. The marker word is matched case-sensitively as given (`D-section-case`, proposed: case-sensitive; the alternative accepts `Section` for `SECTION`). Text before the first marker is allowed (`D-section-preamble`, proposed: allowed). Numbers need not be in order (`D-section-numbering`, proposed: any numbers).
- `detectable_format:number_bullet_lists` — "Your answer must contain exactly {N} bullet points. Use the markdown bullet points such as: * This is point 1. * This is point 2" A bullet point is a line that starts, after optional indentation, with `*`, `-` or `+`, then a space, then text; a horizontal rule (`***`, `* * *`, `---`) and a bold line (`**Title**`) are not bullets. Pass iff the count of bullet lines, nested ones included, is exactly N (`D-bullet-marker`, proposed: `*`, `-` and `+` all count; the alternative counts only `*`).
- `detectable_format:number_highlighted_sections` — "Highlight at least {N} sections in your answer with markdown, i.e. *highlighted section*." A highlight is a span `*text*` with non-empty text that does not start or end with a space, on one line. Pass iff the count >= N. A bold span `**text**` also counts as one highlight (`D-highlight-bold`, proposed: counts; the alternative counts only single-asterisk spans).
- `detectable_format:sentence_hyphens` — "All sentences must be connected using hyphens, with no spaces between them." Pass iff every two consecutive sentences are joined by a hyphen with no whitespace on either side, so the text between the end of one sentence and the start of the next is exactly `-`. A one-sentence response passes. A line break between sentences fails.
- `detectable_format:square_brackets` — "Enclose every word in your response within square brackets." Pass iff every word is inside its own bracket pair `[word]`; punctuation outside brackets is allowed. A bracket pair with several words does not enclose each word (`D-brackets-per-word`, proposed: one word per pair; the alternative accepts any word inside some pair).
- `detectable_format:title` — "Your answer must contain a title, wrapped in double angular brackets, such as <<poem of joy>>." Pass iff the graded text contains `<<` + text with at least one non-space character and no line break + `>>`. The title may be anywhere (`D-title-position`, proposed: anywhere, as "contain" says).

### first_word

- `first_word:first_word_answer` — "The first word of your response should be the word {w}." Pass iff the first word of the graded text equals w (`D-edge-markup`, `D-word-case`).
- `first_word:first_word_sent` — "The first word of each sentence should be the word {w}." Pass iff every sentence's first word equals w (`D-sentence`).

### keywords

- `keywords:existence` — "Include keywords [{k1}, {k2}] in the response." Pass iff every keyword occurs (keyword occurrence as defined above).
- `keywords:forbidden_words` — "Do not include keywords [{k1}, {k2}] in the response." Fail iff any keyword occurs.
- `keywords:frequency` — "In your response, the word {k} should appear {at least|less than} {N} times." Pass iff the number of occurrences meets the relation.
- `keywords:keyword_specific_position` — "Include keyword {k} in the {n}-th sentence, as the {m}-th word of that sentence." Pass iff sentence n (1-based) exists and its word m (1-based) equals k (`D-sentence`, `D-word-case`).
- `keywords:letter_frequency` — "In your response, the letter {l} should appear {at least|less than} {N} times." Count the letter in both cases (`D-letter-case`, proposed: case-insensitive). Pass iff the count meets the relation.
- `keywords:no_adjacent_consecutive` — "No two adjacent words can start with consecutive letters of the alphabet." For each two adjacent words whose first characters are letters a-z (case-insensitive), fail if the letters are consecutive in either order (`D-consecutive-order`, proposed: either order, `b`/`a` as well as `a`/`b`). Words that start with another character are not compared.
- `keywords:palindrome` — "Include a palindrome in your response." Pass iff some word of at least three letters reads the same backwards, case-insensitively, or a run of consecutive words does when spaces and punctuation are removed and it has at least three letters (`D-palindrome-length`, proposed: at least three letters; the alternative accepts `a`, `I`, `aa`).
- `keywords:start_end` — "Start and end your response with the same word (do not write anything after the last word, not even punctuation)." Pass iff the first word equals the last word (case-insensitive) and nothing but whitespace follows the last word. Markdown or punctuation before the first word is skipped (`D-edge-markup`).
- `keywords:word_count_different_numbers` — "In your response, the word {k} should appear {N} times." The text gives no relation. Pass iff the keyword occurs exactly N times (`D-word-count-relation`, proposed: exactly N; the other reading the text allows is "at least N"). The kwargs carry a relation (`at least` or `less than`) that the model never sees; a "less than N" verdict is not a reading of the text.
- `keywords:word_once` — "Include keyword {k} in your response." Pass iff the keyword occurs at least once.

### language

- `language:response_language` — "Your ENTIRE response should be in {Language} language, no other language is allowed." Pass iff the prose of the graded text is in the named language; code, numbers, URLs and proper names are allowed; a sentence in another language fails (`D-language-mixed`, proposed: as stated; the alternative judges the dominant language). Grader A only.

### last_word

- `last_word:last_word_answer` — "The last word of your response should be the word {w}." Pass iff the last word of the graded text equals w (`D-edge-markup`, `D-word-case`).
- `last_word:last_word_sent` — "The last word of each sentence, before punctuation, should be the word {w}." Pass iff every sentence's last word equals w (`D-sentence`).

### length_constraints

- `length_constraints:nth_paragraph_first_word` — "There should be {N} paragraphs. Paragraphs and only paragraphs are separated with each other by two new lines as if it was '\n\n' in python. Paragraph {i} must start with word {w}." Paragraphs are the non-empty parts of the graded text split at blank lines (two or more line breaks with only whitespace between them; `D-blank-run`, proposed: a run of several blank lines is one separator; the alternative splits at every `\n\n` and counts the empty parts). Pass iff there are exactly N paragraphs and paragraph i's first word equals w.
- `length_constraints:number_paragraphs` — "There should be {N} paragraphs. Paragraphs are separated with the markdown divider: ***" A divider is a line that is `***` after trimming whitespace. Pass iff the dividers split the graded text into exactly N parts and every part is non-empty (a divider at the start or end, or two dividers in a row, fails). With N = 1 there is no divider.
- `length_constraints:number_sentences` — "Your response should contain {at least|less than} {N} sentences." Pass iff the sentence count meets the relation (`D-sentence`).
- `length_constraints:number_words` — "Answer with {at least|less than} {N} words." Pass iff the word count meets the relation (`D-word`, `D-word-cjk`).

### letters

- `letters:letter_counting` — "Answer with {at least|less than} {N} letters." Count the letters (alphabetic characters of any script) in the graded text. Pass iff the count meets the relation (`D-letter-unit`, proposed: letters are alphabetic characters; the alternative reads "letters" as words). Grader A only.
- `letters:letter_counting2` — "In your response, the letter {l} should appear {at least|less than} {N} times." Same as `keywords:letter_frequency`.

### paragraphs

- `paragraphs:paragraphs` — "There should be 2 paragraphs. Paragraphs are separated with the markdown divider: ***" Same as `length_constraints:number_paragraphs` with N = 2.
- `paragraphs:paragraphs2` — "There should be 2 paragraphs. Paragraphs and only paragraphs are separated with each other by two line breaks." Pass iff the graded text split at blank lines (`D-blank-run`) has exactly 2 non-empty paragraphs.

### punctuation

- `punctuation:no_comma` — "In your entire response, refrain from the use of any commas." Fail iff the graded text contains a comma: `,` and the other comma characters, fullwidth `，` (U+FF0C), ideographic `、` (U+3001), Arabic `،` (U+060C) and small `﹐` (`D-comma-chars`, proposed: any comma character; the alternative only `,`).
- `punctuation:punctuation_dot` — "In your entire response, refrain from the use of . (i.e. dots) as punctuation and in general." Fail iff the graded text contains `.` anywhere (in decimals, URLs and code too, "in general"), or a dot character: fullwidth `．` (U+FF0E), ellipsis `…` (U+2026) (`D-dot-chars`, proposed: these count; the ideographic full stop `。` is not a dot; the alternative counts only `.`).
- `punctuation:punctuation_exclamation` — "In your entire response, refrain from the use of ! (i.e. exclamation marks) as punctuation and in general." Fail iff the graded text contains `!` or fullwidth `！` (U+FF01) (`D-exclamation-chars`, proposed: both; `¡` also counts as an exclamation mark).

### startend

- `startend:end_checker` — "Finish your response with this exact phrase {p}. No other words should follow this phrase." Pass iff the graded text, after removing trailing whitespace, ends with p, compared character by character (case-sensitive). Trailing markdown emphasis or a closing quote after the phrase (`**Any other questions?**`) is not a word (`D-end-trailing`, proposed: allowed when only `*`, `_`, `"` or `'` characters follow; the alternative requires the phrase to be the last characters).
- `startend:quotation` — "Wrap your entire response with double quotation marks." Pass iff the trimmed graded text has at least two characters, starts with a double quotation mark and ends with one: `"` or the typographic pair `“ ”` (`D-quote-chars`, proposed: both).

## 5. Rendering notes (text the model sees versus kwargs)

- `detectable_content:postscript`: in 147 of the 324 constraints whose kwargs marker is `P.S.`, all with inline rendering, the prompt shows the marker without its final dot ("P.S" followed by a comma, " and", or the end of the instruction). The model sees "P.S". The 320 `P.P.S` constraints are rendered as given. Counted with audit/scripts/template_check.py.
- All keyword-like kwargs (`keyword`, `keywords`, `forbidden_words`, `first_word`, `last_word`) are single lowercase words matching `[a-z]+`.
- `keywords:word_count_different_numbers`: the kwargs carry `relation` (`at least` 320, `less than` 206) that the rendered text never shows.
- `paragraphs:paragraphs` and `paragraphs:paragraphs2`: kwargs are `{}`; the text fixes 2 paragraphs.
- All other 46 ids: every constraint's rendered text appears in its prompt with the kwargs' values.

## 6. Decision entries

| Id | Question | Reading A | Reading B | Example (A / B verdict) | Proposed |
|---|---|---|---|---|---|
| D-outer-whitespace | Is leading/trailing whitespace of the graded text part of the answer? | ignored | part of the answer | `"\n\"Hi\""` for quotation: pass / fail | A |
| D-word | Which characters form words? | letters, digits, inner `'` and `-` | whitespace-separated tokens | `"--- end"` has 1 / 2 words | A |
| D-word-cjk | How are words counted in text without spaces? | one word per CJK character | one word per space-separated token | `"你好世界"` is 4 / 1 words | A |
| D-word-case | Are word comparisons case-insensitive? | yes | no | first word `Development` for `development`: pass / fail | A |
| D-keyword-match | Does a word that contains the keyword count? | whole word only | substring or inflection counts | `beers` for keyword `beer`: no / yes | A |
| D-sentence | Do line breaks end sentences? | a line without final punctuation is a sentence | only `.!?` end sentences | `"Title\nOne. Two."` has 3 / 2 sentences | A |
| D-edge-markup | Are markdown and punctuation skipped when finding the first or last word? | skipped | the first token must be the word | `"**Hello** there"` first word `hello`: pass / fail | A |
| D-allcaps-single | Do one-letter capitals (`I`, `A`) count as all-capital words? | count | do not count | `"I SAW IT"`: 3 / 2 | A |
| D-english | Must an all-caps or lowercase response be in English? | yes, the prose must be English | only the case matters | `"BONJOUR TOUT LE MONDE"`: fail / pass | A |
| D-repeat-center | Which word positions are "the center"? | the middle word (either middle word of 6) | any word but the first and last | 5-word phrase with word 2 replaced: fail / pass | A |
| D-repeat-original | May the unchanged phrase also appear? | allowed, not counted | it counts as a repetition | original + 2 variants for n=2: pass / fail | A |
| D-lowercase-counting | "all lowercase words should appear at most N times" | each lowercase word at most N times | total lowercase words at most N | `"the cat and the dog"` N=2: pass / fail | A |
| D-placeholder-link | Does a markdown link's `[text]` count as a placeholder? | counts | does not | `"[docs](http://x)"` N=1: pass / fail | A |
| D-postscript-end | Must the postscript be at the end? | marker line in the last block | marker line anywhere | `"P.S. hi\n\nMain text."`: fail / pass | A |
| D-postscript-dot | Marker `P.S.` shown as "P.S": is `P.S:` accepted? | the text the model saw decides | the kwargs marker decides | `"P.S: thanks"` when the prompt shows "P.S": pass / fail | A |
| D-bigram-odd | Odd word count: may the last group hold one word? | yes | no | `"<<a b>> <<c>>"`: pass / fail | A |
| D-constrained-exact | May text surround the chosen option? | no, the response is the option | yes, if exactly one option appears | `"My answer is yes. Because..."`: fail / pass | A |
| D-json-scalar | Does a bare JSON scalar count as "wrapped in JSON format"? | no, object or array only | any JSON value | `"\"hello\""`: fail / pass | A |
| D-section-case | Is the section word case-sensitive? | yes | no | `"Section 1"` for `SECTION`: fail / pass | A |
| D-section-preamble | May text precede the first section marker? | yes | no | `"Intro\nSECTION 1\nx"` N=1: pass / fail | A |
| D-section-numbering | Must the numbers run 1..N? | no | yes | `"SECTION 2 ... SECTION 1"` N=2: pass / fail | A |
| D-bullet-marker | Which markers make bullet points? | `*`, `-`, `+` | only `*` | three `-` lines, N=3: pass / fail | A |
| D-highlight-bold | Does `**bold**` count as a highlighted section? | yes | no, only `*x*` | `"**a** **b**"` N=2: pass / fail | A |
| D-brackets-per-word | Must each word have its own brackets? | yes | any word inside some brackets | `"[two words]"`: fail / pass | A |
| D-title-position | May the title be anywhere? | yes | must open the response | `"Text.\n<<T>>"`: pass / fail | A |
| D-letter-case | Does the letter count include the uppercase form? | yes | lowercase only | `"Pp"` letter p, at least 2: pass / fail | A |
| D-consecutive-order | Are letters consecutive in either order? | yes (`b`,`a` too) | only alphabetical order | `"big apple"`: fail / pass | A |
| D-palindrome-length | Minimum palindrome length | 3 letters | any length | `"I am here."`: fail / pass | A |
| D-word-count-relation | "should appear N times" with no relation | exactly N | at least N | keyword 4 times, N=3: fail / pass | A |
| D-language-mixed | Is a response with some other-language prose in the named language? | no, the whole prose | yes, if it is dominant | Spanish answer with one English sentence: fail / pass | A |
| D-blank-run | Is a run of several blank lines one paragraph break? | yes | each `\n\n` splits, empty parts count | `"a\n\n\n\nb"` 2 paragraphs: pass / fail | A |
| D-letter-unit | "Answer with less than N letters": letters or words? | alphabetic characters | words | `"Yes"` less than 3: fail / pass | A |
| D-comma-chars | Do fullwidth and ideographic commas count? | yes | only `,` | `"你好，世界"`: fail / pass | A |
| D-dot-chars | Do `．` and `…` count as dots? | yes | only `.` | `"wait…"`: fail / pass | A |
| D-exclamation-chars | Does `！` count? | yes | only `!` | `"好！"`: fail / pass | A |
| D-end-trailing | May emphasis or quote marks follow the end phrase? | yes | no | `"**Any other questions?**"`: pass / fail | A |
| D-quote-chars | Do typographic quotes count? | yes | only `"` | `"“Hi”"`: pass / fail | A |
