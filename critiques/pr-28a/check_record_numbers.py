"""Re-derive every tree-readable number in PR-28a's records and fail if one has moved.

Record accuracy is a mechanical check, not a review round (owner, 2026-08-07). This
re-derives the numbers in `critiques/pr-28a-validation.md`, in PR-28a's entries in
`critiques/deferred-observations.md`, and in the plan's PR-28a entry, from the tree
itself, and reports any that no longer reproduces.

Needles are matched with all runs of whitespace collapsed to one space, so a number
that happens to sit across a line break still matches.

What it cannot check: numbers that come from running something rather than from
reading the tree -- the suite id counts, the capture's scenario and line counts.
Those carry their commands in the record, and nothing here re-derives them, so a
needle for one of them would only be this file asserting its own literal. It does
check that the one test id the record names exists.

Run from the repository root with the tree's own interpreter, 3.11 or newer (this
reads pyproject.toml through tomllib):

    python critiques/pr-28a/check_record_numbers.py

It prints one line per number that does not reproduce, and exits 1 if any does not.
"""

import pathlib
import re
import subprocess
import sys

import tomllib

BASE = 'b8b9703'                # the commit this PR branched from

RECORDS = ('critiques/pr-28a-validation.md',
           'critiques/deferred-observations.md',
           'plans/2026-07-25-modernization-plan.md')

# The files whose base and head line counts the record's section 2 table carries.
COUNTED = ('src/pdsfile/holdings_maintenance/_common.py',
           'src/pdsfile/holdings_maintenance/_shelf_common.py',
           'src/pdsfile/holdings_maintenance/_indexshelf_common.py',
           'tests/holdings_maintenance/test_driver_setup.py')

# The block as it stood in each driver at BASE: (file, first line, last line).
BLOCKS = (('src/pdsfile/holdings_maintenance/_common.py', 284, 308),
          ('src/pdsfile/holdings_maintenance/_shelf_common.py', 423, 447),
          ('src/pdsfile/holdings_maintenance/_indexshelf_common.py', 528, 552))

TEST_ID = ('tests/holdings_maintenance/test_driver_setup.py',
           'test_a_log_root_gets_every_handler_the_spec_declares')

failures = []


def collapsed(path):
    """Return a document's text with every run of whitespace collapsed to one space."""

    return re.sub(r'\s+', ' ', pathlib.Path(path).read_text(encoding='utf-8'))


DOCS = {path: collapsed(path) for path in RECORDS}


def expect(needle, why):
    """Record a failure unless the needle appears in at least one record."""

    flat = re.sub(r'\s+', ' ', needle)
    if not any(flat in text for text in DOCS.values()):
        failures.append(f'{why}: no record says {needle!r}')


def at_base(path):
    """Return a file's text as of BASE."""

    return subprocess.run(['git', 'show', f'{BASE}:{path}'],
                          capture_output=True, text=True, check=True).stdout


def check_line_counts():
    """Check each file's base and head counts, and the net the record draws from them."""

    delta = 0
    for path in COUNTED:
        head = len(pathlib.Path(path).read_text(encoding='utf-8').splitlines())
        expect(f'| {head} |', f'{path} head line count')
        try:
            base = len(at_base(path).splitlines())
        except subprocess.CalledProcessError:
            continue                    # the file did not exist at BASE
        expect(f'| {base} |', f'{path} base line count')
        if path.startswith('src/'):
            delta += head - base

    expect(f'**{-delta}\nlines shorter**', 'the net change across the three sources')


def check_the_block_was_identical():
    """The premise: the three blocks differ only in the _common. qualifier."""

    cuts = []
    for path, first, last in BLOCKS:
        lines = at_base(path).splitlines()[first - 1:last]
        cuts.append([line.replace('_common.', '') for line in lines])

    if len({tuple(cut) for cut in cuts}) != 1:
        failures.append('the three blocks at BASE are not identical once the '
                        '_common. qualifier is removed')

    if len(cuts[0]) != 25:
        failures.append(f'the block is {len(cuts[0])} lines, not 25')
    expect('**25 lines**', 'block length')

    code = [line for line in cuts[0] if line.strip() and not line.strip().startswith('#')]
    if len(code) != 15:
        failures.append(f'the block holds {len(code)} code lines, not 15')
    expect('15 of them code', 'block code-line count')


def check_the_ratchet():
    data = tomllib.loads(pathlib.Path('pyproject.toml').read_text(encoding='utf-8'))
    ignores = data['tool']['ruff']['lint']['per-file-ignores']
    expect(f'**{len(ignores)} entries', 'ratchet entry count')
    expect(f'{sum(len(codes) for codes in ignores.values())} slots',
           'ratchet code-slot count')
    expect(f'**{len(data["project"]["scripts"])}** at both', '[project.scripts] count')


def check_the_named_test_exists():
    path, name = TEST_ID
    if f'def {name}(' not in pathlib.Path(path).read_text(encoding='utf-8'):
        failures.append(f'{path} defines no {name}')
    expect(name, 'the named test id')


def check_the_tool_counts():
    """Ten of the console scripts reach one of the three drivers."""

    data = tomllib.loads(pathlib.Path('pyproject.toml').read_text(encoding='utf-8'))
    reached = 0
    for target in data['project']['scripts'].values():
        module = target.partition(':')[0].replace('.', '/')
        text = pathlib.Path('src', module + '.py').read_text(encoding='utf-8')
        if re.search(r'\b(run_main|run_selection_main|run_index_main)\(', text):
            reached += 1

    if reached != 10:
        failures.append(f'{reached} console scripts reach a driver, not 10')
    expect('Ten tools reach the three drivers', 'the count of driver-backed tools')


check_line_counts()
check_the_block_was_identical()
check_the_ratchet()
check_the_named_test_exists()
check_the_tool_counts()

for failure in failures:
    print(failure)

print(f'{len(failures)} number(s) did not reproduce')
sys.exit(1 if failures else 0)
