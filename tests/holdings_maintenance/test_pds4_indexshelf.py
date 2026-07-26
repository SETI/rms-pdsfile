##########################################################################################
# tests/holdings_maintenance/test_pds4_indexshelf.py
#
# pds4indexshelf against a copy of the declared PDS4 metadata subset.
#
# This module cannot run the task cycle its pds3 twin runs, because pds4indexshelf
# cannot shelve any PDS4 metadata table that exists today. It is pinned rather than
# fixed (PR-13 is behavior-preserving; PR-27 owns the indexshelf pair):
#
#   generate_indexdict() builds a pdstable.PdsTable from `pdsf.label_abspath`
#   (pds4indexshelf.py:52) -- a PDS3 detached-label reader. PDS4 metadata index
#   files are .csv with either no PDS3 label at all (uranus_occs_earthbased, where
#   label_abspath is empty and the read falls through to a FileNotFoundError) or an
#   .xml label that the PDS3 reader misparses (cassini_uvis_solarocc_..., which
#   raises "row count mismatch"). Neither of the two PDS4 bundle sets that exist
#   can be shelved.
#
# The `tool_tree` fixture is module-scoped, so these tests share one temporary tree
# and run in definition order.
##########################################################################################

import pytest

from tests.holdings_maintenance import subsets, support

pytestmark = pytest.mark.full_holdings

SOURCE_FLAVOR = 'pds4'
SOURCE_FINGERPRINTS = subsets.PDS4_METADATA_SOURCES
SOURCE_PATHS = subsets.paths_of(subsets.PDS4_METADATA_SOURCES)
SOURCE_MTIMES = subsets.PDS4_METADATA_MTIMES

METADATA_DIR = f'metadata/{subsets.PDS4_BUNDLESET}/{subsets.PDS4_BUNDLE}'
RINGS_INDEX = f'{METADATA_DIR}/{subsets.PDS4_BUNDLE}_rings_index.csv'
SHELF_DIR = f'_indexshelf-metadata/{subsets.PDS4_BUNDLESET}/{subsets.PDS4_BUNDLE}'


def test_initialize_cannot_read_a_pds4_index(tool_tree):
    """Pin the known defect: an unlabelled PDS4 .csv index cannot be shelved.

    When PR-27 gives pds4indexshelf a PDS4-aware table reader, this test must be
    replaced by the same --initialize -> golden -> --validate -> corrupt -> --repair
    cycle test_pds3_indexshelf.py runs.
    """

    run = support.run_tool(tool_tree, 'pds4indexshelf', '--initialize',
                           tool_tree.path(RINGS_INDEX))
    assert run.returncode == 1, run.describe()
    assert 'FileNotFoundError' in run.output, run.describe()
    assert not tool_tree.path(SHELF_DIR).exists(), run.describe()


def test_non_metadata_argument_is_rejected(tool_tree):
    """A path outside metadata/ is refused before any table work is attempted.

    This part of the CLI contract does work, and PR-27 must preserve it.
    """

    outside = support.add_file(
        tool_tree, f'bundles/{subsets.PDS4_BUNDLESET}/{subsets.PDS4_BUNDLE}/readme.txt',
        b'not a metadata table\n', subsets.PDS4_MTIMES[RINGS_INDEX])
    run = support.run_tool(tool_tree, 'pds4indexshelf', '--initialize', outside)
    assert run.returncode == 1, run.describe()
    assert 'Not a metadata file' in run.output, run.describe()

    outside.unlink()


def test_non_table_metadata_argument_is_rejected(tool_tree):
    """A non-.csv file inside metadata/ is refused as well."""

    other = support.add_file(tool_tree, f'{METADATA_DIR}/notes.txt',
                             b'not a table\n', subsets.PDS4_MTIMES[RINGS_INDEX])
    run = support.run_tool(tool_tree, 'pds4indexshelf', '--initialize', other)
    assert run.returncode == 1, run.describe()
    assert 'Not a table file' in run.output, run.describe()

    other.unlink()


def test_a_missing_table_is_refused(tool_tree):
    """A path that does not exist is refused before any work is done."""

    run = support.run_tool(tool_tree, 'pds4indexshelf', '--initialize',
                           tool_tree.path(f'{METADATA_DIR}/nonexistent_index.csv'))
    assert run.returncode == 1, run.describe()
    assert 'No such file or directory' in run.output, run.describe()
