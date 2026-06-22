# Figure selection

## Start with the evidence

| Data relationship | Preferred display | Required checks |
| --- | --- | --- |
| Continuous outcome versus continuous predictor | Scatter; optionally a model fit and interval | One dot per unit, missingness, nonlinear structure, repeated measures |
| Outcome across ordered time or dose | Line plus point/ribbon | Ordering is genuine, repeated units are identifiable, uncertainty is visible |
| Outcome across unordered groups | Raw points plus box, violin, or interval | Show observations when feasible; state the estimator and uncertainty |
| Composition across a whole | Stacked bar only when parts sum to a meaningful whole | Constant denominator, readable ordering, avoid comparison of non-baseline segments |
| Matrix of comparable measurements | Heatmap with explicit scale and clustering policy | Missing values, color scale, row/column ordering and normalization |

## Default publication choices

- Plot raw observations for samples up to a visually manageable count. Overlay a clearly defined summary rather than replacing the observations.
- Use a color-blind-safe categorical palette such as Okabe-Ito. Do not encode groups with red versus green alone.
- State whether error bars are SD, SEM, CI, bootstrap CI, or another quantity; do not use unlabeled error bars.
- Label axes with measured quantity and units. Prefer direct labels or a compact legend.
- Use a zero baseline for bars. For other plot types, use a focused axis range only if it does not mislead and the range is visible.

## Statistical claims

A plotting task is not authorization to run a hypothesis test. Before adding p-values, establish the analysis unit, independent groups versus paired/repeated data, pre-specified comparison set, distributional assumptions, and multiple-comparison policy. Report effect sizes and uncertainty where suitable.
