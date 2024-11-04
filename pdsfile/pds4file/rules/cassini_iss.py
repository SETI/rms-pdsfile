##########################################################################################
# pds4file/rules/cassini_iss.py
##########################################################################################

import pdsfile.pds4file as pds4file
import translator
import re

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
    (r'.*/(cassini_iss/cassini_iss\w*/data(.*|_[a-z]*])/.*)\.[a-z]{3}', 0,
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
    (r'.*/(cassini_iss/cassini_iss\w*)/(data|browse)(.*|_[a-z]*]/.*)\.[a-z]{3}', 0,
        [r'bundles/\1/data\3.img',
         r'bundles/\1/data\3.xml',
         r'bundles/\1/browse\3-full.png',
         r'bundles/\1/browse\3-full.xml',
        ]),
    (r'documents/cassini_iss.*', 0,
        [r'bundles/cassini_iss',
         r'bundles/cassini_iss',
         r'bundles/cassini_iss',
        ]),
])

associations_to_calibrated = translator.TranslatorByRegex([
    (r'.*/((cassini_iss/cassini_iss\w*)/(data|browse)(.*|_[a-z]*]/.*))\.[a-z]{3}', 0,
        [r'calibrated/\1_CALIB.IMG',
         r'calibrated/\1_CALIB.LBL',
        ]),
])

associations_to_previews = translator.TranslatorByRegex([
    (r'.*/(cassini_iss/cassini_iss\w*/(data|browse)(.*|_[a-z]*])/.*)\.[a-z]{3}', 0,
        [r'previews/\1_full.png',
         r'previews/\1_med.png',
         r'previews/\1_small.png',
         r'previews/\1_thumb.png',
        ]),
])

associations_to_metadata = translator.TranslatorByRegex([
    (r'.*/(cassini_iss)/(cassini_iss\w*)/(data|browse)(.*|_[a-z]*])/(.*)\.[a-z]{3}', 0,
        [r'metadata/\1/\2/\2_index.tab/\5',
         r'metadata/\1/\2/\2_ring_summary.tab/\5',
         r'metadata/\1/\2/\2_moon_summary.tab/\5',
         r'metadata/\1/\2/\2_saturn_summary.tab/\5',
         r'metadata/\1/\2/\2_jupiter_summary.tab/\5',
        ]),
])

associations_to_documents = translator.TranslatorByRegex([
    (r'(bundles|calibrated)/cassini_iss/.*', 0,
         r'documents/cassini_iss/*'),
    (r'(bundles|calibrated)/cassini_iss', 0,
         r'documents/cassini_iss'),
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
     (r'.*/cassini_iss/cassini_iss\w*/[a-z]*_raw/\d{3}xxxxxxx/\d{5}xxxxx/(\d{10})(n|w).*[a-z]{3}', 0, r'co-iss-\2\1')
])

##########################################################################################
# FILESPEC_TO_BUNDLESET
##########################################################################################

filespec_to_bundleset = translator.TranslatorByRegex([
    (r'(cassini_iss)_.*', 0, r'\1'),
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
# Map a bundle set or a bundle to a list of logical paths of the archive file names.
# TODO: split regex matched pattern group 1 (bundles|metadata|previews|doagrams) into
# separate entries if we use different archive file names for different categories
archive_paths = translator.TranslatorByRegex([
    # cassini_iss_cruise
    (r'.*(bundles|metadata|previews|diagrams)/(cassini_iss/cassini_iss_cruise)', 0, [
        # bundle xml and other non browse_raw & data_row collections
        r'archives-\1/\2/bundle_xml_non_data_browse_collections.tar.gz',
        # browse_raw
        r'archives-\1/\2/browse_raw.tar.gz',
        # data_row
        *[rf'archives-\1/\2/data_raw_1{num}xxxxxxx.tar.gz' for num in range(29,46)],
        r'archives-\1/\2/data_raw_col_xml_csv_metadata.tar.gz',
    ]),

    # cassini_iss_saturn
    (r'.*(bundles|metadata|previews|diagrams)/(cassini_iss/cassini_iss_saturn)', 0, [
        # bundle xml, context, document, and xml_schema
        r'archives-\1/\2/bundle_xml_non_data_browse_collections.tar.gz',
        # browse_raw
        *[rf'archives-\1/\2/browse_raw_{num}xxxxxxxx.tar.gz' for num in range(14, 19)],
        r'archives-\1/\2/browse_raw_col_xml_csv.tar.gz',
        # data_row
        *[rf'archives-\1/\2/data_raw_1{num}xxxxxxx.tar.gz' for num in range(45, 89)],
        r'archives-\1/\2/data_raw_col_xml_csv_metadata.tar.gz',
    ]),
])

# Map a logical path of an archive file name to a list of logical paths of the included
# directories
archive_dirs = translator.TranslatorByRegex([
    # cassini_iss_cruise
    # bundle xml, non browse_raw or data_row collections
    (r'.*archives-(.*/cassini_iss)/(cassini_iss_cruise)/bundle_xml_non_data_browse_collections.tar.gz', 0,
        [r'\1/\2/bundle.xml',
         r'\1/\2/document',
         r'\1/\2/xml_schema',
         r'\1/\2/context']
    ),
    # browse_raw
    (r'.*archives-(.*/cassini_iss)/(cassini_iss_cruise)/(browse_raw).tar.gz', 0,
        [r'\1/\2/\3']
    ),
    # data_row
    *[
        (rf'.*archives-(.*/cassini_iss)/(cassini_iss_cruise)/(data_raw)_1{num}xxxxxxx.tar.gz',
         0, [rf'\1/\2/\3/1{num}xxxxxxx'])
        for num in range(29,46)
    ],
    (r'.*archives-(.*/cassini_iss)/(cassini_iss_cruise)/(data_raw)_col_xml_csv_metadata.tar.gz', 0,
        [r'\1/\2/\3/collection_data_raw.csv',
         r'\1/\2/\3/collection_data_raw.xml',
         r'\1/\2/\3/metadata']
    ),

    # cassini_iss_saturn
    # bundle xml, context, document, and xml_schema collections
    (r'.*archives-(.*/cassini_iss)/(cassini_iss_saturn)/bundle_xml_non_data_browse_collections.tar.gz', 0,
        [r'\1/\2/bundle.xml',
         r'\1/\2/document',
         r'\1/\2/xml_schema',
         r'\1/\2/context']
    ),
    # browse_raw
    *[
        (rf'.*archives-(.*/cassini_iss)/(cassini_iss_saturn)/(browse_raw)_{num1}xxxxxxxx.tar.gz',
         0, [rf'\1/\2/\3/{num1}{num2}xxxxxxx' for num2 in range(0, 10)])
        for num1 in range(14,19)
    ],
    (r'.*archives-(.*/cassini_iss)/(cassini_iss_saturn)/(browse_raw)_col_xml_csv.tar.gz', 0,
        [r'\1/\2/\3/collection_browse_raw.csv',
         r'\1/\2/\3/collection_browse_raw.xml']
    ),
    # data_row
    *[
        (rf'.*archives-(.*/cassini_iss)/(cassini_iss_saturn)/(data_raw)_1{num}xxxxxxx.tar.gz',
         0, [rf'\1/\2/\3/1{num}xxxxxxx'])
        for num in range(45, 89)
    ],
    (r'.*archives-(.*/cassini_iss)/(cassini_iss_saturn)/(data_raw)_col_xml_csv_metadata.tar.gz', 0,
        [r'\1/\2/\3/collection_data_raw.csv',
         r'\1/\2/\3/collection_data_raw.xml',
         r'\1/\2/\3/metadata']
    ),
])

##########################################################################################
# Subclass definition
##########################################################################################

class cassini_iss(pds4file.Pds4File): # Cassini_ISS

    pds4file.Pds4File.VOLSET_TRANSLATOR = translator.TranslatorByRegex([('cassini_iss', re.I, 'cassini_iss')]) + \
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
    ASSOCIATIONS['calibrated'] += associations_to_calibrated
    ASSOCIATIONS['previews']   += associations_to_previews
    ASSOCIATIONS['metadata']   += associations_to_metadata
    ASSOCIATIONS['documents']  += associations_to_documents

    ARCHIVE_PATHS = archive_paths + pds4file.Pds4File.ARCHIVE_PATHS
    ARCHIVE_DIRS = archive_dirs + pds4file.Pds4File.ARCHIVE_DIRS

    pds4file.Pds4File.FILESPEC_TO_BUNDLESET = filespec_to_bundleset + pds4file.Pds4File.FILESPEC_TO_BUNDLESET

# Global attribute shared by all subclasses
pds4file.Pds4File.OPUS_ID_TO_SUBCLASS = translator.TranslatorByRegex([(r'co-iss-.*', 0, cassini_iss)]) + \
                                        pds4file.Pds4File.OPUS_ID_TO_SUBCLASS

##########################################################################################
# Update the global dictionary of subclasses
##########################################################################################

pds4file.Pds4File.SUBCLASSES['cassini_iss'] = cassini_iss

##########################################################################################
# Unit tests
##########################################################################################

import pytest
from .pytest_support import *

# @pytest.mark.parametrize(
#     'input_path,category,expected',
#     [
#         ('cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947228n.xml',
#          'bundles',
#          [
#             'bundles/cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947228n.img',
#             'bundles/cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947228n.xml',
#             'bundles/cassini_iss/cassini_iss_cruise/browse_raw/130xxxxxxx/13089xxxxx/1308947228n-full.png',
#             'bundles/cassini_iss/cassini_iss_cruise/browse_raw/130xxxxxxx/13089xxxxx/1308947228n-full.xml'
#          ]),
#         ('cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947228n.xml',
#          'previews',
#          [
#             'previews/cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947228n_full.png',
#             'previews/cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947228n_med.png',
#             'previews/cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947228n_small.png',
#             'previews/cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947228n_thumb.png'
#          ]),
#         ('cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947228n.xml',
#          'calibrated',
#          [
#             'calibrated/cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947228n_CALIB.IMG',
#             'calibrated/cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947228n_CALIB.LBL'
#          ]),
#         ('cassini_iss/cassini_iss_cruise/data_raw/130xxxxxxx/13089xxxxx/1308947228n.xml',
#          'documents',
#          [
#             'documents/cassini_iss/Calibration-Plan.pdf',
#             'documents/cassini_iss/Data-Product-SIS.txt',
#             'documents/cassini_iss/ISS-Users-Guide.docx',
#             'documents/cassini_iss/Data-Product-SIS.pdf',
#             'documents/cassini_iss/Calibration-Theoretical-Basis.pdf',
#             'documents/cassini_iss/VICAR-File-Format.pdf',
#             'documents/cassini_iss/Calibration-Report.link',
#             'documents/cassini_iss/Press-Releases-at-RMS.link',
#             'documents/cassini_iss/VICAR-Home-Page-at-JPL.link',
#             'documents/cassini_iss/Press-Releases-at-JPL-Photojournal.link',
#             'documents/cassini_iss/Porco-etal-2004-SSR.link',
#             'documents/cassini_iss/ISS-Users-Guide.pdf',
#             'documents/cassini_iss/Archive-SIS.pdf',
#             'documents/cassini_iss/PDS-ISS-Home-Page.link',
#             'documents/cassini_iss/CISSCAL-Users-Guide.pdf',
#             'documents/cassini_iss/PDS-ISS-Home-Page-at-RMS.link',
#             'documents/cassini_iss/Archive-SIS.txt',
#             'documents/cassini_iss/Cassini-ISS-Final-Report.pdf',
#             'documents/cassini_iss/Calibration-Report.zip'
#          ]),
#         # TODO: add test case for metadata when correct index files & _indexshelf-metadata
#         # are added
#     ]
# )
# def test_associated_abspaths(input_path, category, expected):
#     target_pdsfile = instantiate_target_pdsfile(input_path)
#     res = target_pdsfile.associated_abspaths(category=category)
#     result_paths = []
#     result_paths += pds4file.Pds4File.logicals_for_abspaths(res)
#     assert len(result_paths) != 0
#     for path in result_paths:
#         assert path in expected

##########################################################################################
