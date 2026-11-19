# Changelog

Notable changes follow Keep a Changelog; versions follow Semantic Versioning.

## [Unreleased]

SPEC 0.2, consolidated from the reviews of the four sites.

### Changed

- The contract is stated on the built site, whatever its generator; the
  Hugo module is one implementation (SPEC §11).
- `tools/check_site.py` checks the built HTML (`--site`, `--config`,
  `--hugo`, `--repo`) with MUST and SHOULD levels, and prints the SPEC
  version. Its 0.1 options `--content` and `--static` are gone.
- SK-HOME-STAMP accepts a commit or a date (a dated run).
- SK-HOME-DISCLAIMER and SK-HOME-PROVENANCE look inside `.disclaimer` only.
- SK-PAGE-UPSTREAM and SK-PAGE-HISTORY are warnings, silenced by an omission
  with its reason in `site-kit.json`.
- SK-MENU-ORDER: at most 8 entries; the menu may come from `site-kit.json`.
- SK-LLMS accepts `llms-full.txt` split into `llms-full-NAME.txt` parts.
- `viz.js`: the tooltip stays inside the chart's figure; a dense chart
  (`data-viz="dense"`) is one tab stop, the arrow keys step through x and the
  tooltip lists every series.

### Added

- SK-CITATION (SHOULD), SK-BADGE-WORD, SK-BADGE-TONE, SK-CHART, SK-MERMAID
  (MUST), SK-SPEC (SHOULD).
- SK-DETERMINISM and `tools/compare_builds.py`, with `volatile` patterns.
- `tools/upstream_status.py` and the snapshot columns `repo number kind
  state created closed merged fixes cited_by title`.
- Tones `alt-dashed` and `neutral-dashed`; `forced-colors` styles; the
  badge shortcode's `siteKit.badgeLabels`.
- `TEMPLATES.md`; `site-kit.json` in the example; CI builds the example
  twice, checks it and compares the builds.

## [0.1.1] - 2026-11-19

### Changed

- `SPEC.md` names no project and no domain: its examples are generic.

## [0.1.0] - 2026-11-19

### Added

- `SPEC.md` version 0.1: the shared structure of the project sites.
- Hugo module: `badge` (tones from `siteKit.badgeTones`), `stats` and `stat`
  shortcodes; Hextra hooks `custom/head-end.html` and `custom/footer.html`;
  `site-kit.css`, `tables.js` and `viz.js`.
- `tools/check_site.py` with rules SK-MODULE, SK-MENU-ORDER, SK-HOME-STAMP,
  SK-HOME-DISCLAIMER, SK-HOME-PROVENANCE, SK-HOME-CITE, SK-PAGE-UPSTREAM,
  SK-PAGE-HISTORY, SK-PAGE-METHODOLOGY, SK-PAGE-STATUSES and SK-LLMS.
- `scripts/install_hugo.sh` and `hugo-version` (Hugo Extended 0.152.2).
- An example site that CI builds against the module.
