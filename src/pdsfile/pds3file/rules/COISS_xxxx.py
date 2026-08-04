##########################################################################################
# pds3file/rules/COISS_xxxx.py
##########################################################################################

import re

import translator
from range_ex import range_regex

import pdsfile.pds3file as pds3file

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

# Map each observation by inclusive 10-digit product-id
_PRODUCT_ID_TO_F_RING_OBSERVATION_ID_MAPPING = {
    (1466448221, 1466485661): 'iss_000ri_satsrchap001_prime',
    (1479201492, 1479254052): 'iss_00ari_spkmovper001_prime',
    (1492052683, 1492102152): 'iss_006ri_lphrlfmov001_prime',
    (1493613276, 1493661051): 'iss_007ri_lphrlfmov001_prime',
    (1493706056, 1493734145): 'iss_007ri_azscnloph001_prime',
    (1493850077, 1493887177): 'iss_007ri_hpmrdfmov001_prime',
    (1538168640, 1538218132): 'iss_029rf_fmovie001_vims',
    (1538269441, 1538300071): 'iss_029rf_fmovie002_vims',
    (1539655570, 1539683497): 'iss_030rf_fmovie001_vims',
    (1541012989, 1541062380): 'iss_031rf_fmovie001_vims',
    (1542047155, 1542096546): 'iss_032rf_fmovie001_vims',
    (1542149816, 1542156952): 'iss_032rf_fmovie002_vims',
    (1543166702, 1543216891): 'iss_033rf_fmovie001_vims',
    (1545556618, 1545609688): 'iss_036rf_fmovie001_vims',
    (1546700688, 1546748805): 'iss_036rf_fmovie002_vims',
    (1549801218, 1549851279): 'iss_039rf_fmovie002_vims',
    (1549901779, 1549911779): 'iss_039rf_fmovie003_vims',
    (1550952562, 1550959642): 'iss_039ri_fmonitor002_cirs',
    (1551253524, 1551307916): 'iss_039rf_fmovie001_vims',
    (1552790437, 1552844437): 'iss_041rf_fmovie002_vims',
    (1552853136, 1552853136): 'iss_041ri_fmonitor001_cirs',
    (1554026927, 1554072073): 'iss_041rf_fmovie001_vims',
    (1555557017, 1555610413): 'iss_043rf_fmovie001_vims',
    (1555706573, 1555707053): 'iss_043ri_fmonitor001_cirs',
    (1555944144, 1555952724): 'iss_043ri_fmonitor001_prime',
    (1557020880, 1557073328): 'iss_044rf_fmovie001_vims',
    (1571435192, 1571475337): 'iss_051ri_lpmrdfmov001_prime',
    (1577809417, 1577857957): 'iss_055rf_fmovie001_vims',
    (1578386361, 1578439565): 'iss_055ri_lpmrdfmov001_prime',
    (1579790806, 1579837831): 'iss_057rf_fmovie001_vims',
    (1581944506, 1581993408): 'iss_059rf_fmovie001_vims',
    (1582549430, 1582602740): 'iss_059rf_fmovie002_vims',
    (1584269462, 1584298342): 'iss_061ri_lpmrdfmov001_prime',
    (1589589182, 1589641908): 'iss_068rf_fmovie001_vims',
    (1592114050, 1592159350): 'iss_072ri_spkhrlpdf001_prime',
    (1593913221, 1593967292): 'iss_075rf_fmovie002_vims',
    (1594182967, 1594205050): 'iss_075rb_bmovie4001_vims',
    (1596333808, 1596335548): 'iss_079ri_fmonitor002_prime',
    (1596680431, 1596713637): 'iss_079rf_fringmrlf002_prime',
    (1597390145, 1597402524): 'iss_080rf_fmovie005_prime',
    (1597577017, 1597578712): 'iss_081ri_fmonitor001_prime',
    (1597886079, 1597933535): 'iss_081ri_fmovie106_vims',
    (1598607164, 1598612144): 'iss_082ri_fmonitor003_prime',
    (1598806665, 1598853071): 'iss_083ri_fmovie109_vims',
    (1598925706, 1598925706): 'iss_083ri_fmonitor002_prime',
    (1599539571, 1599541251): 'iss_084ri_fmonitor002_prime',
    (1600213195, 1600239816): 'iss_085rf_fmovie003_prime_1',
    (1600240376, 1600258555): 'iss_085rf_fmovie003_prime_2',
    (1601485634, 1601526770): 'iss_087rf_fmovie003_prime',
    (1602717403, 1602760410): 'iss_089rf_fmovie003_prime',
    (1604005372, 1604050740): 'iss_091rf_fmovie003_prime',
    (1604279522, 1604292268): 'iss_091ri_apomosl109_vims',
    (1604720757, 1604730703): 'iss_092rf_fmovie003_prime',
    (1605368762, 1605402588): 'iss_093rf_fmovie003_prime',
    (1605530283, 1605536089): 'iss_093rf_fmovie001_prime',
    (1605996366, 1606021302): 'iss_094rf_fmovie001_prime_1',
    (1606022166, 1606035502): 'iss_094rf_fmovie001_prime_2',
    (1606108240, 1606113042): 'iss_094rf_fmovie003_prime',
    (1607625633, 1607670827): 'iss_096rf_fmovie004_prime',
    (1608683935, 1608703375): 'iss_098ri_tmapn30lp001_cirs',
    (1610364098, 1610404395): 'iss_100rf_fmovie003_prime',
    (1610924592, 1610933648): 'iss_100ri_subms20lp001_cirs',
    (1612292043, 1612297908): 'iss_102rf_fmovie001_prime',
    (1612545569, 1612574369): 'iss_102ri_spkfmlflp001_prime',
    (1612969737, 1613007123): 'iss_103rf_fmovie003_prime',
    (1614214055, 1614223071): 'iss_104rf_fmovie003_prime',
    (1614850030, 1614865561): 'iss_105rf_fmovie003_prime',
    (1614936340, 1614936936): 'iss_105ri_tmapn45lp001_cirs_1',
    (1614940960, 1614942156): 'iss_105ri_tmapn45lp001_cirs_2',
    (1614945040, 1614945040): 'iss_105ri_tmapn45lp001_cirs_3',
    (1614950500, 1614950500): 'iss_105ri_tmapn45lp001_cirs_4',
    (1614953740, 1614954636): 'iss_105ri_tmapn45lp001_cirs_5',
    (1614958180, 1614959136): 'iss_105ri_tmapn45lp001_cirs_6',
    (1615342663, 1615352743): 'iss_105ri_tdifs20hp001_cirs',
    (1615465964, 1615514239): 'iss_105rf_fmovie002_prime',
    (1616500071, 1616546465): 'iss_106rf_fmovie002_prime',
    (1617039146, 1617062017): 'iss_107rf_fmovie002_prime',
    (1618050603, 1618070583): 'iss_108ri_spkmvlflp001_prime',
    (1618571707, 1618607233): 'iss_108rf_fmovie001_prime',
    (1619011390, 1619030166): 'iss_109ri_tdifs20hp001_cirs',
    (1620639921, 1620678782): 'iss_110rf_fmovie002_prime',
    (1622022571, 1622049830): 'iss_111rf_fmovie002_prime',
    (1623328380, 1623354366): 'iss_112rf_fmovie002_prime_1',
    (1623355200, 1623373954): 'iss_112rf_fmovie002_prime_2',
    (1626209041, 1626252768): 'iss_114rf_fmovieeqx001_prime',
    (1627609661, 1627654945): 'iss_115rf_fmovieeqx001_prime',
    (1654040868, 1654086464): 'iss_132ri_fmovie001_vims',
    (1656595136, 1656603760): 'iss_134ri_spkmvdfhp001_prime',
    (1662083471, 1662101167): 'iss_137ri_fmovie001_vims',
    (1716469325, 1716499030): 'iss_166ri_fntlpmov001_prime',
    (1719287758, 1719319754): 'iss_168rf_fmovie001_prime',
    (1719534519, 1719548360): 'iss_168rf_fmovie002_prime',
    (1719968608, 1719971583): 'iss_168ri_propretrg001_prime',
    (1723506241, 1723512477): 'iss_170rf_hiresfrng001_prime',
    (1726689810, 1726727886): 'iss_172ri_spokemov001_prime',
    (1726771710, 1726808835): 'iss_172ri_spokemov002_prime',
    (1726857022, 1726902234): 'iss_172rf_fmovie001_prime',
    (1727029513, 1727030885): 'iss_172ri_betpegocc001_vims',
    (1727131934, 1727132875): 'iss_172st_urgampeg001_uvis',
    (1727791458, 1727844180): 'iss_172ri_egapmovmp002_prime',
    (1728245860, 1728279160): 'iss_173ri_spokemov001_prime',
    (1728607763, 1728626213): 'iss_173ri_spokemov002_prime',
    (1728757643, 1728809292): 'iss_173ri_spokemov003_prime',
    (1729024626, 1729053296): 'iss_173rf_fmovie001_prime_1',
    (1729053606, 1729082276): 'iss_173rf_fmovie001_prime_2',
    (1729259467, 1729265183): 'iss_173rf_hiresfrng001_prime',
    (1730573575, 1730683735): 'iss_174ri_spokemov001_prime',
    (1730746588, 1730799478): 'iss_174ri_spokemov002_prime',
    (1731025737, 1731060057): 'iss_174ri_spokemov004_prime',
    (1731106419, 1731132308): 'iss_174rf_frstrchan001_prime_1',
    (1731132699, 1731158588): 'iss_174rf_frstrchan001_prime_2',
    (1733513214, 1733566658): 'iss_176rf_fmovie001_prime',
    (1734557251, 1734578197): 'iss_177rf_fmovie001_prime_1',
    (1734578611, 1734599557): 'iss_177rf_fmovie001_prime_2',
    (1734640040, 1734683888): 'iss_177ri_spokemov001_prime',
    (1735097314, 1735121295): 'iss_177rf_frstrchan001_prime_1',
    (1735121674, 1735135905): 'iss_177rf_frstrchan001_prime_2',
    (1735568047, 1735607575): 'iss_178ri_egapmovmp001_prime',
    (1735820948, 1735858460): 'iss_178ri_spokemov001_prime',
    (1736795325, 1736848419): 'iss_179rf_fmovie001_prime',
    (1737000455, 1737045331): 'iss_179ri_spokemov001_prime',
    (1737159287, 1737173487): 'iss_179rf_fringphot001_vims',
    (1737920302, 1737921018): 'iss_180ri_rlyrocc001_vims',
    (1738003043, 1738047325): 'iss_180rf_fmovie001_prime',
    (1738087703, 1738104009): 'iss_180ri_spokemov001_prime',
    (1738174663, 1738200486): 'iss_180ri_spokemov002_prime',
    (1738234464, 1738244835): 'iss_180ri_rcasocc001_vims',
    (1738425645, 1738439073): 'iss_180rf_hiresfrng001_prime',
    (1739125110, 1739178406): 'iss_181rf_fmovie001_prime',
    (1739296670, 1739313067): 'iss_181ri_spokemov001_prime',
    (1739459317, 1739477914): 'iss_181rf_fringphot001_vims',
    (1739495009, 1739504421): 'iss_181rf_fringphot002_vims',
    (1741130083, 1741151019): 'iss_183rf_fmovie001_prime_1',
    (1741151683, 1741172619): 'iss_183rf_fmovie001_prime_2',
    (1741302783, 1741345070): 'iss_183ri_spokemov001_prime',
    (1742314089, 1742329623): 'iss_184ri_spokemov002_prime',
    (1742332190, 1742352786): 'iss_184rf_fmovie001_prime',
    (1743085105, 1743125381): 'iss_184rf_fmovie002_prime',
    (1743756869, 1743757345): 'iss_185ri_rhyaocc001_vims_1',
    (1743776395, 1743776875): 'iss_185ri_rhyaocc001_vims_2',
    (1746536717, 1746588699): 'iss_189rf_fmovie001_prime',
    (1748340058, 1748391040): 'iss_191rf_fmovie002_prime',
    (1748545110, 1748545586): 'iss_191ri_rcasoccb001_vims',
    (1748745661, 1748754868): 'iss_191rf_fmovie001_prime_1',
    (1748755171, 1748764378): 'iss_191rf_fmovie001_prime_2',
    (1748764681, 1748771919): 'iss_191rf_fmovie001_prime_3',
    (1748772384, 1748781591): 'iss_191rf_fmovie001_prime_4',
    (1748781894, 1748791101): 'iss_191rf_fmovie001_prime_5',
    (1750377261, 1750405525): 'iss_193rf_fmovie001_prime_1',
    (1750405946, 1750434210): 'iss_193rf_fmovie001_prime_2',
    (1751427278, 1751455616): 'iss_194rf_fmovie001_prime_1',
    (1751455948, 1751484286): 'iss_194rf_fmovie001_prime_2',
    (1751567089, 1751568045): 'iss_194ri_mucepocc001_vims',
    (1755729895, 1755782883): 'iss_196rf_fmovie003_prime',
    (1756033137, 1756086539): 'iss_196rf_fmovie004_prime',
    (1756205038, 1756258334): 'iss_196rf_fmovie005_prime',
    (1756377239, 1756428571): 'iss_196rf_fmovie006_prime',
    (1756451240, 1756452676): 'iss_196ri_betandocc001_vims',
    (1757236925, 1757277467): 'iss_197rf_fmovie007_prime',
    (1757523447, 1757523923): 'iss_197ri_whyaocc001_vims',
    (1757926979, 1757978446): 'iss_197rf_fmovie002_prime',
    (1760605062, 1760605482): 'iss_198ri_rlyrocc001_vims',
    (1760810138, 1760838424): 'iss_198rf_fmovie001_prime_1',
    (1760838808, 1760867094): 'iss_198rf_fmovie001_prime_2',
    (1760871907, 1760917141): 'iss_198ri_spokemov004_prime',
    (1761058908, 1761110930): 'iss_198ri_spokemov005_prime_1',
    (1761112336, 1761140456): 'iss_198ri_spokemov005_prime_2',
    (1762867359, 1762917379): 'iss_199ri_spokemov002_prime_1',
    (1762918199, 1762967399): 'iss_199ri_spokemov002_prime_2',
    (1763013921, 1763065753): 'iss_199ri_spokemov003_prime_1',
    (1763066589, 1763118421): 'iss_199ri_spokemov003_prime_2',
    (1763119257, 1763139321): 'iss_199ri_spokemov003_prime_3',
    (1763215522, 1763268470): 'iss_199ri_spokemov004_prime_1',
    (1763269324, 1763316294): 'iss_199ri_spokemov004_prime_2',
    (1763480768, 1763533240): 'iss_199ri_spokemov006_prime_1',
    (1763534177, 1763585712): 'iss_199ri_spokemov006_prime_2',
    (1763586649, 1763637247): 'iss_199ri_spokemov006_prime_3',
    (1764046928, 1764080493): 'iss_199ri_egapmovmp001_prime',
    (1765017544, 1765026670): 'iss_199rf_fmovie002_prime',
    (1766030604, 1766079224): 'iss_200ri_spokemov001_prime',
    (1766474355, 1766526981): 'iss_200ri_spokemov004_prime_1',
    (1766528055, 1766580681): 'iss_200ri_spokemov004_prime_2',
    (1766581755, 1766591421): 'iss_200ri_spokemov004_prime_3',
    (1767589250, 1767605647): 'iss_200ri_spokemov007_prime',
    (1768356955, 1768399165): 'iss_200ri_spokemov011_prime',
    (1768940158, 1768990676): 'iss_201ri_spokemov001_prime_1',
    (1768991430, 1769041948): 'iss_201ri_spokemov001_prime_2',
    (1769084020, 1769084736): 'iss_201ri_l2pupocc001_vims_1',
    (1769130696, 1769131416): 'iss_201ri_l2pupocc001_vims_2',
    (1769731304, 1769757769): 'iss_201rf_fmovie001_prime_1',
    (1769758094, 1769784559): 'iss_201rf_fmovie001_prime_2',
    (1770315948, 1770367142): 'iss_201rf_fmovie001_vims',
    (1770857110, 1770910462): 'iss_201ri_spokemov009_prime_1',
    (1770911164, 1770963112): 'iss_201ri_spokemov009_prime_2',
    (1771092912, 1771136472): 'iss_201ri_spokemov011_prime',
    (1771266373, 1771310533): 'iss_201ri_spokemov013_prime',
    (1771441574, 1771491074): 'iss_201ri_spokemov015_prime',
    (1772406871, 1772429775): 'iss_202rf_fmovie001_prime_1',
    (1772430296, 1772452786): 'iss_202rf_fmovie001_prime_2',
    (1776077815, 1776106170): 'iss_203rf_fmovie001_prime_1',
    (1776106495, 1776134850): 'iss_203rf_fmovie001_prime_2',
    (1782120353, 1782167660): 'iss_205rf_fmovie001_prime',
    (1782327240, 1782328320): 'iss_205ri_l2pupocc002_vims',
    (1784211806, 1784212334): 'iss_206ri_propretrg001_prime_1',
    (1784212436, 1784213057): 'iss_206ri_propretrg001_prime_2',
    (1784216711, 1784217239): 'iss_206ri_propretrg001_prime_3',
    (1784217875, 1784219205): 'iss_206ri_latphase001_vims',
    (1784298322, 1784341522): 'iss_206ri_bmovie001_prime',
    (1785022311, 1785023147): 'iss_206ri_l2pupocc002_vims',
    (1786881633, 1786926973): 'iss_207rf_fmovie001_prime',
    (1789913768, 1789932276): 'iss_208rf_fmovie001_prime_1',
    (1789932533, 1789941725): 'iss_208rf_fmovie001_prime_2',
    (1790414726, 1790440159): 'iss_208rf_fmovie002_prime_1',
    (1790440421, 1790464603): 'iss_208rf_fmovie002_prime_2',
    (1793068408, 1793089959): 'iss_209rf_fmovie001_prime_1',
    (1793090708, 1793111301): 'iss_209rf_fmovie001_prime_2',
    (1798937240, 1798993130): 'iss_211ri_egapmovmp001_prime',
    (1798999446, 1799051990): 'iss_211rf_fmovie001_prime',
    (1799556319, 1799570175): 'iss_211rf_hiresfrng001_prime',
    (1801963509, 1801985486): 'iss_212rf_fmovie001_prime_1',
    (1801985860, 1802007837): 'iss_212rf_fmovie001_prime_2',
    (1804611941, 1804663966): 'iss_213rf_fmovie001_prime',
    (1804721310, 1804767010): 'iss_213rf_fmovie002_prime',
    (1833416551, 1833466786): 'iss_231ri_egapmovmp001_prime',
    (1833759933, 1833807548): 'iss_232rf_fmovie001_prime',
    (1834062095, 1834063171): 'iss_232ri_propretrg001_prime',
    (1834715380, 1834762079): 'iss_232ri_egapmovmp001_prime_1',
    (1834762780, 1834782653): 'iss_232ri_egapmovmp001_prime_2',
    (1835923367, 1835949753): 'iss_233rf_fmovie001_prime_1',
    (1835950068, 1835952458): 'iss_233rf_fmovie001_prime_2',
    (1836263420, 1836266080): 'iss_233ri_hiresafrg001_prime',
    (1838169062, 1838191406): 'iss_234rf_fmovie001_prime',
    (1838765406, 1838810394): 'iss_234ri_egapmovmp001_prime',
    (1840805238, 1840851450): 'iss_235rf_fmovie001_prime',
    (1841517293, 1841542213): 'iss_235rf_fmovie002_prime_1',
    (1841542553, 1841566267): 'iss_235rf_fmovie002_prime_2',
    (1844255680, 1844308631): 'iss_236rf_fmovie002_prime',
    (1848840160, 1848890969): 'iss_239rf_fmovie001_prime',
    (1849277472, 1849292534): 'iss_239ri_hiresafrg001_prime_1',
    (1849292922, 1849298000): 'iss_239ri_hiresafrg001_prime_2',
    (1849701045, 1849727149): 'iss_239rf_fmovie002_prime_1',
    (1849727745, 1849746145): 'iss_239rf_fmovie002_prime_2',
    (1850609421, 1850636617): 'iss_240rf_fmovie002_prime',
    (1851189265, 1851242541): 'iss_241rf_fmovie001_prime',
    (1852769180, 1852822421): 'iss_242rf_fmovie001_prime',
    (1853233598, 1853257114): 'iss_243rf_fmovie001_prime_1',
    (1853259193, 1853282709): 'iss_243rf_fmovie001_prime_2',
    (1854445005, 1854447161): 'iss_244ri_propretrg001_prime',
    (1855140650, 1855149230): 'iss_245ri_hiresafrg002_prime',
    (1856269247, 1856322391): 'iss_246rf_fmovie002_prime',
    (1860621365, 1860623101): 'iss_253rf_fmovie001_prime_1',
    (1860623305, 1860676191): 'iss_253rf_fmovie001_prime_2',
    (1860685105, 1860686471): 'iss_253rf_fmovie001_prime_3',
    (1860782646, 1860785522): 'iss_253ri_hiresafrg001_pie',
    (1862506658, 1862534260): 'iss_256rf_fmovie001_prime_1',
    (1862534858, 1862562460): 'iss_256rf_fmovie001_prime_2',
    (1862691489, 1862700450): 'iss_256ri_hiresafrg002_prime',
    (1864955784, 1865008643): 'iss_260rf_fmovie001_prime',
    (1865103955, 1865106767): 'iss_260ri_hiresafrg001_prime',
    (1866210812, 1866212092): 'iss_262rf_fmovie001_prime_01',
    (1866212222, 1866213502): 'iss_262rf_fmovie001_prime_02',
    (1866213632, 1866214912): 'iss_262rf_fmovie001_prime_03',
    (1866215042, 1866216322): 'iss_262rf_fmovie001_prime_04',
    (1866216452, 1866217732): 'iss_262rf_fmovie001_prime_05',
    (1866217862, 1866219142): 'iss_262rf_fmovie001_prime_06',
    (1866219272, 1866220552): 'iss_262rf_fmovie001_prime_07',
    (1866220682, 1866221962): 'iss_262rf_fmovie001_prime_08',
    (1866222092, 1866223372): 'iss_262rf_fmovie001_prime_09',
    (1866223502, 1866224782): 'iss_262rf_fmovie001_prime_10',
    (1866224912, 1866226192): 'iss_262rf_fmovie001_prime_11',
    (1866226442, 1866230310): 'iss_262rf_fmovie001_prime_12',
    (1866237212, 1866238492): 'iss_262rf_fmovie001_prime_13',
    (1866238622, 1866239902): 'iss_262rf_fmovie001_prime_14',
    (1866240032, 1866241312): 'iss_262rf_fmovie001_prime_15',
    (1866241442, 1866242722): 'iss_262rf_fmovie001_prime_16',
    (1866242852, 1866244132): 'iss_262rf_fmovie001_prime_17',
    (1867972213, 1867991971): 'iss_265rf_fmovie001_prime',
    (1869959036, 1869970267): 'iss_268rf_fmovie001_prime_1',
    (1869972776, 1869974046): 'iss_268rf_fmovie001_prime_2',
    (1869974186, 1869975456): 'iss_268rf_fmovie001_prime_3',
    (1869975606, 1869976876): 'iss_268rf_fmovie001_prime_4',
    (1869977026, 1869978296): 'iss_268rf_fmovie001_prime_5',
    (1869978446, 1869979716): 'iss_268rf_fmovie001_prime_6',
    (1869979866, 1869981136): 'iss_268rf_fmovie001_prime_7',
    (1869981286, 1869982556): 'iss_268rf_fmovie001_prime_8',
    (1869982946, 1869989098): 'iss_268rf_fmovie001_prime_9',
    (1872298361, 1872325959): 'iss_272rf_fmovie001_prime',
    (1873378488, 1873395652): 'iss_274rf_fmovie001_prime',
    (1873415748, 1873456613): 'iss_274rf_fmovie002_prime',
    (1874525875, 1874561901): 'iosic_276rb_complitb4001_si',
    (1874630321, 1874635672): 'iss_276ri_hiresafrg001_prime_1',
    (1874636231, 1874640868): 'iss_276ri_hiresafrg001_prime_2',
    (1875199754, 1875206482): 'iss_277ri_hiresafrg001_prime',
    (1878517941, 1878529007): 'iss_283ra_complita2001_cirs',
    (1880154911, 1880157667): 'iss_286ri_casdivlit001_cirs',
    (1880158471, 1880159957): 'iss_286ri_propretrg001_prime',
    (1880692010, 1880693374): 'iss_287ri_complitcd001_cirs',
    (1880795585, 1880797348): 'iss_287ri_propretrg001_prime',
    (1881776562, 1881830006): 'iss_289rf_fmovie001_prime',
    (1883393812, 1883445888): 'iss_292rf_fmovie001_prime',
    (1883500233, 1883501276): 'iss_292ri_casdivlit001_cirs',
    (1883514713, 1883516501): 'iss_292ri_propretrg001_prime',
}

# Build explicit product id range rules for F Ring cross products.
# This avoids broad wildcard matching during lookup and keeps OPUS import fast.
_f_ring_cross_products_list = []

for product_id_range, observation_id in _PRODUCT_ID_TO_F_RING_OBSERVATION_ID_MAPPING.items():
    product_id_regex = range_regex(*product_id_range)
    _f_ring_cross_products_list += [
        (rf'.*/(COISS_[12]xxx)(|_v[0-9\.]+)/(COISS_[12]...)/data/(\w+/([NW])({product_id_regex})_[0-9]+).*', 0,
            [# F Ring Reproj (cassini_iss_fring_mosaics_rsfrench2025)
                # data_reproj_img
                rf'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025/data_reproj_img/{observation_id}/\6#LOWER#\5_reproj_img_metadata_params.tab',
                rf'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025/data_reproj_img/{observation_id}/\6#LOWER#\5_reproj_img.img',
                rf'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025/data_reproj_img/{observation_id}/\6#LOWER#\5_reproj_img.lblx',
                rf'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025/data_reproj_img/{observation_id}/\6#LOWER#\5_reproj_suppl.txt',
                # browse_reproj_img
                rf'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025/browse_reproj_img/{observation_id}/\6#LOWER#\5_browse_reproj_img_full.png',
                rf'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025/browse_reproj_img/{observation_id}/\6#LOWER#\5_browse_reproj_img_med.png',
                rf'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025/browse_reproj_img/{observation_id}/\6#LOWER#\5_browse_reproj_img_small.png',
                rf'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025/browse_reproj_img/{observation_id}/\6#LOWER#\5_browse_reproj_img_thumb.png',
                rf'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025/browse_reproj_img/{observation_id}/\6#LOWER#\5_browse_reproj_img.lblx',
            ]),
    ]

cross_pds3_pds4_products = translator.TranslatorByRegex([
    (r'.*/(COISS_[12]xxx)(|_v[0-9\.]+)/(COISS_[12]...)/data/(\w+/([NW])(([0-9]{3})[0-9]{7})_[0-9]+).*', 0,
        [   # F Ring Reproj (cassini_iss_fring_mosaics_rsfrench2025)
            # index
            r'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025/miscellaneous/global_reproj_img_index.lblx',
            r'bundles/cassini_iss_fring_mosaics_rsfrench2025/cassini_iss_fring_mosaics_rsfrench2025/miscellaneous/global_reproj_img_index.tab',

            # B Ring Reproj (cassini_iss_spokes_hedman-hamilton-2024)
            # data_derived
            r'bundles/cassini_iss_spokes_hedman-hamilton-2024/cassini_iss_spokes_hedman-hamilton-2024/data_derived/\7XXXXXXX/\6#LOWER#\5_rprj_suppl.txt',
            r'bundles/cassini_iss_spokes_hedman-hamilton-2024/cassini_iss_spokes_hedman-hamilton-2024/data_derived/\7XXXXXXX/\6#LOWER#\5_rprj.fits',
            r'bundles/cassini_iss_spokes_hedman-hamilton-2024/cassini_iss_spokes_hedman-hamilton-2024/data_derived/\7XXXXXXX/\6#LOWER#\5_rprj.lblx',
            # browse_derived
            r'bundles/cassini_iss_spokes_hedman-hamilton-2024/cassini_iss_spokes_hedman-hamilton-2024/browse_derived/\7XXXXXXX/\6#LOWER#\5_rprj_browse.lblx',
            r'bundles/cassini_iss_spokes_hedman-hamilton-2024/cassini_iss_spokes_hedman-hamilton-2024/browse_derived/\7XXXXXXX/\6#LOWER#\5_rprj_browse.png',
        ]),
    *_f_ring_cross_products_list
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
    CROSS_PDS3_PDS4_PRODUCTS = cross_pds3_pds4_products + pds3file.Pds3File.CROSS_PDS3_PDS4_PRODUCTS
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
