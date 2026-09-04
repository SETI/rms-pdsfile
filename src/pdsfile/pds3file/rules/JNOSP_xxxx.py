##########################################################################################
# pds3file/rules/JNOSP_xxxx.py
##########################################################################################

"""Rules for the JNOSP_xxxx volume set: Juno SPICE kernels.

JNOSP_xxxx holds SPICE kernels for the Juno mission. The one volume, JNOSP_1000,
carries data set ID JNO-J/E/SS-SPICE-6-V1.0 (holdings ``_volinfo/JNOSP_xxxx.txt``).
The RMS Node curates a companion document directory, ``documents/JNOSP_xxxx``,
holding links to the SPICE Toolkit and to a Juno kernel selection tool.

The rule tables:

* ``associations_to_documents`` -- sends any path under ``volumes/JNOSP_xxxx`` to the
  curated ``documents/JNOSP_xxxx/`` directory.
* ``filespec_to_bundleset`` -- maps a file specification beginning with a JNOSP_nnnn
  volume ID to the volume set name JNOSP_xxxx.
* ``info_file_basenames`` -- makes ``aareadme.txt`` the information file for a
  directory here, in preference to the ``voldesc.cat`` the default table would pick.

`JNOSP_xxxx.py` is one of three SPICE-kernel rule modules that define the same three
tables; the others are `COSP_xxxx.py` for Cassini and `NHSP_xxxx.py` for New
Horizons.
"""

import re

import translator

import pdsfile.pds3file as pds3file

##########################################################################################
# ASSOCIATIONS
##########################################################################################

associations_to_documents = translator.TranslatorByRegex([
    (r'volumes/JNOSP_xxxx.*', 0,
        r'documents/JNOSP_xxxx/*'),
])

##########################################################################################
# FILESPEC_TO_BUNDLESET
##########################################################################################

filespec_to_bundleset = translator.TranslatorByRegex([
    (r'JNOSP_\d{4}.*', 0, r'JNOSP_xxxx'),
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

class JNOSP_xxxx(pds3file.Pds3File):
    """The ``Pds3File`` subclass for JNOSP_xxxx.

    The class body and the module tail install this module's rule tables on the class
    attributes ``Pds3File`` reads. `pds3file/rules/__init__.py` sets out the routes a
    table takes and which of them leaves the inherited rules in front. The class
    is registered in ``Pds3File.SUBCLASSES`` under the key
    "JNOSP_xxxx".
    The module docstring describes the volume set and every table.
    """

    pds3file.Pds3File.VOLSET_TRANSLATOR = translator.TranslatorByRegex([('JNOSP_xxxx', re.I, 'JNOSP_xxxx')]) + \
                                          pds3file.Pds3File.VOLSET_TRANSLATOR

    ASSOCIATIONS = pds3file.Pds3File.ASSOCIATIONS.copy()
    ASSOCIATIONS['documents'] += associations_to_documents

    INFO_FILE_BASENAMES = info_file_basenames + pds3file.Pds3File.INFO_FILE_BASENAMES

pds3file.Pds3File.FILESPEC_TO_BUNDLESET = filespec_to_bundleset + pds3file.Pds3File.FILESPEC_TO_BUNDLESET

##########################################################################################
# Update the global dictionary of subclasses
##########################################################################################

pds3file.Pds3File.SUBCLASSES['JNOSP_xxxx'] = JNOSP_xxxx

##########################################################################################
