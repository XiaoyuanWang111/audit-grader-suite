# Audit of the RLVR1 instruction-following graders

Graders audited, on the 11,817 `instruction_following_simple_agent` rows of the Nemotron RLVR1 data (28,219 constraints, 47 instruction ids):

- **NV**: the SkyRL reward as configured by default, `final_answer_text` then `grade_instruction_following`, which runs NVIDIA's verifiable-instructions checkers (also the reference implementation).
- **VS**: the SkyRL reward with `verifyit_enabled`, `grade_nemotron_instructions` (NVIDIA's checkers inside verifyit, with four overrides).
- **VG**: the task-curation grader's deterministic gate, verifyit's `ifeval` checks on the non-semantic constraints; a failed check makes the reward 0.0 before the LLM judge is called.
- **R**: the audit's replacement grader, written from the contracts (`audit/replacement.py`), with the proposed reading of every decision entry. **RF**: the same with NVIDIA's side of every decision, so that a difference between RF and NV points to a defect rather than to a choice of reading.

Written 2026-11-12 (UTC). The record of the audit (pins, contract hashes, decisions, changes) is `audit/ISSUE.md`.

## 1. Error rate and effect on scores

**Error rate: not estimated.** Step 6, the blinded review that estimates each grader's error rate, was not run in this exercise (no reviewers). The numbers below are disagreements with the replacement grader, which implements the contracts but has not itself been reviewed; they bound nothing on their own. Section 7 says what the review must show.

What the stored panel shows (23,315 responses from 4 models and 6 runs, 55,783 constraint verdicts; `audit/out/panel_analysis.txt`):

- **NV against the contract.** NV and R disagree on 5,329 constraint verdicts (9.6%). 3,067 of them (5.5% of all verdicts) remain when R takes NVIDIA's side of every decision entry (RF), so they are checker defects under NVIDIA's own readings; 2,262 (4.1%) follow the other reading of a decision entry (section 5).
- **False rewards (RL).** Of the 6,469 responses that NV rewards 1.0, 1,006 (15.6%) fail at least one constraint under the contracts' proposed readings, and 537 (8.3%) fail one even under NVIDIA's readings. Per run, proposed / NVIDIA readings: Qwen2.5-7B-Instruct 30.0% / 10.4%, OLMo-2-1124-7B-Instruct 21.9% / 7.3%, Qwen3-4B-Instruct-2507 sampled 14.1% / 9.0%, greedy 10.2% / 8.2%, Qwen3-4B-Thinking-2507 5.9% / 4.5%. Per constraint, 2,344 of NV's 33,311 passes (7.0%) contradict the contract.
- **Effect on model scores** (share of rows whose constraints all pass; R minus NV, paired bootstrap 95% interval over rows):

| Run | Rows | NV | VS | R | RF | R − NV, points | RF − NV |
|---|---|---|---|---|---|---|---|
| Qwen3-4B-Thinking-2507, thinking, sampled | 1,500 | 55.3 | 54.3 | 65.3 | 63.8 | +10.0 [+8.1, +12.1] | +8.5 |
| Qwen3-4B-Instruct-2507, greedy | 1,000 | 29.3 | 28.3 | 32.9 | 32.0 | +3.6 [+1.7, +5.5] | +2.7 |
| Qwen3-4B-Instruct-2507, greedy rerun | 1,000 | 29.5 | 28.6 | 33.1 | 32.5 | +3.6 [+1.7, +5.5] | +3.0 |
| Qwen3-4B-Instruct-2507, sampled | 11,817 | 29.5 | 28.7 | 32.5 | 32.8 | +3.0 [+2.4, +3.6] | +3.3 |
| Qwen2.5-7B-Instruct, sampled | 4,000 | 20.0 | 19.6 | 20.2 | 22.8 | +0.2 [−0.9, +1.2] | +2.8 |
| OLMo-2-1124-7B-Instruct, sampled | 3,998 | 19.1 | 18.9 | 18.6 | 21.1 | −0.5 [−1.3, +0.4] | +2.1 |

  Rerunning the greedy configuration with identical settings changed 494 of 1,000 responses and moved NV's score by +0.2 points [−0.6, +1.0] (16 rows changed verdict); the replacement's change on the greedy run, +3.6, is outside that. On the held-out 30% of rows (section 6), R − NV is +9.7 [+6.3, +12.9] (thinking), +3.6 [+2.5, +4.7] (Qwen3 sampled), +3.4 [+0.3, +6.4] (greedy), −0.4 [−2.5, +1.7] (Qwen2.5), −0.7 [−2.5, +0.9] (OLMo).
- **VG, the task-curation gate.** VG and R disagree on 8,173 of 50,724 deterministic verdicts (16.1%): VG passes 5,411 that fail the contract and fails 2,762 that pass it. Of the 10,192 responses VG lets through to the judge, 3,007 (29.5%) fail a deterministic constraint under the contract; of the 13,123 it rejects with reward 0.0, 1,612 (12.3%) pass every deterministic constraint. Gate pass rate, VG vs R on the same constraints: Qwen3 sampled 47.8 vs 41.4 (−6.3 points [−7.1, −5.5]), Qwen2.5 33.0 vs 26.3, OLMo 32.0 vs 24.9, thinking 63.4 vs 68.6 (+5.2 [+3.0, +7.5]). Several verifyit checks implement a different instruction from the one the model is given (findings V3, V5, V11, V12, V14, V19).
- **Scored coverage.** NV gives a verdict to 23,314 of 23,315 responses (one `INFRA_ERROR`). VS leaves 473 (2.0%) unscored: 266 `json_format` rows (`ModuleNotFoundError: yaml`), 204 `repeat_phrase` rows (NVIDIA returns `None`, VS rejects it), 2 language, 1 last word. VG converts every row (all 47 ids resolve) and gives deterministic verdicts to 50,724 of 55,783 constraints (90.9%); the other 5,059 (`count_unique`, `bigram_wrapping`, `response_language`, `letter_counting`) go to the judge by design. R covers all.
- **Graded-text extraction.** 139 of the 1,500 thinking responses (9.3%) never close their reasoning; both pipelines grade the reasoning as the answer (finding G1). 23 responses contain an opening `<think>` or `<thinking>` that never closes (22 from models without a reasoning channel, which wrote the tag as text); both pipelines grade them as an empty answer, and NV rewards 8 of them 1.0 (plus one genuinely empty response: 9 of 24).

**Recommendation: fix the graders** (not admit them, and no need to replace the benchmark: the contracts can be implemented and the data needs only small repairs).

1. Task-curation gate: replace verifyit's `ifeval` checks for these 43 ids with checkers that follow the contracts (the replacement, or NVIDIA's checkers with the F-findings fixed). Six verifyit checks test a different requirement from the instruction; on the panel the gate passes 29.5% of its passes wrongly and rejects 12.3% of its rejections wrongly, before the judge is consulted.
2. SkyRL reward: fix NVIDIA's checker defects F1–F26 (or adopt the replacement after step 6), make `final_answer_text` treat a response without a closing reasoning marker from a thinking template as an extraction failure (G1), and make a checker exception a per-constraint grading failure that does not discard the row (G2).
3. Data: drop or repair the 77 unsatisfiable `nth_paragraph_first_word` constraints (G3), show the `relation` of `word_count_different_numbers` in the prompt or ignore it (G4), and render the `P.S.` marker with its dot (G6).
4. Pin the environment: declare PyYAML for `verifyit_enabled`, and stop `_ensure_nltk_data` from downloading NLTK data at run time (G5).
5. Have the evaluation's maintainers choose a reading for each decision entry in section 5; the replacement has one switch per entry.

This recommendation still needs step 6: the measured differences are against an unreviewed replacement (section 7).

## 2. What was run

| Step | Status |
|---|---|
| 1 Pin inputs | Done: `ISSUE.md`, per-row hashes `audit/frozen/row_hashes.tsv`, pin check `scripts/verify_pins.py`. Upstream commits and the HF parquet could not be fetched (offline): listed as unverified with the commands that would verify them. |
| 2 Contracts | Done before reading any grader code: `audit/CONTRACTS.md` v1 hash `da7e3e7a…` recorded 11:33:26 UTC; v2–v4 changes logged with reasons (v4 prompted by development panel responses only). Current v4 `af4ab1bd…`. |
| 3 Fixtures | 263 hand-written fixtures (256 per check, 7 extraction), `audit/tests/test_fixtures.py`, wrong current verdicts `xfail(strict=True)`. Replacement grader built. |
| 4 Stress | Reference comparison (NV vs VG on all fixtures and the panel), 12 property tests, a whitespace metamorphic test, fuzzing (1,507 texts × 74 constraint settings), content-free responses on all rows. |
| 5 Panel | The stored responses only (no generation): all 23,315 graded by NV, VS, VG, R, RF; 30% of rows held out before grading. |
| 6 Blinded review | **Not run** (no reviewers in this exercise). |
| 7 Report | This file. |

Substitutions for the offline exercise: no issue tracker (`audit/ISSUE.md` instead, no `file-issue`); no repository, research branch or `manage-pr` (scripts and tests under `audit/`, nothing landed); no Hugging Face dataset (frozen files under `audit/frozen/` with sha256 in `audit/frozen/SHA256SUMS` and `ISSUE.md`); no job launcher (`use-iris`) and no generation. `skill/references/validation.md` was not provided.

## 3. How to reproduce a verdict

Every counterexample below is a fixture in `audit/fixtures.jsonl`. From Git Bash:

```bash
cd <W>/audit
../.venv/Scripts/python.exe repro.py <fixture-id>
```

`repro.py` prints the input, the contract label and the verdicts of NV, VS, VG and R. It calls the graders as `case/TASK.md` does (`grade_instruction_following` on a one-constraint record; `resolve_checks` and the check, an exception counting as a failure; `grade_nemotron_instructions`'s in-process `_evaluate_with_state`), seeds the global RNG with 20261112, sets `NLTK_DATA` and writes no bytecode. A constraint can also be given directly, e.g. `../.venv/Scripts/python.exe repro.py keywords:word_once '{"keyword": "fix"}' '"Fix it and fix it again."'`, and an extraction case with `repro.py --pipeline [--thinking] ID KWARGS RAW`. All tests: `../.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider tests` (1533 passed, 37 skipped, 278 xfailed: the 263 hand-written fixtures in `test_fixtures.py` and the 199 generated ones in `test_generated.py`, each against NV, VS, VG and R).

In the tables, "→ NV x, VS y, VG z; contract c" is what `repro.py` prints for that fixture (VG "judge" = no deterministic check). Shares are counts on the panel (`out/panel_analysis.txt`): for NV, verdicts of that check where NV and R disagree and RF agrees with R (a defect under NVIDIA's own readings); for VG, all verdicts where VG and R disagree.

## 4. Findings

### Pipeline and data findings

| Id | Stage | Counterexample (exact input) and command | Contract broken (rules G1-G9 are CONTRACTS.md's general rules, not findings) | Share affected (panel) | Status in reference |
|---|---|---|---|---|---|
| G1 | Graded-text extraction, both pipelines (`final_answer_text`, `grade_judge._answer_text`, the same algorithm) | Thinking model, response never closes reasoning: `keywords:existence {"keywords": ["paris"]}`, raw `"The user asks for the capital of France. It is Paris, so the answer should name Paris"`; `repro.py existence:7dec56246841c648` → NV pass, VS pass, VG pass; contract fail. Unclosed `<think>` in a non-thinking answer: `punctuation:no_comma`, raw `"<think>Let me think about this, carefully, before"`; `repro.py no_comma:a7e96eb59284b5d9` → NV pass, VS pass, VG pass; contract fail (graded text becomes `""`, which passes every prohibition) | Contract rule G1: unclosed reasoning is an extraction failure and fails every check; the reasoning is never graded | 139 of 1,500 thinking responses (9.3%) have no `</think>`; NV rewards 1 of them. 24 panel responses get an empty SkyRL action; NV rewards 9 of them 1.0 | Marin code; NVIDIA's checkers do no extraction |
| G2 | Checker exceptions (SkyRL session, VS) | `last_word:last_word_answer {"last_word": "limit"}`, response `""`; `repro.py last_word_answer:ddbd7ccceea1e36a` → NV fail, VS fail, VG fail; contract fail, where NV's and VS's fail is an `IndexError` (printed), which the SkyRL session turns into `INFRA_ERROR` for the whole row, reward 0.0. VS on `copy:repeat_phrase {"phrase": "Time flies when having fun", "small_n": 2}`, `"Time flies when having fun. Time flies when having fun."`; `repro.py repeat_phrase:131167a3c5cf01bf` → NV fail, VS fail, VG pass; contract fail, where VS's fail is a `verification_error` (`RuntimeError: Instruction checker returned a nonboolean result`), so the row is unscored, not failed | Contract rule G9: an exception is a per-constraint grading failure counted apart from model accuracy; it must not discard the row's other verdicts | NV: 1 row (625 of 11,817 rows for an empty answer). VS: 473 rows unscored (2.0%): 266 json, 204 repeat_phrase, 3 other | NVIDIA: `LastWordAnswerChecker` raises on empty text, `RepeatPhraseChecker` returns `None`; the row-level handling is Marin's |
| G3 | Data + reference RNG: `length_constraints:nth_paragraph_first_word` | 77 constraints show "There should be 2 paragraphs … Paragraph 3 must start with word X". `{"num_paragraphs": 2, "nth_paragraph": 3, "first_word": "crash"}`, `"Crash one.\n\nCrash two."`; `repro.py nth_paragraph_first_word:e0a8e3b37f39cfe2` → NV pass, VS pass, VG fail; contract fail. NVIDIA's `build_description` redraws `nth_paragraph = randint(1, num+1)` from the unseeded global RNG, so the verdict is random (passes for 2 of 3 draws here) | The constraint is unsatisfiable; a verdict must not depend on RNG state | 161 panel verdicts; NV passes 13 (8.1%) | NVIDIA defect (randomized argument) + data defect |
| G4 | Data/prompt: `keywords:word_count_different_numbers` | The prompt says "the word skin should appear 2 times"; the row's hidden `relation` is `less than`. `{"keyword": "skin", "frequency": 2, "relation": "less than"}`, `"Skin care and skin health."`; `repro.py word_count_different_numbers:16032b4b762f13e2` → NV fail, VS fail, VG fail; contract pass. `"No mention here."`: `repro.py word_count_different_numbers:81094edcc6d9e311` → NV pass, VS pass, VG pass; contract fail | Exactly N under D-appear-n-times, and at least N under its other reading: `less than N` contradicts both | 309 of 1,015 NV verdicts (30.4%); VG 496 | NVIDIA applies the hidden relation (same in VG) |
| G5 | Unpinned or undeclared dependencies | `detectable_format:json_format`, `"{\"a\": 1}"`; `repro.py json_format:9c76e0fc33b1e713` → NV pass, VS fail, VG pass; contract pass, where VS's fail is `ModuleNotFoundError: No module named 'yaml'` (printed). `_ensure_nltk_data` downloads `punkt_tab` from the network when it is missing (no version) | Every input that can change a verdict is pinned | VS: all 266 json_format verdicts unscored in this environment | Marin code (verifyit's JSON-schema grader, SkyRL NLTK loader). Unverified: whether the production image has PyYAML |
| G6 | Prompt rendering of `P.S.` | 147 prompts show the marker as `P.S` (dot dropped when joined into a sentence). A response `"Main answer.\n\nP.S: thanks."` passes the marker as shown; NV requires `p.s.` with the dot: `repro.py postscript:652b99d5c847e5b7` → NV fail, VS fail, VG fail; contract pass | For these rows the dot is optional under every reading | 91 of 282 panel verdicts on these rows: NV fail, contract pass (section 5 counts them under D-postscript-dot) | NVIDIA (dot required) + data rendering |

### NVIDIA checker findings (NV and VS; VS differs only where noted)

| Id | Check | Counterexample and command | Contract broken | Share (NV, panel) | Status |
|---|---|---|---|---|---|
| F1 | copy:repeat_phrase | `{"phrase": "Time flies when having fun", "small_n": 2}`, `"Time flies when having fun. Time flies while having fun."`; `repro.py repeat_phrase:997ca6db1351b681` → NV pass, VS pass, VG fail; contract fail | Each of the N repetitions changes one center word; NVIDIA checks only the last match's difference count, so an unchanged copy counts. It returns `None` otherwise (G2 under VS) | 57 of 1,059 (5.4%) | Reference defect |
| F2 | count:count_unique | `"I run. You walk. We swim."`; `repro.py count_unique:7fae5ebaa9c9f55d` → NV fail, VS fail, VG judge; contract pass | Punctuation is not a word; NLTK tokens `.` repeat | 95 of 1,341 (7.1%) | Reference defect (judge-only in VG) |
| F3 | count:counting_composition | `{"n_sent": 3, "n_words": 2}`, `"Cats purr. Dogs bark. Birds sing.\n* * *\nFish swim. Frogs leap. Bees buzz.\n* * *\nSun shines. Rain falls. Wind blows."`; `repro.py counting_composition:ea1b49fff95395a0` → NV fail, VS fail, VG pass; contract pass | The text's divider is `* * *`; NVIDIA splits on `***` | 1 constraint in the data | Reference defect |
| F4 | detectable_content:number_placeholders | `{"num_placeholders": 1}`, `"Use [] here."`; `repro.py number_placeholders:cd35db9630a22d00` → NV pass, VS pass, VG fail; contract fail | An empty `[]` is not a placeholder | 9 of 1,201 | Reference defect |
| F5 | detectable_content:postscript | `{"postscript_marker": "P.S."}`, `"My answer, as the P.S. below explains, is yes."`; `repro.py postscript:899fb4c5fca86240` → NV pass, VS pass, VG fail; contract fail. `"Main answer.\n\nP.P.S. Extra note."`; `repro.py postscript:2b61359353ddcb4c` → NV pass, VS pass, VG fail; contract fail | The postscript starts with the marker; NVIDIA's pattern is unanchored and `p.s.` matches inside `p.p.s.` | 60 of 1,277 (4.7%), plus G6 | Reference defect |
| F6 | detectable_format:bigram_wrapping | `"<<I am>> <<at home>> with"`; `repro.py bigram_wrapping:e9046743777b7769` → NV pass, VS pass, VG judge; contract fail. `"<<I>> <<am>> <<at>> <<home>>"`; `repro.py bigram_wrapping:fa7ac263b29012a1` → NV pass, VS pass, VG judge; contract fail | Every word inside a two-word group | 184 of 1,157 (15.9%) | Reference defect (judge-only in VG) |
| F7 | detectable_format:constrained_response | `"My answer is yes. My answer is no."`; `repro.py constrained_response:4ac54e525f8a72e6` → NV pass, VS pass, VG fail; contract fail | One of the options, under both readings of D-constrained-extra | 3 of 243 (plus 75 by D-constrained-extra) | Reference defect |
| F8 | detectable_format:json_format | `"NaN"`; `repro.py json_format:21c8c07ba77a5e6a` → NV pass, VS fail, VG pass; contract fail | Valid JSON (RFC 8259) | 0 on the panel | Reference defect (VS fails it only because of G5) |
| F9 | detectable_format:multiple_sections | `{"num_sections": 2, "section_spliter": "SECTION"}`, `"SECTION 1\nIntro text.\nSECTION 2\nMore text.\nSECTION 3\nEven more."`; `repro.py multiple_sections:3a730a8fb4dd3bda` → NV pass, VS pass, VG fail; contract fail. `"SECTION 1\nSECTION 2\nOnly text here."`; `repro.py multiple_sections:0eed802de6fd5aa3` → NV pass, VS pass, VG pass; contract fail | Exactly N sections, each with content | 44 of 917 (4.8%) | Reference defect (`>=`) |
| F10 | detectable_format:number_bullet_lists | `{"num_bullets": 2}`, `"* Apples\n* Pears\n\n---\n\nThat is all."`; `repro.py number_bullet_lists:7130f5e7bd01fa66` → NV fail, VS fail, VG pass; contract pass. `"*Note: fruit list below*\n* Apples\n* Pears"`; `repro.py number_bullet_lists:f98381340cd6c07f` → NV fail, VS fail, VG pass; contract pass | A horizontal rule or an italic line is not a bullet point | 21 of 1,019 | Reference defect |
| F11 | detectable_format:number_highlighted_sections | `{"num_highlights": 1}`, `"Compute 2 * 3 * 4 now."`; `repro.py number_highlighted_sections:c050be3fbf59d850` → NV pass, VS pass, VG pass; contract fail | Multiplication signs are not emphasis | 8 of 1,070 | Reference defect (VG too) |
| F12 | detectable_format:sentence_hyphens | `"Cats are well-known pets.-They purr."`; `repro.py sentence_hyphens:71cd9de66666941b` → NV fail, VS fail, VG fail; contract pass. `"Calm minds begin – our therapists offer care – empathy drives every session"`; `repro.py sentence_hyphens:50084fe9ebfcf691` → NV pass, VS pass, VG fail; contract fail | Sentences joined by a hyphen with no spaces; a hyphenated word is allowed; clauses joined by spaced dashes are joined with spaces | 523 of 1,300 (40.2%) | Reference defect |
| F13 | detectable_format:square_brackets | `"[Hello], [world]."`; `repro.py square_brackets:6842e90cffe0daf8` → NV fail, VS fail, VG pass; contract pass | Punctuation outside the brackets is not a word | 84 of 1,079 (7.8%) | Reference defect |
| F14 | first_word:first_word_answer, first_word_sent | `{"first_word": "development"}`, `"Development, as a concept, matters."`; `repro.py first_word_answer:1eadfea8e6169452` → NV fail, VS fail, VG pass; contract pass. `{"first_word": "peace"}`, `"Peace is good!! Peace wins."`; `repro.py first_word_sent:a263215597f806ea` → NV fail, VS fail, VG pass; contract pass | Contract rules G3/G6: punctuation attached to a word is not part of it; `!!` ends one sentence | answer 113 of 1,089 (10.4%); sent 72 of 1,024 (7.0%) | Reference defect |
| F15 | keywords:keyword_specific_position | `{"keyword": "village", "n": 1, "m": 3}`, `"First, the village was quiet."`; `repro.py keyword_specific_position:a8635f1303db41e3` → NV fail, VS fail, VG pass; contract pass | The comma is not the 2nd word | 12 of 1,341 | Reference defect |
| F16 | keywords:no_adjacent_consecutive | `"**Apple** **banana** time."`; `repro.py no_adjacent_consecutive:d15d69484e7de768` → NV pass, VS pass, VG pass; contract fail. `"Item 1 2 go."`; `repro.py no_adjacent_consecutive:57cad6158f3a09b5` → NV fail, VS fail, VG pass; contract pass | Words' first letters, not markup or digits | 97 of 1,499 (6.5%) | Reference defect |
| F17 | keywords:palindrome | `"- Cats run fast\n- Dogs walk home"`; `repro.py palindrome:62307c5d5f02f08c` → NV pass, VS pass, VG fail; contract fail. `"Level up your game."`; `repro.py palindrome:34d60f6a352520bb` → NV fail, VS fail, VG pass; contract pass. `"Look at the radar."`; `repro.py palindrome:f6b247aacb1b02bf` → NV fail, VS fail, VG pass; contract pass | A dash is not a palindrome; case and attached punctuation do not matter | 56 of 1,165 (4.8%), plus 165 by D-palindrome-min | Reference defect |
| F18 | keywords:start_end | `"**Hello** world and **hello**"`; `repro.py start_end:0f490c0a2611346f` → NV pass, VS pass, VG pass; contract fail | Nothing, not even punctuation, after the last word; NLTK tokens `*` compare equal | 15 of 989 | Reference defect |
| F19 | keywords:word_once | `{"keyword": "fix"}`, `"Fix it and fix it again."`; `repro.py word_once:82e6638247be732c` → NV fail, VS fail, VG fail; contract pass. `"Please fix the prefix."`; `repro.py word_once:1dae2ca298402cf1` → NV fail, VS fail, VG pass; contract pass | "Include keyword X": at least once; NVIDIA requires exactly one substring match | 900 of 1,808 (49.8%) | Reference defect |
| F20 | language:response_language | `{"language": "es"}`, `""`; `repro.py response_language:d1023f2b285f477d` → NV pass, VS fail, VG judge; contract fail. `"12345 67890"`; `repro.py response_language:6eaf24bddfce5046` → NV pass, VS fail, VG judge; contract fail | A response with no letters is not in Spanish; NVIDIA counts `LangDetectException` as followed | 13 of 1,600; all 780 rows for an empty answer | Reference defect (VS raises instead, G2) |
| F21 | length_constraints:nth_paragraph_first_word | `{"num_paragraphs": 2, "nth_paragraph": 2, "first_word": "crash"}`, `"Intro.\n\nCrash: tests are useful."`; `repro.py nth_paragraph_first_word:b00e3044c541bf6a` → NV fail, VS fail, VG pass; contract pass | Punctuation after the first word (`:`, `;`) is not part of it | 16 of 1,048, plus G3 | Reference defect |
| F22 | letters:letter_counting | `{"N": 3, "relation": "at least"}`, `"Привет"`; `repro.py letter_counting:ae3c943defe220a4` → NV fail, VS fail, VG judge; contract pass | Cyrillic letters are letters; NVIDIA counts `[a-zA-Z]` | 101 of 961 (10.5%) | Reference defect |
| F23 | startend:end_checker | `{"end_phrase": "Any other questions?"}`, `"Here is the answer. Many other questions?"`; `repro.py end_checker:bae78e0cbb6e880f` → NV pass, VS pass, VG fail; contract fail | The phrase, not the tail of a longer word | 4 of 997 (plus 161 by D-end-case) | Reference defect |
| F24 | change_case:english_capital | `"SCHOOL OF REALISM"`; `repro.py english_capital:e7bf08ba54c47bb5` → NV fail, VS fail, VG pass; contract pass | English in capitals; langdetect on all-caps text misidentifies English | 104 of 1,534 (6.8%) | Reference defect |
| F25 | change_case:capital_word_frequency | `{"capital_frequency": 3, "capital_relation": "at least"}`, `"これはTEST、ROBOT、MATCHです。"`; `repro.py capital_word_frequency:67d9a736667d1ecc` → NV fail, VS fail, VG pass; contract pass | Three all-caps words; NLTK glues them to the CJK text into one token | 16 of 1,207 | Reference defect |
| F26 | Whitespace sensitivity (`sentence_hyphens`, `paragraphs2`) | Metamorphic P2: leading `"  \n"` and trailing `"\n\n\n\n"` change NVIDIA's verdict on 4 fixtures (`out/properties.json`) | Contract rule G2: surrounding whitespace is ignored | None: both pipelines strip the graded text first | Reference defect, masked by Marin's extraction |

### verifyit (VG) findings, against the contract and the reference

| Id | Check | Counterexample and command | Contract broken | Share (VG≠R, panel) | NVIDIA |
|---|---|---|---|---|---|
| V1 | change_case:capital_word_frequency | `{"capital_frequency": 1, "capital_relation": "at least"}`, `"ÉTÉ is a French word."`; `repro.py capital_word_frequency:c323f745351ec989` → NV pass, VS pass, VG fail; contract pass | ASCII-only words | 111 of 1,207 | Correct |
| V2 | change_case:english_capital, english_lowercase | `"C'EST MA RÉPONSE EN FRANÇAIS. JE PARLE DE LA VILLE ET DE SES HABITANTS."`; `repro.py english_capital:cc724e8993c59b77` → NV fail, VS fail, VG pass; contract fail. `"je suis allé à la plage avec mes amis hier soir et nous avons nagé."`; `repro.py english_lowercase:171fdb63030a313a` → NV fail, VS fail, VG pass; contract fail | "in English": verifyit checks only the case | 110 of 1,534; 142 of 1,208 | Checks the language |
| V3 | copy:repeat_phrase | `{"phrase": "Time flies when having fun", "small_n": 2}`, `"Time flies while having fun. Time flies during having fun."`; `repro.py repeat_phrase:c2733dd6e01dabc9` → NV pass, VS pass, VG fail; contract pass. `"Time flies when having fun. Time flies when having fun."`; `repro.py repeat_phrase:131167a3c5cf01bf` → NV fail, VS fail, VG pass; contract fail | Variants with one center word replaced; verifyit counts unchanged copies | 516 of 1,059 (48.7%) | Checks variants (with F1) |
| V4 | count:counting_composition | `{"n_sent": 3, "n_words": 2}`, `"Cats purr loudly. Dogs bark. Birds sing.\n* * *\n…"`; `repro.py counting_composition:9ea8bd6467eb8f0f` → NV fail, VS fail, VG pass; contract fail | Exactly n words per sentence, 3 paragraphs | 1 constraint | Exact (with F3) |
| V5 | count:lowercase_counting | `{"N": 2}`, `"The Cat Sat On The Mat."`; `repro.py lowercase_counting:ec46231f1e39c0e5` → NV pass, VS pass, VG fail; contract pass. `"the the the cat"`; `repro.py lowercase_counting:4f69700ac8bb105c` → NV fail, VS fail, VG pass; contract fail | "at most N times": verifyit requires at least N lowercase words | 1,359 of 1,712 (79.4%) | At most N in total (D-lowercase-scope) |
| V6 | detectable_content:postscript | `{"postscript_marker": "P.P.S"}`, `"Main answer.\n\n**P.P.S.** Thanks again."`; `repro.py postscript:cfe6cb6a06cea96f` → NV pass, VS pass, VG fail; contract pass. `"[Main] [text]\n[P.P.S] [extra]"`; `repro.py postscript:50fb9e5aaba637a4` → NV pass, VS pass, VG fail; contract pass | Emphasis or a bracket before the marker | 175 of 1,277 | Correct here |
| V7 | detectable_format:json_format | `"```JSON\n{\"a\": 1}\n```"`; `repro.py json_format:cea5532434e1e9f0` → NV pass, VS fail, VG fail; contract pass | Any fence tag; verifyit accepts only lowercase `json` | 0 on the panel | Correct |
| V8 | detectable_format:multiple_sections | `{"num_sections": 2, "section_spliter": "SECTION"}`, `"SECTION 1\nIntro.\nSECTION 2\nAs noted in SECTION 1, more."`; `repro.py multiple_sections:828b5ea6a1a9f6f8` → NV pass, VS pass, VG fail; contract pass | A mention inside a line is not a marker | 37 of 917 | Also counts mentions (`>=` hides it) |
| V9 | detectable_format:number_bullet_lists | `{"num_bullets": 2}`, `"* Apples\n* Pears\n\n* * *\n\nDone."`; `repro.py number_bullet_lists:f7b53df539989fd7` → NV fail, VS fail, VG fail; contract pass | `* * *` is a rule | 0 on the panel | Same defect (F10) |
| V10 | detectable_format:number_highlighted_sections | `{"num_highlights": 1}`, `"Note: ** ** here."`; `repro.py number_highlighted_sections:4cb615380bd1ad19` → NV fail, VS fail, VG pass; contract fail | An empty span is not a highlight | 6 of 1,070 | Correct here |
| V11 | detectable_format:sentence_hyphens | `"I like cats.-They are cute.-Dogs are fine too."`; `repro.py sentence_hyphens:27f9ae25ac9de442` → NV pass, VS pass, VG fail; contract pass | Sentences joined by hyphens; verifyit requires each sentence's words joined by hyphens | 277 of 1,300 | Checks sentence joins (with F12) |
| V12 | detectable_format:square_brackets | `"Hello [world]"`; `repro.py square_brackets:50a929bed99ac290` → NV fail, VS fail, VG pass; contract fail | Every word bracketed; verifyit passes any bracket | 859 of 1,079 (79.6%) | Checks every token |
| V13 | detectable_format:title | `"<<   >>\nRoses are red."`; `repro.py title:0f2bbadaf3ef597b` → NV fail, VS fail, VG pass; contract fail | A blank title | 11 of 1,189 | Correct |
| V14 | keywords:no_adjacent_consecutive | `"Big cats run."`; `repro.py no_adjacent_consecutive:89acdd0721db06a5` → NV fail, VS fail, VG pass; contract fail | First letters consecutive in the alphabet; verifyit checks for repeated adjacent words | 958 of 1,499 (63.9%) | Checks letters (with F16) |
| V15 | keywords:palindrome | `"Never odd or even, they say."`; `repro.py palindrome:8d440158f553dcbc` → NV fail, VS fail, VG fail; contract pass | A phrase palindrome | 207 of 1,165 (most by D-palindrome-min) | Same |
| V16 | keywords:start_end | `"Hello world and hello."`; `repro.py start_end:f0f7cf9665a3a781` → NV fail, VS fail, VG pass; contract fail | "not even punctuation" after the last word | 75 of 989 | Correct here |
| V17 | keywords:word_count_different_numbers | as G4 | as G4 | 496 of 1,015 | Same (G4) |
| V18 | keywords:word_once | `"Fix it and fix it again."`; `repro.py word_once:82e6638247be732c` → NV fail, VS fail, VG fail; contract pass | At least once | 882 of 1,808 (48.8%) | Same (F19) |
| V19 | length_constraints:number_paragraphs | `{"num_paragraphs": 2}`, `"First paragraph.\n***\nSecond paragraph."`; `repro.py number_paragraphs:c9821d7f814b8305` → NV pass, VS pass, VG fail; contract pass. `"First paragraph.\n\nSecond paragraph."`; `repro.py number_paragraphs:c60c470800b897bd` → NV fail, VS fail, VG pass; contract fail | Paragraphs separated by `***`; verifyit counts blank-line paragraphs | 583 of 1,345 (43.3%) | Splits on `***` |
| V20 | length_constraints:number_words | `{"num_words": 3, "relation": "at least"}`, `"Привет как дела"`; `repro.py number_words:06800fb5266403dd` → NV pass, VS pass, VG fail; contract pass | Non-Latin words are words | 207 of 1,443 | Correct |
| V21 | paragraphs:paragraphs, paragraphs2 | `"First.\n\nSecond."` for `paragraphs` (`***`); `repro.py paragraphs:304dc481367c2898` → NV fail, VS fail, VG pass; contract fail. `"First.\n\nSecond.\n\nThird."` for `paragraphs2`; `repro.py paragraphs2:f98bd08562c0b9c0` → NV fail, VS fail, VG pass; contract fail | Exactly 2 paragraphs, with the stated separator | 245 of 1,150; 442 of 1,391 | Exactly 2 |
| V22 | startend:quotation | `"'Hello world.'"`; `repro.py quotation:bab5e002a45571a5` → NV fail, VS fail, VG pass; contract fail. `"\""`; `repro.py quotation:87a304aa9523c5b0` → NV fail, VS fail, VG pass; contract fail | Double quotation marks around a response | 3 of 810 | Correct |

verifyit's `letters:letter_counting` counts words, not letters, but no pipeline runs it (judge-only in the gate; VS uses NVIDIA's). The full list of 263 fixtures with every grader's verdict is `audit/out/fixture_results.json`.

## 5. Decision entries for the maintainers

52 entries (`audit/CONTRACTS.md` v4, with an example of each reading). The proposed reading is the contract's; "NV side" is the reading NVIDIA's code follows; the count is panel verdicts where NV and R disagree and flipping that one switch makes R agree with NV.

| Entry | Proposed reading | NV side | Panel |
|---|---|---|---|
| D-lowercase-scope | each lowercase word at most N times (not the total) | other | 273 |
| D-keyword-substring | whole words only | other (`forbidden_words`: proposed) | 216 |
| D-word-cjk | each Han/kana character is a word | other | 207 |
| D-divider-line | `***` divides only on its own line | other | 194 |
| D-palindrome-min | at least 3 letters | other (any token) | 165 |
| D-end-case | the end phrase in its exact case | other | 161 |
| D-first-last-markup | ignore markdown and quotes around the first/last word | other (first word); proposed (last word) | 158 |
| D-word | `don't`, `well-known` are one word | other | 155 |
| D-appear-n-times | "appear N times" = exactly N | neither (hidden relation, G4) | 154 |
| D-sentence-lines | a line without terminal punctuation is a sentence | other | 124 |
| D-postscript-dot | the marker's final dot is optional | other | 92 |
| D-constrained-extra | exactly one option, nothing else | other (contains) | 75 |
| D-postscript-line | the marker begins a line | other | 75 |
| D-postscript-end | the postscript is the last block | other | 69 |
| D-consecutive-order | consecutive in either order | other (ascending) | 48 |
| D-repeat-copies | unchanged copies neither count nor fail | other | 30 |
| D-two-sep-edge | a separator at either end is an extra separator | other | 29 |
| D-comma-variants | full-width, ideographic, Arabic commas count | other | 27 |
| D-start-end-single | one word passes start_end | other | 26 |
| D-keyword-case | keyword occurrence ignores case | proposed (`keyword_specific_position`: other) | 19 |
| D-repeat-center | any word but the first and last | proposed | 16 |
| D-brackets-per-word | each word in its own brackets | proposed | 13 |
| D-exclamation-variants | `！`, `¡`, `‼` count | other | 9 |
| D-end-trailing | closing markup may follow the phrase | other | 7 |
| D-consecutive-script | the letters' own alphabet (Latin, Cyrillic, Greek) | proposed (code points) | 6 |
| D-paragraph-blank | several blank lines are one separator | other | 6 |
| D-quote-curly | curly quotes accepted | other | 4 |
| D-unique-case | `The` and `the` are the same word | other | 2 |
| D-start-markup | leading markup before the first word ignored | other | 1 |
| D-sections-number | sections numbered 1..N in order | other | 1 |
| D-dot-variants | `．` and `…` count, `。` does not | other | 1 |
| D-think-nonthinking | a non-thinking answer is graded whole; only a leading `<think>` block is reasoning | other | (G1) |
| D-allcaps-short, D-case-scope, D-two-sep, D-two-different, D-placeholder, D-postscript-case, D-bigram-odd, D-json-scalar, D-sections-case, D-sections-preamble, D-bullet-markers, D-bullet-nested, D-highlight-bold, D-hyphens-single, D-hyphen-dash, D-title-position, D-letter-case, D-letter-unit | see CONTRACTS.md | `NVIDIA_SIDE` in `replacement.py` | 0 each |
| D-english-mixed, D-language-mixed | see CONTRACTS.md | proposed | not measured (no switch flip computed) |

57 further NV≠R verdicts follow no single entry but a combination (listed in `out/panel_summary.json`). The decision classification of panel disagreements is approximate: it asks whether RF (NVIDIA's side of every entry) agrees with NV.

## 6. Panel details

- Stored responses only: vLLM 0.11.0, each model's chat template at a pinned revision, token limit 2,048 (8,192 thinking). 1,063 responses stopped at the token limit (65, 92, 81, 620, 166, 39 per run); they are graded as written.
- Held-out set, fixed before grading: rows with `int(sha256(uuid), 16) % 10 < 3`. Contract v4 and the replacement changes it caused were developed on the other 70% only (`scripts/inspect_disagreements.py` skips held-out rows). Held-out results are in section 1 and `out/panel_analysis.txt`.
- Per-check pass rates for every grader and the disagreement counts are in `out/panel_analysis.txt`; per-response verdicts in `out/panel_A.jsonl` (sha256 `e155e6da64e745d5bf0057d8a5d295a360864a363bcc99e1b2d612d26507eee0`) and `out/panel_B.jsonl` (sha256 `56600a47201a79aa4fd268764a33505dac90ca2cd7f6c3cb6f4cb6dd8d892790`).
- Content-free responses (all 11,817 rows): an empty answer gets NV reward 1.0 on 1,702 rows (14.4%; contract 1,437, rows whose constraints are all prohibitions) and `INFRA_ERROR` on 625; a restatement of the prompt gets NV 1.0 on 746 rows (contract 458), passing `constrained_response` (100%), `postscript` (77%) and `palindrome` (100%) by echoing the instructions; `"the " * 200` gets NV 1.0 on 729 rows. VG lets an empty answer through to the judge on 810 rows.

## 7. Step 6 not run: what the recommendation still needs

The recommendation rests on disagreement with an unreviewed replacement. It would change if a blinded review found the replacement no better than the current graders. Criterion, recorded in `ISSUE.md` before any review: the replacement passes every fixture (it does: 263 of 263), its scored coverage is complete (it is), and its error rate is lower than NV's, and lower than VG's on the deterministic constraints, with paired 95% intervals that exclude zero. If the replacement's error rate is not lower, fix only the findings above whose fixtures are unambiguous (deps empty) and keep NVIDIA's readings.

The review needs: a frozen, scripted sample from the held-out responses (16,552 constraint verdicts), stratified by NV≠R (1,662 held-out verdicts; sample all or most) and NV=R (about 90% of verdicts; about 170 cases with a consensus give an upper bound near 2% when no error is found), plus a VG≠R stratum (2,432 held-out verdicts); two reviewers per case with the prompt in `skill/references/reviewer-prompt.md`, no grader verdicts or model names shown; per-stratum error rates with bootstrap intervals, Cohen's kappa, and the disputed cases. It should include `english_capital`, `english_lowercase` and `response_language` cases, where the replacement's language identification is langdetect on the text without code and URLs and is itself a possible error source.

## 8. Files

- `audit/ISSUE.md`: the record (pins, contract hashes and times, changes with reasons, decisions, step results, progress).
- `audit/CONTRACTS.md` (v4) and `audit/frozen/CONTRACTS_v1.md` … `_v4.md`; `audit/frozen/row_hashes.tsv`; `audit/frozen/SHA256SUMS`.
- `audit/replacement.py` (replacement grader, 52 switches, `fixes_only()`), `audit/harness.py` (how each pipeline is run), `audit/repro.py`.
- `audit/tests/` (`fixture_defs.py`, `test_fixtures.py`, `expected_wrong.json`, `test_generated.py`, `expected_wrong_generated.json`), `audit/fixtures.jsonl` (462 labeled responses: 263 hand-written, 10 property, 4 metamorphic, 3 fuzz, 182 content-free).
- `audit/scripts/` (every script named above), `audit/out/` (results).
