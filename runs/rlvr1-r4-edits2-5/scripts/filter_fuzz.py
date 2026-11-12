"""Keep the fuzz candidates as fixtures, except finding groups whose label rests on a detail the
contract does not state (listed in EXCLUDE, see ISSUE.md step 3). Writes work/fuzz_fixtures.jsonl."""
import json
from pathlib import Path

W = Path(__file__).resolve().parents[2]
EXCLUDE = {("cura", "number_bullet_lists"), ("cura", "postscript"), ("skyr", "multiple_sections"),
           ("skyr", "number_bullet_lists"), ("skyr", "number_highlighted_sections"), ("cura", "sentence_hyphens"),
           ("cura", "last_word_sent"), ("skyr", "last_word_sent"), ("skyr", "sentence_hyphens"),
           ("skyr", "bigram_wrapping"), ("skyr", "start_end"), ("cura", "start_end"), ("skyr", "number_paragraphs"),
           ("skyr", "english_lowercase"), ("cura", "english_lowercase")}
kept = dropped = 0
src = W / "audit/work/fuzz_candidates.jsonl"
with (W / "audit/work/fuzz_fixtures.jsonl").open("w", encoding="utf-8", newline="\n") as out:
    for line in src.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        _, grader, cls = r["note"].split()[:3]
        if cls == "finding" and (grader[:4], r["instruction_id"].split(":")[1]) in EXCLUDE:
            dropped += 1
            continue
        out.write(line + "\n")
        kept += 1
print("fuzz fixtures kept", kept, "dropped", dropped)
