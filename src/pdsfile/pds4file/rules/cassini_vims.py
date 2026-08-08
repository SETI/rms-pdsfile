##########################################################################################
# pds4file/rules/cassini_vims.py
##########################################################################################

"""Rules for the cassini_vims bundle set: Cassini VIMS cubes in PDS4.

The cassini_vims bundle set holds the Cassini VIMS cubes as PDS4 bundles. The
archive layout described in this module's header comment has two bundles,
cassini_vims_cruise and cassini_vims_saturn, each holding a ``data_raw/``
collection of raw VIMS data and a ``browse_raw/`` collection beside it, together
with the non-data collections ``calibration/``, ``context/``, ``document/`` and
``xml_schema/`` and the ``bundle.xml`` label beside them. The cruise bundle is
packaged as a single
archive. The Saturn bundle is split into 89: one for the non-data, non-browse
collections, and then one per leading three-digit clock block for each of the raw
data and raw browse collections, 44 blocks each. The PDS3 form of the same
observations is served by `pds3file/rules/COVIMS_0xxx.py`.

The rule tables written against PDS4 ``bundles/cassini_vims`` paths:

* ``default_viewables`` -- points a data file at its preview images.
* ``associations_to_bundles``, ``associations_to_previews``,
  ``associations_to_metadata`` and ``associations_to_documents`` -- cross the
  bundles, previews, metadata and documents trees for one cube. The documents entry
  also sends a preview to the VIMS preview interpretation guide.
* ``opus_id`` -- builds an OPUS ID from a PDS4 data file name, in two alternatives.
  A cube filed under a clock-prefixed subdirectory gives
  co-vims-v<clock>_<sub-observation>; one filed directly under the clock block gives
  co-vims-v<clock>.
* ``filespec_to_bundleset`` -- maps a file specification whose first component is
  "cassini_vims" followed by an underscore to the bundle set name cassini_vims.
* ``ARCHIVE_PATHS_DICT``, ``archive_paths`` and ``archive_dirs`` -- the archive
  layout. The dictionary holds, per bundle and per collection kind, the archive file
  name patterns; ``archive_paths`` maps a bundle set, bundle or collection path to
  the archives covering it, and ``archive_dirs`` maps an archive file back to the
  directories inside it.

Eight tables here are byte-identical to the tables of the same name in
`pds3file/rules/COISS_xxxx.py`, which serves Cassini ISS rather than VIMS:
``description_and_icon_by_regex``, ``view_options``, ``neighbors``, ``sort_key``,
``opus_type``, ``opus_format``, ``opus_products`` and
``opus_id_to_primary_logical_path``. Five of the eight key on PDS3 paths -- on
``volumes/`` or on a COISS volume ID; ``sort_key`` keys on basenames and
``opus_format`` on file extensions, so those two are not PDS3-specific; and
``opus_id_to_primary_logical_path`` keys on an OPUS ID and *returns* a PDS3 path
rather than matching one. Four rules of ``description_and_icon_by_regex`` carry no
PDS3 anchor at all and do fire for a ``bundles/cassini_vims`` path, naming its
thumbnail and full-size browse directories. What
``description_and_icon_by_regex`` returns is the Cassini ISS descriptions, naming
narrow- and wide-angle images and the CISSCAL software, and ``opus_type`` files
products under the "Cassini ISS" OPUS category.
"""

import re

import translator

import pdsfile.pds4file as pds4file

##########################################################################################
# DESCRIPTION_AND_ICON
##########################################################################################

description_and_icon_by_regex = translator.TranslatorByRegex([
    (r'volumes/.*/data/.*/N[0-9_]+\.IMG',                        0, ('Narrow-angle image, VICAR',      'IMAGE'   )),
    (r'volumes/.*/data/.*/W[0-9_]+\.IMG',                        0, ('Wide-angle image, VICAR',        'IMAGE'   )),
    (r'volumes/.*/data/.*/extras(/\w+)*(|/)',                    0, ('Preview image collection',       'BROWDIR' )),
    (r'volumes/.*/data/.*/extras/.*\.(jpeg|jpeg_small|tiff)',    0, ('Preview image',                  'BROWSE'  )),
    (r'volumes/.*/COISS_0011/document/.*/[0-9]+\.[0-9]+(|/)',    0, ('Calibration report',             'INFODIR' )),
    (r'volumes/.*/data(|/\w*)',                                  0, ('Images grouped by SC clock',     'IMAGEDIR')),
    (r'calibrated/.*_calib\.img',                                0, ('Calibrated image, VICAR',        'IMAGE'   )),
    (r'calibrated/.*/data(|/\w+)',                               0, ('Calibrated images by SC clock',  'IMAGEDIR')),
    (r'calibrated/\w+(|/\w+)',                                   0, ('Calibrated image collection',    'IMAGEDIR')),
    (r'.*/thumbnail(/\w+)*',                                     0, ('Small browse images',            'BROWDIR' )),
    (r'.*/thumbnail/.*\.(gif|jpg|jpeg|jpeg_small|tif|tiff|png)', 0, ('Small browse image',             'BROWSE'  )),
    (r'.*/(tiff|full)(/\w+)*',                                   0, ('Full-size browse images',        'BROWDIR' )),
    (r'.*/(tiff|full)/.*\.(tif|tiff|png)',                       0, ('Full-size browse image',         'BROWSE'  )),
    (r'volumes/COISS_0xxx.*/COISS_0011/document/report',         0, ('&#11013; <b>ISS Calibration Report</b>',
                                                                                                       'INFO')),
    (r'(volumes/COISS_0xxx.*/COISS_0011/document/report/index.html)', 0,
            ('&#11013; <b>CLICK "index.html"</b> to view the ISS Calibration Report', 'INFO')),
    (r'volumes/COISS_0xxx.*/COISS_0011/document/.*user_guide.*\.pdf',
                                                                 0, ('&#11013; <b>ISS User Guide</b>', 'INFO')),
    (r'volumes/COISS_0xxx.*/COISS_0011/extras',                  0, ('CISSCAL calibration software',   'CODE')),
    (r'volumes/COISS_0xxx.*/COISS_0011/extras/cisscal',          0, ('CISSCAL source code (IDL)',      'CODE')),
    (r'volumes/COISS_0xxx.*/COISS_0011/extras/cisscal\.tar\.gz', 0, ('CISSCAL source code (download)', 'TARBALL')),
])

##########################################################################################
# VIEWABLES
##########################################################################################

default_viewables = translator.TranslatorByRegex([
    (r'.*/(cassini_vims/cassini_vims\w*/data(.*|_[a-z]*])/.*)\.[a-z]{3}', 0,
        [r'previews/\1_full.png',
         r'previews/\1_med.png',
         r'previews/\1_small.png',
         r'previews/\1_thumb.png',
        ]),
])

##########################################################################################
# ASSOCIATIONS
##########################################################################################

associations_to_bundles = translator.TranslatorByRegex([
    (r'.*/(cassini_vims/cassini_vims\w*)/(data|browse)(.*|_[a-z]*]/.*)\.[a-z]{3}', 0,
        [r'bundles/\1/data\3.qub',
         r'bundles/\1/data\3.xml',
         r'bundles/\1/browse\3-full.png',
         r'bundles/\1/browse\3-full.xml',
        ]),
    (r'documents/cassini_vims.*', 0,
        [r'bundles/cassini_vims',
         r'bundles/cassini_vims',
         r'bundles/cassini_vims',
        ]),
])

associations_to_previews = translator.TranslatorByRegex([
    (r'.*/(cassini_vims/cassini_vims\w*/(data|browse)(.*|_[a-z]*])/.*)\.[a-z]{3}', 0,
        [r'previews/\1_full.png',
         r'previews/\1_med.png',
         r'previews/\1_small.png',
         r'previews/\1_thumb.png',
        ]),
])

associations_to_metadata = translator.TranslatorByRegex([
    (r'.*/(cassini_vims)/(cassini_vims\w*)/(data|browse)(.*|_[a-z]*])/(.*)\.[a-z]{3}', 0,
        [r'metadata/\1/\2/\2_index.tab/\5',
         r'metadata/\1/\2/\2_supplemental_index.tab/\5',
         r'metadata/\1/\2/\2_ring_summary.tab/\5',
         r'metadata/\1/\2/\2_moon_summary.tab/\5',
         r'metadata/\1/\2/\2_saturn_summary.tab/\5',
         r'metadata/\1/\2/\2_jupiter_summary.tab/\5',
        ]),
])

associations_to_documents = translator.TranslatorByRegex([
    (r'bundles/cassini_vims/.*', 0,
         r'documents/cassini_vims/*'),
    (r'bundles/cassini_vims', 0,
         r'documents/cassini_vims'),
    (r'previews/cassini_vims.*', 0,
        r'documents/cassini_vims/VIMS-Preview-Interpretation-Guide.pdf'),
])

##########################################################################################
# VIEW_OPTIONS (grid_view_allowed, multipage_view_allowed, continuous_view_allowed)
##########################################################################################

view_options = translator.TranslatorByRegex([
    (r'.*/COISS_[12].../(data|extras/w+)(|/\w+)',     0, (True, True,  True )),
    (r'.*/COISS_3.../(data|extras/w+)/(images|maps)', 0, (True, False, False)),
])

##########################################################################################
# NEIGHBORS
##########################################################################################

neighbors = translator.TranslatorByRegex([
    (r'(.*)/COISS_[12]xxx(.*)/COISS_..../(data|extras/\w+)/\w+', 0, r'\1/COISS_[12]xxx\2/*/\3/*'),
    (r'(.*)/COISS_[12]xxx(.*)/COISS_..../(data|extras/\w+)',     0, r'\1/COISS_[12]xxx\2/*/\3'),
    (r'(.*)/COISS_[12]xxx(.*)/COISS_....',                       0, r'\1/COISS_[12]xxx\2/*'),

    (r'volumes/COISS_0xxx(|_v[0-9\.]+)/COISS_..../data',               0, r'volumes/COISS_0xxx\1/*/data'),
    (r'volumes/COISS_0xxx(|_v[0-9\.]+)/COISS_..../data/(\w+)',         0, r'volumes/COISS_0xxx\1/*/data/\2'),
    (r'volumes/COISS_0xxx(|_v[0-9\.]+)/COISS_..../data/(\w+/\w+)',     0, r'volumes/COISS_0xxx\1/*/data/\2'),
    (r'volumes/COISS_0xxx(|_v[0-9\.]+)/COISS_..../data/(\w+/\w+)/\w+', 0, r'volumes/COISS_0xxx\1/*/data/\2/*'),
])

##########################################################################################
# SORT_KEY
##########################################################################################

sort_key = translator.TranslatorByRegex([

    # Skips over N or W, placing files into chronological order
    (r'([NW])([0-9]{10})(.*)_full.png',  0, r'\2\1\3_1full.jpg'),
    (r'([NW])([0-9]{10})(.*)_med.jpg',   0, r'\2\1\3_2med.jpg'),
    (r'([NW])([0-9]{10})(.*)_small.jpg', 0, r'\2\1\3_3small.jpg'),
    (r'([NW])([0-9]{10})(.*)_thumb.jpg', 0, r'\2\1\3_4thumb.jpg'),
    (r'([NW])([0-9]{10})(.*)', 0, r'\2\1\3'),

    # Used inside COISS_0011/document/report
    ('index.html', 0, '000index.html'),
])

##########################################################################################
# OPUS_TYPE
##########################################################################################

opus_type = translator.TranslatorByRegex([
    (r'volumes/.*\.(IMG|LBL)',                      0, ('Cassini ISS',  0,  'coiss_raw',    'Raw Image',                 True )),
    (r'calibrated/.*_CALIB\.(IMG|LBL)',             0, ('Cassini ISS', 10,  'coiss_calib',  'Calibrated Image',          True )),
    (r'volumes/.*/extras/thumbnail/.*\.jpeg_small', 0, ('Cassini ISS', 110, 'coiss_thumb',  'Extra Preview (thumbnail)', False)),
    (r'volumes/.*/extras/browse/.*\.jpeg',          0, ('Cassini ISS', 120, 'coiss_medium', 'Extra Preview (medium)',    False)),
    (r'volumes/.*/extras/(tiff|full)/.*\.\w+',      0, ('Cassini ISS', 130, 'coiss_full',   'Extra Preview (full)',      False)),
    (r'volumes/.*/extras/(tiff|full)/.*\.\w+',      0, ('Cassini ISS', 130, 'coiss_full',   'Extra Preview (full)',      False)),
    # Documentation
    (r'documents/COISS_0xxx/.*',                    0, ('Cassini ISS', 140, 'coiss_documentation', 'Documentation', False)),
])

##########################################################################################
# OPUS_FORMAT
##########################################################################################

opus_format = translator.TranslatorByRegex([
    (r'.*\.IMG',        0, ('Binary', 'VICAR')),
    (r'.*\.jpeg_small', 0, ('Binary', 'JPEG')),
])

##########################################################################################
# OPUS_PRODUCTS
##########################################################################################

opus_products = translator.TranslatorByRegex([
    (r'.*/(COISS_[12]xxx)(|_v[0-9\.]+)/(COISS_[12]...)/data/(\w+/[NW][0-9]{10}_[0-9]+).*', 0,
            [r'volumes/\1*/\3/data/\4.IMG',
             r'volumes/\1*/\3/data/\4.LBL',
             r'volumes/\1*/\3/extras/thumbnail/\4.IMG.jpeg_small',
             r'volumes/\1*/\3/extras/browse/\4.IMG.jpeg',
             r'volumes/\1*/\3/extras/full/\4.IMG.png',
             r'volumes/\1*/\3/extras/tiff/\4.IMG.tiff',
             r'calibrated/\1*/\3/data/\4_CALIB.IMG',
             r'calibrated/\1*/\3/data/\4_CALIB.LBL',
             r'previews/\1/\3/data/\4_full.png',
             r'previews/\1/\3/data/\4_med.jpg',
             r'previews/\1/\3/data/\4_small.jpg',
             r'previews/\1/\3/data/\4_thumb.jpg',
             r'metadata/\1/\3/\3_moon_summary.tab',
             r'metadata/\1/\3/\3_moon_summary.lbl',
             r'metadata/\1/\3/\3_ring_summary.tab',
             r'metadata/\1/\3/\3_ring_summary.lbl',
             r'metadata/\1/\3/\3_saturn_summary.tab',
             r'metadata/\1/\3/\3_saturn_summary.lbl',
             r'metadata/\1/\3/\3_jupiter_summary.tab',
             r'metadata/\1/\3/\3_jupiter_summary.lbl',
             r'metadata/\1/\3/\3_inventory.csv',
             r'metadata/\1/\3/\3_inventory.lbl',
             r'metadata/\1/\3/\3_index.tab',
             r'metadata/\1/\3/\3_index.lbl',
             r'documents/COISS_0xxx/*.[!lz]*',
            ]),
])

##########################################################################################
# OPUS_ID
##########################################################################################

opus_id = translator.TranslatorByRegex([
    (r'.*/cassini_vims/cassini_vims\w*/[a-z]*_raw/\d{3}xxxxxxx/\d{5}xxxxx/\d{10}_xxx/(\d{10}_\d{3}).*[a-z]{3}|.*/cassini_vims/cassini_vims\w*/[a-z]*_raw/\d{3}xxxxxxx/\d{5}xxxxx/(\d{10}).*[a-z]{3}', 0, r'co-vims-v\1\2'),
]) # Suffix "_vis", "_ir" handled elsewhere in code.

##########################################################################################
# FILESPEC_TO_BUNDLESET
##########################################################################################

filespec_to_bundleset = translator.TranslatorByRegex([
    (r'(cassini_vims)_.*', 0, r'\1'),
])

##########################################################################################
# OPUS_ID_TO_PRIMARY_LOGICAL_PATH
##########################################################################################

# By identifying the first three digits of the spacecraft clock with a range of volumes, we speed things up quite a bit
opus_id_to_primary_logical_path = translator.TranslatorByRegex([
    (r'co-iss-([nw]188.*)',     0,  r'volumes/COISS_2xxx/COISS_211[5-6]/data/*/#UPPER#\1_*.IMG'),
    (r'co-iss-([nw]187.*)',     0,  r'volumes/COISS_2xxx/COISS_211[2-5]/data/*/#UPPER#\1_*.IMG'),
    (r'co-iss-([nw]186.*)',     0, [r'volumes/COISS_2xxx/COISS_2109/data/*/#UPPER#\1_*.IMG',
                                    r'volumes/COISS_2xxx/COISS_211[0-2]/data/*/#UPPER#\1_*.IMG']),
    (r'co-iss-([nw]185.*)',     0,  r'volumes/COISS_2xxx/COISS_210[6-9]/data/*/#UPPER#\1_*.IMG'),
    (r'co-iss-([nw]184.*)',     0,  r'volumes/COISS_2xxx/COISS_210[4-6]/data/*/#UPPER#\1_*.IMG'),
    (r'co-iss-([nw]183.*)',     0,  r'volumes/COISS_2xxx/COISS_210[1-4]/data/*/#UPPER#\1_*.IMG'),
    (r'co-iss-([nw]182.*)',     0, [r'volumes/COISS_2xxx/COISS_209[8-9]/data/*/#UPPER#\1_*.IMG',
                                    r'volumes/COISS_2xxx/COISS_210[0-1]/data/*/#UPPER#\1_*.IMG']),
    (r'co-iss-([nw]181.*)',     0,  r'volumes/COISS_2xxx/COISS_209[6-8]/data/*/#UPPER#\1_*.IMG'),
    (r'co-iss-([nw]180.*)',     0,  r'volumes/COISS_2xxx/COISS_209[4-6]/data/*/#UPPER#\1_*.IMG'),
    (r'co-iss-([nw]179.*)',     0,  r'volumes/COISS_2xxx/COISS_209[1-4]/data/*/#UPPER#\1_*.IMG'),
    (r'co-iss-([nw]178.*)',     0,  r'volumes/COISS_2xxx/COISS_209[0-1]/data/*/#UPPER#\1_*.IMG'),
    (r'co-iss-([nw]177.*)',     0, [r'volumes/COISS_2xxx/COISS_208[8-9]/data/*/#UPPER#\1_*.IMG',
                                    r'volumes/COISS_2xxx/COISS_2090/data/*/#UPPER#\1_*.IMG']),
    (r'co-iss-([nw]176.*)',     0,  r'volumes/COISS_2xxx/COISS_208[6-8]/data/*/#UPPER#\1_*.IMG'),
    (r'co-iss-([nw]175.*)',     0,  r'volumes/COISS_2xxx/COISS_208[3-6]/data/*/#UPPER#\1_*.IMG'),
    (r'co-iss-([nw]174.*)',     0,  r'volumes/COISS_2xxx/COISS_208[0-3]/data/*/#UPPER#\1_*.IMG'),
    (r'co-iss-([nw]173.*)',     0, [r'volumes/COISS_2xxx/COISS_207[8-9]/data/*/#UPPER#\1_*.IMG',
                                    r'volumes/COISS_2xxx/COISS_2080/data/*/#UPPER#\1_*.IMG']),
    (r'co-iss-([nw]172.*)',     0,  r'volumes/COISS_2xxx/COISS_207[6-8]/data/*/#UPPER#\1_*.IMG'),
    (r'co-iss-([nw]171.*)',     0,  r'volumes/COISS_2xxx/COISS_207[2-6]/data/*/#UPPER#\1_*.IMG'),
    (r'co-iss-([nw]170.*)',     0,  r'volumes/COISS_2xxx/COISS_207[1-2]/data/*/#UPPER#\1_*.IMG'),
    (r'co-iss-([nw]169.*)',     0, [r'volumes/COISS_2xxx/COISS_2069/data/*/#UPPER#\1_*.IMG',
                                    r'volumes/COISS_2xxx/COISS_207[0-1]/data/*/#UPPER#\1_*.IMG']),
    (r'co-iss-([nw]168.*)',     0,  r'volumes/COISS_2xxx/COISS_206[7-9]/data/*/#UPPER#\1_*.IMG'),
    (r'co-iss-([nw]167.*)',     0,  r'volumes/COISS_2xxx/COISS_206[6-7]/data/*/#UPPER#\1_*.IMG'),
    (r'co-iss-([nw]166.*)',     0,  r'volumes/COISS_2xxx/COISS_206[4-6]/data/*/#UPPER#\1_*.IMG'),
    (r'co-iss-([nw]165.*)',     0,  r'volumes/COISS_2xxx/COISS_206[2-4]/data/*/#UPPER#\1_*.IMG'),
    (r'co-iss-([nw]164.*)',     0, [r'volumes/COISS_2xxx/COISS_2059/data/*/#UPPER#\1_*.IMG',
                                    r'volumes/COISS_2xxx/COISS_206[0-2]/data/*/#UPPER#\1_*.IMG']),
    (r'co-iss-([nw]163.*)',     0,  r'volumes/COISS_2xxx/COISS_205[7-9]/data/*/#UPPER#\1_*.IMG'),
    (r'co-iss-([nw]162.*)',     0,  r'volumes/COISS_2xxx/COISS_205[4-7]/data/*/#UPPER#\1_*.IMG'),
    (r'co-iss-([nw]161.*)',     0,  r'volumes/COISS_2xxx/COISS_205[2-4]/data/*/#UPPER#\1_*.IMG'),
    (r'co-iss-([nw]160.*)',     0, [r'volumes/COISS_2xxx/COISS_204[8-9]/data/*/#UPPER#\1_*.IMG',
                                    r'volumes/COISS_2xxx/COISS_205[0-2]/data/*/#UPPER#\1_*.IMG']),
    (r'co-iss-([nw]159.*)',     0,  r'volumes/COISS_2xxx/COISS_204[5-8]/data/*/#UPPER#\1_*.IMG'),
    (r'co-iss-([nw]158.*)',     0,  r'volumes/COISS_2xxx/COISS_204[1-5]/data/*/#UPPER#\1_*.IMG'),
    (r'co-iss-([nw]157.*)',     0, [r'volumes/COISS_2xxx/COISS_203[8-9]/data/*/#UPPER#\1_*.IMG',
                                    r'volumes/COISS_2xxx/COISS_204[0-1]/data/*/#UPPER#\1_*.IMG']),
    (r'co-iss-([nw]156.*)',     0,  r'volumes/COISS_2xxx/COISS_203[2-8]/data/*/#UPPER#\1_*.IMG'),
    (r'co-iss-([nw]155.*)',     0, [r'volumes/COISS_2xxx/COISS_2029/data/*/#UPPER#\1_*.IMG',
                                    r'volumes/COISS_2xxx/COISS_203[0-2]/data/*/#UPPER#\1_*.IMG']),
    (r'co-iss-([nw]154.*)',     0,  r'volumes/COISS_2xxx/COISS_202[6-9]/data/*/#UPPER#\1_*.IMG'),
    (r'co-iss-([nw]153.*)',     0,  r'volumes/COISS_2xxx/COISS_202[3-6]/data/*/#UPPER#\1_*.IMG'),
    (r'co-iss-([nw]152.*)',     0,  r'volumes/COISS_2xxx/COISS_202[0-3]/data/*/#UPPER#\1_*.IMG'),
    (r'co-iss-([nw]151.*)',     0, [r'volumes/COISS_2xxx/COISS_201[6-9]/data/*/#UPPER#\1_*.IMG',
                                    r'volumes/COISS_2xxx/COISS_2020/data/*/#UPPER#\1_*.IMG']),
    (r'co-iss-([nw]150.*)',     0,  r'volumes/COISS_2xxx/COISS_201[4-6]/data/*/#UPPER#\1_*.IMG'),
    (r'co-iss-([nw]149.*)',     0,  r'volumes/COISS_2xxx/COISS_201[0-4]/data/*/#UPPER#\1_*.IMG'),
    (r'co-iss-([nw]148.*)',     0, [r'volumes/COISS_2xxx/COISS_200[8-9]/data/*/#UPPER#\1_*.IMG',
                                    r'volumes/COISS_2xxx/COISS_2010/data/*/#UPPER#\1_*.IMG']),
    (r'co-iss-([nw]147.*)',     0,  r'volumes/COISS_2xxx/COISS_200[5-8]/data/*/#UPPER#\1_*.IMG'),
    (r'co-iss-([nw]146.*)',     0,  r'volumes/COISS_2xxx/COISS_200[1-5]/data/*/#UPPER#\1_*.IMG'),
    (r'co-iss-([nw]145.*)',     0, [r'volumes/COISS_1xxx/COISS_1009/data/*/#UPPER#\1_*.IMG',
                                    r'volumes/COISS_2xxx/COISS_2001/data/*/#UPPER#\1_*.IMG']),
    (r'co-iss-([nw]144.*)',     0,  r'volumes/COISS_1xxx/COISS_100[8-9]/data/*/#UPPER#\1_*.IMG'),
    (r'co-iss-([nw]14[123].*)', 0,  r'volumes/COISS_1xxx/COISS_1008/data/*/#UPPER#\1_*.IMG'),
    (r'co-iss-([nw]140.*)',     0,  r'volumes/COISS_1xxx/COISS_100[7-8]/data/*/#UPPER#\1_*.IMG'),
    (r'co-iss-([nw]13[789].*)', 0,  r'volumes/COISS_1xxx/COISS_1007/data/*/#UPPER#\1_*.IMG'),
    (r'co-iss-([nw]136.*)',     0,  r'volumes/COISS_1xxx/COISS_100[6-7]/data/*/#UPPER#\1_*.IMG'),
    (r'co-iss-([nw]135.*)',     0,  r'volumes/COISS_1xxx/COISS_100[1-6]/data/*/#UPPER#\1_*.IMG'),
    (r'co-iss-([nw]13[0-4].*)', 0,  r'volumes/COISS_1xxx/COISS_1001/data/*/#UPPER#\1_*.IMG'),
    (r'co-iss-([nw]12.*)',      0,  r'volumes/COISS_1xxx/COISS_1001/data/*/#UPPER#\1_*.IMG'),
])

##########################################################################################
# Archives
##########################################################################################
# TODO: split regex matched pattern group 1 (bundles|metadata|previews|diagrams) into
# separate entries if we use different archive file names for different categories

# Bundle layout:
# - Each high-level Cassini VIMS bundle (e.g., 'cassini_vims_cruise', 'cassini_vims_saturn')
#   is organized into multiple collections:
#   - 'bundle.xml', 'calibration', 'context', 'document', 'xml_schema' (non-data, non-browse)
#   - 'browse_raw/...': preview/browse collections for raw VIMS data
#   - 'data_raw/...': the primary raw science data collections
#
# How archives are split:
# - For 'cassini_vims_cruise':
#   - All content is packaged into a single monolithic archive per bundle
#   - Archive name: '{bundle_name}.tar.gz' (e.g., 'cassini_vims_cruise.tar.gz')
#   - This simpler approach is used because cruise data volume is smaller
# - For 'cassini_vims_saturn':
#   - Similar to ISS, the bundle is split into multiple archives for better manageability
#   - 'other_col' archives:
#     - Contain bundle.xml, calibration, context, document, and xml_schema collections
#     - Always a single archive per bundle: 'bundle_xml_non_data_browse_collections.tar.gz'
#   - 'browse_raw' archives:
#     - The raw browse collection is split by leading spacecraft clock block
#     - One archive per 1xx clock block where 45 <= xx < 89
#     - Each pattern 'browse_raw_1{num}xxxxxxx.tar.gz' groups all files whose
#       first 3 SCET digits are '1{num}' into a single archive
#   - 'data_raw' archives:
#     - Mirrored strategy to 'browse_raw', but for the underlying raw data collections
#     - Uses the same 1xx clock block range (45-89) as browse_raw
#
# ARCHIVE_PATHS_DICT: A dictionary that organizes archive path patterns by bundle name
# and collection type.
# Dictionary structure:
# - Top-level keys are bundle names (e.g., 'cassini_vims_cruise', 'cassini_vims_saturn')
# - Cruise bundles use an 'all' key containing a single archive pattern
# - Saturn bundles contain sub-dictionaries keyed by collection type:
#     'other_col', 'browse_raw', 'data_raw'
# - Values are lists of regex pattern strings that will be expanded into archive file
#   paths. The patterns use regex backreferences (\1, \2, \3) that are filled from the
#   input logical path (e.g., category, bundle set, and bundle name) when archive_paths
#   is called.
ARCHIVE_PATHS_DICT = {
    'cassini_vims_cruise': {
        'all': [
            r'archives-\1/\2/\3/\3.tar.gz'
        ],
    },
    'cassini_vims_saturn': {
        'other_col': [
            r'archives-\1/\2/bundle_xml_non_data_browse_collections.tar.gz'
        ],
        'browse_raw': [
            *[rf'archives-\1/\2/browse_raw_1{num}xxxxxxx.tar.gz' for num in range(45, 89)],
            # r'archives-\1/\2/browse_raw_col_xml_csv.tar.gz',
        ],
        'data_raw': [
            *[rf'archives-\1/\2/data_raw_1{num}xxxxxxx.tar.gz' for num in range(45, 89)],
            # r'archives-\1/\2/data_raw_col_xml_csv.tar.gz',
        ],
    }
}

# archive_paths: A TranslatorByRegex object that maps logical paths of bundle sets,
# bundles, or bundle collections to lists of logical paths of archive file names.
# When given a PdsFile logical path (e.g., 'bundles/cassini_vims/cassini_vims_saturn'),
# this translator returns the corresponding archive file paths (e.g.,
# 'archives-bundles/cassini_vims/cassini_vims_saturn/browse_raw_1xxxxxxx.tar.gz').
# The translator uses regex patterns to match input paths and extracts archive path
# patterns from ARCHIVE_PATHS_DICT based on the bundle set and collection type.
# These archive paths are used by the archive_paths() method in Pds4File to determine
# which archive files are associated with a given bundle or bundle set.
archive_paths = translator.TranslatorByRegex([
    # input path is the whole cassini_vims bundle set
    (r'.*(bundles|metadata|previews|diagrams)/(cassini_vims)(|/)$', 0, [
        r'archives-\1/\2/\2_cruise/\2_cruise.tar.gz',
        r'archives-\1/\2/\2_saturn/bundle_xml_non_data_browse_collections.tar.gz',
        *[rf'archives-\1/\2/\2_saturn/browse_raw_1{num}xxxxxxx.tar.gz' for num in range(45, 89)],
        *[rf'archives-\1/\2/\2_saturn/data_raw_1{num}xxxxxxx.tar.gz' for num in range(45, 89)],
    ]),
    ### cassini_vims_cruise ###
    (r'.*(bundles|metadata|previews|diagrams)/(cassini_vims)/(cassini_vims_cruise)(|/)$', 0,
        ARCHIVE_PATHS_DICT['cassini_vims_cruise']['all']),

    ### cassini_vims_saturn ###
    # input path is a bundle path
    (r'.*(bundles|metadata|previews|diagrams)/(cassini_vims/cassini_vims_saturn)(|/)$', 0, [
        # bundle xml, context, document, and xml_schema
        *ARCHIVE_PATHS_DICT['cassini_vims_saturn']['other_col'],
        # browse_raw
        *ARCHIVE_PATHS_DICT['cassini_vims_saturn']['browse_raw'],
        # data_raw
        *ARCHIVE_PATHS_DICT['cassini_vims_saturn']['data_raw'],
    ]),
    # input path is a bundle collection path
    # bundle xml, calibration, context, document, and xml_schema
    (r'.*(bundles|metadata|previews|diagrams)/(cassini_vims/cassini_vims_saturn)/(calibration|context|document|xml_schema|bundle\.xml)', 0,
        ARCHIVE_PATHS_DICT['cassini_vims_saturn']['other_col']),
    # browse_raw
    (r'.*(bundles|metadata|previews|diagrams)/(cassini_vims/cassini_vims_saturn)/browse_(\w*)', 0,
        ARCHIVE_PATHS_DICT['cassini_vims_saturn']['browse_raw']),
    # data_raw
    (r'.*(bundles|metadata|previews|diagrams)/(cassini_vims/cassini_vims_saturn)/data_(\w*)', 0,
        ARCHIVE_PATHS_DICT['cassini_vims_saturn']['data_raw']),

])

# archive_dirs: A TranslatorByRegex object that maps logical paths of archive files
# to lists of logical paths of directories included in those archives. When given
# an archive file path (e.g., 'archives-bundles/cassini_vims/cassini_vims_saturn/
# browse_raw_1xxxxxxx.tar.gz'), this translator returns the directory paths that are
# packaged within that archive (e.g., 'bundles/cassini_vims/cassini_vims_saturn/
# browse_raw/1xxxxxxx'). This mapping is used by the archive_dirs() method in Pds4File
# to determine which directories are included in each archive file.
archive_dirs = translator.TranslatorByRegex([
    ### cassini_vims_cruise ###
    (r'.*archives-(.*/cassini_vims)/(cassini_vims_cruise)/.*\.tar\.gz', 0, [r'\1/\2']),

    ### cassini_vims_saturn ###
    # bundle xml, calibration, context, document, and xml_schema collections
    (r'.*archives-(.*/cassini_vims)/(cassini_vims_saturn)/bundle_xml_non_data_browse_collections\.tar\.gz', 0,
        [r'\1/\2/bundle.xml',
         r'\1/\2/document',
         r'\1/\2/xml_schema',
         r'\1/\2/calibration',
         r'\1/\2/context']
    ),
    # browse_raw and data_raw
    (r'.*archives-(.*/cassini_vims)/(cassini_vims_\w+)/(\w+_raw)_1(\d\d)xxxxxxx\.tar\.gz', 0,
        [r'\1/\2/\3/1\4??xxxxx',
         r'\1/\2/\3/collection_\3.csv',
         r'\1/\2/\3/collection_\3.xml']
    ),
])

##########################################################################################
# Subclass definition
##########################################################################################

class cassini_vims(pds4file.Pds4File):
    """The ``Pds4File`` subclass for cassini_vims.

    The class body and the module tail install this module's rule tables on the class
    attributes ``Pds4File`` reads. `pds4file/rules/__init__.py` sets out the routes a
    table takes and which of them leaves the inherited rules in front. The class
    is registered in ``Pds4File.SUBCLASSES`` under the key
    "cassini_vims".
    The module docstring describes the bundle set and every table.
    """

    pds4file.Pds4File.VOLSET_TRANSLATOR = translator.TranslatorByRegex([('cassini_vims', re.I, 'cassini_vims')]) + \
                                          pds4file.Pds4File.VOLSET_TRANSLATOR

    DESCRIPTION_AND_ICON = description_and_icon_by_regex + pds4file.Pds4File.DESCRIPTION_AND_ICON
    VIEW_OPTIONS = view_options + pds4file.Pds4File.VIEW_OPTIONS
    NEIGHBORS = neighbors + pds4file.Pds4File.NEIGHBORS
    SORT_KEY = sort_key + pds4file.Pds4File.SORT_KEY

    OPUS_TYPE = opus_type + pds4file.Pds4File.OPUS_TYPE
    OPUS_FORMAT = opus_format + pds4file.Pds4File.OPUS_FORMAT
    OPUS_PRODUCTS = opus_products + pds4file.Pds4File.OPUS_PRODUCTS
    OPUS_ID = opus_id
    OPUS_ID_TO_PRIMARY_LOGICAL_PATH = opus_id_to_primary_logical_path

    VIEWABLES = {'default': default_viewables}

    ASSOCIATIONS = pds4file.Pds4File.ASSOCIATIONS.copy()
    ASSOCIATIONS['bundles']    += associations_to_bundles
    ASSOCIATIONS['previews']   += associations_to_previews
    ASSOCIATIONS['metadata']   += associations_to_metadata
    ASSOCIATIONS['documents']  += associations_to_documents

    ARCHIVE_PATHS = archive_paths + pds4file.Pds4File.ARCHIVE_PATHS
    ARCHIVE_DIRS = archive_dirs + pds4file.Pds4File.ARCHIVE_DIRS

    pds4file.Pds4File.FILESPEC_TO_BUNDLESET = filespec_to_bundleset + pds4file.Pds4File.FILESPEC_TO_BUNDLESET

# Global attribute shared by all subclasses
pds4file.Pds4File.OPUS_ID_TO_SUBCLASS = translator.TranslatorByRegex([(r'co-vims-.*', 0, cassini_vims)]) + \
                                        pds4file.Pds4File.OPUS_ID_TO_SUBCLASS

##########################################################################################
# Update the global dictionary of subclasses
##########################################################################################

pds4file.Pds4File.SUBCLASSES['cassini_vims'] = cassini_vims
