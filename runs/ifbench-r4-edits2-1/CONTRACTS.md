# IFBench contracts (written from the instruction text only)

Written before reading any grader or reference code. Source: the instruction sentences in the
prompts (`audit/frozen/instruction_templates.json`, checked against all 344 instances) and
`case/panel/CONFIGS.md` for the graded text. Each check's contract states pass and fail conditions.
Where the text allows two verdicts, the contract names a decision entry `D-<topic>` and states the
proposed reading; the decision table at the end lists both readings.

## General definitions

- **G1 Graded text.** The text after the model's last end-of-reasoning marker (`</think>` for
  Qwen3). A completion that opens reasoning (`<think>`) and never closes it is an extraction
  failure: it fails every check and is counted separately. A completion with no reasoning marker
  is graded whole. A separate reasoning field is never graded.
- **G2 Empty graded text** (empty or whitespace only) fails every check: it is no attempt at the
  instruction (`D-vacuous`, reading A, covers non-empty responses only).
- **G3 Word.** A word is a whitespace-separated token after removing leading and trailing
  punctuation and markup (`* _ # > \` ~ " ' “ ” ‘ ’ ( ) [ ] { } < > , . ; : ! ? …` and dashes),
  that still contains a letter or digit. Internal apostrophes and hyphens stay inside the word
  ("don't", "well-known" are one word each; `D-hyphen`). A typographic apostrophe (’) is the same
  as `'`. List labels at the start of a line (`-`, `*`, `•`, `1.`, `2)`, `a)`) and HTML tags are
  markup, not words (`D-list-label`). Numerals are words (`D-numeral-word`).
- **G4 Word comparison** is case-insensitive and ignores the punctuation and markup that G3 strips.
  A keyword matches a word only when the whole word equals it; inflected or longer forms do not
  match ("whispers" is not "whisper"; `D-keyword-form`).
- **G5 Sentence.** A sentence ends at a terminal mark (`.`, `!`, `?`, `…`, or a run of them),
  optionally followed by closing quotes or brackets and by emoji, when whitespace or the end of the
  text follows; a line break also ends a sentence. Every resulting span that contains a word is a
  sentence, including a heading or list item without a terminal mark (`D-sentence-fragment`).
  Abbreviations (Dr., Mr., e.g., i.e., U.S. inside a sentence) and decimal points do not end a
  sentence. Sentence positions are 1-based.
- **G6 Paragraph.** Unless the instruction defines it, paragraphs are separated by one or more
  blank lines. (words:paragraph_last_first defines paragraphs as newline-separated lines.)
- **G7 Markup.** Markdown and HTML markup are presentation: they never count as words, sentences,
  or content, and markup around a word does not change the word (bold `**x**`, italics `*x*`,
  `<b>x</b>`). Exceptions are the checks that ask for markup (format:thesis, format:sub-bullets,
  format:no_bullets_bullets, format:list, format:line_indent).
- **G8 Universal constraints** ("every", "each", "no", "only", "all"): a non-empty response that has
  no unit to check passes, except where the instruction asks for a structure to exist (stated per
  check) (`D-vacuous`).
- **G9 Whitespace at the edges.** Leading whitespace is already removed by the extraction; trailing
  whitespace (for example a final newline) is ignored by every check (`D-trailing-ws`).

## Per-check contracts

### count

- **count:conjunctions** — "Use at least {n} different coordinating conjunctions in the response."
  Pass iff at least n distinct members of {for, and, nor, but, or, yet, so} occur as words used as
  coordinating conjunctions. Fail otherwise. Whether an occurrence used in another role ("for" as a
  preposition, "so" as an adverb) counts is `D-conjunction-role`; proposed: only conjunction uses
  count. Fixtures avoid the disputed uses.
- **count:keywords_multiple** — "Include keyword k1 once …, k2 twice …, k3 three times …, k4 five
  times …, and k5 seven times …". Pass iff k1, k2, k3, k4, k5 occur as whole words (G4) exactly
  1, 2, 3, 5, 7 times. Fail if any count differs (`D-count-exact`: proposed exact, alternative at
  least).
- **count:numbers** — "Include exactly N numbers in the response." Pass iff the number of numerals
  written with digits is exactly N. A numeral is a maximal digit sequence, with internal `.` or `,`
  between digits and an optional leading sign or trailing `%` (3.14, 1,000, -5, 50% are one number
  each). Occurrences count, not distinct values. List labels such as `1.` at line start are markup,
  not numbers (`D-list-label`). Spelled-out number words do not count (`D-number-words`).
- **count:person_names** — "Mention at least N different person names in the response, from this
  list of person names: …". Pass iff at least N distinct names from the given list occur as whole
  words with an initial capital letter (a possessive "Emma's" counts). Names outside the list do not
  count. A lowercase common noun ("grace", "lily") is not a mention (`D-name-case`).
- **count:pronouns** — "The response should include at least N pronouns." Pass iff the number of
  pronoun occurrences is at least N. Personal (I, me, you, he, him, she, her, it, we, us, they,
  them), possessive (mine, yours, his, hers, ours, theirs) and reflexive (myself, …) pronouns count.
  Whether possessive determiners (my, your, its, our, their) and demonstrative, relative,
  interrogative and indefinite pronouns count is `D-pronoun-set`; proposed: they count when they
  stand as pronouns (possessive determiners count). Fixtures use personal pronouns only.
- **count:punctuation** — "Use every standard punctuation mark at least once, including semicolons,
  colons, and the interrobang (?!)." Pass iff the response contains every mark of the standard
  English set: period, comma, question mark, exclamation mark, colon, semicolon, apostrophe,
  quotation mark, hyphen, dash (– or —), parentheses, square brackets, ellipsis (… or ...), slash,
  and an interrobang written `?!`, `!?` or `‽` (`D-punct-set`: the set; alternative all 32 ASCII
  punctuation characters). Fail if any is missing.
- **count:unique_word_count** — "Use at least N unique words in the response." Pass iff the number
  of distinct words (case-insensitive) is at least N (`D-unique`: distinct word types; alternative
  words that occur exactly once).
- **count:word_count_range** — "The response must contain between a and b words." Pass iff
  a <= word count <= b (G3; bounds inclusive, `D-between`).
- **count:words_japanese** — "Every Nth word of your response must be in Japanese." Words are
  whitespace-separated tokens with edge punctuation removed. Pass iff every token at a position
  that is a multiple of N (1-based) is written in Japanese script (hiragana, katakana, kanji; a
  token whose letters are all Japanese). Other tokens are unconstrained (`D-japanese-others`).
  Romaji does not count (`D-japanese-romaji`). A non-empty response with fewer than N tokens passes
  (G8).

### custom

These prompts pose a task whose content can be right or wrong. Proposed for all of them
(`D-custom-content`): grade the stated form and the content facts that the task fixes exactly
(the national animal, the multiples of 7); do not grade open factual completeness (all of
Napoleon's battles, all African countries), which needs an external list.

- **custom:character_reverse** — answer "What animal is the national symbol of the US?" in one
  sentence written in reverse character order. Pass iff the graded text, read backwards character
  by character, is a sentence that answers with the bald eagle (or eagle). Fail if it is forward
  text, word-reversed text, or does not name the eagle. Reversal of letters only versus all
  characters (punctuation position) is `D-reverse-punct`; proposed: punctuation may be at either
  end.
- **custom:word_reverse** — the same answer with its words in reverse order. Pass iff the words
  read in reverse order form a sentence that answers with the (bald) eagle, and the letters inside
  each word are not reversed. Fail on forward text or letter reversal.
- **custom:csv_city** — CSV with columns ["ID", "Country", "City", "Year", "Count"], comma
  delimited, 7 rows. Pass iff the response contains a header row with exactly these five names in
  this order (quotes optional), followed by exactly 7 data rows of 5 comma-separated fields.
  The header is not one of the 7 rows (`D-csv-header-row`). A code fence or a sentence around the
  CSV is allowed (`D-csv-wrapper`).
- **custom:csv_quotes** — columns ["StudentID", "Subject", "Grade", "Semester", "Score"], tab
  delimited, 3 rows, each single field enclosed in double quotes. Pass iff a header row and exactly
  3 data rows, each with 5 tab-separated fields, every field (header included, `D-csv-header-quotes`)
  enclosed in double quotes. Fail on comma delimiters, unquoted fields or another row count.
- **custom:csv_special_character** — columns ["ProductID", "Category", "Brand", "Price", "Stock"],
  comma delimited, 14 rows, one field that contains a special character enclosed in double quotes.
  Pass iff header + exactly 14 data rows of 5 comma-separated fields (a quoted field may contain a
  comma), and at least one field is enclosed in double quotes and contains a character that is not
  a letter, digit or space (`D-special-one`: at least one; alternative exactly one).
- **custom:date_format_list** — start dates of Napoleon's battles, separated by commas, format
  YYYY-MM-DD, no explanation. Pass iff the graded text is a comma-separated list of at least two
  items, each a valid date in YYYY-MM-DD, with no other text (no explanation, no battle names).
  Completeness and factual accuracy are not graded (`D-custom-content`).
- **custom:european_capitals_sort** — capitals of European countries with latitude above 45
  degrees, without country names, comma separated, from highest to lowest latitude. Pass iff the
  graded text is a comma-separated list of capital-city names with no country names and no other
  text, every listed city is such a capital, and the list is in strictly decreasing latitude.
  Completeness and the set of European countries are `D-custom-content` / `D-europe-set`.
- **custom:mcq_count_length** — 4 multiple-choice questions, 5 options each, each question starts
  with the label "Question", progressively longer questions, no explanation. Pass iff exactly 4
  questions, each starting with "Question", each followed by exactly 5 options, the question texts
  strictly increasing in length (`D-mcq-length`: characters of the question stem, excluding
  options; alternative words or stem plus options), and no explanation or answer key.
- **custom:multiples** — "Count from 10 to 50 but only print multiples of 7." Pass iff the numbers
  printed are exactly 14, 21, 28, 35, 42, 49 in this order and nothing else is printed besides
  separators (`D-multiples-prose`: alternative allows a short lead-in sentence).
- **custom:reverse_newline** — "List the countries of Africa in reverse alphabetical order, each on
  a new line." Pass iff each non-empty line holds one country name, the lines are in strictly
  descending alphabetical order, and there is no other text. Completeness is `D-custom-content`.
- **custom:sentence_alphabet** — "Tell me a 26-sentence story where each sentence's first word
  starts with the letters of the alphabet in order." Pass iff exactly 26 sentences (G5) and the
  first word of sentence i starts with the i-th letter (A…Z, case-insensitive). A title line is a
  sentence under G5 (`D-sentence-fragment`).

### format

- **format:emoji** — "Please use an emoji at the end of every sentence." Pass iff every sentence
  ends with an emoji: the last character before or after its terminal mark (ignoring whitespace) is
  an emoji (`D-emoji-position`: both placements pass). Fail if any sentence lacks one.
- **format:line_indent** — "Create stairs by incrementally indenting each new line." Pass iff
  there are at least two non-empty lines and each non-empty line has strictly more leading
  whitespace than the previous non-empty line (blank lines ignored; `D-indent-step`: any increase;
  alternative a constant step). A response on one line fails (no stairs).
- **format:list** — "Answer with a list of items, instead of bullet points use {sep}." Pass iff the
  answer is a list of at least two items delimited by sep, either as a marker before each item or
  as a separator between items (`D-list-sep-position`), and no other bullet marker (`*`, `-`, `•`,
  numbered labels) marks the items unless it is sep itself.
- **format:newline** — "Write each word on a new line." Pass iff no line contains more than one
  word (G3). Blank lines and lines without a word are allowed.
- **format:no_bullets_bullets** — "Your answer must contain at least two sentences ending in a
  period followed by at least two bullet points denoted by *." Pass iff at least two sentences
  that end in a period come before at least two bullet lines that start with `* ` (asterisk and a
  space). Bold text `**x**` is not a bullet. Text after the bullets is allowed (`D-nbb-after`).
- **format:no_whitespace** — "The output should not contain any whitespace." Pass iff the graded
  text, trailing whitespace ignored (G9), contains no whitespace character (space, tab, newline,
  no-break space and every other Unicode White_Space character).
- **format:options** — "Answer with one of the following options: {options}." The options are the
  slash- or comma-separated parts, or the two phrases joined by "or". Pass iff the graded text,
  ignoring case, edge whitespace, markup and a final period, is exactly one option
  (`D-options-extra`: alternative allows explanation after the option as long as exactly one option
  is given).
- **format:output_template** — "Use this exact template for your response: My Answer: [answer]
  My Conclusion: [conclusion] Future Outlook: [outlook]". Pass iff the graded text starts with
  "My Answer:", then contains "My Conclusion:" and then "Future Outlook:", each exactly once and in
  this order, each followed by non-empty content that is not the bare placeholder. Brackets around
  the filled content are optional (`D-template-brackets`); Markdown emphasis around a label is
  allowed (`D-template-markup`).
- **format:parentheses** — "Nest parentheses (and [brackets {and braces}]) at least 5 levels deep."
  Pass iff the response contains a correctly matched nest of bracket pairs (any of `()`, `[]`,
  `{}`) at least 5 levels deep (`D-paren-types`: any mix; alternative all three types must appear).
- **format:quote_unquote** — "Every quoted phrase must be followed by an unquoted explanation."
  Quoted phrases are delimited by double quotes (straight or typographic), guillemets, or single
  quotes used as quotation marks. Pass iff every quoted phrase is followed by unquoted text that
  contains a word before the next quoted phrase or the end. G8 applies (`D-vacuous`).
- **format:quotes** — "Include quotes within quotes within quotes, at least 3 levels deep,
  alternating between double quotes and single quotes." Pass iff there is a quotation nested at
  least 3 levels deep whose levels alternate between double and single quotes (straight or
  typographic; either may be the outer level).
- **format:sub-bullets** — "Your response must include bullet points denoted by * and at least one
  sub-bullet point denoted by - for each bullet point." Pass iff there is at least one bullet line
  starting with `* ` and every such bullet is followed, before the next `* ` bullet, by at least one
  line starting (after optional indentation) with `- `. Indentation of sub-bullets is not required
  (`D-subbullet-indent`).
- **format:thesis** — "Each section must begin with a thesis statement in italics, use HTML to
  indicate the italics." Sections are the parts that Markdown headings start; with no headings, the
  paragraphs (`D-section`). Pass iff the first text after each section's heading (or the first text
  of each paragraph) is a statement wrapped in `<i>…</i>` or `<em>…</em>`. Markdown italics fail.
- **format:title_case** — "Write the entire response in title case (capitalize the first letter of
  every major word)." Pass iff every major word starts with an uppercase letter. Minor words
  (articles, coordinating conjunctions, prepositions of four or fewer letters, "to", "as") may be
  lowercase except as the first word of a line or sentence (`D-titlecase-minor`). Words without a
  letter are ignored.

### ratio

- **ratio:overlap** — "Maintain a trigram overlap of p% (±2%) with the provided reference text."
  The reference text is the rest of the prompt. Proposed (`D-overlap-def`): word trigrams of the
  lowercased texts, punctuation stripped; overlap = share of the response's distinct trigrams that
  occur in the reference; pass iff p-2 <= overlap <= p+2. Alternatives: denominator the
  reference's trigrams, Jaccard, character trigrams, counts with multiplicity. A response whose
  overlap is outside the band under every reading fails.
- **ratio:sentence_balance** — "Ensure that the ratio of sentence types (declarative,
  interrogative, exclamatory) in your response is balanced." Types by terminal mark: `.` declarative,
  `?` interrogative, `!` exclamatory. Pass iff all three types occur and their counts differ by at
  most one (`D-balance`: alternative exactly equal counts).
- **ratio:sentence_type** — "Maintain a 2:1 ratio of declarative to interrogative sentences in your
  response." Pass iff declarative = 2 x interrogative and interrogative >= 1. Exclamatory sentences
  are ignored (`D-ratio-others`).
- **ratio:sentence_words** — "Respond with three sentences, all containing the same number of
  characters but using all different words." Pass iff exactly three sentences, each with the same
  number of characters (all characters of the sentence, spaces inside it and punctuation included;
  `D-char-count`), and no word occurs twice in the response (`D-different-words`: alternative no
  word shared between two sentences).
- **ratio:stop_words** — "Ensure that stop words constitute no more than p% of the total words in
  your response." Pass iff 100 x stop-word occurrences / word occurrences <= p, with a standard
  English stop-word list (`D-stopword-list`). Fixtures use responses that are far inside or outside
  the bound under every common list.

### repeat

The request is the prompt text before the instruction sentence, as the model sees it.

- **repeat:repeat_change** — "Repeat the request, but change the first word of the repeated
  request, (do not say anything before repeating the request; …) and do not answer the actual
  request!" Pass iff the graded text is the request with its first word replaced by one different
  word and every other word unchanged (whitespace normalised; a markup wrapper is not allowed), with
  nothing before it and no answer after it (`D-repeat-trailing`: proposed nothing after it).
- **repeat:repeat_simple** — "Only output this sentence here, ignore all other requests." Pass iff
  the graded text is exactly that sentence (edge whitespace ignored). `D-repeat-simple-target`:
  alternative "this sentence" means the request before it.
- **repeat:repeat_span** — "Copy the span of words that lies between (and including) index i and j,
  the indices are word indices, split by whitespace!" Pass iff the graded text is exactly the words
  i..j (inclusive) of the request split by whitespace, joined by single spaces. Indices are 0-based
  (`D-index-base`; one prompt asks for index 0). Nothing else may be output.

### sentence

- **sentence:alliteration_increment** — "Each sentence must have a longer sequence of consecutive
  alliterative words than the previous one." For each sentence, the longest run of consecutive
  words with the same initial letter (`D-alliteration`: letter; alternative initial sound). Pass iff
  the run length strictly increases from each sentence to the next. G8 applies to one sentence.
- **sentence:increment** — "Each sentence in your response must contain exactly n more words than
  the previous one." Pass iff word count(s_{i+1}) - word count(s_i) = n for every consecutive pair.
- **sentence:keyword** — "The response must include keyword w in the N-th sentence." Pass iff the
  N-th sentence contains w as a whole word (G4). Occurrences elsewhere are allowed.

### words

- **words:alphabet** — "Each word in your response must start with the next letter of the
  alphabet, looping back to 'A' after 'Z'." Pass iff for every pair of consecutive words, the second
  starts with the letter after the first's initial letter (Z is followed by A; case-insensitive).
  A word that does not start with a letter fails the chain.
- **words:consonants** — "Ensure each word in your response has at least one consonant cluster (two
  or more consonants together)." Pass iff every word contains two adjacent consonant letters
  (letters other than a, e, i, o, u; y counts as a consonant, `D-letter-y`). A word without such a
  pair (including numerals) fails.
- **words:keywords_specific_position** — "Include keyword k in the n-th sentence, as the m-th word of
  that sentence." Pass iff the m-th word of the n-th sentence is k (G4).
- **words:last_first** — "the last word of each sentence must become the first word of the next
  sentence." Pass iff for every consecutive pair of sentences, the last word of the first equals the
  first word of the second (G4).
- **words:no_consecutive** — "No two consecutive words can share the same first letter." Pass iff no
  two adjacent words (across sentence and line boundaries) start with the same letter,
  case-insensitive.
- **words:odd_even_syllables** — "Alternate between words with odd and even numbers of syllables."
  Pass iff the parity of the syllable count changes between every pair of consecutive words, with
  dictionary syllable counts (`D-syllables`). Fixtures use words with undisputed counts.
- **words:palindrome** — "Include at least 10 single-word palindromes, each at least 5 characters
  long." Pass iff at least 10 distinct words of at least 5 letters read the same backwards,
  case-insensitive (`D-palindrome-distinct`: alternative occurrences).
- **words:paragraph_last_first** — "Each paragraph of your response must end with the same word it
  started with, separate paragraphs with a newline." Paragraphs are non-empty lines. Pass iff the
  first and last word of every paragraph are equal (G4).
- **words:prime_lengths** — "Use only words with lengths that are prime numbers." Pass iff every
  word's length (letters and digits; internal apostrophes and hyphens not counted) is prime. One-
  letter words ("a", "I") fail.
- **words:repeats** — "The response should not repeat any word more than n times." Pass iff no word
  occurs more than n times (`D-repeat-count`: alternative more than n+1 times).
- **words:start_verb** — "The response must start with a verb." Pass iff the first word (G3, markup
  skipped) is a verb in its context.
- **words:vowel** — "Write a paragraph using words that contain only three types of vowels." Pass iff
  the vowel letters (a, e, i, o, u) used across all words of the response are at most three distinct
  ones (`D-vowel-scope`: alternative each word has at most three vowel types, or exactly three).
- **words:words_position** — "The second word in your response and the second to last word in your
  response should be the word k." Pass iff word 2 and word n-1 both equal k (G4).

## Decision entries

| Id | Reading A (proposed) | Reading B | Example where they differ |
|---|---|---|---|
| D-vacuous | "every/each/no/only" checks pass a non-empty response with no unit to check | such responses fail | "Every quoted phrase…" on a response without quotes |
| D-trailing-ws | trailing whitespace is ignored | trailing whitespace counts | `abc\n` for no_whitespace |
| D-sentence-fragment | headings and list items without a terminal mark are sentences | they are not sentences | a title line before an emoji-ended sentence |
| D-hyphen | hyphenated compounds are one word | each part is a word | "well-known" |
| D-list-label | list labels (`1.`, `-`, `*`) are markup, not words or numbers | they are words / numbers | "1. Apples" for count:numbers |
| D-numeral-word | numerals are words | numerals are not words | "1939" in words:alphabet |
| D-keyword-form | only the exact word matches | inflected/longer forms match | "whispers" for "whisper" |
| D-count-exact | "once/twice/N times" means exactly | at least | keyword used 3 times when "twice" is asked |
| D-conjunction-role | only conjunction uses count | any occurrence of the seven words | "for example" |
| D-number-words | only digit numerals are numbers | number words count | "two" |
| D-name-case | a name must be capitalised | any case | "grace" |
| D-pronoun-set | possessive determiners and pronoun uses of this/that/who/… count | personal, possessive and reflexive pronouns only | "my", "this" |
| D-punct-set | standard English marks + interrobang | all ASCII punctuation | missing `#` |
| D-unique | distinct word types | words that occur once | "the the cat" (2 vs 1) |
| D-between | bounds inclusive | exclusive | exactly 71 words for 71-73 |
| D-japanese-others | other words unconstrained | only every Nth word Japanese | all-Japanese text |
| D-japanese-romaji | romaji does not count | romaji counts | "hinshitsu" |
| D-custom-content | grade form and fixed facts, not open completeness | grade completeness too | a short, well-formatted Napoleon list |
| D-reverse-punct | final punctuation may sit at either end | strict character reversal | ".SU…" vs "SU….“ |
| D-csv-header-row | header not counted among the rows | header counted | 6 data rows + header for "7 rows" |
| D-csv-wrapper | fences / a sentence around the CSV allowed | CSV only | "Here is the data:" |
| D-csv-header-quotes | header fields must be quoted too | data fields only | unquoted header |
| D-special-one | at least one special quoted field | exactly one | two quoted fields |
| D-europe-set | capitals of UN-member European states | another list (Russia, Turkey, …) | Moscow |
| D-mcq-length | stem characters | words, or stem + options | equal word counts, rising characters |
| D-multiples-prose | numbers and separators only | a lead-in sentence allowed | "Here are the multiples: 14, …" |
| D-emoji-position | emoji before or after the terminal mark | only one placement | "Hi. 😀" vs "Hi 😀." |
| D-indent-step | any increase | constant step | indents 0, 2, 6 |
| D-list-sep-position | sep as marker or as separator | only one of them | "a !?!? b" vs "!?!? a" |
| D-nbb-after | text after the bullets allowed | not allowed | closing sentence |
| D-options-extra | exactly one option, nothing else | explanation allowed | "Yes, because…" |
| D-template-brackets | brackets optional | brackets required / forbidden | "My Answer: [Yes]" |
| D-template-markup | emphasis around labels allowed | not allowed | "**My Answer:**" |
| D-paren-types | any bracket types | all three types required | "((((( x )))))" |
| D-subbullet-indent | sub-bullets need not be indented | must be indented | "- x" at column 0 |
| D-section | sections = heading-started parts, else paragraphs | whole response is one section without headings | two paragraphs, only the first italic |
| D-titlecase-minor | minor words may be lowercase | every word capitalised | "The Fall of Rome" |
| D-overlap-def | word trigrams, share of response trigrams | reference denominator / Jaccard / char trigrams / multiset | short paraphrase |
| D-balance | counts differ by at most one | exactly equal | 2/2/1 |
| D-ratio-others | exclamatory sentences ignored | they break the ratio | 2 decl, 1 interr, 1 excl |
| D-char-count | all characters of the sentence | letters only | punctuation-only difference |
| D-different-words | no word repeated anywhere | no word shared between sentences | a word repeated within one sentence |
| D-stopword-list | a standard English list (NLTK) | another list | "also" |
| D-repeat-trailing | nothing after the repetition | non-answer text allowed | "Done." after it |
| D-repeat-simple-target | output the instruction sentence itself | output the request | — |
| D-index-base | 0-based | 1-based | "index 3 and 6" |
| D-alliteration | same initial letter | same initial sound | "cat kite" |
| D-syllables | dictionary counts | other counting rules | "fire" |
| D-palindrome-distinct | distinct palindromes | occurrences | "level" x10 |
| D-letter-y | y is a consonant | y is a vowel in some words | "my" |
| D-repeat-count | at most n occurrences | at most n+1 | a word 5 times for n=4 |
| D-vowel-scope | at most three vowel letters across the response | per word | "idea" |
