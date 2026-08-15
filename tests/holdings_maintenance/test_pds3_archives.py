##########################################################################################
# tests/holdings_maintenance/test_pds3_archives.py
#
# Full task cycle for pdsarchives against a copy of one declared PDS3 subset.
#
# Archives are never compared as bytes: gzip output and os.walk order are not
# reproducible. Every comparison goes through sorted member tuples.
#
# Every test rebuilds the tree first (the `fresh_tree` fixture), so each one is
# independent and order-agnostic.
##########################################################################################

import tarfile
from collections import namedtuple

import pdslogger
import pytest

from pdsfile.holdings_maintenance import _archives_common
from pdsfile.holdings_maintenance._common import is_backup_name
from pdsfile.holdings_maintenance.pds3 import pdsarchives
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
NEW_FILE_BYTES = b'ADDED BY AN UPDATE TEST\r\n'
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


def test_initialize_writes_the_expected_archive(fresh_tree, golden_update):
    """--initialize builds a .tar.gz whose members match the committed golden."""

    support.initialize(fresh_tree, 'pdsarchives', fresh_tree.path(VOLUME_DIR))

    archive = fresh_tree.path(ARCHIVE)
    assert archive.exists()

    text = support.tar_member_text(archive)
    support.check_golden('pds3_archives_members', text, golden_update)

    # The archive really holds the declared subset, at the declared sizes and the
    # pinned modification times.
    for relpath, size, _ in SOURCE_FINGERPRINTS:
        member = relpath.partition(f'{subsets.PDS3_VOLSET}/')[2]
        assert f'{member} file {size} {SOURCE_MTIMES[relpath]}\n' in text, member


def test_initialize_refuses_to_clobber(fresh_tree):
    """A second --initialize reports the existing archive and exits non-zero."""

    support.initialize(fresh_tree, 'pdsarchives', fresh_tree.path(VOLUME_DIR))

    run = support.run_tool(fresh_tree, 'pdsarchives', '--initialize',
                           fresh_tree.path(VOLUME_DIR))
    assert run.returncode == 1, run.describe()
    assert any('Archive file already exists' in line for line in run.error_lines), \
        run.describe()


def test_validate_is_clean_after_initialize(fresh_tree):
    """--validate on an untouched tree exits 0 and logs no errors."""

    support.initialize(fresh_tree, 'pdsarchives', fresh_tree.path(VOLUME_DIR))

    run = support.run_tool(fresh_tree, 'pdsarchives', '--validate',
                           fresh_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()


@pytest.mark.parametrize('corruption', CORRUPTIONS, ids=[c.name for c in CORRUPTIONS])
def test_corruption_is_detected_and_repaired(fresh_tree, corruption):
    """Each fixed corruption fails --validate, and --repair restores a clean tree."""

    support.initialize(fresh_tree, 'pdsarchives', fresh_tree.path(VOLUME_DIR))
    corruption.damage(fresh_tree.path(corruption.target))

    run = support.run_tool(fresh_tree, 'pdsarchives', '--validate',
                           fresh_tree.path(VOLUME_DIR))
    assert run.returncode == 1, f'{corruption.description}\n{run.describe()}'
    assert any(corruption.expected in line and corruption.target.rpartition('/')[2] in line
               for line in run.error_lines), \
        f'{corruption.description}\n{run.describe()}'

    run = support.run_tool(fresh_tree, 'pdsarchives', '--repair',
                           fresh_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert 'Discrepancies found; writing new file' in run.output, run.describe()

    run = support.run_tool(fresh_tree, 'pdsarchives', '--validate',
                           fresh_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()

    # The rewritten archive carries the damaged file's current size and mtime.
    damaged = fresh_tree.path(corruption.target)
    member = corruption.target.partition(f'{subsets.PDS3_VOLSET}/')[2]
    assert (f'{member} file {damaged.stat().st_size} {int(damaged.stat().st_mtime)}\n'
            in support.tar_member_text(fresh_tree.path(ARCHIVE)))


def test_repair_is_a_no_op_when_nothing_changed(fresh_tree):
    """--repair on a matching tree cancels instead of rewriting the archive."""

    support.initialize(fresh_tree, 'pdsarchives', fresh_tree.path(VOLUME_DIR))
    before = fresh_tree.path(ARCHIVE).read_bytes()

    run = support.run_tool(fresh_tree, 'pdsarchives', '--repair',
                           fresh_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert 'Files match; repair canceled' in run.output, run.describe()
    assert fresh_tree.path(ARCHIVE).read_bytes() == before


def test_update_skips_an_existing_archive(fresh_tree):
    """--update deliberately leaves a pre-existing archive alone, even if stale.

    pdsarchives.update() returns early whenever the tar is present, so a file added
    afterwards is not picked up; --update exists to create archives for newly added
    volumes. --repair is the task that refreshes one.
    """

    support.initialize(fresh_tree, 'pdsarchives', fresh_tree.path(VOLUME_DIR))
    before = support.tar_member_names(fresh_tree.path(ARCHIVE))
    support.add_file(fresh_tree, NEW_FILE, NEW_FILE_BYTES, NEW_FILE_MTIME)

    run = support.run_tool(fresh_tree, 'pdsarchives', '--update',
                           fresh_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert 'Archive file exists; skipping' in run.output, run.describe()
    assert support.tar_member_names(fresh_tree.path(ARCHIVE)) == before

    run = support.run_tool(fresh_tree, 'pdsarchives', '--repair',
                           fresh_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    member = NEW_FILE.partition(f'{subsets.PDS3_VOLSET}/')[2]
    assert member in support.tar_member_names(fresh_tree.path(ARCHIVE)), run.describe()


def test_update_creates_a_missing_archive(fresh_tree, golden_update):
    """--update does build an archive for a volume that has none.

    The archive it builds is the same one --initialize would have built.
    """

    run = support.run_tool(fresh_tree, 'pdsarchives', '--update',
                           fresh_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert fresh_tree.path(ARCHIVE).exists(), run.describe()
    support.check_golden('pds3_archives_members',
                         support.tar_member_text(fresh_tree.path(ARCHIVE)),
                         golden_update)


##########################################################################################
# What the archive holds and what the inventory lists have to agree, and validation has
# to report every way they can disagree. Both were once true only for two of the three
# fields, and only for three of the four kinds of skipped file.
##########################################################################################

class TestArchiveAndInventoryAgree:
    """The writer's skip rule and the validator's comparison, pinned directly.

    These call the shared archive code with tuples built here rather than driving a
    tool: the defects they pin are in the comparison and in the filter rather than in
    any one tool's plumbing, and both twins reach the same two functions. The verdict
    is asserted rather than the log text, which is not frozen.
    """

    def test_an_interior_path_mismatch_fails_validation(self):
        """A member stored under the wrong name inside the archive fails validation.

        The size and the modification time match; only the interior path differs.
        That case once passed silently: the mismatch branch fired, compared the other
        two fields, logged nothing and dropped the entry, so an archive whose member
        path was wrong reported as valid.
        """

        dir_tuples = [('/holdings/volumes/V/X/FILE.LBL', 'V/X/FILE.LBL', 100, 1000)]
        tar_tuples = [('/holdings/volumes/V/X/FILE.LBL', 'V/WRONG/FILE.LBL', 100, 1000)]

        assert _archives_common.validate_tuples(pdsarchives.SPEC, dir_tuples,
                                                tar_tuples) is False

    def test_agreeing_tuples_still_validate(self):
        """The added comparison does not reject an archive that agrees."""

        tuples = [('/holdings/volumes/V/X/FILE.LBL', 'V/X/FILE.LBL', 100, 1000)]

        assert _archives_common.validate_tuples(pdsarchives.SPEC, tuples,
                                                list(tuples)) is True

    def test_the_other_two_fields_are_still_compared(self):
        """Adding the interior-path check did not displace the size or the time."""

        base = ('/holdings/volumes/V/X/FILE.LBL', 'V/X/FILE.LBL', 100, 1000)
        wrong_size = [(base[0], base[1], 101, base[3])]
        wrong_time = [(base[0], base[1], base[2], 1100)]

        assert _archives_common.validate_tuples(pdsarchives.SPEC, [base],
                                                wrong_size) is False
        assert _archives_common.validate_tuples(pdsarchives.SPEC, [base],
                                                wrong_time) is False

    def test_one_predicate_decides_what_is_a_backup(self):
        """Both shapes of backup name are recognized, and ordinary names are not."""

        for name in ('FILE_2021-01-01T00-00-00.LBL', 'FILE_backup.LBL',
                     'FILE_original.LBL', 'FILE copy.LBL'):
            assert is_backup_name(name), name

        assert not is_backup_name('FILE.LBL')
        assert not is_backup_name('N4BI01L4Q.ASC')

    def test_the_writer_skips_a_backup_file(self):
        """The filter itself drops it, not merely the predicate it consults.

        `load_directory_info()` has always treated a backup file as an error and left
        it out of the inventory; the writer archived it anyway, so an archive held a
        file its own listing omitted. Asserting the predicate alone would not have
        caught that, because the predicate was never the broken half.
        """

        logger = pdslogger.PdsLogger.get_logger('test.archives.filter')
        archive_filter = _archives_common.make_archive_filter(
            pdsarchives.SPEC, logger, archive_invisibles=False)

        backup = tarfile.TarInfo('V/X/FILE copy.LBL')
        ordinary = tarfile.TarInfo('V/X/FILE.LBL')

        assert archive_filter(backup) is None
        assert archive_filter(ordinary) is ordinary
