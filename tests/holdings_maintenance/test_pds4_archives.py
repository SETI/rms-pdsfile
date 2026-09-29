##########################################################################################
# tests/holdings_maintenance/test_pds4_archives.py
#
# pds4archives against a copy of one declared PDS4 subset.
#
# This module cannot run the full init -> validate -> repair cycle its pds3 twin
# runs, because pds4archives cannot round-trip today and dies on a bundle path.
# Both defects are pinned here rather than fixed; each is described at the test
# that pins it.
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
    resolves to no archive path and takes the "no archive paths resolved" branch,
    which is a bare `raise` outside any `except`. That is a defect, pinned here as
    current behaviour: a fix has to invert these assertions deliberately.
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


def test_validate_round_trips(archived_tree):
    """--validate succeeds immediately after a successful --initialize.

    This assertion is the inverse of what it used to be, changed deliberately. Members
    are written relative to the packaged directory's basename; the reader used to
    rebuild them against a prefix that already ended at the bundle set, so every member
    was reported twice over -- once as missing from the tar under its real path, once as
    missing from the directory under a doubled one -- and the archive had never
    round-tripped, in production either. The reader now takes its anchor from the same
    archive_dirs table the writer used.
    """

    run = support.run_tool(archived_tree, 'pds4archives', '--validate',
                           archived_tree.path(BUNDLESET_DIR))
    assert run.returncode == 0, run.describe()

    for phrase in ('Missing from tar file', 'Missing from directory',
                   'Interior path mismatch'):
        assert not [line for line in run.error_lines if phrase in line], run.describe()

    assert not run.error_lines, run.describe()

    # Every declared source file was seen, so the run validated the tree rather than
    # walking an empty one.
    for relpath, _, _ in SOURCE_FINGERPRINTS:
        name = relpath.rpartition('/')[2]
        assert name in run.output, name


def test_repair_cancels_when_the_archive_matches(archived_tree):
    """--repair over an intact archive does nothing, and says so.

    This is a stricter check than validation passing. repair() cancels only when the
    sorted tuple lists are exactly equal, so while the reader and the writer disagreed
    about where a member name is anchored, repair rewrote every archive on every run --
    intact or not, and write_archive(clobber=True) overwrites in place with no versioned
    copy kept. Validation could have been made to report cleanly while that was still
    true, which is why this asserts the cancellation rather than the absence of errors.
    """

    before = archived_tree.path(ARCHIVE).read_bytes()

    run = support.run_tool(archived_tree, 'pds4archives', '--repair',
                           archived_tree.path(BUNDLESET_DIR))
    assert run.returncode == 0, run.describe()
    assert 'repair canceled' in run.output, run.describe()
    assert 'writing new file' not in run.output, run.describe()
    assert archived_tree.path(ARCHIVE).read_bytes() == before


def test_initialize_refuses_to_clobber(archived_tree):
    """A second --initialize reports the existing archive and exits non-zero."""

    before = archived_tree.path(ARCHIVE).read_bytes()

    run = support.run_tool(archived_tree, 'pds4archives', '--initialize',
                           archived_tree.path(BUNDLESET_DIR))
    assert run.returncode == 1, run.describe()
    assert any('Archive file already exists' in line for line in run.error_lines), \
        run.describe()
    assert archived_tree.path(ARCHIVE).read_bytes() == before
