from pathlib import Path as _P

_W = _P(__file__).resolve().parents[4]
exec(compile(open(_W / "audit/frozen/code/reference/IFBench/ifbench/classic_instructions.py", encoding="utf-8").read(),
             "ref_classic_instructions.py", "exec"))
