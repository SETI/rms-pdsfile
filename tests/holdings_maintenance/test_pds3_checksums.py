##########################################################################################
# tests/holdings_maintenance/test_pds3_checksums.py
#
# Full task cycle for pdschecksums against a copy of one declared PDS3 subset:
# --initialize -> golden -> --validate clean -> corrupt -> --validate reports it ->
# --repair -> --validate clean -> --update after a new file.
#
# Every test rebuilds the tree first (the `fresh_tree` fixture), so each one is
# independent and order-agnostic.
#
# pdschecksums reports failure in the log, not the exit code: main() computes a
# failure flag and never passes it to sys.exit. The tests below pin that as current
# behavior rather than assert the exit code the other tools use
# (support.TOOLS_WITHOUT_EXIT_STATUS).
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
CHECKSUM_FILE = f'checksums-volumes/{subsets.PDS3_VOLSET}/{subsets.PDS3_VOLUME}_md5.txt'
LABEL = f'{VOLUME_DIR}/DATA/VISIT_01/N4BI01L4Q.LBL'
ASCII_TABLE = f'{VOLUME_DIR}/DATA/VISIT_01/N4BI01L4Q.ASC'
PREVIEW = f'{VOLUME_DIR}/DATA/VISIT_01/N4BI01L4Q_CAL.JPG'

# A file the --update test adds, with a pinned modification time.
NEW_FILE = f'{VOLUME_DIR}/DATA/VISIT_01/N4BI01L4Q_EXTRA.TXT'
NEW_FILE_BYTES = b'ADDED BY AN UPDATE TEST\r\n'
NEW_FILE_MTIME = subsets.PDS3_MTIMES[LABEL] + 1000

ERROR_EXIT = support.expected_error_exit_code('pdschecksums')

Corruption = namedtuple('Corruption', 'name description target damage expected')

# Fixed corruption scenarios. Nothing here is randomized or discovered at run time.
CORRUPTIONS = (
    Corruption('label_byte0',
               'overwrite byte 0 of the detached label with 0xFF',
               LABEL, support.overwrite_first_byte, 'Checksum mismatch'),
    Corruption('ascii_truncated',
               'truncate the ASCII table to 100 bytes',
               ASCII_TABLE, lambda path: support.truncate_file(path, 100),
               'Checksum mismatch'),
)


def test_initialize_writes_the_expected_checksum_file(fresh_tree, golden_update):
    """--initialize from scratch produces the committed md5 golden."""

    support.initialize(fresh_tree, 'pdschecksums', fresh_tree.path(VOLUME_DIR))

    checksum_path = fresh_tree.path(CHECKSUM_FILE)
    assert checksum_path.exists()

    support.check_golden('pds3_checksums_md5', support.md5_file_text(checksum_path),
                         golden_update)

    # The golden is a real mapping, not an opaque blob: every declared source file
    # appears with exactly the md5 the source table declares.
    mapping = support.md5_file_mapping(checksum_path)
    for relpath, _, md5 in SOURCE_FINGERPRINTS:
        key = relpath.partition(f'{subsets.PDS3_VOLSET}/')[2]
        assert mapping[key] == md5, f'{relpath}: {mapping[key]} != {md5}'
    assert len(mapping) == len(SOURCE_FINGERPRINTS)


def test_initialize_refuses_to_clobber(fresh_tree):
    """A second --initialize is an error, and leaves the checksum file alone."""

    support.initialize(fresh_tree, 'pdschecksums', fresh_tree.path(VOLUME_DIR))
    before = fresh_tree.path(CHECKSUM_FILE).read_bytes()

    run = support.run_tool(fresh_tree, 'pdschecksums', '--initialize',
                           fresh_tree.path(VOLUME_DIR))
    assert any('Checksum file already exists' in line for line in run.error_lines), \
        run.describe()
    assert run.returncode == ERROR_EXIT, run.describe()
    assert fresh_tree.path(CHECKSUM_FILE).read_bytes() == before


def test_validate_is_clean_after_initialize(fresh_tree):
    """--validate on an untouched tree exits 0 and logs no errors."""

    support.initialize(fresh_tree, 'pdschecksums', fresh_tree.path(VOLUME_DIR))

    run = support.run_tool(fresh_tree, 'pdschecksums', '--validate',
                           fresh_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()


@pytest.mark.parametrize('corruption', CORRUPTIONS, ids=[c.name for c in CORRUPTIONS])
def test_corruption_is_detected_and_repaired(fresh_tree, corruption):
    """Each fixed corruption is reported by --validate; --repair restores a clean tree."""

    support.initialize(fresh_tree, 'pdschecksums', fresh_tree.path(VOLUME_DIR))
    corruption.damage(fresh_tree.path(corruption.target))

    run = support.run_tool(fresh_tree, 'pdschecksums', '--validate',
                           fresh_tree.path(VOLUME_DIR))
    assert any(corruption.expected in line and corruption.target.rpartition('/')[2] in line
               for line in run.error_lines), \
        f'{corruption.description}\n{run.describe()}'
    assert run.returncode == ERROR_EXIT, run.describe()

    run = support.run_tool(fresh_tree, 'pdschecksums', '--repair',
                           fresh_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()

    run = support.run_tool(fresh_tree, 'pdschecksums', '--validate',
                           fresh_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()

    # The repaired file really carries the damaged file's new checksum.
    mapping = support.md5_file_mapping(fresh_tree.path(CHECKSUM_FILE))
    key = corruption.target.partition(f'{subsets.PDS3_VOLSET}/')[2]
    assert mapping[key] == support.md5_of(fresh_tree.path(corruption.target))


def test_missing_file_is_reported_as_a_missing_checksum(fresh_tree):
    """Deleting an md5 entry makes --validate report the file as unchecksummed."""

    support.initialize(fresh_tree, 'pdschecksums', fresh_tree.path(VOLUME_DIR))
    support.delete_md5_entry(fresh_tree.path(CHECKSUM_FILE), PREVIEW.rpartition('/')[2])

    run = support.run_tool(fresh_tree, 'pdschecksums', '--validate',
                           fresh_tree.path(VOLUME_DIR))
    assert any('Missing checksum' in line and PREVIEW.rpartition('/')[2] in line
               for line in run.error_lines), run.describe()
    assert run.returncode == ERROR_EXIT, run.describe()


def test_update_picks_up_a_new_file(fresh_tree):
    """--update adds a newly created file to an existing checksum file."""

    support.initialize(fresh_tree, 'pdschecksums', fresh_tree.path(VOLUME_DIR))
    before = support.md5_file_mapping(fresh_tree.path(CHECKSUM_FILE))
    support.add_file(fresh_tree, NEW_FILE, NEW_FILE_BYTES, NEW_FILE_MTIME)

    run = support.run_tool(fresh_tree, 'pdschecksums', '--update',
                           fresh_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()

    after = support.md5_file_mapping(fresh_tree.path(CHECKSUM_FILE))
    key = NEW_FILE.partition(f'{subsets.PDS3_VOLSET}/')[2]
    assert key in after, run.describe()
    assert after[key] == support.md5_of(fresh_tree.path(NEW_FILE))
    assert set(before) < set(after)
    for old_key, old_md5 in before.items():
        assert after[old_key] == old_md5, f'{old_key} changed during --update'


def test_reinitialize_versions_the_checksum_file_it_replaces(fresh_tree):
    """--reinitialize copies the superseded checksum file into the log directory.

    move_old_checksums() versions the file the task is about to overwrite, as
    <name>_v###.txt beside the run's own log file, one past the highest version
    already there. It reads the module-level LOGDIRS list that main() fills in, so
    a tool whose main() shadows that list with a local versions nothing; this test
    is what makes that visible, here and in the pds4 twin.
    """

    support.initialize(fresh_tree, 'pdschecksums', fresh_tree.path(VOLUME_DIR))
    first = fresh_tree.path(CHECKSUM_FILE).read_bytes()

    run = support.run_tool(fresh_tree, 'pdschecksums', '--reinitialize',
                           fresh_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert 'Checksum file moved from: ' in run.output, run.describe()
    assert 'Checksum file moved to' in run.output, run.describe()

    logs = fresh_tree.disk / 'logs'
    versions = sorted(p.name for p in logs.rglob(f'{subsets.PDS3_VOLUME}_md5_v*.txt'))
    assert versions == [f'{subsets.PDS3_VOLUME}_md5_v001.txt'], run.describe()

    versioned = next(logs.rglob(versions[0]))
    assert versioned.read_bytes() == first
    assert fresh_tree.path(CHECKSUM_FILE).exists()

    # A second run versions the file the first run left, rather than overwriting
    # the copy it made.
    run = support.run_tool(fresh_tree, 'pdschecksums', '--reinitialize',
                           fresh_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()

    versions = sorted(p.name for p in logs.rglob(f'{subsets.PDS3_VOLUME}_md5_v*.txt'))
    assert versions == [f'{subsets.PDS3_VOLUME}_md5_v001.txt',
                        f'{subsets.PDS3_VOLUME}_md5_v002.txt'], run.describe()
