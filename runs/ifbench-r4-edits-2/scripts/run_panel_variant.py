"""Grade the panel with the replacement under the grader's readings of every modelled decision
("rep_gr"): the difference grader vs rep_gr is what the decisions cannot explain (findings,
unmodelled decisions such as D-word and D-sentence, and replacement differences); rep_gr vs rep is the
effect of the decisions. Output: audit/work/panel_rep_gr.tsv (config, run, key, idx, verdict)."""
import json
import multiprocessing as mp
import os
import sys

W = "<W>"
GRADER_READINGS = dict(d_vacuous="pass", d_list_inline=True, d_punct_set="narrow", d_punct_separate=True,
                       d_vowel_paragraph="newline", d_palin_distinct=False, d_keyword_form="substring",
                       d_csv_wrapper=False, d_overlap_unit="char", d_typographic=False, d_options_whitespace=False,
                       d_template_outside=True, d_nows_trailing=False, d_empty_output="all_fail")


def work(args):
    cfg, run = args
    sys.path.insert(0, W + "/audit/scripts")
    import graders
    from run_panel import load_dataset_rows
    rows = load_dataset_rows()
    recs = [json.loads(x) for x in open(f"{W}/case/panel/{cfg}/{run}.jsonl", encoding="utf-8")]
    out = []
    for row, rec in zip(rows, recs):
        ef = cfg.endswith("__thinking") and "</think>" not in rec["raw_response"]
        for idx, (iid, kw) in enumerate(zip(row["ids"], row["kwargs"])):
            if ef:
                v = graders.grader_strict(iid, kw, row["prompt"], rec["response"])  # grader reading: graded as is
            else:
                v = graders.replacement(iid, kw, row["prompt"], rec["response"], **GRADER_READINGS)
            out.append(f"{cfg}\t{run}\t{row['key']}\t{idx}\t{'1' if v is True else '0' if v is False else v}")
    return out


if __name__ == "__main__":
    jobs = []
    for cfg in sorted(os.listdir(W + "/case/panel")):
        if os.path.isdir(f"{W}/case/panel/{cfg}"):
            jobs += [(cfg, fn[:-6]) for fn in sorted(os.listdir(f"{W}/case/panel/{cfg}")) if fn.endswith(".jsonl")]
    with mp.Pool(6) as pool, open(W + "/audit/work/panel_rep_gr.tsv", "w", encoding="utf-8", newline="\n") as fh:
        for lines in pool.imap(work, jobs):
            fh.write("\n".join(lines) + "\n")
    print("done", len(jobs))
