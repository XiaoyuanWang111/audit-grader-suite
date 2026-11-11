"""Locate panel rows where a grader raised, and print the traceback for the replacement."""
import json
import traceback

import common
import replacement as R

for f in sorted((common.W / "audit" / "work" / "panel").glob("*.jsonl")):
    for i, line in enumerate(f.read_text(encoding="utf-8").splitlines()):
        e = json.loads(line)
        if "errors" in e:
            folder, run = f.stem.rsplit("__", 1)
            print(f.stem, "key", e["key"], e["errors"])
            rec = json.loads((common.CASE / "panel" / folder / f"{run}.jsonl").read_text(encoding="utf-8").splitlines()[i])
            r = common.rows()[e["key"]]
            print("  response length", len(rec["response"]), "excerpt", repr(rec["response"][:120]))
            for check, kw in zip(r["instruction_id_list"], r["kwargs"]):
                try:
                    R.grade(check, kw, r["prompt"], rec["response"])
                except Exception:  # noqa: BLE001
                    print("  ", check, traceback.format_exc().splitlines()[-6:])
