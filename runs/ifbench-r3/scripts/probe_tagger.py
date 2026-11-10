import sys
sys.path.insert(0, "audit/lib")
import ifb
import nltk
for s in ["Imagine an empire built on eternal suffering.", "Build an empire of endless pain.", "Consider an empire.",
          "Create a world where minds suffer.", "Explore the idea.", "Envision a realm.", "Picture this empire.",
          "Is it possible?", "Write a story.", "**Imagine** an empire.", "Imagine", "Describe it.", "Let us begin.",
          "Delve into it.", "Discover the empire.", "Craft a tale.", "Establish an empire.", "Forge an empire."]:
    toks = nltk.word_tokenize(s)
    print(f"{s!r:50s} {nltk.pos_tag(toks)[:3]}")
