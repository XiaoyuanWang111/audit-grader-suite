# IFBench contracts (step 2)

Written from the instruction text that the model sees (the dataset `prompt`, with the `kwargs` values substituted), before reading any grader or reference code. Each check states its pass and fail conditions. Where the text allows two verdicts, a decision entry `D-<topic>` gives both readings and the proposed reading; the contract uses the proposal. Decisions are listed at the end.

## 0. Global rules

G1. Graded text. For a configuration with thinking on, the graded text is the completion after the last `</think>`. A completion of a thinking configuration with no `</think>` is an extraction failure: it fails every check, and the report counts these separately. For a configuration with thinking off, the graded text is the whole completion. A separate reasoning field is never graded. Leading and trailing whitespace of the graded text is not part of the answer (D-edge-whitespace), except for `format:no_whitespace` (see there).

G2. Unit of scoring. Each (prompt, instruction) pair gets one verdict (instruction-level). A prompt passes when all its instructions pass (prompt-level). A grader exception is a grading failure, not a model failure, and must not stop the run.

G3. Words (D-word). A word is a whitespace-separated token with leading and trailing punctuation and markup characters removed, that still contains at least one letter or digit. Tokens with no letter or digit (`-`, `*`, `—`, `#`, an emoji alone) are not words. Inner apostrophes and hyphens stay inside the word: `don't`, `well-known` are one word each.

G4. Sentences (D-sentence). A sentence ends at `.`, `!`, `?` (or a run of them, such as `?!` or `...`) followed by whitespace or the end of the text, or at a line break after a line that has text (so a heading or a list item without final punctuation is its own sentence). Abbreviations (`Mr.`, `e.g.`, `U.S.`) and decimal points (`3.14`) do not end a sentence. Empty lines and lines with no word are not sentences.

G5. Matching keywords and words (D-case, D-keyword-form). Comparisons of words with a given keyword are case-insensitive and whole-word: `Whisper` and `whisper,` match `whisper`; `whispers`, `whispered`, `bluebird` do not match `whisper` or `blue`.

G6. Typographic characters (D-typographic). Curly quotation marks and apostrophes (U+2018, U+2019, U+201C, U+201D) count as the straight ones (`'`, `"`) wherever a check involves quotes, apostrophes or word boundaries.

G7. Markup (D-markup). Markdown markup (`**`, `*`, `_`, backticks, a leading `#`) and list labels (`1.`, `-`, `*`, `•` at the start of a line) are not words and not letters of a word. A check about the first or last word ignores them. They do count where the instruction is about them (bullets, lists, indentation).

G8. Presupposed structure (D-vacuous). When an instruction constrains a structure (sentence pairs, quoted phrases, every N-th word, new lines), a response that has none of that structure fails: it does not show the requirement. Affected: `count:words_japanese` (fewer than N words), `format:quote_unquote` (no quoted phrase), `format:line_indent` (one line), `sentence:increment`, `sentence:alliteration_increment`, `words:last_first` (fewer than two sentences), `format:emoji` (no sentence), `format:thesis` (no section).

G9. Loose grading. The task text defines one verdict per response and check. A score-level transform such as "loose" grading (grading edited variants of the response and taking the best) agrees with the contract only when it cannot turn a response that the contract fails into a pass. Any variant that removes a part of the graded text that the check constrains (for example a first line that breaks "start with a verb" or "the second word") contradicts the contract. Loose scores are reported separately from strict scores.

G10. Empty graded text fails every check that asks for content to be present. It can pass only checks that are pure prohibitions under every reading; each such pass is listed in the report.

## 1. count

count:conjunctions. Text: "Use at least {small_n} different coordinating conjunctions in the response." Pass iff the number of distinct words among {and, but, or, nor, for, yet, so} present in the graded text is >= small_n. Fail otherwise. Repeats of one conjunction count once. D-conj-usage: whether a word counts when it is not used as a conjunction (`for` as a preposition, `so` as an adverb). Proposal: count by word form.

count:keywords_multiple. Text: "Include keyword {k1} once in your response, keyword {k2} twice ..., {k3} three times ..., {k4} five times ..., and keyword {k5} seven times in your response." Pass iff the whole-word, case-insensitive counts are exactly 1, 2, 3, 5, 7. Fail if any count differs. D-count-exact: "once", "twice", "five times" as exact counts (proposal) or as minimums.

count:numbers. Text: "Include exactly {N} numbers in the response." Pass iff the graded text contains exactly N numbers. A number is a maximal numeral written in digits, with an optional sign, thousands separators and decimal part: `1,000.5`, `-3`, `2024`, `50%` (one number), `1st` (one), `3-4` (two). D-number-words: spelled-out numbers (`five`) count or not; proposal: not counted. D-number-labels: digits in list labels (`1.`) count; proposal: they count, since they are numbers in the response.

count:person_names. Text: "Mention at least {N} different person names in the response, from this list of person names: Emma, Liam, ... Jonathan ." Pass iff at least N distinct names from the list occur as whole words (a possessive `Emma's` counts). Names outside the list do not count. D-name-case: proposal: case-sensitive match with the listed capitalization (`grace` the noun is not the name `Grace`).

count:pronouns. Text: "The response should include at least {N} pronouns." Pass iff the number of pronoun tokens (occurrences) is >= N. D-pronoun-set: proposal: personal (I, me, you, he, him, she, her, it, we, us, they, them), possessive (my, mine, your, yours, his, hers, its, our, ours, their, theirs), reflexive (myself ... themselves), plus demonstrative, relative, interrogative and indefinite pronouns when used as pronouns (this, that, these, those, who, whom, whose, which, what, someone, anyone, everyone, nothing, something, everything ...). The narrow alternative counts personal, possessive and reflexive forms only.

count:punctuation. Text: "Use every standard punctuation mark at least once, including semicolons, colons, and the interrobang (?!)." Pass iff the graded text contains each standard punctuation mark at least once. D-punct-set: proposal: period, comma, question mark, exclamation mark, semicolon, colon, apostrophe, quotation mark, hyphen or dash, parentheses, and the interrobang written as `?!` or `‽`; brackets, braces, ellipsis, slash and others are not required. Fail if any proposed mark is missing.

count:unique_word_count. Text: "Use at least {N} unique words in the response." Pass iff the number of distinct words (case-insensitive) is >= N. D-unique: distinct word types (proposal) or words that occur exactly once.

count:word_count_range. Text: "The response must contain between {min} and {max} words." Pass iff min <= word count <= max. D-between: inclusive (proposal) or exclusive bounds.

count:words_japanese. Text: "Every {N}th word of your response must be in Japanese." Pass iff the response has at least N words and every word at position k*N (k = 1, 2, ...; 1-based) is written in Japanese script (hiragana, katakana or kanji); other words are unconstrained. Fail if any such word is not Japanese. D-japanese-segmentation: proposal: words are whitespace tokens (G3), so a run of Japanese characters without spaces is one word; the alternative segments Japanese into morphemes.

## 2. custom

custom:character_reverse. Text: "What animal is the national symbol of the US? Respond to this query, but make your sentence in reverse order of what it should be, per letter." Pass iff the graded text, reversed character by character, is a sentence that answers the query (names the bald eagle). Example pass: `.elgae dlab ehT`. Fail: the forward sentence `The bald eagle.`; word-order reversal `eagle bald The`. D-reverse-content: whether the answer must be correct; proposal: it must name the eagle, since the instruction asks to respond to the query.

custom:word_reverse. Same query, "per word". Pass iff the words of the graded text, read in reverse order, form a sentence that answers the query. Example pass: `eagle. bald the is US the of symbol national The`. Fail: the forward sentence; a letter-reversed sentence. D-reverse-punct: proposal: the position of the final punctuation is free.

custom:csv_city. Text: "Generate CSV data: The column names are ["ID", "Country", "City", "Year", "Count"], the data should be comma delimited. Please generate 7 rows." Pass iff the CSV payload parses as comma-delimited records whose first record is exactly the five column names, followed by exactly 7 data records of 5 fields each. D-csv-rows: 7 data rows plus header (proposal) or 7 lines including header. D-csv-wrapper: proposal: the payload is the fenced code block if there is one, else the whole graded text; prose outside a fence is allowed.

custom:csv_quotes. Text: "... column names are ["StudentID", "Subject", "Grade", "Semester", "Score"], the data should be tab delimited. Please generate 3 rows and enclose each single field in double quotes." Pass iff tab-delimited, header plus exactly 3 data records of 5 fields, and every field, header fields included (D-csv-header-quotes, proposal), is enclosed in double quotes. Fail if any field is unquoted or comma-delimited.

custom:csv_special_character. Text: "... ["ProductID", "Category", "Brand", "Price", "Stock"], the data should be comma delimited. Please generate 14 rows. Add one field which contains a special character and enclose it in double quotes." Pass iff comma-delimited, header plus exactly 14 data records of 5 fields, and at least one field contains a special character (not a letter, digit or space) and is enclosed in double quotes. D-csv-special: "one field" = at least one (proposal) or exactly one; inside an existing column (proposal) or as a sixth column.

custom:date_format_list. Text: "List the start dates of all the battles Napoleon fought separated by commas, use the following date format: YYYY-MM-DD. Do not provide an explanation." Pass iff the graded text is a comma-separated list (spaces after commas allowed) of at least two items, each a valid date in `YYYY-MM-DD`, with no other text. D-content: proposal: format only; historical accuracy is not checked mechanically.

custom:european_capitals_sort. Text: "Give me the names of all capital cities of european countries whose latitude is higher than than 45 degrees? List the capital cities without country names, separated by commas, sorted by latitude, from highest to lowest." Pass iff the graded text is a comma-separated list of capital names only, every name is a capital of a European country north of 45 degrees N, the list is in descending latitude order, and it contains all of them. D-europe-set: whether transcontinental states (Russia: Moscow; Kazakhstan: Astana) and non-sovereign capitals count; proposal: sovereign states usually counted as European, Moscow included, Astana excluded; completeness required.

custom:mcq_count_length. Text: "Generate 4 multiple choice questions with 5 options each about "20th century art history". Each question should start with the label "Question". The questions should get progressively longer. Do not provide an explanation." Pass iff exactly 4 questions, each starting with `Question`, each with exactly 5 options, each question longer than the previous one, and no explanation. D-mcq-length: proposal: length of the question text (stem) in characters, strictly increasing; alternative: including options, or in words.

custom:multiples. Text: "Count from 10 to 50 but only print multiples of 7." Pass iff the numbers printed are exactly 14, 21, 28, 35, 42, 49 in that order. Fail on any missing, extra or out-of-order number (7 and 56 are outside the range). D-multiples-extra: proposal: separators and non-numeric words are allowed.

custom:reverse_newline. Text: "List the countries of Africa in reverse alphabetical order, each on a new line." Pass iff the list lines each hold one African country, the lines are in reverse alphabetical order, and all 54 sovereign African states appear. D-africa-list: proposal: an intro line is allowed; completeness is required.

custom:sentence_alphabet. Text: "Tell me a 26-sentence story where each sentence's first word starts with the letters of the alphabet in order." Pass iff the story has exactly 26 sentences and the first word of sentence i starts with the i-th letter, A to Z, case-insensitive. D-title: proposal: a title line before the story is not one of the 26 sentences.

## 3. format

format:emoji. Text: "Please use an emoji at the end of every sentence." Pass iff every sentence ends with an emoji. An emoji directly before or directly after the sentence's final punctuation ends that sentence (`Hello. 😀`, `Hello 😀.`). Fail if any sentence ends without an emoji.

format:line_indent. Text: "Create stairs by incrementally indenting each new line." Pass iff the response has at least two non-empty lines and each non-empty line has strictly more leading whitespace than the previous non-empty line. D-indent-blank: proposal: empty lines are ignored. D-indent-step: strictly increasing (proposal) or by a constant step.

format:list. Text: "Answer with a list of items, instead of bullet points use {sep}." Pass iff the response is a list of at least two items, each item line starts with sep, and no other bullet marker (`*`, `-`, `•`, unless sep is that marker) is used. D-list-inline: proposal: sep at the start of each item line; the alternative accepts items separated by sep inline.

format:newline. Text: "Write each word on a new line." Pass iff every non-empty line holds exactly one word (G3). Lines with no word (punctuation, markup) are ignored. Fail if any line holds two or more words.

format:no_bullets_bullets. Text: "Your answer must contain at least two sentences ending in a period followed by at least two bullet points denoted by *." Pass iff at least two sentences ending in `.` come before the first bullet, and at least two bullet lines starting with `*` follow. D-nbb-after: proposal: text after the bullets is allowed.

format:no_whitespace. Text: "The output should not contain any whitespace." Pass iff the graded text contains no whitespace character (Unicode whitespace: space, tab, newline, no-break space ...). D-nows-trailing: proposal: a single trailing newline at the end of the completion is a serialization artifact and is ignored; every other whitespace fails. Empty graded text passes under every reading (a content-free pass, listed).

format:options. Text: "Answer with one of the following options: {options}." (yes/no/maybe; I know or I don't know; a), b), c), d)); some prompts add "Do not give any explanation." Pass iff the graded text, after removing surrounding whitespace, markup and a final period, and collapsing internal whitespace, is exactly one of the options, case-insensitive. Fail if it adds an explanation, names two options, or uses another answer. D-options-label: for letter options, proposal: the label alone (`b)` or `b`) passes; the label followed by that option's text from the prompt also passes.

format:output_template. Text: "Use this exact template for your response: My Answer: [answer] My Conclusion: [conclusion] Future Outlook: [outlook]". Pass iff the graded text starts with `My Answer:`, contains `My Conclusion:` and then `Future Outlook:`, each label exactly once and in that order, each followed by non-empty content that is not the bracket placeholder, and nothing outside the template. D-template-markup: proposal: line breaks between sections and bold markup around labels are allowed; label words must match case-sensitively.

format:parentheses. Text: "Nest parentheses (and [brackets {and braces}]) at least 5 levels deep." Pass iff some point in the graded text lies inside at least 5 properly matched, nested bracket pairs, counting `()`, `[]`, `{}` together. D-paren-types: proposal: any mix of the three types counts.

format:quote_unquote. Text: "Every quoted phrase must be followed by an unquoted explanation." Pass iff the response has at least one quoted phrase (G8) and every double-quoted phrase is followed, before the next quoted phrase and within the same paragraph, by at least one unquoted word. D-qu-single: proposal: single-quoted phrases count too when the quote is not an apostrophe.

format:quotes. Text: "Include quotes within quotes within quotes, at least 3 levels deep, alternating between double quotes and single quotes." Pass iff there is a quotation nested at least three levels deep with alternating marks (`"... '... "..." ...' ..."` or `'... "... '...' ..." ...'`). Apostrophes in contractions and possessives are not quote marks.

format:sub-bullets. Text: "Your response must include bullet points denoted by * and at least one sub-bullet point denoted by - for each bullet point." Pass iff there is at least one bullet line starting with `* ` (after indentation), and every such bullet is followed, before the next `*` bullet, by at least one line starting with `- ` (after indentation). Lines starting with `**` (bold) are not bullets. D-subbullet-indent: proposal: the `-` line need not be indented.

format:thesis. Text: "Each section must begin with a thesis statement in italics, use HTML to indicate the italics." Pass iff the response has at least one section and each section starts (after an optional heading line) with a sentence wrapped in `<i>...</i>` or `<em>...</em>`. Markdown italics do not count. D-section: proposal: sections are blocks separated by blank lines or started by a heading.

format:title_case. Text: "Write the entire response in title case (capitalize the first letter of every major word)." Pass iff every major word starts with an uppercase letter. Minor words (a, an, the, and, but, or, nor, for, so, yet, as, at, by, in, of, off, on, per, to, up, via) may be lowercase unless first in a line. Words that start with a digit or symbol are ignored. D-title-minor: proposal as listed; the alternative requires every word capitalized.

## 4. ratio

ratio:overlap. Text: "Maintain a trigram overlap of {P}% (±2%) with the provided reference text." Pass iff the trigram overlap is within [P-2, P+2] percent. D-overlap-def: proposal: word trigrams (lowercase, punctuation removed), overlap = share of the response's trigrams that occur in the reference; alternatives: share of the reference's trigrams in the response, or Jaccard. The reference text is the `reference_text` kwarg, which is the user query part of the prompt.

ratio:sentence_balance. Text: "Ensure that the ratio of sentence types (declarative, interrogative, exclamatory) in your response is balanced." Classify sentences by final punctuation: `.` declarative, `?` interrogative, `!` exclamatory. Pass iff all three types occur and their counts are equal. D-balance: equal counts (proposal) or nearly equal (max - min <= 1).

ratio:sentence_type. Text: "Maintain a 2:1 ratio of declarative to interrogative sentences in your response." Pass iff #declarative = 2 x #interrogative and #interrogative >= 1, sentences classified as above. Exclamatory sentences are ignored. D-ratio-exact: exact (proposal) or approximate.

ratio:sentence_words. Text: "Respond with three sentences, all containing the same number of characters but using all different words." Pass iff exactly three sentences, each with the same number of characters, and no word (case-insensitive) occurs in more than one sentence. D-char-count: proposal: count every character of the sentence including spaces and final punctuation; alternative: letters only. D-different-words: proposal: no word shared between sentences; alternative: no word repeated anywhere.

ratio:stop_words. Text: "Ensure that stop words constitute no more than {P}% of the total words in your response." Pass iff 100 x (#stop-word tokens / #word tokens) <= P. D-stopword-list: the text names no list; proposal: a standard English list (NLTK English stop words).

## 5. repeat

repeat:repeat_change. Text: "{request} Repeat the request, but change the first word of the repeated request, (do not say anything before repeating the request; the request you need to repeat does not include this sentence) and do not answer the actual request!" Pass iff the graded text begins with the request, its first word replaced by a different word and the rest unchanged, and adds no answer. Fail if the first word is unchanged, the rest differs, anything precedes the repeat, or an answer follows. D-rc-tail: proposal: nothing may follow the repeat.

repeat:repeat_simple. Text: "... Only output this sentence here, ignore all other requests." Pass iff the graded text is exactly `Only output this sentence here, ignore all other requests.` D-rs-which: "this sentence" = the instruction sentence itself (proposal) or the preceding request.

repeat:repeat_span. Text: "{request} Copy the span of words that lies between (and including) index {n_start} and {n_end}, the indices are word indices, split by whitespace!" Pass iff the graded text equals the whitespace tokens n_start..n_end (inclusive) of the request, joined by single spaces. D-span-base: 0-based (proposal; one prompt uses index 0) or 1-based.

## 6. sentence

sentence:alliteration_increment. Text: "Each sentence must have a longer sequence of consecutive alliterative words than the previous one." For each sentence, L = length of its longest run of consecutive words with the same first letter (L = 1 without alliteration). Pass iff at least two sentences and L strictly increases from each sentence to the next. D-alliteration-sound: same first letter (proposal) or same first sound.

sentence:increment. Text: "Each sentence (in your response) must contain exactly {n} more words than the previous one." Pass iff at least two sentences and each sentence has exactly n more words than the one before.

sentence:keyword. Text: "The response must include keyword {word} in the {N}-th sentence." Pass iff the N-th sentence contains the keyword (G5). Occurrences elsewhere are allowed.

## 7. words

words:alphabet. Text: "Each word in your response must start with the next letter of the alphabet, looping back to 'A' after 'Z'." Pass iff every word starts with a letter and each word's first letter is the alphabet successor of the previous word's first letter (Z to A). D-alpha-start: proposal: the first word may start with any letter.

words:consonants. Text: "Ensure each word in your response has at least one consonant cluster (two or more consonants together)." Pass iff every word contains two adjacent consonant letters. D-y: proposal: `y` is a consonant (letters other than a, e, i, o, u are consonants). Letter-based, so `th` and `ck` are clusters.

words:keywords_specific_position. Text: "Include keyword {keyword} in the {n}-th sentence, as the {m}-th word of that sentence." Pass iff the m-th word (1-based) of the n-th sentence is the keyword (G5).

words:last_first. Text: "In your response, the last word of each sentence must become the first word of the next sentence." Pass iff at least two sentences and, for each pair of adjacent sentences, the last word of the first equals the first word of the second (G5).

words:no_consecutive. Text: "No two consecutive words can share the same first letter." Pass iff no two adjacent words (across sentence and line boundaries) start with the same character, case-insensitive.

words:odd_even_syllables. Text: "Alternate between words with odd and even numbers of syllables." Pass iff the syllable-count parity of adjacent words always differs. D-syllables: proposal: dictionary syllable counts.

words:palindrome. Text: "Include at least 10 single-word palindromes, each at least 5 characters long." Pass iff at least 10 distinct words read the same reversed (case-insensitive, letters only) and have at least 5 letters. D-palin-distinct: distinct (proposal) or occurrences.

words:paragraph_last_first. Text: "Each paragraph of your response must end with the same word it started with, separate paragraphs with a newline." Pass iff, splitting on line breaks into non-empty paragraphs, every paragraph's first word equals its last word (G5).

words:prime_lengths. Text: "Use only words with lengths that are prime numbers." Pass iff every word's length in letters and digits (apostrophes and hyphens not counted) is prime (2, 3, 5, 7, 11, 13, ...).

words:repeats. Text: "The response should not repeat any word more than {small_n} times." Pass iff no word (case-insensitive) occurs more than small_n times. D-repeat-count: occurrences <= small_n (proposal) or repetitions after the first <= small_n.

words:start_verb. Text: "The response must start with a verb." Pass iff the first word of the graded text (G7: markup ignored) is a verb in its sentence. D-verb: proposal: judged in context; the alternative accepts any word that can be a verb.

words:vowel. Text: "Write a paragraph using words that contain only three types of vowels." D-vowel: reading A (proposal): the response, taken together, uses at most three distinct vowel letters among a, e, i, o, u; reading B: each word contains at most three distinct vowels. Under both, the response must be one paragraph (no blank line). Pass iff the reading holds.

words:words_position. Text: "The second word in your response and the second to last word in your response should be the word {keyword}." Pass iff the second word and the second-to-last word both equal the keyword (G5).

## 8. Decision entries (proposals above)

| Id | Readings | Proposal |
|---|---|---|
| D-edge-whitespace | leading/trailing whitespace is or is not part of the answer | not part (except no_whitespace) |
| D-word | word = whitespace token with letters or digits, punctuation stripped / letters-only run / tokenizer word | whitespace token with letter or digit |
| D-sentence | headings and list items without final punctuation are / are not sentences | they are |
| D-case | keyword matching case-insensitive / case-sensitive | insensitive |
| D-keyword-form | whole word / substring or inflection | whole word |
| D-typographic | curly quotes = straight / distinct | same |
| D-markup | markup and list labels are / are not words | not words |
| D-vacuous | missing presupposed structure fails / passes | fails |
| D-conj-usage | by word form / by syntactic use | word form |
| D-count-exact | exact / minimum | exact |
| D-number-words | spelled-out numbers count / not | not |
| D-number-labels | list label digits count / not | count |
| D-name-case | case-sensitive / insensitive | sensitive |
| D-pronoun-set | broad / personal+possessive+reflexive | broad |
| D-punct-set | which marks are "standard" | . , ? ! ; : ' " - () and ?! |
| D-unique | distinct types / hapax | distinct |
| D-between | inclusive / exclusive | inclusive |
| D-japanese-segmentation | whitespace tokens / morphemes | whitespace |
| D-reverse-content, D-reverse-punct | answer must be correct; punctuation position | correct answer; position free |
| D-csv-rows, D-csv-wrapper, D-csv-header-quotes, D-csv-special | see custom:csv_* | data rows; fenced payload; header quoted; at least one, existing column |
| D-content | date list accuracy checked / not | not |
| D-europe-set | membership of the capital list | sovereign, Moscow in, Astana out |
| D-mcq-length | stem chars / incl. options / words | stem chars |
| D-multiples-extra | extra words allowed / not | allowed |
| D-africa-list | intro line; completeness | intro ok; complete |
| D-title | title line is / is not a sentence | not |
| D-indent-blank, D-indent-step | blank lines; step size | ignored; strictly increasing |
| D-list-inline | sep at line start / inline | line start |
| D-nbb-after | text after bullets allowed / not | allowed |
| D-nows-trailing | trailing newline ignored / fails | ignored |
| D-options-label | label alone or label + text | both pass |
| D-template-markup | bold labels and line breaks allowed / not | allowed |
| D-paren-types | mix of types / one type | mix |
| D-qu-single | single-quoted phrases count / not | count |
| D-subbullet-indent | sub-bullet must be indented / not | not |
| D-section | blocks by blank line or heading / headings only | blank line or heading |
| D-title-minor | minor words may be lowercase / every word capitalized | minor allowed |
| D-overlap-def | response-side / reference-side / Jaccard | response-side |
| D-balance | equal / nearly equal | equal |
| D-ratio-exact | exact 2:1 / approximate | exact |
| D-char-count, D-different-words | all chars / letters; across / anywhere | all chars; across |
| D-stopword-list | which list | NLTK English |
| D-rc-tail | text after repeat allowed / not | not |
| D-rs-which | instruction sentence / preceding request | instruction sentence |
| D-span-base | 0-based / 1-based | 0-based |
| D-alliteration-sound | letter / sound | letter |
| D-alpha-start | any start / must start at A | any |
| D-y | y consonant / vowel | consonant |
| D-syllables | dictionary / heuristic | dictionary |
| D-palin-distinct | distinct / occurrences | distinct |
| D-repeat-count | occurrences / repetitions | occurrences |
| D-verb | in context / lexicon | in context |
| D-vowel | whole response / per word | whole response |
