##########################################################################################
# pdsfile/__init__.py
##########################################################################################

try:
    from ._version import __version__
except ImportError:
    __version__ = 'Version unspecified'

# Re-exported so callers can write `pdsfile.PdsFile`. The redundant alias marks
# the import as intentional; the name is not referenced below.
from pdsfile.pdsfile import PdsFile as PdsFile

from .pds3file import *
from .pds4file import *
