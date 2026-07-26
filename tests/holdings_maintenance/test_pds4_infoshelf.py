##########################################################################################
# tests/holdings_maintenance/test_pds4_infoshelf.py
#
# Full task cycle for pds4infoshelf against a copy of one declared PDS4 subset.
# pds4infoshelf reads the checksum file written by pds4checksums, so every test
# dogfoods pds4checksums first (the `tree` fixture).
#
# Note the deliberate contrast with test_pds3_infoshelf.py: pds4infoshelf compares
# modification times and checksums correctly, so the two corruptions its pds3 twin
# silently accepts are reported here. See entry 10 of "From PR-13" in
# critiques/deferred-observations.md; when the pair is folded onto a shared core,
# both modules must agree.
#
# Every test rebuilds the tree first, so each one is independent and order-agnostic.
##########################################################################################

import datetime
from collections import namedtuple

import pytest

from tests.holdings_maintenance import subsets, support

pytestmark = pytest.mark.full_holdings

SOURCE_FLAVOR = 'pds4'
SOURCE_FINGERPRINTS = subsets.PDS4_BUNDLE_SOURCES
SOURCE_PATHS = subsets.paths_of(subsets.PDS4_BUNDLE_SOURCES)
SOURCE_MTIMES = subsets.PDS4_BUNDLE_MTIMES

BUNDLE_DIR = f'bundles/{subsets.PDS4_BUNDLESET}/{subsets.PDS4_BUNDLE}'
SHELF_DIR = f'_infoshelf-bundles/{subsets.PDS4_BUNDLESET}'
SIDECAR = f'{SHELF_DIR}/{subsets.PDS4_BUNDLE}_info.py'
PICKLE = f'{SHELF_DIR}/{subsets.PDS4_BUNDLE}_info.pickle'
ALPHA_LABEL = f'{BUNDLE_DIR}/data/rings/u0_kao_91cm_734nm_radius_alpha_egress_1000m.xml'
ALPHA_TABLE = f'{BUNDLE_DIR}/data/rings/u0_kao_91cm_734nm_radius_alpha_egress_1000m.tab'

NEW_FILE = f'{BUNDLE_DIR}/data/rings/u0_kao_91cm_extra_added_by_tests.xml'
NEW_FILE_BYTES = b'<added-by-an-update-test/>\n'
NEW_FILE_MTIME = subsets.PDS4_MTIMES[ALPHA_LABEL] + 1000

Corruption = namedtuple('Corruption', 'name description target damage expected')

# Fixed corruption scenarios, all of which pds4infoshelf --validate detects.
CORRUPTIONS = (
    Corruption('alpha_table_truncated',
               'truncate the alpha-ring data table to 100 bytes',
               ALPHA_TABLE, lambda path: support.truncate_file(path, 100),
               'File size mismatch'),
    Corruption('alpha_label_byte0_same_size',
               'overwrite byte 0 of the alpha-ring label, keeping size and mtime',
               ALPHA_LABEL, support.overwrite_first_byte, 'Checksum mismatch'),
    Corruption('alpha_label_mtime_plus_100',
               'move the alpha-ring label mtime forward by 100 seconds',
               ALPHA_LABEL, lambda path: support.shift_mtime(path, 100),
               'Modification time mismatch'),
)


def sidecar_line(text, key):
    """Return the sidecar line for one path, or None."""

    return next((line for line in text.splitlines()
                 if line.strip().startswith(f'"{key}"')), None)


def refresh_checksums(tree):
    """Re-run pds4checksums --repair so the checksum file matches the tree."""

    run = support.run_tool(tree, 'pds4checksums', '--repair', tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()


@pytest.fixture
def tree(fresh_tree):
    """A freshly rebuilt tree with checksums generated (pds4infoshelf needs them)."""

    support.initialize(fresh_tree, 'pds4checksums', fresh_tree.path(BUNDLE_DIR))

    return fresh_tree


@pytest.fixture
def shelved_tree(tree):
    """A freshly rebuilt tree with both the checksum file and the info shelf."""

    support.initialize(tree, 'pds4infoshelf', tree.path(BUNDLE_DIR))

    return tree


def test_initialize_writes_the_expected_sidecar(tree, golden_update):
    """--initialize builds the info shelf and the .py sidecar matches the golden."""

    support.initialize(tree, 'pds4infoshelf', tree.path(BUNDLE_DIR))

    sidecar = tree.path(SIDECAR)
    assert sidecar.exists()
    assert tree.path(PICKLE).exists()

    text = support.sidecar_text(sidecar)
    support.check_golden('pds4_infoshelf_sidecar', text, golden_update)

    for relpath, size, md5 in SOURCE_FINGERPRINTS:
        line = sidecar_line(text, relpath.partition(f'{subsets.PDS4_BUNDLE}/')[2])
        assert line is not None, f'{relpath} missing from sidecar\n{text}'
        assert str(size) in line, line
        assert md5 in line, line
        stamp = datetime.datetime.fromtimestamp(
            SOURCE_MTIMES[relpath], tz=datetime.timezone.utc)
        assert f'"{stamp.strftime("%Y-%m-%d %H:%M:%S.%f")}"' in line, line


def test_initialize_refuses_to_clobber(shelved_tree):
    """A second --initialize reports the existing shelf and exits non-zero."""

    run = support.run_tool(shelved_tree, 'pds4infoshelf', '--initialize',
                           shelved_tree.path(BUNDLE_DIR))
    assert run.returncode == 1, run.describe()
    assert any('Info shelf file already exists' in line for line in run.error_lines), \
        run.describe()


def test_validate_is_clean_after_initialize(shelved_tree):
    """--validate on an untouched tree exits 0 and logs no errors."""

    run = support.run_tool(shelved_tree, 'pds4infoshelf', '--validate',
                           shelved_tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()


@pytest.mark.parametrize('corruption', CORRUPTIONS, ids=[c.name for c in CORRUPTIONS])
def test_corruption_is_detected_and_repaired(shelved_tree, corruption):
    """Each fixed corruption fails --validate, and --repair restores the shelf."""

    corruption.damage(shelved_tree.path(corruption.target))
    refresh_checksums(shelved_tree)

    run = support.run_tool(shelved_tree, 'pds4infoshelf', '--validate',
                           shelved_tree.path(BUNDLE_DIR))
    assert run.returncode == 1, f'{corruption.description}\n{run.describe()}'
    assert any(corruption.expected in line and corruption.target.rpartition('/')[2] in line
               for line in run.error_lines), \
        f'{corruption.description}\n{run.describe()}'

    run = support.run_tool(shelved_tree, 'pds4infoshelf', '--repair',
                           shelved_tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()

    run = support.run_tool(shelved_tree, 'pds4infoshelf', '--validate',
                           shelved_tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()

    line = sidecar_line(support.sidecar_text(shelved_tree.path(SIDECAR)),
                        corruption.target.partition(f'{subsets.PDS4_BUNDLE}/')[2])
    assert str(shelved_tree.path(corruption.target).stat().st_size) in line, line


def test_update_picks_up_a_new_file(shelved_tree):
    """--update adds the new file's info to an existing shelf.

    As in pds3, --update is additive and leaves the parent directories' aggregate
    byte counts stale, so the following --validate reports them; --repair is what
    rewrites the whole shelf.
    """

    support.add_file(shelved_tree, NEW_FILE, NEW_FILE_BYTES, NEW_FILE_MTIME)
    refresh_checksums(shelved_tree)

    run = support.run_tool(shelved_tree, 'pds4infoshelf', '--update',
                           shelved_tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()

    text = support.sidecar_text(shelved_tree.path(SIDECAR))
    line = sidecar_line(text, NEW_FILE.partition(f'{subsets.PDS4_BUNDLE}/')[2])
    assert line is not None, text
    assert f'({len(NEW_FILE_BYTES):11d},' in line, line
    assert support.md5_of(shelved_tree.path(NEW_FILE)) in line, line

    run = support.run_tool(shelved_tree, 'pds4infoshelf', '--validate',
                           shelved_tree.path(BUNDLE_DIR))
    assert run.returncode == 1, run.describe()
    assert all(any(kind in line for kind in ('File size mismatch',
                                             'Child count mismatch',
                                             'Modification time mismatch'))
               for line in run.error_lines), run.describe()
    assert not any('extra_added_by_tests' in line for line in run.error_lines), \
        run.describe()
    # Unlike its pds3 twin, this tool reports the real shelved child count, and it
    # notices the parent directory's modification time moving.
    assert any('Child count mismatch 7 6' in line for line in run.error_lines), \
        run.describe()
    assert any('Modification time mismatch' in line for line in run.error_lines), \
        run.describe()

    run = support.run_tool(shelved_tree, 'pds4infoshelf', '--repair',
                           shelved_tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()

    run = support.run_tool(shelved_tree, 'pds4infoshelf', '--validate',
                           shelved_tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()
