##########################################################################################
# tests/core/test_pdscache_set_multi.py
#
# Regression tests for the two set_multi() implementations in pdsfile.pdscache.
#
# Neither method has a caller anywhere in this repository, so nothing in the suite
# reached them. Both were unconditionally broken for a non-empty dictionary:
# DictionaryCache.set_multi() forwarded a keyword its own set() does not accept, and
# MemcachedCache.set_multi() unpacked a dictionary's keys as if they were pairs.
#
# These tests build their own cache objects and need no holdings tree.
##########################################################################################

import pytest

from pdsfile import pdscache

pytestmark = pytest.mark.holdings_free


##########################################################################################
# DictionaryCache
##########################################################################################
class TestDictionaryCacheSetMulti:

    def test_every_key_is_stored(self):
        cache = pdscache.DictionaryCache(lifetime=0, limit=100)

        assert cache.set_multi({'a': 1, 'b': 2, 'c': 3}) == []

        assert cache['a'] == 1
        assert cache['b'] == 2
        assert cache['c'] == 3
        assert len(cache) == 3

    def test_an_explicit_lifetime_is_applied_to_every_key(self):
        cache = pdscache.DictionaryCache(lifetime=0, limit=100)

        cache.set_multi({'a': 1, 'b': 2}, lifetime=3600)

        # A non-zero lifetime gives each entry an expiration, which is what puts its
        # key into the trimmable set; lifetime=0 entries never expire and are not
        # tracked there.
        assert cache.keys == {'a', 'b'}
        assert cache.dict['a'][1] is not None
        assert cache.dict['b'][1] is not None

    def test_lifetime_zero_stores_entries_that_never_expire(self):
        cache = pdscache.DictionaryCache(lifetime=0, limit=100)

        cache.set_multi({'a': 1})

        assert cache.dict['a'][1] is None
        assert cache.keys == set()

    def test_the_pause_flag_is_accepted_and_still_stores_everything(self):
        cache = pdscache.DictionaryCache(lifetime=0, limit=100)

        assert cache.set_multi({'a': 1, 'b': 2}, pause=True) == []

        assert cache['a'] == 1
        assert cache['b'] == 2

    def test_an_empty_dictionary_is_a_no_op(self):
        cache = pdscache.DictionaryCache(lifetime=0, limit=100)

        assert cache.set_multi({}) == []

        assert len(cache) == 0


##########################################################################################
# MemcachedCache
##########################################################################################
class _StubMemcacheClient:
    """Stand-in for the pylibmc client held in MemcachedCache.mc.

    Only get_multi() is needed: it is the one client call set_multi() makes before
    it hands the values to set_local().
    """

    def __init__(self, contents):
        self.contents = dict(contents)
        self.get_multi_calls = []

    def get_multi(self, keys):
        keys = set(keys)
        self.get_multi_calls.append(keys)
        return {key: self.contents[key] for key in keys if key in self.contents}


def _detached_memcached_cache(mc):
    """Return a MemcachedCache that is not connected to a memcached server.

    MemcachedCache.__init__ opens a pylibmc connection and probes it, so the class
    cannot be instantiated in a test environment (pylibmc is not even a required
    dependency). The attributes assigned here are exactly the ones set_multi() and
    set_local() read. pauses=1 leaves is_paused True so the method never calls
    flush(), which is the only other path that would touch the client.
    """

    cache = pdscache.MemcachedCache.__new__(pdscache.MemcachedCache)
    cache.mc = mc
    cache.toobig_dict = {}
    cache.local_value_by_key = {}
    cache.local_lifetime_by_key = {}
    cache.local_keys_by_lifetime = {}
    cache.permanent_values = {}
    cache.pauses = 1
    cache.lifetime = 86400
    cache.lifetime_func = None
    cache.logger = None
    return cache


class TestMemcachedCacheSetMulti:

    def test_the_lifetime_recorded_in_memcache_is_preserved(self):
        # Keys long enough that unpacking one as a pair is an error rather than a
        # silent two-character split.
        key = 'volumes/coiss_2xxx/coiss_2001'
        mc = _StubMemcacheClient({key: ('previous value', 300)})
        cache = _detached_memcached_cache(mc)

        assert cache.set_multi({key: 'new value'}) == []

        assert mc.get_multi_calls == [{key}]
        assert cache.local_value_by_key[key] == 'new value'
        assert cache.local_lifetime_by_key[key] == 300
        assert cache.local_keys_by_lifetime[300] == [key]

    def test_an_explicit_lifetime_skips_the_memcache_lookup(self):
        key = 'volumes/coiss_2xxx/coiss_2002'
        mc = _StubMemcacheClient({key: ('previous value', 300)})
        cache = _detached_memcached_cache(mc)

        assert cache.set_multi({key: 'new value'}, lifetime=60) == []

        assert mc.get_multi_calls == []
        assert cache.local_value_by_key[key] == 'new value'
        assert cache.local_lifetime_by_key[key] == 60

    def test_keys_already_held_locally_are_not_looked_up_in_memcache(self):
        key = 'volumes/coiss_2xxx/coiss_2003'
        mc = _StubMemcacheClient({key: ('previous value', 300)})
        cache = _detached_memcached_cache(mc)
        cache.local_value_by_key[key] = 'previous value'
        cache.local_lifetime_by_key[key] = 120
        cache.local_keys_by_lifetime[120] = [key]

        assert cache.set_multi({key: 'new value'}) == []

        assert mc.get_multi_calls == []
        assert cache.local_value_by_key[key] == 'new value'
        assert cache.local_lifetime_by_key[key] == 120

    def test_oversized_keys_are_routed_to_the_toobig_dictionary(self):
        key = 'volumes/coiss_2xxx/coiss_2004'
        cache = _detached_memcached_cache(_StubMemcacheClient({}))
        cache.toobig_dict[key] = 'previous value'

        assert cache.set_multi({key: 'new value'}) == []

        assert cache.toobig_dict[key] == 'new value'
        assert key not in cache.local_value_by_key

##########################################################################################
