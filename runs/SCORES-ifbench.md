# Score card: blind rerun of the audit-grader skill on IFBench

One run of the skill on a real benchmark, scored against an earlier audit of the same grader. The skill files are in
`skill/r3/` (`SKILL.md` and `references/reviewer-prompt.md` at the head of marin-community/marin PR #10422,
`ea5bd452b`; the run had no `references/ifbench.md` and no `references/validation.md`). The case is described in
`cases/ifbench/`, the run's own files are in `runs/ifbench-r3/`, and the key and the scoring rule are in
`keys/ifbench.md`. `RUNNER.md` gives the prompts. The last section scores two more runs that tested one candidate
rule for the skill.

## Who ran what

| Part of the run | Session | Model | Time (UTC) |
|---|---|---|---|
| Steps 1 to 6.3: pins, contract, fixtures, replacement grader, stress tests, panel, frozen review sample | auditor, session 1 | Claude Opus 5.5 | 2026-11-09 21:55 to 23:54 |
| Step 6.4: 458 labels each | reviewer A and reviewer B, two separate sessions | Claude Opus 5.5 | 2026-11-09 23:55 to 2026-11-10 00:14 (A) and 00:20 (B) |
| Steps 6.5 and 7, and the analysis after the labels | auditor, session 2 | Claude Opus 5.5 | 2026-11-10 07:15 to 07:52 |

Session 1 stopped once it had frozen the review sample, as its brief asked. Session 2 was a new session in the same
working directory. It started from the files when both reviews were in, and was told to write the report before any
further analysis. Everything that the report marks "post-label" comes from session 2.

## Against the earlier audit's findings

| Earlier audit's findings | Reported as a finding | As a decision entry | Not reported | Left out (rule 6) |
|---|---|---|---|---|
| 34 checker findings that hold under every reading | 28 | 3 | 3 | 0 |
| 9 checker findings that rest on a decision | 3 | 5 | 1 | 0 |
| 7 protocol findings | 3 | 2 | 1 | 1 |

Before the review labels arrived, the counts for the 34 findings that hold under every reading were 27 as findings, 3
as decision entries and 4 not reported. The fourth, F27, was added by session 2 from a review case.

"In part" in the table below means that the rerun shows some of the behaviors that the earlier finding lists.

| Earlier finding | Check | Class | Rerun's item | Note |
|---|---|---|---|---|
| F1 | repeat:repeat_span | finding | F-span-characters |  |
| F2 | ratio:overlap | decision entry | D-overlap | character trigrams are the grader's reading of D-overlap |
| F3 | format:sub-bullets | finding | F-subbullets-none, F-subbullets-any-hyphen, F-subbullets-bold |  |
| F4 | format:list | finding | F-list-anywhere |  |
| F5 (rests on a decision) | format:parentheses | decision entry | D-paren |  |
| F6 | ratio:sentence_words | finding | F-sentwords-no-word-check |  |
| F7 | count:keywords_multiple | decision entry | D-match | substring counts are the grader's reading of D-match |
| F8 | words:words_position | finding | F-wordspos-comma |  |
| F9 | custom:sentence_alphabet | finding | F-alphabet-story-quote |  |
| F10 | format:thesis | finding | F-thesis-anywhere | in part: not the `<em>` slicing |
| F11 | format:quote_unquote | finding | F-quote-curly | in part: not the guillemets |
| F12 | format:quotes | finding | F-quotes-apostrophe |  |
| F13 | count:conjunctions | finding | F-conj-surface-forms |  |
| F14 | custom:european_capitals_sort | finding | F-capitals-kyiv |  |
| F15 | custom:csv_quotes | finding | F-csvquotes-indexerror |  |
| F16 | custom:csv_special_character | finding | F-csvspecial-early-return |  |
| F17 | ratio:sentence_type, ratio:sentence_balance | finding | F-ratio-quote-endings | both checks |
| F18 | sentence:alliteration_increment | finding | F-alliteration-sum |  |
| F19 | format:newline | finding | F-newline-blank-offset |  |
| F20 | format:line_indent | finding | F-indent-blank-lines, F-indent-tabs |  |
| F21 | words:paragraph_last_first | finding | F-paralastfirst-comma |  |
| F22 | format:no_bullets_bullets | finding | F-nbb-blank-line, F-nbb-period, F-nbb-trailing-text |  |
| F23 | repeat:repeat_change | finding | F-repeatchange-whitespace |  |
| F24 | format:output_template | finding | F-template-presence-only |  |
| F25 | format:title_case | finding | F-title-contraction | in part: lowercase minor words are the decision D-title |
| F26 | format:options | finding | F-options-whitespace |  |
| F27 | format:emoji | finding | F-emoji-flag | in part, and only after the review: flags, not keycaps or an emoji followed by a letter |
| F28 | words:start_verb | finding | F-startverb-tagger |  |
| F29 (rests on a decision) | count:numbers | finding | F-numbers-joined |  |
| F30 | count:unique_word_count | decision entry | D-word | a standalone punctuation token as a word is the grader's reading of D-word |
| F31 (rests on a decision) | words:consonants | decision entry | D-word |  |
| F32 | words:prime_lengths | not reported | none | curly quotes count toward a word's length |
| F33 (rests on a decision) | count:words_japanese | decision entry | D-vacuous |  |
| F34 (rests on a decision) | words:last_first, words:paragraph_last_first, sentence:increment, format:line_indent | decision entry | D-vacuous |  |
| F35 (rests on a decision) | words:palindrome | decision entry | D-palindrome |  |
| F36 (rests on a decision) | words:keywords_specific_position | finding | F-position-contractions |  |
| F37 | custom:date_format_list | finding | F-dates-invalid | in part: month 00 and day 00, not 1801-02-29 |
| F38 | custom:reverse_newline, custom:word_reverse, custom:character_reverse | finding | F-wordrev-mixed, F-charrev-substring | two of the three checks |
| F39 | custom:mcq_count_length | finding | F-mcq-label-number | in part: not the text before the first label |
| F40 | words:last_first | not reported | none | a comma after the repeated word; F-lastfirst-quotes is another behavior of the check |
| F41 (rests on a decision) | words:start_verb | finding | F-startverb-markup |  |
| F42 (rests on a decision) | words:words_position | not reported | none | a list number shifts the word positions |
| F43 | format:emoji, sentence:keyword | not reported | none | a list label read as a sentence; D-sentence covers line breaks only |
| G1 | protocol | left out | F-loose-deletes-constrained | SKILL.md names loose grading; left out of the counts |
| G2 | protocol | finding | F-options-whitespace | in part: the fixture on prompt 105, not the conflict of its two instructions |
| G3 | protocol | decision entry | D-options |  |
| G4 | protocol | not reported | none | integer arguments stored as doubles |
| G5 | protocol | finding | F-pin-3, F-pin-4 |  |
| G6 | protocol | finding | F-csvquotes-indexerror | in part: the caller that the exception stops is not in the case |
| G7 | protocol | decision entry | D-sentence |  |

Of the earlier audit's 15 decision entries and 3 open questions, the rerun has 11 as decision entries (D-vacuous,
D-distinct-palindromes, D-non-word-tokens, D-minor-words, D-section, D-code-fence, D-list-layout,
D-balanced-nesting, and the three open questions on sentences, sub-bullet nesting and the output surface) and 6 as
findings (D-word-tokens, D-curly-quotes, D-explanation-word, D-tabs, D-option-case, D-number-boundaries). It has no
entry for D-thesis-body.

## The rerun's findings

The rerun lists 56 findings: 40 match the earlier audit, 5 are valid and new, 8 are decision-level, 3 are not about
the grader, and none is false.

No finding is false: every counterexample reproduces on the pinned grader. The scorer reran the run's fixture tests
(`fixture_repro.py`: 277 fixtures, the grader wrong on 84, as the run records) and the run's own command,
`audit/scripts/repro.py --all`, which prints one line for each of the 48 findings that have a fixture; in each the
grader's verdict differs from the contract's label (`keys/tools/ifbench/outputs/repro_all.txt`). Of the other eight,
four are unpinned inputs and have no counterexample, and `repro.py <finding id>` reproduces the other four
(`probe_scoring.py` and `probe_csvquotes.py` reproduce two of them independently).

Three findings are not about the grader files: two are about what the case folder records, and one is about the
stored panel. Eight findings are decision-level under rule 7: the earlier audit lists seven of the questions as
decision entries, and for the eighth one of the rerun's reviewers marked all three reviewed cases ambiguous. The
two audits also disagree the other way: the rerun files as decision entries three behaviors that the earlier audit
counts as findings (F2, F7, F30).

| Rerun's finding | Class | Earlier finding or reason |
|---|---|---|
| F-pin-1 | not about the grader | the working directory records no commit for the vendored grader |
| F-pin-2 | not about the grader | the stored panel's settings file lacks stop sequences and one server version |
| F-pin-3 | matches the earlier audit | G5 |
| F-pin-4 | matches the earlier audit | G5 |
| F-conj-surface-forms | matches the earlier audit | F13 |
| F-numbers-joined | matches the earlier audit | F29 |
| F-pronouns-determiners | decision-level | one of the rerun's two reviewers marked all 3 reviewed cases ambiguous |
| F-punct-six-marks | valid and new | count:punctuation: only six marks and the interrobang are required; in 4 reviewed cases both reviewers gave a definite fail to a response the grader passed |
| F-wordcount-contractions | decision-level | the earlier audit's decision D-word-tokens (is `don't` one word) |
| F-japanese-skip-tokens | valid and new | count:words_japanese: a hyphen at position 5 is skipped; wrong whether or not a hyphen is a word |
| F-charrev-substring | matches the earlier audit | F38 |
| F-wordrev-mixed | matches the earlier audit | F38 |
| F-csvspecial-early-return | matches the earlier audit | F16 |
| F-dates-invalid | matches the earlier audit | F37 |
| F-capitals-kyiv | matches the earlier audit | F14 |
| F-mcq-label-number | matches the earlier audit | F39 |
| F-africa-numbering | valid and new | custom:reverse_newline: a numbered list in the right order fails; the same list without numbers passes |
| F-alphabet-story-quote | matches the earlier audit | F9 |
| F-indent-tabs | matches the earlier audit | F20 |
| F-indent-blank-lines | matches the earlier audit | F20 |
| F-list-anywhere | matches the earlier audit | F4 |
| F-newline-blank-offset | matches the earlier audit | F19 |
| F-nbb-blank-line | matches the earlier audit | F22 |
| F-nbb-trailing-text | matches the earlier audit | F22 |
| F-nbb-period | matches the earlier audit | F22 |
| F-options-case | decision-level | the earlier audit's decision D-option-case |
| F-options-whitespace | matches the earlier audit | F26, G2 |
| F-template-presence-only | matches the earlier audit | F24 |
| F-quote-curly | matches the earlier audit | F11 |
| F-quotes-apostrophe | matches the earlier audit | F12 |
| F-quotes-curly | decision-level | the earlier audit's decision D-curly-quotes |
| F-subbullets-none | matches the earlier audit | F3 |
| F-subbullets-any-hyphen | matches the earlier audit | F3 |
| F-subbullets-bold | matches the earlier audit | F3 |
| F-thesis-anywhere | matches the earlier audit | F10 |
| F-title-contraction | matches the earlier audit | F25 |
| F-ratio-quote-endings | matches the earlier audit | F17 |
| F-sentwords-no-word-check | matches the earlier audit | F6 |
| F-stopwords-contractions | decision-level | the earlier audit's decision D-word-tokens |
| F-repeatchange-whitespace | matches the earlier audit | F23 |
| F-span-characters | matches the earlier audit | F1 |
| F-alliteration-sum | matches the earlier audit | F18 |
| F-position-contractions | matches the earlier audit | F36 |
| F-lastfirst-quotes | valid and new | words:last_first: a quotation mark stays on the last word; the same sentence without quotes passes |
| F-noconsec-digits | decision-level | the earlier audit's decision D-non-word-tokens (are numbers words) |
| F-paralastfirst-comma | matches the earlier audit | F21 |
| F-startverb-tagger | matches the earlier audit | F28 |
| F-startverb-markup | matches the earlier audit | F41 |
| F-wordspos-comma | matches the earlier audit | F8 |
| F-csvquotes-indexerror | matches the earlier audit | F15, G6 |
| F-loose-deletes-constrained | matches the earlier audit | G1 |
| F-extract-unclosed | not about the grader | the stored panel keeps responses whose reasoning never closes |
| F-sentence-html-tags | valid and new | sentence checks: a period followed by an HTML closing tag does not end a sentence, so `<i>Cats sleep.</i> Dogs run fast.` is one sentence; added after the review. The earlier audit notes the behavior under its open question on sentences and found no changed verdict |
| F-wordcount-html-tags | decision-level | the earlier audit's decision D-non-word-tokens (are HTML tags words); added after the review |
| F-emoji-flag | matches the earlier audit | F27 |
| F-quote-separator | decision-level | the earlier audit's decision D-explanation-word (is a symbol after a quote an explanation); added after the review |

## What the missed findings have in common

The four checker findings that the rerun does not report are present in the pinned grader (`probe_scoring.py`).
Each is an input form that the rerun used to show a defect in another check:

| Missed | Input form | Where the rerun used the form |
|---|---|---|
| F42 (`words:words_position`), F43 (`format:emoji`, `sentence:keyword`) | a list label such as `1.` | `custom:reverse_newline` (F-africa-numbering) |
| F32 (`words:prime_lengths`) | curly quotation marks | `format:quotes` (F-quotes-curly), `format:quote_unquote` (F-quote-curly) |
| F40 (`words:last_first`) | punctuation after the repeated word | `words:paragraph_last_first` (F-paralastfirst-comma) |

The rerun's replacement grader gives the verdict that the instruction text asks for on the probe inputs of F32, F40
and F43, so the contract was right and no fixture tried the form on those checks. On F42 the replacement fails with
the grader.

After the review, session 2 went through the two review cases that all three graders got wrong, and it graded the
6,181 panel verdicts on which the grader and the replacement differ again under every reading of the decision
entries: one reading reproduces the grader in 2,873, a pair of readings in 21, none in 3,287. Reading the cases that
no reading explains added four findings (F-emoji-flag, which is part of F27; F-sentence-html-tags;
F-wordcount-html-tags; F-quote-separator) and one error of the replacement, which rejects flag emoji too. The skill
does not ask for this step.

## Step 6

| | Rerun | Earlier audit, round 1 | Earlier audit, round 2 |
|---|---|---|---|
| Error rate of the grader, strict | 7.2% [5.9, 9.1] | 7.6% [4.7, 11.3] | 6.1% [3.9, 10.1] |

The intervals overlap (rule 10). The rerun's sample is 458 of 5,452 held-out verdicts in four strata; the reviewers'
leans agree on 444 cases, Cohen's kappa 0.939. The scorer recomputed the rates from the frozen labels and the run's
key with another bootstrap seed (`score_review.py`): grader 7.22% [5.88, 9.11], replacement 3.02% [1.68, 4.88],
difference +4.20 points [+3.48, +4.90]; the run reports 7.22% [5.87, 9.15], 3.02% [1.68, 4.93] and +4.20 [+3.47,
+4.91]. The two reviewers gave word-for-word identical reasons on 31 cases without access to each other's files,
so the agreement of two runs of one model overstates what two people would reach. The rerun recommends fixing the
grader, as the earlier audit did.

## Counts for the improvement loop

- False findings: 0 of 56. Findings that belong in a decision entry: 8.
- Earlier findings that the rerun does not report: 4 of 43 checker findings (5 before the review) and 1 of 6
  protocol findings.
- Valid findings that one audit has and the other lacks: the rerun has 5, the earlier audit has 4.
- Two-list estimate (rule 11) with n1 = 43 earlier checker findings, n2 = 44 (the 39 that the rerun has as findings
  or decision entries, and its 5 new ones) and m = 39: N = 48.5, against 48 distinct findings in the two lists. Both
  audits used Claude models and the same line of method, so this is a lower bound.

## The auditor's notes on the skill

Session 2 ended with a list of places where the skill's text was unclear:

- Whether "the share of verdicts it affects" means the verdicts that a defect changes or the verdicts that it makes
  wrong. The report gives both.
- Whether "passes every fixture" in the rule recorded before the review covers fixtures added after the labels were
  read. The auditor applied it to the 277 fixtures that existed before.
- What counts as held-out responses "that no earlier round used" when round 1 drew from every held-out run.

## Errors in the run's record

Found while scoring, and left as the auditor wrote them:

- `ISSUE.md`, step 6.3, says that 20 responses longer than 6,000 characters are cut in the batches. One of the 458
  responses is longer than 6,000 characters, and each batch set has one cut response.
- `ISSUE.md`, step 1, abbreviates the sha256 of five case files with a wrong ending (`instructions.py` of the grader;
  `ifbench/instructions.py`, `ifbench/instructions_registry.py`, `evaluation_lib.py` and `instructions_test.py` of
  the reference). The beginnings are right, and the full hashes in the case's `MANIFEST.sha256` match the files.

## Checks on the sessions

A script read every tool call of each session (`rerun_integrity.py`, `reviewer_commands.py`), and another listed the
model of every turn (`transcript_models.py`): all four sessions ran on `claude-opus-5-5` only. The auditor's sessions
ran no command that reaches the network and read nothing outside the working directory. Session 2 wrote one
temporary copy of its report to a scratch folder outside the working directory, for a diff, and deleted it. The
only matches of the script's patterns are the run's own sentence that two skill files were not provided, and
searches for two function names in the grader's code. Each reviewer read only its own batch folder. Both kept
working scripts in a scratch folder outside it, and neither opened the other's files, the key, the case list or a
grader. The sessions were told to work offline inside their folders; nothing enforced it.

## Limits

- One run of one skill version on one benchmark.
- The auditor and both reviewers were Claude Opus 5.5. The earlier audit's reviewers were Claude models too, so the
  two audits can share blind spots.
- The matching of the two reports was done by hand by one scorer, who also coordinated the run, and no second
  reader checked it.

## Two more runs: one candidate rule, with a control

The four missed findings suggest a rule: carry an input form that shows a wrong verdict in one check to the other
checks. Two more blind runs tested it. Both audited the same case through step 5, with one brief
(`runs/ifbench-r4-prompts/brief.txt`), no review, and Claude Opus 5.5:

- `runs/ifbench-r4/`, the control, with `skill/r4/`: SKILL.md of the follow-up to PR #10422, which adds the
  replacement-grader rule to step 3 and the zero-error interval rule to step 6.
- `runs/ifbench-r4-rule/`, with `skill/r4-rule/`: the same file plus one sentence in step 4's bullet on property
  tests: "When an input form shows a wrong verdict in one check, such as a list label before a line, markup around a
  word, a typographic quotation mark, or punctuation after a word, apply it to passing responses of every other
  check, and file each wrong verdict that it causes."

The comparison uses the earlier audit's 143 public fixtures (`key_battery.py`, `battery_table.py`). The grader gets
81 of them wrong, at least one for each of the 43 checker findings. A run "has" a behavior when its replacement
grader, written from its own contracts, gives the earlier audit's label.

| | First rerun (`ifbench-r3`) | Control (`ifbench-r4`) | Rule (`ifbench-r4-rule`) |
|---|---|---|---|
| Of the 81 fixtures that the grader gets wrong, the run's replacement gives the earlier label on | 73 | 56 | 66 |
| Earlier findings with all / some / none of their fixtures corrected | 37 / 5 / 1 | 25 / 9 / 9 | 33 / 6 / 4 |
| Of the 62 fixtures that the grader gets right, the replacement gives the earlier label on | 51 | 57 | 54 |
| Findings in the report | 52 before the review, 56 after | 43 | 42 rows, several over more than one check |
| Fixtures | 277 | 208 | 215 |

The five earlier findings that the first rerun lacked before its review, as reported findings:

| Earlier finding | First rerun | Control | Rule |
|---|---|---|---|
| F27, flag or keycap emoji | after the review (flag) | yes (flag) | yes (flag and keycap) |
| F32, a typographic mark counted in a word's length | no | yes, with a curly apostrophe | yes, with a curly apostrophe |
| F40, a comma after the repeated word | no | yes | no |
| F42, a list number in `words:words_position` | no | no | no; its decision entry D-word names list labels |
| F43, a list label read as a sentence | no | no | no |

The run with the rule followed it: its property tests apply five edits (a trailing newline, curly quotes, a bold
first word, a comma after the first word, an em dash between words) to every passing fixture of the checks that allow
the edit, 199 cases, of which 15 change the grader's verdict, and one of its findings covers seven word checks. It
did not use a list label, the rule's first example. The control found three of the five without the rule.

The first rerun had the earlier skill version, a longer brief and the review, so only the control and the rule run
compare like with like. They differ by 10 of 81 fixtures, with one run each. One run per version does not separate
the rule's effect from the variation between runs. The rule is not in the follow-up to PR #10422.

Both sessions ran on `claude-opus-5-5` only and opened neither the first rerun's folder nor each other's. The control
wrote one temporary file outside its folder, and the rule run read the output file of one of its own background
commands in a temporary folder. The scoring of these two runs is limited to the fixture battery and the five
findings above; their other findings were not matched to the earlier audit one by one.
