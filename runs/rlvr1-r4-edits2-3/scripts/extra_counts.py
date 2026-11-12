"""Counts for specific findings: data rows and panel verdicts. Writes audit/panel/extra_counts.json."""

import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIT = os.path.dirname(HERE)
sys.path.insert(0, AUDIT)

import harness as h  # noqa: E402

rows = h.load_rows()
by_uuid = {r["uuid"]: r for r in rows}
out = {}

# data: unsatisfiable or contradictory rows
co = collections.Counter()
for r in rows:
    ids = set(r["ids"])
    kws = dict(zip(r["ids"], r["kwargs"]))
    if "change_case:english_lowercase" in ids and "startend:end_checker" in ids:
        co["english_lowercase + end_checker (phrase has capitals)"] += 1
    if "change_case:english_capital" in ids and "startend:end_checker" in ids:
        co["english_capital + end_checker (phrase has lower case)"] += 1
    if "change_case:english_lowercase" in ids and "detectable_content:postscript" in ids:
        co["english_lowercase + postscript (P.S. capitals)"] += 1
    if "change_case:english_capital" in ids and "detectable_content:postscript" in ids:
        co["english_capital + postscript"] += 1
    k = kws.get("length_constraints:nth_paragraph_first_word")
    if k and k["nth_paragraph"] > k["num_paragraphs"]:
        co["nth_paragraph > num_paragraphs"] += 1
    if "punctuation:punctuation_dot" in ids and "detectable_content:postscript" in ids:
        co["no dots + postscript P.S."] += 1
    if "punctuation:no_comma" in ids and "language:response_language" in ids:
        co["no_comma + response_language"] += 1
    k = kws.get("detectable_content:postscript")
    if k and k["postscript_marker"] == "P.S." and "postscript starting with P.S." not in r["prompt"]:
        co["postscript shown as P.S (no period)"] += 1
    if "keywords:word_count_different_numbers" in ids:
        co["word_count_different_numbers rows"] += 1
out["data_rows"] = dict(co)

# panel: postscript rows shown as P.S where the answer writes P.S without the period
pc = collections.Counter()
recs = [json.loads(line) for line in open(os.path.join(AUDIT, "panel", "verdicts.jsonl"), encoding="utf-8")]
for v in recs:
    r = by_uuid[v["uuid"]]
    for i, iid in enumerate(v["ids"]):
        if iid == "detectable_content:postscript" and r["kwargs"][i]["postscript_marker"] == "P.S." \
                and "postscript starting with P.S." not in r["prompt"]:
            pc["verdicts on rows showing P.S"] += 1
            if v["rep"]["results"][i] and not v["skyrl"]["results"][i]:
                pc["contract pass, SkyRL fail"] += 1
            if v["rep"]["results"][i] and v["tc"]["results"][i] is False:
                pc["contract pass, task curation fail"] += 1
out["panel_postscript_shown_without_period"] = dict(pc)

# panel: extraction outcomes
ec = collections.Counter()
for v in recs:
    if v["reasoning_model"] and not v["has_close_think"]:
        ec["thinking: reasoning never closed"] += 1
        ec["thinking: never closed, SkyRL reward 1.0"] += v["skyrl"]["reward"] == 1.0
        ec["thinking: never closed, task-curation gate passed"] += v["tc"]["gate"]
    if not v["reasoning_model"] and v["has_open_think"]:
        ec["non-reasoning answer containing <think> (graded as empty)"] += 1
        ec["... of which SkyRL reward 1.0"] += v["skyrl"]["reward"] == 1.0
        ec["... of which gate passed"] += v["tc"]["gate"]
    if v["reasoning_model"] and v["has_close_think"] and v["skyrl"]["action_empty"]:
        ec["thinking: answer after </think> contains <think> (graded as empty)"] += 1
    if v["skyrl"]["infra"]:
        ec["SkyRL INFRA_ERROR rows"] += 1
out["panel_extraction"] = dict(ec)

# panel: truncated responses and their verdicts
tc_ = collections.Counter()
for v in recs:
    if v["finish_reason"] == "length":
        tc_["truncated"] += 1
        tc_["truncated, SkyRL reward 1.0"] += v["skyrl"]["reward"] == 1.0
        tc_["truncated, contract all pass"] += all(v["rep"]["results"]) and not v["rep"]["extraction_failure"]
out["panel_truncation"] = dict(tc_)

with open(os.path.join(AUDIT, "panel", "extra_counts.json"), "w", encoding="utf-8", newline="\n") as f:
    json.dump(out, f, indent=1)
print(json.dumps(out, indent=1))
