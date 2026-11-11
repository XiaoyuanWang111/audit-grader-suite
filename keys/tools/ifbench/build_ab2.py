"""Build sealed workspaces for the later controlled runs of the audit-grader skill on IFBench.

Arms: A2 and A3 (control: SKILL.md of the follow-up branch at b698ee759), C1 and C2 (the same file with a list of
edits added to step 4's bullet on property tests: skill/r4-edits), D1 and D2 (the list with two edits spelled out and
one more sentence: skill/r4-edits2). Each workspace gets its own copy of the case and of the Python environment of the
source workspace, a TASK.md with its own path, a MANIFEST.sha256 whose TASK.md line is recomputed, and an environment
with every pointer to the source workspace removed (activate scripts rewritten, launcher executables other than
python removed, one bytecode file deleted). Nothing from any earlier run's audit folder is copied. Prints, per arm:
manifest mismatches, the files that still name the source workspace, the skill's sha256, and the environment's
prefix.

Usage: python keys/tools/ifbench/build_ab2.py <source workspace> <output root> <marin clone or worktree> <arm> [...]
"""

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
if len(sys.argv) < 5:
    sys.exit(__doc__)
SRC = Path(sys.argv[1])
ROOT = Path(sys.argv[2])
MARIN = Path(sys.argv[3])
BASE_COMMIT = "b698ee759"
OLD = str(SRC).replace(chr(92), "/")

RULE_OLD = (
    "- Add property and metamorphic tests. A verdict must stay the same under edits\n"
    "  that the contract ignores, and a passing response must fail after an edit\n"
    "  that the contract forbids.\n"
)
RULE_V2 = (
    "- Add property and metamorphic tests. A verdict must stay the same under edits\n"
    "  that the contract ignores, and a passing response must fail after an edit\n"
    "  that the contract forbids. Apply each ignored edit to a passing response of\n"
    "  every check whose contract ignores it, not only to the check where it first\n"
    "  came up. For a grader of text responses, try at least these edits: a list\n"
    "  label before a line (`1.`, `-`), markup around a word (bold, italics, an HTML\n"
    "  tag), typographic quotation marks and apostrophes in place of straight ones,\n"
    "  punctuation directly after a word, a blank line between lines, and a trailing\n"
    "  newline. File each wrong verdict that an edit causes.\n"
)
RULE_V3 = (
    "- Add property and metamorphic tests. A verdict must stay the same under edits\n"
    "  that the contract ignores, and a passing response must fail after an edit\n"
    "  that the contract forbids. Apply each ignored edit to a passing response of\n"
    "  every check whose contract ignores it, not only to the check where it first\n"
    "  came up. For a grader of text responses, try at least these edits: a\n"
    "  numbered label (`1.`, `2.`) and a bullet (`-`) before each line, markup\n"
    "  around a word (bold, italics, an HTML tag), typographic quotation marks\n"
    "  around a word and a typographic apostrophe inside one, punctuation directly\n"
    "  after a word, a blank line between lines, and a trailing newline. Put the\n"
    "  word edits on a word that the check reads, such as the first or last word\n"
    "  of a sentence. File each wrong verdict that an edit causes.\n"
)
SKILLS = {"A2": None, "A3": None, "C1": RULE_V2, "C2": RULE_V2, "D1": RULE_V3, "D2": RULE_V3}


def git_show(path: str) -> bytes:
    command = ["git", "-C", str(MARIN), "show", f"{BASE_COMMIT}:{path}"]
    return subprocess.run(command, capture_output=True, check=True).stdout


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def spellings(path: str) -> list[bytes]:
    forward = path
    back = path.replace("/", chr(92))
    double = path.replace("/", chr(92) * 2)
    msys = "/" + path[0].lower() + path[2:]
    lower = path[0].lower() + path[1:]
    return [s.encode() for s in (forward, back, double, msys, lower)]


def build(arm: str) -> None:
    skill = git_show(".agents/skills/audit-grader/SKILL.md").decode("utf-8")
    assert skill.count(RULE_OLD) == 1
    if SKILLS[arm] is not None:
        skill = skill.replace(RULE_OLD, SKILLS[arm])
    work = ROOT / arm
    if work.exists():
        sys.exit(f"{work} exists; remove it first")
    (work / "skill" / "references").mkdir(parents=True)
    (work / "skill" / "SKILL.md").write_text(skill, encoding="utf-8", newline="\n")
    prompt = git_show(".agents/skills/audit-grader/references/reviewer-prompt.md")
    (work / "skill" / "references" / "reviewer-prompt.md").write_bytes(prompt)
    shutil.copytree(SRC / "case", work / "case")
    shutil.copytree(SRC / ".venv", work / ".venv")
    new = str(work).replace(chr(92), "/")
    pairs = list(zip(spellings(OLD), spellings(new), strict=True))

    task = (work / "case" / "TASK.md").read_bytes()
    for old, repl in pairs:
        task = task.replace(old, repl)
    (work / "case" / "TASK.md").write_bytes(task)
    lines, bad = [], 0
    for line in (work / "case" / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        actual = sha(work / "case" / name)
        if name == "TASK.md":
            lines.append(f"{actual}  {name}")
        else:
            bad += actual != digest
            lines.append(line)
    (work / "case" / "MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    scripts = work / ".venv" / "Scripts"
    for path in scripts.iterdir():
        if path.suffix == ".exe" and path.name not in ("python.exe", "pythonw.exe"):
            path.unlink()
            continue
        if path.suffix == ".exe":
            continue
        data = path.read_bytes()
        for old, repl in pairs:
            data = data.replace(old, repl)
        path.write_bytes(data)
    stale = work / ".venv" / "Lib" / "site-packages" / "__pycache__" / "_virtualenv.cpython-312.pyc"
    if stale.exists():
        stale.unlink()

    needle = SRC.parent.name.encode()
    leftovers = [str(p) for p in work.rglob("*") if p.is_file() and needle in p.read_bytes()]
    probe = subprocess.run(
        [str(scripts / "python.exe"), "-B", "-c", "import sys, nltk, emoji, syllapy, pytest; print(sys.prefix)"],
        capture_output=True,
        text=True,
    )
    print(
        f"arm {arm}: {new}; manifest mismatches {bad}; files that name the source workspace: {len(leftovers)} "
        f"{leftovers[:3]}; skill sha256 {sha(work / 'skill' / 'SKILL.md')[:12]}; "
        f"python prefix: {probe.stdout.strip() or probe.stderr.strip()[:200]}"
    )


if __name__ == "__main__":
    for name in sys.argv[4:]:
        build(name)
