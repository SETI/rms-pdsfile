"""Caches that hold PdsFile objects and the bookkeeping a preload builds.

Two working classes share one interface, so a caller can be handed either:

  * ``DictionaryCache`` keeps everything in a dictionary inside one process. Nothing is
    shared, nothing is serialized, and the cache disappears with the process.
  * ``MemcachedCache`` keeps everything in a memcached server, so several processes see
    one cache. Values are buffered locally and written in batches.

``PdsCache`` is their common base. It declares nothing, so it records the kinship of the
two classes rather than enforcing an interface; the interface is whatever both classes
happen to implement.

That interface is dictionary-like -- ``get()``, ``set()``, ``delete()``, the ``in``
test, ``len()``, and item syntax for all three -- plus batch forms ``get_multi()``,
``set_multi()`` and ``delete_multi()``, a ``clear()``, and three accessors that say
where an answer may come from: ``get_local()`` reads only what this process holds,
``get_now()`` reads only the shared store, and ``set_local()`` writes only locally.

Every entry has a lifetime in seconds. Zero means the entry never expires. None means
"use this cache's default", which is either the constant or the function the cache was
built with; a function is called with the value being stored and returns its lifetime.
A cache built with a *constant* default of zero cannot resolve a lifetime of None,
because the test that picks between the constant and the function is a truth test on
the constant: such a call raises TypeError instead of storing a permanent entry.

Both classes count nested pauses. ``pause()`` and ``resume()`` bracket bulk work;
``is_paused`` reports the state. What a pause defers differs: a paused
``DictionaryCache`` does not trim, and a paused ``MemcachedCache`` does not flush.
Resuming to a count of zero performs the deferred work at once.

``MemcachedCache`` alone offers the cross-process facilities: ``wait_and_block()`` and
``unblock()`` claim and release exclusive use through a key every process consults,
``was_cleared()`` and ``replicate_clear()`` propagate one process's ``clear()`` to the
others, and ``flush()`` writes the local buffer out. ``DictionaryCache`` accepts all of
those calls and does nothing, since a cache one process owns needs no coordination.

``MEMCACHED_LOADED`` records whether ``pylibmc`` imported. Where it did not, the name
``pylibmc`` is unbound and constructing a ``MemcachedCache`` raises NameError.
"""

import os
import random

# `sys` is not referenced below; it is re-exported for callers that reach it as
# pdsfile.pdscache.sys. The redundant `as` alias is the explicit re-export form.
import sys as sys
import time

try:
    import pylibmc
    MEMCACHED_LOADED = True
except ImportError:
    MEMCACHED_LOADED = False

################################################################################
################################################################################
################################################################################

class PdsCache:
    """Common base of the cache classes.

    It has no attributes and no methods, so it constrains nothing: it exists so that
    ``DictionaryCache`` and ``MemcachedCache`` share a type, and so that a caller can
    test for a cache with one ``isinstance()``. The methods the two classes share are
    described in the module docstring; each class implements them independently.
    """

    pass

################################################################################
################################################################################
################################################################################

class DictionaryCache(PdsCache):
    """A cache held in one process's memory, in a plain dictionary.

    Values are stored as they are, not serialized, so a caller gets back the same object
    it stored. Nothing is shared with another process and nothing survives this one.

    An entry with a non-zero lifetime expires. Expiry is lazy: an entry past its time
    stays in the dictionary until something asks for it, so it still counts toward
    ``len()`` and still answers the ``in`` test, and it is ``get()`` that notices and
    removes it. An entry with a lifetime of zero is permanent -- it never expires and
    never counts against the size limit.

    The size limit is enforced by trimming. Once the number of expiring entries exceeds
    the limit by a margin of the larger of 20 and a tenth of the limit, the entries
    closest to expiring are discarded until the limit is met. Trimming happens after a
    ``set()`` and is deferred while the cache is paused.

    The blocking, flushing and clear-replication calls are accepted and do nothing,
    since one process owns the whole cache.
    """

    def __init__(self, lifetime=86400, limit=1000, logger=None):
        """Construct an empty cache.

        Parameters:
            lifetime: the default lifetime of an entry, used whenever a call passes no
                lifetime of its own. Either a number of seconds, where zero means the
                entry never expires, or a function taking the value being stored and
                returning that number. Only a plain function or a lambda is recognized
                as a function; a bound method is taken for a constant. A constant zero
                is a trap: it cannot be told apart from an absent default, so storing
                without an explicit lifetime then raises TypeError.
            limit (int): the number of expiring entries to keep. Permanent entries do
                not count toward it.
            logger: optional PdsLogger, which receives a message each time the cache
                trims, pauses or resumes.
        """

        self.dict = {}              # returns (value, expiration) by key
        self.keys = set()           # set of non-permanent keys

        if type(lifetime).__name__ == 'function':
            self.lifetime_func = lifetime
            self.lifetime = None
        else:
            self.lifetime = lifetime
            self.lifetime_func = None

        self.limit = limit
        self.slop = max(20, self.limit/10)
        self.logger = logger

        self.pauses = 0

        self.preload_eligible = True

    def _trim(self):
        """Discard the entries closest to expiring, if the cache has grown too large.

        Nothing happens until the number of expiring entries exceeds the limit by the
        margin fixed at construction. Once it does, entries are discarded in order of
        expiration, soonest first, until exactly the limit remains. Permanent entries
        are never candidates.
        """

        if len(self.keys) > self.limit + self.slop:
            expirations = [(self.dict[k][1], k) for k in self.keys if
                            self.dict[k][1] is not None]
            expirations.sort()
            pairs = expirations[:-self.limit]
            for (_, key) in pairs:
                del self.dict[key]
                self.keys.remove(key)

            if self.logger:
                self.logger.debug('%d items trimmed from DictionaryCache',
                                  len(pairs))

    def _trim_if_necessary(self):
        """Trim the cache unless it is paused.

        A paused cache is left alone, however far over the limit it has grown; the
        ``resume()`` that returns the pause count to zero trims it.
        """

        if self.pauses == 0:
            self._trim()

    def flush(self):
        """Do nothing.

        A dictionary cache buffers nothing, so there is nothing to write out. The call
        exists so that a caller can flush either kind of cache.
        """
        return

    def wait_for_unblock(self, funcname=''):
        """Do nothing and return at once.

        Only a shared cache can be blocked, so there is never anything to wait for.

        Parameters:
            funcname (str): ignored. It names the calling function in the messages the
                shared cache logs while it waits.
        """
        return

    def wait_and_block(self, funcname=''):
        """Do nothing and return at once.

        Only a shared cache can be blocked, so there is no block to claim.

        Parameters:
            funcname (str): ignored. It names the calling function in the messages the
                shared cache logs while it waits.
        """
        return

    def unblock(self, flush=True):
        """Do nothing.

        Only a shared cache can be blocked, so there is no block to release.

        Parameters:
            flush (bool): ignored. It tells the shared cache whether to write its buffer
                out as it unblocks.
        """
        return

    def is_blocked(self):
        """Report that the cache is not blocked, which it never is.

        Returns:
            bool: False, always.
        """
        return False

    def pause(self):
        """Defer trimming until the matching resume.

        Pauses nest: this increments a count, and only the ``resume()`` that returns the
        count to zero trims.
        """

        self.pauses += 1
        if self.pauses == 1 and self.logger:
            self.logger.debug('DictionaryCache trimming paused')

    @property
    def is_paused(self):
        """Whether trimming is currently deferred.

        Returns:
            bool: True while at least one pause is outstanding.
        """

        return self.pauses > 0

    def resume(self):
        """Release one pause, and trim if that was the last one.

        A call on a cache that is not paused is harmless: the count does not go
        negative, and the cache is trimmed as though the last pause had just been
        released.
        """

        if self.pauses > 0:
            self.pauses -= 1

        if self.pauses == 0:
            self._trim()
            if self.logger:
                self.logger.debug('DictionaryCache trimming resumed')

    def __contains__(self, key):
        """Report whether a key has an entry, expired or not.

        Expiry is not considered, so a key whose entry has expired but has not yet been
        read is still reported as present. Reading it through ``get()`` removes it, and
        the same test then answers False.

        Parameters:
            key: the key to test.

        Returns:
            bool: True if the key has an entry.
        """
        return (key in self.dict)

    def __len__(self):
        """Report how many entries the cache holds, expired or not.

        Permanent and expiring entries are counted alike, and an expired entry is
        counted until something reads it.

        Returns:
            int: the number of entries.
        """

        return len(self.dict)

    ######## Get methods

    def get(self, key):
        """Return the value stored under a key.

        An entry found to have expired is deleted, and the answer is None as though it
        had never been there. A stored value of None is therefore indistinguishable from
        a missing key.

        Parameters:
            key: the key to read.

        Returns:
            The stored value, or None if the key is absent or its entry has expired.
        """

        if key not in self.dict:
            return None

        (value, expiration) = self.dict[key]

        if expiration is None:
            return value

        if expiration < time.time():
            del self[key]
            return None

        return value

    def __getitem__(self, key):
        """Return the value stored under a key, insisting that there is one.

        A key whose stored value is None is treated the same as a missing key, because
        the two are indistinguishable to ``get()``.

        Parameters:
            key: the key to read.

        Returns:
            The stored value.

        Raises:
            KeyError: if the key is absent, its entry has expired, or its value is None.
        """

        value = self.get(key)
        if value is None:
            raise KeyError(key)

        return value

    def get_multi(self, keys):
        """Return the values stored under several keys, insisting that all are present.

        Every key must resolve. The first that does not -- because it is absent, has
        expired, or holds None -- stops the call with KeyError, so a partial result is
        never returned.

        Parameters:
            keys: the keys to read, as any iterable.

        Returns:
            dict: the value stored under each key, keyed by that key.

        Raises:
            KeyError: if any key is absent, expired, or holds None. It comes from the
                item lookup, ``__getitem__()``, that each key is read through.
        """

        mydict = {}
        for key in keys:
            value = self[key]
            if value is not None:
                mydict[key] = value

        return mydict

    def get_local(self, key):
        """Return the value stored under a key, reading only what this process holds.

        Everything a dictionary cache holds is local, so this is ``get()``, expiry check
        included.

        Parameters:
            key: the key to read.

        Returns:
            The stored value, or None if the key is absent or its entry has expired.
        """

        return self.get(key)

    def get_now(self, key):
        """Return the value stored under a key, bypassing any local buffer.

        A dictionary cache has no buffer to bypass, so this is ``get()``, expiry check
        included.

        Parameters:
            key: the key to read.

        Returns:
            The stored value, or None if the key is absent or its entry has expired.
        """

        return self.get(key)

    ######## Set methods

    def set(self, key, value, lifetime=None):
        """Store a value under a key, replacing any entry already there.

        The cache is trimmed afterwards unless it is paused.

        Parameters:
            key: the key to store under.
            value: the value to store. It is kept as it is, not copied.
            lifetime: how long the entry should last, in seconds. Zero makes it
                permanent. None means use the cache's default, which raises TypeError
                if that default is the constant zero.
        """

        # Determine the expiration time
        if lifetime is None:
            if self.lifetime:
                lifetime = self.lifetime
            else:
                lifetime = self.lifetime_func(value)

        if lifetime == 0:
            expiration = None
        else:
            expiration = time.time() + lifetime

        # Save in the dictionary
        self.dict[key] = (value, expiration)
        if expiration:
            self.keys.add(key)

        # Trim if necessary
        if not self.is_paused:
            self._trim_if_necessary()

    def __setitem__(self, key, value):
        """Store a value under a key, with the cache's default lifetime.

        Parameters:
            key: the key to store under.
            value: the value to store.
        """

        self.set(key, value)

    def set_multi(self, mydict, lifetime=0, pause=False):
        """Store several values at once.

        Each entry is stored exactly as ``set()`` would store it, so the cache may trim
        between one key and the next. The default lifetime here is zero rather than
        None, so entries stored without an explicit lifetime are permanent and are
        exempt from the size limit.

        Parameters:
            mydict (dict): the values to store, keyed by the key to store each under.
            lifetime: the lifetime to give every entry, in seconds. Zero, the default,
                makes them permanent. None means use the cache's default, which raises
                TypeError if that default is the constant zero.
            pause (bool): if True, skip the single trim that would otherwise follow the
                batch. It does not suppress the trims the individual stores perform, so
                a cache that is not already paused still trims during the batch.

        Returns:
            list: empty, always. The shared cache returns the keys it failed to store,
            and this returns the same shape so a caller can treat the two alike.
        """

        for (key, value) in mydict.items():
            self.set(key, value, lifetime)

        if not pause:
            self._trim_if_necessary()

        return []

    def set_local(self, key, value, lifetime=None):
        """Store a value under a key without writing to any shared store.

        A dictionary cache has no shared store, so this is ``set()``.

        Parameters:
            key: the key to store under.
            value: the value to store.
            lifetime: how long the entry should last, in seconds. Zero makes it
                permanent. None means use the cache's default.

        Returns:
            Nothing. The value passed on from ``set()`` is None.
        """

        return self.set(key, value, lifetime=lifetime)

    ######## Delete methods

    def delete(self, key):
        """Remove one entry, if it is there.

        Parameters:
            key: the key to remove.

        Returns:
            bool: True if an entry was removed, False if the key was absent.
        """

        if key in self.dict:
            del self.dict[key]
            return True

        return False

    def __delitem__(self, key):
        """Remove one entry, insisting that it is there.

        An expired entry that has not yet been read still counts as present and is
        removed without complaint.

        Parameters:
            key: the key to remove.

        Raises:
            KeyError: if the key is absent.
        """

        if key in self.dict:
            del self.dict[key]
            return

        raise KeyError(key)

    def delete_multi(self, keys):
        """Remove several entries, skipping the keys that are not there.

        Parameters:
            keys: the keys to remove, as any iterable.

        Returns:
            bool: True if every key named had an entry to remove, False if any did not.
        """

        status = True
        for key in keys:
            if key in self.dict:
                del self.dict[key]
            else:
                status = False

        return status

    def clear(self, block=False):
        """Remove every entry, permanent ones included.

        The pause count and the size limit are left as they are.

        Parameters:
            block (bool): ignored. It tells the shared cache to keep other processes out
                while it clears.
        """

        self.dict.clear()
        self.keys = set()

    def replicate_clear(self, clear_count):
        """Do nothing and report that nothing was cleared.

        Only a shared cache can be cleared by somebody else, so there is never anything
        to replicate.

        Parameters:
            clear_count: ignored. It is the count another process would have
                incremented by clearing.

        Returns:
            bool: False, always.
        """

        return False

    def replicate_clear_if_necessary(self):
        """Do nothing and report that nothing was cleared.

        Only a shared cache can be cleared by somebody else, so there is never anything
        to replicate.

        Returns:
            bool: False, always.
        """

        return False

    def was_cleared(self):
        """Report that nobody else has cleared the cache, which nobody else can.

        A ``clear()`` this process performed is not reported either; the question is
        about another process.

        Returns:
            bool: False, always.
        """

        return False

################################################################################
################################################################################
################################################################################

MAX_BLOCK_SECONDS = 120.

class MemcachedCache(PdsCache):
    """A cache held in a memcached server, so that several processes share one copy.

    Values are pickled by the client, so a caller gets back an equal object rather than
    the one it stored. Each entry is stored as the pair ``(value, lifetime)``, which is
    how a process that did not write an entry can still learn how long it was meant to
    last.

    Writes are buffered. A ``set()`` records the value locally and then flushes unless
    the cache is paused, and a flush groups the buffered keys by lifetime and writes one
    batch per group. Until a flush happens, this process reads its own writes and no
    other process sees them.

    Three local dictionaries back that buffer, and two more outlive it.
    ``permanent_values`` keeps a copy of every entry stored with a lifetime of zero, and
    restores the whole set to the server if one of them is ever found missing.
    ``toobig_dict`` keeps any value the server refused as too large; a key that lands
    there is served locally from then on and is never asked of the server again.

    Because the cache is shared, it can be blocked and it can be cleared out from under
    this process. ``wait_and_block()`` claims exclusive use by writing this process's ID
    to a key every process consults, and the other calls wait on that key before
    touching the server; a block older than ``MAX_BLOCK_SECONDS`` is broken by whoever
    is waiting. ``clear()`` increments a shared counter, and every other process notices
    the change on its next read and empties its own local dictionaries to match.

    A pause here defers flushing rather than trimming. Size is the server's business, so
    this class has no limit of its own.
    """

    def __init__(self, port=11211, lifetime=86400, logger=None):
        """Connect to a memcached server and prepare the local buffers.

        The server must already be running. The connection is tested by storing and
        deleting one randomly named key, so a construction that returns has proved the
        server reachable and writable. The shared bookkeeping keys are created if this
        is the first process to arrive.

        Parameters:
            port: the memcached port on the local host, as an integer, or the absolute
                path to a Unix socket, as a string.
            lifetime: the default lifetime of an entry, used whenever a call passes no
                lifetime of its own. Either a number of seconds, rounded up to a whole
                second and with zero meaning the entry never expires, or a function
                taking the value being stored and returning that number. A constant zero
                is a trap: it cannot be told apart from an absent default, so storing
                without an explicit lifetime then raises TypeError.
            logger: optional PdsLogger, which receives a message for each flush, block,
                clear and oversized value.
        """

        self.port = port

        if type(port) is str:
            self.mc = pylibmc.Client([port], binary=True)
        else:
            self.mc = pylibmc.Client(['127.0.0.1:%d' % port], binary=True)

        if type(lifetime).__name__ in ('function', 'method'):
            self.lifetime_func = lifetime
            self.lifetime = None
        else:
            self.lifetime = int(lifetime + 0.999)
            self.lifetime_func = None

        self.local_value_by_key = {}
        self.local_lifetime_by_key = {}
        self.local_keys_by_lifetime = {}
        # local_values_by_key is an internal dictionary of values that have not
        # yet been flushed to memcache.
        # local_lifetime_by_key is an internal dictionary of their lifetimes in
        # seconds, using the same key.
        # local_keys_by_lifetime is the inverse dictionary, which returns a list
        # of keys given a lifetime value.

        self.pauses = 0
        # This counter is incremented for every call to pause() and decremented
        # by every call to resume(). Flushing will not occur unless this value
        # is zero. Note that pauses can be nested, which is why it is a counter
        # and not a flag.

        self.permanent_values = {}
        # This is an internal copy of all values that this thread has
        # encountered lifetime == 0. It is used for extra protection in case
        # memcache allows a permanent value to expire.

        self.toobig_dict = {}
        # Any object that triggers a "TooBig" error is stored inside this
        # internal dictionary. It is not removed from memcached (if there)
        # because other threads might still use it, but this thread will never
        # again try to retrieve it from memcached. As a result, this dictionary
        # has to be the first place to look for any key.

        self.logger = logger

        # Test the cache with a random key so as not to clobber existing keys
        while True:
            key = str(random.randint(0,10**40))
            if key in self.mc:
                continue

            self.mc[key] = 1
            del self.mc[key]
            break

        # Save the ID of this process
        self.pid = os.getpid()

        # Initialize cache as unblocked
        ok_pid = self.mc.get('$OK_PID')
        if ok_pid is None:
            self.mc.set('$OK_PID', 0, time=0)
        # When the cached value of '$OK_PID' is nonzero, it means that the
        # thread with this process ID is currently blocking it.

        # Get the current count of clear() events and save it internally
        self.clear_count = self.mc.get('$CLEAR_COUNT')
        if self.clear_count is None:
            self.clear_count = 0
            self.mc.set('$CLEAR_COUNT', 0, time=0)
        # This is the internal copy of the cached value of '$CLEAR_COUNT'. When
        # a thread clears the cache, this value is incremented. If this thread
        # finds a cached value that differs from its internal value, it knows
        # to clear its own contents.

    def _wait_for_ok(self, funcname='', try_to_block=False):
        """Wait until no other process is blocking the cache, then optionally block it.

        A block held longer than ``MAX_BLOCK_SECONDS`` is broken: the blocking process's
        ID is overwritten, with this process's ID if it wants the block and zero
        otherwise, and the call returns at once.

        Breaking a block writes a warning without first testing for a logger, so a cache
        built without one raises AttributeError at that point rather than breaking the
        block.

        Parameters:
            funcname (str): name of the calling method, used in the log messages.
            try_to_block (bool): if True, claim the block once the wait ends.

        Returns:
            bool: True if any waiting was necessary, False if the cache was free
            immediately.
        """

        was_blocked = False
        while True:
            blocking_pid = self.mc.get('$OK_PID')
            if blocking_pid in (0, self.pid):
                break

            was_blocked = True
            unblock_time = time.time() + MAX_BLOCK_SECONDS
            if self.logger:
                if funcname:
                    self.logger.info(f'Process {self.pid} is blocked by ' +
                                     f'{blocking_pid} at {funcname}() on ' +
                                     f'MemcacheCache [{self.port}]')
                else:
                    self.logger.info(f'Process {self.pid} is blocked by ' +
                                     f'{blocking_pid} on ' +
                                     f'MemcacheCache [{self.port}]')

            while True:
                time.sleep(0.5 * (1. + random.random())) # A random short delay

                test_pid = self.mc.get('$OK_PID')
                if test_pid != blocking_pid:
                    break

                if time.time() > unblock_time:
                    new_pid = self.pid if try_to_block else 0
                    self.mc.set('$OK_PID', new_pid, time=0)
                    self.logger.warn(f'Process {self.pid} broke a block by ' +
                                     f'{blocking_pid} on ' +
                                     f'MemcacheCache [{self.port}]')
                    return True

        if try_to_block and blocking_pid != self.pid:
            self.mc.set('$OK_PID', self.pid, time=0)

        return was_blocked

    def wait_for_unblock(self, funcname=''):
        """Wait until no other process is blocking the cache, and claim nothing.

        A block this process holds itself does not count, so the call returns at once.

        Parameters:
            funcname (str): name of the calling method, used in the log messages.

        Returns:
            bool: True if any waiting was necessary, False if the cache was free
            immediately.
        """

        was_blocked = self._wait_for_ok(funcname=funcname, try_to_block=False)
        if was_blocked and self.logger:
            self.logger.info(f'Process {self.pid} is unblocked on ' +
                             f'MemcacheCache [{self.port}]')

        return was_blocked

    def wait_and_block(self, funcname=''):
        """Wait until the cache is free, then claim it for this process alone.

        Two processes can finish waiting at the same moment, in which case only one wins
        the claim; the loser logs the fact and waits again, so the call does not return
        until this process holds the block. Losing the race writes a warning without
        first testing for a logger, so a cache built without one raises AttributeError
        at that point.

        The block stays until ``unblock()`` or a ``clear()`` that does not keep it.

        Parameters:
            funcname (str): name of the calling method, used in the log messages.

        Returns:
            bool: True if any waiting was necessary, False if the cache was free
            immediately.
        """

        was_blocked = False
        while True:
            was_blocked |= self._wait_for_ok(funcname=funcname,
                                             try_to_block=True)

            test_pid = self.mc.get('$OK_PID')
            if test_pid == self.pid:
                if self.logger:
                    self.logger.info(f'Process {self.pid} is now blocking '
                                     f'MemcachedCache [{self.port}]')
                return was_blocked

            self.logger.warn(f'Process {self.pid} was outraced by {test_pid} ' +
                             'while waiting to block')

    def unblock(self, flush=True):
        """Release this process's block, letting other processes touch the cache again.

        A cache that is not blocked, or one blocked by another process, is an error: the
        call logs it and returns without changing anything. Both of those refusals are
        conditioned on a logger being present, so a cache built without one goes ahead
        and clears the block in either case, including a block another process holds.

        Parameters:
            flush (bool): if True, write the local buffer out after releasing the block.
        """

        test_pid = self.mc.get('$OK_PID')
        if not test_pid and self.logger:
            self.logger.error(f'Process {self.pid} is unable to unblock ' +
                              f'MemcachedCache [{self.port}]; ' +
                              'Cache is already unblocked')
            return

        if test_pid != self.pid and self.logger:
            self.logger.error(f'Process {self.pid} is unable to unblock ' +
                              f'MemcachedCache [{self.port}]; ' +
                              f'Cache is blocked by process {test_pid}')
            return

        self.mc.set('$OK_PID', 0, time=0)
        if self.logger:
            self.logger.info(f'Process {self.pid} removed block of ' +
                             f'MemcachedCache [{self.port}]')

        if flush:
            self.flush()

    def is_blocked(self):
        """Report which other process, if any, is blocking the cache.

        A block this process holds itself does not count. A missing bookkeeping key is
        repaired by writing it back as unblocked.

        Returns:
            int: the process ID of the process holding the block, or 0 if the cache is
            free or this process holds it.
        """

        test_pid = self.mc.get('$OK_PID')
        if test_pid is None:                    # repair a missing $OK_PID
            self.mc.set('$OK_PID', 0, time=0)
            test_pid = 0

        if test_pid in (0, self.pid):
            return 0
        else:
            return test_pid

    def pause(self):
        """Defer flushing until the matching resume.

        Pauses nest: this increments a count, and only the ``resume()`` that returns the
        count to zero flushes. Values stored while paused stay visible to this process
        and invisible to every other one.
        """
        self.pauses += 1

        if self.pauses == 1 and self.logger:
            self.logger.debug(f'Process {self.pid} has paused flushing on ' +
                              f'MemcachedCache [{self.port}]')

    @property
    def is_paused(self):
        """Whether flushing is currently deferred.

        Returns:
            bool: True while at least one pause is outstanding.
        """

        return self.pauses > 0

    def resume(self):
        """Release one pause, and flush if that was the last one.

        A call on a cache that is not paused is harmless: the count does not go
        negative, and the buffer is written out as though the last pause had just been
        released.
        """

        if self.pauses > 0:
            self.pauses -= 1

        if self.pauses == 0:
            if self.logger:
                self.logger.debug(f'Process {self.pid} has resumed flushing ' +
                                  f'on MemcachedCache [{self.port}]')
            self.flush()

    def __contains__(self, key):
        """Report whether a key has an entry anywhere this process can see.

        The oversized values, the unflushed buffer and the permanent copies are
        consulted before the server, so a key is reported present even when the server
        has never been told about it or has let it expire.

        Parameters:
            key: the key to test.

        Returns:
            bool: True if the key has an entry.
        """

        if key in self.toobig_dict:
            return True
        if key in self.local_value_by_key:
            return True
        if key in self.permanent_values:
            return True
        return key in self.mc

    def __len__(self):
        """Report how many entries this process can see.

        The count starts from everything the server holds -- for every process, not just
        this one -- and adds this process's oversized and unflushed entries that the
        server does not already have.

        Returns:
            int: the number of entries.
        """

        items = self.len_mc()

        for key in self.toobig_dict:
            if key not in self.mc:
                items += 1

        for key in self.local_value_by_key:
            if key not in self.mc:
                items += 1

        return items

    def len_mc(self):
        """Report how many entries the memcached server holds.

        The count covers every process using the server, and the bookkeeping keys as
        well. It comes from the first server in the client's list, so a client
        configured with more than one server undercounts.

        Returns:
            int: the server's current item count.
        """

        return int(self.mc.get_stats()[0][1]['curr_items'])

    ######## Flush methods

    def flush(self):
        """Write the buffered values to the server and empty the buffer.

        An empty buffer returns at once. So does a flush that discovers another process
        has cleared the cache, since replicating that clear has already emptied the
        buffer. Otherwise the call waits for any block to lift, copies the entries whose
        lifetime is zero into the permanent set, and writes one batch per distinct
        lifetime.

        A value the server rejects as too large is retried on its own and, on a second
        rejection, moved to the oversized dictionary, where this process serves it from
        then on; the buffer is emptied as usual, so the remaining batches still go out.

        Any other server error takes a path that does not complete: with a logger, the
        reporting step raises AttributeError, and the buffer is left unwritten and
        unemptied. Without a logger, the batch's keys are counted as failures, the
        remaining batches go out, and the buffer is emptied, so the values the failed
        batch held are lost rather than retried.
        """

        # Nothing to do if local cache is empty
        if len(self.local_value_by_key) == 0:
            return

        if self.replicate_clear_if_necessary():
            return

        # Save non-expiring values to the permanent dictionary
        if 0 in self.local_keys_by_lifetime:
            for k in self.local_keys_by_lifetime[0]:
                self.permanent_values[k] = self.local_value_by_key[k]

        self.wait_for_unblock('flush')

        # Cache items grouped by lifetime
        failures = []
        toobigs = []
        for lifetime in self.local_keys_by_lifetime:

            # Save tuples (value, lifetime)
            mydict = {k:(self.local_value_by_key[k], lifetime) for
                                k in self.local_keys_by_lifetime[lifetime]}

            # Update to memcache
            try:
                self.mc.set_multi(mydict, time=lifetime)
            except pylibmc.TooBig:
                for (k,v) in mydict.items():
                    try:
                        self.mc.set(k, v, time=lifetime)
                    except pylibmc.TooBig:
                        toobigs.append(k)
                        failures.append(k)
                        self.toobig_dict[k] = v[0]
                        if self.logger:
                            self.logger.warn('TooBig error in process ' +
                                             f'{self.pid}; ' +
                                             'saved to internal cache', k)
            except pylibmc.Error as e:
                if self.logger:
                    self.logger.exception(e)

                keys = mydict.keys()
                if self.logger:
                    keys.sort()
                    for key in keys:
                        self.logger.error(f'Process {self.pid} has failed ' +
                                          'to flush; deleted', key)

                failures += keys

        if self.logger:
            count = len(self.local_keys_by_lifetime) - len(failures)
            if count == 1:
                desc = '1 item,'
            else:
                desc = str(count) + ' items, including'
            self.logger.debug(f'Process {self.pid} has flushed {desc} ' +
                              list(mydict.keys())[0] +
                              f', to MemcachedCache [{self.port}]; ' +
                              f'current size is {self.len_mc()}')
            if toobigs:
                count = len(self.toobig_dict)
                noun = 'item' if count == 1 else 'items'
                self.logger.debug(f'Process {self.pid} now has {count} ' +
                                  f'toobig {noun} cached locally')

        # Clear internal dictionaries
        self.local_lifetime_by_key.clear()
        self.local_value_by_key.clear()
        self.local_keys_by_lifetime.clear()

    ######## Get methods

    def get(self, key):
        """Return the value stored under a key.

        A clear performed by another process is replicated first, so a value this
        process buffered before that clear is gone by the time the lookup runs. The
        oversized values are consulted first, then the unflushed buffer, then the
        server. A permanent entry the server has lost is served from the permanent copy,
        and every permanent entry is written back to the server at that point.

        Parameters:
            key: the key to read.

        Returns:
            The stored value, or None if no source has it.
        """

        self.replicate_clear_if_necessary()

        # Return from local caches if found
        if key in self.toobig_dict:
            return self.toobig_dict[key]

        if key in self.local_value_by_key:
            return self.local_value_by_key[key]

        # Otherwise, go to memcache
        self.wait_for_unblock('get')
        pair = self.mc.get(key)

        # Value not found...
        if pair is None:

            # Check the permanent dictionary in case it was wrongly deleted
            if key in self.permanent_values:
                self._restore_permanent_to_cache()
                return self.permanent_values[key]

            # Otherwise, return None
            return None

        (value, lifetime) = pair

        # If this is a permanent value, update the local copy
        if lifetime == 0:
            self.permanent_values[key] = value

        return value

    def __getitem__(self, key):
        """Return the value stored under a key, insisting that there is one.

        A key whose stored value is None is treated the same as a missing key, because
        the two are indistinguishable to ``get()``.

        Parameters:
            key: the key to read.

        Returns:
            The stored value.

        Raises:
            KeyError: if no source has the key, or its value is None.
        """

        value = self.get(key)
        if value is None:
            raise KeyError(key)

        return value

    def get_multi(self, keys):
        """Return the values stored under several keys, skipping the ones with none.

        A clear performed by another process is replicated first. The keys are split
        between the oversized values, the unflushed buffer and the server, and the
        server is asked for its share one key at a time rather than in a batch. If any
        of the requested keys is a permanent entry the server has lost, every permanent
        entry is written back to the server.

        Parameters:
            keys: the keys to read, as a list or a set.

        Returns:
            dict: the value found for each key, keyed by that key. A key with no value
            anywhere is absent from the result.
        """

        self.replicate_clear_if_necessary()

        # Separate keys into local, toobig, and non-local (in memcache)
        nonlocal_keys = set(keys)
        toobig_keys = set(self.toobig_dict.keys()) & nonlocal_keys
        nonlocal_keys -= toobig_keys

        local_keys = set(self.local_value_by_key.keys()) & nonlocal_keys
        nonlocal_keys -= local_keys

        # Retrieve non-local keys if any
        if nonlocal_keys:
            self.wait_for_unblock('get_multi')

# Memcached->get_multi hangs on long lists; individual requests work fine
#             mydict = self.mc.get_multi(nonlocal_keys)
            mydict = {}
            for key in nonlocal_keys:
                pair = self.mc.get(key)
                if pair:
                    mydict[key] = pair

            for (key, pair) in mydict.items():
                (value, lifetime) = pair
                mydict[key] = value

                # Update the local copy of any permanent values
                if lifetime == 0:
                    self.permanent_values[key] = value

            # Check the permanent dictionary in case it was wrongly deleted
            for key in nonlocal_keys:
                if key in self.permanent_values and key not in mydict:
                    self._restore_permanent_to_cache()
                    break

        else:
            mydict = {}

        # Augment the dictionary with the locally-cached values
        for key in toobig_keys:
            mydict[key] = self.toobig_dict[key]

        for key in local_keys:
            mydict[key] = self.local_value_by_key[key]

        return mydict

    def get_local(self, key):
        """Return the value stored under a key, reading only what this process holds.

        The oversized values and the unflushed buffer are consulted; the server is not,
        and neither is the permanent copy.

        Parameters:
            key: the key to read.

        Returns:
            The stored value, or None if this process holds none.
        """

        # Return from local cache if found
        if key in self.toobig_dict:
            return self.toobig_dict[key]

        if key in self.local_value_by_key:
            return self.local_value_by_key[key]

        return None

    def get_now(self, key):
        """Return the value the server holds under a key, ignoring everything local.

        The call does not wait for a block to lift and does not replicate another
        process's clear, so it answers even while the cache is blocked. A value this
        process has buffered but not flushed is not visible to it.

        Parameters:
            key: the key to read.

        Returns:
            The value the server holds, or None if the server has none.
        """

        result = self.mc.get(key)
        if result is None:
            return None

        (value, _lifetime) = result
        return value

    ######## Set methods

    def set(self, key, value, lifetime=None):
        """Store a value under a key, and flush unless the cache is paused.

        A key already in the oversized dictionary is updated there and nowhere else; the
        server is not told, and the call returns without flushing.

        With no lifetime given and none already buffered for this key, the lifetime
        recorded on the server for that key is looked up and reused, which lets a
        process that did not write an entry replace its value without shortening its
        life. A key the server does not have falls through to the cache's default.

        Parameters:
            key: the key to store under.
            value: the value to store.
            lifetime: how long the entry should last, in seconds. Zero makes it
                permanent. None means keep the lifetime this key already has, and
                failing that use the cache's default.

        Returns:
            bool: True, except on the oversized path, which returns None.
        """

        if key in self.toobig_dict:
            self.toobig_dict[key] = value
            return

        if (lifetime is None) and (key not in self.local_lifetime_by_key):
            try:
                (_, lifetime) = self.mc[key]
            except KeyError:
                pass

        self.set_local(key, value, lifetime)

        if not self.is_paused:
            self.flush()

        return True

    def __setitem__(self, key, value):
        """Store a value under a key, keeping the lifetime that key already has.

        Parameters:
            key: the key to store under.
            value: the value to store.
        """

        _ = self.set(key, value, lifetime=None)

    def set_multi(self, mydict, lifetime=None):
        """Store several values at once, and flush unless the cache is paused.

        Keys already in the oversized dictionary are updated there and nowhere else.

        With no lifetime given, the lifetimes recorded on the server are looked up for
        the keys the server has, in one batch. One lifetime is then applied to the whole
        batch: the loop that reads them leaves a single value behind, and that value is
        what every key is stored with, whether or not the server had a different one for
        it. Keys already buffered locally are excluded from the lookup and, when the
        lookup finds nothing at all, keep their buffered lifetime.

        Storing resets the clock on every key, so an entry keeps its length of life but
        not its remaining life.

        Parameters:
            mydict (dict): the values to store, keyed by the key to store each under.
            lifetime: the lifetime to give every entry, in seconds. Zero makes them
                permanent. None means take the lifetimes from the server as described
                above.

        Returns:
            list: empty, always. The keys a flush fails to store are not reported here.
        """

        # Separate keys into local, toobig, and non-local (in memcache)
        nonlocal_keys = set(mydict.keys())
        toobig_keys = set(self.toobig_dict.keys()) & nonlocal_keys
        nonlocal_keys -= toobig_keys

        local_keys = set(self.local_value_by_key.keys()) & nonlocal_keys
        nonlocal_keys -= local_keys

        # Retrieve lifetimes from cache if necessary
        if lifetime is None and nonlocal_keys:
            nonlocal_dict = self.mc.get_multi(nonlocal_keys)
            for (key, pair) in nonlocal_dict.items():
                lifetime = pair[1]
                self.local_lifetime_by_key[key] = lifetime

        # Save or update values in local cache
        for (key, value) in mydict.items():
            if key in toobig_keys:
                self.toobig_dict[key] = value
            else:
                self.set_local(key, value, lifetime)

        if not self.is_paused:
            self.flush()

        return []

    def set_local(self, key, value, lifetime=None):
        """Buffer a value under a key without writing to the server.

        The value waits in the buffer until a flush. A key already in the oversized
        dictionary is updated there instead and never enters the buffer.

        The key is recorded both by lifetime and by key, so a flush can group the keys
        that share a lifetime into one batch. Changing a key's lifetime moves it between
        those groups.

        Parameters:
            key: the key to store under.
            value: the value to store.
            lifetime: how long the entry should last, in seconds, rounded up to a whole
                second. Zero makes it permanent. None means keep the lifetime this key
                already has in the buffer, and failing that use the cache's default; the
                server is not consulted either way.
        """

        if key in self.toobig_dict:
            self.toobig_dict[key] = value
            return

        # Save the value
        self.local_value_by_key[key] = value

        # Determine the lifetime
        if lifetime is None:
            try:
                lifetime = self.local_lifetime_by_key[key]
            except KeyError:
                if self.lifetime:
                    lifetime = self.lifetime
                else:
                    lifetime = int(self.lifetime_func(value) + 0.999)

        # Remove an outdated key from the lifetime-to-keys dictionary
        try:
            prev_lifetime = self.local_lifetime_by_key[key]
            if prev_lifetime != lifetime:
                self.local_keys_by_lifetime[prev_lifetime].remove(key)
                if len(self.local_keys_by_lifetime[prev_lifetime]) == 0:
                    del self.local_keys_by_lifetime[prev_lifetime]
        except (KeyError, ValueError):
            pass

        # Insert the key into the lifetime-to-keys dictionary
        if lifetime not in self.local_keys_by_lifetime:
            self.local_keys_by_lifetime[lifetime] = [key]
        elif key not in self.local_keys_by_lifetime[lifetime]:
            self.local_keys_by_lifetime[lifetime].append(key)

        # Insert the key into the key-to-lifetime dictionary
        self.local_lifetime_by_key[key] = lifetime

    ######## Delete methods

    def delete(self, key):
        """Remove one entry from the server and from every local dictionary.

        The permanent copy and the oversized value are dropped too, so the key does not
        come back on the next lookup.

        Parameters:
            key: the key to remove.

        Returns:
            bool: True if the server or this process had something to remove, False if
            neither did.
        """

        self.wait_for_unblock('delete')
        status1 = self.mc.delete(key)
        status2 = self._delete_local(key)

        if key in self.permanent_values:
            del self.permanent_values[key]

        if key in self.toobig_dict:
            del self.toobig_dict[key]

        return status1 or status2

    def __delitem__(self, key):
        """Remove one entry, insisting that it is there.

        Parameters:
            key: the key to remove.

        Raises:
            KeyError: if neither the server nor this process had anything to remove.
        """

        status = self.delete(key)
        if status:
            return

        raise KeyError(key)

    def delete_multi(self, keys):
        """Remove several entries from the server and from every local dictionary.

        The server is told first, and then each key is removed locally through a helper
        this class does not define, so any non-empty batch raises AttributeError at its
        first key. The server-side deletion has already happened by then, and the local
        dictionaries and the permanent copies are left holding whatever they held.

        Parameters:
            keys: the keys to remove, as a list.

        Returns:
            bool: reached only by an empty batch, which removes nothing and answers
            True. The test compares a count that any real deletion drives negative
            against the number of keys, so it could not answer True for a batch that had
            work to do.
        """

        self.wait_for_unblock('delete_multi')
        _ = self.mc.del_multi(keys)

        # Save the current length
        prev_len = len(self)

        # Delete whatever we can from the local cache and  permanent dictionary
        for key in keys:
            _ = self._del_local(key)

            if key in self.permanent_values:
                del self.permanent_values[key]

            if key in self.toobig_dict:
                del self.toobig_dict[key]

        count = len(self) - prev_len
        return (count == len(keys))

    def _delete_local(self, key):
        """Remove one key from this process's dictionaries, leaving the server alone.

        The oversized value and the buffered value are both removed, along with the
        key's lifetime bookkeeping. The permanent copy is not touched.

        Parameters:
            key: the key to remove.

        Returns:
            bool: True if anything was removed, False if this process held nothing under
            that key.
        """

        deleted = False
        if key in self.toobig_dict:
            del self.toobig_dict[key]
            deleted = True

        if key in self.local_lifetime_by_key:
            del self.local_value_by_key[key]
            deleted = True

            lifetime = self.local_lifetime_by_key[key]
            self.local_keys_by_lifetime[lifetime].remove(key)
            if len(self.local_keys_by_lifetime[lifetime]) == 0:
                del self.local_keys_by_lifetime[lifetime]

            del self.local_lifetime_by_key[key]

        return deleted

    def clear(self, block=False):
        """Empty the server and every local dictionary, for every process.

        The shared clear counter is incremented, which is how the other processes learn
        to empty their own dictionaries on their next read. The cache is blocked for the
        duration whether or not ``block`` was asked for; ``block`` decides only whether
        the block is kept afterwards.

        Parameters:
            block (bool): if True, keep the block after clearing, so this process can
                repopulate the cache before anything else reads it. The caller is then
                responsible for calling ``unblock()``.
        """

        if block:
            self.wait_and_block('clear')
        else:
            self.wait_for_unblock('clear')

        clear_count = max(self.mc.get('$CLEAR_COUNT'), self.clear_count) + 1
        self.mc.flush_all()
        self.mc.set_multi({'$OK_PID': self.pid, # retain block!
                           '$CLEAR_COUNT': clear_count}, time=0)

        self.local_value_by_key.clear()
        self.local_keys_by_lifetime.clear()
        self.local_lifetime_by_key.clear()
        self.permanent_values.clear()
        self.toobig_dict.clear()
        self.clear_count = clear_count

        if self.logger:
            self.logger.info(f'Process {self.pid} has set clear count to ' +
                             f'{self.clear_count} on ' +
                             f'MemcacheCache [{self.port}]')

        if block:
            if self.logger:
                self.logger.info(f'Process {self.pid} has completed clear() ' +
                                 f'of MemcacheCache [{self.port}] ' +
                                 'but continues to block')
        else:
            self.unblock()

    def replicate_clear(self, clear_count):
        """Empty this process's dictionaries if the shared clear counter has moved.

        A counter matching the one this process last saw means nothing has happened and
        nothing is done. Otherwise every local dictionary is emptied, permanent copies
        and oversized values included, and the new counter is remembered.

        A counter of None means the server has lost the bookkeeping key. That case
        writes the None straight back to the server rather than restoring the count this
        process knows, which leaves the key holding a value no comparison can use.

        Parameters:
            clear_count: the shared counter's current value, as read from the server.

        Returns:
            bool: True if the local dictionaries were emptied, False otherwise.
        """

        if clear_count == self.clear_count:
            return False

        if clear_count is None:         # lost from memcache!
            self.mc.set('$CLEAR_COUNT', clear_count, time=0)
            return False

        self.local_value_by_key.clear()
        self.local_keys_by_lifetime.clear()
        self.local_lifetime_by_key.clear()
        self.permanent_values.clear()
        self.toobig_dict.clear()
        self.clear_count = clear_count

        if self.logger:
            self.logger.info(f'Process {self.pid} has replicated clear of ' +
                             f'MemcacheCache [{self.port}]')
        return True

    def replicate_clear_if_necessary(self):
        """Read the shared clear counter and replicate any clear it reports.

        This is what the read and write paths call so that a clear by another process
        takes effect here before anything else happens.

        Returns:
            bool: True if the local dictionaries were emptied, False otherwise.
        """

        clear_count = self.mc.get('$CLEAR_COUNT')
        return self.replicate_clear(clear_count)

    def was_cleared(self):
        """Report whether the cache has been cleared since this process last noticed.

        Nothing is emptied here; the answer is a comparison only. A server that has lost
        the bookkeeping key makes the comparison raise TypeError.

        Returns:
            bool: True if the shared clear counter is ahead of the one this process
            last saw.
        """

        clear_count = self.mc.get('$CLEAR_COUNT')
        return clear_count > self.clear_count

    def _restore_permanent_to_cache(self):
        """Write every permanent entry back to the server.

        This runs when a permanent entry is found missing from the server, which should
        not happen but does. Each permanent key is read back one at a time, so a value
        the server still has refreshes this process's copy rather than being overwritten
        by it; only the ones the server has actually lost are written.

        A permanent value the server rejects as too large is moved to the oversized
        dictionary and dropped from the permanent set, so the next lost entry does not
        try it again. That report is written without first testing for a logger, so a
        cache built without one raises AttributeError at that point.
        """

        if self.logger:
            self.logger.warn(f'Process {self.pid} is restoring permanent ' +
                             f'values to MemcacheCache [{self.port}]')

        # Update permanent values from cache
        local_dict = self.permanent_values.copy()

# Memcached->get_multi hangs on long lists; individual requests work fine
#         permanent_keys = list(self.permanent_values.keys())
#         mydict = self.mc.get_multi(permanent_keys)
#         for (key, pair) in mydict.items():
#             self.permanent_values[key] = pair[0]
#             del local_dict[key]

        for key in self.permanent_values:
            pair = self.mc.get(key)
            if pair:
                self.permanent_values[key] = pair[0]
                del local_dict[key]

        # At this point, local_dict contains all the permanent values currently
        # missing from the cache. Also, self.permanent_values is as up to date
        # as it can be.

        mydict = {k:(v,0) for (k,v) in local_dict.items()}
        try:
            self.mc.set_multi(mydict, time=0)

        except pylibmc.TooBig:

        # This happens if a "TooBig" item is supposed to be in the permanent
        # cache. It means that we have to remove it from the permanent_values
        # dictionary so this doesn't happen again.

            for (k,v) in mydict.items():
                try:
                    self.mc.set(k, v, time=0)
                except pylibmc.TooBig:
                    self.logger.warn('Permanent object is TooBig in process ' +
                                     f'{self.pid}; ' +
                                     'removed from permanent list and saved ' +
                                     'to internal cache', k)
                    self.toobig_dict[k] = v[0]
                    del self.permanent_values[k]
