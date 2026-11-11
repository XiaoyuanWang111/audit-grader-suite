"""Print, for every metamorphic edit, the problems where each grader breaks the expectation.

Run from W:  python -B audit/scripts/property_matrix.py
"""
import pathlib
import sys

sys.dont_write_bytecode = True
W = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W / "audit" / "tests"))

import fixtures  # noqa: E402
import harness  # noqa: E402
import properties  # noqa: E402


def matrix():
    items = []
    for name, expect, depends, pid, resp in properties.cases(fixtures.PROBLEMS):
        items.append({"id": f"{name}|{pid}", "problem_id": pid, "response": resp,
                      "edit": name, "expect": expect, "depends": depends})
    res = harness.grade_all(items, "properties")
    out = {}
    for it in items:
        v = res[it["id"]]
        row = out.setdefault(it["edit"], {"expect": it["expect"], "depends": it["depends"], "n": 0,
                                          "grader": [], "reference": [], "replacement": []})
        row["n"] += 1
        for g in ("grader", "reference", "replacement"):
            if harness.binary(v[g]) != it["expect"]:
                row[g].append(it["problem_id"])
    return out


def main():
    m = matrix()
    print(f"{'edit':<28}{'expect':<12}{'n':>3}  {'grader breaks on':<34}{'reference breaks on':<34}replacement")
    for edit, row in m.items():
        def fmt(lst):
            return (",".join(lst) if len(lst) < 12 else f"all {len(lst)}") or "-"
        dep = f" [{row['depends']}]" if row["depends"] else ""
        print(f"{edit:<28}{row['expect']:<12}{row['n']:>3}  {fmt(row['grader']):<34}{fmt(row['reference']):<34}{fmt(row['replacement'])}{dep}")


if __name__ == "__main__":
    main()
