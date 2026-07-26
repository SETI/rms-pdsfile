##########################################################################################
# tests/holdings_maintenance/test_pds3_linkshelf.py
#
# Full task cycle for pdslinkshelf against a copy of one declared PDS3 subset.
#
# The subject volume's detached label (N4BI01L4Q.LBL) points at all five of its
# sibling products, so the shelf it produces is a real link graph rather than an
# empty one.
#
# The `tool_tree` fixture is module-scoped, so these tests share one temporary tree
# and run in definition order; every mutating test restores a clean tree.
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

NEW_FILE = f'{VOLUME_DIR}/DATA/VISIT_01/N4BI01L4Q_EXTRA.TXT'
NEW_FILE_BYTES = b'ADDED BY THE PDS-13 UPDATE TEST\r\n'
NEW_FILE_MTIME = subsets.PDS3_MTIMES[LABEL] + 1000

Corruption = namedtuple('Corruption', 'name description target damage expected')

# Fixed corruption scenarios. pdslinkshelf compares the link graph it derives from
# the labels against the shelved graph, so damage that changes the graph is what
# it reports.
CORRUPTIONS = (
    Corruption('link_target_removed',
               'delete the CAL preview that the label points at',
               LINK_TARGET, lambda path: path.unlink(),
               'Link shelf file entry found for missing file'),
)


def repin_mtimes(tree):
    """Restore every declared source file's pinned modification time."""

    for relpath, mtime in SOURCE_MTIMES.items():
        path = tree.path(relpath)
        if path.exists():
            support.shift_mtime(path, mtime - path.stat().st_mtime)


def test_initialize_writes_the_expected_sidecar(tool_tree, golden_update):
    """--initialize builds the link shelf and the .py sidecar matches the golden."""

    run = support.run_tool(tool_tree, 'pdslinkshelf', '--initialize',
                           tool_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()

    sidecar = tool_tree.path(SIDECAR)
    assert sidecar.exists(), run.describe()
    assert tool_tree.path(PICKLE).exists(), run.describe()

    text = support.sidecar_text(sidecar)
    support.check_golden('pds3_linkshelf_sidecar', text, golden_update)

    # The shelved graph is real: the label lists all five of its products, and each
    # product points back at the label.
    for product in ('N4BI01L4Q.ASC', 'N4BI01L4Q_RAW.TIF', 'N4BI01L4Q_RAW.JPG',
                    'N4BI01L4Q_IMA.JPG', 'N4BI01L4Q_CAL.JPG'):
        assert f'DATA/VISIT_01/{product}' in text, text
        assert f'"DATA/VISIT_01/{product}"' in text
    assert text.count('"DATA/VISIT_01/N4BI01L4Q.LBL"') == 6, text


def test_initialize_refuses_to_clobber(tool_tree):
    """A second --initialize reports the existing shelf and exits non-zero."""

    run = support.run_tool(tool_tree, 'pdslinkshelf', '--initialize',
                           tool_tree.path(VOLUME_DIR))
    assert run.returncode == 1, run.describe()
    assert any('Link shelf file already exists' in line for line in run.error_lines), \
        run.describe()


def test_validate_is_clean_after_initialize(tool_tree):
    """--validate on an untouched tree exits 0 and logs no errors."""

    run = support.run_tool(tool_tree, 'pdslinkshelf', '--validate',
                           tool_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()


@pytest.mark.parametrize('corruption', CORRUPTIONS, ids=[c.name for c in CORRUPTIONS])
def test_corruption_is_detected_and_repaired(tool_tree, corruption):
    """Each fixed corruption fails --validate, and --repair restores a clean shelf."""

    target = tool_tree.path(corruption.target)
    original = target.read_bytes()
    corruption.damage(target)

    run = support.run_tool(tool_tree, 'pdslinkshelf', '--validate',
                           tool_tree.path(VOLUME_DIR))
    assert run.returncode == 1, f'{corruption.description}\n{run.describe()}'
    assert any(corruption.expected in line and corruption.target.rpartition('/')[2] in line
               for line in run.error_lines), \
        f'{corruption.description}\n{run.describe()}'

    run = support.run_tool(tool_tree, 'pdslinkshelf', '--repair',
                           tool_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()

    run = support.run_tool(tool_tree, 'pdslinkshelf', '--validate',
                           tool_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()
    assert corruption.target.rpartition('/')[2] not in \
        support.sidecar_text(tool_tree.path(SIDECAR))

    # Put the product back; the shelf must list it again after a second repair.
    target.write_bytes(original)
    repin_mtimes(tool_tree)
    run = support.run_tool(tool_tree, 'pdslinkshelf', '--repair',
                           tool_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()

    run = support.run_tool(tool_tree, 'pdslinkshelf', '--validate',
                           tool_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()


def test_update_picks_up_a_new_file(tool_tree):
    """--update adds an unlinked new file to the shelf and revalidates clean."""

    support.add_file(tool_tree, NEW_FILE, NEW_FILE_BYTES, NEW_FILE_MTIME)

    run = support.run_tool(tool_tree, 'pdslinkshelf', '--validate',
                           tool_tree.path(VOLUME_DIR))
    assert run.returncode == 1, run.describe()
    assert any('Missing link shelf file entry for' in line
               and 'N4BI01L4Q_EXTRA.TXT' in line for line in run.error_lines), \
        run.describe()

    run = support.run_tool(tool_tree, 'pdslinkshelf', '--update',
                           tool_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert 'N4BI01L4Q_EXTRA.TXT' in support.sidecar_text(tool_tree.path(SIDECAR))

    run = support.run_tool(tool_tree, 'pdslinkshelf', '--validate',
                           tool_tree.path(VOLUME_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()
