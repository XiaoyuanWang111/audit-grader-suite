"""Break down the sentence_hyphens verdicts where A (or B) fails and R passes, by response shape."""
import collections
import json
import os
import sys

import regex as re

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIT = os.path.dirname(HERE)
W = os.path.dirname(AUDIT)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(AUDIT, "replacement"))
import contract_grader as R  # noqa: E402
from heldout import is_heldout  # noqa: E402

sub = sys.argv[1] if len(sys.argv) > 1 else "dev"
raw = {}
for run in {"Qwen__Qwen2.5-7B-Instruct/sample0.jsonl", "Qwen__Qwen3-4B-Instruct-2507/greedy.jsonl",
            "Qwen__Qwen3-4B-Instruct-2507/greedy_repeat.jsonl", "Qwen__Qwen3-4B-Instruct-2507/sample0.jsonl",
            "Qwen__Qwen3-4B-Thinking-2507__thinking/sample0.jsonl", "allenai__OLMo-2-1124-7B-Instruct/sample0.jsonl"}:
    with open(os.path.join(W, "case", "panel", run), encoding="utf-8") as f:
        raw[run] = [json.loads(x)["raw_response"] for x in f]
cnt = collections.Counter()
with open(os.path.join(AUDIT, "work", "panel_verdicts.jsonl"), encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        h = is_heldout(r["run"], r["uuid"])
        if (sub == "dev" and h) or (sub == "heldout" and not h) or r["extraction_failure"]:
            continue
        for c in r["constraints"]:
            if c["iid"] != "detectable_format:sentence_hyphens" or not c["R"]:
                continue
            t = R.graded_text(raw[r["run"]][r["line"]], r["reasoning_model"])
            key = []
            key.append("A_fail" if not c["A"] else "A_pass")
            key.append("has_end_punct" if re.search(r"[.!?。！？]", t) else "no_end_punct")
            key.append("spaced_dash" if re.search(r"\s[-–—]\s", t) else "no_spaced_dash")
            key.append("has_space" if re.search(r"\s", t) else "no_space")
            key.append("cjk" if re.search(r"\p{Han}", t) else "no_cjk")
            cnt[tuple(key)] += 1
for k, v in cnt.most_common():
    print(v, k)
