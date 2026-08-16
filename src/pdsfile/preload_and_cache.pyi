"""Type stubs for ``pdsfile.preload_and_cache`` (see the module docstring there).

The implementation is unannotated (modernization ground rule 5); these stubs
declare the public surface frozen in ``tests/api/api_manifest.json``: the nine
public names of the preload subsystem, re-exported at runtime from the private
module ``pdsfile._preload`` and typed here at their definitions.
"""

from typing import Any

from pdsfile.pdsfile import PdsFile

DEFAULT_FILE_CACHE_LIFETIME: int
DICTIONARY_CACHE_LIMIT: int
FOEVER_FILE_CACHE_LIFETIME: int
LONG_FILE_CACHE_LIFETIME: int
SHORT_FILE_CACHE_LIFETIME: int

def cache_lifetime_for_class(arg: Any, cls: type[PdsFile] | None = None) -> int: ...

# The '$PRELOADING' cache entry is written by nothing in this package, so the
# answer is whatever an external caller stored (None when nothing did).
def is_preloading(cls: type[PdsFile]) -> Any: ...
def pause_caching(cls: type[PdsFile]) -> None: ...
def resume_caching(cls: type[PdsFile]) -> None: ...
