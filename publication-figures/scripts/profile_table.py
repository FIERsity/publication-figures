#!/usr/bin/env python3
"""Profile a CSV, TSV, Excel, or Parquet table for plotting decisions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def read_table(path: Path, sheet: str | None) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".tsv", ".tab"}:
        return pd.read_csv(path, sep="\t")
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path, sheet_name=sheet or 0)
    if suffix == ".parquet":
        return pd.read_parquet(path)
    raise ValueError("Supported inputs: .csv, .tsv, .tab, .xlsx, .xls, .parquet")


def summarize(df: pd.DataFrame, source: Path) -> dict:
    columns = []
    for name in df.columns:
        series = df[name]
        item = {
            "name": str(name),
            "dtype": str(series.dtype),
            "missing": int(series.isna().sum()),
            "unique": int(series.nunique(dropna=True)),
        }
        if pd.api.types.is_numeric_dtype(series):
            nonnull = series.dropna()
            item["numeric_summary"] = {
                "min": float(nonnull.min()) if len(nonnull) else None,
                "max": float(nonnull.max()) if len(nonnull) else None,
                "mean": float(nonnull.mean()) if len(nonnull) else None,
                "median": float(nonnull.median()) if len(nonnull) else None,
            }
        else:
            item["examples"] = [str(value) for value in series.dropna().unique()[:5]]
        columns.append(item)
    return {"source": str(source), "rows": int(len(df)), "columns": columns}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--sheet", help="Excel sheet name; default is the first sheet")
    parser.add_argument("--output", type=Path, help="Write JSON profile to this path")
    args = parser.parse_args()
    profile = summarize(read_table(args.input, args.sheet), args.input)
    payload = json.dumps(profile, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
