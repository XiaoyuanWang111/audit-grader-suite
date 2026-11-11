You are an independent reviewer for the ToyOrders RL reward. Your labels will be compared with automatic graders that you will never see, so they must come only from your own reading of the requirement text.

Your batch file: audit/frozen/round1/batch_B.md
Write your results to: audit/frozen/round1/review_B.jsonl

For every case in the batch, decide which reward the single REQUIREMENT TO JUDGE assigns to the RESPONSE, the way a careful human grader would who reads the requirement literally.

Rules:
1. Judge only that one requirement. Ignore every other requirement in the prompt, and ignore whether the content is correct, useful or well written unless the requirement is about that. Judge against the reference answer as given. Do not use your own knowledge of the facts. If the reference answer looks wrong, set verdict ambiguous and say why.
2. Go by the requirement's own words. If a phrase has more than one reasonable reading and the readings give different verdicts, set verdict "ambiguous", name the readings in the reason, and still give your "lean": the verdict under the reading you find most natural.
3. When the requirement involves counting, positions, ratios, overlap or ordering, compute it with code instead of estimating it. This helper prints the exact response of a case: python -B audit/frozen/round1/show_case.py <case id>. If a case says its response is truncated, read the full text from the file it names.
4. Independence: read only your batch file, the helper above, and the full-response files your batch names. Do not open, list or search any other file or folder, and do not use the web. Do not look for or reimplement grader code; reason from the requirement text.
5. Quoting: never copy more than ten consecutive words of any prompt or response into your messages, printed output or reasons, and never reproduce song lyrics, poems or other published text from memory. Paraphrase or give counts instead. When a script prints text, print only short snippets or counts.
6. Write as you go: after judging each case, append its line to the output file, so that partial work is kept. One JSON object per line, in the batch's case order, with exactly these fields: "case_id", "verdict" (the reward as a number with 4 decimals, such as 0.8750, or "ambiguous"), "lean" (the reward under the reading you find most natural, a number with 4 decimals), "confidence" ("high", "medium" or "low"), "reason" (at most 40 words: the deciding fact or the numbers you computed). Every case must appear exactly once. If the file already has lines from an earlier attempt, keep them and continue after the last case written.
7. When done, reply with one line: the number of cases written and the count of each verdict.
