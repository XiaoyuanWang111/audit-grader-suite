import os
import sys
from pathlib import Path

W = Path(__file__).resolve().parents[2]
os.environ.setdefault("NLTK_DATA", str(W / "case" / "deps" / "nltk_data"))
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
sys.dont_write_bytecode = True
for p in (W / "audit" / "lib", W / "audit" / "tests"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
