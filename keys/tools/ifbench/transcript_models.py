"""Per model, the time range and the tool calls of an agent transcript, and the files each model wrote.

A transcript is a JSON-lines file in which an assistant record carries `message.model` and `message.content` blocks
of type `tool_use`. The script prints tool metadata only (tool name, file path, time); never message text. With
--hits PATTERN, it also prints a short excerpt around each match of PATTERN inside Write and Edit inputs.

Usage: python -B keys/tools/ifbench/transcript_models.py <transcript.jsonl> [--hits REGEX]
"""

import collections
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
path = Path(sys.argv[1])
pattern = re.compile(sys.argv[3], re.IGNORECASE) if len(sys.argv) > 3 and sys.argv[2] == "--hits" else None

spans = collections.OrderedDict()
segments = []
writes = collections.defaultdict(list)
tools = collections.defaultdict(collections.Counter)
for line in path.read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    record = json.loads(line)
    if record.get("type") != "assistant":
        continue
    message = record.get("message") or {}
    model = message.get("model", "?")
    stamp = record.get("timestamp", "")[:19]
    first, last, count = spans.get(model, (stamp, stamp, 0))
    spans[model] = (min(first, stamp), max(last, stamp), count + 1)
    if not segments or segments[-1][0] != model:
        segments.append([model, stamp, stamp, 0])
    segments[-1][2] = stamp
    segments[-1][3] += 1
    for block in message.get("content") or []:
        if block.get("type") != "tool_use":
            continue
        tools[model][block["name"]] += 1
        data = block.get("input") or {}
        if block["name"] in ("Write", "Edit"):
            writes[model].append((stamp, block["name"], data.get("file_path", "")))
            if pattern:
                text = (data.get("content") or "") + "\n" + (data.get("new_string") or "")
                for match in pattern.finditer(text):
                    lo, hi = max(0, match.start() - 110), min(len(text), match.end() + 110)
                    print(f"HIT {stamp} {block['name']} {data.get('file_path', '')}: ...{text[lo:hi]!a}...")

print(path.name)
for model, (first, last, count) in spans.items():
    print(f"  {model}: {count} assistant records, {first} to {last}; tool calls {dict(tools[model])}")
print("  segments in order:")
for model, first, last, count in segments:
    print(f"    {first} to {last}  {model}  {count} records")
for model, items in writes.items():
    print(f"  files written or edited by {model}:")
    for stamp, name, file_path in items:
        print(f"    {stamp} {name} {file_path}")
