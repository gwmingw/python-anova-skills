"""Inspect a CSV or create and execute an ANOVA notebook."""

import argparse
import csv
import json
import os
from pathlib import Path
from pprint import pformat
import re
from tempfile import TemporaryDirectory


def check_csv_header(path, encoding):
    with path.open(encoding=encoding, newline='') as file:
        header = next(csv.reader(file), [])
    if not header or any(not column.strip() for column in header) or len(set(header)) != len(header):
        raise ValueError('The CSV needs a nonempty header with distinct column names.')


def inspect_data(path, encoding):
    import pandas as pd

    frame = pd.read_csv(path, encoding=encoding)
    metadata = []
    for column, values in frame.items():
        unique = int(values.nunique())
        details = {'column': column, 'dtype': str(values.dtype),
                   'missing': int(values.isna().sum()), 'unique': unique}
        if 0 < unique <= 12:
            details['counts'] = {str(key): int(count) for key, count in values.value_counts().items()}
        metadata.append(details)
    print(json.dumps({'rows': len(frame), 'columns': metadata}, ensure_ascii=False, indent=2))


def read_design(path):
    design = json.loads(path.read_text(encoding='utf-8-sig'))
    required = {'response', 'factors'}
    allowed = required | {'interaction', 'block', 'block_first', 'ss_type', 'contrast', 'posthoc'}
    if not isinstance(design, dict) or not required <= design.keys() <= allowed:
        raise ValueError('Design must provide response and factors. See the runner interface for optional keys.')
    factors = design['factors']
    if not isinstance(factors, list) or len(factors) not in (1, 2):
        raise ValueError('Provide a list with one or two factor column names.')
    block = design.get('block')
    names = [design['response'], *factors] + ([block] if block is not None else [])
    if not all(isinstance(name, str) and name.strip() for name in names) or len(set(names)) != len(names):
        raise ValueError('Response, factors, and block must name different columns.')
    if len(factors) == 2 and 'interaction' not in design:
        raise ValueError('Specify interaction as true or false for a two-factor design.')
    if any(type(design.get(key, False)) is not bool for key in ('interaction', 'block_first')):
        raise ValueError('interaction and block_first must be Boolean.')
    if len(factors) == 1 and (block is not None or design.get('interaction')):
        raise ValueError('This runner supports fixed blocks and interactions with two factors.')
    if design.get('block_first') and block is None:
        raise ValueError('block_first requires a fixed block.')
    ss_type = design.setdefault('ss_type', 2)
    if type(ss_type) is not int or ss_type not in (1, 2, 3):
        raise ValueError('ss_type must be 1, 2, or 3.')
    if design.setdefault('contrast', 'sum') not in ('sum', 'treatment'):
        raise ValueError('contrast must be sum or treatment.')
    posthoc = design.get('posthoc')
    if posthoc is not None:
        if not isinstance(posthoc, dict) or not {'factor', 'method'} <= posthoc.keys() <= {'factor', 'method', 'alpha'}:
            raise ValueError('Post hoc settings require factor and method, with optional alpha.')
        if posthoc['factor'] not in factors or posthoc['method'] not in ('fisher_lsd', 'holm'):
            raise ValueError('Post hoc comparisons need a specified factor and fisher_lsd or holm.')
        alpha = posthoc.setdefault('alpha', 0.05)
        if type(alpha) not in (int, float) or not 0 < alpha < 1:
            raise ValueError('Post hoc alpha must lie between zero and one.')
    return design


def make_notebook(args, design, output):
    import nbformat as nbf

    template = Path(__file__).with_name('notebook_cells.py').read_text(encoding='utf-8')
    parts = re.split(r'^# %% (\w+)\s*$', template, flags=re.MULTILINE)
    sections = {key: source.strip() for key, source in zip(parts[1::2], parts[2::2])}
    shared_style = Path(__file__).resolve().parents[2] / 'report-plot-style' / 'scripts' / 'report_plot_style.py'
    if not shared_style.is_file():
        raise FileNotFoundError('Install report-plot-style alongside python-anova to generate a notebook.')
    setup = shared_style.read_text(encoding='utf-8-sig').strip() + '\n\n' + sections['setup']
    try:
        data_path = os.path.relpath(args.data.resolve(strict=True), start=output.parent)
    except ValueError:
        data_path = str(args.data.resolve(strict=True))
    parameters = (f'data_csv = {Path(data_path).as_posix()!r}\n'
                  f'encoding = {args.encoding!r}\n'
                  f'design = {pformat(design, sort_dicts=False)}')
    headings = {
        'ko': ('입력 및 분석 설정', '데이터 불러오기', '실험 데이터 전처리', '입력 검증 및 모형 적합',
               '분산분석표', '주효과 및 교호작용 그래프', '잔차 진단', '사후비교'),
        'en': ('Input and Analysis Settings', 'Load Data', 'Study-Specific Preprocessing',
               'Validate Input and Fit the Model', 'ANOVA Table', 'Effect Plots', 'Residual Diagnostics',
               'Post Hoc Comparisons'),
    }[args.lang]
    introduction = {
        'ko': '설정 셀에서 CSV 위치와 모형을 확인할 수 있습니다. 원본 CSV와 동일한 열 구조를 사용해 전체 셀을 다시 실행할 수 있습니다.',
        'en': 'The settings cell records the CSV location and model. Run all cells again with the original CSV or a CSV with the same columns.',
    }[args.lang]
    sequence = [('settings', parameters), ('input', sections['input'])]
    if args.preprocess:
        sequence.append(('preprocess', args.preprocess.read_text(encoding='utf-8-sig').strip()))
    sequence.extend((key, sections[key]) for key in ('fit', 'table', 'effects', 'diagnostics'))
    if design.get('posthoc'):
        sequence.append(('posthoc', sections['posthoc']))
    heading_by_section = dict(zip(
        ('settings', 'input', 'preprocess', 'fit', 'table', 'effects', 'diagnostics', 'posthoc'), headings
    ))
    cells = [nbf.v4.new_markdown_cell(f'# Python ANOVA\n\n{introduction}'),
             nbf.v4.new_code_cell(setup)]
    for number, (key, code) in enumerate(sequence, start=1):
        cells.append(nbf.v4.new_markdown_cell(f'## {number}. {heading_by_section[key]}'))
        cells.append(nbf.v4.new_code_cell(code, metadata={'tags': [key]}))
    return nbf.v4.new_notebook(cells=cells, metadata={
        'kernelspec': {'name': 'python3', 'language': 'python', 'display_name': 'Python 3'},
        'language_info': {'name': 'python'},
    })


def run_notebook(args):
    import nbformat as nbf
    from IPython.core.interactiveshell import InteractiveShell
    from IPython.utils.capture import capture_output
    from traitlets.config import Config

    output = args.output.resolve()
    if output.suffix.lower() != '.ipynb' or not output.parent.is_dir():
        raise ValueError('Use an .ipynb output path in an existing directory.')
    if output.exists():
        raise FileExistsError(f'Choose a new notebook path: {output}')
    design = read_design(args.design)
    notebook = make_notebook(args, design, output)
    os.environ['MPLBACKEND'] = 'Agg'
    previous_directory = Path.cwd()
    with TemporaryDirectory(prefix='python-anova-') as profile:
        config = Config({'HistoryManager': {'enabled': False}})
        shell = InteractiveShell.instance(ipython_dir=profile, config=config)
        try:
            os.chdir(output.parent)
            code_cells = (cell for cell in notebook.cells if cell.cell_type == 'code')
            for number, cell in enumerate(code_cells, start=1):
                with capture_output() as capture:
                    result = shell.run_cell(cell.source, store_history=False, silent=False)
                if not result.success:
                    section = ', '.join(cell.metadata.get('tags', ['setup']))
                    raise RuntimeError(f'Notebook cell {number} ({section}) failed.') from (
                        result.error_before_exec or result.error_in_exec
                    )
                cell.execution_count = number
                for stream in ('stdout', 'stderr'):
                    if content := getattr(capture, stream):
                        cell.outputs.append(nbf.v4.new_output('stream', name=stream, text=content))
                for item in capture.outputs:
                    cell.outputs.append(nbf.v4.new_output('display_data', data=item.data,
                                                           metadata=item.metadata))
        finally:
            os.chdir(previous_directory)
    nbf.validate(notebook)
    payload = nbf.writes(notebook) + '\n'
    with output.open('x', encoding='utf-8', newline='\n') as file:
        file.write(payload)
    print(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    inspect = commands.add_parser('inspect', help='Read column names, types and counts.')
    run = commands.add_parser('run', help='Create and execute one notebook.')
    for command in (inspect, run):
        command.add_argument('data', type=Path)
        command.add_argument('--encoding', default='utf-8-sig')
    run.add_argument('design', type=Path)
    run.add_argument('output', type=Path)
    run.add_argument('--lang', choices=('ko', 'en'), default='ko')
    run.add_argument('--preprocess', type=Path, help='A trusted Python file to insert after CSV loading.')
    args = parser.parse_args()
    check_csv_header(args.data, args.encoding)
    if args.command == 'inspect':
        inspect_data(args.data, args.encoding)
    else:
        run_notebook(args)


if __name__ == '__main__':
    main()
