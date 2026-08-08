##########################################################################################
# pds3file/rules/ASTROM_xxxx.py
##########################################################################################

"""Rules for the ASTROM_xxxx volume set: HST WFPC2 astrometry of Saturn's moons.

ASTROM_xxxx is described in the holdings as a satellite astrometry collection. Its
two volumes are ASTROM_0001, "HST WFPC2 astrometry of Saturn's moons, 1994-2002",
and ASTROM_0101, the same for 1996-2005 (holdings ``_volinfo/ASTROM_xxxx.txt``).

`ASTROM_xxxx.py` defines one rule table, because everything else about this volume
set is covered by the defaults in `pds3file/rules/__init__.py`:

* ``filespec_to_bundleset`` -- maps a file specification beginning with an
  ASTROM_nnnn volume ID to the volume set name ASTROM_xxxx.

The class body puts ASTROM_xxxx in front of ``Pds3File.VOLSET_TRANSLATOR``, and the
module tail registers the subclass in ``Pds3File.SUBCLASSES``.
"""

import re

import translator

import pdsfile.pds3file as pds3file

##########################################################################################
# FILESPEC_TO_BUNDLESET
##########################################################################################

filespec_to_bundleset = translator.TranslatorByRegex([
    (r'ASTROM_\d{4}.*', 0, r'ASTROM_xxxx'),
])

##########################################################################################
# Subclass definition
##########################################################################################

class ASTROM_xxxx(pds3file.Pds3File):
    """The ``Pds3File`` subclass for ASTROM_xxxx.

    The class body puts this module's rule tables in front of the class attributes
    ``Pds3File`` reads, and the module tail registers the class in
    ``Pds3File.SUBCLASSES`` under the key "ASTROM_xxxx".
    The module docstring describes the volume set and every table.
    """

    pds3file.Pds3File.VOLSET_TRANSLATOR = translator.TranslatorByRegex([('ASTROM_xxxx', re.I, 'ASTROM_xxxx')]) + \
                                          pds3file.Pds3File.VOLSET_TRANSLATOR

pds3file.Pds3File.FILESPEC_TO_BUNDLESET = filespec_to_bundleset + pds3file.Pds3File.FILESPEC_TO_BUNDLESET

##########################################################################################
# Update the global dictionary of subclasses
##########################################################################################

pds3file.Pds3File.SUBCLASSES['ASTROM_xxxx'] = ASTROM_xxxx

##########################################################################################
