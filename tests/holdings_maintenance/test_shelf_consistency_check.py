##########################################################################################
# tests/holdings_maintenance/test_shelf_consistency_check.py
#
# shelf_consistency_check has no main() yet, so it is driven here as a subprocess
# (`python -m ...`) -- the same interface an in-process main() will replace later
# without changing what is asserted.
#
# The tool walks a tree looking for a `shelves/<info|links|index>/...` hierarchy
# and reports shelf files with no counterpart under `holdings/`. That hierarchy is
# a *legacy* holdings layout: current holdings keep shelves in
# `_infoshelf-volumes/`, `_linkshelf-volumes/` and `_indexshelf-metadata/`, none of
# which contain the string "shelves", so the tool finds nothing in a modern tree.
# Both facts are pinned below.
#
# Most of these tests build their own tiny legacy tree and need no holdings at all;
# only the last one runs against a dogfooded copy of real holdings.
##########################################################################################

import pytest

from tests.holdings_maintenance import subsets, support

SOURCE_FLAVOR = 'pds3'
SOURCE_FINGERPRINTS = subsets.PDS3_VOLUME_SOURCES
SOURCE_PATHS = subsets.paths_of(subsets.PDS3_VOLUME_SOURCES)
SOURCE_MTIMES = subsets.PDS3_VOLUME_MTIMES

VOLUME_DIR = f'volumes/{subsets.PDS3_VOLSET}/{subsets.PDS3_VOLUME}'


def counts(run):
    """Return the (tests performed, errors found) the tool printed.

    Args:
        run: The ToolRun to read.

    Returns:
        tuple[int, int]: The two summary counts.
    """

    tests = errors = None
    for line in run.output.splitlines():
        if line.startswith('Tests performed: '):
            tests = int(line.rpartition(' ')[2])
        elif line.startswith('Errors found: '):
            errors = int(line.rpartition(' ')[2])

    assert tests is not None, run.describe()
    assert errors is not None, run.describe()

    return (tests, errors)


@pytest.fixture
def legacy_tree(tmp_path_factory):
    """Build a minimal legacy `shelves/` + `holdings/` tree and return its ToolTree.

    The temporary directory is created with a fixed neutral prefix rather than from
    `tmp_path`: the tool filters directories with `if 'shelves' not in root`, on the
    *whole* absolute path, so a temp directory named after a test whose name
    contains "shelves" would make every directory in the tree look like a shelf
    directory.
    """

    root = tmp_path_factory.mktemp('legacy_tree')
    tree = support.ToolTree(root, 'pds3')
    (root / 'holdings' / 'volumes' / 'VG_28xx' / 'VG_2801').mkdir(parents=True)
    (root / 'shelves' / 'info' / 'volumes' / 'VG_28xx').mkdir(parents=True)

    return tree


@pytest.mark.holdings_free
def test_a_consistent_legacy_tree_is_clean(legacy_tree):
    """Shelves whose holdings directory exists are counted, not reported."""

    shelves = legacy_tree.disk / 'shelves' / 'info' / 'volumes' / 'VG_28xx'
    (shelves / 'VG_2801_info.pickle').write_bytes(b'')
    (shelves / 'VG_2801_info.py').write_bytes(b'')

    run = support.run_tool(legacy_tree, 'shelf_consistency_check', legacy_tree.disk)
    assert run.returncode == 0, run.describe()
    assert counts(run) == (2, 0), run.describe()
    assert '***' not in run.output, run.describe()


@pytest.mark.holdings_free
def test_a_shelf_without_its_holdings_directory_is_reported(legacy_tree):
    """A shelf naming a directory that does not exist is an error."""

    shelves = legacy_tree.disk / 'shelves' / 'info' / 'volumes' / 'VG_28xx'
    (shelves / 'VG_2801_info.pickle').write_bytes(b'')
    (shelves / 'VG_9999_info.pickle').write_bytes(b'')

    run = support.run_tool(legacy_tree, 'shelf_consistency_check', legacy_tree.disk)
    assert run.returncode == 1, run.describe()
    assert counts(run) == (2, 1), run.describe()
    assert 'Extraneous shelf' in run.output, run.describe()
    assert 'VG_9999_info.pickle' in run.output, run.describe()
    assert 'VG_2801_info.pickle' not in run.output, run.describe()


@pytest.mark.holdings_free
def test_an_unexpected_extension_is_reported(legacy_tree):
    """Anything that is not a .py or .pickle shelf is an error, except .DS_Store."""

    shelves = legacy_tree.disk / 'shelves' / 'info' / 'volumes' / 'VG_28xx'
    (shelves / 'VG_2801_info.pickle').write_bytes(b'')
    (shelves / 'README.txt').write_bytes(b'')
    (shelves / '.DS_Store').write_bytes(b'')

    run = support.run_tool(legacy_tree, 'shelf_consistency_check', legacy_tree.disk)
    assert run.returncode == 1, run.describe()
    assert counts(run) == (3, 1), run.describe()
    assert 'Extraneous file found' in run.output, run.describe()
    assert 'README.txt' in run.output, run.describe()
    assert '.DS_Store' not in run.output, run.describe()


@pytest.mark.holdings_free
def test_an_unknown_shelves_subdirectory_is_reported(legacy_tree):
    """Only info/, links/ and index/ are valid immediately below shelves/."""

    (legacy_tree.disk / 'shelves' / 'bogus').mkdir(parents=True)

    run = support.run_tool(legacy_tree, 'shelf_consistency_check', legacy_tree.disk)
    assert run.returncode == 1, run.describe()
    assert 'Not a valid shelves directory' in run.output, run.describe()
    assert counts(run) == (1, 1), run.describe()


@pytest.mark.holdings_free
def test_verbose_lists_the_holdings_path_of_every_shelf(legacy_tree):
    """--verbose prints the holdings path each shelf maps to."""

    shelves = legacy_tree.disk / 'shelves' / 'info' / 'volumes' / 'VG_28xx'
    (shelves / 'VG_2801_info.pickle').write_bytes(b'')

    run = support.run_tool(legacy_tree, 'shelf_consistency_check', '--verbose',
                           legacy_tree.disk)
    assert run.returncode == 0, run.describe()
    assert str(legacy_tree.disk / 'holdings' / 'volumes' / 'VG_28xx' / 'VG_2801') \
        in run.output, run.describe()


@pytest.mark.holdings_free
def test_an_extraneous_index_shelf_raises(legacy_tree):
    """Pin the known defect: the index branch increments an undefined name.

    The index branch increments an undefined name where every other branch uses
    the counter, so the first extraneous *index* shelf kills the run with
    NameError instead of being counted. Pinned as current behaviour; see entry 6
    of "From PR-13" in critiques/deferred-observations.md.
    """

    index_dir = legacy_tree.disk / 'shelves' / 'index' / 'metadata' / 'VG_28xx'
    index_dir.mkdir(parents=True)
    (index_dir / 'VG_2801_index.pickle').write_bytes(b'')

    run = support.run_tool(legacy_tree, 'shelf_consistency_check', legacy_tree.disk)
    assert run.returncode == 1, run.describe()
    assert "NameError: name 'error' is not defined" in run.output, run.describe()
    assert 'Tests performed:' not in run.output, run.describe()


@pytest.mark.full_holdings
def test_a_modern_holdings_tree_has_nothing_to_check(fresh_tree):
    """Pin the layout gap: the tool finds no shelves in a current holdings tree.

    Current holdings keep shelves in `_infoshelf-volumes/` and friends, none of
    which contain the substring "shelves" the walk filters on, so a dogfooded tree
    with real, valid shelves reports zero tests and zero errors. Pinned as current
    behaviour; see entry 6 of "From PR-13" in critiques/deferred-observations.md.
    """

    run = support.run_tool(fresh_tree, 'pdschecksums', '--initialize',
                           fresh_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    run = support.run_tool(fresh_tree, 'pdsinfoshelf', '--initialize',
                           fresh_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert fresh_tree.path(
        f'_infoshelf-volumes/{subsets.PDS3_VOLSET}/'
        f'{subsets.PDS3_VOLUME}_info.pickle').exists()

    run = support.run_tool(fresh_tree, 'shelf_consistency_check', fresh_tree.disk)
    assert run.returncode == 0, run.describe()
    assert counts(run) == (0, 0), run.describe()
