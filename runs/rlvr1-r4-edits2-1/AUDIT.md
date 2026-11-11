# Audit of the RLVR1 instruction-following graders: SkyRL reward and task-curation gate

Offline audit, 2026-11-11, of the two graders that score the 11,817 instruction-following rows of Marin's
Nemotron RLVR1 data (Marin `af9c678`): the SkyRL reward `grade_instruction_following`, which runs NVIDIA's
verifiable-instructions checkers (`f46a5ac`, also the reference implementation), and the deterministic gate of
the task-curation grader, which runs verifyit's `ifeval` checks before an LLM judge. Followed
`skill/SKILL.md`; the record that the skill keeps in an issue is `audit/ISSUE.md`.

## 1. Error rate and effect on scores

**The error rate is not estimated.** Step 6, the blinded review that estimates it, did not run (no
reviewers in this exercise). What this audit measures instead is the share of verdicts that the contract
contradicts under every reading in the decision table, as judged by the audit's replacement grader
(`audit/lib/contracts_grader.py`, written from the instruction texts). That is a defect rate, not a
reviewer-estimated error rate; decision-dependent verdicts are counted apart.

| Panel: 23,315 stored responses, 55,783 constraint verdicts | SkyRL reward (NVIDIA checkers) | Task-curation gate (verifyit) |
|---|---|---|
| Constraint verdicts the contract contradicts under every reading | 2,253 of 55,783 (4.0%): 740 false passes, 1,513 false fails | 6,018 of 50,724 deterministic verdicts (11.9%): 4,286 false passes, 1,732 false fails |
| Further disagreements that depend on a decision entry | 3,250 | 2,080 |
| Passes the contract contradicts (defects only) | 343 of 6,471 reward-1.0 responses (5.3%) are false rewards | 2,445 of 10,192 gate passes (24.0%) should have failed the gate |
| Same, under the proposed readings of every decision | 1,059 of 6,471 (16.4%) | 3,041 of 10,192 (29.8%) |
| Score change when only the defects are fixed (prompt level, 95% bootstrap interval) | +0.65 [+0.08, +1.30] to +5.93 [+4.53, +7.40] points | -9.1 [-11.5, -6.9] to +5.07 [+3.33, +6.87] points |
| Rerun noise (Qwen3-4B-Instruct greedy rerun, same settings) | 16 of 1,000 prompt verdicts, +0.2 points | 27 of 1,000, +0.1 points |

Every fix-only score change is larger than the rerun difference; the smallest, Qwen2.5-7B's SkyRL change
(+0.65), has an interval that reaches down to +0.08.
Three more results bear on the reward directly:

- **Content-free responses earn reward.** An empty response gets SkyRL reward 1.0 on 1,702 of the 11,817
  rows (14.4%) and passes the gate on 810; a lone "." gets reward 1.0 on 1,144 rows. Whether an empty
  response may pass negative checks is decision D-empty-response, but an empty response also reaches the
  reward through two extraction defects (F37, F38).
- **One check type is graded at random.** For 77 rows whose instruction asks for paragraph n of fewer than n
  paragraphs, NVIDIA's checker redraws n at random on every call (F44): one fixed response got reward 1.0
  under 41 of 200 random seeds. The rows themselves are unsatisfiable (G1).
- **Two checks fail compliant responses most of the time.** `keywords:word_once` requires exactly one
  occurrence where the text says "Include keyword X" (F02, 44% of its verdicts wrong in SkyRL), and
  `keywords:word_count_different_numbers` is graded with a relation the model never sees (F01, 26%).

**Recommendation: fix both graders** (do not admit them; the benchmark does not need replacing). Bring the
47 checks to the contracts, starting with F01, F02, F04, F09, F11, F18, F20, F21 and F26 (each wrong on more
than 14% of its check's verdicts) and the extraction stage (F37, F38); make the nth-paragraph rows
deterministic and drop or repair the 77 unsatisfiable rows (F44, G1); pin the NLTK data; and send the
decision entries (section 5) to the maintainers. The recommendation still needs step 6 (section 8):
the replacement passes every fixture and has complete coverage, but its lower error rate has not been
measured by a blinded review.

## 2. Substitutions in this offline run

- No issue tracker: the issue record (pinned inputs, contract hash and time, decision entries, findings,
  frozen-file hashes, every contract change with its reason) is `audit/ISSUE.md`.
- No repository, research branch, Hugging Face dataset or job launcher: fixtures are runnable tests in
  `audit/tests/`, frozen files are in `audit/frozen/` with their sha256 in ISSUE.md, scripts are in
  `audit/scripts/`, and no PR, branch, dataset revision or job was made. Fixtures that a current grader
  fails are marked `xfail(strict=True)`, as the skill asks.
- Step 5: no compute. The panel is the stored responses in `case/panel/` (6 runs of 4 models); no response
  was generated.
- Step 6: not run (section 8).
- The LLM judge of the task-curation grader is not in the case. The gate's verdicts are reported; the
  final task-curation reward (judge fraction after the gate) is not.

## 3. Inputs (step 1) and graded text

Full list with hashes in ISSUE.md. In short: grader files by git blob from `case/SOURCES.md`; the installed
`verifiable_instructions` and `verifyit` are byte-identical to the case copies (`audit/scripts/check_pins.py`,
run before and after each panel run: OK); data extract sha256 `96144deb...` with one sha256 per row in
`audit/frozen/row_hashes.tsv` (`496221f7...`); prompt = the row's single user message; panel generation
settings from `case/panel/CONFIGS.md`; NLTK `punkt_tab` by zip hash; nltk 3.10.3, langdetect 1.0.9.

Graded text. Both pipelines strip closed `<think>...</think>` blocks and keep the text after the last
closing marker (`final_answer_text` in SkyRL, verifyit `_answer_text` in the gate, the same algorithm). The
contract (`audit/CONTRACTS.md`, section 0) adds: a response whose reasoning never closes is an extraction
failure and fails every check. Both pipelines break that rule in two ways (F37, F38).

Unverified or unpinned inputs (finding G2):
- Every row has `route == "skyrl_gym"`, but `NemotronTaskSession` raises for any route other than
  `"task_session"`; the code that serves route `skyrl_gym` is not in the case. Verify with
  `git -C marin grep -n "skyrl_gym" af9c6789 -- vendor/skyrl/skyrl-gym`.
- `_ensure_nltk_data` downloads `punkt_tab` from the network when it is missing; NLTK data has no version.
  NLTK also searches the user's home and the venv, so `NLTK_DATA` must point at the pinned copy.
- The panel records do not give stop sequences or the server's reasoning parser (they matter for F38).
- The upstream repositories and the Hugging Face file could not be fetched (no network); the commands
  that would verify them are in ISSUE.md.

## 4. Findings

N = NVIDIA checker as the SkyRL reward runs it (also the reference implementation, so "reference: same"
means the defect is upstream); V = verifyit check as the gate runs it. Panel share = defect verdicts
attributed to the finding over the verdicts of the named checks (attribution in
`audit/scripts/analyze_extra.py`; defects that no single finding explains are listed as residual). The
exact input of each counterexample, the contract label and both graders' verdicts are in the table after
this list; reproduce any of them with the command in section 9.

| Id | Grader | Check or stage | Contract it breaks | Panel share | Reference |
|---|---|---|---|---|---|
| F01 | N, V | `keywords:word_count_different_numbers` | text "should appear {f} times" (no relation shown); graded with the hidden `relation` kwarg, so f occurrences fail under `less than` and zero pass | N 261 (144 fp, 117 ff) = 25.7% of 1,015; V 260 = 25.6% | same |
| F02 | N, V | `keywords:word_once` | "Include keyword X in your response" = at least once; graders require exactly one | N 803 ff = 44.4% of 1,808; V 766 = 42.4% | same |
| F03 | N | `copy:repeat_phrase` | each repetition transformed; only the last found copy's differences are checked, so a verbatim copy passes | N 54 (51 fp) = 5.1% of 1,059 (with F05) | same |
| F04 | V | `copy:repeat_phrase` | counts verbatim copies (>= small_n): transformed copies fail, verbatim repeats pass | V 481 (453 fp) = 45.4% of 1,059 | not in reference |
| F05 | N | `copy:repeat_phrase` | an earlier occurrence of the phrase's first word on the line breaks the match | in F03's count | same |
| F06 | N | `detectable_format:constrained_response` | substring test passes a response with two different options | N 3 = 1.2% of 243 | same |
| F07 | N | `detectable_format:multiple_sections` | "must have N sections"; tests `>=` | N 32 = 3.5% of 917 | same |
| F09 | V | `length_constraints:number_paragraphs` | paragraphs separated by `***`; counts blank-line paragraphs, so the divider line is a paragraph and no divider is needed | V 426 (370 ff) = 31.7% of 1,345 | not in reference |
| F10 | N | `length_constraints:number_paragraphs` | splits at `***` inside a line (bold-italic markup) | N 1 = 0.1% | same |
| F11 | V | `paragraphs:paragraphs`, `paragraphs:paragraphs2` | "There should be 2 paragraphs"; passes 2 or more, by divider or blank line | V 565 fp = 22.2% of 2,541 | not in reference |
| F12 | N | first-word checks (`first_word_answer`, `first_word_sent`, `nth_paragraph_first_word`) | punctuation right after the word (`Development,`, `Feedback:`) makes the word differ | N 72 ff = 3.4% of 2,137, plus 44 = 4.3% of `first_word_sent` (with F42) | same |
| F13 | N | `keywords:keyword_specific_position` | punctuation tokens count as words, shifting the position | N 11 = 0.8% of 1,341 | same |
| F14 | N | `keywords:palindrome` | palindrome followed by punctuation missed; a bullet `-` counts as a palindrome | N 49 (16 fp, 33 ff) = 4.2% of 1,165 | same |
| F15 | N | `keywords:start_end` | compares tokens, so text starting and ending with `**` passes | N 11 = 1.1% of 989 (with F41) | same |
| F16 | V | `keywords:start_end` | ignores "not even punctuation" after the last word | V 69 (56 fp) = 7.0% of 989 | not in reference |
| F17 | N | `keywords:no_adjacent_consecutive` | uses the first character of whitespace tokens, so markup, brackets or quotes hide the letter | N 58 (56 fp) = 3.9% of 1,499 | same |
| F18 | V | `keywords:no_adjacent_consecutive` | checks adjacent duplicate words, a different requirement | V 819 (787 fp) = 54.6% of 1,499 | not in reference |
| F19 | N | `detectable_format:square_brackets` | punctuation outside the brackets (`[world].`, `-`) fails the response | N 61 (49 ff) = 5.7% of 1,079 | same |
| F20 | V | `detectable_format:square_brackets` | passes when any one bracketed span exists | V 657 (655 fp) = 60.9% of 1,079 | not in reference |
| F21 | N | `detectable_format:bigram_wrapping` | one-word groups pass; punctuation after a group fails | N 171 fp = 14.8% of 1,157 | same (judge in V) |
| F22 | N | `detectable_format:sentence_hyphens` | a hyphenated word inside a sentence fails a compliant response | N 14 = 1.1% of 1,300 (with F43) | same |
| F23 | V | `detectable_format:sentence_hyphens` | passes sentences separated by a space | V 2 = 0.2% | not in reference |
| F24 | N | `count:count_unique` | punctuation and markup tokens count as words, so two commas fail | N 106 (100 ff) = 7.9% of 1,341 | same (judge in V) |
| F25 | N, V | `count:counting_composition` (1 row) | NVIDIA splits at `***`, not the instructed `* * *`, and counts period tokens as words (no compliant response passes); V tests `>=` on the first sentences | 1 verdict in the panel (all fail) | same |
| F26 | V | `count:lowercase_counting` | inverted: requires at least N lowercase words for "at most N times" | V 1,317 (1,167 fp) = 76.9% of 1,712 | not in reference |
| F27 | V | `change_case:english_capital`, `english_lowercase` | no test that the text is English (Russian passes) | V 166 fp = 6.1% of 2,742 | not in reference |
| F28 | V | `startend:quotation` | single quotation marks accepted as double | 0 in panel | not in reference |
| F29 | N | `detectable_content:postscript` | unanchored substring: `P.P.S.` satisfies the `P.S.` marker | N 9 = 0.7% of 1,277 | same |
| F30 | N | `detectable_format:number_bullet_lists` | a `---` rule and a line starting with an italic span count as bullets | N 21 (18 ff) = 2.1% of 1,019 | same |
| F31 | V | `detectable_format:json_format` | an upper-case fence tag (```` ```JSON ````) fails | 0 in panel | not in reference |
| F32 | N, V | `detectable_format:json_format` | `NaN` / `Infinity` accepted as JSON | 0 in panel | same |
| F33 | N, V | placeholders, title | empty or whitespace-only `[]`, `[ ]` (N, V) and `<<   >>` (V) count | N 2, V 2 (0.1 to 0.2%) | same for `[]` |
| F34 | V | every word-based check | verifyit's word pattern `[A-Za-z0-9'\-]+` is ASCII-only: Cyrillic and other scripts have no words | V 270 (204 + 66 with F43) over the word-based checks | not in reference |
| F35 | V | word counts | a typographic apostrophe splits a word, a straight one does not (`don’t` 2 words, `don't` 1); NVIDIA's count is consistent and rests on D-word-apostrophe | not separated from F34 | not in reference |
| F36 | N, V | `combination:two_responses` | seven asterisks accepted as the six-asterisk separator | N 2, V 2 = 0.4% of 557 | same |
| F37 | N, V | extraction | an unclosed `<think>` (or `<thinking>`) gives graded text "", which passes negative checks (reward 1.0 on an all-negative row) | 23 non-reasoning responses leave a literal `<think>` (14) or `<thinking>` (9) unclosed; SkyRL grades "" for them, 8 got reward 1.0 | not applicable |
| F38 | N, V | extraction | a response cut inside its reasoning, from a model whose template opens `<think>`, is graded as its reasoning | 139 of 1,500 Qwen3-Thinking responses (9.3%); 84 SkyRL and 113 gate false constraint passes, 18 gate passes | not applicable |
| F39 | N | `last_word:last_word_answer`, session | `IndexError` on empty text, which the session reports as INFRA_ERROR | 1 panel response; 625 rows when the response is empty | same |
| F40 | N | `change_case:english_capital`, `english_lowercase` | English test = `isupper()`/`islower()` + langdetect on the raw text: all-capital English is rejected, mostly-Chinese text accepted | N 100 (77 ff) = 3.6% of 2,742 | same |
| F41 | N | last-word and start/end checks | whitespace tokens merge words not separated by spaces (CJK text, `habits.chemistry`) | N 62 ff = 4.8% of 1,285, plus 44 = 3.7% of `last_word_sent` (with F42) | same |
| F42 | N | sentence checks | the sentence splitter ends a sentence at every period, even with no space after it (`Float.parseFloat()`) | in F12 and F41 counts | same |
| F43 | N, V | sentence checks | a CJK full stop `。` does not end a sentence | `number_sentences`: N 72 = 6.4%, V 86 = 7.6% of 1,131 | same |
| F44 | N | `length_constraints:nth_paragraph_first_word` | nth > num is redrawn at random on each call (`build_description`; SkyRL's guard covers only a missing nth) | 161 verdicts in the panel, 12 random passes, 7 rewards of 1.0 | same |
| F45 | V | word counts | the word pattern matches a bare hyphen, so `Good - fine` is 3 words | metamorphic only (bullet edits) | not in reference |
| F46 | N, V | sentence checks | a numbered label `1.` is read as a sentence | metamorphic: 40 of 40 `last_word_sent` passes flip | same |
| F47 | N | `count:lowercase_counting` | counts only ASCII lowercase words (`\b[a-z]+\b`), so a Russian response passes | N 40 fp = 2.3% of 1,712 | same |
| G1 | data | 77 rows | ask for paragraph nth of fewer than nth paragraphs: no response can pass | 77 rows | - |
| G2 | inputs | pipeline | route `skyrl_gym` vs the session's `task_session` check; NLTK data downloaded unversioned; stop sequences and reasoning parser unrecorded | - | - |

F08 (a mid-line `SECTION 2` counted by verifyit) was withdrawn after contract change C3: it is correct under
the other reading of D-section-line-start, so it is a decision. Residual defect verdicts that no finding
explains: SkyRL 33 (0.4% of the verdicts of six checks, mostly langdetect differences in
`language:response_language` and word-boundary differences), verifyit 11; they were not reviewed one by one.

Counterexamples (from `audit/tests/fixtures_data.py`; the decision rows show the proposed reading as the
label):

| Ref | Fixture id (repro argument) | Check, kwargs | Exact response (Python repr) | Contract | NVIDIA/SkyRL | verifyit gate |
|---|---|---|---|---|---|---|
| D-allcaps-short-words | `change_case:capital_word_frequency:61717c8dd1365436` | `change_case:capital_word_frequency` {"capital_frequency": 2, "capital_relation": "at least"} | `'I think A plan works.'` | pass | pass | fail |
| D-bullet-markers | `detectable_format:number_bullet_lists:c6f348cd23b81afd` | `detectable_format:number_bullet_lists` {"num_bullets": 2} | `'+ One\n+ Two'` | pass | fail | fail |
| D-comma-variants | `punctuation:no_comma:30be7d7b84ddffe1` | `punctuation:no_comma` {} | `'你好，世界'` | fail | pass | pass |
| D-consecutive-order | `keywords:no_adjacent_consecutive:c59f903a7bdda0df` | `keywords:no_adjacent_consecutive` {} | `'banana apple pie'` | fail | pass | pass |
| D-constrained-exact | `detectable_format:constrained_response:44c0c7033e4414b1` | `detectable_format:constrained_response` {} | `'I think so. My answer is yes.'` | fail | pass | fail |
| D-dot-variants | `punctuation:punctuation_dot:7a62d6278a10ff64` | `punctuation:punctuation_dot` {} | `'你好。'` | fail | pass | pass |
| D-empty-response | `language:response_language:7fec956f1aace6b0` | `language:response_language` {"language": "ta"} | `'12345'` | fail | pass | judge |
| D-empty-response | `punctuation:no_comma:06be01996cae30a4` | `punctuation:no_comma` {} | `''` | fail | pass | pass |
| D-empty-response | `keywords:forbidden_words:c5114f3a883fc996` | `keywords:forbidden_words` {"forbidden_words": ["law"]} | `''` | fail | pass | pass |
| D-empty-response | `change_case:capital_word_frequency:cb04a3b518e50051` | `change_case:capital_word_frequency` {"capital_frequency": 3, "capital_relation": "less than"} | `''` | fail | pass | pass |
| D-end-case | `startend:end_checker:5564798a9c45e629` | `startend:end_checker` {"end_phrase": "Any other questions?"} | `'Done. Do you have any other questions?'` | fail | pass | fail |
| D-end-trailing-nonwords | `startend:end_checker:202cc85eac51d7f3` | `startend:end_checker` {"end_phrase": "Any other questions?"} | `'"Done. Any other questions?"'` | pass | pass | fail |
| D-exclamation-variants | `punctuation:punctuation_exclamation:8decc8ce5798133c` | `punctuation:punctuation_exclamation` {} | `'你好！'` | fail | pass | pass |
| D-json-scalar | `detectable_format:json_format:09503a41da527628` | `detectable_format:json_format` {} | `'"hello"'` | fail | pass | pass |
| D-keyword-substring | `keywords:existence:87d66a02bc4c2852` | `keywords:existence` {"keywords": ["art"]} | `'He started early.'` | fail | pass | fail |
| D-keyword-substring | `keywords:frequency:0355f5e2479b28af` | `keywords:frequency` {"keyword": "cat", "frequency": 2, "relation": "less than"} | `'Educated cats catch mice.'` | pass | fail | pass |
| D-letter-script | `letters:letter_counting:48838d595cccf0ac` | `letters:letter_counting` {"N": 2, "relation": "at least"} | `'Да'` | pass | fail | judge |
| D-lowercase-counting-scope | `count:lowercase_counting:7d5a791ee4026a55` | `count:lowercase_counting` {"N": 2} | `'One cat and one dog.'` | pass | fail | pass |
| D-markup-around-word | `first_word:first_word_answer:cbf2d138fd47eae7` | `first_word:first_word_answer` {"first_word": "development"} | `'**Development** matters.'` | pass | fail | pass |
| D-palindrome-case | `keywords:palindrome:62a8ded21110d7dd` | `keywords:palindrome` {} | `'Level ground helps.'` | pass | fail | pass |
| D-postscript-case | `detectable_content:postscript:4674ca3e3b73e74e` | `detectable_content:postscript` {"postscript_marker": "P.S."} | `'Main text.\n\np.s. extra note.'` | fail | pass | pass |
| D-postscript-line-start | `detectable_content:postscript:a0b8a5d3a6e0af88` | `detectable_content:postscript` {"postscript_marker": "P.S."} | `'Main text here. P.S. Extra note.'` | fail | pass | fail |
| D-postscript-position | `detectable_content:postscript:a8302688a3f54f05` | `detectable_content:postscript` {"postscript_marker": "P.S."} | `'P.S. Note first.\n\nThen the main answer follows here.'` | fail | pass | pass |
| D-section-line-start | `detectable_format:multiple_sections:d967086adf8065b4` | `detectable_format:multiple_sections` {"num_sections": 2, "section_spliter": "SECTION"} | `'SECTION 1\nThis part leads into SECTION 2.\nSECTION 2\nThis part ends it.'` | pass | pass | fail |
| D-section-line-start | `detectable_format:multiple_sections:b686605e7dff55ae` | `detectable_format:multiple_sections` {"num_sections": 2, "section_spliter": "SECTION"} | `'SECTION 1 is the intro. SECTION 2 is the end.'` | fail | pass | pass |
| D-section-marker-case | `detectable_format:multiple_sections:dd762be1089097bd` | `detectable_format:multiple_sections` {"num_sections": 2, "section_spliter": "SECTION"} | `'Section 1\nFirst part.\nSection 2\nSecond part.'` | fail | fail | pass |
| D-sentence-hyphens-dash | `detectable_format:sentence_hyphens:0b2d46601bde67d2` | `detectable_format:sentence_hyphens` {} | `'It rains - we stay in'` | fail | fail | fail |
| D-sentence-hyphens-spaces | `detectable_format:sentence_hyphens:1b4531546d3ac76d` | `detectable_format:sentence_hyphens` {} | `'It rains.-We stay in.'` | pass | pass | fail |
| D-square-brackets-grouping | `detectable_format:square_brackets:0526f144406b939b` | `detectable_format:square_brackets` {} | `'[Hello world]'` | fail | fail | pass |
| D-two-responses-extra-separator | `combination:two_responses:3d4b0705945215fa` | `combination:two_responses` {} | `'******\nFirst answer.\n******\nSecond answer.'` | fail | pass | pass |
| D-typographic-quotes | `startend:quotation:f3d9800cc2e16c79` | `startend:quotation` {} | `'“Hello there.”'` | pass | fail | pass |
| D-wcdn-relation | `keywords:word_count_different_numbers:0a2727f4f83ac447` | `keywords:word_count_different_numbers` {"keyword": "world", "frequency": 2, "relation": "at least"} | `'The world, the world, the world.'` | fail | pass | pass |
| D-word-apostrophe | `length_constraints:number_words:2b637a05948ea7b3` | `length_constraints:number_words` {"num_words": 4, "relation": "less than"} | `"I don't know"` | pass | fail | pass |
| D-word-case | `count:count_unique:f4d49a98da39b7aa` | `count:count_unique` {} | `'The cat saw the dog.'` | fail | pass | judge |
| F01 | `keywords:word_count_different_numbers:d32bced3c86c1f74` | `keywords:word_count_different_numbers` {"keyword": "world", "frequency": 2, "relation": "less than"} | `'The world is big and the world is old.'` | pass | fail | fail |
| F01 | `keywords:word_count_different_numbers:1b7ff6b07ab7cfd1` | `keywords:word_count_different_numbers` {"keyword": "world", "frequency": 2, "relation": "less than"} | `'The sky is big and the sea is old.'` | fail | pass | pass |
| F02 | `keywords:word_once:aa6ffee1a1e70878` | `keywords:word_once` {"keyword": "garden"} | `'The garden is green and the garden is quiet.'` | pass | fail | fail |
| F03 | `copy:repeat_phrase:52248bed0dc9b92f` | `copy:repeat_phrase` {"phrase": "All that glitters is not gold", "small_n": 2} | `'All that glitters is not gold. All that sparkles is not gold.'` | fail | pass | fail |
| F04 | `copy:repeat_phrase:deaebb3577268c95` | `copy:repeat_phrase` {"phrase": "All that glitters is not gold", "small_n": 2} | `'All that shines is not gold. All that sparkles is not gold.'` | pass | pass | fail |
| F04 | `copy:repeat_phrase:bd08dbeb93bb86d1` | `copy:repeat_phrase` {"phrase": "All that glitters is not gold", "small_n": 2} | `'All that glitters is not gold. All that glitters is not gold.'` | fail | fail | pass |
| F05 | `copy:repeat_phrase:da89c01a2205d20d` | `copy:repeat_phrase` {"phrase": "The early bird catches the worm", "small_n": 2} | `'The saying goes: The early riser catches the worm. The early bird grabs the worm.'` | pass | fail | fail |
| F06 | `detectable_format:constrained_response:0848d7a857912939` | `detectable_format:constrained_response` {} | `'My answer is yes. My answer is no.'` | fail | pass | fail |
| F07 | `detectable_format:multiple_sections:d64c8ce4bd4ad86c` | `detectable_format:multiple_sections` {"num_sections": 2, "section_spliter": "SECTION"} | `'SECTION 1\nFirst part.\nSECTION 2\nSecond part.\nSECTION 3\nThird part.'` | fail | pass | fail |
| F09 | `length_constraints:number_paragraphs:96f04c0630061d3d` | `length_constraints:number_paragraphs` {"num_paragraphs": 2} | `'Para one.\n\n***\n\nPara two.'` | pass | pass | fail |
| F09 | `length_constraints:number_paragraphs:60b7e63238f379ff` | `length_constraints:number_paragraphs` {"num_paragraphs": 2} | `'Para one.\n\nPara two.'` | fail | fail | pass |
| F09 | `length_constraints:number_paragraphs:6c50db45b8c45fbd` | `length_constraints:number_paragraphs` {"num_paragraphs": 2} | `'Para one.\n***\nPara two.'` | pass | pass | fail |
| F10 | `length_constraints:number_paragraphs:2dc2b5204358c976` | `length_constraints:number_paragraphs` {"num_paragraphs": 2} | `'Some ***key*** words here.\n***\nPara two.'` | pass | fail | fail |
| F11 | `paragraphs:paragraphs:1d11e8c48b33d225` | `paragraphs:paragraphs` {} | `'P one.\n\nP two.\n\nP three.'` | fail | fail | pass |
| F11 | `paragraphs:paragraphs:906cae2a5a49570c` | `paragraphs:paragraphs` {} | `'P one.\n***\nP two.\n***\nP three.'` | fail | fail | pass |
| F11 | `paragraphs:paragraphs2:b983b1a8aaea3e60` | `paragraphs:paragraphs2` {} | `'P one.\n\nP two.\n\nP three.'` | fail | fail | pass |
| F12 | `length_constraints:nth_paragraph_first_word:fe47a28b3412d0da` | `length_constraints:nth_paragraph_first_word` {"num_paragraphs": 2, "nth_paragraph": 2, "first_word": "feedback"} | `'Intro here.\n\nFeedback: it was good.'` | pass | fail | pass |
| F12 | `first_word:first_word_answer:f9ca3d9b34e97991` | `first_word:first_word_answer` {"first_word": "development"} | `'Development, in short, matters.'` | pass | fail | pass |
| F12 | `first_word:first_word_sent:b6be20bb443c533b` | `first_word:first_word_sent` {"first_word": "peace"} | `'Peace, friends, matters. Peace is good.'` | pass | fail | pass |
| F13 | `keywords:keyword_specific_position:dbcd5e8747df93f5` | `keywords:keyword_specific_position` {"keyword": "shot", "n": 1, "m": 3} | `'Well, the shot was good.'` | pass | fail | pass |
| F14 | `keywords:palindrome:611009cfa08c2499` | `keywords:palindrome` {} | `'It works like radar.'` | pass | fail | pass |
| F14 | `keywords:palindrome:4daa0b05ff042291` | `keywords:palindrome` {} | `'Steps:\n- Mix it\n- Bake it'` | fail | pass | fail |
| F15 | `keywords:start_end:6c42729e5565ee96` | `keywords:start_end` {} | `'**Plan** ahead and finish the **work**'` | fail | pass | fail |
| F16 | `keywords:start_end:c33188e95cb5eae1` | `keywords:start_end` {} | `'Hello world hello.'` | fail | fail | pass |
| F17 | `keywords:no_adjacent_consecutive:960345bbb5258e5c` | `keywords:no_adjacent_consecutive` {} | `'**Apple** banana pie'` | fail | pass | pass |
| F18 | `keywords:no_adjacent_consecutive:31146edd99ae82ae` | `keywords:no_adjacent_consecutive` {} | `'apple banana pie'` | fail | fail | pass |
| F18 | `keywords:no_adjacent_consecutive:87dd002f7df99707` | `keywords:no_adjacent_consecutive` {} | `'the the dog'` | pass | pass | fail |
| F19 | `detectable_format:square_brackets:2afd86cfd1de4aae` | `detectable_format:square_brackets` {} | `'[Hello] [world].'` | pass | fail | pass |
| F20 | `detectable_format:square_brackets:dc5cc467c8778358` | `detectable_format:square_brackets` {} | `'Hello [world] and more.'` | fail | fail | pass |
| F21 | `detectable_format:bigram_wrapping:b83af35d3038992a` | `detectable_format:bigram_wrapping` {} | `'<<I am>> <<at home>>.'` | pass | fail | judge |
| F21 | `detectable_format:bigram_wrapping:9ce1657eb52d8bc8` | `detectable_format:bigram_wrapping` {} | `'<<I>> <<am>> <<at>> <<home>>'` | fail | pass | judge |
| F22 | `detectable_format:sentence_hyphens:35eaac3027e6ac23` | `detectable_format:sentence_hyphens` {} | `'This is a well-known fact.-It is true.'` | pass | fail | fail |
| F23 | `detectable_format:sentence_hyphens:b35fa391063dc7d8` | `detectable_format:sentence_hyphens` {} | `'One-two. Three-four.'` | fail | fail | pass |
| F24 | `count:count_unique:406b86d8fed40ab1` | `count:count_unique` {} | `'Apples, pears, plums.'` | pass | fail | judge |
| F25 | `count:counting_composition:927af582c2b67ef1` | `count:counting_composition` {"n_sent": 3, "n_words": 2} | `'Cats purr. Dogs bark. Birds sing.\n* * *\nFish swim. Frogs leap. Bees buzz.\n* * *\nSuns rise. Moons glow. Stars shine.'` | pass | fail | pass |
| F25 | `count:counting_composition:c0f3c8241349e759` | `count:counting_composition` {"n_sent": 3, "n_words": 2} | `'Cats purr softly today. Dogs bark.\nFish swim.'` | fail | fail | pass |
| F26 | `count:lowercase_counting:eb56c7395899c66c` | `count:lowercase_counting` {"N": 2} | `'HELLO WORLD'` | pass | pass | fail |
| F26 | `count:lowercase_counting:925fbcb1888cedf0` | `count:lowercase_counting` {"N": 2} | `'the cat and the dog and the bird'` | fail | fail | pass |
| F27 | `change_case:english_capital:38fd65ee2f111090` | `change_case:english_capital` {} | `'ПРИВЕТ МИР'` | fail | fail | pass |
| F27 | `change_case:english_lowercase:d09299cda2d40fbf` | `change_case:english_lowercase` {} | `'привет мир'` | fail | fail | pass |
| F28 | `startend:quotation:69768847ade01bd4` | `startend:quotation` {} | `"'Hello there.'"` | fail | fail | pass |
| F29 | `detectable_content:postscript:4d22e36c6b921eac` | `detectable_content:postscript` {"postscript_marker": "P.S."} | `'Main text.\n\nP.P.S. Extra note.'` | fail | pass | fail |
| F30 | `detectable_format:number_bullet_lists:26c960fe0e93a01d` | `detectable_format:number_bullet_lists` {"num_bullets": 2} | `'* One\n* Two\n\n---\n\nDone.'` | pass | fail | pass |
| F30 | `detectable_format:number_bullet_lists:78af5d2676a4e206` | `detectable_format:number_bullet_lists` {"num_bullets": 2} | `'*Note:* this matters.\n* One\n* Two'` | pass | fail | pass |
| F31 | `detectable_format:json_format:27e1d2926988316a` | `detectable_format:json_format` {} | `'```JSON\n{"a": 1}\n```'` | pass | pass | fail |
| F32 | `detectable_format:json_format:747be635f047909d` | `detectable_format:json_format` {} | `'[NaN]'` | fail | pass | pass |
| F33 | `detectable_format:title:168b3648ff2c3b67` | `detectable_format:title` {} | `'<<   >>\nText here.'` | fail | fail | pass |
| F33 | `detectable_content:number_placeholders:0b75045b9ab486d6` | `detectable_content:number_placeholders` {"num_placeholders": 2} | `'Use [] and [] here.'` | fail | pass | fail |
| F33 | `detectable_content:number_placeholders:cb748719ed5e33ba` | `detectable_content:number_placeholders` {"num_placeholders": 2} | `'Use [ ] and [ ] here.'` | fail | pass | pass |
| F34 | `length_constraints:number_words:7834f601e845c90f` | `length_constraints:number_words` {"num_words": 3, "relation": "at least"} | `'Это очень хороший ответ'` | pass | pass | fail |
| F35 | `length_constraints:number_words:1e2fed917b0dd89d` | `length_constraints:number_words` {"num_words": 4, "relation": "less than"} | `'I don’t know'` | pass | fail | fail |
| F36 | `combination:two_responses:623abc890e8a842b` | `combination:two_responses` {} | `'First answer.\n*******\nSecond answer.'` | fail | pass | pass |
| F40 | `change_case:english_capital:034f58028d153c7d` | `change_case:english_capital` {} | `'REVIEW WHITE MATTER INJURY LINKS DIRECTLY BLOOD FLOW REDUCED'` | pass | fail | pass |
| F41 | `last_word:last_word_answer:5757303d80aa3214` | `last_word:last_word_answer` {"last_word": "store"} | `'这是答案，store'` | pass | fail | pass |
| F41 | `last_word:last_word_answer:619508866504b367` | `last_word:last_word_answer` {"last_word": "chemistry"} | `'Reflect on your habits.chemistry'` | pass | fail | pass |
| F42 | `last_word:last_word_sent:0a2db1b2165e2943` | `last_word:last_word_sent` {"last_word": "baseball"} | `'Call Float.parseFloat() for baseball.'` | pass | fail | pass |
| F43 | `length_constraints:number_sentences:6640a290137f1ed4` | `length_constraints:number_sentences` {"num_sentences": 2, "relation": "at least"} | `'今天下雨。我们在家。'` | pass | fail | fail |
| F43 | `detectable_format:sentence_hyphens:ccea86639e130705` | `detectable_format:sentence_hyphens` {} | `'今天下雨。我们在家。'` | fail | pass | fail |
| F45 | `length_constraints:number_words:e66cb6fea0e8eb8c` | `length_constraints:number_words` {"num_words": 3, "relation": "less than"} | `'Good - fine'` | pass | pass | fail |
| F46 | `last_word:last_word_sent:b2d076554d1b938b` | `last_word:last_word_sent` {"last_word": "limit"} | `'1. We hit the limit.\n2. We pass the limit.'` | pass | fail | fail |
| F47 | `count:lowercase_counting:4a1c4059e5a6f8d4` | `count:lowercase_counting` {"N": 2} | `'это и это и это'` | fail | pass | fail |

## 5. Decision entries for the maintainers

57 entries where the instruction text allows two verdicts (45 in contract v1, 8 added in C2 and 4 in C3,
each with its reason in `audit/CONTRACTS.md` section 3). Each has a switch in the replacement grader. The
two numeric columns flip that one switch on the whole panel. The entries that move scores most:
D-word-case (whether `Peace` is the word `peace`), the three sentence-hyphen entries, and
D-lowercase-counting-scope (NVIDIA counts all lowercase words together; the proposal counts each word).

| Entry | Proposed reading | Other reading | Constraint verdicts that change (panel) | Net prompt score change, points (all 23,315 responses) | Fixture |
|---|---|---|---|---|---|
| D-word-case | `Peace` equals `peace` | case must match | 1226 | -2.08 | `count:count_unique:f4d49a98da39b7aa` |
| D-sentence-hyphens-single | one sentence passes | at least two sentences needed | 675 | -1.49 | - |
| D-keyword-substring | keyword `law` not in `lawyer` | substring match: `lawyer` contains `law` | 414 | +0.35 | `keywords:existence:87d66a02bc4c2852`, `keywords:frequency:0355f5e2479b28af` |
| D-sentence-hyphens-spaces | spaces inside a sentence are allowed; none between sentences | no spaces anywhere (words joined by hyphens) | 401 | -0.92 | `detectable_format:sentence_hyphens:1b4531546d3ac76d` |
| D-sentence-hyphens-dash | a dash with a space beside it (`It rains - we stay in`) joins sentences with a space and fails | only terminal punctuation marks sentences, so that text is one sentence and passes | 323 | +0.82 | `detectable_format:sentence_hyphens:0b2d46601bde67d2` |
| D-lowercase-counting-scope | each lowercase word at most N times | total lowercase words at most N | 309 | -0.69 | `count:lowercase_counting:7d5a791ee4026a55` |
| D-word-hyphen | `well-known` is one word | two words | 243 | +0.32 | - |
| D-palindrome-length | at least three letters | any palindrome word, `a`, `I`, `aa` | 229 | +0.31 | - |
| D-wcdn-relation | "should appear N times" = exactly N | at least N | 209 | +0.38 | `keywords:word_count_different_numbers:0a2727f4f83ac447` |
| D-sentence-linebreak | a line break ends a sentence (a heading line is a sentence) | only `.!?` end sentences | 179 | +0.22 | - |
| D-divider-line | `***` divider must be on its own line | `***` anywhere splits | 179 | +0.18 | - |
| D-square-brackets-grouping | each word in its own brackets | one pair around many words is enough | 169 | +0.44 | `detectable_format:square_brackets:0526f144406b939b` |
| D-end-case | "exact phrase" is case-sensitive (`any other questions?` fails) | case-insensitive | 165 | +0.35 | `startend:end_checker:5564798a9c45e629` |
| D-paragraph-empty-piece | empty pieces fail | empty pieces are ignored | 159 | +0.24 | - |
| D-letter-counting-unit | letters = alphabetic characters | letters = words | 138 | +0.12 | - |
| D-adjacent-alphabet | only Latin a-z first letters are checked | consecutive letters of any alphabet (Cyrillic а,б) | 127 | -0.30 | - |
| D-letter-case | `S` counts as letter `s` | case-sensitive | 119 | +0.03 | - |
| D-postscript-line-start | the marker starts a line (`Main text.\nP.S. note`) | the marker may follow text on its line (`Main text. P.S. note`) | 117 | +0.12 | `detectable_content:postscript:a0b8a5d3a6e0af88` |
| D-keyword-inflection | `gardens` is not `garden` | inflected forms count | 105 | +0.06 | - |
| D-letter-script | letters of any script count for letters:letter_counting | only Latin a-z | 96 | -0.12 | `letters:letter_counting:48838d595cccf0ac` |
| D-postscript-position | postscript is the final part | marker anywhere | 92 | +0.15 | `detectable_content:postscript:a8302688a3f54f05` |
| D-english-detection | proper nouns, code and numbers allowed inside English text | any non-English token fails | 86 | -0.22 | - |
| D-allcaps-short-words | `I` and `A` count as all-capital words | one-letter words do not count | 85 | +0.20 | `change_case:capital_word_frequency:61717c8dd1365436` |
| D-constrained-exact | G is exactly one option | G contains one option among other text | 75 | +0.32 | `detectable_format:constrained_response:44c0c7033e4414b1` |
| D-word-apostrophe | `don't` is one word | `don` and `t` are two words | 68 | +0.01 | `length_constraints:number_words:2b637a05948ea7b3` |
| D-palindrome-case | case-insensitive (`Level` is a palindrome) | case-sensitive | 61 | -0.12 | `keywords:palindrome:62a8ded21110d7dd` |
| D-postscript-case | marker case as written (`p.s.` does not start a `P.S.` postscript) | case-insensitive | 58 | +0.09 | `detectable_content:postscript:4674ca3e3b73e74e` |
| D-highlight-bold | `**bold**` counts once | only single-asterisk `*x*` | 55 | -0.07 | - |
| D-dot-variants | `．`, `。`, `…` are dots | only ASCII `.` | 55 | +0.10 | `punctuation:punctuation_dot:7a62d6278a10ff64` |
| D-section-preamble | text before SECTION 1 is allowed | a preamble counts as an extra section or fails | 54 | -0.08 | - |
| D-consecutive-order | `c b` violates as `b c` does | only ascending pairs violate | 53 | +0.15 | `keywords:no_adjacent_consecutive:c59f903a7bdda0df` |
| D-markup-around-word | leading `**`/quotes before the first word ignored | any character before the first word fails | 51 | -0.12 | `first_word:first_word_answer:cbf2d138fd47eae7` |
| D-start-end-single | at least two words | a one-word G starts and ends with the same word | 42 | +0.12 | - |
| D-markup-around-marker | `**P.S.**`, `## SECTION 1` count as markers | marker must be the first characters of the line | 36 | -0.05 | - |
| D-end-trailing-nonwords | non-word characters (closing quotes, punctuation, markup) may follow the phrase; no word may (change C1) | nothing but whitespace may follow the phrase | 35 | -0.08 | `startend:end_checker:202cc85eac51d7f3` |
| D-two-responses-extra-separator | separators only between the two responses (`******` before the first one fails) | a leading or trailing separator is ignored | 31 | +0.09 | `combination:two_responses:3d4b0705945215fa` |
| D-repeat-verbatim | a verbatim copy fails | verbatim copies are ignored | 30 | +0.06 | - |
| D-comma-variants | `，`, `、`, `،` are commas | only ASCII `,` | 27 | +0.05 | `punctuation:no_comma:30be7d7b84ddffe1` |
| D-adjacent-scope | adjacency crosses punctuation and line breaks | only words in the same sentence/clause | 24 | +0.06 | - |
| D-section-marker-case | `SECTION` and `Section` are different markers | case-insensitive | 22 | +0.00 | `detectable_format:multiple_sections:dd762be1089097bd` |
| D-sentence-abbreviation | `Dr.` and `3.5` do not end a sentence | every `.` + space ends one | 17 | -0.03 | - |
| D-repeat-center | any word but the first and last may be replaced | only the middle word(s) | 15 | -0.06 | - |
| D-title-position | `<<title>>` anywhere | must be the first line | 10 | -0.02 | - |
| D-section-line-start | a section marker starts a line | a marker may stand mid-line (`SECTION 1 intro. SECTION 2 end.`) | 10 | +0.00 | `detectable_format:multiple_sections:d967086adf8065b4`, `detectable_format:multiple_sections:b686605e7dff55ae` |
| D-exclamation-variants | `！`, `¡`, `‼` are exclamation marks | only ASCII `!` | 9 | +0.01 | `punctuation:punctuation_exclamation:8decc8ce5798133c` |
| D-placeholder-content | any non-empty `[text]` counts, including `[1]` | only placeholder-like names (`[address]`) | 7 | -0.02 | - |
| D-paragraph-separator-count | three or more newlines still separate two paragraphs | more than two newlines make an empty paragraph or break the rule | 7 | +0.00 | - |
| D-two-responses-different | parts must differ after trimming | any two parts, even identical | 6 | +0.02 | - |
| D-bullet-markers | `*`, `-`, `+` bullets count | only `*` | 6 | +0.01 | `detectable_format:number_bullet_lists:c6f348cd23b81afd` |
| D-blank-line-whitespace | a line of only spaces is a blank line between paragraphs | only `\n\n` exactly separates | 6 | +0.00 | - |
| D-bullet-nesting | indented sub-bullets count | only top-level bullets count | 4 | +0.01 | - |
| D-typographic-quotes | `“ ”` count | only ASCII `"` | 4 | -0.00 | `startend:quotation:f3d9800cc2e16c79` |
| D-empty-response | empty G fails every check | literal: empty G passes negative checks (no commas, forbidden words, at most N, less than N) | 1 | +0.00 | `language:response_language:7fec956f1aace6b0`, `punctuation:no_comma:06be01996cae30a4` |
| D-bigram-odd | a final single-word group is allowed for odd counts | every group exactly two words | 1 | -0.00 | - |
| D-section-numbering | numbers 1..N in order | any numbers | 1 | +0.00 | - |
| D-surrounding-whitespace | leading/trailing whitespace of G is ignored (`"x"\n` passes quotation) | whitespace counts as content (`"x"\n` fails) | 0 | +0.00 | - |
| D-json-scalar | object or array only | any JSON value (`"hi"`, `3`) | 0 | +0.00 | `detectable_format:json_format:09503a41da527628` |

## 6. Model panel (step 5)

Stored records first: `finish_reason == "length"` on 65 / 92 / 81 / 620 / 166 / 39 responses (Qwen2.5-7B
sample0 / Qwen3-4B-Instruct greedy / greedy_repeat / sample0 / Qwen3-4B-Thinking sample0 / OLMo-2-7B
sample0); 139 Qwen3-Thinking responses never close their reasoning (F38); 14 non-reasoning responses
leave a literal `<think>` unclosed and 9 a literal `<thinking>` (F37); one OLMo response is empty. Held-out responses (one in five per run, by
hash, fixed before any panel result) were set aside before the panel prompted contract change C3.

Prompt-level scores (share of responses whose constraints all pass). "Fixes only" keeps each grader's
verdict except on defect verdicts; "replacement" uses the proposed reading of every decision. Intervals are
95% paired bootstrap intervals over responses.

| Run (responses) | SkyRL | Fixes only | Change | Replacement | Gate | Gate, fixes only | Change | Replacement, gate checks only |
|---|---|---|---|---|---|---|---|---|
| Qwen2.5-7B-Instruct sample0 (4,000) | 19.98 | 20.63 | +0.65 [+0.08, +1.30] | 19.63 | 32.98 | 26.93 | -6.05 [-7.10, -5.10] | 25.03 |
| Qwen3-4B-Instruct greedy (1,000) | 29.30 | 31.40 | +2.10 [+0.90, +3.40] | 32.90 | 49.90 | 40.80 | -9.10 [-11.50, -6.90] | 41.10 |
| Qwen3-4B-Instruct greedy_repeat (1,000) | 29.50 | 31.90 | +2.40 [+1.10, +3.70] | 33.10 | 50.00 | 41.40 | -8.60 [-10.90, -6.40] | 41.50 |
| Qwen3-4B-Instruct sample0 (11,817) | 29.53 | 32.54 | +3.01 [+2.56, +3.44] | 32.60 | 47.75 | 41.30 | -6.46 [-7.21, -5.69] | 41.28 |
| Qwen3-4B-Thinking sample0 (1,500) | 55.40 | 61.33 | +5.93 [+4.53, +7.40] | 64.93 | 63.40 | 68.47 | +5.07 [+3.33, +6.87] | 68.13 |
| OLMo-2-1124-7B-Instruct sample0 (3,998) | 19.11 | 20.16 | +1.05 [+0.53, +1.58] | 17.81 | 32.02 | 24.69 | -7.33 [-8.45, -6.28] | 23.66 |

On the held-out responses alone the replacement-minus-SkyRL differences keep their sign: Qwen2.5 18.2 vs
17.7, Qwen3 sample0 28.9 vs 33.5, Qwen3-Thinking 53.1 vs 63.5, OLMo 18.9 vs 17.5
(`audit/results/extra_tables.txt`). The SkyRL scores themselves moved between two
grading runs of the same responses (up to 0.08 points), because of F44.

Scored coverage: SkyRL gives a verdict to 23,314 of 23,315 responses (one INFRA_ERROR, F39); the gate gives a
deterministic verdict to 50,724 of 55,783 constraints (90.9%); 166 responses (94 data rows) have only
judged constraints and pass the gate by default; the replacement grades every response (extraction
failures fail).

Reference comparison (step 4) on the same responses: verifyit and NVIDIA disagree on 7,822 of 50,724 gated
verdicts (15.4%). Under the decision table, 4,710 are verifyit defects with NVIDIA inside some reading, 637
are NVIDIA defects with verifyit inside some reading, and 2,475 are decisions.

Per-check pass rates and defect counts (all runs):

| Check | Verdicts | Pass % replacement | Pass % SkyRL | SkyRL defects (false pass / false fail) | SkyRL decision-only | Pass % gate | Gate defects (fp / ff) | Gate decision-only |
|---|---|---|---|---|---|---|---|---|
| `change_case:capital_word_frequency` | 1207 | 75.5 | 76.2 | 13 (9 / 4) | 14 | 79.5 | 30 (11 / 19) | 81 |
| `change_case:english_capital` | 1534 | 51.4 | 45.1 | 94 (17 / 77) | 37 | 55.0 | 61 (61 / 0) | 6 |
| `change_case:english_lowercase` | 1208 | 70.0 | 69.0 | 8 (6 / 2) | 16 | 77.4 | 107 (105 / 2) | 13 |
| `combination:two_responses` | 557 | 76.1 | 81.5 | 3 (2 / 1) | 29 | 81.5 | 3 (2 / 1) | 29 |
| `copy:repeat_phrase` | 1059 | 4.4 | 8.9 | 54 (51 / 3) | 5 | 45.6 | 487 (459 / 28) | 43 |
| `count:count_unique` | 1341 | 22.3 | 15.0 | 106 (6 / 100) | 8 | judge | - | - |
| `count:counting_composition` | 1 | 0.0 | 0.0 | 0 (0 / 0) | 0 | 0.0 | 0 (0 / 0) | 0 |
| `count:lowercase_counting` | 1712 | 29.5 | 15.2 | 41 (41 / 0) | 285 | 88.4 | 1331 (1181 / 150) | 22 |
| `detectable_content:number_placeholders` | 1201 | 90.9 | 91.5 | 9 (8 / 1) | 0 | 91.4 | 8 (7 / 1) | 0 |
| `detectable_content:postscript` | 1277 | 60.5 | 83.3 | 17 (16 / 1) | 276 | 72.4 | 9 (8 / 1) | 153 |
| `detectable_format:bigram_wrapping` | 1157 | 3.4 | 19.4 | 185 (185 / 0) | 0 | judge | - | - |
| `detectable_format:constrained_response` | 243 | 57.6 | 89.7 | 3 (3 / 0) | 75 | 57.6 | 0 (0 / 0) | 0 |
| `detectable_format:json_format` | 266 | 82.0 | 82.0 | 0 (0 / 0) | 0 | 82.0 | 0 (0 / 0) | 0 |
| `detectable_format:multiple_sections` | 917 | 82.2 | 86.9 | 39 (37 / 2) | 8 | 85.1 | 4 (2 / 2) | 34 |
| `detectable_format:number_bullet_lists` | 1019 | 81.6 | 80.1 | 21 (3 / 18) | 0 | 81.6 | 0 (0 / 0) | 0 |
| `detectable_format:number_highlighted_sections` | 1070 | 92.7 | 93.4 | 9 (8 / 1) | 0 | 93.4 | 7 (7 / 0) | 0 |
| `detectable_format:sentence_hyphens` | 1300 | 52.5 | 19.6 | 14 (10 / 4) | 549 | 19.5 | 2 (2 / 0) | 435 |
| `detectable_format:square_brackets` | 1079 | 18.3 | 16.2 | 61 (12 / 49) | 27 | 95.2 | 665 (663 / 2) | 169 |
| `detectable_format:title` | 1189 | 96.6 | 97.1 | 11 (9 / 2) | 0 | 97.1 | 11 (9 / 2) | 0 |
| `first_word:first_word_answer` | 1089 | 84.7 | 72.2 | 69 (0 / 69) | 67 | 85.1 | 5 (5 / 0) | 2 |
| `first_word:first_word_sent` | 1024 | 41.3 | 32.3 | 44 (2 / 42) | 74 | 43.3 | 14 (14 / 0) | 24 |
| `keywords:existence` | 1856 | 68.8 | 75.6 | 4 (4 / 0) | 124 | 72.1 | 5 (4 / 1) | 59 |
| `keywords:forbidden_words` | 1687 | 96.7 | 96.6 | 1 (1 / 0) | 3 | 96.6 | 1 (1 / 0) | 3 |
| `keywords:frequency` | 1200 | 79.8 | 81.0 | 3 (3 / 0) | 60 | 80.9 | 3 (3 / 0) | 15 |
| `keywords:keyword_specific_position` | 1341 | 3.8 | 2.8 | 11 (3 / 8) | 15 | 3.7 | 7 (3 / 4) | 9 |
| `keywords:letter_frequency` | 1507 | 56.5 | 56.9 | 6 (6 / 0) | 0 | 56.9 | 6 (6 / 0) | 0 |
| `keywords:no_adjacent_consecutive` | 1499 | 23.8 | 23.7 | 58 (56 / 2) | 163 | 76.8 | 819 (787 / 32) | 103 |
| `keywords:palindrome` | 1165 | 73.3 | 90.3 | 53 (20 / 33) | 219 | 63.4 | 102 (6 / 96) | 49 |
| `keywords:start_end` | 989 | 29.9 | 29.6 | 12 (5 / 7) | 1 | 37.2 | 70 (57 / 13) | 30 |
| `keywords:word_count_different_numbers` | 1015 | 36.3 | 54.2 | 263 (146 / 117) | 233 | 54.2 | 262 (146 / 116) | 232 |
| `keywords:word_once` | 1808 | 72.3 | 25.5 | 803 (0 / 803) | 140 | 25.9 | 766 (0 / 766) | 101 |
| `language:response_language` | 1600 | 88.4 | 88.3 | 12 (5 / 7) | 0 | judge | - | - |
| `last_word:last_word_answer` | 1285 | 74.9 | 69.7 | 62 (0 / 62) | 5 | 76.0 | 15 (14 / 1) | 0 |
| `last_word:last_word_sent` | 1203 | 26.7 | 27.8 | 44 (14 / 30) | 35 | 33.3 | 45 (45 / 0) | 43 |
| `length_constraints:nth_paragraph_first_word` | 1048 | 38.0 | 38.7 | 15 (12 / 3) | 3 | 38.4 | 4 (4 / 0) | 0 |
| `length_constraints:number_paragraphs` | 1345 | 63.5 | 74.1 | 1 (0 / 1) | 188 | 42.4 | 426 (56 / 370) | 66 |
| `length_constraints:number_sentences` | 1131 | 73.1 | 70.5 | 76 (18 / 58) | 72 | 69.7 | 90 (21 / 69) | 71 |
| `length_constraints:number_words` | 1443 | 73.5 | 73.6 | 13 (7 / 6) | 17 | 70.5 | 68 (12 / 56) | 7 |
| `letters:letter_counting` | 961 | 66.1 | 61.7 | 5 (5 / 0) | 97 | judge | - | - |
| `letters:letter_counting2` | 1346 | 53.8 | 54.5 | 10 (10 / 0) | 0 | 54.5 | 10 (10 / 0) | 0 |
| `paragraphs:paragraphs` | 1150 | 72.3 | 83.5 | 0 (0 / 0) | 136 | 97.1 | 135 (135 / 0) | 150 |
| `paragraphs:paragraphs2` | 1391 | 62.5 | 62.5 | 0 (0 / 0) | 5 | 94.3 | 440 (440 / 0) | 2 |
| `punctuation:no_comma` | 1523 | 86.9 | 88.7 | 0 (0 / 0) | 27 | 88.7 | 0 (0 / 0) | 27 |
| `punctuation:punctuation_dot` | 1749 | 48.5 | 51.6 | 0 (0 / 0) | 55 | 51.6 | 0 (0 / 0) | 55 |
| `punctuation:punctuation_exclamation` | 1284 | 94.6 | 95.3 | 0 (0 / 0) | 9 | 95.3 | 0 (0 / 0) | 9 |
| `startend:end_checker` | 997 | 71.8 | 87.4 | 0 (0 / 0) | 169 | 68.3 | 0 (0 / 0) | 35 |
| `startend:quotation` | 810 | 86.4 | 85.9 | 0 (0 / 0) | 4 | 86.0 | 0 (0 / 0) | 3 |

## 7. Stress tests (step 4)

- Content-free responses on all 11,817 rows (SkyRL reward 1.0 / gate passes / replacement passes): empty
  1,702 / 810 / 0, with 625 more rows raising IndexError (F39); "." 1,144 / 682 / 530; "ok " repeated 200
  times 607 / 1,069 / 562; the row's own prompt as the answer 746 / 1,365 / 458. The replacement's passes
  are content-free texts that literally satisfy negative checks; whether they should is D-empty-response
  for empty text and otherwise a matter for the judge.
- Metamorphic edits on panel responses that all graders pass (bold, italics, HTML tag, typographic quotes,
  typographic apostrophe, punctuation after the first or last word; numbered label, bullet, blank line or
  trailing newline per line): the flips where the replacement still passes are in
  `audit/results/stress_tables.txt`. They repeat F12, F17, F19, F21, F24, F41 and give F45 and F46; the
  rest rest on D-markup-around-word, D-lowercase-counting-scope or D-paragraph-separator-count. A trailing
  newline changes no verdict.
- Fuzzing: 71,379 (check, kwargs, text) cases per grader. Exceptions only in NVIDIA
  `last_word:last_word_answer` on empty or whitespace text (F39). One exception stops nothing: the SkyRL
  session turns it into INFRA_ERROR with reward 0.0 for that response, the gate counts it as a failed check.
- Score-level transforms: neither pipeline has one (binary all-or-nothing reward; the gate's judge fraction
  is outside the case).
- Reference tests: NVIDIA's repository has no tests, and verifyit's tests are not in the case, so no test
  assertion could be listed.

## 8. Step 6: not run, and what the recommendation still needs from it

No reviewers were available, so no sample was drawn, frozen or rendered. The rule recorded in ISSUE.md
before any review: the recommendation to fix is confirmed if the replacement passes every fixture (true),
its scored coverage is complete (true), and a blinded review of held-out responses finds its error rate
lower than SkyRL's and the gate's, with a paired 95% interval that excludes zero. Step 6 must supply:

1. An error rate for each grader with an interval. Stratify by disagreement with the replacement: for
   SkyRL 5,503 disagreeing and 50,280 agreeing constraint verdicts; sample all or most disagreements and
   about 130 agreements per stratum that holds most of the population. Draw from the held-out responses,
   because the panel prompted contract change C3.
2. The reviewers' leans on the high-volume decisions (D-word-case, D-sentence-hyphens-*,
   D-lowercase-counting-scope, D-wcdn-relation, D-keyword-substring), which set how much of the
   replacement's score change the maintainers should adopt.
3. A check of the residual defects (44 verdicts) and of the semantic approximations (English and
   language detection), which this audit did not review case by case.

## 9. Reproduce

From `<W>/audit` in Git Bash:

```bash
export NLTK_DATA=<W>/case/deps/nltk_data PYTHONDONTWRITEBYTECODE=1
../.venv/Scripts/python.exe -m pytest tests -q -p no:cacheprovider      # fixtures: passed + xfailed, no failure
../.venv/Scripts/python.exe scripts/repro.py <fixture id>               # one counterexample, e.g.:
../.venv/Scripts/python.exe scripts/repro.py keywords:word_once:aa6ffee1a1e70878
../.venv/Scripts/python.exe scripts/repro.py F37    # also F38, F39, F44, G1
../.venv/Scripts/python.exe scripts/check_pins.py   # grader files match the pinned copies
../.venv/Scripts/python.exe scripts/grade_panel.py 4 && ../.venv/Scripts/python.exe scripts/analyze_panel.py 6 \
  && ../.venv/Scripts/python.exe scripts/analyze_extra.py && ../.venv/Scripts/python.exe scripts/stress.py
```

A rerun of the panel chain reproduces every verdict except the SkyRL verdicts on the 161 nth > num
constraint verdicts, which are random (F44); the decompressed panel file analysed here has sha256
`70403305e10a0d91385a0469f4a482070287d8f872aab9e12efc8cd35cf6b028` (the .gz hash also changes with its
timestamp).

`repro.py <fixture id>` prints the exact input, the contract label, and the verdicts of the NVIDIA checker
(as the SkyRL reward runs it), the verifyit check (as the gate runs it) and the replacement. For
`keywords:word_once:aa6ffee1a1e70878` it prints `NVIDIA/SkyRL: fail`, `verifyit gate: fail`,
`replacement: pass`, with the contract label `pass`. `repro.py F37` prints SkyRL reward `1.0` and gate
passed `True` for an unclosed `<think>` on the all-negative row `4b570a0b-5a79-402e-bf2e-24a961571521`;
`repro.py F44` prints a mix of `0.0` and `1.0` rewards for one response over 20 seeds.

## 10. Limitations

- The defect counts depend on the replacement implementing each reading faithfully. Sampled defect
  verdicts for every check with more than 10 were inspected (short excerpts via `scripts/show_cases.py`);
  that inspection led to contract change C3 and two implementation fixes, logged in ISSUE.md.
- English detection and `language:response_language` are semantic; the replacement approximates them
  with langdetect on code-stripped text plus a Latin-script share. F40 rests on clear cases (all-capital
  English rejected), not on that approximation's edges.
- The task-curation reward after the gate depends on the LLM judge, which is not in the case; a gate pass
  is not a reward of 1.0.
- Stored panel only: 4 models, one sampled run each (plus one greedy pair), no thinking-off/on pairs of
  the same model; no new responses were generated.
