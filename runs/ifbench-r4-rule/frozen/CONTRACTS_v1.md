# IFBench check contracts (v1)

Written from the task text only: the 300 prompts of `case/data/train-00000-of-00001.parquet`
(instruction sentences listed per check below, extracted by `audit/scripts/instruction_variants.py`)
and `case/panel/CONFIGS.md`. No grader or reference code was read before this file was hashed.
Later changes are appended at the end under "Changes", each with its reason.

Each check is one instruction id. A prompt passes (prompt-level strict) when every check in it
passes. Unless a check says otherwise, the general rules G1-G7 apply. Where the text allows two
verdicts, the contract names a decision entry `D-<topic>` and states the proposed reading; the
other readings are listed in the decision table (`audit/ISSUE.md`, "Decision entries").

## General rules

- **G1 Graded text.** The text after the last `</think>` in the completion, with leading whitespace
  removed; the whole completion when it contains no `</think>` and never opened reasoning. A
  completion that opened reasoning (`<think>`) and never closed it is an **extraction failure**: it
  fails every check, and the report counts these separately. A separate reasoning field is never
  graded. A truncated completion (`finish_reason == length`) is graded as written.
- **G2 Empty text (D-empty).** An empty or whitespace-only graded text fails every check, including
  checks whose condition is universally quantified ("every word ...").
- **G3 Words (D-word).** A word is a whitespace-separated token after stripping leading and trailing
  characters that are not letters or digits; tokens that become empty (bullets `*`, `-`, `#`,
  `---`, emoji, lone punctuation) are not words. Internal apostrophes and hyphens stay in the word
  (`don't`, `well-known` are one word each). A list label at the start of a line (`1.`, `2)`,
  `a)`) is not a word. Markdown markup (`**`, `_`, backticks, `#`) never changes a word's identity:
  `**Paradox**` is the word `Paradox`.
- **G4 Sentences (D-sentence).** A sentence ends at terminal punctuation (`.`, `!`, `?`, `?!`, `…`,
  `...`, possibly followed by closing quotes, brackets or emoji) followed by whitespace or the end
  of the text. Abbreviations (`e.g.`, `Dr.`, `U.S.`), initials, decimal points and list labels
  (`1.`) do not end a sentence. A line that contains words and has no terminal punctuation (a
  heading, a list item, a table row) ends at the line break and is one sentence.
- **G5 Paragraphs (D-paragraph).** Paragraphs are separated by one or more blank lines, except where
  a check defines its own separator.
- **G6 Word matching (D-keyword-match).** A keyword or name matches a word case-insensitively and as
  a whole word (letters on neither side); inflected or derived forms (`whispers`, `rivers`) do not
  match; a possessive (`river's`) matches.
- **G7 Vacuous conditions (D-vacuous).** When a non-empty response contains no instance of the
  structure that a universally quantified condition constrains (no quoted phrase, fewer than N
  words, a single sentence where consecutive pairs are compared), the condition holds (pass).
- **G8 Markup (D-markup).** Markdown emphasis and heading markers do not count as content for word,
  label or option comparisons (`**My Answer:**` is the label `My Answer:`), but they are characters
  for checks about characters (whitespace, punctuation marks, indentation).

## count

- **count:conjunctions** -- "Use at least N different coordinating conjunctions in the response."
  (N in 2..5; key 8 writes "4.0"). Coordinating conjunctions are the seven words for, and, nor, but,
  or, yet, so. Pass iff at least N distinct members of that set occur in the graded text used as
  coordinating conjunctions (case-insensitive). Fail otherwise. D-conj-usage: whether an occurrence
  of `for`/`so`/`yet` used as a preposition or adverb counts; proposed: it does not.
- **count:keywords_multiple** -- "Include keyword k1 once ..., k2 twice ..., k3 three times ..., k4
  five times ..., and k5 seven times in your response." Pass iff the counts of k1..k5 (G6) are
  exactly 1, 2, 3, 5, 7. D-count-exact: "once/twice/N times" means exactly (proposed) or at least.
- **count:numbers** -- "Include exactly N numbers in the response." Pass iff the graded text contains
  exactly N numerals, counted by occurrence. A numeral is a maximal run of digits, with internal
  `,` or `.` between digit groups (`1,000`, `3.14` are one numeral); a sign, `%` or ordinal suffix
  does not split it (`-5`, `10%`, `1st` are one numeral each); `2024-05-01` is three numerals; list
  labels (`1.`) are numerals. D-number: number words (`two`) do not count (proposed) or count;
  list labels count (proposed) or not.
- **count:person_names** -- "Mention at least N different person names in the response, from this list
  of person names: Emma, ..., Jonathan ." Pass iff at least N distinct names from the 50-name list
  occur as whole words written with an initial capital (G6 otherwise). D-name-usage: a lower-case
  common-noun use (`grace`, `lily`) does not count (proposed) or counts.
- **count:pronouns** -- "The response should include at least N pronouns." Pass iff the graded text
  has at least N pronoun occurrences (not distinct). D-pronoun-set, proposed set: personal (I, me,
  you, he, him, she, her, it, we, us, they, them), possessive (my, mine, your, yours, his, hers,
  its, our, ours, their, theirs), reflexive (myself ... themselves); alternative: also
  demonstrative, relative, interrogative and indefinite pronouns (this, who, which, someone ...).
- **count:punctuation** -- "Use every standard punctuation mark at least once, including semicolons,
  colons, and the interrobang (?!)." Pass iff the graded text contains each of: period, comma,
  question mark, exclamation mark, colon, semicolon, apostrophe, quotation mark, hyphen, dash,
  parentheses, square brackets, braces, ellipsis, and the interrobang written `?!` or `‽`.
  Typographic forms count (`’`, `“ ”`, `—`, `–`, `…`). D-punct-set: proposed the English set
  above; alternative: every ASCII punctuation character (`#`, `$`, `%`, `&`, `*`, `+`, `<`, `=`, `>`,
  `@`, `\`, `^`, `_`, backtick, `|`, `~`, `/` as well).
- **count:unique_word_count** -- "Use at least N unique words in the response." Pass iff the number of
  distinct words (G3, case-insensitive) is at least N. D-unique: distinct word types (proposed) or
  words that occur exactly once.
- **count:word_count_range** -- "The response must contain between A and B words." Pass iff
  A <= word count (G3) <= B. D-between: inclusive (proposed) or exclusive.
- **count:words_japanese** -- "Every Nth word of your response must be in Japanese." Words are
  whitespace tokens (G3); pass iff every word at 1-based position k*N (k = 1, 2, ...) is written in
  Japanese script (hiragana, katakana or kanji, ignoring attached punctuation). Other words are
  unrestricted. G7 applies with fewer than N words. D-japanese-script: romanized Japanese does not
  count (proposed) or counts.

## custom (one prompt each; the whole prompt is the task text)

- **custom:character_reverse** -- "What animal is the national symbol of the US? Respond to this query,
  but make your sentence in reverse order of what it should be, per letter." Pass iff the graded
  text, reversed character by character, is a sentence that answers the query (letter case of the
  reversed form is free; factual correctness is not judged). Fail if any part is not reversed,
  including added unreversed commentary (D-reverse-extra, proposed: added text fails), or if only
  the word order is reversed.
- **custom:csv_city** -- "Generate CSV data: The column names are ["ID", "Country", "City", "Year",
  "Count"], the data should be comma delimited. Please generate 7 rows." Pass iff the CSV payload is
  a header row with exactly these five names in this order, then exactly 7 data rows, every row
  with 5 comma-delimited fields (CSV quoting rules apply; a quoted header name equals the unquoted
  one). D-csv-payload: the payload may be a fenced block surrounded by short prose (proposed) or the
  response must be CSV only. D-csv-rowcount: 7 data rows plus the header (proposed) or 7 lines in all.
- **custom:csv_quotes** -- "... the data should be tab delimited. Please generate 3 rows and enclose
  each single field in double quotes." Pass iff header (StudentID, Subject, Grade, Semester, Score in
  order) plus exactly 3 data rows, tab-delimited, 5 fields per row, and every field of every row,
  header included, enclosed in double quotes. D-csv-payload and D-csv-rowcount as above;
  D-csv-header-quotes: the header fields must be quoted too (proposed) or only data fields.
- **custom:csv_special_character** -- "... comma delimited. Please generate 14 rows. Add one field which
  contains a special character and enclose it in double quotes." Pass iff header (ProductID,
  Category, Brand, Price, Stock) plus exactly 14 data rows of 5 comma-delimited fields, and at least
  one data field is enclosed in double quotes and contains a special character (a character that is
  not a letter, digit or space). D-csv-special: at least one such field (proposed), exactly one, or
  one per row; "add one field" read as a sixth column is not proposed.
- **custom:date_format_list** -- "List the start dates of all the battles Napoleon fought separated by
  commas, use the following date format: YYYY-MM-DD. Do not provide an explanation." Pass iff the
  graded text is a comma-separated list of at least two items, each a valid calendar date written
  YYYY-MM-DD, with no other text. D-custom-content: historical correctness and completeness are not
  judged (proposed) or are judged. D-list-extra: labels or an intro line fail (proposed).
- **custom:european_capitals_sort** -- "Give me the names of all capital cities of european countries
  whose latitude is higher than than 45 degrees? List the capital cities without country names,
  separated by commas, sorted by latitude, from highest to lowest." Pass iff the graded text is a
  comma-separated list of city names only (no country names, no other text), sorted by latitude
  from north to south, containing exactly the capitals of European countries north of 45 N.
  D-capitals-set (proposed: sovereign states wholly or mainly in Europe, Russia included,
  Kazakhstan and dependencies excluded; Reykjavik, Helsinki, Oslo, Tallinn, Stockholm, Riga, Moscow,
  Copenhagen, Vilnius, Minsk, Dublin, Berlin, Amsterdam, Warsaw, London, Brussels, Kyiv, Prague,
  Luxembourg, Paris, Vienna, Bratislava, Budapest, Vaduz, Chisinau, Bern, Ljubljana, Zagreb).
- **custom:mcq_count_length** -- "Generate 4 multiple choice questions with 5 options each about '20th
  century art history'. Each question should start with the label 'Question'. The questions should
  get progressively longer. Do not provide an explanation." Pass iff exactly 4 questions, each
  starting with the label `Question` (markup ignored, G8), each with exactly 5 options, question
  lengths strictly increasing, and no explanation. D-mcq-length: length of the question stem in
  characters (proposed), in words, or of the whole question block with its options. D-mcq-answer:
  an answer key without reasons is not an explanation (proposed).
- **custom:multiples** -- "Count from 10 to 50 but only print multiples of 7." Pass iff the graded
  text prints 14, 21, 28, 35, 42, 49 in this order and nothing else besides separators.
  D-list-extra: an intro line fails (proposed) or is allowed if it prints no other number.
- **custom:reverse_newline** -- "List the countries of Africa in reverse alphabetical order, each on a
  new line." Pass iff every listed line holds one country name (list labels ignored), the names are
  in strictly descending alphabetical order, and the list holds the 54 UN member states of Africa.
  D-africa-set: completeness required (proposed) or only order and one-per-line. D-list-extra.
- **custom:sentence_alphabet** -- "Tell me a 26-sentence story where each sentence's first word starts
  with the letters of the alphabet in order." Pass iff the story has exactly 26 sentences (G4) and
  the first word of sentence i starts with the i-th letter, A to Z, case-insensitive. A title line
  is a sentence under G4 (D-sentence).
- **custom:word_reverse** -- "... make your sentence in reverse order of what it should be, per word."
  Pass iff the graded text is one sentence whose words, read in reverse order, form a sentence that
  answers the query, with each word spelled normally. D-reverse-extra as above.

## format

- **format:emoji** -- "Please use an emoji at the end of every sentence." Pass iff every sentence (G4)
  ends with an emoji, placed either just before or just after its terminal punctuation. Emoji are
  Unicode emoji characters (Extended_Pictographic, with modifiers and variation selectors); text
  emoticons such as `:)` are not (D-emoji-def).
- **format:line_indent** -- "Create stairs by incrementally indenting each new line." Pass iff every
  non-empty line has more leading whitespace than the previous non-empty line (the first may have
  none). D-indent: strictly increasing on every line (proposed) or a stairs pattern that may reset;
  any Unicode whitespace counts as indentation, a tab counting as one character (D-indent-unit).
- **format:list** -- "Answer with a list of items, instead of bullet points use SEP." (SEP in `!?!?`,
  `-`, `SEPARATOR`). Pass iff the response is a list of at least two items in which SEP stands where
  bullet points would go and no other bullet marker (`*`, `•`, numbering, or `-` when SEP is not
  `-`) marks items. D-list-sep: SEP at the start of each item (bullet position) or SEP between
  items; proposed: both accepted.
- **format:newline** -- "Write each word on a new line." Pass iff every non-empty line holds exactly one
  word (G3); lines that hold no word are allowed.
- **format:no_bullets_bullets** -- "Your answer must contain at least two sentences ending in a period
  followed by at least two bullet points denoted by *." Pass iff at least two sentences ending in `.`
  occur before the first `*` bullet, and at least two bullet points (lines starting with `*` and a
  space, after optional indentation) follow them. Other content is allowed (D-nobullets-order).
- **format:no_whitespace** -- "The output should not contain any whitespace." Pass iff the graded text,
  ignoring leading and trailing whitespace (D-trailing-ws), contains no Unicode whitespace character.
- **format:options** -- "Answer with one of the following options: OPTS." (yes/no/maybe; I know or I
  don't know; a), b), c), d)). Pass iff the graded text, ignoring surrounding whitespace, markup,
  surrounding quotes and a final period, equals exactly one option, case-insensitive.
  D-options-extra: proposed as stated; alternative: the response picks exactly one option and may
  add other text.
- **format:output_template** -- "Use this exact template for your response: My Answer: [answer] My
  Conclusion: [conclusion] Future Outlook: [outlook]". Pass iff the graded text starts with
  `My Answer:` (markup ignored), then has `My Conclusion:` and `Future Outlook:` in this order, each
  label exactly once, each followed by non-empty content that replaces the placeholder (literal
  `[answer]` etc. fail). D-template-brackets: content kept inside square brackets is allowed
  (proposed).
- **format:parentheses** -- "Nest parentheses (and [brackets {and braces}]) at least 5 levels deep."
  Pass iff the graded text contains a properly matched nesting of bracket pairs (any of `()`, `[]`,
  `{}`) at least 5 deep. D-paren-types: any mix of the three types (proposed) or all three types used.
- **format:quote_unquote** -- "Every quoted phrase must be followed by an unquoted explanation." Pass
  iff each quoted phrase (text inside double quotes, straight or typographic) is followed, before the
  next quoted phrase or the end, by unquoted text that explains it. G7 applies when there is no
  quoted phrase. D-quote-chars: single-quoted phrases count too (alternative).
- **format:quotes** -- "Include quotes within quotes within quotes, at least 3 levels deep,
  alternating between double quotes and single quotes." Pass iff the graded text contains a
  quotation nested at least 3 deep whose levels alternate between double and single quotes (either
  type outermost; straight or typographic). Apostrophes inside words are not quotes.
- **format:sub-bullets** -- "Your response must include bullet points denoted by * and at least one
  sub-bullet point denoted by - for each bullet point." Pass iff there is at least one `*` bullet,
  and every `*` bullet is followed, before the next `*` bullet, by at least one line starting with
  `-` (after optional indentation). D-subbullet-indent: indentation not required (proposed) or
  required.
- **format:thesis** -- "Each section must begin with a thesis statement in italics, use HTML to
  indicate the italics." Pass iff every section begins (after its heading, if any) with a statement
  enclosed in `<i>...</i>` or `<em>...</em>`. D-section: sections are delimited by heading lines,
  text before the first heading is a section, and a response without headings is one section
  (proposed); alternative: every paragraph is a section.
- **format:title_case** -- "Write the entire response in title case (capitalize the first letter of
  every major word)." Pass iff every major word starts with an upper-case letter. Minor words
  (articles; coordinating conjunctions; prepositions of four letters or fewer; `to`, `as`) may be
  lower-case except as the first word of a line or sentence; capitalizing them is allowed.
  Tokens that do not start with a letter are ignored. D-title-minor.

## ratio

- **ratio:overlap** -- "Maintain a trigram overlap of P% (±2%) with the provided reference text."
  The reference text is the prompt's request (the prompt without its instruction sentences); the
  prompt never labels it (D-overlap-reference). Pass iff the overlap is within P-2 and P+2
  inclusive. D-overlap-measure: proposed: share of the response's distinct word trigrams
  (lower-cased, punctuation stripped) that occur in the reference; alternatives: share of the
  reference's trigrams found in the response, or Jaccard, or character trigrams.
- **ratio:sentence_balance** -- "Ensure that the ratio of sentence types (declarative, interrogative,
  exclamatory) in your response is balanced." Type by terminal punctuation: `?` interrogative, `!`
  exclamatory, else declarative. Pass iff all three types occur and the largest count exceeds the
  smallest by at most 1. D-balance: tolerance (exactly equal; within 1 (proposed); a looser ratio).
- **ratio:sentence_type** -- "Maintain a 2:1 ratio of declarative to interrogative sentences in your
  response." Pass iff interrogative count >= 1 and declarative count = 2 x interrogative count
  (exclamatory sentences are ignored). D-ratio-exact: exact (proposed) or approximate.
- **ratio:sentence_words** -- "Respond with three sentences, all containing the same number of
  characters but using all different words." Pass iff exactly three sentences (G4), each with the same
  number of characters (all characters of the sentence including spaces and punctuation, D-char-count),
  and no word (case-insensitive) used twice in the response (D-different-words; alternative: no word
  shared between two sentences).
- **ratio:stop_words** -- "Ensure that stop words constitute no more than P% of the total words in your
  response." Pass iff stop words / words (G3) <= P/100. D-stopword-list: the stop-word list is
  undefined; proposed: a standard English list such as NLTK's (179 words).

## repeat

- **repeat:repeat_change** -- "REQUEST Repeat the request, but change the first word of the repeated
  request, (do not say anything before repeating the request; the request you need to repeat does not
  include this sentence) and do not answer the actual request!" Pass iff the graded text starts with
  the request in which the first word is replaced by a different word (a change of letter case only
  is not a change) and the rest is verbatim (whitespace differences ignored), with nothing before it
  and no answer to the request after it. D-repeat-trailing: any text after the repeated request
  fails (proposed) or only text that answers it fails.
- **repeat:repeat_simple** -- "REQUEST Only output this sentence here, ignore all other requests."
  D-repeat-simple-target: "this sentence" is the instruction sentence itself (proposed) or the
  request. Pass iff the graded text, ignoring surrounding whitespace, is exactly
  `Only output this sentence here, ignore all other requests.`
- **repeat:repeat_span** -- "REQUEST Copy the span of words that lies between (and including) index S
  and E, the indices are word indices, split by whitespace!" Indices are 0-based (index 0 occurs).
  Pass iff the graded text, ignoring surrounding whitespace, is words S..E of the request split by
  whitespace, joined by whitespace, with attached punctuation kept and nothing else
  (D-span-extra).

## sentence

- **sentence:alliteration_increment** -- "Each sentence must have a longer sequence of consecutive
  alliterative words than the previous one." For each sentence take the longest run of consecutive
  words with the same first letter (D-alliteration: letter (proposed) or initial sound). Pass iff
  the run lengths strictly increase from each sentence to the next.
- **sentence:increment** -- "Each sentence (in your response) must contain exactly N more words than
  the previous one." Pass iff for each consecutive pair of sentences, words(next) = words(prev) + N.
- **sentence:keyword** -- "The response must include keyword W in the N-th sentence." Pass iff the
  N-th sentence (1-based, G4) contains W (G6). Fewer than N sentences: fail.

## words

- **words:alphabet** -- "Each word in your response must start with the next letter of the alphabet,
  looping back to 'A' after 'Z'." Pass iff for every consecutive pair of words, the second starts with
  the letter after the first's initial (Z then A), case-insensitive. A word that does not start with
  a letter breaks the sequence.
- **words:consonants** -- "Ensure each word in your response has at least one consonant cluster (two or
  more consonants together)." Pass iff every word contains two adjacent consonant letters. Vowels
  are a, e, i, o, u (accented forms included); D-consonant-y: `y` counts as a consonant (proposed)
  or as a vowel.
- **words:keywords_specific_position** -- "Include keyword W in the N-th sentence, as the M-th word of
  that sentence." Pass iff word M (1-based) of sentence N (1-based) is W (G6).
- **words:last_first** -- "In your response(,) the last word of each sentence must become the first word
  of the next sentence." Pass iff for each consecutive pair of sentences, the last word of the first
  equals the first word of the second (case-insensitive, G3).
- **words:no_consecutive** -- "No two consecutive words can share the same first letter." Pass iff no
  two consecutive words (across sentence and line boundaries) start with the same letter,
  case-insensitive (first alphanumeric character).
- **words:odd_even_syllables** -- "Alternate between words with odd and even numbers of syllables."
  Pass iff the syllable counts of consecutive words alternate in parity. D-syllable: counts follow
  standard English pronunciation (proposed); a heuristic count is an approximation.
- **words:palindrome** -- "Include at least 10 single-word palindromes, each at least 5 characters
  long." Pass iff at least 10 distinct words of at least 5 letters read the same backwards
  (case-insensitive). D-palindrome-distinct: distinct (proposed) or occurrences.
- **words:paragraph_last_first** -- "Each paragraph of your response must end with the same word it
  started with, separate paragraphs with a newline." Paragraphs are the non-empty lines. Pass iff in
  every paragraph the first word equals the last word (case-insensitive, G3).
- **words:prime_lengths** -- "Use only words with lengths that are prime numbers." Pass iff every word's
  length (letters and digits, G3; internal apostrophes and hyphens not counted) is prime (2, 3, 5,
  7, 11, ...). `a` and `I` fail.
- **words:repeats** -- "The response should not repeat any word more than N times." Pass iff no word
  (case-insensitive) occurs more than N times. D-repeat-count: occurrences <= N (proposed) or
  repetitions after the first <= N.
- **words:start_verb** -- "The response must start with a verb." Pass iff the first word of the graded
  text (markup ignored) is a verb in its context (an imperative, or a finite or non-finite verb).
- **words:vowel** -- "Write a paragraph using words that contain only three types of vowels." Pass iff
  the response is one paragraph (G5) and the distinct vowel letters (a, e, i, o, u) used across all
  its words number at most three. D-vowel: across the response, at most three (proposed); exactly
  three; or within each word.
- **words:words_position** -- "The second word in your response and the second to last word in your
  response should be the word W." Pass iff word 2 and word (n-1) of the graded text are W (G6).

## Score-level transforms

- Prompt-level strict accuracy: a prompt passes iff all its checks pass on the graded text.
  Instruction-level accuracy: share of (prompt, check) pairs that pass.
- The task text defines no loose grading. A loose pass is consistent with the contract only when the
  text it removes is markup that G8 already ignores; any other loose pass on a response that the
  contract fails is a pass that the contract contradicts (D-loose decides whether loose scores are
  reported at all).

## Changes

(none yet)
