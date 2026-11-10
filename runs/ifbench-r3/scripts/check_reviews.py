"""Step 6.4: check the two reviewers' label files before they are joined with the key.

Checks, for each reviewer: the file's sha256 equals the one in audit/frozen/reviews/README.md;
458 lines; each case of cases.jsonl exactly once; exactly the five fields; valid values; lines in
the order of the reviewer's batch files; reasons of at most 40 words. Prints verdict, lean and
confidence counts. Reads only; writes nothing.

Run from W:  .venv/Scripts/python.exe -B audit/scripts/check_reviews.py
"""
import collections
import glob
import hashlib
import json
import os
import re
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
R1 = os.path.join(W, "audit", "frozen", "review_round1")
REV = os.path.join(W, "audit", "frozen", "reviews")
FIELDS = {"case_id", "verdict", "lean", "confidence", "reason"}


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def main():
    readme = open(os.path.join(REV, "README.md"), encoding="utf-8").read()
    with open(os.path.join(R1, "cases.jsonl"), encoding="utf-8") as fh:
        case_ids = {json.loads(l)["case_id"] for l in fh if l.strip()}
    ok = True
    for who in ("A", "B"):
        path = os.path.join(REV, f"review_{who}.jsonl")
        h = sha(path)
        listed = re.search(rf"`review_{who}\.jsonl` \| (\d+) \| ([0-9a-f]{{64}})", readme)
        hash_ok = bool(listed) and listed.group(2) == h
        with open(path, encoding="utf-8") as fh:
            raw = [l for l in fh.read().split("\n") if l.strip()]
        rows = [json.loads(l) for l in raw]
        ids = [r.get("case_id") for r in rows]
        dup = [i for i, n in collections.Counter(ids).items() if n > 1]
        missing = sorted(case_ids - set(ids))
        unknown = sorted(set(ids) - case_ids)
        bad_fields = [r.get("case_id") for r in rows if set(r) != FIELDS]
        bad_values = [r.get("case_id") for r in rows
                      if r.get("verdict") not in ("pass", "fail", "ambiguous")
                      or r.get("lean") not in ("pass", "fail")
                      or r.get("confidence") not in ("high", "medium", "low")
                      or not isinstance(r.get("reason"), str) or not r.get("reason").strip()]
        # a definite verdict must equal the lean
        lean_mismatch = [r["case_id"] for r in rows if r.get("verdict") in ("pass", "fail") and r["verdict"] != r.get("lean")]
        long_reasons = [(r["case_id"], len(r["reason"].split())) for r in rows if len(str(r.get("reason", "")).split()) > 40]
        batch_order = []
        for b in sorted(glob.glob(os.path.join(R1, f"batches_{who}", f"batch_{who}*.md"))):
            batch_order += re.findall(r"^CASE ID: (R1-[0-9a-f]{5})\s*$", open(b, encoding="utf-8").read(), flags=re.M)
        order_ok = ids == batch_order
        print(f"reviewer {who}: sha256 {h[:12]} {'matches README' if hash_ok else 'DIFFERS FROM README'}; "
              f"{len(rows)} lines; duplicates {len(dup)}; missing {len(missing)}; unknown {len(unknown)}; "
              f"wrong field set {len(bad_fields)}; invalid values {len(bad_values)}; "
              f"definite verdict != lean {len(lean_mismatch)}; reasons over 40 words {len(long_reasons)}; "
              f"order equals batch order: {order_ok} ({len(batch_order)} ids in batches)")
        for k in ("verdict", "lean", "confidence"):
            c = collections.Counter(r[k] for r in rows)
            print(f"  {k}: " + ", ".join(f"{v} {n}" for v, n in sorted(c.items())))
        if long_reasons:
            print("  over 40 words:", long_reasons[:10])
        if lean_mismatch:
            print("  verdict != lean:", lean_mismatch[:10])
        ok &= hash_ok and len(rows) == 458 and not (dup or missing or unknown or bad_fields or bad_values) and order_ok
    print("all checks passed" if ok else "SOME CHECKS FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
