"""Reproduce a finding: print its exact input and the grader's verdict on it.

The grader is imported from the byte-identical copy under audit/work/pkgs/ (ifb.verify_pins checks
it against case/MANIFEST.sha256 first), because importing it from case/ creates folders there.
Verdicts are the grader's strict and loose functions as grader.py applies them, the reference's
strict function, and the replacement under the contract's proposed readings.

Run from W (Git Bash):
  .venv/Scripts/python.exe -B audit/scripts/repro.py F-subbullets-none     one finding, every input
  .venv/Scripts/python.exe -B audit/scripts/repro.py format:sub-bullets-68bc3978   one fixture
  .venv/Scripts/python.exe -B audit/scripts/repro.py --all                  one line per finding
NLTK_DATA is set by audit/lib/ifb.py.
"""
import hashlib
import json
import os
import re
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for p in (os.path.join(W, "audit", "tests"), os.path.join(W, "audit", "lib"), os.path.join(W, "audit", "replacement")):
    sys.path.insert(0, p)
import ifb  # noqa: E402
from fixtures_data import FIXTURES, ROWS  # noqa: E402
from fixtures_post_label import POST  # noqa: E402
import ifbench_contract as rep  # noqa: E402

NL = chr(10)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def kw_prompt(key, iid):
    row = ROWS[key]
    return dict(row["kwargs"][row["instruction_id_list"].index(iid)]), row["prompt"]


def word(v):
    return {True: "pass", False: "fail", None: "exception"}[v]


def verdicts(iid, kwargs, prompt, text):
    g, ge = ifb.verdict("grader", iid, kwargs, prompt, text)
    gl, _ = ifb.verdict("grader", iid, kwargs, prompt, text, mode="loose")
    r, re_ = ifb.verdict("reference", iid, kwargs, prompt, text)
    try:
        p = word(bool(rep.check(iid, kwargs, prompt, text)))
    except Exception as e:  # noqa: BLE001
        p = f"exception {type(e).__name__}"
    out = {"grader strict": word(g), "grader loose": word(gl), "reference strict": word(r), "replacement": p}
    if ge:
        out["grader strict"] += f" ({ge})"
    if re_:
        out["reference strict"] += f" ({re_})"
    return out


def show_input(iid, key, kwargs, text):
    print(f"  check: {iid}   dataset prompt key: {key}   kwargs: {json.dumps(kwargs, ensure_ascii=False)}")
    print(f"  response ({len(text)} characters, Python literal): {text!r}")


def show_fixture(f):
    tag = "   (post-label fixture, audit/tests/fixtures_post_label.py)" if f in POST else ""
    print(f"{f.grader or '(no finding)'}   fixture {f.id}{tag}")
    show_input(f.check, f.key, f.kwargs, f.response)
    v = verdicts(f.check, f.kwargs, f.prompt, f.response)
    print(f"  contract label: {f.label}")
    print("  " + "   ".join(f"{k}: {x}" for k, x in v.items()))
    return v


# ---- findings without a step 3 fixture -------------------------------------------------
KW_PASS = ("The door is blue. Bread and bread. Blue blue. Lamp lamp lamp lamp lamp. "
           "River river river river river river river.")
STAIRS1 = "Line one\n  Line two\n\n    Line three"
CSV_EMPTY = ('"StudentID"\t"Subject"\t"Grade"\t"Semester"\t"Score"\n"1"\t"Math"\t"A"\t"Fall"\t"90"\n'
             '"2"\t"Art"\t\t"Fall"\t"85"\n"3"\t"Music"\t"B"\t"Spring"\t"78"')
LOOSE = [
    ("format:sub-bullets", "126", "* Light drops\n* Temperature falls"),
    ("words:start_verb", "257", "Here is my answer.\nConsider an empire of pain."),
    ("count:keywords_multiple", "2", KW_PASS + "\nRiver."),
    ("count:numbers", "17", "In 2020 the team had 15 players.\nThat was 3 years ago."),
]
VARIANTS = ["the response", "every * removed", "first line removed", "last line removed",
            "first and last lines removed", "first line and every * removed",
            "last line and every * removed", "first and last lines and every * removed"]
STORED = ("Qwen__Qwen3-8B__thinking", "greedy", "234")  # an unclosed <think>; the grader passes words:palindrome


def special(fid):
    if fid == "F-indent-blank-lines":
        for label, text in (("one blank line between stairs", STAIRS1),
                            ("two blank lines between stairs", STAIRS1.replace(NL + NL, NL + NL + NL))):
            kw, pr = kw_prompt("74", "format:line_indent")
            print(f"F-indent-blank-lines   {label}")
            show_input("format:line_indent", "74", kw, text)
            print("  contract label: pass (blank lines are ignored)")
            print("  " + "   ".join(f"{k}: {x}" for k, x in verdicts("format:line_indent", kw, pr, text).items()))
        return True
    if fid == "F-csvquotes-indexerror":
        kw, pr = kw_prompt("275", "custom:csv_quotes")
        print("F-csvquotes-indexerror   header of prompt 275 and 3 data rows; the Grade field of row 2 is empty")
        show_input("custom:csv_quotes", "275", kw, CSV_EMPTY)
        print("  contract label: fail (the empty field is not enclosed in double quotes)")
        print("  " + "   ".join(f"{k}: {x}" for k, x in verdicts("custom:csv_quotes", kw, pr, CSV_EMPTY).items()))
        return True
    if fid == "F-loose-deletes-constrained":
        for iid, key, text in LOOSE:
            kw, pr = kw_prompt(key, iid)
            print(f"F-loose-deletes-constrained   {iid}")
            show_input(iid, key, kw, text)
            win = ifb.loose_winner("grader", iid, kw, pr, text)
            print("  contract label: fail")
            print("  " + "   ".join(f"{k}: {x}" for k, x in verdicts(iid, kw, pr, text).items())
                  + f"   loose variant that passes: {VARIANTS[win] if win is not None else 'none'}")
        return True
    if fid == "F-extract-unclosed":
        cfg, run, key = STORED
        path = os.path.join(W, "case", "panel", cfg, run + ".jsonl")
        with open(path, encoding="utf-8") as fh:
            rec = next(r for r in map(json.loads, fh) if str(r["key"]) == key)
        raw, resp = rec["raw_response"], rec["response"]
        print(f"F-extract-unclosed   stored record case/panel/{cfg}/{run}.jsonl, key {key}")
        print(f"  completion opens <think>: {'<think>' in raw}   closes it: {'</think>' in raw}   "
              f"finish_reason: {rec.get('finish_reason')}   graded `response` = {len(resp)} characters, "
              f"sha256 {hashlib.sha256(resp.encode('utf-8')).hexdigest()[:16]} (reasoning text, not printed)")
        row = ROWS[key]
        for iid, kw in zip(row["instruction_id_list"], row["kwargs"]):
            v = verdicts(iid, dict(kw), row["prompt"], resp)
            print(f"  {iid}: contract label: fail (G1 extraction failure)   grader strict: {v['grader strict']}   "
                  f"grader loose: {v['grader loose']}")
        return True
    if fid == "F-pin-1":
        print("F-pin-1   40-hex commit ids in case/TASK.md and case/panel/CONFIGS.md:")
        for rel in ("TASK.md", "panel/CONFIGS.md"):
            hits = [(n, line) for n, line in enumerate(open(os.path.join(W, "case", rel), encoding="utf-8"), 1)
                    if re.search(r"\b[0-9a-f]{40}\b", line)]
            if rel == "TASK.md":
                for n, line in hits:
                    print(f"  {rel}:{n}: {line.strip()[:90]}")
            else:
                print(f"  {rel}: {len(hits)} table rows, each the Hugging Face revision of a panel model")
        print("  none names a Marin or Evalchemy commit of the vendored grader")
        return True
    if fid == "F-pin-2":
        txt = open(os.path.join(W, "case", "panel", "CONFIGS.md"), encoding="utf-8").read()
        print("F-pin-2   case/panel/CONFIGS.md")
        print(f"  mentions of stop sequences ('stop sequence', 'stop='): {len(re.findall(r'stop sequence|stop=', txt, flags=re.I))}")
        for n, line in enumerate(txt.splitlines(), 1):
            if "not recorded" in line:
                print(f"  line {n}: {line[:110]}")
        return True
    if fid == "F-pin-3":
        src = open(os.path.join(W, "case", "grader", "IFBench", "instructions.py"), encoding="utf-8").read().splitlines()
        print("F-pin-3   case/grader/IFBench/instructions.py lines 26-32:")
        for n in range(26, 33):
            if src[n - 1].strip():
                print(f"  {n}: {src[n - 1]}")
        util = open(os.path.join(W, "case", "grader", "IFBench", "instructions_util.py"), encoding="utf-8").read().splitlines()
        calls = [n for n, l in enumerate(util, 1) if "nltk.download(" in l or l.strip() == "download_nltk_resources()"]
        print(f"  instructions_util.py: nltk.download calls at lines {calls[:-1]}, module-level call at line {calls[-1]}")
        ifb.grader_modules()
        import nltk
        print(f"  after importing the audit's copy: nltk.data.path[0] = {os.path.relpath(nltk.data.path[0], W)}")
        return True
    if fid == "F-pin-4":
        src = open(os.path.join(W, "case", "grader", "IFBench", "eval_instruct.py"), encoding="utf-8").read().splitlines()
        n = next(i for i, l in enumerate(src, 1) if "load_dataset(" in l and "import" not in l)
        print(f"F-pin-4   case/grader/IFBench/eval_instruct.py line {n}: {src[n - 1].strip()}")
        return True
    return False


SPECIAL = ["F-pin-1", "F-pin-2", "F-pin-3", "F-pin-4", "F-indent-blank-lines", "F-csvquotes-indexerror",
           "F-loose-deletes-constrained", "F-extract-unclosed"]


def main():
    ifb.verify_pins()
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    arg = sys.argv[1]
    if arg == "--all":
        seen = []
        for f in FIXTURES + POST:
            if f.grader.startswith("F-") and f.grader not in seen:
                seen.append(f.grader)
                v = verdicts(f.check, f.kwargs, f.prompt, f.response)
                print(f"{f.grader:28s} {f.id:44s} label {f.label:4s} grader {v['grader strict']:4s} "
                      f"reference {v['reference strict'].split(' ')[0]:4s} replacement {v['replacement']}")
        print(f"{len(seen)} findings with a fixture; without one: {', '.join(SPECIAL)}")
        return
    if special(arg):
        return
    fx = [f for f in FIXTURES + POST if f.id == arg or f.grader == arg]
    if not fx:
        sys.exit(f"no fixture or finding {arg}")
    for f in fx:
        show_fixture(f)


if __name__ == "__main__":
    main()
