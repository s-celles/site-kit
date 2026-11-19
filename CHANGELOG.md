# Changelog

Notable changes follow Keep a Changelog; versions follow Semantic Versioning.

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
