##########################################################################################
# tests/holdings_maintenance/test_shelf_common.py
#
# The pieces of the shared maintenance-tool core that a tool runs on, tested
# directly rather than through a tool: the modification-time comparison, the pair
# of log-path method names the driver picks between, and the task names the four
# migrated tools carry.
#
# Holdings-free and in-process; nothing here touches a holdings tree.
##########################################################################################

import datetime
import inspect

import pdslogger
import pytest

import pdsfile
from pdsfile.holdings_maintenance import _indexshelf_common, _linkshelf_common, _shelf_common
from pdsfile.holdings_maintenance.pds3 import pdsindexshelf, pdslinkshelf
from pdsfile.holdings_maintenance.pds4 import pds4indexshelf, pds4linkshelf

pytestmark = pytest.mark.holdings_free

# The format generate_infodict() writes and validate_infodict() reads back.
FORMAT = '%Y-%m-%d %H:%M:%S.%f'


def stamp(seconds):
    """Render a POSIX time the way the info shelf records it."""

    return datetime.datetime.fromtimestamp(seconds,
                                           tz=datetime.UTC).strftime(FORMAT)


def test_the_recorded_format_parses():
    """fromisoformat() reads the space-separated stamp the tools write.

    The separator is a space, not a 'T'. Python accepts an arbitrary separator
    character in that position, but the tools depend on it, so it is pinned.
    """

    text = stamp(1600000000.5)
    assert ' ' in text
    assert 'T' not in text
    assert datetime.datetime.fromisoformat(text).microsecond == 500000


@pytest.mark.parametrize(('delta', 'agree'), [
    (0.0, True),
    (0.5, True),
    (0.999999, True),
    (1.0, False),
    (1.000001, False),
    (2.0, False),
    (-0.999999, True),     # and symmetric
    (-1.0, False),
    (-2.0, False),
])
def test_tolerance(delta, agree):
    """Times agree when they are less than MODTIME_TOLERANCE seconds apart."""

    assert _shelf_common.MODTIME_TOLERANCE == 1
    base = 1600000000.25
    assert _shelf_common.modtimes_agree(stamp(base), stamp(base + delta)) is agree


def test_the_boundary_is_exclusive():
    """Exactly one second apart is a difference; a microsecond less is not.

    Pinned in both directions and outside the table above, because it is the one
    value where a reader could reasonably expect either answer, and because it is a
    deliberate departure from validate_tuples(), which allows a full second
    inclusively. The operands are what differ: validate_tuples() compares a
    tarfile's whole-second time against a filesystem time, where up to a second of
    slack is unavoidable, while both times here come from one generator at
    microsecond precision, so only a sub-second discrepancy is noise. On a
    filesystem storing whole seconds a one-second change is the smallest real change
    there is, and reporting it is the point of the comparison.
    """

    base = 1600000000.25
    assert _shelf_common.modtimes_agree(stamp(base), stamp(base + 0.999999))
    assert not _shelf_common.modtimes_agree(stamp(base), stamp(base + 1.0))
    assert not _shelf_common.modtimes_agree(stamp(base + 1.0), stamp(base))

    # A whole-second shift of a whole-second time, which is the case a coarse
    # filesystem actually produces.
    whole = 1600000000.0
    assert not _shelf_common.modtimes_agree(stamp(whole), stamp(whole + 1.0))


def test_a_boundary_straddle_is_not_a_mismatch():
    """Two times either side of a whole second, but close, are the same time.

    This is the case that separates a tolerance from a truncation. Truncating to
    the second calls these two different because they fall in different seconds;
    the tolerance calls them the same because they are two microseconds apart.
    """

    before = '2020-09-13 12:26:40.999999'
    after = '2020-09-13 12:26:41.000001'
    assert before.rpartition('.')[0] != after.rpartition('.')[0]
    assert _shelf_common.modtimes_agree(before, after)


def test_nine_tenths_of_a_second_agrees_wherever_it_falls():
    """Times 0.9 s apart agree whether or not they share a second.

    Truncation cannot promise that: it agrees or not depending on where the second
    boundary happens to fall between them.
    """

    assert _shelf_common.modtimes_agree('2020-09-13 12:26:40.001',
                                        '2020-09-13 12:26:40.901')
    assert _shelf_common.modtimes_agree('2020-09-13 12:26:40.500',
                                        '2020-09-13 12:26:41.400')


def test_every_reported_mismatch_renders_two_different_seconds():
    """A mismatch can always be reported to the second without looking absurd.

    If two times are more than a second apart they cannot share a whole second, so
    the message never prints the same string twice. That is what lets the report
    keep its original, second-resolution wording.
    """

    base = 1600000000.0
    for offset in (0.0, 0.01, 0.25, 0.5, 0.75, 0.99):
        for delta in (1.0, 1.0001, 1.5, 2.0, 60.0, 100.0):
            one, two = stamp(base + offset), stamp(base + offset + delta)
            assert not _shelf_common.modtimes_agree(one, two)
            assert one.rpartition('.')[0] != two.rpartition('.')[0], (one, two)


def test_the_empty_directory_sentinel():
    """An empty directory records '', which is not a time and compares as a string."""

    assert _shelf_common.modtimes_agree('', '')
    assert not _shelf_common.modtimes_agree('', '2020-09-13 12:26:40.000000')
    assert not _shelf_common.modtimes_agree('2020-09-13 12:26:40.000000', '')


def test_the_two_log_path_methods_exist_on_both_flavors():
    """Both PdsFile classes answer to the pair of names the driver picks between.

    The PDS3 tools used to name log_path_for_volume and log_path_for_volset. Those
    are aliases defined on Pds3File, so the driver reaches the same code through
    the bundle names for both flavors.
    """

    for cls in (pdsfile.Pds3File, pdsfile.Pds4File):
        assert callable(getattr(cls, _shelf_common.UNIT_LOG_PATH_METHOD))
        assert callable(getattr(cls, _shelf_common.UNITSET_LOG_PATH_METHOD))


class RecordingPdsFile(pdsfile.Pds3File):
    """A Pds3File that records what its log-path methods ask _log_path_for for.

    Both the keyword arguments and the path parts are recorded. The parts are the
    half that distinguishes a bundle log path from a bundle set one, so a test
    that compared only the keywords would pass even if the two were swapped.
    """

    category_ = 'volumes/'
    bundleset_ = 'HSTNx_xxxx/'
    bundleset = 'HSTNx_xxxx'
    bundlename = 'HSTN0_7176'
    suffix = ''

    def __init__(self):     # deliberately not super(): no tree is needed
        self.calls = []

    def _log_path_for(self, parts, **kwargs):
        self.calls.append((parts(), kwargs))
        return 'built'


def test_the_pds3_log_path_aliases_agree_with_the_bundle_names():
    """Pds3File's volume/volset log paths are the bundle/bundleset ones.

    Pinned because the driver stopped calling the volume names when these tools
    moved onto it; if the aliases ever diverged, every PDS3 log would move. The
    two are compared by everything they hand to _log_path_for -- the path parts as
    well as the keywords -- so no tree is needed.
    """

    pdsf = RecordingPdsFile()
    pdsf.log_path_for_volume('_info', task='validate', dir='pdsinfoshelf')
    pdsf.log_path_for_bundle('_info', task='validate', dir='pdsinfoshelf')
    assert pdsf.calls[0] == pdsf.calls[1]

    pdsf = RecordingPdsFile()
    pdsf.log_path_for_volset('_md5', 'update', 'pdschecksums')
    pdsf.log_path_for_bundleset('_md5', task='update', dir='pdschecksums')
    assert pdsf.calls[0] == pdsf.calls[1]

    # And the two kinds are genuinely different, so the assertions above are not
    # comparing one thing with itself.
    pdsf = RecordingPdsFile()
    pdsf.log_path_for_bundle('_md5', task='update', dir='pdschecksums')
    pdsf.log_path_for_bundleset('_md5', task='update', dir='pdschecksums')
    assert pdsf.calls[0] != pdsf.calls[1]


##########################################################################################
# The task names the migrated tools carry
##########################################################################################

# The four tools whose tasks live in a family module, with that module and its
# prefix for a task name: _indexshelf_common.index_validate,
# _linkshelf_common.link_validate.
MIGRATED_TOOLS = [
    pytest.param(pdsindexshelf, _indexshelf_common, 'index_', id='pdsindexshelf'),
    pytest.param(pds4indexshelf, _indexshelf_common, 'index_', id='pds4indexshelf'),
    pytest.param(pdslinkshelf, _linkshelf_common, 'link_', id='pdslinkshelf'),
    pytest.param(pds4linkshelf, _linkshelf_common, 'link_', id='pds4linkshelf'),
]

# The same four, for the test that needs only the tool.
MIGRATED_TOOL_MODULES = [pytest.param(case.values[0], id=case.id)
                         for case in MIGRATED_TOOLS]

TASK_NAMES = ('initialize', 'reinitialize', 'validate', 'repair', 'update')


@pytest.mark.parametrize('tool', MIGRATED_TOOL_MODULES)
def test_each_migrated_tool_still_carries_its_five_task_names(tool):
    """A tool module is a library as well as a main program.

    re_validate reaches pdslinkshelf.validate() by attribute, and nothing else in
    the suite would notice one of these names disappearing: the tool tests drive
    each tool as a subprocess through main(), which reads the task table rather
    than the module namespace.
    """

    for name in TASK_NAMES:
        task = getattr(tool, name, None)
        assert callable(task), f'{tool.__name__} does not carry {name}'
        assert task is tool.TASKS[name], f'{tool.__name__}.{name} is not its own task'
        # One target, plus the two keyword arguments a library caller passes.
        inspect.signature(task).bind('target', logger=None, limits={})


@pytest.mark.parametrize(('tool', 'family', 'prefix'), MIGRATED_TOOLS)
def test_each_migrated_tool_binds_its_own_spec_into_its_tasks(tool, family, prefix):
    """The task table is the family's functions with this tool's own spec bound in.

    Without the binding being the tool's own, the pds4 half of a pair could run
    against the pds3 half's PdsFile class and shelve the wrong tree.
    """

    for name in TASK_NAMES:
        task = tool.TASKS[name]
        assert task.args == (tool.SPEC,), f'{tool.__name__}.TASKS[{name!r}]'
        assert task.func is getattr(family, prefix + name), name

    assert tool.SPEC.pdsfile_cls is (pdsfile.Pds4File if tool.__name__.rpartition('.')[2]
                                     .startswith('pds4') else pdsfile.Pds3File)


##########################################################################################
# Reading a shelved link
##########################################################################################

class TestLinkTextOf:
    """The one accessor that lets an update merge a loaded shelf with a fresh scan.

    A link a run has just found is a LinkInfo; one read back from a shelf is the
    plain tuple that was pickled. generate_links() sees both in the same dictionary
    during an update and reads the text of each through this function.

    Tested here rather than through a tool because no scenario in the declared PDS4
    subset makes the value observable in what a tool writes: the loop that reads it
    only assigns a label when a *newly appeared* file's basename matches a link in
    an *already shelved* label, and every file a shelved label links to is itself
    already shelved. The tool tests pin that an update completes and agrees with a
    rebuild; this pins what the accessor returns.
    """

    def test_a_freshly_found_link_reads_as_its_link_text(self):
        info = _linkshelf_common.LinkInfo(233, 'ALPHA.TAB', True)
        assert _linkshelf_common.link_text_of(info) == 'ALPHA.TAB'

    def test_a_shelved_link_reads_as_its_link_text(self):
        # (recno, linktext, target), which is what write_linkdict pickles.
        assert _linkshelf_common.link_text_of((233, 'ALPHA.TAB', 'data/ALPHA.TAB')) \
            == 'ALPHA.TAB'

    def test_the_two_shapes_of_one_link_read_the_same(self):
        """The point of the accessor: the same link, either way round."""

        info = _linkshelf_common.LinkInfo(233, 'ALPHA.TAB', True)
        info.target = 'data/ALPHA.TAB'
        shelved = (info.recno, info.linktext, info.target)

        assert _linkshelf_common.link_text_of(info) \
            == _linkshelf_common.link_text_of(shelved)

    def test_repairing_a_link_does_not_change_what_is_read(self):
        """linkname is the repaired text; linktext is what the file actually said.

        generate_links() rewrites linkname when the REPAIRS table has an entry for a
        known-bad link, and leaves linktext alone. What gets pickled, and so what an
        update reads back, is linktext.
        """

        info = _linkshelf_common.LinkInfo(233, 'ALPHA.TAB', True)
        info.linkname = 'REPAIRED.TAB'

        assert _linkshelf_common.link_text_of(info) == 'ALPHA.TAB'


##########################################################################################
# What validate_links does with an exception
##########################################################################################

def test_validate_links_logs_and_reraises_an_exception_raised_inside_it(tmp_path,
                                                                       monkeypatch):
    """It logs and re-raises; it does not swallow.

    The pds3 flavor used to end `finally: return logger.close()`, and a `return` in
    a `finally` discards whatever the `except` clause re-raised — so a failure
    inside this function ended the run with status 0 and no traceback. The merged
    function takes the pds4 form, which propagates. Nothing in a real run reaches
    this branch, which is exactly why it needs a test rather than a scenario: the
    body only sorts and compares dictionaries, so the raise has to be arranged.

    Both halves are asserted. The `except` clause is the only thing that logs the
    exception, and the `finally` is the only thing that used to discard it, so a
    test that checked one and not the other would pass against half the function.
    """

    class Exploding(list):
        """A shelved value whose sort raises, which is where the try block can fail."""

        def sort(self, *args, **kwargs):
            raise RuntimeError('sorting a link list failed')

    spec = pdsindexshelf.SPEC     # any spec: only pdsfile_cls and logname are read
    monkeypatch.setattr(spec.pdsfile_cls, 'from_abspath',
                        classmethod(lambda cls, path: _StubPdsdir()))

    logfile = tmp_path / 'run.log'
    logger = pdslogger.PdsLogger('pds.test.' + tmp_path.name)
    logger.add_handler(pdslogger.file_handler(str(logfile)))

    key = str(tmp_path / 'A.LBL')
    with pytest.raises(RuntimeError, match='sorting a link list failed'):
        _linkshelf_common.validate_links(spec, str(tmp_path),
                                         {key: Exploding()}, {key: Exploding()},
                                         logger=logger)

    assert 'sorting a link list failed' in logfile.read_text()


class _StubPdsdir:
    """Just enough of a PdsFile for validate_links: a root to log relative to."""

    root_ = '/'
