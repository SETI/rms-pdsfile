"""Check every reproducible number in PR-28's records against the tree.

The two PRs before this one each lost a review round to a number that a later edit
had invalidated rather than to anything wrong in the code, so PR-27 built this gate
and PR-28 wrote its own before writing its record. It re-derives the numbers in
`critiques/pr-28-validation.md`, in PR-28's entries in
`critiques/deferred-observations.md`, and in the plan's PR-28 entry, and it fails if
any of them no longer reproduces.

Every needle is matched against the document with all runs of whitespace collapsed
to one space, so a number that reads correctly but happens to sit across a line
break still matches.

What it cannot check: numbers that come from running something rather than from
reading the tree -- the suite id counts, the transcript record counts, the
`run-all-checks` pass counts. Those carry their command lines in the record instead.
It does check that every test id the record names exists, and that the one it says
was removed does not, which is the part of a suite claim the tree can answer.

Run from the repository root with the tree's own interpreter, which must be 3.11 or
newer -- this reads pyproject.toml through tomllib. The package itself supports 3.10,
so this is a constraint on running the check, not on the tree it checks:

    python critiques/pr-28/check_record_numbers.py

It prints one line per number that does not reproduce, and exits 1 if any does not.
"""

import ast
import difflib
import pathlib
import re
import subprocess
import sys

import tomllib

BASE = '3d044b2'                # the commit this PR branched from

# The files whose line counts the record's section 1 table carries, base and head.
COUNTED = (
    'src/pdsfile/holdings_maintenance/pds3/crlf.py',
    'src/pdsfile/holdings_maintenance/pds3/shelf_consistency_check.py',
    'src/pdsfile/tools/show_opus_products.py',
    'tests/holdings_maintenance/support.py',
    'tests/holdings_maintenance/test_crlf.py',
    'tests/holdings_maintenance/test_shelf_consistency_check.py',
    'tests/holdings_maintenance/test_show_opus_products.py',
)

DRIVERS = (
    ('run_main', 'src/pdsfile/holdings_maintenance/_common.py'),
    ('run_selection_main', 'src/pdsfile/holdings_maintenance/_shelf_common.py'),
    ('run_index_main', 'src/pdsfile/holdings_maintenance/_indexshelf_common.py'),
)

QUALIFIED = {'run_main': '_common.run_main',
             'run_selection_main': '_shelf_common.run_selection_main',
             'run_index_main': '_indexshelf_common.run_index_main'}

# The test ids the record says this PR added, and the one it says it removed.
ADDED = {
    'tests/holdings_maintenance/test_crlf.py': (
        'test_only_invalid_files_are_listed',
        'test_verbose_lists_every_file',
        'test_repair_rewrites_the_file_and_reports_it',
        'test_a_single_file_gets_no_summary_line',
        'test_two_repairs_print_no_summary_at_all',
        'test_flags_are_accepted_among_the_paths',
        'test_no_arguments_prints_nothing',
        'test_help_names_every_flag',
        'test_an_unrecognized_flag_is_a_usage_error',
        'test_an_unreadable_file_raises_rather_than_being_reported',
        'test_the_module_is_runnable_as_python_m',
    ),
    'tests/holdings_maintenance/test_shelf_consistency_check.py': (
        'test_an_index_shelf_whose_label_exists_is_counted_not_reported',
        'test_an_extraneous_index_shelf_is_counted_like_any_other',
        'test_no_arguments_reports_an_empty_run',
        'test_verbose_is_accepted_after_the_shelf_roots',
        'test_an_unrecognized_flag_is_a_usage_error',
        'test_the_module_is_runnable_as_python_m',
    ),
    'tests/holdings_maintenance/test_show_opus_products.py': (
        'test_the_parser_is_built_without_touching_the_environment',
        'test_the_module_imports_with_neither_holdings_root_set',
    ),
}
REMOVED = 'test_an_extraneous_index_shelf_raises'

MIGRATED = ('src/pdsfile/holdings_maintenance/pds3/crlf.py',
            'src/pdsfile/holdings_maintenance/pds3/shelf_consistency_check.py')


def squash(text):
    """Collapse every run of whitespace to one space, so wrapping cannot matter."""

    return re.sub(r'\s+', ' ', text)


def lines(path):
    return len(pathlib.Path(path).read_text(encoding='utf-8').splitlines())


def base_lines(path):
    """Return a file's line count at the PR's base commit."""

    out = subprocess.run(['git', 'show', f'{BASE}:{path}'], capture_output=True,
                         check=True)

    return len(out.stdout.decode('utf-8').splitlines())


def function_body(path, name, *, drop_comments=False, strip_qualifier=False):
    """Return one function's lines, without its docstring, `def` line or blanks."""

    src = pathlib.Path(path).read_text(encoding='utf-8').splitlines()
    node = next(n for n in ast.parse('\n'.join(src)).body
                if isinstance(n, ast.FunctionDef) and n.name == name)
    body = src[node.lineno - 1:node.end_lineno]
    if ast.get_docstring(node, clean=False) is not None:
        first = node.body[0]
        drop = set(range(first.lineno - node.lineno, first.end_lineno - node.lineno + 1))
        body = [ln for i, ln in enumerate(body) if i not in drop]

    body = [ln for ln in body[1:] if ln.strip()]
    if drop_comments:
        body = [ln for ln in body if not ln.strip().startswith('#')]
    if strip_qualifier:
        body = [re.sub(r'\b_common\.', '', ln) for ln in body]

    return body


def identical_with(reference, other):
    """Return how many of two functions' lines are line-identical."""

    matcher = difflib.SequenceMatcher(None, reference, other, autojunk=False)

    return sum(block.size for block in matcher.get_matching_blocks())


def common_subsequence(first, second):
    """Return the lines of `first` that an ordered match with `second` keeps."""

    matcher = difflib.SequenceMatcher(None, first, second, autojunk=False)
    out = []
    for block in matcher.get_matching_blocks():
        out.extend(first[block.a:block.a + block.size])

    return out


def leading_identical(sequences):
    """Return the length of the longest identical leading run of every sequence."""

    n = 0
    while all(n < len(s) for s in sequences) and len({s[n] for s in sequences}) == 1:
        n += 1

    return n


def ruff_findings():
    """Return the finding count with the ratchet emptied, or None if ruff is absent."""

    try:
        out = subprocess.run(['ruff', 'check',
                              '--config', 'lint.per-file-ignores = {}',
                              'src/pdsfile', 'tests', 'scripts'],
                             capture_output=True, check=False)
    except FileNotFoundError:
        return None

    found = re.search(r'Found (\d+) errors?\.', out.stdout.decode('utf-8'))

    return None if found is None else int(found.group(1))


def test_names(path):
    """Return every test function name a test module defines, methods included."""

    tree = ast.parse(pathlib.Path(path).read_text(encoding='utf-8'))

    return {node.name for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')}


def main():
    docs = {
        'record': squash(pathlib.Path('critiques/pr-28-validation.md')
                         .read_text(encoding='utf-8')),
        'deferred': squash(pathlib.Path('critiques/deferred-observations.md')
                           .read_text(encoding='utf-8')),
        'plan': squash(pathlib.Path('plans/2026-07-25-modernization-plan.md')
                       .read_text(encoding='utf-8')),
        'support': squash(pathlib.Path('tests/holdings_maintenance/support.py')
                          .read_text(encoding='utf-8')),
    }
    with open('pyproject.toml', 'rb') as f:
        pyproject = tomllib.load(f)
    missing = []

    def expect(doc, needle):
        if squash(needle) not in docs[doc]:
            missing.append((doc, needle))

    # --- section 1: the line-count table -------------------------------------
    for path in COUNTED:
        expect('record', f'| `{path}` | {base_lines(path)} | {lines(path)} |')

    # --- section 6: the ratchet ----------------------------------------------
    ignores = pyproject['tool']['ruff']['lint']['per-file-ignores']
    entries = len(ignores)
    slots = sum(len(v) for v in ignores.values())
    scripts = len(pyproject['project']['scripts'])
    expect('record', f'| per-file-ignores entries | 67 | **{entries}** |')
    expect('record', f'| code slots | 181 | **{slots}** |')
    expect('record', f'| `[project.scripts]` entries | {scripts} | {scripts} |')
    expect('plan', f'**{entries + 1} → {entries} entries, {slots + 1} → {slots} '
                   f'code slots**')

    # The findings count is only a number if ruff is here to produce it.
    findings = ruff_findings()
    if findings is None:
        print('UNCHECKED: ruff is not on PATH, so the findings count was not '
              're-derived')
    else:
        expect('record', f'| findings with the ratchet emptied | 2,250 | '
                         f'**{findings:,}** |')
        expect('record', f'→ 2,250 at `3d044b2`, {findings:,} at head.')

    crlf_key = 'src/pdsfile/holdings_maintenance/pds3/crlf.py'
    shelf_key = 'src/pdsfile/holdings_maintenance/pds3/shelf_consistency_check.py'
    if ignores.get(crlf_key) != ['PT028']:
        missing.append(('pyproject', f'{crlf_key} should still carry exactly PT028'))
    if shelf_key in ignores:
        missing.append(('pyproject', f'{shelf_key} should carry no entry'))
    # What a rename of test_crlf would leave behind, stated in deferred 137.
    expect('deferred', f'to {entries - 1} entries / {slots - len(ignores[crlf_key])} '
                       f'slots')

    # --- the callers of crlf.test_crlf, which section 6 and deferred 137 count -
    hits = subprocess.run(['grep', '-rl', r'test_crlf\b', '--include=*.py',
                           'src', 'tests'], capture_output=True, check=False)
    callers = sorted(p for p in hits.stdout.decode().split() if p)
    if callers != ['src/pdsfile/holdings_maintenance/pds3/crlf.py',
                   'tests/holdings_maintenance/test_crlf.py']:
        missing.append(('tree', f'test_crlf should have two calling modules, '
                                f'found {callers}'))

    # --- section 8 and deferred 130: the driver measurement -------------------
    names = [name for name, _ in DRIVERS]
    code = {name: function_body(path, name, drop_comments=True, strip_qualifier=True)
            for name, path in DRIVERS}
    raw = {name: function_body(path, name) for name, path in DRIVERS}
    shared = common_subsequence(common_subsequence(code[names[0]], code[names[1]]),
                                code[names[2]])
    raw_shared = common_subsequence(common_subsequence(raw[names[0]], raw[names[1]]),
                                    raw[names[2]])
    preamble = leading_identical([code[n] for n in names])
    total = sum(len(code[n]) for n in names)
    percent = {n: f'{100 * len(shared) / len(code[n]):.1f}%' for n in names}

    expect('record', f'run_main {len(code["run_main"])} code lines, run_selection_main '
                     f'{len(code["run_selection_main"])}, run_index_main '
                     f'{len(code["run_index_main"])}')
    expect('record', f'common to all three (ordered common subsequence): {len(shared)}')
    expect('record', f'{len(shared)} of {total} lines, ' + ' / '.join(
        percent[n] for n in names) + ' of the three')
    expect('record', f'only {preamble} of those {len(shared)} form\na contiguous block')
    expect('record', f'extracting the\n{preamble}-line preamble')

    expect('deferred', f'as an ordered common subsequence: **{len(shared)} lines** — '
                       + ', '.join(f'{percent[n]} of `{n}`' for n in names))
    expect('deferred', f'the same three are {len(raw["run_main"])} / '
                       f'{len(raw["run_selection_main"])} / '
                       f'{len(raw["run_index_main"])} lines with {len(raw_shared)} '
                       f'common')
    expect('deferred', f'Only **{preamble}** consecutive lines are identical')
    expect('deferred', f'{total} code lines across the three today')
    expect('deferred', f'The {preamble}-line preamble is contiguous')
    expect('deferred', f'takes {100 * preamble / len(shared):.0f}% of the commonality')
    for name in names:
        cells = ['—' if other == name else str(identical_with(code[name], code[other]))
                 for other in names]
        expect('deferred',
               f'| `{QUALIFIED[name]}` | {len(code[name])} | ' + ' | '.join(cells) + ' |')

    expect('plan', f'{len(shared)} of {total} code lines are common, but only '
                   f'{preamble} of those are a contiguous block')

    # --- section 5.2: every id the record names, and the one it says is gone ---
    for path, added in ADDED.items():
        present = test_names(path)
        for name in added:
            if name not in present:
                missing.append(('tree', f'{name} is not defined in {path}'))
            expect('record', name)
        if REMOVED in present:
            missing.append(('tree', f'{REMOVED} is still defined in {path}'))
    counted = sum(len(v) for v in ADDED.values())
    expect('record', f'The {counted} added ids and the 1 removed')
    expect('record', f'| `--mode ns` | 1,097 | 1,115 | {counted} | 1 | **0** |')

    # --- the in-process criterion, and deferred 140's premise -----------------
    expect('support',
           "HOLDINGS_FREE_TOOLS = frozenset({'crlf', 'shelf_consistency_check'})")
    for path in MIGRATED:
        imports = set(re.findall(r'^\s*(?:import|from)\s+(\S+)',
                                 pathlib.Path(path).read_text(encoding='utf-8'), re.M))
        if not imports <= {'argparse', 'os', 'sys'}:
            missing.append(('tree', f'{path} imports {sorted(imports)}; deferred 140 '
                                    f'says argparse, os and sys are all it imports'))

    for doc, needle in missing:
        print(f'STALE [{doc}]: {needle!r}')
    print(f'{len(missing)} stale' if missing else 'every checked number reproduces')

    return 1 if missing else 0


if __name__ == '__main__':
    sys.exit(main())
