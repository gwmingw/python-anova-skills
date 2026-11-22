---
name: anova-table-format
description: Format ANOVA results from statsmodels or equivalent ANOVA output as a conventional report table in Python notebooks, DataFrames, Markdown, or images. Use when the user wants an ANOVA summary table, ANOVA 표 정리, or raw anova_lm output formatted for reporting.
---

# ANOVA Table Format

## Table structure

- Use the columns `Source | SS | df | MS | F | p` in that order. `Source` can be a named DataFrame index internally. Expose it once as the first column in the displayed or exported table.
- Order rows as main effects in the study's stated factor order, interactions, any block terms, `Error`, then `Total` when defined. List only terms estimated in the model. Use readable factor names, `A × B` for an interaction, and a label such as `Subject (Block)` for a subject block. For a conventional blocked two-way ANOVA the order is A, B, A × B, Subject (Block), Error, Total. An unblocked two-way ANOVA omits the block row.
- The conventional `Error` row contains SS, df, and MS. The `Total` row contains SS and df. Leave the other cells in those rows blank. Preserve separate error strata or numerator/denominator df when the fitted method reports them, adapting the columns if needed.

## From statsmodels to a numeric table

1. Start from the fitted model's ANOVA result, such as `sm.stats.anova_lm(result, typ=selected_type)`. Use the analysis's selected SS type, contrasts, and tests. When presentation order differs from formula order, reorder the output rows explicitly. Sequential Type I tests can change if the formula's terms are reordered.
2. Copy the raw table. Map `sum_sq` to `SS`, `mean_sq` to `MS` when present, `PR(>F)` to `p`, and `Residual` to `Error`. Map formula terms to source labels. In a conventional ANOVA, compute missing `MS = SS / df` for rows with defined SS and positive df. Preserve the model's F and p. Keep unavailable statistics missing when the method only reports tests, as with statsmodels `AnovaRM`.
3. For conventional unweighted OLS with an intercept, get the actual fitted response from `result.model.endog`. Use `sum((y - y.mean()) ** 2)` for corrected Total SS and `result.nobs - 1` for Total df. This includes only observations used in the fit. For other designs, use the total appropriate to the analysis when defined. Check additivity only for an additive SS decomposition. Adjusted Type II or III sums of squares may fail to add to the corrected total in nonorthogonal designs.
4. Keep full-precision values and numeric missing values in the DataFrame used for analysis. Convert to formatted strings only at display or export time.

## Notebook display and table images

- Format integer df without decimal places. Use three decimals for SS, MS, F, and ordinary p-values by default. Use scientific notation for positive p-values below 0.001 (e.g. `1.897e-13`), or the user's requested threshold notation. When the software reports zero due to numerical underflow, use an inequality such as `< 0.001`. Keep minus signs in exponents and omit thousands separators.
- Display missing cells as empty strings at the formatting layer, e.g. `na_rep=""` for pandas Styler. Keep actual zero-valued statistics visible. Right-align the body entries of SS, df, MS, F, and p, including numbers in the Total row. For a Matplotlib table, apply right alignment to the numeric body cells (`row > 0`, `column > 0` when Source is first and the header is row 0).
- Use the same numeric table, labels, order, and formatting rules for the notebook and image. Render table images directly from the formatted data. Choose fonts, colors, borders, captions, and column widths to suit the destination. Check the rendered header order, numeric alignment, empty cells, and displayed values against the DataFrame.
