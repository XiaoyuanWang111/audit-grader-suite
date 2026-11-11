"""Measure, on the stored panel, how many strict verdicts each finding changes.

For a finding with a one-line fix, the grader's checker is re-run with only that defect fixed (a minimal-fix
variant) and the verdicts that flip are counted. Writes audit/frozen/finding_shares.json.
"""
import csv
import gzip
import json
import re
import string
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "lib"))
sys.path.insert(0, str(HERE.parent))
import harness as H  # noqa: E402

G = H.grader_modules()
ins, util = G["instructions"], G["util"]
nltk = ins.nltk
emoji = ins.emoji
P = string.punctuation

rows = {str(r["key"]): r for r in H.load_rows()}
verd = list(csv.DictReader(gzip.open(H.W / "audit/frozen/panel_verdicts.tsv.gz", "rt", encoding="utf-8"), delimiter="\t"))
resp_cache = {}


def response(v):
    f = H.CASE / "panel" / v["config"] / f"{v['run']}.jsonl"
    if f not in resp_cache:
        resp_cache[f] = {json.loads(l)["key"]: json.loads(l)["response"] for l in f.read_text(encoding="utf-8").splitlines()}
    return resp_cache[f][v["key"]]


def checker(v):
    row = rows[v["key"]]
    idx = int(v["idx"])
    return H.build_grader_checker(v["iid"], row["kwargs"][idx], row["prompt"])


TYPO = str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'", "—": "-", "–": "-", "…": "..."})


# ------------------------------------------------------------------ minimal fixes: f(checker, text) -> bool
def fix_F03(c, t):
    ws = {w.strip(P + " ").lower() for w in t.split()} & {"and", "but", "for", "nor", "or", "so", "yet"}
    return len(ws) >= c._num_conjunctions


def fix_F05(c, t):
    return len(re.findall(r"\d+(?:[.,]\d+)*", t)) == c._count_numbers


def fix_F07(c, t):
    ws = {w.strip(P + " “”‘’—–") for w in t.translate(TYPO).lower().split()}
    ws.discard("")
    return len(ws) >= c._num_unique_words


def fix_F08(c, t):
    ws = [w.strip(P + " ") for w in t.split()]
    ws = [w for w in ws if w]
    pat = re.compile(r"[぀-ヿ一-鿿]")
    return all(bool(pat.search(w)) for i, w in enumerate(ws) if (i + 1) % c._japanese_position == 0)


def fix_F12(c, t):
    import datetime
    if not c.check_following(t):
        return False
    for d in t.strip().split(","):
        y, m, dd = d.strip().split("-")
        try:
            datetime.date(int(y), int(m), int(dd))
        except ValueError:
            return False
    return True


def fix_F11(c, t):
    header = t.split("\n")[0].strip()
    if not re.match(r'^(ProductID|"ProductID"),[ \t]*(Category|"Category"),[ \t]*(Brand|"Brand"),[ \t]*(Price|"Price"),[ \t]*(Stock|"Stock")$', header):
        return False
    data = list(csv.reader(__import__("io").StringIO(t.replace('"', '"""'))))
    if len(data) != 15 or any(len(r) != 5 for r in data[1:]):
        return False
    return any(re.match(r'".*[^\d\w\s].*"', f) for r in data[1:] for f in r)


def _ends_emoji(s):
    s = s.translate(str.maketrans("", "", P)).strip()
    if not s:
        return False
    el = emoji.emoji_list(s)
    return bool(el) and el[-1]["match_end"] >= len(s) - 1


def fix_F16(c, t):
    ss = util.split_into_sentences(t)
    for i, s in enumerate(ss):
        if _ends_emoji(s):
            continue
        if i < len(ss) - 1:
            nxt = ss[i + 1].translate(str.maketrans("", "", P)).strip()
            el = emoji.emoji_list(nxt)
            if nxt and el and el[0]["match_start"] == 0:
                continue
        return False
    return True


def fix_F17(c, t):
    lines = [ln.expandtabs(4) for ln in t.split("\n") if ln.strip()]
    ind = [len(ln) - len(ln.lstrip(" ")) for ln in lines]
    return all(ind[i + 1] > ind[i] for i in range(len(ind) - 1))


def fix_F19(c, t):
    v = t.translate(str.maketrans("", "", P))
    lines = [ln for ln in v.strip().split("\n") if ln.strip()]
    return all(len(ln.split()) <= 1 for ln in lines) and len(lines) >= 1


def fix_F20(c, t):
    lines = [ln for ln in t.split("\n") if ln.strip()]
    return c.check_following("\n".join(lines))


def fix_F21(c, t):
    if c._strict:
        return t.strip().lower() in [o.lower() for o in c._options]
    return c.check_following(t)


def fix_F22(c, t):
    labels = ["My Answer:", "My Conclusion:", "Future Outlook:"]
    if not all(lb in t for lb in labels):
        return False
    pos = [t.index(lb) for lb in labels]
    if not pos[0] < pos[1] < pos[2]:
        return False
    return not any(ph in t for ph in ("[answer]", "[conclusion]", "[outlook]"))


def fix_F28(c, t):
    t2 = re.sub(r"(?<=[A-Za-z])['’](?=[A-Za-z])", "", t)
    return c.check_following(t2)


def fix_F29(c, t):
    ss = util.split_into_sentences(t)
    d = sum(1 for s in ss if s.endswith("."))
    q = sum(1 for s in ss if s.endswith("?"))
    e = sum(1 for s in ss if s.endswith("!"))
    if c.id == "ratio:sentence_type":
        return q >= 1 and d == 2 * q
    return d == q == e and d >= 1


def fix_F31(c, t):
    req = c._prompt_to_repeat.split()
    got = t.split()
    return c.check_following(t) and bool(got) and got[0].strip(P).lower() != req[0].strip(P).lower()


def fix_F32(c, t):
    words = c._prompt_to_repeat.split()
    return t.strip().lower() == " ".join(words[c._n_start:c._n_end + 1]).lower()


def fix_F33(c, t):
    prev = -1
    for s in util.split_into_sentences(t):
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


def fix_F34(c, t):
    return c.check_following(t.translate(TYPO))


def fix_F35(c, t):
    return c.check_following(" ".join(w for w in t.split() if any(ch.isalnum() for ch in w)))


def fix_F36(c, t):
    if c.id == "words:paragraph_last_first":
        for p in t.split("\n"):
            ws = [w.strip(P) for w in p.lower().split()]
            ws = [w for w in ws if w]
            if ws and ws[0] != ws[-1]:
                return False
        return True
    ss = util.split_into_sentences(t)
    for a, b in zip(ss, ss[1:]):
        wa = [w.strip(P) for w in a.split() if w.strip(P)]
        wb = [w.strip(P) for w in b.split() if w.strip(P)]
        if not wa or not wb or wa[-1].lower() != wb[0].lower():
            return False
    return True


def fix_F39(c, t):
    return c.check_following(re.sub(r"([.!?])([”’])", r'\1"', t))


def fix_F15(c, t):  # the reference's fix
    ss = util.split_into_sentences(t)
    if len(ss) != 26:
        return False
    for i, s in enumerate(ss):
        st = s.lstrip(P + string.whitespace)
        if not st or st[0].lower() != chr(97 + i):
            return False
    return True


FIXES = {
    "F-03": (["count:conjunctions"], fix_F03),
    "F-05": (["count:numbers"], fix_F05),
    "F-07": (["count:unique_word_count"], fix_F07),
    "F-08": (["count:words_japanese"], fix_F08),
    "F-11": (["custom:csv_special_character"], fix_F11),
    "F-12": (["custom:date_format_list"], fix_F12),
    "F-15": (["custom:sentence_alphabet"], fix_F15),
    "F-16": (["format:emoji"], fix_F16),
    "F-17": (["format:line_indent"], fix_F17),
    "F-19": (["format:newline"], fix_F19),
    "F-20": (["format:no_bullets_bullets"], fix_F20),
    "F-21": (["format:options"], fix_F21),
    "F-22": (["format:output_template"], fix_F22),
    "F-28": (["format:title_case"], fix_F28),
    "F-29": (["ratio:sentence_balance", "ratio:sentence_type"], fix_F29),
    "F-31": (["repeat:repeat_change"], fix_F31),
    "F-32": (["repeat:repeat_span"], fix_F32),
    "F-33": (["sentence:alliteration_increment"], fix_F33),
    "F-34": (["words:alphabet", "words:no_consecutive", "words:prime_lengths", "words:repeats", "words:last_first",
              "words:paragraph_last_first", "count:unique_word_count", "custom:sentence_alphabet", "words:start_verb",
              "words:words_position", "words:consonants", "words:odd_even_syllables", "words:palindrome"], fix_F34),
    "F-35": (["words:consonants", "words:prime_lengths", "words:alphabet", "words:no_consecutive", "words:odd_even_syllables"], fix_F35),
    "F-36": (["words:paragraph_last_first", "words:last_first"], fix_F36),
    "F-39": (["format:emoji", "sentence:keyword", "sentence:increment", "sentence:alliteration_increment", "words:last_first",
              "words:keywords_specific_position", "ratio:sentence_type", "ratio:sentence_balance", "ratio:sentence_words",
              "custom:sentence_alphabet"], fix_F39),
}


def main():
    out = {}
    for fid, (checks, fn) in FIXES.items():
        flips = Counter()
        n = 0
        ex = []
        for v in verd:
            if v["iid"] not in checks or v["unclosed"] == "1":
                continue
            n += 1
            t = response(v)
            if not t.strip():
                continue
            c = checker(v)
            try:
                new = bool(fn(c, t))
            except Exception as e:  # noqa: BLE001
                new = None
            old = v["g_strict"] == "1"
            if new is not None and new != old:
                flips["to_pass" if new else "to_fail"] += 1
                # agreement of the flipped verdict with the replacement (contract) verdict
                flips["agrees_with_replacement" if (v["rep"] == "1") == new else "disagrees_with_replacement"] += 1
                if len(ex) < 3:
                    ex.append(f"{v['config']}/{v['run']}/key{v['key']}")
        out[fid] = {"checks": checks, "verdicts_in_scope": n, "flips": dict(flips),
                    "share_of_all_verdicts_pct": round(100 * (flips["to_pass"] + flips["to_fail"]) / len(verd), 3),
                    "examples": ex}
        print(fid, out[fid]["verdicts_in_scope"], dict(flips), ex[:2])
    # direct counts
    sp = [v for v in verd if v["iid"] == "repeat:repeat_span"]
    cap = [v for v in verd if v["iid"] == "custom:european_capitals_sort"]
    kyiv = sum(1 for v in cap if re.search(r"\bKyiv\b|\bKiev\b", response(v)))
    out["F-13"] = {"responses": len(cap), "mention_kyiv": kyiv, "grader_passes": sum(1 for v in cap if v["g_strict"] == "1"),
                   "replacement_passes": sum(1 for v in cap if v["rep"] == "1")}
    print("F-13", out["F-13"])
    unc = [v for v in verd if v["unclosed"] == "1"]
    out["F-41"] = {"verdicts": len(unc), "grader_passes": sum(1 for v in unc if v["g_strict"] == "1")}
    lp = [v for v in verd if v["g_loose"] == "1" and v["g_strict"] == "0"]
    out["F-42"] = {"loose_only_passes": len(lp), "of_which_contract_fails": sum(1 for v in lp if v["rep"] == "0")}
    print("F-41", out["F-41"], "F-42", out["F-42"])
    json.dump(out, open(H.W / "audit/frozen/finding_shares.json", "w", encoding="utf-8"), indent=1)


if __name__ == "__main__":
    main()
