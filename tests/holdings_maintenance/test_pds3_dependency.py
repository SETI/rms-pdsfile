##########################################################################################
# tests/holdings_maintenance/test_pds3_dependency.py
#
# pdsdependency against a copy of one declared PDS3 subset.
#
# pdsdependency has no task flags: it inspects a volume's derived products and
# prints the maintenance commands needed to bring them up to date. The tests here
# start from a tree that has *no* derived products, pin the emitted "Steps
# required" list against a golden, then perform some of those steps and show the
# corresponding lines disappear.
#
# pdsdependency is pds3-only by design: the parent plan records that it has no
# pds4 twin and stays a standalone tool.
#
# The `tool_tree` fixture is module-scoped, so these tests share one temporary tree
# and run in definition order.
##########################################################################################

import pytest

from tests.holdings_maintenance import subsets, support

pytestmark = pytest.mark.full_holdings

SOURCE_FLAVOR = 'pds3'
SOURCE_FINGERPRINTS = subsets.PDS3_SOURCES
SOURCE_PATHS = subsets.paths_of(subsets.PDS3_SOURCES)
SOURCE_MTIMES = subsets.PDS3_MTIMES

VOLUME_DIR = f'volumes/{subsets.PDS3_VOLSET}/{subsets.PDS3_VOLUME}'
METADATA_DIR = f'metadata/{subsets.PDS3_VOLSET}/{subsets.PDS3_VOLUME}'


def steps_required(run, tree):
    """Return the "Steps required" commands, with the temporary root masked out.

    Args:
        run: The ToolRun to read.
        tree: The ToolTree the run was made against.

    Returns:
        list[str]: One command per line, in the order the tool printed them.
    """

    lines = run.output.splitlines()
    assert 'Steps required:' in lines, run.describe()
    steps = lines[lines.index('Steps required:') + 1:]

    return [step.strip().replace(str(tree.disk), '$DISK')
            for step in steps if step.strip()]


def test_missing_derived_products_are_reported(tool_tree, golden_update):
    """With no derived products at all, the emitted step list matches the golden."""

    run = support.run_tool(tool_tree, 'pdsdependency', tool_tree.path(VOLUME_DIR))
    assert run.returncode == 1, run.describe()

    steps = steps_required(run, tool_tree)
    support.check_golden('pds3_dependency_steps', ''.join(f'{s}\n' for s in steps),
                         golden_update)

    # The list is a real work plan, not an opaque blob.
    assert any(step.startswith('pdschecksums --initialize') for step in steps), steps
    assert any(step.startswith('pdsinfoshelf --initialize') for step in steps), steps
    assert any(step.startswith('pdsarchives --initialize') for step in steps), steps
    assert any(step.startswith('pdslinkshelf --initialize') for step in steps), steps
    assert any(step.startswith('pdsindexshelf --initialize') for step in steps), steps

    # Every step names a path inside the temporary tree; none leaks a real root.
    for step in steps:
        assert '$DISK' in step, step

    # The errors that motivated the steps name the specific missing products.
    assert any('Missing file' in line and 'checksums-metadata' in line
               for line in run.error_lines), run.describe()


def test_metadata_steps_disappear_once_performed(tool_tree):
    """Running the metadata checksum and info steps removes them from the report."""

    before = steps_required(
        support.run_tool(tool_tree, 'pdsdependency', tool_tree.path(VOLUME_DIR)),
        tool_tree)
    assert any('pdschecksums --initialize' in step and 'metadata' in step
               for step in before), before

    for tool in ('pdschecksums', 'pdsinfoshelf'):
        run = support.run_tool(tool_tree, tool, '--initialize',
                               tool_tree.path(METADATA_DIR))
        assert run.returncode == 0, run.describe()

    after = steps_required(
        support.run_tool(tool_tree, 'pdsdependency', tool_tree.path(VOLUME_DIR)),
        tool_tree)

    assert not any('pdschecksums --initialize' in step and step.endswith(
        f'metadata/{subsets.PDS3_VOLSET}/{subsets.PDS3_VOLUME}') for step in after), after
    assert not any('pdsinfoshelf --initialize' in step and step.endswith(
        f'metadata/{subsets.PDS3_VOLSET}/{subsets.PDS3_VOLUME}') for step in after), after
    assert len(after) < len(before), (before, after)


def test_a_missing_volume_is_refused(tool_tree):
    """A path that does not exist is refused before any dependency work starts."""

    run = support.run_tool(tool_tree, 'pdsdependency',
                           tool_tree.path('volumes/HSTNx_xxxx/HSTN0_0000'))
    assert run.returncode == 1, run.describe()
    assert 'No such file or directory' in run.output, run.describe()
