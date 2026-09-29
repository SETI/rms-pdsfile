##########################################################################################
# tests/holdings_maintenance/test_pds3_infoshelf.py
#
# Full task cycle for pdsinfoshelf against a copy of one declared PDS3 subset.
# pdsinfoshelf reads the checksum file written by pdschecksums, so every test
# dogfoods pdschecksums first (the `tree` fixture).
#
# Every test rebuilds the tree first, so each one is independent and order-agnostic.
##########################################################################################

import datetime
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
SHELF_DIR = f'_infoshelf-volumes/{subsets.PDS3_VOLSET}'
SIDECAR = f'{SHELF_DIR}/{subsets.PDS3_VOLUME}_info.py'
PICKLE = f'{SHELF_DIR}/{subsets.PDS3_VOLUME}_info.pickle'
LABEL = f'{VOLUME_DIR}/DATA/VISIT_01/N4BI01L4Q.LBL'
ASCII_TABLE = f'{VOLUME_DIR}/DATA/VISIT_01/N4BI01L4Q.ASC'

NEW_FILE = f'{VOLUME_DIR}/DATA/VISIT_01/N4BI01L4Q_EXTRA.TXT'
NEW_FILE_BYTES = b'ADDED BY AN UPDATE TEST\r\n'
NEW_FILE_MTIME = subsets.PDS3_MTIMES[LABEL] + 1000

Corruption = namedtuple('Corruption', 'name description target damage expected')

# Fixed corruption scenarios that pdsinfoshelf --validate detects.
DETECTED_CORRUPTIONS = (
    Corruption('ascii_truncated',
               'truncate the ASCII table to 100 bytes',
               ASCII_TABLE, lambda path: support.truncate_file(path, 100),
               'File size mismatch'),
    Corruption('label_byte0_same_size',
               'overwrite byte 0 of the label, keeping its size and mtime',
               LABEL, support.overwrite_first_byte, 'Checksum mismatch'),
    Corruption('label_mtime_plus_100',
               'move the label mtime forward by 100 seconds',
               LABEL, lambda path: support.shift_mtime(path, 100),
               'Modification time mismatch'),
)


def sidecar_line(text, key):
    """Return the sidecar line for one path, or None."""

    return next((line for line in text.splitlines()
                 if line.strip().startswith(f'"{key}"')), None)


def child_count_of(line):
    """Return the child count a sidecar line records, which is its second field."""

    return int(line.partition('(')[2].split(',')[1])


def refresh_checksums(tree):
    """Re-run pdschecksums --repair so the checksum file matches the tree."""

    run = support.run_tool(tree, 'pdschecksums', '--repair', tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()


@pytest.fixture
def tree(fresh_tree):
    """A freshly rebuilt tree with checksums generated (pdsinfoshelf needs them)."""

    support.initialize(fresh_tree, 'pdschecksums', fresh_tree.path(VOLUME_DIR))

    return fresh_tree


@pytest.fixture
def shelved_tree(tree):
    """A freshly rebuilt tree with both the checksum file and the info shelf."""

    support.initialize(tree, 'pdsinfoshelf', tree.path(VOLUME_DIR))

    return tree


def test_initialize_writes_the_expected_sidecar(tree, golden_update):
    """--initialize builds the info shelf and the .py sidecar matches the golden."""

    support.initialize(tree, 'pdsinfoshelf', tree.path(VOLUME_DIR))

    sidecar = tree.path(SIDECAR)
    assert sidecar.exists()
    assert tree.path(PICKLE).exists()

    text = support.sidecar_text(sidecar)
    support.check_golden('pds3_infoshelf_sidecar', text, golden_update)

    # Real values, not an opaque blob: each declared file appears with its declared
    # byte count, its declared md5, and exactly the modification time pinned by
    # SOURCE_MTIMES, rendered in UTC (the subprocess pins TZ).
    for relpath, size, md5 in SOURCE_FINGERPRINTS:
        line = sidecar_line(text, relpath.partition(f'{subsets.PDS3_VOLUME}/')[2])
        assert line is not None, f'{relpath} missing from sidecar\n{text}'
        assert str(size) in line, line
        assert md5 in line, line
        stamp = datetime.datetime.fromtimestamp(
            SOURCE_MTIMES[relpath], tz=datetime.UTC)
        assert f'"{stamp.strftime("%Y-%m-%d %H:%M:%S.%f")}"' in line, line


def test_initialize_refuses_to_clobber(shelved_tree):
    """A second --initialize reports the existing shelf and exits non-zero."""

    run = support.run_tool(shelved_tree, 'pdsinfoshelf', '--initialize',
                           shelved_tree.path(VOLUME_DIR))
    assert run.returncode == 1, run.describe()
    assert any('Info shelf file already exists' in line for line in run.error_lines), \
        run.describe()


def test_validate_is_clean_after_initialize(shelved_tree):
    """--validate on an untouched tree exits 0 and logs no errors."""

    run = support.run_tool(shelved_tree, 'pdsinfoshelf', '--validate',
                           shelved_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()


@pytest.mark.parametrize('corruption', DETECTED_CORRUPTIONS,
                         ids=[c.name for c in DETECTED_CORRUPTIONS])
def test_corruption_is_detected_and_repaired(shelved_tree, corruption):
    """Each detectable corruption fails --validate, and --repair restores the shelf."""

    corruption.damage(shelved_tree.path(corruption.target))
    refresh_checksums(shelved_tree)

    run = support.run_tool(shelved_tree, 'pdsinfoshelf', '--validate',
                           shelved_tree.path(VOLUME_DIR))
    assert run.returncode == 1, f'{corruption.description}\n{run.describe()}'
    assert any(corruption.expected in line and corruption.target.rpartition('/')[2] in line
               for line in run.error_lines), \
        f'{corruption.description}\n{run.describe()}'

    run = support.run_tool(shelved_tree, 'pdsinfoshelf', '--repair',
                           shelved_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()

    run = support.run_tool(shelved_tree, 'pdsinfoshelf', '--validate',
                           shelved_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()

    # The repaired shelf carries the damaged file's current byte count.
    line = sidecar_line(support.sidecar_text(shelved_tree.path(SIDECAR)),
                        corruption.target.partition(f'{subsets.PDS3_VOLUME}/')[2])
    assert str(shelved_tree.path(corruption.target).stat().st_size) in line, line


def test_modification_time_mismatch_reports_both_times(shelved_tree):
    """The modification-time report names the on-disk time and the shelved one.

    The two are compared at full precision and reported to the second, so a
    mismatch always renders two different strings: times more than the tolerance
    apart cannot fall in the same second.
    """

    support.shift_mtime(shelved_tree.path(LABEL), 100)
    refresh_checksums(shelved_tree)

    run = support.run_tool(shelved_tree, 'pdsinfoshelf', '--validate',
                           shelved_tree.path(VOLUME_DIR))
    assert run.returncode == 1, run.describe()

    reported = [line for line in run.error_lines
                if 'Modification time mismatch' in line and 'N4BI01L4Q.LBL' in line]
    assert len(reported) == 1, run.describe()

    shelved = datetime.datetime.fromtimestamp(
        SOURCE_MTIMES[LABEL], tz=datetime.UTC)
    on_disk = shelved + datetime.timedelta(seconds=100)
    fmt = '%Y-%m-%d %H:%M:%S'
    assert f'"{on_disk.strftime(fmt)}" "{shelved.strftime(fmt)}"' in reported[0], \
        reported[0]


def test_modification_time_within_one_second_agrees(shelved_tree):
    """A sub-second difference across a second boundary is not a mismatch.

    The comparison is a one-second tolerance on the parsed times, not a string
    test on times truncated to the second. The two differ exactly here: 0.6 s
    apart, but on opposite sides of a boundary, so truncation would call them
    different and the tolerance calls them the same.
    """

    label = shelved_tree.path(LABEL)
    straddle = float(int(SOURCE_MTIMES[LABEL])) + 0.8
    os.utime(label, (straddle, straddle))
    refresh_checksums(shelved_tree)
    support.run_tool(shelved_tree, 'pdsinfoshelf', '--repair',
                     shelved_tree.path(VOLUME_DIR))

    # Now move it 0.6 s forward, over the next whole second.
    os.utime(label, (straddle + 0.6, straddle + 0.6))
    refresh_checksums(shelved_tree)

    run = support.run_tool(shelved_tree, 'pdsinfoshelf', '--validate',
                           shelved_tree.path(VOLUME_DIR))
    assert run.error_lines == [], run.describe()
    assert run.returncode == 0, run.describe()


def test_extra_file_is_reported(shelved_tree):
    """A file present on disk but absent from the shelf is reported."""

    support.add_file(shelved_tree, NEW_FILE, NEW_FILE_BYTES, NEW_FILE_MTIME)
    refresh_checksums(shelved_tree)

    run = support.run_tool(shelved_tree, 'pdsinfoshelf', '--validate',
                           shelved_tree.path(VOLUME_DIR))
    assert run.returncode == 1, run.describe()
    assert any('Missing shelf info for' in line and 'N4BI01L4Q_EXTRA.TXT' in line
               for line in run.error_lines), run.describe()


def test_update_picks_up_a_new_file(shelved_tree):
    """--update adds the new file's info and re-dates the directories above it.

    A file already shelved keeps its entry and is not measured again, which is what
    makes an update of a large volume affordable. A directory's entry is different in
    kind: it is an aggregate of the children the walk found, so it comes from the
    walk. It used to be kept from the old shelf instead, which left every ancestor's
    byte count, child count and modification time stale until a --repair -- and the
    --validate below is what reported them.
    """

    support.add_file(shelved_tree, NEW_FILE, NEW_FILE_BYTES, NEW_FILE_MTIME)
    refresh_checksums(shelved_tree)

    run = support.run_tool(shelved_tree, 'pdsinfoshelf', '--update',
                           shelved_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()

    text = support.sidecar_text(shelved_tree.path(SIDECAR))
    key = NEW_FILE.partition(f'{subsets.PDS3_VOLUME}/')[2]
    line = sidecar_line(text, key)
    assert line is not None, text
    assert f'({len(NEW_FILE_BYTES):11d},' in line, line
    assert support.md5_of(shelved_tree.path(NEW_FILE)) in line, line

    # The directory that gained it counts seven children, where the shelf was
    # written with six.
    dir_line = sidecar_line(text, key.rpartition('/')[0])
    assert dir_line is not None, text
    assert child_count_of(dir_line) == 7, dir_line

    run = support.run_tool(shelved_tree, 'pdsinfoshelf', '--validate',
                           shelved_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()


def test_update_drops_the_entry_for_a_deleted_file(shelved_tree):
    """--update reports a file that is gone and leaves it out of the shelf.

    A deletion used to survive every update, because the merge began as a copy of the
    old shelf and only added to it. The following --validate is what says the shelf
    and the tree now agree; it used to report "Shelf info for missing file".
    """

    support.remove_file(shelved_tree, ASCII_TABLE)
    refresh_checksums(shelved_tree)

    run = support.run_tool(shelved_tree, 'pdsinfoshelf', '--update',
                           shelved_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert any('Removed entry for missing file' in line and 'N4BI01L4Q.ASC' in line
               for line in run.output.splitlines()), run.describe()

    text = support.sidecar_text(shelved_tree.path(SIDECAR))
    key = ASCII_TABLE.partition(f'{subsets.PDS3_VOLUME}/')[2]
    assert sidecar_line(text, key) is None, text

    dir_line = sidecar_line(text, key.rpartition('/')[0])
    assert child_count_of(dir_line) == 5, dir_line

    run = support.run_tool(shelved_tree, 'pdsinfoshelf', '--validate',
                           shelved_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()


def test_update_versions_the_shelf_file_it_replaces(shelved_tree):
    """--update copies the superseded info shelf into the log directory.

    _shelf_common.move_old() versions the shelf the task is about to rewrite, as
    <name>_v###<ext> beside the run's own log file, and copies the `.py` sidecar
    alongside it. It reads the shared LOGDIRS list that the run fills in through
    _common.set_log_dirs(), so a tool that leaves that list empty versions
    nothing.
    """

    support.add_file(shelved_tree, NEW_FILE, NEW_FILE_BYTES, NEW_FILE_MTIME)
    refresh_checksums(shelved_tree)
    first_pickle = shelved_tree.path(PICKLE).read_bytes()
    first_sidecar = shelved_tree.path(SIDECAR).read_bytes()

    run = support.run_tool(shelved_tree, 'pdsinfoshelf', '--update',
                           shelved_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert 'Info shelf file moved from: ' in run.output, run.describe()
    assert 'Info shelf file moved to: ' in run.output, run.describe()

    logs = shelved_tree.disk / 'logs'
    versions = sorted(p.name for p in logs.rglob(f'{subsets.PDS3_VOLUME}_info_v*'))
    assert versions == [f'{subsets.PDS3_VOLUME}_info_v001.pickle',
                        f'{subsets.PDS3_VOLUME}_info_v001.py'], run.describe()

    assert next(logs.rglob(versions[0])).read_bytes() == first_pickle
    assert next(logs.rglob(versions[1])).read_bytes() == first_sidecar
    assert shelved_tree.path(PICKLE).exists()


def test_initialize_refuses_a_file_selection_instead_of_crashing(tree):
    """--initialize naming one file inside the volume is refused, and says so.

    The driver calls a task without a logger, and this one used to bind its own
    only inside the branch that finds a shelf already there -- so the refusal
    below, which is reached when there is none, called error() on None and ended
    the run in AttributeError. Its pds4 twin binds first and reports; so does this
    one now.
    """

    # A selection has to be a file directly inside the volume, which is what the
    # driver resolves to (directory, basename); the declared subset has none.
    top_level = f'{VOLUME_DIR}/AAREADME.TXT'
    support.add_file(tree, top_level, b'ADDED BY A REFUSAL TEST\r\n', NEW_FILE_MTIME)

    run = support.run_tool(tree, 'pdsinfoshelf', '--initialize', tree.path(top_level))
    assert run.returncode == 1, run.describe()
    assert 'AttributeError' not in run.stderr, run.describe()
    assert 'Traceback' not in run.stderr, run.describe()
    assert any('File selection is disallowed for task "initialize"' in line
               for line in run.error_lines), run.describe()
    assert not tree.path(PICKLE).exists(), run.describe()
