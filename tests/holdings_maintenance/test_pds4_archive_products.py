##########################################################################################
# tests/holdings_maintenance/test_pds4_archive_products.py
#
# The PDS4 archive-side products can actually be built: an archive checksum file
# under checksums-archives-bundles/ and an archive info shelf under
# _infoshelf-archives-bundles/, in the order the dependency rules require
# (archive -> its checksum -> its info shelf).
#
# Every route to these products resolves the checksum file's own path,
# checksums-archives-bundles/<set>_md5.txt, through Pds4File.child, and that
# name used to fail BUNDLESET_PLUS_REGEX (no ending after a bundle-set name),
# so pds4checksums and pds4infoshelf died in a raw ValueError on every
# archives-side target and neither product could be built at all (observation
# 4062). These tests drive both tools through the previously fatal routes
# against the module's temporary tree; the regex itself, both directions, is
# pinned in tests/pds4file/test_pds4file_bundleset_plus.py.
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
ARCHIVES_DIR = f'archives-bundles/{subsets.PDS4_BUNDLESET}'
ARCHIVE = f'{ARCHIVES_DIR}/{subsets.PDS4_BUNDLESET}.tar.gz'
CHECKSUM_FILE = f'checksums-archives-bundles/{subsets.PDS4_BUNDLESET}_md5.txt'
SHELF_DIR = '_infoshelf-archives-bundles'
PICKLE = f'{SHELF_DIR}/{subsets.PDS4_BUNDLESET}_info.pickle'
SIDECAR = f'{SHELF_DIR}/{subsets.PDS4_BUNDLESET}_info.py'


@pytest.fixture
def archived_tree(fresh_tree):
    """A freshly rebuilt tree with the bundle-set archive already written."""

    support.initialize(fresh_tree, 'pds4archives', fresh_tree.path(BUNDLESET_DIR))
    assert fresh_tree.path(ARCHIVE).exists()

    return fresh_tree


def test_checksums_over_the_archives_writes_the_archive_checksum(archived_tree):
    """--initialize over archives-bundles/<set> builds the archive checksum file."""

    run = support.run_tool(archived_tree, 'pds4checksums', '--initialize',
                           archived_tree.path(ARCHIVES_DIR))
    assert run.returncode == 0, run.describe()
    assert 'Traceback' not in run.stderr, run.describe()

    checksum_path = archived_tree.path(CHECKSUM_FILE)
    assert checksum_path.exists(), run.describe()

    mapping = support.md5_file_mapping(checksum_path)
    key = f'{subsets.PDS4_BUNDLESET}.tar.gz'
    assert key in mapping, run.describe()
    assert mapping[key] == support.md5_of(archived_tree.path(ARCHIVE))


def test_checksums_archives_flag_reaches_the_same_file(archived_tree):
    """--initialize --archives over bundles/<set> builds the same checksum file."""

    run = support.run_tool(archived_tree, 'pds4checksums', '--initialize',
                           '--archives', archived_tree.path(BUNDLESET_DIR))
    assert run.returncode == 0, run.describe()
    assert 'Traceback' not in run.stderr, run.describe()

    mapping = support.md5_file_mapping(archived_tree.path(CHECKSUM_FILE))
    assert mapping == {f'{subsets.PDS4_BUNDLESET}.tar.gz':
                       support.md5_of(archived_tree.path(ARCHIVE))}


def test_infoshelf_over_the_archives_writes_the_archive_info_shelf(archived_tree):
    """--initialize over archives-bundles/<set> builds the archive info shelf.

    pds4infoshelf reads the checksum file its target is covered by, so the
    archive checksum is built first, dogfooding the tool the test above covers.
    """

    support.initialize(archived_tree, 'pds4checksums',
                       archived_tree.path(ARCHIVES_DIR))

    run = support.run_tool(archived_tree, 'pds4infoshelf', '--initialize',
                           archived_tree.path(ARCHIVES_DIR))
    assert run.returncode == 0, run.describe()
    assert 'Traceback' not in run.stderr, run.describe()

    pickle_path = archived_tree.path(PICKLE)
    sidecar_path = archived_tree.path(SIDECAR)
    assert pickle_path.exists(), run.describe()
    assert sidecar_path.exists(), run.describe()

    # The shelf actually describes the archive: its sidecar records the
    # tar file at the size the tree holds.
    text = sidecar_path.read_text()
    tar_line = next((line for line in text.splitlines()
                     if f'{subsets.PDS4_BUNDLESET}.tar.gz' in line), None)
    assert tar_line is not None, text
    size = archived_tree.path(ARCHIVE).stat().st_size
    assert str(size) in tar_line, tar_line
