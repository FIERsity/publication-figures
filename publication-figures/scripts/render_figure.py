#!/usr/bin/env python3
"""Render one validated, publication-style quantitative figure from a YAML spec."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "publication-figures-mpl"))
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from fontTools.ttLib import TTFont
from matplotlib import font_manager
from matplotlib.font_manager import FontProperties
from matplotlib.offsetbox import AnchoredOffsetbox, HPacker, TextArea, VPacker
from matplotlib.transforms import Bbox

PALETTE = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#56B4E9", "#E69F00", "#000000"]
SUPPORTED_KINDS = {"scatter", "line", "point_summary", "box", "violin"}
SUPERSCRIPT = str.maketrans("0123456789+-=()", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾")
SUBSCRIPT = str.maketrans("0123456789+-=()", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎")


class FigureContractError(ValueError):
    """Raised when a spec or exported figure violates the style contract."""


@dataclass(frozen=True)
class Fonts:
    times_path: Path
    songti_path: Path
    times: FontProperties
    songti: FontProperties


def font_names(path: Path) -> tuple[str, str]:
    font = TTFont(path, lazy=True)
    try:
        families = [record.toUnicode() for record in font["name"].names if record.nameID in {1, 16}]
        styles = [record.toUnicode() for record in font["name"].names if record.nameID in {2, 17}]
        return next((name for name in families if name), ""), next((name for name in styles if name), "")
    finally:
        font.close()


def find_font(font_dirs: list[Path], marker: str) -> Path:
    candidates: list[Path] = []
    for directory in font_dirs:
        if not directory.is_dir():
            raise FigureContractError(f"Font directory not found: {directory}")
        candidates.extend(path for path in directory.rglob("*") if path.suffix.lower() in {".ttf", ".otf", ".ttc"})
    matched: list[tuple[Path, str]] = []
    for candidate in candidates:
        try:
            family, style = font_names(candidate)
            if marker.lower() in family.lower():
                matched.append((candidate, style))
        except Exception:
            continue
    for candidate, style in matched:
        if style.lower() in {"regular", "roman", "book"}:
            return candidate
    if matched:
        return matched[0][0]
    raise FigureContractError(f"Required font family not found: {marker}")


def load_fonts(font_dirs: list[Path]) -> Fonts:
    times_path = find_font(font_dirs, "Times New Roman")
    songti_path = find_font(font_dirs, "Songti")
    for path in (times_path, songti_path):
        font_manager.fontManager.addfont(str(path))
    return Fonts(times_path, songti_path, FontProperties(fname=times_path), FontProperties(fname=songti_path))


def read_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".tsv", ".tab"}:
        return pd.read_csv(path, sep="\t")
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    if suffix == ".parquet":
        return pd.read_parquet(path)
    raise FigureContractError(f"Unsupported table format: {suffix}")


def has_cjk(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def has_ascii_letters(text: str) -> bool:
    return any(char.isascii() and char.isalpha() for char in text)


def normalize_segments(value: str | list[dict[str, str]]) -> list[dict[str, str]]:
    if isinstance(value, str):
        if has_cjk(value) and has_ascii_letters(value):
            raise FigureContractError("Mixed Chinese and Latin text requires explicit label segments")
        return [{"text": format_markup(value), "role": "chinese" if has_cjk(value) else "latin"}]
    if not isinstance(value, list) or not value:
        raise FigureContractError("A label must be a string or non-empty segment list")
    normalized = []
    for item in value:
        if not isinstance(item, dict) or set(item) != {"text", "role"} or item["role"] not in {"chinese", "latin"}:
            raise FigureContractError("Each label segment must contain exactly text and role (chinese or latin)")
        normalized.append({"text": format_markup(item["text"]), "role": item["role"]})
    return normalized


def format_markup(text: str) -> str:
    """Convert unambiguous plain-text ^/_ notation to MathText and reject ambiguity."""
    parts = re.split(r"(\$[^$]*\$)", text)
    rendered: list[str] = []
    for part in parts:
        if part.startswith("$") and part.endswith("$"):
            rendered.append(part)
            continue
        def render_script(match: re.Match[str]) -> str:
            marker, content = match.group(1), match.group(2) or match.group(3)
            table = SUPERSCRIPT if marker == "^" else SUBSCRIPT
            if all(char in "0123456789+-=()" for char in content):
                return content.translate(table)
            return f"${marker}{{{content}}}$"

        part = re.sub(r"([_^])(?:\{([^{}]+)\}|(\d+))", render_script, part)
        if "^" in re.sub(r"\$[^$]*\$", "", part) or "_" in re.sub(r"\$[^$]*\$", "", part):
            raise FigureContractError(f"Ambiguous ^/_ markup in {text!r}; use $...$ or a display-label mapping")
        rendered.append(part)
    return "".join(rendered)


def display_label(value: Any, mapping: dict[str, str] | None) -> str:
    raw = str(value)
    return format_markup((mapping or {}).get(raw, raw))


def prop_for(role: str, fonts: Fonts) -> FontProperties:
    return fonts.songti if role == "chinese" else fonts.times


def check_glyphs(segments: list[dict[str, str]], fonts: Fonts) -> None:
    cmaps: dict[str, set[int]] = {}
    for role, path in {"latin": fonts.times_path, "chinese": fonts.songti_path}.items():
        font = TTFont(path, lazy=True)
        try:
            cmap = set()
            for table in font["cmap"].tables:
                cmap.update(table.cmap)
            cmaps[role] = cmap
        finally:
            font.close()
    for segment in segments:
        plain_text = re.sub(r"\$[^$]*\$", "", segment["text"])
        for char in plain_text:
            if char.isspace() or char in "$^_{}\\":
                continue
            if ord(char) not in cmaps[segment["role"]]:
                raise FigureContractError(f"Unsupported glyph {char!r} for {segment['role']} font")


def draw_axis_label(ax: Any, axis: str, value: str | list[dict[str, str]], fonts: Fonts) -> Any:
    segments = normalize_segments(value)
    check_glyphs(segments, fonts)
    if axis == "x":
        child = HPacker(children=[TextArea(item["text"], textprops={"fontproperties": prop_for(item["role"], fonts), "size": 8.5}) for item in segments], align="center", pad=0, sep=0)
        artist = AnchoredOffsetbox(loc="lower center", child=child, frameon=False, bbox_to_anchor=(0.5, -0.38), bbox_transform=ax.transAxes, borderpad=0)
        ax.add_artist(artist)
        return artist
    child = VPacker(children=[TextArea(item["text"], textprops={"fontproperties": prop_for(item["role"], fonts), "size": 8.5, "rotation": 90}) for item in segments], align="center", pad=0, sep=0)
    artist = AnchoredOffsetbox(loc="center left", child=child, frameon=False, bbox_to_anchor=(-0.17, 0.5), bbox_transform=ax.transAxes, borderpad=0)
    ax.add_artist(artist)
    return artist


def bootstrap_interval(values: pd.Series) -> tuple[float, float]:
    array = values.dropna().to_numpy(dtype=float)
    if len(array) < 2:
        return (np.nan, np.nan)
    rng = np.random.default_rng(20260622)
    means = rng.choice(array, size=(4000, len(array)), replace=True).mean(axis=1)
    return tuple(np.quantile(means, [0.025, 0.975]))


def style_axis(ax: Any, fonts: Fonts) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_linewidth(0.65)
    ax.tick_params(direction="out", width=0.65, length=3, labelsize=7.5)
    for label in [*ax.get_xticklabels(), *ax.get_yticklabels()]:
        label.set_fontproperties(fonts.songti if has_cjk(label.get_text()) else fonts.times)


def plot_data(ax: Any, df: pd.DataFrame, plot: dict[str, Any], fonts: Fonts) -> None:
    kind, x, y, group = plot["kind"], plot["x"], plot["y"], plot.get("group")
    display_labels = plot.get("display_labels", {})
    x_labels = display_labels.get("x", {})
    group_labels = display_labels.get("group", {})
    groups = list(df.groupby(group, sort=False, dropna=False)) if group else [(None, df)]
    if kind in {"scatter", "line"}:
        for index, (label, data) in enumerate(groups):
            data = data.sort_values(x) if kind == "line" else data
            style = {"color": PALETTE[index % len(PALETTE)], "label": display_label(label, group_labels) if label is not None else None}
            if kind == "scatter":
                ax.scatter(data[x], data[y], s=24, alpha=0.88, linewidths=0.35, edgecolors="white", **style)
            else:
                ax.plot(data[x], data[y], marker="o", markersize=3.2, linewidth=1.15, **style)
        return

    categories = list(dict.fromkeys(df[x].astype(str)))
    positions = np.arange(len(categories))
    if kind == "point_summary":
        for index, (label, data) in enumerate(groups):
            width = 0.7 / len(groups)
            offset = (index - (len(groups) - 1) / 2) * width
            color = PALETTE[index % len(PALETTE)]
            for position, category in zip(positions, categories):
                values = data.loc[data[x].astype(str) == category, y]
                jitter = np.linspace(-width * 0.18, width * 0.18, len(values)) if len(values) > 1 else [0]
                ax.scatter(position + offset + jitter, values, s=18, color="white", edgecolors=color, linewidths=0.65, zorder=3)
                if len(values):
                    mean = values.mean()
                    low, high = bootstrap_interval(values)
                    ax.errorbar(position + offset, mean, yerr=[[mean - low], [high - mean]] if np.isfinite(low) else None, color=color, marker="o", markersize=4, linewidth=1.0, capsize=2.2, zorder=4)
            if label is not None:
                ax.plot([], [], color=color, marker="o", linewidth=1, label=display_label(label, group_labels))
    else:
        if group:
            raise FigureContractError(f"{kind} does not support group in v1; use point_summary or one series")
        values = [df.loc[df[x].astype(str) == category, y].to_numpy() for category in categories]
        if kind == "box":
            ax.boxplot(values, positions=positions, widths=0.58, showfliers=False, medianprops={"color": "#000000", "linewidth": 1.0})
        else:
            ax.violinplot(values, positions=positions, widths=0.72, showmedians=True)
        for position, value in zip(positions, values):
            ax.scatter(np.full(len(value), position) + np.linspace(-0.08, 0.08, len(value)), value, s=16, color=PALETTE[0], alpha=0.8, zorder=3)
    ax.set_xticks(positions, [display_label(category, x_labels) for category in categories])


def run_qa(fig: Any, ax: Any, fonts: Fonts, pdf_path: Path, axis_labels: list[Any], language: str) -> dict[str, Any]:
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    tight = fig.get_tightbbox(renderer)
    report: dict[str, Any] = {"passed": False, "checks": []}
    legend = ax.get_legend()
    if legend and legend.get_frame_on():
        raise FigureContractError("Legend frame detected")
    report["checks"].append("legend_frameless")
    important = [text for text in ax.texts if text.get_text()] + [ax.xaxis.label, ax.yaxis.label]
    for text in important:
        bbox = text.get_window_extent(renderer).transformed(fig.dpi_scale_trans.inverted())
        if bbox.x0 < tight.x0 - 0.02 or bbox.y0 < tight.y0 - 0.02 or bbox.x1 > tight.x1 + 0.02 or bbox.y1 > tight.y1 + 0.02:
            raise FigureContractError(f"Clipped text detected: {text.get_text()!r}")
    report["checks"].append("no_clipped_axis_text")
    label_boxes = [artist.get_window_extent(renderer) for artist in axis_labels]
    for index, label_box in enumerate(label_boxes):
        for other_box in label_boxes[index + 1 :]:
            overlap = Bbox.intersection(label_box, other_box)
            if overlap and overlap.width * overlap.height > 1:
                raise FigureContractError("Axis labels overlap each other")
    nearby_text = [*ax.get_xticklabels(), *ax.get_yticklabels()]
    if legend:
        nearby_text.extend(legend.get_texts())
    for label_box in label_boxes:
        for text in nearby_text:
            if not text.get_text():
                continue
            other_box = text.get_window_extent(renderer)
            overlap = Bbox.intersection(label_box, other_box)
            if overlap and overlap.width * overlap.height > 1:
                raise FigureContractError(f"Axis label overlaps text: {text.get_text()!r}")
    report["checks"].append("no_label_text_collisions")
    if legend:
        legend_box = legend.get_window_extent(renderer)
        axes_box = ax.get_window_extent(renderer)
        if legend_box.overlaps(axes_box):
            raise FigureContractError("Legend overlaps plotting axes")
    report["checks"].append("legend_outside_axes")
    result = subprocess.run(["pdffonts", str(pdf_path)], capture_output=True, text=True, check=True)
    font_report = result.stdout.lower().replace(" ", "")
    required_markers = ["times"] + (["songti"] if language == "zh" else [])
    missing_fonts = [marker for marker in required_markers if marker not in font_report]
    if missing_fonts:
        raise FigureContractError(f"PDF does not embed required fonts: {', '.join(missing_fonts)}")
    report["checks"].append("pdf_fonts_embedded")
    report["pdffonts"] = result.stdout
    report["passed"] = True
    return report


def resolve_path(value: str, spec_path: Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (spec_path.parent / path).resolve()


def validate_spec(spec: dict[str, Any]) -> None:
    if not isinstance(spec, dict):
        raise FigureContractError("Specification must be a YAML mapping")
    if "title" in spec or "title" in spec.get("plot", {}):
        raise FigureContractError("Figure titles are prohibited by the style contract")
    required = {"name", "data", "plot", "labels", "language", "dimensions_mm", "legend"}
    missing = required - set(spec)
    if missing:
        raise FigureContractError(f"Specification missing: {', '.join(sorted(missing))}")
    if spec["plot"].get("kind") not in SUPPORTED_KINDS:
        raise FigureContractError(f"Unsupported plot kind: {spec['plot'].get('kind')}")
    if spec["language"] not in {"zh", "en"}:
        raise FigureContractError("language must be zh or en")
    if spec["legend"] not in {"auto", "none"}:
        raise FigureContractError("legend must be auto or none")
    dimensions = spec["dimensions_mm"]
    if not all(key in dimensions and float(dimensions[key]) > 0 for key in ("width", "height")):
        raise FigureContractError("dimensions_mm must include positive width and height")


def render(spec_path: Path, font_dirs: list[Path], output_dir: Path) -> dict[str, Any]:
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    validate_spec(spec)
    fonts = load_fonts(font_dirs)
    data_path = resolve_path(spec["data"], spec_path)
    df = read_table(data_path)
    plot = spec["plot"]
    required_columns = [plot["x"], plot["y"]] + ([plot["group"]] if plot.get("group") else [])
    missing = [column for column in required_columns if column not in df.columns]
    if missing:
        raise FigureContractError(f"Data is missing required columns: {', '.join(missing)}")
    df = df.dropna(subset=required_columns)
    if df.empty:
        raise FigureContractError("No complete observations remain after removing missing values")
    plt.rcParams.update({
        "font.size": 8.5,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "path",
        "axes.unicode_minus": False,
        "mathtext.fontset": "custom",
        "mathtext.rm": "Times New Roman",
        "mathtext.it": "Times New Roman:italic",
        "mathtext.bf": "Times New Roman:bold",
        "mathtext.cal": "Times New Roman:italic",
    })
    width, height = spec["dimensions_mm"]["width"] / 25.4, spec["dimensions_mm"]["height"] / 25.4
    fig, ax = plt.subplots(figsize=(width, height), facecolor="white")
    fig.subplots_adjust(left=0.13, right=0.98, bottom=0.20, top=0.80)
    plot_data(ax, df, plot, fonts)
    style_axis(ax, fonts)
    x_label = draw_axis_label(ax, "x", spec["labels"]["x"], fonts)
    y_label = draw_axis_label(ax, "y", spec["labels"]["y"], fonts)
    if spec["legend"] == "auto" and plot.get("group"):
        group_count = df[plot["group"]].nunique(dropna=False)
        legend_labels = ax.get_legend_handles_labels()[1]
        if any(len(text) > 28 for text in legend_labels):
            raise FigureContractError("Legend label exceeds 28 characters; provide a concise plot.display_labels.group mapping")
        legend_font = fonts.songti if any(has_cjk(text) for text in legend_labels) else fonts.times
        if group_count <= 4:
            legend = ax.legend(frameon=False, ncol=2, mode="expand", bbox_to_anchor=(0, 1.02, 1, 0.16), loc="lower left", borderaxespad=0, columnspacing=1.0, handletextpad=0.55, prop=legend_font)
        else:
            legend = ax.legend(frameon=False, bbox_to_anchor=(1.01, 1), loc="upper left", borderaxespad=0, prop=legend_font)
        legend.get_title().set_fontproperties(legend_font)
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = output_dir / spec["name"]
    pdf_path, svg_path, png_path = stem.with_suffix(".pdf"), stem.with_suffix(".svg"), stem.with_suffix(".png")
    with tempfile.TemporaryDirectory(prefix=f".{spec['name']}-", dir=output_dir) as temporary:
        temporary_dir = Path(temporary)
        temporary_pdf = temporary_dir / pdf_path.name
        temporary_svg = temporary_dir / svg_path.name
        temporary_png = temporary_dir / png_path.name
        fig.savefig(temporary_pdf, bbox_inches="tight", transparent=True)
        fig.savefig(temporary_svg, bbox_inches="tight", transparent=True)
        fig.savefig(temporary_png, dpi=600, bbox_inches="tight", transparent=True)
        qa = run_qa(fig, ax, fonts, temporary_pdf, [x_label, y_label], spec["language"])
        temporary_pdf.replace(pdf_path)
        temporary_svg.replace(svg_path)
        temporary_png.replace(png_path)
    provenance = {
        "spec": str(spec_path.resolve()),
        "data": str(data_path),
        "data_sha256": hashlib.sha256(data_path.read_bytes()).hexdigest(),
        "rows_used": int(len(df)),
        "plot": plot,
        "language": spec["language"],
        "dimensions_mm": spec["dimensions_mm"],
        "fonts": {"times_new_roman": str(fonts.times_path), "songti": str(fonts.songti_path)},
        "outputs": {"pdf": str(pdf_path), "svg": str(svg_path), "png": str(png_path)},
    }
    stem.with_suffix(".provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    stem.with_suffix(".qa.json").write_text(json.dumps(qa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    plt.close(fig)
    return {"provenance": provenance, "qa": qa}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", type=Path)
    parser.add_argument("--font-dir", type=Path, action="append", required=True, help="May be provided more than once")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    result = render(args.spec.resolve(), args.font_dir, args.output_dir.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
