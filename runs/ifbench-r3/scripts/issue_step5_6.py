p = "audit/ISSUE.md"
s = open(p, encoding="utf-8").read()


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:80]
    s = s.replace(a, b)


STEP56 = """## Step 5. Panel (stored responses only; no generation)

Every stored response was graded by the grader (strict and loose), the reference (strict and
loose) and the replacement (`audit/replacement/ifbench_contract.py`, proposed readings, plus one
switched decision at a time): `audit/scripts/grade_panel.py` -> `audit/work/panel_verdicts.jsonl`
(78,432 instruction verdicts), summarized by `audit/scripts/analyze_panel.py` ->
`audit/work/analyze_panel.log`, `audit/work/panel_summary.json`. Pins checked before and after
the run (`ifb.verify_pins`).

- Scored coverage: 100% for every grader on the stored panel (no exception on any stored
  response; the csv_quotes crash of step 4 needs an empty field, which no stored response has).
- Pass rates over all 78,432 verdicts: grader strict 27.7%, grader loose 32.4%, reference strict
  27.6%, replacement 25.4%.
- Grader vs reference: 257 verdicts differ (ratio:overlap 227, custom:sentence_alphabet 23,
  words:words_position 5, count:keywords_multiple 1, ratio:sentence_words 1).
- Grader vs replacement: 6,226 verdicts differ (7.9%): grader pass and replacement fail 3,992,
  grader fail and replacement pass 2,234. A single switched decision reproduces the grader's
  verdict in 2,718 of them (largest: D-vacuous B 440, D-section B 360, D-palindrome B or C 317,
  D-subbullet B 245, D-sentence B 230, D-conj B 221, D-overlap D 205, D-paren C 201, D-csv B or C
  146 each, D-word B 87, D-punct-set B 76). Largest per-check differences: format:sub-bullets
  1,216, format:thesis 507, count:conjunctions 416, format:quote_unquote 332, words:palindrome
  326, format:no_bullets_bullets 358, words:start_verb 309, format:quotes 306, count:punctuation
  267, ratio:overlap 205, format:parentheses 202, count:words_japanese 169, count:pronouns 170.
- Extraction failures (G1): 136 thinking-on responses never close `<think>`; their stored
  `response` is the reasoning itself. The grader passes 45 of their 157 instruction verdicts,
  all of which the contract fails (F-extract-unclosed).
- Truncated responses (finish_reason length): 4,588 instruction verdicts; the grader passes
  1,013 of them, the replacement 793.
- Loose transform: 3,666 verdicts (4.7%) pass only under loose grading; the contract fails the
  full response in 2,762 of them (F-loose-deletes-constrained). format:sub-bullets passes 100% of
  2,736 verdicts under loose grading, because deleting every `*` leaves a response with no
  bullets, which the grader passes (F-subbullets-none). Winning variants: no asterisks 1,798, no
  first line 956, no last line 379, no first and last line 479, combinations 54.
- Score change per configuration (prompt-level strict accuracy, mean over runs; replacement minus
  grader, range over runs in brackets; rerun = |greedy - greedy_repeat| under the grader):
  Qwen2.5-14B -4.9 [-7.7, -2.7] rerun 1.0; Qwen2.5-32B -2.3 [-4.0, -0.3] rerun 1.3; Qwen2.5-7B
  -3.4 [-7.3, -1.0] rerun 0.3; Qwen3-14B -1.7 [-3.0, +0.3] rerun 0.3; Qwen3-14B thinking +1.0
  [+0.7, +1.3] rerun 1.0; Qwen3-32B +0.4 [-1.7, +2.3] rerun 0.7; Qwen3-8B -1.5 [-3.3, +0.3] rerun 0;
  Qwen3-8B thinking -1.6 [-2.0, -0.7] rerun 0; Tulu-3-8B +0.6 [-1.7, +2.3] rerun 0.3;
  OLMo-2-32B -2.9 [-4.3, -1.0] rerun 0; OLMo-2-13B -3.9 [-6.0, -2.0] rerun 0; OLMo-2-7B -3.1
  [-6.0, -1.7] rerun 0.7; marin-8b -0.5 [-3.3, +1.7] rerun 1.0; phi-4 +1.2 [-1.3, +3.0] rerun 0;
  Mistral-7B -1.8 [-3.7, -0.3] rerun 0.3; Mistral-Small-24B +1.6 [-0.3, +3.0] rerun 0.3 (points).
  The ranking of the 16 configurations changes (for example Qwen3-14B thinking moves from second
  to first and Qwen2.5-14B from third to fifth). These differences are measured against the
  replacement, whose own error rate step 6 estimates.
- Replacement changes after the panel run, all from non-held-out examples
  (`audit/scripts/inspect_disagreements.py` reads only non-held-out runs) or from crashes:
  count:pronouns reading C crashed (fixed, rows recomputed); words:start_verb (third-person verbs,
  "Here's" removed from the verb list), format:thesis (HTML wrappers such as `<p>` before the
  italics), format:quote_unquote (guillemets as quotation marks), format:list (numbers are not
  bullet symbols in the contract). Rows of these checks were recomputed with
  `audit/scripts/regrade_replacement_rows.py`; the replacement still passes all 277 fixtures.

## Step 6. Blinded review (round 1)

Recorded 2026-11-09 23:48 UTC, before any review started.

Result that would change the step 7 recommendation. Planned recommendation if the review
confirms steps 3 to 5: fix the grader. It changes to:
- admit, if the grader's weighted error rate against the consensus is at most 2% with an upper
  95% bound of at most 3%, and no finding affects more than 1% of verdicts;
- replace the benchmark, if Cohen's kappa between the reviewers' leans is below 0.40 overall, or
  more than 25% of the reviewed cases get an `ambiguous` verdict from either reviewer (the texts
  then do not support reliable grading by any implementation).
The replacement is proposed as the fix only if it passes every fixture (it does, 277 of 277),
scored coverage is complete (it is), and its weighted error rate is lower than the grader's with
a paired 95% bootstrap interval that excludes zero; otherwise the fix is the per-finding repair
list, with the decision entries left to the maintainers.

6.1 Sample (`audit/scripts/draw_review_sample.py`, seed 61109). Population: the held-out run of
every configuration, all instruction instances except the 52 extraction failures (counted under
G1): 5,452 verdicts. Strata and sample sizes:

| Stratum | Definition | Population | Sample |
|---|---|---|---|
| S1a | grader pass, replacement fail | 250 | 170 |
| S1b | grader fail, replacement pass | 180 | 125 |
| S2 | grader = replacement, reference differs | 3 | 3 |
| S3 | grader = replacement = reference | 5,019 | 160 |

6.2 Frozen before any review (files under `audit/frozen/review_round1/`):

| File | sha256 |
|---|---|
| `cases.jsonl` (the case list: id, stratum, check, prompt key, instruction index, response sha256) | f360e3596f16f22c7c53fb117d6096b9784c4849f8406f4ef3a6292c8ad24f4d |
| `key.jsonl` (source configuration and run, every grader verdict; not for reviewers) | f39322475638d564e86a7b2bb63cb6bfccd621e59556c033a93168395634675f |
| `review_cases.jsonl` (what the helper prints from) | 491371ce7905dae83cd492b5dfaaea96497f7b3074eba41ceabdc16da61e6148 |
| `strata.json` | 87f5ac13cd36f426916c6db4c4f543b07584dd771cd11719658562afbee274d0 |
| `show_case.py` (helper) | bd1c6d68d3863110503d6ae732bc26f0da56105f7c857a5f4012ff178c89b80c |
| `prompt_reviewer_A.md` | 8859795100204309c37bb1e5b25efb145524ecc71cac9b0b9373a09c6927a348 |
| `prompt_reviewer_B.md` | feb112b88ac30114f8876c6fd22de6af1e45fd457366a58c6a54ae37ea9e2e74 |
| `MANIFEST.sha256` (every file in the folder: batches, responses, the above) | 5ec4828648954952a495b4b2eeadd015c70627c509f0539d9b44662201a30f3c |

6.3 Rendering. 458 cases, 19 batch files per reviewer (25 cases each, the last 8), in
`audit/frozen/review_round1/batches_A/` and `batches_B/`; the two reviewers get the cases in
different random orders (seeds 61110 and 61111). Each case shows an opaque id (`R1-xxxxx`), the
check name, the requirement text as the prompt renders it (the whole prompt for the 11 custom
checks), the prompt, and the response between BEGIN and END marker lines; no source model,
grader verdict or other reviewer's label. 20 responses longer than 6,000 characters are cut in
the batch and point to `audit/frozen/review_round1/responses/<id>.txt`. Helper:
`W/.venv/Scripts/python.exe W/audit/frozen/review_round1/show_case.py <id>` (`--repr` shows
whitespace, `--json` the whole case). One sampled response introduces itself as Qwen; that is
response text and stays.

How a reviewer returns labels: give reviewer A the text of
`audit/frozen/review_round1/prompt_reviewer_A.md` (the reviewer prompt of
`skill/references/reviewer-prompt.md` with its placeholders filled) and reviewer B
`prompt_reviewer_B.md`, in separate runs. Each writes one JSON object per line, in its batches'
case order, to its own file: reviewer A `audit/frozen/reviews/review_A.jsonl`, reviewer B
`audit/frozen/reviews/review_B.jsonl`, with exactly the fields `case_id`, `verdict` (pass, fail,
ambiguous), `lean` (pass, fail), `confidence` (high, medium, low), `reason` (at most 40 words).
Every case must appear exactly once. Record who or which model ran each reviewer next to the
file (for example in `audit/frozen/reviews/README.md`), since two runs of one model can share
blind spots.

"""
rep("## Findings\n", STEP56 + "## Findings\n")
FIND = "| F-extract-unclosed | response extraction | A thinking-on completion that never closes `<think>` is stored (and graded) as its whole reasoning; the grader passes 45 of those 157 verdicts. | 136 stored responses (`audit/work/panel_scan.csv`) | n/a (pipeline) |\n"
anchor = "| F-loose-deletes-constrained | loose transform (all checks) | Loose grading passes responses by deleting the first or last line or every `*`, text the instructions constrain. | test_properties.py::loose-* | same |\n"
rep(anchor, anchor + FIND)
rep("| 5. Panel | not started (held-out runs chosen) | `audit/frozen/heldout_runs.tsv` |",
    "| 5. Panel | done 2026-11-09 23:45 UTC (stored responses only) | this file, \"Step 5\"; `audit/work/panel_verdicts.jsonl` |")
rep("| 6. Blinded review | not started | `audit/frozen/` |",
    "| 6. Blinded review | 6.1-6.3 done 2026-11-09 23:48 UTC (458 cases frozen and rendered); waiting for reviewer labels (6.4); 6.5 not started | this file, \"Step 6\"; `audit/frozen/review_round1/` |")
rep("Next: step 5 analysis of `audit/work/panel_verdicts.jsonl` (`audit/scripts/analyze_panel.py`), then\n"
    "step 6.1-6.3 (`audit/scripts/draw_review_sample.py`).",
    "Next: two reviewers label the 458 cases (prompts in `audit/frozen/review_round1/prompt_reviewer_A.md`\n"
    "and `_B.md`, outputs `audit/frozen/reviews/review_A.jsonl` and `review_B.jsonl`). Then step 6.5\n"
    "(join labels with `audit/frozen/review_round1/key.jsonl`: consensus, per-stratum error rates\n"
    "weighted by `strata.json`, bootstrap within strata, paired difference, kappa, disputed cases) and\n"
    "step 7 (`audit/AUDIT.md`).")
rep("| `audit/frozen/CONTRACT_v1.md` | b88caf4afb44ecb4f46c08890ab7006084e7da2af57d624816bb24138cee2f95 | 2026-11-09 22:16 UTC |",
    "| `audit/frozen/CONTRACT_v1.md` | b88caf4afb44ecb4f46c08890ab7006084e7da2af57d624816bb24138cee2f95 | 2026-11-09 22:16 UTC |\n"
    "| `audit/frozen/CONTRACT_v2.md` | 5175ec90cbced57cadf39c59e9976731a73ef803e231b06f56df5adc0b0bb813 | 2026-11-09 22:43 UTC |\n"
    "| `audit/frozen/review_round1/cases.jsonl` (review case list) | f360e3596f16f22c7c53fb117d6096b9784c4849f8406f4ef3a6292c8ad24f4d | 2026-11-09 23:47 UTC |\n"
    "| `audit/frozen/review_round1/MANIFEST.sha256` (whole review folder) | 5ec4828648954952a495b4b2eeadd015c70627c509f0539d9b44662201a30f3c | 2026-11-09 23:48 UTC |")
s = s.replace("- 2026-11-09 22:47 UTC: step 3 done, 277 fixtures; findings table added.\n",
              "- 2026-11-09 22:47 UTC: step 3 done, 277 fixtures; findings table added.\n"
              "- 2026-11-09 23:30 UTC: step 4 done (reference tests against the replacement, fuzzing, content-free, metamorphic, loose).\n"
              "- 2026-11-09 23:45 UTC: step 5 panel graded and analyzed.\n"
              "- 2026-11-09 23:48 UTC: step 6.1-6.3: review sample drawn, frozen and rendered; stopped for the reviewers.\n")
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
