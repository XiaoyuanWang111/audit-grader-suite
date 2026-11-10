"""Step 4: fuzzing for exceptions, content-free responses, and the loose transform.

1. Fuzz: for every (dataset row, check) pair, grade N random texts (fixed seed) with the grader
   (as-loaded float kwargs, and int-cast) and the reference; count exceptions per check and type.
2. Content-free responses: empty, whitespace, one repeated word, a repeated sentence, the prompt
   itself, the instruction sentence alone. List the (row, check) pairs each one passes.
3. Loose: hand-made responses that the contract fails but a loose variant passes.
Writes audit/out/fuzz_counts.tsv, audit/out/contentfree.tsv and prints summaries.
"""
import collections
import random
import re
import sys

W = "<W>"
sys.path.insert(0, f"{W}/audit/lib")
import harness as H  # noqa: E402

rng = random.Random(10060)
WORDS = ("the a cat dog run fast blue sky I you he she it we they and but or so yet for nor "
         "giggle vibrant whisper paradox river door bread lamp blue Emma Liam level radar 7 42 3.14 "
         "don't it's state-of-the-art e.g. Dr. U.S. \u65e5\u672c \u4e16\u754c").split()
PUNCT = list(".,;:!?-\u2014\u2013\u2026\"'()[]{}*#\u201c\u201d\u2018\u2019") + ["?!", "...", "**", "\n", "\n\n", "\t", "  "]
EMO = ["\U0001F600", "\u2764\ufe0f", "1\ufe0f\u20e3", "\U0001F1FA\U0001F1F8", "\U0001F44D\U0001F3FD"]


def rand_text():
    n = rng.randint(1, 60)
    parts = []
    for _ in range(n):
        r = rng.random()
        if r < 0.65:
            parts.append(rng.choice(WORDS))
        elif r < 0.95:
            parts.append(rng.choice(PUNCT))
        else:
            parts.append(rng.choice(EMO))
    sep = lambda: rng.choice([" ", " ", " ", "", "\n"])  # noqa: E731
    return "".join(p + sep() for p in parts)


def rand_sentences():
    """30-40 short sentences, some lines, CSV-like and quoted fragments, to reach deep positions."""
    out = []
    for _ in range(rng.randint(30, 40)):
        n = rng.randint(1, 40)
        s = " ".join(rng.choice(WORDS) for _ in range(n))
        out.append(s[:1].upper() + s[1:] + rng.choice([".", "!", "?", ".\n", "\n", ' "x".', ""]))
    if rng.random() < 0.5:
        out.insert(0, '"StudentID"\t"Subject"\t"Grade"\t"Semester"\t"Score"\n"1"\t\t"A"\t"B"\t"C"\n')
    return " ".join(out)


N_FUZZ = 120
pairs = [(r["key"], iid) for r in H.dataset() for iid in r["instruction_id_list"]]
texts = [rand_text() for _ in range(N_FUZZ // 2)] + [rand_sentences() for _ in range(N_FUZZ // 2)]
exc = collections.Counter()
calls = collections.Counter()
examples = {}
for key, iid in pairs:
    for t in texts:
        for impl, ic in (("grader", False), ("grader", True), ("reference", False)):
            v = H.grade(iid, t, key=key, impl=impl, int_cast=ic)
            label = f"{impl}{'_int' if ic else ''}"
            calls[(iid, label)] += 1
            if isinstance(v, str):
                exc[(iid, label, v)] += 1
                examples.setdefault((iid, label, v), (key, t))
with open(f"{W}/audit/out/fuzz_counts.tsv", "w", encoding="utf-8", newline="\n") as out:
    out.write("check\timpl\texception\tcount\tcalls\texample_key\texample_text\n")
    for (iid, label, v), n in sorted(exc.items()):
        k, t = examples[(iid, label, v)]
        out.write(f"{iid}\t{label}\t{v}\t{n}\t{calls[(iid, label)]}\t{k}\t{t!r}\n")
print(f"FUZZ: {len(texts)} texts x {len(pairs)} (row, check) pairs x 3 implementations")
for (iid, label, v), n in sorted(exc.items()):
    print(f"  {iid:36s} {label:12s} {v:22s} {n}/{calls[(iid, label)]}")


def instruction_sentence(prompt, iid):
    # the instruction text is the sentence of the prompt that the template produced; use the
    # dataset kwargs-free approximation: the last sentence that matches the check's template words
    sents = re.split(r"(?<=[.!?])\s+", prompt.strip())
    return sents[-1] if sents else prompt


CF = {
    "empty": lambda r, iid: "",
    "whitespace": lambda r, iid: " \n\t ",
    "repeat_word": lambda r, iid: " ".join(["the"] * 50),
    "repeat_sentence": lambda r, iid: " ".join(["This is a sentence."] * 20),
    "restate_prompt": lambda r, iid: r["prompt"],
    "restate_last_sentence": lambda r, iid: instruction_sentence(r["prompt"], iid),
}
cf_pass = collections.defaultdict(list)
with open(f"{W}/audit/out/contentfree.tsv", "w", encoding="utf-8", newline="\n") as out:
    out.write("response\tkey\tcheck\tgrader\tgrader_int\treference\n")
    for name, fn in CF.items():
        for r in H.dataset():
            for iid in r["instruction_id_list"]:
                t = fn(r, iid)
                g = H.grade(iid, t, key=r["key"])
                gi = H.grade(iid, t, key=r["key"], int_cast=True)
                rf = H.grade(iid, t, key=r["key"], impl="reference")
                out.write(f"{name}\t{r['key']}\t{iid}\t{g}\t{gi}\t{rf}\n")
                if gi is True:
                    cf_pass[name].append((r["key"], iid))
print("\nCONTENT-FREE responses: (row, check) pairs passed by the grader (int-cast kwargs)")
for name in CF:
    lst = cf_pass[name]
    checks = sorted(collections.Counter(i for _, i in lst).items())
    print(f"  {name:22s} {len(lst):3d}/{len(pairs)} pairs; checks: {', '.join(f'{c}({n})' for c, n in checks)}")
