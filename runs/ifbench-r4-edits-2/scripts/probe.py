"""Grade one response with the grader (strict, loose), the reference (strict, loose) and the replacement.

Usage (Git Bash, from W):
  NLTK_DATA=$PWD/case/deps/nltk_data .venv/Scripts/python.exe audit/scripts/probe.py \
      <instruction_id> '<kwargs as JSON object>' '<response as JSON string>'
The response is a JSON string literal, so \\n, \\t and \\uXXXX escapes give the exact characters.
"""
import json
import sys

sys.path.insert(0, "<W>/audit/scripts")
import graders  # noqa: E402

iid, kw, resp = sys.argv[1], json.loads(sys.argv[2]), json.loads(sys.argv[3])
for name, fn in graders.GRADERS.items():
    print(f"{name}: {fn(iid, kw, 'p', resp)}")
print(f"replacement: {graders.replacement(iid, kw, 'p', resp)}")
