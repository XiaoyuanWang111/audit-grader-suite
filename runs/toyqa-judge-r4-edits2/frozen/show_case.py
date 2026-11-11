"""Print a frozen case's exact response.  Usage: python -B audit/frozen/show_case.py CASE_ID [--repr]"""
import pathlib
import sys

p = pathlib.Path(__file__).resolve().parent / "responses" / (sys.argv[1] + ".txt")
text = p.read_bytes().decode("utf-8")
sys.stdout.reconfigure(encoding="utf-8")
print(f"{len(text)} characters")
print("<<<RESPONSE BEGIN>>>")
print(repr(text) if "--repr" in sys.argv else text)
print("<<<RESPONSE END>>>")
