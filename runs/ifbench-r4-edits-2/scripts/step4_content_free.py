"""Step 4: content-free responses. Grades, for every dataset prompt and instruction, five
content-free responses with grader (strict, loose), reference (strict, loose) and replacement,
and lists the checks each one passes. Output: audit/work/content_free.tsv + printed summary."""
import collections
import sys

sys.path.insert(0, "<W>/audit/scripts")
import graders  # noqa: E402
from run_panel import load_dataset_rows  # noqa: E402

rows = load_dataset_rows()
OUT = "<W>/audit/work/content_free.tsv"


def variants(row):
    return {
        "empty": "",
        "whitespace": " \n",
        "repeat_word": " ".join(["the"] * 200),
        "repeat_sentence": " ".join(["This is a sentence."] * 30),
        "restate_prompt": row["prompt"],
    }


NAMES = ["grader_strict", "grader_loose", "reference_strict", "reference_loose", "replacement"]
passes = collections.defaultdict(lambda: collections.defaultdict(set))
with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
    fh.write("key\tiid\tvariant\t" + "\t".join(NAMES) + "\n")
    for row in rows:
        for iid, kw in zip(row["ids"], row["kwargs"]):
            for vname, resp in variants(row).items():
                res = [graders.GRADERS[n](iid, kw, row["prompt"], resp) if n != "replacement"
                       else graders.replacement(iid, kw, row["prompt"], resp) for n in NAMES]
                fh.write(f"{row['key']}\t{iid}\t{vname}\t" + "\t".join(str(r) for r in res) + "\n")
                for n, r in zip(NAMES, res):
                    if r is True:
                        passes[vname][n].add((row["key"], iid))

for vname in ["empty", "whitespace", "repeat_word", "repeat_sentence", "restate_prompt"]:
    print(f"== {vname}")
    for n in NAMES:
        items = sorted(passes[vname][n])
        checks = sorted({i for _, i in items})
        print(f"  {n}: {len(items)} (prompt, instruction) passes over {len(checks)} checks: {', '.join(checks)}")
