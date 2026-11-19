# site-kit

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
- `tools/check_site.py`: checks a generated site against the SPEC's rules.
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
```

Hugo gives precedence to the first import, so site-kit comes before Hextra:
Hextra has its own `badge` shortcode and empty `custom/` hooks. Then
`hugo mod get github.com/s-celles/site-kit@v0.1.0`. A site that needs
more in the page head adds `layouts/_partials/site-kit/head-extra.html`; a
site that defines its own `custom/head-end.html` must call
`{{ partial "site-kit/head.html" . }}` in it.

In CI, after the generator has written `OUT/content` and `OUT/static`:

```sh
git clone --depth 1 --branch v0.1.0 https://github.com/s-celles/site-kit "$RUNNER_TEMP/site-kit"
python3 -I "$RUNNER_TEMP/site-kit/tools/check_site.py" --hugo site/hugo.yaml --content OUT/content --static OUT/static
```

julia-findings is built with Documenter rather than Hugo. It follows
`SPEC.md` and can copy `site-kit.css`, `tables.js` and `viz.js` as assets.

## Develop

```sh
python3 -I tests/test_check_site.py        # the checker's rules
scripts/install_hugo.sh /tmp/hugo && (cd example && /tmp/hugo/hugo --minify)   # the module builds
```

Licence: MIT ([`LICENSE`](LICENSE)). `tables.js` is adapted from
s-celles/julia-findings (MIT). Written with AI assistance; commits carry
`Assisted-by: AI`.
