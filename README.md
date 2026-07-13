# Publication Figures

A reproducible renderer for journal-style quantitative figures from CSV, TSV, Excel, and Parquet data.

It supports scatter, line, point-summary, box, and violin plots; Chinese Songti and English Times New Roman typography; compact external legends; exact inline superscripts; optional linear fits with 95% confidence bands; and validated PDF, outlined SVG, and 600 dpi PNG exports. Every successful render also records QA and data provenance.

The repository includes an eight-case synthetic-data [review gallery](publication-figures/demo-gallery/index.html) for visual regression and feedback. Rebuild it with:

```bash
cd publication-figures
../.venv/bin/python scripts/build_demo_gallery.py
```

See [DEMO_WORKFLOW.md](publication-figures/DEMO_WORKFLOW.md) for the feedback workflow and [SKILL.md](publication-figures/SKILL.md) for the rendering contract.

---

## 中文

这是一个从 CSV、TSV、Excel 和 Parquet 数据生成可复现论文图的绘图工具。

目前支持散点图、折线图、原始点与置信区间汇总图、箱线图和小提琴图；统一使用中文宋体与英文 Times New Roman，支持紧凑外置图例、规范上下标、线性回归及 95% 置信带，并输出经过检查的 PDF、轮廓化 SVG、600 dpi PNG、QA 报告和数据溯源记录。

仓库附带一个包含 8 类合成数据的[反馈画廊](publication-figures/demo-gallery/index.html)，用于浏览、反馈和回归检查。运行以下命令即可完整重建：

```bash
cd publication-figures
../.venv/bin/python scripts/build_demo_gallery.py
```

反馈流程参见 [DEMO_WORKFLOW.md](publication-figures/DEMO_WORKFLOW.md)，绘图规范参见 [SKILL.md](publication-figures/SKILL.md)。
