# Runner interface

Use a Python environment with `numpy`, `pandas`, `scipy`, `statsmodels`, `matplotlib`, `ipython`, `nbformat`, and `jinja2`. The runner executes the generated code cells with IPython and saves the rich outputs with Python 3 kernel metadata. To rerun the notebook interactively, select a Jupyter kernel with the analysis dependencies installed.

```text
python scripts/run_anova.py inspect data.csv
python scripts/run_anova.py run data.csv design.json analysis.ipynb --lang ko
```

The output directory must exist. Select a new `.ipynb` path. The completed notebook refers to the analysis CSV relative to its own directory when accessible on the same drive.

Install `report-plot-style` alongside `python-anova` in the same skills directory. At notebook generation, the runner includes the shared Matplotlib helper in the setup cell. The notebook can run with its CSV and Python packages independently of the skills directory.

`design.json` specifies the original column names. Each row of the CSV represents the agreed analysis unit. Example:

```json
{
  "response": "absolute_error_pct_mvc",
  "factors": ["tested_hand", "target_pct_mvc"],
  "interaction": true,
  "block": "subject_id",
  "ss_type": 2,
  "contrast": "sum",
  "posthoc": {"factor": "target_pct_mvc", "method": "fisher_lsd", "alpha": 0.05}
}
```

- `response` and `factors` are required. Use one or two factors in the requested reporting order. Specify `interaction` for two factors. A fixed `block` is optional with two factors. Omit the block key for unblocked designs.
- Specify `ss_type` as `1`, `2`, or `3` and `contrast` as `sum` or `treatment`. Defaults are `2` and `sum`. Use `block_first: true` if the supplied model puts its block term first, which can matter for a sequential Type I analysis. For supplied formulas, use this runner only when it can preserve the requested factor coding, references, and tested terms.
- Omit `posthoc` for no pairwise tests. `holm` adjusts the family of pairwise p-values for a selected main effect. `fisher_lsd` uses the selected omnibus effect as a gate and reports unadjusted pairwise p-values. Both use estimated marginal means from the fit and the model's pooled error. In supported balanced two-way designs the means average equally across the other factor and any blocks. When the research question concerns an interaction, specify a suitable simple-effect comparison separately.
- `--encoding` defaults to `utf-8-sig`. `--lang` can be `ko` or `en` and defaults to `ko`. The runner reports missing inputs and structural problems before exporting a completed notebook. Use the estimated model and design diagnostics to interpret results.
- For study-specific preparation, pass `--preprocess path/to/preparation.py` with trusted Python you wrote and reviewed. The cell receives the CSV as `data` and assigns the analysis-ready DataFrame back to `data`. Use the prepared column names in the design JSON. The prep code becomes part of the notebook and runs before model validation.
