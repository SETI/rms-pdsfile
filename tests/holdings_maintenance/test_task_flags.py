##########################################################################################
# tests/holdings_maintenance/test_task_flags.py
#
# Pins how the maintenance tools resolve their five task flags today.
#
# Every tool declares --initialize/--reinitialize/--validate/--repair/--update as
# five independent `store_const` actions writing into the same `task` destination.
# They are NOT an argparse mutually exclusive group, so passing two of them is
# accepted and the LAST one on the command line wins, silently.
#
# The Phase 6 consolidation factors this parser into a shared module and is
# forbidden from introducing add_mutually_exclusive_group(), which would turn
# today's silent last-wins into a hard argparse error -- an observable CLI change.
# These tests are what makes that regression visible.
#
# Only the resolution of the task flags is under test; each case asserts which task
# the tool announced, not what it then did. Every test rebuilds the tree first, so
# each one is independent and order-agnostic.
##########################################################################################

import pytest

from tests.holdings_maintenance import subsets, support

pytestmark = pytest.mark.full_holdings

SOURCE_FLAVOR = 'pds3'
SOURCE_FINGERPRINTS = subsets.PDS3_VOLUME_SOURCES
SOURCE_PATHS = subsets.paths_of(subsets.PDS3_VOLUME_SOURCES)
SOURCE_MTIMES = subsets.PDS3_VOLUME_MTIMES

VOLUME_DIR = f'volumes/{subsets.PDS3_VOLSET}/{subsets.PDS3_VOLUME}'


def task_announced(run):
    """Return the task name from the tool's "Task ... for" log header.

    Args:
        run: The ToolRun to read.

    Returns:
        str: The task the tool actually ran.
    """

    for line in run.output.splitlines():
        _, sep, tail = line.partition('| HEADER | Task ')
        if sep and ' for' in tail:
            return tail.partition(' for')[0].strip('" ')

    raise AssertionError(f'no task header in output\n{run.describe()}')


def test_a_missing_task_is_an_error(fresh_tree):
    """With no task flag at all the tool refuses to run."""

    run = support.run_tool(fresh_tree, 'pdsarchives', fresh_tree.path(VOLUME_DIR))
    assert run.returncode == 1, run.describe()
    assert 'pdsarchives error: Missing task' in run.output, run.describe()


@pytest.mark.parametrize(('flags', 'expected'),
                         [(('--validate', '--update'), 'update'),
                          (('--update', '--validate'), 'validate'),
                          (('--initialize', '--validate'), 'validate'),
                          (('--validate', '--initialize', '--update'), 'update')])
def test_two_task_flags_resolve_to_the_last_one(fresh_tree, flags, expected):
    """Multiple task flags are accepted; the rightmost one silently wins.

    If the shared parser ever grows a mutually exclusive group, argparse will exit
    2 with "not allowed with argument" and these cases will fail -- which is the
    point.
    """

    run = support.run_tool(fresh_tree, 'pdsarchives', *flags,
                           fresh_tree.path(VOLUME_DIR))
    assert run.returncode != 2, run.describe()
    assert 'not allowed with argument' not in run.output, run.describe()
    assert task_announced(run) == expected, run.describe()


def test_another_pds3_tool_resolves_task_flags_the_same_way(fresh_tree):
    """A second tool with a different log format resolves the flags identically.

    pdschecksums writes `Task "update" for`, pdsarchives writes `Task update for`;
    both parse the flags the same way. The pds4 half of the pair is covered in
    test_pds4_checksums.py, which has a pds4 tree to point at.
    """

    run = support.run_tool(fresh_tree, 'pdschecksums', '--validate', '--update',
                           fresh_tree.path(VOLUME_DIR))
    assert 'not allowed with argument' not in run.output, run.describe()
    assert task_announced(run) == 'update', run.describe()


def test_short_and_long_aliases_select_the_same_task(fresh_tree):
    """--init is an alias of --initialize, and --reinit of --reinitialize."""

    run = support.run_tool(fresh_tree, 'pdsarchives', '--init',
                           fresh_tree.path(VOLUME_DIR))
    assert task_announced(run) == 'initialize', run.describe()

    run = support.run_tool(fresh_tree, 'pdsarchives', '--reinit',
                           fresh_tree.path(VOLUME_DIR))
    assert task_announced(run) == 'reinitialize', run.describe()
