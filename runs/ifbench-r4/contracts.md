# IFBench check contracts

Written from the text the model sees (the 300 prompts of IFBench_test at revision
2e8a48de) and the benchmark README, before any grader or reference code was read.
Each contract states when a response passes. Where the text allows two verdicts,
the contract names a decision entry `D-<topic>` and follows its proposed reading;
the decision table at the end lists both readings with an example of each.

## General rules

G1. Graded text. For a model without reasoning, the graded text is the whole
completion. For a reasoning model, it is the text after the last end-of-reasoning
marker (`</think>` for Qwen3); a separate reasoning field is never graded. A
completion whose reasoning opens and never closes is an extraction failure: it
fails every check and is counted separately.

G2. Leading and trailing whitespace of the graded text is ignored, except by
`format:line_indent`, where the indentation of every line is the point
(D-trim).

G3. A truncated completion (`finish_reason == "length"`) is graded as it stands.

G4. Empty graded text fails every check (D-empty).

G5. Word. A word is a maximal run of letters, digits, apostrophes and hyphens
that contains at least one letter or digit; all other characters (spaces,
punctuation, symbols, Markdown markers) separate words. "don't" and
"well-known" are one word each; "2021" is a word; "*" and "--" are not words.
Where a contract compares a word with a given word, the comparison ignores case
(D-word, D-case). A word's length counts its letters and digits only.

G6. Sentence. A sentence ends at `.`, `?` or `!` (possibly repeated or followed
by closing quotes or brackets) followed by whitespace or the end of the text,
and also at a line break that ends a non-empty line (a heading, a list item or
a line without terminal punctuation is its own sentence). Abbreviations and
decimals ("e.g.", "3.5") do not end a sentence. Empty lines are not sentences
(D-sentence).

G7. Keyword. "Include keyword X" counts whole-word occurrences of X, ignoring
case; inflected or longer words ("whispered" for "whisper") do not count
(D-keyword-form).

G8. A requirement that quantifies over items ("every quoted phrase", "every Nth
word", "each sentence ... than the previous one") holds when there are no such
items, provided the graded text is not empty (D-vacuous).

G9. A conversational preamble or sign-off line ("Sure, here is ...") is part of
the graded text (D-preamble). Markdown markers are part of the graded text
(D-markdown).

G10. Correctness of content is not graded unless the instruction is about the
content (custom checks with a definite answer: see each contract).

G11. Scores. Instruction-level accuracy is the share of instruction instances
that pass; prompt-level accuracy is the share of prompts whose every
instruction passes. The README states that the paper reports prompt-level
loose accuracy; "loose" is the benchmark's score-level transform and is tested
against these contracts in step 4 (D-loose).

## Contracts

### count

- **count:conjunctions** — "Use at least N different coordinating conjunctions in the response." Pass iff at least N distinct words of {and, but, or, nor, for, yet, so} occur in the graded text, case ignored. Any occurrence of the word form counts, whatever its grammatical role (D-conj-role).
- **count:keywords_multiple** — "Include keyword K1 once in your response, keyword K2 twice ..., K3 three times ..., K4 five times ..., and keyword K5 seven times in your response." Pass iff the whole-word counts of K1..K5 are exactly 1, 2, 3, 5, 7 (D-count-exact, G7).
- **count:numbers** — "Include exactly N numbers in the response." Pass iff the graded text contains exactly N numbers, where a number is a maximal numeral written with digits, with optional sign, thousands separators and one decimal part ("1,000", "-3.5", "2021" are one number each); number words ("five") do not count (D-number).
- **count:person_names** — "Mention at least N different person names in the response, from this list of person names: Emma, ..., Jonathan ." Pass iff at least N distinct names of the list occur as whole words with the list's capitalization (D-name-case). Names not on the list do not count.
- **count:pronouns** — "The response should include at least N pronouns." Pass iff the number of pronoun occurrences is at least N, counting personal, object, possessive (including the determiners my, your, his, her, its, our, their), reflexive pronouns, and also demonstrative, interrogative/relative and indefinite pronouns (this, that, these, those, who, whom, whose, which, what, someone, anyone, everyone, everything, nothing, ...), case ignored (D-pronoun-set).
- **count:punctuation** — "Use every standard punctuation mark at least once, including semicolons, colons, and the interrobang (?!)." Pass iff the graded text contains each of: period, comma, question mark, exclamation mark, semicolon, colon, apostrophe (' or ’), quotation mark (" or “ ”), hyphen or dash, parentheses ( ), and an interrobang written `?!` or `‽` (D-punct-set).
- **count:unique_word_count** — "Use at least N unique words in the response." Pass iff the number of distinct words (case ignored) is at least N (D-unique).
- **count:word_count_range** — "The response must contain between MIN and MAX words." Pass iff MIN <= word count <= MAX (D-between).
- **count:words_japanese** — "Every Nth word of your response must be in Japanese." Words are whitespace-separated tokens with surrounding punctuation removed (a run of Japanese text without spaces is one token) (D-japanese-word). Pass iff every token at positions N, 2N, 3N, ... (1-based) consists of Japanese script (hiragana, katakana, kanji; Japanese punctuation allowed). Other tokens may be in any language (D-japanese-others).

### custom (one prompt each)

- **custom:character_reverse** — "What animal is the national symbol of the US? Respond to this query, but make your sentence in reverse order of what it should be, per letter." Pass iff the graded text, reversed character by character, reads as an English sentence that answers the query (names the bald eagle), and the graded text is not itself forward English. Case and the position of punctuation are not graded (D-reverse-answer).
- **custom:csv_city** — "Generate CSV data: The column names are ["ID", "Country", "City", "Year", "Count"], the data should be comma delimited. Please generate 7 rows." Pass iff the graded text contains a CSV block: a header line with exactly these five names in this order, comma-delimited, followed by exactly 7 data lines of 5 comma-delimited fields. The block may sit in a code fence; prose outside the block is allowed (D-csv-wrapper); the header is required and is not one of the 7 rows (D-csv-header).
- **custom:csv_quotes** — "... the data should be tab delimited. Please generate 3 rows and enclose each single field in double quotes." Pass iff the CSV block has a header line and exactly 3 data lines, each with 5 tab-delimited fields, and every field, header fields included, is enclosed in double quotes (D-csv-header, D-csv-wrapper).
- **custom:csv_special_character** — "... comma delimited. Please generate 14 rows. Add one field which contains a special character and enclose it in double quotes." Pass iff the CSV block has a header and exactly 14 data lines of 5 comma-delimited fields (a quoted field may contain commas), and at least one field contains a special character (not a letter, digit or space) and is enclosed in double quotes (D-csv-special).
- **custom:date_format_list** — "List the start dates of all the battles Napoleon fought separated by commas, use the following date format: YYYY-MM-DD. Do not provide an explanation." Pass iff the graded text is a comma-separated list (spaces after commas allowed) of at least two valid calendar dates written YYYY-MM-DD, with no other text. Completeness and historical accuracy are not graded (D-date-content).
- **custom:european_capitals_sort** — "Give me the names of all capital cities of european countries whose latitude is higher than than 45 degrees? List the capital cities without country names, separated by commas, sorted by latitude, from highest to lowest." Pass iff the graded text is a comma-separated list of capital-city names only (no country names, no other text), the list holds exactly the capitals of European sovereign states north of 45° N, and it is sorted by latitude from north to south. Which states count as European and the latitudes come from an answer key that the maintainers fix (D-capitals-key).
- **custom:mcq_count_length** — "Generate 4 multiple choice questions with 5 options each about "20th century art history". Each question should start with the label "Question". The questions should get progressively longer. Do not provide an explanation." Pass iff there are exactly 4 questions, each beginning with the label "Question", each followed by exactly 5 options, the question texts strictly increasing in length (characters of the question stem, options excluded) (D-mcq-length), and no explanation or answer key.
- **custom:multiples** — "Count from 10 to 50 but only print multiples of 7." Pass iff the numbers printed are exactly 14, 21, 28, 35, 42, 49 in this order, with any separators; other words are allowed (D-multiples-text).
- **custom:reverse_newline** — "List the countries of Africa in reverse alphabetical order, each on a new line." Pass iff each country is on its own line, the country lines are in strictly reverse alphabetical order, and they cover the 54 sovereign African states (common alternative names accepted); a heading or intro line is allowed (D-africa-key).
- **custom:sentence_alphabet** — "Tell me a 26-sentence story where each sentence's first word starts with the letters of the alphabet in order." Pass iff the story has exactly 26 sentences and the first word of sentence i starts with the i-th letter, A to Z, case ignored. A title line is not a story sentence (D-story-title).
- **custom:word_reverse** — "... make your sentence in reverse order of what it should be, per word." Pass iff the graded text's words, read in reverse order, form an English sentence that answers the query (names the bald eagle), the words themselves are not reversed, and the forward word order is not already natural English (D-reverse-answer).

### format

- **format:emoji** — "Please use an emoji at the end of every sentence." Pass iff every sentence ends with an emoji, either as its last character or directly before or after its terminal punctuation (D-emoji-position, G6).
- **format:line_indent** — "Create stairs by incrementally indenting each new line." Pass iff every non-empty line after the first has strictly more leading whitespace than the non-empty line before it; empty lines are ignored; the first line may have no indent (D-indent).
- **format:list** — "Answer with a list of items, instead of bullet points use SEP." (SEP is `!?!?`, `SEPARATOR` or `-`.) Pass iff the graded text is a list of at least two items marked or separated by SEP, and no item is marked with another bullet character (`*`, `•`, or `-` when SEP is not `-`, or a numbered marker). SEP may separate items inline or start each line (D-list-sep).
- **format:newline** — "Write each word on a new line." Pass iff every non-empty line holds exactly one word (punctuation attached to it allowed); empty lines are allowed.
- **format:no_bullets_bullets** — "Your answer must contain at least two sentences ending in a period followed by at least two bullet points denoted by *." Pass iff at least two sentences ending in `.` appear before the first bullet, and at least two lines are bullets of the form `* text`; text after the bullets is allowed (D-nbb-order).
- **format:no_whitespace** — "The output should not contain any whitespace." Pass iff the graded text, after G2, contains no Unicode whitespace character (D-whitespace-set).
- **format:options** — "Answer with one of the following options: OPTIONS. [Do not give any explanation.]" (OPTIONS is `yes/no/maybe`, `I know or I don't know`, or `a), b), c), d)`.) Pass iff the graded text, ignoring case, surrounding whitespace, Markdown emphasis and one trailing period, is exactly one option; for the letter set, the letter with its parenthesis may be followed by that option's text ("b) Larceny") (D-options-exact).
- **format:output_template** — "Use this exact template for your response: My Answer: [answer] My Conclusion: [conclusion] Future Outlook: [outlook]" Pass iff the graded text starts with "My Answer:", contains "My Conclusion:" and then "Future Outlook:", each label once and in this order, and every placeholder is replaced by non-empty text that is not the literal placeholder. Markdown emphasis around a label is allowed (D-template-markup).
- **format:parentheses** — "Nest parentheses (and [brackets {and braces}]) at least 5 levels deep." Pass iff the graded text contains properly matched brackets, of any mix of `()`, `[]`, `{}`, with at least 5 open at once (D-paren-types).
- **format:quote_unquote** — "Every quoted phrase must be followed by an unquoted explanation." Pass iff every quoted phrase (text in straight or curly double quotes, or in single quotes used as quotation marks, not apostrophes) is followed, after its closing mark, by at least one unquoted word of explanation before the next quoted phrase or the end of its sentence (D-explanation, G8).
- **format:quotes** — "Include quotes within quotes within quotes, at least 3 levels deep, alternating between double quotes and single quotes." Pass iff the graded text contains a quotation nested 3 deep whose marks alternate between double and single quotes at each level ("...'..."..."...'..."), starting with either kind; straight and curly marks both count.
- **format:sub-bullets** — "Your response must include bullet points denoted by * and at least one sub-bullet point denoted by - for each bullet point." Pass iff there is at least one bullet line `* text`, and every such bullet is followed, before the next `*` bullet, by at least one line `- text`. Indentation of the `-` line is not required (D-subbullet-indent).
- **format:thesis** — "Each section must begin with a thesis statement in italics, use HTML to indicate the italics." Sections are the parts that Markdown headings start, or, without headings, the blocks separated by blank lines (D-section). Pass iff the first non-heading text of every section is a statement wrapped in `<i>...</i>` or `<em>...</em>`.
- **format:title_case** — "Write the entire response in title case (capitalize the first letter of every major word)." Pass iff every major word starts with an uppercase letter; minor words (articles, coordinating conjunctions, prepositions of up to four letters, "to", "as") may be lower case except as the first word of the response or of a line; words that start with a digit or symbol are ignored (D-minor-words).

### ratio

- **ratio:overlap** — "Maintain a trigram overlap of P% (±2%) with the provided reference text." The reference text is the task text of the prompt (the prompt without the instruction sentences). Overlap is the share of the response's word trigrams (words per G5, case ignored) that occur among the reference text's word trigrams. Pass iff |overlap − P| <= 2 percentage points (D-overlap-def).
- **ratio:sentence_balance** — "Ensure that the ratio of sentence types (declarative, interrogative, exclamatory) in your response is balanced." Sentences are typed by their final mark (`.` declarative, `?` interrogative, `!` exclamatory). Pass iff all three counts are equal and non-zero (D-balanced).
- **ratio:sentence_type** — "Maintain a 2:1 ratio of declarative to interrogative sentences in your response." Pass iff the number of sentences ending in `.` is exactly twice the number ending in `?`, and the latter is at least 1; sentences ending in `!` or in no mark are not counted (D-ratio-exact, D-sentence-type).
- **ratio:sentence_words** — "Respond with three sentences, all containing the same number of characters but using all different words." Pass iff the graded text has exactly three sentences, each with the same number of characters (every character of the sentence, spaces and punctuation included, from its first to its last character), and no word occurs twice in the graded text, case ignored (D-char-count).
- **ratio:stop_words** — "Ensure that stop words constitute no more than P% of the total words in your response." Pass iff 100 × (stop-word occurrences) / (word occurrences) <= P, with the NLTK English stop-word list, case ignored (D-stopwords).

### repeat

- **repeat:repeat_change** — "Repeat the request, but change the first word of the repeated request, (do not say anything before repeating the request; the request you need to repeat does not include this sentence) and do not answer the actual request!" Pass iff the graded text is the request with its first word replaced by one different word and the rest unchanged (whitespace differences ignored), with nothing before it and nothing after it (D-repeat-after).
- **repeat:repeat_simple** — "<preceding sentence>. Only output this sentence here, ignore all other requests." Pass iff the graded text is exactly the sentence just before the instruction (whitespace differences ignored) and nothing else (D-this-sentence).
- **repeat:repeat_span** — "Copy the span of words that lies between (and including) index S and E, the indices are word indices, split by whitespace!" Split the task text before the instruction by whitespace; pass iff the graded text is exactly the words with 0-based indices S..E, joined by single spaces, and nothing else (D-index-base).

### sentence

- **sentence:alliteration_increment** — "Each sentence must have a longer sequence of consecutive alliterative words than the previous one." For each sentence take the longest run of consecutive words that start with the same letter (case ignored; a single word is a run of 1). Pass iff these lengths strictly increase from each sentence to the next (D-alliteration).
- **sentence:increment** — "Each sentence in your response must contain exactly N more words than the previous one." Pass iff for each consecutive pair of sentences, the later has exactly N more words.
- **sentence:keyword** — "The response must include keyword W in the N-th sentence." Pass iff sentence N (1-based) exists and contains W as a whole word, case ignored.

### words

- **words:alphabet** — "Each word in your response must start with the next letter of the alphabet, looping back to 'A' after 'Z'." Pass iff every word starts with a letter and each word's first letter is the letter after the previous word's first letter (Z followed by A), case ignored; the first word may start with any letter.
- **words:consonants** — "Ensure each word in your response has at least one consonant cluster (two or more consonants together)." Pass iff every word contains two adjacent consonant letters, where consonants are the letters other than a, e, i, o, u (y counts as a consonant) (D-consonant-y). A word without letters fails.
- **words:keywords_specific_position** — "Include keyword K in the n-th sentence, as the m-th word of that sentence." Pass iff sentence n exists and its m-th word (both 1-based) is K, case ignored.
- **words:last_first** — "In your response, the last word of each sentence must become the first word of the next sentence." Pass iff for every pair of consecutive sentences, the last word of the first equals the first word of the second, case ignored.
- **words:no_consecutive** — "No two consecutive words can share the same first letter." Pass iff no two adjacent words in the graded text (across sentence and line breaks) start with the same character, case ignored.
- **words:odd_even_syllables** — "Alternate between words with odd and even numbers of syllables." Pass iff the syllable counts of consecutive words alternate between odd and even, starting with either; syllables are counted from a pronouncing dictionary where the word is in it and by a vowel-group rule otherwise (D-syllables).
- **words:palindrome** — "Include at least 10 single-word palindromes, each at least 5 characters long." Pass iff at least 10 distinct words of at least 5 characters read the same backwards, case ignored (D-palindrome-distinct).
- **words:paragraph_last_first** — "Each paragraph of your response must end with the same word it started with, separate paragraphs with a newline." Paragraphs are the non-empty lines (D-paragraph). Pass iff every paragraph's first word equals its last word, case ignored.
- **words:prime_lengths** — "Use only words with lengths that are prime numbers." Pass iff every word's length (letters and digits) is a prime number.
- **words:repeats** — "The response should not repeat any word more than N times." Pass iff no word occurs more than N times, case ignored (D-repeat-count).
- **words:start_verb** — "The response must start with a verb." Pass iff the first word of the graded text, read in its sentence, is a verb (any form, including an imperative) (D-verb).
- **words:vowel** — "Write a paragraph using words that contain only three types of vowels." Pass iff the vowel letters (a, e, i, o, u) used across all words of the graded text are of at most three distinct kinds; the paragraph form is not part of the check (D-vowel).
- **words:words_position** — "The second word in your response and the second to last word in your response should be the word W." Pass iff the second word and the second-to-last word of the graded text are both W, case ignored.

## Decision table

Each entry: the reading the contract proposes (P) and the other reading (A), with an example where they differ.

| Entry | Proposed reading (P) | Other reading (A) | Example that splits them |
|---|---|---|---|
| D-trim | Leading/trailing whitespace of the graded text is ignored (except line_indent). | Every character counts. | `"abc\n"` for no_whitespace: P pass, A fail. |
| D-empty | Empty graded text fails every check. | Empty text passes checks it satisfies literally (no whitespace, every sentence ends with an emoji, ...). | `""` for format:no_whitespace: P fail, A pass. |
| D-word | Word = run of letters/digits/apostrophes/hyphens with a letter or digit (G5). | Word = whitespace-separated token. | `"Yes - no"` has 2 words under P, 3 under A. |
| D-case | Word comparisons ignore case. | Case-sensitive. | Keyword "door" vs "Door". |
| D-keyword-form | Whole-word matches only. | Substrings or inflections count. | "whispered" for keyword "whisper": P no, A yes. |
| D-count-exact | "once", "twice", "N times" are exact counts. | At-least counts. | "kaleidoscope" twice for "once": P fail, A pass. |
| D-conj-role | Any occurrence of a FANBOYS word form counts. | Only words used as coordinating conjunctions. | "for example", "so much": P counts "for", "so"; A does not. |
| D-number | Numerals in digits only; "1,000" and "3.5" are one number each. | Number words count too, or digit groups split at `,`/`.`. | "five apples and 3 pears": P 1 number, A 2. |
| D-name-case | Names count only with the list's capitalization. | Case ignored. | "grace" (common noun) for "Grace": P no, A yes. |
| D-pronoun-set | Personal, possessive, reflexive, demonstrative, interrogative/relative and indefinite pronouns. | Personal, possessive and reflexive only. | "This is what everyone wants" has 3 under P, 0 under A. |
| D-punct-set | . , ? ! ; : ' " - ( ) and `?!` or `‽`. | All ASCII punctuation (adds # $ % & * + / < = > @ [ ] \ ^ _ ` { } | ~) or a different list. | A text with the 11 marks and `?!` but no `@`: P pass, A fail. |
| D-unique | Unique = distinct. | Unique = occurring exactly once. | "a a b": P 2, A 1. |
| D-between | Bounds inclusive. | Bounds exclusive. | 71 words for "between 71 and 73": P pass, A fail. |
| D-japanese-word | Whitespace tokens; a spaceless run of Japanese text is one token. | Japanese runs are segmented into words. | "これはペンです" counts 1 word under P, several under A. |
| D-japanese-others | Non-Nth words unconstrained. | Only the Nth words may be Japanese. | All-Japanese text: P pass, A fail. |
| D-reverse-answer | Graded on reversal and on answering the query. | Graded on reversal only (any sentence). | ".god a si tI" (answer "dog"): P fail, A pass. |
| D-csv-wrapper | Code fence and prose outside the block allowed. | Only the CSV text. | "Here is the data:\n```csv ...```": P pass, A fail. |
| D-csv-header | Header line required; not counted as a row. | Header optional, or counted as one of the rows. | Header + 6 data lines for "7 rows": P fail, A pass. |
| D-csv-special | At least one quoted field contains a special character; 5 columns kept. | Exactly one such field, or an added sixth column. | Two quoted special fields: P pass, A fail. |
| D-date-content | Format only. | Completeness/accuracy graded too. | "1796-04-12, 1805-12-02": P pass, A fail. |
| D-capitals-key | Maintainers fix the set of European states and latitudes. | — (key must be chosen). | Whether Moscow, Astana, Chisinau are included. |
| D-mcq-length | Question stem length in characters, strictly increasing. | Whole question with options, or words. | Longer stems with shorter options. |
| D-multiples-text | Other words allowed around the numbers. | Only the numbers. | "Multiples of 7: 14, 21, ...": P pass, A fail. |
| D-africa-key | 54 sovereign states, alternative names accepted, intro line allowed. | A different country list, or no extra lines. | Inclusion of Western Sahara / Somaliland. |
| D-story-title | A title line is not a story sentence. | Every line counts. | "The Alphabet Tale\nA...": P 26 sentences, A 27. |
| D-sentence | Line breaks also end sentences (G6). | Only `.?!` end sentences. | A heading line "Intro" followed by text: P 2 sentences, A 1. |
| D-emoji-position | Emoji before or after the terminal mark. | Emoji must be the very last character. | "Hi 😀." : P pass, A fail. |
| D-indent | Strictly increasing indent over non-empty lines. | Non-decreasing, or blank lines also count. | Two lines with equal indent: P fail, A pass. |
| D-list-sep | SEP inline between items or at line starts. | Only inline separators. | "- a\n- b" with SEP `-`: P pass, A fail. |
| D-nbb-order | Two period sentences before the first `*` bullet; text after allowed. | The two sentences anywhere. | Bullets first, then sentences: P fail, A pass. |
| D-whitespace-set | Any Unicode whitespace. | ASCII space only. | "a\tb": P fail, A pass. |
| D-options-exact | The whole answer is one option. | The option may appear inside longer text. | "Yes, because ...": P fail, A pass. |
| D-template-markup | Markdown emphasis around labels allowed. | Labels verbatim only. | "**My Answer:** ...": P pass, A fail. |
| D-paren-types | Any mix of (), [], {} counts toward depth. | Each level must use the next bracket type. | "(((((x)))))": P pass, A fail. |
| D-explanation | Unquoted words must follow each quote before the next quote or sentence end. | Any later unquoted text counts. | `"a" "b" explained.` : P fail, A pass. |
| D-subbullet-indent | `-` lines need no indentation. | Sub-bullets must be indented. | "* a\n- b": P pass, A fail. |
| D-section | Sections = heading-started parts, else blank-line blocks. | Sections only where headings exist (whole text is one section otherwise). | Three paragraphs without headings, only the first italic: P fail, A pass. |
| D-minor-words | Minor words may be lower case. | Every word capitalized. | "The Rise of Rome": P pass, A fail. |
| D-overlap-def | Share of response trigrams found in the reference. | Share of reference trigrams found in the response, or Jaccard. | A verbatim copy of half the reference: P 100%, A about 50%. |
| D-balanced | Equal non-zero counts of the three types. | Roughly equal, or all three present. | 3 declarative, 2 interrogative, 2 exclamatory: P fail, A pass. |
| D-ratio-exact | Exactly 2:1. | Approximately 2:1. | 5 declarative, 2 interrogative: P fail, A pass. |
| D-sentence-type | Fragments without a final mark are not typed. | They count as declarative. | A heading line: P ignored, A declarative. |
| D-char-count | All characters of each sentence. | Letters only, or excluding spaces. | Equal letter counts but unequal spaces. |
| D-stopwords | NLTK English list. | Another list. | "also" is not in NLTK's list. |
| D-repeat-after | Nothing after the repeated request. | Trailing text allowed if it does not answer. | "Make ... \nOk.": P fail, A pass. |
| D-this-sentence | "this sentence" = the sentence before the instruction. | = the instruction sentence itself. | Output "Only output this sentence here, ignore all other requests.": P fail, A pass. |
| D-index-base | 0-based indices. | 1-based. | Prompt words "a b c d" with "index 1 and 2": P "b c", A "a b". |
| D-alliteration | Same first letter. | Same first sound. | "cat kite": P run 1, A run 2. |
| D-consonant-y | y is a consonant. | y is a vowel. | "myth": P cluster, A cluster still ("th"); "byte": P "by" cluster, A none. |
| D-syllables | Dictionary pronunciation, else vowel-group rule. | Another counting rule. | "fire": 1 or 2 syllables. |
| D-palindrome-distinct | Distinct words. | Occurrences. | "level" ten times: P 1, A 10. |
| D-paragraph | Paragraph = non-empty line. | Paragraph = blank-line-separated block. | Two lines with no blank line: P 2 paragraphs, A 1. |
| D-repeat-count | At most N occurrences. | At most N+1 occurrences (N repeats after the first use). | A word 5 times for N=4: P fail, A pass. |
| D-verb | First word functions as a verb in context. | First word can be a verb in some reading. | "Light travels fast.": P fail, A pass. |
| D-vowel | At most three distinct vowels across the whole text. | Each word has at most three distinct vowels, or exactly three across the text. | "Cats and dogs sit in huts" (a, o, i, u): P fail, A pass. |
| D-vacuous | Quantified requirements hold with no items (non-empty text). | At least one item required. | No quotes for quote_unquote: P pass, A fail. |
| D-preamble | A preamble/sign-off line is graded. | It is excluded before grading. | "Sure!\nMy Answer: ...": P fail, A pass. |
| D-markdown | Markdown markers are graded. | Emphasis markers are removed first. | "**Imagine** ..." for start_verb: same under both; "*" lines for line counts differ. |
| D-loose | Report strict scores; loose transforms are judged per contract. | Report loose scores as the paper does. | See step 4 loose test. |
