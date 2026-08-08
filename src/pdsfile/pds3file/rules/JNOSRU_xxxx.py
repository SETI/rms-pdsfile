##########################################################################################
# pds3file/rules/JNOSRU_xxxx.py
##########################################################################################

"""Rules for the JNOSRU_xxxx volume set: Juno SRU images.

JNOSRU_xxxx is described in the holdings as the Juno SRU image collection. Its one
volume, JNOSRU_0001, covers orbits 36 through 71 and carries two data set IDs,
JNO-J-SRU-EDR-2-L0-V1.0 for the images and
JNO-J-SRU-COUNTRATE-TABLE-5-L2-V1.0 for the count rate tables
(``_volinfo/JNOSRU_xxxx.txt``).

The rule tables:

* ``description_and_icon_by_regex`` -- names the image, count rate table and preview
  directories and the files inside them. A data file is FITS here, which is why this
  module names it rather than leaving it to the default table.
* ``default_viewables`` -- points a product at its preview images.
* ``associations_to_volumes``, ``associations_to_previews`` and
  ``associations_to_metadata`` -- cross the volumes, previews and metadata trees for
  one observation.
* ``view_options`` -- the grid, multipage and continuous view flags.

This module defines no OPUS tables, so OPUS behavior comes from the defaults in
`pds3file/rules/__init__.py`. Its volume set translator matches JNOSRU_ followed by
any four characters.
"""

import re

import translator

import pdsfile.pds3file as pds3file

##########################################################################################
# DESCRIPTION_AND_ICON
##########################################################################################

description_and_icon_by_regex = translator.TranslatorByRegex([
    (r'volumes/.*/DATA/SRU_EDR[^\.]*',              0, ('Image files',       'IMAGEDIR')),
    (r'volumes/.*/DATA/SRU_EDR.*\.FIT',             0, ('Image file, FITS',  'IMAGE')),
    (r'volumes/.*/DATA/SRU_COUNTRATE_TABLE[^\.]*',  0, ('Count rate tables', 'TABLES')),
    (r'volumes/.*/DATA/SRU_COUNTRATE_TABLE.*\.CSV', 0, ('Count rate table',  'TABLE')),
    (r'previews/.*/DATA/SRU_EDR[^\.]*',             0, ('Preview images',    'BROWDIR')),
    (r'previews/.*/DATA/SRU_EDR.*\.jpg',            0, ('Preview image',     'BROWSE')),
])

##########################################################################################
# VIEWABLES
##########################################################################################

default_viewables = translator.TranslatorByRegex([
    (r'.*/JNOSRU_xxxx(|_v[\d\.]+)/(JNOSRU_0\d\d\d/DATA/SRU_EDR/\w+/\w+/SRU_\d+_20\d{5}T\d{6}_\d\d_V\d\d).*', 0,
            [r'previews/JNOSRU_xxxx/\2_full.jpg',
             r'previews/JNOSRU_xxxx/\2_med.jpg',
             r'previews/JNOSRU_xxxx/\2_small.jpg',
             r'previews/JNOSRU_xxxx/\2_thumb.jpg',
            ]),
])

##########################################################################################
# ASSOCIATIONS
##########################################################################################

associations_to_volumes = translator.TranslatorByRegex([
    # previews to image files
    (r'previews/JNOSRU_xxxx(|_v[\d\.]+)/(JNOSRU_0\d\d\d/DATA/SRU_EDR/\w+/\w+/SRU_\d+_20\d{5}T\d{6}_\d\d_V\d\d).*', 0,
            [r'volumes/JNOSRU_xxxx/\2.FIT',
             r'volumes/JNOSRU_xxxx/\2.LBL']),
    # countrate files to image directories
    (r'volumes/JNOSRU_xxxx(|_v[\d\.]+)/(JNOSRU_0\d\d\d/DATA)/SRU_COUNTRATE_TABLE/(.*)/\w+\.(CSV|LBL)', 0,
            r'volumes/JNOSRU_xxxx\1/\2/SRU_EDR/\3'),
    (r'volumes/JNOSRU_xxxx(|_v[\d\.]+)/(JNOSRU_0\d\d\d/DATA)/SRU_COUNTRATE_TABLE/([^\.]*)', 0,
            r'volumes/JNOSRU_xxxx\1/\2/SRU_EDR/\3'),
    # image files to count rate files
    (r'volumes/JNOSRU_xxxx(|_v[\d\.]+)/(JNOSRU_0\d\d\d/DATA)/SRU_EDR/(.*)/\w+\.(FIT|LBL)', 0,
            [r'volumes/JNOSRU_xxxx\1/\2/SRU_COUNTRATE_TABLE/\3/*.CSV',
             r'volumes/JNOSRU_xxxx\1/\2/SRU_COUNTRATE_TABLE/\3/*.LBL']),
    (r'volumes/JNOSRU_xxxx(|_v[\d\.]+)/(JNOSRU_0\d\d\d/DATA)/SRU_EDR/([^\.]*)', 0,
            [r'volumes/JNOSRU_xxxx\1/\2/SRU_COUNTRATE_TABLE/\3/*.CSV',
             r'volumes/JNOSRU_xxxx\1/\2/SRU_COUNTRATE_TABLE/\3/*.LBL']),
])

associations_to_previews = translator.TranslatorByRegex([
    # image files to previews
    (r'volumes/JNOSRU_xxxx(|_v[\d\.]+)/(JNOSRU_0\d\d\d/DATA/SRU_EDR/\w+/\w+/SRU_\d+_20\d{5}T\d{6}_\d\d_V\d\d)\.(FIT|LBL)', 0,
            [r'previews/JNOSRU_xxxx/\2_full.jpg',
             r'previews/JNOSRU_xxxx/\2_med.jpg',
             r'previews/JNOSRU_xxxx/\2_small.jpg',
             r'previews/JNOSRU_xxxx/\2_thumb.jpg',
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
    """The ``Pds3File`` subclass for JNOSRU_xxxx.

    The class body puts this module's rule tables in front of the class attributes
    ``Pds3File`` reads, and the module tail registers the class in
    ``Pds3File.SUBCLASSES`` under the key "JNOSRU_xxxx".
    The module docstring describes the volume set and every table.
    """

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
