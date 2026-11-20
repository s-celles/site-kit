# Wording templates (SPEC.md §3, §10)

Texts with slots in `{braces}`. Each site's owner approves the final text;
these are a starting point, not a requirement. The checks only look for
"non-commercial" and "AI" inside the home page's `.disclaimer` element.

## Disclaimer

> **Disclaimer.** {Project} is an individual, non-commercial project. It is
> not produced, endorsed or certified by {the standard body, the projects it
> examines, or anyone else}. Its aim is {to help improve the open source
> implementations it examines}.

## Provenance

> **Provenance.** {What an AI assistant wrote: the code, the tests, the
> expected values, the texts.} {What a person checked, and how.} {What may
> still be wrong, and how to report it.} A person decides what is reported
> upstream.

Say concretely which parts an AI assistant wrote. Do not name the model or
the tool: "an AI assistant" is enough, and commits carry `Assisted-by: AI`.
When the expected values rest on a document the owner has no copy of, say
so.

## Home page markup

```html
<p class="data-stamp">Data at commit <a href="{commit URL}"><code>{short sha}</code></a> ({YYYY-MM-DD}).</p>

<div class="disclaimer">

**Disclaimer.** ...

**Provenance.** ...

</div>
```

A site whose numbers come from a dated run rather than from a commit writes
"Data from the run of {YYYY-MM-DD}" instead.

## Citation key

> `{family}{year}{slug}`: for example `celles2026goinlean`, `celles2026casbench`.

The slug is short, lowercase and alphanumeric: the repository name or an
abbreviation of the title. Keep it stable across releases, so that existing
citations keep resolving.

## Footer

> An individual, non-commercial project, not endorsed by {...}. Code
> {licence}, data {licence}. Written with AI assistance.

Hugo sites set it as `params.siteKit.footer`; others put it in their footer
template.

## Sources (sites that reuse third-party material)

> **Sources.** {Source}, {licence}: {generated with | quoted from | derived
> from} it; {what the site changed}.

## Not reproduced

> **Not reproduced here.** {Third-party numbers quoted with their caveats;
> systems not run, and why.}

## Conflict of interest summary (SPEC.md §15)

> Disclosure: {the author's relation to the systems examined or compared, in
> one clause each, or "none"}; {funding, employment or other interest, or
> none}; works with an AI assistant.

The same sentence goes on the home page (near the disclaimer, with a link to
the `conflict-of-interest` page), in the footer, the README, `CITATION.cff`
(for example in `abstract`) and `llms.txt`. The AI assistance rows of
`docs/disclosures.tsv` say what the assistant did and how its output was
reviewed, without naming the model or the tool.
