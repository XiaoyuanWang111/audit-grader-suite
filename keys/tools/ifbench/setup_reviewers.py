"""Set up one isolated folder per blinded reviewer for the IFBench rerun.

The rerun root holds the workspace `W/`. For each reviewer X the script makes `RX/`, which mirrors the workspace layout
and holds only what a reviewer may read: its batch set, the full-response files, the helper `show_case.py` and the
case file the helper prints from (`review_cases.jsonl`). Every copied file is checked against the frozen round's
`MANIFEST.sha256`. The reviewer prompt `RX/prompt_reviewer_X.md` is the auditor's, with the workspace's audit folder
replaced by the reviewer's (the Python interpreter path stays). `--prompt-root` is the rerun root as the auditor's
prompts spell it, when that differs from the folder given (for example after a move); by default the two are the same.
Refuses to run when `RA/` or `RB/` exists.

Usage: python -B keys/tools/ifbench/setup_reviewers.py <rerun root> [--prompt-root TEXT]
"""

import argparse
import hashlib
import shutil
import sys
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
parser.add_argument("root", type=Path, help="the rerun root, which holds W/")
parser.add_argument(
    "--prompt-root", help="the rerun root as the prompts spell it (default: the root, with forward slashes)"
)
args = parser.parse_args()

sys.stdout.reconfigure(encoding="utf-8")
BASE = args.root
PROMPT_ROOT = args.prompt_root or BASE.as_posix()
ROUND = BASE / "W" / "audit" / "frozen" / "review_round1"
W_TEXT = f"{PROMPT_ROOT}/W/audit"
PYTHON = f"{PROMPT_ROOT}/W/.venv/Scripts/python.exe"
# Any other mention of the workspace left in a rewritten prompt.
LEFTOVER = f"{Path(PROMPT_ROOT).name}/W/"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


manifest = {}
for line in (ROUND / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
    digest, name = line.split(maxsplit=1)
    manifest[name.strip().lstrip("*")] = digest

for reviewer in "AB":
    root = BASE / f"R{reviewer}"
    assert not root.exists(), f"{root} exists"
    target = root / "audit" / "frozen" / "review_round1"
    (root / "audit" / "frozen" / "reviews").mkdir(parents=True)
    shutil.copytree(ROUND / f"batches_{reviewer}", target / f"batches_{reviewer}")
    shutil.copytree(ROUND / "responses", target / "responses")
    for name in ("review_cases.jsonl", "show_case.py"):
        shutil.copy2(ROUND / name, target / name)
    copied = [p for p in target.rglob("*") if p.is_file()]
    for path in copied:
        key = path.relative_to(target).as_posix()
        assert manifest[key] == sha(path), key
    prompt = (ROUND / f"prompt_reviewer_{reviewer}.md").read_text(encoding="utf-8")
    assert manifest[f"prompt_reviewer_{reviewer}.md"] == sha(ROUND / f"prompt_reviewer_{reviewer}.md")
    new_text = f"{PROMPT_ROOT}/R{reviewer}/audit"
    count = prompt.count(W_TEXT)
    rewritten = prompt.replace(W_TEXT, new_text)
    assert count == 21 and PYTHON in rewritten and LEFTOVER not in rewritten.replace(PYTHON, ""), count
    (root / f"prompt_reviewer_{reviewer}.md").write_text(rewritten, encoding="utf-8", newline="\n")
    print(f"R{reviewer}: {len(copied)} files copied and checked against the manifest; prompt paths replaced: {count}")
    print(
        "   files outside batches and responses:",
        sorted(
            p.relative_to(root).as_posix()
            for p in root.rglob("*")
            if p.is_file() and p.parent.name not in (f"batches_{reviewer}", "responses")
        ),
    )
