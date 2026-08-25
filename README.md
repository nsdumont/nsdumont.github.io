# nsdumont.github.io

Personal academic website of Nicole Sandra-Yaffa Dumont — <https://nsdumont.github.io>

Built with [Jekyll](https://jekyllrb.com/) on a trimmed-down fork of the
[al-folio](https://github.com/alshedivat/al-folio) theme.

## Local development

```bash
bundle install
bundle exec jekyll serve
```

The site is then available at <http://localhost:4000>.

ImageMagick is required for the responsive-image pipeline (`brew install imagemagick`).

## Deployment

Pushing to `main` triggers `.github/workflows/deploy.yml`, which builds the site,
purges unused CSS, and publishes the result to the `gh-pages` branch.

## Where things live

| Path | Contents |
| --- | --- |
| `_pages/` | The site's pages: about (`/`), publications, cv, repositories, teaching, talks, news |
| `_news/` | News / announcement items shown on the homepage |
| `_bibliography/papers.bib` | Publication list; `selected={true}` marks papers for the homepage |
| `_data/` | Coauthors, venues, socials, and the repositories listed on `/repositories/` |
| `assets/img/publication_preview/` | Thumbnails referenced by `preview={...}` in `papers.bib` |
| `assets/pdf/` | CV, posters, and course outlines |
| `_config.yml` | Site settings |

## Adding a publication

Add the BibTeX entry to `_bibliography/papers.bib`. Optional fields:
`selected={true}` to feature it on the homepage, `preview={filename.png}` for a
thumbnail (place the image in `assets/img/publication_preview/`), plus
`abstract`, `pdf`, `code`, `website`, and `bibtex_show`.

## Adding a news item

Create a file in `_news/`. Short one-liners use `inline: true`; longer items use
`inline: false` and get their own page.
