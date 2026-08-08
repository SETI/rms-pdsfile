##########################################################################################
# pds3file/rules/HSTxx_xxxx.py
##########################################################################################

"""Rules for the HSTxx_xxxx volume sets: HST placeholder volumes for OPUS.

`HSTxx_xxxx.py` serves five volume sets, one per HST instrument, matched by the
pattern HST.x_xxxx: HSTIx_xxxx for WFC3, HSTJx_xxxx for ACS, HSTNx_xxxx for NICMOS,
HSTOx_xxxx for STIS and HSTUx_xxxx for WFPC2. Each is described in the holdings as a
set of placeholder volumes for OPUS queries (``_volinfo/HSTIx_xxxx.txt`` and its
four siblings): what a volume carries is previews, 16-bit TIFFs of raw images, FITS
label listings and PDS labels with download instructions, rather than the archived
data itself. Observations are grouped by visit.

The rule tables:

* ``description_and_icon_by_regex`` -- names the visit directories, the several
  preview kinds (raw, calibrated, drizzled, 2-D image, spectrum line plot), the
  16-bit TIFF of a raw image, the FITS label listing, the PDS label that carries the
  download instructions, and the association indices in the metadata tree.
* ``default_viewables`` -- the preview images for a product.
* ``associations_to_volumes``, ``associations_to_previews``,
  ``associations_to_metadata`` and ``associations_to_documents`` -- cross the
  volumes, previews, metadata and documents trees for one observation.
* ``split_rules``, ``view_options`` and ``neighbors`` -- the basename grouping, the
  view flags and the corresponding directories in sibling volumes.
* ``opus_type`` and ``opus_products`` -- file products under the "HST" OPUS
  category, with a type for each preview kind and for the FITS header text, and list
  what OPUS offers with each.
* ``opus_id`` and ``opus_id_to_primary_logical_path`` -- the OPUS ID and its
  inverse.
* ``filespec_to_bundleset`` -- maps a file specification beginning with a volume ID
  of the form HST, an instrument letter, a digit, an underscore and four digits, as
  in HSTI1_1556, to its volume set name. The default rule cannot do it because it
  replaces only the last three characters, giving HSTI1_1xxx where the volume set is
  HSTIx_xxxx: the digit after the instrument letter has to become an x too.

Two other rule modules serve HST data: `ASTROM_xxxx.py` for the WFPC2 astrometry of
Saturn's moons and `RPX_xxxx.py` for the WFPC2 ring plane crossing observations.
"""

import re

import translator

import pdsfile.pds3file as pds3file

##########################################################################################
# DESCRIPTION_AND_ICON
##########################################################################################

description_and_icon_by_regex = translator.TranslatorByRegex([
    (r'volumes/.*/data/visit_..',                    re.I, ('Images grouped by visit',                  'IMAGEDIR')),
    (r'volumes/.*/data/visit.*/.*\.TIF',             re.I, ('16-bit unscaled TIFF of raw image',        'IMAGE')   ),
    (r'volumes/.*/data/visit.*/.*DRZ\.JPG',          re.I, ('Preview of "drizzled" image',              'IMAGE')   ),
    (r'volumes/.*/data/visit.*/.*_(D0M|RAW).*\.JPG', re.I, ('Preview of raw image',                     'IMAGE')   ),
    (r'volumes/.*/data/visit.*/.*_X1D.*\.JPG',       re.I, ('Line plot of spectrum',                    'DATA')    ),
    (r'volumes/.*/data/visit.*/.*_X2D.*\.JPG',       re.I, ('Preview of 2-D image',                     'IMAGE')   ),
    (r'volumes/.*/data/visit.*/.*_FLT.*\.JPG',       re.I, ('Preview of calibrated image',              'IMAGE')   ),
    (r'volumes/.*/data/visit.*/.*\.ASC',             re.I, ('Listing of FITS label info',               'INFO')    ),
    (r'volumes/.*/data/visit.*/.*\.LBL',             re.I, ('PDS label with download instructions',     'LABEL')   ),
    (r'volumes/.*/index/hstfiles\..*',               re.I, ('Index of associations between data files', 'INDEX')   ),
    (r'volumes/.*/index/hstfiles\..*',               re.I, ('Index of associations between data files', 'INDEX')   ),
    (r'metadata/.*9999/.*hstfiles\..*',              re.I, ('Cumulative index of associations between data files', 'INDEX')),
    (r'metadata/.*9999/.*index\..*',                 re.I, ('Cumulative product index with RMS Node updates',      'INDEX')),
    (r'metadata/.*hstfiles\..*',                     re.I, ('Index of associations between data files, updated',   'INDEX')),
])

##########################################################################################
# SPLIT_RULES
##########################################################################################

split_rules = translator.TranslatorByRegex([
    (r'([IJUON]\w{8})(|_\w+)\.(.*)', 0, (r'\1', r'\2', r'.\3')),
])

##########################################################################################
# VIEWABLES
##########################################################################################

default_viewables = translator.TranslatorByRegex([
    (r'volumes/(.*/DATA/VISIT_..)/([IJUON]\w{8})(|_\w+)\.(.*)', 0,
            [r'previews/\1/\2_full.jpg',
             r'previews/\1/\2_med.jpg',
             r'previews/\1/\2_small.jpg',
             r'previews/\1/\2_thumb.jpg',
            ]),
])

##########################################################################################
# ASSOCIATIONS
##########################################################################################

associations_to_volumes = translator.TranslatorByRegex([
    (r'.*/(HST.x_xxxx)(|_.*)/(HST.._..../DATA/VISIT_../\w{9}).*',   0, r'volumes/\1/\3*'),
    (r'.*/(HST.x_xxxx)(|_.*)/(HST.._..../DATA/VISIT_..)',           0, r'volumes/\1/\3'),
    (r'.*/(HST.x_xxxx)(|_.*)/(HST.._..../DATA)',                    0, r'volumes/\1/\3'),
    (r'.*/(HST.)9_9999.*',                                          0, r'volumes/\1x_xxxx'),
    (r'documents/(HST.x_xxxx).*',                                   0, r'volumes/\1'),
])

associations_to_previews = translator.TranslatorByRegex([
    (r'.*/(HST.._xxxx)(|_.*)/(HST.._..../DATA/VISIT_../\w{9}).*',   0, [r'previews/\1/\3_full.jpg',
                                                                        r'previews/\1/\3_med.jpg',
                                                                        r'previews/\1/\3_small.jpg',
                                                                        r'previews/\1/\3_thumb.jpg']),
    (r'.*/(HST.x_xxxx)(|_.*)/(HST.._..../DATA/VISIT_..)',           0, r'previews/\1/\3'),
    (r'.*/(HST.x_xxxx)(|_.*)/(HST.._..../DATA)',                    0, r'previews/\1/\3'),
    (r'.*/(HST.)9_9999.*',                                          0, r'previews/\1x_xxxx'),
])

associations_to_metadata = translator.TranslatorByRegex([
    (r'volumes/(HST.x_xxxx)(|_.*)/(HST.._....)/DATA/VISIT_../(\w{9}).*', 0, [r'metadata/\1/\3/\3_index.tab/\4',
                                                                             r'metadata/\1/\3/\3_hstfiles.tab/\4']),
    (r'volumes/(HST.x_xxxx)(|_.*)/(HST.._....)/DATA(|/VISIT_..)',        0,  r'metadata/\1/\3'),
    (r'volumes/(HST.x_xxxx)(|_.*)/(HST.._....)/INDEX/INDEX\..*',         0, [r'metadata/\1/\3/\3_index.tab',
                                                                             r'metadata/\1/\3/\3_index.lbl']),
    (r'volumes/(HST.x_xxxx)(|_.*)/(HST.._....)/INDEX/HSTFILES\..*',      0, [r'metadata/\1/\3/\3_hstfiles.tab',
                                                                             r'metadata/\1/\3/\3_hstfiles.lbl']),
    (r'metadata/(HST.)x_xxxx(|_v[0-9\.]+)/HST.[^9]_....',                0,  r'metadata/\1x_xxxx\2/\g<1>9_9999'),
    (r'metadata/(HST.)x_xxxx(|_v[0-9\.]+)/HST.[^9]_..../HST.._....(_.*)\..*',  0,
                                                                       [r'metadata/\1x_xxxx\2/\g<1>9_9999/\g<1>9_9999\3.tab',
                                                                        r'metadata/\1x_xxxx\2/\g<1>9_9999/\g<1>9_9999\3.lbl']),
])

associations_to_documents = translator.TranslatorByRegex([
    (r'volumes/(HST.x_xxxx).*',                                     0, r'documents/\1/*'),
])

##########################################################################################
# VIEW_OPTIONS (grid_view_allowed, multipage_view_allowed, continuous_view_allowed)
##########################################################################################

view_options = translator.TranslatorByRegex([
    (r'(volumes|previews)/HST.x_xxxx/HST.._..../DATA(|/VISIT_..)', 0, (True, True, True)),
])

##########################################################################################
# NEIGHBORS
##########################################################################################

neighbors = translator.TranslatorByRegex([
    (r'(volumes|previews)/(HST.x_xxxx/HST.._..../DATA)',            re.I, r'\1/\2'),
    (r'(volumes|previews)/(HST.x_xxxx/HST.._..../DATA)/(VISIT_..)', re.I, r'\1/\2/*'),
])

##########################################################################################
# OPUS_TYPE
##########################################################################################

opus_type = translator.TranslatorByRegex([
    (r'volumes/.*\.ASC',                 0, ('HST',  10, 'hst_text',        'FITS Header Text',                           True)),
    (r'volumes/.*\.LBL',                 0, ('HST',  10, 'hst_label',       'HST Preview Products',                       True)),
    (r'volumes/.*\.TIF',                 0, ('HST',  20, 'hst_tiff',        'Raw Data Preview (lossless)',                True)),
    (r'volumes/.*_(RAW.*|D0M_...)\.JPG', 0, ('HST',  30, 'hst_raw',         'Raw Data Preview',                           True)),
    (r'volumes/.*_(FLT.*|CAL)\.JPG',     0, ('HST',  40, 'hst_calib',       'Calibrated Data Preview',                    True)),
    (r'volumes/.*_SFL\.JPG',             0, ('HST',  50, 'hst_summed',      'Calibrated Summed Preview',                  True)),
    (r'volumes/.*_CRJ\.JPG',             0, ('HST',  60, 'hst_cosmic_ray',  'Calibrated Cosmic Ray Cleaned Preview',      True)),
    (r'volumes/.*_DRZ\.JPG',             0, ('HST',  70, 'hst_drizzled',    'Calibrated Geometrically Corrected Preview', True)),
    (r'volumes/.*_IMA\.JPG',             0, ('HST',  80, 'hst_ima',         'Pre-mosaic Preview',                         True)),
    (r'volumes/.*_MOS\.JPG',             0, ('HST',  90, 'hst_mosaic',      'Mosaic Preview',                             True)),
    (r'volumes/.*_(X1D|SX1)\.JPG',       0, ('HST', 100, 'hst_1d_spectrum', '1-D Spectrum Preview',                       True)),
    (r'volumes/.*_(X2D|SX2)\.JPG',       0, ('HST', 110, 'hst_2d_spectrum', '2-D Spectrum Preview',                       True)),
    # Documentation
    (r'documents/HST\wx_xxxx/.*',         0, ('HST', 120, 'hst_documentation', 'Documentation', False)),
])

##########################################################################################
# OPUS_PRODUCTS
##########################################################################################

opus_products = translator.TranslatorByRegex([
    (r'.*volumes/(HST.x_xxxx)(|_v.+)/(HST.._....)/(DATA/VISIT_../.{9}).*', 0,
            [r'volumes/\1*/\3/\4*',
             r'previews/\1/\3/\4_full.jpg',
             r'previews/\1/\3/\4_med.jpg',
             r'previews/\1/\3/\4_small.jpg',
             r'previews/\1/\3/\4_thumb.jpg',
             r'metadata/\1/\3/\3_index.lbl',
             r'metadata/\1/\3/\3_index.tab',
             r'metadata/\1/\3/\3_hstfiles.lbl',
             r'metadata/\1/\3/\3_hstfiles.tab',
            ])
])

##########################################################################################
# OPUS_ID
##########################################################################################

opus_id = translator.TranslatorByRegex([
    # Associated HST products share an OPUS ID based on the first nine characters of the file's basename.
    (r'.*/HSTI(.)_(....)/DATA/VISIT_../(\w{9})\w*\..*', 0, r'hst-\1\2-wfc3-#LOWER#\3'),
    (r'.*/HSTJ(.)_(....)/DATA/VISIT_../(\w{9})\w*\..*', 0, r'hst-\1\2-acs-#LOWER#\3'),
    (r'.*/HSTN(.)_(....)/DATA/VISIT_../(\w{9})\w*\..*', 0, r'hst-\1\2-nicmos-#LOWER#\3'),
    (r'.*/HSTO(.)_(....)/DATA/VISIT_../(\w{9})\w*\..*', 0, r'hst-\1\2-stis-#LOWER#\3'),
    (r'.*/HSTU(.)_(....)/DATA/VISIT_../(\w{9})\w*\..*', 0, r'hst-\1\2-wfpc2-#LOWER#\3'),
])

##########################################################################################
# OPUS_ID_TO_PRIMARY_LOGICAL_PATH
##########################################################################################

opus_id_to_primary_logical_path = translator.TranslatorByRegex([
    # The logical path returned points to the combined-detached label.
    (r'hst-(.)(....)-wfc3-(....)(..)(.*)',   0, r'volumes/HSTIx_xxxx/HSTI\1_\2/DATA/VISIT_#UPPER#\4/\3\4\5.LBL'),
    (r'hst-(.)(....)-acs-(....)(..)(.*)',    0, r'volumes/HSTJx_xxxx/HSTJ\1_\2/DATA/VISIT_#UPPER#\4/\3\4\5.LBL'),
    (r'hst-(.)(....)-nicmos-(....)(..)(.*)', 0, r'volumes/HSTNx_xxxx/HSTN\1_\2/DATA/VISIT_#UPPER#\4/\3\4\5.LBL'),
    (r'hst-(.)(....)-stis-(....)(..)(.*)',   0, r'volumes/HSTOx_xxxx/HSTO\1_\2/DATA/VISIT_#UPPER#\4/\3\4\5.LBL'),
    (r'hst-(.)(....)-wfpc2-(....)(..)(.*)',  0, r'volumes/HSTUx_xxxx/HSTU\1_\2/DATA/VISIT_#UPPER#\4/\3\4\5.LBL'),
])

##########################################################################################
# FILESPEC_TO_BUNDLESET
##########################################################################################

filespec_to_bundleset = translator.TranslatorByRegex([
    (r'HST([A-Z])[01]_\d{4}.*', 0, r'HST\1x_xxxx'),
])

##########################################################################################
# Subclass definition
##########################################################################################

class HSTxx_xxxx(pds3file.Pds3File):
    """The ``Pds3File`` subclass for HSTxx_xxxx.

    The class body wires this module's rule tables onto the class attributes
    ``Pds3File`` reads. Where a table is added to the inherited one, a lookup tries
    this module's patterns first and falls through to the defaults; where it is
    assigned outright there is no fall-through. The module tail registers the class
    in ``Pds3File.SUBCLASSES`` under the key
    "HSTxx_xxxx". The module docstring describes the volume set and every table.

    It also sets ``FILENAME_KEYLEN`` to 9, so that the several previews of one
    observation group together.
    """

    pds3file.Pds3File.VOLSET_TRANSLATOR = translator.TranslatorByRegex([('HST.x_xxxx', re.I, 'HSTxx_xxxx')]) + \
                                          pds3file.Pds3File.VOLSET_TRANSLATOR

    DESCRIPTION_AND_ICON = description_and_icon_by_regex + pds3file.Pds3File.DESCRIPTION_AND_ICON
    SPLIT_RULES = split_rules + pds3file.Pds3File.SPLIT_RULES
    VIEW_OPTIONS = view_options + pds3file.Pds3File.VIEW_OPTIONS
    NEIGHBORS = neighbors + pds3file.Pds3File.NEIGHBORS

    OPUS_TYPE = opus_type + pds3file.Pds3File.OPUS_TYPE
    OPUS_PRODUCTS = opus_products + pds3file.Pds3File.OPUS_PRODUCTS
    OPUS_ID = opus_id
    OPUS_ID_TO_PRIMARY_LOGICAL_PATH = opus_id_to_primary_logical_path

    VIEWABLES = {'default': default_viewables}

    ASSOCIATIONS = pds3file.Pds3File.ASSOCIATIONS.copy()
    ASSOCIATIONS['volumes']   += associations_to_volumes
    ASSOCIATIONS['previews']  += associations_to_previews
    ASSOCIATIONS['metadata']  += associations_to_metadata
    ASSOCIATIONS['documents'] += associations_to_documents

    FILENAME_KEYLEN = 9     # trim off suffixes

# Global attribute shared by all subclasses
pds3file.Pds3File.OPUS_ID_TO_SUBCLASS = translator.TranslatorByRegex([(r'hst-.*', 0, HSTxx_xxxx)]) + \
                                        pds3file.Pds3File.OPUS_ID_TO_SUBCLASS

pds3file.Pds3File.FILESPEC_TO_BUNDLESET = filespec_to_bundleset + pds3file.Pds3File.FILESPEC_TO_BUNDLESET

##########################################################################################
# Update the global dictionary of subclasses
##########################################################################################

pds3file.Pds3File.SUBCLASSES['HSTxx_xxxx'] = HSTxx_xxxx
