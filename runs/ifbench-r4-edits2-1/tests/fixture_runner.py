"""Resolve fixtures to (instruction id, kwargs, prompt, response) and grade them with each grader."""
import harness as H
from fixtures_data import FIXTURES, fixture_id

_ROWS = None


def rows():
    global _ROWS
    if _ROWS is None:
        _ROWS = H.load_rows()
    return _ROWS


def resolve(f):
    """Return (kwargs, prompt) for a fixture; a `key` takes them from that dataset row."""
    if f["key"] is None:
        return dict(f["kwargs"]), ""
    row = H.row_by_key(rows(), f["key"])
    for iid, kw in zip(row["instruction_id_list"], row["kwargs"]):
        if iid == f["check"]:
            return dict(kw), row["prompt"]
    raise KeyError((f["key"], f["check"]))


def verdict(grader, f):
    """'pass', 'fail', or 'error:<Exception>' for one fixture."""
    kwargs, prompt = resolve(f)
    try:
        if grader == "grader":
            ok = H.check_grader(f["check"], kwargs, f["response"], prompt)
        elif grader == "reference":
            ok = H.check_reference(f["check"], kwargs, f["response"], prompt)
        elif grader == "replacement":
            from replacement import contract_grader as R

            ok = R.check(f["check"], kwargs, f["response"], prompt)
        else:
            raise ValueError(grader)
    except Exception as e:  # an exception is a grading failure, reported separately
        return f"error:{type(e).__name__}"
    return "pass" if ok else "fail"


ALL = [(fixture_id(f), f) for f in FIXTURES]
