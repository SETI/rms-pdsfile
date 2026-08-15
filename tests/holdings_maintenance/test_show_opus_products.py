##########################################################################################
# tests/holdings_maintenance/test_show_opus_products.py
#
# The tool is driven as a subprocess (`python -m ...`) even though it now has a
# main(), and it is the one tool with a main() here that stays that way. It calls
# Pds3File.use_shelves_only(True) and preloads both holdings roots itself, and
# PdsFile.CACHE is a class-level cache keyed by logical path: called in-process it
# would preload the temporary tree into the same cache the session preloaded the
# real tree into, and leave shelves-only set for every test that followed. See the
# package header.
#
# The tool runs Pds3File.use_shelves_only(True), so it answers entirely out of the
# info shelves. This module therefore dogfoods pdschecksums and pdsinfoshelf onto
# the copied tree first (the `tree` fixture) and then queries it.
#
# Every test rebuilds the tree first, so each one is independent and order-agnostic.
##########################################################################################

import subprocess
import sys

import pytest

from pdsfile.tools import show_opus_products
from tests.holdings_maintenance import subsets, support

pytestmark = pytest.mark.full_holdings

SOURCE_FLAVOR = 'pds3'
SOURCE_FINGERPRINTS = subsets.PDS3_VOLUME_SOURCES + subsets.PDS3_VOLINFO_SOURCES
SOURCE_PATHS = subsets.paths_of(SOURCE_FINGERPRINTS)
SOURCE_MTIMES = subsets.PDS3_MTIMES

VOLUME_DIR = f'volumes/{subsets.PDS3_VOLSET}/{subsets.PDS3_VOLUME}'
LABEL = f'{VOLUME_DIR}/DATA/VISIT_01/N4BI01L4Q.LBL'
LOGICAL_LABEL = LABEL

EXPECTED_OPUS_TYPES = ('hst_text', 'hst_calib', 'hst_ima', 'hst_raw', 'hst_tiff')


def run_without_holdings(argv, cwd):
    """Run any command with neither holdings root set, and this checkout on the path.

    Not support.run_tool_without_holdings(): that one asserts its tool is in
    HOLDINGS_FREE_TOOLS, which this tool is deliberately not, and it only knows how
    to run `python -m <tool>`. The environment comes from the same builder, so the
    two cannot disagree about what a no-holdings run is.

    Args:
        argv: The command line to run.
        cwd: The working directory for the subprocess.

    Returns:
        subprocess.CompletedProcess: With both streams captured as bytes.
    """

    return subprocess.run(argv, cwd=str(cwd), env=support.no_holdings_env(),
                          capture_output=True, timeout=support.TOOL_TIMEOUT,
                          check=False)


@pytest.fixture
def tree(fresh_tree):
    """The module tree with checksums and info shelves generated.

    show_opus_products sets use_shelves_only(True) for Pds3File, so without the
    info shelf it would resolve nothing.
    """

    for tool in ('pdschecksums', 'pdsinfoshelf'):
        support.initialize(fresh_tree, tool, fresh_tree.path(VOLUME_DIR))

    return fresh_tree


def test_table_output_lists_every_opus_type(tree):
    """The default table output names the file and every one of its opus types.

    Asserted structurally rather than against a golden: the table is rendered by
    `tabulate`, so a byte-exact golden would pin a third-party library's formatting
    and break on an unrelated release. The `--pprint` output, which is pdsfile's
    own, carries the byte-exact golden.
    """

    run = support.run_tool(tree, 'show_opus_products', '--paths', tree.path(LABEL))
    assert run.returncode == 0, run.describe()

    assert f'Pdsfile: {LOGICAL_LABEL}' in run.output, run.describe()
    assert 'opus_type' in run.output, run.describe()
    assert 'opus_products' in run.output, run.describe()
    for opus_type in EXPECTED_OPUS_TYPES:
        assert opus_type in run.output, run.describe()

    # Each product appears under the table, by logical path.
    for product in ('N4BI01L4Q.ASC', 'N4BI01L4Q_CAL.JPG', 'N4BI01L4Q_IMA.JPG',
                    'N4BI01L4Q_RAW.JPG', 'N4BI01L4Q_RAW.TIF'):
        assert f'{VOLUME_DIR}/DATA/VISIT_01/{product}' in run.output, run.describe()

    # No absolute path from the temporary tree leaks into what the tool printed.
    # stdout, not the merged capture: the subprocess runs with cwd=tree.disk, so a
    # library warning naming the working directory would fail this spuriously.
    assert str(tree.disk) not in run.stdout, run.describe()


def test_pprint_output_maps_each_product_category(tree, golden_update):
    """--pprint emits the raw product dictionary, keyed by product category."""

    run = support.run_tool(tree, 'show_opus_products', '--pprint',
                           '--paths', tree.path(LABEL))
    assert run.returncode == 0, run.describe()

    # stdout only: a library warning on stderr is not this tool's output.
    text = run.stdout.replace(str(tree.disk), '$DISK')
    support.check_golden('show_opus_products_pprint', text, golden_update)

    # Real values: the TIFF product is reachable and is listed by logical path.
    assert f'{VOLUME_DIR}/DATA/VISIT_01/N4BI01L4Q_RAW.TIF' in run.output, run.describe()
    assert 'hst_tiff' in run.output, run.describe()


def test_logical_paths_are_accepted(tree):
    """A logical path resolves the same way an absolute path does."""

    absolute = support.run_tool(tree, 'show_opus_products', '--paths',
                                tree.path(LABEL))
    logical = support.run_tool(tree, 'show_opus_products', '--paths', LOGICAL_LABEL)
    assert logical.returncode == 0, logical.describe()
    # Both runs producing nothing would satisfy the comparison on its own.
    assert f'Pdsfile: {LOGICAL_LABEL}' in absolute.stdout, absolute.describe()
    assert logical.stdout == absolute.stdout, logical.describe()


def test_opus_type_filter_restricts_the_output(tree):
    """--opus-types keeps only the requested category."""

    run = support.run_tool(tree, 'show_opus_products', '--opus-types', 'hst_tiff',
                           '--paths', tree.path(LABEL))
    assert run.returncode == 0, run.describe()
    assert 'hst_tiff' in run.output, run.describe()
    for opus_type in ('hst_text', 'hst_calib', 'hst_ima', 'hst_raw'):
        assert opus_type not in run.output, run.describe()


def test_an_unknown_opus_type_warns_and_bypasses(tree):
    """An opus type the file does not have is reported and the file is skipped."""

    run = support.run_tool(tree, 'show_opus_products', '--opus-types', 'not_a_type',
                           '--paths', tree.path(LABEL))
    assert run.returncode == 1, run.describe()
    assert 'WARNING: not_a_type is not valid' in run.output, run.describe()
    assert 'bypassing output' in run.output, run.describe()
    # The valid types are offered instead, and no product table is printed.
    assert 'None of the given opus types exist; valid values:' in run.output, \
        run.describe()
    assert 'Pdsfile:' not in run.output, run.describe()
    assert 'N4BI01L4Q_RAW.TIF' not in run.output, run.describe()


def test_a_nonexistent_path_warns_and_fails_the_run(tree):
    """A path that resolves but does not exist is warned about, and fails the run.

    The warning names the path and the run carries on to the remaining paths; the
    exit status is what reports that one of them could not be answered.
    """

    missing = f'{VOLUME_DIR}/DATA/VISIT_01/N4BI01ZZZ.LBL'
    run = support.run_tool(tree, 'show_opus_products', '--paths', missing)
    assert run.returncode == 1, run.describe()
    assert "doesn't exist" in run.output, run.describe()


@pytest.mark.holdings_free
def test_the_parser_is_built_without_touching_the_environment():
    """build_arg_parser() reads no environment and no PdsFile state.

    The parser is what --help and every usage error come out of, so it has to be
    reachable before either holdings root is looked at.
    """

    parser = show_opus_products.build_arg_parser()
    args = parser.parse_args(['--paths', 'a', 'b', '--opus-types', 'hst_tiff'])
    assert args.paths == ['a', 'b']
    assert args.opus_types == ['hst_tiff']
    assert (args.table, args.narrow_table, args.pprint, args.raw, args.debug) == \
        (False, False, False, False, False)

    with pytest.raises(SystemExit) as exit_info:
        parser.parse_args(['--help'])
    assert exit_info.value.code == 0


@pytest.mark.holdings_free
def test_the_module_imports_with_neither_holdings_root_set(tmp_path):
    """Importing the module must not read the environment or preload anything.

    Measured in a subprocess with both variables removed, because this test
    session sets them: the roots are read inside main(), so the import itself
    succeeds without them. That is what lets --help work on a machine with no
    holdings, and what any importer -- an autodoc build, a console script's entry
    point -- would need. The import must also not preload, which would put a
    whole holdings tree into a class-level cache as a side effect of an import.
    """

    probe = ('import os; '
             "assert 'PDS3_HOLDINGS_DIR' not in os.environ; "
             "assert 'PDS4_HOLDINGS_DIR' not in os.environ; "
             'import pdsfile.tools.show_opus_products as m; '
             'assert callable(m.main); assert callable(m.build_arg_parser); '
             "assert not hasattr(m, 'PDS3_HOLDINGS_DIR'); "
             'from pdsfile import Pds3File; '
             'assert Pds3File.LOCAL_PRELOADED == []; '
             'assert Pds3File.SHELVES_ONLY is False')
    proc = run_without_holdings([sys.executable, '-c', probe], tmp_path)
    assert proc.returncode == 0, proc.stderr.decode('utf-8', errors='replace')


@pytest.mark.holdings_free
def test_main_parses_the_argv_it_is_given_and_sys_argv_otherwise(monkeypatch, capsys):
    """Both halves of main(argv=None), without needing a holdings root.

    A usage error is answered by the parser before either root is read, so it is
    the one invocation that reaches main() and comes back on a machine with no
    holdings. The two calls differ only in where the command line comes from.
    """

    monkeypatch.delenv('PDS3_HOLDINGS_DIR', raising=False)
    monkeypatch.delenv('PDS4_HOLDINGS_DIR', raising=False)

    # sys.argv holds a command line the parser accepts, so a main() that read it
    # instead of its argument would go on to the holdings roots and raise KeyError
    # rather than exiting 2 here.
    monkeypatch.setattr(sys, 'argv', ['show_opus_products.py', '--paths', 'a'])
    with pytest.raises(SystemExit) as explicit:
        show_opus_products.main(['show_opus_products.py', '--paths'])
    assert explicit.value.code == 2
    assert 'expected at least one argument' in capsys.readouterr().err

    monkeypatch.setattr(sys, 'argv', ['show_opus_products.py', '--not-a-flag'])
    with pytest.raises(SystemExit) as implicit:
        show_opus_products.main()
    assert implicit.value.code == 2
    assert 'the following arguments are required: --paths' in capsys.readouterr().err


@pytest.mark.holdings_free
def test_the_module_is_runnable_as_python_m(tmp_path):
    """`python -m ...` reaches main() and exits with what it returned.

    A subprocess, and the only test here that shows the module has a `__main__`
    block at all: every other test in this file needs holdings, so on a runner
    without them nothing would notice the block's absence. --help is the one
    invocation that gets through main() with no holdings root set, and argparse's
    exit is a SystemExit(0) that the block has to let through.
    """

    proc = run_without_holdings(
        [sys.executable, '-m', support.TOOL_MODULES['show_opus_products'], '--help'],
        tmp_path)
    stdout = proc.stdout.decode('utf-8', errors='replace')
    assert proc.returncode == 0, proc.stderr.decode('utf-8', errors='replace')
    assert 'usage: show_opus_products.py' in stdout, stdout
    for flag in ('--paths', '--opus-types', '--narrow-table', '--debug'):
        assert flag in stdout, stdout
