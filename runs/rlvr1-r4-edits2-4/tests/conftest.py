import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True
AUDIT = Path(__file__).resolve().parents[1]
os.environ.setdefault("NLTK_DATA", str(AUDIT.parent / "case" / "deps" / "nltk_data"))
sys.path.insert(0, str(AUDIT / "lib"))
