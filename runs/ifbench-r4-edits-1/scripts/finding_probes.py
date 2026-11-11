"""Share of panel verdicts each checker finding affects.

For each finding, `patched(kw, prompt, response)` is the grader's checker with
only that defect fixed (or, where noted, the reference's fixed checker, or the
replacement's logic for that check when no minimal patch is meaningful). The
probe counts panel verdicts (strict harness, extraction failures excluded)
where the patched verdict differs from the grader's.
Writes audit/work/finding_shares.json.
"""
import collections
import json
import re
import string

import common
import replacement as R
from IFBench import instructions as GI
from IFBench import instructions_util as GU
from ifbench import instructions as RI

PUN = "".join(string.punctuation) + " "


def build(cls, kw, prompt):
    inst = cls("x")
    inst.build_description(**{k: v for k, v in kw.items() if v is not None})
    a = inst.get_instruction_args()
    if a and "prompt" in a:
        inst.build_description(prompt=prompt)
    return inst


def ref(cls_name):
    return lambda kw, p, t: build(getattr(RI, cls_name), kw, p).check_following(t)


def repl(check, **opts):
    return lambda kw, p, t: R.grade(check, kw, p, t, opts or None)


def p_conj(kw, p, t):
    n = kw["small_n"]
    found = {w.strip(PUN).lower() for w in t.split()} & {"and", "but", "for", "nor", "or", "so", "yet"}
    return len(found) >= n


def p_num(kw, p, t):
    t = re.sub(r"(?<=\d)[-–/:](?=\d)", " ", t)
    t = t.translate(str.maketrans("", "", string.punctuation))
    return len(re.findall(r"\d+", t)) == kw["N"]


TOK = re.compile(r"\w+(?:['’]\w+)*")


def p_wcr(kw, p, t):
    n = len(TOK.findall(t))
    return kw["min_words"] <= n <= kw["max_words"]


def p_stop(kw, p, t):
    import nltk
    toks = TOK.findall(t.replace("’", "'"))
    if not toks:
        return False
    sw = set(nltk.corpus.stopwords.words("english"))
    return 100 * sum(1 for x in toks if x.lower() in sw) / len(toks) <= kw["percentage"]


def _end(s):
    return s.rstrip(" \"')]*_”’")


def p_stype(kw, p, t):
    ss = GU.split_into_sentences(t)
    d = sum(1 for s in ss if _end(s).endswith("."))
    q = sum(1 for s in ss if _end(s).endswith("?"))
    return q >= 1 and d == 2 * q


def p_stype_zero_only(kw, p, t):
    ss = GU.split_into_sentences(t)
    d = sum(1 for s in ss if s.endswith("."))
    q = sum(1 for s in ss if s.endswith("?"))
    return q >= 1 and d == 2 * q


def p_sbal(kw, p, t):
    ss = GU.split_into_sentences(t)
    c = [sum(1 for s in ss if _end(s).endswith(m)) for m in ".?!"]
    return c[0] == c[1] == c[2]


def p_indent(kw, p, t):
    lines = [ln.expandtabs(4) for ln in t.split("\n") if ln.strip()]
    ind = [len(ln) - len(ln.lstrip()) for ln in lines]
    return all(b > a for a, b in zip(ind, ind[1:]))


def p_newline(kw, p, t):
    v = t.translate(str.maketrans("", "", string.punctuation))
    lines = [ln for ln in v.strip().split("\n") if ln.strip()]
    return len(lines) == len(v.strip().split())


def p_list(kw, p, t):
    sep = kw["sep"]
    return len(re.findall(r"(?:^|(?<=\s))" + re.escape(sep) + r"(?=\s|$)", t, flags=re.M)) >= 2


def p_nbb(kw, p, t):
    lines = [ln for ln in t.split("\n") if ln.strip()]
    first = next((i for i, ln in enumerate(lines) if ln.strip().startswith("*")), None)
    if first is None:
        return False
    nper = sum(1 for ln in lines[:first] for s in GU.split_into_sentences(ln.strip()) if s.endswith("."))
    return nper >= 2 and sum(1 for ln in lines[first:] if ln.strip().startswith("*")) >= 2


def p_options(kw, p, t):
    inst = build(GI.OptionsResponseChecker, kw, p)
    v = t.strip().replace("’", "'")
    if inst._strict:
        return v.lower() in [o.lower() for o in inst._options]
    return inst.check_following(v)


def p_paren(kw, p, t):
    return R.grade("format:parentheses", kw, p, t)


def p_quotes(kw, p, t):
    v = R.norm_quotes(t)
    v = re.sub(r"(?<=[A-Za-z0-9])'(?=[A-Za-z0-9])", "", v)
    return build(GI.NestedQuotesChecker, kw, p).check_following(v)


def p_allit(kw, p, t):
    prev = -1
    for s in GU.split_into_sentences(t):
        ws = [w.lstrip(PUN).lower() for w in s.split()]
        ws = [w for w in ws if w]
        best, run = (1 if ws else 0), 1
        for a, b in zip(ws, ws[1:]):
            run = run + 1 if a[0] == b[0] else 1
            best = max(best, run)
        if best <= prev:
            return False
        prev = best
    return True


def p_capitals(kw, p, t):
    order = ["Reykjavik", "Helsinki", "Oslo", "Tallinn", "Stockholm", "Riga", "Moscow", "Copenhagen", "Vilnius", "Minsk",
             "Dublin", "Berlin", "Amsterdam", "Warsaw", "London", "Brussels", "Kyiv", "Prague", "Luxembourg", "Paris",
             "Vienna", "Bratislava", "Budapest", "Vaduz", "Chisinau", "Bern", "Ljubljana", "Zagreb"]
    caps = [c.strip() for c in R._ascii(t).split(",") if c.strip()]
    return caps == order


def p_africa(kw, p, t):
    inst = build(GI.ReverseNewlineChecker, kw, p)
    v = "\n".join(re.sub(r"^\s*\d+[.)]\s*", "", ln) for ln in t.split("\n"))
    lines = [ln.strip(PUN) for ln in v.split("\n") if ln.strip(PUN)]
    if not lines or "Zimbabwe" not in lines[0]:
        return False
    return inst.check_following(v)


def p_csvspecial(kw, p, t):
    inst = build(GI.SpecialCharacterCSVChecker, kw, p)
    if not inst.check_following(t):
        return False
    import csv
    import io
    data = list(csv.reader(io.StringIO(t.replace('"', '"""'))))
    return all(len(r) == 5 for r in data[1:])


def p_date(kw, p, t):
    inst = build(GI.DateFormatListChecker, kw, p)
    if not inst.check_following(t):
        return False
    return all(int(d.strip().split("-")[1]) >= 1 and int(d.strip().split("-")[2]) >= 1 for d in t.strip().split(","))


def p_mcq(kw, p, t):
    return R.grade("custom:mcq_count_length", kw, p, t)


def p_rchange(kw, p, t):
    a, b = kw["prompt_to_repeat"].split(), t.split()
    return len(a) == len(b) and a[1:] == b[1:] and a[0] != b[0]


def p_markup(check, cls):
    def f(kw, p, t):
        v = R.HTML_TAG.sub("", t)
        v = re.sub(r"(?<![\w*])(\*\*|__|\*|_)(?=\w)|(?<=\w)(\*\*|__|\*|_)(?![\w*])", "", v)
        return build(cls, kw, p).check_following(v)
    return f


PROBES = [
    ("F-CONJ", "count:conjunctions", p_conj, "minimal patch"),
    ("F-KWM", "count:keywords_multiple", ref("KeywordsMultipleChecker"), "reference checker"),
    ("F-NUM", "count:numbers", p_num, "minimal patch"),
    ("F-CONTRACTION", "count:word_count_range", p_wcr, "minimal patch"),
    ("F-CONTRACTION", "ratio:stop_words", p_stop, "minimal patch"),
    ("F-STYPE", "ratio:sentence_type", p_stype, "minimal patch (both defects)"),
    ("F-STYPE(0:0 only)", "ratio:sentence_type", p_stype_zero_only, "minimal patch"),
    ("F-SBAL", "ratio:sentence_balance", p_sbal, "minimal patch"),
    ("F-SWORDS", "ratio:sentence_words", ref("CharacterCountUniqueWordsChecker"), "reference checker"),
    ("F-INDENT", "format:line_indent", p_indent, "minimal patch"),
    ("F-NEWLINE", "format:newline", p_newline, "minimal patch"),
    ("F-LIST", "format:list", p_list, "minimal patch"),
    ("F-NBB", "format:no_bullets_bullets", p_nbb, "minimal patch"),
    ("F-OPTIONS", "format:options", p_options, "minimal patch"),
    ("F-TEMPLATE", "format:output_template", repl("format:output_template"), "replacement logic"),
    ("F-PAREN", "format:parentheses", p_paren, "replacement logic"),
    ("F-QU", "format:quote_unquote", repl("format:quote_unquote"), "replacement logic"),
    ("F-QUOTES", "format:quotes", p_quotes, "minimal patch"),
    ("F-SUBB", "format:sub-bullets", repl("format:sub-bullets"), "replacement logic"),
    ("F-THESIS", "format:thesis", repl("format:thesis", **{"D-section": "whole"}), "replacement logic, whole-response section"),
    ("F-TITLE", "format:title_case", repl("format:title_case"), "replacement logic"),
    ("F-ALLIT", "sentence:alliteration_increment", p_allit, "minimal patch"),
    ("F-CAPITALS", "custom:european_capitals_sort", p_capitals, "minimal patch"),
    ("F-AFRICA", "custom:reverse_newline", p_africa, "minimal patch"),
    ("F-ALPHA-SENT", "custom:sentence_alphabet", ref("SentenceAlphabetChecker"), "reference checker"),
    ("F-CSVSPECIAL", "custom:csv_special_character", p_csvspecial, "minimal patch"),
    ("F-DATE", "custom:date_format_list", p_date, "minimal patch"),
    ("F-MCQ", "custom:mcq_count_length", p_mcq, "replacement logic"),
    ("F-RCHANGE", "repeat:repeat_change", p_rchange, "minimal patch"),
    ("F-RSPAN", "repeat:repeat_span", ref("RepeatSpanChecker"), "reference checker"),
    ("F-VERB", "words:start_verb", repl("words:start_verb"), "replacement logic (APPROX)"),
    ("F-WPOS", "words:words_position", ref("WordsPositionChecker"), "reference checker"),
    ("F-MARKUP", "count:person_names", p_markup("count:person_names", GI.PersonNameCountChecker), "markup stripped"),
    ("F-MARKUP", "count:pronouns", p_markup("count:pronouns", GI.PronounCountChecker), "markup stripped"),
    ("F-MARKUP", "words:no_consecutive", p_markup("words:no_consecutive", GI.NoConsecutiveFirstLetterChecker), "markup stripped"),
]

if __name__ == "__main__":
    rows = common.rows()
    order = common.row_list()
    stored = {}
    for f in (common.W / "audit" / "work" / "panel").glob("*.jsonl"):
        stored[f.stem] = [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines()]
    by_check = collections.defaultdict(list)
    for fid, check, fn, how in PROBES:
        by_check[check].append((fid, fn, how))
    res = collections.defaultdict(lambda: collections.Counter())
    examples = collections.defaultdict(list)
    for f in sorted((common.CASE / "panel").glob("*/*.jsonl")):
        stem = f"{f.parent.name}__{f.stem}"
        st = stored[stem]
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines()):
            ent = st[i]
            if ent["extraction_failure"]:
                continue
            rec = json.loads(line)
            r = rows[order[i]]
            t = rec["response"]
            for j, (check, kw) in enumerate(zip(r["instruction_id_list"], r["kwargs"])):
                for fid, fn, how in by_check.get(check, []):
                    g = ent["checks"][j]["gs"]
                    try:
                        v = bool(t.strip()) and bool(fn(kw, r["prompt"], t))
                    except Exception as e:  # noqa: BLE001
                        v = None
                    key = (fid, check)
                    res[key]["n"] += 1
                    if v is None:
                        res[key]["probe_error"] += 1
                    elif v != g:
                        res[key]["flips"] += 1
                        res[key]["grader_pass_to_fail" if g else "grader_fail_to_pass"] += 1
                        if v == ent["checks"][j]["rep"]:
                            res[key]["flip_agrees_with_replacement"] += 1
                        if len(examples[key]) < 5:
                            examples[key].append(dict(run=stem, key=r["key"], grader=g, patched=v))
    out = []
    for fid, check, fn, how in PROBES:
        c = res[(fid, check)]
        out.append(dict(finding=fid, check=check, probe=how, verdicts=c["n"], flips=c["flips"],
                        share_of_check=c["flips"] / c["n"] if c["n"] else 0, share_of_all=c["flips"] / 78432,
                        pass_to_fail=c["grader_pass_to_fail"], fail_to_pass=c["grader_fail_to_pass"],
                        agrees_with_replacement=c["flip_agrees_with_replacement"], probe_errors=c["probe_error"],
                        examples=examples[(fid, check)]))
        print(f"{fid:<18} {check:<32} n={c['n']:>5} flips={c['flips']:>4} ({(c['flips'] / c['n'] if c['n'] else 0):.3f}) "
              f"p->f {c['grader_pass_to_fail']:>4} f->p {c['grader_fail_to_pass']:>4} err={c['probe_error']} | {how}")
    (common.W / "audit" / "work" / "finding_shares.json").write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
