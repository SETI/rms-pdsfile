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

import os
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
    """Run a command with neither holdings root set, and this checkout on the path.

    Args:
        argv: The command line to run.
        cwd: The working directory for the subprocess.

    Returns:
        subprocess.CompletedProcess: With both streams captured as bytes.
    """

    env = dict(os.environ)
    env['PYTHONPATH'] = str(support.REPO_ROOT / 'src')
    for name in ('PDS3_HOLDINGS_DIR', 'PDS4_HOLDINGS_DIR', 'PDSFILE_TEST_HOLDINGS',
                 'PDSFILE_TEST_DATA_DIR'):
        env.pop(name, None)

    return subprocess.run(argv, cwd=str(cwd), env=env, capture_output=True,
                          timeout=support.TOOL_TIMEOUT, check=False)


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
    assert run.returncode == 0, run.describe()
    assert 'WARNING: not_a_type is not valid' in run.output, run.describe()
    assert 'bypassing output' in run.output, run.describe()
    # The valid types are offered instead, and no product table is printed.
    assert 'None of the given opus types exist; valid values:' in run.output, \
        run.describe()
    assert 'Pdsfile:' not in run.output, run.describe()
    assert 'N4BI01L4Q_RAW.TIF' not in run.output, run.describe()


def test_a_nonexistent_path_warns_rather_than_failing(tree):
    """A path that resolves but does not exist produces a warning, not an error."""

    missing = f'{VOLUME_DIR}/DATA/VISIT_01/N4BI01ZZZ.LBL'
    run = support.run_tool(tree, 'show_opus_products', '--paths', missing)
    assert run.returncode == 0, run.describe()
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

    probe = ('import pdsfile.tools.show_opus_products as m; '
             'assert callable(m.main); assert callable(m.build_arg_parser); '
             "assert not hasattr(m, 'PDS3_HOLDINGS_DIR'); "
             'from pdsfile import Pds3File; '
             'assert Pds3File.LOCAL_PRELOADED == []; '
             'assert Pds3File.SHELVES_ONLY is False')
    proc = run_without_holdings([sys.executable, '-c', probe], tmp_path)
    assert proc.returncode == 0, proc.stderr.decode('utf-8', errors='replace')


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
