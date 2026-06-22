---
name: publication-figures
description: Create reproducible, journal-neutral quantitative manuscript figures from CSV, TSV, XLSX, or Parquet data. Use when Codex must inspect research data, choose a defensible scatter, line, point-summary, box, or violin plot, enforce Chinese Songti and English Times New Roman typography, export publication PDF/SVG/PNG, or validate chart layout, fonts, and provenance.
---

# Publication Figures

Render observed data only. Never use an image model to fabricate data marks, microscopy, spectra, statistics, or experimental evidence.

## Workflow

1. Establish the claim, observational unit, comparison, units, and whether the requested result is exploratory or confirmatory. Inspect the source with `scripts/profile_table.py` before choosing a plot.
2. Create a declarative YAML specification. Read `references/figure-spec.md` for the complete schema and `references/figure-selection.md` for chart selection.
3. Supply legal Times New Roman and Songti font files through one or more `--font-dir` arguments. Do not render if either exact font family is unavailable.
4. Render and validate in one command:

   ```bash
   python scripts/render_figure.py figure.yaml --font-dir /path/to/times --font-dir /path/to/songti --output-dir figures
   ```

5. Inspect the emitted PNG and read `*.qa.json` before handing off. Use the PDF for manuscripts, outlined-text SVG for graphics editing, and 600-dpi PNG only for review or raster-only submissions.

## Mandatory style contract

- Never place a title inside the figure. Put titles in the manuscript or caption.
- Use Songti for Chinese strings and Times New Roman for English, numbers, units, and math symbols. A mixed-language label must use explicit text segments in the YAML specification.
- Treat every `^` and `_` as a potential superscript/subscript instruction. Convert unambiguous numeric forms before rendering; reject ambiguous machine-style markup until the agent supplies a reviewed display-label mapping.
- Use an unframed legend. The renderer places it outside the axes; do not overlay data.
- Preserve raw observations for group comparisons. `point_summary` overlays a mean and 95% bootstrap confidence interval; it is not summary-only.
- Use a white background, restrained color-blind-safe palette, consistent line weights, and no top or right spine.
- Treat missing columns, missing fonts, unsupported glyphs, titles, clipping, collision, framed legend, overlong legend labels, and unembedded PDF fonts as render failures. Render to a temporary directory and publish artifacts only after QA passes.

## Scope

Support single-panel scatter, line, point-summary, box, and violin charts. Do not use this Skill for multi-panel composition, graphical abstracts, or mechanism illustrations.

## Resources

- `scripts/profile_table.py`: profile supported tabular inputs without modifying them.
- `scripts/render_figure.py`: validate a figure specification and emit PDF, outlined SVG, PNG, provenance, and QA artifacts.
- `references/figure-spec.md`: specification schema and segmented-label format.
- `references/figure-selection.md`: evidence-preserving chart selection rules.
