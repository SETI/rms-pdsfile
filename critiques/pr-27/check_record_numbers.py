"""Check every reproducible number in PR-27's records against the tree.

Four review rounds each found at least one number in a record that a later edit had
invalidated -- a `wc -l` table taken before the commit that changed a module, a
per-cause table that had drifted from the enumeration explaining it, a duplication
figure restated after the function it measures had moved. The code had five gates
and the record had none. This is the record's gate.

Run from the repository root with the tree's own interpreter, which must be 3.11 or
newer -- this reads pyproject.toml through tomllib. The package itself supports 3.10,
so this is a constraint on running the check, not on the tree it checks:

    python critiques/pr-27/check_record_numbers.py

It prints one line per number that does not reproduce, and exits 1 if any does not.
"""

import ast
import difflib
import pathlib
import re
import subprocess
import sys

import tomllib

HOLDINGS = 'src/pdsfile/holdings_maintenance/'

# The modules PR-27's line-count table covers, plus the one it names as the module
# still over the 1,000-line limit.
MODULES = ('_common.py', '_archives_common.py', '_shelf_common.py',
           '_indexshelf_common.py', '_linkshelf_common.py',
           'pds3/pdsindexshelf.py', 'pds4/pds4indexshelf.py',
           'pds3/pdslinkshelf.py', 'pds4/pds4linkshelf.py',
           'pds3/linkshelf_repairs.py', 'pds3/pdsdependency.py')

# What each module measured at the PR's base, for the table's left column.
BASE = {'_common.py': 337, '_archives_common.py': 242, '_shelf_common.py': 539,
        'pds3/pdsindexshelf.py': 548, 'pds4/pds4indexshelf.py': 538,
        'pds3/pdslinkshelf.py': 1730, 'pds4/pds4linkshelf.py': 1224}

# The two pairs' base line counts, which the rate is a fraction of.
INDEX_PAIR = 1086
LINK_PAIR = 2954
REPAIRS_LINES = 536
PROJECTION = 748           # deferred entry 98's rate applied to these two pairs


def lines(path):
    return len(pathlib.Path(path).read_text(encoding='utf-8').splitlines())


def function_body(path, name):
    """Return one function's lines, without its docstring, `def` line or blanks."""

    src = pathlib.Path(path).read_text(encoding='utf-8').splitlines()
    node = next(n for n in ast.parse('\n'.join(src)).body
                if isinstance(n, ast.FunctionDef) and n.name == name)
    body = src[node.lineno - 1:node.end_lineno]
    if ast.get_docstring(node, clean=False) is not None:
        first = node.body[0]
        drop = set(range(first.lineno - node.lineno, first.end_lineno - node.lineno + 1))
        body = [ln for i, ln in enumerate(body) if i not in drop]

    return [ln for ln in body[1:] if ln.strip()]


def identical_with(reference, other):
    """Return how many of two functions' lines are line-identical."""

    matcher = difflib.SequenceMatcher(None, reference, other, autojunk=False)

    return sum(block.size for block in matcher.get_matching_blocks())


def main():
    record = pathlib.Path('critiques/pr-27-validation.md').read_text(encoding='utf-8')
    plan = pathlib.Path('plans/2026-07-25-modernization-plan.md').read_text(
        encoding='utf-8')
    deferred = pathlib.Path('critiques/deferred-observations.md').read_text(
        encoding='utf-8')

    missing = []

    def expect(where, text, needle):
        if needle not in text:
            missing.append((where, needle))

    measured = {name: lines(HOLDINGS + name) for name in MODULES}

    # The line-count table, and the two totals derived from it.
    for name, base in BASE.items():
        expect('table', record, f'| `{name}` | {base:,} | {measured[name]} |')
    for name in ('_indexshelf_common.py', '_linkshelf_common.py',
                 'pds3/linkshelf_repairs.py'):
        expect('table', record, f'| `{name}` | — | {measured[name]} |')

    total = sum(v for k, v in measured.items() if k != 'pds3/pdsdependency.py')
    expect('table total', record, f'| **total** | **5,158** | **{total:,}** |')

    tools = sum(measured[k] for k in ('pds3/pdsindexshelf.py', 'pds4/pds4indexshelf.py',
                                      'pds3/pdslinkshelf.py', 'pds4/pds4linkshelf.py'))
    expect('four tools', record, f'from 4,040 lines to {tools:,}.')
    expect('four tools', plan, f'from 4,040 lines to {tools:,}.')
    expect('over the limit', record,
           f"`pds3/pdsdependency.py`, {measured['pds3/pdsdependency.py']:,} lines")

    # The shared-code figure, the rate, and everything derived from them.
    index_shared = measured['_indexshelf_common.py']
    link_shared = measured['_linkshelf_common.py']
    shared = index_shared + link_shared
    expect('shared', record, f'**{shared:,}** — the projection is short by '
                             f'{shared - PROJECTION} lines')
    expect('shared', plan, f'the measurement is {shared:,} — the')
    expect('shared', deferred, f'the measurement is {shared:,},')
    expect('rate', record, f'| PR-27 (indexshelf + linkshelf) | 4,040 | {shared:,} | '
                           f'{100 * shared / (INDEX_PAIR + LINK_PAIR):.1f}% |')
    expect('index rate', record, f'({100 * index_shared / INDEX_PAIR:.1f}% of its '
                                 f'{INDEX_PAIR:,} lines')
    expect('link rate', record, f'({100 * link_shared / LINK_PAIR:.1f}% of {LINK_PAIR:,}')
    expect('link rate', record,
           f'{100 * link_shared / (LINK_PAIR - REPAIRS_LINES):.1f}% with the `REPAIRS`')

    # The split: what one module would have been, and what the parts are.
    expect('split', record, f"523 + {index_shared} + {link_shared} =")
    for name in ('_common.py', '_indexshelf_common.py', '_linkshelf_common.py'):
        expect('wc block', record, f'   {measured[name]} {name}')
    expect('entry 66', deferred, f'({link_shared}) and the 536-line')
    expect('entry 114', deferred, f'`_indexshelf_common.py` {index_shared},')
    expect('entry 114', deferred, f'`_linkshelf_common.py` {link_shared}.')
    expect('plan split', plan, f'`_indexshelf_common.py` ({index_shared}), '
                               f'`_linkshelf_common.py` ({link_shared}).')

    # The ratchet.
    config = tomllib.loads(pathlib.Path('pyproject.toml').read_text(encoding='utf-8'))
    ignores = config['tool']['ruff']['lint']['per-file-ignores']
    expect('ratchet', record, f'| entries | 69 | {len(ignores)} |')
    expect('ratchet', record,
           f'| code slots | 184 | {sum(len(v) for v in ignores.values())} |')
    findings = subprocess.run([sys.executable, '-m', 'ruff', 'check', '--config',
                               'lint.per-file-ignores = {}',
                               'src/pdsfile', 'tests', 'scripts'],
                              capture_output=True, text=True, check=False).stdout
    count = int(re.search(r'Found (\d+) errors', findings).group(1))
    expect('ratchet', record,
           f'| findings with the ignores disabled | 2,271 | {count:,} |')

    # The two driver duplication measurements, which justify the third driver.
    reference = function_body(HOLDINGS + '_common.py', 'run_main')
    for name, path in (('run_index_main', HOLDINGS + '_indexshelf_common.py'),
                       ('run_selection_main', HOLDINGS + '_shelf_common.py')):
        other = function_body(path, name)
        same = identical_with(reference, other)
        expect(name, record, f'{len(reference)} lines, {name} {len(other)} lines')
        expect(name, record,
               f'{same} line-identical = {100 * same / len(other):.0f}% of {name}')
        if name == 'run_index_main':
            expect(name, deferred,
                   f"`run_main`'s {len(reference)}, with {same} line-identical")

    for where, needle in missing:
        print(f'DOES NOT REPRODUCE  [{where}]  {needle}')
    print(f'{len(missing)} number(s) do not reproduce')

    return 1 if missing else 0


if __name__ == '__main__':
    sys.exit(main())
