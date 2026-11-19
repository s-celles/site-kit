# site-kit

> **SPEC 0.2, proposed.** It is agreed when each site's agent has answered
> yes or "does not apply"; see `SPEC.md`, §14.

The shared structure and building blocks of the project sites of
[s-celles](https://github.com/s-celles): iec61131-conformance, go-in-lean,
julia-findings and computer_algebra_system_benchmarks. These sites publish
findings, results and their evidence.

- [`SPEC.md`](SPEC.md): what every site has, in which order (menu, home page,
  registry entries, statuses, upstream, history, methodology, citation,
  `llms.txt`, build).
- A Hugo module for sites built with [Hextra](https://github.com/imfing/hextra):
  - shortcodes `badge`, `stats` and `stat`;
  - the Hextra hooks `custom/head-end.html` and `custom/footer.html`;
  - styles (`assets/css/site-kit/site-kit.css`): badges, stat tiles,
    disclaimer, data stamp, tables and charts, with validated light and dark
    palettes;
  - scripts: `tables.js` (filter, sort and page tables in the browser) and
    `viz.js` (tooltips and crosshair for SVG charts, keyboard reachable).
- Tools for every generator (Python standard library only):
  - `tools/check_site.py`: checks a **built** site (Hugo's `public/`,
    Documenter's `build/`) against the SPEC's rules, MUST and SHOULD;
  - `tools/compare_builds.py`: checks that two builds of one commit are
    identical, generator date lines masked (SK-DETERMINISM);
  - `tools/upstream_status.py`: refreshes the upstream snapshot TSV from
    GitHub.
- `TEMPLATES.md`: disclaimer, provenance and footer texts with slots.
- `scripts/install_hugo.sh` and `hugo-version`: the pinned Hugo Extended,
  checked by checksum.

## Use

In the site's `hugo.yaml`:

```yaml
module:
  imports:
    - path: github.com/s-celles/site-kit   # before Hextra: the first import wins
    - path: github.com/imfing/hextra
params:
  siteKit:
    themeColor: "#173f66"
    icon: brand/mark.svg
    footer: "An individual, non-commercial project. Code MIT, data CC BY 4.0."
    badgeTones:        # status word (lower case) -> tone
      pass: good
      fail: bad
      error: warn-dashed
    badgeLabels:       # optional: word (lower case) -> display form
      proved_in_model: Proved in model
```

Hugo gives precedence to the first import, so site-kit comes before Hextra:
Hextra has its own `badge` shortcode and empty `custom/` hooks. Then
`hugo mod get github.com/s-celles/site-kit@v0.2.0`. A site that needs
more in the page head adds `layouts/_partials/site-kit/head-extra.html`; a
site that defines its own `custom/head-end.html` must call
`{{ partial "site-kit/head.html" . }}` in it.

In CI, after the site is built (twice, for the determinism check):

```sh
git clone --depth 1 --branch v0.2.0 https://github.com/s-celles/site-kit "$RUNNER_TEMP/site-kit"
python3 -I "$RUNNER_TEMP/site-kit/tools/check_site.py" --site public --config site-kit.json --repo . [--hugo site/hugo.yaml]
python3 -I "$RUNNER_TEMP/site-kit/tools/compare_builds.py" public public-again --config site-kit.json
```

A site built with another generator (Documenter, for one) follows the same
markup contract (`SPEC.md` §11), runs the same tools on its build, and copies
`site-kit.css`, `tables.js` and `viz.js` as assets. It declares its menu and
any generator date line in `site-kit.json`.

## Develop

```sh
for t in tests/test_*.py; do python3 -I "$t"; done   # the tools
scripts/install_hugo.sh /tmp/hugo && (cd example && /tmp/hugo/hugo --minify)   # the module builds
```

Licence: MIT ([`LICENSE`](LICENSE)). `tables.js` is adapted from
s-celles/julia-findings (MIT). Written with AI assistance; commits carry
`Assisted-by: AI`.
