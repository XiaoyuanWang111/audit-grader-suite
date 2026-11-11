"""Grade every stored panel response with grader A, grader B and the replacement R (step 5).

Each grader gets the text its own extraction produces: A `final_answer_text`, B `_answer_text`,
R the contract's rule (text after the last `</think>` for the thinking model, whose responses
without `</think>` are extraction failures; the whole response otherwise).

For each constraint R also records which decision entries its check consulted, its verdict with each
of those entries flipped to reading B (the effect of each reading), and, where A or B disagrees with
R, the single entries whose reading B reproduces that grader's verdict.

Output: audit/out/panel_verdicts.jsonl, one line per response. Usage: python panel.py [workers]
"""
import json
import random
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W / "audit" / "lib"))
PANEL = W / "case" / "panel"
OUT = W / "audit" / "out" / "panel_verdicts.jsonl"

_rows = None


def _init():
    global _rows
    import graders_under_audit as gu
    _rows = {r["uuid"]: r for r in gu.load_rows()}


def grade_chunk(args):
    import contract_grader as cg
    import graders_under_audit as gu

    rel, lines = args
    reasoning = rel.split("/")[0].endswith("__thinking")
    out = []
    for line_no, line in lines:
        resp = json.loads(line)
        row = _rows[resp["uuid"]]
        rec, raw = row["record"], resp["raw_response"]
        random.seed(0)  # F29: NVIDIA draws from the global random state for out-of-range nth_paragraph
        a_reward, a_det = gu.reward_a(raw, rec)
        a_text = gu.extract_a(raw)
        b_text = gu.extract_b(raw)
        r_text = cg.graded_text(raw, reasoning)
        ids, kws = rec["instruction_id_list"], rec["kwargs"]
        cons = []
        for i, (iid, kw) in enumerate(zip(ids, kws)):
            ctx = {}
            if iid == "detectable_content:postscript":
                ctx["shown_marker"] = cg.shown_postscript_marker(row["prompt"], kw["postscript_marker"])
            a = a_det["follow_instruction_list"][i]
            a_err = a_det["instruction_errors"][i]
            b = gu.check_b(iid, kw, b_text)
            b_err = isinstance(b, str)
            if b_err:
                b = False
            c = {"id": iid, "A": a, "A_err": a_err, "B": b, "B_err": b_err}
            if r_text is None:
                c["R"] = False
                c["used"] = []
                c["flips"] = {}
            else:
                v, used = cg.check_used(iid, kw, r_text, None, ctx)
                c["R"] = v
                c["used"] = sorted(used)
                c["flips"] = {d: cg.check(iid, kw, r_text, {d: "B"}, ctx) for d in sorted(used)}
                c["flips"] = {d: fv for d, fv in c["flips"].items() if fv is not v}
                for g in ("A", "B"):
                    gv = c[g]
                    if gv is None or gv is v:
                        continue
                    c[g + "_explained"] = sorted(d for d in c["flips"])  # flips all give `not v` == gv
                    if not c[g + "_explained"]:
                        every = cg.check(iid, kw, r_text, {d: "B" for d in used}, ctx)
                        c[g + "_explained_all_used"] = every is gv
            cons.append(c)
        out.append({
            "file": rel, "line": line_no, "uuid": resp["uuid"], "model": resp["model"], "run": resp["run"],
            "finish": resp["finish_reason"], "reasoning": reasoning,
            "r_extraction_failed": r_text is None,
            "extraction_differs_A": r_text is None or a_text != (r_text or "").strip(),
            "extraction_differs_B": r_text is None or b_text != (r_text or "").strip(),
            "A_reward": a_reward, "A_infra_error": any(a_det["instruction_errors"]),
            "A_session_reward": 0.0 if any(a_det["instruction_errors"]) else a_reward,
            "B_gate": all(c["B"] is True for c in cons if c["B"] is not None),
            "R_reward": float(r_text is not None and all(c["R"] for c in cons)),
            "cons": cons,
        })
    return out


def chunks():
    for path in sorted(PANEL.glob("*/*.jsonl")):
        rel = path.relative_to(PANEL).as_posix()
        lines = list(enumerate(path.open(encoding="utf-8").read().splitlines(), 1))
        for i in range(0, len(lines), 250):
            yield rel, lines[i:i + 250]


def main():
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    n = 0
    with ProcessPoolExecutor(max_workers=workers, initializer=_init) as ex, OUT.open("w", encoding="utf-8", newline="\n") as f:
        for result in ex.map(grade_chunk, chunks()):
            for rec in result:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n += 1
            if n % 2000 < 250:
                print("graded", n, flush=True)
    print("done", n)


if __name__ == "__main__":
    main()
