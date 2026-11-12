# Audit of the RLVR1 instruction-following graders

Written 2026-11-12T11:08Z (UTC), revised at the end of the session (see section 8). Graders under
audit, on the 11,817 instruction-following rows of `open-athena/Nemotron-RL-Ultra-RLVR1-Cleaned-v3`
(28,219 constraints, 47 instruction ids):

- **A, the SkyRL reward**: `final_answer_text`, then `grade_instruction_following`, which runs
  NVIDIA's verifiable-instructions checkers (`f46a5ac`) through Marin's wrapper (`af9c678`).
  Binary: 1.0 when every constraint passes.
- **B, the task-curation gate**: `_answer_text` (reasoning stripped), then verifyit's `ifeval`
  checks (`af9c678`) on every constraint except the four the LLM judge scores. A failed check
  gives reward 0.0 and the judge is not called. NVIDIA's checkers are B's reference.
- **R, the replacement**: `audit/replacement/contract_grader.py`, written from
  `audit/CONTRACTS.md`, with one switch per decision entry.

Step 6 (blinded review) was not run in this exercise, so no reviewed error rate exists. Every
rate below is a disagreement with the replacement, split into verdicts that some allowed reading
explains (decisions) and verdicts that no reading explains (defect candidates). Section 7 says
what the review still has to show.

## 1. Result

**Recommendation: fix both graders before they train or filter anything.** Grader A has 27
checker findings, most of them small, plus three pipeline findings (extraction, randomness,
exceptions); `keywords:word_once` alone wrongly fails half of its verdicts. Grader B's
deterministic gate checks a different property from the instruction on nine ids
(no_adjacent_consecutive, lowercase_counting, repeat_phrase, square_brackets, sentence_hyphens,
number_paragraphs, paragraphs, paragraphs2, counting_composition) and has 13 more findings; it is
not fit as a gate until those nine checks are rewritten. Decide the 44 decision entries (section
4) first, because the fix for several checks depends on the reading chosen. The data needs two
fixes as well: the 308 impossible rows (F-G4) and the relation the model cannot see (F-A2).

Verdict level, whole panel (23,315 stored responses, 55,783 constraint verdicts):

| | Grader A (SkyRL reward) | Grader B (curation gate) |
|---|---|---|
| Verdicts graded (outside extraction failures) | 55,433 | 50,413 (gate ids only) |
| Contradicts the contract under every reading considered | 3,300 (6.0%) | 6,277 (12.5%) |
| Same, held-out quarter only (5,756 responses) | 815 of 13,656 (6.0%) | 1,522 of 12,428 (12.2%) |
| Differs from the proposed reading, but an allowed reading explains it | 2,005 (3.6%) | 1,580 (3.1%) |
| Checker exceptions | 1 (F-G3) | 0 |

As a reward (rows): grader A gives reward 1.0 to 6,477 panel rows. 908 of them (14.0%) fail the
contract under the proposed readings, and 403 (6.2%) fail it under every reading considered:
those are false rewards. Grader B passes the gate on 10,192 rows; 2,908 (28.5%) fail the
contract under the proposed readings and 2,272 (22.3%) under every reading.

Effect on scores. "Fixes only" keeps each grader's verdict wherever an allowed reading explains
it and takes the contract's verdict elsewhere (and scores extraction failures 0), so each change
is a defect fix. Row-level score, percentage points, 95% bootstrap interval over rows, rows
gained/lost:

| Run (rows) | A | A fixes only | change | B gate | B fixes only | change |
|---|---|---|---|---|---|---|
| Qwen2.5-7B-Instruct sample0 (4,000) | 20.1 | 22.6 | +2.5 [+1.8, +3.4] (+189/−88) | 33.0 | 29.7 | −3.3 [−4.4, −2.2] (+167/−299) |
| Qwen3-4B-Instruct-2507 greedy (1,000) | 29.3 | 33.6 | +4.3 [+2.7, +6.0] (+56/−13) | 49.9 | 44.7 | −5.2 [−7.7, −2.7] (+56/−108) |
| Qwen3-4B-Instruct-2507 greedy_repeat (1,000) | 29.5 | 33.9 | +4.4 [+2.8, +6.1] (+59/−15) | 50.0 | 44.8 | −5.2 [−7.6, −2.8] (+56/−108) |
| Qwen3-4B-Instruct-2507 sample0 (11,817) | 29.6 | 34.3 | +4.8 [+4.2, +5.3] (+779/−215) | 47.8 | 44.7 | −3.0 [−3.8, −2.2] (+939/−1,294) |
| Qwen3-4B-Thinking-2507 sample0 (1,500) | 55.3 | 64.3 | +8.9 [+7.2, +10.7] (+159/−25) | 63.4 | 69.7 | +6.3 [+4.5, +8.2] (+157/−63) |
| OLMo-2-1124-7B-Instruct sample0 (3,998) | 19.1 | 20.8 | +1.7 [+1.2, +2.4] (+116/−47) | 32.0 | 26.1 | −5.9 [−7.2, −4.8] (+163/−400) |

- The rerun of Qwen3-4B-Instruct's greedy decode with identical settings changed 16 of 1,000 row
  rewards under A and moved A's score by +0.2 points [−0.6, +1.0] (B: 27 rows, +0.1). Every
  fixes-only change above is larger than that rerun difference.
- The changes move models by different amounts (A: +1.7 to +8.9 points), so the graders also
  change the ranking gaps between models, not only the level.
- Sensitivity: the replacement is least reliable on sentence_hyphens, response_language and
  bigram_wrapping. Keeping the graders' own verdicts on those three ids, the A changes are +1.2,
  +4.4, +4.5, +4.9, +6.8 and +1.6 points and the B changes −4.7, −6.6, −6.5, −4.6, +5.5 and −6.8
  (same row order), so the direction and size hold.
- Held-out quarter only (`audit/work/analyze_heldout.out`): A fixes only +2.1, +2.9, +4.0, +4.6,
  +11.4, +2.2; B fixes only −2.3, −3.7, −6.7, −2.7, +10.0, −6.4. These agree with the whole panel
  within their intervals.
- Largest drivers (`audit/work/row_drivers.out`): under A, `keywords:word_once` (F-A1) is the
  largest source of wrongly failed rows in every run (378 of Qwen3-4B-Instruct sample0's 779
  gained rows); under B, `count:lowercase_counting` (F-B2), `keywords:no_adjacent_consecutive`
  (F-B1), `detectable_format:square_brackets` (F-B4) and `paragraphs:paragraphs2` (F-B7) cause
  most false gate passes, and `keywords:word_once` (F-B18) most false gate fails.

Scored coverage: every one of the 55,783 expected verdicts was produced by each grader; grader A
raised one exception (F-G3), which the SkyRL session turns into reward 0.0 with outcome
INFRA_ERROR. OLMo-2 did not answer 2 of its 4,000 rows (prompt longer than its context); 139 of
the 1,500 Qwen3-Thinking responses never closed their reasoning (F-G1).

## 2. Scope and inputs

Pinned inputs, with hashes, are in `audit/ISSUE.md` sections 1 and "1 (part 2)": the case
manifest (all 176 files verified), Marin `af9c678`, NVIDIA `f46a5ac` (installed copies identical
to the case copies), the dataset revision `600262dd` with one sha256 per row
(`audit/frozen/row_hashes.tsv`), the panel files' sha256, the lockfile (nltk 3.10.3, langdetect
1.0.9) and NLTK `punkt_tab` by zip hash.

Unverified (location and the field that would verify each): the panel's stop sequences,
chat-template files and reasoning parser (the generation manifests, not in the case); the RL
run's own `verifyit_enabled`, output budget and reasoning-merge policy (the run's SkyRL session
config); how Marin's runs pin the dataset revision and the NLTK data; and the step that rewrites
the rows' `route: skyrl_gym` to the `task_session` that `NemotronTaskSession` requires
(`skyrl_gym.source_task.session_parameters`).

Skipped because this exercise has no tracker, repository, research branch, Hugging Face dataset,
job launcher, compute or reviewers: filing the issue (kept in `audit/ISSUE.md`), landing fixture
tests and fixes through a PR, the research branch, the immutable artifact for frozen samples,
generating new responses, and step 6. The reference has no unit tests, and verifyit's and
SkyRL's tests are not in the case, so no reference test could be run against the replacement.

## 3. Findings

How to reproduce any counterexample (Git Bash):

```bash
cd <W>/case
export NLTK_DATA=<W>/case/deps/nltk_data PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8
../.venv/Scripts/python.exe ../audit/repro.py <fixture-id>     # or G1, G2, G3
```

`repro.py` prints the exact input, the contract's label and the verdicts of A, B and R. It also
takes an explicit input: `repro.py <instruction-id> '<kwargs JSON>' '<response JSON>'`. Every
fixture is also a test in `audit/tests/test_fixtures.py`, marked `xfail(strict=True)` for each
grader that gets it wrong today. "Share" is the count of panel verdicts on that id that the
grader gets wrong under every reading considered (section 1's defect candidates), over the id's
panel verdicts; it measures the finding where the finding is the only defect of that grader on
that id, and bounds it otherwise.

### Pipeline and data findings

| Id | Stage | Counterexample (exact input) | Contract broken | Share | Reference status |
|---|---|---|---|---|---|
| F-G1 | Graded-text extraction, both graders | `repro.py G1`: a Qwen3-Thinking response cut by the token limit, `"Okay, the user wants a quote about teaching. Let me think about which quote fits best and"` (no `</think>`), row `keywords:existence ["quote","teaching"]`: A reward 1.0, B gate passes | G1: reasoning that never closes is an extraction failure and fails every check | 139 of 1,500 thinking responses (9.3%); A rewards 1 of them, B's gate passes 18 | Marin wrapper (`final_answer_text`, `_answer_text`); NVIDIA has no extraction |
| F-G2 | `build_instruction`, grader A | `repro.py G2`: row `nth_paragraph_first_word {num_paragraphs 3, nth_paragraph 4, first_word crash}`, response `"A.\n\nB.\n\nCrash."`: reward 1.0 for random seeds 5 and 7, 0.0 for the other eight of 0-9 | Verdicts must not depend on process state; paragraph 4 of 3 cannot exist | 77 rows in the data; 161 panel verdicts, of which A passes 19 | NVIDIA's `build_description` redraws `nth_paragraph`; Marin repairs only `None` |
| F-G3 | Exception handling, grader A | `repro.py G3`: `last_word_answer {last_word limit}` on `""` raises `IndexError`; the session reports INFRA_ERROR, reward 0.0 | An empty answer is a model failure (fail), not a grading failure | 1 panel verdict (Qwen3-4B-Instruct sample0, line 8186, uuid `003597dc-859c-4e4d-b0e6-b68d998ba578`); the empty response raises on all 625 such rows | NVIDIA `LastWordAnswerChecker` |
| F-G4 | Data: impossible rows | 77 rows ask for paragraph n of fewer than n paragraphs; 28 combine `count:count_unique` with a keyword that must appear 2+ times; 203 `letters:letter_counting` rows ask for fewer than 2 or 3 letters in the whole answer. Command: `../.venv/Scripts/python.exe ../audit/scripts/data_checks.py` (prints the counts and example rows, e.g. row 248: `{"first_word": "feedback", "nth_paragraph": 4, "num_paragraphs": 3}`) | A row's constraints must be satisfiable together | 308 distinct rows (2.6%) that no ordinary answer can pass | Data |
| F-G5 | Content-free reward, grader A | The empty response gets reward 1.0 on 1,702 of 11,817 rows (14.4%); `"ok ok ... ok"` on 609; a copy of the prompt on 746. Command: `../.venv/Scripts/python.exe ../audit/scripts/content_free.py` (about a minute; prints the rows rewarded and the per-check passes for `""`, `"ok ok ... ok"` and the prompt) | — (under the contract the empty response still passes 967 rows whose constraints are all prohibitions) | 1,702 rows | The 735 rows above the contract's 967 come from F-A19, F-A2 and vacuous passes of `first_word_sent`, `last_word_sent`, `bigram_wrapping` on empty text |
| F-G6 | Unpinned dependency | `_ensure_nltk_data` (`case/reference/skyrl_gym/envs/nemotron_ultra/instruction_following.py`, line 33) calls `nltk.download("punkt_tab")` when the data is missing, with no hash or version; not reproducible offline | Every input that changes a verdict is pinned | — | Marin wrapper |

### Grader A (NVIDIA checkers as the SkyRL reward runs them)

Every grader-A checker finding is in the reference by construction: A runs NVIDIA's checkers
unchanged.

| Id | Check | Fixture: exact input → A's verdict (contract) | Contract broken | Share |
|---|---|---|---|---|
| F-A1 | keywords:word_once | `word_once:9bc26825b6c823d8`: `{"keyword": "fix"}`, `"Fix it now, then fix it again."` → fail (pass) | "Include keyword X": at least once; A requires exactly one | 906 / 1,808 (50.1%) |
| F-A2 | keywords:word_count_different_numbers | `word_count_different_numbers:22a61be79b67a56b`: `{"keyword": "skin", "frequency": 1, "relation": "less than"}`, `"No mention here."` → pass (fail) | The text says "should appear N times"; A applies a hidden relation the model never sees | 289 / 1,015 (28.5%); 200 more are `D-appear-n-times` |
| F-A3 | first_word_answer, first_word_sent, nth_paragraph_first_word | `nth_paragraph_first_word:244670a8e81f7f4f`: `{"num_paragraphs": 3, "nth_paragraph": 2, "first_word": "crash"}`, `"Intro.\n\nCrash: tests matter.\n\nEnd."` → fail (pass); also `first_word_answer:52cd135831518478` (`**Development**: ...`) | G4: punctuation and markdown around a word are not part of it | 133 / 1,089 (12.2%), 101 / 1,024 (9.9%), 4 / 1,048 |
| F-A4 | keywords:keyword_specific_position | `keyword_specific_position:95780d5af1cf52d9`: `{"keyword": "shot", "n": 2, "m": 3}`, `"I tried hard. Then a Shot rang out."` → fail (pass) | G4 case; G3 punctuation tokens are not words (`c3e1bd3df5ed9f78`) | 17 / 1,341 (1.3%) |
| F-A5 | count:count_unique | `count_unique:171e20fc214710d6`: `"Red, green, blue, yellow."` → fail (pass) | Punctuation tokens are not words | 106 / 1,341 (7.9%) |
| F-A6 | count:counting_composition | `counting_composition:17bfa4831df725b7`: three 3-sentence paragraphs of 2-word sentences divided by `* * *`, the divider the instruction names → fail (pass) | The instructed divider `* * *` must count | 1 row; 0 panel verdicts differ |
| F-A7 | detectable_content:number_placeholders | `number_placeholders:19d2230d50ede69d`: `{"num_placeholders": 2}`, `"Dear [], see [ ]."` → pass (fail) | Blank brackets are not placeholders | 2 / 1,201 |
| F-A8 | detectable_content:postscript | `postscript:4d22e36c6b921eac`: `{"postscript_marker": "P.S."}`, `"Main text.\n\nP.P.S. Extra note."` → pass (fail); `postscript:47b14e99fbb4f78f`: `"Main text.\n\nP.S: one more thing."` → fail (pass) | A `P.P.S` line is not a `P.S.` postscript; inline prompts show the marker as "P.S", so `P.S:` must count; a marker mid-line is not a postscript | 221 / 1,277 (17.3%) |
| F-A9 | detectable_format:bigram_wrapping | `bigram_wrapping:ea482050fedc4b68`: `"<<I am>> <<at home>>."` → fail (pass); single-word groups such as `<<Kompally>> <<Carnival>>` pass | Every group holds a word pair; punctuation may stand outside | 182 / 1,157 (15.7%; the replacement is unreliable on Chinese) |
| F-A10 | detectable_format:constrained_response | `constrained_response:39c350ccd1b1efd3`: `"My answer is yes. My answer is no."` → pass (fail) | One option, not several | 3 / 243; a copy of the prompt passes all 120 rows |
| F-A11 | detectable_format:multiple_sections | `multiple_sections:e373e502b54e1d72`: `{"num_sections": 2, "section_spliter": "SECTION"}`, three sections → pass (fail); `1744f13dda7bc73e` (an empty section) → pass (fail) | "must have N sections" means N, each with content | 37 / 917 (4.0%) |
| F-A12 | detectable_format:number_bullet_lists | `number_bullet_lists:f268b2713e3bacde`: `{"num_bullets": 2}`, `"* First.\n* Second.\n* * *\nEnd."` → fail (pass); also `---` rules, `*Note:*` lines, `-5 degrees` lines | Rules, dividers, italics and negative numbers are not bullet points | 21 / 1,019 (2.1%) |
| F-A13 | detectable_format:number_highlighted_sections | `number_highlighted_sections:bf401f59c7f0d7e1`: `{"num_highlights": 1}`, `"Compute 2 * 3 * 4 now."` → pass (fail) | `* 3 *` is arithmetic, not emphasis | 7 / 1,070 |
| F-A14 | detectable_format:sentence_hyphens | `sentence_hyphens:708923dd6032f558`: `"My well-known recipe works.-It is quick."` → fail (pass) | Hyphens inside a sentence are allowed | 590 / 1,300 (45.4%; the replacement cannot see unpunctuated sentence ends, see section 7) |
| F-A15 | detectable_format:square_brackets | `square_brackets:863a8dc427f8cf15`: `"[Hello], [world]!"` → fail (pass); `[J][u][s][t] [g][o]` → pass (fail) | Punctuation may stand outside the brackets; letters in brackets are not words in brackets | 77 / 1,079 (7.1%) |
| F-A16 | keywords:no_adjacent_consecutive | `no_adjacent_consecutive:5c46c933aa56d687`: `"Cats * + run."` → fail (pass); `"Room 1 2 3 was open."` → fail (pass); words starting with `[` or `<` are never compared | Only letters at the start of words count | 53 / 1,499 (3.5%) |
| F-A17 | keywords:palindrome | `palindrome:edf215253ac6227f`: `"Wow, that was fun."` → fail (pass); `"- item one\n- item two"` → pass (fail) | Case and punctuation do not matter; a bullet `-` is not a word | 45 / 1,165 (3.9%) |
| F-A18 | keywords:start_end | `start_end:d913ec0ca2a73b7a`: `"**Hello** there my friend hello"` → fail (pass) | Leading markdown is not a word | 4 / 989 |
| F-A19 | language:response_language | `response_language:63eb3cf12cff81ff`: `{"language": "fr"}`, `""` → pass (fail) | An empty answer is in no language; langdetect's exception counts as a pass | 140 / 1,600 (8.8%; mostly mixed-language answers, where the replacement is approximate); the empty response passes all 780 rows |
| F-A20 | number_paragraphs, paragraphs:paragraphs | `paragraphs:96f258ff5addc74a`: `"First ***bold*** words here.\n***\nSecond."` → fail (pass) | Bold italic `***x***` is not a divider | 3 / 2,495 |
| F-A21 | length_constraints:number_words | `number_words:382b53392cc1aa48`: `{"num_words": 5, "relation": "less than"}`, `"I don't like it"` → fail (pass) | "don't" is one word under every reading | 22 / 1,443 (1.5%) |
| F-A22 | combination:two_responses | `two_responses:1c9432eb1afde32f`: `"Use a map.\n*******\nAsk a local."` → pass (fail) | The separator is 6 asterisks | 1 / 557 |
| F-A23 | copy:repeat_phrase | `repeat_phrase:7c99458c0aeb60ee`: phrase "Live each day to the fullest", 2, `"live each moment to the fullest. LIVE EACH WEEK TO THE FULLEST."` → fail (pass) | Case does not matter | 8 / 1,059 |
| F-A24 | change_case:english_capital, english_lowercase | `english_capital:7473be84b7613e32`: `"OKAY."` → fail (pass); `"HELLO WORLD"` → fail (langdetect says Somali) | Short or all-capital English is English | 115 / 1,534 (7.5%) and 14 / 1,208 |
| F-A25 | count:lowercase_counting | `lowercase_counting:41428cb0175422c8`: `{"N": 2}`, `"мы мы мы идём"` → pass (fail) | Non-ASCII lowercase words are lowercase words | 49 / 1,712 (2.9%) |
| F-A26 | letters:letter_counting | `letter_counting:4b28f1bfc2d4e78d`: `{"N": 3, "relation": "at least"}`, `"Привет мир друзья"` → fail (pass) | Cyrillic letters are letters (whether Han characters are letters is open) | 71 / 961 (7.4%) |
| F-A27 | first_word:first_word_sent, last_word:last_word_sent | fuzz case `fuzz:A:last_word_sent:pass` (`audit/tests/fuzz_cases.json`): `{"last_word": "alarm"}`, `""` → pass (fail). Command: `../.venv/Scripts/python.exe ../audit/repro.py last_word:last_word_sent '{"last_word": "alarm"}' '""'` | "The first/last word of each sentence" needs a sentence; a text with none fails | Empty text passes all 540 and 600 rows (content-free run); 24 panel responses have empty graded text |

Residual grader-A disagreements that no finding above names (60 verdicts, mostly
`last_word_sent`, `number_sentences`, `capital_word_frequency`) come from NVIDIA's sentence
splitter and tokenizer, which neither reading of `D-sentence` or `D-word` matches exactly; they
need the review. The 19 unexplained `nth_paragraph_first_word` passes are all F-G2.

### Grader B (verifyit `ifeval` checks of the task-curation gate)

| Id | Check | Fixture: exact input → B's verdict (contract) | Contract broken | Share | In the reference (NVIDIA)? |
|---|---|---|---|---|---|
| F-B1 | keywords:no_adjacent_consecutive | `no_adjacent_consecutive:3210e18590f5a885`: `"A big dog."` → pass (fail) | B checks repeated adjacent words, a different property | 839 / 1,499 (56.0%) | No |
| F-B2 | count:lowercase_counting | `lowercase_counting:925fbcb1888cedf0`: `{"N": 2}`, `"the cat and the dog and the bird"` → pass (fail); `"Apples are red."` (N 3) → fail (pass) | "at most N": B requires at least N lowercase words | 1,310 / 1,712 (76.5%) | No (NVIDIA counts the total, `D-lowercase-scope`) |
| F-B3 | copy:repeat_phrase | `repeat_phrase:5d8284bd53c9d337`: `"Live each moment to the fullest. Live each week to the fullest."` → fail (pass) | B counts unchanged copies (at least N) instead of transformed ones (exactly N) | 279 / 1,059 (26.3%) | No |
| F-B4 | detectable_format:square_brackets | `square_brackets:f84f106da34c9ad4`: `"[I] like [tea]"` → pass (fail) | Every word, not any word | 675 / 1,079 (62.6%) | No |
| F-B5 | detectable_format:sentence_hyphens | `sentence_hyphens:1fb021dfd14f7021`: `"I like tea.-It is warm.-It calms me."` → fail (pass); `"I like tea."` → fail (pass) | B requires every sentence to be one hyphenated token | 482 / 1,300 (37.1%) | No (NVIDIA has F-A14) |
| F-B6 | length_constraints:number_paragraphs | `number_paragraphs:4cd68abde1c2e725`: `{"num_paragraphs": 3}`, `"First.\n***\nSecond.\n***\nThird."` → fail (pass); `"First.\n\nSecond.\n\nThird."` → pass (fail) | Paragraphs are separated by `***`; B counts blank-line paragraphs | 427 / 1,345 (31.7%) | No |
| F-B7 | paragraphs:paragraphs, paragraphs2 | `paragraphs:87036b2c94bca795`: three `***` paragraphs → pass (fail); `paragraphs2:4ee668c1c630deed`: three blank-line paragraphs → pass (fail) | "There should be 2 paragraphs": B accepts 2 or more, by either separator | 128 / 1,150 (11.1%), 435 / 1,391 (31.3%) | No |
| F-B8 | Word-based checks (number_words and others) | `number_words:dde6f80e745cf577`: `{"num_words": 5, "relation": "at least"}`, `"Привет как у тебя дела"` → fail (pass) | B's words are ASCII only, so non-Latin words do not exist | 66 / 1,443 (4.6%) on number_words | No |
| F-B9 | keywords:start_end | `start_end:60545103580f7377`: `"Hello there my friend hello."` → pass (fail) | "not even punctuation" after the last word | 63 / 989 (6.4%) | No |
| F-B10 | startend:quotation | `quotation:31a947e61dca766e`: `"\""` → pass (fail); `"'Hello there.'"` → pass (fail) | Double quotation marks, around a response | 0 panel verdicts | No |
| F-B11 | detectable_content:postscript | `postscript:442940f2e9c7a8b5`: `"Main text.\n\n**P.S.** One more thing."` → fail (pass); `P.S:` → fail (pass) | Markdown before the marker and "P.S" without the dot count | 97 / 1,277 (7.6%) | Partly (NVIDIA rejects `P.S:` too, F-A8) |
| F-B12 | detectable_format:constrained_response | `constrained_response:e6b8897167a20de5`: `"**My answer is maybe.**"` → fail (pass) | Fails under both readings of `D-constrained-exact` | 0 panel verdicts beyond the 75 that are `D-constrained-exact` | No |
| F-B13 | detectable_format:json_format | `json_format:cbf6df16a4458001`: ```` "```JSON\n{\"a\": 1}\n```" ```` → fail (pass) | Any markdown fence label is allowed | 0 panel verdicts | No |
| F-B14 | detectable_format:multiple_sections | `multiple_sections:60d6666e9ca34bdd`: one section that mentions "Section 2" in a sentence → fail (pass); empty sections pass | A mention is not a marker; a section has content | 11 / 917 | Partly (NVIDIA counts mentions too, F-A11) |
| F-B15 | detectable_format:number_bullet_lists | `number_bullet_lists:f268b2713e3bacde`: `* * *` counted as a bullet → fail (pass) | A divider is not a bullet | 0 panel verdicts | Yes (F-A12) |
| F-B16 | detectable_format:number_highlighted_sections | `number_highlighted_sections:bf401f59c7f0d7e1` → pass (fail) | As F-A13 | 5 / 1,070 | Yes (F-A13) |
| F-B17 | detectable_format:title | `title:7d4eb1644008f31a`: `"<< >> text"` → pass (fail) | A blank title is not a title | 0 panel verdicts | No |
| F-B18 | keywords:word_once | `word_once:9bc26825b6c823d8` → fail (pass) | As F-A1 | 861 / 1,808 (47.6%) | Yes (F-A1) |
| F-B19 | keywords:word_count_different_numbers | `word_count_different_numbers:22a61be79b67a56b` → pass (fail) | As F-A2 | 289 / 1,015 (28.5%) | Yes (F-A2) |
| F-B20 | count:counting_composition | `counting_composition:4eeaed6321b424cf`: two paragraphs instead of three → pass (fail) | B checks only "at least N sentences of at least M words" | 1 row; 0 panel verdicts | No |
| F-B21 | combination:two_responses | `two_responses:1c9432eb1afde32f` → pass (fail) | As F-A22 | 1 / 557 | Yes (F-A22) |
| F-B22 | keywords:palindrome | `palindrome:c5a716e285831734`: `"A man, a plan, a canal, Panama."` → fail (pass) | A palindromic phrase is a palindrome | 135 / 1,165 (11.6%) | No |

Classification against the reference (step 4): on the panel, B's verdict differs from NVIDIA's
(grader A's checker) on 7,781 gate-id verdicts. Classified against the contract, through the
replacement and its alternative readings (per-check tables in `audit/work/analyze_all.out`):
most are B defects (F-B1 to F-B9, F-B22), some are reference defects on which B agrees with the
contract (grader-A findings that grader B does not share, such as F-A3, F-A14 and F-A24), and
the rest are decisions (section 4). Where both disagree with the contract in the same
direction, the defect is shared (column "In the reference").

## 4. Decision entries

Each entry has both readings, an example of each in the fixtures (`audit/tests/fixtures_data.py`,
tag in the last field), and the proposal. "Panel" counts disagreements with the proposed reading
that the alternative explains (A / B). The maintainers of the evaluation decide.

| Entry | Proposed reading | Alternative | Example (fixture) | Panel A / B |
|---|---|---|---|---|
| D-appear-n-times | "should appear N times" = exactly N | at least N | `word_count_different_numbers:3700d6b1ce4d8891` "Skin, skin, skin." (N 2) | 159 / 159 |
| D-divider-empty | an empty part between `***` fails | ignored | `number_paragraphs:ba05dfbd34e6a6f6` (trailing `***`) | 182 / 96 |
| D-lowercase-scope | each lowercase word ≤ N times | ≤ N lowercase words in total | `lowercase_counting:65969631d8d59ca1` | 262 / 9 |
| D-sentence | line breaks end sentences; abbreviations kept | no line-break boundary | `last_word_sent:1a2da0f079ebf26a` | 128 / 141 |
| D-repeat-original | an unchanged copy does not count | counts | `repeat_phrase:41aafb168dc23143` | 50 / 217 |
| D-palindrome-length | 3+ characters | any length ("a") | `palindrome:44d9cdc8690a453a` | 219 / 8 |
| D-keyword-boundary | whole word | substring ("prefix" has "fix") | `word_once:bf1035882a7c78c7` | 176 / 30 |
| D-bracket-group | one word per pair | several words per pair | `square_brackets:58c91a96a380c612` | 21 / 169 |
| D-english-part | "in English" is checked | only letter case | `english_capital:6450bacf39fa97d2` | 18 / 168 |
| D-word | runs of letters/digits, ' and - join | whitespace tokens | (implicit in word checks) | 129 / 37 |
| D-end-case | exact phrase, case-sensitive | case-insensitive | `end_checker:929dd9edaa6fc740` | 162 / 0 |
| D-consecutive-script | Latin a-z only | any alphabet | `no_adjacent_consecutive:d36979acc1fd72f0` | 109 / 32 |
| D-postscript-end | the postscript ends the response | anywhere | `postscript:10ab45e1b11fc0d8` | 71 / 65 |
| D-dot-chars | `.`, `。`, `．`, `…` | ASCII only | `punctuation_dot:4941d635c4b3e7d0` | 55 / 55 |
| D-consecutive-order | both orders (b then a) | ascending only | `no_adjacent_consecutive:d49d8b7ae89b4c30` | 45 / 40 |
| D-capital-single-letter | "I", "A" count | 2+ letters | `capital_word_frequency:f29ea7f2bc1e8597` | 3 / 80 |
| D-constrained-exact | contains exactly one option | is exactly one option | `constrained_response:f6577a7ae78999bd` | 0 / 75 |
| D-start-end-one-word | one-word answer passes | fails | `start_end:c7a9a22d8d4a966b` | 42 / 13 |
| D-two-responses-edge | leading/trailing `******` fails | ignored | `two_responses:d8a6fe7ed84f76fd` | 29 / 29 |
| D-comma-chars | all comma characters | ASCII only | `no_comma:0bb6f27365f66241` | 27 / 27 |
| D-end-trailing | trailing quotes/markdown allowed | nothing may follow | `end_checker:c50a91cf44283b42` | 7 / 35 |
| D-divider-form | non-emphasis `***` or `* * *` anywhere | a line that is exactly `***` | `number_paragraphs:8ced25466eeb3df5` | 5 / 28 |
| D-letters-unit | letters = alphabetic characters | letters = words | `letter_counting:0c6ed63e571d8fee` | 25 / 0 |
| D-sections-case | spliter case-insensitive | exact case | `multiple_sections:37bf49bd78a57db4` | 23 / 1 |
| D-excl-chars | all exclamation characters | ASCII only | `punctuation_exclamation:c1486cf155eee3e6` | 9 / 9 |
| D-lowercase-count | lowercase-written occurrences | all occurrences | `lowercase_counting:e91e2da5a67a3e4e` | 13 / 3 |
| D-repeat-center | any non-edge word | the middle word only | (switch only) | 1 / 15 (+13 with D-repeat-original) |
| D-blank-run | 2+ newlines = one separator | exactly two | `nth_paragraph_first_word` fixture with `\n\n\n` | 6 / 2 |
| D-quote-chars | `"` and `“ ”` | ASCII only | `quotation:3ea7fa238e6fe5b6` | 4 / 3 |
| D-highlight-bold | `*x*` and `**x**` | `*x*` only | `number_highlighted_sections` bold fixture | 3 / 3 |
| D-language-mixed | predominantly in the language | no foreign word | `response_language` Russian+Python fixture | 2 / 0 |
| D-unique-case | case-insensitive | case-sensitive | `count_unique:2e099542b0eccd3d` | 2 / 0 |
| D-postscript-case | case-insensitive marker | case-sensitive | `postscript` lowercase fixture | 0 / 1 |
| D-think-markup | grade a non-reasoning `<think>` span | strip it to its close or the end | (14 panel responses) | 1 / 0 |
| D-sections-preamble | preamble allowed | not allowed | `multiple_sections` preamble fixture | 0 / 1 |
| D-sections-numbering, D-placeholder-kind, D-json-toplevel, D-bigram-odd, D-title-position, D-letter-case, D-hyphen-dash, D-bullet-marker, D-bullet-nested | see CONTRACTS.md | | fixtures tagged with each | 0 / 0 |

Notable combinations: grader A's `copy:repeat_phrase` passes `[unchanged, transformed]` and
fails `[transformed, unchanged]` (it checks only the last copy), so each verdict matches one
reading of `D-repeat-original` but no single reading gives both.

## 5. Panel details

Stored records only (`audit/work/analyze_all.out`, produced by `audit/scripts/grade_panel.py`
and `audit/scripts/analyze_panel.py`): 23,315 responses in six run files; truncated
(`finish_reason` length): 65, 92, 81, 620, 166 and 39 by run; empty graded text after extraction:
24 responses (14 of them non-reasoning answers containing an unclosed `<think>`, which both
pipelines turn into empty text, `D-think-markup`). Per-check pass rates of A, B and R, and the
split of disagreements into decision-explained and unexplained, are in the per-check table of
`audit/work/analyze_all.out`. Grader B's pass rate is far above the contract's on the checks of
F-B1 (76.8% vs 23.8%), F-B2 (87.6% vs 29.5%), F-B4 (94.4% vs 17.7%) and F-B7 (94.0% vs 62.5% on
paragraphs2), and far below on F-B6 (42.4% vs 63.7%).

## 6. Stress tests (step 4)

- Fixtures: 265 hand-written fixtures, 385 metamorphic and forbidden-edit cases, 4 pipeline
  fixtures and 35 fuzz cases. The whole suite (`cd audit; ../.venv/Scripts/python.exe -m pytest
  -q -p no:cacheprovider tests`, with NLTK_DATA set) gives 1,635 passed, 33 skipped (a fuzz case
  recorded for the other grader) and 355 expected failures (xfail strict), each tied to a finding
  or decision (`audit/tests/known_failures.json`, `known_failures_props.json`,
  `fuzz_cases.json`). The replacement passes every case. `audit/fixtures.jsonl` lists all 830
  labeled responses (with 141 content-free representatives).
- Content-free responses (`audit/scripts/content_free.py`, `audit/work/content_free.out`): see
  F-G5. The empty response raises `IndexError` in grader A on all 625 `last_word_answer` rows
  (F-G3). A copy of the prompt passes A's `postscript` on 497 of 644 rows (F-A8: the prompt
  itself contains "P.S." mid-line) and `constrained_response` on all 120 rows (F-A10).
- Metamorphic and forbidden-edit cases (`audit/scripts/make_property_cases.py`,
  `run_property_cases.py`, `audit/work/property_cases.out`, tests in
  `audit/tests/test_properties.py`): 386 cases built from the fixtures by edits the contract
  ignores (doubling spaces inside lines, curly apostrophes, upper case for case-insensitive
  checks) and by one forbidden edit per check applied to passing fixtures; 1 dropped because the
  replacement cannot see the unpunctuated sentence end it adds. Property violations (a neutral
  edit flips the grader's verdict, or a forbidden edit leaves a pass):
  - A: 10 forbidden edits still pass (a second option added, F-A10; a third or ninth section
    added, F-A11); upper-casing flips 4 verdicts (F-A23, F-A4); doubling spaces flips 9
    `multiple_sections` verdicts (`SECTION  1` with two spaces is not a marker for NVIDIA,
    F-A11).
  - B: 20 forbidden edits still pass (F-B1, F-B2, F-B4, F-B6, F-B7, F-B9); curly apostrophes flip
    2 verdicts (F-B8, and one `quotation` case where the flip is toward the label); doubling
    spaces flips 1 (F-B3).
  - The replacement: none.
- Fuzzing: section 8.
- Exceptions do not stop a run in either pipeline: grader A catches each checker's exception,
  records it in `instruction_errors`, and the session then voids the row (INFRA_ERROR, reward
  0.0); grader B's `_passes` counts the exception as a failed constraint and only logs a warning,
  so a crash in B is indistinguishable from a model failure.
- Score-level transforms: none apply; both graders are binary on the row (no loose variants, no
  fraction mode in use: no row sets `grading_mode`).

## 7. Step 6 not run: what the recommendation still needs

The rates above are disagreements with the replacement, not a reviewed error rate. The
recommendation to fix both graders needs, from a blinded review of frozen held-out panel cases
(the held-out set is frozen: `audit/frozen/heldout_v1.txt`, sha256 `86aaf172…`):

1. a paired difference in error rate between each grader and the replacement whose 95%
   interval excludes zero (pre-registered in ISSUE.md), stratified by whether the grader and the
   replacement disagree, sampling most disagreements;
2. confirmation on the three ids where the replacement is weakest: `sentence_hyphens` (it cannot
   see a sentence end without punctuation; 590 of A's and 482 of B's disagreements are there),
   `response_language` and the "in English" part of `change_case` (script share plus langdetect),
   and `bigram_wrapping` on Chinese text;
3. reviewer leans on the decision entries with the largest counts (`D-appear-n-times`,
   `D-divider-empty`, `D-lowercase-scope`, `D-sentence`, `D-repeat-original`,
   `D-palindrome-length`, `D-keyword-boundary`, `D-end-case`).

The findings with a counterexample under every reading (all F- ids above) do not depend on the
review; their panel shares do.

## 8. Revisions

- Fuzzing (added 11:24Z): `audit/scripts/fuzz.py 2000` (seed 20261112, `audit/work/fuzz.out`)
  draws 2,000 random token mixes (English words, the row's keywords in four casings,
  punctuation and markdown runs, Cyrillic/Han/Greek/Arabic words, layout breaks, numbers) for
  random constraints of the real rows. No exception in either grader (these inputs are rarely
  empty; F-G3 needs empty text). Disagreements with the replacement that no reading explains:
  117 for A on 16 ids and 146 for B on 17 ids (and 138 and 48 that a decision explains); counts
  depend on this generator and are not rates.
  The smallest reproducing response of each (grader, id, verdict) was kept after greedy
  deletion; 41 were read by hand, 35 kept as tests (`audit/tests/fuzz_cases.json`, run by
  `test_properties.py`), and 6 dropped because the contract does not settle their label (an
  empty text for bigram_wrapping, sentence_hyphens and square_brackets, a lone "g", Arabic-Latin
  noise, and "P.S. ς"). Every kept case falls under an existing finding except one new one,
  F-A27 (sentence checks pass a text with no sentence). Examples: `"BLOOD blood"` fails
  word_once in both graders (F-A1, F-B18); `"<"` is a palindrome for A (F-A17); `">>"` starts
  and ends with the same word for A (F-A18); `"with with"` fails B's no_adjacent_consecutive and
  `"a b"` passes it (F-B1); `"n[5]"` passes B's square_brackets (F-B4); `"é

>"` is two
  paragraphs for B's paragraphs:paragraphs (F-B7).

- Harness fidelity (added 11:22Z): the audit grades grader A per constraint
  (`audit/harness.py`); calling `grade_instruction_following` on the whole row reproduces those
  row rewards on 2,332 panel rows (every tenth line of each run file), with 0 mismatches. Grader
  B's gate is replayed from `grade_judge.py`'s own `_answer_text` and `_passes` source, executed
  byte for byte (its module imports openai, which is not installed).

## Appendix: per-check panel table

From `audit/work/analyze_all.out` (whole panel). Columns: verdicts; pass % of A, B, R (proposed
readings); for A and for B: disagreements with R, split into (unexplained grader passes /
unexplained grader fails, decision-explained); A exceptions. B is not run on the four judged ids.
Extraction failures (F-G1) are counted in the verdicts but not in the disagreements.

```text
per check: n, pass% A B R | A vs R: disagree (unexplained pass/fail, decision) | B vs R: same | A_err
change_case:capital_word_frequency              1207  75.7  78.7  75.5 | A   21 (   8/   3,   10) | B  101 (   2/  19,   80) | 0
change_case:english_capital                     1534  45.1  55.0  51.7 | A  129 (   0/ 115,   14) | B   67 (   0/   8,   59) | 0
change_case:english_lowercase                   1208  69.0  77.4  69.8 | A   18 (   0/  14,    4) | B  126 (   0/  17,  109) | 0
combination:two_responses                        557  81.3  81.3  75.9 | A   30 (   1/   0,   29) | B   30 (   1/   0,   29) | 0
copy:repeat_phrase                              1059   8.9  45.0   4.4 | A   59 (   3/   5,   51) | B  524 ( 247/  32,  245) | 0
count:count_unique                              1341  15.0  80.7  22.3 | A  114 (   0/ 106,    8) | B    0 (   0/   0,    0) | 0
count:counting_composition                         1   0.0   0.0   0.0 | A    0 (   0/   0,    0) | B    0 (   0/   0,    0) | 0
count:lowercase_counting                        1712  15.2  87.6  29.5 | A  326 (  39/  10,  277) | B 1339 (1150/ 160,   29) | 0
detectable_content:number_placeholders          1201  90.9  90.8  90.9 | A    2 (   1/   1,    0) | B    1 (   0/   1,    0) | 0
detectable_content:postscript                   1277  82.7  71.8  74.4 | A  292 ( 128/  93,   71) | B  163 (   0/  97,   66) | 0
detectable_format:bigram_wrapping               1157  19.4   2.1   3.4 | A  185 ( 182/   0,    3) | B    0 (   0/   0,    0) | 0
detectable_format:constrained_response           243  89.7  57.6  88.5 | A    3 (   3/   0,    0) | B   75 (   0/   0,   75) | 0
detectable_format:json_format                    266  82.0  82.0  82.0 | A    0 (   0/   0,    0) | B    0 (   0/   0,    0) | 0
detectable_format:multiple_sections              917  86.3  85.1  85.2 | A   60 (  35/   2,   23) | B   13 (   6/   5,    2) | 0
detectable_format:number_bullet_lists           1019  80.1  81.6  81.6 | A   21 (   3/  18,    0) | B    0 (   0/   0,    0) | 0
detectable_format:number_highlighted_sections   1070  93.2  93.2  93.0 | A   10 (   6/   1,    3) | B    8 (   5/   0,    3) | 0
detectable_format:sentence_hyphens              1300  19.6  19.5  56.2 | A  590 (  57/ 533,    0) | B  482 (   2/ 480,    0) | 0
detectable_format:square_brackets               1079  16.2  94.4  17.7 | A   98 (  20/  57,   21) | B  844 ( 667/   8,  169) | 0
detectable_format:title                         1189  96.4  96.4  96.6 | A    2 (   0/   2,    0) | B    2 (   0/   2,    0) | 0
first_word:first_word_answer                    1089  72.2  85.1  84.7 | A  136 (   0/ 133,    3) | B    7 (   6/   1,    0) | 0
first_word:first_word_sent                      1024  32.3  43.3  41.4 | A  115 (   0/ 101,   14) | B   35 (  12/   8,   15) | 0
keywords:existence                              1856  75.4  71.9  71.9 | A   66 (   0/   0,   66) | B    0 (   0/   0,    0) | 0
keywords:forbidden_words                        1687  96.6  96.6  96.6 | A    0 (   0/   0,    0) | B    0 (   0/   0,    0) | 0
keywords:frequency                              1200  80.8  80.7  80.7 | A   45 (   0/   0,   45) | B    0 (   0/   0,    0) | 0
keywords:keyword_specific_position              1341   2.8   3.7   3.7 | A   24 (   3/  14,    7) | B   16 (   4/   4,    8) | 0
keywords:letter_frequency                       1507  56.5  56.5  56.5 | A    0 (   0/   0,    0) | B    0 (   0/   0,    0) | 0
keywords:no_adjacent_consecutive                1499  23.7  76.8  23.8 | A  221 (  53/   0,  168) | B  922 ( 810/  29,   83) | 0
keywords:palindrome                             1165  90.0  63.1  73.6 | A  264 (   8/  37,  219) | B  143 (   2/ 133,    8) | 0
keywords:start_end                               989  29.5  37.1  34.2 | A   54 (   3/   1,   50) | B   83 (  54/   9,   20) | 0
keywords:word_count_different_numbers           1015  54.0  54.0  36.6 | A  489 ( 144/ 145,  200) | B  489 ( 144/ 145,  200) | 0
keywords:word_once                              1808  25.5  25.9  73.5 | A  944 (   0/ 906,   38) | B  862 (   0/ 861,    1) | 0
language:response_language                      1600  88.2  82.9  79.9 | A  142 ( 137/   3,    2) | B    0 (   0/   0,    0) | 0
last_word:last_word_answer                      1285  69.7  76.0  74.9 | A   67 (   0/   3,   64) | B   15 (  14/   1,    0) | 1
last_word:last_word_sent                        1203  27.8  33.3  27.3 | A   79 (   9/  16,   54) | B   80 (  34/   2,   44) | 0
length_constraints:nth_paragraph_first_word     1048  39.4  38.4  38.0 | A   25 (  19/   4,    2) | B    4 (   4/   0,    0) | 0
length_constraints:number_paragraphs            1345  74.1  42.4  63.7 | A  142 (   1/   1,  140) | B  491 (  57/ 370,   64) | 0
length_constraints:number_sentences             1131  70.1  69.3  70.6 | A   93 (   4/  14,   75) | B  108 (   8/  26,   74) | 0
length_constraints:number_words                 1443  73.3  70.1  73.5 | A   25 (  10/  12,    3) | B   70 (  11/  55,    4) | 0
letters:letter_counting                          961  61.2  65.6  66.2 | A   96 (  16/  55,   25) | B    0 (   0/   0,    0) | 0
letters:letter_counting2                        1346  53.9  53.9  53.8 | A    1 (   1/   0,    0) | B    1 (   1/   0,    0) | 0
paragraphs:paragraphs                           1150  83.5  96.7  80.2 | A   48 (   1/   0,   47) | B  190 ( 128/   0,   62) | 0
paragraphs:paragraphs2                          1391  62.5  94.0  62.5 | A    5 (   0/   0,    5) | B  437 ( 435/   0,    2) | 0
punctuation:no_comma                            1523  88.7  88.7  86.9 | A   27 (   0/   0,   27) | B   27 (   0/   0,   27) | 0
punctuation:punctuation_dot                     1749  51.6  51.6  48.5 | A   55 (   0/   0,   55) | B   55 (   0/   0,   55) | 0
punctuation:punctuation_exclamation             1284  95.3  95.3  94.6 | A    9 (   0/   0,    9) | B    9 (   0/   0,    9) | 0
startend:end_checker                             997  87.4  68.3  71.8 | A  169 (   0/   0,  169) | B   35 (   0/   0,   35) | 0
startend:quotation                               810  85.9  86.0  86.4 | A    4 (   0/   0,    4) | B    3 (   0/   0,    3) | 0
TOTAL {'n': 55783, 'A_disagree': 5305, 'A_unexplained': 3300, 'A_decision': 2005, 'B_disagree': 7857, 'B_unexplained': 6277, 'B_decision': 1580, 'A_err': 1}
```
