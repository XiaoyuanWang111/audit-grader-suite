"""For every constraint, check whether the requirement text that its kwargs
predict (the main template per id, from survey_templates.py) occurs in the
prompt. Prints per-id counts of misses and a few miss excerpts.

Data only; no grader code.
"""
import collections
import json
import pathlib
import re

W = pathlib.Path(__file__).resolve().parents[2]
DATA = W / "case" / "data" / "rlvr1_instruction_following.jsonl"
T = json.loads((W / "audit" / "out" / "templates.json").read_text(encoding="utf-8"))

LANG = {}


def render(template, kw):
    out = template
    for k, v in kw.items():
        if isinstance(v, list):
            v = repr(v)
        out = out.replace("{" + k + "}", str(v))
    return out


def main():
    rows = [json.loads(l) for l in DATA.open(encoding="utf-8")]
    miss = collections.Counter()
    tot = collections.Counter()
    ex = collections.defaultdict(list)
    for row in rows:
        text = row["prompt"][0]["content"]
        rec = json.loads(row["extra_info"]["nemotron_ultra"]["record_json"])
        for iid, kw in zip(rec["instruction_id_list"], rec["kwargs"]):
            kw = {k: v for k, v in (kw or {}).items() if v is not None}
            tot[iid] += 1
            if iid == "language:response_language":
                ok = re.search(r"Your ENTIRE response should be in \w+ language, no other language is allowed", text)
                if not ok:
                    miss[iid] += 1
                    ex[iid].append(text[-200:])
                continue
            temps = T[iid]["templates"]
            if not temps:
                continue
            main_t = temps[0][0].rstrip(".").split("\n")[0]
            r = render(main_t, kw)
            alt = None
            if iid in ("length_constraints:nth_paragraph_first_word",):
                alt = render(main_t.replace("{num_paragraphs}", "{nth_paragraph}"), kw)
            if r in text or (alt and alt in text):
                continue
            miss[iid] += 1
            if len(ex[iid]) < 3:
                ex[iid].append({"kw": kw, "expect": r[:160], "tail": text[-260:]})
    for iid in sorted(tot):
        print(f"{iid}: {tot[iid]} constraints, {miss[iid]} without the main template text")
        for e in ex[iid][:2]:
            print("    ", json.dumps(e, ensure_ascii=False)[:600])


if __name__ == "__main__":
    main()
