##########################################################################################
# pdsfile/_preload.py
# Preload management: the cache the PdsFile classes share, the lifetimes it assigns,
# and the traversal that fills it from one or more holdings directories
##########################################################################################

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
    """Return the default cache lifetime in seconds with a given object. A returned
    lifetime of zero means keep forever.

    Keyword arguments:
        arg -- an object
        cls -- the class calling the method (default True)
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
    return cls.CACHE.get_now('$PRELOADING')

def pause_caching(cls):
    cls.CACHE.pause()

def resume_caching(cls):
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
    be permanent and preloads again if any has gone missing. cache_lifetime is the
    per-object lifetime function preload hands to a cache it creates, and it
    delegates to the module-level cache_lifetime_for_class above.

    Every attribute these methods read or write on a PdsFile object or on a
    PdsFile class, and nothing else -- str, list, dict, file, os, os.path,
    pdscache, pdsviewable, pylibmc, time and logger methods are not in scope:

      class attributes read       CATEGORY_LIST, DICTIONARY_CACHE_LIMIT,
                                  EXTRA_README_BASENAMES, LOGGER, PRELOAD_TRIES,
                                  VOLTYPES, and the one the interpreter supplies,
                                  __name__
      class attributes WRITTEN    CACHE, DEFAULT_CACHING, FS_IS_CASE_INSENSITIVE,
                                  LOCAL_PRELOADED, MEMCACHE_PORT
      lazy properties read        childnames, is_bundleset, is_category_dir, isdir
      instance attributes read    abspath, logical_path
      instance attributes WRITTEN permanent, on every directory preload visits;
                                  and _childnames_filled, whose list is mutated in
                                  place when a child turns out to be out of place
      other methods called        child, from_abspath, new_merged_dir

    Every one of those is defined on PdsFile itself rather than only on Pds3File
    and Pds4File, which is what makes the module tail's PdsFile.cache_category_merged_dirs()
    call work on the bare class at import time. Two more come from a sibling
    mixin: os_path_exists and os_path_isdir from _LocalFsMixin. All of them are
    attribute lookups on cls or on a PdsFile object at run time, not imports,
    which is what lets the layers live in different modules.

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
    """

    ############################################################################
    # Preload management
    ############################################################################
    @classmethod
    def get_permanent_values(cls, holdings_list, port):
        """Load the most obvious set of permanent values from the cache to ensure
        we have current local copies.

        Keyword arguments:
            holdings_list -- the path of holdings dir that we will preload if the permanent
                            value from cache is missing
            port          -- value for the class attribute
            cls           -- the class calling the method
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

        Each record contains a sequence of values separated by "|":
            key: bundleset, bundleset/bundlename, category/bundleset, or
                 category/bundleset/bundlename
            description
            icon_type or blank for default
            version ID or a string of dashes "-" if not applicable
            publication date or a string of dashes "-" if not applicable
            data set ID (if any) or MD5 checksum if this is in the documents/ tree
            additional data set IDs (if any)

        This creates and caches a dictionary based on the key identified above. Each
        entry is a tuple with five elements:
            description,
            icon_type or blank for default,
            version ID or None,
            publication date or None,
            list of data set IDs,
            MD5 checksum or ''

        A value only containing a string of dashes "-" is replaced by None.
        Blank records and those beginning with "#" are ignored.

        Keyword arguments:
            holdings -- the path of the holdings directory
            cls      -- the class calling the method
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
        for category in cls.CATEGORY_LIST:
            if category not in cls.CACHE:
                cls.CACHE.set(category, cls.new_merged_dir(category), lifetime=0)

    @classmethod
    def preload(cls, holdings_list, port=0, clear=False, force_reload=False,
                icon_url=None, icon_color='blue'):
        """Cache the top-level directories, starting from the given holdings directories.

        Keyword arguments:
            holdings_list -- a single abslute path to a holdings directory, or else a list
                             of absolute paths
            port          -- port to use for memcached; zero to prevent use of memcached
            clear         -- True to clear the cache before preloading
            force_reload  -- Re-load the cache regardless of whether the cache appears to
                             contain the needed holdings
            icon_url      -- URL root to use for loading icons; defaults to
                             "/holdings/_icons" or "/holdings<n>/_icons" as needed
            icon_color    -- color of the icons to load from each holdings directory
                             (default 'blue')
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
                # A wait suggests the answer might have changed, so try again.
                if not waited:
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
        return cache_lifetime_for_class(arg, cls)
