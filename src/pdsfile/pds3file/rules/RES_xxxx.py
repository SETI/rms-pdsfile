##########################################################################################
# pds3file/rules/RES_xxxx.py
##########################################################################################

"""Rules for the RES_xxxx volume set: resonance calculations for the Saturn system.

RES_xxxx holds derived resonance calculations. The one volume, RES_0001, is
described as "Resonance calculations for the Saturn system", carries data set ID
SR-5-DDR-RESONANCES-V0.9, and sits under the volume set name RES_xxxx_prelim
(holdings ``_volinfo/RES_xxxx.txt``).

`RES_xxxx.py` defines no rule tables at all. The whole module is the subclass
declaration: it puts RES_xxxx in front of ``Pds3File.VOLSET_TRANSLATOR`` so that a
path under this volume set resolves to this class, and registers the class in
``Pds3File.SUBCLASSES``. Every rule the class uses is the default from
`pds3file/rules/__init__.py`.
"""

import re

import translator

import pdsfile.pds3file as pds3file

##########################################################################################
# Subclass definition
##########################################################################################

class RES_xxxx(pds3file.Pds3File):
    """The ``Pds3File`` subclass for RES_xxxx.

    The class body puts this module's rule tables in front of the class attributes
    ``Pds3File`` reads, and the module tail registers the class in
    ``Pds3File.SUBCLASSES`` under the key "RES_xxxx".
    The module docstring describes the volume set and every table.
    """

    pds3file.Pds3File.VOLSET_TRANSLATOR = translator.TranslatorByRegex([('RES_xxxx', re.I, 'RES_xxxx')]) + \
                                          pds3file.Pds3File.VOLSET_TRANSLATOR

##########################################################################################
# Update the global dictionary of subclasses
##########################################################################################

pds3file.Pds3File.SUBCLASSES['RES_xxxx'] = RES_xxxx

##########################################################################################
