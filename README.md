# Publication Figures

A compact workspace for producing reproducible, publication-ready research figures.

## Purpose

This repository keeps figure-generation assets separate from data collection and analysis projects. Each figure should be traceable to a script or notebook, use explicit input and output paths, and remain reproducible without project-specific hidden state.

## Suggested structure

```text
data/       # Small, shareable inputs or documented placeholders
scripts/    # Figure-generation code
figures/    # Exported publication assets
styles/     # Shared themes, fonts, and palettes
```

Store large or restricted datasets outside the repository and document how they are obtained. Prefer vector output (`PDF` or `SVG`) for line art and high-resolution `PNG` for raster graphics.

---

## 中文

用于生成可复现、可发表科研图件的轻量仓库。

本仓库将制图资产与数据采集、实证分析项目分离。每张图应对应明确的脚本或 Notebook，输入输出路径清晰，且不依赖未说明的本地状态。

建议使用 `data/`、`scripts/`、`figures/` 和 `styles/` 分别管理输入、代码、导出图件与样式。大型或受限数据应存放在仓库外，并说明获取方式；线图优先导出 `PDF` 或 `SVG`，栅格图使用高分辨率 `PNG`。
