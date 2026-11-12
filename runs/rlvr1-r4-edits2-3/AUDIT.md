# Audit of the RLVR1 instruction-following graders

Graders audited: SkyRL's reward for the 11,817 `instruction_following_simple_agent` rows
(`grade_instruction_following`, which runs NVIDIA's verifiable-instructions checkers; NVIDIA's
checkers are also the reference implementation) and the deterministic gate of Marin's
task-curation grader (verifyit `ifeval` checks, `convert_instruction_following` +
`grade_judge_candidate`). Record of the audit: `audit/ISSUE.md`. Contracts:
`audit/contracts.md`. Replacement grader: `audit/replacement/contract_grader.py`.

## 1. Error rate and effect on scores

**No blinded error rate exists yet: step 6 (the review) was not run in this exercise.** Every
"contradicted" number below compares a grader with the replacement grader, which implements
the contracts under the proposed reading of every decision entry. The replacement passes all
242 hand and fuzz fixtures and all 1,233 metamorphic and property cases, but no reviewer has
checked it on model responses, and its language checks (`english_capital`,
`english_lowercase`, `response_language`) are approximations built on langdetect.

Panel: the 23,315 stored responses in `case/panel/` (6 runs of 4 models; nothing generated).

| Run | n | SkyRL score | Contract score | Contract − SkyRL, points [95% CI] | Task-curation gate pass | Contract gate pass | Contract gate − TC gate [95% CI] |
|---|---|---|---|---|---|---|---|
| Qwen2.5-7B-Instruct sample0 | 4,000 | 20.05 | 20.55 | +0.50 [−0.55, +1.52] | 32.98 | 26.05 | −6.92 [−8.18, −5.73] |
| Qwen3-4B-Instruct-2507 sample0 | 11,817 | 29.51 | 32.80 | +3.29 [+2.70, +3.89] | 47.75 | 41.54 | −6.21 [−7.08, −5.35] |
| Qwen3-4B-Instruct-2507 greedy | 1,000 | 29.30 | 33.00 | +3.70 [+1.9, +5.6] | 49.90 | 41.20 | −8.70 [−11.4, −6.0] |
| Qwen3-4B-Instruct-2507 greedy_repeat | 1,000 | 29.50 | 33.10 | +3.60 [+1.7, +5.5] | 50.00 | 41.50 | −8.50 [−11.3, −5.8] |
| Qwen3-4B-Thinking-2507 (thinking) sample0 | 1,500 | 55.27 | 65.40 | +10.13 [+8.2, +12.13] | 63.40 | 68.53 | +5.13 [+3.07, +7.27] |
| OLMo-2-1124-7B-Instruct sample0 | 3,998 | 19.08 | 18.41 | −0.68 [−1.53, +0.15] | 32.02 | 24.36 | −7.65 [−8.95, −6.40] |

Scores are row-level and binary (every constraint passes), in percent. The task-curation reward
also depends on the LLM judge, which is not in the case, so its column is the gate: every
deterministic constraint passes. Intervals: paired bootstrap over responses, 2,000 resamples.
On the held-out half (fixed before any panel verdict was read; `audit/ISSUE.md`), the changes
are the same within their intervals (Qwen3-4B-Instruct sample0: +3.39 [+2.54, +4.23] and
−6.13 [−7.31, −4.94]; thinking: +9.06 and +3.70).

- Rerun: the greedy rerun returned a byte-identical response for 506 of 1,000 rows, and moved
  the SkyRL score by +0.2 points, the contract score by +0.1 and the gate by +0.1. Every score
  change in the table except Qwen2.5's and OLMo's SkyRL change is many times larger.
- False rewards (SkyRL as an RL reward): 944 of the 6,471 SkyRL rewards of 1.0 (14.6%) are
  contradicted by the contracts; 455 of them by a checker defect that no decision entry
  explains, 479 only by decision entries, and 10 by extraction (9 answers graded as empty
  text, 1 unclosed reasoning). Held-out half: 459 of 3,252 (14.1%). SkyRL also gives 0.0 to
  1,549 responses that satisfy every contract.
- Task-curation gate: 3,043 of its 10,192 passes (29.9%) contain a deterministic constraint
  that the contract fails (held-out 29.3%), and it blocks 1,631 responses that satisfy every
  deterministic contract (reward 0.0 without calling the judge).
- Scored coverage: complete for both graders. Every row converts (`resolve_checks` accepts all
  47 ids) and every constraint gets a SkyRL verdict; the task-curation gate leaves 5,020 of
  55,433 constraint verdicts to the judge (the four judged ids), by design. One panel row got
  a SkyRL INFRA_ERROR (finding G3).

## 2. Recommendation

**Fix both graders; do not admit either as is.** Both contradict the instruction text on
large, systematic classes of responses (findings below), and the gate's errors are mostly
inverted or unrelated checks (T1 to T6). The replacement grader is the proposed basis for the
fix, but the recommendation to adopt it still needs step 6: a blinded two-reviewer review of a
frozen, stratified sample (strata: replacement agrees / disagrees with each grader; all or most
disagreements), drawn from the held-out half, with the decision rule recorded in the issue
before the review (proposed: the replacement passes every fixture, coverage is complete, and
its error rate is lower than each grader's with a paired 95% interval that excludes zero; plus
reviewer verdicts on the language-detection checks, where the replacement is approximate).
Independently of the grader, fix or drop the data rows listed in G4, G5, G6 and G8, and decide
the decision entries in section 5.

## 3. How to reproduce a verdict

Every finding gives an exact input and a command. Run them in Git Bash:

```bash
cd <W>/audit
export NLTK_DATA=../case/deps/nltk_data PYTHONDONTWRITEBYTECODE=1
P=../.venv/Scripts/python.exe
```

`repro.py <instruction_id> '<kwargs JSON>' '<response as a JSON string>' [--reasoning] [--prompt '<JSON string>']`
grades one constraint with SkyRL (after `final_answer_text`), the task-curation gate (after
`_answer_text`) and the contract, and prints `skyrl=… task_curation=… contract=…`. The JSON
string form keeps `\n` exact. `audit/scripts/check_report_commands.py` runs every command in
this file and compares the output with the line after it.

## 4. Findings

Ids: G = pipeline, data and protocol; S = NVIDIA checker as SkyRL runs it (SkyRL runs the
reference, so its status in the reference is always "same"); T = verifyit check in the
task-curation gate (reference status = NVIDIA's verdict on the same input). Panel counts are
constraint verdicts on the 23,315 stored responses where the grader and the contract disagree;
"[n not explained]" counts the disagreements that neither one decision entry's other reading
nor all other readings together explain (`audit/panel/summary.json`, `per_check`).

### Pipeline, data and protocol

**G1. Extraction drops a non-reasoning answer that contains `<think>`** (both graders; SkyRL
`final_answer_text`, task curation `_answer_text`). An answer that wraps words in double angle
brackets writes `<<think>>`, which contains `<think>`; the extraction treats it as an unfinished
reasoning block and grades the empty string, which passes every negative check (no commas, no
dots, forbidden words, the language check). Contract G1: a non-reasoning model's whole response
is the graded text. Panel: 14 non-reasoning answers and 1 thinking answer (after `</think>`)
were graded as empty; 7 of them got SkyRL reward 1.0 and 6 passed the gate.

```bash
$P repro.py punctuation:no_comma '{}' '"I <<think>> this works, yes."'
```
Prints `skyrl=pass task_curation=pass contract=fail`.

**G2. Unclosed reasoning is graded as the answer** (both graders). Qwen3-4B-Thinking's
template supplies `<think>`, so a response cut off before `</think>` has no marker at all and
both extractions grade the reasoning text. Contract G1: extraction failure, every check fails.
Panel: 139 of 1,500 thinking responses (9.3%); 1 got SkyRL reward 1.0 and 18 passed the gate.
A response that keeps its opening `<think>` is graded as empty text instead (G3, content-free).

```bash
$P repro.py punctuation:no_comma '{}' '"Okay let me think about this answer and plan it"' --reasoning
```
Prints `skyrl=pass task_curation=pass contract=fail`.

**G3. `last_word:last_word_answer` raises on empty graded text** (SkyRL only).
`value.split()[-1]` raises IndexError; SkyRL turns any checker error into INFRA_ERROR with
reward 0.0 for the whole row, so every empty or extraction-dropped answer on the 625 rows with
this constraint is reported as an infrastructure error. Fuzzing: 464 of 30,000 random samples
(30 without reasoning markers); the only exception type in either grader. Panel: 1 row.

```bash
$P repro.py last_word:last_word_answer '{"last_word":"limit"}' '""'
```
Prints `skyrl=EXCEPTION IndexError: list index out of range (row reward 0.0, INFRA_ERROR) task_curation=fail contract=fail`.

**G4. Nondeterministic SkyRL verdicts on 77 contradictory rows** (data + NVIDIA
`ParagraphFirstWordCheck`). In 77 rows `nth_paragraph` exceeds `num_paragraphs` (the prompt
says, for example, "There should be 3 paragraphs … Paragraph 4 must start with word
feedback"); the contract can never pass. `build_description` then redraws the index with
`random.randint(1, num_paragraphs + 1)` on every grading, so the same response passes or fails
at random. Two identical gradings of the panel differed on 16 verdicts. `instruction_references.py`
and `build_instruction` patch only the missing-index case.

```bash
for i in 1 2 3 4 5 6 7 8 9 10; do $P repro.py length_constraints:nth_paragraph_first_word '{"num_paragraphs":3,"nth_paragraph":4,"first_word":"feedback"}' '"Intro.\n\nFeedback here.\n\nEnd."'; done | sort | uniq -c
```
Prints two lines, `skyrl=fail …` and `skyrl=pass task_curation=fail contract=fail`, with
counts that change from run to run (8 and 2 in the recorded run).

**G5. The prompt shows `P.S` but both graders require `P.S.`** (data rendering). In 147 of
the 324 rows whose kwarg is `P.S.`, the inline joining of requirements drops the period, so
the model reads "postscript starting with P.S". A postscript that starts with `P.S:` follows
the text and fails both graders. Panel: on these rows, 93 SkyRL and 100 gate verdicts fail a
postscript that the contract passes.

```bash
$P repro.py detectable_content:postscript '{"postscript_marker":"P.S."}' '"Thanks for reading.\n\nP.S: Remember to rest."' --prompt '"Please ensure your answer follows these guidelines: In your entire response, refrain from the use of any commas and At the end of your response, please explicitly add a postscript starting with P.S"'
```
Prints `skyrl=fail task_curation=fail contract=pass`.

**G6. `keywords:word_count_different_numbers` grades a relation the model never sees** (both
graders, data). All 526 rows say "the word X should appear N times"; the kwargs carry
"at least" (320) or "less than" (206), and both graders apply it. A response with exactly N
occurrences fails every "less than" row; a response with none passes every "less than" row.
Panel: SkyRL 336 false passes and 158 false fails of 1,012 verdicts [297 and 117 not
explained]; the gate the same within a few verdicts.

```bash
$P repro.py keywords:word_count_different_numbers '{"keyword":"tree","relation":"less than","frequency":2}' '"A tree and another tree."'
$P repro.py keywords:word_count_different_numbers '{"keyword":"tree","relation":"less than","frequency":2}' '"A tree here."'
```
Print `skyrl=fail task_curation=fail contract=pass` and `skyrl=pass task_curation=pass contract=fail`.

**G7. Unpinned or unverified inputs.** (a) `_ensure_nltk_data` downloads `punkt_tab` at run
time when it is missing, with no version or hash; NLTK data has no version. (b) The RL run's
chat template, output budget and reasoning parser are not in any stored record of the case.
(c) `NemotronTaskSession` raises unless `route` is `task_session`, but all 11,817 rows say
`skyrl_gym`; the code that lowers these rows (and any `skyrl_gym`-route environment) is not in
the case, so which code grades them in training is unverified. (d) `verifyit_enabled`
(default false) would switch SkyRL to `grade_nemotron_instructions`, a third variant; the
run's value is unverified. Locations and verification commands: `audit/ISSUE.md`, step 1.

**G8. Rows that no response can pass under the contract** (data). `english_lowercase` +
`end_checker` (48 rows: the end phrases contain capitals and the text says "exact phrase"),
`english_capital` + `end_checker` (45 rows), and the 77 rows of G4. Under D-end-case's other
reading the first 93 become satisfiable; SkyRL already grades the end phrase case-insensitively.
The lower-case phrase fails the end check, and the exact phrase fails the lower-case check:

```bash
$P repro.py startend:end_checker '{"end_phrase":"Any other questions?"}' '"here is my answer. any other questions?"'
$P repro.py change_case:english_lowercase '{}' '"here is my answer. Any other questions?"'
```
Print `skyrl=pass task_curation=fail contract=fail` and `skyrl=fail task_curation=fail contract=fail`.

**G9. Content-free responses** (step 4; `audit/content_free.json`). An empty response gets
SkyRL reward 1.0 on 1,702 of 11,817 rows (14.4%) and is an INFRA_ERROR on 625; the contract
passes it on 587 rows (rows whose constraints are all negative, such as "no commas"). Checks
the empty response passes in SkyRL but not under the contract: `response_language` (780 of 780:
`LangDetectException` counts as followed), `sentence_hyphens`, `square_brackets`,
`bigram_wrapping`, `first_word_sent`, `last_word_sent` (all vacuous; decision D-empty-each).
Echoing the prompt back gets SkyRL 1.0 on 746 rows, the gate on 1,365 and the contract on 458:
the prompt itself contains the title example `<<poem of joy>>`, the keyword lists and the three
constrained options. The gate passes the empty response on 810 rows and then asks the judge.
Reproduce the row counts with `$P scripts/content_free.py` (about two minutes; writes
`content_free.json`), and one of the vacuous passes with:

```bash
$P repro.py first_word:first_word_sent '{"first_word":"we"}' '""'
```
Prints `skyrl=pass task_curation=fail contract=fail`.

### NVIDIA checkers as SkyRL runs them

| Id | Check | Defect | Exact counterexample (kwargs; response) | Grader / contract | Panel disagreements |
|---|---|---|---|---|---|
| S1 | `keywords:word_once` | Requires exactly one occurrence; the text says "Include keyword X" | `{"keyword":"garden"}`; `"The garden is green. I love the garden."` | fail / pass | 895 false fails [803] |
| S2 | `copy:repeat_phrase` | Only the last match's difference count is checked, so an unchanged copy before a variant passes | `{"phrase":"Live each day to the fullest","small_n":2}`; `"Live each day to the fullest. Live each moment to the fullest."` | pass / fail | 53 false passes [51] |
| S3 | `count:count_unique` | Punctuation tokens count as words | `{}`; `"Apples, pears, plums."` | fail / pass | 108 false fails [91] |
| S4 | `detectable_format:bigram_wrapping` | Only checks that tokens at even positions start with `<<` and the next ends with `>>`: single-word groups pass, a final period fails | `{}`; `"<<I am>> <<at home>>."` | fail / pass | 185 false passes [185] |
| S5 | `detectable_content:postscript` | The marker anywhere, even mid-sentence or inside `P.P.S.`, counts | `{"postscript_marker":"P.S."}`; `"Thanks for reading.\n\nP.P.S. Remember to rest."` | pass / fail | 130 false passes [59] |
| S6 | `detectable_format:multiple_sections` | Counts at least N, not N, and counts mentions | `{"num_sections":2,"section_spliter":"SECTION"}`; `"SECTION 1\nIntro.\nSECTION 2\nMore.\nSECTION 3\nEven more."` | pass / fail | 66 false passes [66] |
| S7 | `first_word:first_word_answer` (also `first_word_sent`, `nth_paragraph_first_word`) | Punctuation attached to the first word makes it a different word | `{"first_word":"development"}`; `"development, as a concept, matters."` | fail / pass | 136 [67], 103 [42], 5 false fails |
| S8 | `keywords:keyword_specific_position` | Commas and periods count as words | `{"keyword":"main","n":2,"m":3}`; `"First, sentence here. Yes, the main point."` | fail / pass | 19 false fails [9] |
| S9 | `keywords:no_adjacent_consecutive` | Compares code points of any first character: digits, punctuation and CJK fail | `{}`; `"Steps 1 2 3 follow."` | fail / pass | 27 false fails [25] |
| S10 | `keywords:palindrome` | A punctuation token is a palindrome; case and attached punctuation break real ones | `{}`; `"It costs five dollars - not much."` | pass / fail | 241 false passes [15], 33 false fails [30] |
| S11 | `detectable_format:number_bullet_lists` | Counts `---` and `* * *` rules and lines starting with `-5` as bullets | `{"num_bullets":3}`; `"* one\n* two\n* three\n\n---\nDone."` | fail / pass | 18 false fails [18] |
| S12 | `detectable_format:square_brackets` | Punctuation after a bracketed word fails; unspaced scripts pass as one token | `{}`; `"[Hello] [world]."` | fail / pass | 53 false fails [41], 23 false passes [12] |
| S13 | `detectable_format:sentence_hyphens` | A hyphenated word inside a sentence fails | `{}`; `"The well-known sun rose.-Birds sang."` | fail / pass | 489 false fails [7], 69 false passes [69] |
| S14 | `combination:two_responses` | A separator at the start or end, or inside a longer run of asterisks, still counts | `{}`; `"******\nAnswer one.\n******\nAnswer two."` | pass / fail | 30 false passes [30] |
| S15 | `detectable_content:number_placeholders` | `[]` counts as a placeholder | `{"num_placeholders":2}`; `"Dear [], your order [ ] shipped."` | pass / fail | 1 |
| S16 | `detectable_format:constrained_response` | Two different options pass | `{}`; `"My answer is yes. My answer is no."` | pass / fail | 3 |
| S17 | `detectable_format:number_highlighted_sections` | `2 * 3 * 4` is a highlight | `{"num_highlights":1}`; `"Compute 2 * 3 * 4 here."` | pass / fail | 7 false passes [7] |
| S18 | `language:response_language` | Empty text passes (`LangDetectException` → followed) | `{"language":"fr"}`; `""` | pass / fail | reachable through G1/G2; 780 of 780 rows on empty text |
| S19 | `length_constraints:number_words` | `\w+` splits contractions and Indic vowel signs | `{"relation":"less than","num_words":3}`; `"Don't stop."` | fail / pass | 15 false fails [11] |
| S20 | `length_constraints:number_sentences`, `last_word:last_word_sent` | Sentence splitting ignores `。`, so a Chinese answer is one sentence | `{"relation":"at least","num_sentences":3}`; `"第一句话。第二句话。第三句话。"` and `{"last_word":"end"}`; `"这是第一句。这是第二句 end。"` | fail / pass and pass / fail | 89 false fails [58], 55 false passes [14]; 47 [16] / 33 [12] |
| S21 | `count:counting_composition` | Splits at `***`, but the text's divider is `* * *` (1 row) | `{"n_sent":3,"n_words":2}`; three 3-sentence paragraphs of 2-word sentences split by `* * *` | fail / pass | 0 (1 row) |
| S22 | `change_case:english_capital` | langdetect on upper-case English often returns another language (suspected; needs review, the contract side is also langdetect) | `{}`; `"SESSION OF SIGNIFICANCE: HOWARD MOVES TO ATLANTIC SUN"` (an OLMo panel answer) | fail / pass | 80 false fails, 21 false passes |

Commands for the table rows (each prints the two verdicts in the "Grader / contract" column, and
the task-curation verdict):

```bash
$P repro.py keywords:word_once '{"keyword":"garden"}' '"The garden is green. I love the garden."'
```
Prints `skyrl=fail task_curation=fail contract=pass`.
```bash
$P repro.py copy:repeat_phrase '{"phrase":"Live each day to the fullest","small_n":2}' '"Live each day to the fullest. Live each moment to the fullest."'
```
Prints `skyrl=pass task_curation=fail contract=fail`.
```bash
$P repro.py count:count_unique '{}' '"Apples, pears, plums."'
```
Prints `skyrl=fail task_curation=judged contract=pass`.
```bash
$P repro.py detectable_format:bigram_wrapping '{}' '"<<I am>> <<at home>>."'
```
Prints `skyrl=fail task_curation=judged contract=pass`.
```bash
$P repro.py detectable_content:postscript '{"postscript_marker":"P.S."}' '"Thanks for reading.\n\nP.P.S. Remember to rest."'
```
Prints `skyrl=pass task_curation=fail contract=fail`.
```bash
$P repro.py detectable_format:multiple_sections '{"num_sections":2,"section_spliter":"SECTION"}' '"SECTION 1\nIntro.\nSECTION 2\nMore.\nSECTION 3\nEven more."'
```
Prints `skyrl=pass task_curation=fail contract=fail`.
```bash
$P repro.py first_word:first_word_answer '{"first_word":"development"}' '"development, as a concept, matters."'
```
Prints `skyrl=fail task_curation=pass contract=pass`.
```bash
$P repro.py keywords:keyword_specific_position '{"keyword":"main","n":2,"m":3}' '"First, sentence here. Yes, the main point."'
```
Prints `skyrl=fail task_curation=pass contract=pass`.
```bash
$P repro.py keywords:no_adjacent_consecutive '{}' '"Steps 1 2 3 follow."'
```
Prints `skyrl=fail task_curation=pass contract=pass`.
```bash
$P repro.py keywords:palindrome '{}' '"It costs five dollars - not much."'
```
Prints `skyrl=pass task_curation=fail contract=fail`.
```bash
$P repro.py detectable_format:number_bullet_lists '{"num_bullets":3}' '"* one\n* two\n* three\n\n---\nDone."'
```
Prints `skyrl=fail task_curation=pass contract=pass`.
```bash
$P repro.py detectable_format:square_brackets '{}' '"[Hello] [world]."'
```
Prints `skyrl=fail task_curation=pass contract=pass`.
```bash
$P repro.py detectable_format:sentence_hyphens '{}' '"The well-known sun rose.-Birds sang."'
```
Prints `skyrl=fail task_curation=fail contract=pass`.
```bash
$P repro.py combination:two_responses '{}' '"******\nAnswer one.\n******\nAnswer two."'
```
Prints `skyrl=pass task_curation=pass contract=fail`.
```bash
$P repro.py detectable_content:number_placeholders '{"num_placeholders":2}' '"Dear [], your order [ ] shipped."'
```
Prints `skyrl=pass task_curation=fail contract=fail`.
```bash
$P repro.py detectable_format:constrained_response '{}' '"My answer is yes. My answer is no."'
```
Prints `skyrl=pass task_curation=fail contract=fail`.
```bash
$P repro.py detectable_format:number_highlighted_sections '{"num_highlights":1}' '"Compute 2 * 3 * 4 here."'
```
Prints `skyrl=pass task_curation=pass contract=fail`.
```bash
$P repro.py language:response_language '{"language":"fr"}' '""'
```
Prints `skyrl=pass task_curation=judged contract=fail`.
```bash
$P repro.py length_constraints:number_words '{"relation":"less than","num_words":3}' "\"Don't stop.\""
```
Prints `skyrl=fail task_curation=pass contract=pass`.
```bash
$P repro.py count:counting_composition '{"n_sent":3,"n_words":2}' '"Cats sleep. Dogs bark. Birds sing.\n* * *\nFish swim. Frogs jump. Bees buzz.\n* * *\nKids play. Adults work. Elders rest."'
```
Prints `skyrl=fail task_curation=pass contract=pass`.
```bash
$P repro.py length_constraints:number_sentences '{"relation":"at least","num_sentences":3}' '"第一句话。第二句话。第三句话。"'
```
Prints `skyrl=fail task_curation=fail contract=pass`.
```bash
$P repro.py last_word:last_word_sent '{"last_word":"end"}' '"这是第一句。这是第二句 end。"'
```
Prints `skyrl=pass task_curation=pass contract=fail`.
```bash
$P repro.py change_case:english_capital '{}' '"SESSION OF SIGNIFICANCE: HOWARD MOVES TO ATLANTIC SUN"'
```
Prints `skyrl=fail task_curation=pass contract=pass`.

### verifyit checks in the task-curation gate

| Id | Check | Defect | Exact counterexample (kwargs; response) | Gate / contract / NVIDIA | Panel disagreements |
|---|---|---|---|---|---|
| T1 | `keywords:no_adjacent_consecutive` | Checks adjacent duplicate words, not consecutive first letters | `{}`; `"Apple banana cherry."` | pass / fail / fail | 921 false passes [767], 37 false fails [32] |
| T2 | `count:lowercase_counting` | Requires at least N lower-case words: inverted | `{"N":2}`; `"the the the end"` | pass / fail / fail | 1,167 false passes [1,167], 172 false fails [150] |
| T3 | `detectable_format:square_brackets` | Passes when any one `[...]` exists | `{}`; `"Hello [world]"` | pass / fail / fail | 814 false passes [655] |
| T4 | `length_constraints:number_paragraphs` | Splits at blank lines and ignores the `***` divider the text asks for | `{"num_paragraphs":2}`; `"First paragraph.\n\n***\n\nSecond paragraph."` | fail / pass / pass | 388 false fails [370], 104 false passes [56] |
| T5 | `paragraphs:paragraphs`, `paragraphs:paragraphs2` | At least 2 paragraphs, by either separator; the text says 2, by one named separator | `{}`; `"One.\n\nTwo.\n\nThree."` (paragraphs2) | pass / fail / fail | 279 [130], 437 [435] false passes |
| T6 | `copy:repeat_phrase` | Counts unchanged copies, at least n; transformed repetitions fail | `{"phrase":"Live each day to the fullest","small_n":2}`; `"Live each moment to the fullest. Live each day for the fullest."` | fail / pass / pass | 477 false passes [454], 47 false fails [31] |
| T7 | `detectable_format:sentence_hyphens` | Requires each sentence to have no spaces at all, so the canonical answer fails | `{}`; `"The sun rose.-Birds sang.-We woke."` | fail / pass / pass | 426 false fails [2] (most also hinge on D-hyphen-single) |
| T8 | `keywords:word_once` | Exactly once (as S1) | `{"keyword":"garden"}`; `"The garden is green. I love the garden."` | fail / pass / fail | 853 false fails [766] |
| T9 | `change_case:english_capital`, `english_lowercase` | No English check | `{}`; `"ESTO ES MI RESPUESTA EN ESPAÑOL Y NO EN INGLÉS PORQUE ASÍ LO QUIERO."` | pass / fail / fail | 99 and 121 false passes (approximate, as S22) |
| T10 | `keywords:start_end` | Ignores punctuation after the last word; the text forbids it | `{}`; `"Hello there, I say hello."` | pass / fail / fail | 55 false passes [55] |
| T11 | `detectable_format:multiple_sections` | Counts case-insensitive mentions anywhere | `{"num_sections":2,"section_spliter":"SECTION"}`; `"SECTION 1\nIntro, as SECTION 2 explains later.\nSECTION 2\nMore."` | fail / pass / pass | 36 false passes [36] |
| T12 | `length_constraints:number_sentences` | Splits after abbreviations | `{"relation":"less than","num_sentences":3}`; `"Dr. Smith arrived. He sat."` | fail / pass / pass | 100 false fails [69], 57 false passes [16] |
| T13 | `length_constraints:number_words` (also first/last word, start_end) | Words are ASCII only; a lone `-` is a word | `{"relation":"at least","num_words":5}`; `"我们 今天 去 公园 玩。"` | fail / pass / pass | 60 false fails [58] |
| T14 | `keywords:palindrome` | Dashes and digits form palindromes; an apostrophe attaches to the word | `{}`; `"'level"` | fail / pass / fail | 121 false fails [117] |
| T15 | `startend:quotation` | Single quotation marks pass | `{}`; `"'Hello world.'"` | pass / fail / fail | 0 |
| T16 | `detectable_format:json_format` | A ```` ```JSON ```` fence is not removed | `{}`; `"```JSON\n{\"a\": 1}\n```"` | fail / pass / pass | 0 |
| T17 | `detectable_format:title` | `<< >>` is a title | `{}`; `"<< >>\nRoses are red."` | pass / fail / fail | 0 |
| T18 | `count:counting_composition` | No paragraph count, "at least" instead of exactly | `{"n_sent":3,"n_words":2}`; two paragraphs only | pass / fail / fail | 0 (1 row) |
| T19 | `combination:two_responses` | As S14 (same split rule) | as S14 | pass / fail / pass | 30 false passes [30] |

```bash
$P repro.py keywords:no_adjacent_consecutive '{}' '"Apple banana cherry."'
```
Prints `skyrl=fail task_curation=pass contract=fail`.
```bash
$P repro.py count:lowercase_counting '{"N":2}' '"the the the end"'
```
Prints `skyrl=fail task_curation=pass contract=fail`.
```bash
$P repro.py detectable_format:square_brackets '{}' '"Hello [world]"'
```
Prints `skyrl=fail task_curation=pass contract=fail`.
```bash
$P repro.py length_constraints:number_paragraphs '{"num_paragraphs":2}' '"First paragraph.\n\n***\n\nSecond paragraph."'
```
Prints `skyrl=pass task_curation=fail contract=pass`.
```bash
$P repro.py paragraphs:paragraphs2 '{}' '"One.\n\nTwo.\n\nThree."'
```
Prints `skyrl=fail task_curation=pass contract=fail`.
```bash
$P repro.py copy:repeat_phrase '{"phrase":"Live each day to the fullest","small_n":2}' '"Live each moment to the fullest. Live each day for the fullest."'
```
Prints `skyrl=pass task_curation=fail contract=pass`.
```bash
$P repro.py detectable_format:sentence_hyphens '{}' '"The sun rose.-Birds sang.-We woke."'
```
Prints `skyrl=pass task_curation=fail contract=pass`.
```bash
$P repro.py change_case:english_capital '{}' '"ESTO ES MI RESPUESTA EN ESPAÑOL Y NO EN INGLÉS PORQUE ASÍ LO QUIERO."'
```
Prints `skyrl=fail task_curation=pass contract=fail`.
```bash
$P repro.py keywords:start_end '{}' '"Hello there, I say hello."'
```
Prints `skyrl=fail task_curation=pass contract=fail`.
```bash
$P repro.py detectable_format:multiple_sections '{"num_sections":2,"section_spliter":"SECTION"}' '"SECTION 1\nIntro, as SECTION 2 explains later.\nSECTION 2\nMore."'
```
Prints `skyrl=pass task_curation=fail contract=pass`.
```bash
$P repro.py length_constraints:number_sentences '{"relation":"less than","num_sentences":3}' '"Dr. Smith arrived. He sat."'
```
Prints `skyrl=pass task_curation=fail contract=pass`.
```bash
$P repro.py length_constraints:number_words '{"relation":"at least","num_words":5}' '"我们 今天 去 公园 玩。"'
```
Prints `skyrl=pass task_curation=fail contract=pass`.
```bash
$P repro.py keywords:palindrome '{}' "\"'level\""
```
Prints `skyrl=fail task_curation=fail contract=pass`.
```bash
$P repro.py startend:quotation '{}' "\"'Hello world.'\""
```
Prints `skyrl=fail task_curation=pass contract=fail`.
```bash
$P repro.py detectable_format:json_format '{}' '"```JSON\n{\"a\": 1}\n```"'
```
Prints `skyrl=pass task_curation=fail contract=pass`.
```bash
$P repro.py detectable_format:title '{}' '"<< >>\nRoses are red."'
```
Prints `skyrl=fail task_curation=pass contract=fail`.
```bash
$P repro.py count:counting_composition '{"n_sent":3,"n_words":2}' '"Cats sleep. Dogs bark. Birds sing.\n* * *\nFish swim. Frogs jump. Bees buzz."'
```
Prints `skyrl=fail task_curation=pass contract=fail`.

### Reference comparison (task-curation gate against NVIDIA, step 4)

On the panel, the gate and NVIDIA disagree on 7,774 of the 50,413 constraint verdicts both
give. Against the contract: verifyit is wrong in 5,533 (4,776 not explained by any decision),
NVIDIA in 2,241 (688 not explained). The largest verifyit-side counts are
`lowercase_counting` (1,302), `no_adjacent_consecutive` (795), `square_brackets` (644),
`repeat_phrase` (481), `paragraphs2` (435) and `number_paragraphs` (425); the largest
NVIDIA-side counts are `palindrome` (213, mostly one-letter words, D-palindrome-length),
`end_checker` (190, D-end-case/D-end-trailing) and `lowercase_counting` (272,
D-lowercase-counting). Per check: `audit/panel/summary.json`, keys `ref_comparison: …`.

## 5. Decision entries (for the maintainers)

The text allows two verdicts in each; the proposed reading is the replacement's default, and
each is one switch in `Readings`. "Flipped" is the number of panel constraint verdicts that the
other reading changes (`decision_effects` in `audit/panel/summary.json`); "SkyRL / TC" says
which reading each grader follows where it matters.

| Entry | Question | Proposed | Other reading | Flipped | SkyRL / TC |
|---|---|---|---|---|---|
| D-word-case | Compare named words case-insensitively? | yes | exact case | 1,214 | case-insensitive except keyword_specific_position, repeat_phrase / insensitive |
| D-hyphen-single | One sentence satisfies sentence_hyphens? | yes | no | 667 | yes / no |
| D-keyword-boundary | Keyword inside a longer word counts? | no | yes | 415 | substring (existence, frequency, word_once, wcdn); whole word (forbidden) / whole word |
| D-word-unspaced | Unspaced script: run = one word? | yes | each character | 312 | run / ASCII only |
| D-lowercase-counting | "all lowercase words at most N times": per word? | per word | total | 308 | total / neither (T2) |
| D-markup-transparent | Markup or tags around a word change it? | no | yes | 308 | yes for first word, start_end, no_adjacent / mostly no |
| D-word-hyphen | `well-known` one word? | one | two | 280 | two (count_words) / one |
| D-palindrome-length | Minimum palindrome length | 3 letters | 1 | 232 | 1 (any token) / 3 |
| D-divider-line | `***` must stand on its own line? | yes | anywhere | 178 | anywhere / blank lines (T4) |
| D-sentence-lines | Line break ends a sentence? | yes | no | 176 | no / no |
| D-end-case | End phrase case-sensitive? | yes | no | 161 | no / yes |
| D-divider-empty | Empty piece at start/end fails? | yes | ignored | 160 | ignored / — |
| D-bracket-group | `[Hello world]` encloses both words? | no | yes | 158 | no / yes |
| D-letter-case | "the letter m" counts `M`? | yes | no | 119 | yes / yes |
| D-letter-def | Letters of any script count? | yes | Latin only | 96 | Latin / judged |
| D-capital-single | `I`, `A` are all-capital words? | yes | 2+ letters | 84 | yes / no |
| D-postscript-end | Postscript must end the response? | yes | anywhere | 76 | anywhere / anywhere |
| D-constrained-extra | Text around the option allowed? | yes | option alone | 75 | yes / no |
| D-postscript-case | `p.s.` counts? | yes | exact | 60 | yes / yes |
| D-highlight-bold | `**bold**` is a highlight? | yes | italic only | 59 | yes / yes |
| D-section-preamble | Text before the first header allowed? | yes | no | 54 | yes / yes |
| D-consecutive-order | `b` then `a` consecutive? | yes | ascending only | 54 | ascending / — |
| D-end-trailing | Punctuation or quotes may follow the end phrase? | no | yes | 43 | strips `"` / no |
| D-start-end-single | One-word response starts and ends with the same word? | yes | no | 42 | no / yes |
| D-repeat-original | Unchanged copy fails repeat_phrase? | yes | ignored | 30 | — / counts copies |
| D-comma-unicode | `，` `、` `،` are commas? | yes | `,` only | 27 | `,` only / `,` only |
| D-section-case | `Section 1` marks a `SECTION` section? | yes | exact | 22 | exact / insensitive |
| D-repeat-center | Any inner word may be replaced? | yes | middle only | 15 | any / — |
| D-empty-each | No sentence/word fails "each/every"? | yes | vacuous pass | 11 | vacuous / mixed |
| D-title-position | Title anywhere? | yes | first line | 10 | anywhere / anywhere |
| D-exclamation-unicode, D-dot-unicode | Full-width and other forms count? | yes | ASCII only | 9, 1 | ASCII / ASCII |
| D-unique-case | `The`/`the` the same word? | yes | no | 8 | no / judged |
| D-paragraph-blank-lines | Run of blank lines (with spaces) one separator? | yes | exactly `\n\n` | 7 | exactly `\n\n` / any |
| D-bullet-markers, D-bullet-nested | `+`/`-` and nested bullets count? | yes | `*` only, top level | 6, 4 | `*` and `-` / `*` and `-` |
| D-list-label | List labels (`1.`, `-`) are not words or sentences? | yes | they are | 5 | they are / they are |
| D-quotation-typographic | `“ ”` are double quotation marks? | yes | `"` only | 4 | `"` only / both (and single) |
| D-postscript-line | Postscript may start after a sentence end on the same line? | yes | line start only | — | anywhere / line start |
| D-consecutive-script | Greek and Cyrillic alphabets count? | yes | Latin only | — | any code point / — |
| D-two-separator, D-json-scalar, D-placeholder, D-bigram-odd, D-section-markup, D-empty-english, D-start-end-trailing | see `audit/contracts.md` | | | 0 to 2 each | |

## 6. Steps and what was not done

- Step 1: inputs pinned in `audit/ISSUE.md` (manifest verified, per-row hashes in
  `audit/frozen/row_hashes.tsv`, sha256 `af6e8ed3…2997`). The HF dataset revision and the RL
  run's generation settings could not be fetched offline (listed as unverified).
- Step 2: `audit/contracts.md` written from the prompts before any code was read (sha256
  `08406d2a…a298`, 09:34 UTC); later changes and new decision entries are listed with reasons in
  `audit/ISSUE.md` and appended to the contract file.
- Step 3: 242 labeled fixtures (225 hand-written, 17 fuzz minima) plus 1,233 metamorphic and
  property cases, all in `audit/fixtures.jsonl` (1,475 lines) and run by
  `audit/tests/test_fixtures.py` with `xfail(strict=True)` marks for the 540 SkyRL and 355
  task-curation verdicts that contradict their label. No repository, research branch or PR:
  the tests live under `audit/tests/` instead.
- Step 4: reference comparison above; NVIDIA has no unit tests, and verifyit's tests are not in
  the case, so no test assertions could be listed. Metamorphic edits (numbered label, bullet,
  bold/italic/HTML/typographic quotes on the first and last word, typographic apostrophe,
  punctuation after a word, blank lines, trailing newline) caused 77 SkyRL and 72 gate verdicts
  to go wrong on bases each grader had right (`audit/property_summary.json`). Fuzzing: 30,000
  samples with and 30,000 without reasoning markers (`audit/fuzz_results*.json`); one exception
  type (G3). Content-free: G9.
- Step 5: stored panel only (no compute), graded by all three graders
  (`audit/panel/verdicts.jsonl`, `summary.json`, `extra_counts.json`). Stored records show 1,063
  truncated responses (`finish_reason` length) and 139 unclosed thinking responses; both
  graders grade truncated text as is.
- Step 6: **not run** (no reviewers). No sample drawn, frozen or rendered. See section 2 for what
  the recommendation needs from it.
- Records: no issue tracker (`audit/ISSUE.md` stands in), no Hugging Face artifact, no job
  launcher; frozen files are under `audit/frozen/` with hashes in the issue file.
