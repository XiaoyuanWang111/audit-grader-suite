"""Step 5, records first: what the stored panel already shows, before grading.

Counts per configuration: responses, key/prompt alignment with the dataset,
length-truncated completions, thinking-on completions with no </think>
(extraction failures), thinking-off completions containing think tags, empty
graded text, and graded text with trailing whitespace. Also checks that
`response` equals the CONFIGS.md extraction rule applied to `raw_response`.
Writes audit/work/panel_facts.json.
"""
import collections
import json
import pathlib

import common

rows = common.rows()
order = common.row_list()
files = sorted((common.CASE / "panel").glob("*/*.jsonl"))
facts = collections.defaultdict(collections.Counter)
example_ids = {}
for f in files:
    folder = f.parent.name
    lines = [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines()]
    facts[folder]["files"] += 1
    if len(lines) != 300:
        facts[folder]["files_not_300"] += 1
    for i, r in enumerate(lines):
        c = facts[folder]
        c["responses"] += 1
        if str(r["key"]) != order[i] or r["prompt"] != rows[order[i]]["prompt"]:
            c["misaligned"] += 1
        if r["finish_reason"] == "length":
            c["truncated_length"] += 1
        raw = r["raw_response"]
        expect = raw.rsplit("</think>", 1)[1].lstrip() if "</think>" in raw else raw
        if r["response"] != expect:
            c["response_not_extraction_rule"] += 1
        if folder.endswith("__thinking") and "</think>" not in raw:
            c["extraction_failure_no_close"] += 1
            if r["finish_reason"] == "length":
                c["extraction_failure_and_truncated"] += 1
        if not folder.endswith("__thinking") and ("<think>" in raw or "</think>" in raw):
            c["thinking_off_with_think_tag"] += 1
        if not r["response"].strip():
            c["empty_graded_text"] += 1
        if r["response"] != r["response"].rstrip():
            c["trailing_whitespace"] += 1
        if r["response"].endswith("\n"):
            c["trailing_newline"] += 1
out = {k: dict(v) for k, v in sorted(facts.items())}
(common.W / "audit" / "work" / "panel_facts.json").write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
tot = collections.Counter()
for k, v in out.items():
    tot.update(v)
    print(k, {a: b for a, b in v.items() if a not in ("files",)})
print("TOTAL", dict(tot))
