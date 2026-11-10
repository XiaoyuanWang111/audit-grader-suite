import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.join(os.path.dirname(HERE), "lib"), os.path.join(os.path.dirname(HERE), "replacement")):
    if p not in sys.path:
        sys.path.insert(0, p)

import ifb  # noqa: E402,F401  (sets NLTK_DATA before nltk is imported)
