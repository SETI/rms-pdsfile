##########################################################################################
# tests/holdings_maintenance/test_pds4_checksums.py
#
# Full task cycle for pds4checksums against a copy of one declared PDS4 subset:
# --initialize -> golden -> --validate clean -> corrupt -> --validate reports it ->
# --repair -> --validate clean -> --update after a new file.
#
# Like its pds3 twin, pds4checksums exits 0 even after logging ERRORs
# (support.TOOLS_WITHOUT_EXIT_STATUS); the log is the signal, and PR-25's shared
# run_main() is expected to change that.
#
# The `tool_tree` fixture is module-scoped, so these tests share one temporary tree
# and run in definition order; every mutating test restores a clean tree.
##########################################################################################

from collections import namedtuple

import pytest

from tests.holdings_maintenance import subsets, support

pytestmark = pytest.mark.full_holdings

SOURCE_FLAVOR = 'pds4'
SOURCE_FINGERPRINTS = subsets.PDS4_BUNDLE_SOURCES
SOURCE_PATHS = subsets.paths_of(subsets.PDS4_BUNDLE_SOURCES)
SOURCE_MTIMES = subsets.PDS4_BUNDLE_MTIMES

BUNDLE_DIR = f'bundles/{subsets.PDS4_BUNDLESET}/{subsets.PDS4_BUNDLE}'
CHECKSUM_FILE = (f'checksums-bundles/{subsets.PDS4_BUNDLESET}/'
                 f'{subsets.PDS4_BUNDLE}_md5.txt')
ALPHA_LABEL = f'{BUNDLE_DIR}/data/rings/u0_kao_91cm_734nm_radius_alpha_egress_1000m.xml'
ALPHA_TABLE = f'{BUNDLE_DIR}/data/rings/u0_kao_91cm_734nm_radius_alpha_egress_1000m.tab'
BETA_TABLE = f'{BUNDLE_DIR}/data/rings/u0_kao_91cm_734nm_radius_beta_egress_1000m.tab'

NEW_FILE = f'{BUNDLE_DIR}/data/rings/u0_kao_91cm_extra_added_by_tests.xml'
NEW_FILE_BYTES = b'<added-by-the-pr-13-update-test/>\n'
NEW_FILE_MTIME = subsets.PDS4_MTIMES[ALPHA_LABEL] + 1000

Corruption = namedtuple('Corruption', 'name description target damage expected')

# Fixed corruption scenarios. Nothing here is randomized or discovered at run time.
CORRUPTIONS = (
    Corruption('alpha_label_byte0',
               'overwrite byte 0 of the alpha-ring label with 0xFF',
               ALPHA_LABEL, support.overwrite_first_byte, 'Checksum mismatch'),
    Corruption('alpha_table_truncated',
               'truncate the alpha-ring data table to 100 bytes',
               ALPHA_TABLE, lambda path: support.truncate_file(path, 100),
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

    run = support.run_tool(tool_tree, 'pds4checksums', '--initialize',
                           tool_tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()

    checksum_path = tool_tree.path(CHECKSUM_FILE)
    assert checksum_path.exists(), run.describe()

    support.check_golden('pds4_checksums_md5', support.md5_file_text(checksum_path),
                         golden_update)

    mapping = support.md5_file_mapping(checksum_path)
    for relpath, _, md5 in SOURCE_FINGERPRINTS:
        key = relpath.partition(f'{subsets.PDS4_BUNDLESET}/')[2]
        assert mapping[key] == md5, f'{relpath}: {mapping[key]} != {md5}'
    assert len(mapping) == len(SOURCE_FINGERPRINTS)


def test_initialize_refuses_to_clobber(tool_tree):
    """A second --initialize is an error, and leaves the checksum file alone."""

    before = tool_tree.path(CHECKSUM_FILE).read_bytes()
    run = support.run_tool(tool_tree, 'pds4checksums', '--initialize',
                           tool_tree.path(BUNDLE_DIR))
    assert any('Checksum file already exists' in line for line in run.error_lines), \
        run.describe()
    assert run.returncode == 0, run.describe()     # known defect, pinned
    assert tool_tree.path(CHECKSUM_FILE).read_bytes() == before


def test_validate_is_clean_after_initialize(tool_tree):
    """--validate on an untouched tree exits 0 and logs no errors."""

    run = support.run_tool(tool_tree, 'pds4checksums', '--validate',
                           tool_tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()


@pytest.mark.parametrize('corruption', CORRUPTIONS, ids=[c.name for c in CORRUPTIONS])
def test_corruption_is_detected_and_repaired(tool_tree, corruption):
    """Each fixed corruption is reported by --validate; --repair restores the tree."""

    target = tool_tree.path(corruption.target)
    original = target.read_bytes()
    corruption.damage(target)

    run = support.run_tool(tool_tree, 'pds4checksums', '--validate',
                           tool_tree.path(BUNDLE_DIR))
    assert any(corruption.expected in line and corruption.target.rpartition('/')[2] in line
               for line in run.error_lines), \
        f'{corruption.description}\n{run.describe()}'

    run = support.run_tool(tool_tree, 'pds4checksums', '--repair',
                           tool_tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()

    run = support.run_tool(tool_tree, 'pds4checksums', '--validate',
                           tool_tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()

    target.write_bytes(original)
    repin_mtimes(tool_tree)
    run = support.run_tool(tool_tree, 'pds4checksums', '--repair',
                           tool_tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()


def test_missing_file_is_reported_as_a_missing_checksum(tool_tree):
    """Deleting an md5 entry makes --validate report the file as unchecksummed."""

    checksum_path = tool_tree.path(CHECKSUM_FILE)
    original = checksum_path.read_bytes()
    support.delete_md5_entry(checksum_path, BETA_TABLE.rpartition('/')[2])

    run = support.run_tool(tool_tree, 'pds4checksums', '--validate',
                           tool_tree.path(BUNDLE_DIR))
    assert any('Missing checksum' in line and BETA_TABLE.rpartition('/')[2] in line
               for line in run.error_lines), run.describe()

    checksum_path.write_bytes(original)


def test_two_task_flags_resolve_to_the_last_one(tool_tree):
    """The pds4 half of a tool pair resolves multiple task flags exactly as pds3 does.

    See test_task_flags.py for why this is pinned: PR-25's shared parser must not
    turn today's silent last-wins into an argparse error.
    """

    run = support.run_tool(tool_tree, 'pds4checksums', '--initialize', '--validate',
                           tool_tree.path(BUNDLE_DIR))
    assert 'not allowed with argument' not in run.output, run.describe()
    assert '| HEADER | Task "validate" for' in run.output, run.describe()
    assert 'Checksum file already exists' not in run.output, run.describe()


def test_update_picks_up_a_new_file(tool_tree):
    """--update adds a newly created file to an existing checksum file."""

    before = support.md5_file_mapping(tool_tree.path(CHECKSUM_FILE))
    support.add_file(tool_tree, NEW_FILE, NEW_FILE_BYTES, NEW_FILE_MTIME)

    run = support.run_tool(tool_tree, 'pds4checksums', '--update',
                           tool_tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()

    after = support.md5_file_mapping(tool_tree.path(CHECKSUM_FILE))
    key = NEW_FILE.partition(f'{subsets.PDS4_BUNDLESET}/')[2]
    assert key in after, run.describe()
    assert after[key] == support.md5_of(tool_tree.path(NEW_FILE))
    assert set(before) < set(after)
    for old_key, old_md5 in before.items():
        assert after[old_key] == old_md5, f'{old_key} changed during --update'
