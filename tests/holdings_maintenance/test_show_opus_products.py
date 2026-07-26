##########################################################################################
# tests/holdings_maintenance/test_show_opus_products.py
#
# show_opus_products has no main() yet -- that is PR-28 -- so it is driven here as a
# subprocess (`python -m ...`), which is the same interface PR-28's in-process
# main() will replace without changing what is asserted.
#
# The tool runs Pds3File.use_shelves_only(True), so it answers entirely out of the
# info shelves. This module therefore dogfoods pdschecksums and pdsinfoshelf onto
# the copied tree first (the `tree` fixture) and then queries it.
#
# The `tool_tree` fixture is module-scoped, so these tests share one temporary tree
# and run in definition order.
##########################################################################################

import pytest

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


@pytest.fixture(scope='module')
def tree(tool_tree):
    """The module tree with checksums and info shelves generated.

    show_opus_products sets use_shelves_only(True) for Pds3File, so without the
    info shelf it would resolve nothing.
    """

    for tool in ('pdschecksums', 'pdsinfoshelf'):
        run = support.run_tool(tool_tree, tool, '--initialize',
                               tool_tree.path(VOLUME_DIR))
        assert run.returncode == 0, run.describe()

    return tool_tree


def test_table_output_lists_every_opus_type(tree, golden_update):
    """The default table output matches the committed golden."""

    run = support.run_tool(tree, 'show_opus_products', '--paths', tree.path(LABEL))
    assert run.returncode == 0, run.describe()

    text = run.output.replace(str(tree.disk), '$DISK')
    support.check_golden('show_opus_products_table', text, golden_update)

    for opus_type in EXPECTED_OPUS_TYPES:
        assert opus_type in run.output, run.describe()
    assert f'Pdsfile: {LOGICAL_LABEL}' in run.output, run.describe()


def test_pprint_output_maps_each_product_category(tree, golden_update):
    """--pprint emits the raw product dictionary, keyed by product category."""

    run = support.run_tool(tree, 'show_opus_products', '--pprint',
                           '--paths', tree.path(LABEL))
    assert run.returncode == 0, run.describe()

    text = run.output.replace(str(tree.disk), '$DISK')
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
    assert logical.output == absolute.output, logical.describe()


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
