# ToyOrders reward: contract

Written from `case/TASK.md` (sections "What the policy sees", "Reward specification", "How the reward is run") and
`case/prompt_template.txt`. Version 1. Each later change is listed at the end with its reason.

## Inputs and graded text

- `reward(response, reference)` gets the rollout's text and the order's `reference`, which the trainer loads with
  `json.loads(line, parse_float=Decimal)`: `total` is a `Decimal`, each `qty` an `int`.
- The graded text is the whole `response` string. The task names no reasoning marker, so no part of the response is
  removed before rule C1.

## C1. Answer extraction (pipeline stage)

1. `T` = the response with whitespace removed at both ends. Which characters are whitespace: `D-whitespace`.
2. `T` is one fenced block when its first line is ` ```json ` or ` ``` `, optionally followed by spaces
   (tabs: `D-fence-tab`), its last line is exactly ` ``` `, and it has at least these two lines. Lines end at `\n`
   (`\r\n`: `D-crlf`). The content is the text between the first and the last line. Any other opening line, such as
   ` ```JSON `, ` ```python ` or ` ``` json `, makes `T` not a fenced block.
3. The answer is the content when `T` is one fenced block, and `T` otherwise.
4. The answer passes when Python's `json` module parses it as exactly one JSON value, that value is an object, and
   nothing but whitespace (`D-whitespace`) surrounds it. Numbers are read exactly: integers as `int`, numbers with a
   fraction or exponent as `decimal.Decimal`. A repeated key keeps its last value. `NaN` and `Infinity`:
   `D-json-constants`.
5. Otherwise the reward is 0.0. This covers any other text before or after the object (prose, a full stop, a second
   object, a fence line when `T` is not one fenced block), a top-level value that is not an object (array, string,
   number, `true`, `false`, `null`), and any text that the `json` module fails to parse, whatever error it raises.

## C2. `customer`

1 if the value is a string and equals the reference name after removing whitespace at both ends of both
(`D-whitespace`) and applying `str.casefold`; else 0. A missing key scores 0.

## C3. `date`

1 if the value is a string exactly equal to the reference date; else 0.

## C4. `items`

0 if the value is not a list (or the key is missing). Otherwise every element of the list is an answer item,
including elements that are not objects. An answer item matches a reference item when it is an object whose `sku` is
a string equal to the reference sku (exact, case-sensitive) and whose `qty` is an integer equal to the reference
quantity; other keys inside the item are ignored. What counts as an integer: an `int` from a JSON integer literal;
`2.0`-style values: `D-qty-decimal`; `true`/`false`: `D-qty-bool`. The matching is one-to-one: each reference item is
matched by at most one answer item and each answer item matches at most one reference item, and the count is the
largest such matching. Score = matched reference items / max(number of reference items, number of answer items).

## C5. `total`

1 if the value is a number (an `int` or `Decimal`, not `true` or `false`) whose exact distance from the reference total
is at most 0.005 (boundary: `D-total-boundary`); else 0. A string such as `"35.00"` is not a number.

## C6. Penalty

0.1 for each top-level key of the parsed object other than `customer`, `date`, `items`, `total`. Keys are counted after
parsing, so a repeated key counts once.

## C7. Aggregation

Reward = (customer + date + items + total) / 4 - penalty, clipped to [0, 1], returned as a Python `float`.

## C8. Robustness

`reward` returns a float for every string response and raises no exception (TASK.md: "must return a float for every
response, whatever text the policy produces"). Text the `json` module cannot parse gets 0.0 under C1.5.

## Decision entries (both readings, an example of each, the proposed reading)

| Id | Question | Reading A | Reading B | Proposed |
|---|---|---|---|---|
| `D-whitespace` | Which characters are "whitespace" in C1.1, C1.4 and C2 | Python `str.strip()` set (Unicode White_Space, such as U+00A0 and U+3000) | JSON whitespace only (space, tab, LF, CR) | A, because the specification is written against Python (`str.casefold`, the `json` module), and "whitespace at both ends is removed" reads as `str.strip()` |
| `D-fence-tab` | May a tab follow the tag on the opening fence line ("spaces may follow the tag") | Yes, spaces and tabs | No, U+0020 only | A, because the prompt offers a "```json code block" and Markdown accepts a tab after the info string; the parenthesis is there to tolerate invisible trailing blanks |
| `D-crlf` | Does `\r\n` end a line in the fenced-block rule | Yes | No, only `\n` | A, because CRLF is a line break in every text convention the policy may emit |
| `D-json-constants` | Are `NaN`, `Infinity`, `-Infinity` (accepted by Python's `json`, not by RFC 8259) part of a valid answer | Yes: the answer parses; such a `total` is not within 0.005 and scores 0 | No: the answer is not JSON, reward 0.0 | A, because the specification names Python's `json` module as the parser |
| `D-qty-decimal` | Is a `qty` written with a fraction part or exponent but an integral value (`2.0`, `2e0`, parsed as `Decimal`) "an integer" | No: only `int` from an integer literal | Yes: any number with an integral value | A, because the specification reads decimal fractions as `Decimal` and then requires "an integer", and the prompt asks for "the quantity, an integer" |
| `D-qty-bool` | Is `true` an integer (Python `bool` is an `int` subclass, `true == 1`) | No | Yes | A, because JSON `true` is a boolean, and the `total` rule shows the author does not treat booleans as numbers |
| `D-total-boundary` | Is a distance of exactly 0.005 "within 0.005" | Yes (inclusive) | No (exclusive) | A, the ordinary meaning of "within" |

Examples, on order `o01` (reference total 64.50, items AB-100 x2 and CD-220 x1; `V` = the reference's correct
object):

- `D-whitespace`: `V` followed by U+00A0: A gives 1.0, B gives 0.0.
- `D-fence-tab`: "```json" + TAB + "\n" + `V` + "\n```": A gives 1.0, B gives 0.0.
- `D-crlf`: "```json\r\n" + `V` + "\r\n```": A gives 1.0, B gives 0.0.
- `D-json-constants`: `V` with `"total": NaN`: A gives 0.75, B gives 0.0.
- `D-qty-decimal`: `V` with AB-100 `"qty": 2.0`: A gives 0.875, B gives 1.0.
- `D-qty-bool`: `V` with CD-220 `"qty": true`: A gives 0.875, B gives 1.0.
- `D-total-boundary`: `V` with `"total": 64.505`: A gives 1.0, B gives 0.75.

## Changes

(none)
