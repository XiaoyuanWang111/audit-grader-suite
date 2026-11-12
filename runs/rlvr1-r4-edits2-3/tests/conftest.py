import os
import sys

AUDIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.dirname(AUDIT)
os.environ.setdefault("NLTK_DATA", os.path.join(W, "case", "deps", "nltk_data"))
sys.dont_write_bytecode = True
for p in (AUDIT, os.path.join(AUDIT, "replacement")):
    if p not in sys.path:
        sys.path.insert(0, p)
