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
# pdschecksums reports a logged fatal or error in its exit status, the same way every
# other tool here does: main() exits with the status the run computed, so a --validate
# that reports a mismatch exits 1.
##########################################################################################

import os
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

ERROR_EXIT = support.ERROR_EXIT_CODE

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

    _shelf_common.move_old() versions the file the task is about to overwrite,
    as <name>_v###.txt beside the run's own log file, one past the highest version
    already there. It reads the shared LOGDIRS list that the run fills in through
    _common.set_log_dirs(), so a tool that leaves that list empty versions
    nothing; this test is what makes that visible, here and in the pds4 twin.
    """

    support.initialize(fresh_tree, 'pdschecksums', fresh_tree.path(VOLUME_DIR))
    first = fresh_tree.path(CHECKSUM_FILE).read_bytes()

    run = support.run_tool(fresh_tree, 'pdschecksums', '--reinitialize',
                           fresh_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert 'Checksum file moved from: ' in run.output, run.describe()
    assert 'Checksum file moved to: ' in run.output, run.describe()

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


##########################################################################################
# The --infoshelf chain
#
# pdschecksums --infoshelf re-runs its own command line as a pdsinfoshelf command,
# which it builds by rewriting argv[0]. That only resolves to the other tool when
# argv[0] is a console script, so these tests invoke it as an install would.
##########################################################################################

@pytest.fixture
def scripts(tmp_path):
    """Console scripts for the two tools the chain involves."""

    return support.console_scripts(tmp_path / 'bin', 'pdschecksums', 'pdsinfoshelf')


def test_infoshelf_chain_runs_the_infoshelf_tool(fresh_tree, scripts):
    """--initialize --infoshelf writes the checksum file and then the info shelf."""

    run = support.run_console_script(fresh_tree, scripts / 'pdschecksums',
                                     '--initialize', '--infoshelf',
                                     fresh_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert fresh_tree.path(CHECKSUM_FILE).exists(), run.describe()

    shelf = fresh_tree.path(
        f'_infoshelf-volumes/{subsets.PDS3_VOLSET}/{subsets.PDS3_VOLUME}_info.pickle')
    assert shelf.exists(), run.describe()

    # Both tools logged, the second one under its own logger name.
    assert 'pds.validation.checksums' in run.output, run.describe()
    assert 'pds.validation.fileinfo' in run.output, run.describe()


def test_infoshelf_chain_reports_the_chained_run_exit_code(fresh_tree, scripts):
    """The chained command's exit code is the exit code of the whole run.

    The chained run is executed as an argument list, so its status arrives intact.
    Handing the command to a shell instead returns a wait status -- the exit code
    shifted left by eight -- and passing that to sys.exit() truncates it to the low
    byte, turning every failure into a success.
    """

    support.initialize(fresh_tree, 'pdschecksums', fresh_tree.path(VOLUME_DIR))

    # Checksums validate cleanly, so the chain runs; the info shelf does not exist,
    # so the chained pdsinfoshelf --validate fails with exit 1.
    run = support.run_console_script(fresh_tree, scripts / 'pdschecksums',
                                     '--validate', '--infoshelf',
                                     fresh_tree.path(VOLUME_DIR))
    assert run.returncode == 1, run.describe()
    assert any('Info shelf file does not exist' in line for line in run.error_lines), \
        run.describe()


def test_infoshelf_chain_passes_a_path_containing_spaces(tool_tree, tmp_path, scripts):
    """A holdings path with spaces in it reaches the chained run in one piece.

    The chained command is passed as an argument list rather than joined into a
    shell command line, so nothing in it is word-split or otherwise interpreted.
    A holdings root under a directory whose name contains spaces is not
    hypothetical: real deployments have them.

    A shell would split this path into four words, and the chained tool would
    reject each fragment as "Not a holdings subdirectory" before it opened a log.
    So the chained run's logger name appearing in the output is what says the path
    arrived whole.
    """

    disk = tmp_path / 'a directory with spaces'
    tree = support.build_tree(disk, tool_tree.source_dir, 'pds3',
                              SOURCE_PATHS, SOURCE_MTIMES)
    assert ' ' in str(tree.path(VOLUME_DIR))

    support.initialize(tree, 'pdschecksums', tree.path(VOLUME_DIR))

    run = support.run_console_script(tree, scripts / 'pdschecksums',
                                     '--validate', '--infoshelf',
                                     tree.path(VOLUME_DIR))
    assert 'Not a holdings subdirectory' not in run.output, run.describe()
    assert 'pds.validation.fileinfo' in run.output, run.describe()
    assert any('Info shelf file does not exist' in line for line in run.error_lines), \
        run.describe()
    assert run.returncode == 1, run.describe()


def test_no_targets_leaves_no_unbound_state(fresh_tree, scripts):
    """A volume set with no volumes in it completes instead of raising.

    Expanding the command-line path can legitimately yield nothing, and the run
    then has no task result to decide the chain on. It reports success and does
    not chain, rather than failing on a variable that was never assigned.
    """

    empty = fresh_tree.holdings / 'volumes' / 'EMPTYx_xxxx'
    empty.mkdir(parents=True, exist_ok=True)

    run = support.run_console_script(fresh_tree, scripts / 'pdschecksums',
                                     '--validate', '--infoshelf', empty)
    assert run.returncode == 0, run.describe()
    assert 'UnboundLocalError' not in run.stderr, run.describe()
    assert 'Traceback' not in run.stderr, run.describe()


def test_update_drops_the_entry_for_a_deleted_file(fresh_tree):
    """--update reports a file that is gone and leaves it out of the manifest.

    A deletion used to be invisible rather than merely un-removed: the entry was
    copied across from the old manifest whatever the walk found, so the comparison
    that decides whether to rewrite still held and the run reported "update
    canceled". The following --validate is what says the manifest and the tree
    now agree.
    """

    support.initialize(fresh_tree, 'pdschecksums', fresh_tree.path(VOLUME_DIR))
    before = support.md5_file_mapping(fresh_tree.path(CHECKSUM_FILE))
    key = PREVIEW.partition(f'{subsets.PDS3_VOLSET}/')[2]
    assert key in before

    support.remove_file(fresh_tree, PREVIEW)

    run = support.run_tool(fresh_tree, 'pdschecksums', '--update',
                           fresh_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert any('Removed entry for missing file' in line and 'N4BI01L4Q_CAL.JPG' in line
               for line in run.output.splitlines()), run.describe()

    after = support.md5_file_mapping(fresh_tree.path(CHECKSUM_FILE))
    assert key not in after, run.describe()
    assert set(after) == set(before) - {key}, run.describe()

    run = support.run_tool(fresh_tree, 'pdschecksums', '--validate',
                           fresh_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()


def test_a_blank_record_in_the_manifest_is_reported_rather_than_fatal(fresh_tree):
    """A manifest with a blank line is read to the end, and the line is an error.

    The parse takes fixed offsets, so a short record yields an empty path; the
    invisible-file test below it used to subscript that empty basename and end the
    read in IndexError.
    """

    support.initialize(fresh_tree, 'pdschecksums', fresh_tree.path(VOLUME_DIR))
    check_path = fresh_tree.path(CHECKSUM_FILE)
    check_path.write_bytes(check_path.read_bytes() + b'\n')

    run = support.run_tool(fresh_tree, 'pdschecksums', '--validate',
                           fresh_tree.path(VOLUME_DIR))
    assert 'IndexError' not in run.stderr, run.describe()
    assert 'Traceback' not in run.stderr, run.describe()
    assert any('Blank record in checksum file' in line
               for line in run.error_lines), run.describe()
    # Every other record was still read, so nothing is reported as missing.
    assert not any('Missing checksum' in line for line in run.error_lines), \
        run.describe()


@pytest.mark.skipif(os.geteuid() == 0,
                    reason='root reads a directory whatever its mode')
def test_update_keeps_the_entries_below_an_unreadable_directory(fresh_tree):
    """A walk that could not read a directory judges nothing below it missing.

    ``os.walk()`` passes over a directory it cannot open without raising, so the
    files under it never reach the set the deletion sweep compares against. Their
    entries have to survive: an unreadable subtree costs the run its digests there
    and not the manifest's record of them.
    """

    support.initialize(fresh_tree, 'pdschecksums', fresh_tree.path(VOLUME_DIR))
    before = support.md5_file_mapping(fresh_tree.path(CHECKSUM_FILE))

    closed = fresh_tree.path(f'{VOLUME_DIR}/DATA/VISIT_01')
    closed.chmod(0o000)
    try:
        run = support.run_tool(fresh_tree, 'pdschecksums', '--update',
                               fresh_tree.path(VOLUME_DIR))
    finally:
        closed.chmod(0o755)

    assert run.returncode == ERROR_EXIT, run.describe()
    assert any('Directory could not be read' in line
               for line in run.error_lines), run.describe()
    assert not any('Removed entry for missing file' in line
                   for line in run.output.splitlines()), run.describe()

    after = support.md5_file_mapping(fresh_tree.path(CHECKSUM_FILE))
    assert after == before, run.describe()
