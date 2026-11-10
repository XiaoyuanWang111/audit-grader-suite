"""Hand the two blinded reviewers' label files to the auditor of the IFBench rerun.

The rerun root holds the workspace `W/` and the reviewers' folders `RA/` and `RB/` (see `setup_reviewers.py`). The
script copies each label file unchanged from `RX/audit/frozen/reviews/` into `W/audit/frozen/reviews/`, checks the
copies by sha256, and writes the README that the audit's ISSUE.md asks for (who or which model ran each reviewer).
The README's times and findings are those of the IFBench rerun. Refuses to write unless the target folder exists and
is empty.

Usage: python -B keys/tools/ifbench/deliver_reviews.py <rerun root>
"""

import hashlib
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
if len(sys.argv) != 2:
    sys.exit(__doc__)
ROOT = Path(sys.argv[1])
TARGET = ROOT / "W" / "audit" / "frozen" / "reviews"
assert TARGET.is_dir() and not any(TARGET.iterdir()), "the reviews folder must exist and be empty"

digests = {}
for letter in "AB":
    source = ROOT / f"R{letter}" / "audit" / "frozen" / "reviews" / f"review_{letter}.jsonl"
    data = source.read_bytes()
    assert data.count(b"\r") == 0 and data.endswith(b"\n") and data.count(b"\n") == 458, source
    (TARGET / source.name).write_bytes(data)
    copied = (TARGET / source.name).read_bytes()
    assert copied == data
    digests[source.name] = hashlib.sha256(copied).hexdigest()
    print(source.name, len(copied), "bytes", digests[source.name])

readme = f"""# Review round 1: who ran the reviewers

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
| `review_A.jsonl` | 458 | {digests["review_A.jsonl"]} |
| `review_B.jsonl` | 458 | {digests["review_B.jsonl"]} |
"""
assert all(len(line) <= 112 for line in readme.splitlines())
(TARGET / "README.md").write_text(readme, encoding="utf-8", newline="\n")
print("README.md", len(readme), "characters")
print(sorted(p.name for p in TARGET.iterdir()))
