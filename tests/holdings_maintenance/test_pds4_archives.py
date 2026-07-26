##########################################################################################
# tests/holdings_maintenance/test_pds4_archives.py
#
# pds4archives against a copy of one declared PDS4 subset.
#
# This module cannot run the full init -> validate -> repair cycle its pds3 twin
# runs, because pds4archives cannot round-trip today. Both defects are pinned here
# rather than fixed (PR-13 is behavior-preserving; PR-25 owns the archives pair):
#
#   1. write_archive() adds members with `arcname=<bundle-set basename>`
#      (pds4archives.py:238-241), while read_archive_info() rebuilds each member's
#      path with the prefix that already ends at the bundle set
#      (pds4archives.py:126-135, via dirpath_and_prefix_for_archive). Every member
#      therefore comes back doubled -- bundles/<bs>/<bs>/... -- so --validate
#      reports every file as both "Missing from tar file" and "Missing from
#      directory" and exits 1 immediately after a successful --initialize. The
#      complete holdings set's archives-bundles/<bs>/ directory is empty, i.e. this
#      has never round-tripped in production either.
#   2. Pointed at a *bundle* rather than a bundle set, write_archive() takes its
#      "no archive paths resolved" branch, which is a bare `raise` outside any
#      except block (pds4archives.py:214-218) and dies with
#      "RuntimeError: No active exception to reraise".
#
# The `tool_tree` fixture is module-scoped, so these tests share one temporary tree
# and run in definition order.
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


def test_initialize_on_a_bundle_raises(tool_tree):
    """Pin defect 2: pointing the tool at a bundle hits a bare `raise`.

    uranus_occs_earthbased defines archives at the bundle-set level only, so the
    bundle path resolves to no archive path and takes the broken branch. PR-25 must
    replace that bare `raise` with a real error; when it does, this pin must change.
    """

    run = support.run_tool(tool_tree, 'pds4archives', '--initialize',
                           tool_tree.path(BUNDLE_DIR))
    assert run.returncode == 1, run.describe()
    assert 'No active exception to reraise' in run.output, run.describe()
    assert 'No archive paths resolved for' in run.output, run.describe()
    assert not tool_tree.path(ARCHIVE).exists(), run.describe()


def test_initialize_on_the_bundleset_writes_the_expected_archive(tool_tree,
                                                                 golden_update):
    """--initialize on the bundle set builds a .tar.gz matching the golden members."""

    run = support.run_tool(tool_tree, 'pds4archives', '--initialize',
                           tool_tree.path(BUNDLESET_DIR))
    assert run.returncode == 0, run.describe()

    archive = tool_tree.path(ARCHIVE)
    assert archive.exists(), run.describe()

    support.check_golden('pds4_archives_members', support.tar_member_text(archive),
                         golden_update)

    # The archive really holds the declared subset, at the declared sizes.
    text = support.tar_member_text(archive)
    for relpath, size, _ in SOURCE_FINGERPRINTS:
        member = relpath.partition(f'{subsets.PDS4_BUNDLESET}/')[2]
        assert f'{subsets.PDS4_BUNDLESET}/{member} file {size} ' in text, member


def test_validate_cannot_round_trip(tool_tree):
    """Pin defect 1: --validate fails immediately after a successful --initialize.

    Every member is reported twice over -- once as missing from the tar (the real
    path) and once as missing from the directory (the doubled path). PR-25 must
    make this cycle clean; when it does, this pin must be replaced by the same
    init -> validate -> corrupt -> repair cycle the pds3 archives tests run.
    """

    run = support.run_tool(tool_tree, 'pds4archives', '--validate',
                           tool_tree.path(BUNDLESET_DIR))
    assert run.returncode == 1, run.describe()

    missing_from_tar = [line for line in run.error_lines if 'Missing from tar file' in line]
    missing_from_dir = [line for line in run.error_lines
                        if 'Missing from directory' in line]
    assert missing_from_tar, run.describe()
    assert missing_from_dir, run.describe()

    doubled = f'{subsets.PDS4_BUNDLESET}/{subsets.PDS4_BUNDLESET}'
    assert all(doubled in line for line in missing_from_dir), run.describe()
    assert not any(doubled in line for line in missing_from_tar), run.describe()


def test_initialize_refuses_to_clobber(tool_tree):
    """A second --initialize reports the existing archive and exits non-zero."""

    run = support.run_tool(tool_tree, 'pds4archives', '--initialize',
                           tool_tree.path(BUNDLESET_DIR))
    assert run.returncode == 1, run.describe()
    assert any('Archive file already exists' in line for line in run.error_lines), \
        run.describe()
