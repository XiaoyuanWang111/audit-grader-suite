"""Build two sealed workspaces for a controlled blind rerun of the audit-grader skill on IFBench.

Arm A (control): SKILL.md of the follow-up branch (commit b698ee759) and reviewer-prompt.md.
Arm B (treatment): the same SKILL.md with one rule added to step 4 (carry an input form that shows a wrong verdict in
one check to the other checks).

Each workspace gets its own copy of the case folder and of the Python environment of the source workspace (the first
rerun's), a TASK.md with the workspace's own path, and a MANIFEST.sha256 whose TASK.md line is recomputed. Nothing
from the source workspace's audit folder is copied. Prints what it did and the checks: TASK.md paths replaced,
manifest mismatches, text files outside the environment that still name the source workspace's folder, the skill's
sha256, and the environment's package versions. For the IFBench runs the operator then removed the remaining
pointers to the source workspace from each copied environment by hand (its activate scripts were rewritten, and its
launcher executables and one bytecode file deleted).

Usage: python keys/tools/ifbench/build_ab.py <source workspace> <output root> <marin clone or worktree>
"""

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
if len(sys.argv) != 4:
    sys.exit(__doc__)
SRC = Path(sys.argv[1])
ROOT = Path(sys.argv[2])
MARIN = Path(sys.argv[3])
BASE_COMMIT = "b698ee759"
OLD = SRC.as_posix()
OLD_BACK = OLD.replace("/", "\\")

RULE_OLD = (
    "- Add property and metamorphic tests. A verdict must stay the same under edits\n"
    "  that the contract ignores, and a passing response must fail after an edit\n"
    "  that the contract forbids.\n"
)
RULE_NEW = (
    "- Add property and metamorphic tests. A verdict must stay the same under edits\n"
    "  that the contract ignores, and a passing response must fail after an edit\n"
    "  that the contract forbids. When an input form shows a wrong verdict in one\n"
    "  check, such as a list label before a line, markup around a word, a\n"
    "  typographic quotation mark, or punctuation after a word, apply it to passing\n"
    "  responses of every other check, and file each wrong verdict that it causes.\n"
)


def git_show(path: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(MARIN), "show", f"{BASE_COMMIT}:{path}"], capture_output=True, check=True
    ).stdout


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    skill = git_show(".agents/skills/audit-grader/SKILL.md").decode("utf-8")
    prompt = git_show(".agents/skills/audit-grader/references/reviewer-prompt.md")
    assert skill.count(RULE_OLD) == 1
    variants = {"A": skill, "B": skill.replace(RULE_OLD, RULE_NEW)}
    for arm, text in variants.items():
        work = ROOT / arm
        if work.exists():
            sys.exit(f"{work} exists; remove it first")
        (work / "skill" / "references").mkdir(parents=True)
        (work / "skill" / "SKILL.md").write_text(text, encoding="utf-8", newline="\n")
        (work / "skill" / "references" / "reviewer-prompt.md").write_bytes(prompt)
        shutil.copytree(SRC / "case", work / "case")
        shutil.copytree(SRC / ".venv", work / ".venv")
        new = str(work).replace("\\", "/")
        task = (work / "case" / "TASK.md").read_text(encoding="utf-8")
        count = task.count(OLD) + task.count(OLD_BACK)
        task = task.replace(OLD, new).replace(OLD_BACK, new.replace("/", "\\"))
        (work / "case" / "TASK.md").write_text(task, encoding="utf-8", newline="\n")
        manifest = (work / "case" / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines()
        fixed, bad = [], 0
        for line in manifest:
            digest, name = line.split("  ", 1)
            target = work / "case" / name
            actual = sha(target)
            if name == "TASK.md":
                fixed.append(f"{actual}  {name}")
            else:
                bad += actual != digest
                fixed.append(line)
        (work / "case" / "MANIFEST.sha256").write_text("\n".join(fixed) + "\n", encoding="utf-8", newline="\n")
        leftovers = [
            str(p)
            for p in work.rglob("*")
            if p.is_file()
            and p.suffix in {".md", ".txt", ".cfg"}
            and ".venv" not in p.parts
            and SRC.parent.name in p.read_text(encoding="utf-8", errors="ignore")
        ]
        probe = subprocess.run(
            [
                str(work / ".venv" / "Scripts" / "python.exe"),
                "-B",
                "-c",
                "import sys, nltk, emoji, syllapy, pytest; "
                "print(sys.prefix, nltk.__version__, emoji.__version__, pytest.__version__)",
            ],
            capture_output=True,
            text=True,
        )
        print(
            f"arm {arm}: {work}; TASK.md paths replaced {count}; manifest lines {len(manifest)}, mismatches {bad}; "
            f"files still naming the first workspace: {leftovers}; "
            f"skill sha256 {sha(work / 'skill' / 'SKILL.md')[:12]}; "
            f"python: {probe.stdout.strip() or probe.stderr.strip()[:300]}"
        )
    print("rule present in B only:", RULE_NEW in variants["B"], RULE_NEW in variants["A"])


if __name__ == "__main__":
    main()
