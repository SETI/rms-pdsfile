##########################################################################################
# tests/holdings_maintenance/test_shelf_common.py
#
# The pieces of _shelf_common.py that every checksum and shelf tool runs on, tested
# directly rather than through a tool: the modification-time comparison, and the
# pair of log-path method names the driver picks between.
#
# Holdings-free and in-process; nothing here touches a holdings tree.
##########################################################################################

import datetime

import pytest

import pdsfile
from pdsfile.holdings_maintenance import _shelf_common

pytestmark = pytest.mark.holdings_free

# The format generate_infodict() writes and validate_infodict() reads back.
FORMAT = '%Y-%m-%d %H:%M:%S.%f'


def stamp(seconds):
    """Render a POSIX time the way the info shelf records it."""

    return datetime.datetime.fromtimestamp(seconds,
                                           tz=datetime.timezone.utc).strftime(FORMAT)


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
    (1.0, True),           # the tolerance is inclusive
    (1.000001, False),
    (2.0, False),
    (-1.0, True),          # and symmetric
    (-2.0, False),
])
def test_tolerance(delta, agree):
    """Times agree when they are no more than MODTIME_TOLERANCE seconds apart."""

    assert _shelf_common.MODTIME_TOLERANCE == 1
    base = 1600000000.25
    assert _shelf_common.modtimes_agree(stamp(base), stamp(base + delta)) is agree


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


def test_a_whole_second_apart_inside_the_tolerance():
    """Times 0.9 s apart agree wherever they fall, which truncation cannot promise."""

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
    for offset in (0.01, 0.25, 0.5, 0.75, 0.99):
        for delta in (1.0001, 1.5, 2.0, 60.0, 100.0):
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
    """A Pds3File that records what its log-path methods ask _log_path_for for."""

    def __init__(self):     # deliberately not super(): no tree is needed
        self.calls = []

    def _log_path_for(self, parts, **kwargs):
        self.calls.append(kwargs)
        return 'built'


def test_the_pds3_log_path_aliases_agree_with_the_bundle_names():
    """Pds3File's volume/volset log paths are the bundle/bundleset ones.

    Pinned because the driver stopped calling the volume names when these tools
    moved onto it; if the aliases ever diverged, every PDS3 log would move. The
    two are compared by what they hand to _log_path_for, so no tree is needed.
    """

    pdsf = RecordingPdsFile()
    pdsf.log_path_for_volume('_info', task='validate', dir='pdsinfoshelf')
    pdsf.log_path_for_bundle('_info', task='validate', dir='pdsinfoshelf')
    assert pdsf.calls[0] == pdsf.calls[1]

    pdsf = RecordingPdsFile()
    pdsf.log_path_for_volset('_md5', 'update', 'pdschecksums')
    pdsf.log_path_for_bundleset('_md5', task='update', dir='pdschecksums')
    assert pdsf.calls[0] == pdsf.calls[1]
