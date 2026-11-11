# Audit of the RLVR1 instruction-following graders

Report of step 7, written 2026-11-11 12:00Z. The record (pinned inputs, contract hashes and times, contract
changes, held-out split, file hashes) is in `audit/ISSUE.md`; the contracts and decision entries are in
`audit/CONTRACTS.md`.

Graders under audit, on the 11,817 rows (28,219 constraints, 47 instruction ids):

- **SkyRL reward**: `final_answer_text` then `grade_instruction_following`, which runs NVIDIA's
  verifiable-instructions checkers (also the reference implementation). Binary row reward.
- **Curation gate**: the deterministic gate of `convert_instruction_following` / `grade_judge_candidate`, which
  runs verifyit's `ifeval` checks on 43 of the 47 ids (the four semantic ids go to an LLM judge that is not part
  of this case). A failed check sets the reward to 0.

## 1. Headline

No error rate is reported: step 6 (blinded review) was not run, because this exercise has no reviewers. What
the audit measured is how often each grader contradicts the contracts, using a replacement grader written from
the contracts (`audit/replacement.py`, passes all 203 fixtures), on 23,315 stored panel responses (55,783
constraint verdicts). A disagreement is split into a **contract contradiction** (no single decision reading
gives the grader's verdict) and a **decision-dependent** disagreement (the non-proposed reading of one decision
entry gives it). These rates are not error rates: the replacement can be wrong too (its language checks are
approximations, section 4), and only the blinded review of step 6 can say which side is right.

| Constraint verdicts | Contract contradictions | Decision-dependent |
|---|---|---|
| SkyRL / NVIDIA, held-out runs (19,142 verdicts) | 816 (4.3%) | 1,101 (5.8%) |
| SkyRL / NVIDIA, development runs (36,641) | 1,889 (5.2%) | 1,385 (3.8%) |
| Curation gate / verifyit, held-out (17,386) | 2,166 (12.5%) | 724 (4.2%) |
| Curation gate / verifyit, development (33,338) | 4,302 (12.9%) | 1,195 (3.6%) |

As an RL reward (held-out runs, Qwen2.5-7B-Instruct and OLMo-2-1124-7B-Instruct): of the 1,564 rows that
SkyRL rewards 1.0, **361 (23.1%) are false rewards** under the proposed readings, and **164 (10.5%)** are false
under every single-decision reading. The curation gate lets through 2,599 held-out rows, of which **978 (37.6%)**
fail the contract and **819 (31.5%)** fail it under every single-decision reading.

Effect on scores (row-level score, in points; 95% bootstrap interval of the paired difference):

| Run | Rows | SkyRL reward | Replacement, all constraints | Change | Gate pass | Replacement, gate constraints | Change |
|---|---|---|---|---|---|---|---|
| Qwen3-4B-Instruct-2507 sample0 | 11,817 | 29.5 | 33.4 | +3.9 [+3.3, +4.5] | 47.8 | 42.2 | -5.6 [-6.5, -4.7] |
| Qwen3-4B-Instruct-2507 greedy | 1,000 | 29.3 | 33.1 | +3.8 [+2.1, +5.7] | 49.9 | 41.6 | -8.3 [-11.1, -5.6] |
| Qwen3-4B-Instruct-2507 greedy_repeat | 1,000 | 29.5 | 33.4 | +3.9 [+2.1, +5.7] | 50.0 | 42.1 | -7.9 [-10.8, -5.1] |
| Qwen3-4B-Thinking-2507 sample0 | 1,500 | 55.3 | 65.3 | +10.1 [+7.9, +12.1] | 63.4 | 68.6 | +5.2 [+3.1, +7.4] |
| Qwen2.5-7B-Instruct sample0 (held out) | 4,000 | 20.0 | 20.6 | +0.6 [-0.4, +1.7] | 33.0 | 26.0 | -7.0 [-8.2, -5.8] |
| OLMo-2-1124-7B-Instruct sample0 (held out) | 3,998 | 19.1 | 18.9 | -0.2 [-1.0, +0.6] | 32.0 | 24.8 | -7.2 [-8.5, -5.9] |

The rerun of the greedy configuration (same settings) produced identical text for only 506 of 1,000 rows; it
changed 16 SkyRL row verdicts (+0.2 points), 27 gate verdicts (+0.1) and 19 replacement verdicts (+0.3). Every
score change above except the two held-out SkyRL ones is at least ten times the rerun difference. The small
net SkyRL changes on the held-out models hide large gross movement: on Qwen2.5-7B the replacement gains 237
rows and loses 212.

The largest single causes, by panel verdicts moved:

- `keywords:word_once` (B1): both graders require exactly one occurrence; the text says "Include keyword X".
  906 of 1,808 NVIDIA verdicts (50%) are false fails.
- `count:lowercase_counting` (V4): verifyit inverts the relation (requires at least N lowercase words); 1,273 of
  1,712 verdicts (74%) wrong. `keywords:no_adjacent_consecutive` (V11): verifyit checks repeated adjacent words
  instead of consecutive initial letters; 905 of 1,499 (60%). `detectable_format:square_brackets` (V10): any one
  bracketed span passes; 665 of 1,079 (62%) false passes. `length_constraints:number_paragraphs` (V13) and
  `paragraphs:*` (V14): 1,011 wrong verdicts.
- `keywords:word_count_different_numbers` (B2, P5): the text says "should appear N times" but the hidden kwarg
  `relation` is "less than" for 206 of 526 constraints; on those, N occurrences fail and 0 pass. 302 of 393
  NVIDIA verdicts and 328 of 393 verifyit verdicts with that relation contradict the text.
- Content-free answers (step 4): an **empty answer earns SkyRL reward 1.0 on 1,702 of 11,817 rows (14.4%)**
  and passes the curation gate on 810 rows (6.9%); 625 more rows raise an exception (N16). This rests on
  decision D-empty (a prohibition such as "no commas" holds vacuously for an empty answer), so it is a decision
  and not a defect, but it is the reward-hacking exposure with the largest reach.

**Recommendation: fix the graders.** Do not admit either grader as is. For the SkyRL reward, fix the extraction
(P1, P2), the exception policy (N16, P3), the random re-draw (N17) and the contract contradictions N1-N18, B1-B7;
for the curation gate, the verifyit checks contradict the contract on 12.5% of held-out verdicts, and findings
V1-V18 and B1-B7 touch at least 26 of the 43 gated ids, so rewrite those checks from the contracts (for most of
them, NVIDIA's behavior plus the N and B fixes). Send the D-entries to the maintainers; the largest are D-empty, D-hyphens-single, D-first-last-case and
D-divider. This recommendation is provisional until step 6 runs (section 9).

## 2. Scope, skipped steps and substitutions

- No issue tracker: the record is `audit/ISSUE.md`. No repository, research branch, Hugging Face dataset or job
  launcher: fixtures are pytest files under `audit/tests/`, frozen files under `audit/frozen/` with their sha256
  in ISSUE.md, scripts under `audit/scripts/`. No PRs (manage-pr) and no pinned dataset revision of the samples.
- Step 5: no generation; the stored responses in `case/panel/` are the panel. The greedy pair is the rerun.
- Step 6: not run (no reviewers). No review sample was drawn, frozen or rendered.
- Not audited: the LLM judge (not in the case), `grade_nemotron_instructions` (the SkyRL path when the session
  config sets `verifyit_enabled`; read but not run, because it needs a worker subprocess); `instruction_references.py`.
- The four semantic ids get no gate verdict; their 5,059 panel verdicts are graded only by SkyRL and the replacement.
- Step 4 asks to run the reference's unit tests against the replacement: NVIDIA's repository has no tests, and
  `grader/verifyit` ships none for these checks, so there were none to run. Instead, the verifyit docstrings that
  state a reading: `sentence_hyphens` ("join its words with hyphens", V9), `no_adjacent_consecutive` ("No two
  adjacent words may be identical", V11), and the self-described approximations `count_unique`,
  `bigram_wrapping`, `response_language` and `letter_counting` (the four semantic ids, not gated).

## 3. Inputs (step 1)

Pinned in ISSUE.md with hashes: Marin `af9c678` (SkyRL files, verifyit, graders.py; installed copies byte-identical,
manifest OK), NVIDIA `f46a5ac`, the data revision `600262dd` with one hash per row (`audit/frozen/row_hashes.tsv`),
nltk 3.10.3, langdetect 1.0.9, punkt_tab by zip hash, the panel's vLLM 0.11.0 settings. Unverified: which reward
the RL run used (`verifyit_enabled`, U1) and the RL rollout settings (U2). The extraction rules and the exception
policy were pinned after the contract hash, from the code (ISSUE.md, "Step 1 addendum").

## 4. Method

- Contracts (step 2): written from the 47 instruction texts in the prompts before any grader code was read;
  hash `c76b255f...` at 11:28:31Z. Twelve later changes are listed with reasons at the end of CONTRACTS.md: six
  after reading the code (two new decision entries, entries split or extended), and six prompted by
  development-set panel disagreements (CJK sentence ends, spaced hyphens, phrase palindromes, dotted words,
  D-alphabet, D-postscript-line). The held-out split was recorded before any panel verdict was inspected.
- Fixtures (step 3): 203 labeled responses, each run on the three graders; 484 tests pass and 121 are strict
  xfails, each mapped to a finding or a decision in `audit/tests/known_wrong.py`.
- Replacement (`audit/replacement.py`): one switch per decision entry (42 switches; D-english, D-language-mixed
  and D-two-responses' "substantive" reading are not modeled). It uses langdetect (seeded) for "in English" and
  for `language:response_language`, on lowercased text for the all-capital check; these are approximations.
- Classification: a grader/replacement disagreement is decision-dependent when flipping one decision to its
  other reading gives the grader's verdict (`repl_flips` in the verdict files); combinations of two decisions
  are not tried, so a few contradictions may be decision-dependent under two readings at once.

## 5. Findings

Reproduce any finding from the case folder:

```bash
cd <W>/case
export NLTK_DATA=<W>/case/deps/nltk_data
export PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8
../.venv/Scripts/python.exe ../audit/scripts/repro.py N1      # or any id below; "all" runs every one
```

`repro.py` prints each counterexample's check, kwargs and exact response, the contract label, and the verdicts
of SkyRL (final_answer_text + NVIDIA check), the curation gate (verifyit check) and the replacement. The full
output of `repro.py all` is in `audit/out/repro_all.txt`. "Panel share" is the share of that check's panel
verdicts (all six runs) that the grader gets wrong under every single-decision reading (from
`audit/out/panel_table.txt`); a check with several findings reports one joint share.

### SkyRL reward / NVIDIA checkers (N). NVIDIA is the reference, so each is also present in the reference.

| Id | Check | Counterexample (kwargs; exact response) | Grader verdict | Contract broken | Panel share |
|---|---|---|---|---|---|
| N1 | copy:repeat_phrase | phrase "Live each day to the fullest", small_n 3; `Live each day to the fullest. Live each day to the fullest. Live each hour to the fullest.` | pass | each repetition replaces one word; only the last match's difference is checked, so unchanged copies count. Markup on a phrase word also hides a match (`**Live** each moment ...` fails) | 58 / 1,059 (5.5%) |
| N2 | count:count_unique | `Hello, world, friend.` | fail | punctuation is not a word; `word_tokenize` makes the two commas a repeated word | 101 / 1,341 (7.5%) |
| N3 | count:counting_composition | n_sent 3, n_words 2; three paragraphs of `Dogs bark. Cats purr. Birds sing.` joined by `* * *` lines | fail | the text names the divider `* * *`, the checker splits at `***` and counts the period as a word: an exact answer fails | 1 constraint in the data |
| N4 | detectable_content:postscript | P.S.; `Thanks, as the P.S. says, for reading.` and `Thanks.\n\nP.P.S. See you soon.` | pass, pass | the postscript must start with the marker; matched anywhere, and `P.P.S.` contains `p.s.` | 113 / 1,277 (8.8%) with B7 |
| N5 | detectable_format:constrained_response | `My answer is yes. My answer is no.` | pass | answer with one option; two different options pass | 3 / 243 |
| N6 | detectable_format:multiple_sections | 2, SECTION; `SECTION 1\nA text.\nSECTION 2\nB text.\nSECTION 3\nC text.` | pass | "must have 2 sections"; the checker tests >= | 74 / 917 (8.1%) |
| N7 | detectable_format:number_bullet_lists | 3; `* one\n* two\n* three\n\n---\n\nDone.` and `*Note*: intro\n* one\n* two\n* three` | fail, fail | a `---` rule and an italic line start are not bullets | 20 / 1,019 (2.0%) with B6 |
| N8 | detectable_format:number_highlighted_sections | 3; `* **Alpha**: one\n* **Beta**: two` | pass | two highlights; a bold span after a `* ` bullet counts twice | 14 / 1,070 (1.3%) |
| N9 | detectable_format:sentence_hyphens | `Tea is well-known.-Coffee is too.` | fail | a hyphenated word inside a sentence is allowed | 16 / 1,300 (1.2%) |
| N10 | detectable_format:square_brackets | `[I], [like] [tea].` | fail | punctuation outside the brackets is not a word | 67 / 1,079 (6.2%) |
| N11 | first-word and last-word checks | `**Development** matters.`; `Development, as a field, matters.` (first_word_answer); `Tea, I think, is warm. Tea is calm.` (first_word_sent); `Fuel: costly.\n\nPrices rise.` (nth_paragraph_first_word); `It remains a mystery in modern history—expression.` (last_word_answer "expression") | fail (all) | the first or last word ignores attached punctuation and markup; NVIDIA compares the whitespace token | first_word_answer 74 / 1,089 (6.8%), first_word_sent 66 / 1,024 (6.4%), last_word_answer 61 / 1,285 (4.7%), last_word_sent 46 / 1,203 (3.8%), nth_paragraph 13 / 1,048 (1.2%) |
| N12 | keywords:keyword_specific_position | tea, n 2, m 3; `I like coffee. Yes, drink tea daily.` | fail | the comma is not a word; tea is the 3rd word | 14 / 1,341 (1.0%) |
| N13 | keywords:no_adjacent_consecutive | `Step 1 2 done.`; `"A" big dog.` | fail; pass | digits are not letters; a quote mark does not hide the letter a | 66 / 1,499 (4.4%) |
| N14 | keywords:palindrome | `This - that.`; `Level up now.` | pass; fail | `-` is not a word; `Level` is a palindrome ignoring case | 57 / 1,165 (4.9%) |
| N15 | change_case:english_capital, language:response_language | `HELLO WORLD`; `PROFESIÓN DEL SUSTENTADOR PRINCIPAL DE LA FAMILIA; TRABAJA COMO CUIDADORA DE MAYORES A DOMICILIO.`; ta, `12345` | fail; pass; pass | langdetect misreads all-capital text both ways, and a langdetect exception counts as a pass (empty or digit-only answers pass the language check; 208 of 1,000 fuzz inputs) | english_capital 104 / 1,534 (6.8%); language 4 / 1,600 |
| N16 | last_word:last_word_answer | `last_word` end; empty answer `` | IndexError | an exception makes `NemotronTaskSession` return `INFRA_ERROR` (reward 0, ungraded) for the whole row | 1 panel row; 625 of 11,817 rows on an empty answer; 134 of 1,000 fuzz inputs |
| N17 | length_constraints:nth_paragraph_first_word | num_paragraphs 2, nth_paragraph 3, fuel; `Fuel is costly.\n\nFuel prices rise.` | reward 1.0 for 15 of 20 seeds | the instruction cannot be met (77 of 515 constraints have nth > num); `build_description` re-draws nth from the global `random` on every call | 9 of 161 panel verdicts pass; the reward is nondeterministic |
| N18 | sentence-based checks | at least 3; `我喜欢茶。你喜欢咖啡。他喜欢水。` | fail | `。！？` end sentences; Punkt (English) does not split them | within number_sentences 77 / 1,131 (6.8%) |

### Both graders (B)

| Id | Check | Counterexample | NVIDIA / verifyit | Contract broken | Panel share NVIDIA / verifyit |
|---|---|---|---|---|---|
| B1 | keywords:word_once | beer; `Beer is good and beer is cold.` | fail / fail | "Include keyword beer": two occurrences include it; both require exactly one | 906 / 863 of 1,808 (50% / 48%) |
| B2 | keywords:word_count_different_numbers | box, 2, less than; `A box and a box.` and `No containers here.` | fail, pass / fail, pass | "should appear 2 times": no reading means fewer than 2 | relation "less than": 302 / 328 of 393; all relations 305 / 302 of 1,015 |
| B3 | combination:two_responses | `Tea is warm.\n*******\nCoffee is strong.` | pass / pass | separated by 6 asterisks; 7 are accepted | 31 / 31 of 557 (5.6%) |
| B4 | detectable_content:number_placeholders | 2; `Dear [name], see [] and [ ].` | pass / pass | an empty bracket pair is not a placeholder | 9 / 8 of 1,201 |
| B5 | detectable_format:json_format | `{"a": NaN}` | pass / pass | NaN is not JSON (`json.loads` accepts it) | 0 on the panel |
| B6 | detectable_format:number_bullet_lists | 3; `* one\n* two\n* three\n\n* * *\n\nEnd.` | fail / fail | a `* * *` divider is not a bullet | within N7; verifyit 0 |
| B7 | detectable_content:postscript | P.P.S; `The two limits are equal.\n\nP.P.S.` | pass / pass | "add a postscript": a bare marker has no postscript | within N4 / V5 |

### Curation gate / verifyit (V). Status in the reference: NVIDIA gets the fixture right unless noted.

| Id | Check | Counterexample | verifyit | Contract broken | Panel share |
|---|---|---|---|---|---|
| V1 | change_case:english_capital, english_lowercase | `ПРИВЕТ МИР, КАК ТВОИ ДЕЛА СЕГОДНЯ?`; `bonjour je suis très content de vous voir aujourd'hui mon ami` | pass, pass | "in English" is not checked | 110 / 1,534 and 140 / 1,208 |
| V2 | copy:repeat_phrase | `Live each moment to the fullest. Live each hour to the fullest.` (n 2); `Live each day to the fullest. Live each day to the fullest.` | fail; pass | counts unchanged copies, >= n; the text asks for transformed copies | 493 / 1,059 (46.6%) |
| V3 | count:counting_composition | n_sent 3, n_words 2; `Dogs bark loudly. Cats purr softly. Birds sing sweetly.` | pass | first n_sent sentences with >= n_words words; ignores paragraphs and "exactly" (NVIDIA also wrong, N3) | 1 constraint |
| V4 | count:lowercase_counting | 2; `the cat and the dog and the bird`; `Hello World` | pass; fail | "at most 2 times" checked as at least 2 lowercase words | 1,273 / 1,712 (74.4%) |
| V5 | detectable_content:postscript | `Thanks.\n\n**P.S.** See you soon.` | fail | markup before the marker | 43 / 1,277 with B7 |
| V6 | detectable_format:json_format | `` ```JSON\n{"a": 1}\n``` `` | fail | an upper-case fence tag is a fence | 0 on the panel |
| V7 | detectable_format:multiple_sections | 2, SECTION; `SECTION 1\nAs SECTION 2 below shows, tea.\nSECTION 2\nB text.` | fail | a mention inside a line is not a section marker (also case-insensitive: D-sections-case) | 39 / 917 (4.3%) |
| V8 | detectable_format:number_highlighted_sections | 1; `Text.\n\n* * *\n\nMore.` | pass | a divider is not a highlight | 12 / 1,070 |
| V9 | detectable_format:sentence_hyphens | `I like tea.-You like coffee.-We both like water.` | fail | sentences are joined by hyphens; the docstring reads it as "join its words with hyphens" (NVIDIA also wrong on hyphenated words, N9) | 5 / 1,300 contradictions; 551 decision-dependent |
| V10 | detectable_format:square_brackets | `[I] like tea` | pass | every word in brackets; one bracketed span passes | 665 / 1,079 (61.6%) |
| V11 | keywords:no_adjacent_consecutive | `A big dog.`; `The the cat.`; `вот где дом` | pass; fail; pass | consecutive initial letters; the check (and its docstring) tests repeated adjacent words | 905 / 1,499 (60.4%) |
| V12 | keywords:start_end | `Hello there my friend hello.` | pass | "not even punctuation" after the last word | 79 / 989 (8.0%) |
| V13 | length_constraints:number_paragraphs | 3; `One.\n***\nTwo.\n***\nThree.`; `One.\n\nTwo.\n\nThree.` | fail; pass | paragraphs are separated by `***`; the check splits at blank lines | 437 / 1,345 (32.5%) |
| V14 | paragraphs:paragraphs, paragraphs:paragraphs2 | `One.\n***\nTwo.\n***\nThree.` (paragraphs); `One.\n***\nTwo.` (paragraphs2) | pass; pass | exactly 2 paragraphs with the named separator; >= 2 with either separator passes | 134 / 1,150 and 440 / 1,391 |
| V15 | startend:quotation | `'Hello there.'` | pass | double quotation marks; single quotes accepted | 1 / 810 |
| V16 | word extraction (all word-based checks) | at least 5; `Это очень хороший ответ сегодня.`; `- Development matters.` | fail; fail | words in other scripts are words, and a lone `-` (or an HTML tag name such as `b`) is not: the regex is ASCII-only and includes `-` (NVIDIA also fails the second, N11) | number_words 90 / 1,443 (6.2%), start_end and palindrome shares include it |
| V17 | keywords:palindrome | `A man, a plan, a canal: Panama.` | fail | a phrase palindrome is a palindrome | within 139 / 1,165 (11.9%) with V16 |
| V18 | sentence-based checks | at least 3; `我喜欢茶。你喜欢咖啡。他喜欢水。` | fail | as N18 | within number_sentences 91 / 1,131 (8.0%) |

### Pipeline, data and dependencies (P)

| Id | Stage | Counterexample / evidence | Verdict | Contract broken | Share |
|---|---|---|---|---|---|
| P1 | extraction (both) | Qwen3 thinking response cut inside its reasoning; the chat template opened `<think>`, so the text has no marker: `Okay the user wants an answer without any commas so I should plan the reply first and then` with `punctuation:no_comma` (`repro.py P1`) | SkyRL reward 1.0; gate pass | a response whose reasoning never closes is an extraction failure and fails every check; both extractors grade the reasoning text as the answer | 139 of 1,500 thinking responses (9.3%); 84 of their 350 constraint verdicts pass NVIDIA; 1 row rewarded; 18 pass the gate |
| P2 | extraction (both) | `<think>I will avoid commas and` with `punctuation:no_comma` (`repro.py P2`) | graded as `""`; reward 1.0; gate pass | same rule: an unclosed reasoning block is a failure, not an empty answer that prohibitions accept | 14 non-reasoning panel rows with a literal `<think>`; 7 rewarded 1.0 |
| P3 | SkyRL error policy | any checker exception (N16) | row `INFRA_ERROR`, reward 0 | scored coverage: the row gets no verdict | 1 of 23,315 panel rows; 625 of 11,817 rows on an empty answer |
| P4 | dependencies | `_ensure_nltk_data` downloads `punkt_tab` at grading time when missing, with no hash; NVIDIA's `requirements.txt` gives lower bounds only (`nltk>=3.8`), and nltk < 3.8.2 needs the `punkt` pickle, which nothing installs | - | grader data and versions must be pinned | all sentence and word-tokenizer checks |
| P5 | data | `keywords:word_count_different_numbers` text omits the `relation` kwarg (526 constraints, 206 "less than"); 77 `nth_paragraph_first_word` constraints ask for a paragraph after the last one | - | the model cannot see the condition it is graded on, or cannot meet it | B2, N17 |

## 6. Decision entries (for the maintainers)

Proposed reading is A for every entry; the full readings and examples are in CONTRACTS.md. "Moves" counts the
panel constraint verdicts whose replacement verdict changes when that one entry takes reading B; the last
column gives the reading each grader follows where the fixtures show it.

| Entry | Question | Moves | NVIDIA / verifyit follow |
|---|---|---|---|
| D-empty | does an empty answer satisfy prohibitions vacuously? | 18 panel; 1,702 rows rewarded on an empty answer (step 4) | B / B |
| D-hyphens-single | does a one-sentence answer satisfy sentence_hyphens? | 791 | A / B |
| D-first-last-case | must a required word match case? | 730 | A for first/last word, B for keyword_specific_position / A |
| D-divider | is `***` inside a line a divider; do empty edge parts count? | 383 | B / - (V13) |
| D-lowercase-total | lowercase words at most N each, or in total? | 312 | B / - (V4) |
| D-keyword-match | whole word, or substring (`foods` for food)? | 296 | B for existence/frequency/word_once, A for forbidden / A |
| D-palindrome-length | do one- and two-letter words count? | 238 | B / A |
| D-word-count-exact | "should appear N times": exactly, or at least? | 222 | B for "at least" kwargs / B |
| D-sentence | does a line end a sentence? | 184 | B / B |
| D-end-phrase-case | must the end phrase match case? | 162 | B / A |
| D-square-brackets | each word in its own brackets? | 157 | A / B |
| D-letter-case | do upper-case letters count for the letter? | 119 | A / A |
| D-lowercase-counting | do capitalized occurrences count? | 97 | A / - |
| D-letters-count | letters of any script, or a-z? | 96 | B / - |
| D-word | hyphenated and apostrophe words one word? | 94 | B (`\w+`) / A |
| D-punct-variants | do `，` `…` `！` count? | 90 | B / B |
| D-capital-word | do `I` and `A` count as capital words? | 84 | A / B |
| D-constrained-exact | may other text surround the option? | 75 | A / B |
| D-postscript, D-postscript-case, D-postscript-line | postscript last? case? marker mid-line after a sentence? | 69, 56, 55 | B, B, B / B, B, A |
| D-palindrome-phrase | do accidental cross-word palindromes (`as a`) count? | 61 | - / - (neither counts phrases) |
| D-highlight | does `**bold**` count as a highlight? | 55 | A / A |
| D-consecutive-order | does `big apple` (b then a) violate? | 55 | B / - (V11) |
| D-sections-preamble, -case, -numbering | preamble allowed? `Section` for `SECTION`? numbers 1..N? | 52, 22, 1 | A, A, B / A, B, B |
| D-alphabet | Latin/Cyrillic/Greek alphabet order, or Unicode code points? | 38 | B / - |
| D-repeat-original, D-repeat-center | unchanged copy allowed? which words are "the center"? | 30, 15 | - |
| D-end-phrase-markup | closing markup after the end phrase allowed? | 30 | B / B |
| D-title | title anywhere or at the start? | 17 | A / A |
| D-literal-think | is a literal `<think>` in a non-reasoning answer text or a reasoning block? | 13 | B / B (and then graded as empty: P2) |
| D-bullets, D-count-unique-case, D-paragraph-separator, D-placeholder, D-quotation-typographic, D-start-end-lead, D-bigram-odd | see CONTRACTS.md | 10, 8, 7, 4, 4, 2, 1 | mixed |
| D-english, D-language-mixed, D-two-responses | not modeled by a switch | - | - |

## 7. Reference comparison and stress tests (step 4)

- NVIDIA and verifyit disagree on 7,819 of 50,724 gated constraint verdicts (15.4%). Classified against the
  replacement: verifyit is the one contradicting the contract in 6,468 verdicts, NVIDIA in 2,705 (both counts
  over all six runs), and many disagreements are decision-dependent (section 6).
- Metamorphic edits (`audit/scripts/step4.py`, edits the contract ignores, applied to every passing fixture of
  every check whose contract ignores them): NVIDIA flips pass to fail under bold, italics, an HTML tag,
  typographic quotes or a semicolon on the first word for first_word_answer, first_word_sent,
  nth_paragraph_first_word and copy:repeat_phrase (N1, N11), and under `**SECTION** 1` for multiple_sections;
  verifyit flips under a `- ` bullet or an HTML tag on the first word (V16) and under `**SECTION** 1`. Typographic
  apostrophes, blank lines and a trailing newline changed no verdict where the contract ignores them.
- Fuzz (1,000 random texts per check, kwargs from the data): NVIDIA raised on 134 `last_word_answer` inputs
  (N16) and counted 208 langdetect exceptions in `response_language` as passes (N15); verifyit and the
  replacement raised nothing. One exception does not stop a run, but in SkyRL it voids the whole row (P3).
- Content-free answers on all 11,817 rows (SkyRL reward 1.0 / gate pass / replacement pass): empty
  1,702 / 810 / 0 (plus 625 SkyRL infrastructure errors); a sentence repeated 30 times 265 / 821 / 232; the
  prompt restated verbatim 746 / 1,365 / 453. Restating the prompt passes `keywords:existence`, `title` and
  `constrained_response` on every row and `word_once` on 907 of 917 under NVIDIA (verifyit: `existence` and
  `title` on every row, `word_once` on 913 of 917), because the instruction text
  itself contains the keywords, the `<<poem of joy>>` example and the options: the checks cannot tell an answer
  from an echo of the instruction. Empty text passes 13 ids under NVIDIA on every row: the prohibitions, the
  "every word" and "each sentence" checks, and the language check (through N15).
- Score-level transforms: none; both graders aggregate as all-pass.

## 8. Scored coverage and extraction counts (step 5)

- SkyRL: 23,314 of 23,315 panel rows graded (one `INFRA_ERROR`, N16). Curation gate: 50,724 of 50,724 gated
  verdicts; the 5,059 semantic verdicts go to the judge and are outside this audit.
- Stored records: 1,063 of 23,315 responses stopped at the token limit; 139 of the 1,500 thinking responses
  never close their reasoning (P1); 14 non-reasoning responses contain a literal `<think>` (P2); one OLMo
  response is empty.

## 9. What the recommendation still needs from step 6

Before step 6, record in ISSUE.md the result that would change the recommendation. Proposed: the replacement
passes every fixture (it does), its scored coverage is complete (it is), and its error rate is lower than each
grader's with a paired 95% interval that excludes zero. Then:

1. Draw the review sample with a recorded seed from the held-out runs (Qwen2.5-7B-Instruct and OLMo sample0,
   19,142 constraint verdicts), stratified by whether the replacement and each grader disagree: all or most of
   the 816 NVIDIA and 2,166 verifyit contradictions, the 1,101 / 724 decision-dependent disagreements, and about
   130 agreements per grader (the agreement stratum holds about 90% of verdicts).
2. Freeze it (sha256 of the case list in ISSUE.md), render blinded batches with `references/reviewer-prompt.md`,
   two reviewers per case in different orders, and estimate each grader's error rate per stratum with bootstrap
   intervals, the paired difference, Cohen's kappa and the disputed cases.
3. The review also has to settle what the replacement only approximates: "in English" and the response language
   (langdetect), and the sentence splitter.

## 10. Files

- `audit/ISSUE.md`: the record (progress, pins, hashes, contract changes, held-out split).
- `audit/CONTRACTS.md`: contracts, decision table, changes after v1; `audit/frozen/CONTRACTS_v1_2026-11-11T1128Z.md`.
- `audit/harness.py` (the graders as the pipelines run them), `audit/replacement.py` (the replacement).
- `audit/tests/`: `fixtures_data.py` (203 fixtures), `known_wrong.py` (strict xfails), `test_fixtures.py`,
  `verdicts.py`. Run: `../.venv/Scripts/python.exe -m pytest -p no:cacheprovider -q ../audit/tests` from `case/`.
- `audit/scripts/`: `grade_panel.py` (step 5 grading), `analyze_panel.py`, `table.py`, `review.py` (development-set
  excerpts), `step4.py`, `repro.py`, `run_fixtures.py`, data scripts.
- `audit/out/`: per-run verdict files `panel/*.jsonl`, `panel_summary.json`, `panel_table.txt`, `step4.json`,
  `repro_all.txt`, `fixture_verdicts.json`.
