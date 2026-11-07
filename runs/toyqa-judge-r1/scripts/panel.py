"""Step 5: grade the stored run (48 responses, recorded judge replies) with every pipeline and stage variant.

- Runs the three CLIs as the evaluation runs them (grader, reference, replacement) and keeps their outputs.
- Grades every response with stage variants of the grader, one finding fixed at a time, so each score change belongs
  to one stage; checks that the unfixed variant reproduces the grader's CLI and the all-fixed one the replacement's.
- Repeats each judgment with the recorded call-2 reply and counts verdict flips; rescores with call 2 first.
- Checks every pinned input before and after.

    python -I audit/scripts/panel.py      # writes audit/work/panel/
"""

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))

from toyqa_audit_lib import (CASE, QUESTIONS, ROOT, TEMPLATE, WORK, contract_parse, contract_scores,  # noqa: E402
                             grader_module, judges, load_jsonl, replacement_module, sha256_text)

OUT = WORK / "panel"
PY = [sys.executable, "-I"]
LABEL_OF_GRADE = {"A": "correct", "B": "incorrect", "C": "not_attempted"}
MODELS = ["orca-7b", "puffin-13b", "heron-32b-think", "ibis-8b-think"]


def check_pins(when):
    p = subprocess.run(PY + [str(ROOT / "audit" / "scripts" / "check_pins.py")], capture_output=True, text=True,
                       cwd=str(ROOT))
    print(f"[pins {when}] {p.stdout.strip().splitlines()[-1]}")
    if p.returncode:
        sys.exit(f"pinned input changed ({when}):\n{p.stdout}")


def run_cli(name, cmd):
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=str(ROOT))
    (OUT / f"{name}.stdout.txt").write_text(p.stdout + (("\nSTDERR:\n" + p.stderr) if p.stderr else ""),
                                            encoding="utf-8", newline="\n")
    return p.returncode, p.stdout


def variant(extract, failure_label, render, parse):
    """A pipeline assembled from stage functions; returns grade(judge, q, response) -> row dict."""
    def grade(judge, q, response):
        graded = extract(response)
        if graded is None:
            return {"label": failure_label, "grade": None, "judge_calls": 0, "prompt_sha256": None}
        prompt = render(TEMPLATE, q, graded)
        for call in (1, 2):
            g = parse(judge(prompt, call))
            if g is not None:
                return {"label": LABEL_OF_GRADE[g], "grade": g, "judge_calls": call, "prompt_sha256": sha256_text(prompt)}
        return {"label": "judge_error", "grade": None, "judge_calls": 2, "prompt_sha256": sha256_text(prompt)}
    return grade


G, R = grader_module, replacement_module
VARIANTS = {
    "grader": variant(G.extract_graded_text, "not_attempted", G.render_prompt, G.parse_grade),
    "fix_F1": variant(G.extract_graded_text, "extraction_failure", G.render_prompt, G.parse_grade),
    "fix_F2_F3": variant(G.extract_graded_text, "not_attempted", R.render_prompt, G.parse_grade),
    "fix_F4": variant(G.extract_graded_text, "not_attempted", G.render_prompt, R.parse_grade),
    "all_fixed": variant(G.extract_graded_text, "extraction_failure", R.render_prompt, R.parse_grade),
}


def grade_all(grade_fn, judge, rows):
    out = {}
    for r in rows:
        try:
            out[r["id"]] = grade_fn(judge, QUESTIONS[r["question_id"]], r["response"])
        except LookupError:
            out[r["id"]] = {"label": "uncovered", "grade": None, "judge_calls": None, "prompt_sha256": None}
        except Exception as e:  # noqa: BLE001
            out[r["id"]] = {"label": f"exception:{type(e).__name__}", "grade": None, "judge_calls": None,
                            "prompt_sha256": None}
    return out


def scores_by_model(labels, rows):
    table = {}
    for m in MODELS:
        ls = [labels[r["id"]] for r in rows if r["model"] == m]
        s = contract_scores(ls)
        table[m] = {k: (round(100 * v, 1) if isinstance(v, float) else v) for k, v in s.items()}
        table[m]["uncovered"] = sum(1 for x in ls if x == "uncovered" or x.startswith("exception"))
    return table


class SwappedJudge:
    """The recorded judge with calls 1 and 2 swapped: call 2's reply is used first, call 1's as the retry."""

    def __init__(self, recorded):
        self.recorded = recorded

    def __call__(self, prompt, call):
        return self.recorded(prompt, 3 - call)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    check_pins("before")
    rows = load_jsonl(CASE / "responses.jsonl")
    replies = {(r["prompt_sha256"], r["call"]): r["reply"] for r in load_jsonl(CASE / "judge_replies.jsonl")}
    recorded = judges.RecordedJudge(CASE / "judge_replies.jsonl")

    # 1. The three CLIs, as the evaluation runs them.
    cli = {
        "grader": PY + [str(CASE / "judge_pipeline.py"), "--out", str(OUT / "grader.labels.jsonl")],
        "reference": PY + [str(CASE / "reference" / "pipeline_ref.py"), str(CASE / "questions.jsonl"),
                           str(CASE / "responses.jsonl"), "recorded", str(OUT / "reference.labels.jsonl")],
        "replacement": PY + [str(ROOT / "audit" / "replacement" / "toyqa_replacement.py"),
                             "--out", str(OUT / "replacement.labels.jsonl")],
    }
    cli_labels = {}
    for name, cmd in cli.items():
        code, stdout = run_cli(name, cmd)
        print(f"== {name} CLI, exit {code}\n{stdout.rstrip()}")
        cli_labels[name] = {d["id"]: d["label"] for d in load_jsonl(OUT / f"{name}.labels.jsonl")} if code == 0 else {}

    # 2. Stage variants with the recorded judge.
    graded = {name: grade_all(fn, recorded, rows) for name, fn in VARIANTS.items()}
    labels = {name: {i: g["label"] for i, g in res.items()} for name, res in graded.items()}
    assert labels["grader"] == cli_labels["grader"], "variant 'grader' does not reproduce the grader CLI"
    assert labels["all_fixed"] == cli_labels["replacement"], "variant 'all_fixed' differs from the replacement CLI"
    ref_vs_repl = sum(cli_labels["reference"][i] != cli_labels["replacement"][i] for i in cli_labels["replacement"])
    print(f"\nreference vs replacement label differences: {ref_vs_repl} of {len(rows)}")

    # Coverage of the recorded judge for each variant's prompts.
    for name, res in graded.items():
        unc = sum(1 for g in res.values() if g["label"] == "uncovered" or g["label"].startswith("exception"))
        print(f"coverage {name}: {len(rows) - unc}/{len(rows)} rows labeled")

    # 3. Scores per variant and model, and the change from the grader.
    score_tables = {name: scores_by_model(ls, rows) for name, ls in labels.items()}
    keys = ["accuracy", "cga", "f_score", "not_attempted_rate", "correct", "incorrect", "not_attempted",
            "extraction_failure", "judge_error"]
    print("\nscores (percent; counts)")
    print(f"{'variant':<11}{'model':<17}" + "".join(f"{k[:9]:>10}" for k in keys))
    for name in VARIANTS:
        for m in MODELS:
            t = score_tables[name][m]
            print(f"{name:<11}{m:<17}" + "".join(f"{t[k]:>10}" for k in keys))

    # 4. Verdict disagreements between the grader and the all-fixed pipeline (= replacement = reference).
    disagreements = [(r["id"], r["model"], r["question_id"], labels["grader"][r["id"]], labels["all_fixed"][r["id"]])
                     for r in rows if labels["grader"][r["id"]] != labels["all_fixed"][r["id"]]]
    print(f"\ngrader vs all_fixed disagreements: {len(disagreements)} of {len(rows)}")
    for d in disagreements:
        cause = [n for n in ("fix_F1", "fix_F2_F3", "fix_F4") if labels[n][d[0]] != labels["grader"][d[0]]]
        print(f"  {d[0]} {d[1]:<16} {d[2]} grader={d[3]:<14} contract={d[4]:<18} changed by {cause}")

    # 5. Judge repeat: call 1 versus call 2 for every judged row (contract prompts), contract parser.
    flips, judged, flip_rows, per_prompt = 0, 0, [], {}
    for r in rows:
        g = graded["all_fixed"][r["id"]]
        if g["prompt_sha256"] is None:
            continue
        judged += 1
        r1, r2 = replies[(g["prompt_sha256"], 1)], replies[(g["prompt_sha256"], 2)]
        g1, g2 = contract_parse(r1), contract_parse(r2)
        per_prompt[g["prompt_sha256"]] = (g1, g2)
        if g1 is not None and g2 is not None and g1 != g2:
            flips += 1
            flip_rows.append((r["id"], g1, g2))
    distinct_flips = sum(1 for g1, g2 in per_prompt.values() if g1 is not None and g2 is not None and g1 != g2)
    no_grade_call1 = sum(1 for g1, _ in per_prompt.values() if g1 is None)
    print(f"\njudge repeat: {judged} judged rows, {len(per_prompt)} distinct prompts; verdict flips call 1 vs 2: "
          f"{flips} rows, {distinct_flips} prompts; call 1 without a grade: {no_grade_call1} prompts; flips {flip_rows}")
    swapped = grade_all(VARIANTS["all_fixed"], SwappedJudge(recorded), rows)
    swapped_scores = scores_by_model({i: g["label"] for i, g in swapped.items()}, rows)
    print("rescored with call 2 first (all_fixed): change from call 1 first")
    for m in MODELS:
        a, b = score_tables["all_fixed"][m], swapped_scores[m]
        print(f"  {m:<16} " + ", ".join(f"{k} {b[k] - a[k]:+.1f}" for k in ("accuracy", "cga", "f_score",
                                                                            "not_attempted_rate")))
    grader_swapped = grade_all(VARIANTS["grader"], SwappedJudge(recorded), rows)
    grader_swapped_scores = scores_by_model({i: g["label"] for i, g in grader_swapped.items()}, rows)

    # 6. Save everything.
    per_row = []
    for r in rows:
        g = graded["all_fixed"][r["id"]]
        sha = g["prompt_sha256"]
        per_row.append({"id": r["id"], "model": r["model"], "question_id": r["question_id"],
                        "finish_reason": r["finish_reason"],
                        **{f"label_{n}": labels[n][r["id"]] for n in VARIANTS},
                        "label_reference_cli": cli_labels["reference"].get(r["id"]),
                        "prompt_sha256": sha,
                        "reply_call1": replies.get((sha, 1)) if sha else None,
                        "reply_call2": replies.get((sha, 2)) if sha else None,
                        "label_all_fixed_call2_first": swapped[r["id"]]["label"]})
    with open(OUT / "per_row.jsonl", "w", encoding="utf-8", newline="\n") as f:
        for d in per_row:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    summary = {"scores": score_tables, "scores_call2_first_all_fixed": swapped_scores,
               "scores_call2_first_grader": grader_swapped_scores,
               "disagreements": disagreements, "judge_repeat": {"judged_rows": judged, "distinct_prompts": len(per_prompt),
                                                                "flip_rows": flip_rows, "flip_prompts": distinct_flips,
                                                                "call1_no_grade_prompts": no_grade_call1},
               "reference_vs_replacement_label_differences": ref_vs_repl}
    (OUT / "panel_summary.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8", newline="\n")
    check_pins("after")


if __name__ == "__main__":
    main()
