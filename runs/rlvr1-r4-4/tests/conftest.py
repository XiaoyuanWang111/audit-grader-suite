import logging
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIT = os.path.dirname(HERE)
W = os.path.dirname(AUDIT)
os.environ.setdefault("NLTK_DATA", os.path.join(W, "case", "deps", "nltk_data"))
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True
for p in (HERE, AUDIT):
    if p not in sys.path:
        sys.path.insert(0, p)
logging.getLogger("absl").setLevel(logging.CRITICAL)
