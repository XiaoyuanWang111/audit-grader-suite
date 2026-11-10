# Review round 1: who ran the reviewers

Both reviewers are runs of one model, Claude Opus 5.5 (`claude-opus-5-5`). They were started as two separate
agents on 2026-11-09 at 23:55 UTC, each with only its prompt as context. Reviewer A returned its 458 labels at
00:14 UTC on 2026-11-10 and reviewer B at 00:20 UTC. No person labeled any case.

Each run received the text of its prompt in `../review_round1/` (`prompt_reviewer_A.md` or
`prompt_reviewer_B.md`), with the paths changed to a folder of its own outside the workspace. That folder held
copies of the run's batch files, the full-response files, `show_case.py` and `review_cases.jsonl`, and nothing
else from the audit. The operator of this run copied each label file here unchanged.

After the runs, a script read every tool call of both runs in full. Neither run opened `cases.jsonl`,
`key.jsonl`, `strata.json`, the other reviewer's batches or labels, the grader, the reference or the
replacement, and neither used the network. Each ran `show_case.py` with the workspace's Python and kept its
working scripts in a temporary folder of its own.

| File | Lines | sha256 |
|---|---|---|
| `review_A.jsonl` | 458 | 5eec6b187962afa8847f9341f55f8bc7ca627c6ee1bdeaa0f1f31e752e2321fc |
| `review_B.jsonl` | 458 | d809a126270b878b5dd43c07989d9a81b10600ef24b25a702006bf54ea3cb0a3 |
