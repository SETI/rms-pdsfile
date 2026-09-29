##########################################################################################
# tests/holdings_maintenance/test_tool_naming.py
#
# What each of the ten tools calls itself, and the suffix its log files carry.
#
# A spec's progname is read in five places and reaches three things a user sees: the
# --help description, the "Missing task" error, and the subdirectory of every log root.
# Every tool names itself, so a PDS3 run and a PDS4 run of one kind write into separate
# log directories rather than into one shared with the other flavor's. That is the pin
# here: the five PDS4 tools once carried their PDS3 twin's name in all three places.
#
# log_suffix is the other half of a log file's name. Each is the tool's own kind, and
# the two archive tools agree on '_archives'; the PDS3 one passed '_links' -- the link
# shelf tools' suffix -- and collided with nothing only because the prognames above
# separated the two directories.
#
# The tests read the specs and build a parser, and need no holdings tree.
##########################################################################################

import pytest

from pdsfile.holdings_maintenance import _common
from pdsfile.holdings_maintenance.pds3 import (
    pdsarchives,
    pdschecksums,
    pdsindexshelf,
    pdsinfoshelf,
    pdslinkshelf,
)
from pdsfile.holdings_maintenance.pds4 import (
    pds4archives,
    pds4checksums,
    pds4indexshelf,
    pds4infoshelf,
    pds4linkshelf,
)

pytestmark = pytest.mark.holdings_free

# Every tool, with the name it answers to and the suffix its log files carry. An
# index shelf log path takes no suffix argument, which an empty string is how a spec
# says.
TOOLS = [
    pytest.param(pdsarchives, 'pdsarchives', '_archives', id='pdsarchives'),
    pytest.param(pdschecksums, 'pdschecksums', '_md5', id='pdschecksums'),
    pytest.param(pdsindexshelf, 'pdsindexshelf', '', id='pdsindexshelf'),
    pytest.param(pdsinfoshelf, 'pdsinfoshelf', '_info', id='pdsinfoshelf'),
    pytest.param(pdslinkshelf, 'pdslinkshelf', '_links', id='pdslinkshelf'),
    pytest.param(pds4archives, 'pds4archives', '_archives', id='pds4archives'),
    pytest.param(pds4checksums, 'pds4checksums', '_md5', id='pds4checksums'),
    pytest.param(pds4indexshelf, 'pds4indexshelf', '', id='pds4indexshelf'),
    pytest.param(pds4infoshelf, 'pds4infoshelf', '_info', id='pds4infoshelf'),
    pytest.param(pds4linkshelf, 'pds4linkshelf', '_links', id='pds4linkshelf'),
]

# The two flavors of each kind, which are what a shared name would have collided in.
PAIRS = [
    pytest.param(pdsarchives, pds4archives, id='archives'),
    pytest.param(pdschecksums, pds4checksums, id='checksums'),
    pytest.param(pdsindexshelf, pds4indexshelf, id='indexshelf'),
    pytest.param(pdsinfoshelf, pds4infoshelf, id='infoshelf'),
    pytest.param(pdslinkshelf, pds4linkshelf, id='linkshelf'),
]


@pytest.mark.parametrize(('module', 'progname', 'log_suffix'), TOOLS)
def test_each_tool_names_itself(module, progname, log_suffix):
    """A spec's progname is its own module's name, and never its twin's."""

    assert module.SPEC.progname == progname
    assert module.__name__.rpartition('.')[2] == progname


@pytest.mark.parametrize(('module', 'progname', 'log_suffix'), TOOLS)
def test_the_help_description_opens_with_the_tools_own_name(module, progname,
                                                            log_suffix):
    """--help describes the tool the command line named.

    The description is the one place progname reaches that a --help run shows, and
    build_arg_parser() is where the substitution happens.
    """

    parser = _common.build_arg_parser(module.SPEC)

    assert parser.description.startswith(progname + ':')


@pytest.mark.parametrize(('module', 'progname', 'log_suffix'), TOOLS)
def test_each_tool_logs_under_its_own_suffix(module, progname, log_suffix):
    """The suffix in a log file's basename is the tool's own kind."""

    assert module.SPEC.log_suffix == log_suffix


@pytest.mark.parametrize(('pds3_module', 'pds4_module'), PAIRS)
def test_the_two_flavors_of_a_kind_log_into_separate_directories(pds3_module,
                                                                 pds4_module):
    """One kind's two tools disagree on progname, which is the log root subdirectory.

    They still share a logname, which is what stops the two from being driven from a
    single process, so a test that only compared the two specs field by field would
    pass on the shared value alone.
    """

    assert pds3_module.SPEC.progname != pds4_module.SPEC.progname
    assert pds3_module.SPEC.logname == pds4_module.SPEC.logname
