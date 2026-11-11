"""Step 4: metamorphic tests.

Ignored edits (the contract's verdict must not change): trailing newline, typographic quotes,
bold markup around an inner word, a list label before the first line, a comma after an inner
word, a blank line between lines. Each edit is applied to passing responses of every check whose
contract ignores it: all pass-labeled fixtures plus up to 25 panel responses per check that the
replacement passes (greedy runs; the panel grading must have finished).
Forbidden edits (a passing response must fail): one per check family listed in FORBIDDEN.

Output: audit/work/metamorphic.tsv and a printed summary of verdict flips per grader.
"""
import collections
import csv
import glob
import json
import random
import re
import sys

sys.path.insert(0, "<W>/audit/scripts")
sys.path.insert(0, "<W>/audit/tests")
import graders  # noqa: E402
from fixtures import FIXTURES  # noqa: E402
from run_panel import load_dataset_rows  # noqa: E402

W = "<W>"
rng = random.Random(10060)
ALL = set(graders.ALL_IDS)
CUSTOM = {i for i in ALL if i.startswith("custom:")}
REPEAT = {i for i in ALL if i.startswith("repeat:")}
EXACTISH = CUSTOM | REPEAT | {"format:options", "format:no_whitespace"}


def inner_word_span(t):
    """(start, end) of an alphabetic word that is neither first nor last on its line."""
    cands = []
    for m in re.finditer(r"[^\n]+", t):
        line = m.group(0)
        ws = list(re.finditer(r"(?<![\w'*<>])[A-Za-z]{3,}(?![\w'*<>])", line))
        for w in ws[1:-1]:
            cands.append((m.start() + w.start(), m.start() + w.end()))
    return rng.choice(cands) if cands else None


def e_trailing_newline(t):
    return t + "\n"


def e_typographic(t):
    if "'" not in t and '"' not in t:
        return None
    out, dq = [], False
    for i, ch in enumerate(t):
        if ch == '"':
            out.append("\u201d" if dq else "\u201c")
            dq = not dq
        elif ch == "'":
            prev = t[i - 1] if i else " "
            out.append("\u2019" if prev.isalnum() else "\u2018")
        else:
            out.append(ch)
    return "".join(out)


def e_bold(t):
    sp = inner_word_span(t)
    return None if not sp else t[:sp[0]] + "**" + t[sp[0]:sp[1]] + "**" + t[sp[1]:]


def e_label(t):
    m = re.match(r"(\s*)", t)
    return t[:m.end()] + "- " + t[m.end():]


def e_comma(t):
    sp = inner_word_span(t)
    if not sp or t[sp[1]:sp[1] + 1] in ",.;:!?":
        return None
    return t[:sp[1]] + "," + t[sp[1]:]


def e_blank_line(t):
    i = t.find("\n")
    return None if i < 0 or i == len(t.rstrip()) else t[:i] + "\n" + t[i:]


IGNORED = {  # edit -> checks whose contract ignores it
    "trailing_newline": ALL,
    "typographic": ALL,
    "bold_inner_word": ALL - EXACTISH - {"format:sub-bullets", "ratio:sentence_words"} | {"custom:multiples"},
    "list_label_first_line": ALL - EXACTISH - {"count:numbers", "count:punctuation", "format:list", "format:sub-bullets",
                                               "format:no_bullets_bullets", "format:output_template", "format:thesis",
                                               "ratio:sentence_words", "format:line_indent", "words:paragraph_last_first"},
    "comma_after_word": ALL - EXACTISH - {"ratio:sentence_words", "count:punctuation"} | {"custom:multiples"},
    "blank_line": ALL - EXACTISH - {"words:vowel", "format:thesis", "custom:mcq_count_length"},
}
EDITS = {"trailing_newline": e_trailing_newline, "typographic": e_typographic, "bold_inner_word": e_bold,
         "list_label_first_line": e_label, "comma_after_word": e_comma, "blank_line": e_blank_line}


def f_insert_space(t, kw):
    return t[:1] + " " + t[1:] if len(t) > 1 else None


def f_lower_major(t, kw):
    m = re.search(r"(?<![\w'])([A-Z])([a-z]{4,})", t[1:])
    return None if not m else t[:1 + m.start()] + m.group(1).lower() + t[1 + m.start() + 1:]


def f_prepend_the(t, kw):
    return "The " + t


def f_second_word(t, kw):
    ws = t.split(" ", 2)
    return None if len(ws) < 3 else ws[0] + " zzzq " + ws[2]


def f_join_lines(t, kw):
    i = t.find("\n")
    return None if i < 0 else t[:i] + " " + t[i + 1:].lstrip("\n")


def f_append_words(t, kw):
    return t + " " + " ".join(["extra"] * (int(kw.get("max_words", 0)) + 5))


def f_drop_label(t, kw):
    return t.replace("My Conclusion:", "", 1) if "My Conclusion:" in t else None


def f_append_sure(t, kw):
    return t + " Sure."


def f_append_reason(t, kw):
    return t + " because of the evidence"


def f_dup_word(t, kw):
    ws = t.split(" ")
    return None if len(ws) < 3 else " ".join(ws[:2] + [ws[1]] + ws[2:])


def f_append_56(t, kw):
    return t + ", 56"


def f_append_number(t, kw):
    return t + " 7"


def f_append_plain(t, kw):
    return t + " And this one ends plainly."


def f_append_dangling_quote(t, kw):
    return t + ' "dangling"'


def f_kill_keyword(t, kw):
    k = kw.get("word") or kw.get("keyword")
    return None if not k else re.sub(re.escape(k), "zzzq", t, flags=re.I)


def f_repeat_top(t, kw):
    ws = re.findall(r"[A-Za-z]+", t)
    if not ws:
        return None
    w = collections.Counter(x.lower() for x in ws).most_common(1)[0][0]
    return t + " " + " ".join([w] * (int(kw["small_n"]) + 1))


FORBIDDEN = {
    "format:no_whitespace": f_insert_space, "format:title_case": f_lower_major, "words:start_verb": f_prepend_the,
    "words:words_position": f_second_word, "format:newline": f_join_lines, "count:word_count_range": f_append_words,
    "format:output_template": f_drop_label, "repeat:repeat_simple": f_append_sure, "format:options": f_append_reason,
    "words:no_consecutive": f_dup_word, "words:alphabet": f_dup_word, "custom:multiples": f_append_56,
    "count:numbers": f_append_number, "format:emoji": f_append_plain, "format:quote_unquote": f_append_dangling_quote,
    "sentence:keyword": f_kill_keyword, "words:keywords_specific_position": f_kill_keyword, "words:repeats": f_repeat_top,
}


def seeds():
    """(source, iid, kwargs, prompt, response) of passing responses."""
    out = []
    for f in FIXTURES:
        if f["label"] == "pass":
            out.append(("fixture:" + f["id"], f["check"], f["kwargs"], "fixture prompt", f["response"]))
    rows = {str(r["key"]): r for r in load_dataset_rows()}
    per = collections.defaultdict(list)
    for path in sorted(glob.glob(W + "/audit/work/panel/*__greedy.tsv")):
        cfg = path.split("/")[-1].split("\\")[-1][:-len("__greedy.tsv")]
        recs = [json.loads(x) for x in open(f"{W}/case/panel/{cfg}/greedy.jsonl", encoding="utf-8")]
        bykey = {str(r["key"]): r for r in recs}
        for line in open(path, encoding="utf-8"):
            c = line.rstrip("\n").split("\t")
            if c[15] == "1":
                per[c[4]].append((cfg, c[2], int(c[3])))
    for iid, items in per.items():
        rng.shuffle(items)
        for cfg, key, idx in items[:25]:
            row = rows[key]
            recs = [json.loads(x) for x in open(f"{W}/case/panel/{cfg}/greedy.jsonl", encoding="utf-8")]
            resp = recs[[str(r["key"]) for r in recs].index(key)]["response"]
            out.append((f"panel:{cfg}/greedy/{key}", iid, row["kwargs"][idx], row["prompt"], resp))
    return out


def verdicts(iid, kw, prompt, resp):
    return {"grader_strict": graders.grader_strict(iid, kw, prompt, resp),
            "reference_strict": graders.reference_strict(iid, kw, prompt, resp),
            "replacement": graders.replacement(iid, kw, prompt, resp)}


if __name__ == "__main__":
    S = seeds()
    print(len(S), "passing seeds")
    flips = collections.Counter()
    applied = collections.Counter()
    examples = {}
    with open(W + "/audit/work/metamorphic.tsv", "w", encoding="utf-8", newline="\n") as fh:
        fh.write("kind\tedit\tsource\tiid\tgrader_before\tgrader_after\treference_before\treference_after\treplacement_before\treplacement_after\n")
        for src, iid, kw, prompt, resp in S:
            before = verdicts(iid, kw, prompt, resp)
            for ename, fn in EDITS.items():
                if iid not in IGNORED[ename]:
                    continue
                new = fn(resp)
                if new is None or new == resp:
                    continue
                after = verdicts(iid, kw, prompt, new)
                applied[(ename, iid)] += 1
                fh.write("\t".join(["ignored", ename, src, iid] + [str(x) for g in before for x in (before[g], after[g])]) + "\n")
                for g in before:
                    if before[g] is True and after[g] is not True:
                        flips[("ignored", ename, iid, g)] += 1
                        examples.setdefault(("ignored", ename, iid, g), (src, resp[:200], new[:200]))
            if iid in FORBIDDEN:
                new = FORBIDDEN[iid](resp, kw)
                if new is not None and new != resp:
                    after = verdicts(iid, kw, prompt, new)
                    applied[("forbidden", iid)] += 1
                    fh.write("\t".join(["forbidden", FORBIDDEN[iid].__name__, src, iid] + [str(x) for g in before for x in (before[g], after[g])]) + "\n")
                    for g in before:
                        if before[g] is True and after[g] is True:
                            flips[("forbidden", FORBIDDEN[iid].__name__, iid, g)] += 1
                            examples.setdefault(("forbidden", FORBIDDEN[iid].__name__, iid, g), (src, resp[:200], new[:200]))
    print("edits applied:", sum(applied.values()))
    for g in ["grader_strict", "reference_strict", "replacement"]:
        rows = sorted((k, n) for k, n in flips.items() if k[3] == g)
        print(f"== {g}: {sum(n for _, n in rows)} wrong verdicts after an edit")
        for k, n in rows:
            print(f"   {k[0]:9s} {k[1]:22s} {k[2]:34s} {n}")
    json.dump({"|".join(k): v for k, v in examples.items()}, open(W + "/audit/work/metamorphic_examples.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
