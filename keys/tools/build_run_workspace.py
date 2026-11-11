"""Build the working directory for one audit run of a small case, as RUNNER.md describes it.

Each directory `<output root>/<case>` gets `skill/SKILL.md`, `skill/references/ifbench.md` and
`skill/references/reviewer-prompt.md` from the given `skill/r<N>` folder, and `case/`, a copy of `cases/<case>`
without bytecode folders. The script checks the copy against the case's MANIFEST.sha256 and prints the files that
the manifest does not list. Nothing else is copied: no key, no other case, no file of this repository.

Usage: python -B keys/tools/build_run_workspace.py <skill/r<N> folder> <output root> [<case> ...]
       default cases: the five small cases
"""

import hashlib
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
if len(sys.argv) < 3:
    sys.exit(__doc__)
SUITE = Path(__file__).resolve().parents[2]
SKILL = Path(sys.argv[1])
ROOT = Path(sys.argv[2])
CASES = ["toymath-extract", "toycode-exec", "toyqa-judge", "toyjson-reward", "toyagent-verify"]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


for case in sys.argv[3:] or CASES:
    work = ROOT / case
    if work.exists():
        sys.exit(f"{work} exists; remove it first")
    (work / "skill" / "references").mkdir(parents=True)
    shutil.copyfile(SKILL / "SKILL.md", work / "skill" / "SKILL.md")
    for name in ("ifbench.md", "reviewer-prompt.md"):
        shutil.copyfile(SKILL / "references" / name, work / "skill" / "references" / name)
    shutil.copytree(SUITE / "cases" / case, work / "case", ignore=shutil.ignore_patterns("__pycache__"))
    lines = (work / "case" / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines()
    bad = 0
    for line in lines:
        digest, name = line.split("  ", 1)
        bad += sha(work / "case" / name) != digest
    listed = {line.split("  ", 1)[1] for line in lines} | {"MANIFEST.sha256"}
    extra = [
        p.relative_to(work / "case").as_posix()
        for p in (work / "case").rglob("*")
        if p.is_file() and p.relative_to(work / "case").as_posix() not in listed
    ]
    print(
        f"{work.as_posix()}: {len(lines)} case files, manifest mismatches {bad}, files not in the manifest "
        f"{extra[:4]}, skill sha256 {sha(work / 'skill' / 'SKILL.md')[:12]}"
    )
