##########################################################################################
# pds3file/rules/RES_xxxx.py
##########################################################################################

import pdsfile.pds3file as pds3file
import translator
import re

##########################################################################################
# Subclass definition
##########################################################################################

class RES_xxxx(pds3file.Pds3File):

    pds3file.Pds3File.VOLSET_TRANSLATOR = translator.TranslatorByRegex([('RES_xxxx', re.I, 'RES_xxxx')]) + \
                                          pds3file.Pds3File.VOLSET_TRANSLATOR

##########################################################################################
# Update the global dictionary of subclasses
##########################################################################################

pds3file.Pds3File.SUBCLASSES['RES_xxxx'] = RES_xxxx

##########################################################################################
