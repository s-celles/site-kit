# site-kit specification, version 0.1

The project sites of s-celles (iec61131-conformance, go-in-lean,
julia-findings, computer_algebra_system_benchmarks) present findings,
results and their evidence. This specification is the structure they share.
A rule marked with an identifier (SK-...) is checked by
`tools/check_site.py`; the other rules are reviewed by hand.

"Registry" below means the project's main collection: findings, results,
tests, properties, benches.

## 1. Principles

- The site is generated from data committed in the repository, outside the
  repository (no generated page is committed), on every build.
- Two builds of the same commit produce the same files: no time stamp of the
  build, a stable order. A test of the generator renders twice and compares.
- A build needs no network beyond fetching the pinned Hugo modules. Data from
  elsewhere (upstream issue states, external history) comes from a dated
  snapshot that a script refreshes and that is committed.
- Every page that shows numbers says which commit they come from
  (SK-HOME-STAMP on the home page; recommended on every such page): a
  paragraph `<p class="data-stamp">Data at commit <code>abc1234</code> (date).</p>`.

## 2. Navigation

Menu `main`, in this order, entries that a site does not have being left out
(SK-MENU-ORDER):

1. the project's registries, in the order the project chooses (for example
   Results, Findings, Tests, Runtimes; or Findings, Properties);
2. Upstream;
3. History;
4. Methodology;
5. Docs;
6. GitHub;
7. Search.

The sidebar follows the same order (page weights).

The Hugo configuration imports `github.com/s-celles/site-kit` and then Hextra
(SK-MODULE). The order matters: the first import wins, and Hextra has its own
`badge` shortcode and empty `custom/` hooks.

## 3. Home page

In this order:

1. kicker (`<div class="sk-kicker">`), one bold sentence saying what the
   project is, a short paragraph;
2. the data stamp (SK-HOME-STAMP);
3. a `<div class="disclaimer">` with two paragraphs:
   - **Disclaimer**: an individual, non-commercial project, not produced,
     endorsed or certified by any standards body, vendor or the projects it
     examines, with its aim (SK-HOME-DISCLAIMER: the words "non-commercial");
   - **Provenance**: what an AI assistant wrote and what a person checked
     (SK-HOME-PROVENANCE: the word "AI");
4. four stat tiles (`{{< stats >}}{{< stat ... >}}{{< /stats >}}`) and links
   to the registry, Methodology and Statuses;
5. a short table of the current state (for example passed per runtime);
6. the newest entries (findings, upstream reports or runs);
7. `## Cite` with a citation from `CITATION.cff` (SK-HOME-CITE).

The footer of every page (site parameter `siteKit.footer`) repeats the
disclaimer in one sentence and names the licences.

## 4. Registry entries

Each entry has its own page with, in this order:

- a title with its identifier;
- a line: target (runtime, package, system), status badge, source file;
- upstream: each issue or pull request with its state from the snapshot,
  issue and fix shown separately where they differ;
- evidence: the reproducer (runnable as given), the raw output of every
  system, not only a verdict;
- related entries (tests citing a finding, findings citing a test);
- history of the entry's status, dated, when the project records it.

The registry index is one table, filterable and sortable in the browser
(`<div class="filterable">` around a Markdown table; `tables.js`), complete
without JavaScript.

## 5. Statuses

A page `statuses` defines every word a badge can carry (SK-PAGE-STATUSES):
results, entry statuses, upstream states. Badges come from the `badge`
shortcode; the site maps each word to a tone in `siteKit.badgeTones`
(good, bad, bad-dashed, warn, warn-dashed, info, alt, neutral). The word is
always shown, so no meaning rests on colour alone.

## 6. Upstream

A page `upstream` lists every upstream issue and pull request the project
cites, by repository, with kind, state, opened, closed and title, from the
snapshot (SK-PAGE-UPSTREAM). It says that a closed issue does not prove that
a fix reached a release.

## 7. History

A page `history` charts the project over time (SK-PAGE-HISTORY): the size of
the registry, its results, the upstream reports. Time is on the x axis. One y
axis per chart, starting at 0. More than three series become small
multiples on one scale. Every point has a tooltip that the keyboard reaches
(`viz.js`: `g.viz-pt` with `tabindex="0"` and an `aria-label`). A table under
the charts gives every value. The data come from the git history at build
time (checkout with `fetch-depth: 0`) or from a committed file with one row
per run.

## 8. Methodology

A page `methodology` (SK-PAGE-METHODOLOGY) shows the pipeline from inputs to
published results as a diagram, says what a result does and does not mean,
and lists the checks of the expected values. Mermaid diagrams keep
semicolons, angle brackets and hashes out of node labels.

## 9. Machine-readable output and citation

- `llms.txt` and `llms-full.txt` at the site root (SK-LLMS): the pitch, the
  disclaimer and provenance, the pages, and the full registry as text.
- `CITATION.cff` in the repository; its citation on the home page.
- The licences of code and of data, and the terms of third-party sources,
  are named in the footer and the README.

## 10. Build

- Hugo Extended at the version of `hugo-version`, installed with a checksum
  (`scripts/install_hugo.sh`), theme Hextra and this module as Hugo modules.
- The generator writes `content/` and `static/` outside the repository;
  `build.sh OUT [HUGO]` runs it, Hugo, then copies `static/`.
- CI: the generator's tests, `check_site.py`, the build; deploy `main` with
  `actions/configure-pages` (base URL from Pages) and `actions/deploy-pages`.
- Accessibility: badges carry words, charts have an aria-label, a tooltip
  reachable from the keyboard and a table view; light and dark palettes are
  validated for colour-vision deficiency.
