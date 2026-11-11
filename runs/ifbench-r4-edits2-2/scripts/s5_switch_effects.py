"""Step 5: effect of each decision entry's reading on the panel, measured with the frozen
replacement's switches.

For every instruction instance, re-grade with each single switch set to its alternative
reading (only switches the check's code reads), and once with every switch set to the
reading closest to the grader's behavior ("grader-aligned"). Writes
audit/work/switch_effects.json:
  per switch: verdicts changed, passes gained/lost, mean change in prompt-level strict
  accuracy (over all 228 runs);
  grader-aligned: remaining disagreements with the grader (a lower bound on the
  disagreements that no reading explains, i.e. finding-driven), by check.
"""
import glob
import inspect
import json
import os
import re
import sys
from collections import defaultdict
from multiprocessing import Pool

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ALT = {
    "D-strip": "raw", "D-word": "whitespace", "D-sentence": "nltk", "D-case": "sensitive", "D-vacuous": "pass",
    "D-typographic": "ascii", "D-conj-usage": "strict", "D-keyword-count": "at_least",
    "D-keyword-match": "inflections", "D-number-def": "words", "D-name-case": "insensitive",
    "D-pronoun-set": "broad", "D-punct-set": "core", "D-between": "exclusive", "D-japanese-kanji": "no",
    "D-japanese-digits": "yes", "D-japanese-segmentation": "whitespace", "D-reverse-content": "form_only",
    "D-csv-wrapper": "strict", "D-csv-rows": "incl_header", "D-csv-header-quoted": "data_only",
    "D-csv-one-field": "exactly_one", "D-capitals-set": "subset", "D-mcq-length": "words",
    "D-mcq-answer": "no_key", "D-multiples-prose": "only_numbers", "D-africa-set": "order_only",
    "D-title": "counts", "D-emoji-pos": "after_only", "D-indent": "blank_lines_count",
    "D-list-sep": "line_start_only", "D-list-intro": "no_intro", "D-newline-punct": "count_tokens",
    "D-bullets-after": "nothing_after", "D-whitespace-set": "zwsp", "D-options-exact": "contains",
    "D-options-label": "label_only", "D-template-markup": "plain_only", "D-paren-mix": "all_types",
    "D-paren-closed": "inner_closed", "D-quote-chars": "single_too", "D-subbullet-indent": "indented",
    "D-section": "whole", "D-titlecase-minor": "all_words", "D-overlap-reference": "prompt",
    "D-trigram-def": "char", "D-balanced": "within_one", "D-char-count": "no_spaces",
    "D-different-words": "across_sentences", "D-repeat-exact": "exact", "D-change-case": "case_counts",
    "D-span-index": "one_based", "D-alphabet-start": "from_a", "D-y": "vowel",
    "D-palindrome-distinct": "tokens", "D-repeat-count": "repetitions", "D-verb": "any_form",
    "D-vowel-reading": "exactly_three",
}
# the reading closest to the grader's behavior, where the grader's behavior matches one
GRADER_ALIGNED = {
    "D-strip": "raw", "D-word": "whitespace", "D-sentence": "nltk", "D-vacuous": "pass",
    "D-typographic": "ascii", "D-keyword-match": "inflections", "D-punct-set": "core",
    "D-japanese-digits": "yes", "D-japanese-segmentation": "whitespace", "D-reverse-content": "form_only",
    "D-csv-wrapper": "strict", "D-capitals-set": "subset", "D-africa-set": "order_only", "D-title": "counts",
    "D-indent": "blank_lines_count", "D-bullets-after": "nothing_after",
    "D-options-label": "label_only", "D-template-markup": "plain_only", "D-paren-closed": "inner_closed",
    "D-section": "whole", "D-trigram-def": "char", "D-change-case": "case_counts",
    "D-palindrome-distinct": "tokens", "D-verb": "any_form",
}
GLOBAL = {"words_of": "D-word", "sentences_of": "D-sentence", "norm_word": "D-case", "_quote_spans": "D-typographic",
          "_type_counts": "D-sentence"}


def relevant_switches():
    sys.path.insert(0, os.path.join(W, "audit", "replacement"))
    import ifb_replacement as rep
    out = {}
    for iid, fn in rep.CHECKS.items():
        src = inspect.getsource(fn)
        names = set(re.findall(r'"(D-[\w\-]+)"', src))
        for helper, sw in GLOBAL.items():
            if helper in src:
                names.add(sw)
        if "_csv_rows" in src or "_csv_payload" in src:
            names |= {"D-csv-wrapper", "D-csv-rows"}
        if "_kw_count" in src:
            names |= {"D-keyword-match", "D-case"}
        names.add("D-strip")
        out[iid] = sorted(n for n in names if n in ALT)
    return out


def work(path):
    sys.path.insert(0, os.path.join(W, "audit", "replacement"))
    os.environ.setdefault("NLTK_DATA", os.path.join(W, "case", "deps", "nltk_data"))
    import pyarrow.parquet as pq
    import ifb_replacement as rep
    rel = relevant_switches()
    rows = {x["key"]: x for x in pq.read_table(os.path.join(W, "case", "data", "train-00000-of-00001.parquet")).to_pylist()}
    verdicts = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    cfg, run = verdicts[0]["cfg"], verdicts[0]["run"]
    recs = {str(json.loads(l)["key"]): json.loads(l) for l in open(os.path.join(W, "case", "panel", cfg, run + ".jsonl"), encoding="utf-8")}
    res = []
    for v in verdicts:
        row = rows[str(v["key"])]
        kw = {k: x for k, x in row["kwargs"][v["i"]].items() if x is not None}
        resp = recs[str(v["key"])]["response"]
        d = {"key": v["key"], "i": v["i"], "iid": v["iid"], "gs": v["gs"], "ps": v["ps"], "alt": {}}
        if v["xfail"]:
            d["aligned"] = 0
            res.append(d)
            continue
        for sw in rel[v["iid"]]:
            try:
                d["alt"][sw] = 1 if rep.check(v["iid"], kw, resp, prompt=row["prompt"], switches={sw: ALT[sw]}) else 0
            except Exception:  # noqa: BLE001
                d["alt"][sw] = -1
        try:
            d["aligned"] = 1 if rep.check(v["iid"], kw, resp, prompt=row["prompt"], switches=GRADER_ALIGNED) else 0
        except Exception:  # noqa: BLE001
            d["aligned"] = -1
        res.append(d)
    return cfg, run, res


def main():
    paths = sorted(glob.glob(os.path.join(W, "audit", "work", "panel_verdicts", "*.jsonl")))
    per_switch = defaultdict(lambda: {"changed": 0, "gained": 0, "lost": 0, "instances": 0})
    run_prompt = defaultdict(lambda: defaultdict(dict))  # (cfg,run) -> key -> {variant: all-pass}
    aligned_rem = defaultdict(int)
    aligned_total = 0
    base_dis = 0
    with Pool(16) as pool:
        for cfg, run, res in pool.imap_unordered(work, paths):
            by_key = defaultdict(list)
            for d in res:
                by_key[d["key"]].append(d)
                if d["gs"] != d["ps"]:
                    base_dis += 1
                if d.get("aligned") is not None:
                    aligned_total += 1
                    if d["aligned"] != d["gs"]:
                        aligned_rem[d["iid"]] += 1
                for sw, val in d["alt"].items():
                    ps = per_switch[sw]
                    ps["instances"] += 1
                    if val != d["ps"]:
                        ps["changed"] += 1
                        ps["gained" if val == 1 else "lost"] += 1
            # prompt-level change per switch: a prompt's verdict with that switch flipped
            for key, lst in by_key.items():
                base = all(x["ps"] == 1 for x in lst)
                run_prompt[(cfg, run)][key]["base"] = base
                sws = set(s for x in lst for s in x["alt"])
                for sw in sws:
                    run_prompt[(cfg, run)][key][sw] = all((x["alt"].get(sw, x["ps"]) == 1) for x in lst)
                run_prompt[(cfg, run)][key]["aligned"] = all(x.get("aligned", x["ps"]) == 1 for x in lst)
                run_prompt[(cfg, run)][key]["grader"] = all(x["gs"] == 1 for x in lst)
    runs = list(run_prompt)
    out = {"switches": {}, "aligned": {}}
    for sw, d in sorted(per_switch.items(), key=lambda kv: -kv[1]["changed"]):
        deltas = []
        for rk in runs:
            pk = run_prompt[rk]
            deltas.append(sum((v.get(sw, v["base"]) - v["base"]) for v in pk.values()) / len(pk))
        d["mean_prompt_delta_points"] = 100 * sum(deltas) / len(deltas)
        d["max_abs_run_delta_points"] = 100 * max(abs(x) for x in deltas)
        out["switches"][sw] = d
    g_minus_al = [sum(v["aligned"] - v["grader"] for v in run_prompt[rk].values()) / len(run_prompt[rk]) for rk in runs]
    out["aligned"] = {"instances": aligned_total, "baseline_disagreements": base_dis,
                      "remaining_disagreements": sum(aligned_rem.values()), "by_check": dict(sorted(aligned_rem.items(), key=lambda kv: -kv[1])),
                      "mean_prompt_delta_aligned_minus_grader_points": 100 * sum(g_minus_al) / len(g_minus_al),
                      "switches": GRADER_ALIGNED}
    json.dump(out, open(os.path.join(W, "audit", "work", "switch_effects.json"), "w"), indent=1)
    print(f"baseline grader-vs-replacement disagreements {base_dis}; with grader-aligned readings {sum(aligned_rem.values())}")
    print("aligned remaining by check:", dict(list(out["aligned"]["by_check"].items())[:25]))
    print("mean prompt delta aligned - grader (points):", round(out["aligned"]["mean_prompt_delta_aligned_minus_grader_points"], 2))
    print("switch effects (verdicts changed; mean prompt-score change in points):")
    for sw, d in out["switches"].items():
        if d["changed"]:
            print(f"  {sw:26s} changed {d['changed']:5d} (+{d['gained']}/-{d['lost']}) of {d['instances']:6d}  mean {d['mean_prompt_delta_points']:+.2f}  max run {d['max_abs_run_delta_points']:.2f}")


if __name__ == "__main__":
    main()
