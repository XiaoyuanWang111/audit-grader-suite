# Audit report: the RLVR1 instruction-following graders

Graders audited, on the 11,817 rows of `case/data/rlvr1_instruction_following.jsonl` (28,219
constraints, 47 instruction ids):

- **Grader A**, the SkyRL reward: `final_answer_text`, then `grade_instruction_following`, which runs
  NVIDIA's verifiable-instructions checkers (Marin `af9c678`, NVIDIA `f46a5ac`). NVIDIA's checkers
  are the data's own grader and the reference implementation for grader B.
- **Grader B**, the deterministic gate of Marin's task-curation grader: reasoning stripping, then
  verifyit's `ifeval` check of every constraint outside `SEMANTIC_INSTRUCTION_CONSTRAINTS`.

The audit followed `skill/SKILL.md` with the substitutions of this offline exercise. The record
is in `audit/ISSUE.md`; the contracts in `audit/CONTRACTS.md` (v4); everything here can be rebuilt
with `bash audit/scripts/run_all.sh` (regrading the panel can move grader A's counts by a few rows,
section 5). Report written 2026-11-12, 11:59–12:10 UTC.

## 1. Result

**Error rate: not estimated.** Step 6 (blinded review) was not run in this exercise, so no error rate
and no interval exist for either grader. What the audit measured instead is how often each grader
disagrees with the replacement grader, a direct implementation of the contracts that no reviewer has
checked:

| On the stored panel (23,315 responses, 6 runs of 4 models) | Grader A | Grader B |
|---|---|---|
| Constraint verdicts | 55,783 | 50,724 (the other 5,059 go to the LLM judge) |
| Differ from the contract (proposed readings) | 10.3% | 17.2% |
| … because of a finding (wrong under every reading) | 4.6% | 12.0% |
| … only because of a decision entry (the reading is open) | 5.6% | 5.0% |
| … because the response's reasoning never closed | 84 verdicts | 113 verdicts |

**Effect on scores.** Fixing only the findings (keeping each grader's reading on every decision
entry) moves grader A's row score by −1.3 to +5.6 points per run and grader B's gate pass rate by
−7.9 to +4.7 points. Rerunning the same greedy decode of Qwen3-4B-Instruct-2507 (1,000 rows; 494
answers changed) moved grader A's score by +0.2 points (16 rows changed) and grader B's gate pass
rate by +0.1 points (27 rows changed). Every finding-only change in the table exceeds that rerun difference.

| Run | Grader A score | A, findings fixed | A, contract (all proposed readings) [95% CI of the change] | B gate pass | B, findings fixed | B, contract [95% CI] |
|---|---|---|---|---|---|---|
| OLMo-2-1124-7B-Instruct, sample0 (3,998) | 19.1 | 20.3 | 18.1 (−1.0 [−2.0, −0.1]) | 31.6 | 23.9 | 23.7 (−7.9 [−9.0, −6.5]) |
| Qwen2.5-7B-Instruct, sample0 (4,000) | 20.0 | 18.7 | 19.7 (−0.4 [−1.5, +0.7]) | 32.5 | 24.6 | 24.6 (−7.9 [−9.2, −6.6]) |
| Qwen3-4B-Instruct-2507, greedy (1,000) | 29.3 | 31.6 | 34.6 (+5.3 [+3.3, +7.3]) | 49.6 | 41.8 | 42.8 (−6.8 [−9.6, −4.1]) |
| Qwen3-4B-Instruct-2507, greedy rerun (1,000) | 29.5 | 32.2 | 34.9 (+5.4 [+3.4, +7.4]) | 49.7 | 42.3 | 43.3 (−6.4 [−9.2, −3.5]) |
| Qwen3-4B-Instruct-2507, sample0 (11,817) | 29.6 | 32.7 | 34.8 (+5.3 [+4.6, +5.9]) | 47.3 | 41.3 | 43.3 (−4.1 [−5.0, −3.1]) |
| Qwen3-4B-Thinking-2507, sample0 (1,500) | 55.3 | 60.9 | 65.5 (+10.2 [+8.1, +12.1]) | 63.3 | 67.9 | 68.7 (+5.4 [+3.3, +7.7]) |

Scores are percentages of rows (grader A: binary reward; grader B: rows whose deterministic gate
passes, which then go to the LLM judge). Intervals are paired bootstrap intervals over rows (1,000
resamples, seed 20261112).

**As an RL reward.** Of grader A's 6,475 rewards of 1.0 on the panel, 986 (15.2%) are false rewards
by the contract's proposed readings: 435 rows have at least one finding behind the pass, 550 only
decision entries, 1 an unclosed reasoning block. On the held-out part of the panel (every response
after the first 300 of each run file, 21,515 responses), the share is 919 of 5,868 (15.7%). The
false-reward share is highest for the two weakest models (Qwen2.5 32.2%, OLMo 25.6%).

**Content-free answers.** The empty answer gets grader A's reward 1.0 on 1,702 rows (14.4%) and
passes grader B's gate on 716 rows. The proposed reading of `D-empty` fails it everywhere; the
literal reading would pass 2,022 rows. 81 of the 1,702 are wrong under every reading (A-F2).
Example (row with `response_language`, `first_word_sent`, `count_unique`):
`$PY scripts/repro.py row eb817d5f-9f71-4bac-9f5e-9863c5e3957a ''` → A 1.0, B failed, C 0.0.

**Recommendation: fix both graders**, provisionally until step 6 has run (section 6).

- Grader A: fix A-F1 to A-F22 and G1–G4 in the reward wrapper or in a patched copy of the checkers;
  drop or repair the 77 unsatisfiable rows (G3) and the hidden `relation` of
  `keywords:word_count_different_numbers` (A-F2); treat a checker exception as a grading failure
  outside the reward (G4); decide `D-empty` before training, since an RL policy can learn to answer
  nothing on the 1,702 rows.
- Grader B: B-F1 to B-F5 replace the instruction with a different one (`repeat_phrase`,
  `lowercase_counting`, `no_adjacent_consecutive`, the three paragraph checks); verifyit should port
  NVIDIA's semantics for these and fix the word and sentence tokenizers (B-F10, B-F11).
- Both: the decision entries of section 4 go to the maintainers; the replacement grader
  (`audit/replacement/contract_grader.py`) has one switch per entry and can serve as the fixed
  grader once the entries are decided and step 6 has measured it.

## 2. What was run

| Step | Status |
|---|---|
| 1. Pin inputs | Done (`ISSUE.md`). Unpinned: the panel's stop sequences, chat templates and reasoning parser (U1), the parquet itself (U2, no network), the RL run's generation settings (U3); NLTK data is downloaded at grading time when missing (G5). |
| 2. Contracts | Written from the 47 requirement texts before any grader code was read (v1 hash recorded 11:22:25Z). Three later versions (v2–v4), each change with its reason in `ISSUE.md` and `CONTRACTS.md`; v4 (`audit/frozen/CONTRACTS_v4.md`, sha256 `076eafa8…`) is final. |
| 3. Fixtures | 945 fixtures in `audit/fixtures.jsonl` after removing duplicates (205 hand-written, 3 extraction, 514 property and metamorphic, 99 fuzz, 124 content-free), run as `pytest` tests in `audit/tests/` against both graders and the replacement; grader failures are `xfail(strict=True)` from `audit/tests/known_failures.json`. Replacement grader built because fixtures showed fixable defects. |
| 4. Reference and stress | NVIDIA's repository has no unit tests and verifyit's and SkyRL's tests are not in the case, so no grader test that encodes a decision could be listed. Property and metamorphic edits, fuzzing (300 random responses per check, seed 20261112) and content-free responses on all rows. |
| 5. Panel | The stored responses in `case/panel/` only (no generation): every response graded by A, B and the replacement. The first 300 responses of each run file are the development part; the replacement was changed once (v4) after inspecting development disagreements only. |
| 6. Blinded review | Not run (no reviewers). No sample drawn or frozen. |
| Repository, research branch, HF dataset, job launcher | Not available; frozen files are in `audit/frozen/` with their sha256 in `ISSUE.md`. |

Classification rule for every wrong verdict (fixtures and panel): it is a **decision** when some
combination of non-proposed readings of the check's decision entries gives the grader's verdict (the
entries are named), and a **finding** otherwise (`audit/scripts/fixture_lib.py`, `explain`).

## 3. Findings

Reproduce any counterexample from `audit/` in Git Bash:

```bash
cd <W>/audit
export NLTK_DATA=<W>/case/deps/nltk_data PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8
PY=../.venv/Scripts/python.exe
```

`scripts/repro.py check ID KWARGS RESPONSE` prints grader A's verdict (`A`), grader B's (`B`) and the
contract's (`C`); `scripts/repro.py row UUID RESPONSE` prints the row reward. In the tables, `…`
stands for the same command as the one before it with only the response changed; the appendix
lists all 56 commands in full. All 56 were run exactly as printed there and print the verdicts
given (`$PY scripts/check_report_appendix.py; bash work/appendix_commands.sh | $PY
scripts/check_commands.py` → "56 of 56"). "Panel share" is the share of the check's panel verdicts on which the
grader differs from the contract and the difference is a finding (it covers every finding of that
check). "Reference" says whether the other grader shares the defect; NVIDIA's checkers are grader A.

### Pipeline and data

| Id | Stage | Counterexample (exact input) and verdicts | Contract broken | Panel share | Reference |
|---|---|---|---|---|---|
| G1 | Graded-text extraction, A and B | A reasoning model's response whose reasoning never closes, `no_comma`: `$PY scripts/repro.py check punctuation:no_comma null 'Okay the user wants a short answer so I will think about it' --reasoning` → A pass, B pass, C fail | Section 0: unclosed reasoning is an extraction failure and fails every check. Both extractors grade the whole reasoning text when the opening `<think>` came from the chat template. | 139 of 1,500 thinking responses (9.3%) never close; A passes 84 of their 350 constraints and gives 1 row reward; B's gate passes 18 of them | Same in both (`final_answer_text`, `_answer_text`) |
| G2 | Extraction, A and B | A non-reasoning answer that mentions the tag: `$PY scripts/repro.py check keywords:existence '{"keywords": ["tag"]}' 'Write the <think> tag before your notes.'` → A fail, B fail, C pass | Section 0: a non-reasoning model's whole response is graded. An unmatched opening marker empties the answer. | 22 panel answers emptied; A gives 8 of them reward 1.0 (empty-answer passes, see `D-empty`) | Same in both |
| G3 | Data and A | 77 rows ask for paragraph N+1 of N (`There should be 2 paragraphs … Paragraph 3 must start with word history`), e.g. `$PY scripts/repro.py check length_constraints:nth_paragraph_first_word '{"num_paragraphs": 2, "nth_paragraph": 3, "first_word": "history"}' $'History is long.\n\nHistory is fun.' --runs 30` → A passes in some of the 30 gradings and fails in the others (the count varies by run), B fail, C fail | The requirement cannot be met; A's `build_description` replaces the out-of-range index with an unseeded `random.randint(1, N+1)`, so the verdict is random and checks a paragraph the model was not asked about | 161 panel responses on these rows; for 23, A's row reward changed across 10 gradings of the same response | B fails these rows (correct); the rows should be dropped or repaired |
| G4 | A, exception handling | `$PY scripts/repro.py check last_word:last_word_answer '{"last_word": "hello"}' ' '` → A raises `IndexError` (row becomes `INFRA_ERROR` "Verifier configuration failed", reward 0.0), B fail, C fail | Section 0: an exception is a grading failure; here an empty answer, a model failure, is reported as a verifier configuration error. B instead counts any crash as a failed constraint, silently (none observed). | 1 panel row; 625 rows on the empty answer; 11 of 300 fuzz inputs | B has no exception here |
| G5 | Inputs | `_ensure_nltk_data` downloads `punkt_tab` at grading time when it is missing (no version or hash); nltk 3.10.3 maps the `punkt/english.pickle` path that `count_sentences` loads to `punkt_tab` | Step 1: every input that can change a verdict is pinned | — | — |

### Grader A (SkyRL reward, NVIDIA checkers)

| Id | Check | Counterexample and verdicts | Contract broken | Panel share | In grader B |
|---|---|---|---|---|---|
| A-F1 | `keywords:word_once` | `$PY scripts/repro.py check keywords:word_once '{"keyword": "fix"}' 'Fix it now and fix it well.'` → A fail (C pass); `… 'Let me fix the prefix.'` → A fail (substring count 2) | "Include keyword fix in your response" sets no maximum; the checker requires exactly one substring match | 819 of 1,808 (45%) | Same (exactly one, whole word) |
| A-F2 | `keywords:word_count_different_numbers` | `$PY scripts/repro.py check keywords:word_count_different_numbers '{"keyword": "box", "frequency": 2, "relation": "less than"}' 'A box and another box.'` → A fail; `… 'No crates here.'` → A pass | The text says "should appear 2 times"; the kwarg `relation` (206 of 526 rows "less than") is not shown to the model, and "less than N" contradicts every reading | 263 of 1,015 (26%) | Same |
| A-F3 | `first_word:first_word_answer`, `first_word_sent`, `nth_paragraph_first_word` | `$PY scripts/repro.py check first_word:first_word_answer '{"first_word": "development"}' 'Development, as a concept, matters.'` → A fail; `$PY scripts/repro.py check length_constraints:nth_paragraph_first_word '{"num_paragraphs": 2, "nth_paragraph": 2, "first_word": "if"}' $'Cats are nice.\n\nIf: you like dogs, fine.'` → A fail | Punctuation or a quotation mark next to a word is not part of it | 114 of 1,089 (10.5%), 80 of 1,024 (7.8%), 17 of 1,048 | B correct |
| A-F4 | `keywords:keyword_specific_position` | `$PY scripts/repro.py check keywords:keyword_specific_position '{"keyword": "shot", "n": 2, "m": 3}' 'I went out. Then, the shot came.'` → A fail; `… '{"keyword": "repeat", "n": 1, "m": 1}' 'Repeat after me. Good.'` → A fail | Punctuation tokens are counted as words; a capitalized sentence-initial keyword does not match | 13 of 1,341 | B correct |
| A-F5 | `count:count_unique` | `$PY scripts/repro.py check count:count_unique null 'Apples, pears, plums.'` → A fail | Repeated commas and periods are not repeated words | 99 of 1,341 (7.4%) | Judged by the LLM in B |
| A-F6 | `count:counting_composition` | `$PY scripts/repro.py check count:counting_composition '{"n_sent": 3, "n_words": 2}' $'Birds sing. Cats sleep. Dogs run.\n* * *\nRain falls. Wind blows. Trees sway.\n* * *\nKids play. Parents watch. Time flies.'` → A fail | The text's divider is `* * *` (A splits on `***` only) and a period is not a word (A counts it) | 1 row in the data | B wrong differently (B-F7) |
| A-F7 | `detectable_format:bigram_wrapping` | `$PY scripts/repro.py check detectable_format:bigram_wrapping null '<<I am>> home'` → A pass; `… Hello` → A pass | Every word must be inside a two-word `<<…>>` group; A never checks an odd last word, and text without spaces (Chinese) is one word | 183 of 1,157 (15.8%) | Judged by the LLM in B |
| A-F8 | `detectable_format:constrained_response` | `$PY scripts/repro.py check detectable_format:constrained_response null 'My answer is yes. My answer is no.'` → A pass | "Answer with one of the following options" excludes giving two | 3 of 243 | B correct |
| A-F9 | `detectable_format:multiple_sections` | `$PY scripts/repro.py check detectable_format:multiple_sections '{"num_sections": 2, "section_spliter": "SECTION"}' $'SECTION 1\nCats are great; see SECTION 2 for dogs.'` → A pass, B pass | An inline mention does not mark the beginning of a section | 44 of 917 (4.8%) | Same (39 of 917) |
| A-F10 | `detectable_format:number_bullet_lists` | `$PY scripts/repro.py check detectable_format:number_bullet_lists '{"num_bullets": 2}' $'* Apples.\n* Bananas.\n\n---\n\nThat is all.'` → A fail; `… $'*Note* the list:\n* Apples.\n* Bananas.'` → A fail | A `---` divider and an italic word at line start are not bullet points | 22 of 1,019 | B correct |
| A-F11 | `detectable_format:square_brackets` | `$PY scripts/repro.py check detectable_format:square_brackets null '[I] [like] [cats].'` → A fail | A period outside the brackets is not a word | 73 of 1,079 (6.8%) | B wrong differently (B-F6) |
| A-F12 | `keywords:no_adjacent_consecutive` | `$PY scripts/repro.py check keywords:no_adjacent_consecutive null '(apple) banana split.'` → A pass; `… 'Pick 1, 2 or 9'` → A fail | A reads the first character of each whitespace token, so a word behind a parenthesis or quote is skipped and digits count as letters | 162 of 1,499 (10.8%) | B checks a different rule (B-F3) |
| A-F13 | `keywords:palindrome` | `$PY scripts/repro.py check keywords:palindrome null 'Cats run - dogs walk.'` → A pass | A symbol token (`-`, `*`, `---`, `:`) is not a palindrome | 45 of 1,165 | B passes `---` (B-F12) |
| A-F14 | `detectable_content:postscript` | `$PY scripts/repro.py check detectable_content:postscript '{"postscript_marker": "P.S."}' 'Ship the parcel with U.P.S. today.'` → A pass | A searches `p.s.` anywhere, inside words too | 61 of 1,277 (4.8%) | B correct |
| A-F15 | `language:response_language` | `$PY scripts/repro.py check language:response_language '{"language": "fr"}' '12345 67890'` → A pass | A passes whenever langdetect raises, so a text without letters passes (an empty text passes too, which is `D-empty`) | 8 of 1,600 | Judged by the LLM in B |
| A-F16 | `length_constraints:number_paragraphs`, `paragraphs:paragraphs` | `$PY scripts/repro.py check length_constraints:number_paragraphs '{"num_paragraphs": 2}' '***Cats*** are nice and dogs are loyal.'` → A pass | A splits at any `***`, also bold-italic markup inside a line; a markdown divider is a line of its own | 81 of 1,345 (6.0%), 104 of 1,150 (9.0%) | B ignores `***` altogether (B-F4, B-F5) |
| A-F17 | sentence checks (`first_word_sent`, `last_word_sent`, `keyword_specific_position`, `number_sentences`) | `$PY scripts/repro.py check first_word:first_word_sent '{"first_word": "peace"}' '1. Peace is good. Peace is calm.'` → A fail, B fail | A list label `1.` is not a sentence | part of the sentence-check shares above | Same in B |
| A-F18 | `copy:repeat_phrase` | `$PY scripts/repro.py check copy:repeat_phrase '{"phrase": "Laughter is the best medicine", "small_n": 2}' 'Laughter is the best medicine. Laughter is our best medicine.'` → A pass | Only the last match must differ in A; an unchanged earlier copy passes, so one transformation is counted as two | 57 of 1,059 (5.4%) | B wrong differently (B-F1) |
| A-F19 | `change_case:english_capital` | `$PY scripts/repro.py check change_case:english_capital null 'I LIKE CATS AND DOGS VERY MUCH.'` → A fail | langdetect on upper-case text often misses English; the case requirement is met and the text is English | 77 of 1,534 (5.0%) | B skips the English test (`D-english`) |
| A-F20 | `length_constraints:number_sentences` (and every sentence check) | `$PY scripts/repro.py check length_constraints:number_sentences '{"num_sentences": 3, "relation": "at least"}' '我很好。你呢？他也很好。'` → A fail, B fail | `。` and `？` end sentences; A's and B's splitters need a space after the mark | 71 of 1,131 (6.3%) | Same in B |
| A-F21 | `count:lowercase_counting`, `letters:letter_counting` | `$PY scripts/repro.py check count:lowercase_counting '{"N": 2}' '<b>I</b> like it'` → A fail | The letters of an inline HTML tag are not words or letters | rare (property tests only) | B correct |
| A-F22 | `count:count_unique` | `$PY scripts/repro.py check count:count_unique null '**Every** word here appears once.'` → A fail | Markdown asterisks are not repeated words | within A-F5's share | Judged by the LLM in B |

### Grader B (task-curation gate, verifyit `ifeval`)

| Id | Check | Counterexample and verdicts | Contract broken | Panel share | In grader A (reference) |
|---|---|---|---|---|---|
| B-F1 | `copy:repeat_phrase` | `$PY scripts/repro.py check copy:repeat_phrase '{"phrase": "Laughter is the best medicine", "small_n": 2}' 'Laughter is a best medicine. Laughter is our best medicine.'` → B fail (C pass); `… 'Laughter is the best medicine. Laughter is the best medicine.'` → B pass | B counts unchanged copies (at least n); the text asks for n copies each with one centre word replaced | 485 of 1,059 (46%) | A correct on both |
| B-F2 | `count:lowercase_counting` | `$PY scripts/repro.py check count:lowercase_counting '{"N": 2}' 'the the the end'` → B pass; `… 'Hello World'` → B fail | B requires at least N lowercase words; the text says at most | 1,219 of 1,712 (71%) | A correct on both |
| B-F3 | `keywords:no_adjacent_consecutive` | `$PY scripts/repro.py check keywords:no_adjacent_consecutive null 'A big dog.'` → B pass; `… 'Tom ate ate cake.'` → B fail | B checks adjacent duplicate words, not consecutive initial letters | 870 of 1,499 (58%) | A correct on both |
| B-F4 | `length_constraints:number_paragraphs` | `$PY scripts/repro.py check length_constraints:number_paragraphs '{"num_paragraphs": 2}' $'Cats are nice.\n***\nDogs are loyal.'` → B fail; `… $'Cats are nice.\n\nDogs are loyal.'` → B pass | B splits at blank lines and ignores the `***` divider the text names | 480 of 1,345 (36%) | A correct on both |
| B-F5 | `paragraphs:paragraphs`, `paragraphs:paragraphs2` | `$PY scripts/repro.py check paragraphs:paragraphs '{}' $'Cats.\n***\nDogs.\n***\nBirds.'` → B pass; `$PY scripts/repro.py check paragraphs:paragraphs2 '{}' $'Cats.\n\nDogs.\n\nBirds.'` → B pass | "There should be 2 paragraphs": B passes 2 or more, with either separator | 240 of 1,150 (21%), 435 of 1,391 (31%) | A correct on both |
| B-F6 | `detectable_format:square_brackets` | `$PY scripts/repro.py check detectable_format:square_brackets null '[I] like cats.'` → B pass | Every word must be enclosed; B needs one bracketed span | 724 of 1,079 (67%) | A correct |
| B-F7 | `count:counting_composition` | `$PY scripts/repro.py check count:counting_composition '{"n_sent": 3, "n_words": 2}' 'Birds sing. Cats sleep. Dogs run.'` → B pass | B ignores the three paragraphs and treats "exactly" as "at least" | 1 row in the data | A wrong differently (A-F6) |
| B-F8 | `keywords:start_end` | `$PY scripts/repro.py check keywords:start_end null 'Hello world and hello.'` → B pass | "do not write anything after the last word, not even punctuation" | 65 of 989 (6.6%) | A correct |
| B-F9 | `startend:quotation` | `$PY scripts/repro.py check startend:quotation null $'\'Hello there.\''` → B pass | Single quotes are not double quotation marks | 0 on the panel | A correct |
| B-F10 | word tokenizer (`number_words`, first and last word, `capital_word_frequency`, `palindrome`, `keyword_specific_position`) | `$PY scripts/repro.py check length_constraints:number_words '{"num_words": 5, "relation": "at least"}' 'Привет как дела у тебя'` → B fail; `$PY scripts/repro.py check first_word:first_word_answer '{"first_word": "development"}' 'Привет development'` → B pass | B's `WORD` is `[A-Za-z0-9'\-]+`: words in other scripts and accented letters are dropped or split, and a lone `-` bullet is a word | 59 of 1,443 (4.1%) for `number_words`; 20 of 1,207 for `capital_word_frequency` | A counts Unicode words |
| B-F11 | sentence splitter | `$PY scripts/repro.py check length_constraints:number_sentences '{"num_sentences": 3, "relation": "at least"}' 'Dr. Smith runs. You walk.'` → B pass | An abbreviation does not end a sentence | 87 of 1,131 (7.7%) with A-F20 | A handles `Dr.` |
| B-F12 | `keywords:palindrome` | `$PY scripts/repro.py check keywords:palindrome null 'A man, a plan, a canal: Panama!'` → B fail; `… $'Cats run.\n\n---\n\nDogs walk.'` → B pass | A phrase palindrome counts; a `---` divider is not a word | 145 of 1,165 (12.4%) | A passes both (A-F13 for `---`) |
| B-F13 | `detectable_format:number_highlighted_sections` | `$PY scripts/repro.py check detectable_format:number_highlighted_sections '{"num_highlights": 1}' $'Intro.\n\n* * *\n\nEnd.'` → B pass | A `* * *` divider is not a highlighted section | 32 of 1,070 | A correct |
| B-F14 | `detectable_format:title` | `$PY scripts/repro.py check detectable_format:title null $'<< >>\nIt was fine.'` → B pass | An empty title is not a title | 2 of 1,189 | A correct |
| B-F15 | `detectable_format:json_format` | `$PY scripts/repro.py check detectable_format:json_format null '```json {"answer": "Paris"} ```'` → B fail | The text allows markdown ticks; B needs a line break after the opening fence | 0 on the panel | A correct |

Coverage: grader B gives no deterministic verdict to 2,539 of the 28,219 constraints (the four
semantic ids) and 94 rows have no deterministic constraint at all; those go to the LLM judge, which
is not part of this case. Grader A scored every panel row except 1 (`INFRA_ERROR`, G4).

## 4. Decision entries for the maintainers

Each entry's readings are in `audit/CONTRACTS.md`. "Panel" counts the verdicts whose difference from
the proposed reading the entry explains (a verdict can involve several entries).

| Entry | Question | Proposed | Grader A | Grader B | Panel A / B |
|---|---|---|---|---|---|
| D-empty | Does an empty answer pass checks that only forbid something? | No, it fails every check | Yes (1,702 rows reward 1.0) | Yes (716 rows to the judge) | 2 / 0 (content-free: 1,621 rows) |
| D-hyphen-scope | `sentence_hyphens`: hyphens between sentences, or inside every sentence? | Between sentences | Between | Inside | 576 / 816 |
| D-hyphen-single | One sentence: pass? | Pass | Pass | Fail | 239 / – |
| D-keyword-match | Whole word, case-insensitive vs substring | Whole word | Substring (`existence`, `frequency`, `word_once`) | Whole word | 301 / 149 |
| D-lowercase-counting-scope | "all lowercase words should appear at most N times": each word, or in total? | Each word | Total | (B-F2) | 272 / 63 |
| D-palindrome-length | Do `a`, `I` count? | No (3+ letters) | Yes | No | 210 / 7 |
| D-bare-count | "should appear N times": exactly or at least? | Exactly | Hidden `relation` (A-F2) | Same | 172 / 170 |
| D-divider-edge | A `***` at the very start or end | Fails | Ignored | (B-F4) | 140 / 52 |
| D-sentence | Does a line break end a sentence? | Yes | No | No | 135 / 134 |
| D-edge-word | Markup around the first or last word | Skipped | Not skipped (first word) | Skipped | 135 / 4 |
| D-word | Word = joined runs vs whitespace tokens vs split at `'`/`-` | Joined | Split (`\w+`, `word_tokenize`) | ASCII runs | 123 / 93 |
| D-postscript-position, -marker, -case, -line, -pps | Where and how the `P.S.` marker may appear | At the end; `P.S` and `p.s.` accepted; may follow a sentence; `P.P.S` is not `P.S.` | Anywhere; `P.S.` with dot; any case; `P.P.S.` passes `P.S.` | Line start anywhere; exact marker; any case | 115 + 90 + 1 / 93 + 91 + 53 (position + marker + line) |
| D-letters-unit | "letters": alphabetic in any script, or a–z? | Any script | a–z | Judge | 96 / – |
| D-language-mixed | One paragraph in another language | Fails | Whole-text detection | Judge | 78 / – |
| D-constrained-extra | An option plus explanation | Fails | Passes | Fails | 75 / 0 |
| D-english | Must `english_capital`/`english_lowercase` answers be English? | Yes | Yes | No | 56 / 233 |
| D-end-case (proposal changed in v4) | `end_checker` case | Case-insensitive (93 rows pair it with a letter-case rule) | Case-insensitive | Case-sensitive | 0 / 161 |
| D-sections-case (v4), D-sections-count | `SECTION` vs `Section`; exactly N vs at least N | Any case; exactly N | Case-sensitive; at least N | Any case; exactly N | 22+24 / 1 |
| D-consecutive-order | Is `b a` "consecutive letters"? | Yes | Ascending only | (B-F3) | 48 / 41 |
| D-start-end-one-word, -leading | One-word answer; markup before the first word | Pass; allowed | Fail; not allowed | Pass; allowed | 42+2 / 13+1 |
| D-two-responses-edge, D-asterisk-run | Separator at the start or end; `*******` | Fails; not a separator | Ignored; split inside | Ignored; split inside | 30+1 / 30+1 |
| D-end-trailing-markup | `**…?**` or a closing quote after the end phrase | Fails | Quote allowed | Fails | 29 / 0 |
| D-comma-, D-dot-, D-exclamation-variants | `，` `。` `！` | Count | ASCII only | ASCII only | 27/55/9 each |
| D-brackets-one-word | `[I like cats]` | Fails | Fails | (B-F6) | 15 / 144 |
| D-capital-single-letter | Do `I`, `A` count as capital words? | Yes | Yes | No | 3 / 80 |
| D-strip, D-unique-case, D-repeat-center/-unchanged/-distinct, D-placeholder-form, D-json-scalar, D-bullet-dash/-nested, D-highlight-bold, D-title-position, D-letter-case, D-paragraph-blank-run, D-quotation-typographic, D-sections-preamble/-numbering, D-bigram-odd | See CONTRACTS.md | | | | ≤ 22 each |

The v4 change of three proposals (D-end-case, D-postscript-case, D-sections-case to
case-insensitive) rests on the data: 93, 71 and 20 rows combine those checks with
`change_case:english_lowercase` or `english_capital`, and those rows cannot reach reward 1 under a
case-sensitive reading.

## 5. Panel details

Stored records (no generation): truncated answers (`finish_reason` length) 39 OLMo, 65 Qwen2.5,
92 / 81 / 620 Qwen3-Instruct greedy / rerun / sample0, 166 Qwen3-Thinking; of the thinking run's
166, 139 never closed their reasoning and 27 closed it and were cut in the answer. 22 non-reasoning
answers contain a literal `<think>` (G2). The greedy rerun reproduced only 506 of 1,000 answers
byte for byte.

Per run (full panel; held-out part in brackets):

| Run | A passes | A false rewards | A missed rewards | B false gate passes | B false gate fails |
|---|---|---|---|---|---|
| OLMo sample0 | 763 | 195 (25.6%) | 155 | 507 | 195 |
| Qwen2.5 sample0 | 801 | 258 (32.2%) | 244 | 503 | 189 |
| Qwen3-Instruct greedy | 293 | 25 (8.5%) | 78 | 144 | 76 |
| Qwen3-Instruct greedy rerun | 295 | 27 (9.2%) | 81 | 143 | 79 |
| Qwen3-Instruct sample0 | 3,493 | 429 (12.3%) | 1,051 | 1,658 | 1,182 |
| Qwen3-Thinking sample0 | 830 | 52 (6.3%) | 205 | 104 | 185 |
| All (held-out) | 6,475 (5,868) | 986, 15.2% (919, 15.7%) | | | |

All panel numbers come from `audit/frozen/panel_verdicts.jsonl`. Regrading the panel
(`scripts/panel_grade.py`) can change grader A's verdicts on the responses to the 77 rows of G3,
because grader A draws the paragraph index at random; two gradings gave Qwen2.5 803 and 801 passes.

"False" and "missed" are by the contract's proposed readings, so decision entries are included;
the finding-only view is the "findings fixed" columns of section 1. Per-check pass rates and
disagreement classes are in `audit/work/panel_tables.md` (generated by `scripts/panel_extra.py`).

## 6. What step 6 must still provide

The recommendation is provisional: no reviewer has checked the contracts or the replacement's
verdicts. Before the replacement is used as the fixed grader, step 6 should:

- record the decision rule first, for example: the replacement (with the maintainers' readings)
  passes every fixture, its scored coverage is complete, and its error rate is lower than grader A's
  and grader B's with paired intervals that exclude zero;
- draw the final round from the held-out panel part (responses after the first 300 of each run
  file), stratified by replacement-versus-grader disagreement, sampling most of the 5,365 grader A
  and 8,106 grader B held-out disagreements' strata and about 130 agreement cases per grader for an
  upper bound below 2%;
- report the error rates of A, B and the replacement with intervals, Cohen's kappa between reviewers,
  and the cases that bear on the largest decision entries (`D-empty`, `D-hyphen-scope`,
  `D-keyword-match`, `D-lowercase-counting-scope`, `D-palindrome-length`).

## 7. Files

- `audit/ISSUE.md`: pinned inputs, contract hashes and times, step entries, held-out split.
- `audit/CONTRACTS.md` (v4) and `audit/frozen/CONTRACTS_v1.md`–`v4.md`.
- `audit/replacement/contract_grader.py`: the replacement, one switch per decision entry.
- `audit/fixtures.jsonl` (945 lines: `instruction_id`, `kwargs`, `response`, `label`, plus each
  grader's verdict and class); `audit/tests/test_fixtures.py`, `fixture_defs.py`,
  `known_failures.json`. Run: `$PY -m pytest -q -p no:cacheprovider tests` (2,209 passed, 74 skipped
  semantic, 552 xfailed when this report was written).
- `audit/scripts/`: `survey_data.py`, `graders.py` (both pipelines), `fixture_lib.py`,
  `build_fixtures.py`, `step4_properties.py`, `step4_fuzz.py`, `filter_fuzz.py`,
  `step4_content_free.py`, `panel_grade.py`, `panel_analyze.py`, `panel_extra.py`,
  `panel_inspect.py`, `repro.py`, `report_cases.py`, `check_commands.py`,
  `check_report_appendix.py`, `run_all.sh`.
- `audit/frozen/panel_verdicts.jsonl` (sha256 `4f864eeb…`), `audit/work/*`: intermediate outputs.

## Appendix: every counterexample command

Run from `audit/` after the three setup lines of section 3. Each line: finding id, then the command.

```bash
# G1
$PY scripts/repro.py check punctuation:no_comma null 'Okay the user wants a short answer so I will think about it' --reasoning
# G2
$PY scripts/repro.py check keywords:existence '{"keywords": ["tag"]}' 'Write the <think> tag before your notes.'
# G3
$PY scripts/repro.py check length_constraints:nth_paragraph_first_word '{"num_paragraphs": 2, "nth_paragraph": 3, "first_word": "history"}' $'History is long.\n\nHistory is fun.' --runs 30
# G4
$PY scripts/repro.py check last_word:last_word_answer '{"last_word": "hello"}' ' '
# D-empty
$PY scripts/repro.py row eb817d5f-9f71-4bac-9f5e-9863c5e3957a ''
# A-F1
$PY scripts/repro.py check keywords:word_once '{"keyword": "fix"}' 'Fix it now and fix it well.'
# A-F1
$PY scripts/repro.py check keywords:word_once '{"keyword": "fix"}' 'Let me fix the prefix.'
# A-F2
$PY scripts/repro.py check keywords:word_count_different_numbers '{"keyword": "box", "frequency": 2, "relation": "less than"}' 'A box and another box.'
# A-F2
$PY scripts/repro.py check keywords:word_count_different_numbers '{"keyword": "box", "frequency": 2, "relation": "less than"}' 'No crates here.'
# A-F3
$PY scripts/repro.py check first_word:first_word_answer '{"first_word": "development"}' 'Development, as a concept, matters.'
# A-F3
$PY scripts/repro.py check length_constraints:nth_paragraph_first_word '{"num_paragraphs": 2, "nth_paragraph": 2, "first_word": "if"}' $'Cats are nice.\n\nIf: you like dogs, fine.'
# A-F4
$PY scripts/repro.py check keywords:keyword_specific_position '{"keyword": "shot", "n": 2, "m": 3}' 'I went out. Then, the shot came.'
# A-F4
$PY scripts/repro.py check keywords:keyword_specific_position '{"keyword": "repeat", "n": 1, "m": 1}' 'Repeat after me. Good.'
# A-F5
$PY scripts/repro.py check count:count_unique null 'Apples, pears, plums.'
# A-F6
$PY scripts/repro.py check count:counting_composition '{"n_sent": 3, "n_words": 2}' $'Birds sing. Cats sleep. Dogs run.\n* * *\nRain falls. Wind blows. Trees sway.\n* * *\nKids play. Parents watch. Time flies.'
# A-F7
$PY scripts/repro.py check detectable_format:bigram_wrapping null '<<I am>> home'
# A-F7
$PY scripts/repro.py check detectable_format:bigram_wrapping null Hello
# A-F8
$PY scripts/repro.py check detectable_format:constrained_response null 'My answer is yes. My answer is no.'
# A-F9
$PY scripts/repro.py check detectable_format:multiple_sections '{"num_sections": 2, "section_spliter": "SECTION"}' $'SECTION 1\nCats are great; see SECTION 2 for dogs.'
# A-F10
$PY scripts/repro.py check detectable_format:number_bullet_lists '{"num_bullets": 2}' $'* Apples.\n* Bananas.\n\n---\n\nThat is all.'
# A-F10
$PY scripts/repro.py check detectable_format:number_bullet_lists '{"num_bullets": 2}' $'*Note* the list:\n* Apples.\n* Bananas.'
# A-F11
$PY scripts/repro.py check detectable_format:square_brackets null '[I] [like] [cats].'
# A-F12
$PY scripts/repro.py check keywords:no_adjacent_consecutive null '(apple) banana split.'
# A-F12
$PY scripts/repro.py check keywords:no_adjacent_consecutive null 'Pick 1, 2 or 9'
# A-F13
$PY scripts/repro.py check keywords:palindrome null 'Cats run - dogs walk.'
# A-F14
$PY scripts/repro.py check detectable_content:postscript '{"postscript_marker": "P.S."}' 'Ship the parcel with U.P.S. today.'
# A-F15
$PY scripts/repro.py check language:response_language '{"language": "fr"}' '12345 67890'
# A-F16
$PY scripts/repro.py check length_constraints:number_paragraphs '{"num_paragraphs": 2}' '***Cats*** are nice and dogs are loyal.'
# A-F17
$PY scripts/repro.py check first_word:first_word_sent '{"first_word": "peace"}' '1. Peace is good. Peace is calm.'
# A-F18
$PY scripts/repro.py check copy:repeat_phrase '{"phrase": "Laughter is the best medicine", "small_n": 2}' 'Laughter is the best medicine. Laughter is our best medicine.'
# A-F19
$PY scripts/repro.py check change_case:english_capital null 'I LIKE CATS AND DOGS VERY MUCH.'
# A-F20
$PY scripts/repro.py check length_constraints:number_sentences '{"num_sentences": 3, "relation": "at least"}' '我很好。你呢？他也很好。'
# A-F21
$PY scripts/repro.py check count:lowercase_counting '{"N": 2}' '<b>I</b> like it'
# A-F22
$PY scripts/repro.py check count:count_unique null '**Every** word here appears once.'
# B-F1
$PY scripts/repro.py check copy:repeat_phrase '{"phrase": "Laughter is the best medicine", "small_n": 2}' 'Laughter is a best medicine. Laughter is our best medicine.'
# B-F1
$PY scripts/repro.py check copy:repeat_phrase '{"phrase": "Laughter is the best medicine", "small_n": 2}' 'Laughter is the best medicine. Laughter is the best medicine.'
# B-F2
$PY scripts/repro.py check count:lowercase_counting '{"N": 2}' 'the the the end'
# B-F2
$PY scripts/repro.py check count:lowercase_counting '{"N": 2}' 'Hello World'
# B-F3
$PY scripts/repro.py check keywords:no_adjacent_consecutive null 'A big dog.'
# B-F3
$PY scripts/repro.py check keywords:no_adjacent_consecutive null 'Tom ate ate cake.'
# B-F4
$PY scripts/repro.py check length_constraints:number_paragraphs '{"num_paragraphs": 2}' $'Cats are nice.\n***\nDogs are loyal.'
# B-F4
$PY scripts/repro.py check length_constraints:number_paragraphs '{"num_paragraphs": 2}' $'Cats are nice.\n\nDogs are loyal.'
# B-F5
$PY scripts/repro.py check paragraphs:paragraphs '{}' $'Cats.\n***\nDogs.\n***\nBirds.'
# B-F5
$PY scripts/repro.py check paragraphs:paragraphs2 '{}' $'Cats.\n\nDogs.\n\nBirds.'
# B-F6
$PY scripts/repro.py check detectable_format:square_brackets null '[I] like cats.'
# B-F7
$PY scripts/repro.py check count:counting_composition '{"n_sent": 3, "n_words": 2}' 'Birds sing. Cats sleep. Dogs run.'
# B-F8
$PY scripts/repro.py check keywords:start_end null 'Hello world and hello.'
# B-F9
$PY scripts/repro.py check startend:quotation null $'\'Hello there.\''
# B-F10
$PY scripts/repro.py check length_constraints:number_words '{"num_words": 5, "relation": "at least"}' 'Привет как дела у тебя'
# B-F10
$PY scripts/repro.py check first_word:first_word_answer '{"first_word": "development"}' 'Привет development'
# B-F11
$PY scripts/repro.py check length_constraints:number_sentences '{"num_sentences": 3, "relation": "at least"}' 'Dr. Smith runs. You walk.'
# B-F12
$PY scripts/repro.py check keywords:palindrome null 'A man, a plan, a canal: Panama!'
# B-F12
$PY scripts/repro.py check keywords:palindrome null $'Cats run.\n\n---\n\nDogs walk.'
# B-F13
$PY scripts/repro.py check detectable_format:number_highlighted_sections '{"num_highlights": 1}' $'Intro.\n\n* * *\n\nEnd.'
# B-F14
$PY scripts/repro.py check detectable_format:title null $'<< >>\nIt was fine.'
# B-F15
$PY scripts/repro.py check detectable_format:json_format null '```json {"answer": "Paris"} ```'
```
