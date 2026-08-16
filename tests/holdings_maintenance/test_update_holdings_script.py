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
#     removing "<category>/$VOLSET" as a directory removes nothing there.
#
# The tests parse the script's text and need no holdings tree. The parsing asserts
# what it extracted, so a rewrite of the script's shell idioms fails loudly here
# rather than letting three vacuous set comparisons pass.
##########################################################################################

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

# The categories whose products are one file per volume set at the category's top
# level rather than a directory per volume set.
FLAT_PREFIXES = ('checksums-archives-', '_infoshelf-archives-')

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
# rm -f "$HOLDINGS"/checksums-archives-metadata/${VOLSET}_* both match: the quote
# may close before or after the category, and the target may be the volume set's
# directory or a glob over files named for it.
_RM_REGEX = re.compile(r'^rm -r?f "\$HOLDINGS"?/([^/"]+)/([^"\s]+)"?$')

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
            deletions.append((match.group(1), match.group(2)))
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
    """A deletion under a flat category names the volume set's files.

    checksums-archives-metadata/ and _infoshelf-archives-metadata/ hold
    <volset>_metadata_md5.txt and <volset>_info.{pickle,py} at the category's top
    level, so the only deletion that removes anything is a glob over
    ${VOLSET}-prefixed file names; "<category>/$VOLSET" names a directory that
    never exists.
    """

    deletions, _ = parse_script()

    for category, target in deletions:
        if category.startswith(FLAT_PREFIXES):
            assert target.startswith('${VOLSET}_'), (
                f'{category} deletion targets {target}, which is not a '
                f'${{VOLSET}}-prefixed file glob')
        else:
            assert target == '$VOLSET', (
                f'{category} deletion targets {target} rather than the volume '
                f"set's directory")
