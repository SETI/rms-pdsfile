##########################################################################################
# tests/holdings_maintenance/test_pds3_infoshelf.py
#
# Full task cycle for pdsinfoshelf against a copy of one declared PDS3 subset.
# pdsinfoshelf reads the checksum file written by pdschecksums, so every test
# dogfoods pdschecksums first (the `tree` fixture).
#
# Two of the scenarios below pin corruptions that pdsinfoshelf --validate does NOT
# report today, and one pins a wrong log message; see entry 1 of "From PR-13" in
# critiques/deferred-observations.md. Its pds4 twin compares correctly, which is
# why test_pds4_infoshelf.py expects the opposite outcome.
#
# Every test rebuilds the tree first, so each one is independent and order-agnostic.
##########################################################################################

import datetime
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

# Fixed corruption scenarios that pdsinfoshelf --validate does detect.
DETECTED_CORRUPTIONS = (
    Corruption('ascii_truncated',
               'truncate the ASCII table to 100 bytes',
               ASCII_TABLE, lambda path: support.truncate_file(path, 100),
               'File size mismatch'),
)

# Fixed corruption scenarios pdsinfoshelf --validate does NOT detect today.
UNDETECTED_CORRUPTIONS = (
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
            SOURCE_MTIMES[relpath], tz=datetime.timezone.utc)
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


@pytest.mark.parametrize('corruption', UNDETECTED_CORRUPTIONS,
                         ids=[c.name for c in UNDETECTED_CORRUPTIONS])
def test_known_undetected_corruption(shelved_tree, corruption):
    """These corruptions pass --validate today; the comparison is defective.

    See entry 1 of "From PR-13" in critiques/deferred-observations.md. When the
    comparison is fixed these assertions must be inverted -- that is the point of
    pinning them.
    """

    corruption.damage(shelved_tree.path(corruption.target))
    refresh_checksums(shelved_tree)

    run = support.run_tool(shelved_tree, 'pdsinfoshelf', '--validate',
                           shelved_tree.path(VOLUME_DIR))
    assert run.returncode == 0, f'{corruption.description}\n{run.describe()}'
    assert run.error_lines == [], f'{corruption.description}\n{run.describe()}'
    assert corruption.expected not in run.output, \
        f'{corruption.description}\n{run.describe()}'


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
    """--update adds the new file's info to an existing shelf.

    --update is deliberately additive: it fills in only the keys the shelf lacks,
    so the aggregate byte counts already recorded for the parent directories are
    left stale and the following --validate reports them. --repair is what
    rewrites the whole shelf.
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

    run = support.run_tool(shelved_tree, 'pdsinfoshelf', '--validate',
                           shelved_tree.path(VOLUME_DIR))
    assert run.returncode == 1, run.describe()
    assert all('File size mismatch' in line or 'Child count mismatch' in line
               for line in run.error_lines), run.describe()
    assert not any('N4BI01L4Q_EXTRA.TXT' in line for line in run.error_lines), \
        run.describe()
    # The child-count message reports the on-disk count twice instead of on-disk
    # versus shelved (6); see entry 1 of "From PR-13" in the deferred observations.
    assert any('Child count mismatch 7 7' in line for line in run.error_lines), \
        run.describe()

    run = support.run_tool(shelved_tree, 'pdsinfoshelf', '--repair',
                           shelved_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()

    run = support.run_tool(shelved_tree, 'pdsinfoshelf', '--validate',
                           shelved_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()
