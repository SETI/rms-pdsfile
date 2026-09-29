##########################################################################################
# pdsfile/__init__.py
##########################################################################################

"""Interface to the file system of a PDS holdings tree.

Importing this package binds three things into ``pdsfile``:

  * ``__version__``. It comes from the ``_version.py`` that ``setuptools_scm`` writes at
    build time; in a source tree with no build metadata that file is absent and the
    version reads ``'Version unspecified'``.
  * ``PdsFile``, the base class, which represents one file or directory in a holdings
    tree and is the entry point to almost everything the package does.
  * The public names of the ``pds3file`` and ``pds4file`` subpackages. Those include the
    two concrete classes ``Pds3File`` and ``Pds4File``, one per PDS version, and the
    per-bundleset rule modules each of them registers.

Choosing a class: ``Pds3File`` reads a PDS3 holdings tree, whose data live under
``volumes/``; ``Pds4File`` reads a PDS4 tree, whose data live under ``bundles/``. Each
locates its own tree through its own environment variable. ``PdsFile`` itself is
abstract in practice: it carries the shared behavior, but the configuration tables that
make path parsing work are filled in by the two subclasses.

Two module-level caches back the classes and are documented with them: ``pdscache``
holds the cache classes, and ``preload_and_cache`` holds the preload machinery that
fills a cache from a holdings tree.
"""

try:
    from ._version import __version__
except ImportError:
    __version__ = 'Version unspecified'

# Re-exported so callers can write `pdsfile.PdsFile`. The redundant alias marks
# the import as intentional; the name is not referenced below.
from pdsfile.pdsfile import PdsFile as PdsFile

from .pds3file import *
from .pds4file import *
