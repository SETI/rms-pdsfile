##########################################################################################
# pds3file/rules/COUVIS_8xxx.py
##########################################################################################

"""Rules for the COUVIS_8xxx volume set: Cassini UVIS ring occultation profiles.

COUVIS_8xxx is described in the holdings as Cassini UVIS occultation profiles of
Saturn's rings, 2005-2017 (``_volinfo/COUVIS_8xxx.txt``). A product is a radial
profile at one of two sampling intervals, 1 km or 10 km.

The rule tables:

* ``description_and_icon_by_regex`` -- distinguishes the 1 km profile from the 10 km
  profile.
* ``default_viewables`` and ``diagrams_viewables`` -- the preview images for a
  profile and the observation diagrams for it. The class offers them as the
  "default" and "diagram" viewable sets.
* ``associations_to_volumes``, ``associations_to_previews``,
  ``associations_to_diagrams``, ``associations_to_metadata`` and
  ``associations_to_documents`` -- cross the five trees for one profile.
* ``versions`` -- the paths of the same profile in the other versions of this volume
  set, which cannot be found by wildcarding the version suffix alone. Three
  different things are in the way. The earliest version put the data under
  ``DATA/EASYDATA/`` rather than ``data/``, which is what the table's ``#UPPER#``
  directive rewrites; it also wrote an underscore after "TAU"; and its first three
  entries pair observations whose dates differ, repairing files that were misnamed.
  The data file basenames are upper case in both versions.
* ``view_options`` and ``split_rules`` -- the view flags and the basename grouping.
* ``opus_type`` and ``opus_products`` -- file products under the "Cassini UVIS" OPUS
  category as "Occultation Profile (1 km)" and "(10 km)", and list what OPUS offers
  with each. The product list names files explicitly rather than by wildcard.
* ``opus_id`` and ``opus_id_to_primary_logical_path`` -- the OPUS ID and its
  inverse.

`COVIMS_8xxx.py` serves the VIMS occultation profiles of the same rings and defines
a table of each of these same names; `CORSS_8xxx.py` serves the radio occultation
profiles.
"""

import re

import translator

import pdsfile.pds3file as pds3file

##########################################################################################
# DESCRIPTION_AND_ICON
##########################################################################################

description_and_icon_by_regex = translator.TranslatorByRegex([
    (r'volumes/.*_TAU01KM\.TAB', 0, ('Occultation Profile (1 km)',  'SERIES')),
    (r'volumes/.*_TAU10KM\.TAB', 0, ('Occultation Profile (10 km)', 'SERIES')),
])

##########################################################################################
# VIEWABLES
##########################################################################################

default_viewables = translator.TranslatorByRegex([
    (r'volumes/COUVIS_8xxx(|_v[0-9\.]+)/(COUVIS_8...)/(data|DATA/EASYDATA)/(UVIS_HSP.*)_TAU_?\d+KM\.(TAB|LBL)', 0,
            [r'previews/COUVIS_8xxx/\2/data/\4_full.jpg',
             r'previews/COUVIS_8xxx/\2/data/\4_med.jpg',
             r'previews/COUVIS_8xxx/\2/data/\4_small.jpg',
             r'previews/COUVIS_8xxx/\2/data/\4_thumb.jpg',
            ]),
])

diagrams_viewables = translator.TranslatorByRegex([
    (r'volumes/COUVIS_8xxx(|_v[0-9\.]+)/(COUVIS_8...)/(data|DATA/EASYDATA)/(UVIS_HSP.*)_TAU_?\d+KM\.(TAB|LBL)', 0,
            [r'diagrams/COUVIS_8xxx/\2/data/\4_full.jpg',
             r'diagrams/COUVIS_8xxx/\2/data/\4_med.jpg',
             r'diagrams/COUVIS_8xxx/\2/data/\4_small.jpg',
             r'diagrams/COUVIS_8xxx/\2/data/\4_thumb.jpg',
            ]),
])

##########################################################################################
# ASSOCIATIONS
##########################################################################################

associations_to_volumes = translator.TranslatorByRegex([
    (r'.*/COUVIS_8xxx(|_v[0-9\.]+)/(COUVIS_8...)/(data|DATA/EASYDATA)/(UVIS_HSP.*)_(TAU\w+KM|[a-z]+)\..*', 0,
            [r'volumes/COUVIS_8xxx\1/\2/\3/\4_TAU_01KM.LBL',
             r'volumes/COUVIS_8xxx\1/\2/\3/\4_TAU_01KM.TAB',
             r'volumes/COUVIS_8xxx\1/\2/\3/\4_TAU_10KM.LBL',
             r'volumes/COUVIS_8xxx\1/\2/\3/\4_TAU_10KM.TAB',
            ]),
    (r'documents/COUVIS_8xxx.*', 0,
             r'volumes/COUVIS_8xxx'),
])

associations_to_previews = translator.TranslatorByRegex([
    (r'.*/COUVIS_8xxx(|_v[0-9\.]+)/(COUVIS_8...)/(data|DATA/EASYDATA)/(UVIS_HSP.*)_(TAU\w+KM|[a-z]+)\..*', 0,
            [r'previews/COUVIS_8xxx/\2/data/\3_full.jpg',
             r'previews/COUVIS_8xxx/\2/data/\3_med.jpg',
             r'previews/COUVIS_8xxx/\2/data/\3_small.jpg',
             r'previews/COUVIS_8xxx/\2/data/\3_thumb.jpg',
            ]),
])

associations_to_diagrams = translator.TranslatorByRegex([
    (r'.*/COUVIS_8xxx(|_v[0-9\.]+)/(COUVIS_8...)/(data|DATA/EASYDATA)/(UVIS_HSP.*)_(TAU\w+KM|[a-z]+)\..*', 0,
            [r'diagrams/COUVIS_8xxx/\2/data/\3_full.jpg',
             r'diagrams/COUVIS_8xxx/\2/data/\3_med.jpg',
             r'diagrams/COUVIS_8xxx/\2/data/\3_small.jpg',
             r'diagrams/COUVIS_8xxx/\2/data/\3_thumb.jpg',
            ]),
])

associations_to_metadata = translator.TranslatorByRegex([
    (r'volumes/COUVIS_8xxx(|_v[0-9\.]+)/(COUVIS_8...)/(data|DATA/EASYDATA)/(UVIS_HSP.*)_(TAU\w+KM)\..*', 0,
            [r'metadata/COUVIS_8xxx/\2/\2_index.tab/\4_\5',
             r'metadata/COUVIS_8xxx/\2/\2_supplemental_index.tab/\4_TAU01',
            ]),
])

associations_to_documents = translator.TranslatorByRegex([
    (r'volumes/COUVIS_8xxx(|_[^/]+)/COUVIS_8\d\d\d',    0, r'documents/COUVIS_8xxx/*'),
    (r'volumes/COUVIS_8xxx(|_[^/]+)/COUVIS_8\d\d\d/.+', 0, r'documents/COUVIS_8xxx'),
])

##########################################################################################
# VERSIONS
##########################################################################################

# _v1 had upper case file names and used "DATA/EASYDATA" in place of "data"
# _v1 data files had an underscore after "TAU".
# Case conversions are inconsistent, sometimes mixed case file names are unchanged

versions = translator.TranslatorByRegex([

    # Associate erroneous file names found in early versions
    (r'volumes/COUVIS_8xxx(|_v[0-9\.]+)/COUVIS_8001/data/UVIS_HSP_(2005_139|2009_062)_THEHYA_E_TAU(.*)', 0,
            [r'volumes/COUVIS_8xxx*/COUVIS_8001/data/UVIS_HSP_2009_062_THEHYA_E_TAU\3',
             r'volumes/COUVIS_8xxx*/COUVIS_8001/data/UVIS_HSP_2005_139_THEHYA_E_TAU\3',
            ]),
    (r'volumes/COUVIS_8xxx(|_v[0-9\.]+)/COUVIS_8001/data/UVIS_HSP_(2007_038|2008_026)_SAO205839_I_TAU(.*)', 0,
            [r'volumes/COUVIS_8xxx*/COUVIS_8001/data/UVIS_HSP_2008_026_SAO205839_I_TAU\3',
             r'volumes/COUVIS_8xxx*/COUVIS_8001/data/UVIS_HSP_2007_038_SAO205839_I_TAU\3',
            ]),
    (r'volumes/COUVIS_8xxx(|_v[0-9\.]+)/COUVIS_8001/data/UVIS_HSP_2010_14[89]_LAMAQL_E_TAU(.*)', 0,
            [r'volumes/COUVIS_8xxx*/COUVIS_8001/data/UVIS_HSP_2010_148_LAMAQL_E_TAU\2',
             r'volumes/COUVIS_8xxx*/COUVIS_8001/data/UVIS_HSP_2010_149_LAMAQL_E_TAU\2',
            ]),

    # General corrections...
    (r'volumes/COUVIS_8xxx(|_v[0-9\.]+)/COUVIS_8001/(data|DATA/EASYDATA)/(.*_TAU)_?(.*)', 0,
            [r'volumes/COUVIS_8xxx*/COUVIS_8001/data/\3\4',
             r'volumes/COUVIS_8xxx_v1/COUVIS_8001/DATA/EASYDATA/\3_\4',
            ]),
    (r'volumes/COUVIS_8xxx(|_v[0-9\.]+)/COUVIS_8001/(data|DATA/EASYDATA)', 0,
            [r'volumes/COUVIS_8xxx*/COUVIS_8001/data',
             r'volumes/COUVIS_8xxx_v1/COUVIS_8001/DATA/EASYDATA',
            ]),
    (r'volumes/COVIMS_8xxx(|_v[0-9\.]+)/COUVIS_8001/(\w+[^aA])(|/.*)', 0,   # don't match "data" directory
            [r'volumes/COUVIS_8xxx*/COUVIS_8001/#LOWER#\2\3',
             r'volumes/COUVIS_8xxx*/COUVIS_8001/#LOWER#\2#MIXED#\3',
             r'volumes/COUVIS_8xxx_v1/COUVIS_8001/#UPPER#\2\3',
             r'volumes/COUVIS_8xxx_v1/COUVIS_8001/#UPPER#\2#MIXED#\3',
            ]),
])

##########################################################################################
# VIEW_OPTIONS (grid_view_allowed, multipage_view_allowed, continuous_view_allowed)
##########################################################################################

view_options = translator.TranslatorByRegex([
    (r'(volumes|previews|diagrams)/COUVIS_8xxx.*/COUVIS_8.../data', 0, (True, True, False)),
    (r'volumes/COUVIS_8xxx_v1/COUVIS_8001/DATA/EASYDATA',           0, (True, True, False)),
])

##########################################################################################
# SPLIT_RULES
##########################################################################################

split_rules = translator.TranslatorByRegex([
    (r'(UVIS_HSP_...._..._\w+_[IE])_(\w+)\.(.*)', 0, (r'\1', r'_\2', r'.\3')),

    # Group atlas files and their label
    (r'(.*atlas.*)\.(pdf|lbl)', re.I, ('atlas', r'\1', r'.\2')),
])

##########################################################################################
# OPUS_TYPE
##########################################################################################

opus_type = translator.TranslatorByRegex([
    (r'volumes/.*_TAU_?01KM\.(TAB|LBL)', 0, ('Cassini UVIS', 10, 'couvis_occ_01', 'Occultation Profile (1 km)',  True)),
    (r'volumes/.*_TAU_?10KM\.(TAB|LBL)', 0, ('Cassini UVIS', 20, 'couvis_occ_10', 'Occultation Profile (10 km)', True)),
    # Documentation
    (r'documents/COUVIS_8xxx/.*',        0, ('Cassini UVIS', 30, 'couvis_occ_documentation', 'Documentation', False)),
])

##########################################################################################
# OPUS_PRODUCTS
##########################################################################################

# Use of explicit file names means we don't need to invoke glob.glob(); this goes much faster
opus_products = translator.TranslatorByRegex([
    (r'.*/COUVIS_8xxx(|_v[0-9\.]+)/(COUVIS_....)/(data|DATA/EASYDATA)/(UVIS_HSP.*)_(TAU.*|[a-z]+)\..*', 0,
            [r'volumes/COUVIS_8xxx*/\2/data/\4_TAU01KM.LBL',
             r'volumes/COUVIS_8xxx*/\2/data/\4_TAU01KM.TAB',
             r'volumes/COUVIS_8xxx*/\2/data/\4_TAU10KM.LBL',
             r'volumes/COUVIS_8xxx*/\2/data/\4_TAU10KM.TAB',
             r'volumes/COUVIS_8xxx_v1/\2/DATA/EASYDATA/\4_TAU_01KM.LBL',
             r'volumes/COUVIS_8xxx_v1/\2/DATA/EASYDATA/\4_TAU_01KM.TAB',
             r'volumes/COUVIS_8xxx_v1/\2/DATA/EASYDATA/\4_TAU_10KM.LBL',
             r'volumes/COUVIS_8xxx_v1/\2/DATA/EASYDATA/\4_TAU_10KM.TAB',
             r'previews/COUVIS_8xxx/\2/data/\4_full.jpg',
             r'previews/COUVIS_8xxx/\2/data/\4_med.jpg',
             r'previews/COUVIS_8xxx/\2/data/\4_small.jpg',
             r'previews/COUVIS_8xxx/\2/data/\4_thumb.jpg',
             r'diagrams/COUVIS_8xxx/\2/data/\4_full.jpg',
             r'diagrams/COUVIS_8xxx/\2/data/\4_med.jpg',
             r'diagrams/COUVIS_8xxx/\2/data/\4_small.jpg',
             r'diagrams/COUVIS_8xxx/\2/data/\4_thumb.jpg',
             r'metadata/COUVIS_8xxx/\2/\2_index.lbl',
             r'metadata/COUVIS_8xxx/\2/\2_index.tab',
             r'metadata/COUVIS_8xxx/\2/\2_supplemental_index.lbl',
             r'metadata/COUVIS_8xxx/\2/\2_supplemental_index.tab',
            ]),
])

##########################################################################################
# OPUS_ID
##########################################################################################

opus_id = translator.TranslatorByRegex([
    (r'.*/COUVIS_8xxx.*/(data|DATA/EASYDATA)/UVIS_HSP_(\d{4})_(\d{3})_(\w+)_([IE]).*', 0, r'co-uvis-occ-#LOWER#\2-\3-\4-\5'),
])

##########################################################################################
# OPUS_ID_TO_PRIMARY_LOGICAL_PATH
##########################################################################################

opus_id_to_primary_logical_path = translator.TranslatorByRegex([
    (r'co-uvis-occ-(....)-(...)-(.*)-([ie])', 0,  r'volumes/COUVIS_8xxx/COUVIS_8001/data/#UPPER#UVIS_HSP_\1_\2_\3_\4_TAU01KM.TAB'),
])

##########################################################################################
# Subclass definition
##########################################################################################

class COUVIS_8xxx(pds3file.Pds3File):
    """The ``Pds3File`` subclass for COUVIS_8xxx.

    The class body wires this module's rule tables onto the class attributes
    ``Pds3File`` reads. Where a table is added to the inherited one, a lookup tries
    this module's patterns first and falls through to the defaults; where it is
    assigned outright there is no fall-through. The module tail registers the class
    in ``Pds3File.SUBCLASSES`` under the key
    "COUVIS_8xxx". The module docstring describes the volume set and every table.
    """

    pds3file.Pds3File.VOLSET_TRANSLATOR = translator.TranslatorByRegex([('COUVIS_8xxx', re.I, 'COUVIS_8xxx')]) + \
                                          pds3file.Pds3File.VOLSET_TRANSLATOR

    DESCRIPTION_AND_ICON = description_and_icon_by_regex + pds3file.Pds3File.DESCRIPTION_AND_ICON
    VIEW_OPTIONS = view_options + pds3file.Pds3File.VIEW_OPTIONS
    SPLIT_RULES = split_rules + pds3file.Pds3File.SPLIT_RULES

    OPUS_TYPE = opus_type + pds3file.Pds3File.OPUS_TYPE
    OPUS_PRODUCTS = opus_products + pds3file.Pds3File.OPUS_PRODUCTS
    OPUS_ID = opus_id
    OPUS_ID_TO_PRIMARY_LOGICAL_PATH = opus_id_to_primary_logical_path

    VIEWABLES = {
        'default': default_viewables,
        'diagram': diagrams_viewables,
    }

    ASSOCIATIONS = pds3file.Pds3File.ASSOCIATIONS.copy()
    ASSOCIATIONS['volumes']  += associations_to_volumes
    ASSOCIATIONS['previews'] += associations_to_previews
    ASSOCIATIONS['diagrams'] += associations_to_diagrams
    ASSOCIATIONS['metadata'] += associations_to_metadata
    ASSOCIATIONS['documents'] += associations_to_documents

    VERSIONS = versions + pds3file.Pds3File.VERSIONS

# Global attribute shared by all subclasses
pds3file.Pds3File.OPUS_ID_TO_SUBCLASS = translator.TranslatorByRegex([(r'co-uvis-occ.*', 0, COUVIS_8xxx)]) + \
                                        pds3file.Pds3File.OPUS_ID_TO_SUBCLASS

##########################################################################################
# Update the global dictionary of subclasses
##########################################################################################

pds3file.Pds3File.SUBCLASSES['COUVIS_8xxx'] = COUVIS_8xxx
