"""Write the commands of AUDIT.md's appendix, exactly as written, into work/appendix_commands.sh with the
verdicts of report_cases.CASES (same order). Then: bash work/appendix_commands.sh | python scripts/check_commands.py"""
import json
import shlex
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
W = HERE.parents[1]
sys.path.insert(0, str(HERE))
from report_cases import CASES  # noqa: E402

text = (W / "audit/AUDIT.md").read_text(encoding="utf-8")
appendix = text.split("## Appendix: every counterexample command", 1)[1]
NL = chr(10)
block = appendix.split("```bash" + NL, 1)[1].split(NL + "```" + NL, 1)[0]
commands = [line for line in block.splitlines() if line.startswith("$PY ")]
assert len(commands) == len(CASES), (len(commands), len(CASES))
lines = ["cd \"$(dirname \"$0\")/..\"", 'export NLTK_DATA="<W>/case/deps/nltk_data"',
         "export PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8", "PY=../.venv/Scripts/python.exe"]
for cmd, (fid, _, _, expected) in zip(commands, CASES):
    lines.append(f"echo '== {fid} ' {shlex.quote(json.dumps(expected))}")
    lines.append(cmd + " 2>/dev/null")
script = W / "audit/work/appendix_commands.sh"
script.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
print(f"wrote {script}; run: bash work/appendix_commands.sh | python scripts/check_commands.py")
