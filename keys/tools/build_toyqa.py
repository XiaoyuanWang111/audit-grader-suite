"""Write cases/toyqa-judge/responses.jsonl and judge_replies.jsonl. Private: part of the keys.

The recorded replies stand in for the deployed judge model. Each panel prompt gets two calls; call 1 is what the
stored run used, call 2 is the retry or a repeat at the same settings.
"""

import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
CASE = os.path.join(HERE, "..", "..", "cases", "toyqa-judge")
MODELS = ["orca-7b", "puffin-13b", "heron-32b-think", "ibis-8b-think"]

HERON_Q12 = (
    "<think>Between Africa and Australia lies the Indian Ocean.</think>\n\n"
    "Looking at a map of the Southern Hemisphere, Africa sits to the west and Australia to the east, and the "
    "water between them stretches from the Arabian Sea and the Bay of Bengal in the north all the way down to "
    "the Southern Ocean near Antarctica, with Madagascar, Mauritius, Reunion, the Seychelles and Sri Lanka "
    "scattered across it. That body of water is the Indian Ocean, the third largest ocean on Earth."
)

HERON_Q05 = (
    "<think>This is the Colombian novelist.</think>\n\n"
    "Gabriel García Márquez wrote it. The novel, first published in 1967, follows seven generations of the "
    "Buendía family in the fictional town of Macondo and is one of the defining works of magical realism; it "
    "was a major reason for the author's Nobel Prize in Literature in 1982, and it has been translated into "
    "dozens of languages."
)

IBIS_Q02 = (
    "<think>\nThe question asks when the Peace of Westphalia was signed. Let me recall what I know. The Peace "
    "of Westphalia ended the Thirty Years' War in the Holy Roman Empire and the Eighty Years' War between Spain "
    "and the Dutch Republic. It was a set of treaties negotiated in the cities of Osnabrück and Münster. I "
    "believe the treaties were signed in 1648, in October for the main treaties, although the Peace of Münster "
    "between Spain and the Dutch was signed earlier that year, in January or May. Let me double-check this "
    "against other dates I know. The Thirty Years' War started in 1618 with the Defenestration of Prague, and "
    "thirty years after 1618 is 1648, which is consistent. So the answer should be 1648. But wait, the user "
    "might be asking about a specific treaty within the Peace of Westphalia, so I should consider whether"
)

IBIS_Q05 = (
    "<think>\nOne Hundred Years of Solitude is a famous novel of magical realism. It was written by a "
    "Colombian author, Gabriel García Márquez, and published in 1967 in Spanish as Cien años de soledad. Let me "
    "make sure I am not confusing it with another novel. Other famous novels of magical realism include Love "
    "in the Time of Cholera, which is also by García Márquez, and The House of the Spirits, which is by Isabel "
    "Allende. So One Hundred Years of Solitude is by García Márquez. He won the Nobel Prize in Literature in "
    "1982. The novel tells the story of the Buendía family over seven generations in the town of Macondo. I "
    "am fairly confident about this, but let me think about whether the question wants the full name or just "
    "the surname, and whether there is any chance that the question refers to a different book with"
)

IBIS_Q10 = (
    "<think>\nThe Brandenburg Gate is an 18th-century neoclassical monument. It was built on the orders of "
    "the Prussian king Frederick William II, and it is one of the best-known landmarks of Germany. It stands "
    "at the western end of the boulevard Unter den Linden, at Pariser Platz, in Berlin. During the Cold War "
    "it stood next to the Berlin Wall, and it became a symbol of the division of the city and later of "
    "German reunification. Wait, there is also a Brandenburg Gate in Potsdam, which is a different and older "
    "gate, so I should make sure which one the question means. The question says the Brandenburg Gate, which "
    "usually refers to the one in Berlin, but the name Brandenburg might also suggest the state of "
    "Brandenburg, whose capital is Potsdam, so the user might be thinking of"
)

# question_id -> model -> (response, finish_reason, [reply call 1, reply call 2] or None)
# Items with the same rendered prompt share one cached reply, so their reply lists must agree.
P = {
    "q01": {
        "orca-7b": ("Canberra.", "stop", ["A", "A"]),
        "puffin-13b": ("Sydney", "stop", ["B", "B"]),
        "heron-32b-think": (
            "<think>The user asks for the capital of Australia. Sydney is the largest city, but the "
            "capital is Canberra.</think>\n\nCanberra",
            "stop",
            ["A", "A"],
        ),
        "ibis-8b-think": (
            "<think>\nAustralia's capital is Canberra, not Sydney.\n</think>\nCanberra",
            "stop",
            ["A", "A"],
        ),
    },
    "q02": {
        "orca-7b": ("The Peace of Westphalia was signed in 1648.", "stop", ["A", "A"]),
        "puffin-13b": ("Either 1648 or 1658, I believe.", "stop", ["B", "A"]),
        "heron-32b-think": (
            "<think>The Peace of Westphalia ended the Thirty Years' War; the treaties were signed in "
            "1648.</think>\n\n1648",
            "stop",
            ["A", "A"],
        ),
        "ibis-8b-think": (IBIS_Q02, "length", None),
    },
    "q03": {
        "orca-7b": (
            "The chemical symbol for tungsten is Tu.",
            "stop",
            ["After checking the symbol, the grade is B", "B"],
        ),
        "puffin-13b": ("W", "stop", ["A", "A"]),
        "heron-32b-think": (
            "<think>Tungsten's symbol comes from its other name, wolfram.</think>\n\nW",
            "stop",
            ["A", "A"],
        ),
        "ibis-8b-think": ("<think>\nTungsten is W.\n</think>\nW", "stop", ["A", "A"]),
    },
    "q04": {
        "orca-7b": ("Saturn", "stop", ["A", "A"]),
        "puffin-13b": ("Titan orbits Saturn.", "stop", ["A", "A"]),
        "heron-32b-think": ("<think>Titan is the largest moon of Saturn.</think>\n\nSaturn", "stop", ["A", "A"]),
        "ibis-8b-think": (
            "<think>\nTitan is a large moon. I think it orbits Jupiter, like Ganymede.\n</think>\nJupiter",
            "stop",
            ["Clearly wrong: B", "B"],
        ),
    },
    "q05": {
        "orca-7b": ("Gabriel Garcia Marquez", "stop", ["A", "A"]),
        "puffin-13b": ("I'm not sure who wrote it.", "stop", ["C", "C"]),
        "heron-32b-think": (HERON_Q05, "stop", ["A", "A"]),
        "ibis-8b-think": (IBIS_Q05, "length", None),
    },
    "q06": {
        "orca-7b": ("The skin.", "stop", ["A", "A"]),
        "puffin-13b": ("Skin", "stop", ["Comparing it with the gold target: A", "A"]),
        "heron-32b-think": (
            "<think>The skin is the largest organ by area and by weight.</think>\n\nThe skin",
            "stop",
            ["A", "A"],
        ),
        "ibis-8b-think": (
            "<think>\nThe largest internal organ is the liver.\n</think>\nThe liver",
            "stop",
            ["A liver is not skin. B", "B"],
        ),
    },
    "q07": {
        "orca-7b": ("There are 206 bones in the adult human body.", "stop", ["Grade: A", "A"]),
        "puffin-13b": ("206", "stop", ["A", "A"]),
        "heron-32b-think": ("<think>An adult skeleton typically has 206 bones.</think>\n\n206", "stop", ["A", "A"]),
        "ibis-8b-think": ("<think>\n206 bones.\n</think>\n206", "stop", ["A", "A"]),
    },
    "q08": {
        "orca-7b": ("The Amazon.", "stop", ["A", "A"]),
        "puffin-13b": ("The Amazon River", "stop", ["**A**", "A"]),
        "heron-32b-think": (
            "<think>The Amazon is the longest river in South America.</think>\n\nThe Amazon River",
            "stop",
            ["**A**", "A"],
        ),
        "ibis-8b-think": (
            "<think>\nThe longest river is the Nile.\n</think>\nThe Nile",
            "stop",
            ["Cannot be the Amazon, so this is wrong.", "B"],
        ),
    },
    "q09": {
        "orca-7b": ("Iron (Fe).", "stop", ["A", "A"]),
        "puffin-13b": ("Iron", "stop", ["Based on the gold target, the grade is A.", "A"]),
        "heron-32b-think": (
            "<think>Atomic number 26 is iron, symbol Fe.</think>\n\nIron",
            "stop",
            ["Based on the gold target, the grade is A.", "A"],
        ),
        "ibis-8b-think": (
            "<think>\nAtomic number 26. Iron or cobalt?\n</think>\nEither iron or cobalt.",
            "stop",
            ["A", "A"],
        ),
    },
    "q10": {
        "orca-7b": ("Munich", "stop", ["B", "B"]),
        "puffin-13b": ("Berlin", "stop", ["Answer matches the gold target. A", "A"]),
        "heron-32b-think": (
            "<think>The Brandenburg Gate stands in Berlin.</think>\n\nBerlin",
            "stop",
            ["Answer matches the gold target. A", "A"],
        ),
        "ibis-8b-think": (IBIS_Q10, "length", None),
    },
    "q11": {
        "orca-7b": ("It is either 1 or 2.", "stop", ["B", "B"]),
        "puffin-13b": ("2", "stop", ["A", "A"]),
        "heron-32b-think": ("<think>1 is not prime; the smallest prime is 2.</think>\n\n2", "stop", ["A", "A"]),
        "ibis-8b-think": ("<think>\nThe smallest prime is 2.\n</think>\n2", "stop", ["A", "A"]),
    },
    "q12": {
        "orca-7b": ("The Indian Ocean.", "stop", ["A", "A"]),
        "puffin-13b": ("I don't know.", "stop", ["C", "C"]),
        "heron-32b-think": (HERON_Q12, "stop", ["C", "C"]),
        "ibis-8b-think": ("<think>\nThe Indian Ocean.\n</think>\nThe Indian Ocean", "stop", ["A", "A"]),
    },
}


def contract_prompt(template, q, response):
    if "</think>" in response:
        graded = response.rsplit("</think>", 1)[1].strip()
    elif "<think>" in response:
        return None, None
    else:
        graded = response.strip()
    assert graded and "\n" not in graded and len(graded.splitlines()) == 1, (q["question_id"], graded)
    target = q["gold"] + (" (also accepted: " + ", ".join(q["aliases"]) + ")" if q["aliases"] else "")
    return graded, template.format(question=q["question"], target=target, predicted_answer=graded[:300])


def main():
    with open(os.path.join(CASE, "questions.jsonl"), encoding="utf-8") as f:
        questions = {q["question_id"]: q for q in map(json.loads, filter(str.strip, f))}
    with open(os.path.join(CASE, "judge_template.txt"), encoding="utf-8") as f:
        template = f.read()
    responses, by_prompt, order = [], {}, []
    n = 0
    for qid in sorted(P):
        for model in MODELS:
            text, finish, reps = P[qid][model]
            n += 1
            responses.append(
                {
                    "id": f"a{n:02d}",
                    "model": model,
                    "question_id": qid,
                    "response": text,
                    "finish_reason": finish,
                    "max_tokens": 192,
                    "temperature": 0.0,
                }
            )
            graded, prompt = contract_prompt(template, questions[qid], text)
            assert (prompt is None) == (reps is None), (qid, model)
            if prompt is not None:
                sha = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
                if sha in by_prompt:
                    assert by_prompt[sha] == reps, ("cached prompt with different replies", qid, model, graded)
                else:
                    by_prompt[sha] = reps
                    order.append(sha)
    replies = [
        {"prompt_sha256": sha, "call": call, "reply": reply}
        for sha in order
        for call, reply in enumerate(by_prompt[sha], 1)
    ]
    with open(os.path.join(CASE, "responses.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        for r in responses:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(os.path.join(CASE, "judge_replies.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        for r in replies:
            f.write(json.dumps(r) + "\n")
    print(f"distinct judge prompts: {len(order)}")
    trap = HERON_Q12.rsplit("</think>", 1)[1].strip()
    print(
        f"wrote {len(responses)} responses and {len(replies)} replies; trap answer length {len(trap)}, "
        f"'Indian Ocean' at {trap.find('Indian Ocean')}; q05 long answer length "
        f"{len(HERON_Q05.rsplit('</think>', 1)[1].strip())}"
    )


if __name__ == "__main__":
    main()
