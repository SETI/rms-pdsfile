##########################################################################################
# tests/core/test_log_path_timetag.py
#
# The time tag in a log file name, and the pin that gives one run's two log paths
# the same one.
#
# A log path is dated to the second. A tool writes one run's log in up to two places
# and builds the two paths with two calls, so two calls that straddle a second
# boundary would date the two copies of one log a second apart. The clock these
# tests install advances one second on every reading, which turns that rare race
# into the certain outcome; every test that asserts the pin holds is paired with an
# unpinned case in the same test, and the unpinned case is what proves the clock is
# being read where the assertion says it is.
#
# The tests build their own PdsFile objects and need no holdings tree.
##########################################################################################

import datetime
import re
from types import SimpleNamespace

import pytest

from pdsfile import Pds3File, Pds4File, _derived_paths
from pdsfile.holdings_maintenance import _common
from pdsfile.holdings_maintenance.pds3 import pdsarchives
from pdsfile.holdings_maintenance.pds4 import pds4archives
from pdsfile.pdsfile import PdsFile

pytestmark = pytest.mark.holdings_free

# The tag LOGFILE_TIME_FMT renders, wherever it appears in a path.
TIMETAG = re.compile(r'\d{4}-\d\d-\d\dT\d\d-\d\d-\d\d')

# The two archives tools, each with the PdsFile class its spec drives.
ARCHIVE_SPECS = [
    pytest.param(Pds3File, pdsarchives.SPEC, 'volumes/', id='pds3'),
    pytest.param(Pds4File, pds4archives.SPEC, 'bundles/', id='pds4'),
]


class TickingClock:
    """A now() that reads one second later every time it is asked."""

    def __init__(self, start):
        self.next_reading = start
        self.readings = []

    def now(self):
        reading = self.next_reading
        self.next_reading = reading + datetime.timedelta(seconds=1)
        self.readings.append(reading)
        return reading


@pytest.fixture
def ticking_clock(monkeypatch):
    """Make every reading of the clock land one second after the one before it."""

    clock = TickingClock(datetime.datetime(2026, 8, 5, 12, 0, 0))
    monkeypatch.setattr(_derived_paths, 'datetime', SimpleNamespace(datetime=clock))

    return clock


def blank_target(cls, category_, bundleset, bundlename):
    """Return a blank PdsFile carrying only the fields a log path is built from.

    The bundle set named here exists in no holdings tree, so the object can never be
    mistaken for a real one.
    """

    pdsf = cls()
    pdsf.disk_ = '/nonexistent-holdings/'
    pdsf.category_ = category_
    pdsf.bundleset_ = bundleset + '/'
    pdsf.bundleset = bundleset
    pdsf.bundlename = bundlename
    pdsf.basename = bundlename
    pdsf.logical_path = category_ + bundleset + '/' + bundlename
    pdsf.abspath = pdsf.disk_ + pdsf.logical_path

    return pdsf


def timetags_of(paths):
    """Return the set of time tags the given log paths carry."""

    return {TIMETAG.search(path).group() for path in paths}


##########################################################################################
# The pin on the mixin
##########################################################################################
class TestPinnedLogTimetag:

    def test_unpinned_calls_disagree_and_pinned_calls_agree(self, ticking_clock):
        """The control and the fix, measured on one object under one clock."""

        pdsf = blank_target(Pds3File, 'volumes/', 'XXXXX_xxxx', 'XXXXX_0001')

        unpinned = [pdsf.log_path_for_bundle('_md5', task='validate', dir='tool'),
                    pdsf.log_path_for_bundle('_md5', task='validate', dir='tool',
                                             place='parallel')]
        assert len(timetags_of(unpinned)) == 2

        with Pds3File._pinned_log_timetag():
            pinned = [pdsf.log_path_for_bundle('_md5', task='validate', dir='tool'),
                      pdsf.log_path_for_bundle('_md5', task='validate', dir='tool',
                                               place='parallel')]
        assert len(timetags_of(pinned)) == 1

        # The clock really was read five times: twice unpinned, once on the way into
        # the block, and not again for either path built inside it.
        assert len(ticking_clock.readings) == 3

    def test_the_pin_reaches_a_rule_subclass_of_the_pinned_class(self, ticking_clock):
        """Production targets are rule subclasses, and the pin is set on Pds3File."""

        subclass = Pds3File.SUBCLASSES['ASTROM_xxxx']
        pdsf = blank_target(subclass, 'volumes/', 'ASTROM_xxxx', 'ASTROM_0001')
        assert type(pdsf) is not Pds3File

        with Pds3File._pinned_log_timetag():
            paths = [pdsf.log_path_for_bundle('_links', task='repair', dir='tool'),
                     pdsf.log_path_for_bundle('_links', task='repair', dir='tool',
                                              place='parallel')]

        assert len(timetags_of(paths)) == 1

    def test_the_pin_is_released_on_the_way_out(self, ticking_clock):
        """Leaving the block puts the class back to dating each path from the clock."""

        pdsf = blank_target(Pds3File, 'volumes/', 'XXXXX_xxxx', 'XXXXX_0001')

        with Pds3File._pinned_log_timetag():
            inside = pdsf.log_path_for_bundle('_md5', task='validate', dir='tool')

        assert Pds3File._LOG_TIMETAG is None
        after = [pdsf.log_path_for_bundle('_md5', task='validate', dir='tool'),
                 pdsf.log_path_for_bundle('_md5', task='validate', dir='tool')]
        assert len(timetags_of(after) | timetags_of([inside])) == 3

    def test_the_pin_is_released_when_the_block_raises(self, ticking_clock):
        """A task that raises inside the block must not leave the tag pinned."""

        with pytest.raises(ValueError, match='the task failed'), \
                Pds3File._pinned_log_timetag():
            raise ValueError('the task failed')

        assert Pds3File._LOG_TIMETAG is None

    def test_nesting_restores_the_outer_tag(self, ticking_clock):
        """The pin saves and restores, rather than clearing on the way out."""

        pdsf = blank_target(Pds3File, 'volumes/', 'XXXXX_xxxx', 'XXXXX_0001')

        with Pds3File._pinned_log_timetag():
            outer_before = pdsf.log_path_for_bundle('_md5', task='validate', dir='tool')
            with Pds3File._pinned_log_timetag():
                inner = pdsf.log_path_for_bundle('_md5', task='validate', dir='tool')
            outer_after = pdsf.log_path_for_bundle('_md5', task='validate', dir='tool')

        assert timetags_of([outer_before]) == timetags_of([outer_after])
        assert timetags_of([inner]) != timetags_of([outer_before])

    def test_the_pin_leaves_the_class_dictionary_as_it_found_it(self, ticking_clock):
        """A class that inherits the default must not be left holding its own copy.

        Writing the restored value back unconditionally would leave a shadowing entry
        in the class dictionary, and a class carrying its own value stops seeing one
        set on a base class -- so a flavor that had been pinned once would quietly
        become immune to a pin taken above it.
        """

        assert '_LOG_TIMETAG' not in vars(Pds3File)

        with Pds3File._pinned_log_timetag():
            assert vars(Pds3File)['_LOG_TIMETAG'] is not None

        assert '_LOG_TIMETAG' not in vars(Pds3File)

        with pytest.raises(ValueError, match='the task failed'), \
                Pds3File._pinned_log_timetag():
            raise ValueError('the task failed')

        assert '_LOG_TIMETAG' not in vars(Pds3File)

    def test_a_flavor_pinned_once_still_sees_a_pin_taken_above_it(self, ticking_clock):
        """The consequence of the test above, measured on the paths themselves."""

        pdsf = blank_target(Pds3File, 'volumes/', 'XXXXX_xxxx', 'XXXXX_0001')

        with Pds3File._pinned_log_timetag():
            pass

        with PdsFile._pinned_log_timetag():
            paths = [pdsf.log_path_for_bundle('_md5', task='validate', dir='tool'),
                     pdsf.log_path_for_bundle('_md5', task='validate', dir='tool')]

        assert len(timetags_of(paths)) == 1
        assert PdsFile._LOG_TIMETAG is None

    def test_the_two_flavors_pin_independently(self, ticking_clock):
        """Pinning one class must not date the other class's paths."""

        pds3 = blank_target(Pds3File, 'volumes/', 'XXXXX_xxxx', 'XXXXX_0001')
        pds4 = blank_target(Pds4File, 'bundles/', 'xxxxx_yyyy', 'xxxxx_yyyy_0001')

        with Pds3File._pinned_log_timetag():
            held = [pds3.log_path_for_bundle('_md5', task='validate', dir='tool'),
                    pds3.log_path_for_bundle('_md5', task='validate', dir='tool')]
            free = [pds4.log_path_for_bundle('_md5', task='validate', dir='tool'),
                    pds4.log_path_for_bundle('_md5', task='validate', dir='tool')]

        assert len(timetags_of(held)) == 1
        assert len(timetags_of(free)) == 2
        assert Pds4File._LOG_TIMETAG is None


##########################################################################################
# The caller: the log paths one target's run writes
##########################################################################################
class TestLogPathsFor:
    """_common.log_paths_for is the one place in the tree that builds the pair.

    All eleven maintenance tools reach it -- the archives pair through `run_main`
    and the other ten directly -- so the pin, the ordering and the deduplication are
    decided once. It lives with the maintenance tools rather than with the core, but
    it is what makes the pin reach a real run, so the control belongs beside the
    pin's own.
    """

    @pytest.mark.parametrize(('cls', 'spec', 'category_'), ARCHIVE_SPECS)
    def test_the_two_places_are_two_paths_under_one_timetag(self, cls, spec, category_,
                                                            ticking_clock, monkeypatch):
        monkeypatch.setattr(cls, 'LOG_ROOT_', '/nonexistent-logroot/')
        pdsf = blank_target(cls, category_, 'XXXXX_xxxx', 'XXXXX_0001')

        build = getattr(pdsf, spec.log_path_method)
        unpinned = [build(spec.log_suffix, task='validate', dir=spec.progname),
                    build(spec.log_suffix, task='validate', dir=spec.progname,
                          place='parallel')]
        assert len(timetags_of(unpinned)) == 2

        paths = _common.log_paths_for(pdsf, spec.log_path_method, spec.log_suffix,
                                      task='validate', dir=spec.progname)
        assert len(paths) == 2
        assert len(timetags_of(paths)) == 1

    @pytest.mark.parametrize(('cls', 'spec', 'category_'), ARCHIVE_SPECS)
    def test_the_two_places_collapse_to_one_path_with_no_log_root(self, cls, spec,
                                                                  category_,
                                                                  ticking_clock,
                                                                  monkeypatch):
        """With no log root the two places name one file, and the pin is what lets
        the duplicate be recognized as one."""

        monkeypatch.setattr(cls, 'LOG_ROOT_', None)
        pdsf = blank_target(cls, category_, 'XXXXX_xxxx', 'XXXXX_0001')

        build = getattr(pdsf, spec.log_path_method)
        unpinned = [build(spec.log_suffix, task='validate', dir=spec.progname),
                    build(spec.log_suffix, task='validate', dir=spec.progname,
                          place='parallel')]
        assert unpinned[0] != unpinned[1]

        assert len(_common.log_paths_for(pdsf, spec.log_path_method, spec.log_suffix,
                                         task='validate', dir=spec.progname)) == 1

    def test_the_default_place_comes_first(self, ticking_clock, monkeypatch):
        """The result is ordered, not a set, so the two `Log file:` lines and the two
        versioned copies come out in the same order on every run."""

        monkeypatch.setattr(Pds3File, 'LOG_ROOT_', '/nonexistent-logroot/')
        pdsf = blank_target(Pds3File, 'volumes/', 'XXXXX_xxxx', 'XXXXX_0001')

        paths = _common.log_paths_for(pdsf, 'log_path_for_volume', '_md5',
                                      task='validate', dir='tool')

        assert isinstance(paths, list)
        assert paths[0].startswith('/nonexistent-logroot/')     # the configured root
        assert paths[1].startswith('/nonexistent-holdings/')    # parallel to holdings


class TestTheIndexshelfDedupe:
    """The indexshelf pair deduplicates its pair explicitly, and the race defeated it.

    `pdsindexshelf` and `pds4indexshelf` were the only two tools that built a list
    and then dropped the second entry when it equalled the first. That equality test
    compares two strings each carrying its own reading of a one-second clock, so on a
    straddling second it was False when it should have been True and the tool wrote
    one run's log twice, into one directory, under two names. Both now call
    log_paths_for, which reads the clock once and then compares.
    """

    def index_target(self, cls, logical_path):
        pdsf = cls()
        pdsf.disk_ = '/nonexistent-holdings/'
        pdsf.logical_path = logical_path
        pdsf.abspath = pdsf.disk_ + logical_path
        pdsf.basename = logical_path.rpartition('/')[2]
        pdsf._is_index = True

        return pdsf

    @pytest.mark.parametrize(('cls', 'logical_path'), [
        pytest.param(Pds3File, 'metadata/XXXXX_xxxx/XXXXX_0001/XXXXX_0001_index.tab',
                     id='pds3'),
        pytest.param(Pds4File, 'metadata/xxxxx_yyyy/xxxxx_yyyy_index.csv', id='pds4'),
    ])
    def test_one_log_file_with_no_log_root(self, cls, logical_path, ticking_clock,
                                           monkeypatch):
        monkeypatch.setattr(cls, 'LOG_ROOT_', None)
        pdsf = self.index_target(cls, logical_path)

        # The control: built the way the tool used to, under the same clock, the two
        # paths differ and the tool's `logfiles[0] == logfiles[1]` test fails to fire.
        unpinned = [pdsf.log_path_for_index(task='validate', dir='pdsindexshelf'),
                    pdsf.log_path_for_index(task='validate', dir='pdsindexshelf',
                                            place='parallel')]
        assert unpinned[0] != unpinned[1]

        paths = _common.log_paths_for(pdsf, 'log_path_for_index', task='validate',
                                      dir='pdsindexshelf')
        assert len(paths) == 1

    @pytest.mark.parametrize(('cls', 'logical_path'), [
        pytest.param(Pds3File, 'metadata/XXXXX_xxxx/XXXXX_0001/XXXXX_0001_index.tab',
                     id='pds3'),
        pytest.param(Pds4File, 'metadata/xxxxx_yyyy/xxxxx_yyyy_index.csv', id='pds4'),
    ])
    def test_two_log_files_under_one_timetag_with_a_log_root(self, cls, logical_path,
                                                             ticking_clock, monkeypatch):
        monkeypatch.setattr(cls, 'LOG_ROOT_', '/nonexistent-logroot/')
        pdsf = self.index_target(cls, logical_path)

        paths = _common.log_paths_for(pdsf, 'log_path_for_index', task='validate',
                                      dir='pdsindexshelf')
        assert len(paths) == 2
        assert len(timetags_of(paths)) == 1

##########################################################################################
