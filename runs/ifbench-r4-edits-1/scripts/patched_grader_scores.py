"""Score the panel with the grader plus every finding patch from finding_probes.py.

For each check with a probe, the patched verdict replaces the grader's; other
checks keep the grader's verdict. Variant A excludes the APPROX start_verb probe,
variant B includes it. Extraction failures fail every check (contract G2) in
variant "+G2". The difference grader -> patched is the effect of the findings;
patched -> replacement is the effect of the decision readings plus checks whose
probe is replacement logic. Writes audit/work/patched_grader.json.
"""
import collections
import json

import common
import finding_probes as FP

PRIMARY = {}
for fid, check, fn, how in FP.PROBES:
    if fid in ("F-STYPE(0:0 only)",) or fid == "F-MARKUP":
        continue
    PRIMARY.setdefault(check, (fid, fn, how))

rows = common.rows()
order = common.row_list()
summ = json.load(open(common.W / "audit" / "work" / "panel_summary.json", encoding="utf-8"))
acc = collections.defaultdict(lambda: collections.Counter())
for f in sorted((common.CASE / "panel").glob("*/*.jsonl")):
    stem = f"{f.parent.name}__{f.stem}"
    stored = [json.loads(x) for x in (common.W / "audit" / "work" / "panel" / f"{stem}.jsonl").read_text(encoding="utf-8").splitlines()]
    for i, line in enumerate(f.read_text(encoding="utf-8").splitlines()):
        rec = json.loads(line)
        r = rows[order[i]]
        st = stored[i]
        vA, vB, vC = [], [], []
        for j, (check, kw) in enumerate(zip(r["instruction_id_list"], r["kwargs"])):
            g = st["checks"][j]["gs"] is True
            a = b = g
            if check in PRIMARY:
                fid, fn, how = PRIMARY[check]
                p = bool(rec["response"].strip()) and bool(fn(kw, r["prompt"], rec["response"]))
                b = p
                a = g if "APPROX" in how else p
            vA.append(a)
            vB.append(b)
            vC.append(False if st["extraction_failure"] else a)
        c = acc[f.parent.name]
        c["runs_x_prompts"] += 1
        c["A"] += all(vA)
        c["B"] += all(vB)
        c["C"] += all(vC)
out = {}
print(f"{'config':<44} {'grader':>7} {'patchedA':>9} {'patchedB':>9} {'A+G2':>7} {'repl':>7} {'find(A)':>8} {'rest':>7}")
tot = collections.Counter()
for cfg in sorted(acc):
    c = acc[cfg]
    n = c["runs_x_prompts"]
    g = summ["per_config"][cfg]["gs"]["prompt_mean"]
    rp = summ["per_config"][cfg]["rep"]["prompt_mean"]
    A, B, C = c["A"] / n, c["B"] / n, c["C"] / n
    out[cfg] = dict(grader=g, patched_A=A, patched_B=B, patched_A_G2=C, replacement=rp, findings_effect_A=A - g, rest=rp - A)
    tot.update(c)
    print(f"{cfg:<44} {g:>7.3f} {A:>9.3f} {B:>9.3f} {C:>7.3f} {rp:>7.3f} {A - g:>+8.3f} {rp - A:>+7.3f}")
pooled = {k: tot[k] / tot["runs_x_prompts"] for k in ("A", "B", "C")}
print("pooled", pooled)
(common.W / "audit" / "work" / "patched_grader.json").write_text(json.dumps(dict(per_config=out, pooled=pooled,
                                                                                    probes={k: v[0] + " / " + v[2] for k, v in PRIMARY.items()}), indent=1),
                                                                   encoding="utf-8", newline="\n")
