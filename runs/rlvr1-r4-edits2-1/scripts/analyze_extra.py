"""Per-finding shares, decision sensitivity, held-out numbers and extraction counts (step 5).

Reads audit/frozen/panel_verdicts.jsonl.gz and audit/results/defect_cases.jsonl.gz; writes
audit/results/extra_summary.json and prints tables.
"""
import glob
import gzip
import json
import os
import sys
from collections import Counter, defaultdict
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
sys.path.insert(0, HERE)
CASE = "<W>/case"
RES = os.path.join(HERE, "..", "results")

# (grader, check) -> finding label for defect verdicts not explained by extraction (F37/F38) or F44.
MAP = {
    ("sk", "keywords:word_count_different_numbers"): "F01", ("vi", "keywords:word_count_different_numbers"): "F01",
    ("sk", "keywords:word_once"): "F02", ("vi", "keywords:word_once"): "F02",
    ("sk", "copy:repeat_phrase"): "F03/F05", ("vi", "copy:repeat_phrase"): "F04",
    ("sk", "detectable_format:constrained_response"): "F06",
    ("sk", "detectable_format:multiple_sections"): "F07", ("vi", "detectable_format:multiple_sections"): "residual",
    ("vi", "length_constraints:number_paragraphs"): "F09", ("sk", "length_constraints:number_paragraphs"): "F10",
    ("vi", "paragraphs:paragraphs"): "F11", ("vi", "paragraphs:paragraphs2"): "F11",
    ("sk", "first_word:first_word_answer"): "F12", ("sk", "first_word:first_word_sent"): "F12/F42",
    ("sk", "length_constraints:nth_paragraph_first_word"): "F12",
    ("sk", "keywords:keyword_specific_position"): "F13", ("sk", "keywords:palindrome"): "F14",
    ("sk", "keywords:start_end"): "F15/F41", ("vi", "keywords:start_end"): "F16",
    ("sk", "keywords:no_adjacent_consecutive"): "F17", ("vi", "keywords:no_adjacent_consecutive"): "F18",
    ("sk", "detectable_format:square_brackets"): "F19", ("vi", "detectable_format:square_brackets"): "F20",
    ("sk", "detectable_format:bigram_wrapping"): "F21", ("sk", "detectable_format:sentence_hyphens"): "F22/F43",
    ("vi", "detectable_format:sentence_hyphens"): "F23", ("sk", "count:count_unique"): "F24",
    ("vi", "count:lowercase_counting"): "F26", ("vi", "change_case:english_capital"): "F27",
    ("vi", "change_case:english_lowercase"): "F27", ("vi", "startend:quotation"): "F28",
    ("sk", "detectable_content:postscript"): "F29", ("sk", "detectable_format:number_bullet_lists"): "F30",
    ("sk", "detectable_format:json_format"): "F32", ("vi", "detectable_format:json_format"): "F31/F32",
    ("sk", "detectable_content:number_placeholders"): "F33", ("vi", "detectable_content:number_placeholders"): "F33",
    ("vi", "detectable_format:title"): "F33", ("sk", "combination:two_responses"): "F36",
    ("vi", "combination:two_responses"): "F36", ("sk", "change_case:english_capital"): "F40", ("sk", "change_case:english_lowercase"): "F40",
    ("sk", "count:lowercase_counting"): "F47",
    ("sk", "last_word:last_word_answer"): "F41", ("sk", "last_word:last_word_sent"): "F41/F42",
    ("sk", "length_constraints:number_sentences"): "F43", ("vi", "length_constraints:number_sentences"): "F43",
    ("vi", "length_constraints:number_words"): "F34", ("vi", "first_word:first_word_sent"): "F34/F43",
    ("vi", "last_word:last_word_sent"): "F34/F43", ("vi", "keywords:palindrome"): "F34",
    ("vi", "change_case:capital_word_frequency"): "F34", ("vi", "last_word:last_word_answer"): "F34",
    ("vi", "first_word:first_word_answer"): "F34", ("vi", "length_constraints:nth_paragraph_first_word"): "F34",
    ("vi", "keywords:keyword_specific_position"): "F34/F43",
}


def load_lines():
    with gzip.open(os.path.join(HERE, "..", "frozen", "panel_verdicts.jsonl.gz"), "rt", encoding="utf-8") as f:
        return [json.loads(x) for x in f]


def attribution(lines, rows):
    by_key = {(r["run"], r["uuid"]): r for r in lines}
    counts = Counter()
    per_check_total = Counter()
    for r in lines:
        for iid in r["ids"]:
            per_check_total[iid] += 1
    examples = {}
    with gzip.open(os.path.join(RES, "defect_cases.jsonl.gz"), "rt", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            r = by_key[(d["run"], d["uuid"])]
            rec = rows[d["uuid"]]
            kw = rec["kwargs"][d["j"]] or {}
            if r["ext"]["repl_failure"]:
                label = "F38"
            elif r["ext"]["has_open"] and (r["ext"]["skyrl_empty"] if d["grader"] == "sk" else r["ext"]["vi_empty"]):
                label = "F37"
            elif d["iid"] == "length_constraints:nth_paragraph_first_word" and d["grader"] == "sk" and \
                    kw.get("nth_paragraph", 0) > kw.get("num_paragraphs", 99):
                label = "F44"
            else:
                label = MAP.get((d["grader"], d["iid"]), "residual")
            kind = "falsepass" if d["verdict"] else "falsefail"
            counts[(d["grader"], label, d["iid"], kind)] += 1
            examples.setdefault((d["grader"], label, d["iid"]), (d["run"], d["uuid"], d["j"]))
    return counts, per_check_total, examples


_C = None


def _init():
    global _C, _raw, _rows
    import contracts_grader as C
    import pipelines as P
    from analyze_panel import load_raw
    _C = C
    _raw = load_raw()
    _rows = P.load_rows()


def sensitivity_task(args):
    """For one decision switch, the constraint verdicts it changes, per run (replacement)."""
    from dataclasses import replace
    from analyze_panel import RELEVANT, COMMON
    entry, field, value, lines_small = args
    r_alt = replace(_C.PROPOSED, **{field: value})
    changed = Counter()
    prompt_changed = Counter()
    prompt_delta = Counter()
    for run, uuid, rp in lines_small:
        rec = _rows[uuid]
        g = _C.graded_text(_raw[(run, uuid)], run.split("/")[0].endswith("__thinking"))
        if g is None:
            continue
        new = list(rp)
        any_change = False
        for j, iid in enumerate(rec["instruction_id_list"]):
            if field not in COMMON and field not in RELEVANT[iid]:
                continue
            kw = {k: v for k, v in (rec["kwargs"][j] or {}).items() if v is not None}
            v = _C.check(iid, kw, g, r_alt)
            if v != rp[j]:
                changed[run] += 1
                new[j] = v
                any_change = True
        if any_change and all(new) != all(rp):
            prompt_changed[run] += 1
            prompt_delta[run] += (1 if all(new) else -1)
    return entry, dict(changed), dict(prompt_changed), dict(prompt_delta)


def main():
    import pipelines as P
    import contracts_grader as C
    rows = P.load_rows()
    lines = load_lines()
    counts, per_check_total, examples = attribution(lines, rows)
    total_verdicts = sum(per_check_total.values())
    agg = defaultdict(lambda: Counter())
    for (g, label, iid, kind), n in counts.items():
        agg[(g, label)][kind] += n
        agg[(g, label)]["checks:" + iid] += n
    print("Per finding (defect verdicts on the panel; share of all 55,783 constraint verdicts)")
    finding_rows = []
    for (g, label), c in sorted(agg.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        n = c["falsepass"] + c["falsefail"]
        checks = {k[7:]: v for k, v in c.items() if k.startswith("checks:")}
        denom = sum(per_check_total[i] for i in checks)
        finding_rows.append({"grader": g, "finding": label, "n": n, "falsepass": c["falsepass"],
                             "falsefail": c["falsefail"], "checks": checks, "check_verdicts": denom})
        print(f"{label:10s} {g}: {n:5d} (false pass {c['falsepass']}, false fail {c['falsefail']}) "
              f"= {100 * n / denom:.1f}% of the {denom} verdicts of {', '.join(sorted(checks))}")

    # held-out numbers (prompt level), replacement vs graders
    held = defaultdict(lambda: Counter())
    for r in lines:
        if not r["held_out"]:
            continue
        h = held[r["run"]]
        h["n"] += 1
        h["skyrl"] += r["sk_reward"] if not r["sk_err"] else 0.0
        h["replacement"] += all(r["rp"])
        h["gate"] += r["gate"]
        h["replacement_gate"] += all(v for v, s in zip(r["rp"], r["vi"]) if s is not None)
        if r["sk_reward"] == 1.0 and not r["sk_err"]:
            h["skyrl_passes"] += 1
            h["false_reward_proposed"] += not all(r["rp"])
    print("\nHeld-out responses (prompt level)")
    for run, h in sorted(held.items()):
        n = h["n"]
        print(f"{run}: n={n} SkyRL {100 * h['skyrl'] / n:.1f} replacement {100 * h['replacement'] / n:.1f} "
              f"gate {100 * h['gate'] / n:.1f} replacement-gate {100 * h['replacement_gate'] / n:.1f} "
              f"false rewards (proposed) {h['false_reward_proposed']}/{h['skyrl_passes']}")

    # extraction and content-free outcomes in the stored records
    ext = defaultdict(Counter)
    for r in lines:
        e = ext[r["run"]]
        e["n"] += 1
        e["length"] += r["finish_reason"] == "length"
        if r["ext"]["repl_failure"]:
            e["extraction_failure"] += 1
            e["extraction_failure_sk_reward1"] += r["sk_reward"] == 1.0
            e["extraction_failure_gate_pass"] += r["gate"]
            e["extraction_failure_sk_constraint_passes"] += sum(r["sk"])
        if r["ext"]["skyrl_empty"]:
            e["skyrl_empty"] += 1
            e["skyrl_empty_reward1"] += r["sk_reward"] == 1.0
            e["skyrl_empty_infra"] += bool(r["sk_err"])
        if r["ext"]["has_open"] and not r["run"].split("/")[0].endswith("__thinking"):
            e["literal_think_tag_nonreasoning"] += 1
        if r["sk_err"]:
            e["infra_error"] += 1
    print("\nExtraction outcomes")
    for run, e in sorted(ext.items()):
        print(run, dict(e))

    # F44 rows in the panel
    f44 = Counter()
    for r in lines:
        rec = rows[r["uuid"]]
        for j, iid in enumerate(r["ids"]):
            kw = rec["kwargs"][j] or {}
            if iid == "length_constraints:nth_paragraph_first_word" and kw["nth_paragraph"] > kw["num_paragraphs"]:
                f44["verdicts"] += 1
                f44["sk_pass"] += r["sk"][j]
                f44["sk_reward1"] += r["sk_reward"] == 1.0
    print("\nF44 (nth > num) verdicts in panel:", dict(f44))

    # decision sensitivity
    lines_small = [(r["run"], r["uuid"], r["rp"]) for r in lines]
    tasks = [(entry, f, v, lines_small) for entry, (f, v) in C.DECISION_SWITCHES.items()]
    sens = {}
    with Pool(6, initializer=_init) as pool:
        for entry, changed, pchanged, pdelta in pool.imap_unordered(sensitivity_task, tasks):
            sens[entry] = {"constraint_changes": sum(changed.values()), "prompt_changes": sum(pchanged.values()),
                           "prompt_delta": sum(pdelta.values()), "by_run_delta": pdelta}
    print("\nDecision sensitivity (replacement: flip one switch to the other reading)")
    n_resp = len(lines)
    for entry, s in sorted(sens.items(), key=lambda kv: -kv[1]["constraint_changes"]):
        print(f"{entry}: {s['constraint_changes']} constraint verdicts, {s['prompt_changes']} prompt verdicts, "
              f"net prompt score change {100 * s['prompt_delta'] / n_resp:+.2f} points over all {n_resp} responses")
    out = {"findings": finding_rows, "held_out": {k: dict(v) for k, v in held.items()},
           "extraction": {k: dict(v) for k, v in ext.items()}, "f44": dict(f44), "sensitivity": sens,
           "examples": {f"{g}|{lab}|{iid}": ex for (g, lab, iid), ex in examples.items()},
           "total_verdicts": total_verdicts}
    with open(os.path.join(RES, "extra_summary.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, indent=1)


if __name__ == "__main__":
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    main()
