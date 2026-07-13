#!/usr/bin/env python3
"""Create deterministic synthetic datasets, render them, and build an HTML review gallery."""

from __future__ import annotations

import argparse
import csv
import html
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import yaml

from render_figure import render


CASES = [
    ("F01", "连续变量散点", "检查点密度、离群值、坐标轴和英文单位", "scatter"),
    ("F02", "双组剂量响应", "检查折线辨识度、图例位置和科学单位", "line"),
    ("F03", "三组时间序列", "检查多折线、中文图例和紧凑画布", "line"),
    ("F04", "处理组点汇总", "检查原始点、均值和 95% bootstrap CI", "point_summary"),
    ("F05", "偏态数据箱线图", "检查偏态、离群值和原始观测的表达", "box"),
    ("F06", "双峰分布小提琴图", "检查分布形状、重叠和分类标签", "violin"),
    ("F07", "中文区域比较", "检查纯中文标签、缺失值处理和窄图", "point_summary"),
    ("F08", "五模型布局压力测试", "检查五组颜色、右侧图例和长画布", "point_summary"),
]


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def spec(name: str, data: Path, kind: str, x: str, y: str, labels: dict, *, group: str | None = None,
         display_labels: dict | None = None, language: str = "zh", width: int = 110, height: int = 72) -> dict:
    plot = {"kind": kind, "x": x, "y": y}
    if group:
        plot["group"] = group
    if display_labels:
        plot["display_labels"] = display_labels
    return {
        "name": name, "data": str(data), "plot": plot, "labels": labels,
        "language": language, "dimensions_mm": {"width": width, "height": height},
        "legend": "auto" if group else "none",
    }


def generate(root: Path) -> list[Path]:
    rng = np.random.default_rng(20260713)
    data_dir, spec_dir = root / "data", root / "specs"
    data_dir.mkdir(parents=True, exist_ok=True)
    spec_dir.mkdir(parents=True, exist_ok=True)
    specs: list[dict] = []

    x = np.linspace(2, 98, 74)
    y = 1.8 + 0.055 * x + rng.normal(0, 0.62, len(x)); y[[9, 61]] += [2.6, -2.2]
    p = data_dir / "F01_scatter.csv"
    write_csv(p, ["soil_carbon", "respiration"], [{"soil_carbon": round(a, 3), "respiration": round(b, 3)} for a, b in zip(x, y)])
    specs.append(spec("F01_scatter", p, "scatter", "soil_carbon", "respiration",
                      {"x": [{"text": "土壤有机碳 ", "role": "chinese"}, {"text": "(g·kg$^{-1}$)", "role": "latin"}],
                       "y": [{"text": "呼吸速率 ", "role": "chinese"}, {"text": "(μmol·m$^{-2}$·s$^{-1}$)", "role": "latin"}]}))
    specs[-1]["plot"]["fit"] = "linear"

    rows = []
    for treatment, shift in [("control", 0.0), ("amended", 0.12)]:
        for dose in [0, 1, 2, 5, 10, 20, 40]:
            rows.append({"dose": dose, "response": round(0.12 + shift + 0.72 * dose / (dose + 6) + rng.normal(0, .025), 4), "treatment": treatment})
    p = data_dir / "F02_dose_response.csv"; write_csv(p, ["dose", "response", "treatment"], rows)
    specs.append(spec("F02_dose_response", p, "line", "dose", "response",
                      {"x": [{"text": "浓度 ", "role": "chinese"}, {"text": "(μM)", "role": "latin"}], "y": "Response (fraction)"},
                      group="treatment", display_labels={"group": {"control": "Control", "amended": "Amended"}}, width=120))

    rows = []
    for group, base, slope in [("北部", 12, .34), ("中部", 10.5, .25), ("南部", 9.8, .18)]:
        for day in range(0, 29, 4): rows.append({"day": day, "chlorophyll": round(base + slope * day + rng.normal(0, .55), 3), "region": group})
    p = data_dir / "F03_time_series.csv"; write_csv(p, ["day", "chlorophyll", "region"], rows)
    specs.append(spec("F03_time_series", p, "line", "day", "chlorophyll",
                      {"x": "观测日", "y": [{"text": "叶绿素 a ", "role": "chinese"}, {"text": "(μg L$^{-1}$)", "role": "latin"}]}, group="region", width=135))

    rows = []
    for method, shift in [("baseline", 0), ("method_a", .07), ("method_b", .13)]:
        for split, penalty in [("random", 0), ("spatial", -.10), ("temporal", -.16)]:
            for value in .68 + shift + penalty + rng.normal(0, .035, 12): rows.append({"split": split, "score": round(value, 4), "method": method})
    p = data_dir / "F04_point_summary.csv"; write_csv(p, ["split", "score", "method"], rows)
    specs.append(spec("F04_point_summary", p, "point_summary", "split", "score", {"x": "验证方案", "y": "R²"}, group="method",
                      display_labels={"x": {"random": "随机", "spatial": "空间", "temporal": "时间"}, "group": {"baseline": "Baseline", "method_a": "Method A", "method_b": "Method B"}}, width=140, height=78))

    rows = []
    for site, scale in [("forest", 1.0), ("grassland", .75), ("wetland", 1.35)]:
        vals = rng.lognormal(mean=1.35, sigma=.55, size=34) * scale
        for value in vals: rows.append({"habitat": site, "biomass": round(value, 3)})
    p = data_dir / "F05_box.csv"; write_csv(p, ["habitat", "biomass"], rows)
    specs.append(spec("F05_box", p, "box", "habitat", "biomass", {"x": "Habitat", "y": "Biomass (g m$^{-2}$)"},
                      display_labels={"x": {"forest": "Forest", "grassland": "Grassland", "wetland": "Wetland"}}, language="en"))

    rows = []
    for stage, centers in [("early", (1.8, 3.1)), ("middle", (2.5, 4.0)), ("late", (3.0, 5.2))]:
        values = np.r_[rng.normal(centers[0], .28, 25), rng.normal(centers[1], .35, 21)]
        for value in values: rows.append({"stage": stage, "expression": round(value, 3)})
    p = data_dir / "F06_violin.csv"; write_csv(p, ["stage", "expression"], rows)
    specs.append(spec("F06_violin", p, "violin", "stage", "expression", {"x": "Stage", "y": "Relative expression"},
                      display_labels={"x": {"early": "Early", "middle": "Middle", "late": "Late"}}, language="en"))

    rows = []
    for region, center in [("东北", 71), ("华北", 66), ("华东", 78), ("西南", 62)]:
        for i, value in enumerate(rng.normal(center, 7, 18)): rows.append({"区域": region, "生态指数": "" if i == 3 and region == "华北" else round(value, 2)})
    p = data_dir / "F07_chinese.csv"; write_csv(p, ["区域", "生态指数"], rows)
    specs.append(spec("F07_chinese", p, "point_summary", "区域", "生态指数", {"x": "区域", "y": "生态质量指数"}, width=88, height=68))

    rows = []
    models = [("linear_model", .61), ("random_forest", .69), ("gradient_boost", .73), ("neural_network", .71), ("ensemble", .77)]
    for model, center in models:
        for dataset, delta in [("internal", 0), ("external", -.09)]:
            for value in rng.normal(center + delta, .025, 9): rows.append({"dataset": dataset, "accuracy": round(value, 4), "model": model})
    p = data_dir / "F08_stress.csv"; write_csv(p, ["dataset", "accuracy", "model"], rows)
    specs.append(spec("F08_stress", p, "point_summary", "dataset", "accuracy", {"x": "Evaluation set", "y": "Balanced accuracy"}, group="model",
                      display_labels={"x": {"internal": "Internal", "external": "External"}, "group": {"linear_model": "Linear", "random_forest": "Random forest", "gradient_boost": "Gradient boost", "neural_network": "Neural network", "ensemble": "Ensemble"}}, language="en", width=165, height=82))

    paths = []
    for index, payload in enumerate(specs):
        path = spec_dir / f"{CASES[index][0]}_{CASES[index][3]}.yaml"
        path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
        paths.append(path)
    return paths


def gallery(root: Path, results: list[dict]) -> None:
    cards = []
    for case, result in zip(CASES, results):
        fid, title, prompt, _ = case
        name = Path(result["provenance"]["outputs"]["png"]).stem
        cards.append(f'''<article id="{fid}"><h2>{fid} · {html.escape(title)}</h2>
<a href="figures/{name}.png"><img src="figures/{name}.png" alt="{fid} {html.escape(title)}"></a>
<p>{html.escape(prompt)}</p><p class="meta">使用 {result['provenance']['rows_used']} 行 · QA: 通过 ·
<a href="figures/{name}.pdf">PDF</a> · <a href="figures/{name}.svg">SVG</a> · <a href="figures/{name}.qa.json">QA</a> · <a href="specs/{Path(result['provenance']['spec']).name}">配置</a></p></article>''')
    page = f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Publication Figures 反馈画廊</title><style>body{{max-width:1200px;margin:30px auto;padding:0 20px;font:16px system-ui;color:#222}}header{{margin-bottom:28px}}main{{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:24px}}article{{border:1px solid #ddd;border-radius:10px;padding:18px;background:#fff}}img{{width:100%;background:#fafafa}}h2{{font-size:18px}}.meta{{font-size:13px;color:#666}}code{{background:#eee;padding:2px 5px}}</style>
<header><h1>Publication Figures 反馈画廊</h1><p>全部为固定随机种子生成的合成数据，仅用于功能和视觉测试。请按编号反馈，例如：<code>F04 原始点太密，CI 不够醒目</code>。</p></header><main>{''.join(cards)}</main></html>'''
    (root / "index.html").write_text(page, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("demo-gallery"))
    parser.add_argument("--font-dir", type=Path, action="append", default=[])
    args = parser.parse_args()
    root = args.output_dir.resolve()
    if root.exists(): shutil.rmtree(root)
    root.mkdir(parents=True)
    specs = generate(root)
    fonts = args.font_dir or [Path("/System/Library/Fonts/Supplemental")]
    results = []
    for item in specs:
        print(f"Rendering {item.stem}...", flush=True)
        results.append(render(item, fonts, root / "figures"))
    gallery(root, results)
    summary = {"passed": len(results), "total": len(specs), "gallery": str(root / "index.html")}
    (root / "build-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try: main()
    except Exception as exc:
        print(f"DEMO BUILD FAILED: {exc}", file=sys.stderr)
        raise
