##########################################################################################
# tests/holdings_maintenance/test_pds3_linkshelf.py
#
# Full task cycle for pdslinkshelf against a copy of one declared PDS3 subset.
#
# The subject volume's detached label points at all five of its sibling products,
# so the shelf it produces is a real link graph rather than an empty one.
#
# Every test rebuilds the tree first, so each one is independent and order-agnostic.
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
SHELF_DIR = f'_linkshelf-volumes/{subsets.PDS3_VOLSET}'
SIDECAR = f'{SHELF_DIR}/{subsets.PDS3_VOLUME}_links.py'
PICKLE = f'{SHELF_DIR}/{subsets.PDS3_VOLUME}_links.pickle'
LABEL = f'{VOLUME_DIR}/DATA/VISIT_01/N4BI01L4Q.LBL'
LINK_TARGET = f'{VOLUME_DIR}/DATA/VISIT_01/N4BI01L4Q_CAL.JPG'

PRODUCTS = ('N4BI01L4Q.ASC', 'N4BI01L4Q_RAW.TIF', 'N4BI01L4Q_RAW.JPG',
            'N4BI01L4Q_IMA.JPG', 'N4BI01L4Q_CAL.JPG')

NEW_FILE = f'{VOLUME_DIR}/DATA/VISIT_01/N4BI01L4Q_EXTRA.TXT'
NEW_FILE_BYTES = b'ADDED BY AN UPDATE TEST\r\n'
NEW_FILE_MTIME = subsets.PDS3_MTIMES[LABEL] + 1000

Corruption = namedtuple('Corruption', 'name description target damage expected')

# Fixed corruption scenarios. pdslinkshelf compares the link graph it derives from
# the labels against the shelved graph, so damage that changes the graph is what it
# reports.
CORRUPTIONS = (
    Corruption('link_target_removed',
               'delete the CAL preview that the label points at',
               LINK_TARGET, lambda path: path.unlink(),
               'Link shelf file entry found for missing file'),
)


@pytest.fixture
def shelved_tree(fresh_tree):
    """A freshly rebuilt tree with the link shelf already generated."""

    support.initialize(fresh_tree, 'pdslinkshelf', fresh_tree.path(VOLUME_DIR))

    return fresh_tree


def test_initialize_writes_the_expected_sidecar(fresh_tree, golden_update):
    """--initialize builds the link shelf and the .py sidecar matches the golden."""

    support.initialize(fresh_tree, 'pdslinkshelf', fresh_tree.path(VOLUME_DIR))

    sidecar = fresh_tree.path(SIDECAR)
    assert sidecar.exists()
    assert fresh_tree.path(PICKLE).exists()

    text = support.sidecar_text(sidecar)
    support.check_golden('pds3_linkshelf_sidecar', text, golden_update)

    # The shelved graph is real: the label lists all five of its products, and each
    # product points back at the label.
    label_entry = text.partition('"DATA/VISIT_01/N4BI01L4Q.LBL"')[2]
    label_entry = label_entry.partition('\n  "')[0]
    for product in PRODUCTS:
        assert f'DATA/VISIT_01/{product}' in label_entry, label_entry
        product_line = next(line for line in text.splitlines()
                            if line.strip().startswith(f'"DATA/VISIT_01/{product}"'))
        assert product_line.rstrip().endswith('"DATA/VISIT_01/N4BI01L4Q.LBL",'), \
            product_line


def test_initialize_refuses_to_clobber(shelved_tree):
    """A second --initialize reports the existing shelf and exits non-zero."""

    run = support.run_tool(shelved_tree, 'pdslinkshelf', '--initialize',
                           shelved_tree.path(VOLUME_DIR))
    assert run.returncode == 1, run.describe()
    assert any('Link shelf file already exists' in line for line in run.error_lines), \
        run.describe()


def test_validate_is_clean_after_initialize(shelved_tree):
    """--validate on an untouched tree exits 0 and logs no errors."""

    run = support.run_tool(shelved_tree, 'pdslinkshelf', '--validate',
                           shelved_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()


@pytest.mark.parametrize('corruption', CORRUPTIONS, ids=[c.name for c in CORRUPTIONS])
def test_corruption_is_detected_and_repaired(shelved_tree, corruption):
    """Each fixed corruption fails --validate, and --repair restores a clean shelf."""

    corruption.damage(shelved_tree.path(corruption.target))

    run = support.run_tool(shelved_tree, 'pdslinkshelf', '--validate',
                           shelved_tree.path(VOLUME_DIR))
    assert run.returncode == 1, f'{corruption.description}\n{run.describe()}'
    assert any(corruption.expected in line and corruption.target.rpartition('/')[2] in line
               for line in run.error_lines), \
        f'{corruption.description}\n{run.describe()}'

    run = support.run_tool(shelved_tree, 'pdslinkshelf', '--repair',
                           shelved_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()

    run = support.run_tool(shelved_tree, 'pdslinkshelf', '--validate',
                           shelved_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()

    # The repaired shelf no longer references the deleted product.
    assert corruption.target.rpartition('/')[2] not in \
        support.sidecar_text(shelved_tree.path(SIDECAR))


def test_update_picks_up_a_new_file(shelved_tree):
    """--update adds an unlinked new file to the shelf and revalidates clean."""

    support.add_file(shelved_tree, NEW_FILE, NEW_FILE_BYTES, NEW_FILE_MTIME)

    run = support.run_tool(shelved_tree, 'pdslinkshelf', '--validate',
                           shelved_tree.path(VOLUME_DIR))
    assert run.returncode == 1, run.describe()
    assert any('Missing link shelf file entry for' in line
               and 'N4BI01L4Q_EXTRA.TXT' in line for line in run.error_lines), \
        run.describe()

    run = support.run_tool(shelved_tree, 'pdslinkshelf', '--update',
                           shelved_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert 'N4BI01L4Q_EXTRA.TXT' in support.sidecar_text(shelved_tree.path(SIDECAR))

    run = support.run_tool(shelved_tree, 'pdslinkshelf', '--validate',
                           shelved_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()


def test_update_versions_the_shelf_file_it_replaces(shelved_tree):
    """--update copies the superseded link shelf into the log directory.

    _common.move_old_links() versions the shelf the task is about to rewrite, as
    <name>_v###<ext> beside the run's own log file, and copies the `.py` and
    `.pickle` files alongside it. It reads the shared LOGDIRS list that main()
    fills in through _common.set_log_dirs(), so a tool that leaves that list empty
    versions nothing.
    """

    support.add_file(shelved_tree, NEW_FILE, NEW_FILE_BYTES, NEW_FILE_MTIME)
    first_pickle = shelved_tree.path(PICKLE).read_bytes()
    first_sidecar = shelved_tree.path(SIDECAR).read_bytes()

    run = support.run_tool(shelved_tree, 'pdslinkshelf', '--update',
                           shelved_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert 'Link shelf file moved from: ' in run.output, run.describe()
    assert 'Link shelf file moved to ' in run.output, run.describe()

    logs = shelved_tree.disk / 'logs'
    versions = sorted(p.name for p in logs.rglob(f'{subsets.PDS3_VOLUME}_links_v*'))
    assert versions == [f'{subsets.PDS3_VOLUME}_links_v001.pickle',
                        f'{subsets.PDS3_VOLUME}_links_v001.py'], run.describe()

    assert next(logs.rglob(versions[0])).read_bytes() == first_pickle
    assert next(logs.rglob(versions[1])).read_bytes() == first_sidecar
    assert shelved_tree.path(PICKLE).exists()
