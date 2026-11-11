# IFBench check contracts (written from the prompt text only)

Written before reading any grader or reference code. Sources: the `prompt` column of
`case/data/train-00000-of-00001.parquet` (the text the model sees) and, for the check
names and parameter values, the `instruction_id_list` and `kwargs` columns. Each later
change is appended to the change log at the end with its reason.

## 0. Rules for every check

- **Graded text.** For a model with a reasoning block, the text after the last
  `</think>`; never a separate reasoning field. A completion that opens `<think>` and
  never closes it is an extraction failure: it fails every check of its prompt and is
  counted separately. For other models, the whole completion. Leading and trailing
  whitespace of the graded text is ignored (D-strip), except where a check is about
  whitespace and says otherwise below.
- **Truncated responses** (finish_reason `length`) are graded as they stand; the
  contract gives them no allowance. They are counted separately in the report.
- **Prompt score.** A prompt passes (strict) when every check in its
  `instruction_id_list` passes. Instruction accuracy averages over checks.
- **Words (D-word).** A word is a maximal run of letters or digits, allowing internal
  apostrophes (straight or typographic) and internal hyphens. Punctuation, emoji and
  Markdown symbols (`*`, `**`, `_`, `#`, `>`, backticks, list markers such as `-`, `1.`)
  are not words and are not part of words. Comparison of words is case-insensitive
  (D-case) unless the check says otherwise.
- **Sentences (D-sentence).** A sentence ends at a run of terminal punctuation
  (`.`, `!`, `?`, `…`, including `?!` and `...`), optionally followed by closing quotes
  or brackets, then whitespace or the end of the text. A line break that ends a
  non-empty line without terminal punctuation (a heading, a list item) also ends a
  sentence. Abbreviations (`e.g.`, `Dr.`), decimals (`3.5`) and list labels (`1.`) do not
  end a sentence. Empty segments are not sentences.
- **Typography.** Typographic quotes `“ ” ‘ ’` and the typographic apostrophe `’` are
  punctuation like `"` and `'` wherever a check reads words (v2). D-typographic (v2):
  whether typographic quotes delimit quotations in format:quotes and
  format:quote_unquote; proposal yes.
- **Vacuous responses (D-vacuous).** A check phrased "each/every X must ..." or as a
  ratio fails when the response has no X (or a zero denominator), and a check that
  compares each sentence with the previous one needs at least two sentences.
- **Parameters.** The numbers and strings in the contract are those in the prompt text.
  Where a `kwargs` value differs from the prompt text, the prompt text wins and the
  difference is a finding against the dataset/grader input.

## 1. count

- **count:conjunctions** -- "Use at least N different coordinating conjunctions in the
  response." Coordinating conjunctions = for, and, nor, but, or, yet, so. Pass iff the
  number of distinct members of that set that occur as whole words (case-insensitive)
  is >= N. Fail otherwise. Substrings ("Oregon", "android", "sore") do not count.
  D-conj-usage: whether `for`/`so`/`yet` count when used as a preposition or adverb
  ("for example"); proposal: every occurrence counts (lexical reading).
  Prompt key 8 prints the number as "4.0"; read as 4.
- **count:keywords_multiple** -- "Include keyword k1 once ..., k2 twice ..., k3 three times
  ..., k4 five times ..., and k5 seven times in your response." Pass iff each keyword
  occurs as a whole word (case-insensitive) exactly 1, 2, 3, 5, 7 times. D-keyword-count:
  exactly vs at least; proposal exactly. D-keyword-match: whether inflected forms
  ("whispers") or substrings count; proposal whole word only, inflections do not count.
- **count:numbers** -- "Include exactly N numbers in the response." Pass iff the response
  contains exactly N numbers. D-number-def: proposal: a number is a maximal run of
  digits, with internal `.` or `,` between digits and an optional leading sign belonging
  to the same number (`3.14`, `1,000`, `-5` are one number each); it counts wherever it
  appears, including list labels, years, ordinals (`1st`) and digits inside words
  (`H2O`); spelled-out number words ("five") do not count. Alternative readings: count
  number words; skip list labels.
- **count:person_names** -- "Mention at least N different person names in the response,
  from this list of person names: Emma, Liam, Sophia, Jackson, Olivia, Noah, Ava, Lucas,
  Isabella, Mason, Mia, Ethan, Charlotte, Alexander, Amelia, Benjamin, Harper, Leo, Zoe,
  Daniel, Chloe, Samuel, Lily, Matthew, Grace, Owen, Abigail, Gabriel, Ella, Jacob,
  Scarlett, Nathan, Victoria, Elijah, Layla, Nicholas, Audrey, David, Hannah,
  Christopher, Penelope, Thomas, Nora, Andrew, Aria, Joseph, Claire, Ryan, Stella,
  Jonathan ." Pass iff >= N distinct names from the list occur as whole words; a
  possessive (`Emma's`) counts; substrings ("Leon", "Miami", "Avalon") do not.
  D-name-case: proposal: the capitalized name counts wherever it occurs (also when used
  as a common noun or place, "Grace", "Victoria"); lower-case "grace" does not.
- **count:pronouns** -- "The response should include at least N pronouns." Pass iff the
  number of pronoun occurrences (tokens, not distinct) is >= N. D-pronoun-set: proposal:
  personal (I, me, you, he, him, she, her, it, we, us, they, them), possessive (my, mine,
  your, yours, his, hers, its, our, ours, their, theirs), reflexive (myself ... themselves),
  reciprocal (each other, one another), and indefinite pronouns ending in -one, -body,
  -thing; alternative: also demonstrative, relative and interrogative pronouns (this,
  that, these, those, who, whom, whose, which, what) when used as pronouns.
- **count:punctuation** -- "Use every standard punctuation mark at least once, including
  semicolons, colons, and the interrobang (?!)." Pass iff all of: period, comma, question
  mark, exclamation mark, semicolon, colon, apostrophe, quotation mark, hyphen, dash
  (en or em dash, or `--`), parentheses, square brackets, braces, ellipsis (`...` or `…`)
  occur, and the interrobang occurs as `?!` (or `‽`). D-punct-set: which marks are
  "standard"; proposal: the 14 marks above; alternatives: drop braces/brackets/ellipsis,
  or the ASCII punctuation set (which adds `@ # $ % & * ...`; proposal says no).
- **count:unique_word_count** -- "Use at least N unique words in the response." Pass iff
  the number of distinct words (case-insensitive, D-word) is >= N.
- **count:word_count_range** -- "The response must contain between A and B words." Pass
  iff A <= word count <= B (D-between: inclusive; proposal inclusive).
- **count:words_japanese** -- "Every Nth word of your response must be in Japanese." Split
  the response into whitespace-separated words; the words at 1-based positions N, 2N,
  3N, ... must be Japanese (their letters are hiragana, katakana or kanji; attached
  punctuation is ignored). Other words are unconstrained. Fail if any such word is not
  Japanese, or if the response has fewer than N words (D-vacuous). D-japanese-kanji:
  whether a kanji-only word counts as Japanese; proposal yes. D-japanese-digits (v2):
  whether a numeral in a Japanese slot counts as Japanese; proposal no.

## 2. custom (one prompt each; no kwargs, so the grader must encode the content)

- **custom:character_reverse** -- "What animal is the national symbol of the US? Respond
  to this query, but make your sentence in reverse order of what it should be, per
  letter." Pass iff the graded text, reversed character by character, is an English
  sentence that answers the question (names the (bald) eagle), e.g.
  `.elgae dlab eht si lobmys lanoitan ehT`. Fail: forward text, word-order reversal,
  reversed text that does not answer. D-reverse-content: whether naming the eagle is
  required (proposal yes: the response must "respond to this query").
- **custom:word_reverse** -- same question, "per word". Pass iff the words, read in
  reverse order, form an English sentence answering the question, with each word
  spelled normally, e.g. `eagle bald the is US the of symbol national The`.
  Punctuation position and capitalization are ignored (D-reverse-punct).
- **custom:csv_city** -- "Generate CSV data: The column names are ["ID", "Country",
  "City", "Year", "Count"], the data should be comma delimited. Please generate 7 rows."
  Pass iff the CSV payload has the header row with exactly those five names in order,
  then exactly 7 data rows, each with exactly 5 comma-separated fields. D-csv-wrapper:
  whether prose or a code fence around the CSV is allowed; proposal: a code fence is
  allowed, prose outside it is ignored. D-csv-rows: whether "7 rows" counts the header;
  proposal: 7 data rows plus the header.
- **custom:csv_quotes** -- columns StudentID, Subject, Grade, Semester, Score, "tab
  delimited. Please generate 3 rows and enclose each single field in double quotes."
  Pass iff header + exactly 3 data rows, fields separated by tabs, 5 fields per row,
  and every field (header included, D-csv-header-quoted; proposal included) enclosed in
  double quotes.
- **custom:csv_special_character** -- columns ProductID, Category, Brand, Price, Stock,
  comma delimited, "14 rows. Add one field which contains a special character and
  enclose it in double quotes." Pass iff header + exactly 14 data rows, 5 fields each
  (a quoted field counts as one field even if it contains a comma), and at least one
  field contains a special character (a character other than a letter, digit or space)
  and is enclosed in double quotes. D-csv-one-field: exactly one vs at least one such
  field; proposal at least one.
- **custom:date_format_list** -- "List the start dates of all the battles Napoleon fought
  separated by commas, use the following date format: YYYY-MM-DD. Do not provide an
  explanation." Pass iff the graded text is a comma-separated list of valid calendar
  dates, each exactly `YYYY-MM-DD`, with no other text. D-content-history: whether the
  dates must be correct and complete; proposal: format only (valid dates within
  1769-1821).
- **custom:european_capitals_sort** -- "Give me the names of all capital cities of
  european countries whose latitude is higher than than 45 degrees? List the capital
  cities without country names, separated by commas, sorted by latitude, from highest to
  lowest." Pass iff the graded text is a comma-separated list of capital names only (no
  country names, no other text), every listed capital is above 45 deg N, and the list is
  in strictly decreasing latitude. Reference latitudes (deg N, approx.): Reykjavik 64.1,
  Helsinki 60.2, Oslo 59.9, Tallinn 59.4, Stockholm 59.3, Riga 56.9, Moscow 55.8,
  Copenhagen 55.7, Vilnius 54.7, Minsk 53.9, Dublin 53.3, Berlin 52.5, Amsterdam 52.4,
  Warsaw 52.2, London 51.5, Astana 51.2 (transcontinental), Brussels 50.8, Kyiv 50.4,
  Prague 50.1, Luxembourg 49.6, Paris 48.9, Vienna 48.2, Bratislava 48.1, Budapest 47.5,
  Vaduz 47.1, Chisinau 47.0, Bern 46.9, Ljubljana 46.1, Zagreb 45.8. D-capitals-set:
  whether completeness is required and which states count as European; proposal:
  completeness over UN-member European states (Kazakhstan excluded), name variants
  accepted (Kiev/Kyiv, Chisinau/Chişinău).
- **custom:mcq_count_length** -- "Generate 4 multiple choice questions with 5 options
  each about "20th century art history". Each question should start with the label
  "Question". The questions should get progressively longer. Do not provide an
  explanation." Pass iff exactly 4 questions, each starting with the label "Question"
  (number and colon may follow), each with exactly 5 options, question stems strictly
  increasing in length, and no explanation text. D-mcq-length: length measured on the
  question stem in characters (proposal) vs words vs stem plus options. D-mcq-answer:
  whether an answer key (without reasons) is an explanation; proposal: allowed.
- **custom:multiples** -- "Count from 10 to 50 but only print multiples of 7." Pass iff the
  numbers printed, in order, are exactly 14, 21, 28, 35, 42, 49. D-multiples-prose:
  proposal: separators and prose without numerals are allowed; any other numeral
  (including 10, 50 or 7 in prose) fails. Alternative: nothing but the six numbers.
- **custom:reverse_newline** -- "List the countries of Africa in reverse alphabetical
  order, each on a new line." Pass iff each country is on its own line, the country
  lines are in strictly reverse alphabetical order, and the list covers the 54 African
  UN member states. D-africa-set: name variants (Côte d'Ivoire / Ivory Coast, Eswatini /
  Swaziland, the two Congos), partially recognized states, and whether an intro line is
  allowed; proposal: variants accepted, Western Sahara and Somaliland optional, one
  intro line allowed.
- **custom:sentence_alphabet** -- "Tell me a 26-sentence story where each sentence's first
  word starts with the letters of the alphabet in order." Pass iff the story has exactly
  26 sentences and sentence i's first word starts with the i-th letter (A..Z,
  case-insensitive). D-title: whether a title line counts as a sentence; proposal: a
  title line without terminal punctuation is not part of the story.

## 3. format

- **format:emoji** -- "Please use an emoji at the end of every sentence." Pass iff every
  sentence ends with an emoji (Unicode emoji; text emoticons do not count). D-emoji-pos:
  proposal: the emoji may come right before or right after the sentence's terminal
  punctuation.
- **format:line_indent** -- "Create stairs by incrementally indenting each new line."
  Pass iff each non-blank line has strictly more leading whitespace than the previous
  non-blank line (the first line may have none). D-indent: proposal: blank lines are
  ignored, the step need not be constant, indentation width is the number of leading
  whitespace columns with a tab expanded to 4 columns; a single-line response fails
  (D-vacuous).
- **format:list** -- "Answer with a list of items, instead of bullet points use SEP." Pass
  iff the answer is a list of at least two items, each item marked by SEP in the
  position of a bullet (start of the item's line), and no other bullet marker (`*`, `•`,
  and `-` unless SEP is `-`) is used for items. D-list-sep: whether SEP between items on
  one line also passes ("a !?!? b !?!? c"); proposal yes. D-list-intro: whether a
  sentence before the list is allowed; proposal yes.
- **format:newline** -- "Write each word on a new line." Pass iff every non-blank line
  contains exactly one word (D-word; attached punctuation allowed). Lines with only
  punctuation or Markdown symbols contain no word and are allowed (D-newline-punct).
- **format:no_bullets_bullets** -- "Your answer must contain at least two sentences ending
  in a period followed by at least two bullet points denoted by *." Pass iff at least two
  period-terminated sentences occur before the bullets, followed by at least two bullet
  lines starting with `*` (then a space). Sentences inside bullets do not count toward
  the two sentences. D-bullets-after: whether text may follow the bullets; proposal yes.
- **format:no_whitespace** -- "The output should not contain any whitespace." Pass iff the
  graded text contains no whitespace character (Unicode White_Space: space, tab, line
  breaks, NBSP, U+2000-U+200A, U+3000, ...). U+200B (zero-width space) is not White_Space
  (D-whitespace-set, proposal). Trailing whitespace at the end of the completion is
  ignored (D-strip). An empty response fails (D-vacuous).
- **format:options** -- "Answer with one of the following options: OPTIONS." Options in the
  data: `yes/no/maybe`; `I know or I don't know`; `a), b), c), d)`. Pass iff the graded
  text, ignoring case, surrounding whitespace, Markdown emphasis and one trailing
  period, is exactly one option. For `a), b), c), d)` the option is the label (`c)`),
  optionally followed by that option's own text (D-options-label; proposal). Two
  options, or any explanation, fail. D-options-exact: whether the option may be embedded
  in a longer answer; proposal no.
- **format:output_template** -- "Use this exact template for your response: My Answer:
  [answer] My Conclusion: [conclusion] Future Outlook: [outlook]". Pass iff the response
  starts with `My Answer:`, contains `My Conclusion:` and `Future Outlook:` after it in
  that order, each label followed by non-empty content that replaces the placeholder,
  and no text precedes `My Answer:`. D-template-markup: proposal: line breaks between
  sections and Markdown emphasis on labels are allowed; a literal unfilled `[answer]`
  fails.
- **format:parentheses** -- "Nest parentheses (and [brackets {and braces}]) at least 5
  levels deep." Pass iff the response contains a properly nested and closed group of
  `()`, `[]`, `{}` at depth >= 5 (any mix of types). D-paren-mix: whether all three types
  must be used; proposal no. D-paren-closed (v3): whether the enclosing groups must also
  close properly (proposal) or a group that closes while at least four others are open
  suffices.
- **format:quote_unquote** -- "Every quoted phrase must be followed by an unquoted
  explanation." Pass iff the response has at least one quoted phrase (text between
  double quotes, straight or typographic) and each quoted phrase is followed, before
  the next quoted phrase or the end, by unquoted text containing at least one word.
  D-quote-chars: whether single-quoted phrases count; proposal: double quotes only.
- **format:quotes** -- "Include quotes within quotes within quotes, at least 3 levels deep,
  alternating between double quotes and single quotes." Pass iff the response contains
  a quotation nested at least 3 levels deep with alternating types (double, single,
  double; or single, double, single), straight or typographic. Apostrophes inside words
  are not quotes.
- **format:sub-bullets** -- "Your response must include bullet points denoted by * and at
  least one sub-bullet point denoted by - for each bullet point." Pass iff there is at
  least one bullet line starting with `*` and every `*` bullet is followed, before the
  next `*` bullet, by at least one line starting (after optional indentation) with `-`.
  D-subbullet-indent: proposal: indentation of the `-` lines is not required.
- **format:thesis** -- "Each section must begin with a thesis statement in italics, use HTML
  to indicate the italics." Pass iff every section's first content (after an optional
  heading line) is an HTML italic element (`<i>...</i>` or `<em>...</em>`) containing a
  statement. D-section: proposal: sections are delimited by Markdown headings when the
  response has headings, otherwise by blank lines; a response with no sections fails.
- **format:title_case** -- "Write the entire response in title case (capitalize the first
  letter of every major word)." Pass iff every major word starts with an upper-case
  letter. D-titlecase-minor: proposal: minor words (articles; coordinating conjunctions;
  prepositions of up to four letters) may be in either case; words that do not start
  with a letter are ignored.

## 4. ratio

- **ratio:overlap** -- "Maintain a trigram overlap of P% (±2%) with the provided reference
  text." Pass iff |overlap - P| <= 2 percentage points. D-overlap-reference: the prompt
  does not label a reference text; proposal: the prompt text other than the instruction
  sentences. D-trigram-def: proposal: word trigrams (D-word, lower-case), overlap = share
  of the response's distinct trigrams that occur in the reference; alternatives: share of
  the reference's trigrams, Jaccard, character trigrams.
- **ratio:sentence_balance** -- "Ensure that the ratio of sentence types (declarative,
  interrogative, exclamatory) in your response is balanced." Pass iff the numbers of
  declarative (ending `.`), interrogative (`?`) and exclamatory (`!`) sentences are
  equal and at least 1. D-balanced: exactly equal (proposal) vs within one.
  D-sentence-type: type by terminal punctuation (proposal) vs by grammar.
- **ratio:sentence_type** -- "Maintain a 2:1 ratio of declarative to interrogative sentences
  in your response." Pass iff #declarative = 2 x #interrogative and #interrogative >= 1;
  exclamatory sentences are not counted. D-ratio-exact: proposal exact.
- **ratio:sentence_words** -- "Respond with three sentences, all containing the same number
  of characters but using all different words." Pass iff exactly three sentences, each
  with the same number of characters (counting every character of the sentence from its
  first character through its terminal punctuation, D-char-count proposal), and no word
  occurs more than once in the response (D-different-words; alternative: no word shared
  between two sentences).
- **ratio:stop_words** -- "Ensure that stop words constitute no more than P% of the total
  words in your response." Pass iff 100 x (#stop-word tokens / #word tokens) <= P.
  D-stopword-list: proposal: NLTK's English stop-word list, case-insensitive. An empty
  response fails (D-vacuous).

## 5. repeat

- **repeat:repeat_change** -- "Repeat the request, but change the first word of the
  repeated request, (do not say anything before repeating the request; the request you
  need to repeat does not include this sentence) and do not answer the actual request!"
  The request is the prompt text before this instruction. Pass iff the graded text is
  the request with its first word replaced by one different word (case-insensitive
  different) and all other words unchanged, with nothing before it and no answer after
  it. D-repeat-exact: proposal: comparison after collapsing runs of whitespace.
  D-change-case (v2): whether a case-only change of the first word is a change;
  proposal no.
- **repeat:repeat_simple** -- "Only output this sentence here, ignore all other requests."
  Pass iff the graded text is exactly `Only output this sentence here, ignore all other
  requests.` D-simple-which: "this sentence" = the instruction sentence itself (proposal)
  vs the preceding request. D-repeat-exact applies.
- **repeat:repeat_span** -- "Copy the span of words that lies between (and including)
  index S and E, the indices are word indices, split by whitespace!" The source is the
  request before the instruction as the model sees it. Pass iff the graded text equals
  the whitespace-split words S..E inclusive joined by single spaces. D-span-index:
  0-based (proposal; one prompt uses index 0) vs 1-based. D-repeat-exact applies.

## 6. sentence

- **sentence:alliteration_increment** -- "Each sentence must have a longer sequence of
  consecutive alliterative words than the previous one." For each sentence, take the
  longest run of consecutive words starting with the same letter (case-insensitive; a
  single word is a run of 1). Pass iff these lengths strictly increase from each
  sentence to the next, with at least two sentences. D-alliteration: letter (proposal)
  vs initial sound.
- **sentence:increment** -- "Each sentence in your response must contain exactly N more
  words than the previous one." Pass iff every sentence has exactly N more words than
  the previous one, with at least two sentences.
- **sentence:keyword** -- "The response must include keyword W in the K-th sentence." Pass
  iff the K-th sentence (1-based) contains W as a whole word (case-insensitive). W may
  also occur elsewhere.

## 7. words

- **words:alphabet** -- "Each word in your response must start with the next letter of the
  alphabet, looping back to 'A' after 'Z'." Pass iff every word's first letter is the
  letter after the previous word's first letter (case-insensitive, Z then A). The first
  word may start with any letter (D-alphabet-start). A word that starts with a digit
  breaks the sequence.
- **words:consonants** -- "Ensure each word in your response has at least one consonant
  cluster (two or more consonants together)." Pass iff every word contains two adjacent
  consonant letters (by spelling). D-y: proposal: y is a consonant. Words without
  letters (numbers) fail the check (D-word).
- **words:keywords_specific_position** -- "Include keyword K in the n-th sentence, as the
  m-th word of that sentence." Pass iff the n-th sentence's m-th word (both 1-based)
  is K (case-insensitive).
- **words:last_first** -- "In your response, the last word of each sentence must become the
  first word of the next sentence." Pass iff for every pair of consecutive sentences the
  last word of the first equals the first word of the second (case-insensitive), with
  at least two sentences.
- **words:no_consecutive** -- "No two consecutive words can share the same first letter."
  Pass iff no two adjacent words start with the same letter (case-insensitive), across
  sentence boundaries too. Tokens without letters are skipped.
- **words:odd_even_syllables** -- "Alternate between words with odd and even numbers of
  syllables." Pass iff the syllable counts of consecutive words alternate in parity
  (either parity first). D-syllable: dictionary pronunciation (proposal) vs heuristic.
- **words:palindrome** -- "Include at least 10 single-word palindromes, each at least 5
  characters long." Pass iff at least 10 distinct words (D-palindrome-distinct, proposal
  distinct) of at least 5 letters read the same reversed (case-insensitive).
- **words:paragraph_last_first** -- "Each paragraph of your response must end with the same
  word it started with, separate paragraphs with a newline." Paragraphs are separated
  by line breaks; blank lines are ignored. Pass iff every paragraph's first word equals
  its last word (case-insensitive, punctuation ignored).
- **words:prime_lengths** -- "Use only words with lengths that are prime numbers." Pass iff
  every word's length in letters and digits (apostrophes and hyphens not counted) is
  prime (2, 3, 5, 7, 11, 13, ...).
- **words:repeats** -- "The response should not repeat any word more than N times." Pass iff
  no word (case-insensitive) occurs more than N times. D-repeat-count: occurrences <= N
  (proposal) vs repetitions <= N (occurrences <= N + 1).
- **words:start_verb** -- "The response must start with a verb." Pass iff the first word of
  the graded text, skipping leading non-letter characters, functions as a verb in its
  sentence. D-verb: in-context part of speech (proposal) vs any word that can be a verb.
- **words:vowel** -- "Write a paragraph using words that contain only three types of
  vowels." Pass iff the response is one paragraph and the set of distinct vowel letters
  (a, e, i, o, u; y not a vowel) used across all its words has at most three members.
  D-vowel-reading: union over the paragraph at most three (proposal) vs exactly three vs
  each word separately.
- **words:words_position** -- "The second word in your response and the second to last word
  in your response should be the word W." Pass iff word 2 and the second-to-last word
  are both W (case-insensitive, punctuation ignored).

## 8. Score-level transforms

- **Loose grading** (IFBench's second metric) re-grades transformed copies of the
  response (for example with the first or last line removed, or Markdown asterisks
  removed) and passes a check when any copy passes. The contract judges the response
  itself, so a loose pass whose untransformed response fails the contract is a pass the
  contract contradicts. D-loose: whether the evaluation reports loose or strict scores;
  proposal: strict is the score of record.

## Change log

- **v2, 2026-11-11 00:21 UTC** (after reading the grader code; each change states its
  reason, and none adopts a grader behavior as the proposal):
  1. D-typographic narrowed. Reason: for word-level checks the typographic apostrophe
     and typographic quotes are punctuation under every reading (`don’t` is the word
     `don't`; `“The”` is the word `The`), so there is no second verdict to decide. The
     decision entry now covers only which characters delimit a quotation in
     format:quotes and format:quote_unquote (the prompt itself names "double quotes and
     single quotes", which a reader could take as the ASCII characters only). Fixtures
     that put typographic marks on words are therefore labeled without a D-tag.
  2. New D-japanese-digits (count:words_japanese). Reason: a probe put the numeral
     `2024` in a Japanese slot, and a careful reader could call Arabic numerals
     language-neutral (they are written in Japanese text) or not Japanese. Proposal:
     a numeral is not a Japanese word.
  3. New D-change-case (repeat:repeat_change). Reason: a probe changed only the case of
     the first word (`write` for `Write`); a reader could call that a changed word.
     Proposal: case-only change is not a change.
  4. format:emoji: emoji are recognized as Unicode emoji sequences, including flags
     (regional-indicator pairs) and keycaps. Reason: v1 said "Unicode emoji" without
     naming the multi-code-point forms; this is a clarification, not a new reading.
- **v3, 2026-11-11 00:32 UTC**: new D-paren-closed (format:parentheses). Reason: the
  reference's unit test `TEST_NESTED_PARENTHESES_TRUE2` (instructions_test.py line 256)
  is a 21-deep run of openings whose closers do not match; on reflection a careful reader
  could call that "nested at least 5 levels deep" even though it is not properly closed,
  so the v1 wording "properly nested and closed" is a reading, not the only one. The
  proposal stays: properly closed.
- **v4, 2026-11-11 00:44 UTC** (after looking at non-held-out panel responses): new
  D-japanese-segmentation (count:words_japanese). Reason: panel responses written
  entirely in Japanese have few or no spaces, so whitespace splitting finds fewer than N
  "words", although every word of such a response is Japanese. Proposal: a response
  whose letters are all Japanese passes; otherwise whitespace tokens as in v1.
  Alternative: whitespace tokens always (then such a response fails by D-vacuous).
