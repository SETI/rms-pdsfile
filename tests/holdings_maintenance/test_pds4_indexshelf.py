##########################################################################################
# tests/holdings_maintenance/test_pds4_indexshelf.py
#
# pds4indexshelf against a copy of the declared PDS4 metadata subset.
#
# This module cannot run the task cycle its pds3 twin runs, because pds4indexshelf
# reads its tables through a PDS3 detached-label reader and so cannot shelve any
# PDS4 metadata table that exists today. Pinned rather than fixed; see entry 3 of
# "From PR-13" in critiques/deferred-observations.md.
#
# Every test rebuilds the tree first, so each one is independent and order-agnostic.
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


def test_initialize_cannot_read_a_pds4_index(fresh_tree):
    """An unlabelled PDS4 .csv index cannot be shelved.

    Pinned as current behaviour; see entry 3 of "From PR-13" in
    critiques/deferred-observations.md. When the tool gains a PDS4-aware table
    reader, this test must be replaced by the same cycle test_pds3_indexshelf.py
    runs.
    """

    run = support.run_tool(fresh_tree, 'pds4indexshelf', '--initialize',
                           fresh_tree.path(RINGS_INDEX))
    assert run.returncode == 1, run.describe()
    assert 'FileNotFoundError' in run.output, run.describe()
    assert not fresh_tree.path(SHELF_DIR).exists(), run.describe()


def test_non_metadata_argument_is_rejected(fresh_tree):
    """A path outside metadata/ is refused before any table work is attempted.

    This part of the CLI contract does work, and the Phase 6 consolidation must
    preserve it.
    """

    outside = support.add_file(
        fresh_tree, f'bundles/{subsets.PDS4_BUNDLESET}/{subsets.PDS4_BUNDLE}/stray.csv',
        b'not a metadata table\n', SOURCE_MTIMES[RINGS_INDEX])
    run = support.run_tool(fresh_tree, 'pds4indexshelf', '--initialize', outside)
    assert run.returncode == 1, run.describe()
    assert 'Not a metadata file' in run.output, run.describe()


def test_non_table_metadata_argument_is_rejected(fresh_tree):
    """A non-.csv file inside metadata/ is refused as well."""

    other = support.add_file(fresh_tree, f'{METADATA_DIR}/notes.txt',
                             b'not a table\n', SOURCE_MTIMES[RINGS_INDEX])
    run = support.run_tool(fresh_tree, 'pds4indexshelf', '--initialize', other)
    assert run.returncode == 1, run.describe()
    assert 'Not a table file' in run.output, run.describe()


def test_a_missing_table_is_refused(fresh_tree):
    """A path that does not exist is refused before any work is done."""

    run = support.run_tool(fresh_tree, 'pds4indexshelf', '--initialize',
                           fresh_tree.path(f'{METADATA_DIR}/nonexistent_index.csv'))
    assert run.returncode == 1, run.describe()
    assert 'No such file or directory' in run.output, run.describe()
