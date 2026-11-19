#!/usr/bin/env python3
"""Refresh the upstream snapshot of a site (SPEC.md §6) from GitHub.

    python3 -I upstream_status.py OUT.tsv --scan FILE...     # cited_by = each file's stem
    python3 -I upstream_status.py OUT.tsv --refs refs.txt    # lines "owner/repo#N [cited_by ...]"

References are GitHub issue and pull request URLs and owner/repo#N short
forms (owner/file.md#N anchors are not references). Each is fetched with
`gh api` when gh is installed, otherwise from the REST API with the token in
GITHUB_TOKEN if set. A reference that cannot be fetched keeps its row from
the previous snapshot. The TSV columns are COLUMNS; the build reads only
this file, never the network.
"""
import argparse
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import urllib.request

COLUMNS = ("repo", "number", "kind", "state", "created", "closed", "merged", "fixes", "cited_by", "title")
NAME = r"[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?"
DOC_EXT = (".md", ".markdown", ".txt", ".html", ".htm", ".rst", ".adoc")
REF = re.compile(rf"https://github\.com/({NAME}/[\w.-]+)/(?:issues|pull)/(\d+)"
                 rf"|(?<![\w./-])({NAME}/[\w.-]+)#(\d+)\b")
FIXES = re.compile(r"(?i)\b(?:fix(?:e[sd])?|close[sd]?|resolve[sd]?)\s*:?\s+((?:[\w.-]+/[\w.-]+)?#\d+)")


def references(text):
    """[(repo, number)] in the order they appear, without duplicates."""
    out = []
    for m in REF.finditer(text):
        repo, num = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4))
        if repo.lower().endswith(DOC_EXT):
            continue
        ref = (repo, int(num))
        if ref not in out:
            out.append(ref)
    return out


def scan(paths):
    refs = {}
    for p in paths:
        p = pathlib.Path(p)
        for ref in references(p.read_text(errors="replace")):
            refs.setdefault(ref, set()).add(p.stem)
    return refs


def read_refs(path):
    refs = {}
    for line in pathlib.Path(path).read_text().splitlines():
        parts = line.split()
        if not parts or parts[0].startswith("#"):
            continue
        repo, num = parts[0].rsplit("#", 1)
        refs.setdefault((repo, int(num)), set()).update(parts[1:])
    return refs


def _day(ts):
    return (ts or "")[:10]


def _clean(s):
    return re.sub(r"[\t\r\n]+", " ", s or "").strip()


def row(repo, issue, pull, cited_by):
    """A snapshot row from the issues endpoint's JSON and, for a pull
    request, the pulls endpoint's JSON."""
    is_pr = "pull_request" in issue
    state = issue.get("state", "")
    if state == "closed" and issue.get("state_reason") == "not_planned":
        state = "not planned"
    merged = _day((pull or {}).get("merged_at")) if is_pr else ""
    if is_pr and merged:
        state = "merged"
    fixes = []
    if is_pr:
        for ref in FIXES.findall(issue.get("body") or ""):
            ref = ref if not ref.startswith("#") else f"{repo}{ref}"
            if ref not in fixes:
                fixes.append(ref)
    return {"repo": repo, "number": str(issue.get("number", "")), "kind": "pr" if is_pr else "issue",
            "state": state, "created": _day(issue.get("created_at")), "closed": _day(issue.get("closed_at")),
            "merged": merged, "fixes": " ".join(fixes), "cited_by": " ".join(sorted(cited_by)),
            "title": _clean(issue.get("title"))}


def write_tsv(path, rows):
    lines = ["\t".join(COLUMNS)] + ["\t".join(_clean(str(r.get(c, ""))) for c in COLUMNS) for r in rows]
    pathlib.Path(path).write_text("\n".join(lines) + "\n")


def read_tsv(path):
    path = pathlib.Path(path)
    if not path.exists():
        return {}
    lines = path.read_text().splitlines()
    head = lines[0].split("\t")
    out = {}
    for line in lines[1:]:
        r = dict(zip(head, line.split("\t")))
        out[(r["repo"], int(r["number"]))] = r
    return out


def refresh(refs, fetch, old):
    """(rows sorted by repository and number, references that failed)."""
    rows, failed = [], []
    for (repo, num) in sorted(refs, key=lambda r: (r[0].lower(), r[1])):
        try:
            issue, pull = fetch(repo, num)
            rows.append(row(repo, issue, pull, refs[(repo, num)]))
        except (OSError, ValueError, KeyError, subprocess.CalledProcessError):
            failed.append((repo, num))
            prev = dict(old.get((repo, num)) or {"repo": repo, "number": str(num), "state": "unknown"})
            prev["cited_by"] = " ".join(sorted(refs[(repo, num)]))
            rows.append(prev)
    return rows, failed


def github_fetch(repo, num):
    def get(path):
        if shutil.which("gh"):
            return json.loads(subprocess.run(["gh", "api", path], check=True, capture_output=True, text=True).stdout)
        req = urllib.request.Request(f"https://api.github.com/{path}", headers={"Accept": "application/vnd.github+json"})
        if os.environ.get("GITHUB_TOKEN"):
            req.add_header("Authorization", f"Bearer {os.environ['GITHUB_TOKEN']}")
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    issue = get(f"repos/{repo}/issues/{num}")
    pull = get(f"repos/{repo}/pulls/{num}") if "pull_request" in issue else None
    return issue, pull


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("out")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--scan", nargs="+", metavar="FILE")
    g.add_argument("--refs", metavar="FILE")
    a = ap.parse_args(argv)
    refs = scan(a.scan) if a.scan else read_refs(a.refs)
    rows, failed = refresh(refs, github_fetch, read_tsv(a.out))
    write_tsv(a.out, rows)
    for repo, num in failed:
        print(f"kept the previous row of {repo}#{num}: it could not be fetched", file=sys.stderr)
    print(f"{a.out}: {len(rows)} references")
    return 0


if __name__ == "__main__":
    sys.exit(main())
