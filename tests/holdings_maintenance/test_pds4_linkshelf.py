##########################################################################################
# tests/holdings_maintenance/test_pds4_linkshelf.py
#
# Full task cycle for pds4linkshelf against a copy of one declared PDS4 subset.
#
# The declared subset is three matched label/table pairs, so the shelved graph has
# real edges in both directions (label -> table, table -> label) rather than the
# empty lists a labels-only subset would produce.
#
# The final test pins a known defect: --update raises against any existing shelf,
# so --repair is the only working path.
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
SHELF_DIR = f'_linkshelf-bundles/{subsets.PDS4_BUNDLESET}'
SIDECAR = f'{SHELF_DIR}/{subsets.PDS4_BUNDLE}_links.py'
PICKLE = f'{SHELF_DIR}/{subsets.PDS4_BUNDLE}_links.pickle'
ALPHA_LABEL = f'{BUNDLE_DIR}/data/rings/u0_kao_91cm_734nm_radius_alpha_egress_1000m.xml'
ALPHA_TABLE = f'{BUNDLE_DIR}/data/rings/u0_kao_91cm_734nm_radius_alpha_egress_1000m.tab'

RING_STEMS = ('alpha', 'beta', 'gamma')

NEW_FILE = f'{BUNDLE_DIR}/data/rings/u0_kao_91cm_extra_added_by_tests.txt'
NEW_FILE_BYTES = b'added by an update test\n'
NEW_FILE_MTIME = subsets.PDS4_MTIMES[ALPHA_LABEL] + 1000

Corruption = namedtuple('Corruption', 'name description target damage expected')

# Fixed corruption scenarios. Removing a table that a label points at breaks a
# shelved edge in both directions.
CORRUPTIONS = (
    Corruption('alpha_table_removed',
               'delete the alpha-ring table that its label points at',
               ALPHA_TABLE, lambda path: path.unlink(),
               'Link shelf file entry found for missing file'),
)


@pytest.fixture
def shelved_tree(fresh_tree):
    """A freshly rebuilt tree with the link shelf already generated."""

    support.initialize(fresh_tree, 'pds4linkshelf', fresh_tree.path(BUNDLE_DIR))

    return fresh_tree


def test_initialize_writes_the_expected_sidecar(fresh_tree, golden_update):
    """--initialize builds the link shelf and the .py sidecar matches the golden."""

    support.initialize(fresh_tree, 'pds4linkshelf', fresh_tree.path(BUNDLE_DIR))

    sidecar = fresh_tree.path(SIDECAR)
    assert sidecar.exists()
    assert fresh_tree.path(PICKLE).exists()

    text = support.sidecar_text(sidecar)
    support.check_golden('pds4_linkshelf_sidecar', text, golden_update)

    # Every label points at its table, and every table points back at its label.
    for stem in RING_STEMS:
        label = f'data/rings/u0_kao_91cm_734nm_radius_{stem}_egress_1000m.xml'
        table = f'data/rings/u0_kao_91cm_734nm_radius_{stem}_egress_1000m.tab'
        label_line = next(line for line in text.splitlines()
                          if line.strip().startswith(f'"{label}"'))
        assert table in label_line, label_line
        table_line = next(line for line in text.splitlines()
                          if line.strip().startswith(f'"{table}"'))
        assert table_line.rstrip().endswith(f'"{label}",'), table_line


def test_initialize_refuses_to_clobber(shelved_tree):
    """A second --initialize reports the existing shelf and exits non-zero."""

    run = support.run_tool(shelved_tree, 'pds4linkshelf', '--initialize',
                           shelved_tree.path(BUNDLE_DIR))
    assert run.returncode == 1, run.describe()
    assert any('Link shelf file already exists' in line for line in run.error_lines), \
        run.describe()


def test_validate_is_clean_after_initialize(shelved_tree):
    """--validate on an untouched tree exits 0 and logs no errors."""

    run = support.run_tool(shelved_tree, 'pds4linkshelf', '--validate',
                           shelved_tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()


@pytest.mark.parametrize('corruption', CORRUPTIONS, ids=[c.name for c in CORRUPTIONS])
def test_corruption_is_detected_and_repaired(shelved_tree, corruption):
    """Each fixed corruption fails --validate, and --repair restores a clean shelf."""

    corruption.damage(shelved_tree.path(corruption.target))

    run = support.run_tool(shelved_tree, 'pds4linkshelf', '--validate',
                           shelved_tree.path(BUNDLE_DIR))
    assert run.returncode == 1, f'{corruption.description}\n{run.describe()}'
    assert any(corruption.expected in line and corruption.target.rpartition('/')[2] in line
               for line in run.error_lines), \
        f'{corruption.description}\n{run.describe()}'

    run = support.run_tool(shelved_tree, 'pds4linkshelf', '--repair',
                           shelved_tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()

    run = support.run_tool(shelved_tree, 'pds4linkshelf', '--validate',
                           shelved_tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()

    # The repaired shelf no longer references the deleted table.
    text = support.sidecar_text(shelved_tree.path(SIDECAR))
    assert corruption.target.rpartition('/')[2] not in text, text


def test_update_is_broken_and_repair_is_the_working_path(shelved_tree):
    """--update raises against any existing shelf; --repair is what works.

    generate_links() is handed the loaded shelf as old_links, whose values are the
    plain tuples that were pickled, and then dereferences info.linktext on them.
    That is a defect, pinned here as current behaviour; its pds3 twin merges the
    same data correctly, so this is pds4-only.
    """

    support.add_file(shelved_tree, NEW_FILE, NEW_FILE_BYTES, NEW_FILE_MTIME)

    run = support.run_tool(shelved_tree, 'pds4linkshelf', '--validate',
                           shelved_tree.path(BUNDLE_DIR))
    assert run.returncode == 1, run.describe()
    assert any('Missing link shelf file entry for' in line
               and 'extra_added_by_tests' in line for line in run.error_lines), \
        run.describe()

    run = support.run_tool(shelved_tree, 'pds4linkshelf', '--update',
                           shelved_tree.path(BUNDLE_DIR))
    assert run.returncode == 1, run.describe()
    assert "'tuple' object has no attribute 'linktext'" in run.output, run.describe()

    run = support.run_tool(shelved_tree, 'pds4linkshelf', '--repair',
                           shelved_tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()
    assert 'extra_added_by_tests' in support.sidecar_text(shelved_tree.path(SIDECAR))

    run = support.run_tool(shelved_tree, 'pds4linkshelf', '--validate',
                           shelved_tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()
