##########################################################################################
# tests/holdings_maintenance/test_pds3_indexshelf.py
#
# Full task cycle for pdsindexshelf against a copy of the declared PDS3 metadata
# subset. pdsindexshelf shelves the row indices of a labelled metadata table, so
# this module declares only the metadata slice of the subset.
#
# The `tool_tree` fixture is module-scoped, so these tests share one temporary tree
# and run in definition order; every mutating test restores a clean tree.
##########################################################################################

from collections import namedtuple

import pytest

from tests.holdings_maintenance import subsets, support

pytestmark = pytest.mark.full_holdings

SOURCE_FLAVOR = 'pds3'
SOURCE_FINGERPRINTS = subsets.PDS3_METADATA_SOURCES
SOURCE_PATHS = subsets.paths_of(subsets.PDS3_METADATA_SOURCES)
SOURCE_MTIMES = subsets.PDS3_METADATA_MTIMES

METADATA_DIR = f'metadata/{subsets.PDS3_VOLSET}/{subsets.PDS3_VOLUME}'
INDEX_TABLE = f'{METADATA_DIR}/{subsets.PDS3_VOLUME}_index.tab'
INDEX_LABEL = f'{METADATA_DIR}/{subsets.PDS3_VOLUME}_index.lbl'
HSTFILES_TABLE = f'{METADATA_DIR}/{subsets.PDS3_VOLUME}_hstfiles.tab'
SHELF_DIR = f'_indexshelf-metadata/{subsets.PDS3_VOLSET}/{subsets.PDS3_VOLUME}'
SIDECAR = f'{SHELF_DIR}/{subsets.PDS3_VOLUME}_index.py'
PICKLE = f'{SHELF_DIR}/{subsets.PDS3_VOLUME}_index.pickle'

Corruption = namedtuple('Corruption', 'name description damage expected')


def drop_last_row(path):
    """Remove the final record from an index table, leaving the label's ROWS stale."""

    data = path.read_bytes()
    path.write_bytes(data[:data[:-1].rfind(b'\n') + 1])


def rename_first_key(path):
    """Rewrite the first record's file specification, preserving the record length.

    The shelf keys come from the basename of the FILE_SPECIFICATION_NAME column
    truncated to the rules' filename key length, so this is what changes a key.
    """

    support.replace_bytes(path, b'"DATA/VISIT_01/N4BI01010.LBL"',
                          b'"DATA/VISIT_01/N4BI01ZZZ.LBL"')


# Fixed corruption scenarios. The shelf records one entry per table row, keyed by
# the product's filename key, so renaming a key makes shelf and table disagree in
# both directions at once.
CORRUPTIONS = (
    Corruption('first_index_key_renamed',
               'rewrite the first record file specification N4BI01010 as N4BI01ZZZ',
               rename_first_key, 'not in shelf'),
)


def repin_mtimes(tree):
    """Restore every declared source file's pinned modification time."""

    for relpath, mtime in SOURCE_MTIMES.items():
        path = tree.path(relpath)
        if path.exists():
            support.shift_mtime(path, mtime - path.stat().st_mtime)


def test_initialize_writes_the_expected_sidecar(tool_tree, golden_update):
    """--initialize shelves the index table and the .py sidecar matches the golden."""

    run = support.run_tool(tool_tree, 'pdsindexshelf', '--initialize',
                           tool_tree.path(INDEX_TABLE))
    assert run.returncode == 0, run.describe()

    sidecar = tool_tree.path(SIDECAR)
    assert sidecar.exists(), run.describe()
    assert tool_tree.path(PICKLE).exists(), run.describe()

    text = support.sidecar_text(sidecar)
    support.check_golden('pds3_indexshelf_sidecar', text, golden_update)

    # The shelf really indexes the table: one entry per data record, keyed by the
    # product's filename key, with contiguous row numbers from zero.
    rows = [line for line in text.splitlines() if line.strip().startswith('"')]
    table_rows = tool_tree.path(INDEX_TABLE).read_bytes().count(b'\n')
    assert len(rows) == table_rows, text
    assert rows[0].strip().endswith(': 0,'), rows[0]
    assert f': {table_rows - 1},' in rows[-1], rows[-1]


def test_initialize_refuses_to_clobber(tool_tree):
    """A second --initialize reports the existing shelf and exits non-zero."""

    run = support.run_tool(tool_tree, 'pdsindexshelf', '--initialize',
                           tool_tree.path(INDEX_TABLE))
    assert run.returncode == 1, run.describe()
    assert any('Index shelf file already exists' in line for line in run.error_lines), \
        run.describe()


def test_directory_argument_shelves_every_table(tool_tree):
    """Pointing the tool at the metadata directory shelves all of its .tab files."""

    run = support.run_tool(tool_tree, 'pdsindexshelf', '--update',
                           tool_tree.path(METADATA_DIR))
    assert run.returncode == 0, run.describe()

    hstfiles_sidecar = tool_tree.path(
        f'{SHELF_DIR}/{subsets.PDS3_VOLUME}_hstfiles.py')
    assert hstfiles_sidecar.exists(), run.describe()
    assert 'hstfiles = {' in support.sidecar_text(hstfiles_sidecar)


def test_non_metadata_argument_is_rejected(tool_tree):
    """A path outside metadata/ is refused before any work is done."""

    outside = tool_tree.path(INDEX_LABEL)
    run = support.run_tool(tool_tree, 'pdsindexshelf', '--initialize', outside)
    assert run.returncode == 1, run.describe()
    assert 'Not a table file' in run.output, run.describe()


def test_validate_is_clean_after_initialize(tool_tree):
    """--validate on an untouched shelf exits 0 and logs no errors."""

    run = support.run_tool(tool_tree, 'pdsindexshelf', '--validate',
                           tool_tree.path(INDEX_TABLE))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()


@pytest.mark.parametrize('corruption', CORRUPTIONS, ids=[c.name for c in CORRUPTIONS])
def test_corruption_is_detected_and_repaired(tool_tree, corruption):
    """Each fixed corruption fails --validate, and --repair restores a clean shelf."""

    target = tool_tree.path(INDEX_TABLE)
    original = target.read_bytes()
    corruption.damage(target)

    run = support.run_tool(tool_tree, 'pdsindexshelf', '--validate',
                           tool_tree.path(INDEX_TABLE))
    assert run.returncode == 1, f'{corruption.description}\n{run.describe()}'
    assert any(corruption.expected in line for line in run.error_lines), \
        f'{corruption.description}\n{run.describe()}'

    run = support.run_tool(tool_tree, 'pdsindexshelf', '--repair',
                           tool_tree.path(INDEX_TABLE))
    assert run.returncode == 0, run.describe()

    run = support.run_tool(tool_tree, 'pdsindexshelf', '--validate',
                           tool_tree.path(INDEX_TABLE))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()

    # Restore the pristine table and rebuild the shelf for the next test.
    target.write_bytes(original)
    repin_mtimes(tool_tree)
    run = support.run_tool(tool_tree, 'pdsindexshelf', '--repair',
                           tool_tree.path(INDEX_TABLE))
    assert run.returncode == 0, run.describe()
    assert support.sidecar_text(tool_tree.path(SIDECAR)) == \
        support.sidecar_text(support.GOLDEN_DIR / 'pds3_indexshelf_sidecar.txt')


def test_row_count_disagreeing_with_the_label_is_refused(tool_tree):
    """A table shorter than its label's ROWS count is refused, not silently shelved."""

    target = tool_tree.path(INDEX_TABLE)
    original = target.read_bytes()
    drop_last_row(target)

    run = support.run_tool(tool_tree, 'pdsindexshelf', '--validate',
                           tool_tree.path(INDEX_TABLE))
    assert run.returncode == 1, run.describe()
    assert any('row count mismatch' in line for line in run.error_lines), run.describe()

    target.write_bytes(original)
    repin_mtimes(tool_tree)
    run = support.run_tool(tool_tree, 'pdsindexshelf', '--validate',
                           tool_tree.path(INDEX_TABLE))
    assert run.returncode == 0, run.describe()
