"""F-43: grader verdicts that change when the stored response loses its leading whitespace.

The panel's extraction removes leading whitespace only for completions that contain </think>.
Writes audit/frozen/leading_ws_effect.json.
"""
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "lib"))
import harness as H  # noqa: E402

rows = {str(r["key"]): r for r in H.load_rows()}
flips = Counter()
n_resp = 0
examples = []
by_cfg = Counter()
for f in sorted((H.CASE / "panel").glob("*/*.jsonl")):
    for line in f.read_text(encoding="utf-8").splitlines():
        d = json.loads(line)
        resp = d["response"]
        if not resp or not resp[0].isspace() or not resp.strip():
            continue
        n_resp += 1
        row = rows[str(d["key"])]
        a = H.grade_grader(row, resp, "strict")
        b = H.grade_grader(row, resp.lstrip(), "strict")
        for iid, x, y in zip(row["instruction_id_list"], a, b):
            if x != y:
                flips[(iid, "to_pass" if y else "to_fail")] += 1
                by_cfg[f.parent.name] += 1
                if len(examples) < 5:
                    examples.append(f"{f.parent.name}/{f.stem}/{d['key']}")
out = {"responses_with_leading_ws": n_resp, "flips": {f"{a}|{b}": c for (a, b), c in flips.items()},
       "total_flips": sum(flips.values()), "by_config": dict(by_cfg), "examples": examples}
json.dump(out, open(H.W / "audit/frozen/leading_ws_effect.json", "w", encoding="utf-8"), indent=1)
print(json.dumps(out, indent=1))
