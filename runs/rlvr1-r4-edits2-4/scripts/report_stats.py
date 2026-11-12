"""Tables for AUDIT.md from audit/work/panel_summary.json and panel_verdicts.jsonl.
Writes audit/work/report_stats.json and prints markdown tables."""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

A = Path("<W>/audit")
CASE = A.parent / "case"
sys.path.insert(0, str(A / "lib"))
S = json.loads((A / "work" / "panel_summary.json").read_text(encoding="utf-8"))
recs = [json.loads(line) for line in open(A / "work" / "panel_verdicts.jsonl", encoding="utf-8")]
counts_in_data = json.loads((A / "work" / "instruction_texts.json").read_text(encoding="utf-8"))
SEMANTIC = {"count:count_unique", "detectable_format:bigram_wrapping", "language:response_language", "letters:letter_counting"}
MAIN = {("Qwen__Qwen2.5-7B-Instruct", "sample0"), ("Qwen__Qwen3-4B-Instruct-2507", "greedy"),
        ("Qwen__Qwen3-4B-Instruct-2507", "sample0"), ("Qwen__Qwen3-4B-Thinking-2507__thinking", "sample0"),
        ("allenai__OLMo-2-1124-7B-Instruct", "sample0")}  # greedy_repeat is the rerun only
out = {}

# overall constraint-level agreement (main runs, i.e. without greedy_repeat)
tot = Counter()
for r in recs:
    if (r["folder"], r["run"]) not in MAIN:
        continue
    for j, iid in enumerate(r["ids"]):
        s, g, p = bool(r["skyrl"][j]), r["gate"][j], bool(r["repl"][j])
        tot["n"] += 1
        tot["skyrl_disagree"] += s != p
        if g is not None:
            tot["gate_n"] += 1
            tot["gate_disagree"] += g != p
            tot["gate_vs_skyrl"] += g != s
    tot["rows"] += 1
    tot["skyrl_rewards"] += r["skyrl_reward"] == 1.0
    tot["false_rewards"] += r["skyrl_reward"] == 1.0 and not all(r["repl"])
    LANG = {"language:response_language", "change_case:english_capital", "change_case:english_lowercase"}
    nolang = all((bool(sv) if iid in LANG else rv) for iid, sv, rv in zip(r["ids"], r["skyrl"], r["repl"]))
    tot["false_rewards_nolang"] += r["skyrl_reward"] == 1.0 and not nolang
    tot["gate_passes"] += r["gate_pass"]
    rg = all(v for v, gv in zip(r["repl"], r["gate"]) if gv is not None)
    tot["false_gate_passes"] += r["gate_pass"] and not rg
    tot["extraction_failures"] += r["extraction_failure"]
out["overall_main_runs"] = dict(tot)
print("overall (main runs):", dict(tot))

# attribution totals per grader (all runs in the summary)
att = S["attribution"]
agg = {"skyrl": Counter(), "gate": Counter()}
dec = {"skyrl": Counter(), "gate": Counter()}
for key, c in att.items():
    iid, g = key.split("|")
    for k, v in c.items():
        if k.startswith("defect_"):
            agg[g][k] += v
        elif k == "any_decision":
            agg[g]["decision"] += v
        elif k == "extraction_failure":
            agg[g]["extraction_failure"] += v
        elif k.startswith("decision:"):
            dec[g][k[len("decision:"):]] += v
out["attribution_totals_all_runs"] = {g: dict(c) for g, c in agg.items()}
out["decision_counts_all_runs"] = {g: dict(c.most_common()) for g, c in dec.items()}
print("attribution totals (all runs):", out["attribution_totals_all_runs"])

# per-check table (all runs)
print("\n| Check | Rows' constraints | Panel verdicts | SkyRL pass | Gate pass | Replacement pass | SkyRL defect FP / FF | SkyRL decision | Gate defect FP / FF | Gate decision |")
print("|---|---|---|---|---|---|---|---|---|---|")
table = {}
for iid, c in S["per_check"].items():
    a_s = att.get(f"{iid}|skyrl", {})
    a_g = att.get(f"{iid}|gate", {})
    n = c["n"]
    gate = "judged" if iid in SEMANTIC else f"{100 * c.get('gate_pass', 0) / max(c.get('gate_n', 1), 1):.1f}%"
    row = (iid, counts_in_data[iid]["count"], n, f"{100 * c['skyrl_pass'] / n:.1f}%", gate, f"{100 * c['repl_pass'] / n:.1f}%",
           f"{a_s.get('defect_false_pass', 0)} / {a_s.get('defect_false_fail', 0)}", a_s.get("any_decision", 0),
           "-" if iid in SEMANTIC else f"{a_g.get('defect_false_pass', 0)} / {a_g.get('defect_false_fail', 0)}",
           "-" if iid in SEMANTIC else a_g.get("any_decision", 0))
    table[iid] = row
    print("| " + " | ".join(str(x) for x in row) + " |")
out["per_check_table"] = table

# two_responses: SkyRL passes that the replacement fails, with a separator at the start or end
raw = {}
for path in sorted((CASE / "panel").glob("*/*.jsonl")):
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            raw[(path.parent.name, path.stem, i)] = json.loads(line)["raw_response"]
import harness as h  # noqa: E402

edge = 0
total_fp = 0
for r in recs:
    if "combination:two_responses" in r["ids"] and not r["extraction_failure"]:
        j = r["ids"].index("combination:two_responses")
        if r["skyrl"][j] and not r["repl"][j]:
            total_fp += 1
            t = h.skyrl_text(raw[(r["folder"], r["run"], r["i"])]).strip()
            edge += t.startswith("******") or t.endswith("******")
out["two_responses_fp_edge"] = {"skyrl_false_pass": total_fp, "separator_at_start_or_end": edge}
print("\ntwo_responses SkyRL passes failed by the replacement:", total_fp, "with a separator at the start or end:", edge)

# F47: english_capital SkyRL fails on text with no lowercase letter whose lower-cased text detects as English
import langdetect  # noqa: E402
from langdetect import DetectorFactory  # noqa: E402

DetectorFactory.seed = 0
f47 = Counter()
for r in recs:
    if "change_case:english_capital" in r["ids"] and not r["extraction_failure"]:
        j = r["ids"].index("change_case:english_capital")
        t = h.skyrl_text(raw[(r["folder"], r["run"], r["i"])])
        if not r["skyrl"][j] and t and not any(c.islower() for c in t) and any(c.isalpha() for c in t):
            f47["no_lowercase_but_skyrl_fail"] += 1
            try:
                f47["lowercased_detects_en"] += langdetect.detect(t.lower()) == "en"
            except Exception:
                pass
out["f47_english_capital"] = dict(f47)
print("F47 english_capital:", dict(f47))
(A / "work" / "report_stats.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
