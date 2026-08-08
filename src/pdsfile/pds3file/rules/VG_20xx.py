##########################################################################################
# pds3file/rules/VG_20xx.py
##########################################################################################

"""Rules for the VG_20xx volume set: selected Voyager IRIS thermal infrared data.

VG_20xx is described in the holdings as selected Voyager IRIS thermal infrared data,
original release. The one volume, VG_2001, carries four data set IDs, one each for
the Jupiter, Saturn, Uranus and Neptune encounters of Voyager 1 and Voyager 2
(holdings ``_volinfo/VG_20xx.txt``).

The rule tables:

* ``description_and_icon_by_regex`` -- names the directories of the volume, which
  are split first by planet and then by spacecraft, so that a directory reads as
  "Voyager 2 Uranus data" rather than as a bare code.
* ``filespec_to_bundleset`` -- maps a file specification beginning with a VG_20nn
  volume ID to the volume set name VG_20xx, which the default rule cannot do because
  this volume set name ends in two x's rather than three.

`VGIRIS_xxxx.py` covers the extended IRIS collection restored from the original
tapes and defines tables of these same two names for it.
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
    (r'VG_20\d{2}.*', 0, r'VG__20xx'),
])

##########################################################################################
# Subclass definition
##########################################################################################

class VG_20xx(pds3file.Pds3File):
    """The ``Pds3File`` subclass for VG_20xx.

    The class body puts this module's rule tables in front of the class attributes
    ``Pds3File`` reads, and the module tail registers the class in
    ``Pds3File.SUBCLASSES`` under the key "VG_20xx".
    The module docstring describes the volume set and every table.
    """

    pds3file.Pds3File.VOLSET_TRANSLATOR = translator.TranslatorByRegex([('VG_20xx', re.I, 'VG_20xx')]) + \
                                          pds3file.Pds3File.VOLSET_TRANSLATOR

    DESCRIPTION_AND_ICON = description_and_icon_by_regex + pds3file.Pds3File.DESCRIPTION_AND_ICON

pds3file.Pds3File.FILESPEC_TO_BUNDLESET = filespec_to_bundleset + pds3file.Pds3File.FILESPEC_TO_BUNDLESET

##########################################################################################
# Update the global dictionary of subclasses
##########################################################################################

pds3file.Pds3File.SUBCLASSES['VG_20xx'] = VG_20xx

##########################################################################################
