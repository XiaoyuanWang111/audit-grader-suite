"""Counterexamples cited in AUDIT.md, with the verdicts the report states.

python scripts/report_cases.py verify    -> runs every case, prints OK/MISMATCH per case
python scripts/report_cases.py commands  -> prints the Git Bash command of every case (for AUDIT.md)
Each case: (finding id, kind, args, expected) where expected maps A/B/C to the stated verdict:
A = grader A (SkyRL checker or row reward), B = grader B (curation gate), C = contract.
"""
from __future__ import annotations

import json
import shlex
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
W = HERE.parents[1]
sys.path.insert(0, str(HERE))
import fixture_lib as fl  # noqa: E402
import graders as g  # noqa: E402

N = "null"
CASES = [
    # pipeline
    ("G1", "check", ["punctuation:no_comma", N, "Okay the user wants a short answer so I will think about it", "--reasoning"], {"A": "pass", "B": "pass", "C": "fail"}),
    ("G2", "check", ["keywords:existence", '{"keywords": ["tag"]}', "Write the <think> tag before your notes."], {"A": "fail", "B": "fail", "C": "pass"}),
    ("G3", "check", ["length_constraints:nth_paragraph_first_word", '{"num_paragraphs": 2, "nth_paragraph": 3, "first_word": "history"}', "History is long.\n\nHistory is fun.", "--runs", "30"], {"A": "some", "B": "fail", "C": "fail"}),
    ("G4", "check", ["last_word:last_word_answer", '{"last_word": "hello"}', " "], {"A": "exception", "B": "fail", "C": "fail"}),
    ("D-empty", "row", ["eb817d5f-9f71-4bac-9f5e-9863c5e3957a", ""], {"A": "1.0", "B": "failed", "C": "0.0"}),
    # grader A
    ("A-F1", "check", ["keywords:word_once", '{"keyword": "fix"}', "Fix it now and fix it well."], {"A": "fail", "B": "fail", "C": "pass"}),
    ("A-F1", "check", ["keywords:word_once", '{"keyword": "fix"}', "Let me fix the prefix."], {"A": "fail", "B": "pass", "C": "pass"}),
    ("A-F2", "check", ["keywords:word_count_different_numbers", '{"keyword": "box", "frequency": 2, "relation": "less than"}', "A box and another box."], {"A": "fail", "B": "fail", "C": "pass"}),
    ("A-F2", "check", ["keywords:word_count_different_numbers", '{"keyword": "box", "frequency": 2, "relation": "less than"}', "No crates here."], {"A": "pass", "B": "pass", "C": "fail"}),
    ("A-F3", "check", ["first_word:first_word_answer", '{"first_word": "development"}', "Development, as a concept, matters."], {"A": "fail", "B": "pass", "C": "pass"}),
    ("A-F3", "check", ["length_constraints:nth_paragraph_first_word", '{"num_paragraphs": 2, "nth_paragraph": 2, "first_word": "if"}', "Cats are nice.\n\nIf: you like dogs, fine."], {"A": "fail", "B": "pass", "C": "pass"}),
    ("A-F4", "check", ["keywords:keyword_specific_position", '{"keyword": "shot", "n": 2, "m": 3}', "I went out. Then, the shot came."], {"A": "fail", "B": "pass", "C": "pass"}),
    ("A-F4", "check", ["keywords:keyword_specific_position", '{"keyword": "repeat", "n": 1, "m": 1}', "Repeat after me. Good."], {"A": "fail", "B": "pass", "C": "pass"}),
    ("A-F5", "check", ["count:count_unique", N, "Apples, pears, plums."], {"A": "fail", "B": "judge", "C": "pass"}),
    ("A-F6", "check", ["count:counting_composition", '{"n_sent": 3, "n_words": 2}', "Birds sing. Cats sleep. Dogs run.\n* * *\nRain falls. Wind blows. Trees sway.\n* * *\nKids play. Parents watch. Time flies."], {"A": "fail", "B": "pass", "C": "pass"}),
    ("A-F7", "check", ["detectable_format:bigram_wrapping", N, "<<I am>> home"], {"A": "pass", "B": "judge", "C": "fail"}),
    ("A-F7", "check", ["detectable_format:bigram_wrapping", N, "Hello"], {"A": "pass", "B": "judge", "C": "fail"}),
    ("A-F8", "check", ["detectable_format:constrained_response", N, "My answer is yes. My answer is no."], {"A": "pass", "B": "fail", "C": "fail"}),
    ("A-F9", "check", ["detectable_format:multiple_sections", '{"num_sections": 2, "section_spliter": "SECTION"}', "SECTION 1\nCats are great; see SECTION 2 for dogs."], {"A": "pass", "B": "pass", "C": "fail"}),
    ("A-F10", "check", ["detectable_format:number_bullet_lists", '{"num_bullets": 2}', "* Apples.\n* Bananas.\n\n---\n\nThat is all."], {"A": "fail", "B": "pass", "C": "pass"}),
    ("A-F10", "check", ["detectable_format:number_bullet_lists", '{"num_bullets": 2}', "*Note* the list:\n* Apples.\n* Bananas."], {"A": "fail", "B": "pass", "C": "pass"}),
    ("A-F11", "check", ["detectable_format:square_brackets", N, "[I] [like] [cats]."], {"A": "fail", "B": "pass", "C": "pass"}),
    ("A-F12", "check", ["keywords:no_adjacent_consecutive", N, "(apple) banana split."], {"A": "pass", "B": "pass", "C": "fail"}),
    ("A-F12", "check", ["keywords:no_adjacent_consecutive", N, "Pick 1, 2 or 9"], {"A": "fail", "B": "pass", "C": "pass"}),
    ("A-F13", "check", ["keywords:palindrome", N, "Cats run - dogs walk."], {"A": "pass", "B": "fail", "C": "fail"}),
    ("A-F14", "check", ["detectable_content:postscript", '{"postscript_marker": "P.S."}', "Ship the parcel with U.P.S. today."], {"A": "pass", "B": "fail", "C": "fail"}),
    ("A-F15", "check", ["language:response_language", '{"language": "fr"}', "12345 67890"], {"A": "pass", "B": "judge", "C": "fail"}),
    ("A-F16", "check", ["length_constraints:number_paragraphs", '{"num_paragraphs": 2}', "***Cats*** are nice and dogs are loyal."], {"A": "pass", "B": "fail", "C": "fail"}),
    ("A-F17", "check", ["first_word:first_word_sent", '{"first_word": "peace"}', "1. Peace is good. Peace is calm."], {"A": "fail", "B": "fail", "C": "pass"}),
    ("A-F18", "check", ["copy:repeat_phrase", '{"phrase": "Laughter is the best medicine", "small_n": 2}', "Laughter is the best medicine. Laughter is our best medicine."], {"A": "pass", "B": "fail", "C": "fail"}),
    ("A-F19", "check", ["change_case:english_capital", N, "I LIKE CATS AND DOGS VERY MUCH."], {"A": "fail", "B": "pass", "C": "pass"}),
    ("A-F20", "check", ["length_constraints:number_sentences", '{"num_sentences": 3, "relation": "at least"}', "我很好。你呢？他也很好。"], {"A": "fail", "B": "fail", "C": "pass"}),
    ("A-F21", "check", ["count:lowercase_counting", '{"N": 2}', "<b>I</b> like it"], {"A": "fail", "B": "pass", "C": "pass"}),
    ("A-F22", "check", ["count:count_unique", N, "**Every** word here appears once."], {"A": "fail", "B": "judge", "C": "pass"}),
    # grader B
    ("B-F1", "check", ["copy:repeat_phrase", '{"phrase": "Laughter is the best medicine", "small_n": 2}', "Laughter is a best medicine. Laughter is our best medicine."], {"A": "pass", "B": "fail", "C": "pass"}),
    ("B-F1", "check", ["copy:repeat_phrase", '{"phrase": "Laughter is the best medicine", "small_n": 2}', "Laughter is the best medicine. Laughter is the best medicine."], {"A": "fail", "B": "pass", "C": "fail"}),
    ("B-F2", "check", ["count:lowercase_counting", '{"N": 2}', "the the the end"], {"A": "fail", "B": "pass", "C": "fail"}),
    ("B-F2", "check", ["count:lowercase_counting", '{"N": 2}', "Hello World"], {"A": "pass", "B": "fail", "C": "pass"}),
    ("B-F3", "check", ["keywords:no_adjacent_consecutive", N, "A big dog."], {"A": "fail", "B": "pass", "C": "fail"}),
    ("B-F3", "check", ["keywords:no_adjacent_consecutive", N, "Tom ate ate cake."], {"A": "pass", "B": "fail", "C": "pass"}),
    ("B-F4", "check", ["length_constraints:number_paragraphs", '{"num_paragraphs": 2}', "Cats are nice.\n***\nDogs are loyal."], {"A": "pass", "B": "fail", "C": "pass"}),
    ("B-F4", "check", ["length_constraints:number_paragraphs", '{"num_paragraphs": 2}', "Cats are nice.\n\nDogs are loyal."], {"A": "fail", "B": "pass", "C": "fail"}),
    ("B-F5", "check", ["paragraphs:paragraphs", "{}", "Cats.\n***\nDogs.\n***\nBirds."], {"A": "fail", "B": "pass", "C": "fail"}),
    ("B-F5", "check", ["paragraphs:paragraphs2", "{}", "Cats.\n\nDogs.\n\nBirds."], {"A": "fail", "B": "pass", "C": "fail"}),
    ("B-F6", "check", ["detectable_format:square_brackets", N, "[I] like cats."], {"A": "fail", "B": "pass", "C": "fail"}),
    ("B-F7", "check", ["count:counting_composition", '{"n_sent": 3, "n_words": 2}', "Birds sing. Cats sleep. Dogs run."], {"A": "fail", "B": "pass", "C": "fail"}),
    ("B-F8", "check", ["keywords:start_end", N, "Hello world and hello."], {"A": "fail", "B": "pass", "C": "fail"}),
    ("B-F9", "check", ["startend:quotation", N, "'Hello there.'"], {"A": "fail", "B": "pass", "C": "fail"}),
    ("B-F10", "check", ["length_constraints:number_words", '{"num_words": 5, "relation": "at least"}', "Привет как дела у тебя"], {"A": "pass", "B": "fail", "C": "pass"}),
    ("B-F10", "check", ["first_word:first_word_answer", '{"first_word": "development"}', "Привет development"], {"A": "fail", "B": "pass", "C": "fail"}),
    ("B-F11", "check", ["length_constraints:number_sentences", '{"num_sentences": 3, "relation": "at least"}', "Dr. Smith runs. You walk."], {"A": "fail", "B": "pass", "C": "fail"}),
    ("B-F12", "check", ["keywords:palindrome", N, "A man, a plan, a canal: Panama!"], {"A": "pass", "B": "fail", "C": "pass"}),
    ("B-F12", "check", ["keywords:palindrome", N, "Cats run.\n\n---\n\nDogs walk."], {"A": "pass", "B": "pass", "C": "fail"}),
    ("B-F13", "check", ["detectable_format:number_highlighted_sections", '{"num_highlights": 1}', "Intro.\n\n* * *\n\nEnd."], {"A": "fail", "B": "pass", "C": "fail"}),
    ("B-F14", "check", ["detectable_format:title", N, "<< >>\nIt was fine."], {"A": "fail", "B": "pass", "C": "fail"}),
    ("B-F15", "check", ["detectable_format:json_format", N, '```json {"answer": "Paris"} ```'], {"A": "pass", "B": "fail", "C": "pass"}),
]


def run(kind, args):
    args = list(args)
    reasoning = "--reasoning" in args
    if reasoning:
        args.remove("--reasoning")
    runs = 1
    if "--runs" in args:
        i = args.index("--runs")
        runs = int(args[i + 1])
        del args[i:i + 2]
    out = {}
    if kind == "check":
        iid, kw, resp = args[0], json.loads(args[1]), args[2]
        res = [fl.verdict_skyrl(iid, kw, resp) for _ in range(runs)]
        if res[0][1]:
            out["A"] = "exception"
        elif runs > 1:
            k = sum(bool(v) for v, _ in res)
            out["A"] = "some" if 0 < k < runs else ("pass" if k == runs else "fail")
        else:
            out["A"] = "pass" if res[0][0] else "fail"
        v, _ = fl.verdict_curation(iid, kw, resp)
        out["B"] = "judge" if v is None else ("pass" if v else "fail")
        out["C"] = "pass" if fl.verdict_replacement(iid, kw, resp, reasoning) else "fail"
    else:
        uuid, resp = args
        for line in (W / "case/data/rlvr1_instruction_following.jsonl").open(encoding="utf-8"):
            rec = json.loads(json.loads(line)["extra_info"]["nemotron_ultra"]["record_json"])
            if rec["uuid"] == uuid:
                break
        out["A"] = str(g.skyrl_row(resp, rec)["reward"])
        out["B"] = "passed" if g.curation_row(resp, rec)["gate_passed"] else "failed"
        out["C"] = str(float(all(fl.cg.grade_constraint(i, k, resp) for i, k in zip(rec["instruction_id_list"], rec["kwargs"]))))
    return out


def bash_quote(s):
    if "\n" in s or "'" in s:
        return "$'" + s.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n") + "'"
    return shlex.quote(s) if s else "''"


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "verify"
    if mode == "script":
        # A shell script that runs every report command as printed in AUDIT.md, for check_commands.py.
        out = ["#!/usr/bin/env bash", "cd \"$(dirname \"$0\")/..\"",
               'export NLTK_DATA="<W>/case/deps/nltk_data"',
               "export PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8", "PY=../.venv/Scripts/python.exe"]
        for fid, kind, args, expected in CASES:
            cmd = f"$PY scripts/repro.py {kind} " + " ".join(a if a.startswith("--") or a.isdigit() else bash_quote(a) for a in args)
            out.append(f"echo '== {fid} ' {shlex.quote(json.dumps(expected))}")
            out.append(cmd + " 2>/dev/null")
        Path(W / "audit/work/report_commands.sh").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
        print("wrote audit/work/report_commands.sh")
        sys.exit(0)
    bad = 0
    for fid, kind, args, expected in CASES:
        if mode == "commands":
            print(f"{fid}: $PY scripts/repro.py {kind} " + " ".join(a if a.startswith("--") or a.isdigit() else bash_quote(a) for a in args))
            continue
        got = run(kind, args)
        ok = all(got[k] == v for k, v in expected.items())
        bad += not ok
        print(("OK       " if ok else "MISMATCH ") + fid, got if not ok else "")
    if mode == "verify":
        print(f"{len(CASES) - bad} of {len(CASES)} cases print what the report states")
