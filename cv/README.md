# CV

The LaTeX file in this folder is the single source of truth for the CV.

- **Web page** (`/cv/`): at build time, `_plugins/cv-from-tex.rb` runs `build_cv.py`, which parses the AltaCV macros (`\cvsection`, `\cvsubsection`, `\cvevent`, `\divider`, `itemize`, `\fullcite`, `\href`, `\textbf`, ...) into structured data that `_pages/cv.md` renders as HTML. Citations are formatted from the `.bib` file named in `\addbibresource`.
- **PDF** (`assets/pdf/CV.pdf`): the deploy workflow compiles the same file with LuaLaTeX on every push and copies the result into the site. To refresh the committed copy or preview locally, run `cv/build_pdf.sh` (needs a TeX Live install with `latexmk`, `biber`, `academicons`, `fontawesome` and the Carlito font).

## Updating the CV

1. Edit the `.tex` file (and the `.bib` file for publications) as usual.
2. Optionally check the parsed structure: `python3 cv/build_cv.py | less`. Warnings about unknown commands are printed to stderr.
3. Commit and push. The site rebuilds the page and the PDF.

The `jekyll serve` dev server does not watch this folder (it is excluded so the sources are not published), so after editing the `.tex` file locally, touch any other file or restart the server to see the change.

## Notes for the parser

- Layout-only commands (`\vspace`, `\pagebreak`, `\smallskip`, font sizes, ...) are ignored.
- An `itemize` directly after a `\cvevent` becomes that event's bullet list; elsewhere it becomes a standalone list.
- `\footnotesize`/`\small` text is rendered smaller and muted; `flushright` blocks are right-aligned.
- Unknown commands keep their argument text and print a warning, so new macros degrade gracefully.
- The file name is set by `cv_tex` in `_config.yml` and `root_file` in `.github/workflows/deploy.yml`.
