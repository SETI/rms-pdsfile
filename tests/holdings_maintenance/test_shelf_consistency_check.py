##########################################################################################
# tests/holdings_maintenance/test_shelf_consistency_check.py
#
# The tool is driven in-process, by calling main() through
# support.run_tool_in_process(): it imports no PdsFile class and reads neither
# holdings root, so the class-level-cache hazard that keeps the other tools on
# subprocesses (see the package header) cannot arise. One test keeps the
# subprocess, because only a subprocess shows that `python -m ...` reaches main()
# and that the process exit code is what main() returned.
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
    for line in run.stdout.splitlines():
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

    run = support.run_tool_in_process('shelf_consistency_check', legacy_tree.disk)
    assert run.returncode == 0, run.describe()
    assert counts(run) == (2, 0), run.describe()
    assert '***' not in run.output, run.describe()


@pytest.mark.holdings_free
def test_a_shelf_without_its_holdings_directory_is_reported(legacy_tree):
    """A shelf naming a directory that does not exist is an error."""

    shelves = legacy_tree.disk / 'shelves' / 'info' / 'volumes' / 'VG_28xx'
    (shelves / 'VG_2801_info.pickle').write_bytes(b'')
    (shelves / 'VG_9999_info.pickle').write_bytes(b'')

    run = support.run_tool_in_process('shelf_consistency_check', legacy_tree.disk)
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

    run = support.run_tool_in_process('shelf_consistency_check', legacy_tree.disk)
    assert run.returncode == 1, run.describe()
    assert counts(run) == (3, 1), run.describe()
    assert 'Extraneous file found' in run.output, run.describe()
    assert 'README.txt' in run.output, run.describe()
    assert '.DS_Store' not in run.output, run.describe()


@pytest.mark.holdings_free
def test_an_unknown_shelves_subdirectory_is_reported(legacy_tree):
    """Only info/, links/ and index/ are valid immediately below shelves/."""

    (legacy_tree.disk / 'shelves' / 'bogus').mkdir(parents=True)

    run = support.run_tool_in_process('shelf_consistency_check', legacy_tree.disk)
    assert run.returncode == 1, run.describe()
    assert 'Not a valid shelves directory' in run.output, run.describe()
    assert counts(run) == (1, 1), run.describe()


@pytest.mark.holdings_free
def test_verbose_lists_the_holdings_path_of_every_shelf(legacy_tree):
    """--verbose prints the holdings path each shelf maps to."""

    shelves = legacy_tree.disk / 'shelves' / 'info' / 'volumes' / 'VG_28xx'
    (shelves / 'VG_2801_info.pickle').write_bytes(b'')

    run = support.run_tool_in_process('shelf_consistency_check', '--verbose',
                                      legacy_tree.disk)
    assert run.returncode == 0, run.describe()
    assert str(legacy_tree.disk / 'holdings' / 'volumes' / 'VG_28xx' / 'VG_2801') \
        in run.output, run.describe()


@pytest.mark.holdings_free
def test_an_index_shelf_whose_label_exists_is_counted_not_reported(legacy_tree):
    """An index shelf is matched against the holdings *label*, not a directory."""

    index_dir = legacy_tree.disk / 'shelves' / 'index' / 'metadata' / 'VG_28xx'
    index_dir.mkdir(parents=True)
    (index_dir / 'VG_2801_index.pickle').write_bytes(b'')
    label = legacy_tree.disk / 'holdings' / 'metadata' / 'VG_28xx'
    label.mkdir(parents=True)
    (label / 'VG_2801_index.lbl').write_bytes(b'')

    run = support.run_tool_in_process('shelf_consistency_check', legacy_tree.disk)
    assert run.returncode == 0, run.describe()
    assert counts(run) == (1, 0), run.describe()
    assert '***' not in run.output, run.describe()


@pytest.mark.holdings_free
def test_an_extraneous_index_shelf_is_counted_like_any_other(legacy_tree):
    """The index branch counts its error and the walk carries on.

    Regression test for the branch that used to increment an undefined name,
    where every other branch increments the counter: the first extraneous *index*
    shelf killed the run with NameError before any summary was printed. The two
    shelves below are in different `shelves/` subtrees, so an exception in the
    index branch would also lose the info shelf's count -- which is what the
    (2, 1) below rules out.
    """

    index_dir = legacy_tree.disk / 'shelves' / 'index' / 'metadata' / 'VG_28xx'
    index_dir.mkdir(parents=True)
    (index_dir / 'VG_9999_index.pickle').write_bytes(b'')
    shelves = legacy_tree.disk / 'shelves' / 'info' / 'volumes' / 'VG_28xx'
    (shelves / 'VG_2801_info.pickle').write_bytes(b'')

    run = support.run_tool_in_process('shelf_consistency_check', legacy_tree.disk)
    assert run.returncode == 1, run.describe()
    assert counts(run) == (2, 1), run.describe()
    assert 'Extraneous shelf' in run.output, run.describe()
    assert 'VG_9999_index.pickle' in run.output, run.describe()
    assert 'NameError' not in run.output, run.describe()


@pytest.mark.holdings_free
def test_no_arguments_reports_an_empty_run():
    """Naming no shelf root at all walks nothing and succeeds."""

    run = support.run_tool_in_process('shelf_consistency_check')
    assert run.returncode == 0, run.describe()
    assert counts(run) == (0, 0), run.describe()


@pytest.mark.holdings_free
def test_verbose_is_accepted_between_the_shelf_roots(legacy_tree, tmp_path):
    """The flag is positional-order-independent, as it was before argparse.

    The flag sits *between* two roots, which is the placement plain
    `parse_args` rejects; a flag trailing the last positional is accepted by
    either spelling, so it would not tell the two apart.
    """

    shelves = legacy_tree.disk / 'shelves' / 'info' / 'volumes' / 'VG_28xx'
    (shelves / 'VG_2801_info.pickle').write_bytes(b'')
    second = tmp_path / 'second_root'
    second.mkdir()

    run = support.run_tool_in_process('shelf_consistency_check', legacy_tree.disk,
                                      '--verbose', second)
    assert run.returncode == 0, run.describe()
    assert counts(run) == (1, 0), run.describe()
    assert str(legacy_tree.disk / 'holdings' / 'volumes' / 'VG_28xx' / 'VG_2801') \
        in run.output, run.describe()


@pytest.mark.holdings_free
def test_an_unrecognized_flag_is_a_usage_error(legacy_tree):
    """argparse rejects an unknown option rather than treating it as a path."""

    run = support.run_tool_in_process('shelf_consistency_check', '--bogus',
                                      legacy_tree.disk)
    assert run.returncode == 2, run.describe()
    assert 'unrecognized arguments: --bogus' in run.output, run.describe()
    assert 'Tests performed:' not in run.output, run.describe()


@pytest.mark.holdings_free
def test_an_abbreviated_flag_is_a_usage_error(legacy_tree):
    """`--verb` is not `--verbose`: an option has to be spelled out.

    The parser sets allow_abbrev=False, so a misspelling is rejected rather
    than quietly turning an option on.
    """

    shelves = legacy_tree.disk / 'shelves' / 'info' / 'volumes' / 'VG_28xx'
    (shelves / 'VG_2801_info.pickle').write_bytes(b'')

    run = support.run_tool_in_process('shelf_consistency_check', '--verb',
                                      legacy_tree.disk)
    assert run.returncode == 2, run.describe()
    assert 'unrecognized arguments: --verb' in run.output, run.describe()
    assert 'Tests performed:' not in run.output, run.describe()


@pytest.mark.holdings_free
@pytest.mark.parametrize('flag', ['--help', '-h'])
def test_help_names_the_flag_and_the_positional(flag):
    """Both spellings of help answer; the tool had neither before argparse."""

    run = support.run_tool_in_process('shelf_consistency_check', flag)
    assert run.returncode == 0, run.describe()
    assert '--verbose' in run.stdout, run.describe()
    assert 'shelf_root' in run.stdout, run.describe()
    assert 'Tests performed:' not in run.stdout, run.describe()


@pytest.mark.holdings_free
def test_a_flag_given_a_value_is_a_usage_error(legacy_tree):
    """--verbose takes no value, so `--verbose=1` is rejected outright."""

    run = support.run_tool_in_process('shelf_consistency_check', '--verbose=1',
                                      legacy_tree.disk)
    assert run.returncode == 2, run.describe()
    assert 'ignored explicit argument' in run.output, run.describe()
    assert 'Tests performed:' not in run.output, run.describe()


@pytest.mark.holdings_free
def test_a_shelf_root_beginning_with_a_dash_is_a_usage_error(tmp_path, monkeypatch):
    """argparse reads a leading `-` as an option here too.

    The same loss `crlf` takes, on a root rather than a file: the walk accepted
    any string before, and a directory named `-something` is now unreachable
    except after another root and a `--` separator.
    """

    (tmp_path / '-dashroot').mkdir()
    monkeypatch.chdir(tmp_path)

    run = support.run_tool_in_process('shelf_consistency_check', '-dashroot')
    assert run.returncode == 2, run.describe()
    assert 'Tests performed:' not in run.output, run.describe()


@pytest.mark.holdings_free
def test_the_module_is_runnable_as_python_m(legacy_tree, tmp_path):
    """`python -m ...` reaches main(), and the process exit code is its return value.

    Driven as a subprocess with neither holdings variable set, which the
    in-process cases above cannot show: they call main() by name, so they would
    pass whether or not the module has a `__main__` block, and they inherit this
    process's environment.
    """

    shelves = legacy_tree.disk / 'shelves' / 'info' / 'volumes' / 'VG_28xx'
    (shelves / 'VG_2801_info.pickle').write_bytes(b'')
    (shelves / 'VG_9999_info.pickle').write_bytes(b'')

    run = support.run_tool_without_holdings('shelf_consistency_check',
                                            legacy_tree.disk, cwd=tmp_path)
    assert run.returncode == 1, run.describe()
    assert counts(run) == (2, 1), run.describe()
    assert 'Extraneous shelf' in run.output, run.describe()


@pytest.mark.full_holdings
def test_a_modern_holdings_tree_has_nothing_to_check(fresh_tree):
    """Pin the layout gap: the tool finds no shelves in a current holdings tree.

    Current holdings keep shelves in `_infoshelf-volumes/` and friends, none of
    which contain the substring "shelves" the walk filters on, so a dogfooded tree
    with real, valid shelves reports zero tests and zero errors -- the tool checks
    nothing at all unless it is pointed at a legacy tree. Pinned as current
    behaviour, not endorsed: a fix has to invert this assertion deliberately.
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

    run = support.run_tool_in_process('shelf_consistency_check', fresh_tree.disk)
    assert run.returncode == 0, run.describe()
    assert counts(run) == (0, 0), run.describe()
