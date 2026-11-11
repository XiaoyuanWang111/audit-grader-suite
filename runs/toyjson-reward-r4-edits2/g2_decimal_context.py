"""G2: case/reward.py's total score depends on the caller's thread-local decimal context, which nothing pins.

    python -B audit/g2_decimal_context.py

Prints the grader's reward for one response under the default context (precision 28) and after the caller sets
precision 9 (the precision of decimal.BasicContext). The contract's reward is 0.75 in both cases.
"""

import decimal
import json
import os
import sys
from decimal import Decimal

sys.dont_write_bytecode = True
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(W, "case"))

import reward  # noqa: E402

REF = json.loads('{"customer": "Kenji Watanabe", "date": "2026-01-15", "items": [{"sku": "EF-310", "qty": 3}], '
                 '"total": 29.97}', parse_float=Decimal)
RESPONSE = ('{"customer": "Kenji Watanabe", "date": "2026-01-15", "items": [{"sku": "EF-310", "qty": 3}], '
            '"total": 29.975000000001}')

print("response:", RESPONSE)
print("default context (prec 28):", reward.reward(RESPONSE, REF))
decimal.getcontext().prec = 9
print("caller set prec 9:        ", reward.reward(RESPONSE, REF))
