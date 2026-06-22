# Figure specification

Write a YAML document. Paths may be absolute or relative to the specification file.

```yaml
name: recovery_curve
data: /absolute/path/to/data.csv
plot:
  kind: line                 # scatter | line | point_summary | box | violin
  x: k
  y: recovery_fraction
  group: benchmark_tier      # optional; required for multi-series line/scatter
labels:
  x: "排名阈值"
  y:
    - text: "召回率 "
      role: chinese
    - text: "(fraction)"
      role: latin
language: zh
dimensions_mm:
  width: 85
  height: 62
legend: auto                 # auto | none
```

## Rules

- Do not include `title` anywhere in the document.
- `kind: point_summary` uses the mean plus a 95% bootstrap confidence interval and keeps raw observations.
- Use a single-string label only when it belongs entirely to one font role. Use a sequence of `{text, role}` segments for Chinese-plus-English x or y labels; `role` is `chinese` or `latin`.
- Use Unicode directly for common symbols and indices, for example `μM`, `m²`, `CO₂`. Use MathText only inside `$...$` and only for expressions supported by Matplotlib MathText.
- Treat `^` and `_` as scientific-markup candidates. The renderer automatically converts unambiguous numeric forms such as `IC_50`, `m^2`, and `SO_4^{2-}`. Use `$...$` for more complex MathText. An underscore or caret followed by letters is ambiguous and fails unless `plot.display_labels` maps that raw category or group to a reviewed display label.
- Use `plot.display_labels.x` and `plot.display_labels.group` to replace machine identifiers before they reach tick labels or legends. This is mandatory for labels such as `random_split` or `expert_cytotox_strong`.
- Keep every legend label to 28 characters or fewer. The renderer rejects longer labels to prevent a visually unbalanced figure; define a concise group display label and explain its full wording in the caption.
- `legend: auto` is rendered outside the axes; `legend: none` suppresses it.
