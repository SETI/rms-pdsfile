##########################################################################################
# pds3file/rules/JNOJNC_xxxx.py
##########################################################################################

import re
import pdsfile.pds3file as pds3file
import translator

##########################################################################################
# DESCRIPTION_AND_ICON
##########################################################################################

description_and_icon_by_regex = translator.TranslatorByRegex([
    (r'volumes/.*/DATA/SRU_EDR[^\.]*',              0, ('Image files',              'IMAGEDIR')),
    (r'volumes/.*/DATA/SRU_EDR.*\.FIT',             0, ('Image file, FITS',         'IMAGE')),
    (r'volumes/.*/DATA/SRU_COUNTRATE_TABLE[^\.]*',  0, ('Count rate tables',        'TABLEDIR')),
    (r'volumes/.*/DATA/SRU_COUNTRATE_TABLE.*\.CSV', 0, ('Count rate table',         'TABLE')),
    (r'previews/.*/DATA/SRU_EDR[^\.]*',             0, ('Preview image collection', 'BROWDIR')),
    (r'previews/.*/DATA/SRU_EDR.*\.jpg',            0, ('Preview image',            'BROWSE')),
])

##########################################################################################
# VIEWABLES
##########################################################################################

default_viewables = translator.TranslatorByRegex([
    (r'.*/JNOSRU_xxxx(|_v[\d\.]+)/(JNOSRU_0\d\d\d/DATA/SRU_EDR/\w+/\w+/SRU_\d+_20\d{5}T\d{6}_\d\d_V\d\d).*', 0,
            [r'previews/\2_full.jpg',
             r'previews/\2_med.jpg',
             r'previews/\2_small.jpg',
             r'previews/\2_thumb.jpg',
            ]),
])

##########################################################################################
# ASSOCIATIONS
##########################################################################################

associations_to_volumes = translator.TranslatorByRegex([
    # previews to image files
    (r'previews/JNOSRU_xxxx(|_v[\d\.]+)/(JNOSRU_0\d\d\d/DATA/SRU_EDR/\w+/\w+/SRU_\d+_20\d{5}T\d{6}_\d\d_V\d\d).*', 0,
            r'volumes/JNOSRU_xxxx/\2.FIT'),
    # countrate files to image directories
    (r'volumes/JNOSRU_xxxx(|_v[\d\.]+)/(JNOSRU_0\d\d\d/DATA)/SRU_COUNTRATE_TABLE/(.*)/\w+\.(CSV|LBL)', 0,
            r'volumes/JNOSRU_xxxx\1/\2/SRU_EDR/\3'),
    (r'volumes/JNOSRU_xxxx(|_v[\d\.]+)/(JNOSRU_0\d\d\d/DATA)/SRU_COUNTRATE_TABLE/([^\.]*)', 0,
            r'volumes/JNOSRU_xxxx\1/\2/SRU_EDR/\3'),
    # image files to count rate files
    (r'volumes/JNOSRU_xxxx(|_v[\d\.]+)/(JNOSRU_0\d\d\d/DATA)/SRU_EDR/(.*)/\w+\.(FIT|LBL)', 0,
            r'volumes/JNOSRU_xxxx\1/\2/SRU_COUNTRATE_TABLE/\3/*.CSV'),
    (r'volumes/JNOSRU_xxxx(|_v[\d\.]+)/(JNOSRU_0\d\d\d/DATA)/SRU_EDR/([^\.]*)', 0,
            r'volumes/JNOSRU_xxxx\1/\2/SRU_COUNTRATE_TABLE/\3/*.CSV'),
])

associations_to_previews = translator.TranslatorByRegex([
    # image files to previews
    (r'volumes/JNOSRU_xxxx(|_v[\d\.]+)/(JNOSRU_0\d\d\d/DATA/SRU_EDR/\w+/\w+/SRU_\d+_20\d{5}T\d{6}_\d\d_V\d\d)\.(FIT|LBL)', 0,
            [r'previews/\2_full.jpg',
             r'previews/\2_med.jpg',
             r'previews/\2_small.jpg',
             r'previews/\2_thumb.jpg',
            ]),
])

associations_to_metadata = translator.TranslatorByRegex([
    (r'.*/JNOSRU_xxxx(|_v[\d\.]+)/(JNOSRU_0\d\d\d)/DATA/\w+/\w+/\w+/(\w+)\.(CSV|FIT|LBL)', 0,
            r'metadata/JNOSRU_xxxx\1/\2/\2_index.tab/\3'),
    (r'.*/JNOSRU_xxxx(|_v[\d\.]+)/(JNOSRU_0\d\d\d)/DATA[^\.]*', 0,
            r'metadata/JNOSRU_xxxx\1/\2/\2_*.tab'),
])

##########################################################################################
# VIEW_OPTIONS (grid_view_allowed, multipage_view_allowed, continuous_view_allowed)
##########################################################################################

view_options = translator.TranslatorByRegex([
    (r'.*/JNOSRU_xxxx(|_v[\d\.]+)/(JNOSRU_0\d\d\d)/DATA/\w+/\w+/ORBIT_\d+.*', 0, (True, True, True)),
])

##########################################################################################
# Subclass definition
##########################################################################################

class JNOSRU_xxxx(pds3file.Pds3File):

    pds3file.Pds3File.VOLSET_TRANSLATOR = translator.TranslatorByRegex([('JNOSRU_....', re.I, 'JNOSRU_xxxx')]) + \
                                          pds3file.Pds3File.VOLSET_TRANSLATOR

    DESCRIPTION_AND_ICON = description_and_icon_by_regex + pds3file.Pds3File.DESCRIPTION_AND_ICON
    VIEW_OPTIONS = view_options + pds3file.Pds3File.VIEW_OPTIONS

    VIEWABLES = {'default': default_viewables}

    ASSOCIATIONS = pds3file.Pds3File.ASSOCIATIONS.copy()
    ASSOCIATIONS['volumes']  += associations_to_volumes
    ASSOCIATIONS['previews'] += associations_to_previews
    ASSOCIATIONS['metadata'] += associations_to_metadata

##########################################################################################
# Update the global dictionary of subclasses
##########################################################################################

pds3file.Pds3File.SUBCLASSES['JNOSRU_xxxx'] = JNOSRU_xxxx

##########################################################################################
