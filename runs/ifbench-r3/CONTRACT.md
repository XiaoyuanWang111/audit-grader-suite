# IFBench contracts (step 2)

Written from the text the model sees (the 300 prompts of `case/data/train-00000-of-00001.parquet`,
templates extracted by `audit/scripts/dump_templates.py`) before any grader or reference code was
read. Each check is one instruction id. "Text" quotes the instruction as the prompts render it,
with kwargs in braces. "Pass" and "Fail" give the contract under the proposed reading of every
decision entry; the entries are listed at the end with both readings, an example of each, and the
proposed reading. Later changes to this file are marked "Changed <date>: reason".

## G. Rules shared by all checks

- G1 Graded text. The stored `response` field: the text after the last `</think>` of the
  completion, leading whitespace removed. A thinking-on completion that opens `<think>` and never
  closes it is an extraction failure: it fails every check of its prompt and is counted separately
  (the stored `response` of such a completion is the unclosed reasoning and must not be graded).
  Text inside `reasoning_content`-style fields is never graded (none exists in these records).
- G2 Truncated responses (`finish_reason == "length"`) are graded as they stand and counted
  separately.
- G3 Each instruction of a prompt is graded on its own; prompt-level accuracy is the share of
  prompts whose instructions all pass, instruction-level accuracy the share of instructions that
  pass.
- G4 Loose grading, or any other score-level transform, may change which text is graded only by
  removing text that the instruction does not constrain. A pass obtained by deleting or rewriting
  text that the instruction constrains (for example a first line that breaks a "start with" or
  "first word" rule, or a final line that breaks an "end with" rule) contradicts the contract.
- G5 Units. Unless a check says otherwise: a word follows D-word, a sentence D-sentence, a
  paragraph D-paragraph, keyword matching D-match. Markdown markup (`#`, `*`, `**`, `_`, backticks,
  `>`, table pipes, list markers such as `-`, `*`, `1.`) and HTML tags are formatting: they are not
  words and do not create sentences, but they are characters for character-level checks.
- G6 A requirement on units the response does not contain (an empty response, a response with no
  sentence, no quoted phrase, fewer than N words) follows D-vacuous.

## Checks

### count:conjunctions
Text: "Use at least {small_n} different coordinating conjunctions in the response." (small_n 2 to 5;
prompt 8 prints "4.0").
Pass: at least small_n distinct members of {for, and, nor, but, or, yet, so} occur, each in at
least one place where it functions as a coordinating conjunction (joins words, phrases or
clauses of equal rank). Fail: fewer. Case-insensitive. Words such as "however", "because",
"although", "therefore" are not coordinating conjunctions. Decisions: D-conj, D-word.

### count:keywords_multiple
Text: "Include keyword {k1} once in your response, keyword {k2} twice ..., keyword {k3} three times
..., keyword {k4} five times ..., and keyword {k5} seven times in your response."
Pass: k1 occurs exactly 1 time, k2 exactly 2, k3 exactly 3, k4 exactly 5, k5 exactly 7, counting
whole-word, case-insensitive occurrences (D-match). Fail: any count differs. Decisions:
D-keyword-count, D-match.

### count:numbers
Text: "Include exactly {N} numbers in the response." (N 2 to 36)
Pass: the response contains exactly N numbers, counting occurrences (a repeated number counts each
time). A number is a numeral written with digits; a maximal run of digits with internal thousands
commas or a decimal point is one number ("10,000", "3.14"); signs, %, currency symbols and
ordinal suffixes ("21st") do not split or add numbers; list markers ("1.") and years count.
Fail: any other count. Decisions: D-number.

### count:person_names
Text: "Mention at least {N} different person names in the response, from this list of person names:
Emma, Liam, ..., Jonathan ." (50 names; N 3 to 39)
Pass: at least N distinct names of the list occur as capitalized whole words (possessive "Emma's"
counts as Emma). Names outside the list do not count. Fail: fewer. Decisions: D-names-case, D-match.

### count:pronouns
Text: "The response should include at least {N} pronouns." (N 4 to 39)
Pass: the number of pronoun occurrences is at least N. Pronouns: personal (I, me, you, he, him,
she, her, it, we, us, they, them), possessive (my, mine, your, yours, his, her, hers, its, our,
ours, their, theirs), reflexive (myself ... themselves, oneself), and, used as pronouns,
demonstrative (this, that, these, those), relative and interrogative (who, whom, whose, which,
what, that), and indefinite (someone, anybody, everything, nothing, none, each, both, all, ...).
Fail: fewer. A count of personal, possessive and reflexive forms alone that reaches N is a pass
under every reading; a count under the widest reading below N is a fail under every reading.
Decisions: D-pronoun.

### count:punctuation
Text: "Use every standard punctuation mark at least once, including semicolons, colons, and the
interrobang (?!)."
Pass: the response contains each standard English punctuation mark: period, comma, question mark,
exclamation mark, colon, semicolon, apostrophe, quotation mark, hyphen, dash (en or em dash, or
"--"), parentheses, square brackets, braces, ellipsis ("..." or "…"); and an interrobang written
"?!", "!?" or "‽". Fail: any of these missing. Characters that are symbols rather than
punctuation marks (@ # $ % ^ & * _ ~ ` | \ < > = +) are never required. Decisions: D-punct-set.

### count:unique_word_count
Text: "Use at least {N} unique words in the response." (N 36 to 170)
Pass: the number of distinct words (case-insensitive types, D-word) is at least N. Fail: fewer.
Decisions: D-unique, D-word.

### count:word_count_range
Text: "The response must contain between {min_words} and {max_words} words."
Pass: min_words <= word count <= max_words (D-word). Fail otherwise. Decisions: D-between, D-word.

### count:words_japanese
Text: "Every {N}th word of your response must be in Japanese." (N 5, 17, 25, 29)
Pass: the response has at least N words and the words at positions N, 2N, 3N, ... (1-based,
whitespace-delimited, D-word) are Japanese: written in Japanese script (hiragana, katakana, kanji,
with Japanese punctuation allowed) with no Latin letters. Other words may be in any language.
Fail: any such position holds a non-Japanese word, or fewer than N words (D-vacuous).
Decisions: D-japanese, D-vacuous.

### custom:character_reverse (prompt 273)
Text: "What animal is the national symbol of the US? Respond to this query, but make your sentence
in reverse order of what it should be, per letter."
Pass: the response, read backwards character by character, is a sentence answering the query (it
names the bald eagle), and nothing else is in the response. Fail: letters in normal order, only the
word order reversed, letters reversed within each word but the words kept in order, or a different
answer. Decisions: D-char-reverse, D-custom-facts.

### custom:csv_city (prompt 274)
Text: "Generate CSV data: The column names are ["ID", "Country", "City", "Year", "Count"], the
data should be comma delimited. Please generate 7 rows."
Pass: the CSV has the header ID,Country,City,Year,Count (fields may be quoted) followed by exactly
7 data rows, every row comma-delimited with 5 fields. Fail: other row count, other delimiter, wrong
or missing header, rows with another field count. Decisions: D-csv.

### custom:csv_quotes (prompt 275)
Text: "... column names are ["StudentID", "Subject", "Grade", "Semester", "Score"], the data should
be tab delimited. Please generate 3 rows and enclose each single field in double quotes."
Pass: header plus exactly 3 data rows, fields separated by tab characters, 5 fields per row, every
field enclosed in double quotes. Fail: other delimiter (spaces instead of tabs), an unquoted field,
other row count. Decisions: D-csv.

### custom:csv_special_character (prompt 276)
Text: "... ["ProductID", "Category", "Brand", "Price", "Stock"], the data should be comma delimited.
Please generate 14 rows. Add one field which contains a special character and enclose it in double
quotes."
Pass: header plus exactly 14 data rows, comma-delimited, 5 fields per row (a quoted field may
contain a comma); exactly one field contains a special character (a character other than letters,
digits and spaces, such as & @ # , ') and that field is enclosed in double quotes. Fail: no such
field, the special-character field unquoted, other row count. Decisions: D-csv.

### custom:date_format_list (prompt 277)
Text: "List the start dates of all the battles Napoleon fought separated by commas, use the
following date format: YYYY-MM-DD. Do not provide an explanation."
Pass: the response consists only of valid calendar dates written YYYY-MM-DD, separated by commas
(spaces after commas allowed), at least two dates. Fail: any other date format, other separators,
any explanation or other text. Decisions: D-custom-facts, D-custom-extra-text.

### custom:european_capitals_sort (prompt 278)
Text: "Give me the names of all capital cities of european countries whose latitude is higher than
than 45 degrees? List the capital cities without country names, separated by commas, sorted by
latitude, from highest to lowest."
Pass: the response is only a comma-separated list of capital-city names, without country names,
containing the capitals of European countries north of 45 degrees N (Reykjavik ... Zagreb), each
once, in descending order of latitude. Fail: country names, other separators, a missing or extra
capital, wrong order. Decisions: D-custom-facts, D-custom-extra-text.

### custom:mcq_count_length (prompt 279)
Text: "Generate 4 multiple choice questions with 5 options each about "20th century art history".
Each question should start with the label "Question". The questions should get progressively
longer. Do not provide an explanation."
Pass: exactly 4 questions; each starts with the label "Question" (for example "Question 1:");
each has exactly 5 options; each question is longer than the one before; no explanation. Fail:
otherwise. Decisions: D-mcq.

### custom:multiples (prompt 280)
Text: "Count from 10 to 50 but only print multiples of 7."
Pass: the numbers printed are 14, 21, 28, 35, 42, 49, each once, in this order, and no other
number appears. Fail: a missing, extra or out-of-order number. Decisions: D-custom-extra-text.

### custom:reverse_newline (prompt 281)
Text: "List the countries of Africa in reverse alphabetical order, each on a new line."
Pass: every non-empty line holds one African country (list numbering allowed), the lines are in
reverse alphabetical order, and the list covers the 54 sovereign African states (common name
variants accepted). Fail: two countries on a line, wrong order, missing or non-African entries.
Decisions: D-custom-facts, D-custom-extra-text.

### custom:sentence_alphabet (prompt 282)
Text: "Tell me a 26-sentence story where each sentence's first word starts with the letters of the
alphabet in order."
Pass: the story has exactly 26 sentences and the first word of sentence i starts with the i-th
letter of A to Z (case-insensitive). Fail: other sentence count, any letter out of place.
Decisions: D-sentence.

### custom:word_reverse (prompt 283)
Text: "What animal is the national symbol of the US? Respond to this query, but make your sentence
in reverse order of what it should be, per word."
Pass: the response is one sentence whose words, read from last to first, form a sentence that
answers the query (names the bald eagle); each word is spelled normally. Fail: normal word order,
letters reversed, a different answer. Decisions: D-custom-facts.

### format:emoji
Text: "Please use an emoji at the end of every sentence."
Pass: the response has at least one sentence and every sentence (D-sentence) ends with an emoji: a
Unicode emoji character or sequence is the sentence's last visible character, or stands directly
before its terminal punctuation. Text emoticons such as ":)" are not emoji. Fail: any sentence
without one. Decisions: D-sentence, D-emoji-position, D-vacuous.

### format:line_indent
Text: "Create stairs by incrementally indenting each new line."
Pass: at least two non-empty lines, and each non-empty line starts with more leading whitespace
than the non-empty line before it. Blank lines are ignored. Fail: any line indented the same as or
less than the line before. Decisions: D-indent, D-vacuous.

### format:list
Text: "Answer with a list of items, instead of bullet points use {sep}." (sep "!?!?", "SEPARATOR",
"-")
Pass: the answer is a list of at least two items marked with sep, either at the start of each item
in place of a bullet or between consecutive items, and no item is marked with another bullet
symbol (*, •, or "-" when sep is not "-"). Fail: no list, another marker, a single item.
Decisions: D-list.

### format:newline
Text: "Write each word on a new line."
Pass: every line that contains a word contains exactly one word (D-word); lines without words
(blank, punctuation only) are allowed. Fail: any line with two or more words. Decisions: D-word,
D-vacuous.

### format:no_bullets_bullets
Text: "Your answer must contain at least two sentences ending in a period followed by at least two
bullet points denoted by *."
Pass: before the first `*` bullet there are at least two sentences ending in a period, and after
them at least two bullet points whose lines start with `*` followed by a space. Fail: fewer
sentences before the bullets, fewer than two `*` bullets, or bullets only marked with other
symbols. Decisions: D-sentence.

### format:no_whitespace
Text: "The output should not contain any whitespace."
Pass: the graded text is non-empty and contains no whitespace character (space, tab, newline,
no-break space, other Unicode White_Space characters), including at its end. Fail: any whitespace.
Decisions: D-trailing-ws, D-vacuous.

### format:options
Text: "Answer with one of the following options: {options}." with options "yes/no/maybe",
"I know or I don't know", "a), b), c), d)". Prompts 101 to 105 also say "Do not give any
explanation."; prompt 100 does not.
Pass: after removing surrounding whitespace, markdown emphasis and a final period, and collapsing
internal whitespace (including line breaks) to single spaces, the response is exactly one option,
case-insensitive: "yes", "no", "maybe"; "I know", "I don't know"; "a)", "b)", "c)", "d)", the last
optionally followed by that option's text from the prompt. Fail: two options, no option, an
option with explanation. Decisions: D-options.

### format:output_template
Text: "Use this exact template for your response: My Answer: [answer] My Conclusion: [conclusion]
Future Outlook: [outlook]"
Pass: the response starts with "My Answer:" and contains "My Conclusion:" and "Future Outlook:"
exactly once each, in that order, each followed by non-empty content that replaces the bracketed
placeholder; line breaks between the parts and markdown emphasis around a label are allowed.
Fail: text before "My Answer:", a missing, renamed or repeated label, a label with no content, a
placeholder left in brackets. Decisions: D-template.

### format:parentheses
Text: "Nest parentheses (and [brackets {and braces}]) at least 5 levels deep."
Pass: somewhere in the response at least 5 brackets of the kinds (), [], {} are open at once, and
those brackets are properly closed in reverse order (each closer matches the most recent opener).
Kinds may be mixed. Fail: maximum properly nested depth below 5. Decisions: D-paren.

### format:quote_unquote
Text: "Every quoted phrase must be followed by an unquoted explanation."
Pass: the response has at least one quoted phrase (text between a matching pair of double quotes,
straight or curly, or single quotes used as quotation marks, not apostrophes), and every quoted
phrase is followed by unquoted text that explains it before the next quoted phrase or the end.
Fail: a quoted phrase at the end, a quoted phrase directly followed by another quoted phrase, or no
quoted phrase. Decisions: D-vacuous.

### format:quotes
Text: "Include quotes within quotes within quotes, at least 3 levels deep, alternating between
double quotes and single quotes."
Pass: the response contains a quotation nested at least three levels deep whose levels alternate
between double and single quotation marks (" ' " or ' " '), straight or curly, each level closed
inside the one around it. Apostrophes inside words are not quotation marks. Fail: depth below 3
or two adjacent levels of the same kind.

### format:sub-bullets
Text: "Your response must include bullet points denoted by * and at least one sub-bullet point
denoted by - for each bullet point."
Pass: at least one bullet point whose line starts (after optional indentation) with `*` and a
space, and every such bullet has at least one sub-bullet: a line starting with `-` and a space,
placed after it and before the next `*` bullet, indented deeper than the bullet. Fail: a `*`
bullet without a `-` sub-bullet, no `*` bullets. Decisions: D-subbullet.

### format:thesis
Text: "Each section must begin with a thesis statement in italics, use HTML to indicate the
italics."
Pass: every section starts with a statement wrapped in an HTML italic element (`<i>...</i>` or
`<em>...</em>`); a section's heading line does not count as its start, so the first content after
the heading must be the italic thesis. Markdown italics (`*text*`, `_text_`) do not count. Fail:
any section that does not begin so. Decisions: D-section.

### format:title_case
Text: "Write the entire response in title case (capitalize the first letter of every major word)."
Pass: every major word starts with an uppercase letter; minor words (articles, coordinating
conjunctions, prepositions of four letters or fewer, the infinitive "to") may be lower case except
as the first word of a line or sentence; capitalizing a minor word is allowed. Words that start
with a digit or symbol are ignored. Fail: any major word starting with a lowercase letter.
Decisions: D-title.

### ratio:overlap
Text: "Maintain a trigram overlap of {percentage}% (±2%) with the provided reference text."
(percentage 6 to 93). The reference text is the request text of the prompt (kwarg
`reference_text`, the prompt without the instruction sentences).
Pass: the overlap is within 2 percentage points of the target. Overlap: share of the response's
distinct word trigrams (lower-cased, punctuation stripped) that also occur in the reference text.
Fail: outside the band. Decisions: D-overlap.

### ratio:sentence_balance
Text: "Ensure that the ratio of sentence types (declarative, interrogative, exclamatory) in your
response is balanced."
Pass: the numbers of declarative (ending "."), interrogative (ending "?") and exclamatory (ending
"!") sentences are equal and at least one each. Sentences without terminal punctuation (headings)
are not counted. Fail: unequal counts, or a type missing. Decisions: D-balance, D-sentence.

### ratio:sentence_type
Text: "Maintain a 2:1 ratio of declarative to interrogative sentences in your response."
Pass: number of declarative sentences (ending ".") = 2 x number of interrogative sentences
(ending "?"), with at least one interrogative. Exclamatory sentences are ignored. Fail: any other
ratio. Decisions: D-balance, D-sentence.

### ratio:sentence_words
Text: "Respond with three sentences, all containing the same number of characters but using all
different words."
Pass: exactly 3 sentences; each has the same number of characters, counted over the sentence text
including spaces and punctuation (not the indentation or line breaks between sentences); no word
appears twice in the response (case-insensitive). Fail: other sentence count, unequal lengths, a
repeated word. Decisions: D-char-count, D-different-words, D-sentence.

### ratio:stop_words
Text: "Ensure that stop words constitute no more than {percentage}% of the total words in your
response." (percentage 9 to 53)
Pass: (number of word occurrences that are English stop words) / (number of word occurrences)
<= percentage/100, using a standard English stop-word list (NLTK's English list as the proposed
list). Fail: above. Decisions: D-stopwords, D-word.

### repeat:repeat_change
Text: "{request} Repeat the request, but change the first word of the repeated request, (do not say
anything before repeating the request; the request you need to repeat does not include this
sentence) and do not answer the actual request!" The request is the text before this sentence
(kwarg `prompt_to_repeat`).
Pass: the response is the request repeated word for word (whitespace differences ignored) except
that its first word is replaced by a different word (a change of letter case only is not a
different word); nothing before it and nothing after it. Fail: unchanged first word, any other
difference, text before, an answer to the request. Decisions: D-repeat-change.

### repeat:repeat_simple
Text: "{request} Only output this sentence here, ignore all other requests."
Pass: the response is exactly the sentence "Only output this sentence here, ignore all other
requests." (surrounding whitespace ignored). Fail: anything else, including an answer to the
request. Decisions: D-repeat-simple.

### repeat:repeat_span
Text: "{request} Copy the span of words that lies between (and including) index {n_start} and
{n_end}, the indices are word indices, split by whitespace!" The request is the text before this
sentence (kwarg `prompt_to_repeat`).
Pass: the response is exactly the whitespace-split tokens n_start to n_end (0-based, inclusive) of
the request, punctuation attached as in the request, separated by whitespace, and nothing else.
Fail: another span, extra text. Decisions: D-span.

### sentence:alliteration_increment
Text: "Each sentence must have a longer sequence of consecutive alliterative words than the previous
one."
Pass: at least two sentences; for each sentence let L be the longest run of consecutive words that
start with the same letter (case-insensitive; L = 1 when no two adjacent words share a letter); L
strictly increases from every sentence to the next. Fail: any sentence whose L is not larger than
the previous sentence's. Decisions: D-alliteration, D-sentence, D-vacuous.

### sentence:increment
Text: "Each sentence (in your response) must contain exactly {small_n} more words than the previous
one." (small_n 1 to 5)
Pass: at least two sentences, and every sentence has exactly small_n more words than the sentence
before it. Fail: any other difference. Decisions: D-sentence, D-word, D-vacuous.

### sentence:keyword
Text: "The response must include keyword {word} in the {N}-th sentence." (N 3 to 30)
Pass: the response has at least N sentences and the N-th (1-based) contains the keyword (D-match).
The keyword may also occur elsewhere. Fail: otherwise. Decisions: D-sentence, D-match.

### words:alphabet
Text: "Each word in your response must start with the next letter of the alphabet, looping back to
'A' after 'Z'."
Pass: at least two words, and the first letter of every word after the first is the alphabet
successor of the previous word's first letter (Z is followed by A), case-insensitive. The first
word may start with any letter. Fail: any break in the sequence, a word that does not start with a
letter. Decisions: D-alphabet-start, D-word, D-word-numbers.

### words:consonants
Text: "Ensure each word in your response has at least one consonant cluster (two or more consonants
together)."
Pass: every word contains two adjacent consonant letters; consonants are the letters other than a,
e, i, o, u (y counts as a consonant). Fail: any word without two adjacent consonants (for example
"a", "I", "is", "to", "the", "idea"). Decisions: D-y, D-word, D-word-numbers.

### words:keywords_specific_position
Text: "Include keyword {keyword} in the {n}-th sentence, as the {m}-th word of that sentence."
(n 22 to 25, m 33 to 36)
Pass: the n-th sentence (1-based) exists and its m-th word (1-based, punctuation stripped,
case-insensitive) is the keyword. Fail: otherwise. Decisions: D-sentence, D-word.

### words:last_first
Text: "In your response(,) the last word of each sentence must become the first word of the next
sentence."
Pass: at least two sentences, and for every pair of consecutive sentences the last word of the
first equals the first word of the second (case-insensitive, punctuation stripped). Fail: any pair
that differs. Decisions: D-sentence, D-vacuous.

### words:no_consecutive
Text: "No two consecutive words can share the same first letter."
Pass: no two adjacent words start with the same letter (case-insensitive). A token without a
letter (a number) shares no letter with its neighbours. Fail: any adjacent pair with the same first
letter, across sentence and line boundaries too. Decisions: D-word, D-vacuous.

### words:odd_even_syllables
Text: "Alternate between words with odd and even numbers of syllables."
Pass: at least two words, and the syllable counts of every two adjacent words differ in parity,
syllables counted by standard dictionary pronunciation. Fail: two adjacent words with the same
parity. Decisions: D-syllables, D-word, D-vacuous.

### words:palindrome
Text: "Include at least 10 single-word palindromes, each at least 5 characters long."
Pass: at least 10 distinct words (case-insensitive, punctuation stripped) of at least 5 letters
that read the same backwards, each a real word or name (level, radar, civic, kayak, refer, madam,
rotor, racecar, ...). Fail: fewer. Decisions: D-palindrome.

### words:paragraph_last_first
Text: "Each paragraph of your response must end with the same word it started with, separate
paragraphs with a newline."
Pass: paragraphs are the non-empty lines; in every paragraph the first word equals the last word
(case-insensitive, punctuation stripped). Fail: any paragraph whose first and last words differ.
Decisions: D-paragraph, D-vacuous.

### words:prime_lengths
Text: "Use only words with lengths that are prime numbers."
Pass: every word's length is prime (2, 3, 5, 7, 11, 13, ...), length = number of letters and
digits in the word (apostrophes, hyphens and surrounding punctuation not counted). Fail: any word
of length 1, 4, 6, 8, 9, 10, 12, ... Decisions: D-prime-length, D-word, D-word-numbers.

### words:repeats
Text: "The response should not repeat any word more than {small_n} times." (small_n 2 to 5)
Pass: no word (case-insensitive) occurs more than small_n times. Fail: some word occurs more than
small_n times. Decisions: D-repeat-count, D-word, D-vacuous.

### words:start_verb
Text: "The response must start with a verb."
Pass: the first word of the response (after markup) is a verb form used as a verb: imperative,
finite verb, auxiliary or modal, or an -ing or -ed form heading a verb phrase. Fail: a noun,
adjective, article, pronoun or other first word, including a title line that starts with a noun.
Decisions: D-verb.

### words:vowel
Text: "Write a paragraph using words that contain only three types of vowels."
Pass: the response is a single paragraph, and its words together use at most three distinct vowel
letters out of a, e, i, o, u (y is not counted as a vowel). Fail: four or five vowel letters used,
or more than one paragraph. Decisions: D-vowel, D-paragraph.

### words:words_position
Text: "The second word in your response and the second to last word in your response should be the
word {keyword}."
Pass: the second word and the second-to-last word (D-word, punctuation stripped, case-insensitive)
are both the keyword. Fail: otherwise.

## Decision entries

Each entry: the readings, an example that separates them, the proposed reading (the one the
contracts above use). The maintainers of the evaluation decide.

Changed 2026-11-09 22:43 UTC (version 2), after the grader code had been read; no proposed
reading changed:

- D-paragraph gains reading C (every line break starts a paragraph). Reason: version 1 used
  that reading only for `words:paragraph_last_first`; in plain text a single line break is
  also commonly read as a paragraph break elsewhere, so a careful reader could defend it for
  `words:vowel` ("Write a paragraph").
- D-options gains reading D (only the bare option string counts). Reason: for the a)-d)
  prompts, which add "Do not give any explanation", a careful reader could defend that
  repeating the option's text after the label is more than the option; version 1 listed only
  more lenient alternatives.

| Id | Checks | Reading A (proposed) | Reading B (and C) | Example that separates them |
|---|---|---|---|---|
| D-vacuous | every universal or negative check | A requirement on units the response lacks fails: an empty response fails every check; "every sentence/quoted phrase/paragraph", alternation and increment checks need at least one (or two) units; "every Nth word" needs at least N words. | The requirement holds vacuously: an empty response passes negative checks ("no whitespace", "no word more than 3 times"), and a response without the units passes universal checks. | Empty response, `format:no_whitespace`: A fail, B pass. A response with no quotation marks, `format:quote_unquote`: A fail, B pass. |
| D-word | all word-based checks | A word is a whitespace-delimited token with leading and trailing punctuation removed that contains a letter or digit; contractions and hyphenated compounds are one word; standalone punctuation and markup are not words. | B: hyphenated and slash-joined compounds count as several words. C: every whitespace-delimited token is a word, standalone dashes and symbols included (word-processor count). | "A well-known fact — true." A: 4 words; B: 5; C: 5. |
| D-word-numbers | letter-based word checks (alphabet, consonants, prime lengths, no_consecutive, vowel, syllables) | Digit-only tokens are words and are tested like any word (so "2024" breaks a consonant-cluster or alphabet rule). | Digit-only tokens are not words for letter-based rules and are skipped. | "Strong 2024 trends" under `words:consonants`: A fail, B pass. |
| D-sentence | all sentence-based checks | A sentence ends at ".", "!", "?", "…" (or a run of them, with closing quotes or brackets) followed by whitespace or the end, and at a line break; abbreviations and decimals do not end sentences; markdown headings and label lines (a line that is only a heading, only bold text, or ends with ":") are not sentences. | B: only terminal punctuation ends a sentence; a line break without punctuation does not, so a heading joins the next sentence. C: every non-empty line fragment is a sentence, headings and labels included. | "# Title\nFirst one. Second one." A: 2 sentences; B: 2 ("Title First one." and "Second one."); C: 3. |
| D-paragraph | words:paragraph_last_first, words:vowel | For `paragraph_last_first`, whose text says "separate paragraphs with a newline", every non-empty line is a paragraph; elsewhere paragraphs are blocks separated by blank lines. | B: paragraphs are always blank-line blocks. C: every line break starts a new paragraph, in every check (changed 2026-11-09, v2). | "Cats are cats\nDogs like dogs" A: 2 paragraphs, both pass; B: 1 paragraph, "Cats ... dogs" fails. |
| D-match | keyword checks, person names | Whole word, case-insensitive, possessive "'s" allowed, other inflections and longer words do not match. | B: substring match ("door" inside "doorway"). C: inflected forms match ("clouds" for "cloud"). | Keyword "river", text "riverbank rivers": A 0 occurrences; B 2; C 1. |
| D-keyword-count | count:keywords_multiple | "once / twice / three times" means exactly that many. | At least that many. | k1 used twice: A fail, B pass. |
| D-conj | count:conjunctions | A word counts only where it functions as a coordinating conjunction. | Every occurrence of for, and, nor, but, or, yet, so counts. | "and", "but", "or", "so" as conjunctions plus "for example", small_n 5: A fail (4), B pass (5). |
| D-number | count:numbers | Numerals in digits, each maximal digit group (with internal "," or ".") once per occurrence; list markers and years count. | B: list markers do not count. C: spelled-out cardinal numbers also count. | "1. Two cats, 3 dogs" with N 2: A pass (1, 3); B fail (3 only); C fail (1, two, 3). |
| D-names-case | count:person_names | The name must appear capitalized. | Case-insensitive ("grace", "mason" as common nouns count). | "with grace", "Grace said": A counts only the second. |
| D-pronoun | count:pronouns | All pronoun classes (personal, possessive incl. determiners, reflexive, demonstrative, relative, interrogative, indefinite) when used as pronouns. | B: personal, possessive and reflexive forms only. C: B without possessive determiners (my, your, ...). | "This is what everyone wants for their kids" counts 4 under A (this, what, everyone, their), 1 under B, 0 under C. |
| D-punct-set | count:punctuation | The 14 marks listed in the contract plus the interrobang. | B: the core marks only (. , ? ! ; : ' " - ( )) plus the interrobang; brackets, braces, dashes and ellipsis optional. | A response with all core marks and "?!" but no braces: A fail, B pass. |
| D-unique | count:unique_word_count | Distinct word types, case-insensitive. | B: case-sensitive types. C: words that occur exactly once. | "The cat saw the cat": A 3, B 4, C 1. |
| D-between | count:word_count_range | Inclusive bounds. | Exclusive bounds. | 71 words for "between 71 and 73": A pass, B fail. |
| D-japanese | count:words_japanese | Words are whitespace-delimited; a Japanese word is a token in Japanese script with no Latin letters. | B: Japanese text is segmented into linguistic words even without spaces. C: romanized Japanese ("sakura") counts as Japanese. | A fully Japanese reply with no spaces: A has 1 word (fewer than N, fail); B may pass. |
| D-emoji-position | format:emoji | The emoji may stand after or directly before the terminal punctuation. | Only after the punctuation (the emoji is the last character of the sentence). | "This is fun 🎉." A pass, B fail. |
| D-indent | format:line_indent | Strictly increasing leading whitespace over non-empty lines; blank lines ignored. | B: indentation must also grow by a constant step. C: blank lines count as lines and break the stairs. | Indents 0, 2, 3, 7: A pass, B fail. |
| D-list | format:list | The separator marks at least two items, at the start of each item or between items; a short lead-in line is allowed. | B: only at the start of each item (bullet position). C: only between items. D: no text other than the list. | "Here are the items:\n!?!? one\n!?!? two": A pass, B pass, C fail, D fail. |
| D-options | format:options | The whole response is one option (whitespace, emphasis and a final period aside; for a), b), c), d) the option text may follow the label). | B: the response starts with one option and may explain it (where the prompt does not forbid explanation). C: for the a)-d) options a bare letter ("d") also counts. D: only the bare option string counts; for a)-d) the option text after the label is extra text (changed 2026-11-09, v2). | Prompt 100, "Maybe. It depends on ...": A fail, B pass. |
| D-template | format:output_template | Markdown emphasis on labels and line breaks are allowed; nothing before "My Answer:". | B: the template text must match character for character apart from the placeholders (no emphasis). C: a title or lead-in before the template is allowed. | "**My Answer:** ..." A pass, B fail. |
| D-paren | format:parentheses | Any mix of (), [], {} counts toward depth; brackets must be properly matched. | B: depth counts only round parentheses. C: unmatched opening brackets count (depth = maximum count of open brackets). | "( [ { ( [ x ] ) } ] )": A depth 5, B depth 2. |
| D-subbullet | format:sub-bullets | A sub-bullet must be indented deeper than its bullet. | Any "- " line after a bullet counts as its sub-bullet, indented or not. | "* a\n- b": A fail, B pass. |
| D-section | format:thesis | Sections are heading-delimited blocks; without headings, each blank-line paragraph is a section. | B: without headings the whole response is one section, so only its start needs a thesis. | Three paragraphs without headings, only the first begins with `<i>`: A fail, B pass. |
| D-title | format:title_case | Minor words (articles, coordinating conjunctions, prepositions of up to four letters) may be lower case except first in a line or sentence. | B: every word must be capitalized. C: minor words must be lower case. | "The Rise of Rome": A pass, B fail; "The Rise Of Rome": A pass, C fail. |
| D-overlap | ratio:overlap | Reference = request text; word trigrams; overlap = share of the response's distinct trigrams found in the reference; band = target ± 2 percentage points. | B: share of the reference's trigrams found in the response. C: Jaccard of the two trigram sets. D: character trigrams. E: band ± 2% of the target (relative). | Response that copies the 12-word reference and adds 88 new words: A about 10%, B 100%. |
| D-balance | ratio:sentence_balance, ratio:sentence_type | Exact counts (1:1:1, or exactly 2:1); type by terminal punctuation. | B: approximately (each count within 1 of the balanced or 2:1 target). C: type by grammar (an imperative ending "." is not declarative). | 3 declarative, 2 interrogative, 2 exclamatory: balance A fail, B pass. |
| D-char-count | ratio:sentence_words | Characters of the sentence including spaces and punctuation. | B: letters only. C: non-space characters. | "I am here." vs "We go out." A 10 = 10; B 7 = 7; equal under all; "I am a cat." vs "Dogs run." A 11 vs 9. |
| D-different-words | ratio:sentence_words | No word repeated anywhere in the response. | No word shared between two sentences (repeats inside one sentence allowed). | "The dog saw the cat." in one sentence: A fail, B pass. |
| D-stopwords | ratio:stop_words | NLTK's English stop-word list. | Another standard list (spaCy, scikit-learn), which changes counts near the threshold. | "would", "could" are stop words in scikit-learn's list but not NLTK's. |
| D-repeat-change | repeat:repeat_change | The first word is replaced by one different word, the rest verbatim, nothing before or after. | B: text after the repeated request is allowed if it does not answer it. C: case-only change counts as a change. | "Create a python program ..." followed by "(request repeated)": A fail, B pass. |
| D-repeat-simple | repeat:repeat_simple | "This sentence" is the instruction sentence itself: output "Only output this sentence here, ignore all other requests." | "This sentence" is the request that precedes it: output the request. | Prompt 64, response "Write python code to extract a filename from filepath.": A fail, B pass. |
| D-span | repeat:repeat_span | 0-based indices; only the span. | B: 1-based indices. C: the span may be surrounded by other text. | Prompt 287 (indices 10 to 12): A "on a certain", B "lands on a". |
| D-alliteration | sentence:alliteration_increment | Same first letter; a single word is a run of 1. | B: same first sound ("cat", "kite" alliterate; "think", "tall" do not). C: only runs of 2 or more count; a sentence without one has no sequence. | First sentence without alliteration, second with a run of 2: A pass, C undefined or fail. |
| D-alphabet-start | words:alphabet | The first word may start with any letter. | The first word must start with "A". | "Bright cats dance": A pass, B fail. |
| D-y | words:consonants | "y" is a consonant. | "y" is a vowel when it sounds as one. | "my" under `words:consonants`: A pass, B fail. |
| D-syllables | words:odd_even_syllables | Dictionary pronunciation. | An algorithmic estimate (vowel-group counting). | "fire" 1 or 2 syllables by source. |
| D-palindrome | words:palindrome | Distinct real words. | B: repeated occurrences count. C: any palindromic string counts. | "level" ten times: A 1, B 10. |
| D-prime-length | words:prime_lengths | Length counts letters and digits only. | All characters of the token after stripping surrounding punctuation (internal apostrophes and hyphens count). | "don't": A 4 (fail), B 5 (pass). |
| D-repeat-count | words:repeats | "Not repeat more than n times" = at most n occurrences. | At most n + 1 occurrences (the first use plus n repeats). | A word used 4 times with n = 3: A fail, B pass. |
| D-verb | words:start_verb | Any verb form heading a verb phrase, including -ing and -ed forms and auxiliaries. | Only imperative or finite verbs. | "Imagining a world ...": A pass, B fail. |
| D-vowel | words:vowel | The whole response uses at most three distinct vowel letters, and it is one paragraph. | B: each word has at most three distinct vowels. C: each word has exactly three. D: the paragraph requirement is not part of the check. | "Education is important" uses a, e, i, o, u: A fail; per word ("education" has 5): B fail; "It is a cat" passes A and B. |
| D-custom-facts | custom checks | Content named by the prompt is part of the check: the bald eagle, the capitals north of 45 degrees and their order, the 54 African states; for the Napoleon dates only the format is checked. | B: only the format is checked everywhere. C: the Napoleon dates must also be correct start dates of his battles. | "elgae dlab ehT" vs "noil ehT": A pass and fail, B pass and pass. |
| D-custom-extra-text | custom:multiples, custom:date_format_list, custom:reverse_newline, custom:european_capitals_sort | The date, capitals and countries responses contain only the requested items (list numbering allowed for reverse_newline); the multiples response may contain words but no number other than the multiples. | B: lead-in or closing text is allowed in all four. C: the multiples response contains nothing but the multiples. | "Here are the multiples: 14, 21, 28, 35, 42, 49": A pass, C fail. "Dates: 1796-04-12, 1805-12-02": A fail, B pass. |
| D-csv | custom CSV checks | "N rows" are data rows after the header; the CSV may sit in a code fence after a short lead-in; csv_quotes quotes header fields too; csv_special_character has exactly one quoted special-character field. | B: N rows include the header. C: no text outside the CSV. D: only data fields need quotes. E: at least one special-character field. | Header plus 6 data rows for "7 rows": A fail, B pass. |
| D-char-reverse | custom:character_reverse | The whole sentence is reversed character by character. | Each word's letters are reversed, words kept in order. | "ehT dlab elgae": A fail, B pass. |
| D-mcq | custom:mcq_count_length | Length of the question text (without options) in characters; an answer key is not an explanation. | B: length in words, or of the whole block with options. C: an answer key counts as explanation. | Questions whose stems grow but whose option blocks shrink: A pass, B fail. |
| D-trailing-ws | format:no_whitespace | Whitespace anywhere in the graded text counts, a final newline included. | Whitespace at the very end of the output is ignored. | "Answer\n": A fail, B pass. |
