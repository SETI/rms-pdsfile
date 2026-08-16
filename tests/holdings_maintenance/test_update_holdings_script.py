##########################################################################################
# tests/holdings_maintenance/test_update_holdings_script.py
#
# The internal consistency of update_holdings_for_new_metadata.sh.
#
# The script deletes every derived product of one volume set's metadata and rebuilds
# them all with --initialize runs. That design carries three obligations the shell
# gives no help with, and each is a test here:
#
#   * every product it deletes must be rebuilt by one of its commands, and every
#     product it rebuilds must first have been deleted, because --initialize aborts
#     over a product that already exists;
#   * the rebuilds must run in an order that satisfies pdsdependency.py's rules --
#     an info shelf reads the checksum file it covers, and the archives' checksums
#     and info shelf read the archives themselves;
#   * a deletion under a flat category -- checksums-archives-metadata/ and
#     _infoshelf-archives-metadata/, which hold files named for the volume set
#     rather than a directory per volume set -- must target those files, because
#     removing "<category>/$VOLSET" as a directory removes nothing there;
#   * a flat-category deletion must remove exactly the files its rebuild writes,
#     because the versioned siblings sharing the directory -- <volset>_v1.0_... --
#     are derived from frozen versioned trees no command of the script rebuilds,
#     so a glob that reaches them destroys files the run cannot restore.
#
# The tests parse the script's text and need no holdings tree. The parsing asserts
# what it extracted, so a rewrite of the script's shell idioms fails loudly here
# rather than letting vacuous set comparisons pass.
##########################################################################################

import fnmatch
import re
from pathlib import Path

import pytest

from pdsfile.holdings_maintenance import pds3

pytestmark = pytest.mark.holdings_free

SCRIPT_PATH = Path(pds3.__file__).parent / 'update_holdings_for_new_metadata.sh'

# What each tool writes when aimed at a category: the product's category is the
# tool's own prefix put in front of the target's name, which is the naming rule
# the categories chapter of the user guide states and pdsdependency.py encodes.
TOOL_PREFIXES = {
    'pdsarchives': 'archives-',
    'pdschecksums': 'checksums-',
    'pdsinfoshelf': '_infoshelf-',
    'pdsindexshelf': '_indexshelf-',
    'pdslinkshelf': '_linkshelf-',
}

# The categories whose products are files named for the volume set at the
# category's top level rather than a directory per volume set, and the exact
# deletion target each requires: the one file (or file pair) that this run's
# rebuild writes for the unversioned volume set, and nothing wider. A versioned
# sibling's name -- <volset>_v1.0_metadata_md5.txt, <volset>_v1.0_info.pickle --
# matches neither target.
FLAT_CATEGORY_TARGETS = {
    'checksums-archives-metadata': '${VOLSET}_metadata_md5.txt',
    '_infoshelf-archives-metadata': '${VOLSET}_info.*',
}

# A directory listing for each flat category, modeled on the real holdings: the
# unversioned products the rebuild writes, versioned siblings, and a neighboring
# volume set whose name shares a prefix shape. Only the first group may be deleted.
SAMPLE_VOLSET = 'COISS_1xxx'
FLAT_CATEGORY_LISTINGS = {
    'checksums-archives-metadata': {
        'rebuilt': {'COISS_1xxx_metadata_md5.txt'},
        'bystanders': {'COISS_1xxx_v1.0_metadata_md5.txt',
                       'COISS_1xxx_v1.1_metadata_md5.txt',
                       'COISS_2xxx_metadata_md5.txt'},
    },
    '_infoshelf-archives-metadata': {
        'rebuilt': {'COISS_1xxx_info.pickle', 'COISS_1xxx_info.py'},
        'bystanders': {'COISS_1xxx_v1.0_info.pickle', 'COISS_1xxx_v1.0_info.py',
                       'COISS_2xxx_info.pickle'},
    },
}

# Every derived product of a metadata tree, which is what the script exists to
# rebuild. Dropping a deletion and its rebuild together would keep the sets equal,
# so the tests also compare against this list.
METADATA_PRODUCTS = {
    'archives-metadata',
    'checksums-archives-metadata',
    'checksums-metadata',
    '_indexshelf-metadata',
    '_infoshelf-archives-metadata',
    '_infoshelf-metadata',
    '_linkshelf-metadata',
}

# rm -rf "$HOLDINGS/archives-metadata/$VOLSET" and
# rm -f "$HOLDINGS/_infoshelf-archives-metadata/${VOLSET}_info".* both match: the
# quote may close before or after the target, and the target may be the volume
# set's directory, a file named for it, or a glob over such files. The parse is
# deliberately wider than the script's current quoting so that a reintroduced
# wide glob is parsed and then failed on its semantics rather than its shape.
_RM_REGEX = re.compile(r'^rm -r?f "\$HOLDINGS"?/([^/"]+)/([^"\s]+)"?(\.\*)?$')

_COMMAND_REGEX = re.compile(
    r'^python (pds\w+)\.py --initialize "\$HOLDINGS/([^/"]+)/\$VOLSET"$')


def parse_script():
    """Return (deletions, commands) parsed from the script's text.

    deletions is a list of (category, target) pairs, one per rm line, where target is
    what follows the category in the deleted path. commands is a list of
    (tool, target category) pairs, one per python line, in the script's order.
    """

    deletions = []
    commands = []
    for line in SCRIPT_PATH.read_text().splitlines():
        line = line.strip()
        if line.startswith('rm '):
            match = _RM_REGEX.match(line)
            assert match, f'unparsed rm line: {line}'
            deletions.append((match.group(1), match.group(2) + (match.group(3) or '')))
        elif line.startswith('python '):
            match = _COMMAND_REGEX.match(line)
            assert match, f'unparsed command line: {line}'
            assert match.group(1) in TOOL_PREFIXES, f'unknown tool: {line}'
            commands.append((match.group(1), match.group(2)))

    assert deletions, 'no rm lines parsed from the script'
    assert commands, 'no python lines parsed from the script'
    return deletions, commands


def products_in_order(commands):
    """Return the product category each command writes, in the script's order."""

    return [TOOL_PREFIXES[tool] + target for (tool, target) in commands]


def test_every_deleted_product_is_rebuilt_and_vice_versa():
    """The deletion list and the rebuild list both name every metadata product.

    A product deleted and not rebuilt is the failure pdsdependency.py would later
    report as a missing file; a product rebuilt without being deleted is an
    --initialize run that aborts over the survivor. Both sets are compared against
    the full product list rather than against each other alone, so removing a
    deletion and its rebuild together fails here too.
    """

    deletions, commands = parse_script()

    deleted = {category for (category, _) in deletions}
    rebuilt = set(products_in_order(commands))
    assert deleted == METADATA_PRODUCTS
    assert rebuilt == METADATA_PRODUCTS

    # Exactly one deletion and one rebuild per product: a duplicate --initialize
    # aborts at runtime over the product its twin just built, and a duplicate rm
    # would hide one from the set comparison above.
    assert len(deletions) == len(METADATA_PRODUCTS)
    assert len(commands) == len(METADATA_PRODUCTS)


def test_rebuild_order_satisfies_the_dependency_rules():
    """Each command's inputs are rebuilt before the command runs.

    Two kinds of input, both from pdsdependency.py's rule table: an info shelf
    reads the checksum file of the tree it covers, and a command aimed at a
    category the script deleted needs that category rebuilt first.
    """

    deletions, commands = parse_script()

    deleted = {category for (category, _) in deletions}
    products = products_in_order(commands)
    for position, (tool, target) in enumerate(commands):
        requirements = set()
        if tool == 'pdsinfoshelf':
            requirements.add('checksums-' + target)
        if target in deleted:
            requirements.add(target)

        for requirement in requirements:
            assert requirement in products[:position], (
                f'{tool} over {target} runs before {requirement} is rebuilt')


def test_flat_category_deletions_target_files_not_a_directory():
    """A deletion under a flat category names exactly its category's files.

    checksums-archives-metadata/ and _infoshelf-archives-metadata/ hold
    <volset>_metadata_md5.txt and <volset>_info.{pickle,py} at the category's top
    level, so the only deletion that removes anything names those files;
    "<category>/$VOLSET" names a directory that never exists. The targets are
    pinned exactly: a wider pattern would also reach the versioned siblings the
    test below protects, and a prefix check alone would accept it.
    """

    deletions, _ = parse_script()

    for category, target in deletions:
        if category in FLAT_CATEGORY_TARGETS:
            assert target == FLAT_CATEGORY_TARGETS[category], (
                f'{category} deletion targets {target} rather than '
                f'{FLAT_CATEGORY_TARGETS[category]}')
        else:
            assert target == '$VOLSET', (
                f'{category} deletion targets {target} rather than the volume '
                f"set's directory")


def test_flat_category_deletions_spare_what_the_run_cannot_rebuild():
    """Each flat-category deletion, expanded as a glob, removes exactly what the
    rebuild writes.

    The deletion targets are expanded the way the shell would -- ${VOLSET}
    substituted, then the pattern matched against a directory listing modeled on
    the real category contents -- and the matched set must equal the rebuilt set.
    In particular a versioned sibling such as <volset>_v1.0_metadata_md5.txt must
    survive: it is derived from a frozen versioned tree that no command of the
    script reads or rebuilds, so deleting it is a loss the run cannot repair.
    """

    deletions, _ = parse_script()
    targets = dict(deletions)

    for category, listing in FLAT_CATEGORY_LISTINGS.items():
        pattern = targets[category].replace('${VOLSET}', SAMPLE_VOLSET)
        assert '$' not in pattern, f'unsubstituted variable in {pattern}'

        names = listing['rebuilt'] | listing['bystanders']
        matched = {name for name in names if fnmatch.fnmatchcase(name, pattern)}
        assert matched == listing['rebuilt'], (
            f'{category} deletion {targets[category]} removes {sorted(matched)} '
            f'but the rebuild writes {sorted(listing["rebuilt"])}')
