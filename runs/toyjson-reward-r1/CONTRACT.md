# Contract for the ToyOrders reward

Written from the text the policy sees (`case/prompt_template.txt`) and the reward
specification in `case/TASK.md` ("Reward specification", "How the reward is run"), before
`case/reward.py` was opened. Quotes below are from `case/TASK.md` unless marked as from the
prompt. Every later change to this file is listed in its change log, with its reason.

## 0. Units and the graded text

- A rollout is one stored response to one order. The trainer calls
  `reward(response, reference)` once per rollout, with `reference` the order's `reference`
  object loaded by `json.loads(line, parse_float=Decimal)`. So the reference `total` is a
  `decimal.Decimal`, each reference `qty` is an `int`, and `customer`, `date` and each `sku`
  are `str`.
- The graded text is the whole `response` string. The specification has no
  end-of-reasoning marker, and `TASK.md` does not describe the policy as a reasoning model, so
  a reasoning block, if a response had one, is part of the graded text.
- Checks, each scored separately: `answer` (the gate, section 1), `customer`, `date`, `items`,
  `total` (section 2), `extra_keys` (section 3), and the aggregation `reward` (section 4).
  Section 5 states the robustness requirement and section 6 the command line.

## 1. Check `answer`: extraction and parsing

1. Let `s` be the response with whitespace removed at both ends ("Whitespace at both ends of
   the response is removed"), that is `response.strip()` in the specification's Python terms.
2. `s` is one fenced block when all of these hold, with lines separated by `\n`:
   - it has at least two lines;
   - its first line is ```` ```json ```` or ```` ``` ````, followed by zero or more spaces
     (U+0020) and nothing else ("spaces may follow the tag"). Only the lowercase tag `json`
     is named, so ```` ```JSON ````, ```` ```js ```` or ```` ``` json ```` is not an opening
     line;
   - its last line is exactly ```` ``` ```` (after step 1 it cannot have trailing whitespace);
   - the content is every line between the first and the last.
   If `s` is one fenced block, the answer is its content; otherwise the answer is `s` itself.
3. The answer must be a single JSON object with nothing around it but whitespace, parsed with
   Python's `json` module, which keeps the last value of a repeated key, with integers read as
   `int` and numbers with a fraction or exponent read as `decimal.Decimal` ("numbers are read
   exactly"). Otherwise the reward is 0.0. So the reward is 0.0 when:
   - the answer is empty, or is not valid JSON to Python's `json` module (for example a raw
     control character inside a string, or a trailing comma);
   - the top-level value is not an object (an array, a string, a number, `null`);
   - anything other than whitespace precedes or follows the object, such as a sentence before
     a fenced block, text after the closing fence, a second object, or a second fenced block.
4. A response that fails this check gets 0.0 and no field is scored. The report counts these
   responses separately from responses that parse but score low.

Pass examples: `{"customer": ...}` alone; the same inside ```` ```json ```` and ```` ``` ````
lines; the same with spaces after `json` on the opening line; the same with blank lines or
surrounding spaces inside the block. Fail examples: `Here it is: {...}`; a correct block
followed by `Hope this helps!`; ```` ```json {...}``` ```` on one line; `[{...}]`; two objects.

Open points (see the decision table in `audit/ISSUE.md`):
- **D-fence-newline.** With `\r\n` line breaks, the opening line read with `\n` separators is
  ```` ```json ```` plus a carriage return, which is not a space. Reading A: lines are split on
  `\n` only, so the block is not a fenced block and the reward is 0.0. Reading B: `\r\n` is a
  line break, so the block is one fenced block. Proposed: B, because the text is the same
  fenced block to any reader and the specification does not mention line-break characters.
- **D-inner-whitespace.** Whitespace that JSON does not allow (for example U+00A0) between the
  fence lines and the object. Reading A: the answer is stripped like the response, then
  parsed. Reading B: `json.loads` on the content as it is, which rejects it. Proposed: A,
  because "nothing around it but whitespace" uses the same word as step 1.

## 2. Field checks

Each field score is 0 or 1, except `items`. A missing key scores 0. The field checks look at
the parsed top-level object only.

### `customer`
1 if the value is a `str` and `value.strip().casefold() == reference.strip().casefold()`, else
0. Whitespace inside the name is not normalized (`Maria  Lopez` with two spaces scores 0), and
`casefold` is the stated comparison (so `LARS NILSSON` and `lars nilsson` score 1; a `ß` in
place of `ss` also casefolds to `ss` and scores 1).

### `date`
1 if the value is a `str` exactly equal to the reference date, else 0. No trimming, no other
formats (`2026-3-7`, `2026/03/07`, ` 2026-03-07` score 0).

### `items`
- 0 if the value is not a list (an object, a string, `null`).
- An answer item is any element of the list. An answer item matches a reference item when it
  is an object whose `sku` is a `str` equal to the reference sku (exact: no case folding or
  trimming) and whose `qty` is an integer equal to the reference quantity. Other keys in the
  item are ignored. An element that is not an object matches nothing but still counts as an
  answer item.
- Each reference item can be matched by at most one answer item, and an answer item that
  matches one reference item is used up. Matching is by equality of (`sku`, `qty`), so a
  greedy matching is a maximum matching.
- Score = (number of matched reference items) / max(number of reference items, number of
  answer items). So a duplicated correct line does not count twice and lowers the score
  (two copies of `AB-100` x 2 against `AB-100` x 2, `CD-220` x 1 score 1/2), an extra wrong
  line lowers the score (3 answer items, 2 matched: 2/3), and an empty list scores 0.
- "An integer": a JSON integer, read by Python's `json` module as `int`. Open points:
  - **D-qty-bool.** Python's `True == 1` and `isinstance(True, int)`. Reading A: `true` and
    `false` are not integers, as the `total` rule says of numbers ("not true or false").
    Reading B: `true` equals the integer 1 in Python, so it matches a reference quantity of 1.
    Proposed: A, because the prompt asks for "the quantity, an integer", and a JSON boolean is
    not a quantity.
  - **D-qty-integral.** `2.0`, `2.00` or `2e0` is read as `Decimal`. Reading A: only a JSON
    integer (`int`) is an integer. Reading B: any number with an integral value is an integer.
    Proposed: A, because the specification reads numbers by type ("decimal fractions as
    `decimal.Decimal`") and the prompt asks for "an integer".
- Not reachable with these 12 references: no reference has two lines with the same sku, and no
  reference list is empty, so whether one answer item can match two identical reference
  items, and the score of an empty reference list, never change a verdict here.

### `total`
1 if the value is a number other than `true` or `false` (an `int`, a `Decimal`, or the float
that Python's `json` module gives for `NaN`, `Infinity` or `-Infinity`) within 0.005 of the
reference total, else 0. The comparison is exact, because "numbers are read exactly": no
binary floating point. `NaN` and the infinities are never within 0.005, so they score 0. A
string such as `"64.50"` or `"$64.50"` scores 0. An integer `47` against a reference `47.00`
scores 1, and so does `6.45e1` against `64.50`.

Open point:
- **D-total-boundary.** A total exactly 0.005 from the reference (64.505 against 64.50).
  Reading A: "within 0.005" includes the boundary, so it scores 1. Reading B: strictly less
  than 0.005, so it scores 0. Proposed: A, the usual reading of "within".

## 3. Check `extra_keys`: the penalty

0.1 for each key of the parsed top-level object other than `customer`, `date`, `items` and
`total`. Keys are those of the parsed object, so a repeated key counts once. Keys are
case-sensitive: `Customer` is an extra key, and the `customer` field then scores 0. Missing
keys add no penalty. Keys inside items are not top-level keys.

## 4. Check `reward`: aggregation

Reward = (customer + date + items + total) / 4 - 0.1 x (number of extra keys), clipped to
[0, 1], returned as a Python `float`. So a fully correct answer with no extra key gets 1.0
exactly, one extra key gives 0.9, and eleven extra keys on a fully correct answer give 0.0.
Comparisons between reward values in this audit allow 1e-9 for binary rounding.

## 5. Robustness

"The reward function must return a float for every response, whatever text the policy
produces." For every `str` response and every reference in `orders.jsonl`, `reward` returns a
`float` in [0, 1] and raises nothing. Any exception (for example from a non-string `customer`,
an item that is not an object, an unhashable `sku`, deep nesting, or arithmetic on an extreme
number such as `1e1000000`) breaks this contract, whatever the response. The verdict must
depend only on the response and the reference: the same inputs give the same reward in any
order and any process.

## 6. The command line

`python reward.py` and `python reward.py --responses other.jsonl --out rewards.jsonl`, run
from `case/`:
- read the references from `orders.jsonl` with `parse_float=Decimal`, and grade each rollout
  against the reference with the same `order_id`;
- accept any JSON-lines file whose rows have at least `id`, `checkpoint`, `order_id` and
  `response`;
- print, for each checkpoint, the mean reward over its rollouts and the number of rollouts
  whose reward is exactly 1.0;
- with `--out`, write one JSON line per rollout with its reward, identified so that it can be
  joined back to the rollout (its `id`);
- grade every rollout: one bad response must not stop the run (it gets a reward, per
  section 5).

## Change log

- 2026-11-06: first version, written before `case/reward.py` was opened.
