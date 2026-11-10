"""Count what the stored panel records already show (step 5, first paragraph).

Per configuration: responses, finish_reason counts, truncated (length) share,
raw completions containing '<think>' / '</think>', reasoning that never closes,
empty graded text, whether `response` matches the documented extraction rule,
prompt equality with the dataset, and the revision field.

Also writes audit/frozen/panel_files.sha256 (sha256 per run file).
Usage: python audit/scripts/panel_records.py
"""
import hashlib
import json
import os
from collections import Counter, defaultdict

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PANEL = os.path.join(W, "case", "panel")
ROWS = [json.loads(l) for l in open(os.path.join(W, "audit", "frozen", "dataset_rows.jsonl"), encoding="utf-8")]


def extract(raw):
    k = raw.rfind("</think>")
    if k < 0:
        return raw
    return raw[k + len("</think>"):].lstrip()


def main():
    shas = []
    tot = Counter()
    for cfg in sorted(os.listdir(PANEL)):
        d = os.path.join(PANEL, cfg)
        if not os.path.isdir(d):
            continue
        c = Counter()
        fins = Counter()
        revs = set()
        models = set()
        runs = sorted(os.listdir(d))
        for fn in runs:
            p = os.path.join(d, fn)
            shas.append((hashlib.sha256(open(p, "rb").read()).hexdigest(), f"{cfg}/{fn}"))
            lines = open(p, encoding="utf-8").read().splitlines()
            c["files"] += 1
            if len(lines) != 300:
                c["bad_linecount"] += 1
            for i, line in enumerate(lines):
                r = json.loads(line)
                c["n"] += 1
                fins[r["finish_reason"]] += 1
                revs.add(r["revision"])
                models.add(r["model"])
                raw, resp = r["raw_response"], r["response"]
                if r["prompt"] != ROWS[i]["prompt"]:
                    c["prompt_mismatch"] += 1
                if r.get("key") != ROWS[i]["key"]:
                    c["key_mismatch"] += 1
                if extract(raw) != resp:
                    c["extract_rule_mismatch"] += 1
                has_open, has_close = "<think>" in raw, "</think>" in raw
                c["has_think_open"] += has_open
                c["has_think_close"] += has_close
                if has_open and not has_close:
                    c["reasoning_never_closes"] += 1
                    if r["finish_reason"] == "length":
                        c["never_closes_and_length"] += 1
                if resp.strip() == "":
                    c["empty_graded_text"] += 1
                if r["finish_reason"] == "length":
                    c["length"] += 1
                if r["run"] != fn[:-6]:
                    c["run_field_mismatch"] += 1
        tot.update(c)
        print(f"{cfg}: files={c['files']} n={c['n']} finish={dict(fins)} length={c['length']} "
              f"think_open={c['has_think_open']} think_close={c['has_think_close']} never_closes={c['reasoning_never_closes']} "
              f"(length {c['never_closes_and_length']}) empty={c['empty_graded_text']} extract_mismatch={c['extract_rule_mismatch']} "
              f"prompt_mismatch={c['prompt_mismatch']} key_mismatch={c['key_mismatch']} run_mismatch={c['run_field_mismatch']} "
              f"badlines={c['bad_linecount']} models={sorted(models)} revs={sorted(revs)}")
    print("TOTAL", dict(tot))
    with open(os.path.join(W, "audit", "frozen", "panel_files.sha256"), "w", encoding="utf-8", newline="\n") as f:
        for h, rel in shas:
            f.write(f"{h}  {rel}\n")


if __name__ == "__main__":
    main()
