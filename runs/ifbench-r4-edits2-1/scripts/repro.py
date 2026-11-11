"""Reproduce a verdict of the grader under audit (and, for comparison, the reference and the replacement).

  repro.py <fixture_id>                 one fixture from audit/tests/fixtures_data.py
  repro.py --loose <n>                  loose-transform probe n (0-based) from audit/scripts/stress.py
  repro.py --panel <config>/<run>/<key> a stored panel response (prints verdicts; prints an excerpt only
                                        when the response has no unclosed reasoning)
  repro.py --lstrip <config>/<run>/<key> grader verdicts on the stored response and on it without leading whitespace
Run from W with NLTK_DATA=W/case/deps/nltk_data and W/.venv/Scripts/python.exe.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "lib"))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / "tests"))
import harness as H  # noqa: E402


def v(x):
    return "pass" if x is True else ("fail" if x is False else str(x))


def safe(fn):
    try:
        return v(bool(fn()))
    except Exception as e:  # noqa: BLE001
        return f"exception {type(e).__name__}: {e}"


def fixture(fid):
    from fixture_runner import ALL, resolve
    from replacement import contract_grader as R

    f = dict(ALL)[fid]
    kw, prompt = resolve(f)
    shown = {k: (val if not (isinstance(val, str) and len(val) > 60) else val[:60] + "...") for k, val in kw.items() if val is not None}
    print(f"fixture: {fid}")
    print(f"check: {f['check']}   kwargs: {json.dumps(shown, ensure_ascii=False)}" + (f"   (dataset key {f['key']})" if f["key"] else ""))
    print(f"response: {f['response']!r}")
    print(f"contract: {f['label']}  ({f['kind']}{' ' + ','.join(f['decisions']) if f['decisions'] else ''})")
    print(f"grader: {safe(lambda: H.check_grader(f['check'], kw, f['response'], prompt))}")
    print(f"reference: {safe(lambda: H.check_reference(f['check'], kw, f['response'], prompt))}")
    print(f"replacement: {safe(lambda: R.check(f['check'], kw, f['response'], prompt))}")


def loose(n):
    from stress import LOOSE_PROBES
    from replacement import contract_grader as R

    iid, key, resp = LOOSE_PROBES[n]
    row = H.row_by_key(H.load_rows(), key)
    idx = row["instruction_id_list"].index(iid)
    one = {"key": row["key"], "prompt": row["prompt"], "instruction_id_list": [iid], "kwargs": [row["kwargs"][idx]]}
    print(f"check {iid} (dataset key {key})\nresponse {resp!r}")
    print(f"grader strict: {v(H.grade_grader(one, resp, 'strict')[0])}; grader loose: {v(H.grade_grader(one, resp, 'loose')[0])}; "
          f"contract (replacement): {v(R.check(iid, row['kwargs'][idx], resp, row['prompt']))}")


def _stored(spec):
    cfg, run, key = spec.split("/")
    for line in (H.CASE / "panel" / cfg / f"{run}.jsonl").read_text(encoding="utf-8").splitlines():
        d = json.loads(line)
        if str(d["key"]) == key:
            return d
    raise KeyError(spec)


def panel(spec):
    from replacement import contract_grader as R

    d = _stored(spec)
    row = H.row_by_key(H.load_rows(), d["key"])
    unclosed = R.extraction_failure(d["raw_response"])
    print(f"{spec}: finish_reason={d['finish_reason']} num_tokens={d['num_tokens']} reasoning_never_closed={unclosed} "
          f"response_chars={len(d['response'])}")
    if not unclosed:
        print(f"excerpt {d['response'][:120]!r}")
    gs = H.grade_grader(row, d["response"], "strict")
    gl = H.grade_grader(row, d["response"], "loose")
    rs = H.grade_reference(row, d["response"], "strict")
    for i, (iid, kw) in enumerate(zip(row["instruction_id_list"], row["kwargs"])):
        rep = False if unclosed else R.check(iid, kw, d["response"], row["prompt"])
        print(f"  {iid}: grader strict: {v(gs[i])}; grader loose: {v(gl[i])}; reference strict: {v(rs[i])}; replacement: {v(rep)}")


def lstrip(spec):
    d = _stored(spec)
    row = H.row_by_key(H.load_rows(), d["key"])
    a = H.grade_grader(row, d["response"], "strict")
    b = H.grade_grader(row, d["response"].lstrip(), "strict")
    print(f"{spec}: leading chars {d['response'][:3]!r}")
    for iid, x, y in zip(row["instruction_id_list"], a, b):
        print(f"  {iid}: grader on stored response: {v(x)}; grader without leading whitespace: {v(y)}")


if __name__ == "__main__":
    if sys.argv[1] == "--loose":
        loose(int(sys.argv[2]))
    elif sys.argv[1] == "--panel":
        panel(sys.argv[2])
    elif sys.argv[1] == "--lstrip":
        lstrip(sys.argv[2])
    else:
        fixture(sys.argv[1])
