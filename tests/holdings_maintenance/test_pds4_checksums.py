##########################################################################################
# tests/holdings_maintenance/test_pds4_checksums.py
#
# Full task cycle for pds4checksums against a copy of one declared PDS4 subset:
# --initialize -> golden -> --validate clean -> corrupt -> --validate reports it ->
# --repair -> --validate clean -> --update after a new file.
#
# Like its pds3 twin, pds4checksums reports a logged fatal or error in its exit
# status, the same way every other tool here does: main() exits with the status the
# run computed, so a --validate that reports a mismatch exits 1.
#
# Every test rebuilds the tree first, so each one is independent and order-agnostic.
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
NEW_FILE_BYTES = b'<added-by-an-update-test/>\n'
NEW_FILE_MTIME = subsets.PDS4_MTIMES[ALPHA_LABEL] + 1000

ERROR_EXIT = support.ERROR_EXIT_CODE

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


def test_initialize_writes_the_expected_checksum_file(fresh_tree, golden_update):
    """--initialize from scratch produces the committed md5 golden."""

    support.initialize(fresh_tree, 'pds4checksums', fresh_tree.path(BUNDLE_DIR))

    checksum_path = fresh_tree.path(CHECKSUM_FILE)
    assert checksum_path.exists()

    support.check_golden('pds4_checksums_md5', support.md5_file_text(checksum_path),
                         golden_update)

    mapping = support.md5_file_mapping(checksum_path)
    for relpath, _, md5 in SOURCE_FINGERPRINTS:
        key = relpath.partition(f'{subsets.PDS4_BUNDLESET}/')[2]
        assert mapping[key] == md5, f'{relpath}: {mapping[key]} != {md5}'
    assert len(mapping) == len(SOURCE_FINGERPRINTS)


def test_initialize_refuses_to_clobber(fresh_tree):
    """A second --initialize is an error, and leaves the checksum file alone."""

    support.initialize(fresh_tree, 'pds4checksums', fresh_tree.path(BUNDLE_DIR))
    before = fresh_tree.path(CHECKSUM_FILE).read_bytes()

    run = support.run_tool(fresh_tree, 'pds4checksums', '--initialize',
                           fresh_tree.path(BUNDLE_DIR))
    assert any('Checksum file already exists' in line for line in run.error_lines), \
        run.describe()
    assert run.returncode == ERROR_EXIT, run.describe()
    assert fresh_tree.path(CHECKSUM_FILE).read_bytes() == before


def test_validate_is_clean_after_initialize(fresh_tree):
    """--validate on an untouched tree exits 0 and logs no errors."""

    support.initialize(fresh_tree, 'pds4checksums', fresh_tree.path(BUNDLE_DIR))

    run = support.run_tool(fresh_tree, 'pds4checksums', '--validate',
                           fresh_tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()


@pytest.mark.parametrize('corruption', CORRUPTIONS, ids=[c.name for c in CORRUPTIONS])
def test_corruption_is_detected_and_repaired(fresh_tree, corruption):
    """Each fixed corruption is reported by --validate; --repair restores the tree."""

    support.initialize(fresh_tree, 'pds4checksums', fresh_tree.path(BUNDLE_DIR))
    corruption.damage(fresh_tree.path(corruption.target))

    run = support.run_tool(fresh_tree, 'pds4checksums', '--validate',
                           fresh_tree.path(BUNDLE_DIR))
    assert any(corruption.expected in line and corruption.target.rpartition('/')[2] in line
               for line in run.error_lines), \
        f'{corruption.description}\n{run.describe()}'
    assert run.returncode == ERROR_EXIT, run.describe()

    run = support.run_tool(fresh_tree, 'pds4checksums', '--repair',
                           fresh_tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()

    run = support.run_tool(fresh_tree, 'pds4checksums', '--validate',
                           fresh_tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()

    mapping = support.md5_file_mapping(fresh_tree.path(CHECKSUM_FILE))
    key = corruption.target.partition(f'{subsets.PDS4_BUNDLESET}/')[2]
    assert mapping[key] == support.md5_of(fresh_tree.path(corruption.target))


def test_missing_file_is_reported_as_a_missing_checksum(fresh_tree):
    """Deleting an md5 entry makes --validate report the file as unchecksummed."""

    support.initialize(fresh_tree, 'pds4checksums', fresh_tree.path(BUNDLE_DIR))
    support.delete_md5_entry(fresh_tree.path(CHECKSUM_FILE),
                             BETA_TABLE.rpartition('/')[2])

    run = support.run_tool(fresh_tree, 'pds4checksums', '--validate',
                           fresh_tree.path(BUNDLE_DIR))
    assert any('Missing checksum' in line and BETA_TABLE.rpartition('/')[2] in line
               for line in run.error_lines), run.describe()
    assert run.returncode == ERROR_EXIT, run.describe()


def test_two_task_flags_resolve_to_the_last_one(fresh_tree):
    """The pds4 half of a tool pair resolves multiple task flags exactly as pds3 does.

    See test_task_flags.py for why this is pinned.
    """

    support.initialize(fresh_tree, 'pds4checksums', fresh_tree.path(BUNDLE_DIR))

    run = support.run_tool(fresh_tree, 'pds4checksums', '--initialize', '--validate',
                           fresh_tree.path(BUNDLE_DIR))
    # Merged output on purpose: argparse writes its errors to stderr, so reading
    # stdout here would make this assertion vacuous.
    assert 'not allowed with argument' not in run.output, run.describe()
    assert '| HEADER | Task "validate" for' in run.output, run.describe()
    assert 'Checksum file already exists' not in run.output, run.describe()


def test_update_picks_up_a_new_file(fresh_tree):
    """--update adds a newly created file to an existing checksum file."""

    support.initialize(fresh_tree, 'pds4checksums', fresh_tree.path(BUNDLE_DIR))
    before = support.md5_file_mapping(fresh_tree.path(CHECKSUM_FILE))
    support.add_file(fresh_tree, NEW_FILE, NEW_FILE_BYTES, NEW_FILE_MTIME)

    run = support.run_tool(fresh_tree, 'pds4checksums', '--update',
                           fresh_tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()

    after = support.md5_file_mapping(fresh_tree.path(CHECKSUM_FILE))
    key = NEW_FILE.partition(f'{subsets.PDS4_BUNDLESET}/')[2]
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
    nothing; this test is what makes that visible, here and in the pds3 twin.
    """

    support.initialize(fresh_tree, 'pds4checksums', fresh_tree.path(BUNDLE_DIR))
    first = fresh_tree.path(CHECKSUM_FILE).read_bytes()

    run = support.run_tool(fresh_tree, 'pds4checksums', '--reinitialize',
                           fresh_tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()
    assert 'Checksum file moved from: ' in run.output, run.describe()
    assert 'Checksum file moved to: ' in run.output, run.describe()

    logs = fresh_tree.disk / 'logs'
    versions = sorted(p.name for p in logs.rglob(f'{subsets.PDS4_BUNDLE}_md5_v*.txt'))
    assert versions == [f'{subsets.PDS4_BUNDLE}_md5_v001.txt'], run.describe()

    versioned = next(logs.rglob(versions[0]))
    assert versioned.read_bytes() == first
    assert fresh_tree.path(CHECKSUM_FILE).exists()

    # A second run versions the file the first run left, rather than overwriting
    # the copy it made.
    run = support.run_tool(fresh_tree, 'pds4checksums', '--reinitialize',
                           fresh_tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()

    versions = sorted(p.name for p in logs.rglob(f'{subsets.PDS4_BUNDLE}_md5_v*.txt'))
    assert versions == [f'{subsets.PDS4_BUNDLE}_md5_v001.txt',
                        f'{subsets.PDS4_BUNDLE}_md5_v002.txt'], run.describe()


def test_no_targets_leaves_no_unbound_state(fresh_tree):
    """A bundle set with no bundles in it completes instead of raising.

    Expanding the command-line path can legitimately yield nothing, and the run
    then has no task result to decide the --infoshelf chain on. Both checksums
    tools share the driver that used to leave that result unassigned; this is the
    pds4 half of the pds3 test of the same name.

    The bundle set has to be one PDS4 recognizes, so this empties the declared one
    rather than inventing a name: a bundle set directory with its bundles removed
    is the state a fresh mirror is in before anything has been synced into it.
    """

    import shutil

    bundleset = fresh_tree.holdings / 'bundles' / subsets.PDS4_BUNDLESET
    shutil.rmtree(bundleset / subsets.PDS4_BUNDLE, ignore_errors=True)
    assert bundleset.is_dir()
    assert not any(bundleset.iterdir())

    run = support.run_tool(fresh_tree, 'pds4checksums', '--validate', bundleset)
    assert run.returncode == 0, run.describe()
    assert 'UnboundLocalError' not in run.stderr, run.describe()
    assert 'Traceback' not in run.stderr, run.describe()


##########################################################################################
# The --infoshelf chain
#
# pds4checksums --infoshelf re-runs its own command line as a pds4infoshelf command,
# which it builds by rewriting argv[0]. That only resolves to the other tool when
# argv[0] is a console script, so this test invokes it as an install would.
##########################################################################################

@pytest.fixture
def scripts(tmp_path):
    """Console scripts for the two tools the chain involves."""

    return support.console_scripts(tmp_path / 'bin', 'pds4checksums', 'pds4infoshelf')


def test_infoshelf_chain_runs_the_infoshelf_tool(fresh_tree, scripts):
    """--initialize --infoshelf writes the checksum file and then the info shelf."""

    run = support.run_console_script(fresh_tree, scripts / 'pds4checksums',
                                     '--initialize', '--infoshelf',
                                     fresh_tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()
    assert fresh_tree.path(CHECKSUM_FILE).exists(), run.describe()

    shelf = fresh_tree.path(f'_infoshelf-bundles/{subsets.PDS4_BUNDLESET}/'
                            f'{subsets.PDS4_BUNDLE}_info.pickle')
    assert shelf.exists(), run.describe()

    # Both tools logged, the second one under its own logger name.
    assert 'pds.validation.checksums' in run.output, run.describe()
    assert 'pds.validation.fileinfo' in run.output, run.describe()
