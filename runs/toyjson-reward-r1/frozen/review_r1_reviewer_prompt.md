# Reviewer prompt, round 1 (not run)

Adapted from `skill/references/reviewer-prompt.md` for a reward with numeric labels and a
reference answer: the verdict and lean are reward values, rule 1 carries the reference-answer
addition, and each label adds the per-check values so that a disagreement can be located.
No example from the audit's decision table is included. Give each reviewer run this text with
`<X>` replaced by its batch letter, `A` or `B`.

```text
You are an independent reviewer for the ToyOrders reward. Your labels will be compared with automatic graders that you will never see, so they must come only from your own reading of the requirement text.

Your batch file: audit/frozen/review_r1_batch_<X>.md
Write your results to: audit/frozen/review_r1_labels_<X>.jsonl

For every case in the batch, compute the reward that the REQUIREMENT TO JUDGE gives the RESPONSE against the REFERENCE, the way a careful human grader would who reads the requirement literally.

Rules:
1. Judge only that requirement, and ignore whether the content is useful or well written. Judge against the reference answer as given. Do not use your own knowledge of the facts. If the reference answer looks wrong, set verdict ambiguous and say why.
2. Go by the requirement's own words. If a phrase has more than one reasonable reading and the readings give different rewards, set verdict "ambiguous", name the readings in the reason, and still give your "lean": the reward under the reading you find most natural.
3. When the requirement involves counting, positions, ratios, overlap or ordering, compute it with code instead of estimating it. This helper prints the exact response of a case: python -I audit/frozen/review_r1_show.py <case id>.
4. Independence: read only your batch file and the helper's output. Do not open, list or search any other file or folder, and do not use the web. Do not look for or reimplement grader code; reason from the requirement text.
5. Quoting: never copy more than ten consecutive words of any prompt or response into your messages, printed output or reasons, and never reproduce song lyrics, poems or other published text from memory. Paraphrase or give counts instead. When a script prints text, print only short snippets or counts.
6. Write as you go: after judging each case, append its line to the output file, so that partial work is kept. One JSON object per line, in the batch's case order, with exactly these fields: "case_id"; "verdict" (the reward as a number with four decimals, or "ambiguous"); "lean" (the reward, a number with four decimals); "checks" (an object with "answer": "pass" or "fail", and when the answer passes, "customer", "date" and "total" as 0 or 1, "items" as a fraction such as "2/3", and "extra_keys" as a count); "confidence" ("high", "medium" or "low"); "reason" (at most 40 words: the deciding fact or the numbers you computed). Every case must appear exactly once. If the file already has lines from an earlier attempt, keep them and continue after the last case written.
7. When done, reply with one line: the number of cases written and the count of each verdict.
```
