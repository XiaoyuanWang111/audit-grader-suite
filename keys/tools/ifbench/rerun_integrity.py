"""Integrity check for a blind run: list every tool call in an agent transcript that touches a path outside the sealed
workspace, uses a web or agent tool, runs a command that can reach the network, or names key material.

A transcript is a JSON-lines file in which an assistant record carries `message.content` blocks of type `tool_use`
(`name`, `input`). The script prints tool-call metadata only (tool name, paths, a short command excerpt); it never
prints the agent's reasoning or message text. Key material is any match of the built-in pattern (the earlier IFBench
audit's repository and data files, the skill references that the run withheld, the suite itself, agent settings,
operator notes) or of a `--key-pattern` regular expression. For the IFBench rerun the operator also passed the names
of its local work folders, which held the earlier audit's data, the skill's worktree and the case build.

Usage: python -B keys/tools/ifbench/rerun_integrity.py <workspace root> <transcript.jsonl> [...]
       [--key-pattern REGEX ...]
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
parser.add_argument("root", help="the sealed workspace")
parser.add_argument("transcripts", nargs="+", help="agent transcripts (JSON lines)")
parser.add_argument("--key-pattern", action="append", default=[], help="extra key-material regex (repeatable)")
args = parser.parse_args()

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(args.root).resolve()
ROOT_KEY = str(ROOT).replace("\\", "/").lower()
# Git Bash spells D:/x as /d/x.
ROOT_MSYS = "/" + ROOT_KEY[0] + ROOT_KEY[2:]

PATH_TOOLS = {
    "Read": ["file_path"],
    "Write": ["file_path"],
    "Edit": ["file_path"],
    "NotebookEdit": ["notebook_path"],
    "Glob": ["path"],
    "Grep": ["path"],
}
SHELL_TOOLS = {"Bash", "PowerShell"}
QUIET_TOOLS = set(PATH_TOOLS) | SHELL_TOOLS | {"TodoWrite", "TaskOutput", "BashOutput", "KillShell", "TaskStop"}
NETWORK = re.compile(
    r"pip3? +(install|download)|uv +(pip|add|sync)|git +(clone|fetch|pull|ls-remote|push)|\bcurl\b|\bwget\b|https?://|"
    r"Invoke-WebRequest|\biwr\b|Invoke-RestMethod|\birm\b|huggingface|hf_hub|snapshot_download|load_dataset|requests\.(get|post)|"
    r"urllib\.request|urlopen|nltk\.download|\bssh\b|\bscp\b|\bgh +",
    re.IGNORECASE,
)
# The earlier audit, the skill's withheld references, the suite and the operator's notes: any hit here is a breach.
KEY_MATERIAL = re.compile(
    "|".join(
        [
            r"ifbench_audit|ifbench-audit|ifbench\.md|validation\.md|audit-grader-suite|[\\/]\.claude[\\/]|NOTES\.md|"
            r"findings\.jsonl|decisions\.jsonl",
            *args.key_pattern,
        ]
    ),
    re.IGNORECASE,
)
WINDOWS_PATH = re.compile(r"(?<![A-Za-z0-9])([A-Za-z]:[\\/][^\s\"'`;|&<>()*?,=]*)")
MSYS_PATH = re.compile(r"(?<![\w.$:/\\-])(/(?:[a-z]|tmp|home|usr|etc|mnt|var|opt)/[^\s\"'`;|&<>()*?,=]*)")
HOME = re.compile(
    r"(~[\\/]|\$HOME|\$env:USERPROFILE|\$env:TEMP|\$env:TMP|%TEMP%|%USERPROFILE%|\$TMPDIR|\bmktemp\b|tempfile\.)"
)


def inside(path: str) -> bool:
    key = path.replace("\\", "/").lower().rstrip("/")
    return key == ROOT_KEY or key.startswith(ROOT_KEY + "/") or key == ROOT_MSYS or key.startswith(ROOT_MSYS + "/")


def check_shell(command: str) -> list[str]:
    notes = []
    outside = sorted({p for p in WINDOWS_PATH.findall(command) + MSYS_PATH.findall(command) if not inside(p)})
    if outside:
        notes.append("outside paths: " + ", ".join(p[:110] for p in outside[:6]))
    if NETWORK.search(command):
        notes.append("network pattern: " + ", ".join(sorted({m.group(0)[:30] for m in NETWORK.finditer(command)})[:6]))
    if HOME.search(command):
        notes.append("home or temp reference: " + ", ".join(sorted({m.group(0) for m in HOME.finditer(command)})))
    return notes


for transcript in args.transcripts:
    tools = Counter()
    models = Counter()
    flagged = []
    breaches = []
    stamps = []
    relative = 0
    for line in Path(transcript).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("timestamp"):
            stamps.append(record["timestamp"])
        message = record.get("message") or {}
        if record.get("type") != "assistant" or not isinstance(message.get("content"), list):
            continue
        if message.get("model"):
            models[message["model"]] += 1
        for block in message["content"]:
            if block.get("type") != "tool_use":
                continue
            name, tool_args = block["name"], block.get("input") or {}
            tools[name] += 1
            stamp = record.get("timestamp", "")[:19]
            blob = json.dumps(tool_args, ensure_ascii=False)
            if KEY_MATERIAL.search(blob):
                breaches.append(f"{stamp} {name}: {sorted({m.group(0) for m in KEY_MATERIAL.finditer(blob)})}")
            if name in PATH_TOOLS:
                for field in PATH_TOOLS[name]:
                    value = tool_args.get(field)
                    if value is None:
                        if name in ("Glob", "Grep"):
                            flagged.append(f"{stamp} {name}: no path given (searches the session's working directory)")
                        continue
                    if not re.match(r"^([A-Za-z]:[\\/]|/)", value):
                        relative += 1
                        flagged.append(f"{stamp} {name}: relative path {value[:120]}")
                    elif not inside(value):
                        flagged.append(f"{stamp} {name}: outside path {value[:160]}")
            elif name in SHELL_TOOLS:
                for note in check_shell(tool_args.get("command", "")):
                    flagged.append(f"{stamp} {name}: {note} || {tool_args.get('command', '')[:150]!r}")
            elif name not in QUIET_TOOLS:
                flagged.append(f"{stamp} {name}: other tool, input keys {sorted(tool_args)}")
    print(f"\n=== {Path(transcript).name}")
    print(f"records from {min(stamps)[:19] if stamps else '?'} to {max(stamps)[:19] if stamps else '?'}")
    print(f"models: {dict(models)}")
    print(f"tool calls: {sum(tools.values())} {dict(tools.most_common())}")
    print(f"key-material hits: {len(breaches)}")
    for item in breaches:
        print("   BREACH", item)
    print(f"flagged calls: {len(flagged)} (relative paths: {relative})")
    for item in flagged:
        print("  ", item[:330])
