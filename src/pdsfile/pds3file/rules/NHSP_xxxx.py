##########################################################################################
# pds3file/rules/NHSP_xxxx.py
##########################################################################################

import pdsfile.pds3file as pds3file
import translator
import re

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
