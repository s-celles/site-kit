#!/usr/bin/env python3
"""Check a built site against the site-kit SPEC.

    python3 -I check_site.py --site public [--config site-kit.json] [--hugo hugo.yaml] [--repo .]

The rules are checked on the built HTML, so they hold whatever generator
produced it (Hugo, Documenter, another). --config is the site's
site-kit.json (menu, omitted pages, volatile patterns); --hugo a Hugo
configuration, for the menu and the module order; --repo the repository,
for CITATION.cff and docs/disclosures.tsv. Each rule has the identifier and the level SPEC.md gives
it. Exit status 1 if a MUST rule fails (SHOULD rules are warnings), 2 if
there is no built site.
"""
import argparse
import json
import pathlib
import re
import sys
from collections import namedtuple
from html.parser import HTMLParser

SPEC_VERSION = "0.3"
Violation = namedtuple("Violation", "rule level message")

RULES = {
    "SK-HOME-STAMP": "MUST", "SK-HOME-DISCLAIMER": "MUST", "SK-HOME-PROVENANCE": "MUST",
    "SK-HOME-CITE": "MUST", "SK-CITATION": "SHOULD",
    "SK-PAGE-STATUSES": "MUST", "SK-PAGE-METHODOLOGY": "MUST",
    "SK-PAGE-UPSTREAM": "SHOULD", "SK-PAGE-HISTORY": "SHOULD",
    "SK-LLMS": "MUST", "SK-BADGE-WORD": "MUST", "SK-BADGE-TONE": "MUST",
    "SK-CHART": "MUST", "SK-MERMAID": "MUST", "SK-MENU-ORDER": "MUST", "SK-MODULE": "MUST",
    "SK-SPEC": "SHOULD",
    "SK-PAGE-DISCLOSURE": "MUST", "SK-DISCLOSURES": "MUST", "SK-HOME-DISCLOSURE": "SHOULD",
}
PAGES = {"SK-PAGE-STATUSES": "statuses", "SK-PAGE-METHODOLOGY": "methodology",
         "SK-PAGE-UPSTREAM": "upstream", "SK-PAGE-HISTORY": "history",
         "SK-PAGE-DISCLOSURE": "conflict-of-interest"}
OMITTABLE = {"SK-PAGE-UPSTREAM", "SK-PAGE-HISTORY", "SK-PAGE-DISCLOSURE"}      # with a reason in site-kit.json
DISCLOSURE_PAGE = "conflict-of-interest"
DISCLOSURE_COLUMNS = ["contributor", "orcid", "project", "kind", "role", "note"]
DISCLOSURE_KINDS = {"examined system", "compared system", "tool", "benchmark", "AI assistance", "other"}  # and "source of NAME"
ORCID = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")
TAIL = ("Upstream", "History", "Methodology", "Disclosure", "Docs", "GitHub", "Search")   # SPEC.md §2
MENU_MAX = 9
MODULE = "github.com/s-celles/site-kit"
HEXTRA = "github.com/imfing/hextra"
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


# --- a small DOM, enough for class and attribute queries --------------------------------

class Node:
    def __init__(self, tag, attrs, parent=None):
        self.tag, self.attrs, self.parent, self.children = tag, dict(attrs), parent, []

    @property
    def classes(self):
        return (self.attrs.get("class") or "").split()

    def text(self):
        return "".join(c if isinstance(c, str) else c.text() for c in self.children)

    def iter(self):
        for c in self.children:
            if isinstance(c, Node):
                yield c
                yield from c.iter()

    def find(self, tag=None, cls=None):
        return [n for n in self.iter() if (tag is None or n.tag == tag) and (cls is None or cls in n.classes)]


class _Builder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#document", {})
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs, self.cur)
        self.cur.children.append(n)
        if tag not in VOID:
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        self.cur.children.append(Node(tag, attrs, self.cur))

    def handle_endtag(self, tag):
        n = self.cur
        while n is not None and n.tag != tag:
            n = n.parent
        if n is not None and n.parent is not None:     # an end tag without a start tag is ignored
            self.cur = n.parent

    def handle_data(self, data):
        self.cur.children.append(data)


def parse(text):
    b = _Builder()
    b.feed(text)
    b.close()
    return b.root


# --- configuration ---------------------------------------------------------------------

def hugo_menu(hugo_text):
    """[name] of menu.main in weight order, read from the YAML without a YAML
    library: the entries are `- name:` lines followed by their keys."""
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
    return [n for n, w in sorted(out, key=lambda x: x[1] if x[1] is not None else 0.0)]


def menu_problems(names):
    out = []
    if len(names) > MENU_MAX:
        out.append(f"{len(names)} menu entries, at most {MENU_MAX}: {names}")
    tail = [n for n in names if n in TAIL]
    if tail != [n for n in TAIL if n in tail]:
        out.append(f"menu order {tail}, expected {[n for n in TAIL if n in tail]}")
    first = min((names.index(n) for n in tail), default=len(names))
    if any(n not in TAIL for n in names[first:]):
        out.append(f"a registry comes after {names[first]}: {names}")
    return out


# --- mermaid ---------------------------------------------------------------------------

BAD_LABEL = re.compile(r"[;<#]")
SEQ_MESSAGE = re.compile(r"^\s*[^\s:]+\s*(?:-{1,2}(?:>>|>|x|\))[+-]?)\s*[^:]+:(.*)$")
NOTE = re.compile(r"^\s*note\s+(?:left of|right of|over)\s+[^:]+:(.*)$", re.I)
FLOW_LABELS = re.compile(r"\[([^\]]*)\]|\(([^)]*)\)|\{([^}]*)\}|\|([^|]*)\|")


def mermaid_labels(src):
    """The labels and messages of a Mermaid diagram, where ;, < and # break
    the rendering. Statement separators, comments, style lines are not labels."""
    lines = [l for l in src.splitlines() if not l.strip().startswith("%%")]
    kind = next((l.split()[0] for l in lines if l.strip()), "")
    out = []
    for line in lines[1:]:
        s = line.strip()
        if re.match(r"^(classDef|class|style|linkStyle|click)\b", s):
            continue
        m = NOTE.match(s) or (SEQ_MESSAGE.match(s) if kind.startswith("sequenceDiagram") else None)
        if m:
            out.append(m.group(1))
            continue
        if kind.split(";")[0] in ("flowchart", "graph"):
            out += [next(g for g in m.groups() if g is not None) for m in FLOW_LABELS.finditer(s)]
    return out


# --- the check -------------------------------------------------------------------------

def find_page(site, name):
    """A page NAME: NAME/index.html (pretty URLs) or NAME.html, at any depth."""
    for p in sorted(site.rglob("index.html")):
        if p.parent.name == name:
            return p
    return next(iter(sorted(site.rglob(f"{name}.html"))), None)


def disclosure_problems(text):
    """What is wrong with a docs/disclosures.tsv text (SPEC §15), as messages."""
    lines = [l for l in text.splitlines() if l.strip() and not l.startswith("#")]
    if not lines or lines[0].split("\t") != DISCLOSURE_COLUMNS:
        return [f"the header is not {' '.join(DISCLOSURE_COLUMNS)}"]
    out, people, with_ai = [], set(), set()
    for n, line in enumerate(lines[1:], 2):
        f = line.split("\t")
        if len(f) != len(DISCLOSURE_COLUMNS):
            out.append(f"row {n}: {len(f)} columns")
            continue
        who, orcid, project, kind, role, _ = f
        if not who or not project or not role:
            out.append(f"row {n}: contributor, project and role are required")
        if not ORCID.match(orcid):
            out.append(f"row {n}: invalid ORCID {orcid!r}")
        if kind not in DISCLOSURE_KINDS and not (kind.startswith("source of ") and len(kind) > len("source of ")):
            out.append(f"row {n}: unknown kind {kind!r}")
        people.add(who)
        if kind == "AI assistance":
            with_ai.add(who)
    if len(lines) == 1:
        out.append("no declaration")
    out += [f"{who} has no AI assistance row" for who in sorted(people - with_ai)]
    return out


def check(site, config=None, hugo=None, repo=None):
    site = pathlib.Path(site)
    cfg = json.loads(pathlib.Path(config).read_text()) if config else {}
    out = []

    def fail(rule, message):
        out.append(Violation(rule, RULES[rule], message))

    if cfg.get("spec") and cfg["spec"] != SPEC_VERSION:
        fail("SK-SPEC", f"site-kit.json names SPEC {cfg['spec']}, this checker is {SPEC_VERSION}")

    # home page
    home_file = site / "index.html"
    home = parse(home_file.read_text(errors="replace")) if home_file.exists() else Node("#document", {})
    stamps = home.find(cls="data-stamp")
    if not any(re.search(r"\b[0-9a-f]{7,40}\b|\b\d{4}-\d{2}-\d{2}\b", n.text()) for n in stamps):
        fail("SK-HOME-STAMP", "the home page has no .data-stamp naming a commit or a date")
    disclaimer = " ".join(n.text() for n in home.find(cls="disclaimer"))
    if not re.search(r"non[-‐‑]commercial", disclaimer, re.I):
        fail("SK-HOME-DISCLAIMER", "the home page's .disclaimer does not call the project non-commercial")
    if not re.search(r"\bAI\b", disclaimer):
        fail("SK-HOME-PROVENANCE", "the home page's .disclaimer does not say what an AI assistant did")
    if not any(n.tag in ("h1", "h2", "h3", "h4", "h5", "h6") and n.text().strip().startswith("Cite") for n in home.iter()):
        fail("SK-HOME-CITE", "the home page has no heading 'Cite'")
    if repo is not None and not (pathlib.Path(repo) / "CITATION.cff").exists():
        fail("SK-CITATION", f"no CITATION.cff in {repo}")
    omit = cfg.get("omit", {})
    disclosure_omitted = bool(str(omit.get(DISCLOSURE_PAGE, "")).strip())
    if not disclosure_omitted:
        if not any(re.search(rf"/{DISCLOSURE_PAGE}(/|\.html)?(#.*)?$", n.attrs.get("href") or "") for n in home.iter() if n.tag == "a"):
            fail("SK-HOME-DISCLOSURE", "the home page does not link to the conflict of interest page")
        if repo is not None:
            tsv = pathlib.Path(repo) / "docs" / "disclosures.tsv"
            if not tsv.exists():
                fail("SK-DISCLOSURES", f"no docs/disclosures.tsv in {repo}")
            else:
                for problem in disclosure_problems(tsv.read_text()):
                    fail("SK-DISCLOSURES", f"docs/disclosures.tsv: {problem}")

    # pages
    for rule, name in PAGES.items():
        if find_page(site, name) is None:
            if rule in OMITTABLE and str(omit.get(name, "")).strip():
                continue
            fail(rule, f"no {name} page" + (" (an omission in site-kit.json needs a reason)" if name in omit else ""))
    if not (site / "llms.txt").exists():
        fail("SK-LLMS", "no llms.txt at the site root")
    if not (site / "llms-full.txt").exists() and not list(site.glob("llms-full-*.txt")):
        fail("SK-LLMS", "no llms-full.txt (or llms-full-NAME.txt parts) at the site root")

    # markup, on every page
    tones = {}
    for f in sorted(site.rglob("*.html")):
        rel = f.relative_to(site).as_posix()
        doc = home if f == home_file else parse(f.read_text(errors="replace"))
        for b in doc.find(cls="sk-badge"):
            word = (b.attrs.get("data-status") or "").strip()
            if not b.text().strip():
                fail("SK-BADGE-WORD", f"{rel}: a badge without a label (data-status={word!r})")
            tone = next((c[len("sk-tone--"):] for c in b.classes if c.startswith("sk-tone--")), None)
            if word and tone:
                tones.setdefault(word.lower(), {}).setdefault(tone, rel)
        charts = doc.find("svg", "viz-chart")
        if charts and not doc.find("table"):
            fail("SK-CHART", f"{rel}: {len(charts)} chart(s) and no table of their values")
        for c in charts:
            if not (c.attrs.get("aria-label") or "").strip():
                fail("SK-CHART", f"{rel}: a chart without an aria-label")
            if any(not (p.attrs.get("aria-label") or "").strip() for p in c.find("g", "viz-pt")):
                fail("SK-CHART", f"{rel}: a chart point (g.viz-pt) without an aria-label")
        for m in doc.find(cls="mermaid"):
            for label in mermaid_labels(m.text()):
                if BAD_LABEL.search(label):
                    fail("SK-MERMAID", f"{rel}: Mermaid label {label.strip()!r} contains ; < or #")
    for word, ts in sorted(tones.items()):
        if len(ts) > 1:
            fail("SK-BADGE-TONE", f"the word {word!r} has tones " + ", ".join(f"{t} ({p})" for t, p in sorted(ts.items())))

    # configuration
    hugo_text = pathlib.Path(hugo).read_text() if hugo else ""
    names = cfg.get("menu") or (hugo_menu(hugo_text) if hugo else [])
    for problem in menu_problems(names):
        fail("SK-MENU-ORDER", problem)
    if hugo:
        paths = re.findall(r"(?m)^\s*-\s*path:\s*(\S+)", hugo_text)
        if MODULE not in paths:
            fail("SK-MODULE", f"{hugo} does not import {MODULE}")
        elif HEXTRA in paths and paths.index(MODULE) > paths.index(HEXTRA):
            fail("SK-MODULE", f"{MODULE} must be imported before Hextra, or Hextra's badge and hooks win")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--site", required=True, help="the built site (Hugo's public/, Documenter's build/)")
    ap.add_argument("--config", help="the site's site-kit.json")
    ap.add_argument("--hugo", help="a Hugo configuration (menu, module order)")
    ap.add_argument("--repo", help="the repository root (CITATION.cff)")
    a = ap.parse_args(argv)
    if not pathlib.Path(a.site).is_dir():
        print(f"site-kit: no built site at {a.site}")
        return 2
    vs = check(a.site, a.config, a.hugo, a.repo)
    print(f"site-kit: checking {a.site} against SPEC {SPEC_VERSION}")
    for v in vs:
        print(f"{v.level} {v.rule}: {v.message}")
    must = [v for v in vs if v.level == "MUST"]
    print("site-kit: conforms" if not vs else f"site-kit: {len(must)} MUST and {len(vs) - len(must)} SHOULD rule(s) fail")
    return 1 if must else 0


if __name__ == "__main__":
    sys.exit(main())
