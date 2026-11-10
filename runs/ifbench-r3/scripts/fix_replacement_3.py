p = "audit/replacement/ifbench_contract.py"
s = open(p, encoding="utf-8").read()
anchor = '    "uganda": "uganda", "zambia": "zambia", "zimbabwe": "zimbabwe", "western sahara": "EXTRA", "somaliland": "EXTRA",\n}'
assert s.count(anchor) == 1
extra = ('    "uganda": "uganda", "zambia": "zambia", "zimbabwe": "zimbabwe", "western sahara": "EXTRA", "somaliland": "EXTRA",\n'
         '    "congo (republic of the)": "congo", "congo (republic)": "congo", "republic of the congo (congo-brazzaville)": "congo",\n'
         '    "congo (democratic republic of the)": "drc", "congo, the democratic republic of the": "drc",\n'
         '    "democratic republic of the congo (drc)": "drc", "democratic republic of congo (drc)": "drc",\n'
         '    "cape verde (cabo verde)": "cabo verde", "cabo verde (cape verde)": "cabo verde",\n'
         '    "cote d\'ivoire (ivory coast)": "civ", "ivory coast (cote d\'ivoire)": "civ", "swaziland (eswatini)": "eswatini",\n'
         '    "gambia, the": "gambia", "sao tome & principe": "stp", "tanzania, united republic of": "tanzania",\n'
         '}')
s = s.replace(anchor, extra)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")
