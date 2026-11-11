# IFBench contracts (written from the task text only)

Written before any grader or reference code was opened. Sources: the 300 prompts
of `case/data/train-00000-of-00001.parquet` (the instruction sentences listed in
`audit/out/instruction_phrasings.txt`), their kwargs, and `case/TASK.md`.
Each later change is appended in the change log at the end with its reason.

## G. General rules

- **G1 Graded text.** The text after the last `</think>` of the completion. A
  completion of a thinking model with no closing `</think>` is an extraction
  failure: it fails every check and is counted separately. A separate reasoning
  field is never graded.
- **G2 Trimming.** Leading and trailing whitespace of the graded text is not part
  of the answer (`D-trim`).
- **G3 Empty answer.** An empty graded text fails every check (`D-empty`).
- **G4 Word.** A word is a whitespace-delimited token with leading and trailing
  punctuation and markup symbols removed; a token that becomes empty (`—`, `*`,
  `#`, `-`, `|`) is not a word. Internal apostrophes and hyphens stay inside the
  word (`don't`, `well-known` are one word each). Numerals such as `2024` are
  words. A word's length counts its letters and digits only (`D-word`).
- **G5 Sentence.** A sentence ends at `.`, `!`, `?` (or a run of them, such as
  `?!` or `...`), optionally followed by closing quotes or brackets, when next
  comes whitespace or the end of the text. A line break that ends a non-empty
  line also ends a sentence (headings, list items, table rows). Decimal points
  and common abbreviations (`e.g.`, `i.e.`, `Dr.`, `U.S.`) do not end a sentence
  (`D-sentence`).
- **G6 Keyword match.** A keyword matches a word when the two are equal ignoring
  case; inflected or longer forms (`whispers`, `whispering`) do not match, and a
  keyword inside another word does not match (`D-keyword-match`).
- **G7 Vacuous instances.** A rule of the form "every X must ..." passes a
  non-empty answer that has no X or one X where the rule needs two (`D-vacuous`).
- **G8 Prompt score.** Strict prompt-level accuracy: a prompt passes when every
  instruction in its `instruction_id_list` passes. Instruction-level accuracy:
  the share of instruction instances that pass. Instructions present in the prompt
  text but not in the list are not graded.
- **G9 Loose score.** The task text defines no loose score. A score computed on
  edited copies of the answer (lines removed, symbols removed) is a score-level
  transform; a loose pass whose untransformed graded text fails the contract is a
  contract violation of the transform (`D-loose`).
- **G10 Instruction text vs kwargs.** The model sees the prompt text, so the text
  wins where it differs from the kwargs.

## C. Contracts per check

Notation: N, P, W, K are the kwargs that the prompt text states.

### count

- **count:conjunctions** "Use at least N different coordinating conjunctions in
  the response." Pass iff the number of distinct words among
  {for, and, nor, but, or, yet, so} used in the answer (G6 match) is >= N.
  `D-conj-role` (any use of the word vs. only uses as a conjunction).
- **count:keywords_multiple** "Include keyword K1 once ..., K2 twice, K3 three
  times, K4 five times, and K5 seven times." Pass iff the G6 counts are exactly
  1, 2, 3, 5, 7. `D-count-exact` (exactly vs. at least).
- **count:numbers** "Include exactly N numbers in the response." Pass iff the
  answer contains exactly N numbers, counted as occurrences. A number is a numeral
  written with digits, with an optional sign, decimal part, or thousands
  separators (`1,000`, `3.5`, `-2`); `2nd` and `1960s` contain one number each; a
  date `2024-01-01` is three numbers under the proposal. Spelled-out number words
  do not count under the proposal (`D-number`).
- **count:person_names** "Mention at least N different person names in the
  response, from this list of person names: ...". Pass iff the number of distinct
  names from the prompt's list that occur as whole words, capitalized, is >= N; a
  possessive (`Emma's`) counts. `D-name-case`.
- **count:pronouns** "The response should include at least N pronouns." Pass iff
  the number of pronoun occurrences is >= N. Pronouns under the proposal:
  personal (I, me, you, he, him, she, her, it, we, us, they, them), possessive
  (my, mine, your, yours, his, hers, its, our, ours, their, theirs), reflexive
  (myself ... themselves), reciprocal (each other, one another), plus
  demonstrative, interrogative, relative and indefinite pronouns when they stand
  for a noun (`D-pronoun-set`).
- **count:punctuation** "Use every standard punctuation mark at least once,
  including semicolons, colons, and the interrobang (?!)." Pass iff the answer
  contains each of: period, comma, question mark, exclamation mark, colon,
  semicolon, apostrophe, quotation mark, hyphen, dash (en or em), parentheses
  (both), square brackets (both), braces (both), ellipsis, and an interrobang
  written `?!` or `‽`. ASCII or typographic forms both count (`D-punct-set`).
- **count:unique_word_count** "Use at least N unique words in the response."
  Pass iff the number of distinct words (case-insensitive) is >= N.
  `D-unique` (distinct types vs. words used exactly once).
- **count:word_count_range** "The response must contain between MIN and MAX
  words." Pass iff MIN <= word count <= MAX (inclusive).
- **count:words_japanese** "Every Nth word of your response must be in Japanese."
  Pass iff every word at a 1-based position that is a multiple of N is written
  in Japanese script (hiragana, katakana, kanji, ignoring punctuation). Other
  words are free. Words are G4 tokens; a run of Japanese text with no spaces is
  one token (`D-japanese-words`). Fewer than N words: G7.

### format

- **format:emoji** "Please use an emoji at the end of every sentence." Pass iff
  every sentence ends with an emoji (a Unicode emoji character), placed right
  before or right after its terminal punctuation; an emoji may itself end a
  sentence. `D-emoji-position`. Sentences per G5, so a heading or list item
  without an emoji fails.
- **format:line_indent** "Create stairs by incrementally indenting each new
  line." Pass iff, over the non-blank lines, each line has strictly more leading
  whitespace than the previous one (the first line may have none). Blank lines are
  ignored (`D-stairs-blank`). A one-line answer: G7.
- **format:list** "Answer with a list of items, instead of bullet points use
  SEP." Pass iff the answer contains at least two list items, each introduced by
  SEP at the start of a line (after optional indentation), and no line is a list
  item introduced by another bullet marker (`*`, `•`, `-` unless SEP is `-`).
  Other text (an introduction) is allowed (`D-list-form`).
- **format:newline** "Write each word on a new line." Pass iff every non-blank
  line contains exactly one word (G4); punctuation attached to the word is fine.
- **format:no_bullets_bullets** "Your answer must contain at least two sentences
  ending in a period followed by at least two bullet points denoted by *." Pass
  iff there are two sentences ending in `.` (outside bullet lines) that come
  before at least two bullet lines starting with `* `. `D-nbb-order` (all
  sentences before all bullets vs. the proposal).
- **format:no_whitespace** "The output should not contain any whitespace." Pass
  iff the trimmed graded text (G2) contains no Unicode whitespace character
  (`D-whitespace`).
- **format:options** "Answer with one of the following options: O1/O2/...". Pass
  iff the answer gives exactly one of the options as its answer: the trimmed
  answer, ignoring case, markdown emphasis and final punctuation, starts with an
  option and selects no other option. For the letter options `a), b), c), d)` the
  letter with `)`, `.`, or in parentheses counts, in either case. Explanation after
  the option is allowed under the proposal (`D-options`).
- **format:output_template** "Use this exact template for your response: My
  Answer: [answer] My Conclusion: [conclusion] Future Outlook: [outlook]". Pass
  iff the answer starts with `My Answer:` and contains `My Conclusion:` and
  `Future Outlook:` once each, in that order, case-sensitive, each followed by
  non-empty text that is not the literal placeholder. Markdown emphasis around a
  label is allowed (`D-template-markup`); no text before `My Answer:`.
- **format:parentheses** "Nest parentheses (and [brackets {and braces}]) at
  least 5 levels deep." Pass iff some matched bracket pair has nesting depth >= 5,
  counting (), [] and {} together, matching each closer to the most recent
  unclosed opener of the same type, and ignoring unmatched closers.
  `D-paren-types` (all three types required vs. any).
- **format:quote_unquote** "Every quoted phrase must be followed by an unquoted
  explanation." Pass iff every quoted phrase (text in double quotes, straight or
  curly, or guillemets) is followed, before the next quoted phrase or the end of
  the answer, by unquoted text that contains at least one word. No quoted phrase:
  G7. `D-quote-chars`, `D-explanation`.
- **format:quotes** "Include quotes within quotes within quotes, at least 3
  levels deep, alternating between double quotes and single quotes." Pass iff
  the answer contains a quotation nested at least 3 deep whose levels alternate
  between double and single quotes (either may be outermost); straight and
  curly forms both count; apostrophes inside words are not quote marks.
- **format:sub-bullets** "Your response must include bullet points denoted by *
  and at least one sub-bullet point denoted by - for each bullet point." Pass iff
  there are at least two `* ` bullet lines and each is followed, before the next
  `* ` bullet, by at least one `- ` sub-bullet line. Indentation of the sub-bullet
  is not required (`D-subbullet-indent`); `D-plural`.
- **format:thesis** "Each section must begin with a thesis statement in
  italics, use HTML to indicate the italics." Sections are separated by markdown
  headings, or by blank lines when there are no headings (`D-section`). Pass iff
  the first text of every section (after its heading) starts with an `<i>` or
  `<em>` element that contains a statement; markdown italics do not count.
- **format:title_case** "Write the entire response in title case (capitalize the
  first letter of every major word)." Pass iff every word that is not a minor word
  starts with an uppercase letter. Minor words: articles, coordinating
  conjunctions, and prepositions of up to four letters; they may take either case.
  Words that start with a digit or symbol are ignored. Only the first letter is
  constrained, so all caps passes (`D-titlecase`).

### ratio

- **ratio:overlap** "Maintain a trigram overlap of P% (±2%) with the provided
  reference text." Word trigrams, lowercased, punctuation removed; overlap = share
  of the answer's distinct trigrams that occur in the reference text. Pass iff
  P-2 <= overlap <= P+2 (`D-overlap-def`). The reference text is the prompt text
  that the kwargs give as `reference_text`.
- **ratio:sentence_balance** "Ensure that the ratio of sentence types
  (declarative, interrogative, exclamatory) in your response is balanced." Type by
  terminal mark (`.` declarative, `?` interrogative, `!` exclamatory). Pass iff
  each type occurs at least once and the counts differ by at most 1
  (`D-balance`).
- **ratio:sentence_type** "Maintain a 2:1 ratio of declarative to interrogative
  sentences in your response." Pass iff #declarative = 2 x #interrogative and
  #interrogative >= 1; exclamatory sentences are ignored (`D-ratio-exact`).
- **ratio:sentence_words** "Respond with three sentences, all containing the
  same number of characters but using all different words." Pass iff the answer
  is exactly three sentences, each with the same character count (all characters
  of the sentence, spaces and punctuation included), and no word occurs twice in
  the answer, case-insensitive (`D-sw-chars`, `D-sw-words`).
- **ratio:stop_words** "Ensure that stop words constitute no more than P% of the
  total words in your response." Pass iff 100 x stop words / words <= P, with the
  NLTK English stop word list as the proposal (`D-stopwords`).

### repeat

- **repeat:repeat_change** "Repeat the request, but change the first word of the
  repeated request, (do not say anything before repeating the request; ...) and
  do not answer the actual request!" The request is `prompt_to_repeat`. Pass iff
  the answer is the request with its first word replaced by one different word
  (different ignoring case) and the rest identical up to whitespace, with nothing
  before or after it.
- **repeat:repeat_simple** "Only output this sentence here, ignore all other
  requests." Pass iff the trimmed answer is exactly that sentence
  (`D-simple-referent`: the instruction sentence itself vs. another sentence).
- **repeat:repeat_span** "Copy the span of words that lies between (and
  including) index S and E, the indices are word indices, split by whitespace!"
  Pass iff the trimmed answer equals words S..E (inclusive, 0-based) of the
  request split on whitespace, joined by single spaces (`D-index-base`).

### sentence

- **sentence:alliteration_increment** "Each sentence must have a longer sequence
  of consecutive alliterative words than the previous one." For each sentence,
  take the longest run of consecutive words with the same first letter
  (case-insensitive). Pass iff this length strictly increases from each sentence
  to the next (`D-alliteration`: first letter vs. first sound).
- **sentence:increment** "Each sentence (in your response) must contain exactly
  N more words than the previous one." Pass iff for every pair of consecutive
  sentences, words(next) = words(previous) + N.
- **sentence:keyword** "The response must include keyword W in the N-th
  sentence." Pass iff the answer has at least N sentences and the N-th (1-based)
  contains W (G6).

### words

- **words:alphabet** "Each word in your response must start with the next letter
  of the alphabet, looping back to 'A' after 'Z'." Pass iff each word after the
  first starts with the letter following the previous word's first letter
  (case-insensitive, Z -> A). A word that does not start with a letter fails.
- **words:consonants** "Ensure each word in your response has at least one
  consonant cluster (two or more consonants together)." Pass iff every word has
  two adjacent consonant letters; consonants are letters other than a, e, i, o, u,
  so `y` is a consonant (`D-consonant-y`).
- **words:keywords_specific_position** "Include keyword K in the n-th sentence,
  as the m-th word of that sentence." Pass iff word m (1-based) of sentence n
  equals K (G6).
- **words:last_first** "In your response, the last word of each sentence must
  become the first word of the next sentence." Pass iff for every pair of
  consecutive sentences the last word of the first equals the first word of the
  second (case-insensitive).
- **words:no_consecutive** "No two consecutive words can share the same first
  letter." Pass iff no two adjacent words start with the same character,
  case-insensitive.
- **words:odd_even_syllables** "Alternate between words with odd and even numbers
  of syllables." Pass iff the parity of the syllable count changes from every word
  to the next, with dictionary syllable counts (`D-syllables`).
- **words:palindrome** "Include at least 10 single-word palindromes, each at least
  5 characters long." Pass iff at least 10 distinct words (case-insensitive) of
  at least 5 letters read the same reversed (`D-palindrome`).
- **words:paragraph_last_first** "Each paragraph of your response must end with
  the same word it started with, separate paragraphs with a newline." Each
  non-blank line is a paragraph. Pass iff in every paragraph the first and last
  words are equal (case-insensitive).
- **words:prime_lengths** "Use only words with lengths that are prime numbers."
  Pass iff every word's length (G4) is prime.
- **words:repeats** "The response should not repeat any word more than N times."
  Pass iff no word occurs more than N times, case-insensitive (`D-repeats`).
- **words:start_verb** "The response must start with a verb." Pass iff the first
  word, after leading markup, is a verb form in its sentence (imperative, finite,
  or -ing/-ed form) (`D-verb`).
- **words:vowel** "Write a paragraph using words that contain only three types of
  vowels." Pass iff the answer is one paragraph and the set of vowel letters
  (a, e, i, o, u) used across all its words has exactly three members
  (`D-vowel`).
- **words:words_position** "The second word in your response and the second to
  last word in your response should be the word W." Pass iff word 2 and the
  second-to-last word both equal W (G6).

### custom (one prompt each)

- **custom:character_reverse** (key 273) Pass iff the answer, reversed character
  by character, is a sentence that answers "What animal is the national symbol of
  the US?" (bald eagle), and the answer itself is not the forward sentence.
  Capitalization and punctuation follow the reversal (`D-reverse-form`).
- **custom:word_reverse** (key 283) Pass iff the answer is one sentence whose
  words, read in reverse order, form a sentence that answers the same query.
  Placement of capitals and final punctuation is free (`D-reverse-form`).
- **custom:csv_city** (key 274) Pass iff the CSV is a header row with the five
  named columns plus exactly 7 data rows, comma-delimited, 5 fields per row. The
  CSV may sit in a code block; text outside the CSV is allowed (`D-csv-wrap`).
- **custom:csv_quotes** (key 275) Header plus exactly 3 data rows, tab-delimited,
  5 fields per row, every field (header included) enclosed in double quotes.
- **custom:csv_special_character** (key 276) Header plus exactly 14 data rows,
  comma-delimited, 5 fields per row, and exactly one field that contains a
  character other than a letter, digit or space and is enclosed in double quotes
  (`D-special`).
- **custom:date_format_list** (key 277) Pass iff the answer is only a
  comma-separated list of valid YYYY-MM-DD dates (no explanation). Historical
  completeness is not checked (`D-custom-content`).
- **custom:european_capitals_sort** (key 278) Pass iff the answer is only a
  comma-separated list of capital names (no country names) of European countries
  with latitude above 45°N, sorted from highest to lowest latitude
  (`D-custom-content` for completeness).
- **custom:mcq_count_length** (key 279) Pass iff there are exactly 4 questions,
  each starting with the label "Question", each with exactly 5 options, question
  texts strictly increasing in length (characters of the question stem), and no
  explanation (`D-mcq-length`).
- **custom:multiples** (key 280) Pass iff the numbers printed are exactly 14, 21,
  28, 35, 42, 49 in that order and no other number appears (`D-custom-content`).
- **custom:reverse_newline** (key 281) Pass iff the answer lists African countries
  one per line in strictly reverse alphabetical order (`D-custom-content` for
  completeness).
- **custom:sentence_alphabet** (key 282) Pass iff the story has exactly 26
  sentences and sentence i starts with a word whose first letter is the i-th letter
  of the alphabet.

## D. Decision entries (proposal first)

| id | reading A (proposed) | reading B | example where they differ |
|---|---|---|---|
| D-trim | ignore leading/trailing whitespace of the graded text | every character counts | `"abc\n"` for no_whitespace |
| D-empty | an empty answer fails every check | literal reading per check | `""` for no_whitespace, repeats |
| D-word | whitespace tokens, edge punctuation stripped, pure-symbol tokens dropped | regex word characters only / raw whitespace tokens | `well-known` = 1 word (A) or 2 (regex `\w+`) |
| D-sentence | terminal `.!?` + whitespace, or end of a non-empty line | terminal punctuation only (lines join) | heading `Intro` then `Text.` = 2 sentences (A) or 1 (B) |
| D-keyword-match | whole word, case-insensitive, no inflections | substring / inflections count | `whispers` counts for `whisper` only under B |
| D-vacuous | no instance -> pass | no instance -> fail | one-sentence answer for sentence:increment |
| D-loose | report loose score only as a separate, labeled metric | treat loose as the score | loose pass by deleting the first line |
| D-conj-role | count the word forms | count only conjunction uses | `for example` counts `for` under A |
| D-count-exact | "once/twice/..." means exactly | at least | keyword seven times needed, eight given |
| D-number | digit numerals, occurrences | also number words / distinct values | `two` counts only under B |
| D-name-case | capitalized whole-word name | any case | `grace` |
| D-pronoun-set | personal, possessive incl. determiners, reflexive, + others standing for nouns | personal pronouns only | `my`, `this` |
| D-punct-set | 15 common marks listed above + `?!` | all ASCII punctuation (`string.punctuation`) | answer lacking `#`, `@`, `~` |
| D-unique | distinct word types | words used exactly once | `a a b` = 2 unique (A) or 1 (B) |
| D-japanese-words | a run of Japanese without spaces is one word | each Japanese character / morpheme is a word | `日本語です` |
| D-emoji-position | emoji before or after the terminal mark | emoji must follow the mark | `Hi 😀.` |
| D-stairs-blank | blank lines ignored | blank lines break the stairs | |
| D-list-form | SEP-marked items, other text allowed | the whole answer is list items | intro line before the list |
| D-nbb-order | two period sentences precede two `*` bullets | no text after the bullets / all sentences first | |
| D-whitespace | Unicode whitespace | ASCII whitespace only | NBSP U+00A0 |
| D-options | starts with exactly one option, explanation allowed | answer equals the option | `Yes, because ...` |
| D-template-markup | markdown emphasis around labels allowed | labels verbatim only | `**My Answer:**` |
| D-paren-types | any bracket type counts toward depth | all three types required | `(((((x)))))` |
| D-quote-chars | double quotes and guillemets delimit quoted phrases | single quotes too | `'word'` |
| D-explanation | at least one unquoted word after the quote | a clause or sentence | `"x" here.` |
| D-subbullet-indent | sub-bullet need not be indented | must be indented under its bullet | `* a\n- b` |
| D-plural | "bullet points"/"list of items" -> at least two | at least one | one bullet with a sub-bullet |
| D-section | headings, else blank-line blocks, delimit sections | whole answer is one section | |
| D-titlecase | minor words free, all caps passes | minor words must be lowercase / all caps fails | `THE END` |
| D-overlap-def | share of the answer's distinct word trigrams found in the reference | share of the reference's trigrams in the answer / Jaccard / character trigrams | |
| D-balance | each type present, counts within 1 | exactly equal | 2 `.`, 1 `?`, 1 `!` |
| D-ratio-exact | exactly 2:1 | approximately 2:1 | 5 `.`, 2 `?` |
| D-sw-chars | all characters of the sentence | letters only | |
| D-sw-words | no word repeated anywhere | no word shared between sentences | `the` twice in one sentence |
| D-stopwords | NLTK English list | another list (spaCy, sklearn) | |
| D-simple-referent | the instruction sentence itself | another sentence of the prompt | |
| D-index-base | 0-based | 1-based | |
| D-alliteration | same first letter | same first sound | `cat kite` |
| D-consonant-y | `y` is a consonant | `y` is a vowel | `my` |
| D-syllables | dictionary counts | heuristic counts | |
| D-palindrome | distinct words, letters only, any token | occurrences / dictionary words | `level` x10 |
| D-repeats | at most N occurrences | at most N+1 occurrences | word used N+1 times |
| D-verb | any verb form, by context | base or finite form only | `Exploring ...` |
| D-vowel | one paragraph, union of vowels exactly 3 | each word has at most 3 / exactly 3 vowel types | |
| D-reverse-form | exact reversal of an answer sentence | loose reversal | |
| D-csv-wrap | code block and surrounding text allowed | CSV only | |
| D-special | exactly one quoted field with a non-alphanumeric, non-space character | at least one | |
| D-custom-content | format plus checkable content; completeness not required | completeness required | |
| D-mcq-length | stem length in characters | words / whole block | |

## Change log

Entries after the v1 hash (`b25309b9...9f82`, 2026-11-10 23:05:36 UTC). Each was
prompted by reading the grader code, which showed a reading the v1 table did not
name; none changes a v1 proposal.

- 2026-11-10 23:20 UTC, **D-keyword-match** clarified: reading B is "inflected
  forms of the keyword also count" (`whispers`). A hit inside a different word
  (`fish` in `selfish`, `door` in `indoor`, `bread` in `breadth`) is not a reading
  of "include keyword X". Reason: the grader counts substrings.
- 2026-11-10 23:20 UTC, **D-word** clarified: reading B is "regex word-character
  runs" (`don't` = `don` + `t`, `well-known` = 2). Raw whitespace tokens with
  punctuation attached are not a reading: no careful reader counts `word,` and
  `word` as two different words, or `—` / `*` as a word. Reason: several checks
  count such tokens.
- 2026-11-10 23:20 UTC, **D-pronoun-set** reading C added: every word on a pronoun
  list counts whatever its role (`that` as a conjunction, `this` as a
  determiner). Reason: the grader counts word forms.
- 2026-11-10 23:20 UTC, **D-punct-set** reading C added: the six marks
  `. , ! ? ; :` plus the interrobang. Reason: the grader checks only these.
- 2026-11-10 23:20 UTC, **D-vowel** reading C added: at most three vowel types
  across the paragraph. Reason: the grader checks `<= 3`.
- 2026-11-10 23:20 UTC, **D-syllables** reading B changed to "an accepted variant
  pronunciation" (`fire` 1 or 2, `every` 2 or 3). A heuristic's miscount of a word
  with one accepted count is not a reading.
- 2026-11-10 23:20 UTC, **D-number** extended: a time `10:30` and a fraction `5/7`
  are one number under reading B and two under A; a range `3-5` and a list `1,2,3`
  are two and three numbers under every reading.
- 2026-11-10 23:20 UTC, new **D-change-case** (repeat:repeat_change): A (proposed)
  a change of letter case only (`Write` -> `write`) is not a change of the word;
  B it is.
- 2026-11-10 23:20 UTC, new **D-simple-case** (repeat:repeat_simple): A
  (proposed) the copy must match letter case; B case-insensitive.
- 2026-11-10 23:38 UTC, new **D-list-placement** (format:list): A (proposed) SEP
  introduces each item at the start of a line, as a bullet does; B SEP may also
  separate items inside a line (`apples !?!? pears !?!? plums`). Under both, a
  hyphen inside a word (`well-known`) is not an item marker, and a mention of the
  marker that separates no items does not make a list. Reason: panel responses
  (non-held-out runs) use SEP between items on one line, a reading v1 did not
  list.
- 2026-11-10 23:45 UTC, new **D-bullet-syntax** (format:no_bullets_bullets,
  format:sub-bullets): A (proposed) a bullet is a line whose marker (`*` or `-`)
  is followed by a space, as in markdown; B the marker may be followed directly by
  the text (`*The protagonist ...`). Under both, a line that opens with `**bold**`
  is not a bullet. Reason: panel responses (non-held-out runs) write `*Text`.
