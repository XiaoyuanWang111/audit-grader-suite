"""Reproduce one fixture: print the exact input and each grader's verdict.

Usage (Git Bash, from W):
  NLTK_DATA=case/deps/nltk_data .venv/Scripts/python.exe -B audit/scripts/repro.py <fixture id> [...]
The grader verdict is computed by the grader's own strict path
(IFBench.grader.test_instruction_following_strict) on a one-instruction row.
"""
import json
import sys
from pathlib import Path

W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W / "audit" / "scripts"))
sys.path.insert(0, str(W / "audit" / "tests"))
sys.path.insert(0, str(W / "audit" / "replacement"))
import harness as H  # noqa: E402
import ifbench_fixed as RF  # noqa: E402
from fixtures_data import FIXTURES  # noqa: E402

BY_ID = {f["id"]: f for f in FIXTURES}
for fid in sys.argv[1:]:
    f = BY_ID[fid]
    g = H.check_one(f["check"], f["kwargs"], f["response"], which="grader", prompt=f["prompt"])
    r = H.check_one(f["check"], f["kwargs"], f["response"], which="reference", prompt=f["prompt"])
    x = RF.check(f["check"], f["kwargs"], f["response"], prompt=f["prompt"] or "PROMPT", opts=RF.PROPOSED)
    print(f"fixture   {fid}")
    print(f"check     {f['check']}")
    print(f"kwargs    {json.dumps(f['kwargs'], ensure_ascii=True)}")
    print(f"response  {json.dumps(f['response'], ensure_ascii=True)}")
    print(f"contract  {'pass' if f['label'] else 'fail'}  (decisions: {', '.join(f['dec']) or 'none'})")
    print(f"grader    {g if isinstance(g, str) else ('pass' if g else 'fail')}")
    print(f"reference {r if isinstance(r, str) else ('pass' if r else 'fail')}")
    print(f"replacement(PROPOSED) {'pass' if x else 'fail'}")
    print()
