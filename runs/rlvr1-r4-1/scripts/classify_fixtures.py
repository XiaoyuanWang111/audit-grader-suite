"""Grade every fixture with the replacement (proposed readings), the SkyRL checker and the
verifyit check; classify each grader disagreement with the contract label.

A disagreement is a decision when some combination of alternative readings (searched over
single switches and pairs of switches) makes the replacement give the grader's verdict; the
entries are named. Otherwise it is a finding.

Writes audit/tests/fixture_expectations.json and prints a table.
Usage: python audit/scripts/classify_fixtures.py [--check-only]
"""
import dataclasses
import itertools
import json
import pathlib
import sys

W = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W / "audit"))
sys.path.insert(0, str(W / "audit" / "tests"))

import harness  # noqa: E402
import replacement as rp  # noqa: E402
from fixtures import EXTRACTION, all_fixtures  # noqa: E402

# switch -> (decision entry, alternative value)
SWITCHES = {
    "literal_think": ("D-literal-think", False),
    "word_mode": ("D-word", None),  # handled specially: "whitespace" and "split"
    "markup_transparent": ("D-word-markup", False),
    "word_ignore_case": ("D-word-case", False),
    "keyword_whole_word": ("D-keyword-match", False),
    "sentence_split_lines": ("D-sentence", False),
    "paragraph_blank_runs": ("D-paragraph-split", False),
    "divider_line_only": ("D-divider", False),
    "letter_ignore_case": ("D-letter-case", False),
    "letters_any_script": ("D-letter-counting", False),
    "capital_single_letter": ("D-capital-word", False),
    "two_resp_exact_six": ("D-two-responses-separator", False),
    "repeat_any_inner_word": ("D-repeat-center", False),
    "repeat_copies_neutral": ("D-repeat-exact-copy", False),
    "lowercase_exact_form": ("D-lowercase-count", False),
    "lowercase_each_word": ("D-lowercase-scope", False),
    "placeholder_any": ("D-placeholder", False),
    "ps_accept_without_dot": ("D-ps-marker", False),
    "ps_case_sensitive": ("D-ps-case", False),
    "bigram_odd_final_single": ("D-bigram-odd", False),
    "constrained_exact": ("D-constrained-surround", False),
    "json_object_or_array": ("D-json-value", False),
    "sections_case_sensitive": ("D-sections-case", False),
    "sections_exact": ("D-sections-exact", False),
    "bullet_all_markers": ("D-bullet-marker", False),
    "bullet_nested": ("D-bullet-nested", False),
    "highlight_bold_counts": ("D-highlight-markup", False),
    "hyphens_single_ok": ("D-hyphens-single", False),
    "brackets_each_word": ("D-brackets-each", False),
    "title_anywhere": ("D-title-position", False),
    "consecutive_either_order": ("D-consecutive-order", False),
    "palindrome_min3": ("D-palindrome", False),
    "word_count_exact": ("D-word-count-relation", False),
    "unicode_commas": ("D-comma-chars", False),
    "unicode_dots": ("D-dot-chars", False),
    "unicode_exclamations": ("D-exclamation-chars", False),
    "end_strict": ("D-end-trailing", False),
    "end_case_sensitive": ("D-end-case", False),
    "curly_quotes": ("D-quote-chars", False),
    "divider_edges_strict": ("D-divider-edges", False),
    "two_resp_edges_strict": ("D-two-responses-edges", False),
    "consecutive_latin_only": ("D-consecutive-alphabet", False),
    "start_end_single_ok": ("D-start-end-single", False),
}


def alternatives():
    singles = []
    for name, (entry, alt) in SWITCHES.items():
        if name == "word_mode":
            singles.append(((entry,), {"word_mode": "whitespace"}))
            singles.append(((entry,), {"word_mode": "split"}))
        else:
            singles.append(((entry,), {name: alt}))
    yield from singles
    for (e1, a1), (e2, a2) in itertools.combinations(singles, 2):
        if e1 == e2:
            continue
        yield e1 + e2, {**a1, **a2}


ALTS = list(alternatives())


def classify(check, kwargs, text, grader_verdict):
    """All single alternative readings that give the grader's verdict; else all pairs; else a finding."""
    found = []
    for size in (1, 2):
        for entries, change in ALTS:
            if len(entries) != size:
                continue
            r = dataclasses.replace(rp.PROPOSED, **change)
            try:
                v = rp.check_constraint(check, kwargs, text, r)
            except Exception:  # noqa: BLE001
                continue
            if v == grader_verdict:
                found.append("+".join(entries))
        if found:
            return "decision", sorted(set(found))
    return "finding", []


def main():
    rows = []
    bad_labels = []
    for fx in all_fixtures():
        c, kw, t, lab = fx["check"], fx["kwargs"], fx["text"], fx["label"]
        rv = rp.check_constraint(c, kw, t)
        if rv != lab:
            bad_labels.append((fx["id"], fx["note"], lab, rv))
        sk = harness.skyrl_check(c, kw, t)
        vi = None if c in harness.SEMANTIC else harness.curation_check(c, kw, t)
        entry = {**fx, "replacement": rv, "skyrl": sk, "verifyit": vi}
        for g in ("skyrl", "verifyit"):
            gv = entry[g]
            if gv is None or gv == lab:
                entry[g + "_class"] = "agree" if gv is not None else "not gated"
                entry[g + "_decisions"] = []
            else:
                cls, ents = classify(c, kw, t, gv)
                entry[g + "_class"] = cls
                entry[g + "_decisions"] = ents
        rows.append(entry)
    ext = []
    for suffix, reasoning, raw, record, label, note in EXTRACTION:
        gt = rp.graded_text(raw, reasoning)
        rv, _ = rp.grade_row(gt, record)
        sk, _, _, sk_text = harness.skyrl_grade(raw, record)
        gate, _, gate_text = harness.curation_gate(raw, record)
        alt_ok = None
        if not reasoning:
            alt = rp.graded_text(raw, reasoning, dataclasses.replace(rp.PROPOSED, literal_think=False))
            alt_ok = rp.grade_row(alt, record)[0]
        ext.append({"id": "extraction:" + suffix, "reasoning_model": reasoning, "raw": raw, "record": record,
                    "label": label, "replacement": rv, "skyrl_reward": sk, "skyrl_graded_text": sk_text,
                    "gate_passed": gate, "gate_graded_text": gate_text, "alt_literal_think_reward": alt_ok, "note": note})
    out = {"fixtures": rows, "extraction": ext}
    if "--check-only" not in sys.argv:
        (W / "audit" / "tests" / "fixture_expectations.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(f"{len(rows)} fixtures; replacement disagrees with the label on {len(bad_labels)}")
    for b in bad_labels:
        print("  LABEL MISMATCH", b)
    for g in ("skyrl", "verifyit"):
        f = [r for r in rows if r[g + "_class"] == "finding"]
        d = [r for r in rows if r[g + "_class"] == "decision"]
        print(f"{g}: {len(f)} finding fixtures, {len(d)} decision fixtures, "
              f"{sum(r[g + '_class'] == 'agree' for r in rows)} agree")
        for r in f:
            print(f"   F {r['id']}  label={r['label']} grader={r[g]}  {r['note']}")
        for r in d:
            print(f"   D {r['id']}  label={r['label']} grader={r[g]}  {r['note']}  via {r[g + '_decisions']}")
    for e in ext:
        print("EXTRACTION", e["id"], "label", e["label"], "replacement", e["replacement"], "skyrl", e["skyrl_reward"],
              "gate passed", e["gate_passed"], "alt", e["alt_literal_think_reward"])


if __name__ == "__main__":
    main()
