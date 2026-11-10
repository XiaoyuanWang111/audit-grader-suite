"""Build the score card tables of the IFBench blind rerun from a hand-made mapping, and check the mapping against the
two reports.

The mapping below was made by hand, under a scoring rule written down before any item of the rerun was matched to the
earlier audit: it says, for each finding of the earlier audit, whether the rerun reports the behavior as a finding, as
a decision entry, or not at all, and for each finding of the rerun, what it is when set against the earlier audit. The
script checks that the mapping covers every checker and protocol finding of the earlier audit and every finding id in
the rerun's report, counts the classes, and prints the tables as Markdown.

The earlier audit's findings are `data/findings.jsonl` of the Hugging Face dataset xiaoyuanwang/ifbench-audit; the
rerun's report is `runs/ifbench-r3/AUDIT.md`. Read-only, except the optional Markdown output.

Usage: python -B keys/tools/ifbench/ifbench_scorecard.py <earlier audit findings.jsonl> <rerun AUDIT.md> [<out.md>]
"""

import collections
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# fmt: off
# Earlier audit's finding id -> (class, the rerun's items, note). Classes: finding, decision, missed.
KEY = {
    "F1": ("finding", ["F-span-characters"], ""),
    "F2": ("decision", ["D-overlap"], "character trigrams are the grader's reading of D-overlap"),
    "F3": ("finding", ["F-subbullets-none", "F-subbullets-any-hyphen", "F-subbullets-bold"], ""),
    "F4": ("finding", ["F-list-anywhere"], ""),
    "F5": ("decision", ["D-paren"], ""),
    "F6": ("finding", ["F-sentwords-no-word-check"], ""),
    "F7": ("decision", ["D-match"], "substring counts are the grader's reading of D-match"),
    "F8": ("finding", ["F-wordspos-comma"], ""),
    "F9": ("finding", ["F-alphabet-story-quote"], ""),
    "F10": ("finding", ["F-thesis-anywhere"], "in part: not the `<em>` slicing"),
    "F11": ("finding", ["F-quote-curly"], "in part: not the guillemets"),
    "F12": ("finding", ["F-quotes-apostrophe"], ""),
    "F13": ("finding", ["F-conj-surface-forms"], ""),
    "F14": ("finding", ["F-capitals-kyiv"], ""),
    "F15": ("finding", ["F-csvquotes-indexerror"], ""),
    "F16": ("finding", ["F-csvspecial-early-return"], ""),
    "F17": ("finding", ["F-ratio-quote-endings"], "both checks"),
    "F18": ("finding", ["F-alliteration-sum"], ""),
    "F19": ("finding", ["F-newline-blank-offset"], ""),
    "F20": ("finding", ["F-indent-blank-lines", "F-indent-tabs"], ""),
    "F21": ("finding", ["F-paralastfirst-comma"], ""),
    "F22": ("finding", ["F-nbb-blank-line", "F-nbb-period", "F-nbb-trailing-text"], ""),
    "F23": ("finding", ["F-repeatchange-whitespace"], ""),
    "F24": ("finding", ["F-template-presence-only"], ""),
    "F25": ("finding", ["F-title-contraction"], "in part: lowercase minor words are the decision D-title"),
    "F26": ("finding", ["F-options-whitespace"], ""),
    "F27": ("finding", ["F-emoji-flag"],
            "in part, and only after the review: flags, not keycaps or an emoji followed by a letter"),
    "F28": ("finding", ["F-startverb-tagger"], ""),
    "F29": ("finding", ["F-numbers-joined"], ""),
    "F30": ("decision", ["D-word"], "a standalone punctuation token as a word is the grader's reading of D-word"),
    "F31": ("decision", ["D-word"], ""),
    "F32": ("missed", [], "curly quotes count toward a word's length"),
    "F33": ("decision", ["D-vacuous"], ""),
    "F34": ("decision", ["D-vacuous"], ""),
    "F35": ("decision", ["D-palindrome"], ""),
    "F36": ("finding", ["F-position-contractions"], ""),
    "F37": ("finding", ["F-dates-invalid"], "in part: month 00 and day 00, not 1801-02-29"),
    "F38": ("finding", ["F-wordrev-mixed", "F-charrev-substring"], "two of the three checks"),
    "F39": ("finding", ["F-mcq-label-number"], "in part: not the text before the first label"),
    "F40": ("missed", [], "a comma after the repeated word; F-lastfirst-quotes is another behavior of the check"),
    "F41": ("finding", ["F-startverb-markup"], ""),
    "F42": ("missed", [], "a list number shifts the word positions"),
    "F43": ("missed", [], "a list label read as a sentence; D-sentence covers line breaks only"),
    "G1": ("hinted", ["F-loose-deletes-constrained"], "SKILL.md names loose grading; left out of the counts"),
    "G2": ("finding", ["F-options-whitespace"], "in part: the fixture on prompt 105, not the conflict of its two instructions"),
    "G3": ("decision", ["D-options"], ""),
    "G4": ("missed", [], "integer arguments stored as doubles"),
    "G5": ("finding", ["F-pin-3", "F-pin-4"], ""),
    "G6": ("finding", ["F-csvquotes-indexerror"], "in part: the caller that the exception stops is not in the case"),
    "G7": ("decision", ["D-sentence"], ""),
}

# Rerun finding id -> class when it matches no finding of the earlier audit, with the reason.
NEW_VALID = {
    "F-lastfirst-quotes": "words:last_first: a quotation mark stays on the last word; the same sentence without quotes passes",
    "F-japanese-skip-tokens": "count:words_japanese: a hyphen at position 5 is skipped; wrong whether or not a hyphen is a word",
    "F-africa-numbering": "custom:reverse_newline: a numbered list in the right order fails; the same list without numbers passes",
    "F-punct-six-marks": "count:punctuation: only six marks and the interrobang are required; in 4 reviewed cases both "
                         "reviewers gave a definite fail to a response the grader passed",
    "F-sentence-html-tags": "sentence checks: a period followed by an HTML closing tag does not end a sentence, so "
                            "`<i>Cats sleep.</i> Dogs run fast.` is one sentence; added after the review. The earlier "
                            "audit notes the behavior under its open question on sentences and found no changed verdict",
}
DECISION_LEVEL = {
    "F-options-case": "the earlier audit's decision D-option-case",
    "F-quotes-curly": "the earlier audit's decision D-curly-quotes",
    "F-wordcount-contractions": "the earlier audit's decision D-word-tokens (is `don't` one word)",
    "F-stopwords-contractions": "the earlier audit's decision D-word-tokens",
    "F-noconsec-digits": "the earlier audit's decision D-non-word-tokens (are numbers words)",
    "F-pronouns-determiners": "one of the rerun's two reviewers marked all 3 reviewed cases ambiguous",
    "F-quote-separator": "the earlier audit's decision D-explanation-word (is a symbol after a quote an explanation); "
                         "added after the review",
    "F-wordcount-html-tags": "the earlier audit's decision D-non-word-tokens (are HTML tags words); added after the review",
}
NOT_THE_GRADER = {
    "F-pin-1": "the working directory records no commit for the vendored grader",
    "F-pin-2": "the stored panel's settings file lacks stop sequences and one server version",
    "F-extract-unclosed": "the stored panel keeps responses whose reasoning never closes",
}
FALSE = {}
# fmt: on


def main():
    key_rows = [json.loads(line) for line in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines() if line.strip()]
    key_ids = [row["id"] for row in key_rows]
    assert sorted(key_ids) == sorted(KEY), sorted(set(key_ids) ^ set(KEY))
    rests = {row["id"] for row in key_rows if row["rests_on_decision"]}
    report = Path(sys.argv[2]).read_text(encoding="utf-8")
    start = re.search(r"\n## (?:\d+\. )?Findings\n", report)
    table = report[start.end() :].split("\n## ", 1)[0]
    rerun_ids = re.findall(r"^\| (F-[a-z0-9-]+) \|", table, flags=re.MULTILINE)
    assert len(rerun_ids) == len(set(rerun_ids)), "duplicate finding id in the report"

    matched = collections.defaultdict(list)
    for key_id, (_cls, items, _note) in KEY.items():
        for item in items:
            if item.startswith("F-"):
                matched[item].append(key_id)
    classes = {}
    for rid in rerun_ids:
        places = [
            name
            for name, group in (
                ("matches the earlier audit", matched),
                ("valid and new", NEW_VALID),
                ("decision-level", DECISION_LEVEL),
                ("not about the grader", NOT_THE_GRADER),
                ("false", FALSE),
            )
            if rid in group
        ]
        assert len(places) == 1, (rid, places)
        classes[rid] = places[0]
    unknown = (set(matched) | set(NEW_VALID) | set(DECISION_LEVEL) | set(NOT_THE_GRADER) | set(FALSE)) - set(rerun_ids)
    assert not unknown, f"mapped ids that the report does not list: {sorted(unknown)}"

    out = []
    counts = collections.Counter()
    for key_id in sorted(KEY, key=lambda k: (k[0], int(k[1:]))):
        cls = KEY[key_id][0]
        group = (
            "protocol"
            if key_id.startswith("G")
            else ("rests on a decision" if key_id in rests else "holds under every reading")
        )
        counts[(group, cls)] += 1
    out.append("| Earlier audit's findings | Reported as a finding | As a decision entry | Not reported | Left out |")
    out.append("|---|---|---|---|---|")
    for group in ("holds under every reading", "rests on a decision", "protocol"):
        total = sum(v for (g, _), v in counts.items() if g == group)
        out.append(
            f"| {group} ({total}) | {counts[(group, 'finding')]} | {counts[(group, 'decision')]} | "
            f"{counts[(group, 'missed')]} | {counts[(group, 'hinted')]} |"
        )
    out.append("")
    out.append("| Earlier finding | Check | Class | Rerun's item | Note |")
    out.append("|---|---|---|---|---|")
    by_id = {row["id"]: row for row in key_rows}
    for key_id in sorted(KEY, key=lambda k: (k[0], int(k[1:]))):
        cls, items, note = KEY[key_id]
        row = by_id[key_id]
        check = ", ".join(row["instruction_ids"]) or "protocol"
        mark = " (rests on a decision)" if key_id in rests else ""
        shown = {"finding": "finding", "decision": "decision entry", "missed": "not reported", "hinted": "left out"}[cls]
        out.append(f"| {key_id}{mark} | {check} | {shown} | {', '.join(items) or 'none'} | {note} |")
    out.append("")
    tally = collections.Counter(classes.values())
    out.append(
        f"Rerun findings: {len(rerun_ids)}. "
        + "; ".join(
            f"{name}: {tally[name]}"
            for name in ("matches the earlier audit", "valid and new", "decision-level", "not about the grader", "false")
        )
        + "."
    )
    out.append("")
    out.append("| Rerun's finding | Class | Earlier finding or reason |")
    out.append("|---|---|---|")
    for rid in rerun_ids:
        cls = classes[rid]
        reason = (
            ", ".join(matched[rid])
            if cls == "matches the earlier audit"
            else {**NEW_VALID, **DECISION_LEVEL, **NOT_THE_GRADER, **FALSE}[rid]
        )
        out.append(f"| {rid} | {cls} | {reason} |")
    text = "\n".join(out) + "\n"
    if len(sys.argv) > 3:
        Path(sys.argv[3]).write_text(text, encoding="utf-8", newline="\n")
    print(text[: text.index("| Earlier finding |")])
    print(f"Rerun findings: {len(rerun_ids)}; {dict(tally)}")
    key_matched = sorted({k for ks in matched.values() for k in ks}, key=lambda k: (k[0], int(k[1:])))
    print(
        f"rerun ids that match a key finding: {sum(1 for r in rerun_ids if r in matched)}; key entries they match: {len(key_matched)}"
    )


if __name__ == "__main__":
    main()
