"""Measures for the report that the panel summary does not hold.

1. Seed sensitivity of grader A on the constraints whose nth_paragraph exceeds num_paragraphs.
2. Responses whose graded text is empty after extraction, and their rewards.
3. Grader A exceptions on the panel.
4. Content-free responses graded on every data row (empty, a repeated word, the row's own
   instruction texts): rows that grader A rewards and rows whose gate grader B passes.
5. Data rows whose constraints contradict each other under the contract.
Writes audit/results/extra_measures.json.
"""
import collections
import json
import os
import random
import sys

AUDIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, AUDIT)
import graders as G  # noqa: E402

CASE = os.path.join(AUDIT, "..", "case")
out = {}

recs = {}
order = []
with open(os.path.join(CASE, "data", "rlvr1_instruction_following.jsonl"), encoding="utf-8") as f:
    for line in f:
        rec = json.loads(json.loads(line)["extra_info"]["nemotron_ultra"]["record_json"])
        recs[rec["uuid"]] = rec
        order.append(rec["uuid"])
panel = {}
for folder in os.listdir(os.path.join(CASE, "panel")):
    d = os.path.join(CASE, "panel", folder)
    if not os.path.isdir(d):
        continue
    for name in os.listdir(d):
        with open(os.path.join(d, name), encoding="utf-8") as f:
            for line in f:
                p = json.loads(line)
                panel[(folder, name[:-6], p["uuid"])] = p["raw_response"]

# 1. seed sensitivity
flips = collections.Counter()
examples = []
for (folder, run, uuid), raw in panel.items():
    rec = recs[uuid]
    for iid, kw in zip(rec["instruction_id_list"], rec["kwargs"]):
        if iid == "length_constraints:nth_paragraph_first_word" and kw["nth_paragraph"] > kw["num_paragraphs"]:
            text = G.final_answer_text(raw)
            verdicts = [G.check_a(iid, kw, text, seed=s)[0] for s in range(20)]
            flips["constraints"] += 1
            flips["passes_seed0"] += verdicts[0]
            flips["passes_any_seed"] += any(verdicts)
            flips["verdict_changes_with_seed"] += len(set(verdicts)) > 1
            if len(set(verdicts)) > 1 and len(examples) < 3:
                examples.append({"folder": folder, "run": run, "uuid": uuid, "kwargs": kw,
                                 "passes_of_20_seeds": sum(verdicts)})
out["nth_paragraph_seed"] = {**flips, "examples": examples}

# 2. empty graded text and 3. exceptions
empty = []
exc = []
for (folder, run, uuid), raw in panel.items():
    rec = recs[uuid]
    text = G.final_answer_text(raw)
    if not text.strip():
        random.seed(0)
        reward, detail = G.grade_instruction_following(text, rec)
        empty.append({"folder": folder, "run": run, "uuid": uuid, "literal_think": "<think>" in raw,
                      "raw_chars": len(raw), "A_reward": reward, "errors": [e for e in detail["instruction_errors"] if e],
                      "ids": rec["instruction_id_list"]})
    random.seed(0)
    reward, detail = G.grade_instruction_following(text, rec)
    if any(detail["instruction_errors"]):
        exc.append({"folder": folder, "run": run, "uuid": uuid, "errors": [e for e in detail["instruction_errors"] if e],
                    "text_chars": len(text)})
out["empty_graded_text"] = empty
out["A_exceptions"] = exc

# 4. content-free responses on every row
texts = collections.defaultdict(list)
with open(os.path.join(AUDIT, "scripts", "instruction_texts.jsonl"), encoding="utf-8") as f:
    for line in f:
        e = json.loads(line)
        texts[e["uuid"]].append(e["text"])
cf = {}
per_check_pass = {}
for kind in ("empty", "repeated", "restated"):
    c = collections.Counter()
    checks = collections.Counter()
    for uuid in order:
        rec = recs[uuid]
        if kind == "empty":
            t = ""
        elif kind == "repeated":
            t = " ".join(["the"] * 40)
        else:
            t = "\n".join(texts[uuid])
        random.seed(0)
        reward, detail = G.grade_instruction_following(t, rec)
        gate, b = G.row_b_gate(t, rec)
        r_all = all(G.check_r(i, k, t) for i, k in zip(rec["instruction_id_list"], rec["kwargs"]))
        c["rows"] += 1
        c["A_reward_1"] += reward == 1.0
        c["B_gate_pass"] += gate
        c["R_all_pass"] += r_all
        for i, v in zip(rec["instruction_id_list"], detail["follow_instruction_list"]):
            checks[(i, "A")] += v
        for i, v in zip(rec["instruction_id_list"], b):
            if v is not None:
                checks[(i, "B")] += v
        for i in rec["instruction_id_list"]:
            checks[(i, "n")] += 1
    cf[kind] = dict(c)
    per_check_pass[kind] = {f"{i}|{g}": v for (i, g), v in sorted(checks.items())}
out["content_free_rows"] = cf
out["content_free_checks"] = per_check_pass

# 5. contradictory rows
contra = collections.Counter()
for uuid in order:
    rec = recs[uuid]
    ids = rec["instruction_id_list"]
    kws = [G.clean_kwargs(k) for k in rec["kwargs"]]
    d = dict(zip(ids, kws))
    if any(i == "length_constraints:nth_paragraph_first_word" and k["nth_paragraph"] > k["num_paragraphs"]
           for i, k in zip(ids, kws)):
        contra["nth_paragraph > num_paragraphs"] += 1
    if "detectable_content:postscript" in d and "punctuation:punctuation_dot" in d:
        contra["postscript marker with dots + no dots"] += 1
    if "detectable_format:constrained_response" in d and "punctuation:punctuation_dot" in d:
        contra["constrained option ends with a period + no dots"] += 1
    if "detectable_format:constrained_response" in d and ("change_case:english_lowercase" in d or "change_case:english_capital" in d):
        contra["constrained option + all lowercase/all capitals"] += 1
    if "startend:end_checker" in d and ("change_case:english_lowercase" in d or "change_case:english_capital" in d):
        contra["exact end phrase + all lowercase/all capitals (under D-end-phrase-case A)"] += 1
    if "change_case:english_lowercase" in d and "change_case:capital_word_frequency" in d and \
            d["change_case:capital_word_frequency"]["capital_relation"] == "at least":
        contra["all lowercase + at least N capital words"] += 1
    if "startend:quotation" in d and "keywords:start_end" in d:
        contra["wrap in quotes + nothing after the last word"] += 1
    if "startend:end_checker" in d and "keywords:start_end" in d:
        contra["end phrase ending in ? + nothing after the last word"] += 1
    if "first_word:first_word_answer" in d and "first_word:first_word_sent" in d and \
            d["first_word:first_word_answer"]["first_word"] != d["first_word:first_word_sent"]["first_word"]:
        contra["first word of response != first word of each sentence"] += 1
    if "last_word:last_word_answer" in d and "last_word:last_word_sent" in d and \
            d["last_word:last_word_answer"]["last_word"] != d["last_word:last_word_sent"]["last_word"]:
        contra["last word of response != last word of each sentence"] += 1
    if "startend:end_checker" in d and "last_word:last_word_sent" in d:
        contra["end phrase + last word of each sentence"] += 1
    if "startend:end_checker" in d and "last_word:last_word_answer" in d:
        contra["end phrase + last word of response"] += 1
    if "punctuation:punctuation_exclamation" in d and "count:count_unique" in d:
        pass
    if "letters:letter_counting" in d and d["letters:letter_counting"]["relation"] == "less than" and len(ids) > 1:
        contra["fewer than 2-3 letters + another constraint needing words"] += any(
            i not in ("punctuation:no_comma", "punctuation:punctuation_dot", "punctuation:punctuation_exclamation",
                      "keywords:forbidden_words", "letters:letter_counting") for i in ids)
contra["rows with at least one listed contradiction"] = 0
out["contradictions"] = dict(contra)

with open(os.path.join(AUDIT, "results", "extra_measures.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print(json.dumps({k: out[k] for k in ("nth_paragraph_seed", "content_free_rows", "contradictions")}, indent=1))
print("empty graded text:", len(empty), [(e["folder"][:12], e["literal_think"], e["A_reward"], e["raw_chars"]) for e in empty])
print("A exceptions:", exc)
