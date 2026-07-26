##########################################################################################
# tests/holdings_maintenance/test_pds3_archives.py
#
# Full task cycle for pdsarchives against a copy of one declared PDS3 subset.
#
# Archives are never compared as bytes: gzip output and os.walk order are not
# reproducible. Every comparison goes through sorted member tuples
# (support.tar_member_text).
#
# The `tool_tree` fixture is module-scoped, so these tests share one temporary tree
# and run in definition order; every mutating test restores a clean tree.
##########################################################################################

from collections import namedtuple

import pytest

from tests.holdings_maintenance import subsets, support

pytestmark = pytest.mark.full_holdings

SOURCE_FLAVOR = 'pds3'
SOURCE_FINGERPRINTS = subsets.PDS3_VOLUME_SOURCES
SOURCE_PATHS = subsets.paths_of(subsets.PDS3_VOLUME_SOURCES)
SOURCE_MTIMES = subsets.PDS3_VOLUME_MTIMES

VOLUME_DIR = f'volumes/{subsets.PDS3_VOLSET}/{subsets.PDS3_VOLUME}'
ARCHIVE = f'archives-volumes/{subsets.PDS3_VOLSET}/{subsets.PDS3_VOLUME}.tar.gz'
LABEL = f'{VOLUME_DIR}/DATA/VISIT_01/N4BI01L4Q.LBL'
ASCII_TABLE = f'{VOLUME_DIR}/DATA/VISIT_01/N4BI01L4Q.ASC'

NEW_FILE = f'{VOLUME_DIR}/DATA/VISIT_01/N4BI01L4Q_EXTRA.TXT'
NEW_FILE_BYTES = b'ADDED BY THE PDS-13 UPDATE TEST\r\n'
NEW_FILE_MTIME = subsets.PDS3_MTIMES[LABEL] + 1000

Corruption = namedtuple('Corruption', 'name description target damage expected')

# Fixed corruption scenarios. pdsarchives compares byte counts and modification
# times against the tar members; it does not compare content.
CORRUPTIONS = (
    Corruption('label_mtime_plus_100',
               'move the detached label mtime forward by 100 seconds',
               LABEL, lambda path: support.shift_mtime(path, 100),
               'Modification time mismatch'),
    Corruption('ascii_truncated',
               'truncate the ASCII table to 100 bytes',
               ASCII_TABLE, lambda path: support.truncate_file(path, 100),
               'Byte count mismatch'),
)


def repin_mtimes(tree):
    """Restore every declared source file's pinned modification time."""

    for relpath, mtime in SOURCE_MTIMES.items():
        path = tree.path(relpath)
        if path.exists():
            support.shift_mtime(path, mtime - path.stat().st_mtime)


def test_initialize_writes_the_expected_archive(tool_tree, golden_update):
    """--initialize builds a .tar.gz whose members match the committed golden."""

    run = support.run_tool(tool_tree, 'pdsarchives', '--initialize',
                           tool_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()

    archive = tool_tree.path(ARCHIVE)
    assert archive.exists(), run.describe()

    support.check_golden('pds3_archives_members', support.tar_member_text(archive),
                         golden_update)

    # The archive really holds the declared subset, at the declared sizes.
    names = support.tar_member_names(archive)
    for relpath, size, _ in SOURCE_FINGERPRINTS:
        member = relpath.partition(f'{subsets.PDS3_VOLSET}/')[2]
        assert member in names, run.describe()
        assert f'{member} file {size} ' in support.tar_member_text(archive)


def test_initialize_refuses_to_clobber(tool_tree):
    """A second --initialize reports the existing archive and exits non-zero."""

    run = support.run_tool(tool_tree, 'pdsarchives', '--initialize',
                           tool_tree.path(VOLUME_DIR))
    assert run.returncode == 1, run.describe()
    assert any('Archive file already exists' in line for line in run.error_lines), \
        run.describe()


def test_validate_is_clean_after_initialize(tool_tree):
    """--validate on an untouched tree exits 0 and logs no errors."""

    run = support.run_tool(tool_tree, 'pdsarchives', '--validate',
                           tool_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()


@pytest.mark.parametrize('corruption', CORRUPTIONS, ids=[c.name for c in CORRUPTIONS])
def test_corruption_is_detected_and_repaired(tool_tree, corruption):
    """Each fixed corruption fails --validate, and --repair restores a clean tree."""

    target = tool_tree.path(corruption.target)
    original = target.read_bytes()
    corruption.damage(target)

    run = support.run_tool(tool_tree, 'pdsarchives', '--validate',
                           tool_tree.path(VOLUME_DIR))
    assert run.returncode == 1, f'{corruption.description}\n{run.describe()}'
    assert any(corruption.expected in line and corruption.target.rpartition('/')[2] in line
               for line in run.error_lines), \
        f'{corruption.description}\n{run.describe()}'

    run = support.run_tool(tool_tree, 'pdsarchives', '--repair',
                           tool_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert 'Discrepancies found; writing new file' in run.output, run.describe()

    run = support.run_tool(tool_tree, 'pdsarchives', '--validate',
                           tool_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()

    # Restore the pristine subset, then rebuild the archive for the next test.
    target.write_bytes(original)
    repin_mtimes(tool_tree)
    run = support.run_tool(tool_tree, 'pdsarchives', '--repair',
                           tool_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()


def test_repair_is_a_no_op_when_nothing_changed(tool_tree):
    """--repair on a matching tree cancels instead of rewriting the archive."""

    run = support.run_tool(tool_tree, 'pdsarchives', '--repair',
                           tool_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert 'Files match; repair canceled' in run.output, run.describe()


def test_update_skips_an_existing_archive(tool_tree):
    """--update deliberately leaves a pre-existing archive alone, even if stale.

    This pins current behavior: pdsarchives.update() returns early with "Archive
    file exists; skipping" whenever the tar is present, so a file added afterwards
    is NOT picked up. --update exists to create archives for newly added volumes.
    """

    before = support.tar_member_names(tool_tree.path(ARCHIVE))
    support.add_file(tool_tree, NEW_FILE, NEW_FILE_BYTES, NEW_FILE_MTIME)

    run = support.run_tool(tool_tree, 'pdsarchives', '--update',
                           tool_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert 'Archive file exists; skipping' in run.output, run.describe()
    assert support.tar_member_names(tool_tree.path(ARCHIVE)) == before

    # A --repair, by contrast, does pick the new file up.
    run = support.run_tool(tool_tree, 'pdsarchives', '--repair',
                           tool_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    member = NEW_FILE.partition(f'{subsets.PDS3_VOLSET}/')[2]
    assert member in support.tar_member_names(tool_tree.path(ARCHIVE)), run.describe()
