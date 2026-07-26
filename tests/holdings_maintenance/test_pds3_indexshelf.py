##########################################################################################
# tests/holdings_maintenance/test_pds3_indexshelf.py
#
# Full task cycle for pdsindexshelf against a copy of the declared PDS3 metadata
# subset. pdsindexshelf shelves the row indices of a labelled metadata table, so
# this module declares only the metadata slice of the subset.
#
# Every test rebuilds the tree first, so each one is independent and order-agnostic.
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

    The shelf keys come from the basename of the file-specification column
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


@pytest.fixture
def shelved_tree(fresh_tree):
    """A freshly rebuilt tree with the index shelf already generated."""

    support.initialize(fresh_tree, 'pdsindexshelf', fresh_tree.path(INDEX_TABLE))

    return fresh_tree


def test_initialize_writes_the_expected_sidecar(fresh_tree, golden_update):
    """--initialize shelves the index table and the .py sidecar matches the golden."""

    support.initialize(fresh_tree, 'pdsindexshelf', fresh_tree.path(INDEX_TABLE))

    sidecar = fresh_tree.path(SIDECAR)
    assert sidecar.exists()
    assert fresh_tree.path(PICKLE).exists()

    text = support.sidecar_text(sidecar)
    support.check_golden('pds3_indexshelf_sidecar', text, golden_update)

    # The shelf really indexes the table: one entry per data record, keyed by the
    # product's filename key, with contiguous row numbers from zero.
    rows = [line for line in text.splitlines() if line.strip().startswith('"')]
    table_rows = fresh_tree.path(INDEX_TABLE).read_bytes().count(b'\n')
    assert len(rows) == table_rows, text
    assert [int(line.rpartition(':')[2].strip().rstrip(',')) for line in rows] == \
        list(range(table_rows))
    assert rows[0].strip().startswith('"N4BI01010"'), rows[0]


def test_initialize_refuses_to_clobber(shelved_tree):
    """A second --initialize reports the existing shelf and exits non-zero."""

    run = support.run_tool(shelved_tree, 'pdsindexshelf', '--initialize',
                           shelved_tree.path(INDEX_TABLE))
    assert run.returncode == 1, run.describe()
    assert any('Index shelf file already exists' in line for line in run.error_lines), \
        run.describe()


def test_directory_argument_shelves_every_table(fresh_tree):
    """Pointing the tool at the metadata directory shelves all of its .tab files."""

    run = support.run_tool(fresh_tree, 'pdsindexshelf', '--update',
                           fresh_tree.path(METADATA_DIR))
    assert run.returncode == 0, run.describe()

    for table in ('index', 'hstfiles'):
        sidecar = fresh_tree.path(f'{SHELF_DIR}/{subsets.PDS3_VOLUME}_{table}.py')
        assert sidecar.exists(), run.describe()
        assert f'{table} = {{' in support.sidecar_text(sidecar)


def test_update_shelves_a_table_that_has_none_and_leaves_the_rest(shelved_tree):
    """--update over a partly shelved directory adds only what is missing.

    The index table is already shelved; the sibling hstfiles table is not.
    """

    hstfiles_sidecar = shelved_tree.path(
        f'{SHELF_DIR}/{subsets.PDS3_VOLUME}_hstfiles.py')
    assert not hstfiles_sidecar.exists()
    before = support.sidecar_text(shelved_tree.path(SIDECAR))

    run = support.run_tool(shelved_tree, 'pdsindexshelf', '--update',
                           shelved_tree.path(METADATA_DIR))
    assert run.returncode == 0, run.describe()

    assert hstfiles_sidecar.exists(), run.describe()
    assert 'hstfiles = {' in support.sidecar_text(hstfiles_sidecar)
    assert support.sidecar_text(shelved_tree.path(SIDECAR)) == before

    run = support.run_tool(shelved_tree, 'pdsindexshelf', '--validate',
                           shelved_tree.path(METADATA_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()


def test_non_table_metadata_argument_is_rejected(fresh_tree):
    """A non-.tab file inside metadata/ is refused before any work is done."""

    run = support.run_tool(fresh_tree, 'pdsindexshelf', '--initialize',
                           fresh_tree.path(INDEX_LABEL))
    assert run.returncode == 1, run.describe()
    assert 'Not a table file' in run.output, run.describe()


def test_non_metadata_argument_is_rejected(fresh_tree):
    """A .tab file outside metadata/ is refused before any work is done."""

    outside = support.add_file(
        fresh_tree, f'volumes/{subsets.PDS3_VOLSET}/{subsets.PDS3_VOLUME}/STRAY.TAB',
        b'not a metadata table\r\n', SOURCE_MTIMES[INDEX_TABLE])
    run = support.run_tool(fresh_tree, 'pdsindexshelf', '--initialize', outside)
    assert run.returncode == 1, run.describe()
    assert 'Not a metadata file' in run.output, run.describe()


def test_validate_is_clean_after_initialize(shelved_tree):
    """--validate on an untouched shelf exits 0 and logs no errors."""

    run = support.run_tool(shelved_tree, 'pdsindexshelf', '--validate',
                           shelved_tree.path(INDEX_TABLE))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()


@pytest.mark.parametrize('corruption', CORRUPTIONS, ids=[c.name for c in CORRUPTIONS])
def test_corruption_is_detected_and_repaired(shelved_tree, corruption):
    """Each fixed corruption fails --validate, and --repair restores a clean shelf."""

    corruption.damage(shelved_tree.path(INDEX_TABLE))

    run = support.run_tool(shelved_tree, 'pdsindexshelf', '--validate',
                           shelved_tree.path(INDEX_TABLE))
    assert run.returncode == 1, f'{corruption.description}\n{run.describe()}'
    assert any(corruption.expected in line for line in run.error_lines), \
        f'{corruption.description}\n{run.describe()}'

    run = support.run_tool(shelved_tree, 'pdsindexshelf', '--repair',
                           shelved_tree.path(INDEX_TABLE))
    assert run.returncode == 0, run.describe()

    run = support.run_tool(shelved_tree, 'pdsindexshelf', '--validate',
                           shelved_tree.path(INDEX_TABLE))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()

    # The repaired shelf really carries the renamed key.
    assert '"N4BI01ZZZ"' in support.sidecar_text(shelved_tree.path(SIDECAR))


def test_row_count_disagreeing_with_the_label_is_refused(shelved_tree):
    """A table shorter than its label's ROWS count is refused, not silently shelved."""

    before = support.sidecar_text(shelved_tree.path(SIDECAR))
    drop_last_row(shelved_tree.path(INDEX_TABLE))

    run = support.run_tool(shelved_tree, 'pdsindexshelf', '--validate',
                           shelved_tree.path(INDEX_TABLE))
    assert run.returncode == 1, run.describe()
    assert any('row count mismatch' in line for line in run.error_lines), run.describe()
    assert support.sidecar_text(shelved_tree.path(SIDECAR)) == before
