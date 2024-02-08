##########################################################################################
# pds3file/rules/ASTROM_xxxx.py
##########################################################################################

import pdsfile.pds3file as pds3file
import translator
import re

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

    pds3file.Pds3File.VOLSET_TRANSLATOR = translator.TranslatorByRegex([('ASTROM_xxxx', re.I, 'ASTROM_xxxx')]) + \
                                          pds3file.Pds3File.VOLSET_TRANSLATOR

pds3file.Pds3File.FILESPEC_TO_BUNDLESET = filespec_to_bundleset + pds3file.Pds3File.FILESPEC_TO_BUNDLESET

##########################################################################################
# Update the global dictionary of subclasses
##########################################################################################

pds3file.Pds3File.SUBCLASSES['ASTROM_xxxx'] = ASTROM_xxxx

##########################################################################################
