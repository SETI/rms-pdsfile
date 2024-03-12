##########################################################################################
# pdsfile/__init__.py
##########################################################################################

try:
    from ._version import __version__
except ImportError as err:
    __version__ = 'Version unspecified'

from pdsfile import *
from .pds3file import *
from .pds4file import *
