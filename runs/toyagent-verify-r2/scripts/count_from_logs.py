"""Count server errors in the task's logs under the audit contract (CONTRACT.md, C0).

Reads only the sandbox input files. Prints the contract count and the counts that
common wrong methods give, so wrong answers in the trials can be traced.
"""
import gzip
import pathlib
import re
import sys

LOGS = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "case/task/environment/logs")
LINE = re.compile(r'^(\S+) (\S+) (\S+) \[([^\]]*)\] "(.*)" (\S+) (\S+)$')


def lines(name):
    p = LOGS / name
    raw = gzip.decompress(p.read_bytes()) if name.endswith(".gz") else p.read_bytes()
    text = raw.decode("ascii")
    assert text.endswith("\n"), name
    return text[:-1].split("\n")


def main():
    total = 0
    per_file = {}
    awk9 = 0          # awk '$9 ~ /^5/' style: 9th whitespace field
    loose = 0         # grep ' 5[0-9][0-9]' anywhere in the line
    bad = []
    for name in ("access.log", "access.log.1", "access.log.2.gz"):
        n = 0
        a = 0
        g = 0
        for i, ln in enumerate(lines(name), 1):
            m = LINE.match(ln)
            if not m:
                bad.append((name, i, ln))
                continue
            status = m.group(6)
            if re.fullmatch(r"[0-9]{3}", status) and 500 <= int(status) <= 599:
                n += 1
            f = ln.split()
            if len(f) >= 9 and re.fullmatch(r"5[0-9][0-9]", f[8]):
                a += 1
            if re.search(r" 5[0-9][0-9]", ln):
                g += 1
        per_file[name] = (n, a, g, i)
        total += n
        awk9 += a
        loose += g
    for k, (n, a, g, cnt) in per_file.items():
        print(f"{k}: lines={cnt} contract={n} awk_field9={a} grep_space5xx={g}")
    print("unparsed lines:", bad)
    print("CONTRACT COUNT N =", total)
    print("awk $9 count (all three files) =", awk9)
    print("grep ' 5[0-9][0-9]' count (all three files) =", loose)
    no_gz = per_file["access.log"][0] + per_file["access.log.1"][0]
    print("contract count without the .gz file =", no_gz)
    print("contract count of access.log only =", per_file["access.log"][0])


if __name__ == "__main__":
    main()
