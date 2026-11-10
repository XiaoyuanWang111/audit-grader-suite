import re, difflib
import pandas as pd
df = pd.read_parquet("case/data/train-00000-of-00001.parquet")
def norm(s): return re.sub(r"\s+", " ", s).strip()
for key in ["8", "144", "145", "146", "147", "148", "150", "213", "286"]:
    row = df[df.key == key].iloc[0]
    p = row["prompt"]
    for iid, kw in zip(list(row["instruction_id_list"]), row["kwargs"]):
        for k in ("reference_text", "prompt_to_repeat"):
            v = kw.get(k)
            if v is None: continue
            print(f"key={key} {iid} {k}: len(ref)={len(v)} len(prompt)={len(p)} ws-normalized contained: {norm(v) in norm(p)}")
            if norm(v) not in norm(p):
                sm = difflib.SequenceMatcher(None, norm(v), norm(p), autojunk=False)
                for tag, i1, i2, j1, j2 in sm.get_opcodes():
                    if tag != "equal":
                        print("   ", tag, repr(norm(v)[i1:i2][:80]), "->", repr(norm(p)[j1:j2][:80]))
    if key == "8":
        i = p.find("4.0"); print("key 8 context:", repr(p[max(0,i-200):i+120]))
