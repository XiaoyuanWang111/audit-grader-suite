"""Check that each row's kwargs agree with the instruction text the model sees,
and list template phrases of instructions that appear in a prompt but are not in
its instruction_id_list (ungraded instructions)."""
import re
import sys
from pathlib import Path

import pandas as pd

W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W / "audit/scripts"))
from dump_phrasings import PAT  # noqa: E402

df = pd.read_parquet(W / "case/data/train-00000-of-00001.parquet")


def num(x):
    return int(x) if float(x).is_integer() else x


TEXT_RE = {
    "count:conjunctions": (r"Use at least (\d+) different coordinating", ["small_n"]),
    "count:numbers": (r"Include exactly (\d+) numbers", ["N"]),
    "count:person_names": (r"Mention at least (\d+) different person names", ["N"]),
    "count:pronouns": (r"at least (\d+) pronouns", ["N"]),
    "count:unique_word_count": (r"Use at least (\d+) unique words", ["N"]),
    "count:word_count_range": (r"between (\d+) and (\d+) words", ["min_words", "max_words"]),
    "count:words_japanese": (r"Every (\d+)\w* word of your response must be in Japanese", ["N"]),
    "ratio:overlap": (r"trigram overlap of (\d+)%", ["percentage"]),
    "ratio:stop_words": (r"no more than (\d+)% of the total words", ["percentage"]),
    "sentence:increment": (r"exactly (\d+) more words than the previous", ["small_n"]),
    "sentence:keyword": (r"must include keyword (\S+) in the (\d+)-\w+ sentence", ["word", "N"]),
    "words:keywords_specific_position": (r"Include keyword (\S+) in the (\d+)-\w+ sentence, as the (\d+)-\w+ word", ["keyword", "n", "m"]),
    "words:repeats": (r"not repeat any word more than (\d+) times", ["small_n"]),
    "repeat:repeat_span": (r"between \(and including\) index (\d+) and (\d+)", ["n_start", "n_end"]),
    "words:words_position": (r"should be the word (\w+)", ["keyword"]),
    "format:list": (r"instead of bullet points use (\S+?)\.?(?:\s|$)", ["sep"]),
    "format:options": (r"following options: (.+?)\.(?:\s|$)", ["options"]),
}

lines = []
for _, r in df.iterrows():
    p = r["prompt"]
    ids = list(r["instruction_id_list"])
    for iid, kw in zip(ids, r["kwargs"]):
        kw = {k: (v.tolist() if hasattr(v, "tolist") else v) for k, v in kw.items() if v is not None}
        if iid in TEXT_RE:
            rx, keys = TEXT_RE[iid]
            m = re.search(rx, p)
            if not m:
                lines.append(f"NO_TEXT_MATCH key={r['key']} {iid} kwargs={kw}")
                continue
            got = m.groups()
            want = [kw.get(k) for k in keys]
            ok = all(str(g) == str(num(w) if isinstance(w, float) else w) for g, w in zip(got, want))
            if not ok:
                lines.append(f"MISMATCH key={r['key']} {iid} text={got} kwargs={dict(zip(keys, want))}")
        if iid == "count:keywords_multiple":
            m = re.findall(r"keyword (\w+) (once|twice|three times|five times|seven times)", p)
            want = [kw[f"keyword{i}"] for i in range(1, 6)]
            if [w for w, _ in m] != want or [c for _, c in m] != ["once", "twice", "three times", "five times", "seven times"]:
                lines.append(f"MISMATCH key={r['key']} {iid} text={m} kwargs={want}")
        if iid == "repeat:repeat_change" or iid == "repeat:repeat_span":
            ptr = kw.get("prompt_to_repeat")
            if ptr is not None and ptr not in p:
                # whitespace-normalised containment
                norm = lambda s: re.sub(r"\s+", " ", s).strip()
                tag = "WS_ONLY" if norm(ptr) in norm(p) else "ABSENT"
                lines.append(f"PROMPT_TO_REPEAT_{tag} key={r['key']} {iid}")
    # ungraded instruction phrases
    for other, pat in PAT.items():
        if other in ids:
            continue
        if other == "words:keywords_specific_position" and "count:keywords_multiple" in ids:
            continue
        if re.search(pat, p):
            if other in ("count:numbers", "words:prime_lengths", "words:words_position", "format:newline",
                         "count:pronouns", "count:punctuation", "words:odd_even_syllables", "ratio:stop_words",
                         "count:person_names", "count:words_japanese", "format:no_whitespace", "format:emoji"):
                # generic phrases; print with context so they can be judged by eye
                m = re.search(pat, p)
                ctx = p[max(0, m.start() - 60): m.end() + 40].replace("\n", " ")
                lines.append(f"PHRASE key={r['key']} ids={ids} has '{other}' phrase: ...{ctx}...")
            else:
                lines.append(f"PHRASE key={r['key']} ids={ids} has '{other}' phrase")

with open(W / "audit/out/kwargs_text_check.txt", "w", newline="\n", encoding="utf-8") as f:
    for l in lines:
        f.write(l + "\n")
print(len(lines))
