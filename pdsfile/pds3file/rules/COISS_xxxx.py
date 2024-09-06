##########################################################################################
# pds3file/rules/COISS_xxxx.py
##########################################################################################

import pdsfile.pds3file as pds3file
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
    (r'.*/(COISS_[12]xxx)(|_v[0-9\.]+)/(COISS_[12].../data/\w+/[NW][0-9]{10}_[0-9]+).*', 0,
            [r'previews/\1/\3_full.png',
             r'previews/\1/\3_med.jpg',
             r'previews/\1/\3_small.jpg',
             r'previews/\1/\3_thumb.jpg',
            ]),
    (r'.*/(COISS_3xxx.*/COISS_3.../data)/(images|maps)/(\w+)\..*', 0,
            [r'previews/\1/\2/\3_full.png',
             r'previews/\1/\2/\3_med.png',
             r'previews/\1/\2/\3_small.png',
             r'previews/\1/\2/\3_thumb.png',
             r'previews/\1/\2/\3_full.jpg',
             r'previews/\1/\2/\3_med.jpg',
             r'previews/\1/\2/\3_small.jpg',
             r'previews/\1/\2/\3_thumb.jpg',
            ]),
])

##########################################################################################
# ASSOCIATIONS
##########################################################################################

associations_to_volumes = translator.TranslatorByRegex([

    # COISS_1xxx and COISS_2xxx
    (r'.*/(COISS_[12]xxx.*/COISS_....)/(data|extras/\w+)/(\w+/[NW][0-9]{10}_[0-9]+).*', 0,
            [r'volumes/\1/data/\3.IMG',
             r'volumes/\1/data/\3.LBL',
             r'volumes/\1/extras/thumbnail/\3.IMG.jpeg_small',
             r'volumes/\1/extras/browse/\3.IMG.jpeg',
             r'volumes/\1/extras/full/\3.IMG.png',
             r'volumes/\1/extras/tiff/\3.IMG.tiff',
            ]),
    (r'.*/(COISS_[12]xxx.*/COISS_....)/(data|extras/\w+)(|/\w+)', 0,
            [r'volumes/\1/data\3',
             r'volumes/\1/extras/thumbnail\3',
             r'volumes/\1/extras/browse\3',
             r'volumes/\1/extras/full\3',
            ]),
    (r'.*/(COISS_[12]xxx.*/COISS_....)/extras', 0,
            r'volumes/\1/data'),
    (r'.*/(COISS_[12])999.*', 0,
            r'volumes/\1xxx'),
    (r'documents/COISS_0xxx.*', 0,
            [r'volumes/COISS_0xxx',
             r'volumes/COISS_1xxx',
             r'volumes/COISS_2xxx',
            ]),

    # COISS_3xxx
    (r'.*/(COISS_3xxx.*/COISS_3...)/(data|extras/\w+)/(images/\w+[A-Z]+)(|_[a-z]+)\..*', 0,
            [r'volumes/\1/data/\3.IMG',
             r'volumes/\1/extras/browse/\3.IMG.jpeg',
             r'volumes/\1/extras/thumbnail/\3.IMG.jpeg_small',
             r'volumes/\1/extras/full/\3.IMG.png',
            ]),
    (r'.*/(COISS_3xxx.*/COISS_3...)/(data|extras/\w+)/(maps/\w+_SMN).*', 0,
            [r'volumes/\1/data/\3.lbl',
             r'volumes/\1/data/\3.PDF',
             r'volumes/\1/extras/browse/\3.jpg',
             r'volumes/\1/extras/browse/\3_browse.jpg',
             r'volumes/\1/extras/browse/\3.PDF.jpeg',
             r'volumes/\1/extras/thumbnail/\3.jpg',
             r'volumes/\1/extras/thumbnail/\3_thumb.jpg',
             r'volumes/\1/extras/thumbnail/\3.PDF.jpeg',
             r'volumes/\1/extras/full/\3.PDF.png',
            ]),
    (r'.*/(COISS_3xxx.*/COISS_3...)/(data|extras/\w+)(|/images|/maps)', 0,
            [r'volumes/\1/data/\3',
             r'volumes/\1/extras/browse/\3',
             r'volumes/\1/extras/thumbnail/\3',
             r'volumes/\1/extras/full/\3',
            ]),
    (r'.*/(COISS_3xxx.*/COISS_3...)/extras', 0,
            r'volumes/\1/data'),
])

associations_to_calibrated = translator.TranslatorByRegex([
    (r'.*/(COISS_[12]xxx)(|_v[0-9\.]+)/(COISS_....)/(data|extras/\w+)/(\w+/[NW][0-9]{10}_[0-9]+).*', 0,
            [r'calibrated/\1/\3/data/\5_CALIB.IMG',
             r'calibrated/\1/\3/data/\5_CALIB.LBL',
            ]),
    (r'.*/(COISS_[12]xxx)(|_v[0-9\.]+)/(COISS_....)/(data|extras/\w+)(|/\w+)', 0,
            r'calibrated/\1/\3/data\5'),
    (r'.*/(COISS_[12])999.*', 0,
            r'calibrated/\1xxx'),
])

associations_to_previews = translator.TranslatorByRegex([

    # COISS_1xxx and COISS_2xxx
    (r'.*/(COISS_[12]xxx)(|_v[0-9\.]+)/(COISS_....)/(data|extras/\w+)/(\w+/[NW][0-9]{10}_[0-9]+).*', 0,
            [r'previews/\1/\3/data/\5_full.png',
             r'previews/\1/\3/data/\5_med.jpg',
             r'previews/\1/\3/data/\5_small.jpg',
             r'previews/\1/\3/data/\5_thumb.jpg',
            ]),
    (r'.*/(COISS_[12]xxx)(|_v[0-9\.]+)/(COISS_....)/(data|extras/\w+)(|/\w+)', 0,
            r'previews/\1/\3/data\5'),
    (r'.*/(COISS_[12])999.*', 0,
            r'previews/\1xxx'),

    # COISS_3xxx
    (r'.*/(COISS_3xxx.*/COISS_3...)/(data|extras/\w+)/(images/\w+[A-Z]+)(|_[a-z]+)\..*', 0,
            [r'previews/\1/data/\3_full.jpg',
             r'previews/\1/data/\3_med.jpg',
             r'previews/\1/data/\3_small.jpg',
             r'previews/\1/data/\3_thumb.jpg',
            ]),
    (r'.*/(COISS_3xxx.*/COISS_3...)/(data|extras/\w+)/(maps/\w+_SMN).*', 0,
            [r'previews/\1/data/\3_full.png',
             r'previews/\1/data/\3_med.png',
             r'previews/\1/data/\3_small.png',
             r'previews/\1/data/\3_thumb.png',
            ]),
    (r'.*/(COISS_3xxx.*/COISS_3...)/(data|extras/\w+)(|/images|/maps)', 0,
            [r'previews/\1/data/\3',
             r'previews/\1/extras/browse/\3',
             r'previews/\1/extras/thumbnail/\3',
             r'previews/\1/extras/full/\3',
            ]),
    (r'.*/(COISS_3xxx.*/COISS_3...)/extras', 0,
            r'previews/\1/data'),
])

associations_to_metadata = translator.TranslatorByRegex([
    (r'.*/(COISS_[12]xxx)(|_v[0-9\.]+)/(COISS_....)/(data|extras/w+)/\w+/([NW][0-9]{10}_[0-9]+).*', 0,
            [r'metadata/\1/\3/\3_index.tab/\5',
             r'metadata/\1/\3/\3_ring_summary.tab/\5',
             r'metadata/\1/\3/\3_moon_summary.tab/\5',
             r'metadata/\1/\3/\3_saturn_summary.tab/\5',
             r'metadata/\1/\3/\3_jupiter_summary.tab/\5',
            ]),
    (r'metadata/(COISS_.xxx/COISS_[12])...', 0,
            r'metadata/\g<1>999'),
    (r'metadata/(COISS_.xxx/COISS_[12]).../(COISS_.)..._(.*)\..*', 0,
            [r'metadata/\g<1>999/\g<2>999_\3.tab',
             r'metadata/\g<1>999/\g<2>999_\3.csv',
             r'metadata/\g<1>999/\g<2>999_\3.lbl',
            ]),
])

associations_to_documents = translator.TranslatorByRegex([
    (r'(volumes|calibrated)/COISS_[0-3]xxx(|_[\w\.]+)(|/COISS_[0-3]\d\d\d)', 0,
            r'documents/COISS_0xxx/*'),
    (r'(volumes|calibrated)/COISS_[0-3]xxx.*/COISS_[0-3]\d\d\d/.+', 0,
            r'documents/COISS_0xxx'),
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
    (r'.*/COISS_[12]xxx.*/([NW][0-9]{10})_[0-9]+.*', 0, r'co-iss-#LOWER#\1'),
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
# Subclass definition
##########################################################################################

class COISS_xxxx(pds3file.Pds3File):

    pds3file.Pds3File.VOLSET_TRANSLATOR = translator.TranslatorByRegex([('COISS_[0123x]xxx', re.I, 'COISS_xxxx')]) + \
                                          pds3file.Pds3File.VOLSET_TRANSLATOR

    DESCRIPTION_AND_ICON = description_and_icon_by_regex + pds3file.Pds3File.DESCRIPTION_AND_ICON
    VIEW_OPTIONS = view_options + pds3file.Pds3File.VIEW_OPTIONS
    NEIGHBORS = neighbors + pds3file.Pds3File.NEIGHBORS
    SORT_KEY = sort_key + pds3file.Pds3File.SORT_KEY

    OPUS_TYPE = opus_type + pds3file.Pds3File.OPUS_TYPE
    OPUS_FORMAT = opus_format + pds3file.Pds3File.OPUS_FORMAT
    OPUS_PRODUCTS = opus_products + pds3file.Pds3File.OPUS_PRODUCTS
    OPUS_ID = opus_id
    OPUS_ID_TO_PRIMARY_LOGICAL_PATH = opus_id_to_primary_logical_path

    VIEWABLES = {'default': default_viewables}

    ASSOCIATIONS = pds3file.Pds3File.ASSOCIATIONS.copy()
    ASSOCIATIONS['volumes']    += associations_to_volumes
    ASSOCIATIONS['calibrated'] += associations_to_calibrated
    ASSOCIATIONS['previews']   += associations_to_previews
    ASSOCIATIONS['metadata']   += associations_to_metadata
    ASSOCIATIONS['documents']  += associations_to_documents

    def FILENAME_KEYLEN(self):
        if self.bundleset[:10] == 'COISS_3xxx':
            return 0
        else:
            return 11   # trim off suffixes

# Global attribute shared by all subclasses
pds3file.Pds3File.OPUS_ID_TO_SUBCLASS = translator.TranslatorByRegex([(r'co-iss-.*', 0, COISS_xxxx)]) + \
                                        pds3file.Pds3File.OPUS_ID_TO_SUBCLASS

##########################################################################################
# Update the global dictionary of subclasses
##########################################################################################

pds3file.Pds3File.SUBCLASSES['COISS_xxxx'] = COISS_xxxx

##########################################################################################
# Unit tests
##########################################################################################

import pytest
from .pytest_support import *

@pytest.mark.parametrize(
    'input_path,expected',
    [
        ('volumes/COISS_1xxx/COISS_1001/data/1294561143_1295221348/W1294561202_1.IMG',
         'COISS_xxxx/opus_products/W1294561202_1.txt')
    ]
)
def test_opus_products(request, input_path, expected):
    update = request.config.option.update
    opus_products_test(pds3file.Pds3File, input_path, TEST_RESULTS_DIR+expected, update)

@pytest.mark.parametrize(
    'input_path,category,expected',
    [
        ('volumes/COISS_1xxx/COISS_1001/data/1294561143_1295221348/W1294561202_1.IMG',
         'volumes',
         'COISS_xxxx/associated_abspaths/volumes_W1294561202_1.txt')
    ]
)
def test_associated_abspaths(request, input_path, category, expected):
    update = request.config.option.update
    associated_abspaths_test(pds3file.Pds3File, input_path, category,
                             TEST_RESULTS_DIR+expected, update)

def test_opus_id_to_primary_logical_path():
    TESTS = [
        'volumes/COISS_1xxx/COISS_1001/data/1294561143_1295221348/W1294561143_1.IMG',
        'volumes/COISS_1xxx/COISS_1001/data/1294561143_1295221348/W1294561143_1.IMG',
        'volumes/COISS_1xxx/COISS_1001/data/1294561143_1295221348/W1294561143_1.IMG',
        'volumes/COISS_1xxx/COISS_1001/data/1295221411_1313633653/N1308947228_1.IMG',
        'volumes/COISS_1xxx/COISS_1001/data/1295221411_1313633653/W1313632011_1.IMG',
        'volumes/COISS_1xxx/COISS_1001/data/1313633670_1327290527/N1327288147_1.IMG',
        'volumes/COISS_1xxx/COISS_1001/data/1327290583_1338696666/N1338691304_1.IMG',
        'volumes/COISS_1xxx/COISS_1001/data/1339271046_1347931867/N1343347810_1.IMG',
        'volumes/COISS_1xxx/COISS_1001/data/1349949286_1350045260/N1350015006_2.IMG',
        'volumes/COISS_1xxx/COISS_1002/data/1351738505_1351858128/N1351738505_2.IMG',
        'volumes/COISS_1xxx/COISS_1003/data/1353756268_1353778349/N1353756268_1.IMG',
        'volumes/COISS_1xxx/COISS_1004/data/1354880676_1354900741/N1354880676_1.IMG',
        'volumes/COISS_1xxx/COISS_1005/data/1357564438_1357640357/N1357564438_1.IMG',
        'volumes/COISS_1xxx/COISS_1006/data/1359362956_1359397189/N1359362956_2.IMG',
        'volumes/COISS_1xxx/COISS_1006/data/1359572855_1360152309/N1360147206_2.IMG',
        'volumes/COISS_1xxx/COISS_1007/data/1363539046_1363614390/N1363539046_2.IMG',
        'volumes/COISS_1xxx/COISS_1007/data/1369655797_1372649162/N1372647808_1.IMG',
        'volumes/COISS_1xxx/COISS_1007/data/1373866554_1383124726/N1382817284_2.IMG',
        'volumes/COISS_1xxx/COISS_1007/data/1383621738_1401901046/N1390365159_1.IMG',
        'volumes/COISS_1xxx/COISS_1007/data/1383621738_1401901046/N1401900419_1.IMG',
        'volumes/COISS_1xxx/COISS_1008/data/1405160033_1405415729/W1405160033_1.IMG',
        'volumes/COISS_1xxx/COISS_1008/data/1405680221_1412538101/N1412536155_1.IMG',
        'volumes/COISS_1xxx/COISS_1008/data/1413924399_1421842328/N1421686098_1.IMG',
        'volumes/COISS_1xxx/COISS_1008/data/1429942583_1431947672/W1431917802_4.IMG',
        'volumes/COISS_1xxx/COISS_1008/data/1432088513_1441663700/N1441663594_1.IMG',
        'volumes/COISS_1xxx/COISS_1009/data/1444749868_1444867753/W1444749868_1.IMG',
        'volumes/COISS_1xxx/COISS_1009/data/1449088396_1451040707/N1451037606_1.IMG',
        'volumes/COISS_2xxx/COISS_2001/data/1454725799_1455008789/N1454725799_1.IMG',
        'volumes/COISS_2xxx/COISS_2001/data/1454725799_1455008789/N1454725799_1.IMG',
        'volumes/COISS_2xxx/COISS_2001/data/1459921583_1460008828/N1460002297_1.IMG',
        'volumes/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460960653_1.IMG',
        'volumes/COISS_2xxx/COISS_2003/data/1463538487_1463784347/N1463538487_1.IMG',
        'volumes/COISS_2xxx/COISS_2004/data/1465674475_1465709620/N1465674475_2.IMG',
        'volumes/COISS_2xxx/COISS_2005/data/1469618524_1469750418/N1469618524_1.IMG',
        'volumes/COISS_2xxx/COISS_2005/data/1469981571_1470014339/N1470001452_1.IMG',
        'volumes/COISS_2xxx/COISS_2006/data/1472808065_1472939163/W1472808065_1.IMG',
        'volumes/COISS_2xxx/COISS_2007/data/1475025242_1475045793/N1475025242_1.IMG',
        'volumes/COISS_2xxx/COISS_2008/data/1477654052_1477675228/W1477654052_1.IMG',
        'volumes/COISS_2xxx/COISS_2008/data/1479919543_1480697632/N1480002343_2.IMG',
        'volumes/COISS_2xxx/COISS_2009/data/1484573295_1484664788/N1484573295_1.IMG',
        'volumes/COISS_2xxx/COISS_2010/data/1488210352_1488278467/N1488210352_1.IMG',
        'volumes/COISS_2xxx/COISS_2010/data/1489518473_1490053457/N1490010708_2.IMG',
        'volumes/COISS_2xxx/COISS_2011/data/1491006469_1491034038/W1491006469_2.IMG',
        'volumes/COISS_2xxx/COISS_2012/data/1493885952_1493944410/N1493885952_1.IMG',
        'volumes/COISS_2xxx/COISS_2013/data/1498351302_1498388686/N1498351302_1.IMG',
        'volumes/COISS_2xxx/COISS_2014/data/1498874330_1499156249/W1498874330_1.IMG',
        'volumes/COISS_2xxx/COISS_2014/data/1499856675_1500013423/N1500006715_2.IMG',
        'volumes/COISS_2xxx/COISS_2015/data/1503245366_1503271060/N1503245366_1.IMG',
        'volumes/COISS_2xxx/COISS_2016/data/1506820488_1506897334/N1506820488_1.IMG',
        'volumes/COISS_2xxx/COISS_2016/data/1509948065_1510209922/N1510008716_2.IMG',
        'volumes/COISS_2xxx/COISS_2017/data/1510209962_1510426007/N1510209962_1.IMG',
        'volumes/COISS_2xxx/COISS_2018/data/1514331399_1514634386/W1514331399_1.IMG',
        'volumes/COISS_2xxx/COISS_2019/data/1514778151_1514830870/N1514778151_1.IMG',
        'volumes/COISS_2xxx/COISS_2020/data/1517073797_1517146910/N1517073797_1.IMG',
        'volumes/COISS_2xxx/COISS_2020/data/1519943879_1520053888/N1520006135_1.IMG',
        'volumes/COISS_2xxx/COISS_2021/data/1520513039_1520518635/N1520513039_3.IMG',
        'volumes/COISS_2xxx/COISS_2022/data/1522542711_1523193741/N1522542711_1.IMG',
        'volumes/COISS_2xxx/COISS_2023/data/1526038904_1526111192/N1526038904_1.IMG',
        'volumes/COISS_2xxx/COISS_2023/data/1529895763_1530155194/W1530002554_1.IMG',
        'volumes/COISS_2xxx/COISS_2024/data/1530431891_1530501147/N1530431891_2.IMG',
        'volumes/COISS_2xxx/COISS_2025/data/1536146721_1536354642/N1536146721_3.IMG',
        'volumes/COISS_2xxx/COISS_2026/data/1538857861_1539059851/N1538857861_2.IMG',
        'volumes/COISS_2xxx/COISS_2026/data/1539755921_1540366583/N1540125444_1.IMG',
        'volumes/COISS_2xxx/COISS_2027/data/1542736810_1542749552/N1542736810_1.IMG',
        'volumes/COISS_2xxx/COISS_2028/data/1546310212_1546460050/W1546310212_1.IMG',
        'volumes/COISS_2xxx/COISS_2029/data/1548767843_1548774401/N1548767843_1.IMG',
        'volumes/COISS_2xxx/COISS_2029/data/1549990838_1550038740/W1550033236_1.IMG',
        'volumes/COISS_2xxx/COISS_2030/data/1550624073_1550700768/N1550624073_1.IMG',
        'volumes/COISS_2xxx/COISS_2031/data/1554109737_1554473730/N1554109737_1.IMG',
        'volumes/COISS_2xxx/COISS_2032/data/1557397713_1557609277/N1557397713_1.IMG',
        'volumes/COISS_2xxx/COISS_2032/data/1559931859_1560139498/N1560053930_1.IMG',
        'volumes/COISS_2xxx/COISS_2033/data/1560553718_1560701909/N1560553718_1.IMG',
        'volumes/COISS_2xxx/COISS_2034/data/1561952702_1562041232/N1561952702_1.IMG',
        'volumes/COISS_2xxx/COISS_2035/data/1564917522_1564929339/N1564917522_1.IMG',
        'volumes/COISS_2xxx/COISS_2036/data/1567440378_1567559253/N1567440378_1.IMG',
        'volumes/COISS_2xxx/COISS_2037/data/1569482861_1569493895/N1569482861_1.IMG',
        'volumes/COISS_2xxx/COISS_2038/data/1569890544_1570029791/W1569890544_1.IMG',
        'volumes/COISS_2xxx/COISS_2038/data/1569890544_1570029791/W1570012344_1.IMG',
        'volumes/COISS_2xxx/COISS_2039/data/1573186009_1573197826/N1573186009_1.IMG',
        'volumes/COISS_2xxx/COISS_2040/data/1576929656_1577178609/N1576929656_1.IMG',
        'volumes/COISS_2xxx/COISS_2041/data/1577839261_1577984737/N1577839261_1.IMG',
        'volumes/COISS_2xxx/COISS_2041/data/1579991990_1580182202/W1580000037_1.IMG',
        'volumes/COISS_2xxx/COISS_2042/data/1580849253_1580865001/N1580849253_1.IMG',
        'volumes/COISS_2xxx/COISS_2043/data/1585391197_1585519454/N1585391197_1.IMG',
        'volumes/COISS_2xxx/COISS_2044/data/1585714912_1585780819/W1585714912_1.IMG',
        'volumes/COISS_2xxx/COISS_2045/data/1589107831_1589118941/N1589107831_1.IMG',
        'volumes/COISS_2xxx/COISS_2045/data/1589878260_1590402341/W1590085657_1.IMG',
        'volumes/COISS_2xxx/COISS_2046/data/1592543394_1592591885/N1592543394_1.IMG',
        'volumes/COISS_2xxx/COISS_2047/data/1593567330_1593842462/W1593567330_1.IMG',
        'volumes/COISS_2xxx/COISS_2048/data/1597823641_1597899095/N1597823641_1.IMG',
        'volumes/COISS_2xxx/COISS_2048/data/1599954723_1600044537/W1600040969_1.IMG',
        'volumes/COISS_2xxx/COISS_2049/data/1601512976_1601609640/N1601512976_1.IMG',
        'volumes/COISS_2xxx/COISS_2050/data/1604723153_1604729503/N1604723153_1.IMG',
        'volumes/COISS_2xxx/COISS_2051/data/1608534807_1608704571/N1608534807_1.IMG',
        'volumes/COISS_2xxx/COISS_2052/data/1609475102_1609640902/W1609475102_1.IMG',
        'volumes/COISS_2xxx/COISS_2052/data/1609906195_1610170084/W1610050266_1.IMG',
        'volumes/COISS_2xxx/COISS_2053/data/1612979358_1613001698/N1612979358_1.IMG',
        'volumes/COISS_2xxx/COISS_2054/data/1617276884_1617526187/W1617276884_1.IMG',
        'volumes/COISS_2xxx/COISS_2054/data/1619945739_1620034486/N1620033982_1.IMG',
        'volumes/COISS_2xxx/COISS_2055/data/1622025855_1622043254/N1622025855_1.IMG',
        'volumes/COISS_2xxx/COISS_2056/data/1625115008_1625673763/N1625115008_1.IMG',
        'volumes/COISS_2xxx/COISS_2057/data/1629144588_1629174249/N1629144588_1.IMG',
        'volumes/COISS_2xxx/COISS_2057/data/1629783492_1630072138/N1630067008_1.IMG',
        'volumes/COISS_2xxx/COISS_2058/data/1633303611_1633479552/W1633303611_1.IMG',
        'volumes/COISS_2xxx/COISS_2059/data/1637523963_1637583900/N1637523963_1.IMG',
        'volumes/COISS_2xxx/COISS_2059/data/1639828825_1640396084/N1640086093_1.IMG',
        'volumes/COISS_2xxx/COISS_2060/data/1641034395_1641138458/W1641034395_1.IMG',
        'volumes/COISS_2xxx/COISS_2061/data/1646527563_1646768040/W1646527563_1.IMG',
        'volumes/COISS_2xxx/COISS_2062/data/1648877205_1649318589/N1648877205_1.IMG',
        'volumes/COISS_2xxx/COISS_2062/data/1649655448_1650199130/N1650067971_1.IMG',
        'volumes/COISS_2xxx/COISS_2063/data/1655080584_1655742520/N1655080584_1.IMG',
        'volumes/COISS_2xxx/COISS_2064/data/1656702236_1656971527/W1656702236_1.IMG',
        'volumes/COISS_2xxx/COISS_2064/data/1659806659_1660200780/N1660189250_1.IMG',
        'volumes/COISS_2xxx/COISS_2065/data/1662813294_1662830270/W1662813294_1.IMG',
        'volumes/COISS_2xxx/COISS_2066/data/1664840694_1664864289/N1664840694_1.IMG',
        'volumes/COISS_2xxx/COISS_2066/data/1669905491_1670314125/N1670272836_1.IMG',
        'volumes/COISS_2xxx/COISS_2067/data/1672660228_1673101740/W1672660228_1.IMG',
        'volumes/COISS_2xxx/COISS_2067/data/1679185535_1680197976/N1680116378_1.IMG',
        'volumes/COISS_2xxx/COISS_2068/data/1680805782_1681997642/N1680805782_1.IMG',
        'volumes/COISS_2xxx/COISS_2069/data/1688230146_1688906749/N1688230146_1.IMG',
        'volumes/COISS_2xxx/COISS_2069/data/1689632036_1690197264/N1690096018_1.IMG',
        'volumes/COISS_2xxx/COISS_2070/data/1695761485_1695858003/N1695761485_1.IMG',
        'volumes/COISS_2xxx/COISS_2071/data/1696121676_1696191173/N1696121676_1.IMG',
        'volumes/COISS_2xxx/COISS_2071/data/1699466410_1700755962/N1700538447_1.IMG',
        'volumes/COISS_2xxx/COISS_2072/data/1704074026_1704214582/W1704074026_1.IMG',
        'volumes/COISS_2xxx/COISS_2072/data/1709957622_1710063433/N1710000122_1.IMG',
        'volumes/COISS_2xxx/COISS_2073/data/1710382571_1711034250/N1710382571_1.IMG',
        'volumes/COISS_2xxx/COISS_2074/data/1711950276_1712333086/W1711950276_1.IMG',
        'volumes/COISS_2xxx/COISS_2075/data/1718119446_1718562614/N1718119446_1.IMG',
        'volumes/COISS_2xxx/COISS_2076/data/1719817887_1720730045/N1720100180_1.IMG',
        'volumes/COISS_2xxx/COISS_2076/data/1719817887_1720730045/W1719817887_1.IMG',
        'volumes/COISS_2xxx/COISS_2077/data/1727539187_1727552003/N1727539187_1.IMG',
        'volumes/COISS_2xxx/COISS_2078/data/1727768838_1727812668/W1727768838_1.IMG',
        'volumes/COISS_2xxx/COISS_2078/data/1729265963_1730390645/N1730390485_1.IMG',
        'volumes/COISS_2xxx/COISS_2079/data/1732778945_1732866015/W1732778945_1.IMG',
        'volumes/COISS_2xxx/COISS_2080/data/1735820948_1735929909/W1735820948_1.IMG',
        'volumes/COISS_2xxx/COISS_2080/data/1739877669_1740026406/N1740007676_1.IMG',
        'volumes/COISS_2xxx/COISS_2081/data/1740280756_1740609413/N1740280756_4.IMG',
        'volumes/COISS_2xxx/COISS_2082/data/1743471132_1743623984/W1743471132_1.IMG',
        'volumes/COISS_2xxx/COISS_2083/data/1748626091_1748700568/N1748626091_1.IMG',
        'volumes/COISS_2xxx/COISS_2083/data/1749919104_1750028426/W1750001919_1.IMG',
        'volumes/COISS_2xxx/COISS_2084/data/1751331417_1751453318/W1751331417_1.IMG',
        'volumes/COISS_2xxx/COISS_2085/data/1757175285_1757258239/N1757175285_1.IMG',
        'volumes/COISS_2xxx/COISS_2086/data/1759651531_1760115334/N1759651531_1.IMG',
        'volumes/COISS_2xxx/COISS_2086/data/1759651531_1760115334/W1760083483_1.IMG',
        'volumes/COISS_2xxx/COISS_2087/data/1767109271_1767192679/N1767109271_1.IMG',
        'volumes/COISS_2xxx/COISS_2088/data/1767238922_1767334417/N1767238922_1.IMG',
        'volumes/COISS_2xxx/COISS_2088/data/1769918570_1770040939/W1770011506_1.IMG',
        'volumes/COISS_2xxx/COISS_2089/data/1773012953_1773094509/N1773012953_1.IMG',
        'volumes/COISS_2xxx/COISS_2090/data/1775058309_1775181685/N1775058309_1.IMG',
        'volumes/COISS_2xxx/COISS_2090/data/1779277411_1781294064/N1780138481_1.IMG',
        'volumes/COISS_2xxx/COISS_2091/data/1782983700_1783438162/N1782983700_1.IMG',
        'volumes/COISS_2xxx/COISS_2091/data/1789919172_1790023794/N1790006907_1.IMG',
        'volumes/COISS_2xxx/COISS_2092/data/1790059188_1790215306/W1790059188_1.IMG',
        'volumes/COISS_2xxx/COISS_2093/data/1791082750_1791181380/N1791082750_1.IMG',
        'volumes/COISS_2xxx/COISS_2094/data/1798826179_1798965530/N1798826179_1.IMG',
        'volumes/COISS_2xxx/COISS_2094/data/1799748810_1800073849/W1800031257_1.IMG',
        'volumes/COISS_2xxx/COISS_2095/data/1805088286_1805229944/N1805088286_1.IMG',
        'volumes/COISS_2xxx/COISS_2096/data/1806542109_1806660268/W1806542109_1.IMG',
        'volumes/COISS_2xxx/COISS_2096/data/1809932433_1810019577/N1810000041_1.IMG',
        'volumes/COISS_2xxx/COISS_2097/data/1812153587_1812673879/N1812153587_1.IMG',
        'volumes/COISS_2xxx/COISS_2098/data/1814434262_1814467790/N1814434262_1.IMG',
        'volumes/COISS_2xxx/COISS_2098/data/1819882326_1820081329/N1820037062_1.IMG',
        'volumes/COISS_2xxx/COISS_2099/data/1820648744_1820668365/N1820648744_1.IMG',
        'volumes/COISS_2xxx/COISS_2100/data/1822395235_1823032096/N1822395235_1.IMG',
        'volumes/COISS_2xxx/COISS_2101/data/1829539156_1829548178/N1829539156_1.IMG',
        'volumes/COISS_2xxx/COISS_2101/data/1829796937_1830040346/N1830032820_1.IMG',
        'volumes/COISS_2xxx/COISS_2102/data/1830403828_1831023635/N1830403828_1.IMG',
        'volumes/COISS_2xxx/COISS_2103/data/1837313417_1837374306/N1837313417_1.IMG',
        'volumes/COISS_2xxx/COISS_2104/data/1838169062_1838275771/N1838169062_1.IMG',
        'volumes/COISS_2xxx/COISS_2104/data/1839950576_1840263036/N1840141265_1.IMG',
        'volumes/COISS_2xxx/COISS_2105/data/1844319700_1844455199/N1844319700_1.IMG',
        'volumes/COISS_2xxx/COISS_2106/data/1846032655_1846125258/N1846032655_1.IMG',
        'volumes/COISS_2xxx/COISS_2106/data/1849924886_1850088089/W1850083457_1.IMG',
        'volumes/COISS_2xxx/COISS_2107/data/1851331524_1851342631/N1851331524_1.IMG',
        'volumes/COISS_2xxx/COISS_2108/data/1854009318_1854287039/N1854009318_1.IMG',
        'volumes/COISS_2xxx/COISS_2109/data/1859795917_1860623101/N1859795917_1.IMG',
        'volumes/COISS_2xxx/COISS_2109/data/1859795917_1860623101/N1860474403_7.IMG',
        'volumes/COISS_2xxx/COISS_2110/data/1861975118_1862056749/N1861975118_1.IMG',
        'volumes/COISS_2xxx/COISS_2111/data/1866071296_1866225122/N1866071296_1.IMG',
        'volumes/COISS_2xxx/COISS_2112/data/1869784516_1869980408/N1869784516_1.IMG',
        'volumes/COISS_2xxx/COISS_2112/data/1869980499_1870085550/N1870058057_1.IMG',
        'volumes/COISS_2xxx/COISS_2113/data/1873427694_1873496724/N1873427694_1.IMG',
        'volumes/COISS_2xxx/COISS_2114/data/1876494184_1876764383/W1876494184_3.IMG',
        'volumes/COISS_2xxx/COISS_2115/data/1877634459_1877840382/N1877634459_1.IMG',
        'volumes/COISS_2xxx/COISS_2115/data/1879964192_1880041598/N1880041282_1.IMG',
        'volumes/COISS_2xxx/COISS_2116/data/1881830414_1881948814/N1881830414_1.IMG',
    ]

    for logical_path in TESTS:
        test_pdsf = pds3file.Pds3File.from_logical_path(logical_path)
        opus_id = test_pdsf.opus_id
        opus_id_pdsf = pds3file.Pds3File.from_opus_id(opus_id)
        assert opus_id_pdsf.logical_path == logical_path

        # Gather all the associated OPUS products
        product_dict = test_pdsf.opus_products()
        product_pdsfiles = []
        for pdsf_lists in product_dict.values():
            for pdsf_list in pdsf_lists:
                product_pdsfiles += pdsf_list

        # Filter out the metadata/documents products and format files
        product_pdsfiles = [pdsf for pdsf in product_pdsfiles
                                 if pdsf.voltype_ != 'metadata/'
                                 and pdsf.voltype_ != 'documents/']
        product_pdsfiles = [pdsf for pdsf in product_pdsfiles
                                 if pdsf.extension.lower() != '.fmt']

        # Gather the set of absolute paths
        opus_id_abspaths = set()
        for pdsf in product_pdsfiles:
            opus_id_abspaths.add(pdsf.abspath)

        for pdsf in product_pdsfiles:
            # Every version is in the product set
            for version_pdsf in pdsf.all_versions().values():
                assert version_pdsf.abspath in opus_id_abspaths

            # Every viewset is in the product set
            for viewset in pdsf.all_viewsets.values():
                for viewable in viewset.viewables:
                    assert viewable.abspath in opus_id_abspaths

            # Every associated product is in the product set except metadata
            for category in ('volumes', 'calibrated', 'previews'):
                for abspath in pdsf.associated_abspaths(category):
                    assert abspath in opus_id_abspaths

##########################################################################################
