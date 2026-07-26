##########################################################################################
# tests/holdings_maintenance/test_pds4_infoshelf.py
#
# Full task cycle for pds4infoshelf against a copy of one declared PDS4 subset.
# pds4infoshelf reads the checksum file written by pds4checksums, so the module
# dogfoods pds4checksums first (the `tree` fixture).
#
# Note the deliberate contrast with test_pds3_infoshelf.py: pds4infoshelf's
# validate_infodict compares `modtime1 != modtime2` and `checksum1 != checksum2`
# (pds4infoshelf.py:393-399), so the two corruptions its pds3 twin silently
# accepts are reported here. When PR-26 folds the pair onto a shared core, both
# modules must agree.
#
# The `tool_tree` fixture is module-scoped, so these tests share one temporary tree
# and run in definition order; every mutating test restores a clean tree.
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
NEW_FILE_BYTES = b'<added-by-the-pr-13-update-test/>\n'
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


def repin_mtimes(tree):
    """Restore every declared source file's pinned modification time."""

    for relpath, mtime in SOURCE_MTIMES.items():
        path = tree.path(relpath)
        if path.exists():
            support.shift_mtime(path, mtime - path.stat().st_mtime)


def refresh_checksums(tree):
    """Re-run pds4checksums --repair so the checksum file matches the tree."""

    run = support.run_tool(tree, 'pds4checksums', '--repair', tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()


@pytest.fixture(scope='module')
def tree(tool_tree):
    """The module tree with checksums already generated (pds4infoshelf needs them)."""

    run = support.run_tool(tool_tree, 'pds4checksums', '--initialize',
                           tool_tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()

    return tool_tree


def test_initialize_writes_the_expected_sidecar(tree, golden_update):
    """--initialize builds the info shelf and the .py sidecar matches the golden."""

    run = support.run_tool(tree, 'pds4infoshelf', '--initialize', tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()

    sidecar = tree.path(SIDECAR)
    assert sidecar.exists(), run.describe()
    assert tree.path(PICKLE).exists(), run.describe()

    text = support.sidecar_text(sidecar)
    support.check_golden('pds4_infoshelf_sidecar', text, golden_update)

    for relpath, size, md5 in SOURCE_FINGERPRINTS:
        key = relpath.partition(f'{subsets.PDS4_BUNDLE}/')[2]
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

    run = support.run_tool(tree, 'pds4infoshelf', '--initialize', tree.path(BUNDLE_DIR))
    assert run.returncode == 1, run.describe()
    assert any('Info shelf file already exists' in line for line in run.error_lines), \
        run.describe()


def test_validate_is_clean_after_initialize(tree):
    """--validate on an untouched tree exits 0 and logs no errors."""

    run = support.run_tool(tree, 'pds4infoshelf', '--validate', tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()


@pytest.mark.parametrize('corruption', CORRUPTIONS, ids=[c.name for c in CORRUPTIONS])
def test_corruption_is_detected_and_repaired(tree, corruption):
    """Each fixed corruption fails --validate, and --repair restores the shelf."""

    target = tree.path(corruption.target)
    original = target.read_bytes()
    corruption.damage(target)
    refresh_checksums(tree)

    run = support.run_tool(tree, 'pds4infoshelf', '--validate', tree.path(BUNDLE_DIR))
    assert run.returncode == 1, f'{corruption.description}\n{run.describe()}'
    assert any(corruption.expected in line and corruption.target.rpartition('/')[2] in line
               for line in run.error_lines), \
        f'{corruption.description}\n{run.describe()}'

    run = support.run_tool(tree, 'pds4infoshelf', '--repair', tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()

    run = support.run_tool(tree, 'pds4infoshelf', '--validate', tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()

    target.write_bytes(original)
    repin_mtimes(tree)
    refresh_checksums(tree)
    run = support.run_tool(tree, 'pds4infoshelf', '--repair', tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()


def test_update_picks_up_a_new_file(tree):
    """--update adds the new file's info to an existing shelf."""

    support.add_file(tree, NEW_FILE, NEW_FILE_BYTES, NEW_FILE_MTIME)
    refresh_checksums(tree)

    run = support.run_tool(tree, 'pds4infoshelf', '--update', tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()

    text = support.sidecar_text(tree.path(SIDECAR))
    assert 'u0_kao_91cm_extra_added_by_tests.xml' in text, text
    assert str(len(NEW_FILE_BYTES)) in text

    # As in pds3, --update is additive and leaves the parent directories' aggregate
    # byte counts stale; --repair is what rewrites the whole shelf.
    run = support.run_tool(tree, 'pds4infoshelf', '--repair', tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()

    run = support.run_tool(tree, 'pds4infoshelf', '--validate', tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()
