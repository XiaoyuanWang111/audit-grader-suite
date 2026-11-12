"""Data facts that the grader code makes relevant (no responses involved)."""
import json
import re
from collections import Counter

DATA = "<W>/case/data/rlvr1_instruction_following.jsonl"
routes = Counter()
env = Counter()
gt = Counter()
grading = Counter()
regex_kw = Counter()
nth_gt_num = 0
kw_with_space = Counter()
kw_none_values = Counter()
examples = {}
with open(DATA, encoding="utf-8") as f:
    for line in f:
        row = json.loads(line)
        nu = row["extra_info"]["nemotron_ultra"]
        routes[nu["route"]] += 1
        env[row["env_class"]] += 1
        gt[row["reward_model"]["ground_truth"]] += 1
        rec = json.loads(nu["record_json"])
        grading[rec.get("grading_mode", "<absent>")] += 1
        for iid, kw in zip(rec["instruction_id_list"], rec["kwargs"]):
            kw = kw or {}
            for k, v in kw.items():
                if v is None:
                    kw_none_values[(iid, k)] += 1
            for key in ("keyword", "first_word", "last_word"):
                v = kw.get(key)
                if isinstance(v, str):
                    if re.search(r"[.^$*+?{}\[\]\\|()]", v):
                        regex_kw[(iid, key)] += 1
                        examples.setdefault(f"regex {iid}", v)
                    if " " in v.strip() or v != v.strip():
                        kw_with_space[(iid, key)] += 1
                        examples.setdefault(f"space {iid}", v)
            for key in ("keywords", "forbidden_words"):
                for v in kw.get(key) or []:
                    if re.search(r"[.^$*+?{}\[\]\\|()]", v):
                        regex_kw[(iid, key)] += 1
                        examples.setdefault(f"regex {iid}", v)
                    if " " in v.strip():
                        kw_with_space[(iid, key)] += 1
                        examples.setdefault(f"space {iid}", v)
            if iid == "length_constraints:nth_paragraph_first_word":
                if kw.get("nth_paragraph") is not None and kw.get("num_paragraphs") is not None and kw["nth_paragraph"] > kw["num_paragraphs"]:
                    nth_gt_num += 1
print("route", dict(routes))
print("env_class", dict(env))
print("ground_truth", dict(gt))
print("grading_mode", dict(grading))
print("kwargs with regex metacharacters", dict(regex_kw))
print("kwargs with spaces", dict(kw_with_space))
print("kwargs None values (dropped before grading)", dict(kw_none_values))
print("nth_paragraph > num_paragraphs", nth_gt_num)
for k, v in examples.items():
    print(k, repr(v))
