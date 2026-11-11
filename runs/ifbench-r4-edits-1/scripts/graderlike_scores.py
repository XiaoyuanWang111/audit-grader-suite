"""Replacement with the grader's readings: isolates the score effect of findings.

GRADERLIKE sets every decision entry to the reading the grader under audit
implements, where the grader's behavior corresponds to one of the table's
readings. Remaining differences from the grader are findings (or replacement
approximations); differences between this and the proposed readings are
decisions. Writes audit/work/graderlike.json.
"""
import collections
import json
import multiprocessing as mp

import common

GRADERLIKE = {
    "D-sentence": "punct", "D-paragraph": "line", "D-strip-ends": "keep", "D-pronoun-set": "broad",
    "D-punct-set": "grader6", "D-palindrome-distinct": "occurrences", "D-overlap-def": "char",
    "D-indent-min": "one", "D-section": "whole", "D-options-text": "exact", "D-csv-wrapper": "only",
    "D-verb-context": "can-be", "D-word-numbers": "include", "D-africa-complete": "order", "D-list-intro": "allow",
    "D-reverse-extra": "allow", "D-repeat-format": "loose", "D-sentence-type": "exclude", "D-balanced": "equal",
}


def work(path):
    import replacement as R
    path = common.pathlib.Path(path)
    folder, run = path.parent.name, path.stem
    rows = common.rows()
    stored = [json.loads(x) for x in (common.W / "audit" / "work" / "panel" / f"{folder}__{run}.jsonl").read_text(encoding="utf-8").splitlines()]
    out = dict(folder=folder, run=run, prompts=0, prompt_pass=0, checks=0, instr_pass=0, by_check={})
    bc = collections.defaultdict(collections.Counter)
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
        rec = json.loads(line)
        r = rows[str(rec["key"])]
        st = stored[i]
        vals = []
        for j, (check, kw) in enumerate(zip(r["instruction_id_list"], r["kwargs"])):
            v = False if st["extraction_failure"] else bool(R.grade(check, kw, r["prompt"], rec["response"], GRADERLIKE))
            vals.append(v)
            g = st["checks"][j]["gs"] is True
            bc[check]["n"] += 1
            bc[check]["gl_pass_rep_fail" if g and not v else "gl_fail_rep_pass" if v and not g else "same"] += 1
        out["prompts"] += 1
        out["prompt_pass"] += all(vals)
        out["checks"] += len(vals)
        out["instr_pass"] += sum(vals)
    out["by_check"] = {k: dict(v) for k, v in bc.items()}
    return out


if __name__ == "__main__":
    files = sorted(str(p) for p in (common.CASE / "panel").glob("*/*.jsonl"))
    with mp.Pool(6) as pool:
        res = pool.map(work, files)
    summ = json.load(open(common.W / "audit" / "work" / "panel_summary.json", encoding="utf-8"))
    per = collections.defaultdict(list)
    for r in res:
        per[r["folder"]].append(r)
    cfg_out = {}
    print(f"{'config':<44} {'grader':>7} {'repl-graderlike':>15} {'repl-proposed':>13} {'findings':>9} {'decisions':>9}")
    for cfg in sorted(per):
        gl = sum(x["prompt_pass"] / x["prompts"] for x in per[cfg]) / len(per[cfg])
        g = summ["per_config"][cfg]["gs"]["prompt_mean"]
        p = summ["per_config"][cfg]["rep"]["prompt_mean"]
        cfg_out[cfg] = dict(grader=g, graderlike=gl, proposed=p, findings_effect=gl - g, decisions_effect=p - gl)
        print(f"{cfg:<44} {g:>7.3f} {gl:>15.3f} {p:>13.3f} {gl - g:>+9.3f} {p - gl:>+9.3f}")
    tot = collections.Counter()
    bc = collections.defaultdict(collections.Counter)
    for r in res:
        tot.update({k: r[k] for k in ("prompts", "prompt_pass", "checks", "instr_pass")})
        for k, v in r["by_check"].items():
            bc[k].update(v)
    pooled = dict(prompt=tot["prompt_pass"] / tot["prompts"], instr=tot["instr_pass"] / tot["checks"])
    dis = sum(v["gl_pass_rep_fail"] + v["gl_fail_rep_pass"] for v in bc.values())
    print("pooled graderlike", pooled, "disagreements with grader", dis, dis / tot["checks"])
    (common.W / "audit" / "work" / "graderlike.json").write_text(json.dumps(dict(readings=GRADERLIKE, per_config=cfg_out, pooled=pooled,
                                                                                   disagreements=dis, by_check={k: dict(v) for k, v in bc.items()}), indent=1),
                                                                  encoding="utf-8", newline="\n")
    for k, v in sorted(bc.items(), key=lambda kv: -(kv[1]["gl_pass_rep_fail"] + kv[1]["gl_fail_rep_pass"]))[:20]:
        print(f"  {k:<34} grader-pass/repl-fail {v['gl_pass_rep_fail']:>5}  grader-fail/repl-pass {v['gl_fail_rep_pass']:>5}")
