##########################################################################################
# pdsfile/_preload.py
##########################################################################################

"""Filling the cache the PdsFile classes share, from one or more holdings directories.

Walking a holdings tree is expensive and its top is stable, so a process that will serve
many requests walks the top once at startup and keeps what it found. That walk is the
preload, and this module is it.

``preload()`` is the entry point. It chooses the cache implementation, walks each
holdings directory down as far as its bundle sets, constructs and caches what it finds,
loads the bundle descriptions and the icons, and records which holdings it has covered so
that a second call does not repeat the work. The walk deliberately stops at the bundle
set: below that, objects are built on demand.

What makes several physical holdings directories look like one tree is the **merged
directory**: for each category there is one cache entry whose children are the union of
that category's children in every holdings directory.
``cache_category_merged_dirs()`` creates the ones a category does not have yet, and it
runs at import time, so a tree that is never preloaded still has them. ``preload()``
does not go through it: it rebuilds every category's merged directory unconditionally,
discarding whatever the import-time call left there.

The cache holds four kinds of permanent entry beside the PdsFile objects themselves --
the version ranks per category, the directory paths per version, the list of holdings
already preloaded, and the bundle descriptions read from the ``_volinfo`` tables. The
comment block below names their keys. ``get_permanent_values()`` re-reads them and
preloads again if any has gone missing, which is how a shared memcached that has been
trimmed or restarted is repaired.

``cache_lifetime_for_class()`` decides, per object, how long that object should be kept,
and the four lifetimes are the module constants below. What ``preload()`` hands a cache
it builds is not that function but ``cache_lifetime()``, the class method that wraps it.
A memcached cache takes a method as a lifetime function; a dictionary cache does not, and
stores it as a constant default instead, so the first store into such a cache that needs
the default raises TypeError.

``is_preloading()``, ``pause_caching()`` and ``resume_caching()`` are the small
operations a caller outside the package reaches through ``pdsfile.preload_and_cache``.
"""

import os
import time

from pdsfile import pdscache, pdsviewable

# Import module for memcached if possible, otherwise flag
try: # pragma: no cover
    import pylibmc
    HAS_PYLIBMC = True
except ImportError: # pragma: no cover
    HAS_PYLIBMC = False

from ._path_utils import _clean_abspath, _clean_join

##########################################################################################
# Memcached and other cache support
##########################################################################################

# Cache of PdsFile objects:
#
# These entries in the cache are permanent:
#
# CACHE['$RANKS-<category>/']
#       This is a dictionary keyed by [bundleset] or [bundlename], which returns a
#       sorted list of ranks. Ranks are the PdsFile way of tracking versions of
#       objects. A higher rank (an integer) means a later version. All keys are
#       lower case. Replace "<category>" above by one of the names of the
#       holdings/ subdirectories.
#
# CACHE['$VOLS-<category>/']
#       This is a dictionary of dictionaries, keyed by [bundleset][rank] or
#       [bundlename][rank]. It returns the directory path of the bundleset or bundlename.
#       Keys are lower case.
#
# CACHE['$PRELOADED']
#       This is a list of holdings abspaths that have been preloaded.
#
# CACHE['$VOLINFO-<bundleset>']
# CACHE['$VOLINFO-<bundleset/bundlename>']
#       Returns (description, icon_type, version, publication date, list of
#                data set IDs)
#       for bundlenames and bundlesets. Keys are lower case.
#
# In addition...
#
# CACHE[<logical-path-in-lower-case>]
#       Returns the PdsFile object associated with the given path, if it has
#       been cached.

DEFAULT_FILE_CACHE_LIFETIME =  12 * 60 * 60      # 12 hours
LONG_FILE_CACHE_LIFETIME = 7 * 24 * 60 * 60      # 7 days
SHORT_FILE_CACHE_LIFETIME = 2 * 24 * 60 * 60     # 2 days
FOEVER_FILE_CACHE_LIFETIME = 0                   # forever
DICTIONARY_CACHE_LIMIT = 200000

def cache_lifetime_for_class(arg, cls=None):
    """Return how long an object should be kept in the cache, in seconds.

    Zero means forever, which is what the cache classes read a zero lifetime as.

    Six cases, in the order they are tested. A string is a rendered page and lives the
    default lifetime. Anything that is not an instance of the class given lives forever,
    which is what keeps the bookkeeping entries -- the rank and version tables, the list
    of preloaded holdings, the bundle descriptions -- from expiring. A bundle set or
    bundle, recognized by having no interior path, lives a long time. A directory below
    that whose name ends in ``data`` also lives a long time, because it is the one most
    often revisited; any other directory lives a short time. Anything else lives the
    default lifetime.

    **The class is what separates the second case from the rest, and it is optional.**
    Called without one, no object is recognized as a bookkeeping entry, so a bookkeeping
    value reaches the third test and raises AttributeError on the interior attribute it
    does not have.

    Parameters:
        arg: the object about to be cached.
        cls: the PdsFile subclass whose instances are the objects being cached. None
            skips the bookkeeping case entirely.

    Returns:
        int: the lifetime in seconds, or zero for forever.
    """

    # Keep Viewmaster HTML for 12 hours
    if isinstance(arg, str):
        return DEFAULT_FILE_CACHE_LIFETIME

    # Keep RANKS, VOLS, etc. forever
    elif cls is not None and not isinstance(arg, cls):
        return FOEVER_FILE_CACHE_LIFETIME

    # Cache PdsFile bundlesets/bundles for a long time, but not necessarily forever
    elif not arg.interior:
        return LONG_FILE_CACHE_LIFETIME

    elif arg.isdir and arg.interior.lower().endswith('data'):
        return LONG_FILE_CACHE_LIFETIME     # .../bundlename/*data for a long time
    elif arg.isdir:
        return SHORT_FILE_CACHE_LIFETIME            # Other directories for two days
    else:
        return DEFAULT_FILE_CACHE_LIFETIME

def is_preloading(cls):
    """Return whatever the cache records under the preloading flag.

    The value is read past any local buffer, so a flag set by another process sharing a
    memcached is seen. Nothing in this package ever writes that entry, so the answer is
    None unless something outside it has.

    Parameters:
        cls: the PdsFile subclass whose cache to read.

    Returns:
        the value stored under the flag, or None.
    """

    return cls.CACHE.get_now('$PRELOADING')

def pause_caching(cls):
    """Stop a cache from writing through to its external store.

    While paused, a dictionary cache stops trimming and a memcached cache buffers its
    writes locally instead of sending them. Pauses nest, so an inner pause does not
    release an outer one.

    Parameters:
        cls: the PdsFile subclass whose cache to pause.
    """

    cls.CACHE.pause()

def resume_caching(cls):
    """Let a cache write through to its external store again.

    This undoes one pause. A cache that was paused more than once stays paused until the
    last pause has been resumed, and the buffered writes are sent then.

    Parameters:
        cls: the PdsFile subclass whose cache to resume.
    """

    cls.CACHE.resume()


##########################################################################################
# Preload mixin
##########################################################################################
class _PreloadMixin:
    """Filling and configuring the cache the PdsFile classes share.

    A mixin of PdsFile; it holds methods only and defines no state of its own.

    preload is the entry point: given one or more holdings directories it picks
    the cache implementation -- a DictionaryCache, or a MemcachedCache when
    pylibmc is importable and either the port argument or the class's
    MEMCACHE_PORT is non-zero -- then walks each holdings
    tree down through its category directories and bundlesets, constructing and
    caching their children as it goes, and records which holdings it has loaded.
    load_volume_info reads the "|"-separated _volinfo tables that describe each
    bundleset and bundle. cache_category_merged_dirs seeds the category-level
    merged directories, which is what makes one logical tree out of several
    physical ones. get_permanent_values re-reads the entries that are supposed to
    be permanent and preloads again if any has gone missing. cache_lifetime is
    what preload hands a cache it creates as that cache's default lifetime, and it
    delegates to the module-level cache_lifetime_for_class above. Being a class
    method rather than a plain function, it counts as a lifetime function to a
    MemcachedCache but not to a DictionaryCache, which keeps it as a constant
    default and raises TypeError on the first store that needs one.

    Every attribute these methods and the module-level functions above them read
    or write on a PdsFile object or on a PdsFile class, and nothing else -- str,
    list, dict, file, os, os.path, pdscache, pdsviewable, pylibmc, time and logger
    methods are not in scope::

      class attributes read       CACHE, CATEGORY_LIST, DICTIONARY_CACHE_LIMIT,
                                  EXTRA_README_BASENAMES, LOCAL_PRELOADED, LOGGER,
                                  MEMCACHE_PORT, PRELOAD_TRIES, VOLTYPES, and the
                                  one the interpreter supplies, __name__
      class attributes WRITTEN    CACHE, DEFAULT_CACHING, FS_IS_CASE_INSENSITIVE,
                                  LOCAL_PRELOADED, MEMCACHE_PORT. The first, the
                                  fourth and the fifth are read as well as written
      lazy properties read        childnames, is_bundleset, is_category_dir, isdir
      instance attributes read    abspath, interior, logical_path
      instance attributes WRITTEN permanent, on every directory preload visits;
                                  and _childnames_filled, whose list is mutated in
                                  place when a child turns out to be out of place
      other methods called        child, from_abspath, new_merged_dir

    Every one of those is defined on PdsFile itself rather than only on Pds3File
    and Pds4File, which is what makes cache_category_merged_dirs work on the bare
    class: pdsfile.py calls it at the foot of that file, and each subclass
    package calls it again at the foot of its own. Two more
    come from a sibling mixin: os_path_exists and os_path_isdir from
    _LocalFsMixin. All of them are attribute lookups on cls or on a PdsFile object
    at run time, not imports, which is what lets the layers live in different
    modules.

    preload decides whether to look for _volinfo by comparing cls.__name__ against
    'Pds4File' -- the name, not the class object, the same way _index_rows.py
    reads __bases__[0].__name__ -- so nothing here has to import pdsfile.pdsfile.

    The memcached half of preload runs only when pylibmc is importable and either
    the port argument or the class's MEMCACHE_PORT is non-zero -- the second
    disjunct matters, because preload writes the port it was given back onto the
    class, so a later argumentless call still takes the memcached path. Neither
    condition holds in this repo's test environment, so MemcachedCache, the
    PRELOAD_TRIES retry loop, pylibmc.Error and DEFAULT_CACHING = 'all' are
    reached by no test here; they are live in deployment, where Viewmaster passes
    port=.

    The case-sensitivity test preload runs at the end works by capitalizing the
    substring "/holdings" in each preloaded path and asking whether the result
    still exists. A holdings directory whose path does not contain that exact
    substring is therefore compared against itself, which always exists, so the
    class is marked case-insensitive whatever the filesystem is. The PDS4 tree,
    conventionally at a path ending "pds4-holdings", is such a case.
    """

    ############################################################################
    # Preload management
    ############################################################################
    @classmethod
    def get_permanent_values(cls, holdings_list, port):
        """Re-read the entries that are supposed to be permanent, and repair the cache
        if any is gone.

        A shared memcached can lose entries that were meant to last -- it can be trimmed,
        restarted, or written by another program -- and a cache missing one of them
        answers wrongly rather than slowly. So every one is read back: the version rank
        and directory tables for each category, each category directory itself, each
        bundle set inside it, and each bundle inside that. Names ending ``.txt`` or
        ``.tar.gz`` are not directories and are skipped.

        Two of the values are used to drive the walk: the category directory supplies the
        bundle sets to visit, and each bundle set supplies its bundles. The rank and
        version tables and the bundle-level entry are read and discarded. What matters
        for all of them is whether the read succeeds: the first one that does not
        triggers a warning and a fresh preload of the whole holdings list. Caching is
        paused around the reads, so re-reading does not itself cost writes, and is
        resumed however the call ends.

        Where every read succeeds, the count that is logged is taken from the cache's
        ``permanent_values``, which only a memcached cache has, so the whole-success path
        raises AttributeError on a dictionary cache. ``preload()`` reaches this method
        only when the class carries a non-zero memcached port; a direct call carries no
        such guard, and the ``port`` argument is passed on rather than checked.

        Parameters:
            holdings_list: the holdings directories to preload again if a value is
                missing, in whatever form ``preload()`` accepts.
            port (int): the memcached port to preload with.
        """

        try:
            pause_caching(cls)

            # For each category...
            for category in cls.CATEGORY_LIST:

                # Get the cached values
                _ = cls.CACHE['$RANKS-' + category + '/']
                _ = cls.CACHE['$VOLS-'  + category + '/']
                pdsf0 = cls.CACHE[category]

                # Also get the bundleset-level PdsFile inside each category
                for bundleset in pdsf0.childnames:
                    if bundleset.endswith('.txt') or bundleset.endswith('.tar.gz'):
                        continue
                    # Get the entry keyed by the logical path
                    pdsf1 = cls.CACHE[category + '/' + bundleset.lower()]

                    # Also get its bundle-level children
                    for bundlename in pdsf1.childnames:
                        if bundlename.endswith('.txt') or bundlename.endswith('.tar.gz'):
                            continue

                        key = (pdsf1.logical_path + '/' + bundlename).lower()
                        # The value is not needed; the lookup is a presence
                        # probe whose KeyError triggers the reload below.
                        _ = cls.CACHE[key]

        except KeyError as e:
            cls.LOGGER.warn('Permanent value %s missing from Memcache; '
                            'preloading again', str(e))
            cls.preload(holdings_list, port, force_reload=True)

        else:
            cls.LOGGER.info('Permanent values retrieved from Memcache',
                        str(len(cls.CACHE.permanent_values)))

        finally:
            resume_caching(cls)

    @classmethod
    def load_volume_info(cls, holdings):
        """Load bundle info associated with this holdings directory.

        Each record contains a sequence of values separated by "|"::

            key: bundleset, bundleset/bundlename, category/bundleset, or
                 category/bundleset/bundlename
            description
            icon_type or blank for default
            version ID or a string of dashes "-" if not applicable
            publication date or a string of dashes "-" if not applicable
            data set ID (if any) or MD5 checksum if this is in the documents/ tree
            additional data set IDs (if any)

        This creates and caches a dictionary based on the key identified above. Each
        entry is a tuple with six elements::

            description,
            icon_type or None for default,
            version ID or None,
            publication date or None,
            list of data set IDs,
            MD5 checksum or ''

        An icon_type that is empty or contains only dashes "-" is replaced by None, and
        so is a version ID or a publication date that contains only dashes. An empty
        version ID, an empty publication date and an empty data set ID stay empty
        strings.

        Blank records and those beginning with "#" are ignored. Every ``.txt`` file
        directly inside the ``_volinfo`` directory is read, and files whose names begin
        with a period are skipped.

        A record with no data set IDs of its own inherits them from the same bundle in
        another category: the bundle set name is reduced to its first two underscore-
        separated parts, and the entry for that bundle with no category, and then the one
        under ``volumes/``, are tried in turn. Only records whose category is a known
        volume type are given this treatment.

        Every entry is written to the cache with a lifetime of zero, so the descriptions
        never expire.

        Parameters:
            holdings (str): the path of the holdings directory whose ``_volinfo``
                directory to read.

        Raises:
            OSError: raised by ``listdir()`` if the holdings directory has no
                ``_volinfo`` directory, and by ``open()`` if a table disappears between
                the listing and the read.
        """

        volinfo_path = _clean_join(holdings, '_volinfo')

        volinfo_dict = {}           # the master dictionary of high-level paths vs.
                                    # (description, icon_type, version ID,
                                    #  publication date, optional list of data set
                                    #  IDs, optional checksum)

        keys_without_dsids = []     # internal list of entries without data set IDs
        dsids_vs_key = {}           # global dictionary of data set IDs for entries
                                    # that have them

        # For each file in the volinfo subdirectory...
        children = os.listdir(volinfo_path)
        for child in children:

            # Ignore these
            if child.startswith('.'):
                continue
            if not child.endswith('.txt'):
                continue

            # Read the file
            table_path = _clean_join(volinfo_path, child)
            with open(table_path, encoding='utf-8') as f:
                recs = f.readlines()

            # Interpret each record...
            for rec in recs:
                if rec[0] == '#':
                    continue                        # ignore comments

                parts = rec.split('|')              # split by "|"
                parts = [p.strip() for p in parts]  # remove extraneous blanks
                if parts == ['']:
                    continue                        # ignore blank lines

                # Identify missing info
                while len(parts) <= 5:
                    parts.append('')

                if parts[2] == '' or set(parts[2]) == {'-'}:
                    parts[2] = None
                if set(parts[3]) == {'-'}:
                    parts[3] = None
                if set(parts[4]) == {'-'}:
                    parts[4] = None

                if (parts[0].startswith('documents/') or
                    parts[0].rpartition('/')[2] in cls.EXTRA_README_BASENAMES):
                    md5 = parts[5]
                    dsids = []
                else:
                    md5 = ''
                    dsids = list(parts[5:])

                # Update either keys_without_dsids or dsids_vs_key. This is used
                # to fill in data set IDs for voltypes other than "volumes/".
                if dsids == ['']:
                    dsids = []

                if dsids:
                    dsids_vs_key[parts[0]] = dsids
                else:
                    keys_without_dsids.append(parts[0])

                # Fill in the master dictionary
                volinfo = (parts[1], parts[2], parts[3], parts[4], dsids, md5)
                volinfo_dict[parts[0]] = volinfo

        # Update the list of data set IDs wherever it's missing
        for key in keys_without_dsids:
            (category, _, remainder) = key.partition('/')
            if category in cls.VOLTYPES:
                (volset_with_suffix, _, remainder) = remainder.partition('/')
                bundleset = '_'.join(volset_with_suffix.split('_')[:2])
                alt_keys = (bundleset + '/' + remainder,
                            'volumes/' + bundleset + '/' + remainder)
                for alt_key in alt_keys:
                    if alt_key in dsids_vs_key:
                        volinfo_dict[key] = (volinfo_dict[key][:4] +
                                            (dsids_vs_key[alt_key],
                                            volinfo_dict[key][5]))
                        break

        # Save the master dictionary in the cache now
        for key,volinfo in volinfo_dict.items():
            cls.CACHE.set('$VOLINFO-' + key.lower(), volinfo, lifetime=0)

        cls.LOGGER.info('Volume info loaded', volinfo_path)

    @classmethod
    def cache_category_merged_dirs(cls):
        """Create the merged directory for each category that has none yet.

        A merged directory is one cache entry per category whose children are the union
        of that category's children across every holdings directory, which is what makes
        several physical trees look like one. They are stored with a lifetime of zero, so
        they never expire.

        A category that already has an entry is left alone, so this can be called at any
        time and will not discard a merged directory a preload has already filled.
        ``preload()`` does not go through this method: it overwrites every category's
        entry itself.
        """

        for category in cls.CATEGORY_LIST:
            if category not in cls.CACHE:
                cls.CACHE.set(category, cls.new_merged_dir(category), lifetime=0)

    @classmethod
    def preload(cls, holdings_list, port=0, clear=False, force_reload=False,
                icon_url=None, icon_color='blue'):
        """Fill the cache from one or more holdings directories.

        The cache implementation is chosen first. A memcached cache is used when pylibmc
        imported and a non-zero port is available, either from the argument or from a
        port a previous call recorded on the class; a failure to connect is retried, with
        the wait doubling each time, and a dictionary cache is used if the tries run out.
        Anything else uses a dictionary cache. Which one is chosen also sets the default
        caching policy, since only a shared cache is worth filling with everything. A
        dictionary cache is constructed only where the cache in place is not already one,
        and it is given ``cache_lifetime()`` as its default; that is a class method, which
        such a cache keeps as a constant rather than calling, so its first store that
        needs the default raises TypeError.

        Then the holdings list is compared with what has already been loaded. Nothing to
        do means returning early, after re-reading the permanent values on a memcached
        cache in case any has been lost. Otherwise the cache is blocked against other
        processes and paused against its own writes for the duration.

        The walk itself creates the category-level merged directories and the empty rank
        and version tables, then, per holdings directory, reads the bundle descriptions,
        descends each category directory as far as its bundle sets, and loads the icons.
        Everything it caches is permanent. A child that cannot be constructed is dropped
        from its parent's child list rather than reported. A category directory that is
        missing is warned about and skipped. **One that exists but is not a directory is
        warned about as ignored and is not ignored**: that branch has no skip, so the
        path is constructed, cached permanently, and merged into the category-level
        merged directory's child list. Nothing below it is walked, because the walk
        returns at once on anything that is not a directory.

        The list of preloaded holdings is written, the pause lifted and the block
        released however the walk ends, so a failure part way through does not leave the
        cache blocked.

        Last, the class is marked according to whether its filesystem is case-sensitive,
        by the test the class docstring describes.

        Parameters:
            holdings_list: one absolute path to a holdings directory, or a list or tuple
                of them. Each is resolved against the working directory and written with
                forward slashes.
            port (int): the memcached port. Zero asks for a dictionary cache, unless the
                class already carries a port from an earlier call.
            clear (bool): whether to empty the cache first, holding the block from then
                until the preload finishes.
            force_reload (bool): whether to walk the holdings again even if they are
                recorded as already loaded.
            icon_url: the URL root the icons are served from. None builds one per
                holdings directory, ``/holdings/_icons`` for the first and
                ``/holdings<n>/_icons`` for the rest.
            icon_color (str): which color set of icons to load.
        """

        # Convert holdings to a list of absolute paths
        if not isinstance(holdings_list, (list,tuple)):
            holdings_list = [holdings_list]

        holdings_list = [_clean_abspath(h) for h in holdings_list]

        # Use cache as requested
        if (port == 0 and cls.MEMCACHE_PORT == 0) or not HAS_PYLIBMC:
            if not isinstance(cls.CACHE, pdscache.DictionaryCache):
                cls.CACHE = pdscache.DictionaryCache(lifetime=cls.cache_lifetime,
                                                     limit=cls.DICTIONARY_CACHE_LIMIT,
                                                     logger=cls.LOGGER)
            cls.LOGGER.info('Using local dictionary cache')

        else:
            cls.MEMCACHE_PORT = cls.MEMCACHE_PORT or port

            for k in range(cls.PRELOAD_TRIES):
                try:
                    cls.CACHE = pdscache.MemcachedCache(cls.MEMCACHE_PORT,
                                                        lifetime=cls.cache_lifetime,
                                                        logger=cls.LOGGER)
                    cls.LOGGER.info('Connecting to PdsFile Memcache [%s]',
                                    cls.MEMCACHE_PORT)
                    break

                except pylibmc.Error:
                    if k < cls.PRELOAD_TRIES - 1:
                        cls.LOGGER.warn(('Failed to connect PdsFile Memcache [%s]; ' +
                                         'trying again in %d sec') %
                                        (cls.MEMCACHE_PORT, 2**k))
                        time.sleep(2.**k)       # try then wait 1 sec, then 2 sec

                    else:       # give up after three tries
                        cls.LOGGER.error(('Failed to connect PdsFile Memcache [%s]; '+
                                          'using dictionary instead') %
                                         cls.MEMCACHE_PORT)

                        cls.MEMCACHE_PORT = 0
                        if not isinstance(cls.CACHE, pdscache.DictionaryCache):
                            cls.CACHE = pdscache.DictionaryCache(
                                            lifetime=cls.cache_lifetime,
                                            limit=cls.DICTIONARY_CACHE_LIMIT,
                                            logger=cls.LOGGER
                                        )

        # Define default caching based on whether MemCache is active
        if cls.MEMCACHE_PORT == 0:
            cls.DEFAULT_CACHING = 'dir'
        else:
            cls.DEFAULT_CACHING = 'all'

        # This suppresses long absolute paths in the logs
        cls.LOGGER.add_root(holdings_list)

        #### Get the current list of preloaded holdings directories and decide how
        #### to proceed

        if clear:
            cls.CACHE.clear(block=True) # For a MemcachedCache, this will pause for any
                                    # other thread's block, then clear, and retain
                                    # the block until the preload is finished.
            cls.LOCAL_PRELOADED = []
            cls.LOGGER.info('Cache cleared')

        elif force_reload:
            cls.LOCAL_PRELOADED = []
            cls.LOGGER.info('Forcing a complete new preload')
            cls.CACHE.wait_and_block()

        else:
            while True:
                cls.LOCAL_PRELOADED = cls.CACHE.get_now('$PRELOADED') or []

                # Report status
                something_is_missing = False
                for holdings in holdings_list:
                    if holdings in cls.LOCAL_PRELOADED:
                        cls.LOGGER.info('Holdings are already cached', holdings)
                    else:
                        something_is_missing = True

                if not something_is_missing:
                    if cls.MEMCACHE_PORT:
                        cls.get_permanent_values(holdings_list, cls.MEMCACHE_PORT)
                        # Note that if any permanently cached values are missing,
                        # this call will recursively clear the cache and preload
                        # again. This reduces the chance of a corrupted cache.

                    return

                waited = cls.CACHE.wait_and_block()
                if not waited:      # A wait suggests the answer might have changed,
                                    # so try again.
                    break

                cls.CACHE.unblock()

        # At this point, the cache is blocked.

        # Pause the cache before proceeding--saves I/O
        cls.CACHE.pause()       # Paused means no local changes will be flushed to the
                            # external cache until resume() is called.

        ########################################################################
        # Interior function to recursively preload one physical directory
        ########################################################################

        def _preload_dir(pdsdir, cls):
            """Cache one directory and, if it is shallow enough, its children.

            The walk stops below the bundle set: a category directory and a bundle set
            are descended into, and anything else returns at once, which is what keeps
            the preload from reading the whole tree. Each directory it does visit is
            marked permanent, so it is never trimmed.

            A child whose construction raises is taken to be a file that does not belong
            where it is, and is **removed from its parent's child list**, so the cached
            listing does not show it.

            Parameters:
                pdsdir: the directory to cache.
                cls: the PdsFile subclass the walk is being done for.
            """

            if not pdsdir.isdir:
                return

            # Log category directories as info
            if pdsdir.is_category_dir:
                cls.LOGGER.info('Pre-loading: ' + pdsdir.abspath)

            # Log bundlesets as debug
            elif pdsdir.is_bundleset:
                cls.LOGGER.debug('Pre-loading: ' + pdsdir.abspath)

            # Don't go deeper
            else:
                return

            # Preloaded dirs are permanent
            pdsdir.permanent = True

            # Make recursive calls and cache
            for basename in list(pdsdir.childnames):
                try:
                    child = pdsdir.child(basename, fix_case=False, lifetime=0)
                    _preload_dir(child, cls)
                except ValueError:              # Skip out-of-place files
                    pdsdir._childnames_filled.remove(basename)

        #### Fill CACHE

        try:    # we will undo the pause and block in the "finally" clause below

            # Create and cache permanent, category-level merged directories. These
            # are roots of the cache tree and their list of children is merged from
            # multiple physical directories. This makes it possible for our data
            # sets to exist on multiple physical drives in a way that is invisible
            # to the user.
            for category in cls.CATEGORY_LIST:
                cls.CACHE.set(category, cls.new_merged_dir(category), lifetime=0)

            # Initialize RANKS, VOLS and category list
            for category in cls.CATEGORY_LIST:
                category_ = category + '/'
                key = '$RANKS-' + category_
                try:
                    _ = cls.CACHE[key]
                except KeyError:
                    cls.CACHE.set(key, {}, lifetime=0)

                key = '$VOLS-'  + category_
                try:
                    _ = cls.CACHE[key]
                except KeyError:
                    cls.CACHE.set(key, {}, lifetime=0)

            # Cache all of the top-level PdsFile directories
            for h,holdings in enumerate(holdings_list):

                if holdings in cls.LOCAL_PRELOADED:
                    cls.LOGGER.info('Pre-load not needed for ' + holdings)
                    continue

                cls.LOCAL_PRELOADED.append(holdings)
                cls.LOGGER.info('Pre-loading ' + holdings)

                # Load volume info
                # PDS4 will ignore _volinfo directory
                if cls.__name__ != 'Pds4File':
                    cls.load_volume_info(holdings)

                # Load directories starting from here
                holdings_ = holdings.rstrip('/') + '/'

                for c in cls.CATEGORY_LIST:
                    category_abspath = holdings_ + c
                    if not cls.os_path_exists(category_abspath):
                        cls.LOGGER.warn('Missing category dir: ' + category_abspath)
                        continue
                    if not cls.os_path_isdir(category_abspath):
                        cls.LOGGER.warn('Not a directory, ignored: ' + category_abspath)

                    # This is a physical PdsFile, but from_abspath also adds its
                    # childnames to the list of children for the category-level
                    # merged directory.
                    pdsdir = cls.from_abspath(category_abspath, fix_case=False,
                                                caching='all', lifetime=0)
                    _preload_dir(pdsdir, cls)

                # Load the icons
                icon_path = _clean_join(holdings, '_icons')
                if os.path.exists(icon_path):
                    final_icon_url = icon_url
                    if final_icon_url is None:
                        final_icon_url = '/holdings' + (str(h) if h > 0 else '') + '/_icons'
                    pdsviewable.load_icons(icon_path, final_icon_url, icon_color,
                                           cls.LOGGER)

        finally:
            cls.CACHE.set('$PRELOADED', cls.LOCAL_PRELOADED, lifetime=0)
            cls.CACHE.resume()
            cls.CACHE.unblock(flush=True)

        cls.LOGGER.info('PdsFile preloading completed')

        # Determine if the file system is case-sensitive
        # If any physical bundle is case-insensitive, then we treat the whole file
        # system as case-insensitive.
        cls.FS_IS_CASE_INSENSITIVE = False
        for holdings_dir in cls.LOCAL_PRELOADED:
            testfile = holdings_dir.replace('/holdings', '/HoLdInGs')
            if os.path.exists(testfile):
                cls.FS_IS_CASE_INSENSITIVE = True
                break

    @classmethod
    def cache_lifetime(cls, arg):
        """Return how long an object should be kept in this class's cache, in seconds.

        This is what ``preload()`` hands a cache it builds as that cache's default
        lifetime. It is the module-level rule with this class supplied, so an object that
        is not an instance of this class is treated as a bookkeeping entry and kept
        forever.

        It is a class method rather than a plain function. A memcached cache accepts that
        as a lifetime function; a dictionary cache does not, and keeps it as a constant
        default, so the first store into such a cache that needs the default raises
        TypeError.

        Parameters:
            arg: the object about to be cached.

        Returns:
            int: the lifetime in seconds, or zero for forever.
        """

        return cache_lifetime_for_class(arg, cls)
