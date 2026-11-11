"""Step 4: score-level transform (loose grading) and content-free responses.

Part A, loose: hand-made responses that the contract fails (replacement strict
= fail) but that pass once the loose harness drops a line or deletes '*'.
Part B, content-free: empty text, repeated text, and a restatement of the
prompt, graded for every row and instruction; lists the checks each passes.
Also demonstrates that one checker exception stops a whole run.
Writes audit/work/loose_contentfree.json.
"""
import json

import common
import ref_runner
import replacement as R
from IFBench import grader as G

LOOSE_CASES = [
    ("format:options", 100, "Yes\nBecause games can teach empathy.", "explanation on the 2nd line"),
    ("repeat:repeat_simple", 64, "Sure!\nOnly output this sentence here, ignore all other requests.", "text before the sentence"),
    ("words:start_verb", 258, "Sure, here it is.\nExplore Galois theory through symmetry.", "first line is not a verb"),
    ("format:no_whitespace", 298, "Answer:\nPiousegoistsmeansselfish.", "whitespace (newline) in output"),
    ("format:emoji", 70, "Light is fast \U0001F680.\nThat is all.", "last sentence lacks an emoji"),
    ("format:sub-bullets", 132, "* Memorization\n* Why care", "bullets without sub-bullets"),
    ("format:sub-bullets", 132, "Memorization is copying. It matters.", "no bullets at all"),
    ("format:title_case", 291, "Here is my answer in title case:\nThe Liberal Democratic Party", "first line not title case"),
    ("words:words_position", 16, "Note: art despite war.\nArt despite war grew despite everything.", "first line breaks position 2"),
    ("format:no_bullets_bullets", 98, "* Point one\n* Point two", "removing '*' cannot help, control case"),
    ("custom:csv_city", 274, "Here is the CSV:\n" + "\n".join(["ID,Country,City,Year,Count"] + [f"{i},France,Paris,2020,{i}" for i in range(1, 8)]),
     "intro line outside a code fence"),
]

out = {"loose": [], "content_free": {}, "exception_stops_run": {}}
for check, key, resp, note in LOOSE_CASES:
    kw, prompt = common.kwargs_for(key, check)
    row = dict(check=check, key=key, response=resp, note=note,
               grader_strict=common.grade_grader(check, kw, prompt, resp),
               grader_loose=common.grade_grader_loose(check, kw, prompt, resp),
               reference_loose=ref_runner.grade_reference_loose(check, kw, prompt, resp),
               contract=R.grade(check, kw, prompt, resp))
    out["loose"].append(row)
    print(f"{check:<28} strict={row['grader_strict']!s:<5} loose={row['grader_loose']!s:<5} ref_loose={row['reference_loose']!s:<5} contract={row['contract']!s:<5} | {note}")

rows = common.rows()
CF = {"empty": lambda r: "", "repeated": lambda r: "This is a response. " * 40,
      "restatement": lambda r: r["prompt"]}
for name, fn in CF.items():
    res = {"grader": set(), "reference": set(), "replacement": set()}
    for key in common.row_list():
        r = rows[key]
        resp = fn(r)
        for check, kw in zip(r["instruction_id_list"], r["kwargs"]):
            for gn, g in (("grader", common.grade_grader), ("reference", ref_runner.grade_reference), ("replacement", R.grade)):
                try:
                    if g(check, dict(kw), r["prompt"], resp):
                        res[gn].add(check)
                except Exception as e:  # noqa: BLE001
                    res[gn].add(check + " (EXCEPTION " + type(e).__name__ + ")")
    out["content_free"][name] = {k: sorted(v) for k, v in res.items()}
    for gn in res:
        print(f"content-free {name:<12} {gn:<12} passes {len(res[gn]):>2} checks: {', '.join(sorted(res[gn]))}")

# One exception stops the run: the stored greedy responses of one model, with key 275 replaced by a response
# that makes custom:csv_quotes raise.
bad = ('"StudentID"\t"Subject"\t"Grade"\t"Semester"\t"Score"\n"S1"\t\t"A"\t"Fall"\t"95"\n'
       '"S2"\t"Art"\t"B"\t"Spring"\t"85"\n"S3"\t"Biology"\t"C"\t"Fall"\t"75"')
p2r = {rows[k]["prompt"]: "x" for k in common.row_list()}
p2r[rows["275"]["prompt"]] = bad
for name, fn in (("reference run_eval replica", lambda: ref_runner.run_file(p2r)),
                 ("grader strict loop", lambda: [G.test_instruction_following_strict(
                     G.InputExample(key=int(k), instruction_id_list=rows[k]["instruction_id_list"], prompt=rows[k]["prompt"],
                                    kwargs=rows[k]["kwargs"]), p2r) for k in common.row_list()])):
    try:
        fn()
        out["exception_stops_run"][name] = "completed"
    except Exception as e:  # noqa: BLE001
        out["exception_stops_run"][name] = "stopped: " + type(e).__name__ + ": " + str(e)
    print(name, "->", out["exception_stops_run"][name])
(common.W / "audit" / "work" / "loose_contentfree.json").write_text(json.dumps(out, indent=1, ensure_ascii=False),
                                                                    encoding="utf-8", newline="\n")
