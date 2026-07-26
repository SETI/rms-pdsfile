##########################################################################################
# tests/holdings_maintenance/test_pds3_infoshelf.py
#
# Full task cycle for pdsinfoshelf against a copy of one declared PDS3 subset.
# pdsinfoshelf reads the checksum file written by pdschecksums, so the module
# dogfoods pdschecksums first (the `tree` fixture).
#
# Three of the scenarios below pin *known defects* in pdsinfoshelf.validate_infodict
# rather than working detection; each says so and names PR-26, which owns the fix:
#
#   pdsinfoshelf.py:391  abs(modtime1 != modtime2) > 1   -> abs(bool) is 0 or 1,
#                        never > 1, so modification-time drift is never reported.
#   pdsinfoshelf.py:395  checksum1 != checksum1          -> compares a value to
#                        itself, so content changes are never reported.
#   pdsinfoshelf.py:386  'Child count mismatch %d %d' % (count1, count1)
#                        -> prints the directory count twice, so the message can
#                        never show the shelved value.
#
# The `tool_tree` fixture is module-scoped, so these tests share one temporary tree
# and run in definition order; every mutating test restores a clean tree.
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
PREVIEW = f'{VOLUME_DIR}/DATA/VISIT_01/N4BI01L4Q_CAL.JPG'

NEW_FILE = f'{VOLUME_DIR}/DATA/VISIT_01/N4BI01L4Q_EXTRA.TXT'
NEW_FILE_BYTES = b'ADDED BY THE PDS-13 UPDATE TEST\r\n'
NEW_FILE_MTIME = subsets.PDS3_MTIMES[LABEL] + 1000

Corruption = namedtuple('Corruption', 'name description target damage expected')

# Fixed corruption scenarios that pdsinfoshelf --validate DOES detect today.
DETECTED_CORRUPTIONS = (
    Corruption('ascii_truncated',
               'truncate the ASCII table to 100 bytes',
               ASCII_TABLE, lambda path: support.truncate_file(path, 100),
               'File size mismatch'),
)

# Fixed corruption scenarios that pdsinfoshelf --validate does NOT detect today,
# because of the two comparison defects named in the module docstring. These pin
# the defect; PR-26 must flip them.
UNDETECTED_CORRUPTIONS = (
    Corruption('label_byte0_same_size',
               'overwrite byte 0 of the label, keeping its size and mtime',
               LABEL, support.overwrite_first_byte, 'Checksum mismatch'),
    Corruption('label_mtime_plus_100',
               'move the label mtime forward by 100 seconds',
               LABEL, lambda path: support.shift_mtime(path, 100),
               'Modification time mismatch'),
)


def repin_mtimes(tree):
    """Restore every declared source file's pinned modification time."""

    for relpath, mtime in SOURCE_MTIMES.items():
        path = tree.path(relpath)
        if path.exists():
            support.shift_mtime(path, mtime - path.stat().st_mtime)


def refresh_checksums(tree):
    """Re-run pdschecksums --repair so the checksum file matches the tree."""

    run = support.run_tool(tree, 'pdschecksums', '--repair', tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()


@pytest.fixture(scope='module')
def tree(tool_tree):
    """The module tree with checksums already generated (pdsinfoshelf needs them)."""

    run = support.run_tool(tool_tree, 'pdschecksums', '--initialize',
                           tool_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()

    return tool_tree


def test_initialize_writes_the_expected_sidecar(tree, golden_update):
    """--initialize builds the info shelf and the .py sidecar matches the golden."""

    run = support.run_tool(tree, 'pdsinfoshelf', '--initialize', tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()

    sidecar = tree.path(SIDECAR)
    assert sidecar.exists(), run.describe()
    assert tree.path(PICKLE).exists(), run.describe()

    text = support.sidecar_text(sidecar)
    support.check_golden('pds3_infoshelf_sidecar', text, golden_update)

    # Real values, not an opaque blob: each declared file appears with its declared
    # byte count, its declared md5, and exactly the modification time pinned by
    # SOURCE_MTIMES, rendered in UTC (the subprocess pins TZ).
    for relpath, size, md5 in SOURCE_FINGERPRINTS:
        key = relpath.partition(f'{subsets.PDS3_VOLUME}/')[2]
        line = next((ln for ln in text.splitlines() if ln.strip().startswith(f'"{key}"')),
                    None)
        assert line is not None, f'{key} missing from sidecar\n{text}'
        assert str(size) in line, line
        assert md5 in line, line
        stamp = datetime.datetime.fromtimestamp(
            SOURCE_MTIMES[relpath], tz=datetime.timezone.utc)
        assert f'"{stamp.strftime("%Y-%m-%d %H:%M:%S.%f")}"' in line, line


def test_initialize_refuses_to_clobber(tree):
    """A second --initialize reports the existing shelf and exits non-zero."""

    run = support.run_tool(tree, 'pdsinfoshelf', '--initialize', tree.path(VOLUME_DIR))
    assert run.returncode == 1, run.describe()
    assert any('Info shelf file already exists' in line for line in run.error_lines), \
        run.describe()


def test_validate_is_clean_after_initialize(tree):
    """--validate on an untouched tree exits 0 and logs no errors."""

    run = support.run_tool(tree, 'pdsinfoshelf', '--validate', tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()


@pytest.mark.parametrize('corruption', DETECTED_CORRUPTIONS,
                         ids=[c.name for c in DETECTED_CORRUPTIONS])
def test_corruption_is_detected_and_repaired(tree, corruption):
    """Each detectable corruption fails --validate, and --repair restores the shelf."""

    target = tree.path(corruption.target)
    original = target.read_bytes()
    corruption.damage(target)
    refresh_checksums(tree)

    run = support.run_tool(tree, 'pdsinfoshelf', '--validate', tree.path(VOLUME_DIR))
    assert run.returncode == 1, f'{corruption.description}\n{run.describe()}'
    assert any(corruption.expected in line and corruption.target.rpartition('/')[2] in line
               for line in run.error_lines), \
        f'{corruption.description}\n{run.describe()}'

    run = support.run_tool(tree, 'pdsinfoshelf', '--repair', tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()

    run = support.run_tool(tree, 'pdsinfoshelf', '--validate', tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()

    # Restore the pristine subset and rebuild both artifacts for the next test.
    target.write_bytes(original)
    repin_mtimes(tree)
    refresh_checksums(tree)
    run = support.run_tool(tree, 'pdsinfoshelf', '--repair', tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()


@pytest.mark.parametrize('corruption', UNDETECTED_CORRUPTIONS,
                         ids=[c.name for c in UNDETECTED_CORRUPTIONS])
def test_known_undetected_corruption(tree, corruption):
    """Pin the two comparison defects: these corruptions pass --validate today.

    See the module docstring. When PR-26 fixes `checksum1 != checksum1` and the
    `abs(modtime1 != modtime2) > 1` tolerance, these assertions must be inverted --
    that is the point of pinning them.
    """

    target = tree.path(corruption.target)
    original = target.read_bytes()
    corruption.damage(target)
    refresh_checksums(tree)

    run = support.run_tool(tree, 'pdsinfoshelf', '--validate', tree.path(VOLUME_DIR))
    assert run.returncode == 0, f'{corruption.description}\n{run.describe()}'
    assert run.error_lines == [], f'{corruption.description}\n{run.describe()}'
    assert corruption.expected not in run.output, \
        f'{corruption.description}\n{run.describe()}'

    target.write_bytes(original)
    repin_mtimes(tree)
    refresh_checksums(tree)
    run = support.run_tool(tree, 'pdsinfoshelf', '--repair', tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()


def test_extra_file_is_reported(tree):
    """A file present on disk but absent from the shelf is reported."""

    support.add_file(tree, NEW_FILE, NEW_FILE_BYTES, NEW_FILE_MTIME)
    refresh_checksums(tree)

    run = support.run_tool(tree, 'pdsinfoshelf', '--validate', tree.path(VOLUME_DIR))
    assert run.returncode == 1, run.describe()
    assert any('Missing shelf info for' in line and 'N4BI01L4Q_EXTRA.TXT' in line
               for line in run.error_lines), run.describe()


def test_update_picks_up_a_new_file(tree):
    """--update adds the new file's info to an existing shelf.

    --update is deliberately additive: generate_infodict() merges over the shelf's
    existing entries and only fills in keys that are absent, so the aggregate byte
    counts already recorded for the parent directories are left stale and the
    following --validate reports them. That is pinned here as current behavior;
    --repair is what rewrites the whole shelf.
    """

    run = support.run_tool(tree, 'pdsinfoshelf', '--update', tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()

    text = support.sidecar_text(tree.path(SIDECAR))
    assert 'N4BI01L4Q_EXTRA.TXT' in text, text
    assert str(len(NEW_FILE_BYTES)) in text

    run = support.run_tool(tree, 'pdsinfoshelf', '--validate', tree.path(VOLUME_DIR))
    assert run.returncode == 1, run.describe()
    assert all('File size mismatch' in line or 'Child count mismatch' in line
               for line in run.error_lines), run.describe()
    assert not any('N4BI01L4Q_EXTRA.TXT' in line for line in run.error_lines), \
        run.describe()
    # Pins pdsinfoshelf.py:386 -- the child-count message formats (count1, count1),
    # so it reports the on-disk count twice instead of on-disk vs shelved (6).
    assert any('Child count mismatch 7 7' in line for line in run.error_lines), \
        run.describe()

    run = support.run_tool(tree, 'pdsinfoshelf', '--repair', tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()

    run = support.run_tool(tree, 'pdsinfoshelf', '--validate', tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()
