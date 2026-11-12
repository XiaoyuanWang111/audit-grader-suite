"""Recompute the git blob sha1 of every file listed in case/SOURCES.md and compare."""
import hashlib
import re

W = "<W>"
rows = re.findall(r"^\| `([^`]+)` \| (\w+) \| `[^`]+` \| `([0-9a-f]{40})` \| ([\d,]+) \|$",
                  open(f"{W}/case/SOURCES.md", encoding="utf-8").read(), re.M)
bad = 0
for path, repo, blob, size in rows:
    data = open(f"{W}/case/{path}", "rb").read()
    h = hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()
    if h != blob or len(data) != int(size.replace(",", "")):
        bad += 1
        print("MISMATCH", path, h, blob, len(data), size)
print(f"{len(rows)} files checked, {bad} mismatches")
