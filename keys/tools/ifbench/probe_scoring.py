"""Reproduce the inputs that the IFBench rerun's score card rests on, on the grader, the reference and the audit's
replacement: the earlier audit's findings that the rerun did not report (so that "missed" means the defect is present
in the grader), the rerun's findings that have no fixture, and controls for the rerun's new findings.

The workspace is a folder that holds `case/` (rebuilt as `cases/ifbench/SOURCES.md` describes) and `audit/` (a copy
of `runs/ifbench-r3/`). The script also reads the `fixture_repro.json` that `fixture_repro.py` writes, for one
fixture's response. It writes only the output file. Run it with the case's Python environment.

Usage: <python> -B -X utf8 keys/tools/ifbench/probe_scoring.py <workspace> <fixture_repro.json> <out.json>
"""

import json
import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8")
if len(sys.argv) != 4:
    sys.exit(__doc__)
W, FIXTURE_REPRO, OUT = (Path(a).resolve() for a in sys.argv[1:4])
for sub in ("audit/tests", "audit/lib", "audit/replacement"):
    sys.path.insert(0, str(W / sub))
os.chdir(W)

import ifb

ifb.verify_pins()
import ifbench_contract as rep

ROWS = ifb.load_rows()
FIXTURES = {r["id"]: r for r in json.loads(FIXTURE_REPRO.read_text(encoding="utf-8"))["rows"]}

FLAG = "\U0001f1fa\U0001f1f8"
KEYCAP = "1️⃣"
TREE, DROP, GRIN = "\U0001f333", "\U0001f4a7", "\U0001f600"
LDQ, RDQ = "“", "”"


def first_row(iid, key=None):
    for row in ROWS:
        if iid in row["instruction_id_list"] and (key is None or str(row["key"]) == str(key)):
            j = row["instruction_id_list"].index(iid)
            return row, row["kwargs"][j] or {}
    raise KeyError((iid, key))


def run(tag, iid, response, key=None, kwargs=None, expect=None, note=""):
    row, row_kwargs = first_row(iid, key)
    kw = {k: v for k, v in (kwargs if kwargs is not None else row_kwargs).items() if v is not None}
    out = {
        "tag": tag,
        "check": iid,
        "key": row["key"],
        "kwargs": kw,
        "response": response,
        "expect_by_text": expect,
        "note": note,
    }
    for name in ("grader", "reference"):
        verdict, error = ifb.verdict(name, iid, kw, row["prompt"], response)
        out[name] = "EXC " + error if verdict is None else ("pass" if verdict else "fail")
    loose, _ = ifb.verdict("grader", iid, kw, row["prompt"], response, mode="loose")
    out["grader_loose"] = None if loose is None else ("pass" if loose else "fail")
    try:
        out["replacement"] = "pass" if rep.check(iid, kw, row["prompt"], response) else "fail"
    except Exception as exc:
        out["replacement"] = f"EXC {type(exc).__name__}: {exc}"
    return out


results = []
# Earlier-audit findings that the rerun did not report.
results += [
    run("F27 flag", "format:emoji", f"I love it. {FLAG}", expect="pass", note="a flag is one emoji"),
    run("F27 flag control", "format:emoji", f"I love it. {GRIN}", expect="pass"),
    run("F27 keycap", "format:emoji", f"Done. {KEYCAP}", expect="pass"),
    run("F27 emoji then letter", "format:emoji", f"Smile {GRIN}x", expect="fail", note="the sentence ends in a letter"),
    run("F32 curly quotes", "words:prime_lengths", f"{LDQ}Hi{RDQ}", expect="pass", note="Hi has length 2"),
    run("F32 control", "words:prime_lengths", "Hi", expect="pass"),
    run("F32 straight quotes", "words:prime_lengths", '"Hi"', expect="pass"),
    run(
        "F40 comma",
        "words:last_first",
        "Life needs extreme conditions. Conditions, such as heat, shape life.",
        expect="pass",
    ),
    run(
        "F40 control",
        "words:last_first",
        "Life needs extreme conditions. Conditions such as heat shape life.",
        expect="pass",
    ),
    run(
        "F42 list number",
        "words:words_position",
        "1. Colors vibrant fill a vibrant room.",
        kwargs={"keyword": "vibrant"},
        expect="pass",
        note="decision-dependent in the earlier key (are list numbers words?)",
    ),
    run(
        "F42 control",
        "words:words_position",
        "Colors vibrant fill a vibrant room.",
        kwargs={"keyword": "vibrant"},
        expect="pass",
    ),
    run("F43 emoji list labels", "format:emoji", f"1. Plant a tree. {TREE}\n2. Water it daily. {DROP}", expect="pass"),
    run("F43 emoji control", "format:emoji", f"Plant a tree. {TREE}\nWater it daily. {DROP}", expect="pass"),
    run(
        "F43 keyword third sentence",
        "sentence:keyword",
        "1. Cats purr.\n2. Dogs bark.\n3. Owls hoot.",
        kwargs={"N": 3.0, "word": "owls"},
        expect="pass",
        note="the third sentence is 'Owls hoot.'",
    ),
    run(
        "F43 keyword control",
        "sentence:keyword",
        "Cats purr. Dogs bark. Owls hoot.",
        kwargs={"N": 3.0, "word": "owls"},
        expect="pass",
    ),
]
# Rerun findings without a fixture.
results += [
    run("F-indent-blank-lines two blanks", "format:line_indent", "a\n\n\n  b\n    c", expect="pass"),
    run("F-indent-blank-lines one blank", "format:line_indent", "a\n\n  b\n    c", expect="pass"),
    run("F-indent-blank-lines control", "format:line_indent", "a\n  b\n    c", expect="pass"),
]
row, kw = first_row("custom:csv_quotes")
header = next((line for line in row["prompt"].splitlines() if "\t" in line), None)
results.append({"tag": "csv_quotes prompt head", "prompt_head": row["prompt"][:600]})
# Controls for the rerun's new findings.
africa = FIXTURES["custom:reverse_newline-a8b76fa4"]["response"]
plain = "\n".join(line.split(". ", 1)[1] for line in africa.splitlines())
results += [
    run("F-africa-numbering numbered", "custom:reverse_newline", africa, expect="pass"),
    run("F-africa-numbering plain", "custom:reverse_newline", plain, expect="pass"),
    run("F-lastfirst-quotes", "words:last_first", 'Saturn has "clouds." Clouds form ice.', expect="pass"),
    run("F-lastfirst-quotes period outside", "words:last_first", 'Saturn has "clouds". Clouds form ice.', expect="pass"),
    run(
        "F-japanese-skip-tokens hyphen at 5",
        "count:words_japanese",
        "One two three four - five six seven eight 日本",
        kwargs={"N": 5.0},
        expect="fail",
        note="the fifth word is '-' or 'five'; neither is Japanese",
    ),
    run(
        "F-japanese-skip-tokens control",
        "count:words_japanese",
        "One two three four five six seven eight nine 日本",
        kwargs={"N": 5.0},
        expect="fail",
    ),
    run(
        "F-noconsec-digits",
        "words:no_consecutive",
        "Open talk on 10 11 topics helps.",
        expect=None,
        note="are numbers words with a first letter?",
    ),
    run(
        "F-pronouns-determiners",
        "count:pronouns",
        "This book, that pen, these cups, those hats, and all bags are here.",
        kwargs={"N": 5.0},
        expect=None,
    ),
]
OUT.write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
for r in results:
    if "check" not in r:
        continue
    shown = r["response"] if len(r["response"]) <= 70 else r["response"][:67] + "..."
    print(
        f"{r['tag']:36s} {r['check']:24s} text={r['expect_by_text']!s:5s} grader={r['grader'][:40]:5s} "
        f"loose={r['grader_loose']} "
        f"ref={r['reference'][:40]:5s} repl={r['replacement'][:40]:5s} | {shown!a}"
    )
print("csv_quotes prompt head:", ascii(results[18]["prompt_head"][:400]) if "prompt_head" in results[18] else "")
