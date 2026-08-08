##########################################################################################
# pds3file/rules/COSP_xxxx.py
##########################################################################################

"""Rules for the COSP_xxxx volume set: Cassini SPICE kernels.

COSP_xxxx holds Cassini navigation and ancillary data in the form of SPICE kernels.
The one volume, COSP_1000, carries data set ID CO-S/J/E/V-SPICE-6-V1.0 (holdings
``_volinfo/COSP_xxxx.txt``). The RMS Node curates a companion document directory,
``documents/COSP_xxxx``, holding links to the SPICE Toolkit and to a Cassini kernel
selection tool.

The rule tables:

* ``associations_to_documents`` -- sends any path under ``volumes/COSP_xxxx`` to the
  curated ``documents/COSP_xxxx/`` directory.
* ``filespec_to_bundleset`` -- maps a file specification beginning with a COSP_nnnn
  volume ID to the volume set name COSP_xxxx.
* ``info_file_basenames`` -- makes ``aareadme.txt`` the information file for a
  directory here, in preference to the ``voldesc.cat`` the default table would pick.

`COSP_xxxx.py` is one of three SPICE-kernel rule modules that define the same three
tables; the others are `JNOSP_xxxx.py` for Juno and `NHSP_xxxx.py` for New Horizons.
"""

import re

import translator

import pdsfile.pds3file as pds3file

##########################################################################################
# ASSOCIATIONS
##########################################################################################

associations_to_documents = translator.TranslatorByRegex([
    (r'volumes/COSP_xxxx.*', 0,
        r'documents/COSP_xxxx/*'),
])

##########################################################################################
# FILESPEC_TO_BUNDLESET
##########################################################################################

filespec_to_bundleset = translator.TranslatorByRegex([
    (r'COSP_\d{4}.*', 0, r'COSP_xxxx'),
])

##########################################################################################
# INFO_FILE_BASENAMES
##########################################################################################

info_file_basenames = translator.TranslatorByRegex([
    (r'(aareadme\.txt)', re.I, r'\1'),      # this is the best choice, not voldesc.cat
])

##########################################################################################
# Subclass definition
##########################################################################################

class COSP_xxxx(pds3file.Pds3File):
    """The ``Pds3File`` subclass for COSP_xxxx.

    The class body and the module tail install this module's rule tables on the class
    attributes ``Pds3File`` reads. `pds3file/rules/__init__.py` sets out the routes a
    table takes and which of them leaves the inherited rules in front. The class
    is registered in ``Pds3File.SUBCLASSES`` under the key
    "COSP_xxxx".
    The module docstring describes the volume set and every table.
    """

    pds3file.Pds3File.VOLSET_TRANSLATOR = translator.TranslatorByRegex([('COSP_xxxx', re.I, 'COSP_xxxx')]) + \
                                          pds3file.Pds3File.VOLSET_TRANSLATOR

    ASSOCIATIONS = pds3file.Pds3File.ASSOCIATIONS.copy()
    ASSOCIATIONS['documents'] += associations_to_documents

    INFO_FILE_BASENAMES = info_file_basenames + pds3file.Pds3File.INFO_FILE_BASENAMES

pds3file.Pds3File.FILESPEC_TO_BUNDLESET = filespec_to_bundleset + pds3file.Pds3File.FILESPEC_TO_BUNDLESET

##########################################################################################
# Update the global dictionary of subclasses
##########################################################################################

pds3file.Pds3File.SUBCLASSES['COSP_xxxx'] = COSP_xxxx

##########################################################################################
