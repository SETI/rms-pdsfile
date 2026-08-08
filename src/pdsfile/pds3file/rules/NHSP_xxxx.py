##########################################################################################
# pds3file/rules/NHSP_xxxx.py
##########################################################################################

"""Rules for the NHSP_xxxx volume set: New Horizons SPICE kernels.

NHSP_xxxx holds SPICE kernels for New Horizons. The one volume, NHSP_1000, covers
the Jupiter flyby and carries data set ID NH-J/P/SS-SPICE-6-V1.0 (holdings
``_volinfo/NHSP_xxxx.txt``). The RMS Node curates a companion document directory,
``documents/NHSP_xxxx``, holding links to the SPICE Toolkit and to a New Horizons
kernel selection tool.

The rule tables:

* ``associations_to_documents`` -- sends any path under ``volumes/NHSP_xxxx`` to the
  curated ``documents/NHSP_xxxx/`` directory.
* ``filespec_to_bundleset`` -- maps a file specification beginning with an NHSP_nnnn
  volume ID to the volume set name NHSP_xxxx.
* ``info_file_basenames`` -- makes ``aareadme.txt`` the information file for a
  directory here, in preference to the ``voldesc.cat`` the default table would pick.

`NHSP_xxxx.py` is one of three SPICE-kernel rule modules that define the same three
tables; the others are `COSP_xxxx.py` for Cassini and `JNOSP_xxxx.py` for Juno. Its
volume set translator is the only one of the three written with a trailing wildcard,
so it also matches a versioned volume set name such as NHSP_xxxx_v1.
"""

import re

import translator

import pdsfile.pds3file as pds3file

##########################################################################################
# ASSOCIATIONS
##########################################################################################

associations_to_documents = translator.TranslatorByRegex([
    (r'volumes/NHSP_xxxx.*', 0,
        r'documents/NHSP_xxxx/*'),
])

##########################################################################################
# FILESPEC_TO_BUNDLESET
##########################################################################################

filespec_to_bundleset = translator.TranslatorByRegex([
    (r'NHSP_\d{4}.*', 0, r'NHSP_xxxx'),
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

class NHSP_xxxx(pds3file.Pds3File):
    """The ``Pds3File`` subclass for NHSP_xxxx.

    The class body puts this module's rule tables in front of the class attributes
    ``Pds3File`` reads, and the module tail registers the class in
    ``Pds3File.SUBCLASSES`` under the key "NHSP_xxxx".
    The module docstring describes the volume set and every table.
    """

    pds3file.Pds3File.VOLSET_TRANSLATOR = translator.TranslatorByRegex([('NHSP_xxxx.*', re.I, 'NHSP_xxxx')]) + \
                                          pds3file.Pds3File.VOLSET_TRANSLATOR

    ASSOCIATIONS = pds3file.Pds3File.ASSOCIATIONS.copy()
    ASSOCIATIONS['documents'] += associations_to_documents

    INFO_FILE_BASENAMES = info_file_basenames + pds3file.Pds3File.INFO_FILE_BASENAMES

pds3file.Pds3File.FILESPEC_TO_BUNDLESET = filespec_to_bundleset + pds3file.Pds3File.FILESPEC_TO_BUNDLESET

##########################################################################################
# Update the global dictionary of subclasses
##########################################################################################

pds3file.Pds3File.SUBCLASSES['NHSP_xxxx'] = NHSP_xxxx

##########################################################################################
