"""Print each instruction id's instruction sentence(s), deduplicated after digit normalization.

The template core is the longest common substring of two prompts of the id, with
digits generalized; each match is widened to sentence boundaries. Rows where the
core is not found are listed by number.

Usage: python audit/scripts/instr_sentences.py id ...   (no ids = all multi-row ids)
"""
import difflib
import json
import os
import re
import sys
from collections import OrderedDict

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROWS = [json.loads(l) for l in open(os.path.join(W, "audit", "frozen", "dataset_rows.jsonl"), encoding="utf-8")]


def nn(kw):
    return {k: v for k, v in kw.items() if v is not None}


def core(a, b):
    a2, b2 = re.sub(r"\d+", "0", a), re.sub(r"\d+", "0", b)
    sm = difflib.SequenceMatcher(None, a2, b2, autojunk=False)
    m = sm.find_longest_match(0, len(a2), 0, len(b2))
    return a2[m.a:m.a + m.size]


def main(argv):
    ids = argv or sorted({x for r in ROWS for x in r["instruction_id_list"]})
    for iid in ids:
        rows = [(i, r) for i, r in enumerate(ROWS) if iid in r["instruction_id_list"]]
        if len(rows) < 2:
            continue
        best = ""
        for a in range(min(4, len(rows))):
            for b in range(a + 1, len(rows)):
                c = core(rows[a][1]["prompt"], rows[b][1]["prompt"])
                if len(c) > len(best):
                    best = c
        best = best.strip()
        pat = re.escape(best).replace("0", r"\d+")
        sents = OrderedDict()
        missing = []
        for i, r in rows:
            p = r["prompt"]
            m = re.search(pat, p)
            if not m:
                missing.append(i)
                continue
            s, e = m.start(), m.end()
            while s > 0 and not (p[s - 1] in "\n" or (p[s - 2:s] in (". ", "? ", "! ") and s >= 2)):
                s -= 1
            while e < len(p) and p[e - 1] not in ".?!\n":
                e += 1
            sent = re.sub(r"\d+", "N", p[s:e].strip())
            sents.setdefault(sent, []).append(i)
        kws = [nn(r["kwargs"][r["instruction_id_list"].index(iid)]) for _, r in rows]
        print("=" * 6, iid, "n=", len(rows))
        for s, rs in sents.items():
            print("   S:", repr(s[:700]), rs)
        if missing:
            print("   core not found in rows", missing)
        print("   kwargs:", kws)


if __name__ == "__main__":
    main(sys.argv[1:])
