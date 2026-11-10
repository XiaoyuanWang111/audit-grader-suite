# Changes to audit/contracts.md after its hash was recorded

`audit/contracts.md` (sha256 fcbfcf62..., 2026-11-10 05:55:05 UTC) is kept as hashed.
Each change below was made after reading the grader code, with its reason. None of
them adopts the grader's behavior as a contract; C1 and C2 narrow a decision whose
non-proposed reading the text does not support, and C3-C9 add readings or split
entries so that a grader verdict is classified as a decision rather than a finding.

| Id | Entry | Change | Reason |
|---|---|---|---|
| C1 | D-keyword-form | The other reading is narrowed to inflected forms of the keyword ("doors", "whispered"). A match inside an unrelated word ("indoor" for "door", "selfish" for "fish", "throughout" for "through") is wrong under every reading. | The original A column lumped inflections with arbitrary substrings; no careful reader counts "fish" in "selfish" as the keyword. |
| C2 | D-minor-words | The reading "every word capitalized" is dropped. The instruction defines title case in its own parenthetical as capitalizing "every major word", so a lower-case minor word ("of", "the", "and", "a") is allowed under the text. The remaining decision is which words are minor (for example five-letter prepositions such as "about"). | The original A column contradicted the definition the prompt gives. |
| C3 | D-punct-set | A third reading is added: the six clause and sentence marks `. , ? ! ; :` plus the interrobang. P is unchanged. | A careful reader could take "standard punctuation marks ... including semicolons, colons" to mean the sentence-level marks only. |
| C4 | D-vowel | Split into D-vowel-scope (across the whole text, P; or per word, A) and D-vowel-paragraph (paragraph form not graded, P; or the response must be one paragraph with no line break, A). | "Write a paragraph" is a second requirement that a reader may or may not grade. |
| C5 | D-list-sep | A reading is added: SEP is a line-start marker, one per item (at least two markers), as bullet points are. P (inline or line-start) is unchanged. | "instead of bullet points use SEP" supports the marker reading. |
| C6 | D-nbb-order | A reading is added: nothing but bullets may follow the first bullet. P (text after the bullets allowed) is unchanged. | "two sentences ... followed by ... two bullet points" can be read as the whole layout. |
| C7 | D-pronoun-set | Clarified that P counts word forms whatever their role (as D-conj-role does), so determiner uses of all, some, each, this, that count; the other reading counts only pronoun uses. | Same form-versus-role question as D-conj-role. |
| C8 | D-japanese-digits (new) | P: a numeral at an Nth position is not Japanese, so it fails. A: numerals are language-neutral and may stand at an Nth position. | The text does not say whether digits belong to a language. |
| C9 | D-options-exact | Clarified that the entry also covers letter-option variants: "B)", "b", "(b)" and "b) Larceny" pass under P, and only the exact strings "a)".."d)" pass under the strictest reading. | Case and the option text after the letter are both undefined by "Answer with one of the following options". |
| C10 | D-template-repeat (new) | P: the filled template appears once. A: a response may fill the template more than once. | 43 panel responses repeat all three labels; "Use this exact template" does not say whether a second filled copy breaks it. |
| C11 | D-section | No change to the entry; the replacement grader gives it a switch. Under A (whole text is one section when there are no headings) the grader's single-italic test is still wrong when the first section does not begin with the italic thesis or when a heading-delimited section lacks one (F-thesis-each). | Separates the decision from the finding in the panel counts. |
