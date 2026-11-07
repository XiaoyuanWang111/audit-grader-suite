"""Write cases/toymath-extract/responses.jsonl (the stored panel). Private: part of the keys."""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "cases", "toymath-extract", "responses.jsonl")

MODELS = ["alpha-7b", "beta-14b", "gamma-32b", "delta-8b"]

DELTA_P03 = (
    "Let's think about this step by step, carefully, so that we do not make any mistakes along the way.\n\n"
    "First, let's understand the situation described in the problem. We have a tank, and at the start the tank "
    "contains 2,500 liters of water. That is our starting amount, and we will need to keep track of how it changes "
    "over time.\n\n"
    "Next, the problem tells us that the tank loses water. Specifically, it loses 35 liters per day, and this "
    "happens for 20 days. To find the total amount of water lost, we need to multiply the daily loss by the number "
    "of days. So the total loss is 35 liters per day multiplied by 20 days.\n\n"
    "Let me compute that multiplication carefully. 35 times 20 can be computed as 35 times 2, which is 70, and then "
    "multiplied by 10, which gives 700. So the tank loses a total of 700 liters over the 20 days.\n\n"
    "Now, after those 20 days, the amount of water remaining in the tank is the starting amount minus the total "
    "loss. That is 2,500 liters minus 700 liters. Let me compute this subtraction carefully: 2,500 minus 700 is "
    "1,800. So after the 20 days of leaking, the tank contains 1,800 liters.\n\n"
    "But we are not done yet, because the problem also says that after this, some water is added to the tank. "
    "Specifically, 450 liters are added. So we need to take the 1,800 liters that remain and"
)

DELTA_P09 = (
    "Okay, let's carefully work through this problem one step at a time so that we get the right answer.\n\n"
    "The problem says that three friends are splitting a restaurant bill. The total amount of the bill is $86.40. "
    "They want to split it equally, which means each of the three friends pays exactly the same amount, and the "
    "three amounts together must add up to the full bill.\n\n"
    "To find out how much each friend pays, we need to divide the total bill by the number of friends. The number "
    "of friends is 3. So we need to compute 86.40 divided by 3.\n\n"
    "Let's do the division carefully. First, let's think about the whole-dollar part. 86 divided by 3 is 28 with a "
    "remainder of 2, because 3 times 28 is 84, and 86 minus 84 is 2. So far, each friend pays 28 dollars, and there "
    "are 2 dollars left over to share.\n\n"
    "Now we have the leftover 2 dollars plus the 40 cents from the original bill. That is 2 dollars and 40 cents, "
    "or 2.40 dollars. We need to divide 2.40 by 3 as well. 2.40 divided by 3 is 0.80, because 3 times 0.80 is 2.40. "
    "So each friend pays an extra 0.80 dollars on top of the 28 dollars.\n\n"
    "Adding these together, each friend pays 28 dollars plus 0.80 dollars. Let me add these carefully to make sure "
    "that the total is right, and then let me double-check the result by multiplying it by 3 to"
)

# (problem_id, {model: (response, finish_reason)})
PANEL = [
    (
        "p01",
        {
            "alpha-7b": (
                "Each muffin costs $2.75, so 6 muffins cost 6 × 2.75 = 16.50 dollars.\n"
                "Lena pays with $20, so her change is 20 − 16.50 = 3.50 dollars.\nAnswer: 3.5",
                "stop",
            ),
            "beta-14b": (
                "Cost of the muffins: 6 × $2.75 = $16.50.\nChange: $20.00 − $16.50 = $3.50.\n\nAnswer: 3.50",
                "stop",
            ),
            "gamma-32b": (
                "Step 1: Find the total cost. 6 muffins × $2.75 per muffin = $16.50.\n"
                "Step 2: Subtract it from the amount paid. $20 − $16.50 = $3.50.\n"
                "Lena receives $3.50 in change.\n\nAnswer: $3.50",
                "stop",
            ),
            "delta-8b": ("6 × 2.75 = 15.50\n20 − 15.50 = 4.50\nAnswer: 4.5", "stop"),
        },
    ),
    (
        "p02",
        {
            "alpha-7b": ("18 classes × 27 students = 486 students.\nAnswer: 486", "stop"),
            "beta-14b": (
                "Multiply the number of classes by the class size: 18 × 27 = 18 × 20 + 18 × 7 = 360 + 126 = 486.\n\n"
                "Answer: 486",
                "stop",
            ),
            "gamma-32b": (
                "To find the total, multiply the number of classes by the students per class.\n"
                "18 × 27 = 486.\nThe school has 486 students.\n\nAnswer: 486 students",
                "stop",
            ),
            "delta-8b": ("18 × 27 = 476\nAnswer: 476", "stop"),
        },
    ),
    (
        "p03",
        {
            "alpha-7b": (
                "Water lost: 35 × 20 = 700 liters.\nWater left: 2,500 − 700 = 1,800 liters.\nAnswer: 1,800",
                "stop",
            ),
            "beta-14b": (
                "Loss over 20 days: 35 × 20 = 700 L.\nAfter the leak: 2,500 − 700 = 1,800 L.\n"
                "After adding 450 L: 1,800 + 450 = 2,250 L.\n\nAnswer: 2,250",
                "stop",
            ),
            "gamma-32b": (
                "Daily loss: 35 L for 20 days, so 700 L are lost.\nRemaining: 2500 − 700 = 1800 L.\n"
                "Add 450 L: 1800 + 450 = 2250 L.\n\nAnswer: 2250",
                "stop",
            ),
            "delta-8b": (DELTA_P03, "length"),
        },
    ),
    (
        "p04",
        {
            "alpha-7b": ("Starting temperature: 4 °C. It drops by 11 degrees: 4 − 11 = −7.\nAnswer: -7", "stop"),
            "beta-14b": ("4 − 11 = −7, so the temperature at midnight was −7 °C.\n\nAnswer: -7", "stop"),
            "gamma-32b": (
                "The temperature fell 11 degrees from 4 °C, so it reached 4 − 11 = −7 °C.\n\nAnswer: -7\n\n"
                "Let me know if you would like this converted to Fahrenheit.",
                "stop",
            ),
            "delta-8b": (
                "The temperature dropped by 11 degrees from 4 degrees, so the difference is 11 − 4 = 7.\nAnswer: 7",
                "stop",
            ),
        },
    ),
    (
        "p05",
        {
            "alpha-7b": ("Speed = distance / time = 180 / 2.5 = 72 km/h.\nAnswer: 72", "stop"),
            "beta-14b": ("Average speed = 180 km ÷ 2.5 h = 72 km/h.\n\nAnswer: 72", "stop"),
            "gamma-32b": (
                "Average speed is total distance divided by total time.\n180 km ÷ 2.5 h = 72 km/h.\n\n"
                "Answer: 72 km/h",
                "stop",
            ),
            "delta-8b": ("180 / 2.5 = 7.2\nAnswer: 7.2", "stop"),
        },
    ),
    (
        "p06",
        {
            "alpha-7b": (
                "After Sam gives 5, Sam has 9 and Ria has 19. After Ria gives 5 back, Sam has 14 and Ria has 14. "
                "The difference is 14 − 14 = 0.\nAnswer: 0",
                "stop",
            ),
            "beta-14b": (
                "The two transfers cancel out, so both still have 14 marbles. Sam has 0 more than Ria.\n\nAnswer: 0",
                "stop",
            ),
            "gamma-32b": (
                "Start: Sam 14, Ria 14.\nAfter Sam gives 5: Sam 9, Ria 19.\nAfter Ria gives 5: Sam 14, Ria 14.\n"
                "Difference: 14 − 14 = 0.\n\nAnswer: 0",
                "stop",
            ),
            "delta-8b": (
                "Sam gives Ria 5 marbles, so Sam has 9 and Ria has 19. Ria has 10 more marbles.\nAnswer: 10",
                "stop",
            ),
        },
    ),
    (
        "p07",
        {
            "alpha-7b": ("25% of 12000 is 3000. February revenue = 12000 + 3000 = 15000.\nAnswer: 15000", "stop"),
            "beta-14b": (
                "Growth: 25% × $12,000 = $3,000.\nFebruary revenue: $12,000 + $3,000 = $15,000.\n\nAnswer: 15,000",
                "stop",
            ),
            "gamma-32b": (
                "February revenue = January revenue × 1.25 = 12,000 × 1.25 = 15,000 dollars.\n\nAnswer: 15000",
                "stop",
            ),
            "delta-8b": ("25% of 12,000 = 3,000\nAnswer: 3000", "stop"),
        },
    ),
    (
        "p08",
        {
            "alpha-7b": ("The width is (46 − 15) / 2 = 15.5 cm. Area = 15 × 15.5 = 232.5.\nAnswer: 232.5", "stop"),
            "beta-14b": (
                "Perimeter = 2(L + W), so 46 = 2(15 + W), 23 = 15 + W and W = 8.\nArea = 15 × 8 = 120 cm².\n\n"
                "Answer: 120",
                "stop",
            ),
            "gamma-32b": (
                "2 × (15 + w) = 46, so 15 + w = 23 and w = 8 cm.\nArea = 15 × 8 = 120 cm².\n\nAnswer: 120\n"
                "(The rectangle measures 15 cm by 8 cm.)",
                "stop",
            ),
            "delta-8b": ("Half the perimeter is 23. Width = 23 − 15 = 8. Area = 15 × 8 = 120.\nAnswer: 120", "stop"),
        },
    ),
    (
        "p09",
        {
            "alpha-7b": ("86.40 / 3 = 28.80\nAnswer: 28.8", "stop"),
            "beta-14b": ("$86.40 ÷ 3 = $28.80 per person.\n\nAnswer: 28.80", "stop"),
            "gamma-32b": ("Each friend pays an equal share: $86.40 ÷ 3 = $28.80.\n\nAnswer: 28.80 dollars", "stop"),
            "delta-8b": (DELTA_P09, "length"),
        },
    ),
    (
        "p10",
        {
            "alpha-7b": ("312 ÷ 24 = 13 days.\nAnswer: 13", "stop"),
            "beta-14b": ("312 / 24 = 13, so Mia needs 13 days.\n\nAnswer: 13", "stop"),
            "gamma-32b": (
                "Pages per day: 24. Days = 312 / 24.\n24 × 12 = 288, so after 12 days she has read 288 pages.\n"
                "Answer: 12\n\nWait, 288 is less than 312, so 12 days are not enough. 24 × 13 = 312, so she "
                "finishes on day 13.\n\nAnswer: 13",
                "stop",
            ),
            "delta-8b": ("312 / 24 = 13\nAnswer: 13", "stop"),
        },
    ),
    (
        "p11",
        {
            "alpha-7b": ("7 rows × 12 plants = 84 plants.\nAnswer: 84", "stop"),
            "beta-14b": ("Plants: 7 × 12 = 84. Tomatoes: 84 × 9 = 756.\n\nAnswer: 756", "stop"),
            "gamma-32b": ("Number of plants: 7 × 12 = 84.\nTomatoes: 84 × 9 = 756.\n\nAnswer: 756", "stop"),
            "delta-8b": (
                "There are 7 × 12 = 84 plants, and each yields 9 tomatoes, so the garden yields 84 × 9 = 756 "
                "tomatoes.",
                "stop",
            ),
        },
    ),
    (
        "p12",
        {
            "alpha-7b": ("3 eggs per 2 cups is 1.5 eggs per cup. 10 cups × 1.5 = 15 eggs.\nAnswer: 15", "stop"),
            "beta-14b": (
                "The ratio is 3 eggs to 2 cups. 10 cups is 5 times 2 cups, so we need 5 × 3 = 15 eggs.\n\n" "Answer: 15",
                "stop",
            ),
            "gamma-32b": (
                "Scale the recipe: 10 cups ÷ 2 cups = 5 batches, and 5 × 3 eggs = 15 eggs.\n\nAnswer: 15",
                "stop",
            ),
            "delta-8b": ("3 / 2 × 10 = 15\nAnswer: 15", "stop"),
        },
    ),
]


def main():
    rows = []
    n = 0
    for pid, by_model in PANEL:
        for model in MODELS:
            text, finish = by_model[model]
            n += 1
            rows.append(
                {
                    "id": f"r{n:02d}",
                    "model": model,
                    "problem_id": pid,
                    "response": text,
                    "finish_reason": finish,
                    "max_tokens": 256,
                    "temperature": 0.0,
                }
            )
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"wrote {len(rows)} responses to {os.path.normpath(OUT)}")


if __name__ == "__main__":
    main()
