"""pytest plugin: point the reference unit tests (instructions_test.py) at a chosen target.

IFB_TARGET=R   the reference checkers (baseline)
IFB_TARGET=G   the grader under audit: `ifbench.instructions` is replaced by IFBench.instructions
IFB_TARGET=X   the replacement grader, as-is switches: each OOD class's check_following calls X.check
IFB_TARGET=XP  the replacement grader, proposed switches
"""
import os
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(W, "audit", "lib"))

import ifbaudit as A  # noqa: E402

TARGET = os.environ.get("IFB_TARGET", "R")

if TARGET == "G":
    import ifbench
    from IFBench import instructions as G_inst
    sys.modules["ifbench.instructions"] = G_inst
    ifbench.instructions = G_inst
elif TARGET in ("X", "XP"):
    import replacement as X
    from ifbench import instructions as R_inst

    sw = X.PROPOSED if TARGET == "XP" else None
    for iid, cls in A.R_registry.INSTRUCTION_DICT.items():
        if ":" in iid and iid.split(":")[0] in ("count", "custom", "format", "ratio", "repeat", "sentence", "words"):
            orig = cls.check_following

            def make(iid=iid, orig=orig):
                def check_following(self, value):
                    args = self.get_instruction_args() or {}
                    return X.check(iid, args, value, "", sw)
                return check_following

            cls._orig_check_following = orig
            cls.check_following = make()
