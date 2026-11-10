"""Shared helpers for the audit: pinned package copies, dataset rows, grader and reference verdicts.

The grader and the reference are imported from byte-identical copies under
audit/work/pkgs/ (checked against case/MANIFEST.sha256 by verify_pins), because importing
them from case/ would create case/grader/IFBench/.nltk_data and __pycache__ folders
(instructions.py makes a .nltk_data folder next to itself at import time).

Dataset rows are read with pyarrow's to_pylist(), which gives the same Python types as
datasets.load_dataset (int64 columns stay int, double columns are float, nulls are None).
"""
import hashlib
import json
import os
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CASE = os.path.join(W, "case")
PKG_G = os.path.join(W, "audit", "work", "pkgs", "grader")
PKG_R = os.path.join(W, "audit", "work", "pkgs", "reference")
os.environ["NLTK_DATA"] = os.path.join(CASE, "deps", "nltk_data")
sys.dont_write_bytecode = True
for p in (PKG_R, PKG_G):
    if p not in sys.path:
        sys.path.insert(0, p)

COPIES = {
    os.path.join(PKG_G, "IFBench", f): "grader/IFBench/" + f
    for f in ("__init__.py", "eval_instruct.py", "grader.py", "instructions.py",
              "instructions_registry.py", "instructions_util.py")
}
COPIES.update({
    os.path.join(PKG_R, "ifbench", f): "reference/IFBench/ifbench/" + f
    for f in ("__init__.py", "classic_instructions.py", "instructions.py",
              "instructions_registry.py", "instructions_util.py")
})
COPIES[os.path.join(PKG_R, "evaluation_lib.py")] = "reference/IFBench/evaluation_lib.py"
COPIES[os.path.join(PKG_R, "instructions_test.py")] = "reference/IFBench/instructions_test.py"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def manifest():
    out = {}
    with open(os.path.join(CASE, "MANIFEST.sha256"), encoding="utf-8") as f:
        for line in f:
            d, p = line.rstrip("\n").split("  ", 1)
            out[p] = d
    return out


def verify_pins():
    """Raise if a package copy, the dataset or the panel differs from the manifest."""
    m = manifest()
    bad = [rel for path, rel in COPIES.items() if sha256_file(path) != m[rel]]
    for rel in ("data/train-00000-of-00001.parquet", "deps/requirements.lock.txt"):
        if sha256_file(os.path.join(CASE, rel)) != m[rel]:
            bad.append(rel)
    if bad:
        raise RuntimeError(f"pinned files differ from case/MANIFEST.sha256: {bad}")
    return True


def load_rows():
    import pyarrow.parquet as pq
    rows = pq.read_table(os.path.join(CASE, "data", "train-00000-of-00001.parquet")).to_pylist()
    out = []
    for r in rows:
        out.append({
            "key": r["key"],
            "prompt": r["prompt"],
            "instruction_id_list": list(r["instruction_id_list"]),
            "kwargs": [{k: v for k, v in kw.items() if v is not None} for kw in r["kwargs"]],
        })
    return out


_G = None
_R = None


def grader_modules():
    global _G
    if _G is None:
        from IFBench import grader as g
        from IFBench import instructions_registry as gr
        _G = (g, gr)
    return _G


def reference_modules():
    global _R
    if _R is None:
        import evaluation_lib as rl
        from ifbench import instructions_registry as rr
        _R = (rl, rr)
    return _R


def loose_variants(response):
    """The eight candidates of the loose transform (identical in grader and reference)."""
    lines = response.split("\n")
    first = "\n".join(lines[1:]).strip()
    last = "\n".join(lines[:-1]).strip()
    both = "\n".join(lines[1:-1]).strip()
    return [response, response.replace("*", ""), first, last, both,
            first.replace("*", ""), last.replace("*", ""), both.replace("*", "")]


def _instance(which, iid, kwargs, prompt):
    if which == "grader":
        g, _ = grader_modules()
        return g._build_instruction(iid, dict(kwargs), prompt)
    _, rr = reference_modules()
    inst = rr.INSTRUCTION_DICT[iid](iid)
    inst.build_description(**{k: v for k, v in kwargs.items() if v is not None})
    args = inst.get_instruction_args()
    if args and "prompt" in args:
        inst.build_description(prompt=prompt)
    return inst


def verdict(which, iid, kwargs, prompt, response, mode="strict"):
    """Return (verdict, error). verdict is True/False, or None when the checker raised.

    Strict: the response must be non-empty after strip, then check_following(response).
    Loose: True if any loose variant is non-empty after strip and passes.
    """
    try:
        inst = _instance(which, iid, kwargs, prompt)
        if mode == "strict":
            return bool(response and response.strip() and inst.check_following(response)), None
        for cand in loose_variants(response):
            if cand.strip() and inst.check_following(cand):
                return True, None
        return False, None
    except Exception as e:  # noqa: BLE001 - every exception is a grading failure to count
        return None, f"{type(e).__name__}: {e}"


def loose_winner(which, iid, kwargs, prompt, response):
    """Index of the first loose variant that passes (0 = the response itself), or None."""
    inst = _instance(which, iid, kwargs, prompt)
    for i, cand in enumerate(loose_variants(response)):
        if cand.strip() and inst.check_following(cand):
            return i
    return None


def iter_panel(cfgs=None, runs=None):
    """Yield (cfg, run, line_index, record) for the stored panel."""
    import glob
    for path in sorted(glob.glob(os.path.join(CASE, "panel", "*", "*.jsonl"))):
        cfg = os.path.basename(os.path.dirname(path))
        run = os.path.basename(path)[:-6]
        if cfgs and cfg not in cfgs:
            continue
        if runs and run not in runs:
            continue
        with open(path, encoding="utf-8") as f:
            for i, line in enumerate(f):
                yield cfg, run, i, json.loads(line)


def heldout():
    out = {}
    with open(os.path.join(W, "audit", "frozen", "heldout_runs.tsv"), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                c, r = line.split("\t")
                out[c] = r
    return out


def extraction_failure(rec):
    """Contract G1: a thinking-on completion that opens <think> and never closes it."""
    raw = rec["raw_response"]
    return "<think>" in raw and "</think>" not in raw
