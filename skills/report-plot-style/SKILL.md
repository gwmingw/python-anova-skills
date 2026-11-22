---
name: report-plot-style
description: "Create or restyle Python/Matplotlib report figures using the user's established Arial, blue-marker, light-grid, bottom-caption style. Use for Python plotting requests and report charts that should keep this visual style; a user's explicit alternative style takes precedence."
---

# Report Plot Style

Keep the user's report figures visually consistent with their mean-accuracy scatterplot and vertically stacked Numbers/Letters regression plots. This skill supplies appearance, not a particular dataset or statistical model.

## Default visual style

- White figure, axes, and export backgrounds. Arial, 11 pt; fall back to DejaVu Sans if Arial is unavailable. Reapply the style after any library theme that would override it.
- Text/labels: `#263746`; tick text: `#647482`; grid and visible spines: `#DCE3E8`.
- Primary data: `#4C78A8`. Additional series, only when needed: green `#54A28B`; threshold/reference accent: `#C7774E`. Keep dataset-to-color mappings consistent across panels.
- Scatter markers: filled circles, area 49 pt². Fitted curves: same series color, linewidth 2, dotted. Use connecting lines only when the plot calls for them.
- Light solid horizontal AND vertical major grid lines, linewidth 0.8, behind data. Hide top/right spines; left/bottom spines match the grid. No tick marks; tick-label padding 7 pt; axis-label padding 9 pt.
- Panel titles: 13 pt bold, padding 13 pt. Legends: 9 pt, no frame, positioned away from observations and annotations. Do not add a legend for a single self-explanatory series.
- Point labels: 9 pt, typically 9 pt above the point. Equation/statistic text: 10 pt, dark ink, with a small borderless white backing if needed. Include labels and model summaries when useful for the requested plot, not by default on every chart.
- Bottom caption: centered, 12 pt bold, with sufficient space below the x labels. Preserve supplied figure numbers and wording; do not invent numbering. Treat a document-supplied caption as authoritative.
- Export PNG at 300 dpi with a white background and `bbox_inches="tight"`. Provide another format only when useful or requested.

## Reusable implementation

Use [scripts/report_plot_style.py](scripts/report_plot_style.py) for palette constants, style setup, axes formatting, layout presets, captions, and export. Load it from this skill directory with `importlib`, or copy it beside a deliverable script and import it normally.

For a standalone notebook, include the relevant style constants and small helper definitions in its common setup cell. Do not make delivered code depend on an absolute path in this skill installation. Do not force the Agg backend in a notebook; for batch rendering, select a headless backend before importing pyplot or through the process environment.

The helper exposes:

```python
apply_style()
fig, ax = make_figure("single")
ax.scatter(x, y, **SCATTER_KW)
style_axes(ax, x_label="List length", y_label="Accuracy (%)",
           percent_axis="y", percent_xmax=100)
# Set data-appropriate limits and ticks separately.
add_caption(fig, caption, layout="single")
save_figure(fig, output_path)
```

`make_figure("horizontal")` returns a 1×2 layout; `make_figure("vertical")` returns a 2×1 layout. Pass `sharex`/`sharey` when panels use comparable scales. Set the requested panel order explicitly. Use `show_x_tick_labels=True` when both vertically stacked panels should display x tick labels.

Starting layout presets, adjustable for label/caption length:

| Layout | Figure size (inches) | Margins and spacing |
| --- | --- | --- |
| Single | 9 × 5.8 | left .12, right .98, top .92, bottom .22; caption y .055 |
| 1×2 | 14 × 5.8 | left .07, right .98, top .88, bottom .22, wspace .18; caption y .055 |
| 2×1 | 9 × 10.8 | left .12, right .98, top .94, bottom .12, hspace .38; caption y .035 |

## Adapt to the requested data

- Keep the user's data, requested graph type, and analysis unchanged when restyling. Do not add a regression, threshold, or STM interpretation merely because the reference plots had them.
- Choose limits, ticks, precision, units, and plot size from the current task. Do not carry over list lengths 4–9, a 50% threshold, or a 0–110 y range into unrelated plots.
- Use percentage formatting only for percentage data. Explicitly set `percent_xmax=100` for 0–100 values or `percent_xmax=1` for proportions. Do not also multiply the displayed values.
- When fitting a requested model, preserve the actual predictions; do not clip a curve to change its apparent fit. For a constant response, label R² undefined when SST is zero and do not manufacture a threshold crossing from numerical round-off.
- Preserve meaningful comparisons: share axes when units and ranges are comparable, and use a consistent palette across related figures. Respect an explicitly requested alternative style or layout.

## Finish

Run the plotting code and visually inspect the saved figure for clipped labels, covered observations, and caption/legend overlap. Adjust spacing rather than the data. For an `.ipynb` deliverable, execute its code cells and include the figure outputs. Save files in the requested folder and provide links to the code and images.
