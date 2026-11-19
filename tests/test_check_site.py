#!/usr/bin/env python3
"""Checks for tools/check_site.py. Run with python3 -I tests/test_check_site.py."""
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools"))
import check_site

HUGO = """module:
  imports:
    - path: github.com/s-celles/site-kit
    - path: github.com/imfing/hextra
menu:
  main:
    - name: Findings
      pageRef: /findings
      weight: 1
    - name: Upstream
      pageRef: /upstream
      weight: 2
    - name: History
      pageRef: /history
      weight: 3
    - name: Methodology
      pageRef: /methodology
      weight: 4
    - name: Docs
      pageRef: /docs
      weight: 5
    - name: GitHub
      url: https://github.com/x/y
      weight: 6
    - name: Search
      weight: 7
      params:
        type: search
"""
HOME = """---
title: "X"
---

<p class="data-stamp">Data at commit <a href="u"><code>abc1234</code></a> (2026-11-19).</p>

<div class="disclaimer">

**Disclaimer.** An individual, non-commercial project, not endorsed by anyone.

**Provenance.** Written with an AI assistant.

</div>

## Cite

> A. Author. *X*. Version 1.
"""


def site(tmp, hugo=HUGO, home=HOME, pages=("findings/_index.md", "upstream.md", "history.md", "methodology.md", "statuses.md"),
         static=("llms.txt", "llms-full.txt")):
    root = pathlib.Path(tmp)
    (root / "site").mkdir(parents=True)
    (root / "site/hugo.yaml").write_text(hugo)
    c = root / "content"
    c.mkdir()
    (c / "_index.md").write_text(home)
    for p in pages:
        (c / p).parent.mkdir(parents=True, exist_ok=True)
        (c / p).write_text("---\ntitle: p\n---\n\nbody\n")
    (root / "static").mkdir()
    for s in static:
        (root / "static" / s).write_text("x")
    return root / "site/hugo.yaml", c, root / "static"


class CheckSite(unittest.TestCase):
    def test_a_conforming_site_passes(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(check_site.check(*site(t)), [])

    def test_each_rule(self):
        cases = {
            "SK-MENU-ORDER": dict(hugo=HUGO.replace("weight: 3", "weight: 9")),
            "SK-MODULE": dict(hugo=HUGO.replace("    - path: github.com/s-celles/site-kit\n", "")),
            "SK-MODULE ": dict(hugo=HUGO.replace("    - path: github.com/s-celles/site-kit\n    - path: github.com/imfing/hextra\n",
                                                  "    - path: github.com/imfing/hextra\n    - path: github.com/s-celles/site-kit\n")),
            "SK-HOME-STAMP": dict(home=HOME.replace("Data at commit", "Built from")),
            "SK-HOME-DISCLAIMER": dict(home=HOME.replace("non-commercial", "commercial")),
            "SK-HOME-PROVENANCE": dict(home=HOME.replace("AI assistant", "team")),
            "SK-HOME-CITE": dict(home=HOME.replace("## Cite", "## Notes")),
            "SK-PAGE-STATUSES": dict(pages=("findings/_index.md", "upstream.md", "history.md", "methodology.md")),
            "SK-LLMS": dict(static=("llms.txt",)),
        }
        for rule, kw in cases.items():
            with self.subTest(rule=rule), tempfile.TemporaryDirectory() as t:
                self.assertIn(rule.strip(), {v.rule for v in check_site.check(*site(t, **kw))})

    def test_menu_entries_may_be_absent_but_not_out_of_order(self):
        hugo = HUGO.replace("    - name: History\n      pageRef: /history\n      weight: 3\n", "")
        with tempfile.TemporaryDirectory() as t:
            self.assertNotIn("SK-MENU-ORDER", {v.rule for v in check_site.check(*site(t, hugo=hugo))})


if __name__ == "__main__":
    unittest.main()
