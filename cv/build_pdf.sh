#!/usr/bin/env bash
# Compile the CV locally with LuaLaTeX and copy the PDF to assets/pdf/CV.pdf.
# The deploy workflow does the same thing on every push, so running this is
# only needed to preview the PDF locally or to refresh the committed copy.
set -euo pipefail
cd "$(dirname "$0")"
TEX="${1:-mmayer.tex}"
latexmk -lualatex -interaction=nonstopmode -halt-on-error "$TEX"
cp "${TEX%.tex}.pdf" ../assets/pdf/CV.pdf
latexmk -c "$TEX" >/dev/null
echo "Wrote assets/pdf/CV.pdf"
