# Audit report: IFBench grader (Marin's vendored Evalchemy copy)

Written 2026-11-10 from 07:27 UTC, after both review label files had been read. Paths are relative
to `W = <W>`. The running record (pinned inputs, contract
hashes, decision entries, findings, frozen-sample hashes, log) is `audit/ISSUE.md`; the contracts
and the decision table are in `audit/CONTRACT.md` (version 2). The planned step 6 analysis is
`audit/scripts/analyze_review.py`, written before any label existed. Everything computed after the
labels were read is marked "post-label": some review statistics in section 3, the attribution of
review errors in sections 3.4 to 3.6, every share of verdicts in section 5, the four findings of
section 5.4, the "Review" column of section 6, and section 8. Section 4 and the step 3 to 5
results come from before the review.

## 1. Error rate and effect on scores

- **Error rate.** On the 5,452 instruction verdicts of the held-out runs (one run per
  configuration of the stored panel, extraction failures excluded), the grader's strict verdict
  differs from the consensus of two blinded reviewers on an estimated **7.2%** of verdicts (95%
  bootstrap interval 5.9% to 9.1%). The replacement grader built from the contracts errs on 3.0%
  (1.7% to 4.9%); the paired difference is 4.2 points (3.5 to 4.9). The benchmark authors'
  reference implementation errs on 7.0% (5.6% to 8.9%), loose grading on 7.8% (5.4% to 10.7%).
  Post-label: the grader's 7.2% splits into false passes 3.4% and false fails 3.8%.
- **Extraction failures.** 136 thinking-on responses never close `<think>`; the grader grades their
  reasoning and passes 45 of their 157 instruction verdicts (15 of 52 in the held-out runs), all
  of which the contract fails (finding F-extract-unclosed). They are outside the 7.2%.
- **Effect on scores.** Grading the stored panel (16 configurations, 228 runs, 68,400 responses)
  with the replacement instead of the grader changes prompt-level strict accuracy by -4.9 to +1.6
  points per configuration (mean over runs). The change exceeds the greedy rerun difference for 13
  of the 16 configurations, and the ranking changes: Qwen3-14B with thinking moves from second to
  first, Qwen2.5-14B-Instruct from third to fifth.
- **Findings.** 52 findings were recorded before the review labels were read (4 unpinned inputs,
  46 checker defects, the loose transform and the extraction rule); post-label analysis added 4
  checker defects and 1 replacement error (section 5.4). The decision entries (47) are listed
  separately for the maintainers (section 6).
- **Recommendation: fix the grader.** Under the rule recorded in `audit/ISSUE.md` before the review
  (section 2), the grader is not admitted (error rate above 2%), the benchmark is not replaced
  (reviewer kappa 0.94, ambiguous verdicts 19%), and the replacement qualifies as the fix: it
  passes all 277 fixtures, has complete scored coverage, and has a lower error rate with a paired
  interval that excludes zero.

## 2. Recommendation and the rule recorded before the review

The rule, recorded 2026-11-09 23:48 UTC before any review started (`audit/ISSUE.md`, Step 6):
the planned recommendation is "fix the grader"; it changes to "admit" if the grader's weighted
error rate is at most 2% with an upper 95% bound of at most 3% and no finding affects more than 1%
of verdicts; it changes to "replace the benchmark" if Cohen's kappa between the reviewers' leans
is below 0.40 or more than 25% of the cases get `ambiguous` from either reviewer. The replacement
is proposed as the fix only if it passes every fixture, scored coverage is complete, and its
weighted error rate is lower than the grader's with a paired 95% bootstrap interval that excludes
zero; otherwise the fix is the per-finding repair list.

| Condition | Measured | Met |
|---|---|---|
| Admit: grader error rate at most 2%, upper bound at most 3% | 7.22%, upper bound 9.15% | no |
| Replace: kappa below 0.40 | 0.939 | no |
| Replace: `ambiguous` from either reviewer on more than 25% of cases | 88 of 458 (19.2%) | no |
| Replacement passes every fixture | 277 of 277 (`audit/tests/test_fixtures_replacement.py`, rerun 2026-11-10) | yes |
| Replacement scored coverage complete | 100% of 78,432 panel verdicts, no exception | yes |
| Replacement error lower, paired interval excludes zero | grader minus replacement +4.20 points (+3.47 to +4.91) | yes |

**Recommended action: fix the grader by replacing its checkers with the replacement grader
(`audit/replacement/ifbench_contract.py`), with each of the 47 decision entries set to the reading
the maintainers choose.** The fix also covers the pipeline findings: grade an unclosed reasoning
as an extraction failure (F-extract-unclosed), drop loose grading or limit it to deletions that
G4 allows (F-loose-deletes-constrained), and pin the dataset revision and the NLTK data (F-pin-3,
F-pin-4). Before adoption the replacement also needs one repair found after the review: it does
not take a flag emoji as an emoji (REPL-emoji-flag, section 5.4). That repair, readings that differ
from the proposed ones, or any other change made in response to this round needs another review
round on held-out responses that no earlier round used (step 6.1); section 3.6 lists the readings
the reviewers' consensus preferred.

## 3. Blinded review (step 6)

### 3.1 Sample and reviewers

- Population: the held-out run of each of the 16 configurations (`audit/frozen/heldout_runs.tsv`,
  chosen before any replacement graded the panel), every instruction verdict except the 52
  extraction failures: 5,452 verdicts. Drawn by `audit/scripts/draw_review_sample.py`, seed 61109;
  case list sha256 f360e359…24f4d recorded before any review.
- Reviewers: two runs of one language model, Claude Opus 5.5 (`claude-opus-5-5`); no person
  labeled a case. Each run had only its prompt (`audit/frozen/review_round1/prompt_reviewer_A.md`
  or `_B.md`, from `skill/references/reviewer-prompt.md`) and copies of its own batches in a folder
  of its own, saw the cases in its own random order (seeds 61110 and 61111), and saw no source
  model, grader verdict or other reviewer's label. The operator's record
  (`audit/frozen/reviews/README.md`) states that a script read every tool call of both runs and
  found no access to the key, the graders or the network; the audit relies on that record.
  Because both reviewers are one model, they can share blind spots: their agreement is likely
  higher than independent reviewers would reach, and an error they share does not show as a
  dispute.
- Label files: `audit/frozen/reviews/review_A.jsonl` (sha256 5eec6b18…321fc) and `review_B.jsonl`
  (d809a126…cb0a3), 458 lines each, every case once, valid fields, in batch order
  (`audit/scripts/check_reviews.py`).

### 3.2 Agreement

The leans agree on 444 of 458 cases (96.9%); Cohen's kappa on the leans is 0.939. Reviewer A
gave `ambiguous` 54 times, reviewer B 71 times, either of them 88 times (19.2%).

### 3.3 Error rates

Per stratum, errors among the cases with a consensus:

| Stratum | Definition | Population | Sample | Consensus (pass) | Grader strict | Grader loose | Reference strict | Replacement |
|---|---|---|---|---|---|---|---|---|
| S1a | grader pass, replacement fail | 250 | 170 | 161 (61) | 100 | 100 | 93 | 61 |
| S1b | grader fail, replacement pass | 180 | 125 | 124 (120) | 120 | 74 | 116 | 4 |
| S2 | grader = replacement, reference differs | 3 | 3 | 3 (0) | 0 | 0 | 3 | 0 |
| S3 | all three agree | 5,019 | 160 | 156 (40) | 2 | 5 | 2 | 2 |

Weighted by stratum population, 95% bootstrap intervals from 10,000 draws within strata
(`audit/scripts/analyze_review.py`, output `audit/work/analyze_review.log`):

| Grader | Against the consensus (444 cases) | Over cases with two agreeing definite verdicts (370) |
|---|---|---|
| grader strict | 7.22% (5.87% to 9.15%) | 6.94% (6.01% to 8.45%) |
| grader loose | 7.77% (5.44% to 10.70%) | 7.45% (5.36% to 10.04%) |
| reference strict | 6.97% (5.62% to 8.89%) | 6.75% (5.79% to 8.24%) |
| reference loose | 7.55% (5.22% to 10.47%) | 7.32% (5.19% to 9.91%) |
| replacement | 3.02% (1.68% to 4.93%) | 2.15% (1.24% to 3.63%) |

Paired differences of the weighted error rates (consensus labels):

| Difference | Estimate | 95% interval | Planned |
|---|---|---|---|
| grader strict minus replacement | +4.20 points | +3.47 to +4.91 | yes |
| grader strict minus replacement, definite cases | +4.79 points | +3.93 to +5.62 | yes |
| grader strict minus reference strict | +0.25 points | +0.08 to +0.44 | post-label |
| grader strict minus grader loose | -0.55 points | -3.36 to +1.86 | post-label |
| reference strict minus replacement | +3.95 points | +3.22 to +4.66 | post-label |

Post-label (`audit/scripts/analyze_review_post.py`, output `audit/work/analyze_review_post.log`):
the grader's strict error splits into false passes 3.44% (2.60% to 4.89%) and false fails 3.79%
(3.12% to 5.03%). The graders have two labels, so this split is the whole confusion matrix that
step 6.5 asks for.

How to read these numbers:
- S3 carries 92% of the weight, so each S3 case with an error adds about 0.59 points to a
  grader's rate. Two S3 cases are wrong for the grader, the reference and the replacement alike
  (section 3.5); they add about 1.2 points to each of those rates and cancel in the paired
  differences between them.
- The paired difference between grader and replacement comes from S1a and S1b, where the two
  disagree by construction and which were sampled at 68% and 69% of their population.
- The bootstrap applies no finite-population correction, so the intervals are slightly wide.

### 3.4 Where the errors are (consensus cases)

Grader strict errors and replacement errors per check, from `audit/work/analyze_review.log`; the
last column (post-label) names the findings of section 5 or the decision readings that give the
grader's wrong verdict.

| Check | Cases | Grader errors | Replacement errors | Grader errors explained by |
|---|---|---|---|---|
| format:sub-bullets | 54 | 41 (5 false pass, 36 false fail) | 11 | F-subbullets-bold, F-subbullets-none, F-subbullets-any-hyphen |
| format:no_bullets_bullets | 25 | 23 | 0 | F-nbb-blank-line, F-nbb-trailing-text, F-nbb-period |
| format:quotes | 24 | 18 (13 false pass) | 3 | F-quotes-apostrophe, F-quotes-curly |
| words:start_verb | 18 | 18 (16 false fail) | 0 | F-startverb-tagger, F-startverb-markup |
| count:conjunctions | 18 | 18 (all false pass) | 0 | D-conj B 10, F-conj-surface-forms 8 |
| ratio:overlap | 16 | 12 | 0 | D-overlap D 12 (character trigrams) |
| format:emoji | 14 | 8 (all false fail) | 2 | D-sentence B 8 |
| format:line_indent | 11 | 8 | 0 | D-vacuous B 7 (a single line passes), D-indent C 1 |
| words:palindrome | 8 | 7 | 0 | D-palindrome B or C 7 |
| count:word_count_range | 9 | 6 | 0 | F-wordcount-contractions 4, D-between B 1, D-word B 1 |
| count:punctuation | 8 | 6 | 1 | F-punct-six-marks 5, D-punct-set B 1 |
| format:thesis | 28 | 5 | 19 | F-thesis-anywhere 4, D-section B 1 |
| format:output_template | 7 | 5 | 0 | F-template-presence-only 4, D-template C 1 |
| sentence:alliteration_increment | 8 | 5 | 0 | F-alliteration-sum |
| sentence:keyword | 15 | 4 | 1 | D-sentence B 4 |
| format:options | 7 | 4 | 0 | F-options-whitespace, F-options-case |
| custom:csv_city | 4 | 4 | 0 | D-csv B or C 4 |
| format:quote_unquote | 17 | 3 | 13 | F-quote-separator (straight quotes followed by a separator or by text that does not explain them) |
| custom:csv_quotes | 4 | 3 | 0 | D-csv B or C 3 |
| count:pronouns | 6 | 3 | 0 | F-pronouns-determiners |
| custom:sentence_alphabet | 4 | 3 | 0 | F-alphabet-story-quote 2, D-sentence B 1 |
| words:paragraph_last_first | 4 | 3 | 0 | F-paralastfirst-comma |
| custom:mcq_count_length | 3 | 3 | 0 | F-mcq-label-number 2, D-mcq B 1 |
| the other 31 checks | 132 | 12 | 17 | see `audit/work/analyze_review_post.log` |

The attribution of a grader error to a finding is by check and direction (false pass or false
fail), not by re-running a repaired grader on each case; section 5 says what would measure each
finding's share exactly.

### 3.5 Cases that all three graders get wrong (S3)

- R1-bd01c, custom:date_format_list: all graders pass; consensus fail (A `ambiguous`, lean fail; B
  fail). The response lists six well-formed dates; both reviewers fail it because six dates are
  far from all of Napoleon's battles. The contract checks only the format (D-custom-facts reading
  A); reading C (the dates must be his battles) gives fail.
- R1-cab3d, format:emoji: all graders fail; consensus pass (both definite, high confidence): each
  of ten one-sentence lines ends with an emoji. Post-label: all three fail only because the first
  emoji is the US flag, which they do not recognize as an emoji; each of the other nine lines
  passes alone (finding F-emoji-flag, replacement error REPL-emoji-flag, section 5.4).

### 3.6 Readings the reviewers' consensus took (post-label)

For each replacement error, the key (`audit/frozen/review_round1/key.jsonl`, field
`replacement_alt`) shows which single decision switch would have given the consensus verdict. The
consensus took a non-proposed reading in these cases: D-section B (sections without headings are
one section) 15 of 19 format:thesis errors; D-vacuous B (a response without quoted phrases passes
format:quote_unquote; too few words pass count:words_japanese) 19; D-subbullet B (an unindented
"- " line after a bullet is a sub-bullet) 11; D-paren C (unmatched brackets count toward depth) 6;
one case each for D-sentence B or C, D-match B, D-csv E and D-punct-set B. In the other direction,
the consensus rejected the grader's non-proposed reading for D-sentence B 15 times, D-overlap D 12,
D-conj B 10, D-palindrome B or C 7, D-csv B or C 7 and D-vacuous B 8. These are leans of one model
run twice, not decisions; the maintainers decide (section 6).

### 3.7 Disputed cases (leans differ)

14 cases; the audit does not resolve them. Verdict, lean and confidence are given as A / B;
reasons are paraphrased from the label files.

| Case | Check | Stratum | Grader / replacement | Reviewer A | Reviewer B | What separates them |
|---|---|---|---|---|---|---|
| R1-01ccd | count:punctuation | S1a | pass / fail | fail, fail, medium | ambiguous, pass, low | hyphen, ellipsis or brackets missing; B passes if the core marks suffice (D-punct-set) |
| R1-16c2c | count:punctuation | S1a | pass / fail | fail, fail, medium | ambiguous, pass, low | brackets, dash or ellipsis missing (D-punct-set) |
| R1-41866 | count:punctuation | S1a | pass / fail | fail, fail, medium | ambiguous, pass, low | no dash, ellipsis or braces; "!" only inside the interrobang (D-punct-set) |
| R1-75ca4 | count:punctuation | S1a | pass / fail | fail, fail, medium | ambiguous, pass, low | no brackets, dash or ellipsis; "!" only inside "?!" (D-punct-set) |
| R1-8040f | count:punctuation | S1a | pass / fail | fail, fail, medium | ambiguous, pass, low | no standalone "!" or "?", no ellipsis, braces or dash (D-punct-set) |
| R1-0c405 | format:list | S3 | pass / pass | ambiguous, fail, low | ambiguous, pass, low | "!?!?" after each item inside one paragraph: is a trailing separator a list (D-list) |
| R1-14449 | format:list | S1a | pass / fail | fail, fail, high | ambiguous, pass, low | "-." separators inside running prose (D-list) |
| R1-462f8 | count:unique_word_count | S1a | pass / fail | ambiguous, fail, medium | pass, pass, medium | Russian text with LaTeX: 33 unique words without LaTeX commands, 55 to 59 with them (D-word) |
| R1-dd7c3 | count:unique_word_count | S3 | pass / pass | ambiguous, fail, medium | pass, pass, medium | 49 unique words outside LaTeX; more if LaTeX commands count (D-word) |
| R1-59bba | custom:multiples | S3 | fail / fail | ambiguous, pass, medium | ambiguous, fail, low | correct multiples plus explanation and code that print other numbers (D-custom-extra-text) |
| R1-6f93a | format:quote_unquote | S3 | pass / pass | ambiguous, pass, low | ambiguous, fail, low | the text after the only quoted phrase continues the sentence; is that an explanation |
| R1-7e559 | count:conjunctions | S1a | pass / fail | pass, pass, medium | ambiguous, fail, low | "but" and "so" occur only in a list of conjunctions the response names; "for" as a preposition (D-conj) |
| R1-d86c8 | format:sub-bullets | S1a | pass / fail | ambiguous, pass, low | ambiguous, fail, low | top-level items marked "- *", sub-items "- -": is "- *" a `*` bullet |
| R1-e4820 | format:title_case | S1b | fail / pass | fail, fail, high | ambiguous, pass, low | the response is in capitals: every major word starts with a capital, but it is not title case |

## 4. Effect on scores (step 5, stored panel)

Prompt-level strict accuracy, mean over runs, grader and replacement (proposed readings); the
range of the change over runs in brackets; rerun = |greedy - greedy_repeat| under the grader
(`audit/scripts/analyze_panel.py`, `audit/work/analyze_panel.log`).

| Configuration | Runs | Grader | Replacement | Change (points) | Rerun (points) |
|---|---|---|---|---|---|
| Qwen2.5-14B-Instruct | 17 | 34.1 | 29.1 | -4.9 [-7.7, -2.7] | 1.0 |
| Qwen2.5-32B-Instruct | 13 | 35.2 | 32.9 | -2.3 [-4.0, -0.3] | 1.3 |
| Qwen2.5-7B-Instruct | 17 | 27.4 | 24.1 | -3.4 [-7.3, -1.0] | 0.3 |
| Qwen3-14B | 17 | 27.7 | 26.0 | -1.7 [-3.0, +0.3] | 0.3 |
| Qwen3-14B, thinking | 3 | 34.3 | 35.3 | +1.0 [+0.7, +1.3] | 1.0 |
| Qwen3-32B | 13 | 25.1 | 25.5 | +0.4 [-1.7, +2.3] | 0.7 |
| Qwen3-8B | 17 | 25.2 | 23.7 | -1.5 [-3.3, +0.3] | 0.0 |
| Qwen3-8B, thinking | 3 | 32.4 | 30.9 | -1.6 [-2.0, -0.7] | 0.0 |
| Llama-3.1-Tulu-3-8B | 17 | 22.7 | 23.3 | +0.6 [-1.7, +2.3] | 0.3 |
| OLMo-2-0325-32B-Instruct | 13 | 33.3 | 30.4 | -2.9 [-4.3, -1.0] | 0.0 |
| OLMo-2-1124-13B-Instruct | 17 | 22.6 | 18.8 | -3.9 [-6.0, -2.0] | 0.0 |
| OLMo-2-1124-7B-Instruct | 17 | 20.4 | 17.3 | -3.1 [-6.0, -1.7] | 0.7 |
| marin-8b-instruct | 17 | 17.4 | 16.9 | -0.5 [-3.3, +1.7] | 1.0 |
| phi-4 | 17 | 19.1 | 20.3 | +1.2 [-1.3, +3.0] | 0.0 |
| Mistral-7B-Instruct-v0.3 | 17 | 17.6 | 15.8 | -1.8 [-3.7, -0.3] | 0.3 |
| Mistral-Small-24B-Instruct-2501 | 13 | 21.8 | 23.4 | +1.6 [-0.3, +3.0] | 0.3 |

Other step 5 counts: grader strict passes 27.7% of the 78,432 instruction verdicts, grader loose
32.4%, reference strict 27.6%, replacement 25.4%. Grader and replacement differ on 6,226
verdicts (7.9%); one switched decision reproduces the grader in 2,718 of them. 4,165 responses
(6.1%) stopped at the token limit; they are graded as they stand (G2), and the grader passes 1,013
of their 4,588 instruction verdicts, the replacement 793. These score changes use the proposed
readings; choosing another reading for a decision entry changes the verdicts counted in the
"Panel" column of section 6, and the scores with them.

## 5. Findings

A finding is a verdict that is wrong under every reading the task text allows, an unpinned input,
or a grader exception. 56 findings: before the labels were read, 4 pins, 44 checker defects with a
step 3 fixture, and 4 found by property tests, targeted inputs or the panel; after them, 4 checker
defects (section 5.4). "Ref" is the status in the reference implementation at allenai/IFBench
1c40f0c.

**Share of verdicts** (all post-label, 78,275 panel verdicts without extraction failures).
- "Bound": the panel verdicts in the finding's check and direction (false pass or false fail)
  where the grader and the replacement disagree and no reading of the check's decision entries,
  alone or in pairs, gives the grader's verdict (`audit/scripts/regrade_disagreements.py`,
  `audit/work/regrade_disagreements.log`). It is an upper bound: findings of one check and
  direction share it, and it also holds replacement errors. A bound of 0 means the defect makes
  no stored verdict wrong.
- "Edit": for ten findings, the verdicts that change when an edit the contract ignores removes
  exactly the finding's trigger, for example deleting bold markers for F-subbullets-bold
  (`audit/scripts/metamorphic_shares.py`, `audit/work/metamorphic_shares.log`). This counts the
  verdicts the defect decides; the grader is wrong on those of them that the bound also counts.
- In the tables, a number without a label is the bound.
- What would measure every remaining share exactly: grade the stored `response` field of
  `case/panel/*/*.jsonl` with the grader and with a copy of the grader in which only that defect
  is repaired, and count the verdicts that change.

Of the 3,287 disagreements that no reading explains, all but 11 fall in a check and direction
that a finding covers; the 11 (format:quote_unquote 5 false fails, format:emoji 3 false passes,
format:newline 1, custom:reverse_newline 1, ratio:stop_words 1) are not classified.

Every finding's counterexample, as an exact input with the command that reproduces the grader's
verdict and that command's output, is in Appendix A.

### 5.1 Unpinned inputs

| Id | Stage | Defect | Effect | Ref |
|---|---|---|---|---|
| F-pin-1 | grader provenance | The case records no Marin or Evalchemy commit for the vendored grader; only file hashes in `case/MANIFEST.sha256` pin it. | Cannot be measured from the case. Verify with `git -C <marin checkout> log -1 --format=%H -- <vendored IFBench path>`. | n/a |
| F-pin-2 | generation settings | Stop sequences are recorded for no configuration, and the vLLM version is not recorded for the two thinking configurations (`case/panel/CONFIGS.md`). | Not measurable offline; the field that would show it is the stop list and vLLM version of each run's generation config. | n/a |
| F-pin-3 | grader dependencies | At import, `instructions.py` creates `.nltk_data` next to itself, puts it first on `nltk.data.path`, and sets `NLTK_DATA` to it when unset; `instructions_util.py` then downloads any missing NLTK package (latest version, from the network). The NLTK data used is pinned only when the caller provides it. | Every verdict of the checks that tokenize, tag or use stop words can change with an NLTK data update. | same |
| F-pin-4 | dataset | `eval_instruct.py` line 61 loads `allenai/IFBench_test` with no revision. | A dataset update changes prompts and kwargs silently. | n/a (`run_eval.py` reads the file given by `--input_data`) |

### 5.2 Checker defects

| Id | Check | Defect | Contract it breaks (`audit/CONTRACT.md`) | Fixture | Share of panel verdicts (bound; edit) | Ref |
|---|---|---|---|---|---|---|
| F-conj-surface-forms | count:conjunctions | Distinct conjunctions are counted by raw token, so "and", "And" and "and," are three. | distinct members, case-insensitive | count:conjunctions-81617dea | bound 188 of 1,589 (false pass); edit (lower case, punctuation removed) changes 187 | same |
| F-numbers-joined | count:numbers | Punctuation is deleted before digit runs are counted, so "9-11" is one number. | each maximal digit group is one number | count:numbers-18e30b2e | bound 5 of 1,824 (both directions: "1929-1939" can also bring the count down to N); edit (spaces around the join) changes 5 | same |
| F-pronouns-determiners | count:pronouns | this, that, these, those, all, some, any, each, both count as pronouns when they are determiners. | demonstratives and indefinites count only "used as pronouns" | count:pronouns-776a2e0f | 160 of 1,819 (false pass) | same |
| F-punct-six-marks | count:punctuation | Only . , ? ! ; : and the interrobang are required. | every standard mark, including apostrophe, quotation mark, hyphen, dash, brackets (fails under D-punct-set B too) | count:punctuation-601839ea | 191 of 1,368 (false pass) | same |
| F-wordcount-contractions | count:word_count_range | Words are `\w+` runs, so a contraction or decimal counts as two words. | D-word: a contraction is one word under every reading | count:word_count_range-1cde9d43 | bound 39 of 2,508 (both directions, shared with F-wordcount-html-tags); edit (in-word apostrophes removed) changes 57 | same |
| F-japanese-skip-tokens | count:words_japanese | Punctuation-only tokens take positions but are exempt when they land on an Nth position. | positions N, 2N, ... must hold Japanese words | count:words_japanese-b951151d | 33 of 1,137 (false pass) | same |
| F-charrev-substring | custom:character_reverse | Any response containing "elgae dlab" passes. | the whole response read backwards answers the query, nothing else | custom:character_reverse-20633f9c | 5 of 228 (false pass) | same |
| F-wordrev-mixed | custom:word_reverse | A normal-order answer followed by a reversed copy passes. | one sentence, words in reverse order | custom:word_reverse-babe3eb6 | 5 of 228 (false pass) | same |
| F-csvspecial-early-return | custom:csv_special_character | The row loop returns at the first quoted special field; later rows are not checked for 5 fields. | every row has 5 fields | custom:csv_special_character-5af2501d | 1 of 228 (false pass) | same |
| F-dates-invalid | custom:date_format_list | Month 00 and day 00 are accepted. | valid calendar dates | custom:date_format_list-8e75a21f | 0 of 228 | same |
| F-capitals-kyiv | custom:european_capitals_sort | The expected list omits Kyiv (50.45 N). | all capitals north of 45 degrees N | custom:european_capitals_sort-75101278 | 0 of 228 (no stored response passes either way) | same |
| F-mcq-label-number | custom:mcq_count_length | Questions are split on "Question <digit>", so the label "Question:" fails. | each question starts with the label "Question" | custom:mcq_count_length-05811cfb | 28 of 228 (false fail) | same |
| F-africa-numbering | custom:reverse_newline | List numbers stay in the sorted strings, so a numbered list in correct order fails. | list numbering allowed | custom:reverse_newline-a8b76fa4 | 0 of 225 | same |
| F-alphabet-story-quote | custom:sentence_alphabet | The first character, not the first letter, is compared. | the first word starts with the i-th letter | custom:sentence_alphabet-bfdf2432 | 23 of 228 (false fail) | fixed |
| F-indent-tabs | format:line_indent | Only spaces count as indentation. | more leading whitespace than the line before | format:line_indent-66b6dfe6 | 0 of 2,052 | same |
| F-indent-blank-lines | format:line_indent | One blank line between stairs is ignored, two consecutive blank lines fail (the checker removes items from the list it iterates over). | blank lines are ignored | `audit/tests/test_properties.py::indent-second-blank-line` | at most 2 of 2,052 (false fail; D-indent C also reproduces them) | same |
| F-list-anywhere | format:list | Two occurrences of the separator anywhere pass; with "-", two hyphenated words pass. | a list of at least two items marked with the separator | format:list-ba07ac37 | 79 of 2,051 (false pass) | same |
| F-newline-blank-offset | format:newline | Space-only lines count as lines and offset the line count, so a line with two words can pass. | every line with a word has exactly one word | format:newline-70967df1 | 0 of 1,363 | same |
| F-nbb-blank-line | format:no_bullets_bullets | Any blank line after the first bullet fails the response. | two sentences then two `*` bullets; nothing about blank lines | format:no_bullets_bullets-f3697474 | bound 321 of 1,140, shared with F-nbb-trailing-text (false fail); edit (blank lines collapsed) changes 139 | same |
| F-nbb-trailing-text | format:no_bullets_bullets | Any text after the bullets fails the response. | "at least" two sentences and two bullets; later text is not forbidden | format:no_bullets_bullets-1e4e8bf9 | shared, see F-nbb-blank-line | same |
| F-nbb-period | format:no_bullets_bullets | The sentences before the bullets need not end in a period. | two sentences ending in a period | format:no_bullets_bullets-371f2417 | 37 of 1,140 (false pass) | same |
| F-options-case | format:options | The a)-d) options need an exact, case-sensitive match. | case-insensitive | format:options-e705e191 | bound 78 of 1,368, shared with F-options-whitespace (false fail); all 78 change under the whitespace edit, so 0 are left for this finding | same |
| F-options-whitespace | format:options | A trailing newline, or a line break inside an option, fails. | surrounding whitespace removed, internal whitespace collapsed | format:options-db41d773 (+2) | bound 78 of 1,368 (false fail); edit (whitespace collapsed and stripped) changes 78 | same |
| F-template-presence-only | format:output_template | Only the presence of the three labels is checked. | labels in order, starting the response, each with content | format:output_template-c1479850 (+1) | 47 of 912 (false pass) | same |
| F-quote-curly | format:quote_unquote | Curly quotes are never examined, so a curly-quoted phrase may end the response. | straight or curly quotes, each followed by an explanation | format:quote_unquote-09271858 | edit (curly quotes made straight) changes 0 of 1,140 to fail; the false-pass bound of 83 belongs to F-quote-separator | same |
| F-quotes-apostrophe | format:quotes | Apostrophes count as quote marks, so two quoted contractions make "3 levels". | apostrophes inside words are not quotation marks | format:quotes-986acc3a | bound 212 of 1,817 (false pass) | same |
| F-quotes-curly | format:quotes | Curly quotes are ignored, so a correct curly nest fails. | straight or curly | format:quotes-ba7df411 | bound 93 of 1,817 (false fail); edit (curly quotes made straight) changes 29 fail to pass, but also 13 replacement verdicts, so it is not fully neutral | same |
| F-subbullets-none | format:sub-bullets | A response without any `*` passes. | at least one `*` bullet | format:sub-bullets-68bc3978 | bound 206 of 2,733, shared with F-subbullets-any-hyphen (false pass) | same |
| F-subbullets-any-hyphen | format:sub-bullets | Any hyphen after a `*` counts as a sub-bullet. | a sub-bullet is a line starting with "- " | format:sub-bullets-eac31626 | shared, see F-subbullets-none | same |
| F-subbullets-bold | format:sub-bullets | Bold markup (`**`) makes empty segments, so any bold text fails. | bold text is not forbidden | format:sub-bullets-e7564723 | bound 762 of 2,733 (false fail); edit (bold markers deleted) changes 825 (30.2%) from fail to pass | same |
| F-thesis-anywhere | format:thesis | One italic span anywhere passes. | every section begins with the italic thesis | format:thesis-0be7ab4a | 147 of 2,049 (false pass) | same |
| F-title-contraction | format:title_case | The tokenizer splits "Don't" into "Do" + "n't", and "n't" fails as a lower-case word. | every major word starts with a capital | format:title_case-66236ed6 | bound 0 of 912; edit (in-word apostrophes removed) changes 8, none of them a disagreement that no reading explains | same |
| F-ratio-quote-endings | ratio:sentence_balance, ratio:sentence_type | Sentences ending in a closing quote get no type, so 0:0 counts as balanced and 2:1 can come from untyped sentences. | type by terminal punctuation | ratio:sentence_balance-06d14a8d, ratio:sentence_type-7d8c6c99 | bound 7 of 2,963 (both directions) | same |
| F-sentwords-no-word-check | ratio:sentence_words | "Using all different words" is not checked. | no word appears twice | ratio:sentence_words-65a6de4b | 1 of 1,596 (false pass) | fixed |
| F-stopwords-contractions | ratio:stop_words | `\w+` splits contractions into stop-word fragments ("doesn", "t"). | D-word: a contraction is one word | ratio:stop_words-796f0c51 | 8 of 2,726 (false fail) | same |
| F-repeatchange-whitespace | repeat:repeat_change | An unchanged repetition passes when its whitespace differs from the request. | the first word must change | repeat:repeat_change-14044665 | 0 of 684 | same |
| F-span-characters | repeat:repeat_span | The expected span is cut by character indices; the prompt says word indices. | whitespace-split tokens n_start to n_end | repeat:repeat_span-f5668efe (+2) | 0 of 912 | fixed |
| F-alliteration-sum | sentence:alliteration_increment | All alliterative words of a sentence are summed instead of taking the longest run. | the longest run of consecutive alliterative words | sentence:alliteration_increment-f060bd4c | bound 119 of 1,130 (both directions) | same |
| F-position-contractions | words:keywords_specific_position | The tokenizer splits contractions, shifting word positions. | the m-th word, D-word | words:keywords_specific_position-5d6232b7 | 0 of 912 | same |
| F-lastfirst-quotes | words:last_first | A closing quote stays on the last word. | punctuation stripped | words:last_first-b94487b1 | 35 of 1,140 (false fail) | same |
| F-noconsec-digits | words:no_consecutive | Adjacent numbers starting with the same digit fail. | a token without a letter shares no letter | words:no_consecutive-3f7dfb90 | 0 of 1,820 | same |
| F-paralastfirst-comma | words:paragraph_last_first | Punctuation after the first word breaks the comparison. | punctuation stripped | words:paragraph_last_first-9ba4900d | 29 of 1,368 (false fail) | same |
| F-startverb-tagger | words:start_verb | The NLTK part-of-speech tagger decides: it reads sentence-initial imperatives (Imagine, Build, Explore) as nouns or prepositions, and, in the panel, a first word such as "Dazzling." used as an adjective as a verb. | an imperative first word is a verb; an adjective is not | words:start_verb-4239f418 (+2) | bound 302 of 1,368 (298 false fail, shared with F-startverb-markup; 4 false pass) | same |
| F-startverb-markup | words:start_verb | Markup before the first word ("**Imagine**") is tagged instead of the word. | the first word after markup | words:start_verb-f0af03a0 | edit (markup before the first word and bold markers removed) changes 21 from fail to pass | same |
| F-wordspos-comma | words:words_position | Punctuation tokens count as words except one at the very end. | D-word: punctuation is not a word | words:words_position-bd6267af | 5 of 684 (false fail) | fixed |
| F-csvquotes-indexerror | custom:csv_quotes | An empty field in a response with the header, 3 data rows and 5 fields per row raises `IndexError` (`field.strip()[0]`); the exception leaves `test_instruction_following_strict`, so the run stops unless the caller catches it. | a grader exception; the contract fails the response | targeted input (Appendix A) | 0 of 228 (no stored response has an empty field) | same |

### 5.3 Pipeline findings

| Id | Stage | Defect | Contract | Evidence | Share | Ref |
|---|---|---|---|---|---|---|
| F-loose-deletes-constrained | loose transform (all checks) | Loose grading passes a response if any of 8 variants passes: without its first line, without its last line, without both, each with every `*` removed. These deletions remove text the instructions constrain. | G4 | `audit/tests/test_properties.py::loose-*` (Appendix A) | 2,762 of 78,432 verdicts (3.5%) pass only under loose grading while the contract fails the full response; format:sub-bullets passes 2,736 of 2,736 under loose grading | same |
| F-extract-unclosed | response extraction | A thinking-on completion that never closes `<think>` is stored and graded as its whole reasoning. | G1 | 136 stored responses (`audit/work/panel_scan.csv`); one in Appendix A | 45 of 157 verdicts of those responses pass (15 of 52 in the held-out runs) | n/a |

### 5.4 Findings and a replacement error found after the review labels were read

Found while explaining review case R1-cab3d and the disagreements that no reading explains
(section 8). Their fixtures are in `audit/tests/fixtures_post_label.py`, run by
`audit/tests/test_post_label.py`, and are not part of the 277 fixtures the pre-registered rule
counts.

| Id | Check | Defect | Contract it breaks | Fixture | Share of panel verdicts | Ref |
|---|---|---|---|---|---|---|
| F-sentence-html-tags | sentence-based checks | NLTK's sentence splitter does not end a sentence at a period followed by an HTML closing tag ("distress.</i> This"), so HTML-wrapped sentences merge; on sentence:increment a merged single sentence then passes under D-vacuous B. | D-sentence (every reading) and G5: HTML tags are formatting | sentence:increment-42d871c8 | removing every tag changes 26 of 1,820 sentence:increment verdicts (all pass to fail; 26 of the 27 disagreements there that no reading explains) and no verdict of the other sentence checks among the 377 verdicts tested | same |
| F-wordcount-html-tags | count:word_count_range | `\w+` counts the names inside HTML tags ("p", "i", "em") as words. | G5 | count:word_count_range-cc95e9c6 | removing every tag changes 2 of 2,508 | same |
| F-emoji-flag | format:emoji | `emoji.is_emoji` is applied to single characters, and one regional-indicator character is not an emoji, so a flag at the end of a sentence fails. | "a Unicode emoji character or sequence" | format:emoji-12dd4be2; review case R1-cab3d | replacing each flag with another emoji changes 27 of 2,049 from fail to pass | same |
| F-quote-separator | format:quote_unquote | Only two things are checked: no two quotation marks are adjacent once whitespace is removed, and the text does not end with one. Any symbol between two quoted phrases ("=", "-") counts as an explanation. | every quoted phrase is followed by an explanation | format:quote_unquote-9b7688e5 | bound 83 of 1,140 (false pass) | same |

Replacement error REPL-emoji-flag: the replacement grader also rejects a flag emoji (replacing each
flag changes 35 of its 2,049 format:emoji verdicts). The replacement was not changed in this round;
its 3.0% error rate includes this defect (R1-cab3d).

Reference-only defect (R-loose-order, minor): `evaluation_lib.test_instruction_following_loose`
passes unfiltered kwargs to `build_description`; it works only because `run_eval.py` calls the
strict function first, which replaces `inp.kwargs[index]` with the filtered dict. Run alone, every
instruction raises `TypeError`.

## 6. Decision entries (for the maintainers)

47 entries; each has both readings, an example of each and the proposed reading in the table at
the end of `audit/CONTRACT.md` (version 2). Counted separately from the findings. "Grader" gives
the reading that the grader's verdicts on the step 3 fixtures match ("A" where no fixture shows
another reading). "Panel" is the number of grader-replacement disagreements that switching to the
other reading alone reproduces (of 6,226; `audit/work/analyze_panel.log`, which computed a subset
of readings per check); "-" means the switch was not computed for the panel. "Review"
(post-label) counts consensus cases where the switched reading gives the consensus verdict and the
proposed one does not ("other") and cases where the proposed reading gives the consensus against a
grader verdict that the switch reproduces ("proposed").

| Id | Proposed reading (A) | Other readings | Grader | Panel | Review: other / proposed |
|---|---|---|---|---|---|
| D-vacuous | a requirement on units the response lacks fails | B: holds vacuously | B (a lone "." passes 14 checks the contract fails) | 440 | 19 / 1, plus 7 single-line format:line_indent cases found by reading them (no switch computed) |
| D-word | whitespace token, punctuation stripped, contains a letter or digit | B: hyphenated compounds split; C: every token, symbols included | C | B 87, C 37 | 0 / 1 |
| D-word-numbers | digit-only tokens are words | B: skipped by letter rules | A | 0 | 0 / 0 |
| D-sentence | ends at . ! ? or a line break; headings are not sentences | B: only punctuation ends one; C: every line fragment | B | B 230, C 18 | 1 / 15 |
| D-paragraph | lines for paragraph_last_first, blank-line blocks elsewhere | B: blank-line blocks always; C: every line break | C | 0 | 0 / 0 |
| D-match | whole word, case-insensitive | B: substring; C: inflections | B | B 28, C 1 | 1 / 0 |
| D-keyword-count | exactly that many | at least that many | A | 0 | 0 / 0 |
| D-conj | counts only where it functions as a conjunction | every occurrence | B | 221 | 0 / 10 |
| D-number | digit groups, list markers and years count | B: no list markers; C: spelled-out numbers count | A | 0 | 0 / 0 |
| D-names-case | capitalized name | case-insensitive | A | 0 | 0 / 0 |
| D-pronoun | all pronoun classes used as pronouns | B: personal, possessive, reflexive; C: B without determiners | A (plus F-pronouns-determiners) | B 5, C 5 | 0 / 0 |
| D-punct-set | 14 marks plus the interrobang | B: core marks plus the interrobang | below B (F-punct-six-marks) | 76 | 1 / 1 |
| D-unique | case-insensitive types | B: case-sensitive; C: words used once | A | B 5 | 0 / 0 |
| D-between | inclusive bounds | exclusive | A | 47 | 0 / 1 |
| D-japanese | whitespace words, Japanese script | B: segmented words; C: romaji counts | A | 0 | 0 / 0 |
| D-emoji-position | emoji after or directly before the final punctuation | only after | A | 24 | 0 / 2 |
| D-indent | strictly increasing indent, blank lines ignored | B: constant step; C: blank lines break stairs | C (in part, F-indent-blank-lines) | C 2 | 0 / 1 |
| D-list | separator at item starts or between items, short lead-in allowed | B: starts only; C: between only; D: nothing else | below every reading (F-list-anywhere) | 0 | 0 / 0 |
| D-options | the whole response is one option | B: may explain; C: bare letter; D: bare option string only | D | D 20 | 0 / 0 |
| D-template | emphasis and line breaks allowed, nothing before "My Answer:" | B: exact characters; C: lead-in allowed | C (plus F-template-presence-only) | C 37 | 0 / 1 |
| D-paren | mixed kinds, properly matched | B: round only; C: unmatched openers count | C | C 201, B 39 | 6 / 1 |
| D-subbullet | a sub-bullet is indented deeper | any "- " line after a bullet | B | 245 | 11 / 0 |
| D-section | heading blocks, else blank-line paragraphs | B: no headings means one section | B | 360 | 15 / 1 |
| D-title | minor words may be lower case | B: every word capitalized; C: minor words lower case | B | C 18, B 6 | 0 / 0 |
| D-overlap | reference = request; word trigrams; share of response trigrams | B: share of reference; C: Jaccard; D: character trigrams; E: relative band | D (the reference uses word trigrams) | D 205, B 39, C 33, E 33 | 0 / 12 |
| D-balance | exact counts | B: approximately; C: type by grammar | A | 15 | 0 / 0 |
| D-char-count | all characters | B: letters; C: non-space | A | 0 | 0 / 0 |
| D-different-words | no word repeated anywhere | none shared between sentences | not checked (F-sentwords-no-word-check) | 0 | 0 / 0 |
| D-stopwords | NLTK English list | another list | A | - | 0 / 0 |
| D-repeat-change | first word replaced, rest verbatim, nothing else | B: later text allowed; C: case change counts | C | 0 | 0 / 0 |
| D-repeat-simple | output the instruction sentence | output the request | A | 0 | 0 / 0 |
| D-span | 0-based, only the span | B: 1-based; C: surrounded by text | A (by characters, F-span-characters) | 0 | 0 / 0 |
| D-alliteration | same first letter, single word = run of 1 | B: same sound; C: runs of 2 or more | A (plus F-alliteration-sum) | C 1 | 0 / 0 |
| D-alphabet-start | first word any letter | must start with A | A | 0 | 0 / 0 |
| D-y | y is a consonant | y is a vowel when it sounds as one | A | 0 | 0 / 0 |
| D-syllables | dictionary pronunciation | vowel-group estimate | B (syllapy) | - | 0 / 0 |
| D-palindrome | distinct real words | B: repeats count; C: any palindromic string | B and C | 317 | 0 / 7 |
| D-prime-length | letters and digits | all characters after stripping | A | 0 | 0 / 0 |
| D-repeat-count | at most n occurrences | at most n + 1 | A | 0 | 0 / 0 |
| D-verb | any verb form heading a verb phrase | imperative or finite only | tagger-based (F-startverb-tagger) | 7 | 0 / 0 |
| D-vowel | at most three vowel letters, one paragraph | B: per word; C: exactly three per word; D: no paragraph rule | A | B 1 | 0 / 0 |
| D-custom-facts | content named by the prompt is checked; Napoleon dates format only | B: format only everywhere; C: Napoleon dates must be correct | B and C | B 3, C 1 | 0 / 2 |
| D-custom-extra-text | only the requested items | B: lead-in allowed; C: multiples alone | A | 0 | 0 / 1 |
| D-csv | data rows after the header, code fence allowed, one special field | B: rows include header; C: no text outside; D: data fields only quoted; E: at least one special field | C and E | B 146, C 144, E 12 | 1 / 7 |
| D-char-reverse | whole sentence reversed by character | each word reversed | A (plus F-charrev-substring) | 0 | 0 / 0 |
| D-mcq | question text length in characters | B: words or whole block; C: answer key counts | A | 10 | 0 / 1 |
| D-trailing-ws | whitespace anywhere counts | trailing whitespace ignored | A | 0 | 0 / 0 |

## 7. Steps skipped or substituted

- No issue tracker: `audit/ISSUE.md` holds what the skill puts in the issue; the report is posted
  here instead of in an issue, and `file-issue` was not used.
- No repository, research branch, Hugging Face dataset or job launcher: fixtures are runnable
  tests under `audit/tests/`, frozen samples, keys and reviews are under `audit/frozen/` with
  their sha256 in `audit/ISSUE.md`; nothing went through `research-engineering`, `manage-pr` or
  `use-iris`.
- Step 1: no network, so the reference commit and the dataset revision were checked only against
  `case/MANIFEST.sha256`, not against GitHub or the Hub (the commands that would verify them are
  in `audit/ISSUE.md`). Evalchemy's generation step is not in the case, so the extraction rule the
  grader actually receives is unverified (location: Evalchemy `eval/sources/common.py`).
- Step 5: no compute, so no responses were generated; the 228 stored runs are the panel, and the
  required rerun comparison uses the stored greedy and greedy_repeat runs.
- Step 6: both reviewers are runs of one model, and their separation is the operator's record,
  not something the audit could observe.
- `skill/references/ifbench.md` and `skill/references/validation.md` are linked by the skill but
  not provided in this run.
- The contract was revised once after the grader code had been read (version 2, two readings
  added, no proposed reading changed; reason and effect in `audit/ISSUE.md`, Step 2).

## 8. Further analysis

Done after the first complete version of this report (2026-11-10, 07:31 to 07:45 UTC); all
post-label. Apart from round 1 review cases, responses were read only from non-held-out runs
(`audit/scripts/show_residuals.py`), so that unreviewed held-out responses stay available for a
later round.

1. Regrade of the disagreements (`audit/scripts/regrade_disagreements.py`). The panel grading had
   computed only some decision readings per check. The 6,181 grader-replacement disagreements
   outside extraction failures were graded again with every reading of every decision the
   check's contract lists, plus D-vacuous, alone and in pairs: one reading reproduces the grader
   in 2,873, a pair in 21, none in 3,287. This replaced the cruder per-check bound of
   `audit/scripts/finding_bounds.py` in section 5; for example, all 126 format:line_indent false
   passes are D-vacuous B (a single line passes), not findings.
2. R1-cab3d explained: a flag emoji (F-emoji-flag, REPL-emoji-flag).
3. The 27 sentence:increment disagreements that no reading explains all come from prompts 188,
   189 and 190, which also ask for HTML italics; they led to F-sentence-html-tags. Removing every
   HTML tag (`audit/scripts/metamorphic_post.py`) changes 26 sentence:increment verdicts from pass
   to fail, and 2 count:word_count_range verdicts (F-wordcount-html-tags).
4. The 83 format:quote_unquote false passes that no reading explains are not curly quotes (the
   curly-to-straight edit changes none); reading them led to F-quote-separator.
5. Edit-based shares for ten findings (`audit/scripts/metamorphic_shares.py`), in section 5.

Not done: a second review round. It needs held-out responses that round 1 did not use and a
replacement repaired for REPL-emoji-flag with the maintainers' readings.

## 9. How to reproduce

From W in Git Bash (NLTK_DATA is set by `audit/lib/ifb.py` for the audit's scripts; for pytest set
it as `case/TASK.md` shows):

    export NLTK_DATA=<W>/case/deps/nltk_data
    .venv/Scripts/python.exe -B audit/scripts/pin_inputs.py                 # pins against the manifest
    PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python.exe -m pytest -p no:cacheprovider -q audit/tests
    .venv/Scripts/python.exe -B audit/scripts/check_reviews.py              # step 6.4 label checks
    .venv/Scripts/python.exe -B audit/scripts/analyze_review.py             # step 6.5, planned analysis
    .venv/Scripts/python.exe -B audit/scripts/analyze_review_post.py        # post-label additions
    .venv/Scripts/python.exe -B audit/scripts/regrade_disagreements.py      # section 5 bounds (several minutes)
    .venv/Scripts/python.exe -B audit/scripts/metamorphic_shares.py         # section 5 edit counts
    .venv/Scripts/python.exe -B audit/scripts/metamorphic_post.py           # section 5.4 tag and flag tests
    .venv/Scripts/python.exe -B audit/scripts/repro.py --all                # one line per finding with a fixture
    .venv/Scripts/python.exe -B audit/scripts/repro.py F-subbullets-none    # one finding in full

`audit/scripts/finding_bounds.py` gives the cruder per-check bound that the regrade replaced.
The final test run (section 10) covers the 277 step 3 fixtures against the grader, the reference
and the replacement, the 18 property tests, and the 4 post-label fixtures. Regrading the whole
panel (`audit/scripts/grade_panel.py`) takes much longer and rewrites
`audit/work/panel_verdicts.jsonl`.

## 10. Verification

On 2026-11-10 from 07:44 to 07:51 UTC, `bash audit/scripts/verify_all.sh` reran every command of
section 9 and kept each output under `audit/work/verify/`; each command exited 0.
- `pin_inputs.py`: all 424 manifest entries match, the dataset row-hash list equals the frozen one
  (dead3343…e7ad7), installed packages equal the lock.
- pytest: 679 passed, 182 xfailed. The xfails are the recorded wrong verdicts: grader 84 and
  reference 75 of the 277 step 3 fixtures, 14 property tests, and 9 of the 12 post-label fixture
  tests (grader 4, reference 4, replacement 1). The replacement passes all 277 step 3 fixtures.
- `check_reviews.py`, `analyze_review.py`, `analyze_review_post.py`, `finding_bounds.py`,
  `metamorphic_shares.py`, `metamorphic_post.py` and `regrade_disagreements.py` print output
  identical to the logs this report quotes.
- `verify_report.py` ran each of the 56 commands of Appendix A as a separate process: every
  output equals the text shown.
- Nothing under `audit/frozen/` changed: the review label files and README still have the hashes in
  `audit/ISSUE.md`, and `audit/frozen/review_round1/` still matches its `MANIFEST.sha256`.

## Appendix A. Counterexamples

Each entry gives the command (run from W) and exactly what it prints: the input as a Python string
literal, the dataset prompt whose kwargs and text the check uses, the contract label, and the
verdicts of the grader (strict and loose), the reference (strict) and the replacement.

<!-- counterexamples:begin -->

### F-pin-1

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-pin-1` prints:

```text
F-pin-1   40-hex commit ids in case/TASK.md and case/panel/CONFIGS.md:
  TASK.md:14: - `reference/IFBench/`: the benchmark authors' implementation and its unit tests (`instruc
  TASK.md:15: - `data/train-00000-of-00001.parquet`: the IFBench_test set, 300 prompts (huggingface.co/d
  panel/CONFIGS.md: 16 table rows, each the Hugging Face revision of a panel model
  none names a Marin or Evalchemy commit of the vendored grader
```

### F-pin-2

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-pin-2` prints:

```text
F-pin-2   case/panel/CONFIGS.md
  mentions of stop sequences ('stop sequence', 'stop='): 0
  line 32: | `Qwen__Qwen3-8B__thinking` | Qwen/Qwen3-8B | b968826d9c46dd6066d109eabc6255188de91218 | on | 8,192 | not rec
  line 37: | `Qwen__Qwen3-14B__thinking` | Qwen/Qwen3-14B | 40c069824f4251a91eefaf281ebe4c544efd3e18 | on | 8,192 | not r
  line 46: - The vLLM version was not recorded for the two thinking configurations.
```

### F-pin-3

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-pin-3` prints:

```text
F-pin-3   case/grader/IFBench/instructions.py lines 26-32:
  26: _nltk_data_dir = Path(__file__).parent / ".nltk_data"
  27: _nltk_data_dir.mkdir(exist_ok=True)
  28: os.environ.setdefault("NLTK_DATA", str(_nltk_data_dir))
  30: import nltk
  32: nltk.data.path.insert(0, str(_nltk_data_dir))
  instructions_util.py: nltk.download calls at lines [1556, 1560, 1564, 1568], module-level call at line 1571
  after importing the audit's copy: nltk.data.path[0] = audit\work\pkgs\grader\IFBench\.nltk_data
```

### F-pin-4

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-pin-4` prints:

```text
F-pin-4   case/grader/IFBench/eval_instruct.py line 61: dataset: Dataset = load_dataset("allenai/IFBench_test", split="train")
```

### F-conj-surface-forms

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-conj-surface-forms` prints:

```text
F-conj-surface-forms   fixture count:conjunctions-81617dea
  check: count:conjunctions   dataset prompt key: 7   kwargs: {"small_n": 3.0}
  response (35 characters, Python literal): 'Cats and dogs. And birds and, fish.'
  contract label: fail
  grader strict: pass   grader loose: pass   reference strict: pass   replacement: fail
```

### F-numbers-joined

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-numbers-joined` prints:

```text
F-numbers-joined   fixture count:numbers-18e30b2e
  check: count:numbers   dataset prompt key: 17   kwargs: {"N": 2.0}
  response (28 characters, Python literal): 'The meeting runs 9-11 today.'
  contract label: pass
  grader strict: fail   grader loose: fail   reference strict: fail   replacement: pass
```

### F-pronouns-determiners

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-pronouns-determiners` prints:

```text
F-pronouns-determiners   fixture count:pronouns-776a2e0f
  check: count:pronouns   dataset prompt key: 33   kwargs: {"N": 5.0}
  response (67 characters, Python literal): 'This book, that pen, these cups, those hats, and all bags are here.'
  contract label: fail
  grader strict: pass   grader loose: pass   reference strict: pass   replacement: fail
```

### F-punct-six-marks

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-punct-six-marks` prints:

```text
F-punct-six-marks   fixture count:punctuation-601839ea
  check: count:punctuation   dataset prompt key: 36   kwargs: {}
  response (49 characters, Python literal): 'Really?! Yes, it works: it is fine; yes. Go! Why?'
  contract label: fail
  grader strict: pass   grader loose: pass   reference strict: pass   replacement: fail
```

### F-wordcount-contractions

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-wordcount-contractions` prints:

```text
F-wordcount-contractions   fixture count:word_count_range-1cde9d43
  check: count:word_count_range   dataset prompt key: 43   kwargs: {"max_words": 28.0, "min_words": 24.0}
  response (158 characters, Python literal): "We don't know and it isn't clear. Alpha bravo charlie delta echo foxtrot golf hotel india juliet kilo lima mike november oscar papa quebec romeo sierra tango."
  contract label: pass
  grader strict: fail   grader loose: fail   reference strict: fail   replacement: pass
```

### F-japanese-skip-tokens

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-japanese-skip-tokens` prints:

```text
F-japanese-skip-tokens   fixture count:words_japanese-b951151d
  check: count:words_japanese   dataset prompt key: 47   kwargs: {"N": 5.0}
  response (44 characters, Python literal): 'One two three four - five six seven eight 日本'
  contract label: fail
  grader strict: pass   grader loose: pass   reference strict: pass   replacement: fail
```

### F-charrev-substring

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-charrev-substring` prints:

```text
F-charrev-substring   fixture custom:character_reverse-20633f9c
  check: custom:character_reverse   dataset prompt key: 273   kwargs: {}
  response (69 characters, Python literal): 'The answer is the bald eagle. Reversed: .elgae dlab eht si rewsna ehT'
  contract label: fail
  grader strict: pass   grader loose: pass   reference strict: pass   replacement: fail
```

### F-csvspecial-early-return

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-csvspecial-early-return` prints:

```text
F-csvspecial-early-return   fixture custom:csv_special_character-5af2501d
  check: custom:csv_special_character   dataset prompt key: 276   kwargs: {}
  response (390 characters, Python literal): 'ProductID,Category,Brand,Price,Stock\nP001,Toys,"Tom & Jerry",11,101\nP002,Toys,Brand2,12,102\nP003,Toys,Brand3,13,103\nP004,Toys,Brand4,14,104\nP005,Toys,Brand5,15,105,extra\nP006,Toys,Brand6,16,106\nP007,Toys,Brand7,17,107\nP008,Toys,Brand8,18,108\nP009,Toys,Brand9,19,109\nP010,Toys,Brand10,20,110\nP011,Toys,Brand11,21,111\nP012,Toys,Brand12,22,112\nP013,Toys,Brand13,23,113\nP014,Toys,Brand14,24,114'
  contract label: fail
  grader strict: pass   grader loose: pass   reference strict: pass   replacement: fail
```

### F-dates-invalid

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-dates-invalid` prints:

```text
F-dates-invalid   fixture custom:date_format_list-8e75a21f
  check: custom:date_format_list   dataset prompt key: 277   kwargs: {}
  response (22 characters, Python literal): '1805-00-00, 1796-04-12'
  contract label: fail
  grader strict: pass   grader loose: pass   reference strict: pass   replacement: fail
```

### F-capitals-kyiv

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-capitals-kyiv` prints:

```text
F-capitals-kyiv   fixture custom:european_capitals_sort-75101278
  check: custom:european_capitals_sort   dataset prompt key: 278   kwargs: {}
  response (245 characters, Python literal): 'Reykjavik, Helsinki, Oslo, Tallinn, Stockholm, Riga, Moscow, Copenhagen, Vilnius, Minsk, Dublin, Berlin, Amsterdam, Warsaw, London, Brussels, Kyiv, Prague, Luxembourg, Paris, Vienna, Bratislava, Budapest, Vaduz, Chisinau, Bern, Ljubljana, Zagreb'
  contract label: pass
  grader strict: fail   grader loose: fail   reference strict: fail   replacement: pass
```

### F-mcq-label-number

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-mcq-label-number` prints:

```text
F-mcq-label-number   fixture custom:mcq_count_length-05811cfb
  check: custom:mcq_count_length   dataset prompt key: 279   kwargs: {}
  response (544 characters, Python literal): 'Question: Who painted Guernica?\nA) Picasso\nB) Dali\nC) Miro\nD) Matisse\nE) Braque\n\nQuestion: Which movement did Salvador Dali belong to?\nA) Surrealism\nB) Cubism\nC) Fauvism\nD) Dada\nE) Pop Art\n\nQuestion: Which artist is best known for the drip paintings made in the late 1940s?\nA) Jackson Pollock\nB) Mark Rothko\nC) Willem de Kooning\nD) Franz Kline\nE) Lee Krasner\n\nQuestion: Which German art school, founded in 1919 by Walter Gropius, joined crafts and the fine arts in one program?\nA) Bauhaus\nB) Black Mountain\nC) De Stijl\nD) Vkhutemas\nE) Cranbrook'
  contract label: pass
  grader strict: fail   grader loose: fail   reference strict: fail   replacement: pass
```

### F-africa-numbering

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-africa-numbering` prints:

```text
F-africa-numbering   fixture custom:reverse_newline-a8b76fa4
  check: custom:reverse_newline   dataset prompt key: 281   kwargs: {}
  response (739 characters, Python literal): '1. Zimbabwe\n2. Zambia\n3. Uganda\n4. Tunisia\n5. Togo\n6. Tanzania\n7. Sudan\n8. South Sudan\n9. South Africa\n10. Somalia\n11. Sierra Leone\n12. Seychelles\n13. Senegal\n14. Sao Tome and Principe\n15. Rwanda\n16. Republic of the Congo\n17. Nigeria\n18. Niger\n19. Namibia\n20. Mozambique\n21. Morocco\n22. Mauritius\n23. Mauritania\n24. Mali\n25. Malawi\n26. Madagascar\n27. Libya\n28. Liberia\n29. Lesotho\n30. Kenya\n31. Ivory Coast\n32. Guinea-Bissau\n33. Guinea\n34. Ghana\n35. Gambia\n36. Gabon\n37. Ethiopia\n38. Eswatini\n39. Eritrea\n40. Equatorial Guinea\n41. Egypt\n42. Djibouti\n43. Democratic Republic of the Congo\n44. Comoros\n45. Chad\n46. Central African Republic\n47. Cape Verde\n48. Cameroon\n49. Burundi\n50. Burkina Faso\n51. Botswana\n52. Benin\n53. Angola\n54. Algeria'
  contract label: pass
  grader strict: fail   grader loose: fail   reference strict: fail   replacement: pass
```

### F-alphabet-story-quote

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-alphabet-story-quote` prints:

```text
F-alphabet-story-quote   fixture custom:sentence_alphabet-bfdf2432
  check: custom:sentence_alphabet   dataset prompt key: 282   kwargs: {}
  response (379 characters, Python literal): 'A cat sat. "Birds sing," said Ann. Cows mooed. Dogs barked. Eagles soared. Foxes ran. Geese honked. Horses neighed. Insects buzzed. Jays chirped. Kids laughed. Lions roared. Mice squeaked. Nobody slept. Owls hooted. Pigs grunted. Quails called. Rabbits hopped. Snakes hissed. Turtles crawled. Unicorns danced. Voles dug. Wolves howled. Xerus scurried. Yaks grazed. Zebras rested.'
  contract label: pass
  grader strict: fail   grader loose: fail   reference strict: pass   replacement: pass
```

### F-wordrev-mixed

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-wordrev-mixed` prints:

```text
F-wordrev-mixed   fixture custom:word_reverse-babe3eb6
  check: custom:word_reverse   dataset prompt key: 283   kwargs: {}
  response (77 characters, Python literal): 'The bald eagle is the answer. eagle bald the is US the of symbol national The'
  contract label: fail
  grader strict: pass   grader loose: pass   reference strict: pass   replacement: fail
```

### F-indent-tabs

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-indent-tabs` prints:

```text
F-indent-tabs   fixture format:line_indent-66b6dfe6
  check: format:line_indent   dataset prompt key: 73   kwargs: {}
  response (31 characters, Python literal): 'Line one\n\tLine two\n\t\tLine three'
  contract label: pass
  grader strict: fail   grader loose: pass   reference strict: fail   replacement: pass
```

### F-list-anywhere

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-list-anywhere` prints:

```text
F-list-anywhere   fixture format:list-ba07ac37
  check: format:list   dataset prompt key: 86   kwargs: {"sep": "-"}
  response (83 characters, Python literal): 'Quantum entanglement is well-known, but its link to parallel worlds is far-fetched.'
  contract label: fail
  grader strict: pass   grader loose: pass   reference strict: pass   replacement: fail
```

### F-newline-blank-offset

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-newline-blank-offset` prints:

```text
F-newline-blank-offset   fixture format:newline-70967df1
  check: format:newline   dataset prompt key: 90   kwargs: {}
  response (22 characters, Python literal): 'Remake would\n \nfeature'
  contract label: fail
  grader strict: pass   grader loose: pass   reference strict: pass   replacement: fail
```

### F-nbb-blank-line

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-nbb-blank-line` prints:

```text
F-nbb-blank-line   fixture format:no_bullets_bullets-f3697474
  check: format:no_bullets_bullets   dataset prompt key: 95   kwargs: {}
  response (97 characters, Python literal): 'Deism sees God as distant. This view has problems.\n* It ignores revelation.\n\n* It weakens prayer.'
  contract label: pass
  grader strict: fail   grader loose: fail   reference strict: fail   replacement: pass
```

### F-nbb-period

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-nbb-period` prints:

```text
F-nbb-period   fixture format:no_bullets_bullets-371f2417
  check: format:no_bullets_bullets   dataset prompt key: 95   kwargs: {}
  response (74 characters, Python literal): 'Is God distant? Many say so!\n* It ignores revelation.\n* It weakens prayer.'
  contract label: fail
  grader strict: pass   grader loose: pass   reference strict: pass   replacement: fail
```

### F-nbb-trailing-text

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-nbb-trailing-text` prints:

```text
F-nbb-trailing-text   fixture format:no_bullets_bullets-1e4e8bf9
  check: format:no_bullets_bullets   dataset prompt key: 95   kwargs: {}
  response (122 characters, Python literal): 'Deism sees God as distant. This view has problems.\n* It ignores revelation.\n* It weakens prayer.\nIn short, the view fails.'
  contract label: pass
  grader strict: fail   grader loose: pass   reference strict: fail   replacement: pass
```

### F-options-case

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-options-case` prints:

```text
F-options-case   fixture format:options-e705e191
  check: format:options   dataset prompt key: 102   kwargs: {"options": "a), b), c), d)"}
  response (2 characters, Python literal): 'D)'
  contract label: pass
  grader strict: fail   grader loose: fail   reference strict: fail   replacement: pass
```

### F-options-whitespace

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-options-whitespace` prints:

```text
F-options-whitespace   fixture format:options-db41d773
  check: format:options   dataset prompt key: 100   kwargs: {"options": "yes/no/maybe"}
  response (6 characters, Python literal): 'Maybe\n'
  contract label: pass
  grader strict: fail   grader loose: pass   reference strict: fail   replacement: pass
F-options-whitespace   fixture format:options-7015982d
  check: format:options   dataset prompt key: 102   kwargs: {"options": "a), b), c), d)"}
  response (3 characters, Python literal): 'd)\n'
  contract label: pass
  grader strict: fail   grader loose: pass   reference strict: fail   replacement: pass
F-options-whitespace   fixture format:options-2518151c
  check: format:options   dataset prompt key: 105   kwargs: {"options": "I know or I don't know"}
  response (12 characters, Python literal): "I\ndon't\nknow"
  contract label: pass
  grader strict: fail   grader loose: fail   reference strict: fail   replacement: pass
```

### F-template-presence-only

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-template-presence-only` prints:

```text
F-template-presence-only   fixture format:output_template-c1479850
  check: format:output_template   dataset prompt key: 292   kwargs: {}
  response (96 characters, Python literal): 'Future Outlook: More research.\nMy Answer: Cosmic suffering.\nMy Conclusion: A thought experiment.'
  contract label: fail
  grader strict: pass   grader loose: pass   reference strict: pass   replacement: fail
F-template-presence-only   fixture format:output_template-3e0e9872
  check: format:output_template   dataset prompt key: 292   kwargs: {}
  response (73 characters, Python literal): 'My Answer: [answer] My Conclusion: [conclusion] Future Outlook: [outlook]'
  contract label: fail
  grader strict: pass   grader loose: pass   reference strict: pass   replacement: fail
```

### F-quote-curly

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-quote-curly` prints:

```text
F-quote-curly   fixture format:quote_unquote-09271858
  check: format:quote_unquote   dataset prompt key: 116   kwargs: {}
  response (54 characters, Python literal): 'The statement says “Each neuron connects to all nodes”'
  contract label: fail
  grader strict: pass   grader loose: pass   reference strict: pass   replacement: fail
```

### F-quotes-apostrophe

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-quotes-apostrophe` prints:

```text
F-quotes-apostrophe   fixture format:quotes-986acc3a
  check: format:quotes   dataset prompt key: 119   kwargs: {}
  response (39 characters, Python literal): '"I can\'t" and "won\'t" are contractions.'
  contract label: fail
  grader strict: pass   grader loose: pass   reference strict: pass   replacement: fail
```

### F-quotes-curly

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-quotes-curly` prints:

```text
F-quotes-curly   fixture format:quotes-ba7df411
  check: format:quotes   dataset prompt key: 119   kwargs: {}
  response (55 characters, Python literal): 'He said, “She told me, ‘The sign read “Closed” today.’”'
  contract label: pass
  grader strict: fail   grader loose: fail   reference strict: fail   replacement: pass
```

### F-subbullets-none

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-subbullets-none` prints:

```text
F-subbullets-none   fixture format:sub-bullets-68bc3978
  check: format:sub-bullets   dataset prompt key: 126   kwargs: {}
  response (31 characters, Python literal): 'Eclipses affect plants briefly.'
  contract label: fail
  grader strict: pass   grader loose: pass   reference strict: pass   replacement: fail
```

### F-subbullets-any-hyphen

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-subbullets-any-hyphen` prints:

```text
F-subbullets-any-hyphen   fixture format:sub-bullets-eac31626
  check: format:sub-bullets   dataset prompt key: 126   kwargs: {}
  response (59 characters, Python literal): '* Light drops\n  - Photosynthesis slows\n* Short-term cooling'
  contract label: fail
  grader strict: pass   grader loose: pass   reference strict: pass   replacement: fail
```

### F-subbullets-bold

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-subbullets-bold` prints:

```text
F-subbullets-bold   fixture format:sub-bullets-e7564723
  check: format:sub-bullets   dataset prompt key: 126   kwargs: {}
  response (50 characters, Python literal): '**Effects**\n* Light drops\n  - Photosynthesis slows'
  contract label: pass
  grader strict: fail   grader loose: pass   reference strict: fail   replacement: pass
```

### F-thesis-anywhere

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-thesis-anywhere` prints:

```text
F-thesis-anywhere   fixture format:thesis-0be7ab4a
  check: format:thesis   dataset prompt key: 142   kwargs: {}
  response (95 characters, Python literal): 'The party has a long history.\n\nIt values order, and <i>tradition is central</i> to its program.'
  contract label: fail
  grader strict: pass   grader loose: pass   reference strict: pass   replacement: fail
```

### F-title-contraction

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-title-contraction` prints:

```text
F-title-contraction   fixture format:title_case-66236ed6
  check: format:title_case   dataset prompt key: 291   kwargs: {}
  response (27 characters, Python literal): "Japan's Leaders Don't Rest."
  contract label: pass
  grader strict: fail   grader loose: fail   reference strict: fail   replacement: pass
```

### F-ratio-quote-endings

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-ratio-quote-endings` prints:

```text
F-ratio-quote-endings   fixture ratio:sentence_balance-06d14a8d
  check: ratio:sentence_balance   dataset prompt key: 155   kwargs: {}
  response (88 characters, Python literal): 'Luther called him "a fool." Melanchthon called it "absurd." Others asked, "Is he right?"'
  contract label: fail
  grader strict: pass   grader loose: pass   reference strict: pass   replacement: fail
F-ratio-quote-endings   fixture ratio:sentence_type-7d8c6c99
  check: ratio:sentence_type   dataset prompt key: 163   kwargs: {}
  response (77 characters, Python literal): 'Some call it "paraphrasing." Others say "rewording." Others say "rephrasing."'
  contract label: fail
  grader strict: pass   grader loose: pass   reference strict: pass   replacement: fail
```

### F-sentwords-no-word-check

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-sentwords-no-word-check` prints:

```text
F-sentwords-no-word-check   fixture ratio:sentence_words-65a6de4b
  check: ratio:sentence_words   dataset prompt key: 166   kwargs: {}
  response (38 characters, Python literal): 'The cat sat. The cat ran. The cat hid.'
  contract label: fail
  grader strict: pass   grader loose: pass   reference strict: fail   replacement: fail
```

### F-stopwords-contractions

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-stopwords-contractions` prints:

```text
F-stopwords-contractions   fixture ratio:stop_words-796f0c51
  check: ratio:stop_words   dataset prompt key: 173   kwargs: {"percentage": 20.0}
  response (49 characters, Python literal): "Python doesn't extract filenames quickly anymore."
  contract label: pass
  grader strict: fail   grader loose: fail   reference strict: fail   replacement: pass
```

### F-repeatchange-whitespace

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-repeatchange-whitespace` prints:

```text
F-repeatchange-whitespace   fixture repeat:repeat_change-14044665
  check: repeat:repeat_change   dataset prompt key: 61   kwargs: {"prompt_to_repeat": "Use Python code: construct a 3-layers feedforward network with 8 input neurons, 20 hidden neurons, and 2 output neurons."}
  response (121 characters, Python literal): 'Use Python code: construct a 3-layers feedforward network with 8 input neurons, 20 hidden neurons, and 2 output neurons.\n'
  contract label: fail
  grader strict: pass   grader loose: pass   reference strict: pass   replacement: fail
```

### F-span-characters

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-span-characters` prints:

```text
F-span-characters   fixture repeat:repeat_span-f5668efe
  check: repeat:repeat_span   dataset prompt key: 287   kwargs: {"n_end": 12, "n_start": 10, "prompt_to_repeat": "how to find what value in a quadratic function lands on a certain point. "}
  response (12 characters, Python literal): 'on a certain'
  contract label: pass
  grader strict: fail   grader loose: fail   reference strict: pass   replacement: pass
F-span-characters   fixture repeat:repeat_span-da49c6f3
  check: repeat:repeat_span   dataset prompt key: 287   kwargs: {"n_end": 12, "n_start": 10, "prompt_to_repeat": "how to find what value in a quadratic function lands on a certain point. "}
  response (3 characters, Python literal): 'd w'
  contract label: fail
  grader strict: pass   grader loose: pass   reference strict: fail   replacement: fail
F-span-characters   fixture repeat:repeat_span-022a9cb5
  check: repeat:repeat_span   dataset prompt key: 284   kwargs: {"n_end": 6, "n_start": 3, "prompt_to_repeat": "explain the context, code and theory behind the paper Identifying Candidate Spaces for Advert Implantation."}
  response (22 characters, Python literal): 'code and theory behind'
  contract label: pass
  grader strict: fail   grader loose: fail   reference strict: pass   replacement: pass
```

### F-alliteration-sum

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-alliteration-sum` prints:

```text
F-alliteration-sum   fixture sentence:alliteration_increment-f060bd4c
  check: sentence:alliteration_increment   dataset prompt key: 178   kwargs: {}
  response (65 characters, Python literal): 'Many mighty machines matter. Big bulbs glow and soft songs sound.'
  contract label: fail
  grader strict: pass   grader loose: pass   reference strict: pass   replacement: fail
```

### F-position-contractions

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-position-contractions` prints:

```text
F-position-contractions   fixture words:keywords_specific_position-5d6232b7
  check: words:keywords_specific_position   dataset prompt key: 11   kwargs: {"keyword": "beneath", "m": 34, "n": 23}
  response (844 characters, Python literal): "Sentence bravo stays short. Sentence charlie stays short. Sentence delta stays short. Sentence echo stays short. Sentence foxtrot stays short. Sentence golf stays short. Sentence hotel stays short. Sentence india stays short. Sentence juliet stays short. Sentence kilo stays short. Sentence lima stays short. Sentence mike stays short. Sentence november stays short. Sentence oscar stays short. Sentence papa stays short. Sentence quebec stays short. Sentence romeo stays short. Sentence sierra stays short. Sentence tango stays short. Sentence uniform stays short. Sentence victor stays short. Sentence whiskey stays short. Alpha bravo charlie delta echo foxtrot golf hotel india juliet kilo lima mike november oscar papa quebec romeo sierra tango uniform victor whiskey xray yankee zulu apple banana cherry date elder fig don't beneath today."
  contract label: pass
  grader strict: fail   grader loose: fail   reference strict: fail   replacement: pass
```

### F-lastfirst-quotes

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-lastfirst-quotes` prints:

```text
F-lastfirst-quotes   fixture words:last_first-b94487b1
  check: words:last_first   dataset prompt key: 220   kwargs: {}
  response (37 characters, Python literal): 'Saturn has "clouds." Clouds form ice.'
  contract label: pass
  grader strict: fail   grader loose: fail   reference strict: fail   replacement: pass
```

### F-noconsec-digits

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-noconsec-digits` prints:

```text
F-noconsec-digits   fixture words:no_consecutive-3f7dfb90
  check: words:no_consecutive   dataset prompt key: 225   kwargs: {}
  response (32 characters, Python literal): 'Open talk on 10 11 topics helps.'
  contract label: pass
  grader strict: fail   grader loose: fail   reference strict: fail   replacement: pass
```

### F-paralastfirst-comma

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-paralastfirst-comma` prints:

```text
F-paralastfirst-comma   fixture words:paragraph_last_first-9ba4900d
  check: words:paragraph_last_first   dataset prompt key: 241   kwargs: {}
  response (40 characters, Python literal): 'Sets, in topology, can be infinite sets.'
  contract label: pass
  grader strict: fail   grader loose: fail   reference strict: fail   replacement: pass
```

### F-startverb-tagger

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-startverb-tagger` prints:

```text
F-startverb-tagger   fixture words:start_verb-4239f418
  check: words:start_verb   dataset prompt key: 257   kwargs: {}
  response (45 characters, Python literal): 'Imagine an empire built on eternal suffering.'
  contract label: pass
  grader strict: fail   grader loose: fail   reference strict: fail   replacement: pass
F-startverb-tagger   fixture words:start_verb-92841d44
  check: words:start_verb   dataset prompt key: 257   kwargs: {}
  response (32 characters, Python literal): 'Build an empire of endless pain.'
  contract label: pass
  grader strict: fail   grader loose: fail   reference strict: fail   replacement: pass
F-startverb-tagger   fixture words:start_verb-d6b959c7
  check: words:start_verb   dataset prompt key: 257   kwargs: {}
  response (30 characters, Python literal): 'Explore the idea of an empire.'
  contract label: pass
  grader strict: fail   grader loose: fail   reference strict: fail   replacement: pass
```

### F-startverb-markup

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-startverb-markup` prints:

```text
F-startverb-markup   fixture words:start_verb-f0af03a0
  check: words:start_verb   dataset prompt key: 257   kwargs: {}
  response (41 characters, Python literal): '**Imagine** an empire built on suffering.'
  contract label: pass
  grader strict: fail   grader loose: fail   reference strict: fail   replacement: pass
```

### F-wordspos-comma

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-wordspos-comma` prints:

```text
F-wordspos-comma   fixture words:words_position-bd6267af
  check: words:words_position   dataset prompt key: 16   kwargs: {"keyword": "despite"}
  response (43 characters, Python literal): 'Yes, despite the rain, we went despite all.'
  contract label: pass
  grader strict: fail   grader loose: fail   reference strict: pass   replacement: pass
```

### F-indent-blank-lines

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-indent-blank-lines` prints:

```text
F-indent-blank-lines   one blank line between stairs
  check: format:line_indent   dataset prompt key: 74   kwargs: {}
  response (35 characters, Python literal): 'Line one\n  Line two\n\n    Line three'
  contract label: pass (blank lines are ignored)
  grader strict: pass   grader loose: pass   reference strict: pass   replacement: pass
F-indent-blank-lines   two blank lines between stairs
  check: format:line_indent   dataset prompt key: 74   kwargs: {}
  response (36 characters, Python literal): 'Line one\n  Line two\n\n\n    Line three'
  contract label: pass (blank lines are ignored)
  grader strict: fail   grader loose: pass   reference strict: fail   replacement: pass
```

### F-csvquotes-indexerror

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-csvquotes-indexerror` prints:

```text
F-csvquotes-indexerror   header of prompt 275 and 3 data rows; the Grade field of row 2 is empty
  check: custom:csv_quotes   dataset prompt key: 275   kwargs: {}
  response (128 characters, Python literal): '"StudentID"\t"Subject"\t"Grade"\t"Semester"\t"Score"\n"1"\t"Math"\t"A"\t"Fall"\t"90"\n"2"\t"Art"\t\t"Fall"\t"85"\n"3"\t"Music"\t"B"\t"Spring"\t"78"'
  contract label: fail (the empty field is not enclosed in double quotes)
  grader strict: exception (IndexError: string index out of range)   grader loose: exception   reference strict: exception (IndexError: string index out of range)   replacement: fail
```

### F-loose-deletes-constrained

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-loose-deletes-constrained` prints:

```text
F-loose-deletes-constrained   format:sub-bullets
  check: format:sub-bullets   dataset prompt key: 126   kwargs: {}
  response (33 characters, Python literal): '* Light drops\n* Temperature falls'
  contract label: fail
  grader strict: fail   grader loose: pass   reference strict: fail   replacement: fail   loose variant that passes: every * removed
F-loose-deletes-constrained   words:start_verb
  check: words:start_verb   dataset prompt key: 257   kwargs: {}
  response (46 characters, Python literal): 'Here is my answer.\nConsider an empire of pain.'
  contract label: fail
  grader strict: fail   grader loose: pass   reference strict: fail   replacement: fail   loose variant that passes: first line removed
F-loose-deletes-constrained   count:keywords_multiple
  check: count:keywords_multiple   dataset prompt key: 2   kwargs: {"keyword1": "door", "keyword2": "bread", "keyword3": "blue", "keyword4": "lamp", "keyword5": "river"}
  response (121 characters, Python literal): 'The door is blue. Bread and bread. Blue blue. Lamp lamp lamp lamp lamp. River river river river river river river.\nRiver.'
  contract label: fail
  grader strict: fail   grader loose: pass   reference strict: fail   replacement: fail   loose variant that passes: last line removed
F-loose-deletes-constrained   count:numbers
  check: count:numbers   dataset prompt key: 17   kwargs: {"N": 2.0}
  response (54 characters, Python literal): 'In 2020 the team had 15 players.\nThat was 3 years ago.'
  contract label: fail
  grader strict: fail   grader loose: pass   reference strict: fail   replacement: fail   loose variant that passes: last line removed
```

### F-extract-unclosed

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-extract-unclosed` prints:

```text
F-extract-unclosed   stored record case/panel/Qwen__Qwen3-8B__thinking/greedy.jsonl, key 234
  completion opens <think>: True   closes it: False   finish_reason: length   graded `response` = 28327 characters, sha256 5f67beec97556569 (reasoning text, not printed)
  words:palindrome: contract label: fail (G1 extraction failure)   grader strict: pass   grader loose: pass
```

### F-sentence-html-tags

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-sentence-html-tags` prints:

```text
F-sentence-html-tags   fixture sentence:increment-42d871c8   (post-label fixture, audit/tests/fixtures_post_label.py)
  check: sentence:increment   dataset prompt key: 190   kwargs: {"small_n": 5.0}
  response (33 characters, Python literal): '<i>Cats sleep.</i> Dogs run fast.'
  contract label: fail
  grader strict: pass   grader loose: pass   reference strict: pass   replacement: fail
```

### F-wordcount-html-tags

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-wordcount-html-tags` prints:

```text
F-wordcount-html-tags   fixture count:word_count_range-cc95e9c6   (post-label fixture, audit/tests/fixtures_post_label.py)
  check: count:word_count_range   dataset prompt key: 43   kwargs: {"max_words": 28.0, "min_words": 24.0}
  response (179 characters, Python literal): '<p>Alpha bravo charlie delta echo foxtrot golf hotel india juliet kilo lima mike.</p>\n<p>November oscar papa quebec romeo sierra tango uniform victor whiskey xray yankee zulu.</p>'
  contract label: pass
  grader strict: fail   grader loose: fail   reference strict: fail   replacement: pass
```

### F-emoji-flag

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-emoji-flag` prints:

```text
F-emoji-flag   fixture format:emoji-12dd4be2   (post-label fixture, audit/tests/fixtures_post_label.py)
  check: format:emoji   dataset prompt key: 65   kwargs: {}
  response (40 characters, Python literal): 'I love this country. 🇺🇸 It is my home. 🎉'
  contract label: pass
  grader strict: fail   grader loose: fail   reference strict: fail   replacement: fail
```

### F-quote-separator

`.venv/Scripts/python.exe -B audit/scripts/repro.py F-quote-separator` prints:

```text
F-quote-separator   fixture format:quote_unquote-9b7688e5   (post-label fixture, audit/tests/fixtures_post_label.py)
  check: format:quote_unquote   dataset prompt key: 116   kwargs: {}
  response (47 characters, Python literal): '"Those" = "Diese" is the German word for those.'
  contract label: fail
  grader strict: pass   grader loose: pass   reference strict: pass   replacement: fail
```

<!-- counterexamples:end -->
