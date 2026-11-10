import os
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for p in (os.path.join(W, "audit", "lib"), os.path.join(W, "audit", "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)
