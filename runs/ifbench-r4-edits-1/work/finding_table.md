| F-CONJ | `count:conjunctions#85e471f8` | `'Tea and cake and, jam. And milk. AND bread.'` | fail | True | True |
| F-KWM | `count:keywords_multiple#487922bc` | `'A door. Bread and bread. Blue, blue, blue. Lamp lamp lamp lamp lamp. River river river river river river river. The driver waved.'` | pass | False | True |
| F-NUM | `count:numbers#57019ffa` | `'From 1990-2005 the town grew.'` | pass | False | False |
| F-CONTRACTION | `count:word_count_range#7c51fcd2` | `"alpha bravo charlie delta echo foxtrot golf hotel india juliet kilo lima mike november oscar papa quebec romeo sierra tango uniform victor whiskey xray yankee zulu alpha bravo charlie delta echo foxtrot golf hotel india juliet kilo lima mike november oscar papa quebec romeo sierra tango uniform victor whiskey xray yankee zulu don't can't won't isn't aren't."` | pass | False | False |
| F-CONTRACTION | `ratio:stop_words#2cf31b94` | `"Cats don't bark loudly."` | pass | False | False |
| F-STYPE | `ratio:sentence_type#3738487b` | `'Wow! Amazing!'` | fail | True | True |
| F-STYPE | `ratio:sentence_type#389403cd` | `'It is so. It is "true." Why?'` | pass | False | False |
| F-SBAL | `ratio:sentence_balance#b7761e44` | `'He had critics. "Why?" "Stop!"'` | pass | False | False |
| F-SWORDS | `ratio:sentence_words#9bf12340` | `'Cats sleep all day. Dogs sleep all day. Fish swim in ponds.'` | fail | True | False |
| F-INDENT | `format:line_indent#5ca22c1c` | `'Step one\n\n\n  Step two\n    Step three'` | pass | False | False |
| F-INDENT | `format:line_indent#3006987f` | `'Step one\n\tStep two\n\t\tStep three'` | pass | False | False |
| F-NEWLINE | `format:newline#e5f78837` | `'Alpha Beta\n \nGamma'` | fail | True | True |
| F-NEWLINE | `format:newline#07733d8b` | `'Alpha\n \nGamma'` | pass | False | False |
| F-LIST | `format:list#2584034b` | `'Entanglement is a well-known effect in state-of-the-art physics.'` | fail | True | True |
| F-LIST | `format:list#10c5eeb0` | `'!?!? Preludes are short.\n* Caprichos are lively.\n!?!? Romances are lyrical.'` | fail | True | True |
| F-NBB | `format:no_bullets_bullets#625c6237` | `'Deism is weak.\n\nIt ignores revelation.\n* Point one\n* Point two'` | pass | False | False |
| F-NBB | `format:no_bullets_bullets#d44d9892` | `'Deism is weak. It ignores revelation.\n* Point one\n* Point two\n'` | pass | False | False |
| F-NBB | `format:no_bullets_bullets#653b564a` | `'Deism is weak. It ignores revelation.\n\n* Point one\n* Point two\n\nIn sum, deism fails.'` | pass | False | False |
| F-NBB | `format:no_bullets_bullets#41d069e7` | `'Deism is weak! It ignores revelation!\n* Point one\n* Point two'` | fail | True | True |
| F-OPTIONS | `format:options#927580bf` | `'Yes\n'` | pass | False | False |
| F-OPTIONS | `format:options#bf4d4ea8` | `'I don\u2019t know'` | pass | False | False |
| F-TEMPLATE | `format:output_template#3880c6d1` | `'Sure, here it is.\nMy Answer: X.\nMy Conclusion: Y.\nFuture Outlook: Z.'` | fail | True | True |
| F-TEMPLATE | `format:output_template#e6f2680a` | `'My Conclusion: Y.\nMy Answer: X.\nFuture Outlook: Z.'` | fail | True | True |
| F-TEMPLATE | `format:output_template#32aa85d6` | `'My Answer: [answer] My Conclusion: [conclusion] Future Outlook: [outlook]'` | fail | True | True |
| F-PAREN | `format:parentheses#9fc38630` | `'((((( x )'` | fail | True | True |
| F-QU | `format:quote_unquote#9f008108` | `'"a", "b" means x'` | fail | True | True |
| F-QU | `format:quote_unquote#278caa31` | `'The claim is \u201cfalse\u201d'` | fail | True | True |
| F-QUOTES | `format:quotes#60347bc9` | `'\u201cShe said \u2018He wrote \u201cyes\u201d there\u2019 again\u201d'` | pass | False | False |
| F-SUBB | `format:sub-bullets#212d5ee1` | `'Memorization is copying.'` | fail | True | True |
| F-SUBB | `format:sub-bullets#da21f6a4` | `'* A well-known fact\n* Another long-term view'` | fail | True | True |
| F-SUBB | `format:sub-bullets#35b65fdf` | `'**Overview**\n* Memorization\n  - Copying\n* Why care\n  - Privacy'` | pass | False | False |
| F-THESIS | `format:thesis#844e324a` | `'It favors tradition, <i>the party is conservative</i>.'` | fail | True | True |
| F-THESIS | `format:thesis#8b0c3daa` | `'<i>The party is conservative.</i>'` | pass | False | False |
| F-TITLE | `format:title_case#95beef7e` | `"Don't Stop Believing."` | pass | False | False |
| F-TITLE | `format:title_case#26d02f70` | `'The Party of Japan'` | pass | False | False |
| F-ALLIT | `sentence:alliteration_increment#1a1b19f2` | `'ReLU is simple. Big bold models matter. Very vast vectors vary.'` | pass | False | False |
| F-ALLIT | `sentence:alliteration_increment#20fedc4e` | `'Very vast vectors. Big bold cats, tiny tame dogs, red rats.'` | fail | True | True |
| F-CAPITALS | `custom:european_capitals_sort#113de779` | `'Reykjavik, Helsinki, Oslo, Tallinn, Stockholm, Riga, Moscow, Copenhagen, Vilnius, Minsk, Dublin, Berlin, Amsterdam, Warsaw, London, Brussels, Kyiv, Prague, Luxembourg, Paris, Vienna, Bratislava, Budapest, Vaduz, Chisinau, Bern, Ljubljana, Zagreb'` | pass | False | False |
| F-AFRICA | `custom:reverse_newline#1d2258e7` | `'Zambia\nZimbabwe\nUganda\nTunisia\nTogo\nTanzania\nSudan\nSouth Sudan\nSouth Africa\nSomalia\nSierra Leone\nSeychelles\nSenegal\nSao Tome and Principe\nRwanda\nRepublic of the Congo\nNigeria\nNiger\nNamibia\nMozambique\nMorocco\nMauritius\nMauritania\nMali\nMalawi\nMadagascar\nLibya\nLiberia\nLesotho\nKenya\nIvory Coast\nGuinea-Bissau\nGuinea\nGhana\nGambia\nGabon\nEthiopia\nEswatini\nEritrea\nEquatorial Guinea\nEgypt\nDjibouti\nDemocratic Republic of the Congo\nComoros\nChad\nCentral African Republic\nCameroon\nCabo Verde\nBurundi\nBurkina Faso\nBotswana\nBenin\nAngola\nAlgeria'` | fail | True | True |
| F-AFRICA | `custom:reverse_newline#1a03b821` | `'1. Zimbabwe\n2. Zambia\n3. Uganda\n4. Tunisia\n5. Togo\n6. Tanzania\n7. Sudan\n8. South Sudan\n9. South Africa\n10. Somalia\n11. Sierra Leone\n12. Seychelles\n13. Senegal\n14. Sao Tome and Principe\n15. Rwanda\n16. Republic of the Congo\n17. Nigeria\n18. Niger\n19. Namibia\n20. Mozambique\n21. Morocco\n22. Mauritius\n23. Mauritania\n24. Mali\n25. Malawi\n26. Madagascar\n27. Libya\n28. Liberia\n29. Lesotho\n30. Kenya\n31. Ivory Coast\n32. Guinea-Bissau\n33. Guinea\n34. Ghana\n35. Gambia\n36. Gabon\n37. Ethiopia\n38. Eswatini\n39. Eritrea\n40. Equatorial Guinea\n41. Egypt\n42. Djibouti\n43. Democratic Republic of the Congo\n44. Comoros\n45. Chad\n46. Central African Republic\n47. Cameroon\n48. Cabo Verde\n49. Burundi\n50. Burkina Faso\n51. Botswana\n52. Benin\n53. Angola\n54. Algeria'` | pass | False | False |
| F-ALPHA-SENT | `custom:sentence_alphabet#cca075f6` | `'Alice awoke early. Birds sang outside. "Coffee brewed slowly," she said. Dogs barked twice. Every neighbor waved. Fog covered town. Grandma baked bread. Her kitchen smelled sweet. Its warmth spread. Joy filled hearts. Kids ran around. Laughter echoed loudly. Mothers chatted happily. Nobody felt lonely. Old friends arrived. Puppies played nearby. Quiet returned later. Rain began falling. Soon everyone left. The house grew still. Under blankets, Alice read. Very late, she slept. Wind howled softly. Xylophones chimed in dreams. Yesterday faded away. Zebras danced in her sleep.'` | pass | False | True |
| F-CSVSPECIAL | `custom:csv_special_character#be0ed161` | `'ProductID,Category,Brand,Price,Stock\nP01,Tools,"Smith & Sons",11.99,3\nP02,Tools,Acme\nP03,Tools,Acme\nP04,Tools,Acme\nP05,Tools,Acme\nP06,Tools,Acme\nP07,Tools,Acme\nP08,Tools,Acme\nP09,Tools,Acme\nP10,Tools,Acme\nP11,Tools,Acme\nP12,Tools,Acme\nP13,Tools,Acme\nP14,Tools,Acme'` | fail | True | True |
| F-EXC | `custom:csv_quotes#1737bf8c` | `'"StudentID"\t"Subject"\t"Grade"\t"Semester"\t"Score"\n"S1"\t\t"A"\t"Fall"\t"95"\n"S2"\t"Art"\t"B"\t"Spring"\t"85"\n"S3"\t"Biology"\t"C"\t"Fall"\t"75"'` | fail | IndexError | IndexError |
| F-DATE | `custom:date_format_list#443b4fe3` | `'1796-00-00, 1805-12-02'` | fail | True | True |
| F-MCQ | `custom:mcq_count_length#278fd6e3` | `'Question 1: Who painted Guernica?\nA) Monet\nB) Picasso\nC) Dali\nD) Warhol\nE) Pollock\n\nQuestion 2: Which artist led the Pop Art movement?\nA) Monet\nB) Picasso\nC) Dali\nD) Warhol\nE) Pollock\n\nQuestion 3: Which painter is best known for drip paintings made on the floor?\nA) Monet\nB) Picasso\nC) Dali\nD) Warhol\nE) Pollock\n\nQuestion 4: Which Spanish surrealist painted melting clocks in the famous 1931 work The Persistence of Memory?\nA) Monet\nB) Picasso\nC) Dali\nD) Warhol\nE) Pollock\n\nExplanation: these test core knowledge.'` | fail | True | True |
| F-MCQ | `custom:mcq_count_length#d7804689` | `'**Question 1:** Who painted Guernica?\nA) Monet\nB) Picasso\nC) Dali\nD) Warhol\nE) Pollock\n\n**Question 2:** Which artist led the Pop Art movement?\nA) Monet\nB) Picasso\nC) Dali\nD) Warhol\nE) Pollock\n\n**Question 3:** Which painter is best known for drip paintings made on the floor?\nA) Monet\nB) Picasso\nC) Dali\nD) Warhol\nE) Pollock\n\n**Question 4:** Which Spanish surrealist painted melting clocks in the famous 1931 work The Persistence of Memory?\nA) Monet\nB) Picasso\nC) Dali\nD) Warhol\nE) Pollock'` | pass | False | False |
| F-RCHANGE | `repeat:repeat_change#093afd81` | `'Use Python code: construct a 3-layers feedforward network with 8 input neurons, 20 hidden neurons, and 2 output neurons.\n'` | fail | True | True |
| F-RCHANGE | `repeat:repeat_change#a49f0741` | `'Use  Python code: construct a 3-layers feedforward network with 8 input neurons, 20 hidden neurons, and 2 output neurons.'` | fail | True | True |
| F-RSPAN | `repeat:repeat_span#88520227` | `'code and theory behind'` | pass | False | True |
| F-VERB | `words:start_verb#45b07647` | `'Explore Galois theory through symmetry.'` | pass | False | False |
| F-VERB | `words:start_verb#b16e7117` | `'**Consider** the field extension.'` | pass | False | False |
| F-WPOS | `words:words_position#0b054f68` | `'Art, despite war, grew despite everything.'` | pass | False | True |
| F-MARKUP | `count:person_names#44a20674` | `'Emma, _Liam_ and Sophia met at noon.'` | pass | False | False |
| F-MARKUP | `words:no_consecutive#6af2c5f4` | `'Honest <b>talks</b> build trust.'` | pass | False | False |
