#!/usr/bin/env python3
"""Check a generated site against the site-kit SPEC.

    python3 -I check_site.py --hugo site/hugo.yaml --content OUT/content --static OUT/static

Checks what can be checked on the Hugo configuration and the generated
content, before Hugo runs. Each rule has the identifier SPEC.md gives it.
Exit status 1 if a rule fails.
"""
import argparse
import pathlib
import re
import sys
from collections import namedtuple

Violation = namedtuple("Violation", "rule message")

# menu order after the project's own registries (SPEC.md, "Navigation")
TAIL = ("Upstream", "History", "Methodology", "Docs", "GitHub", "Search")
MODULE = "github.com/s-celles/site-kit"
REQUIRED_PAGES = {"SK-PAGE-UPSTREAM": "upstream", "SK-PAGE-HISTORY": "history",
                  "SK-PAGE-METHODOLOGY": "methodology", "SK-PAGE-STATUSES": "statuses"}


def menu(hugo_text):
    """[(name, weight)] of menu.main, from the YAML without a YAML library:
    the entries are `- name:` lines followed by their keys."""
    out, cur, in_main = [], None, False
    for line in hugo_text.splitlines():
        if re.match(r"^\s*main:\s*$", line):
            in_main = True
            continue
        if in_main and re.match(r"^\S", line):
            break
        if not in_main:
            continue
        m = re.match(r"^\s*-\s*name:\s*(.+?)\s*$", line)
        if m:
            cur = [m.group(1).strip("'\""), None]
            out.append(cur)
            continue
        m = re.match(r"^\s*weight:\s*([\d.]+)\s*$", line)
        if m and cur is not None and cur[1] is None:
            cur[1] = float(m.group(1))
    return [(n, w if w is not None else 0.0) for n, w in out]


def page(content, name):
    for p in (content / f"{name}.md", content / name / "_index.md"):
        if p.exists():
            return p
    return None


def check(hugo, content, static):
    hugo, content, static = pathlib.Path(hugo), pathlib.Path(content), pathlib.Path(static)
    out = []
    text = hugo.read_text()
    paths = re.findall(r"(?m)^\s*-\s*path:\s*(\S+)", text)
    if MODULE not in paths:
        out.append(Violation("SK-MODULE", f"{hugo} does not import {MODULE}"))
    elif "github.com/imfing/hextra" in paths and paths.index(MODULE) > paths.index("github.com/imfing/hextra"):
        out.append(Violation("SK-MODULE", f"{MODULE} must be imported before Hextra, or Hextra's badge and hooks win"))
    items = sorted(menu(text), key=lambda x: x[1])
    names = [n for n, _ in items]
    tail = [n for n in names if n in TAIL]
    if tail != [n for n in TAIL if n in tail]:
        out.append(Violation("SK-MENU-ORDER", f"menu order {tail}, expected {[n for n in TAIL if n in tail]}"))
    first_tail = min((names.index(n) for n in tail), default=len(names))
    if any(n not in TAIL for n in names[first_tail:]):
        out.append(Violation("SK-MENU-ORDER", f"a project registry comes after {names[first_tail]}: {names}"))
    home = content / "_index.md"
    h = home.read_text() if home.exists() else ""
    stamp = re.search(r'class="data-stamp"[^\n]*', h)
    if not stamp or "commit" not in stamp.group(0):
        out.append(Violation("SK-HOME-STAMP", "the home page has no data stamp naming its commit (class data-stamp)"))
    if not re.search(r"non-commercial", h, re.I):
        out.append(Violation("SK-HOME-DISCLAIMER", "the home page has no disclaimer naming the project non-commercial"))
    if not re.search(r"\bAI\b", h):
        out.append(Violation("SK-HOME-PROVENANCE", "the home page does not say what an AI assistant did"))
    if not re.search(r"(?m)^## Cite\b", h):
        out.append(Violation("SK-HOME-CITE", "the home page has no '## Cite' section"))
    for rule, name in REQUIRED_PAGES.items():
        if page(content, name) is None:
            out.append(Violation(rule, f"no {name} page"))
    for f in ("llms.txt", "llms-full.txt"):
        if not (static / f).exists():
            out.append(Violation("SK-LLMS", f"no {f} in {static}"))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--hugo", required=True)
    ap.add_argument("--content", required=True)
    ap.add_argument("--static", required=True)
    a = ap.parse_args()
    bad = check(a.hugo, a.content, a.static)
    for v in bad:
        print(f"{v.rule}: {v.message}")
    print("site-kit: conforms to SPEC.md" if not bad else f"site-kit: {len(bad)} rule(s) fail")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
