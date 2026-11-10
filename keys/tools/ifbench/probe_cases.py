"""Probe the IFBench rerun's three graders on a few exact inputs, to settle the hand check of the review cases that no
listed decision explains (format:emoji, format:quotes, format:thesis, count:numbers, count:words_japanese).

The workspace is a folder that holds `case/` (rebuilt as `cases/ifbench/SOURCES.md` describes) and `audit/` (a copy
of `runs/ifbench-r3/`). The script imports the audit's loader (`audit/lib/ifb.py`) and its replacement grader with
bytecode writing off, so it writes nothing. Prints verdicts and counts only. Run it with the case's Python environment.

Usage: <python> -B -X utf8 keys/tools/ifbench/probe_cases.py <workspace>
"""

import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding="utf-8")
if len(sys.argv) != 2:
    sys.exit(__doc__)
W = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(W / "audit" / "lib"))
sys.path.insert(0, str(W / "audit" / "replacement"))

import ifb  # sets NLTK_DATA before nltk is imported
import ifbench_contract as rep

ROUND = W / "audit" / "frozen" / "review_round1"
shown = {}
for line in (ROUND / "review_cases.jsonl").read_text(encoding="utf-8").splitlines():
    if line.strip():
        record = json.loads(line)
        shown[record["case_id"]] = record
key = {}
for line in (ROUND / "key.jsonl").read_text(encoding="utf-8").splitlines():
    if line.strip():
        record = json.loads(line)
        key[record["case_id"]] = record
rows = {row["key"]: row for row in ifb.load_rows()}

FLAG = "\U0001f1fa\U0001f1f8"
PARTY = "\U0001f389"
KEYCAP = "1️⃣"


def verdicts(check: str, kwargs: dict, prompt: str, response: str) -> str:
    grader = ifb.verdict("grader", check, kwargs, prompt, response)[0]
    loose = ifb.verdict("grader", check, kwargs, prompt, response, mode="loose")[0]
    reference = ifb.verdict("reference", check, kwargs, prompt, response)[0]
    replacement = rep.check(check, kwargs, prompt, response)
    return f"grader {grader!s:5} loose {loose!s:5} reference {reference!s:5} replacement {replacement!s:5}"


def case_inputs(case: str) -> tuple[str, dict, str, str]:
    record = key[case]
    row = rows[record["key"]]
    j = record["j"]
    assert row["instruction_id_list"][j] == record["check"], (case, row["instruction_id_list"], record["check"])
    return record["check"], row["kwargs"][j], row["prompt"], shown[case]["response"]


print("=== format:emoji, case R1-cab3d (S3): the response as reviewed, then the same with the flag replaced")
check, kwargs, prompt, response = case_inputs("R1-cab3d")
print(
    f"   stored verdicts: grader {key['R1-cab3d']['grader']}, replacement {key['R1-cab3d']['replacement']}; "
    f"flag emoji in the response: {response.count(FLAG)}"
)
print("   as reviewed:           ", verdicts(check, kwargs, prompt, response))
print("   flag -> party popper:  ", verdicts(check, kwargs, prompt, response.replace(FLAG, PARTY)))
for label, text in [
    ("'It works. <flag>'", f"It works. {FLAG}"),
    ("'It works. <party>'", f"It works. {PARTY}"),
    ("'I love it <flag>'", f"I love it {FLAG}"),
    ("'I love it <party>'", f"I love it {PARTY}"),
    ("'Done. <keycap 1>'", f"Done. {KEYCAP}"),
    ("'Done <keycap 1>'", f"Done {KEYCAP}"),
    ("'Smile <grin>x'", "Smile \U0001f600x"),
]:
    print(f"   {label:24s}", verdicts("format:emoji", {}, "", text))

print("\n=== format:quotes: exact inputs for the two mechanisms seen in R1-1eba3, R1-8c55c, R1-bcab0")
for case in ("R1-1eba3", "R1-8c55c", "R1-bcab0"):
    check, kwargs, prompt, response = case_inputs(case)
    print(f"   {case} as reviewed:   ", verdicts(check, kwargs, prompt, response))
quote_kwargs = case_inputs("R1-1eba3")[1]
for label, text in [
    ("curly, same kind nested 3x", "She said “the ‘first ‘second ‘third’ level’ here’ ends”."),
    ("double-single-double", 'She said "he wrote \'they call it "deep" now\' twice" today.'),
    ('two levels plus stray "', 'He wrote "the flux, \'called q", grows\' here." Then "more text" followed.'),
    ("two levels only", 'He wrote "the flux, \'called q, grows\' here." Then "more text" followed.'),
]:
    print(f"   {label:28s}", verdicts("format:quotes", quote_kwargs, "", text))

print("\n=== format:thesis: markdown emphasis around the <i> thesis (R1-6ed32, R1-71e3c, R1-86273, R1-bcf9b)")
thesis_kwargs = case_inputs("R1-71e3c")[1]
for label, text in [
    ("<i>T.</i> + body", "<i>The claim holds.</i>\n\nBody text follows here."),
    ("*<i>T.</i>* + body", "*<i>The claim holds.</i>*\n\nBody text follows here."),
    ("**<i>T.</i>** + body", "**<i>The claim holds.</i>**\n\nBody text follows here."),
    ("**<i>T.</i>** same paragraph", "**<i>The claim holds.</i>** Body text follows here."),
]:
    print(
        f"   {label:30s}",
        verdicts("format:thesis", thesis_kwargs, "", text),
        "| replacement with D-section B:",
        rep.check("format:thesis", thesis_kwargs, "", text, {"D-section": "B"}),
    )

print("\n=== count:numbers (R1-46f23) and count:words_japanese (R1-67436, R1-e200b)")
check, kwargs, prompt, response = case_inputs("R1-46f23")
print(f"   kwargs {kwargs}")
for label, text in [
    ("'On 9/11, 67% agreed.'", "On 9/11, 67% of them agreed."),
    ("'On 9-11, 67% agreed.'", "On 9-11, 67% of them agreed."),
    ("'In 2001, 67% agreed.'", "In 2001, 67% of them agreed."),
]:
    print(
        f"   {label:26s}",
        verdicts(check, kwargs, "", text),
        "| replacement readings B, C:",
        rep.check(check, kwargs, "", text, {"D-number": "B"}),
        rep.check(check, kwargs, "", text, {"D-number": "C"}),
    )
check, kwargs, prompt, response = case_inputs("R1-e200b")
print(f"   kwargs {kwargs}")
for label, text in [
    ("5 spaced tokens, 5th Japanese", "one two three four 日本語"),
    ("5th token Japanese+Latin", "one two three four 日本語ABC"),
    ("5th token Japanese+digits", "one two three four 日本語2024"),
]:
    print(f"   {label:30s}", verdicts(check, kwargs, "", text))
for case in ("R1-67436", "R1-e200b"):
    check, kwargs, prompt, response = case_inputs(case)
    tokens = response.split()
    n = int(kwargs.get("N", 5))
    fifth = tokens[n - 1 :: n] if tokens else []
    mixed = sum(1 for token in fifth if rep.JP.search(token) and any("a" <= ch.lower() <= "z" for ch in token))
    latin_only = sum(1 for token in fifth if not rep.JP.search(token))
    print(
        f"   {case}: whitespace tokens {len(tokens)}, every-5th tokens {len(fifth)}, of which Japanese with a Latin "
        f"letter {mixed}, without any Japanese character {latin_only}"
    )


def trace_quotes(text: str) -> None:
    """The replacement's quote parse (c_quotes), repeated here to show which marks make the first match of depth 3."""
    stack, matched = [], []
    for i, ch in enumerate(text):
        if ch in '"“”':
            kind = "d"
        elif ch in "'‘’":
            prev = text[i - 1] if i else " "
            nxt = text[i + 1] if i + 1 < len(text) else " "
            if prev.isalnum() and nxt.isalnum():
                continue
            if ch in "'’" and prev.isalpha() and prev.lower() == "s" and not (stack and stack[-1][0] == "s"):
                continue
            kind = "s"
        else:
            continue
        can_open = ch not in "”’"
        can_close = ch not in "“‘"
        if stack and stack[-1][0] == kind and can_close:
            opened = stack.pop()
            matched.append((opened[1], i, len(stack) + 1, kind))
        elif can_open:
            stack.append((kind, i))
    print(
        f"      quote marks left open at the end: {len(stack)}; matched pairs by depth: "
        + ", ".join(f"depth {d}: {sum(1 for m in matched if m[2] == d)}" for d in sorted({m[2] for m in matched}))
    )
    for start, end, depth, kind in matched:
        if depth >= 3:
            enclosing = sorted((s2, e2, d2, k2) for (s2, e2, d2, k2) in matched if s2 < start and e2 > end)
            if len(enclosing) >= 2:
                chain = [*enclosing, (start, end, depth, kind)]
                print(
                    "      first accepted chain, outermost first (kind, opening mark, span length, "
                    "text after the opening mark):"
                )
                for s2, e2, _d2, k2 in chain:
                    snippet = text[s2 + 1 : s2 + 46].replace(chr(10), " / ")
                    print(f"         {k2} U+{ord(text[s2]):04X} len {e2 - s2 + 1:5d}: {snippet!r}")
                return
    print("      no accepted chain")


print()
print("=== format:quotes: which marks the replacement nests in the three cases")
for case in ("R1-1eba3", "R1-8c55c", "R1-bcab0"):
    print(f"   {case}")
    trace_quotes(case_inputs(case)[3])
