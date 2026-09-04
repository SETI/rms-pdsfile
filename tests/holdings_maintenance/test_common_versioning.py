##########################################################################################
# tests/holdings_maintenance/test_common_versioning.py
#
# The one copy of the versioning step the checksum and shelf tools share.
#
# _shelf_common.move_old() copies the file a task is about to replace into every directory
# the run is logging into, numbering it <name>_v###<ext> one past the highest already
# there, carrying the kind's companion files along, and logging two lines saying so.
# What differs between a checksum file, an info shelf and a link shelf is a
# VersionedFile record -- a noun and a tuple of companion extensions -- and nothing
# else: there is one function body.
#
# Both log lines pass the path as PdsLogger's second argument, so the colon and the
# logger's root replacement come from one mechanism rather than being baked into one
# message and absent from another. Both pass force=True, so a limits dict that caps
# `info` cannot drop the report of a change already made to the filesystem.
#
# The tests build their own files and need no holdings tree.
##########################################################################################

import pdslogger
import pytest

from pdsfile.holdings_maintenance import _common, _shelf_common
from pdsfile.holdings_maintenance.pds3 import pdschecksums, pdsinfoshelf, pdslinkshelf
from pdsfile.holdings_maintenance.pds4 import pds4checksums, pds4infoshelf, pds4linkshelf

pytestmark = pytest.mark.holdings_free

# Each kind, with a file to version, the extra files that have to sit beside it, and
# the extensions it leaves in the log directory. LINK_SHELF lists '.pickle' as a
# companion and the shelf file *is* the `.pickle`, so that one is copied twice to the
# one destination; its versioned extensions are still `.pickle` and `.py`.
KINDS = [
    pytest.param(_shelf_common.CHECKSUM_FILE, 'CHECK_0001_md5.txt', (), ('.txt',),
                 id='checksums'),
    pytest.param(_shelf_common.INFO_SHELF, 'SHELF_0001_info.pickle', ('.py',),
                 ('.pickle', '.py'), id='info'),
    pytest.param(_shelf_common.LINK_SHELF, 'SHELF_0001_links.pickle', ('.py',),
                 ('.pickle', '.py'), id='links'),
]

# The names each of the six tools used to define its own copy of.
MOVED_OUT_OF_THE_TOOLS = ('LOGDIRS', 'hashfile', 'move_old', 'move_old_checksums',
                          'move_old_info', 'move_old_links')

TOOL_MODULES = [pdschecksums, pdsinfoshelf, pdslinkshelf,
                pds4checksums, pds4infoshelf, pds4linkshelf]


def build_target(directory, basename, extra_exts):
    """Write the file to be versioned, plus the extra files its kind expects."""

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


def version_once(kind, basename, extra_exts, tmp_path, monkeypatch, *,
                 limits=None, root=None):
    """Version one file, with the run's log directory recorded, and return the log."""

    holdings = tmp_path / 'holdings'
    holdings.mkdir()
    logdir = tmp_path / 'logs'
    logdir.mkdir()
    monkeypatch.setattr(_common, 'LOGDIRS', [str(logdir)])

    target = build_target(holdings, basename, extra_exts)
    logger, logfile = capture(tmp_path)
    if root:
        logger.replace_root(root)

    logger.open('task', limits=limits or {})
    _shelf_common.move_old(str(target), kind, logger=logger)
    logger.close()

    return logfile.read_text(), logdir, target


##########################################################################################
# One function, one copy
##########################################################################################
@pytest.mark.parametrize('module', TOOL_MODULES)
@pytest.mark.parametrize('name', MOVED_OUT_OF_THE_TOOLS)
def test_the_tool_modules_define_no_copy_of_their_own(module, name):
    """Each of these was defined in all six tools; the shared module holds the copy."""

    assert name not in vars(module), f'{module.__name__} redefines {name}'


def test_the_three_kinds_share_one_function():
    """The per-kind functions are gone; what is left is data."""

    for gone in ('move_old_checksums', 'move_old_info', 'move_old_links'):
        assert not hasattr(_shelf_common, gone), f'{gone} came back'

    assert _shelf_common.CHECKSUM_FILE.noun == 'Checksum file'
    assert _shelf_common.INFO_SHELF.noun == 'Info shelf file'
    assert _shelf_common.LINK_SHELF.noun == 'Link shelf file'
    assert _shelf_common.CHECKSUM_FILE.companions == ()
    assert _shelf_common.INFO_SHELF.companions == ('.py',)
    assert _shelf_common.LINK_SHELF.companions == ('.py', '.pickle')


##########################################################################################
# What the versioning does
##########################################################################################
@pytest.mark.parametrize(('kind', 'basename', 'extra_exts', 'versioned_exts'), KINDS)
def test_each_call_versions_one_past_the_highest_already_there(kind, basename,
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
        _shelf_common.move_old(str(target), kind, logger=logger)
        for ext in versioned_exts:
            assert (logdir / f'{stem}_{version}{ext}').exists()

    assert (logdir / f'{stem}_v001{versioned_exts[0]}').read_bytes() \
        == target.read_bytes()

    # The original is copied, not moved: the task that called this then rewrites it.
    assert target.exists()

    # Nothing beyond the three versions of each extension.
    assert len(list(logdir.iterdir())) == 3 * len(versioned_exts)


@pytest.mark.parametrize(('kind', 'basename', 'extra_exts', 'versioned_exts'), KINDS)
def test_a_file_that_does_not_exist_is_not_versioned(kind, basename, extra_exts,
                                                     versioned_exts, tmp_path,
                                                     monkeypatch):
    """The guard every caller already duplicates, kept so move_old is safe alone.

    Every in-tree call site checks first -- the checksum tasks return earlier when
    the file is absent, and the three shelf tools wrap the call in
    `if os.path.exists(...)` -- so nothing reaches this branch today. It is here so
    that a caller which forgets gets a no-op rather than a FileNotFoundError out of
    shutil.copy, and this test is what keeps it from being deleted as dead.
    """

    logdir = tmp_path / 'logs'
    logdir.mkdir()
    monkeypatch.setattr(_common, 'LOGDIRS', [str(logdir)])
    logger, logfile = capture(tmp_path)

    logger.open('task')
    _shelf_common.move_old(str(tmp_path / 'holdings' / basename), kind, logger=logger)
    logger.close()

    assert list(logdir.iterdir()) == []
    assert 'moved' not in logfile.read_text()


@pytest.mark.parametrize(('kind', 'basename', 'extra_exts', 'versioned_exts'), KINDS)
def test_nothing_is_versioned_when_no_log_directory_is_recorded(kind, basename,
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
    _shelf_common.move_old(str(target), kind, logger=logger)
    logger.close()

    assert 'moved' not in logfile.read_text()


##########################################################################################
# The two log lines
##########################################################################################
class TestTheTwoLogLines:
    """Both lines are `logger.info(noun + ' moved ...', path, force=True)`.

    That shape is what renders the colon, what subjects the path to the logger's
    root replacement, and what keeps a limits cap from dropping the line. Before the
    three kinds were merged the link shelf wrote its "moved to" line as a plain
    concatenation, which rendered without the colon, and all three baked the colon
    into the "moved from" message instead of letting PdsLogger render it.
    """

    @pytest.mark.parametrize(('kind', 'basename', 'extra_exts', 'versioned_exts'),
                             KINDS)
    def test_both_lines_render_the_colon(self, kind, basename, extra_exts,
                                         versioned_exts, tmp_path, monkeypatch):
        text, _logdir, _target = version_once(kind, basename, extra_exts,
                                              tmp_path, monkeypatch)

        assert kind.noun + ' moved from: ' in text
        assert kind.noun + ' moved to: ' in text

        # And nothing renders the colon-less form the link shelf used to write.
        assert kind.noun + ' moved to /' not in text

    @pytest.mark.parametrize(('kind', 'basename', 'extra_exts', 'versioned_exts'),
                             KINDS)
    def test_the_root_replacement_reaches_the_source_path(self, kind, basename,
                                                          extra_exts, versioned_exts,
                                                          tmp_path, monkeypatch):
        """Passing the path as the second argument is what subjects it to the root.

        The destination is under the log tree, so a holdings root never trims it;
        the source is under that root, so it is reported relative to it.
        """

        root = str(tmp_path / 'holdings') + '/'
        text, logdir, _target = version_once(kind, basename, extra_exts,
                                             tmp_path, monkeypatch, root=root)

        assert kind.noun + ' moved from: ' + basename in text
        assert kind.noun + ' moved from: ' + root not in text
        assert kind.noun + ' moved to: ' + str(logdir) in text


class TestReportingUnderAnInfoCap:
    """force=True on both lines, for every kind.

    A scope that caps `info` at zero drops every unforced line, so a test that only
    asserted the lines were present could pass with the cap doing nothing. The
    control is an unforced line emitted in the same kind of scope.
    """

    @pytest.mark.parametrize(('kind', 'basename', 'extra_exts', 'versioned_exts'),
                             KINDS)
    def test_every_kind_still_reports(self, kind, basename, extra_exts,
                                      versioned_exts, tmp_path, monkeypatch):
        text, logdir, _target = version_once(kind, basename, extra_exts,
                                             tmp_path, monkeypatch,
                                             limits={'info': 0})

        assert (logdir / (basename.rpartition('.')[0] + '_v001'
                          + versioned_exts[0])).exists()
        assert kind.noun + ' moved from: ' in text
        assert kind.noun + ' moved to: ' in text

    def test_the_cap_really_drops_an_unforced_line(self, tmp_path, monkeypatch):
        """The control: the same scope, one unforced line, and it is gone."""

        logger, logfile = capture(tmp_path)
        logger.open('task', limits={'info': 0})
        logger.info('an unforced line', '/some/path')
        logger.info('a forced line', '/some/path', force=True)
        logger.close()

        text = logfile.read_text()
        assert 'an unforced line' not in text
        assert 'a forced line: /some/path' in text
        assert 'Additional INFO messages suppressed' in text

##########################################################################################
