"""Share of panel verdicts each checker finding affects: apply the minimal fix for that finding to
the grader's own checker (everything else unchanged) and count strict verdicts that change.

Findings whose fix is decision-laden are measured against the replacement under the most lenient
reading instead (F11, F15, F21: grader passes that fail under every reading).
Output: audit/work/finding_shares.json and a printed table.
"""
import collections
import glob
import json
import re
import string
import sys

sys.path.insert(0, "<W>/audit/scripts")
import graders  # noqa: E402,F401  (paths, NLTK_DATA, download block)
import emoji  # noqa: E402
import nltk  # noqa: E402
from IFBench import instructions as G  # noqa: E402
from IFBench import instructions_util as U  # noqa: E402
import replacement as REP  # noqa: E402
from run_panel import load_dataset_rows  # noqa: E402

W = "<W>"
P = string.punctuation
_TYPO = str.maketrans({"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"'})


def build(iid, kw):
    from IFBench import instructions_registry as reg
    inst = reg.INSTRUCTION_DICT[iid](iid)
    inst.build_description(**kw)
    return inst


# ---- fixed check functions: (inst, value) -> bool
def f01(inst, v):
    ws = inst._prompt_to_repeat.split()
    return v.strip().lower() == " ".join(ws[inst._n_start:inst._n_end + 1]).strip().lower()


def f02(inst, v):
    ss = U.split_into_sentences(v)
    ws = v.lower().translate(str.maketrans("", "", P)).split() if False else " ".join(ss).lower().translate(str.maketrans("", "", P)).split()
    return inst.check_following(v) and len(ws) == len(set(ws))


def f03(inst, v):
    for k, c in zip([inst._keyword1, inst._keyword2, inst._keyword3, inst._keyword4, inst._keyword5], [1, 2, 3, 5, 7]):
        if len(re.findall(r"\b" + re.escape(k) + r"\b", v, re.I)) != c:
            return False
    return True


def f04(inst, v):
    s = {w.strip(P + " ").lower() for w in v.split()} & {"and", "but", "for", "nor", "or", "so", "yet"}
    return len(s) >= inst._num_conjunctions


def f05_type(inst, v):
    ss = U.split_into_sentences(v)
    d = sum(s.endswith(".") for s in ss)
    q = sum(s.endswith("?") for s in ss)
    return q >= 1 and d == 2 * q


def f05_bal(inst, v):
    ss = U.split_into_sentences(v)
    c = [sum(s.endswith(e) for s in ss) for e in ".?!"]
    return min(c) >= 1 and c[0] == c[1] == c[2]


def f06(inst, v):
    prev = -1
    for s in U.split_into_sentences(v):
        ws = [w.lstrip(P + " ") for w in s.lower().split()]
        ws = [w for w in ws if w]
        best = cur = 1 if ws else 0
        for a, b in zip(ws, ws[1:]):
            cur = cur + 1 if a[0] == b[0] else 1
            best = max(best, cur)
        if best <= prev:
            return False
        prev = best
    return True


def f07(inst, v):
    v2 = v.translate(str.maketrans("", "", P))
    lines = [ln for ln in v2.strip().split("\n") if ln.strip()]
    return bool(lines) and all(len(ln.split()) == 1 for ln in lines)


def f08(inst, v):
    lines = [ln.expandtabs(4) for ln in v.split("\n") if ln.strip()]
    ind = [len(ln) - len(ln.lstrip(" ")) for ln in lines]
    return all(b > a for a, b in zip(ind, ind[1:]))


def f09(inst, v):
    v = v.translate(_TYPO)
    v = v.replace("'\"'", "")
    v = "".join(v.split())
    if re.search(r'"[^\w"]*"', v.replace('""', '"x"', 0)) and '""' not in v:
        # a quote followed only by punctuation before the next opening quote
        spans = [m for m in re.finditer(r'"[^"]*"', v)]
        for a, b in zip(spans, spans[1:]):
            if not re.search(r"\w", v[a.end():b.start()]):
                return False
    if '""' in v:
        return False
    st = v.strip(string.digits + P.replace('"', ""))
    return not (st and st[-1] == '"')


def f10(inst, v):
    return sum(1 for ln in v.split("\n") if ln.lstrip().startswith(inst._bullet_marker)) >= 2


def f12(inst, v):
    if not re.search(r"(?m)^\s*\*(?!\*)", v):
        return False
    return inst.check_following(v.replace("**", ""))


def f13(inst, v):
    lines = v.split("\n")
    in_sent, n_s, n_b = True, 0, 0
    for ln in lines:
        if ln.strip().startswith("*"):
            in_sent = False
            if n_s < 2:
                return False
            n_b += 1
        elif in_sent:
            n_s += sum(1 for s in U.split_into_sentences(ln.strip()) if s.endswith("."))
        elif ln.strip():
            return False
    return n_b >= 2


def f14(inst, v):
    return "elgae dlab" in v.lower() and "bald eagle" not in v.lower()


def f17(inst, v):
    header = v.split("\n")[0].strip()
    if not re.match(r'^(ProductID|"ProductID"),[ \t]*(Category|"Category"),[ \t]*(Brand|"Brand"),[ \t]*(Price|"Price"),[ \t]*(Stock|"Stock")$', header):
        return False
    import csv
    import io
    data = list(csv.reader(io.StringIO(v.replace('"', '"""'))))
    if len(data) != 15 or any(len(r) != 5 for r in data[1:]):
        return False
    return any(re.match(r'".*[^\d\w\s].*"', f) for r in data[1:] for f in r)


def f19(inst, v):
    if not inst.check_following(v):
        return False
    return all(re.match(r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$", d.strip()) for d in v.strip().split(","))


MINOR = REP.MINOR


def f20(inst, v):
    toks = U.nltk.word_tokenize(v)
    first = True
    for w in toks:
        if not w or not w[0].isalpha():
            if w in ".!?":
                first = True
            continue
        if w.lower() in ("n't",):
            continue
        if not first and w.lower() in MINOR:
            first = False
            continue
        first = False
        if w[0].islower():
            return False
    return True


def f22(inst, v):
    a, b = inst._prompt_to_repeat.split(), v.split()
    return inst.check_following(v) and bool(b) and b[0].strip(P).lower() != a[0].strip(P).lower()


def f23(inst, v):
    if inst._strict:
        return v.strip().lower() in [o.lower() for o in inst._options]
    return inst.check_following(v)


def f24(inst, v):
    return REP.c_parentheses(v, {}, REP.DEFAULTS)


def f25(inst, v):
    ws = [w for w in v.translate(str.maketrans("", "", P)).split() if any(ch.isalnum() for ch in w)]
    return all(len(w) in {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37} for w in ws)


def f26_last(inst, v):
    ss = U.split_into_sentences(v)
    for a, b in zip(ss, ss[1:]):
        wa = [w.strip(P) for w in a.split() if w.strip(P)]
        wb = [w.strip(P) for w in b.split() if w.strip(P)]
        if not wa or not wb or wa[-1].lower() != wb[0].lower():
            return False
    return True


def f26_para(inst, v):
    for p in v.split("\n"):
        ws = [w.strip(P) for w in p.strip().lower().split() if w.strip(P)]
        if ws and ws[0] != ws[-1]:
            return False
    return True


def _ends_emoji(s):
    s = s.translate(str.maketrans("", "", P)).strip()
    e = emoji.emoji_list(s)
    return bool(e) and e[-1]["match_end"] >= len(s) - 1


def _starts_emoji(s):
    s = s.translate(str.maketrans("", "", P)).strip()
    e = emoji.emoji_list(s)
    return bool(e) and e[0]["match_start"] == 0


def f27(inst, v):
    ss = U.split_into_sentences(v)
    for i, s in enumerate(ss):
        if not s.translate(str.maketrans("", "", P)).strip():
            return False
        if not _ends_emoji(s):
            if i < len(ss) - 1 and _starts_emoji(ss[i + 1]):
                continue
            return False
    return True


def f28(inst, v):
    t = nltk.word_tokenize(v)
    if not t:
        return False
    # the grader's own tagging OR the tagging with the first token lower-cased: a capitalized
    # imperative is tagged NNP by the perceptron tagger ("Imagine" -> NNP, "imagine" -> VB)
    return "VB" in nltk.pos_tag(t)[0][1] or "VB" in nltk.pos_tag([t[0].lower()] + t[1:])[0][1]


FIX = {
    "F01": ("repeat:repeat_span", f01), "F02": ("ratio:sentence_words", f02), "F03": ("count:keywords_multiple", f03),
    "F04": ("count:conjunctions", f04), "F05a": ("ratio:sentence_type", f05_type), "F05b": ("ratio:sentence_balance", f05_bal),
    "F06": ("sentence:alliteration_increment", f06), "F07": ("format:newline", f07), "F08": ("format:line_indent", f08),
    "F09": ("format:quote_unquote", f09), "F10": ("format:list", f10), "F12": ("format:sub-bullets", f12),
    "F13": ("format:no_bullets_bullets", f13), "F14": ("custom:character_reverse", f14),
    "F17": ("custom:csv_special_character", f17), "F19": ("custom:date_format_list", f19),
    "F20": ("format:title_case", f20), "F22": ("repeat:repeat_change", f22), "F23": ("format:options", f23),
    "F24": ("format:parentheses", f24), "F25": ("words:prime_lengths", f25), "F26a": ("words:last_first", f26_last),
    "F26b": ("words:paragraph_last_first", f26_para), "F27": ("format:emoji", f27), "F28": ("words:start_verb", f28),
}

if __name__ == "__main__":
    rows = load_dataset_rows()
    resp = {}
    for path in glob.glob(W + "/case/panel/*/*.jsonl"):
        cfg = path.replace("\\", "/").split("/")[-2]
        run = path.replace("\\", "/").split("/")[-1][:-6]
        for line in open(path, encoding="utf-8"):
            r = json.loads(line)
            resp[(cfg, run, str(r["key"]))] = r["response"]
    panel = []
    for path in sorted(glob.glob(W + "/audit/work/panel/*.tsv")):
        for line in open(path, encoding="utf-8"):
            c = line.rstrip("\n").split("\t")
            panel.append(c)
    rowmap = {str(r["key"]): r for r in rows}
    out = {}
    for fid, (iid, fn) in FIX.items():
        n = chg = to_fail = to_pass = 0
        ex = None
        for c in panel:
            if c[4] != iid:
                continue
            n += 1
            row = rowmap[c[2]]
            kw = row["kwargs"][int(c[3])]
            v = resp[(c[0], c[1], c[2])]
            inst = build(iid, kw)
            new = bool(v and v.strip()) and bool(fn(inst, v))
            old = c[11] == "1"
            if new != old:
                chg += 1
                to_fail += old and not new
                to_pass += new and not old
                ex = ex or f"{c[0]}/{c[1]} key {c[2]}"
        out[fid] = dict(check=iid, verdicts=n, changed=chg, pass_to_fail=to_fail, fail_to_pass=to_pass, example=ex)
    # lenient-reading measurements from the replacement switches stored in the panel files
    lenient = {"F11": ("format:thesis", "d_section"), "F15": ("custom:reverse_newline", "d_africa_complete"),
               "F21": ("format:output_template", "d_template_outside")}
    for fid, (iid, swn) in lenient.items():
        n = chg = 0
        ex = None
        for c in panel:
            if c[4] != iid:
                continue
            n += 1
            alts = json.loads(c[16])
            if c[11] == "1" and c[15] == "0" and alts.get(swn, "0") == "0":
                chg += 1
                ex = ex or f"{c[0]}/{c[1]} key {c[2]}"
        out[fid] = dict(check=iid, verdicts=n, changed=chg, pass_to_fail=chg, fail_to_pass=0, example=ex,
                        method="grader pass, replacement fails under both readings of " + swn)
    json.dump(out, open(W + "/audit/work/finding_shares.json", "w", encoding="utf-8"), indent=1)
    for fid, d in out.items():
        print(f"{fid:5s} {d['check']:34s} verdicts {d['verdicts']:5d} changed {d['changed']:5d} "
              f"({100 * d['changed'] / d['verdicts']:5.1f}%) pass->fail {d['pass_to_fail']:5d} fail->pass {d['fail_to_pass']:5d}  e.g. {d['example']}")
