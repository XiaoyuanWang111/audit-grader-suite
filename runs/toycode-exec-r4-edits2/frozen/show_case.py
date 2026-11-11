"""Print the exact response of one case: python -B show_case.py <case_id> [--repr]."""
import os
import sys

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'responses', sys.argv[1] + '.txt')
text = open(path, 'rb').read().decode('utf-8')
print(repr(text) if '--repr' in sys.argv[2:] else text)
