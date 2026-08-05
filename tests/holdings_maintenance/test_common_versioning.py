##########################################################################################
# tests/holdings_maintenance/test_common_versioning.py
#
# The one copy of the versioning step the checksum and shelf tools share.
#
# move_old_checksums, move_old_info and move_old_links each copy the file a task is
# about to replace into every directory the run is logging into, numbering it
# <name>_v###<ext> one past the highest already there, and log two lines saying so.
# The checksum copy passes force=True to both lines and the two shelf copies do not,
# so under a limits dict that caps `info` the checksum run still reports the
# versioning and a shelf run does not. That difference is what the two tests at the
# bottom measure against each other: the shelf case is the control that proves the
# cap is real, so the checksum case cannot pass by the cap being inert.
#
# The tests build their own files and need no holdings tree.
##########################################################################################

import pdslogger
import pytest

from pdsfile.holdings_maintenance import _common
from pdsfile.holdings_maintenance.pds3 import pdschecksums, pdsinfoshelf, pdslinkshelf
from pdsfile.holdings_maintenance.pds4 import pds4checksums, pds4infoshelf, pds4linkshelf

pytestmark = pytest.mark.holdings_free

# Each versioning function, with the file it versions, the extra files that have to
# sit beside it, and the extensions it leaves in the log directory. move_old_links
# copies the `.pickle` twice -- once as the shelf file and once as its own sidecar,
# to the same destination -- so its two versioned extensions are still `.pickle` and
# `.py`.
VERSIONED = [
    pytest.param(_common.move_old_checksums, 'CHECK_0001_md5.txt', (), ('.txt',),
                 id='checksums'),
    pytest.param(_common.move_old_info, 'SHELF_0001_info.pickle', ('.py',),
                 ('.pickle', '.py'), id='info'),
    pytest.param(_common.move_old_links, 'SHELF_0001_links.pickle', ('.py',),
                 ('.pickle', '.py'), id='links'),
]

# The two shelf movers, which do not force their log lines.
UNFORCED = [
    pytest.param(_common.move_old_info, 'SHELF_0001_info.pickle', ('.py',),
                 'Info shelf file', id='info'),
    pytest.param(_common.move_old_links, 'SHELF_0001_links.pickle', ('.py',),
                 'Link shelf file', id='links'),
]

# The names each of the six tools used to define its own copy of.
MOVED_OUT_OF_THE_TOOLS = ('LOGDIRS', 'hashfile',
                          'move_old_checksums', 'move_old_info', 'move_old_links')

TOOL_MODULES = [pdschecksums, pdsinfoshelf, pdslinkshelf,
                pds4checksums, pds4infoshelf, pds4linkshelf]


def build_target(directory, basename, extra_exts):
    """Write the file to be versioned, plus the extra files its mover expects."""

    target = directory / basename
    target.write_bytes(b'the superseded contents\n')

    stem = basename.rpartition('.')[0]
    for ext in extra_exts:
        (directory / (stem + ext)).write_bytes(b'beside it: ' + ext.encode())

    return target


def capture(tmp_path):
    """Return a logger writing into one file, and that file.

    pdslogger refuses a duplicate logger name within a process, so the name is
    taken from tmp_path, which pytest makes unique per test.
    """

    logfile = tmp_path / 'run.log'
    logger = pdslogger.PdsLogger('pds.test.' + tmp_path.name)
    logger.add_handler(pdslogger.file_handler(str(logfile)))

    return logger, logfile


def version_once(move_old, basename, extra_exts, tmp_path, monkeypatch, *, limits=None):
    """Version one file, with the run's log directory recorded, and return the log."""

    holdings = tmp_path / 'holdings'
    holdings.mkdir()
    logdir = tmp_path / 'logs'
    logdir.mkdir()
    monkeypatch.setattr(_common, 'LOGDIRS', [str(logdir)])

    target = build_target(holdings, basename, extra_exts)
    logger, logfile = capture(tmp_path)

    logger.open('task', limits=limits or {})
    move_old(str(target), logger=logger)
    logger.close()

    return logfile.read_text(), logdir, target


##########################################################################################
# One copy, in _common
##########################################################################################
@pytest.mark.parametrize('module', TOOL_MODULES)
@pytest.mark.parametrize('name', MOVED_OUT_OF_THE_TOOLS)
def test_the_tool_modules_define_no_copy_of_their_own(module, name):
    """Each of these was defined in all six tools; the shared module holds the copy."""

    assert name not in vars(module), f'{module.__name__} redefines {name}'
    assert hasattr(_common, name)


##########################################################################################
# What the versioning does
##########################################################################################
@pytest.mark.parametrize(('move_old', 'basename', 'extra_exts', 'versioned_exts'),
                         VERSIONED)
def test_each_call_versions_one_past_the_highest_already_there(move_old, basename,
                                                               extra_exts,
                                                               versioned_exts,
                                                               tmp_path, monkeypatch):
    holdings = tmp_path / 'holdings'
    holdings.mkdir()
    logdir = tmp_path / 'logs'
    logdir.mkdir()
    monkeypatch.setattr(_common, 'LOGDIRS', [str(logdir)])

    target = build_target(holdings, basename, extra_exts)
    logger, _logfile = capture(tmp_path)
    stem = basename.rpartition('.')[0]

    for version in ('v001', 'v002', 'v003'):
        move_old(str(target), logger=logger)
        for ext in versioned_exts:
            assert (logdir / f'{stem}_{version}{ext}').exists()

    assert (logdir / f'{stem}_v001{versioned_exts[0]}').read_bytes() \
        == target.read_bytes()

    # The original is copied, not moved: the task that called this then rewrites it.
    assert target.exists()

    # Nothing beyond the three versions of each extension.
    assert len(list(logdir.iterdir())) == 3 * len(versioned_exts)


@pytest.mark.parametrize(('move_old', 'basename', 'extra_exts', 'versioned_exts'),
                         VERSIONED)
def test_nothing_is_versioned_when_no_log_directory_is_recorded(move_old, basename,
                                                                extra_exts,
                                                                versioned_exts,
                                                                tmp_path, monkeypatch):
    """A process that never records its log directories versions nothing."""

    holdings = tmp_path / 'holdings'
    holdings.mkdir()
    monkeypatch.setattr(_common, 'LOGDIRS', [])

    target = build_target(holdings, basename, extra_exts)
    logger, logfile = capture(tmp_path)

    logger.open('task')
    move_old(str(target), logger=logger)
    logger.close()

    assert 'moved' not in logfile.read_text()


##########################################################################################
# force=True: which of the two lines survives a capped scope
##########################################################################################
class TestReportingUnderAnInfoCap:

    def test_the_checksum_move_still_reports(self, tmp_path, monkeypatch):
        """Both of its lines pass force=True, so the cap cannot drop them."""

        text, logdir, _target = version_once(_common.move_old_checksums,
                                             'CHECK_0001_md5.txt', (),
                                             tmp_path, monkeypatch,
                                             limits={'info': 0})

        assert (logdir / 'CHECK_0001_md5_v001.txt').exists()
        assert 'Checksum file moved from: ' in text
        assert 'Checksum file moved to: ' in text

    @pytest.mark.parametrize(('move_old', 'basename', 'extra_exts', 'noun'), UNFORCED)
    def test_a_shelf_move_is_silenced_by_the_same_cap(self, move_old, basename,
                                                      extra_exts, noun,
                                                      tmp_path, monkeypatch):
        """The control: the same cap, a mover that does not force, and the lines go.

        The file is still versioned, so what the cap drops is the report of a
        filesystem change that happened anyway.
        """

        text, logdir, _target = version_once(move_old, basename, extra_exts,
                                             tmp_path, monkeypatch,
                                             limits={'info': 0})

        stem = basename.rpartition('.')[0]
        assert (logdir / f'{stem}_v001.pickle').exists()
        assert noun + ' moved' not in text
        assert 'Additional INFO messages suppressed' in text

##########################################################################################
