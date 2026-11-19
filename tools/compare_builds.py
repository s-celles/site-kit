#!/usr/bin/env python3
"""Compare two builds of the same commit (SPEC.md, SK-DETERMINISM).

    python3 -I compare_builds.py BUILD_A BUILD_B [--config site-kit.json] [--volatile REGEX ...]

Two builds of one commit must have the same files with the same contents.
A generator line that cannot be suppressed (a build date) is declared as a
regular expression under "volatile" in site-kit.json, or with --volatile,
and masked in text files before the comparison. Exit status 1 if the builds
differ.
"""
import argparse
import json
import pathlib
import re
import sys

TEXT = {".html", ".htm", ".xml", ".txt", ".json", ".js", ".css", ".svg", ".md", ".csv", ".tsv"}


def files(root):
    return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}


def masked(path, patterns):
    data = path.read_bytes()
    if path.suffix.lower() not in TEXT or not patterns:
        return data
    text = data.decode("utf-8", errors="surrogateescape")
    for p in patterns:
        text = re.sub(p, "", text, flags=re.S)
    return text.encode("utf-8", errors="surrogateescape")


def compare(a, b, volatile=()):
    """Differences between the builds a and b, one line each."""
    a, b = pathlib.Path(a), pathlib.Path(b)
    for d in (a, b):
        if not d.is_dir():
            raise FileNotFoundError(f"no build at {d}")
    fa, fb = files(a), files(b)
    out = [f"{f}: only in {a}" for f in sorted(fa - fb)] + [f"{f}: only in {b}" for f in sorted(fb - fa)]
    for f in sorted(fa & fb):
        da, db = masked(a / f, volatile), masked(b / f, volatile)
        if da == db:
            continue
        if (a / f).suffix.lower() in TEXT:
            la, lb = da.split(b"\n"), db.split(b"\n")
            n = next((i for i, (x, y) in enumerate(zip(la, lb)) if x != y), min(len(la), len(lb)))
            out.append(f"{f}: line {n + 1} differs")
        else:
            out.append(f"{f}: content differs")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--config", help="site-kit.json, for its volatile patterns")
    ap.add_argument("--volatile", action="append", default=[], help="a regular expression to mask")
    args = ap.parse_args(argv)
    volatile = list(args.volatile)
    if args.config:
        volatile += json.loads(pathlib.Path(args.config).read_text()).get("volatile", [])
    try:
        diffs = compare(args.a, args.b, volatile)
    except FileNotFoundError as e:
        print(f"SK-DETERMINISM: {e}")
        return 2
    for d in diffs:
        print(d)
    print("SK-DETERMINISM: the two builds are identical" if not diffs else f"SK-DETERMINISM: {len(diffs)} difference(s)")
    return 1 if diffs else 0


if __name__ == "__main__":
    sys.exit(main())
