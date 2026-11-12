p = "fixtures_data.py"
s = open(p, encoding="utf-8").read()
anchor = "]\n\n\ndef fixture_id"
new = '''    # added after the development panel review (labels from the contract; see ISSUE.md)
    ("detectable_format:multiple_sections", {"num_sections": 2, "section_spliter": "SECTION"}, '"SECTION 1\nText one.\nSECTION 2\nText two."', P, []),
    ("detectable_format:multiple_sections", {"num_sections": 2, "section_spliter": "SECTION"}, "SECTION 1\nText one. SECTION 2\nText two.", P, []),
    ("detectable_format:number_highlighted_sections", {"num_highlights": 2}, "\u8fd9\u662f*\u91cd\u70b9*\u548c*\u5173\u952e*\u3002", P, []),
    ("detectable_format:square_brackets", None, "[J][u][s][t] [g][o]", F, []),
    ("length_constraints:number_paragraphs", {"num_paragraphs": 3}, "First.***\n\nSecond.***\n\nThird.", P, []),
    ("length_constraints:number_paragraphs", {"num_paragraphs": 2}, "First paragraph here. *** Second paragraph here.", P, []),
    ("combination:two_responses", None, "Answer one.\n******\nAnswer two.\n******", F, ["D-two-responses-edge"]),
    ("keywords:no_adjacent_consecutive", None, "\u042f \u0432\u0438\u0436\u0443 \u0433\u043e\u0440\u043e\u0434.", P, ["D-consecutive-script"]),
    (LOW, {"N": 2}, "\u8fd9\u662f \u8fd9\u662f \u8fd9\u662f \u6d4b\u8bd5", P, []),
    (LOW, {"N": 2}, "\u043c\u044b \u043c\u044b \u043c\u044b \u0438\u0434\u0451\u043c", F, []),
    ("keywords:palindrome", None, "A man, a plan, a canal, Panama.", P, []),
    ("keywords:palindrome", None, "Noon is lunch time.", P, []),
    ("detectable_format:sentence_hyphens", None, "I like tea - it is warm - it calms me", F, []),
    ("detectable_format:sentence_hyphens", None, "CAN-DO-USED-IN-THE-BUILDING", P, []),
    ("change_case:english_capital", None, "THIS IS ENGLISH TEXT FOR YOU AND IT IS LONG ENOUGH TO READ.\n\n\u8fd9\u662f\u4e00\u4e2a\u5b8c\u6574\u7684\u4e2d\u6587\u6bb5\u843d\u3002", F, ["D-english-part"]),
'''
assert s.count(anchor) == 1
s = s.replace(anchor, new + anchor)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("added")
