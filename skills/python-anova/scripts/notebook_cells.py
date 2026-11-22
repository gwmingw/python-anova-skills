# %% setup
from io import BytesIO
from itertools import combinations

from IPython.display import Image, display
from matplotlib import font_manager
from matplotlib.textpath import TextToPath
import numpy as np
import pandas as pd
from scipy.stats import probplot
from statsmodels.api import stats
from statsmodels.formula.api import ols
from statsmodels.stats.multitest import multipletests

# %% input
data = pd.read_csv(Path(data_csv), encoding=encoding)

# %% fit
response = design['response']
factors = design['factors']
block = design.get('block')
source_columns = [response, *factors, *([block] if block else [])]
missing = set(source_columns) - set(data.columns)
if missing:
    raise ValueError(f'Missing columns: {sorted(missing)}')
if data.empty or data[source_columns].isna().any().any():
    raise ValueError('Selected analysis columns require observations with no missing values.')

# Map original CSV labels to formula-safe names.
factor_ids = [f'factor_{i}' for i in range(1, len(factors) + 1)]
group_ids = factor_ids + (['block_id'] if block else [])
fit_data = data[source_columns].copy()
fit_data.columns = ['y', *group_ids]
fit_data['y'] = pd.to_numeric(fit_data['y'], errors='raise').astype(float)
if not np.isfinite(fit_data['y']).all() or fit_data['y'].nunique() < 2:
    raise ValueError('The response must have finite numeric values and some variation.')
for column in group_ids:
    if fit_data[column].nunique() < 2:
        raise ValueError(f'{source_columns[fit_data.columns.get_loc(column)]!r} needs at least two levels.')
    fit_data[column] = fit_data[column].astype('category')

counts = fit_data.groupby(group_ids, observed=False).size()
if block and not counts.eq(1).all():
    raise ValueError('The fixed-block design needs one observation per block–factor combination.')
if len(factors) == 2 and not block and (counts.min() < 1 or counts.nunique() != 1):
    raise ValueError('The two-way design needs complete cells with equal sample sizes.')

contrast = {'sum': 'Sum', 'treatment': 'Treatment'}[design['contrast']]
factor_terms = [f'C({term}, {contrast})' for term in factor_ids]
interaction = design.get('interaction', False)
formula_rhs = (' * ' if interaction else ' + ').join(factor_terms)
block_term = f'C(block_id, {contrast})'
if block:
    formula_rhs = (f'{block_term} + {formula_rhs}' if design.get('block_first')
                   else f'{formula_rhs} + {block_term}')
model = ols(f'y ~ {formula_rhs}', data=fit_data, missing='raise').fit()
if model.df_resid <= 0 or model.model.rank != model.model.exog.shape[1]:
    raise ValueError('The design requires a full-rank model and positive residual degrees of freedom.')
total_ss = float(model.centered_tss)
if model.ssr <= total_ss * np.finfo(float).eps ** 2 * 16:
    raise ValueError('Residual variation is too small for a meaningful F test.')

response_terms = (' * ' if interaction else ' + ').join(factors)
if block:
    response_terms += f' + {block} (Block)'
print(f'{response} ~ {response_terms}')
print(f'n = {int(model.nobs)} | SS Type {design["ss_type"]} | {contrast} contrasts')
print('Fitted term order:', ', '.join(model.model.data.design_info.term_names))
condition_summary = (
    data.assign(**{response: fit_data['y']})
    .groupby(factors, observed=True)[response]
    .agg(N='size', Mean='mean', SD='std')
)
display(condition_summary)

# %% table
raw_anova = stats.anova_lm(model, typ=design['ss_type'])
term_labels = dict(zip(factor_terms, factors))
if interaction:
    term_labels[':'.join(factor_terms)] = ' × '.join(factors)
if block:
    term_labels[block_term] = f'{block} (Block)'
term_labels['Residual'] = 'Error'
anova_table = raw_anova.loc[list(term_labels)].rename(
    columns={'sum_sq': 'SS', 'mean_sq': 'MS', 'PR(>F)': 'p'}
).copy()
if 'MS' not in anova_table:
    anova_table['MS'] = anova_table['SS'] / anova_table['df']
if not np.isfinite(anova_table.drop(index='Residual')[['F', 'p']].to_numpy()).all():
    raise ValueError('ANOVA returned a non-finite effect test.')
columns = ['SS', 'df', 'MS', 'F', 'p']
anova_table = anova_table[columns]
anova_table.loc['Total'] = [total_ss, model.nobs - 1, np.nan, np.nan, np.nan]
anova_table['df'] = anova_table['df'].astype(int)
anova_table = anova_table.rename(index=term_labels).rename_axis('Source').reset_index()

def format_p(value):
    if value == 0:
        return '< 0.001'
    return f'{value:.3e}' if value < 0.001 else f'{value:.3f}'

def show_png(fig):
    buffer = BytesIO()
    fig.savefig(buffer, format='png', bbox_inches='tight')
    display(Image(data=buffer.getvalue(), format='png'))
    plt.close(fig)

available_fonts = {font.name for font in font_manager.fontManager.ttflist}
has_hangul = any('\uac00' <= char <= '\ud7a3' for label in source_columns for char in label)
has_hangul = has_hangul or any(
    '\uac00' <= char <= '\ud7a3' for column in group_ids
    for level in fit_data[column].cat.categories for char in str(level)
)
font_order = ['Malgun Gothic', 'NanumGothic', 'Noto Sans CJK KR', 'Arial'] if has_hangul else ['Arial']
font_family = next((font for font in font_order if font in available_fonts), 'DejaVu Sans')
apply_style()
plt.rcParams['font.family'] = [font_family, 'DejaVu Sans']
table_header = '#EAF0F5'
table_total = '#F3F6F8'
formats = {'SS': '{:.3f}', 'df': '{:d}', 'MS': '{:.3f}', 'F': '{:.3f}', 'p': format_p}

display(anova_table.style.hide(axis='index').format(formats, na_rep='', escape='html')
        .set_table_attributes('class="dataframe"')
        .set_properties(subset=columns, **{'text-align': 'right', 'white-space': 'nowrap'})
        .set_properties(subset=['Source'], **{'text-align': 'left'}))

formatted = anova_table.copy()
for column, formatter in formats.items():
    format_value = formatter.format if isinstance(formatter, str) else formatter
    formatted[column] = anova_table[column].map(lambda value: '' if pd.isna(value) else format_value(value))
table_font_size = 11
text_metrics = TextToPath()

def label_width(value, weight='normal'):
    font = font_manager.FontProperties(family=plt.rcParams['font.family'],
                                       size=table_font_size, weight=weight)
    return text_metrics.get_text_width_height_descent(value, font, ismath=False)[0]

cell_padding = 0.07
widths = []
for column in formatted:
    body_widths = [label_width(value, 'bold' if i == len(formatted) - 1 else 'normal')
                   for i, value in enumerate(formatted[column])]
    text_width = max(label_width(column, 'bold'), *body_widths)
    widths.append((text_width + 12) / (1 - 2 * cell_padding))
widths = np.array(widths)
fig, ax = plt.subplots(figsize=(max(6.8, widths.sum() / (72 * 0.96)), 0.38 * (len(formatted) + 1)))
fig.subplots_adjust(left=0.02, right=0.98, bottom=0.03, top=0.97)
ax.set_axis_off()
table = ax.table(cellText=formatted.to_numpy(), colLabels=list(formatted),
                 colWidths=widths / widths.sum(), bbox=[0, 0, 1, 1])
table.auto_set_font_size(False)
table.set_fontsize(table_font_size)
for (row, column), cell in table.get_celld().items():
    cell.set_edgecolor(COLORS['grid'])
    cell.set_linewidth(0.6)
    cell.PAD = cell_padding
    text = cell.get_text()
    text.set_color(COLORS['ink'])
    text.set_ha('right' if row > 0 and column > 0 else ('center' if row == 0 else 'left'))
    if row in (0, len(formatted)):
        text.set_fontweight('bold')
        cell.set_facecolor(table_header if row == 0 else table_total)
show_png(fig)

# %% effects
levels = {key: fit_data[key].cat.categories for key in factor_ids}

def label_levels(ax, key):
    labels = [str(level) for level in levels[key]]
    rotate = len(labels) > 6 or max(map(len, labels)) > 14
    ax.set_xticks(range(len(labels)), labels, rotation=35 if rotate else 0,
                  ha='right' if rotate else 'center')

fig, axes = plt.subplots(1, len(factors), squeeze=False, sharey=True,
                         figsize=(5.5 * len(factors), 4), layout='constrained')
for ax, key, factor in zip(axes.flat, factor_ids, factors):
    means = fit_data.groupby(key, observed=True)['y'].mean().reindex(levels[key])
    ax.plot(range(len(means)), means, 'o-', color=COLORS['data'])
    ax.axhline(fit_data['y'].mean(), **REFERENCE_LINE_KW)
    style_axes(ax, x_label=factor)
    label_levels(ax, key)
axes[0, 0].set_ylabel(f'Mean of {response}')
add_caption(fig, 'Main Effects Plot', y=-0.045)
show_png(fig)

if interaction:
    horizontal, series = factor_ids
    means = fit_data.groupby(factor_ids, observed=True)['y'].mean().unstack(series)
    means = means.reindex(index=levels[horizontal], columns=levels[series])
    fig, ax = plt.subplots(figsize=(7, 4.3), layout='constrained')
    ax.set_prop_cycle(color=[COLORS['data'], COLORS['secondary'], *plt.get_cmap('tab10').colors[4:]])
    for level in means:
        ax.plot(range(len(means)), means[level], 'o-', label=str(level))
    label_levels(ax, horizontal)
    style_axes(ax, x_label=factors[0], y_label=f'Mean of {response}')
    ax.legend(title=factors[1], loc='upper left', bbox_to_anchor=(1.02, 1))
    add_caption(fig, 'Interaction Plot', y=-0.045)
    show_png(fig)

# %% diagnostics
fig, (left, right) = plt.subplots(1, 2, figsize=(10, 4), layout='constrained')
left.scatter(model.fittedvalues, model.resid, alpha=0.7, **SCATTER_KW)
left.axhline(0, **REFERENCE_LINE_KW)
left.set_title('Residuals versus Fitted Values')
style_axes(left, x_label='Fitted values', y_label='Residuals')
(theoretical, residuals), (slope, intercept, _) = probplot(model.resid, dist='norm')
right.scatter(theoretical, residuals, alpha=0.7, **SCATTER_KW)
right.plot(theoretical, slope * theoretical + intercept, **REFERENCE_LINE_KW)
right.set_title('Normal Q–Q Plot')
style_axes(right, x_label='Theoretical normal quantiles', y_label='Ordered residuals')
add_caption(fig, 'Residual Diagnostics', y=-0.045)
show_png(fig)

# %% posthoc
option = design.get('posthoc')
if option:
    factor_index = factors.index(option['factor'])
    factor_key = factor_ids[factor_index]
    omnibus_p = raw_anova.at[factor_terms[factor_index], 'PR(>F)']
    alpha = option['alpha']
    method = option['method']
    if method == 'fisher_lsd' and omnibus_p >= alpha:
        print(f'Protected Fisher LSD gate not met: omnibus p = {format_p(omnibus_p)}, alpha = {alpha:g}.')
    else:
        design_matrix = model.model.exog
        marginal_rows = {level: design_matrix[fit_data[factor_key].eq(level)].mean(axis=0)
                         for level in levels[factor_key]}
        pairs = list(combinations(marginal_rows, 2))
        contrasts = np.stack([marginal_rows[a] - marginal_rows[b] for a, b in pairs])
        tests = model.t_test(contrasts)
        p_values = np.atleast_1d(tests.pvalue)
        p_report = multipletests(p_values, alpha=alpha, method='holm')[1] if method == 'holm' else p_values
        confidence_intervals = tests.conf_int(alpha=alpha)
        p_label = 'Holm p' if method == 'holm' else 'Unadjusted p'
        pairwise_table = pd.DataFrame({
            'Level A': [a for a, _ in pairs], 'Level B': [b for _, b in pairs],
            'Difference (A − B)': tests.effect, 'CI lower': confidence_intervals[:, 0],
            'CI upper': confidence_intervals[:, 1], p_label: p_report,
            'Significant': p_report < alpha,
        })
        print(f'{option["factor"]} | {method} | alpha = {alpha:g} | individual confidence intervals')
        if interaction:
            print('Differences average over the other factor.')
        display(pairwise_table.style.hide(axis='index').format(
            {'Difference (A − B)': '{:.3f}', 'CI lower': '{:.3f}', 'CI upper': '{:.3f}',
             p_label: format_p}, escape='html'))
