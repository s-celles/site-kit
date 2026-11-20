# site-kit specification, version 0.3

> **Status: proposed, 2026-11-20.** Adds the conflict of interest page and
> declarations (§15) and its place in the menu (§2), at the request of the
> owner of the four sites. SPEC 0.2 was agreed on 2026-11-19 by the agents of
> the four sites that use site-kit (README); this version waits for their
> answers (§14). The texts that commit the owner
> (disclaimer, provenance, licences, citation) are approved by the owner, not
> by the agents, site by site.

Sites that publish findings, results and their evidence share the structure
below, whatever their domain and whatever generator builds them (Hugo with
Hextra, Documenter, or another). The contract is stated on the **built
site**: its pages, their HTML markers and its files. The Hugo module of this
repository is one implementation of it. The CSS, the scripts, the snapshot
schema and the checks serve every generator.

A rule with an identifier (SK-...) is checked by `tools/check_site.py` on the
built HTML. **MUST** rules fail the check; **SHOULD** rules are warnings.
Section 13 lists them.

"Registry" means the project's main collection (findings, results, tests,
properties, benches). "Entry" means one item of it.

## 1. Principles

- The site is generated from data committed in the repository, on every
  build. No generated page is committed. The generator writes outside the
  repository, or into a directory that git ignores and that carries a guard
  marker (for example `.sitegen`), so that hand-written files are never
  replaced.
- Two builds of the same commit produce the same files (SK-DETERMINISM,
  checked by `tools/compare_builds.py`): no build time stamp, a stable order.
  A generator that writes a volatile line it cannot suppress (Documenter's
  "generated with ... on DATE" footer note) declares that line's pattern in
  `site-kit.json` (`volatile`, §13), and the comparison masks it. Only such
  generator lines are declared; the site's own content is not masked.
- The build needs no network beyond fetching pinned dependencies. Data from
  elsewhere (upstream issue states, external measurements) comes from a
  committed snapshot with a documented schema and a refresh script.
- Numbers are dated. The data stamp (§3) names the commit the data come
  from, or the dated record the data carry (a run date). A number in prose
  carries its unit.
- No analytics, no tracking, no personal data beyond authorship.

## 2. Navigation

The main menu has at most 9 entries, in this order, entries a site does not
have being left out (SK-MENU-ORDER, checked when the menu is declared in
`site-kit.json` or in a Hugo configuration):

1. the project's registries, in the order the project chooses;
2. Upstream;
3. History;
4. Methodology;
5. Disclosure (the conflict of interest page, §15);
6. Docs;
7. GitHub;
8. Search.

Docs is the catch-all: contributing, agent policy, systems and environment,
how the site is built, changelog. These are sidebar pages, not menu entries.
The sidebar follows the menu's order.

## 3. Home page

MUST, in this order:

1. a one-sentence statement of what the project is (a hero may hold it);
2. the data stamp: an element with class `data-stamp` naming a commit (7 to
   40 hexadecimal digits) or a date (SK-HOME-STAMP);
3. an element with class `disclaimer` holding two paragraphs, from
   `TEMPLATES.md`:
   - **Disclaimer**: an individual, non-commercial project, not produced,
     endorsed or certified by the bodies and projects it examines, with its
     aim (SK-HOME-DISCLAIMER: the words "non-commercial" inside it);
   - **Provenance**: what an AI assistant wrote and what a person checked,
     and that a person decides what is reported upstream
     (SK-HOME-PROVENANCE: the word "AI" inside it);
4. at most four stat tiles, and links to the registry, Methodology and
   Statuses;
5. a heading "Cite" with a citation generated from `CITATION.cff`, not
   copied by hand (SK-HOME-CITE; SK-CITATION: the file exists).

SHOULD, for a site with a conflict of interest page (§15): its one-line
summary near the disclaimer, with a link to the page (SK-HOME-DISCLOSURE).

SHOULD: the newest entries, or the latest runs; a short table of the current
state. MUST for a site that reuses third-party material: a "Sources" section
naming each source, its licence and how it was used ("generated with",
"quoted from", "derived from"), apart from the site's own licences. SHOULD,
here or on Methodology: what is not reproduced (third-party numbers quoted
with caveats, systems not run and why).

A hero image is allowed. The stamp and the disclaimer come before the stat
tiles.

The footer of every page repeats, in one line, the disclaimer and the
licences (`TEMPLATES.md`).

## 4. Registry and entries

The registry index is one table, filterable and sortable in the browser
(`<div class="filterable">` around a table; `tables.js`) and complete without
JavaScript. A site SHOULD also publish the registry as JSON
(`registry.json`).

Each entry has its own page. Its fields:

- MUST: identifier and title; subject (what the entry is about: a system,
  package or component; an entry may have several subjects, each with its
  own status); status badge; the evidence as recorded: the reproducer,
  runnable as given, and its output or outputs, the raw outputs of the
  systems examined, or the counterexample or proof it rests on, never a
  verdict alone;
- when it applies: upstream issues and fixes with their states (§6), issue
  and fix shown separately; related entries; a dated history of the status;
  timings when the project measures them; the source file and line.

The order of the fields is a recommendation. An entry's metadata SHOULD be
machine-readable (YAML front matter or a YAML file per entry) rather than
parsed from prose.

## 5. Statuses

A page `statuses` defines every word a badge can carry: results, entry
statuses, upstream states (SK-PAGE-STATUSES). A badge always shows its word
(SK-BADGE-WORD). A word maps to exactly one tone across the site
(SK-BADGE-TONE). Tones: good, bad, bad-dashed, warn, warn-dashed, info, alt,
alt-dashed, neutral, neutral-dashed. The markup is
`<span class="sk-badge sk-tone--TONE" data-status="WORD">LABEL</span>`. The
label is the word or a display form of it (for example "Proved in model" for
`proved_in_model`); `data-status` keeps the raw word.

## 6. Upstream

When the project cites upstream issues, a page `upstream` lists them by
repository, with kind, state, dates and title, from the snapshot
(SK-PAGE-UPSTREAM, a warning; a site without upstream reports declares the
page omitted in `site-kit.json`, with its reason). The page says that a
closed issue does not prove that a fix reached a release.

The snapshot is a TSV with the columns `repo`, `number`, `kind` (`issue`,
`pr`, `cl`), `state` (GitHub: `open`, `closed`, `not planned`, `merged`;
Gerrit: `new`, `merged`, `abandoned`), `created`, `closed`, `merged`,
`fixes` (the issue a pull request or change fixes, `repo#number`),
`cited_by` (entry identifiers, space-separated) and `title`.
`tools/upstream_status.py` refreshes it for GitHub. A site may keep
hand-written notes next to the generated table.

## 7. History

A page `history` charts the project over time (SK-PAGE-HISTORY, a warning: a
young project may have a single run). The site declares where the data come
from: the git history at build time (`fetch-depth: 0` in CI) for what the
repository records, or a committed snapshot (JSON or TSV, schema documented
in the repository) for anything else.

Charts follow the markup contract of §11:

- time on the x axis, one y axis per chart, starting at 0; a logarithmic
  axis is allowed for quantities spanning orders of magnitude, with its base
  in the axis label;
- more than three series become small multiples on one scale;
- every chart has an `aria-label` and a table of its values on the page
  (SK-CHART);
- a tooltip reachable from the keyboard. A dense chart is one tab stop, and
  the arrow keys step through x with a tooltip listing every series at that
  x. A sparse chart may make each point a tab stop instead. The tooltip
  stays inside the chart's figure;
- the series palette is validated for colour-vision deficiency, in light and
  dark, against the surfaces of the site's theme. The kit's palette is
  validated; a site may use its own validated palette.

## 8. Methodology

A page `methodology` (SK-PAGE-METHODOLOGY) shows the pipeline from inputs to
published results as a diagram, says what a result does and does not mean,
lists the checks of the expected values, and names the site-kit tag the site
pins. Mermaid labels and messages contain no semicolon, angle bracket or
hash (SK-MERMAID): they break the rendering silently.

## 9. Machine-readable output

`llms.txt` and `llms-full.txt` at the site root (SK-LLMS): what the project
is, the disclaimer and provenance, the pages, and the registry as text. Above
about 2 MB, `llms-full.txt` is split per registry (`llms-full-NAME.txt`,
listed in `llms.txt`).

## 10. Wording, licences, citation

`TEMPLATES.md` gives the disclaimer, provenance and footer as texts with
slots (project, examined projects, aim, licences of code and data). Each
site's owner approves its final text. The provenance says concretely what an
AI assistant wrote and what a person checked, without naming the model. The
licence choice stays with each site; the footer and the README name it, and
the terms of third-party sources (§3).

## 11. Markup contract and implementations

The rules above hold on the HTML, whatever produced it:

| What | Markup |
|---|---|
| data stamp | `class="data-stamp"` |
| disclaimer and provenance | `class="disclaimer"` |
| stat tiles | `class="sk-stats"`, each `class="sk-stat"` |
| badge | `class="sk-badge sk-tone--TONE" data-status="WORD"` |
| filterable table | a table inside `class="filterable"` |
| chart | `svg.viz-chart` with `aria-label`, inside `class="viz"`; points `g.viz-pt` with `aria-label`; a chart that is one tab stop has `tabindex="0"` and `data-viz="dense"` |
| dense chart point | its `aria-label` starts with its x value (a date), so the tooltip that joins the labels at one x reads on its own; or the points carry `data-x-label`, shown once as the tooltip's first line |

Implementations in this repository:

- for every generator: `assets/css/site-kit/site-kit.css`,
  `assets/js/site-kit/tables.js` and `assets/js/site-kit/viz.js`,
  `tools/check_site.py`, `tools/compare_builds.py`,
  `tools/upstream_status.py`, `TEMPLATES.md`;
- for Hugo with Hextra: the module (shortcodes `badge`, `stats`, `stat`;
  hooks `custom/head-end.html` and `custom/footer.html`), imported before
  Hextra, since the first import wins and Hextra has its own `badge` and
  empty hooks (SK-MODULE, checked when a Hugo configuration is given). On
  migration, a site deletes or renames its own `badge` shortcode and its own
  `custom/head-end.html`, or calls `partial "site-kit/head.html"` from the
  latter. `scripts/install_hugo.sh` and `hugo-version` pin Hugo Extended.

Generators, registry schemas and page content stay with each site.

## 12. Accessibility

Badges carry words. Charts have an `aria-label`, a keyboard tooltip and a
table. Motion is reduced under `prefers-reduced-motion`. Under
`forced-colors`, badges keep a border and charts keep their lines. Light and
dark palettes are validated against the surfaces of the theme (Hextra:
`#ffffff` light, `#111111` dark).

## 13. Checks

`check_site.py --site BUILT_DIR [--config site-kit.json] [--hugo hugo.yaml]
[--repo DIR]` prints the SPEC version it checks and one line per failed rule,
with its level. It exits with 1 when a MUST rule fails. SK-DETERMINISM is
checked by `tools/compare_builds.py BUILD_A BUILD_B --config site-kit.json`
on two builds of one commit.

| Rule | Level | What it checks |
|---|---|---|
| SK-HOME-STAMP | MUST | home `.data-stamp` names a 7-40 hex commit or a YYYY-MM-DD date |
| SK-HOME-DISCLAIMER | MUST | home `.disclaimer` contains "non-commercial" |
| SK-HOME-PROVENANCE | MUST | home `.disclaimer` contains "AI" |
| SK-HOME-CITE | MUST | home has a heading "Cite" |
| SK-CITATION | SHOULD | `CITATION.cff` exists in the repository (`--repo`) |
| SK-PAGE-STATUSES | MUST | a `statuses` page |
| SK-PAGE-METHODOLOGY | MUST | a `methodology` page |
| SK-PAGE-UPSTREAM | SHOULD | an `upstream` page, unless declared omitted |
| SK-PAGE-HISTORY | SHOULD | a `history` page, unless declared omitted |
| SK-PAGE-DISCLOSURE | MUST | a `conflict-of-interest` page, unless declared omitted with a reason (§15) |
| SK-DISCLOSURES | MUST | `docs/disclosures.tsv` in the repository (`--repo`) has the §15 columns and kinds, and an AI assistance row for every contributor |
| SK-HOME-DISCLOSURE | SHOULD | the home page links to the `conflict-of-interest` page |
| SK-LLMS | MUST | `llms.txt`, and `llms-full.txt` or its `llms-full-NAME.txt` parts, at the root |
| SK-BADGE-WORD | MUST | every `.sk-badge` shows a non-empty label |
| SK-BADGE-TONE | MUST | a `data-status` word has one tone across the site |
| SK-CHART | MUST | every `svg.viz-chart` has an `aria-label`, and its page a table |
| SK-MERMAID | MUST | no `;`, `<` or `#` inside Mermaid labels and messages |
| SK-MENU-ORDER | MUST | the declared menu follows §2 |
| SK-MODULE | MUST | a given Hugo configuration imports site-kit before Hextra |
| SK-DETERMINISM | MUST | `compare_builds.py A B` finds two builds identical, volatile patterns masked |
| SK-SPEC | SHOULD | the `spec` of `site-kit.json` is the version the checker implements |

`site-kit.json`, at the repository root (the two `volatile` patterns are
Documenter's: the footer's colophon date and the build time in
`.documenter-siteinfo.json`):

```json
{
  "spec": "0.3",
  "menu": ["Findings", "Properties", "Upstream", "History", "Methodology", "Disclosure", "Docs", "GitHub", "Search"],
  "omit": {"upstream": "the project cites three issues, listed on Methodology"},
  "volatile": ["<span class=\"colophon-date\"[^>]*>[^<]*</span>", "\"generation_timestamp\":\"[^\"]*\""]
}
```

## 14. Governance

The SPEC changes by pull request on site-kit, merged once each site's agent
has answered yes or "does not apply". Versions follow Semantic Versioning;
each site pins a tag (Hugo: its `go.mod`; others: the tag it fetches) and
names it on its Methodology page. The CHANGELOG has one line per rule
identifier that changes.

## 15. Conflict of interest and AI assistance

A site that examines, compares or evaluates third-party systems publishes a
page `conflict-of-interest`, in the menu as Disclosure (SK-PAGE-DISCLOSURE). A
site that examines none declares the page omitted in `site-kit.json`, with
its reason.

The page is generated from `docs/disclosures.tsv`, committed in the
repository (SK-DISCLOSURES): lines starting with `#` are comments, then a
header and one row per contributor and project, with the tab-separated
columns `contributor`, `orcid`, `project`, `kind`, `role` and `note`. `kind`
is one of `examined system`, `compared system`, `tool`, `source of NAME`,
`benchmark`, `AI assistance`, `other`. A row whose role is `none`, or whose
project is `none`, is also a declaration. Every contributor writes at least
one `AI assistance` row: what an AI assistant did, and how its output was
reviewed, without naming the model or the tool ("an AI assistant").

The page shows:

- a one-line summary;
- one section per contributor, with their ORCID and their rows;
- a matrix with one row per system, source or tool and one column per
  contributor, each cell the declared role or `none`;
- the use of AI assistants;
- what limits the bias;
- how to report an unfair comparison or a wrong declaration.

The one-line summary also appears on the home page (§3), in the footer, the
README, `CITATION.cff` and `llms.txt`. A change that touches an entry, a
test, an adapter, a check or an input list is not complete without the rows
of the person it is made for; an agent that makes it adds or updates those
rows. The site's text uses no em dash.
