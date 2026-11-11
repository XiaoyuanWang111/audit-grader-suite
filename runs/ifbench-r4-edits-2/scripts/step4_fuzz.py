"""Step 4: fuzz every check (dataset kwargs of each prompt) with random and mutated responses.
Counts exceptions per check and grader (strict and loose paths). Seeded: random.Random(10060).
Output: audit/work/fuzz.tsv (one line per exception) and a printed summary."""
import collections
import glob
import json
import random
import sys

sys.path.insert(0, "<W>/audit/scripts")
import graders  # noqa: E402
from run_panel import load_dataset_rows  # noqa: E402

W = "<W>"
rng = random.Random(10060)
ALPH = (list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") * 3 + list(" \t\n\n\r.,;:!?'\"()[]{}*-_#<>/\\|`~@$%^&+=")
        + ["\u201c", "\u201d", "\u2018", "\u2019", "\u2014", "\u00a0", "\u200b", "\u3042", "\u65e5", "\U0001F600", "\U0001F1FA\U0001F1F8",
           "\u2764\ufe0f", "<i>", "</i>", "<em>", "**", "?!", "\u203d", "\t\t", "My Answer:", "Question 1:", "A) x\n", "\n* ", "\n- "])


def rand_text():
    n = rng.choice([1, 2, 3, 5, 10, 30, 100, 400])
    return "".join(rng.choice(ALPH) for _ in range(n))


def mutate(t):
    t = list(t)
    for _ in range(rng.randint(1, 8)):
        op = rng.random()
        pos = rng.randrange(len(t) + 1)
        if op < 0.4 and t:
            del t[min(pos, len(t) - 1)]
        elif op < 0.8:
            t.insert(pos, rng.choice(ALPH))
        else:
            t[pos:pos] = list(rng.choice(["\t\t", '""', "\n\n", "\t\n", ",,", "((((((", "'''", "\u201c\u201d"]))
    return "".join(t)


rows = load_dataset_rows()
by_check = collections.defaultdict(list)
for r in rows:
    for iid, kw in zip(r["ids"], r["kwargs"]):
        by_check[iid].append((r, kw))
panel = collections.defaultdict(list)
for path in sorted(glob.glob(W + "/case/panel/*/greedy.jsonl")):
    for line in open(path, encoding="utf-8"):
        rec = json.loads(line)
        panel[str(rec["key"])].append(rec["response"])

counts = collections.Counter()
inputs = collections.Counter()
with open(W + "/audit/work/fuzz.tsv", "w", encoding="utf-8", newline="\n") as fh:
    fh.write("iid\tkey\tgrader\terror\tinput_json\n")
    for iid, items in sorted(by_check.items()):
        for k in range(300):
            r, kw = items[k % len(items)]
            if k % 2 == 0:
                text = rand_text()
            else:
                text = mutate(rng.choice(panel[str(r["key"])]))
            inputs[iid] += 1
            for name in ["grader_strict", "grader_loose", "reference_strict", "reference_loose", "replacement"]:
                fn = graders.GRADERS.get(name)
                v = fn(iid, kw, r["prompt"], text) if fn else graders.replacement(iid, kw, r["prompt"], text)
                if isinstance(v, str):
                    counts[(iid, name, v.split(":")[1])] += 1
                    fh.write(f"{iid}\t{r['key']}\t{name}\t{v}\t{json.dumps(text, ensure_ascii=False)[:400]}\n")
print("fuzz inputs:", sum(inputs.values()), "over", len(inputs), "checks")
for (iid, name, e), n in sorted(counts.items()):
    print(f"  {iid:34s} {name:17s} {e:22s} {n}")
if not counts:
    print("  no exceptions")
