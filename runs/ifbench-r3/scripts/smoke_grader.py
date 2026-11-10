import sys, time
sys.path.insert(0, "audit/lib")
import ifb
ifb.verify_pins()
rows = ifb.load_rows()
g, gr = ifb.grader_modules()
rl, rr = ifb.reference_modules()
recs = [r for c, run, i, r in ifb.iter_panel(cfgs=["Qwen__Qwen2.5-7B-Instruct"], runs=["greedy"])]
t = time.time()
mine = []
for row, rec in zip(rows, recs):
    for iid, kw in zip(row["instruction_id_list"], row["kwargs"]):
        mine.append(ifb.verdict("grader", iid, kw, row["prompt"], rec["response"])[0])
t1 = time.time() - t
# real grader function
real = []
for row, rec in zip(rows, recs):
    inp = g.InputExample(key=int(row["key"]), instruction_id_list=row["instruction_id_list"], prompt=row["prompt"], kwargs=[dict(k) for k in row["kwargs"]])
    out = g.test_instruction_following_strict(inp, {row["prompt"]: rec["response"]})
    real.extend(out.follow_instruction_list)
print("instructions", len(mine), "agree with real grader function", sum(a == b for a, b in zip(mine, real)), "time per instruction ms", round(1000 * t1 / len(mine), 2))
print("strict instruction accuracy", sum(mine) / len(mine))
# loose
t = time.time()
loose = []
for row, rec in zip(rows, recs):
    for iid, kw in zip(row["instruction_id_list"], row["kwargs"]):
        loose.append(ifb.verdict("grader", iid, kw, row["prompt"], rec["response"], mode="loose")[0])
realL = []
for row, rec in zip(rows, recs):
    inp = g.InputExample(key=int(row["key"]), instruction_id_list=row["instruction_id_list"], prompt=row["prompt"], kwargs=[dict(k) for k in row["kwargs"]])
    realL.extend(g.test_instruction_following_loose(inp, {row["prompt"]: rec["response"]}).follow_instruction_list)
print("loose agree", sum(a == b for a, b in zip(loose, realL)), "loose acc", sum(loose) / len(loose), "time", round(time.time() - t, 1))
# reference strict via its own function
refv = []
for row, rec in zip(rows, recs):
    inp = rl.InputExample(key=int(row["key"]), instruction_id_list=row["instruction_id_list"], prompt=row["prompt"], kwargs=[dict(k) for k in row["kwargs"]])
    refv.extend(rl.test_instruction_following_strict(inp, {row["prompt"]: rec["response"]}).follow_instruction_list)
mineR = []
for row, rec in zip(rows, recs):
    for iid, kw in zip(row["instruction_id_list"], row["kwargs"]):
        mineR.append(ifb.verdict("reference", iid, kw, row["prompt"], rec["response"])[0])
print("reference: mine vs real function agree", sum(a == b for a, b in zip(mineR, refv)), "ref strict acc", sum(refv) / len(refv), "grader vs ref disagreements", sum(a != b for a, b in zip(mine, refv)))
