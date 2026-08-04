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
# pdsdependency is pds3-only by design: it has no pds4 twin and stays a standalone
# tool.
#
# The emitted order is only partly pinned. A dependency rule emits its messages, in
# source order, once per path its glob matched -- and that glob is unsorted, so
# when a rule matches several files its steps land in directory-enumeration order,
# which varies by filesystem. For this subset that is exactly the six steps naming
# an individual metadata table; the other twelve come from rules matching a single
# path and are emitted in a fixed order (verified by running the tool with its
# enumeration forced both ways).
#
# So the golden is compared as a sorted multiset -- pinning the exact set and text
# of every step -- and the twelve stable steps are additionally pinned in exact
# order, which keeps the dependency semantics under test: a target's archive is
# built before the checksums of that archive, and its checksums before its info
# shelf. The unsorted glob is a defect the tests work around rather than assert:
# when the tool starts sorting, these tests keep passing and the golden stays
# valid.
#
# Every test rebuilds the tree first, so each one is independent and order-agnostic.
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


def rule_ordered_steps(steps):
    """Return the steps whose position the tool actually determines, in order.

    Steps naming an individual metadata table come from a rule whose glob matched
    several files, so their position is directory-enumeration order and is not the
    tool's to promise. Every other step comes from a rule that matched one path.

    Args:
        steps: The emitted steps, in order.

    Returns:
        list[str]: The subsequence whose order is deterministic.
    """

    return [step for step in steps if '.tab' not in step]


def steps_required(run, tree):
    """Return the "Steps required" commands, with the temporary root masked out.

    Args:
        run: The ToolRun to read.
        tree: The ToolTree the run was made against.

    Read from stdout only: stderr carries interpreter and library warnings, which
    vary by Python version and dependency version and are no part of the plan.

    Returns:
        list[str]: One command per line, in the order the tool printed them.
    """

    lines = run.stdout.splitlines()
    assert 'Steps required:' in lines, run.describe()
    steps = lines[lines.index('Steps required:') + 1:]

    return [step.strip().replace(str(tree.disk), '$DISK')
            for step in steps if step.strip()]


def test_missing_derived_products_are_reported(fresh_tree, golden_update):
    """With no derived products at all, the emitted step list matches the golden."""

    run = support.run_tool(fresh_tree, 'pdsdependency', fresh_tree.path(VOLUME_DIR))
    assert run.returncode == 1, run.describe()

    steps = steps_required(run, fresh_tree)
    support.check_golden('pds3_dependency_steps', ''.join(f'{s}\n' for s in steps),
                         golden_update, unordered=True)

    # The list is a real work plan, not an opaque blob.
    assert any(step.startswith('pdschecksums --initialize') for step in steps), steps
    assert any(step.startswith('pdsinfoshelf --initialize') for step in steps), steps
    assert any(step.startswith('pdsarchives --initialize') for step in steps), steps
    assert any(step.startswith('pdslinkshelf --initialize') for step in steps), steps
    assert any(step.startswith('pdsindexshelf --initialize') for step in steps), steps

    # Every step whose position the tool determines is pinned in exact order, so a
    # rule reordering its messages -- or the rules themselves being reordered --
    # still fails here even though the golden is compared unordered.
    ordered = rule_ordered_steps(steps)
    assert ordered == rule_ordered_steps(support.golden_lines('pds3_dependency_steps')), \
        '\n'.join(ordered)
    assert len(ordered) == 12, ordered

    # Spelled out for the two relationships that matter most: an archive is built
    # before the checksums of that archive, and a target's checksums before its
    # info shelf.
    for target in (VOLUME_DIR, METADATA_DIR):
        archives = ordered.index(f'pdsarchives --initialize $DISK/holdings/{target}')
        category = target.partition('/')[0]
        archive_sums = ordered.index(
            f'pdschecksums --initialize $DISK/holdings/archives-{category}/'
            f'{subsets.PDS3_VOLSET}')
        assert archives < archive_sums, ordered
        checksums = ordered.index(f'pdschecksums --initialize $DISK/holdings/{target}')
        infoshelf = ordered.index(f'pdsinfoshelf --initialize $DISK/holdings/{target}')
        assert checksums < infoshelf, ordered

    # Every step names a path inside the temporary tree; none leaks a real root.
    for step in steps:
        assert '$DISK' in step, step

    # The errors that motivated the steps name the specific missing products.
    assert any('Missing file' in line and 'checksums-metadata' in line
               for line in run.error_lines), run.describe()


def test_metadata_steps_disappear_once_performed(fresh_tree):
    """Running the metadata checksum and info steps removes them from the report."""

    before = steps_required(
        support.run_tool(fresh_tree, 'pdsdependency', fresh_tree.path(VOLUME_DIR)),
        fresh_tree)
    assert any('pdschecksums --initialize' in step and 'metadata' in step
               for step in before), before

    for tool in ('pdschecksums', 'pdsinfoshelf'):
        run = support.run_tool(fresh_tree, tool, '--initialize',
                               fresh_tree.path(METADATA_DIR))
        assert run.returncode == 0, run.describe()

    after = steps_required(
        support.run_tool(fresh_tree, 'pdsdependency', fresh_tree.path(VOLUME_DIR)),
        fresh_tree)

    assert not any('pdschecksums --initialize' in step and step.endswith(
        f'metadata/{subsets.PDS3_VOLSET}/{subsets.PDS3_VOLUME}') for step in after), after
    assert not any('pdsinfoshelf --initialize' in step and step.endswith(
        f'metadata/{subsets.PDS3_VOLSET}/{subsets.PDS3_VOLUME}') for step in after), after
    assert len(after) < len(before), (before, after)


def test_a_missing_volume_is_refused(fresh_tree):
    """A path that does not exist is refused before any dependency work starts."""

    run = support.run_tool(fresh_tree, 'pdsdependency',
                           fresh_tree.path('volumes/HSTNx_xxxx/HSTN0_0000'))
    assert run.returncode == 1, run.describe()
    assert 'No such file or directory' in run.output, run.describe()
