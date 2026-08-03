##########################################################################################
# pdsfile/preload_and_cache.py
# Compatibility re-exports. The preload machinery lives in pdsfile/_preload.py; every
# name this module has always exported still resolves here. The redundant `as` alias is
# the explicit re-export form, so these do not read as unused imports.
##########################################################################################

from ._preload import DEFAULT_FILE_CACHE_LIFETIME as DEFAULT_FILE_CACHE_LIFETIME
from ._preload import DICTIONARY_CACHE_LIMIT as DICTIONARY_CACHE_LIMIT
from ._preload import FOEVER_FILE_CACHE_LIFETIME as FOEVER_FILE_CACHE_LIFETIME
from ._preload import LONG_FILE_CACHE_LIFETIME as LONG_FILE_CACHE_LIFETIME
from ._preload import SHORT_FILE_CACHE_LIFETIME as SHORT_FILE_CACHE_LIFETIME
from ._preload import cache_lifetime_for_class as cache_lifetime_for_class
from ._preload import is_preloading as is_preloading
from ._preload import pause_caching as pause_caching
from ._preload import resume_caching as resume_caching
