##########################################################################################
# tests/core/test_pdsfile_caching.py
#
# Regression tests for two cache-maintenance defects in pdsfile.pdsfile.
#
#   * the html_path property evaluated self._recache instead of calling it, so the
#     filled value was never written back to the cache;
#   * get_permanent_values() called resume_caching() without the class argument it
#     takes, so the pause it opened could never be closed.
#
# The tests run against cache objects and PdsFile instances they build themselves and
# need no holdings tree. Nothing here touches the session's preloaded cache: the
# pds3_cache fixture swaps in a throwaway one first.
##########################################################################################

import pytest

from pdsfile import Pds3File
from tests.core.support import blank_pds3file

pytestmark = pytest.mark.holdings_free


##########################################################################################
# html_path
##########################################################################################
class TestHtmlPathCaching:

    def test_the_filled_value_is_written_back_to_the_cache(self, pds3_cache):
        pdsf = blank_pds3file('volumes/NOSUCH_0xxx/NOSUCH_0001')
        key = pdsf.logical_path.lower()
        pds3_cache.set(key, pdsf)
        pds3_cache.set_keys.clear()

        assert pdsf.html_path == '/holdings/volumes/NOSUCH_0xxx/NOSUCH_0001'

        assert pds3_cache.set_keys == [key]
        # What write-back means for a non-local cache: the object stored under the
        # key carries the filled field, so a later reader gets the value without
        # recomputing it.
        assert pds3_cache[key] is pdsf
        assert (pds3_cache[key]._html_path_filled ==
                '/holdings/volumes/NOSUCH_0xxx/NOSUCH_0001')

    def test_an_object_that_is_not_in_the_cache_is_not_added_to_it(self, pds3_cache):
        pdsf = blank_pds3file('volumes/NOSUCH_0xxx/NOSUCH_0002')

        assert pdsf.html_path == '/holdings/volumes/NOSUCH_0xxx/NOSUCH_0002'

        # _recache() only refreshes an entry that already exists. That is the bound
        # on the write-back: it can change what a cached key maps to, never which
        # keys the cache holds.
        assert pds3_cache.set_keys == []
        assert len(pds3_cache) == 0

    def test_the_second_read_is_served_from_the_filled_field(self, pds3_cache):
        pdsf = blank_pds3file('volumes/NOSUCH_0xxx/NOSUCH_0003')
        pds3_cache.set(pdsf.logical_path.lower(), pdsf)
        first = pdsf.html_path
        pds3_cache.set_keys.clear()

        assert pdsf.html_path == first
        assert pds3_cache.set_keys == []

    def test_html_path_is_derived_from_the_html_root_and_the_logical_path(self, pds3_cache):
        pdsf = blank_pds3file('volumes/NOSUCH_0xxx/NOSUCH_0004/DATA/FILE.IMG')

        assert (pdsf.html_path ==
                '/holdings/volumes/NOSUCH_0xxx/NOSUCH_0004/DATA/FILE.IMG')
        assert pdsf.url == pdsf.html_path
        assert pds3_cache.set_keys == []


##########################################################################################
# get_permanent_values
##########################################################################################
class _StubCategory:
    """A cached category or bundle-set entry with no children to walk into."""

    def __init__(self):
        self.childnames = []


class _StubMemcache:
    """Stand-in for the MemcachedCache get_permanent_values() is written against.

    A DictionaryCache has no permanent_values attribute, so this method only ever
    ran against memcached, which is why its resume_caching() call was never
    exercised by anything.
    """

    def __init__(self, missing_prefix=None):
        self.events = []
        self.keys_read = []
        self.permanent_values = {}
        self.missing_prefix = missing_prefix

    def pause(self):
        self.events.append('pause')

    def resume(self):
        self.events.append('resume')

    def __getitem__(self, key):
        self.keys_read.append(key)
        if self.missing_prefix is not None and key.startswith(self.missing_prefix):
            raise KeyError(key)
        return _StubCategory()


class TestGetPermanentValues:

    def test_caching_is_resumed_after_the_values_are_read(self, monkeypatch):
        stub = _StubMemcache()
        monkeypatch.setattr(Pds3File, 'CACHE', stub)

        assert Pds3File.get_permanent_values([], 0) is None

        assert stub.events == ['pause', 'resume']
        # The walk really ran: every category was read, not just the first one.
        for category in Pds3File.CATEGORY_LIST:
            assert '$RANKS-' + category + '/' in stub.keys_read
            assert '$VOLS-' + category + '/' in stub.keys_read
            assert category in stub.keys_read

    def test_caching_is_resumed_after_a_missing_value_triggers_a_reload(self, monkeypatch):
        stub = _StubMemcache(missing_prefix='$VOLS-')
        preloads = []
        monkeypatch.setattr(Pds3File, 'CACHE', stub)
        monkeypatch.setattr(
            Pds3File, 'preload',
            classmethod(lambda cls, *args, **kwargs: preloads.append((args, kwargs))))

        assert Pds3File.get_permanent_values(['/holdings'], 11211) is None

        assert preloads == [((['/holdings'], 11211), {'force_reload': True})]
        assert stub.events == ['pause', 'resume']

##########################################################################################
