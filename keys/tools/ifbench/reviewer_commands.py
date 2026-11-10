"""Second integrity pass for a blinded reviewer of the IFBench rerun.

The first pass (`rerun_integrity.py`) only sees absolute paths, and a reviewer that changes directory can reach files
by relative path. This pass reads every tool call's input in full and reports anything that could unblind the
reviewer or break independence: the frozen key, the other reviewer's files, the workspace beyond its Python, a
parent-directory listing, a search tool, or the operator's notes (`NOTES.md` and any `--private-pattern` regular
expression; for the IFBench rerun the operator also passed the names of the local folders that held the case build
and the operator's other work). It prints tool-call metadata only, never the agent's message text, with short
excerpts around each hit, and writes the full text of every shell command to the dump file.

Usage: python -B keys/tools/ifbench/reviewer_commands.py <A|B> <transcript.jsonl> <dump file>
       [<name of the other reviewer's scratch folder>] [--private-pattern REGEX ...]
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
parser.add_argument("letter", choices=["A", "B"], help="the reviewer whose transcript this is")
parser.add_argument("transcript", type=Path, help="the reviewer's agent transcript (JSON lines)")
parser.add_argument("dump", type=Path, help="file for the full text of the shell commands")
parser.add_argument("other_scratch", nargs="?", help="name of the other reviewer's scratch folder")
parser.add_argument("--private-pattern", action="append", default=[], help="extra regex for operator files (repeatable)")
args = parser.parse_args()

sys.stdout.reconfigure(encoding="utf-8")
LETTER = args.letter
OTHER = "B" if LETTER == "A" else "A"
TRANSCRIPT = args.transcript
DUMP = args.dump

SUSPECT = {
    "frozen key or strata": re.compile(r"key\.jsonl|(?<!review_)cases\.jsonl|strata\.json|MANIFEST", re.I),
    "other reviewer's files": re.compile(
        rf"batches_{OTHER}|review_{OTHER}\.jsonl|prompt_reviewer_{OTHER}|(?<![A-Za-z0-9_])R{OTHER}(?![A-Za-z0-9_])"
    ),
    "workspace beyond its python": re.compile(
        r"(?<![A-Za-z0-9_])W[\\/]+(?!\.venv)|[\\/]audit[\\/]+(scripts|tests|replacement)|[\\/]case[\\/]|ISSUE\.md|CONTRACT|"
        r"instructions_registry|evaluation_lib|ifbench_contract",
        re.I,
    ),
    "orchestrator notes or build folder": re.compile("|".join([r"NOTES\.md", *args.private_pattern]), re.I),
    "parent directory": re.compile(
        r"\.\.[\\/]|(?:^|[\s;&|])(?:ls|dir|tree|find|Get-ChildItem|gci)\b[^\n;|&]*\.\.", re.I
    ),
    "other reviewer's scratch folder": re.compile(
        rf"scratchpad[\/]+{re.escape(args.other_scratch)}(?![A-Za-z0-9_])" if args.other_scratch else r"(?!x)x", re.I
    ),
    "network": re.compile(
        r"https?://|\bcurl\b|\bwget\b|pip3? +install|git +(clone|fetch|pull)|urllib\.request|requests\.", re.I
    ),
}
LISTING = re.compile(
    r"(?:^|[\s;&|(])(ls|dir|tree|find|Get-ChildItem|gci|glob\.glob|os\.listdir|os\.walk|rglob|iterdir)\b"
)
CD = re.compile(r"(?:^|[\s;&|(])cd\s+(\"[^\"]+\"|'[^']+'|\S+)")

tools = Counter()
commands = []
reads = []
writes = []
other_calls = []
for line in TRANSCRIPT.read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    record = json.loads(line)
    message = record.get("message") or {}
    if record.get("type") != "assistant" or not isinstance(message.get("content"), list):
        continue
    for block in message["content"]:
        if block.get("type") != "tool_use":
            continue
        name, tool_args = block["name"], block.get("input") or {}
        tools[name] += 1
        stamp = record.get("timestamp", "")[:19]
        if name in ("Bash", "PowerShell"):
            commands.append((stamp, name, tool_args.get("command", "")))
        elif name == "Read":
            reads.append((stamp, tool_args.get("file_path", "")))
        elif name in ("Write", "Edit"):
            writes.append((stamp, name, tool_args.get("file_path", ""), json.dumps(tool_args, ensure_ascii=False)))
        else:
            other_calls.append((stamp, name, json.dumps(tool_args, ensure_ascii=False)[:200]))

DUMP.parent.mkdir(parents=True, exist_ok=True)
DUMP.write_text(
    "\n".join(f"##### {stamp} {name}\n{command}\n" for stamp, name, command in commands), encoding="utf-8", newline="\n"
)

print(f"=== reviewer {LETTER}: {TRANSCRIPT.name}")
print(f"tool calls: {dict(tools.most_common())}")
print(
    f"shell commands: {len(commands)}, total {sum(len(c) for _, _, c in commands):,} characters "
    f"(full text in {DUMP.name})"
)

folders = Counter()
for _stamp, path in reads:
    folders[str(Path(path).parent).replace("\\", "/")] += 1
print("Read calls by folder:")
for folder, count in folders.most_common():
    print(f"   {count:3d}  {folder}")
print(f"Write/Edit calls: {len(writes)}")
for stamp, name, path, _ in writes:
    print(f"   {stamp} {name} {path}")
print(f"other tools: {len(other_calls)}")
for item in other_calls:
    print("  ", item)

dirs = Counter()
for _, _, command in commands:
    for match in CD.finditer(command):
        dirs[match.group(1).strip("\"'")] += 1
print("cd targets:")
for target, count in dirs.most_common():
    print(f"   {count:3d}  {target}")

hits = 0
for label, pattern in SUSPECT.items():
    found = []
    blobs = (
        [(stamp, name, command) for stamp, name, command in commands]
        + [(stamp, name, blob) for stamp, name, _, blob in writes]
        + [(stamp, "Read", path) for stamp, path in reads]
    )
    for stamp, name, text in blobs:
        for match in pattern.finditer(text):
            start, end = max(0, match.start() - 70), min(len(text), match.end() + 70)
            found.append(f"{stamp} {name}: ...{text[start:end]!r}...")
    print(f"[{label}] hits: {len(found)}")
    for item in found[:12]:
        print("   ", item[:330])
    if len(found) > 12:
        print(f"    ... and {len(found) - 12} more")
    hits += len(found)

listings = []
for stamp, name, command in commands:
    for match in LISTING.finditer(command):
        start, end = max(0, match.start() - 10), min(len(command), match.end() + 110)
        listings.append(f"{stamp} {name}: {command[start:end]!r}")
print(f"[listing or search commands] {len(listings)}")
for item in listings[:25]:
    print("   ", item[:300])
if len(listings) > 25:
    print(f"    ... and {len(listings) - 25} more")
print(f"total suspect hits: {hits}")
