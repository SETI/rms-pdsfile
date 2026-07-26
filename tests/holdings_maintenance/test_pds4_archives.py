##########################################################################################
# tests/holdings_maintenance/test_pds4_archives.py
#
# pds4archives against a copy of one declared PDS4 subset.
#
# This module cannot run the full init -> validate -> repair cycle its pds3 twin
# runs, because pds4archives cannot round-trip today and dies on a bundle path.
# Both defects are pinned here rather than fixed; see entries 1 and 2 of
# "From PR-13" in critiques/deferred-observations.md.
#
# Every test rebuilds the tree first, so each one is independent and order-agnostic.
##########################################################################################

import pytest

from tests.holdings_maintenance import subsets, support

pytestmark = pytest.mark.full_holdings

SOURCE_FLAVOR = 'pds4'
SOURCE_FINGERPRINTS = subsets.PDS4_BUNDLE_SOURCES
SOURCE_PATHS = subsets.paths_of(subsets.PDS4_BUNDLE_SOURCES)
SOURCE_MTIMES = subsets.PDS4_BUNDLE_MTIMES

BUNDLESET_DIR = f'bundles/{subsets.PDS4_BUNDLESET}'
BUNDLE_DIR = f'{BUNDLESET_DIR}/{subsets.PDS4_BUNDLE}'
ARCHIVE = (f'archives-bundles/{subsets.PDS4_BUNDLESET}/'
           f'{subsets.PDS4_BUNDLESET}.tar.gz')


@pytest.fixture
def archived_tree(fresh_tree):
    """A freshly rebuilt tree with the bundle-set archive already written."""

    support.initialize(fresh_tree, 'pds4archives', fresh_tree.path(BUNDLESET_DIR))

    return fresh_tree


def test_initialize_on_a_bundle_raises(fresh_tree):
    """Pointing the tool at a bundle hits a bare `raise` and dies.

    This bundle set defines archives at the bundle-set level only, so a bundle path
    resolves to no archive path and takes the broken branch. Pinned as current
    behaviour; see entry 2 of "From PR-13" in critiques/deferred-observations.md.
    """

    run = support.run_tool(fresh_tree, 'pds4archives', '--initialize',
                           fresh_tree.path(BUNDLE_DIR))
    assert run.returncode == 1, run.describe()
    assert 'No active exception to reraise' in run.output, run.describe()
    assert 'No archive paths resolved for' in run.output, run.describe()
    assert not fresh_tree.path(ARCHIVE).exists(), run.describe()


def test_initialize_on_the_bundleset_writes_the_expected_archive(fresh_tree,
                                                                 golden_update):
    """--initialize on the bundle set builds a .tar.gz matching the golden members."""

    support.initialize(fresh_tree, 'pds4archives', fresh_tree.path(BUNDLESET_DIR))

    archive = fresh_tree.path(ARCHIVE)
    assert archive.exists()

    text = support.tar_member_text(archive)
    support.check_golden('pds4_archives_members', text, golden_update)

    # The archive really holds the declared subset, at the declared sizes and the
    # pinned modification times.
    for relpath, size, _ in SOURCE_FINGERPRINTS:
        member = relpath.partition(f'{subsets.PDS4_BUNDLESET}/')[2]
        assert (f'{subsets.PDS4_BUNDLESET}/{member} file {size} '
                f'{SOURCE_MTIMES[relpath]}\n') in text, member


def test_validate_cannot_round_trip(archived_tree):
    """--validate fails immediately after a successful --initialize.

    Members are written relative to the bundle-set basename but read back with a
    prefix that already ends at the bundle set, so every member is reported twice
    over: once as missing from the tar (its real path) and once as missing from the
    directory (a doubled path). Pinned as current behaviour; see entry 1 of
    "From PR-13" in critiques/deferred-observations.md.
    """

    run = support.run_tool(archived_tree, 'pds4archives', '--validate',
                           archived_tree.path(BUNDLESET_DIR))
    assert run.returncode == 1, run.describe()

    missing_from_tar = [line for line in run.error_lines
                        if 'Missing from tar file' in line]
    missing_from_dir = [line for line in run.error_lines
                        if 'Missing from directory' in line]
    assert missing_from_tar, run.describe()
    assert missing_from_dir, run.describe()

    doubled = f'{subsets.PDS4_BUNDLESET}/{subsets.PDS4_BUNDLESET}'
    assert all(doubled in line for line in missing_from_dir), run.describe()
    assert not any(doubled in line for line in missing_from_tar), run.describe()

    # Every declared source file is caught up in it, in both directions.
    for relpath, _, _ in SOURCE_FINGERPRINTS:
        name = relpath.rpartition('/')[2]
        assert any(name in line for line in missing_from_tar), name
        assert any(name in line for line in missing_from_dir), name


def test_initialize_refuses_to_clobber(archived_tree):
    """A second --initialize reports the existing archive and exits non-zero."""

    before = archived_tree.path(ARCHIVE).read_bytes()

    run = support.run_tool(archived_tree, 'pds4archives', '--initialize',
                           archived_tree.path(BUNDLESET_DIR))
    assert run.returncode == 1, run.describe()
    assert any('Archive file already exists' in line for line in run.error_lines), \
        run.describe()
    assert archived_tree.path(ARCHIVE).read_bytes() == before
