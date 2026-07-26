##########################################################################################
# tests/holdings_maintenance/test_pds3_checksums.py
#
# Full task cycle for pdschecksums against a copy of one declared PDS3 subset:
# --initialize -> golden -> --validate clean -> corrupt -> --validate fails with the
# right log text -> --repair -> --validate clean -> --update after a new file.
#
# The `tool_tree` fixture is module-scoped, so these tests share one temporary tree
# and run in definition order. Every mutating test restores a clean tree before it
# returns, so only the final --update test leaves the tree changed.
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

# A file added by the --update test, with a pinned modification time.
NEW_FILE = f'{VOLUME_DIR}/DATA/VISIT_01/N4BI01L4Q_EXTRA.TXT'
NEW_FILE_BYTES = b'ADDED BY THE PDS-13 UPDATE TEST\r\n'
NEW_FILE_MTIME = subsets.PDS3_MTIMES[LABEL] + 1000

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


def repin_mtimes(tree):
    """Restore every declared source file's pinned modification time."""

    for relpath, mtime in SOURCE_MTIMES.items():
        path = tree.path(relpath)
        if path.exists():
            support.shift_mtime(path, mtime - path.stat().st_mtime)


def test_initialize_writes_the_expected_checksum_file(tool_tree, golden_update):
    """--initialize from scratch produces the committed md5 golden."""

    run = support.run_tool(tool_tree, 'pdschecksums', '--initialize',
                           tool_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()

    checksum_path = tool_tree.path(CHECKSUM_FILE)
    assert checksum_path.exists(), run.describe()

    support.check_golden('pds3_checksums_md5', support.md5_file_text(checksum_path),
                         golden_update)

    # The golden is a real mapping, not an opaque blob: every declared source file
    # appears with exactly the md5 the source table declares.
    mapping = support.md5_file_mapping(checksum_path)
    for relpath, _, md5 in SOURCE_FINGERPRINTS:
        key = relpath.partition(f'{subsets.PDS3_VOLSET}/')[2]
        assert mapping[key] == md5, f'{relpath}: {mapping[key]} != {md5}'
    assert len(mapping) == len(SOURCE_FINGERPRINTS)


def test_initialize_refuses_to_clobber(tool_tree):
    """A second --initialize is an error, and leaves the checksum file alone.

    Also pins the known defect that pdschecksums exits 0 after logging an ERROR
    (support.TOOLS_WITHOUT_EXIT_STATUS): its main() never calls sys.exit(status).
    PR-25's shared run_main() is expected to change this.
    """

    before = tool_tree.path(CHECKSUM_FILE).read_bytes()
    run = support.run_tool(tool_tree, 'pdschecksums', '--initialize',
                           tool_tree.path(VOLUME_DIR))
    assert 'Checksum file already exists' in run.output, run.describe()
    assert any('Checksum file already exists' in line for line in run.error_lines), \
        run.describe()
    assert run.returncode == 0, run.describe()     # known defect, pinned
    assert tool_tree.path(CHECKSUM_FILE).read_bytes() == before


def test_validate_is_clean_after_initialize(tool_tree):
    """--validate on an untouched tree exits 0 and logs no errors."""

    run = support.run_tool(tool_tree, 'pdschecksums', '--validate',
                           tool_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()


@pytest.mark.parametrize('corruption', CORRUPTIONS, ids=[c.name for c in CORRUPTIONS])
def test_corruption_is_detected_and_repaired(tool_tree, corruption):
    """Each fixed corruption fails --validate, and --repair restores a clean tree.

    Failure shows up in the log, not the exit code: see
    support.TOOLS_WITHOUT_EXIT_STATUS.
    """

    target = tool_tree.path(corruption.target)
    original = target.read_bytes()
    corruption.damage(target)

    run = support.run_tool(tool_tree, 'pdschecksums', '--validate',
                           tool_tree.path(VOLUME_DIR))
    assert any(corruption.expected in line and corruption.target.rpartition('/')[2] in line
               for line in run.error_lines), \
        f'{corruption.description}\n{run.describe()}'

    run = support.run_tool(tool_tree, 'pdschecksums', '--repair',
                           tool_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()

    run = support.run_tool(tool_tree, 'pdschecksums', '--validate',
                           tool_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()

    # Restore the pristine subset and its checksum file for the next test.
    target.write_bytes(original)
    repin_mtimes(tool_tree)
    run = support.run_tool(tool_tree, 'pdschecksums', '--repair',
                           tool_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()


def test_missing_file_is_reported_as_a_missing_checksum(tool_tree):
    """Deleting an md5 entry makes --validate report the file as unchecksummed."""

    checksum_path = tool_tree.path(CHECKSUM_FILE)
    original = checksum_path.read_bytes()
    support.delete_md5_entry(checksum_path, 'N4BI01L4Q_CAL.JPG')

    run = support.run_tool(tool_tree, 'pdschecksums', '--validate',
                           tool_tree.path(VOLUME_DIR))
    assert any('Missing checksum' in line and 'N4BI01L4Q_CAL.JPG' in line
               for line in run.error_lines), run.describe()

    checksum_path.write_bytes(original)


def test_update_picks_up_a_new_file(tool_tree):
    """--update adds a newly created file to an existing checksum file."""

    before = support.md5_file_mapping(tool_tree.path(CHECKSUM_FILE))
    support.add_file(tool_tree, NEW_FILE, NEW_FILE_BYTES, NEW_FILE_MTIME)

    run = support.run_tool(tool_tree, 'pdschecksums', '--update',
                           tool_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()

    after = support.md5_file_mapping(tool_tree.path(CHECKSUM_FILE))
    key = NEW_FILE.partition(f'{subsets.PDS3_VOLSET}/')[2]
    assert key in after, run.describe()
    assert after[key] == support.md5_of(tool_tree.path(NEW_FILE))
    assert set(before) < set(after)
    for old_key, old_md5 in before.items():
        assert after[old_key] == old_md5, f'{old_key} changed during --update'
