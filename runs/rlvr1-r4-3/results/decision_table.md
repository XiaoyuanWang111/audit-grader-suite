| Entry | Question | Reading A (proposed) | Reading B | Example: A / B | Grader A follows B on | Grader B follows B on |
|---|---|---|---|---|---|---|
| D-outer-whitespace | Is leading/trailing whitespace part of the response? | No: stripped before every check | Yes | end_checker `…help with?\n`: pass / fail | - | - |
| D-empty | Does empty text pass a prohibition? | Yes; requirements fail | Every constraint fails | no_comma on `""`: pass / fail | square_brackets | first_word_sent, last_word_sent, lowercase_counting, sentence_hyphens, square_brackets |
| D-word | What is a word? | Letter/digit runs with inner `'`/`-`; one CJK char = one word; punctuation-only tokens are not words | Whitespace-separated tokens | `Hi - there **` words: 2 / 4 | last_word_answer, last_word_sent, number_words | number_words |
| D-sentence | What ends a sentence? | Terminal punctuation (not abbreviations, decimals, list numbers), or the end of a line without one | Terminal punctuation only | `Title\nOne sentence.`: 2 / 1 sentences | last_word_sent, number_sentences | last_word_sent, number_sentences |
| D-keyword-match | How does a keyword match? | Case-insensitive whole word | Case-insensitive substring | forbidden `art` in `start`: pass / fail | existence, frequency, word_once | - |
| D-letter-case | Does "the letter t" count `T`? | Yes | No | `Tt`, at least 2: pass / fail | - | - |
| D-capital-word | Do one-letter words (`I`, `A`) count as all-capital words? | Yes | No (two or more letters) | `I am`, at least 1: pass / fail | - | capital_word_frequency |
| D-english | What makes a response "in English"? | Its natural-language text is English; names, code, numbers do not count | Every word is English | `THE CAPITAL IS 北京 (BEIJING).`: pass / fail | - | - |
| D-two-responses-different | What makes two responses "different"? | Not identical after stripping whitespace | Different in content (a judgment) | `Yes.\n******\nYes!`: pass / fail | - | - |
| D-repeat-center | Which word is "in the center"? | The middle word (odd length) or either middle word (even) | Any word but the first and last | 6-word phrase, 5th word replaced: fail / pass | repeat_phrase | - |
| D-repeat-original | Does a verbatim copy of the phrase fail? | Yes, it is an untransformed repetition | No, it is ignored | intro quoting the phrase + n variants: fail / pass | - | - |
| D-unique-case | Are `The` and `the` the same word? | Yes | No | `The cat saw the dog`: fail / pass | count_unique | - |
| D-lowercase-counting-scope | "All lowercase words should appear at most N times": per word or in total? | Each lowercase word at most N times | At most N lowercase words in all | N=2, `the cat and the dog`: pass / fail | lowercase_counting | - |
| D-placeholder | What is a placeholder? | Non-empty `[...]` on one line, not a markdown link's text | Any `[...]`, including `[]` and link text | `[x](http://a)`, at least 1: fail / pass | number_placeholders | - |
| D-postscript-marker | Must the marker match the kwarg exactly? | Final period optional, colon allowed, case-sensitive | Exact kwarg string (`P.S.`) | `P.S: thanks` for `P.S.`: pass / fail | postscript | postscript |
| D-postscript-position | Where must the marker be? | At the start of a line (after markup) | Anywhere | `see my P.S. below`: fail / pass | postscript | - |
| D-bigram | Can an odd last word stand alone in `<<...>>`? | No: every unit has exactly two words | Yes, one single-word unit at the end | `<<I am>> <<here>>`: fail / pass | bigram_wrapping | - |
| D-constrained | May other text surround the option? | No: the response is exactly one option | Yes, if exactly one option appears | `My answer is yes. Because…`: fail / pass | constrained_response | - |
| D-json | Is a JSON scalar "JSON format"? | No: object or array | Any JSON value | `"hello"`: fail / pass | json_format | json_format |
| D-sections-case | Must the splitter's case match? | Yes | No | `Section 1` for `SECTION`: fail / pass | - | multiple_sections |
| D-sections-numbering | Must X run 1..n in order? | Yes | No, any X | `SECTION 1`, `SECTION 3` for n=2: fail / pass | multiple_sections | multiple_sections |
| D-sections-preamble | Is text before the first marker allowed? | Yes | No | `Intro\nSECTION 1 …`: pass / fail | - | - |
| D-bullets | Which lines are bullet points? | `*`, `-`, `+` bullets, nested ones included | Only `*` bullets, as in the example | `- a\n- b`, exactly 2: pass / fail | - | - |
| D-highlight | Does bold `**x**` count as a highlight? | Yes | No, only `*x*` | `**Intro**`, at least 1: pass / fail | - | - |
| D-hyphens-single | Does a one-sentence response pass? | Yes | No | `Hello there.`: pass / fail | - | sentence_hyphens |
| D-square-brackets | One word per bracket pair? | Yes | No: every word inside some pair | `[Hello world]`: fail / pass | - | square_brackets |
| D-title | Where may the title be? | Anywhere | At the start | `Text\n<<T>>`: pass / fail | - | - |
| D-palindrome | Do one- or two-letter words count? | No: at least 3 letters | Yes | `I am here`: fail / pass | palindrome | - |
| D-consecutive-order | Are `b`,`a` consecutive letters? | Yes, either order | Only `a` then `b` | `big apple`: fail / pass | no_adjacent_consecutive | no_adjacent_consecutive |
| D-start-end-case | Must the two words match in case? | No | Yes | `Hello world hello`: pass / fail | - | - |
| D-count-exact | "Should appear N times": exactly or at least? | Exactly N | At least N | N+1 occurrences: fail / pass | - | - |
| D-language | How strict is "no other language"? | Names, code, numbers allowed | No foreign word at all | Korean text with `iPhone`: pass / fail | - | - |
| D-divider | Which dividers separate paragraphs? | A line that is exactly `***` | Any markdown thematic break (`---`, `* * *`, `****`) | `a\n---\nb`, 2 paragraphs: fail / pass | - | counting_composition |
| D-paragraph-blank | Is a blank-line run of 3+ newlines one separator? | Yes; whitespace-only lines are blank | No: only `\n\n` separates | `a\n\n\nb`, 2 paragraphs: pass / fail | paragraphs2 | - |
| D-comma-chars | Which characters are commas? | `,` `，` `、` `،` `﹐` `﹑` | `,` only | `你好，世界`: fail / pass | no_comma | no_comma |
| D-dot-chars | Which characters are dots? | `.` `．` `。` `…` | `.` only | `你好。`: fail / pass | punctuation_dot | punctuation_dot |
| D-exclamation-chars | Which characters are exclamation marks? | `!` `！` `¡` `‼` `❗` `❕` | `!` only | `你好！`: fail / pass | punctuation_exclamation | punctuation_exclamation |
| D-end-phrase | May punctuation or markup follow the phrase? | Yes, no words | Nothing but whitespace | `**Any other questions?**`: pass / fail | end_checker | end_checker |
| D-quotation | Do curly quotes count? | Yes | No, only `"` | `“Hi”`: pass / fail | quotation | - |
| D-letters-count | Which characters are letters? | Unicode alphabetic | ASCII a-z, A-Z | `Да`, at least 2: pass / fail | letter_counting | - |
| D-postscript-case | Must the marker's case match? | No | Yes | `p.s. thanks` for `P.S.`: pass / fail | - | - |
| D-start-end-leading | May markup or punctuation precede the first word? | Yes | No | `**Hello** world hello`: pass / fail | start_end | - |
| D-start-end-single | Does a one-word response pass start_end? | Yes | No | `Hello`: pass / fail | start_end | - |
| D-end-phrase-case | Is "this exact phrase" case-sensitive? | Yes | No | `… ANY OTHER QUESTIONS?`: fail / pass | end_checker | - |
| D-first-last-case | Is the word compared case-insensitively? | Yes | No | `Development is…` for `development`: pass / fail | - | - |
| D-first-last-markup | Are markup and punctuation around the word ignored? | Yes | No | `**development** is…`: pass / fail | first_word_answer, nth_paragraph_first_word | - |
| D-separator-edge | Does a divider or separator at the very start or end count? | No, it is ignored | Yes, it makes an empty part | `***\n\nOne paragraph.`, 1 paragraph: pass / fail | - | number_paragraphs |
| D-divider-inline | Does ` *** ` inside a line separate paragraphs? | Yes | No, only a divider line | `One. *** Two.`, 2 paragraphs: pass / fail | - | number_paragraphs |

48 entries
