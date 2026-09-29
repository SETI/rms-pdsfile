##########################################################################################
# pdsfile/preload_and_cache.py
##########################################################################################

"""Public names of the preload subsystem.

The implementation lives in the private module ``pdsfile._preload``, which also holds
``_PreloadMixin`` and so is imported by ``pdsfile.pdsfile``. This module is the public
face of it: it binds the nine names a caller outside the package is meant to use, and
nothing else.

Three of them take a ``PdsFile`` subclass and act on the cache that class holds.
``pause_caching(cls)`` and ``resume_caching(cls)`` bracket a stretch of code during
which that cache should not trim or flush; the calls nest, so an inner pair does not
release an outer one. ``is_preloading(cls)`` reads the cache entry ``'$PRELOADING'``.
No code in this package writes that entry, so the call answers None unless something
outside the package has set it.

``cache_lifetime_for_class(arg, cls=None)`` is the lifetime function every cache in the
package is built with. Given the object about to be stored, it returns the number of
seconds that object should live: a string lives ``DEFAULT_FILE_CACHE_LIFETIME``; an
object that is not an instance of ``cls`` -- the bookkeeping dictionaries a preload
stores, when ``cls`` is supplied -- lives ``FOEVER_FILE_CACHE_LIFETIME``; a bundleset or
bundle, and a data directory inside a bundle, live ``LONG_FILE_CACHE_LIFETIME``; any
other directory lives ``SHORT_FILE_CACHE_LIFETIME``; and anything else lives
``DEFAULT_FILE_CACHE_LIFETIME``.

The four constants are ``DEFAULT_FILE_CACHE_LIFETIME``, 12 hours;
``LONG_FILE_CACHE_LIFETIME``, 7 days; ``SHORT_FILE_CACHE_LIFETIME``, 2 days; and
``FOEVER_FILE_CACHE_LIFETIME``, zero, which means the entry never expires.

``DICTIONARY_CACHE_LIMIT`` is 200000, the item limit a dictionary cache is built with.
The value each class actually passes is its own class attribute of the same name, so
rebinding this module's copy changes nothing.

The redundant ``as`` alias on each import below is the explicit re-export form, which
marks the binding as deliberate rather than as an unused import.
"""

from ._preload import DEFAULT_FILE_CACHE_LIFETIME as DEFAULT_FILE_CACHE_LIFETIME
from ._preload import DICTIONARY_CACHE_LIMIT as DICTIONARY_CACHE_LIMIT
from ._preload import FOEVER_FILE_CACHE_LIFETIME as FOEVER_FILE_CACHE_LIFETIME
from ._preload import LONG_FILE_CACHE_LIFETIME as LONG_FILE_CACHE_LIFETIME
from ._preload import SHORT_FILE_CACHE_LIFETIME as SHORT_FILE_CACHE_LIFETIME
from ._preload import cache_lifetime_for_class as cache_lifetime_for_class
from ._preload import is_preloading as is_preloading
from ._preload import pause_caching as pause_caching
from ._preload import resume_caching as resume_caching
