"""Write audit/fixtures.jsonl: one line per response labeled from a contract and run against a grader.

Sources (field "source"):
- "hand": the hand-written fixtures (tests/fixtures_data.py), labeled from the contract text.
- "property": metamorphic and forbidden-edit cases (tests/property_cases.json), labeled by
  construction from their source fixture.
- "pipeline": the extraction, determinism and exception fixtures of tests/test_pipeline.py.
- "content-free": one representative per instruction id and kind (empty, repeated, prompt
  restatement; the full run graded every row, scripts/content_free.py), labeled by the replacement.
- "fuzz": the smallest reproducing response of each unexplained fuzz disagreement
  (tests/fuzz_cases.json), labeled by the replacement and read by hand.
Fields: instruction_id, kwargs, response, label (pass or fail), plus id, source and, where known,
the finding or decision the case shows.
"""
import json
import os
import sys

AUDIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, AUDIT)
sys.path.insert(0, os.path.join(AUDIT, "tests"))
sys.path.insert(0, os.path.join(AUDIT, "replacement"))
import logging  # noqa: E402
logging.disable(logging.CRITICAL)
from fixtures_data import FIXTURES  # noqa: E402
import contract_grader as R  # noqa: E402

known = json.load(open(os.path.join(AUDIT, "tests", "known_failures.json"), encoding="utf-8"))
known_p = json.load(open(os.path.join(AUDIT, "tests", "known_failures_props.json"), encoding="utf-8"))


def shows(cid, kn):
    s = sorted({v for k, v in kn.items() if k.split("|", 1)[1] == cid})
    return s or None


lines = []
for f in FIXTURES:
    lines.append({"id": f["id"], "source": "hand", "instruction_id": f["instruction_id"], "kwargs": f["kwargs"],
                  "response": f["response"], "label": f["label"], "decisions": f["decisions"], "shows": shows(f["id"], known)})
for c in json.load(open(os.path.join(AUDIT, "tests", "property_cases.json"), encoding="utf-8")):
    lines.append({"id": c["id"], "source": "property:" + c["kind"], "instruction_id": c["instruction_id"],
                  "kwargs": c["kwargs"], "response": c["response"], "label": c["label"], "decisions": c["decisions"],
                  "shows": shows(c["id"], known_p)})
UNCLOSED = "Okay, the user wants a quote about teaching. Let me think about which quote fits best and"
lines += [
    {"id": "pipeline:G1-unclosed", "source": "pipeline", "instruction_id": "keywords:existence",
     "kwargs": {"keywords": ["quote", "teaching"]}, "response": UNCLOSED, "label": "fail",
     "note": "raw response of a reasoning model with no </think>: extraction failure", "shows": ["F-G1"]},
    {"id": "pipeline:G1-closed", "source": "pipeline", "instruction_id": "keywords:existence",
     "kwargs": {"keywords": ["quote", "teaching"]}, "response": "Okay, the user wants a quote about teaching.\n</think>\n\nHere is my answer.",
     "label": "fail", "note": "raw response of a reasoning model; graded text is the answer only", "shows": None},
    {"id": "pipeline:G2-nth-beyond", "source": "pipeline", "instruction_id": "length_constraints:nth_paragraph_first_word",
     "kwargs": {"num_paragraphs": 3, "nth_paragraph": 4, "first_word": "crash"}, "response": "A.\n\nB.\n\nCrash.",
     "label": "fail", "shows": ["F-G2"]},
    {"id": "pipeline:G3-empty", "source": "pipeline", "instruction_id": "last_word:last_word_answer",
     "kwargs": {"last_word": "limit"}, "response": "", "label": "fail", "shows": ["F-G3"]},
]
cf = json.load(open(os.path.join(AUDIT, "work", "content_free.json"), encoding="utf-8"))
rows = {}
with open(os.path.join(os.path.dirname(AUDIT), "case", "data", "rlvr1_instruction_following.jsonl"), encoding="utf-8") as f:
    for line in f:
        rec = json.loads(json.loads(line)["extra_info"]["nemotron_ultra"]["record_json"])
        for iid, kw in zip(rec["instruction_id_list"], rec["kwargs"]):
            rows.setdefault(iid, (kw, rec["prompt"]))
for kind in ("empty", "repeated", "restatement"):
    for iid, (kw, prompt) in sorted(rows.items()):
        resp = {"empty": "", "repeated": ("ok " * 50).strip(), "restatement": prompt}[kind]
        lab = "pass" if R.check(iid, kw, resp) else "fail"
        lines.append({"id": f"content-free:{kind}:{iid}", "source": "content-free", "instruction_id": iid, "kwargs": kw,
                      "response": resp, "label": lab, "shows": None})
fz = os.path.join(AUDIT, "tests", "fuzz_cases.json")
if os.path.exists(fz):
    for c in json.load(open(fz, encoding="utf-8")):
        lines.append({"id": c["id"], "source": "fuzz", "instruction_id": c["instruction_id"], "kwargs": c["kwargs"],
                      "response": c["response"], "label": c["label"], "shows": [c["reason"]]})
with open(os.path.join(AUDIT, "fixtures.jsonl"), "w", encoding="utf-8", newline="\n") as f:
    for x in lines:
        f.write(json.dumps(x, ensure_ascii=False) + "\n")
print(len(lines), "lines")
