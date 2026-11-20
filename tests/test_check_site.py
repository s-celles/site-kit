#!/usr/bin/env python3
"""Checks for tools/check_site.py. Run with python3 -I tests/test_check_site.py."""
import json
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
    - name: Disclosure
      pageRef: /conflict-of-interest
      weight: 4.5
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

HOME = """<!doctype html><html><head><title>X</title><meta charset="utf-8"></head><body>
<main><p>X is a registry of findings.</p>
<p class="data-stamp">Data at commit <a href="u"><code>abc1234</code></a> (2026-11-19).</p>
<div class="disclaimer">
<p><strong>Disclaimer.</strong> An individual, non-commercial project, not endorsed by anyone.</p>
<p><strong>Provenance.</strong> Written with an AI assistant; a person decides what is reported.</p>
</div>
<p>The author maintains one of the systems compared. <a href="/conflict-of-interest/">Conflict of interest</a></p>
<div class="sk-stats"><a class="sk-stat" href="/f"><strong>2</strong><span>findings</span></a></div>
<p><span class="sk-badge sk-tone--good" data-status="PASS">PASS</span></p>
<h2 id="cite">Cite<a class="subheading-anchor" href="#cite"></a></h2>
<blockquote><p>A. Author. <em>X</em>. Version 1.</p></blockquote>
</main></body></html>
"""

PAGE = "<!doctype html><html><body><main><h1>{name}</h1><p>body<br>text</p>{extra}</main></body></html>"

CHART = ('<figure class="viz"><svg class="viz-chart" viewBox="0 0 10 10" role="img" aria-label="tests over time">'
         '<g class="viz-pt" tabindex="0" aria-label="pass: 3, 2026-11-19"><circle class="viz-dot" cx="1" cy="1" r="4"/></g>'
         '</svg></figure>')
TABLE = "<table><tr><th>date</th><th>pass</th></tr><tr><td>2026-11-19</td><td>3</td></tr></table>"
MERMAID = '<pre class="mermaid">flowchart LR\n  A["inputs"] --> B["results"]\n  B -->|published| C(site)\n</pre>'


DISCLOSURES = ("# a comment\ncontributor\torcid\tproject\tkind\trole\tnote\n"
               "A. Author\t0000-0001-2345-6789\tSystem X\tcompared system\tmaintainer\t\n"
               "A. Author\t0000-0001-2345-6789\tSystem Y\tcompared system\tnone\t\n"
               "A. Author\t0000-0001-2345-6789\tan AI assistant\tAI assistance\twrote the harness\treviewed by the author\n")
REPO = {"CITATION.cff": "cff-version: 1.2.0\n", "docs/disclosures.tsv": DISCLOSURES}


def build(tmp, home=HOME, pages=None, files=("llms.txt", "llms-full.txt"), config=None, hugo=None, repo_files=REPO):
    """A built site in tmp/public, and the paths check() takes."""
    root = pathlib.Path(tmp)
    pub = root / "public"
    pub.mkdir(parents=True)
    (pub / "index.html").write_text(home)
    if pages is None:
        pages = {"findings": "", "upstream": "", "history": CHART + TABLE, "methodology": MERMAID, "statuses": "",
                 "conflict-of-interest": ""}
    for name, extra in pages.items():
        (pub / name).mkdir(parents=True, exist_ok=True)
        (pub / name / "index.html").write_text(PAGE.format(name=name, extra=extra))
    for f in files:
        (pub / f).write_text("x")
    repo = root / "repo"
    repo.mkdir()
    for f, text in dict(repo_files).items():
        (repo / f).parent.mkdir(parents=True, exist_ok=True)
        (repo / f).write_text(text)
    kw = {"site": pub, "repo": repo}
    if config is not None:
        (root / "site-kit.json").write_text(json.dumps(config))
        kw["config"] = root / "site-kit.json"
    if hugo is not None:
        (root / "hugo.yaml").write_text(hugo)
        kw["hugo"] = root / "hugo.yaml"
    return kw


def rules(vs, level=None):
    return {v.rule for v in vs if level is None or v.level == level}


class ConformingSite(unittest.TestCase):
    def test_a_conforming_site_passes(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(check_site.check(**build(t, hugo=HUGO)), [])

    def test_every_rule_has_a_level(self):
        for rule, level in check_site.RULES.items():
            self.assertIn(level, ("MUST", "SHOULD"), rule)

    def test_documenter_style_pages_count(self):
        # Documenter without pretty URLs writes NAME.html, possibly in a subdirectory
        with tempfile.TemporaryDirectory() as t:
            kw = build(t, pages={})
            for name, extra in {"statuses": "", "methodology": "", "upstream": "", "reference/history": "",
                                "conflict-of-interest": ""}.items():
                p = kw["site"] / f"{name}.html"
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(PAGE.format(name=name, extra=extra))
            self.assertEqual(rules(check_site.check(**kw)), set())


class HomeRules(unittest.TestCase):
    def failing(self, **kw):
        with tempfile.TemporaryDirectory() as t:
            return rules(check_site.check(**build(t, **kw)))

    def test_stamp(self):
        self.assertIn("SK-HOME-STAMP", self.failing(home=HOME.replace('class="data-stamp"', 'class="note"')))
        self.assertIn("SK-HOME-STAMP", self.failing(home=HOME.replace("abc1234", "HEAD").replace("(2026-11-19)", "")))
        # a dated record instead of a commit
        self.assertNotIn("SK-HOME-STAMP", self.failing(home=HOME.replace("abc1234", "run").replace("(2026-11-19)", "of 2026-11-02")))

    def test_disclaimer_words_must_be_inside_the_disclaimer(self):
        outside = HOME.replace('<div class="disclaimer">', '<div>') + '<div class="disclaimer"><p>x</p></div>'
        got = self.failing(home=outside)
        self.assertIn("SK-HOME-DISCLAIMER", got)
        self.assertIn("SK-HOME-PROVENANCE", got)
        self.assertIn("SK-HOME-DISCLAIMER", self.failing(home=HOME.replace("non-commercial", "commercial")))
        self.assertIn("SK-HOME-PROVENANCE", self.failing(home=HOME.replace("an AI assistant", "a team")))

    def test_cite_heading(self):
        self.assertIn("SK-HOME-CITE", self.failing(home=HOME.replace(">Cite<", ">Notes<")))

    def test_citation_file_is_a_warning(self):
        with tempfile.TemporaryDirectory() as t:
            vs = check_site.check(**build(t, repo_files={"docs/disclosures.tsv": DISCLOSURES}))
            self.assertEqual(rules(vs), {"SK-CITATION"})
            self.assertEqual(rules(vs, "SHOULD"), {"SK-CITATION"})


class PageRules(unittest.TestCase):
    def test_required_and_recommended_pages(self):
        with tempfile.TemporaryDirectory() as t:
            vs = check_site.check(**build(t, pages={"findings": ""}))
            self.assertEqual(rules(vs, "MUST"), {"SK-PAGE-STATUSES", "SK-PAGE-METHODOLOGY", "SK-PAGE-DISCLOSURE"})
            self.assertEqual(rules(vs, "SHOULD"), {"SK-PAGE-UPSTREAM", "SK-PAGE-HISTORY"})

    def test_a_declared_omission_silences_the_warning(self):
        cfg = {"spec": "0.3", "omit": {"upstream": "three issues, listed on Methodology", "history": "a single run",
                                       "conflict-of-interest": "the project examines no third-party system"}}
        with tempfile.TemporaryDirectory() as t:
            vs = check_site.check(**build(t, pages={"statuses": "", "methodology": ""}, config=cfg))
            self.assertEqual(rules(vs), set())

    def test_an_omission_needs_a_reason(self):
        with tempfile.TemporaryDirectory() as t:
            vs = check_site.check(**build(t, pages={"statuses": "", "methodology": "", "history": ""}, config={"omit": {"upstream": ""}}))
            self.assertIn("SK-PAGE-UPSTREAM", rules(vs))

    def test_llms(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertIn("SK-LLMS", rules(check_site.check(**build(t, files=("llms.txt",)))))
        with tempfile.TemporaryDirectory() as t:   # split per registry
            self.assertNotIn("SK-LLMS", rules(check_site.check(**build(t, files=("llms.txt", "llms-full-findings.txt")))))


class MarkupRules(unittest.TestCase):
    def failing(self, extra, where="findings"):
        pages = {"findings": "", "upstream": "", "history": "", "methodology": "", "statuses": ""}
        pages[where] = extra
        with tempfile.TemporaryDirectory() as t:
            return rules(check_site.check(**build(t, pages=pages)))

    def test_badge_shows_a_word(self):
        self.assertIn("SK-BADGE-WORD", self.failing('<span class="sk-badge sk-tone--bad" data-status="FAIL"> </span>'))

    def test_one_tone_per_word_across_the_site(self):
        self.assertIn("SK-BADGE-TONE", self.failing('<span class="sk-badge sk-tone--warn" data-status="pass">pass</span>'))
        self.assertNotIn("SK-BADGE-TONE", self.failing('<span class="sk-badge sk-tone--good sk-badge--result" data-status="PASS">Pass</span>'))

    def test_chart_needs_a_label_and_a_table(self):
        self.assertIn("SK-CHART", self.failing(CHART))                                   # no table on its page
        self.assertIn("SK-CHART", self.failing(CHART.replace(' aria-label="tests over time"', "") + TABLE))
        self.assertIn("SK-CHART", self.failing(CHART.replace(' aria-label="pass: 3, 2026-11-19"', "") + TABLE))
        self.assertNotIn("SK-CHART", self.failing(CHART + TABLE))

    def test_mermaid_labels(self):
        for bad in ('A["a; b"] --> B', 'A["x &lt;br&gt; y"] --> B', 'A -->|step #2| B', 'A{"is it #1"} --> B'):
            with self.subTest(bad=bad):
                self.assertIn("SK-MERMAID", self.failing(f'<pre class="mermaid">flowchart LR\n  {bad}\n</pre>', "methodology"))
        seq = '<pre class="mermaid">sequenceDiagram\n  A->>B: send x; y\n</pre>'
        self.assertIn("SK-MERMAID", self.failing(seq, "methodology"))
        fine = ('<pre class="mermaid">graph LR;\n  A["inputs"] --> B(results);\n  classDef k fill:#fee;\n'
                '  style B fill:#fff\n  %% a comment; with # signs\n</pre>')
        self.assertNotIn("SK-MERMAID", self.failing(fine, "methodology"))


class ConfigRules(unittest.TestCase):
    def test_menu_order_from_the_hugo_configuration(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertIn("SK-MENU-ORDER", rules(check_site.check(**build(t, hugo=HUGO.replace("weight: 3", "weight: 9")))))

    def test_menu_entries_may_be_absent_but_not_out_of_order(self):
        hugo = HUGO.replace("    - name: History\n      pageRef: /history\n      weight: 3\n", "")
        with tempfile.TemporaryDirectory() as t:
            self.assertNotIn("SK-MENU-ORDER", rules(check_site.check(**build(t, hugo=hugo))))

    def test_menu_from_site_kit_json(self):
        ok = ["Findings", "Properties", "Upstream", "History", "Methodology", "Disclosure", "Docs", "GitHub", "Search"]
        with tempfile.TemporaryDirectory() as t:
            self.assertNotIn("SK-MENU-ORDER", rules(check_site.check(**build(t, config={"menu": ok}))))
        for bad in (["Upstream", "Findings"], ok[:1] + ["Tests"] + ok[1:],            # registry after Upstream; 10 entries
                    ["Findings", "Disclosure", "Methodology"]):                      # Disclosure before Methodology
            with self.subTest(bad=bad), tempfile.TemporaryDirectory() as t:
                self.assertIn("SK-MENU-ORDER", rules(check_site.check(**build(t, config={"menu": bad}))))

    def test_module_order(self):
        no_module = HUGO.replace("    - path: github.com/s-celles/site-kit\n", "")
        late = HUGO.replace("    - path: github.com/s-celles/site-kit\n    - path: github.com/imfing/hextra\n",
                            "    - path: github.com/imfing/hextra\n    - path: github.com/s-celles/site-kit\n")
        for hugo in (no_module, late):
            with tempfile.TemporaryDirectory() as t:
                self.assertIn("SK-MODULE", rules(check_site.check(**build(t, hugo=hugo))))

    def test_spec_version_mismatch_is_reported(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertIn("SK-SPEC", rules(check_site.check(**build(t, config={"spec": "9.9"}))))


class DisclosureRules(unittest.TestCase):
    def failing(self, **kw):
        with tempfile.TemporaryDirectory() as t:
            return check_site.check(**build(t, **kw))

    def test_the_page_is_required_unless_omitted_with_a_reason(self):
        pages = {"findings": "", "upstream": "", "history": CHART + TABLE, "methodology": MERMAID, "statuses": ""}
        self.assertIn("SK-PAGE-DISCLOSURE", rules(self.failing(pages=pages), "MUST"))
        self.assertIn("SK-PAGE-DISCLOSURE", rules(self.failing(pages=pages, config={"omit": {"conflict-of-interest": " "}})))
        omitted = self.failing(pages=pages, config={"omit": {"conflict-of-interest": "examines no third-party system"}},
                               repo_files={"CITATION.cff": "cff-version: 1.2.0\n"}, home=HOME.replace('href="/conflict-of-interest/"', 'href="/x/"'))
        self.assertEqual(rules(omitted), set())

    def test_the_declarations_file(self):
        head = "contributor\torcid\tproject\tkind\trole\tnote\n"
        ai = "A\t0000-0001-2345-6789\tan AI assistant\tAI assistance\tx\ty\n"
        for name, text in {
            "missing": None,
            "header": "who\twhat\n" + ai,
            "kind": head + "A\t0000-0001-2345-6789\tX\tfriend\tnone\t\n" + ai,
            "no AI row": head + "A\t0000-0001-2345-6789\tX\tcompared system\tnone\t\n",
            "columns": head + "A\t0000-0001-2345-6789\tX\n" + ai,
            "orcid": head + "A\t12\tan AI assistant\tAI assistance\tx\ty\n",
            "no rows": head,
        }.items():
            with self.subTest(name=name):
                files = {"CITATION.cff": "cff-version: 1.2.0\n"}
                if text is not None:
                    files["docs/disclosures.tsv"] = text
                self.assertIn("SK-DISCLOSURES", rules(self.failing(repo_files=files), "MUST"))
        ok = head + "A\t0000-0001-2345-6789\tSystem X\tsource of bench H\tauthor\t\n" + "A\t0000-0001-2345-6789\tnone\tother\tnone\tno funding\n" + ai
        self.assertNotIn("SK-DISCLOSURES", rules(self.failing(repo_files={"CITATION.cff": "x", "docs/disclosures.tsv": ok})))

    def test_the_home_page_links_to_it(self):
        vs = self.failing(home=HOME.replace('href="/conflict-of-interest/"', 'href="/x/"'))
        self.assertEqual(rules(vs, "SHOULD"), {"SK-HOME-DISCLOSURE"})
        self.assertEqual(rules(vs, "MUST"), set())


class Main(unittest.TestCase):
    def test_exit_status_follows_must_rules(self):
        import contextlib
        import io
        with tempfile.TemporaryDirectory() as t:
            kw = build(t, repo_files={"docs/disclosures.tsv": DISCLOSURES})   # only a SHOULD fails
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = check_site.main(["--site", str(kw["site"]), "--repo", str(kw["repo"])])
            self.assertEqual(code, 0)
            self.assertIn(f"SPEC {check_site.SPEC_VERSION}", out.getvalue())
            self.assertIn("SHOULD SK-CITATION", out.getvalue())
        with tempfile.TemporaryDirectory() as t:
            kw = build(t, files=())
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(check_site.main(["--site", str(kw["site"])]), 1)
                self.assertEqual(check_site.main(["--site", str(kw["site"] / "missing")]), 2)


if __name__ == "__main__":
    unittest.main()
