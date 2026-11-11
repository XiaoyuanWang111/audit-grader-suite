"""Step 5 analysis of audit/frozen/panel_verdicts.jsonl.gz.

For every constraint verdict where a grader (SkyRL = "sk", verifyit gate = "vi") differs from the
replacement under the proposed readings, the replacement is rerun under every combination of the decision
switches relevant to that check. If some combination gives the grader's verdict, the disagreement is a
decision; otherwise it is a defect (the verdict is wrong under every reading the decision table allows).
"Fixes only" takes the grader's verdict except on defects.

Writes audit/results/panel_summary.json and audit/results/panel_tables.txt, and
audit/results/defect_cases.jsonl.gz (one line per defect verdict, for per-finding attribution).
"""
import glob
import gzip
import itertools
import json
import os
import random
import sys
from collections import Counter, defaultdict
from dataclasses import replace
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "lib"))
CASE = "<W>/case"
RES = os.path.join(HERE, "..", "results")
os.makedirs(RES, exist_ok=True)

COMMON = ["strip_whitespace", "empty_fails"]
W = ["apostrophe_joins", "hyphen_joins"]
S = ["linebreak_ends_sentence", "protect_abbreviations"]
KW = ["keyword_substring", "keyword_inflection", "case_insensitive_words"] + W
RELEVANT = {
    "change_case:capital_word_frequency": ["allcaps_short_words"] + W,
    "change_case:english_capital": ["english_lenient"],
    "change_case:english_lowercase": ["english_lenient"],
    "combination:two_responses": ["two_responses_differ", "two_responses_extra_sep_fails"],
    "copy:repeat_phrase": ["repeat_center_middle_only", "repeat_verbatim_fails", "case_insensitive_words"] + W,
    "count:count_unique": ["case_insensitive_words"] + W,
    "count:counting_composition": S + W,
    "count:lowercase_counting": ["lowercase_per_word"] + W,
    "detectable_content:number_placeholders": ["placeholder_any"],
    "detectable_content:postscript": ["marker_markup_ok", "postscript_at_end", "postscript_case_sensitive",
                                     "postscript_line_start"],
    "detectable_format:bigram_wrapping": ["bigram_odd_ok"] + W,
    "detectable_format:constrained_response": ["constrained_exact"],
    "detectable_format:json_format": ["json_container_only"],
    "detectable_format:multiple_sections": ["section_case_sensitive", "section_numbering", "section_preamble_ok",
                                            "marker_markup_ok", "section_line_start"],
    "detectable_format:number_bullet_lists": ["bullet_all_markers", "bullet_nested"],
    "detectable_format:number_highlighted_sections": ["highlight_bold"],
    "detectable_format:sentence_hyphens": ["hyphens_single_ok", "hyphens_spaces_inside_ok", "hyphens_spaced_dash_fails"] + S,
    "detectable_format:square_brackets": ["brackets_each_word"] + W,
    "detectable_format:title": ["title_anywhere"],
    "first_word:first_word_answer": ["leading_markup_ok", "case_insensitive_words"] + W,
    "first_word:first_word_sent": ["leading_markup_ok", "case_insensitive_words"] + S,
    "keywords:existence": KW,
    "keywords:forbidden_words": KW,
    "keywords:frequency": KW,
    "keywords:keyword_specific_position": ["case_insensitive_words"] + S + W,
    "keywords:letter_frequency": ["letter_case_insensitive"],
    "keywords:no_adjacent_consecutive": ["adjacent_cross_punct", "consecutive_both_orders", "adjacent_latin_only"],
    "keywords:palindrome": ["palindrome_min3", "palindrome_case_insensitive"] + W,
    "keywords:start_end": ["start_end_two_words", "leading_markup_ok", "case_insensitive_words"] + W,
    "keywords:word_count_different_numbers": ["wcdn_exact"] + KW,
    "keywords:word_once": KW,
    "language:response_language": [],
    "last_word:last_word_answer": ["case_insensitive_words"] + W,
    "last_word:last_word_sent": ["case_insensitive_words"] + S + W,
    "length_constraints:nth_paragraph_first_word": ["blank_line_whitespace", "paragraph_sep_any_count",
                                                    "leading_markup_ok", "case_insensitive_words"],
    "length_constraints:number_paragraphs": ["divider_own_line", "empty_piece_fails"],
    "length_constraints:number_sentences": S,
    "length_constraints:number_words": W,
    "letters:letter_counting": ["letters_are_chars", "letter_any_script"] + W,
    "letters:letter_counting2": ["letter_case_insensitive"],
    "paragraphs:paragraphs": ["divider_own_line", "empty_piece_fails"],
    "paragraphs:paragraphs2": ["blank_line_whitespace", "paragraph_sep_any_count"],
    "punctuation:no_comma": ["comma_variants"],
    "punctuation:punctuation_dot": ["dot_variants"],
    "punctuation:punctuation_exclamation": ["exclamation_variants"],
    "startend:end_checker": ["end_nonwords_ok", "end_case_sensitive"],
    "startend:quotation": ["typographic_quotes"],
}

_raw = None
_rows = None


def load_raw():
    raw = {}
    for path in sorted(glob.glob(CASE + "/panel/*/*.jsonl")):
        folder = os.path.basename(os.path.dirname(path))
        run = os.path.splitext(os.path.basename(path))[0]
        with open(path, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                raw[(f"{folder}/{run}", r["uuid"])] = r["raw_response"]
    return raw


def _init():
    global _raw, _rows, C
    import contracts_grader as C  # noqa: F401
    import pipelines as P
    globals()["C"] = C
    _raw = load_raw()
    _rows = P.load_rows()


def combos_for(iid):
    names = COMMON + RELEVANT[iid]
    for values in itertools.product([True, False], repeat=len(names)):
        yield dict(zip(names, values))


def classify(task):
    """task: (run, uuid, j, grader verdicts dict). Returns the set of replacement verdicts over all readings."""
    run, uuid, j = task
    rec = _rows[uuid]
    iid = rec["instruction_id_list"][j]
    kw = {k: v for k, v in (rec["kwargs"][j] or {}).items() if v is not None}
    g = C.graded_text(_raw[(run, uuid)], run.split("/")[0].endswith("__thinking"))
    if g is None:
        return task, [False]
    seen = set()
    for combo in combos_for(iid):
        seen.add(C.check(iid, kw, g, replace(C.PROPOSED, **combo)))
        if len(seen) == 2:
            break
    return task, sorted(seen)


def boot_ci(diffs_by_row, n=2000, seed=0):
    rng = random.Random(seed)
    vals = list(diffs_by_row)
    m = len(vals)
    if m == 0:
        return (0.0, 0.0)
    means = []
    for _ in range(n):
        s = 0.0
        for _ in range(m):
            s += vals[rng.randrange(m)]
        means.append(s / m)
    means.sort()
    return (means[int(0.025 * n)], means[int(0.975 * n) - 1])


def main(workers):
    import pipelines as P
    lines = []
    with gzip.open(os.path.join(HERE, "..", "frozen", "panel_verdicts.jsonl.gz"), "rt", encoding="utf-8") as f:
        for line in f:
            lines.append(json.loads(line))
    tasks = []
    for r in lines:
        for j, iid in enumerate(r["ids"]):
            rp = r["rp"][j]
            if r["sk"][j] != rp or (r["vi"][j] is not None and r["vi"][j] != rp):
                tasks.append((r["run"], r["uuid"], j))
    print(f"{len(lines)} responses, {sum(len(r['ids']) for r in lines)} constraint verdicts, "
          f"{len(tasks)} with a disagreement to classify", flush=True)
    readings = {}
    with Pool(workers, initializer=_init) as pool:
        for task, seen in pool.imap_unordered(classify, tasks, chunksize=64):
            readings[task] = seen

    # ---- per-check tables
    per_check = defaultdict(Counter)
    defect_cases = []
    fixes = {}  # (run, uuid) -> {"sk": [...], "vi": [...]}
    for r in lines:
        key = (r["run"], r["uuid"])
        fx_sk, fx_vi = [], []
        for j, iid in enumerate(r["ids"]):
            rp = r["rp"][j]
            c = per_check[iid]
            c["n"] += 1
            c["rp_pass"] += rp
            c["sk_pass"] += r["sk"][j]
            seen = readings.get((r["run"], r["uuid"], j), [rp])
            for g in ("sk", "vi"):
                v = r[g][j]
                if v is None:
                    if g == "vi":
                        fx_vi.append(None)
                    continue
                if g == "vi":
                    c["vi_n"] += 1
                    c["vi_pass"] += v
                if v == rp:
                    c[f"{g}_agree"] += 1
                    fixed = v
                elif v in seen:
                    c[f"{g}_decision"] += 1
                    c[f"{g}_decision_{'pass' if v else 'fail'}"] += 1
                    fixed = v
                else:
                    c[f"{g}_defect"] += 1
                    c[f"{g}_defect_{'falsepass' if v else 'falsefail'}"] += 1
                    fixed = rp
                    defect_cases.append({"run": r["run"], "uuid": r["uuid"], "j": j, "iid": iid, "grader": g,
                                         "verdict": v, "held_out": r["held_out"]})
                (fx_sk if g == "sk" else fx_vi).append(fixed)
            if r["sk"][j] is not None and r["vi"][j] is not None and r["sk"][j] != r["vi"][j]:
                c["sk_vs_vi_disagree"] += 1
        fixes[key] = {"sk": fx_sk, "vi": fx_vi}

    # ---- per-run scores
    runs = defaultdict(list)
    for r in lines:
        runs[r["run"]].append(r)
    run_rows = {}
    for run, rs in sorted(runs.items()):
        n = len(rs)
        infra = sum(1 for r in rs if r["sk_err"])
        sk = [r["sk_reward"] if not r["sk_err"] else 0.0 for r in rs]
        rp_all = [float(all(r["rp"])) for r in rs]
        fx_sk = [float(all(fixes[(r["run"], r["uuid"])]["sk"])) for r in rs]
        gate = [float(r["gate"]) for r in rs]
        rp_gate = [float(all(v for v, s in zip(r["rp"], r["vi"]) if s is not None)) for r in rs]
        fx_vi = [float(all(v for v in fixes[(r["run"], r["uuid"])]["vi"] if v is not None)) for r in rs]
        sk_pass_idx = [i for i, r in enumerate(rs) if r["sk_reward"] == 1.0 and not r["sk_err"]]
        false_reward_fix = sum(1 for i in sk_pass_idx if fx_sk[i] == 0.0)
        false_reward_prop = sum(1 for i in sk_pass_idx if rp_all[i] == 0.0)
        gate_pass_idx = [i for i, r in enumerate(rs) if r["gate"]]
        false_gate_fix = sum(1 for i in gate_pass_idx if fx_vi[i] == 0.0)
        false_gate_prop = sum(1 for i in gate_pass_idx if rp_gate[i] == 0.0)
        d_fix = [a - b for a, b in zip(fx_sk, sk)]
        d_prop = [a - b for a, b in zip(rp_all, sk)]
        d_vi_fix = [a - b for a, b in zip(fx_vi, gate)]
        run_rows[run] = {
            "n": n, "finish_length": sum(r["finish_reason"] == "length" for r in rs),
            "skyrl_empty_text": sum(r["ext"]["skyrl_empty"] for r in rs),
            "extraction_failure": sum(r["ext"]["repl_failure"] for r in rs),
            "infra_error": infra,
            "infra_error_msgs": Counter(m.split(":")[0] for r in rs for m in r["sk_err_msg"]).most_common(3),
            "skyrl": sum(sk) / n, "fixes_only_skyrl": sum(fx_sk) / n, "replacement": sum(rp_all) / n,
            "d_fix": sum(d_fix) / n, "d_fix_ci": boot_ci(d_fix), "d_prop": sum(d_prop) / n,
            "d_prop_ci": boot_ci(d_prop),
            "gate": sum(gate) / n, "fixes_only_gate": sum(fx_vi) / n, "replacement_gate": sum(rp_gate) / n,
            "d_vi_fix": sum(d_vi_fix) / n, "d_vi_fix_ci": boot_ci(d_vi_fix),
            "skyrl_passes": len(sk_pass_idx), "false_reward_fixes_only": false_reward_fix,
            "false_reward_proposed": false_reward_prop,
            "gate_passes": len(gate_pass_idx), "false_gate_fixes_only": false_gate_fix,
            "false_gate_proposed": false_gate_prop,
            "held_out_n": sum(r["held_out"] for r in rs),
        }

    # ---- rerun comparison (greedy vs greedy_repeat)
    a = {r["uuid"]: r for r in runs["Qwen__Qwen3-4B-Instruct-2507/greedy"]}
    b = {r["uuid"]: r for r in runs["Qwen__Qwen3-4B-Instruct-2507/greedy_repeat"]}
    common = sorted(set(a) & set(b))
    rerun = {
        "rows": len(common),
        "identical_text": sum(1 for u in common if _same_text(u)),
        "skyrl_prompt_changes": sum(1 for u in common if a[u]["sk_reward"] != b[u]["sk_reward"]),
        "skyrl_score_diff": (sum(b[u]["sk_reward"] for u in common) - sum(a[u]["sk_reward"] for u in common)) / len(common),
        "gate_prompt_changes": sum(1 for u in common if a[u]["gate"] != b[u]["gate"]),
        "gate_score_diff": (sum(b[u]["gate"] for u in common) - sum(a[u]["gate"] for u in common)) / len(common),
        "replacement_score_diff": (sum(all(b[u]["rp"]) for u in common) - sum(all(a[u]["rp"]) for u in common)) / len(common),
    }

    summary = {"per_check": {k: dict(v) for k, v in per_check.items()}, "runs": run_rows, "rerun": rerun,
               "n_disagreements_classified": len(tasks)}
    with open(os.path.join(RES, "panel_summary.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(summary, f, indent=1, default=list)
    with gzip.open(os.path.join(RES, "defect_cases.jsonl.gz"), "wt", encoding="utf-8") as f:
        for d in defect_cases:
            f.write(json.dumps(d) + "\n")
    write_tables(summary)


_raw_texts = None


def _same_text(uuid):
    global _raw_texts
    if _raw_texts is None:
        _raw_texts = load_raw()
    return (_raw_texts[("Qwen__Qwen3-4B-Instruct-2507/greedy", uuid)] ==
            _raw_texts[("Qwen__Qwen3-4B-Instruct-2507/greedy_repeat", uuid)])


def write_tables(s):
    out = []
    out.append("Per check (constraint verdicts over the whole panel)")
    out.append("check | n | pass% repl | pass% SkyRL | SkyRL decision | SkyRL defect (false pass/false fail) | "
               "verifyit n | pass% verifyit | verifyit decision | verifyit defect (fp/ff) | SkyRL!=verifyit")
    for iid, c in sorted(s["per_check"].items()):
        n = c["n"]
        vn = c.get("vi_n", 0)
        out.append(
            f"{iid} | {n} | {100 * c['rp_pass'] / n:.1f} | {100 * c['sk_pass'] / n:.1f} | {c.get('sk_decision', 0)} | "
            f"{c.get('sk_defect', 0)} ({c.get('sk_defect_falsepass', 0)}/{c.get('sk_defect_falsefail', 0)}) | {vn} | "
            + (f"{100 * c.get('vi_pass', 0) / vn:.1f}" if vn else "-")
            + f" | {c.get('vi_decision', 0)} | {c.get('vi_defect', 0)} ({c.get('vi_defect_falsepass', 0)}/"
              f"{c.get('vi_defect_falsefail', 0)}) | {c.get('sk_vs_vi_disagree', 0)}")
    tot = Counter()
    for c in s["per_check"].values():
        tot.update(c)
    out.append(f"TOTAL n={tot['n']} sk_defect={tot['sk_defect']} (fp {tot['sk_defect_falsepass']}, ff {tot['sk_defect_falsefail']}) "
               f"sk_decision={tot['sk_decision']} vi_n={tot['vi_n']} vi_defect={tot['vi_defect']} (fp {tot['vi_defect_falsepass']}, "
               f"ff {tot['vi_defect_falsefail']}) vi_decision={tot['vi_decision']} sk!=vi={tot['sk_vs_vi_disagree']}")
    out.append("")
    out.append("Per run (prompt level)")
    for run, r in s["runs"].items():
        out.append(json.dumps({run: r}))
    out.append("")
    out.append("Rerun: " + json.dumps(s["rerun"]))
    with open(os.path.join(RES, "panel_tables.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 4)
