##########################################################################################
# pds3file/rules/VGISS_xxxx.py
##########################################################################################

import re

import translator

import pdsfile.pds3file as pds3file

##########################################################################################
# DESCRIPTION_AND_ICON
##########################################################################################

description_and_icon_by_regex = translator.TranslatorByRegex([
    (r'volumes/.*/DATA',                 0, ('Images grouped by SC clock',          'IMAGEDIR')),
    (r'volumes/.*/DATA/C\d+X+',          0, ('Images grouped by SC clock',          'IMAGEDIR')),
    (r'volumes/.*/BROWSE',               0, ('Browse images grouped by SC clock',   'IMAGEDIR')),
    (r'volumes/.*/BROWSE/C\d+X+',        0, ('Browse images grouped by SC clock',   'IMAGEDIR')),
    (r'volumes/.*_RAW\.IMG',             0, ('Raw image, VICAR',                    'IMAGE'   )),
    (r'volumes/.*_CLEANED\.IMG',         0, ('Cleaned raw image, VICAR',            'IMAGE'   )),
    (r'volumes/.*_CALIB\.IMG',           0, ('Calibrated image, VICAR',             'IMAGE'   )),
    (r'volumes/.*_GEOMED\.IMG',          0, ('Undistorted image, VICAR',            'IMAGE'   )),
    (r'volumes/.*_GEOMA\.TAB',           0, ('ASCII distortion table',              'TABLE'   )),
    (r'volumes/.*_GEOMA\.DAT',           0, ('Distortion file, VICAR',              'DATA'    )),
    (r'volumes/.*_RESLOC\.DAT',          0, ('Reseau table, VICAR',                 'DATA'    )),
    (r'volumes/.*_RESLOC\.TAB',          0, ('ASCII Reseau table',                  'TABLE'   )),
    (r'volumes/.*/MIPL/.*\.DAT',         0, ('VICAR data file',                     'DATA'    )),
    (r'volumes/.*/DARKS/.*\.IMG',        0, ('Dark current image, VICAR',           'IMAGE'   )),
    (r'volumes/.*/INDEX/RAWIMAGES\.TAB', 0, ('Cumulative index of raw images only', 'IMAGE'   )),

    (r'volumes/.*/DOCUMENT/TUTORIAL.TXT',   0, ('&#11013; <b>Detailed tutorial</b> for this data set', 'INFO')),
    (r'volumes/.*/DOCUMENT/PROCESSING.TXT', 0, ('&#11013; <b>Processing history</b> of this data set', 'INFO')),
])

##########################################################################################
# SORT_KEY
##########################################################################################

sort_key = translator.TranslatorByRegex([

    # Sort data files into increasing level of processing
    (r'(\w+)(_RAW)\.(JPG|IMG)',     0, r'\1_1RAW.\3'    ),
    (r'(\w+)(_CLEANED)\.(JPG|IMG)', 0, r'\1_2CLEANED.\3'),
    (r'(\w+)(_CALIB)\.(JPG|IMG)',   0, r'\1_3CALIB.\3'  ),
    (r'(\w+)(_GEOMED)\.(JPG|IMG)',  0, r'\1_4GEOMED.\3' ),
    (r'(\w+)(_RESLOC)\.(DAT|TAB)',  0, r'\1_5RESLOC.\3' ),
    (r'(\w+)(_GEOMA)\.(DAT|TAB)',   0, r'\1_6GEOMA.\3'  ),

    (r'(\w+)(_RAW)\.LBL',           0, r'\1_1RAW.zLBL'    ),    # Label after matching file, not after everything
    (r'(\w+)(_CLEANED)\.LBL',       0, r'\1_2CLEANED.zLBL'),
    (r'(\w+)(_CALIB)\.LBL',         0, r'\1_3CALIB.zLBL'  ),
    (r'(\w+)(_GEOMED)\.LBL',        0, r'\1_4GEOMED.zLBL' ),
    (r'(\w+)(_RESLOC)\.LBL',        0, r'\1_5RESLOC.zLBL' ),
    (r'(\w+)(_GEOMA)\.LBL',         0, r'\1_6GEOMA.zLBL'  ),
])

##########################################################################################
# SPLIT_RULES
##########################################################################################

split_rules = translator.TranslatorByRegex([
    (r'(.*)_(RAW|CLEANED|CALIB|GEOMED|RESLOC|GEOMA)\.(.*)', 0, (r'\1', r'_\2', r'.\3')),
])

##########################################################################################
# ASSOCIATIONS
##########################################################################################

associations_to_volumes = translator.TranslatorByRegex([
    (r'.*/(VGISS_.xxx/VGISS_....)/(DATA|BROWSE)/(C\d{5}XX/C\d{7})_\w+\..*', 0,
            [r'volumes/\1/DATA/\3_CALIB.IMG',
             r'volumes/\1/DATA/\3_CALIB.LBL',
             r'volumes/\1/DATA/\3_CLEANED.IMG',
             r'volumes/\1/DATA/\3_CLEANED.LBL',
             r'volumes/\1/DATA/\3_GEOMED.IMG',
             r'volumes/\1/DATA/\3_GEOMED.LBL',
             r'volumes/\1/DATA/\3_RAW.IMG',
             r'volumes/\1/DATA/\3_RAW.LBL',
             r'volumes/\1/DATA/\3_GEOMA.DAT',
             r'volumes/\1/DATA/\3_GEOMA.TAB',
             r'volumes/\1/DATA/\3_GEOMA.LBL',
             r'volumes/\1/DATA/\3_RESLOC.DAT',
             r'volumes/\1/DATA/\3_RESLOC.TAB',
             r'volumes/\1/DATA/\3_RESLOC.LBL',
             r'volumes/\1/BROWSE/\3_CALIB.JPG',
             r'volumes/\1/BROWSE/\3_CALIB.LBL',
             r'volumes/\1/BROWSE/\3_CLEANED.JPG',
             r'volumes/\1/BROWSE/\3_CLEANED.LBL',
             r'volumes/\1/BROWSE/\3_GEOMED.JPG',
             r'volumes/\1/BROWSE/\3_GEOMED.LBL',
             r'volumes/\1/BROWSE/\3_RAW.JPG',
             r'volumes/\1/BROWSE/\3_RAW.LBL',
            ]),

    (r'.*/(VGISS_.xxx/VGISS_....)/(DATA|BROWSE)/(C\d{5}XX)', 0,
            [r'volumes/\1/DATA/\3',
             r'volumes/\1/BROWSE/\3'
            ]),
    (r'.*/(VGISS_.xxx/VGISS_....)/(DATA|BROWSE)', 0,
            [r'volumes/\1/DATA',
             r'volumes/\1/BROWSE'
            ]),
    (r'.*/(VGISS_.)999.*', 0, r'volumes/\1xxx'),
    (r'documents/VGISS_.xxx.*', 0,
            [r'volumes/VGISS_5xxx',
             r'volumes/VGISS_6xxx',
             r'volumes/VGISS_7xxx',
             r'volumes/VGISS_8xxx',
            ]),

# These associations are very slow to execute, not important.
#     # VG_0006 to VG_0008, selected Jupiter
#     (r'.*/VGISS_5xxx/VGISS_..../(DATA|BROWSE)/C.....XX/(C[0-9]{7}).*',
#                                                                 0,  [r'volumes/VG_0xxx/VG_000[6-8]/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_000[6-8]/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_000[6-8]/*/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_000[6-8]/*/*/*/*/\2*']),
#
#     # VG_0013 to VG_0025, Jupiter
#     (r'.*/VGISS_5xxx/VGISS_..../(DATA|BROWSE)/C.....XX/(C14[0-9]{5}|C15[0-4][0-9]{4}).*',
#                                                                 0,  [r'volumes/VG_0xxx/VG_0013/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0013/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0013/*/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0013/*/*/*/*/\2*']),
#     (r'.*/VGISS_5xxx/VGISS_..../(DATA|BROWSE)/C.....XX/(C15[45][0-9]{4}).*',
#                                                                 0,  [r'volumes/VG_0xxx/VG_0014/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0014/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0014/*/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0014/*/*/*/*/\2*']),
#     (r'.*/VGISS_5xxx/VGISS_..../(DATA|BROWSE)/C.....XX/(C15[5-9][0-9]{4}|C160[0-9]{4}).*',
#                                                                 0,  [r'volumes/VG_0xxx/VG_0015/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0015/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0015/*/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0015/*/*/*/*/\2*']),
#     (r'.*/VGISS_5xxx/VGISS_..../(DATA|BROWSE)/C.....XX/(C16[0-2][0-9]{4}).*',
#                                                                 0,  [r'volumes/VG_0xxx/VG_0016/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0016/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0016/*/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0016/*/*/*/*/\2*']),
#     (r'.*/VGISS_5xxx/VGISS_..../(DATA|BROWSE)/C.....XX/(C16[23][0-9]{4}).*',
#                                                                 0,  [r'volumes/VG_0xxx/VG_0017/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0017/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0017/*/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0017/*/*/*/*/\2*']),
#     (r'.*/VGISS_5xxx/VGISS_..../(DATA|BROWSE)/C.....XX/(C16[34][0-9]{4}).*',
#                                                                 0,  [r'volumes/VG_0xxx/VG_0018/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0018/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0018/*/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0018/*/*/*/*/\2*']),
#     (r'.*/VGISS_5xxx/VGISS_..../(DATA|BROWSE)/C.....XX/(C16[4-9][0-9]{4}|C17[0-3][0-9]{4}).*',
#                                                                 0,  [r'volumes/VG_0xxx/VG_0019/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0019/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0019/*/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0019/*/*/*/*/\2*']),
#
#     (r'.*/VGISS_5xxx/VGISS_..../(DATA|BROWSE)/C.....XX/(C175[0-9]{4}).*',
#                                                                 0,  [r'volumes/VG_0xxx/VG_0020/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0020/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0020/*/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0020/*/*/*/*/\2*']),
#     (r'.*/VGISS_5xxx/VGISS_..../(DATA|BROWSE)/C.....XX/(C18[0-9]{5}|C19[0-4][0-9]{4}).*',
#                                                                 0,  [r'volumes/VG_0xxx/VG_0020/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0020/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0020/*/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0020/*/*/*/*/\2*']),
#     (r'.*/VGISS_5xxx/VGISS_..../(DATA|BROWSE)/C.....XX/(C19[4-9][0-9]{4}).*',
#                                                                 0,  [r'volumes/VG_0xxx/VG_0021/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0021/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0021/*/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0021/*/*/*/*/\2*']),
#     (r'.*/VGISS_5xxx/VGISS_..../(DATA|BROWSE)/C.....XX/(C199[0-9]{4}|C20[0-3][0-9]{4}).*',
#                                                                 0,  [r'volumes/VG_0xxx/VG_0022/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0022/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0022/*/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0022/*/*/*/*/\2*']),
#     (r'.*/VGISS_5xxx/VGISS_..../(DATA|BROWSE)/C.....XX/(C20[34][0-9]{4}).*',
#                                                                 0,  [r'volumes/VG_0xxx/VG_0023/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0023/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0023/*/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0023/*/*/*/*/\2*']),
#     (r'.*/VGISS_5xxx/VGISS_..../(DATA|BROWSE)/C.....XX/(C20[4-6][0-9]{4}).*',
#                                                                 0,  [r'volumes/VG_0xxx/VG_0024/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0024/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0024/*/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0024/*/*/*/*/\2*']),
#     (r'.*/VGISS_5xxx/VGISS_..../(DATA|BROWSE)/C.....XX/(C20[67][0-9]{4}).*',
#                                                                 0,  [r'volumes/VG_0xxx/VG_0025//*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0025//*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0025//*/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0025//*/*/*/*/\2*']),
#
#     # VG_0004 to VG_0005, selected Saturn
#     (r'.*/VGISS_6xxx/VGISS_..../(DATA|BROWSE)/C.....XX/(C[0-9]{7}).*',
#                                                                 0,  [r'volumes/VG_0xxx/VG_000[45]/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_000[45]/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_000[45]/*/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_000[45]/*/*/*/*/\2*']),
#
#     # VG_0026 to VG_0038, Saturn
#     (r'.*/VGISS_6xxx/VGISS_..../(DATA|BROWSE)/C.....XX/(C32[0-9]{5}|C33[0-5]{4}).*',
#                                                                 0,  [r'volumes/VG_0xxx/VG_0026/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0026/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0026/*/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0026/*/*/*/*/\2*']),
#     (r'.*/VGISS_6xxx/VGISS_..../(DATA|BROWSE)/C.....XX/(C33[5-9][0-9]{4}|C34[0-4][0-9]{4}).*',
#                                                                 0,  [r'volumes/VG_0xxx/VG_0027/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0027/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0027/*/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0027/*/*/*/*/\2*']),
#     (r'.*/VGISS_6xxx/VGISS_..../(DATA|BROWSE)/C.....XX/(C34[4-7][0-9]{4}).*',
#                                                                 0,  [r'volumes/VG_0xxx/VG_0028/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0028/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0028/*/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0028/*/*/*/*/\2*']),
#     (r'.*/VGISS_6xxx/VGISS_..../(DATA|BROWSE)/C.....XX/(C34[7-9][0-9]{4}|C350[0-9]{4}).*',
#                                                                 0,  [r'volumes/VG_0xxx/VG_0029/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0029/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0029/*/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0029/*/*/*/*/\2*']),
#     (r'.*/VGISS_6xxx/VGISS_..../(DATA|BROWSE)/C.....XX/(C35[0-3][0-9]{4}).*',
#                                                                 0,  [r'volumes/VG_0xxx/VG_0030/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0030/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0030/*/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0030/*/*/*/*/\2*']),
#     (r'.*/VGISS_6xxx/VGISS_..../(DATA|BROWSE)/C.....XX/(C35[3-6][0-9]{4}).*',
#                                                                 0,  [r'volumes/VG_0xxx/VG_0031/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0031/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0031/*/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0031/*/*/*/*/\2*']),
#     (r'.*/VGISS_6xxx/VGISS_..../(DATA|BROWSE)/C.....XX/(C35[6-8][0-9]{4}).*',
#                                                                 0,  [r'volumes/VG_0xxx/VG_0032/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0032/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0032/*/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0032/*/*/*/*/\2*']),
#     (r'.*/VGISS_6xxx/VGISS_..../(DATA|BROWSE)/C.....XX/(C35[89][0-9]{4}|C41[0-9]{5}|C42[0-2][0-9]{4}).*',
#                                                                 0,  [r'volumes/VG_0xxx/VG_0033/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0033/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0033/*/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0033/*/*/*/*/\2*']),
#     (r'.*/VGISS_6xxx/VGISS_..../(DATA|BROWSE)/C.....XX/(C42[2-9][0-9]{4}|C43[0-2][0-9]{4}).*',
#                                                                 0,  [r'volumes/VG_0xxx/VG_0034/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0034/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0034/*/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0034/*/*/*/*/\2*']),
#     (r'.*/VGISS_6xxx/VGISS_..../(DATA|BROWSE)/C.....XX/(C43[2-5][0-9]{4}).*',
#                                                                 0,  [r'volumes/VG_0xxx/VG_0035/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0035/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0035/*/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0035/*/*/*/*/\2*']),
#     (r'.*/VGISS_6xxx/VGISS_..../(DATA|BROWSE)/C.....XX/(C43[5-8][0-9]{4}).*',
#                                                                 0,  [r'volumes/VG_0xxx/VG_0036/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0036/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0036/*/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0036/*/*/*/*/\2*']),
#     (r'.*/VGISS_6xxx/VGISS_..../(DATA|BROWSE)/C.....XX/(C43[89][0-9]{4}|C44[01][0-9]{4}).*',
#                                                                 0,  [r'volumes/VG_0xxx/VG_0037/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0037/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0037/*/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0037/*/*/*/*/\2*']),
#     (r'.*/VGISS_6xxx/VGISS_..../(DATA|BROWSE)/C.....XX/(C44[12][0-9]{4}).*',
#                                                                 0,  [r'volumes/VG_0xxx/VG_0038/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0038/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0038/*/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0038/*/*/*/*/\2*']),
#     (r'.*/VGISS_6xxx/VGISS_..../(DATA|BROWSE)/C.....XX/(C4[23][0-9]{5}).*',
#                                                                 0,   r'volumes/VG_0xxx/VG_0038/FOUND/*/\2*'),
#     (r'.*/VGISS_6xxx/VGISS_..../(DATA|BROWSE)/C.....XX/(C43[0-9]{5}).*',
#                                                                 0,  [r'volumes/VG_0xxx/VG_0038/BROWSE/CALIB/*/\2*']),
#
#     # VG_0001 to VG_0003, Uranus
#     (r'.*/VGISS_7xxx/VGISS_..../(DATA|BROWSE)/C.....XX/(C[0-9]{7}).*',
#                                                                 0,  [r'volumes/VG_0xxx/VG_000[1-3]/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_000[1-3]/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_000[1-3]/*/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_000[1-3]/*/*/*/*/\2*']),
#
#     # VG_0009 to VG_0012, Neptune
#     (r'.*/VGISS_8xxx/VGISS_..../(DATA|BROWSE)/(C.....XX)/(C[0-9]{7}).*',
#                                                                 0,  [r'volumes/VG_0xxx/VG_0009/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0009/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0009/*/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_0009/*/*/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_001[0-2]/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_001[0-2]/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_001[0-2]/*/*/*/\2*',
#                                                                      r'volumes/VG_0xxx/VG_001[0-2]/*/*/*/*/\2*']),
])

associations_to_previews = translator.TranslatorByRegex([
    (r'.*/(VGISS_.xxx/VGISS_....)/(DATA|BROWSE)/(C\d{5}XX/C\d{7})_\w+\..*', 0,
            [r'previews/\1/DATA/\3_full.jpg',
             r'previews/\1/DATA/\3_med.jpg',
             r'previews/\1/DATA/\3_small.jpg',
             r'previews/\1/DATA/\3_thumb.jpg',
            ]),
    (r'.*/(VGISS_.xxx/VGISS_....)/(DATA|BROWSE)/(C\d{5}XX)',    0, r'previews/\1/DATA/\3'),
    (r'.*/(VGISS_.xxx/VGISS_....)/BROWSE',                      0, r'previews/\1/DATA'),
    (r'.*/(VGISS_.)999.*',                                      0, r'previews/\1xxx'),
])

associations_to_metadata = translator.TranslatorByRegex([
    (r'volumes/(VGISS_.xxx)/(VGISS_....)/(DATA|BROWSE)/(C\d{5}XX)/(C\d{7})_\w+\..*', 0,
            [r'metadata/\1/\2/\2_index.tab/\5',
             r'metadata/\1/\2/\2_raw_image_index.tab/\5',
             r'metadata/\1/\2/\2_supplemental_index.tab/\5',
             r'metadata/\1/\2/\2_ring_summary.tab/\5',
             r'metadata/\1/\2/\2_moon_summary.tab/\5',
             r'metadata/\1/\2/\2_jupiter_summary.tab/\5',
             r'metadata/\1/\2/\2_saturn_summary.tab/\5',
             r'metadata/\1/\2/\2_uranus_summary.tab/\5',
             r'metadata/\1/\2/\2_neptune_summary.tab/\5',
            ]),
    (r'volumes/(VGISS_.xxx)/(VGISS_....)/(DATA|BROWSE)/C\d{5}XX',  0, r'metadata/\1/\2'),
    (r'volumes/(VGISS_.xxx)/(VGISS_....)/(DATA|BROWSE)',           0, r'metadata/\1/\2'),
    (r'volumes/(VGISS_.xxx)/(VGISS_....)/INDEX/RAWIMAGES\..*',     0,
            [r'metadata/\1/\2/\2_raw_image_index.tab',
             r'metadata/\1/\2/\2_raw_image_index.lbl',
            ]),
    (r'metadata/(VGISS_.xxx/VGISS_.)[12]..', 0,
            r'metadata/\g<1>999'),
    (r'metadata/(VGISS_.xxx/VGISS_.)[12]../(VGISS_.)..._(.*)\..*', 0,
            [r'metadata/\g<1>999/\g<2>999_\3.tab',
             r'metadata/\g<1>999/\g<2>999_\3.csv',
             r'metadata/\g<1>999/\g<2>999_\3.lbl',
            ]),
])

associations_to_documents = translator.TranslatorByRegex([
    (r'volumes/VGISS_.xxx.*', 0,
            r'documents/VGISS_5xxx/*'),
    (r'(volumes/VGISS_.xxx/VGISS_....).*', 0,
            [r'\1/DOCUMENT/TUTORIAL.TXT',
             r'\1/DOCUMENT/PROCESSING.TXT',
            ]),
    (r'volumes/(VGISS_.)xxx.*', 0,
            [r'volumes/\1xxx/\g<1>201/DOCUMENT/TUTORIAL.TXT',
             r'volumes/\1xxx/\g<1>201/DOCUMENT/PROCESSING.TXT',
            ]),
])

##########################################################################################
# VIEW_OPTIONS (grid_view_allowed, multipage_view_allowed, continuous_view_allowed)
##########################################################################################

view_options = translator.TranslatorByRegex([
    (r'(volumes|previews)/VGISS_..../VGISS_..../(DATA|BROWSE)',     0, (True, True, True)),
    (r'(volumes|previews)/VGISS_..../VGISS_..../(DATA|BROWSE)/\w+', 0, (True, True, True)),
])

##########################################################################################
# NEIGHBORS
##########################################################################################

neighbors = translator.TranslatorByRegex([
    (r'(volumes|previews)/(VGISS_..../VGISS_..)../(DATA|BROWSE)',     0, r'\1/\2*/\3'),
    (r'(volumes|previews)/(VGISS_..../VGISS_..)../(DATA|BROWSE)/\w+', 0, r'\1/\2*/\3/*'),
])

##########################################################################################
# VIEWABLES
##########################################################################################

default_viewables = translator.TranslatorByRegex([
    (r'volumes/(.*)/(DATA/\w+/.*)_(RAW|CLEANED|CALIB|GEOMED)\..*', 0,
            [r'previews/\1/\2_full.jpg',
             r'previews/\1/\2_med.jpg',
             r'previews/\1/\2_small.jpg',
             r'previews/\1/\2_thumb.jpg',
            ]),
])

##########################################################################################
# OPUS_TYPE
##########################################################################################

opus_type = translator.TranslatorByRegex([
    (r'volumes/.*/DATA/.*/C\d{7}_RAW\..*',       0, ('Voyager ISS',  0, 'vgiss_raw',     'Raw Image',                     True)),
    (r'volumes/.*/DATA/.*/C\d{7}_CLEANED\..*',   0, ('Voyager ISS', 10, 'vgiss_cleaned', 'Cleaned Image',                 True)),
    (r'volumes/.*/DATA/.*/C\d{7}_CALIB\..*',     0, ('Voyager ISS', 20, 'vgiss_calib',   'Calibrated Image',              True)),
    (r'volumes/.*/DATA/.*/C\d{7}_GEOMED\..*',    0, ('Voyager ISS', 30, 'vgiss_geomed',  'Geometrically Corrected Image', True)),
    (r'volumes/.*/DATA/.*/C\d{7}_RESLOC\..*',    0, ('Voyager ISS', 40, 'vgiss_resloc',  'Reseau Table',                  True)),
    (r'volumes/.*/DATA/.*/C\d{7}_GEOMA\..*',     0, ('Voyager ISS', 50, 'vgiss_geoma',   'Geometric Tiepoint Table',      True)),
    (r'volumes/.*/BROWSE/.*/C\d{7}_RAW\..*',     0, ('Voyager ISS', 60, 'vgiss_raw_browse',     'Extra Preview (raw)',                     False)),
    (r'volumes/.*/BROWSE/.*/C\d{7}_CLEANED\..*', 0, ('Voyager ISS', 70, 'vgiss_cleaned_browse', 'Extra Preview (cleaned)',                 False)),
    (r'volumes/.*/BROWSE/.*/C\d{7}_CALIB\..*',   0, ('Voyager ISS', 80, 'vgiss_calib_browse',   'Extra Preview (calibrated)',              False)),
    (r'volumes/.*/BROWSE/.*/C\d{7}_GEOMED\..*',  0, ('Voyager ISS', 90, 'vgiss_geomed_browse',  'Extra Preview (geometrically corrected)', False)),
    (r'volumes/.*/BROWSE/.*/C\d{7}_GEOMED\..*',  0, ('Voyager ISS', 90, 'vgiss_geomed_browse',  'Extra Preview (geometrically corrected)', False)),
    # Documentation
    (r'documents/VGISS_.xxx/.*',                 0, ('Voyager ISS', 100, 'vgiss_documentation', 'Documentation', False)),
])

##########################################################################################
# OPUS_FORMAT
##########################################################################################

opus_format = translator.TranslatorByRegex([
    (r'.*\.IMG', 0, ('Binary', 'VICAR')),
    (r'.*\.DAT', 0, ('Binary', 'VICAR')),
    (r'.*\.IMQ', 0, ('Binary', 'Compressed EDR')),
    (r'.*\.IBQ', 0, ('Binary', 'PDS1 Attached Label')),
])

##########################################################################################
# OPUS_PRODUCTS
##########################################################################################

# Note: These patterns do not currently support version numbers in the volset directory name.
opus_products = translator.TranslatorByRegex([
    (r'.*volumes/(VGISS_[5-8]xxx)/(VGISS_[5-8]...)/DATA/(C\d{5}XX/C\d{7})_[A-Z]+\.(IMG|DAT|LBL|TAB)', 0,
            [r'volumes/\1/\2/DATA/\3_CALIB.IMG',
             r'volumes/\1/\2/DATA/\3_CALIB.LBL',
             r'volumes/\1/\2/DATA/\3_CLEANED.IMG',
             r'volumes/\1/\2/DATA/\3_CLEANED.LBL',
             r'volumes/\1/\2/DATA/\3_GEOMED.IMG',
             r'volumes/\1/\2/DATA/\3_GEOMED.LBL',
             r'volumes/\1/\2/DATA/\3_RAW.IMG',
             r'volumes/\1/\2/DATA/\3_RAW.LBL',
             r'volumes/\1/\2/DATA/\3_GEOMA.DAT',
             r'volumes/\1/\2/DATA/\3_GEOMA.TAB',
             r'volumes/\1/\2/DATA/\3_GEOMA.LBL',
             r'volumes/\1/\2/DATA/\3_RESLOC.DAT',
             r'volumes/\1/\2/DATA/\3_RESLOC.TAB',
             r'volumes/\1/\2/DATA/\3_RESLOC.LBL',
             r'volumes/\1/\2/BROWSE/\3_CALIB.JPG',
             r'volumes/\1/\2/BROWSE/\3_CALIB.LBL',
             r'volumes/\1/\2/BROWSE/\3_CLEANED.JPG',
             r'volumes/\1/\2/BROWSE/\3_CLEANED.LBL',
             r'volumes/\1/\2/BROWSE/\3_GEOMED.JPG',
             r'volumes/\1/\2/BROWSE/\3_GEOMED.LBL',
             r'volumes/\1/\2/BROWSE/\3_RAW.JPG',
             r'volumes/\1/\2/BROWSE/\3_RAW.LBL',
             r'previews/\1/\2/DATA/\3_full.jpg',
             r'previews/\1/\2/DATA/\3_med.jpg',
             r'previews/\1/\2/DATA/\3_small.jpg',
             r'previews/\1/\2/DATA/\3_thumb.jpg',
             r'metadata/\1/\2/\2_moon_summary.tab',
             r'metadata/\1/\2/\2_moon_summary.lbl',
             r'metadata/\1/\2/\2_ring_summary.tab',
             r'metadata/\1/\2/\2_ring_summary.lbl',
             r'metadata/\1/\2/\2_jupiter_summary.tab',
             r'metadata/\1/\2/\2_jupiter_summary.lbl',
             r'metadata/\1/\2/\2_saturn_summary.tab',
             r'metadata/\1/\2/\2_saturn_summary.lbl',
             r'metadata/\1/\2/\2_uranus_summary.tab',
             r'metadata/\1/\2/\2_uranus_summary.lbl',
             r'metadata/\1/\2/\2_neptune_summary.tab',
             r'metadata/\1/\2/\2_neptune_summary.lbl',
             r'metadata/\1/\2/\2_inventory.csv',
             r'metadata/\1/\2/\2_inventory.lbl',
             r'metadata/\1/\2/\2_index.tab',
             r'metadata/\1/\2/\2_index.lbl',
             r'metadata/\1/\2/\2_raw_image_index.tab',
             r'metadata/\1/\2/\2_raw_image_index.lbl',
             r'metadata/\1/\2/\2_supplemental_index.tab',
             r'metadata/\1/\2/\2_supplemental_index.lbl',
             r'documents/VGISS_5xxx/*.[!lz]*'
            ]),
])

##########################################################################################
# OPUS_ID
##########################################################################################

opus_id = translator.TranslatorByRegex([
    (r'.*/VGISS_5([12])../DATA/C\d{5}XX/C(\d{7})_.*', 0, r'vg-iss-\1-j-c\2'),
    (r'.*/VGISS_6([12])../DATA/C\d{5}XX/C(\d{7})_.*', 0, r'vg-iss-\1-s-c\2'),
    (r'.*/VGISS_7.../DATA/C\d{5}XX/C(\d{7})_.*',      0, r'vg-iss-2-u-c\1'),
    (r'.*/VGISS_8.../DATA/C\d{5}XX/C(\d{7})_.*',      0, r'vg-iss-2-n-c\1'),
])

##########################################################################################
# OPUS_ID_TO_PRIMARY_LOGICAL_PATH
##########################################################################################

opus_id_to_primary_logical_path = translator.TranslatorByRegex([
    (r'vg-iss-1-j-c(1[3-4]...)(..)', 0, r'volumes/VGISS_5xxx/VGISS_5101/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-j-c(15[0-1]..)(..)', 0, r'volumes/VGISS_5xxx/VGISS_5102/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-j-c(15[2-3]..)(..)', 0, r'volumes/VGISS_5xxx/VGISS_5103/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-j-c(154[0-4].)(..)', 0, r'volumes/VGISS_5xxx/VGISS_5104/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-j-c(154[5-9].)(..)', 0, r'volumes/VGISS_5xxx/VGISS_5105/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-j-c(155..)(..)'    , 0, r'volumes/VGISS_5xxx/VGISS_5106/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-j-c(156..)(..)'    , 0, r'volumes/VGISS_5xxx/VGISS_5107/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-j-c(157..)(..)'    , 0, r'volumes/VGISS_5xxx/VGISS_5108/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-j-c(158..)(..)'    , 0, r'volumes/VGISS_5xxx/VGISS_5109/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-j-c(159..)(..)'    , 0, r'volumes/VGISS_5xxx/VGISS_5110/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-j-c(160..)(..)'    , 0, r'volumes/VGISS_5xxx/VGISS_5111/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-j-c(161..)(..)'    , 0, r'volumes/VGISS_5xxx/VGISS_5112/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-j-c(162[0-4].)(..)', 0, r'volumes/VGISS_5xxx/VGISS_5113/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-j-c(162[5-9].)(..)', 0, r'volumes/VGISS_5xxx/VGISS_5114/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-j-c(163[0-4].)(..)', 0, r'volumes/VGISS_5xxx/VGISS_5115/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-j-c(163[5-9].)(..)', 0, r'volumes/VGISS_5xxx/VGISS_5116/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-j-c(164[0-4].)(..)', 0, r'volumes/VGISS_5xxx/VGISS_5117/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-j-c(164[5-9].)(..)', 0, r'volumes/VGISS_5xxx/VGISS_5118/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-j-c(16[5-9]..)(..)', 0, r'volumes/VGISS_5xxx/VGISS_5119/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-j-c(17...)(..)'    , 0, r'volumes/VGISS_5xxx/VGISS_5120/DATA/C\1XX/C\1\2_RAW.IMG'),

    (r'vg-iss-2-j-c(18[0-7]..)(..)', 0, r'volumes/VGISS_5xxx/VGISS_5201/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-j-c(18[8-9]..)(..)', 0, r'volumes/VGISS_5xxx/VGISS_5202/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-j-c(19[0-1]..)(..)', 0, r'volumes/VGISS_5xxx/VGISS_5202/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-j-c(19[2-3]..)(..)', 0, r'volumes/VGISS_5xxx/VGISS_5203/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-j-c(19[4-5]..)(..)', 0, r'volumes/VGISS_5xxx/VGISS_5204/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-j-c(19[6-7]..)(..)', 0, r'volumes/VGISS_5xxx/VGISS_5205/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-j-c(19[8-9]..)(..)', 0, r'volumes/VGISS_5xxx/VGISS_5206/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-j-c(20[0-1]..)(..)', 0, r'volumes/VGISS_5xxx/VGISS_5207/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-j-c(202..)(..)'    , 0, r'volumes/VGISS_5xxx/VGISS_5208/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-j-c(203..)(..)'    , 0, r'volumes/VGISS_5xxx/VGISS_5209/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-j-c(204..)(..)'    , 0, r'volumes/VGISS_5xxx/VGISS_5210/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-j-c(205[0-4].)(..)', 0, r'volumes/VGISS_5xxx/VGISS_5211/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-j-c(205[5-9].)(..)', 0, r'volumes/VGISS_5xxx/VGISS_5212/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-j-c(206[0-4].)(..)', 0, r'volumes/VGISS_5xxx/VGISS_5213/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-j-c(206[5-9].)(..)', 0, r'volumes/VGISS_5xxx/VGISS_5214/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-j-c(20[7-8]..)(..)', 0, r'volumes/VGISS_5xxx/VGISS_5214/DATA/C\1XX/C\1\2_RAW.IMG'),

    (r'vg-iss-1-s-c(2....)(..)'    , 0, r'volumes/VGISS_6xxx/VGISS_6101/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-s-c(3[0-1]...)(..)', 0, r'volumes/VGISS_6xxx/VGISS_6101/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-s-c(32[0-7]..)(..)', 0, r'volumes/VGISS_6xxx/VGISS_6101/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-s-c(32[8-9]..)(..)', 0, r'volumes/VGISS_6xxx/VGISS_6102/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-s-c(33[0-2]..)(..)', 0, r'volumes/VGISS_6xxx/VGISS_6103/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-s-c(33[2-4]..)(..)', 0, r'volumes/VGISS_6xxx/VGISS_6104/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-s-c(33[5-7]..)(..)', 0, r'volumes/VGISS_6xxx/VGISS_6105/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-s-c(33[8-9]..)(..)', 0, r'volumes/VGISS_6xxx/VGISS_6106/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-s-c(340..)(..)'    , 0, r'volumes/VGISS_6xxx/VGISS_6106/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-s-c(34[1-3]..)(..)', 0, r'volumes/VGISS_6xxx/VGISS_6107/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-s-c(344..)(..)'    , 0, r'volumes/VGISS_6xxx/VGISS_6108/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-s-c(345..)(..)'    , 0, r'volumes/VGISS_6xxx/VGISS_6109/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-s-c(346..)(..)'    , 0, r'volumes/VGISS_6xxx/VGISS_6110/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-s-c(347..)(..)'    , 0, r'volumes/VGISS_6xxx/VGISS_6111/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-s-c(348..)(..)'    , 0, r'volumes/VGISS_6xxx/VGISS_6112/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-s-c(349..)(..)'    , 0, r'volumes/VGISS_6xxx/VGISS_6113/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-s-c(350..)(..)'    , 0, r'volumes/VGISS_6xxx/VGISS_6114/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-s-c(351..)(..)'    , 0, r'volumes/VGISS_6xxx/VGISS_6115/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-s-c(35[2-3]..)(..)', 0, r'volumes/VGISS_6xxx/VGISS_6116/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-s-c(354..)(..)'    , 0, r'volumes/VGISS_6xxx/VGISS_6117/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-s-c(355..)(..)'    , 0, r'volumes/VGISS_6xxx/VGISS_6118/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-s-c(356..)(..)'    , 0, r'volumes/VGISS_6xxx/VGISS_6119/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-s-c(357..)(..)'    , 0, r'volumes/VGISS_6xxx/VGISS_6120/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-1-s-c(35[8-9]..)(..)', 0, r'volumes/VGISS_6xxx/VGISS_6121/DATA/C\1XX/C\1\2_RAW.IMG'),

    (r'vg-iss-2-s-c(3....)(..)'    , 0, r'volumes/VGISS_6xxx/VGISS_6201/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-s-c(40...)(..)'    , 0, r'volumes/VGISS_6xxx/VGISS_6201/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-s-c(41[0-6]..)(..)', 0, r'volumes/VGISS_6xxx/VGISS_6201/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-s-c(41[7-9]..)(..)', 0, r'volumes/VGISS_6xxx/VGISS_6202/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-s-c(42[0-2]..)(..)', 0, r'volumes/VGISS_6xxx/VGISS_6203/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-s-c(42[3-5]..)(..)', 0, r'volumes/VGISS_6xxx/VGISS_6204/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-s-c(42[6-8]..)(..)', 0, r'volumes/VGISS_6xxx/VGISS_6205/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-s-c(429..)(..)'    , 0, r'volumes/VGISS_6xxx/VGISS_6206/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-s-c(43[0-1]..)(..)', 0, r'volumes/VGISS_6xxx/VGISS_6206/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-s-c(43[2-3]..)(..)', 0, r'volumes/VGISS_6xxx/VGISS_6207/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-s-c(434..)(..)'    , 0, r'volumes/VGISS_6xxx/VGISS_6208/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-s-c(435..)(..)'    , 0, r'volumes/VGISS_6xxx/VGISS_6209/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-s-c(436..)(..)'    , 0, r'volumes/VGISS_6xxx/VGISS_6210/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-s-c(437..)(..)'    , 0, r'volumes/VGISS_6xxx/VGISS_6211/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-s-c(438..)(..)'    , 0, r'volumes/VGISS_6xxx/VGISS_6212/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-s-c(439..)(..)'    , 0, r'volumes/VGISS_6xxx/VGISS_6213/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-s-c(44[0-1]..)(..)', 0, r'volumes/VGISS_6xxx/VGISS_6214/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-s-c(44[2-3]..)(..)', 0, r'volumes/VGISS_6xxx/VGISS_6215/DATA/C\1XX/C\1\2_RAW.IMG'),

    (r'vg-iss-2-u-c(24[4-9]..)(..)', 0, r'volumes/VGISS_7xxx/VGISS_7201/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-u-c(25...)(..)'    , 0, r'volumes/VGISS_7xxx/VGISS_7202/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-u-c(26[0-2]..)(..)', 0, r'volumes/VGISS_7xxx/VGISS_7203/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-u-c(26[3-5]..)(..)', 0, r'volumes/VGISS_7xxx/VGISS_7204/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-u-c(26[6-7]..)(..)', 0, r'volumes/VGISS_7xxx/VGISS_7205/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-u-c(26[8-9]..)(..)', 0, r'volumes/VGISS_7xxx/VGISS_7206/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-u-c(27...)(..)'    , 0, r'volumes/VGISS_7xxx/VGISS_7207/DATA/C\1XX/C\1\2_RAW.IMG'),

    (r'vg-iss-2-n-c(08...)(..)'    , 0, r'volumes/VGISS_8xxx/VGISS_8201/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-n-c(09[0-4]..)(..)', 0, r'volumes/VGISS_8xxx/VGISS_8201/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-n-c(09[5-9]..)(..)', 0, r'volumes/VGISS_8xxx/VGISS_8202/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-n-c(10[0-3]..)(..)', 0, r'volumes/VGISS_8xxx/VGISS_8203/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-n-c(10[4-7]..)(..)', 0, r'volumes/VGISS_8xxx/VGISS_8204/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-n-c(10[8-9]..)(..)', 0, r'volumes/VGISS_8xxx/VGISS_8205/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-n-c(11[0-1]..)(..)', 0, r'volumes/VGISS_8xxx/VGISS_8206/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-n-c(11[2-3]..)(..)', 0, r'volumes/VGISS_8xxx/VGISS_8207/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-n-c(11[4-5]..)(..)', 0, r'volumes/VGISS_8xxx/VGISS_8208/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-n-c(11[6-9]..)(..)', 0, r'volumes/VGISS_8xxx/VGISS_8209/DATA/C\1XX/C\1\2_RAW.IMG'),
    (r'vg-iss-2-n-c(12...)(..)'    , 0, r'volumes/VGISS_8xxx/VGISS_8210/DATA/C\1XX/C\1\2_RAW.IMG'),
])

##########################################################################################
# Subclass definition
##########################################################################################

class VGISS_xxxx(pds3file.Pds3File):

    pds3file.Pds3File.VOLSET_TRANSLATOR = translator.TranslatorByRegex([('VGISS_[5678x]xxx', re.I, 'VGISS_xxxx')]) + \
                                          pds3file.Pds3File.VOLSET_TRANSLATOR

    DESCRIPTION_AND_ICON = description_and_icon_by_regex + pds3file.Pds3File.DESCRIPTION_AND_ICON
    SORT_KEY = sort_key + pds3file.Pds3File.SORT_KEY
    SPLIT_RULES = split_rules + pds3file.Pds3File.SPLIT_RULES
    VIEW_OPTIONS = view_options + pds3file.Pds3File.VIEW_OPTIONS
    NEIGHBORS = neighbors + pds3file.Pds3File.NEIGHBORS

    OPUS_TYPE = opus_type + pds3file.Pds3File.OPUS_TYPE
    OPUS_FORMAT = opus_format + pds3file.Pds3File.OPUS_FORMAT
    OPUS_PRODUCTS = opus_products + pds3file.Pds3File.OPUS_PRODUCTS
    OPUS_ID = opus_id
    OPUS_ID_TO_PRIMARY_LOGICAL_PATH = opus_id_to_primary_logical_path

    ASSOCIATIONS = pds3file.Pds3File.ASSOCIATIONS.copy()
    ASSOCIATIONS['volumes']   += associations_to_volumes
    ASSOCIATIONS['previews']  += associations_to_previews
    ASSOCIATIONS['metadata']  += associations_to_metadata
    ASSOCIATIONS['documents'] += associations_to_documents

    VIEWABLES = {'default': default_viewables}

    FILENAME_KEYLEN = 8     # trim off suffixes

# Global attribute shared by all subclasses
pds3file.Pds3File.OPUS_ID_TO_SUBCLASS = translator.TranslatorByRegex([(r'vg-iss-[12]-[jsun]-(?!prof).*', 0, VGISS_xxxx)]) + \
                                        pds3file.Pds3File.OPUS_ID_TO_SUBCLASS

##########################################################################################
# Update the global dictionary of subclasses
##########################################################################################

pds3file.Pds3File.SUBCLASSES['VGISS_xxxx'] = VGISS_xxxx
