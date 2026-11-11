# ToyOrders reward review, round 1, batch B

Each case below shows a case id, the prompt the policy saw, the order's reference values, and the policy's response. The response is the exact text between the line `<<<BEGIN RESPONSE Cnn>>>` and the line `<<<END RESPONSE Cnn>>>`, excluding the newline right after the BEGIN line and the newline right before the END line; leading and trailing whitespace inside the markers is part of the response. Print the exact response, with escapes, with `python -B audit/frozen/round1/show_case.py Cnn`.

## REQUIREMENT TO JUDGE (the same for every case)

Give the reward that the following specification assigns to the response, against the case's reference. The specification is quoted from the task's design document.

## Reward specification (from the task's design document)

1. Answer. Whitespace at both ends of the response is removed. If what remains is one fenced block, that is an
   opening line ` ```json ` or ` ``` ` (spaces may follow the tag), then the content, then a closing line ` ``` `,
   the answer is the block's content; otherwise the answer is all of what remains. The answer must be a single JSON
   object with nothing around it but whitespace; otherwise the reward is 0.0. JSON is parsed with Python's `json` module, which keeps the last value of
   a repeated key; numbers are read exactly (decimal fractions as `decimal.Decimal`).
2. Field scores, each from 0 to 1:
   - `customer`: 1 if it is a string equal to the reference name after removing whitespace at both ends and ignoring
     case (`str.casefold`), else 0.
   - `date`: 1 if it is a string exactly equal to the reference date, else 0.
   - `items`: 0 if it is not a list. Otherwise an answer item matches a reference item when it is an object whose
     `sku` is a string equal to the reference sku and whose `qty` is an integer equal to the reference quantity
     (other keys inside an item are ignored); each reference item can be matched by at most one answer item. The
     score is the number of matched reference items divided by the larger of the number of reference items and the
     number of answer items.
   - `total`: 1 if it is a number (not `true` or `false`) within 0.005 of the reference total, else 0.
3. Penalty: 0.1 for each top-level key other than the four above.
4. Reward = (sum of the four field scores) / 4 minus the penalty, clipped to [0, 1].

The reward function must return a float for every response, whatever text the policy produces.

## Case C47

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
Hello! Please ship my order (placed 4 February 2026) to the usual address. I ordered one GH-405 kettle and two IJ-500 mugs. Total paid: $47.00. Best, Priya Raman
```

REFERENCE (JSON):

```text
{"customer": "Priya Raman", "date": "2026-02-04", "items": [{"sku": "GH-405", "qty": 1}, {"sku": "IJ-500", "qty": 2}], "total": 47.00}
```

<<<BEGIN RESPONSE C47>>>
{"customer": "Priya Raman", "date": "4 February 2026", "items": [{"sku": "GH-405", "qty": 1}, {"sku": "IJ-500", "qty": 2}], "total": 47.00}
<<<END RESPONSE C47>>>

## Case C24

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
This is Sofia Rossi. Order date: March 20, 2026. I ordered 1 x YZ-480 and 3 x AB-590. Total: $35.00.
```

REFERENCE (JSON):

```text
{"customer": "Sofia Rossi", "date": "2026-03-20", "items": [{"sku": "YZ-480", "qty": 1}, {"sku": "AB-590", "qty": 3}], "total": 35.00}
```

<<<BEGIN RESPONSE C24>>>
{"customer": "Sofia Rossi", "date": "2026-03-20", "items": [{"sku": "YZ-480", "qty": 1}, {"sku": "AB-590", "qty": 3}], "total": 35}
<<<END RESPONSE C24>>>

## Case C09

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
Hi! Daniel Okafor here, order from 2026-04-11: 2 CD-605 cables and 2 EF-715 adapters. Total was $31.96. Could you add gift wrap? It was free.
```

REFERENCE (JSON):

```text
{"customer": "Daniel Okafor", "date": "2026-04-11", "items": [{"sku": "CD-605", "qty": 2}, {"sku": "EF-715", "qty": 2}], "total": 31.96}
```

<<<BEGIN RESPONSE C09>>>
{"customer": "Daniel Okafor", "date": "2026-04-11", "items": [{"sku": "CD-605", "qty": 2}, {"sku": "EF-715", "qty": 2}], "total": 31.96}
<<<END RESPONSE C09>>>

## Case C06

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
This is Sofia Rossi. Order date: March 20, 2026. I ordered 1 x YZ-480 and 3 x AB-590. Total: $35.00.
```

REFERENCE (JSON):

```text
{"customer": "Sofia Rossi", "date": "2026-03-20", "items": [{"sku": "YZ-480", "qty": 1}, {"sku": "AB-590", "qty": 3}], "total": 35.00}
```

<<<BEGIN RESPONSE C06>>>
{"customer": "Sofia Rossi", "date": "2026-03-20", "items": [{"sku": "YZ-480", "qty": 1}, {"sku": "AB-590", "qty": 3}], "total": "35.00"}
<<<END RESPONSE C06>>>

## Case C02

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
Hello, Chen Wei here. On 9 January 2026 I bought 5 packs of WX-370 printer paper. Total: $42.50.
```

REFERENCE (JSON):

```text
{"customer": "Chen Wei", "date": "2026-01-09", "items": [{"sku": "WX-370", "qty": 5}], "total": 42.50}
```

<<<BEGIN RESPONSE C02>>>
{"customer": "Chen Wei", "date": "2026-01-09", "items": [{"sku": "WX-370", "qty": 5}], "total": 42.50}
<<<END RESPONSE C02>>>

## Case C26

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
Hi, I'm Grace Kim. I placed an order on April 3, 2026 for 3 x OP-265 notebooks. My total was $13.50.
```

REFERENCE (JSON):

```text
{"customer": "Grace Kim", "date": "2026-04-03", "items": [{"sku": "OP-265", "qty": 3}], "total": 13.50}
```

<<<BEGIN RESPONSE C26>>>
{'customer': 'Grace Kim', 'date': '2026-04-03', 'items': [{'sku': 'OP-265', 'qty': 3}], 'total': 13.5}
<<<END RESPONSE C26>>>

## Case C20

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
Hi, this is Maria Lopez. I'd like to confirm my order from March 7, 2026: 2 x AB-100 (desk lamp) and 1 x CD-220 (bulb pack). The total came to $64.50. Thanks!
```

REFERENCE (JSON):

```text
{"customer": "Maria Lopez", "date": "2026-03-07", "items": [{"sku": "AB-100", "qty": 2}, {"sku": "CD-220", "qty": 1}], "total": 64.50}
```

<<<BEGIN RESPONSE C20>>>
{"customer": "Maria Lopez", "date": "2026-03-07", "items": [{"sku": "AB-100", "qty": 2}, {"sku": "CD-220", "qty": 1}, {"sku": "CD-220", "qty": 1}], "total": 64.50}
<<<END RESPONSE C20>>>

## Case C27

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
Order by Emma Schulz on 5 March 2026: one GH-825 umbrella. Total charged: $24.00.
```

REFERENCE (JSON):

```text
{"customer": "Emma Schulz", "date": "2026-03-05", "items": [{"sku": "GH-825", "qty": 1}], "total": 24.00}
```

<<<BEGIN RESPONSE C27>>>
{"customer": "Emma Schulz", "date": "2026-03-05", "items": [{"sku": "GH-825", "qty": 1}], "total": 24.00}
Note: the email does not say which color the umbrella is.
<<<END RESPONSE C27>>>

## Case C13

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
Hi, it's Aisha Bello. My order from April 1, 2026: 1 OP-830 backpack. It was $59.99 in total; the $5.00 shipping fee is included in that.
```

REFERENCE (JSON):

```text
{"customer": "Aisha Bello", "date": "2026-04-01", "items": [{"sku": "OP-830", "qty": 1}], "total": 59.99}
```

<<<BEGIN RESPONSE C13>>>
{"customer": "Aisha Bello", "date": "2026-04-01", "items": [{"sku": "OP-830", "qty": 1}], "total": 59.99}
<<<END RESPONSE C13>>>

## Case C37

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
Order placed on 2026-01-15 by Kenji Watanabe. Items: EF-310 (qty 3). Order total: $29.97.
```

REFERENCE (JSON):

```text
{"customer": "Kenji Watanabe", "date": "2026-01-15", "items": [{"sku": "EF-310", "qty": 3}], "total": 29.97}
```

<<<BEGIN RESPONSE C37>>>
{"customer": "Kenji Watanabe", "date": "2026-01-15", "items": [{"sku": "EF-310", "qty": 3}], "total": 29.97}

I extracted the customer name, the order date, the items and the total from the email.
<<<END RESPONSE C37>>>

## Case C38

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
From: Tom Becker. Date of order: 12/03/2026 (that is, 12 March). 4 x KL-610, 1 x MN-720. Total $112.80, shipping included.
```

REFERENCE (JSON):

```text
{"customer": "Tom Becker", "date": "2026-03-12", "items": [{"sku": "KL-610", "qty": 4}, {"sku": "MN-720", "qty": 1}], "total": 112.80}
```

<<<BEGIN RESPONSE C38>>>
{"customer": "Tom Becker", "date": "2026-03-12", "items": [{"sku": "KL-610", "qty": 4}, {"sku": "MN-720", "qty": 1}, {"sku": "KL-610", "qty": 1}], "total": 112.80}
<<<END RESPONSE C38>>>

## Case C19

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
Order placed on 2026-01-15 by Kenji Watanabe. Items: EF-310 (qty 3). Order total: $29.97.
```

REFERENCE (JSON):

```text
{"customer": "Kenji Watanabe", "date": "2026-01-15", "items": [{"sku": "EF-310", "qty": 3}], "total": 29.97}
```

<<<BEGIN RESPONSE C19>>>
{"customer": "Kenji Watanabe", "date": "2026-01-15", "items": [{"sku": "EF-310", "qty": 3}], "total": 29.97}
<<<END RESPONSE C19>>>

## Case C05

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
Order confirmation needed: customer Lars Nilsson, ordered 2026-02-28. Products: QR-940 x 2, ST-150 x 2, UV-260 x 1. Grand total: $88.25.
```

REFERENCE (JSON):

```text
{"customer": "Lars Nilsson", "date": "2026-02-28", "items": [{"sku": "QR-940", "qty": 2}, {"sku": "ST-150", "qty": 2}, {"sku": "UV-260", "qty": 1}], "total": 88.25}
```

<<<BEGIN RESPONSE C05>>>
{"customer": "Lars Nilsson", "date": "2026-02-28", "items": [{"sku": "QR-940", "qty": 2}, {"sku": "ST-150", "qty": 2}, {"sku": "UV-260", "qty": 1}], "total": 88.25}
<<<END RESPONSE C05>>>

## Case C34

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
Order placed on 2026-01-15 by Kenji Watanabe. Items: EF-310 (qty 3). Order total: $29.97.
```

REFERENCE (JSON):

```text
{"customer": "Kenji Watanabe", "date": "2026-01-15", "items": [{"sku": "EF-310", "qty": 3}], "total": 29.97}
```

<<<BEGIN RESPONSE C34>>>
{"customer": "Kenji Watanabe", "date": "2026-01-15", "items": [{"sku": "EF-310", "qty": 3}], "total": 29.97}
<<<END RESPONSE C34>>>

## Case C41

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
Hi! Daniel Okafor here, order from 2026-04-11: 2 CD-605 cables and 2 EF-715 adapters. Total was $31.96. Could you add gift wrap? It was free.
```

REFERENCE (JSON):

```text
{"customer": "Daniel Okafor", "date": "2026-04-11", "items": [{"sku": "CD-605", "qty": 2}, {"sku": "EF-715", "qty": 2}], "total": 31.96}
```

<<<BEGIN RESPONSE C41>>>
```json
{"customer": "Daniel Okafor", "date": "2026-04-11", "items": [{"sku": "CD-605", "qty": 2}, {"sku": "EF-715", "qty": 2}], "total": 31.96}
```
<<<END RESPONSE C41>>>

## Case C07

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
Hi, this is Maria Lopez. I'd like to confirm my order from March 7, 2026: 2 x AB-100 (desk lamp) and 1 x CD-220 (bulb pack). The total came to $64.50. Thanks!
```

REFERENCE (JSON):

```text
{"customer": "Maria Lopez", "date": "2026-03-07", "items": [{"sku": "AB-100", "qty": 2}, {"sku": "CD-220", "qty": 1}], "total": 64.50}
```

<<<BEGIN RESPONSE C07>>>
{"customer": "Maria Lopez", "date": "2026-03-07", "items": [{"sku": "AB-100", "qty": 2}, {"sku": "CD-220", "qty": 1}], "total": 64.50}
<<<END RESPONSE C07>>>

## Case C21

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
From: Tom Becker. Date of order: 12/03/2026 (that is, 12 March). 4 x KL-610, 1 x MN-720. Total $112.80, shipping included.
```

REFERENCE (JSON):

```text
{"customer": "Tom Becker", "date": "2026-03-12", "items": [{"sku": "KL-610", "qty": 4}, {"sku": "MN-720", "qty": 1}], "total": 112.80}
```

<<<BEGIN RESPONSE C21>>>
```json
{
  "customer": "Tom Becker",
  "date": "2026-03-12",
  "items": [
    {
      "sku": "KL-610",
      "qty": 4
    },
    {
      "sku": "MN-720",
      "qty": 1
    }
  ],
  "total": 112.8
}
```
<<<END RESPONSE C21>>>

## Case C45

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
Name: Rahul Mehta. Ordered: 2026-02-10. Lines: IJ-935 (2), KL-045 (1), MN-155 (1). Total: $73.40, which includes a $4.90 delivery charge.
```

REFERENCE (JSON):

```text
{"customer": "Rahul Mehta", "date": "2026-02-10", "items": [{"sku": "IJ-935", "qty": 2}, {"sku": "KL-045", "qty": 1}, {"sku": "MN-155", "qty": 1}], "total": 73.40}
```

<<<BEGIN RESPONSE C45>>>
{"customer": "Rahul Mehta", "date": "2026-02-10", "items": [{"sku": "IJ-935", "qty": 2}, {"sku": "KL-045", "qty": 1}, {"sku": "MN-155", "qty": 1}, {"sku": "DELIVERY", "qty": 1}], "total": 73.40}
<<<END RESPONSE C45>>>

## Case C30

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
Order placed on 2026-01-15 by Kenji Watanabe. Items: EF-310 (qty 3). Order total: $29.97.
```

REFERENCE (JSON):

```text
{"customer": "Kenji Watanabe", "date": "2026-01-15", "items": [{"sku": "EF-310", "qty": 3}], "total": 29.97}
```

<<<BEGIN RESPONSE C30>>>
{"customer": "Kenji Watanabe", "date": "2026-01-15", "items": [{"sku": "EF-310", "qty": 3}], "total": 29.97}
Extraction complete.
<<<END RESPONSE C30>>>

## Case C18

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
Name: Rahul Mehta. Ordered: 2026-02-10. Lines: IJ-935 (2), KL-045 (1), MN-155 (1). Total: $73.40, which includes a $4.90 delivery charge.
```

REFERENCE (JSON):

```text
{"customer": "Rahul Mehta", "date": "2026-02-10", "items": [{"sku": "IJ-935", "qty": 2}, {"sku": "KL-045", "qty": 1}, {"sku": "MN-155", "qty": 1}], "total": 73.40}
```

<<<BEGIN RESPONSE C18>>>
{"customer": "Rahul Mehta", "date": "2026-02-10", "items": [{"sku": "IJ-935", "qty": 2}, {"sku": "KL-045", "qty": 1}, {"sku": "MN-155", "qty": 1}], "total": 73.40}
<<<END RESPONSE C18>>>

## Case C11

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
Hi! Daniel Okafor here, order from 2026-04-11: 2 CD-605 cables and 2 EF-715 adapters. Total was $31.96. Could you add gift wrap? It was free.
```

REFERENCE (JSON):

```text
{"customer": "Daniel Okafor", "date": "2026-04-11", "items": [{"sku": "CD-605", "qty": 2}, {"sku": "EF-715", "qty": 2}], "total": 31.96}
```

<<<BEGIN RESPONSE C11>>>
{"customer": "Daniel Okafor", "date": "2026-04-11", "items": [{"sku": "CD-605", "qty": 2}, {"sku": "EF-715", "qty": 2}], "total": 31.96}
<<<END RESPONSE C11>>>

## Case C04

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
Hello, Chen Wei here. On 9 January 2026 I bought 5 packs of WX-370 printer paper. Total: $42.50.
```

REFERENCE (JSON):

```text
{"customer": "Chen Wei", "date": "2026-01-09", "items": [{"sku": "WX-370", "qty": 5}], "total": 42.50}
```

<<<BEGIN RESPONSE C04>>>
{"customer": "Chen Wei", "date": "2026-01-09", "items": [{"sku": "WX-370", "qty": 5}], "total": 42.50}
<<<END RESPONSE C04>>>

## Case C22

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
Hi, it's Aisha Bello. My order from April 1, 2026: 1 OP-830 backpack. It was $59.99 in total; the $5.00 shipping fee is included in that.
```

REFERENCE (JSON):

```text
{"customer": "Aisha Bello", "date": "2026-04-01", "items": [{"sku": "OP-830", "qty": 1}], "total": 59.99}
```

<<<BEGIN RESPONSE C22>>>
```json
{
  "customer": "Aisha Bello",
  "date": "2026-04-01",
  "items": [
    {
      "sku": "OP-830",
      "qty": 1
    }
  ],
  "total": 59.99,
  "shipping": 5.0
}
```
<<<END RESPONSE C22>>>

## Case C42

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
Order by Emma Schulz on 5 March 2026: one GH-825 umbrella. Total charged: $24.00.
```

REFERENCE (JSON):

```text
{"customer": "Emma Schulz", "date": "2026-03-05", "items": [{"sku": "GH-825", "qty": 1}], "total": 24.00}
```

<<<BEGIN RESPONSE C42>>>
```json
{"customer": "Emma Schulz", "date": "2026-03-05", "items": [{"sku": "GH-825", "qty": 1}], "total": 24.00}
```
<<<END RESPONSE C42>>>

## Case C43

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
Hello! Please ship my order (placed 4 February 2026) to the usual address. I ordered one GH-405 kettle and two IJ-500 mugs. Total paid: $47.00. Best, Priya Raman
```

REFERENCE (JSON):

```text
{"customer": "Priya Raman", "date": "2026-02-04", "items": [{"sku": "GH-405", "qty": 1}, {"sku": "IJ-500", "qty": 2}], "total": 47.00}
```

<<<BEGIN RESPONSE C43>>>
{"customer": "Priya Raman", "date": "2026-02-04", "items": [{"sku": "GH-405", "qty": 1}, {"sku": "IJ-500", "qty": 2}], "total": 47.00}
<<<END RESPONSE C43>>>

## Case C29

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
From: Tom Becker. Date of order: 12/03/2026 (that is, 12 March). 4 x KL-610, 1 x MN-720. Total $112.80, shipping included.
```

REFERENCE (JSON):

```text
{"customer": "Tom Becker", "date": "2026-03-12", "items": [{"sku": "KL-610", "qty": 4}, {"sku": "MN-720", "qty": 1}], "total": 112.80}
```

<<<BEGIN RESPONSE C29>>>
{"customer": "Tom Becker", "date": "2026-12-03", "items": [{"sku": "KL-610", "qty": 4}, {"sku": "MN-720", "qty": 1}], "total": 112.80}
<<<END RESPONSE C29>>>

## Case C03

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
Hi, this is Maria Lopez. I'd like to confirm my order from March 7, 2026: 2 x AB-100 (desk lamp) and 1 x CD-220 (bulb pack). The total came to $64.50. Thanks!
```

REFERENCE (JSON):

```text
{"customer": "Maria Lopez", "date": "2026-03-07", "items": [{"sku": "AB-100", "qty": 2}, {"sku": "CD-220", "qty": 1}], "total": 64.50}
```

<<<BEGIN RESPONSE C03>>>
{"customer": "Maria Lopez", "date": "2026-03-07", "items": [{"sku": "AB-100", "qty": 2.0}, {"sku": "CD-220", "qty": 1}], "total": 64.50}
<<<END RESPONSE C03>>>

## Case C10

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
Hi, I'm Grace Kim. I placed an order on April 3, 2026 for 3 x OP-265 notebooks. My total was $13.50.
```

REFERENCE (JSON):

```text
{"customer": "Grace Kim", "date": "2026-04-03", "items": [{"sku": "OP-265", "qty": 3}], "total": 13.50}
```

<<<BEGIN RESPONSE C10>>>
{"customer": "Grace Kim", "date": "2026-04-03", "items": [{"sku": "OP-265", "qty": 3}], "total": 13.50}
Done.
<<<END RESPONSE C10>>>

## Case C17

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
Name: Rahul Mehta. Ordered: 2026-02-10. Lines: IJ-935 (2), KL-045 (1), MN-155 (1). Total: $73.40, which includes a $4.90 delivery charge.
```

REFERENCE (JSON):

```text
{"customer": "Rahul Mehta", "date": "2026-02-10", "items": [{"sku": "IJ-935", "qty": 2}, {"sku": "KL-045", "qty": 1}, {"sku": "MN-155", "qty": 1}], "total": 73.40}
```

<<<BEGIN RESPONSE C17>>>
{"customer": "Rahul Mehta", "date": "2026-02-10", "items": [{"sku": "IJ-935", "qty": 2}, {"sku": "KL-045", "qty": 1}, {"sku": "MN-155", "qty": 1}], "total": 73.40}
<<<END RESPONSE C17>>>

## Case C01

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
Hi, this is Maria Lopez. I'd like to confirm my order from March 7, 2026: 2 x AB-100 (desk lamp) and 1 x CD-220 (bulb pack). The total came to $64.50. Thanks!
```

REFERENCE (JSON):

```text
{"customer": "Maria Lopez", "date": "2026-03-07", "items": [{"sku": "AB-100", "qty": 2}, {"sku": "CD-220", "qty": 1}], "total": 64.50}
```

<<<BEGIN RESPONSE C01>>>
```json
{
  "customer": "Maria Lopez",
  "date": "2026-03-07",
  "items": [
    {
      "sku": "AB-100",
      "qty": 2
    },
    {
      "sku": "CD-220",
      "qty": 1
    }
  ],
  "total": 64.5
}
```
<<<END RESPONSE C01>>>

## Case C36

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
Hello, Chen Wei here. On 9 January 2026 I bought 5 packs of WX-370 printer paper. Total: $42.50.
```

REFERENCE (JSON):

```text
{"customer": "Chen Wei", "date": "2026-01-09", "items": [{"sku": "WX-370", "qty": 5}], "total": 42.50}
```

<<<BEGIN RESPONSE C36>>>
```json
{
  "customer": "Chen Wei",
  "date": "2026-01-09",
  "items": [
    {
      "sku": "WX-370",
      "qty": 5
    }
  ],
  "total": 42.5
}
```
Let me know if you need anything else.
<<<END RESPONSE C36>>>

## Case C40

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
This is Sofia Rossi. Order date: March 20, 2026. I ordered 1 x YZ-480 and 3 x AB-590. Total: $35.00.
```

REFERENCE (JSON):

```text
{"customer": "Sofia Rossi", "date": "2026-03-20", "items": [{"sku": "YZ-480", "qty": 1}, {"sku": "AB-590", "qty": 3}], "total": 35.00}
```

<<<BEGIN RESPONSE C40>>>
{"customer": "Sofia Rossi", "date": "2026-03-20", "items": [{"sku": "YZ-480", "qty": 1}, {"sku": "AB-590", "qty": 3}, {"sku": "YZ-480", "qty": 3}, {"sku": "AB-590", "qty": 1}], "total": 35.00}
<<<END RESPONSE C40>>>

## Case C32

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
Hello! Please ship my order (placed 4 February 2026) to the usual address. I ordered one GH-405 kettle and two IJ-500 mugs. Total paid: $47.00. Best, Priya Raman
```

REFERENCE (JSON):

```text
{"customer": "Priya Raman", "date": "2026-02-04", "items": [{"sku": "GH-405", "qty": 1}, {"sku": "IJ-500", "qty": 2}], "total": 47.00}
```

<<<BEGIN RESPONSE C32>>>
```json
{"customer": "Priya Raman", "date": "2026-02-04", "items": [{"sku": "GH-405", "qty": 1}, {"sku": "IJ-500", "qty": 2}], "total": 47.00}
```
<<<END RESPONSE C32>>>

## Case C15

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
Hi, it's Aisha Bello. My order from April 1, 2026: 1 OP-830 backpack. It was $59.99 in total; the $5.00 shipping fee is included in that.
```

REFERENCE (JSON):

```text
{"customer": "Aisha Bello", "date": "2026-04-01", "items": [{"sku": "OP-830", "qty": 1}], "total": 59.99}
```

<<<BEGIN RESPONSE C15>>>
{"customer": "Aisha Bello", "date": "2026-04-01", "items": [{"sku": "OP-830", "qty": 1}, {"sku": "SHIPPING", "qty": 1}], "total": 59.99}
<<<END RESPONSE C15>>>

## Case C46

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
From: Tom Becker. Date of order: 12/03/2026 (that is, 12 March). 4 x KL-610, 1 x MN-720. Total $112.80, shipping included.
```

REFERENCE (JSON):

```text
{"customer": "Tom Becker", "date": "2026-03-12", "items": [{"sku": "KL-610", "qty": 4}, {"sku": "MN-720", "qty": 1}], "total": 112.80}
```

<<<BEGIN RESPONSE C46>>>
{"customer": "Tom Becker", "date": "2026-03-12", "items": [{"sku": "KL-610", "qty": 4}, {"sku": "MN-720", "qty": 1}], "total": 112.80}
<<<END RESPONSE C46>>>

## Case C35

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
This is Sofia Rossi. Order date: March 20, 2026. I ordered 1 x YZ-480 and 3 x AB-590. Total: $35.00.
```

REFERENCE (JSON):

```text
{"customer": "Sofia Rossi", "date": "2026-03-20", "items": [{"sku": "YZ-480", "qty": 1}, {"sku": "AB-590", "qty": 3}], "total": 35.00}
```

<<<BEGIN RESPONSE C35>>>
{"customer": "Sofia Rossi", "date": "2026-03-20", "items": [{"sku": "YZ-480", "qty": 1}, {"sku": "AB-590", "qty": 3}], "total": 35.00}
<<<END RESPONSE C35>>>

## Case C31

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
Hi! Daniel Okafor here, order from 2026-04-11: 2 CD-605 cables and 2 EF-715 adapters. Total was $31.96. Could you add gift wrap? It was free.
```

REFERENCE (JSON):

```text
{"customer": "Daniel Okafor", "date": "2026-04-11", "items": [{"sku": "CD-605", "qty": 2}, {"sku": "EF-715", "qty": 2}], "total": 31.96}
```

<<<BEGIN RESPONSE C31>>>
{"customer": "Daniel Okafor", "date": "2026-04-11", "items": [{"sku": "CD-605", "qty": 2}, {"sku": "EF-715", "qty": 2}], "total": 31.96, "notes": "gift wrap requested"}
<<<END RESPONSE C31>>>

## Case C12

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
Hello, Chen Wei here. On 9 January 2026 I bought 5 packs of WX-370 printer paper. Total: $42.50.
```

REFERENCE (JSON):

```text
{"customer": "Chen Wei", "date": "2026-01-09", "items": [{"sku": "WX-370", "qty": 5}], "total": 42.50}
```

<<<BEGIN RESPONSE C12>>>
{"customer": "Wei Chen", "date": "2026-01-09", "items": [{"sku": "WX-370", "qty": 5}], "total": 42.50}
<<<END RESPONSE C12>>>

## Case C23

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
Order by Emma Schulz on 5 March 2026: one GH-825 umbrella. Total charged: $24.00.
```

REFERENCE (JSON):

```text
{"customer": "Emma Schulz", "date": "2026-03-05", "items": [{"sku": "GH-825", "qty": 1}], "total": 24.00}
```

<<<BEGIN RESPONSE C23>>>
{"customer": "Emma Schulz", "date": "2026-03-05", "items": [{"sku": "GH-825", "qty": 1}], "total": 25.00}
<<<END RESPONSE C23>>>

## Case C28

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
Hello! Please ship my order (placed 4 February 2026) to the usual address. I ordered one GH-405 kettle and two IJ-500 mugs. Total paid: $47.00. Best, Priya Raman
```

REFERENCE (JSON):

```text
{"customer": "Priya Raman", "date": "2026-02-04", "items": [{"sku": "GH-405", "qty": 1}, {"sku": "IJ-500", "qty": 2}], "total": 47.00}
```

<<<BEGIN RESPONSE C28>>>
{"customer": "Priya Raman", "date": "2026-02-04", "items": [{"sku": "GH-405", "qty": 1}, {"sku": "IJ-500", "qty": 2}], "total": 47.00}
<<<END RESPONSE C28>>>

## Case C44

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
Order confirmation needed: customer Lars Nilsson, ordered 2026-02-28. Products: QR-940 x 2, ST-150 x 2, UV-260 x 1. Grand total: $88.25.
```

REFERENCE (JSON):

```text
{"customer": "Lars Nilsson", "date": "2026-02-28", "items": [{"sku": "QR-940", "qty": 2}, {"sku": "ST-150", "qty": 2}, {"sku": "UV-260", "qty": 1}], "total": 88.25}
```

<<<BEGIN RESPONSE C44>>>
{"customer": "Lars Nilsson", "date": "2026-02-28", "items": [{"sku": "QR-940", "qty": 2}, {"sku": "ST-150", "qty": 2}, {"sku": "UV-260", "qty": 1}], "total": 88.25}
<<<END RESPONSE C44>>>

## Case C08

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
Order confirmation needed: customer Lars Nilsson, ordered 2026-02-28. Products: QR-940 x 2, ST-150 x 2, UV-260 x 1. Grand total: $88.25.
```

REFERENCE (JSON):

```text
{"customer": "Lars Nilsson", "date": "2026-02-28", "items": [{"sku": "QR-940", "qty": 2}, {"sku": "ST-150", "qty": 2}, {"sku": "UV-260", "qty": 1}], "total": 88.25}
```

<<<BEGIN RESPONSE C08>>>
{"customer": "Lars Nilsson", "date": "2026-02-28", "items": [{"sku": "QR-940", "qty": 2}, {"sku": "ST-150", "qty": 2}], "total": 88.25}
<<<END RESPONSE C08>>>

## Case C39

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
Hi, I'm Grace Kim. I placed an order on April 3, 2026 for 3 x OP-265 notebooks. My total was $13.50.
```

REFERENCE (JSON):

```text
{"customer": "Grace Kim", "date": "2026-04-03", "items": [{"sku": "OP-265", "qty": 3}], "total": 13.50}
```

<<<BEGIN RESPONSE C39>>>
{"customer": "Grace Kim", "date": "2026-04-03", "items": [{"sku": "OP-265", "qty": 3.0}], "total": 13.50}
<<<END RESPONSE C39>>>

## Case C16

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
Name: Rahul Mehta. Ordered: 2026-02-10. Lines: IJ-935 (2), KL-045 (1), MN-155 (1). Total: $73.40, which includes a $4.90 delivery charge.
```

REFERENCE (JSON):

```text
{"customer": "Rahul Mehta", "date": "2026-02-10", "items": [{"sku": "IJ-935", "qty": 2}, {"sku": "KL-045", "qty": 1}, {"sku": "MN-155", "qty": 1}], "total": 73.40}
```

<<<BEGIN RESPONSE C16>>>
{"customer": "Rahul Mehta", "date": "2026-02-10", "items": [{"sku": "IJ-935", "qty": 2}, {"sku": "KL-045", "qty": 1}, {"sku": "MN-155", "qty": 1}], "total": 73.40}
<<<END RESPONSE C16>>>

## Case C25

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
Hi, it's Aisha Bello. My order from April 1, 2026: 1 OP-830 backpack. It was $59.99 in total; the $5.00 shipping fee is included in that.
```

REFERENCE (JSON):

```text
{"customer": "Aisha Bello", "date": "2026-04-01", "items": [{"sku": "OP-830", "qty": 1}], "total": 59.99}
```

<<<BEGIN RESPONSE C25>>>
{"customer": "Aisha Bello", "date": "2026-04-01", "items": [{"sku": "OP-830", "qty": 1}], "total": 59.99}
All fields were found in the email.
<<<END RESPONSE C25>>>

## Case C48

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
Order confirmation needed: customer Lars Nilsson, ordered 2026-02-28. Products: QR-940 x 2, ST-150 x 2, UV-260 x 1. Grand total: $88.25.
```

REFERENCE (JSON):

```text
{"customer": "Lars Nilsson", "date": "2026-02-28", "items": [{"sku": "QR-940", "qty": 2}, {"sku": "ST-150", "qty": 2}, {"sku": "UV-260", "qty": 1}], "total": 88.25}
```

<<<BEGIN RESPONSE C48>>>
{"customer": "Lars Nilsson", "date": "2026-02-28", "items": [{"sku": "QR-940", "qty": 2}, {"sku": "ST-150", "qty": 2}, {"sku": "UV-260", "qty": 1}], "total": 88.25}
<<<END RESPONSE C48>>>

## Case C33

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
Order by Emma Schulz on 5 March 2026: one GH-825 umbrella. Total charged: $24.00.
```

REFERENCE (JSON):

```text
{"customer": "Emma Schulz", "date": "2026-03-05", "items": [{"sku": "GH-825", "qty": 1}], "total": 24.00}
```

<<<BEGIN RESPONSE C33>>>
{"customer": "Emma Schulz", "date": "2026-03-05", "items": [{"sku": "GH-825", "qty": 1}], "total": 24.00}
All fields were found in the email.
<<<END RESPONSE C33>>>

## Case C14

PROMPT:

```text
Read the order email below and reply with a JSON object that has exactly these keys:
- "customer": the customer's full name, as written in the email
- "date": the order date, as YYYY-MM-DD
- "items": a list with one object per product line, each {"sku": <the product code, a string>, "qty": <the quantity, an integer>}
- "total": the order total in dollars, as a number
Reply with the JSON object only, optionally inside a ```json code block.

Email:
Hi, I'm Grace Kim. I placed an order on April 3, 2026 for 3 x OP-265 notebooks. My total was $13.50.
```

REFERENCE (JSON):

```text
{"customer": "Grace Kim", "date": "2026-04-03", "items": [{"sku": "OP-265", "qty": 3}], "total": 13.50}
```

<<<BEGIN RESPONSE C14>>>
{"customer": "Grace Kim", "date": "2026-04-03", "items": [{"sku": "OP-265", "qty": 3}], "total": 13.50}
<<<END RESPONSE C14>>>
