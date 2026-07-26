##########################################################################################
# tests/holdings_maintenance/test_pds4_linkshelf.py
#
# Full task cycle for pds4linkshelf against a copy of one declared PDS4 subset.
#
# The declared subset is three matched label/table pairs, so the shelved graph has
# real edges in both directions (label -> table, table -> label) rather than the
# empty lists a labels-only subset would produce.
#
# The final test pins a known defect: --update raises AttributeError against any
# existing shelf (pds4linkshelf.py:395). PR-27 owns the fix.
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
SHELF_DIR = f'_linkshelf-bundles/{subsets.PDS4_BUNDLESET}'
SIDECAR = f'{SHELF_DIR}/{subsets.PDS4_BUNDLE}_links.py'
PICKLE = f'{SHELF_DIR}/{subsets.PDS4_BUNDLE}_links.pickle'
ALPHA_LABEL = f'{BUNDLE_DIR}/data/rings/u0_kao_91cm_734nm_radius_alpha_egress_1000m.xml'
ALPHA_TABLE = f'{BUNDLE_DIR}/data/rings/u0_kao_91cm_734nm_radius_alpha_egress_1000m.tab'

NEW_FILE = f'{BUNDLE_DIR}/data/rings/u0_kao_91cm_extra_added_by_tests.txt'
NEW_FILE_BYTES = b'added by the pr-13 update test\n'
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


def repin_mtimes(tree):
    """Restore every declared source file's pinned modification time."""

    for relpath, mtime in SOURCE_MTIMES.items():
        path = tree.path(relpath)
        if path.exists():
            support.shift_mtime(path, mtime - path.stat().st_mtime)


def test_initialize_writes_the_expected_sidecar(tool_tree, golden_update):
    """--initialize builds the link shelf and the .py sidecar matches the golden."""

    run = support.run_tool(tool_tree, 'pds4linkshelf', '--initialize',
                           tool_tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()

    sidecar = tool_tree.path(SIDECAR)
    assert sidecar.exists(), run.describe()
    assert tool_tree.path(PICKLE).exists(), run.describe()

    text = support.sidecar_text(sidecar)
    support.check_golden('pds4_linkshelf_sidecar', text, golden_update)

    # Every label points at its table, and every table points back at its label.
    for stem in ('alpha', 'beta', 'gamma'):
        label = f'data/rings/u0_kao_91cm_734nm_radius_{stem}_egress_1000m.xml'
        table = f'data/rings/u0_kao_91cm_734nm_radius_{stem}_egress_1000m.tab'
        label_line = next(ln for ln in text.splitlines()
                          if ln.strip().startswith(f'"{label}"'))
        assert table in label_line, label_line
        table_line = next(ln for ln in text.splitlines()
                          if ln.strip().startswith(f'"{table}"'))
        assert table_line.rstrip().endswith(f'"{label}",'), table_line


def test_initialize_refuses_to_clobber(tool_tree):
    """A second --initialize reports the existing shelf and exits non-zero."""

    run = support.run_tool(tool_tree, 'pds4linkshelf', '--initialize',
                           tool_tree.path(BUNDLE_DIR))
    assert run.returncode == 1, run.describe()
    assert any('Link shelf file already exists' in line for line in run.error_lines), \
        run.describe()


def test_validate_is_clean_after_initialize(tool_tree):
    """--validate on an untouched tree exits 0 and logs no errors."""

    run = support.run_tool(tool_tree, 'pds4linkshelf', '--validate',
                           tool_tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()


@pytest.mark.parametrize('corruption', CORRUPTIONS, ids=[c.name for c in CORRUPTIONS])
def test_corruption_is_detected_and_repaired(tool_tree, corruption):
    """Each fixed corruption fails --validate, and --repair restores a clean shelf."""

    target = tool_tree.path(corruption.target)
    original = target.read_bytes()
    corruption.damage(target)

    run = support.run_tool(tool_tree, 'pds4linkshelf', '--validate',
                           tool_tree.path(BUNDLE_DIR))
    assert run.returncode == 1, f'{corruption.description}\n{run.describe()}'
    assert any(corruption.expected in line and corruption.target.rpartition('/')[2] in line
               for line in run.error_lines), \
        f'{corruption.description}\n{run.describe()}'

    run = support.run_tool(tool_tree, 'pds4linkshelf', '--repair',
                           tool_tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()

    run = support.run_tool(tool_tree, 'pds4linkshelf', '--validate',
                           tool_tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()

    # Put the table back; the shelf must list it again after a second repair.
    target.write_bytes(original)
    repin_mtimes(tool_tree)
    run = support.run_tool(tool_tree, 'pds4linkshelf', '--repair',
                           tool_tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()
    assert corruption.target.rpartition('/')[2] in \
        support.sidecar_text(tool_tree.path(SIDECAR))


def test_update_is_broken_and_repair_is_the_working_path(tool_tree):
    """Pin the known defect: pds4linkshelf --update raises on any existing shelf.

    generate_links() is handed the *loaded* shelf as its old_links argument, whose
    values are the plain tuples that were pickled, then dereferences
    `info.linktext` on them (pds4linkshelf.py:395). Any --update against an
    existing shelf therefore dies with AttributeError. Its pds3 twin merges the
    same data correctly, so this is a pds4-only defect; PR-27 owns the fix, and
    when it lands this assertion must be inverted.
    """

    support.add_file(tool_tree, NEW_FILE, NEW_FILE_BYTES, NEW_FILE_MTIME)

    run = support.run_tool(tool_tree, 'pds4linkshelf', '--validate',
                           tool_tree.path(BUNDLE_DIR))
    assert run.returncode == 1, run.describe()
    assert any('Missing link shelf file entry for' in line
               and 'extra_added_by_tests' in line for line in run.error_lines), \
        run.describe()

    run = support.run_tool(tool_tree, 'pds4linkshelf', '--update',
                           tool_tree.path(BUNDLE_DIR))
    assert run.returncode == 1, run.describe()
    assert "'tuple' object has no attribute 'linktext'" in run.output, run.describe()

    # --repair takes the same tree to a clean, complete shelf.
    run = support.run_tool(tool_tree, 'pds4linkshelf', '--repair',
                           tool_tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()
    assert 'extra_added_by_tests' in support.sidecar_text(tool_tree.path(SIDECAR))

    run = support.run_tool(tool_tree, 'pds4linkshelf', '--validate',
                           tool_tree.path(BUNDLE_DIR))
    assert run.returncode == 0, run.describe()
    assert run.error_lines == [], run.describe()
