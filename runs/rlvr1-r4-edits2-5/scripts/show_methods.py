"""Print selected methods of classes in a Python file, without docstrings.

Usage: python show_methods.py FILE CLASS[.METHOD] ...
"""
import ast
import sys

path = sys.argv[1]
src = open(path, encoding="utf-8").read()
lines = src.split(chr(10))
tree = ast.parse(src)
targets = sys.argv[2:]


def strip_doc(node):
    body = node.body
    skip = set()
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) and isinstance(body[0].value.value, str):
        skip.update(range(body[0].lineno, body[0].end_lineno + 1))
    return skip


for t in targets:
    cls, _, meth = t.partition(".")
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name == cls:
            items = [node] if isinstance(node, ast.FunctionDef) else [n for n in node.body if isinstance(n, ast.FunctionDef) and (not meth or n.name in meth.split("+"))]
            print(f"# ---- {cls} (line {node.lineno})" + (f" bases={[ast.unparse(b) for b in node.bases]}" if isinstance(node, ast.ClassDef) else ""))
            for fn in items:
                skip = strip_doc(fn)
                for ln in range(fn.lineno, fn.end_lineno + 1):
                    if ln in skip:
                        continue
                    text = lines[ln - 1]
                    if text.strip().startswith("#") or not text.strip():
                        continue
                    print(f"{ln}: {text}")
