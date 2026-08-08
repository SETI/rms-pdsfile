##########################################################################################
# pds3file/rules/VGIRIS_xxxx.py
##########################################################################################

"""Rules for the VGIRIS_xxxx volume set: extended Voyager IRIS thermal infrared data.

VGIRIS_xxxx is described in the holdings as the Voyager IRIS thermal infrared
extended collection from the original tapes. Its two volumes are VGIRIS_0001 for
Jupiter and VGIRIS_0002 for Saturn, both carrying data set ID
VG1/VG2-J/S-IRIS-3-RDR-EXPANDED-V1.0, and both under the volume set name
VGIRIS_xxxx_peer_review (holdings ``_volinfo/VGIRIS_xxxx.txt``).

The rule tables:

* ``description_and_icon_by_regex`` -- names data files by spacecraft and planet, so
  that ``VG2_NEP.DAT`` reads as "Voyager 2 Neptune data", and carries four bare
  planet directory patterns. Those four do not fire on this volume set: its
  directories are named for planet and spacecraft together, as in
  ``DATA/JUPITER_VG1``, and every pattern in a ``TranslatorByRegex`` is anchored at
  both ends, so they fall through to the default "Data files".
* ``filespec_to_bundleset`` -- maps a file specification beginning with a
  VGIRIS_nnnn volume ID to the volume set name VGIRIS_xxxx_peer_review, which is the
  name the volumes actually sit under.

`VG_20xx.py` covers the original selected-data release from the same instrument and
defines tables of these same two names for it.
"""

import re

import translator

import pdsfile.pds3file as pds3file

##########################################################################################
# DESCRIPTION_AND_ICON
##########################################################################################

description_and_icon_by_regex = translator.TranslatorByRegex([
    (r'.*/JUPITER', re.I, ('Jupiter data', 'DATADIR')),
    (r'.*/SATURN',  re.I, ('Saturn data',  'DATADIR')),
    (r'.*/URANUS',  re.I, ('Uranus data',  'DATADIR')),
    (r'.*/NEPTUNE', re.I, ('Neptune data', 'DATADIR')),

    (r'.*VG1_JUP\.DAT', re.I, ('Voyager 1 Jupiter data', 'DATA')),
    (r'.*VG2_JUP\.DAT', re.I, ('Voyager 2 Jupiter data', 'DATA')),
    (r'.*VG1_SAT\.DAT', re.I, ('Voyager 1 Saturn data',  'DATA')),
    (r'.*VG2_SAT\.DAT', re.I, ('Voyager 2 Saturn data',  'DATA')),
    (r'.*VG2_URA\.DAT', re.I, ('Voyager 2 Uranus data',  'DATA')),
    (r'.*VG2_NEP\.DAT', re.I, ('Voyager 2 Neptune data', 'DATA')),
])

##########################################################################################
# FILESPEC_TO_BUNDLESET
##########################################################################################

filespec_to_bundleset = translator.TranslatorByRegex([
    (r'VGIRIS_\d{4}.*', 0, 'VGIRIS_xxxx_peer_review'),
])

##########################################################################################
# Subclass definition
##########################################################################################

class VGIRIS_xxxx(pds3file.Pds3File):
    """The ``Pds3File`` subclass for VGIRIS_xxxx.

    The class body wires this module's rule tables onto the class attributes
    ``Pds3File`` reads. Where a table is added to the inherited one, a lookup tries
    this module's patterns first and falls through to the defaults; where it is
    assigned outright there is no fall-through. The module tail registers the class
    in ``Pds3File.SUBCLASSES`` under the key
    "VGIRIS_xxxx". The module docstring describes the volume set and every table.
    """

    pds3file.Pds3File.VOLSET_TRANSLATOR = translator.TranslatorByRegex([('VGIRIS_xxxx', re.I, 'VGIRIS_xxxx')]) + \
                                          pds3file.Pds3File.VOLSET_TRANSLATOR

    DESCRIPTION_AND_ICON = description_and_icon_by_regex + pds3file.Pds3File.DESCRIPTION_AND_ICON

pds3file.Pds3File.FILESPEC_TO_BUNDLESET = filespec_to_bundleset + pds3file.Pds3File.FILESPEC_TO_BUNDLESET

##########################################################################################
# Update the global dictionary of subclasses
##########################################################################################

pds3file.Pds3File.SUBCLASSES['VGIRIS_xxxx'] = VGIRIS_xxxx

##########################################################################################
