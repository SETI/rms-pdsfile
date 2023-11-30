##########################################################################################
# pdsfile/preload_and_cache.py
# Store the code for preload management and cache
##########################################################################################

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
