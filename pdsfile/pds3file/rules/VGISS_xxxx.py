##########################################################################################
# pds3file/rules/VGISS_xxxx.py
##########################################################################################

import pdsfile.pds3file as pds3file
import translator
import re

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

##########################################################################################
# Unit tests
##########################################################################################

import pytest
from .pytest_support import *

@pytest.mark.parametrize(
    'input_path,expected',
    [
        ('volumes/VGISS_5xxx/VGISS_5101/DATA/C13854XX/C1385455_RAW.IMG',
         'VGISS_5xxx/opus_products/C1385455_RAW.txt')
    ]
)
def test_opus_products(request, input_path, expected):
    update = request.config.option.update
    opus_products_test(pds3file.Pds3File, input_path, TEST_RESULTS_DIR+expected, update)

@pytest.mark.parametrize(
    'input_path,category,expected',
    [
        ('volumes/VGISS_5xxx/VGISS_5101/DATA/C13854XX/C1385455_RAW.IMG',
         'volumes',
         'VGISS_5xxx/associated_abspaths/volumes_C1385455_RAW.txt')
    ]
)
def test_associated_abspaths(request, input_path, category, expected):
    update = request.config.option.update
    associated_abspaths_test(pds3file.Pds3File, input_path, category,
                             TEST_RESULTS_DIR+expected, update)

def test_opus_id_to_primary_logical_path():
    TESTS = [
        "VGISS_5101/DATA/C13854XX/C1385455_RAW.IMG",
        "VGISS_5101/DATA/C14604XX/C1460413_RAW.IMG",
        "VGISS_5101/DATA/C14700XX/C1470042_RAW.IMG",
        "VGISS_5101/DATA/C14800XX/C1480000_RAW.IMG",
        "VGISS_5101/DATA/C14901XX/C1490141_RAW.IMG",
        "VGISS_5102/DATA/C15000XX/C1500055_RAW.IMG",
        "VGISS_5102/DATA/C15100XX/C1510011_RAW.IMG",
        "VGISS_5103/DATA/C15201XX/C1520154_RAW.IMG",
        "VGISS_5103/DATA/C15301XX/C1530110_RAW.IMG",
        "VGISS_5104/DATA/C15400XX/C1540000_RAW.IMG",
        "VGISS_5105/DATA/C15450XX/C1545000_RAW.IMG",
        "VGISS_5106/DATA/C15508XX/C1550828_RAW.IMG",
        "VGISS_5107/DATA/C15600XX/C1560034_RAW.IMG",
        "VGISS_5108/DATA/C15700XX/C1570000_RAW.IMG",
        "VGISS_5109/DATA/C15801XX/C1580133_RAW.IMG",
        "VGISS_5110/DATA/C15900XX/C1590049_RAW.IMG",
        "VGISS_5111/DATA/C16000XX/C1600003_RAW.IMG",
        "VGISS_5112/DATA/C16100XX/C1610005_RAW.IMG",
        "VGISS_5113/DATA/C16200XX/C1620000_RAW.IMG",
        "VGISS_5113/DATA/C16200XX/C1620000_RAW.IMG",
        "VGISS_5113/DATA/C16210XX/C1621000_RAW.IMG",
        "VGISS_5113/DATA/C16220XX/C1622015_RAW.IMG",
        "VGISS_5113/DATA/C16230XX/C1623001_RAW.IMG",
        "VGISS_5113/DATA/C16240XX/C1624044_RAW.IMG",
        "VGISS_5114/DATA/C16250XX/C1625003_RAW.IMG",
        "VGISS_5114/DATA/C16250XX/C1625003_RAW.IMG",
        "VGISS_5114/DATA/C16260XX/C1626000_RAW.IMG",
        "VGISS_5114/DATA/C16270XX/C1627002_RAW.IMG",
        "VGISS_5114/DATA/C16280XX/C1628024_RAW.IMG",
        "VGISS_5114/DATA/C16290XX/C1629045_RAW.IMG",
        "VGISS_5115/DATA/C16300XX/C1630001_RAW.IMG",
        "VGISS_5115/DATA/C16300XX/C1630001_RAW.IMG",
        "VGISS_5115/DATA/C16310XX/C1631000_RAW.IMG",
        "VGISS_5115/DATA/C16320XX/C1632001_RAW.IMG",
        "VGISS_5115/DATA/C16332XX/C1633236_RAW.IMG",
        "VGISS_5115/DATA/C16340XX/C1634002_RAW.IMG",
        "VGISS_5116/DATA/C16350XX/C1635003_RAW.IMG",
        "VGISS_5116/DATA/C16350XX/C1635003_RAW.IMG",
        "VGISS_5116/DATA/C16360XX/C1636000_RAW.IMG",
        "VGISS_5116/DATA/C16370XX/C1637000_RAW.IMG",
        "VGISS_5116/DATA/C16380XX/C1638000_RAW.IMG",
        "VGISS_5116/DATA/C16390XX/C1639000_RAW.IMG",
        "VGISS_5117/DATA/C16400XX/C1640000_RAW.IMG",
        "VGISS_5117/DATA/C16400XX/C1640000_RAW.IMG",
        "VGISS_5117/DATA/C16410XX/C1641001_RAW.IMG",
        "VGISS_5117/DATA/C16420XX/C1642001_RAW.IMG",
        "VGISS_5117/DATA/C16430XX/C1643000_RAW.IMG",
        "VGISS_5117/DATA/C16440XX/C1644031_RAW.IMG",
        "VGISS_5118/DATA/C16450XX/C1645047_RAW.IMG",
        "VGISS_5118/DATA/C16450XX/C1645047_RAW.IMG",
        "VGISS_5118/DATA/C16467XX/C1646745_RAW.IMG",
        "VGISS_5118/DATA/C16470XX/C1647000_RAW.IMG",
        "VGISS_5118/DATA/C16480XX/C1648000_RAW.IMG",
        "VGISS_5118/DATA/C16495XX/C1649516_RAW.IMG",
        "VGISS_5119/DATA/C16501XX/C1650103_RAW.IMG",
        "VGISS_5119/DATA/C16600XX/C1660024_RAW.IMG",
        "VGISS_5119/DATA/C16730XX/C1673006_RAW.IMG",
        "VGISS_5119/DATA/C16847XX/C1684708_RAW.IMG",
        "VGISS_5119/DATA/C16909XX/C1690938_RAW.IMG",
        "VGISS_5120/DATA/C17182XX/C1718242_RAW.IMG",
        "VGISS_5120/DATA/C17244XX/C1724413_RAW.IMG",
        "VGISS_5120/DATA/C17306XX/C1730620_RAW.IMG",
        "VGISS_5120/DATA/C17502XX/C1750235_RAW.IMG",
        "VGISS_5201/DATA/C18110XX/C1811030_RAW.IMG",
        "VGISS_5201/DATA/C18381XX/C1838155_RAW.IMG",
        "VGISS_5201/DATA/C18409XX/C1840912_RAW.IMG",
        "VGISS_5201/DATA/C18501XX/C1850101_RAW.IMG",
        "VGISS_5201/DATA/C18600XX/C1860017_RAW.IMG",
        "VGISS_5201/DATA/C18702XX/C1870202_RAW.IMG",
        "VGISS_5202/DATA/C18801XX/C1880117_RAW.IMG",
        "VGISS_5202/DATA/C18900XX/C1890032_RAW.IMG",
        "VGISS_5202/DATA/C19002XX/C1900217_RAW.IMG",
        "VGISS_5202/DATA/C19101XX/C1910133_RAW.IMG",
        "VGISS_5203/DATA/C19200XX/C1920049_RAW.IMG",
        "VGISS_5203/DATA/C19312XX/C1931219_RAW.IMG",
        "VGISS_5204/DATA/C19400XX/C1940002_RAW.IMG",
        "VGISS_5204/DATA/C19500XX/C1950015_RAW.IMG",
        "VGISS_5205/DATA/C19602XX/C1960210_RAW.IMG",
        "VGISS_5205/DATA/C19703XX/C1970353_RAW.IMG",
        "VGISS_5206/DATA/C19800XX/C1980023_RAW.IMG",
        "VGISS_5206/DATA/C19900XX/C1990000_RAW.IMG",
        "VGISS_5207/DATA/C20001XX/C2000133_RAW.IMG",
        "VGISS_5207/DATA/C20100XX/C2010040_RAW.IMG",
        "VGISS_5208/DATA/C20209XX/C2020944_RAW.IMG",
        "VGISS_5209/DATA/C20301XX/C2030126_RAW.IMG",
        "VGISS_5210/DATA/C20400XX/C2040000_RAW.IMG",
        "VGISS_5211/DATA/C20501XX/C2050124_RAW.IMG",
        "VGISS_5211/DATA/C20501XX/C2050124_RAW.IMG",
        "VGISS_5211/DATA/C20510XX/C2051004_RAW.IMG",
        "VGISS_5211/DATA/C20520XX/C2052002_RAW.IMG",
        "VGISS_5211/DATA/C20530XX/C2053001_RAW.IMG",
        "VGISS_5211/DATA/C20540XX/C2054000_RAW.IMG",
        "VGISS_5212/DATA/C20550XX/C2055003_RAW.IMG",
        "VGISS_5212/DATA/C20550XX/C2055003_RAW.IMG",
        "VGISS_5212/DATA/C20560XX/C2056002_RAW.IMG",
        "VGISS_5212/DATA/C20570XX/C2057001_RAW.IMG",
        "VGISS_5212/DATA/C20580XX/C2058005_RAW.IMG",
        "VGISS_5212/DATA/C20590XX/C2059002_RAW.IMG",
        "VGISS_5213/DATA/C20603XX/C2060335_RAW.IMG",
        "VGISS_5213/DATA/C20603XX/C2060335_RAW.IMG",
        "VGISS_5213/DATA/C20611XX/C2061131_RAW.IMG",
        "VGISS_5213/DATA/C20620XX/C2062002_RAW.IMG",
        "VGISS_5213/DATA/C20630XX/C2063000_RAW.IMG",
        "VGISS_5213/DATA/C20640XX/C2064024_RAW.IMG",
        "VGISS_5214/DATA/C20650XX/C2065001_RAW.IMG",
        "VGISS_5214/DATA/C20650XX/C2065001_RAW.IMG",
        "VGISS_5214/DATA/C20660XX/C2066000_RAW.IMG",
        "VGISS_5214/DATA/C20671XX/C2067133_RAW.IMG",
        "VGISS_5214/DATA/C20691XX/C2069127_RAW.IMG",
        "VGISS_5214/DATA/C20708XX/C2070805_RAW.IMG",
        "VGISS_5214/DATA/C20856XX/C2085618_RAW.IMG",
        "VGISS_6101/DATA/C27830XX/C2783018_RAW.IMG",
        "VGISS_6101/DATA/C29297XX/C2929725_RAW.IMG",
        "VGISS_6101/DATA/C32146XX/C3214656_RAW.IMG",
        "VGISS_6101/DATA/C32499XX/C3249921_RAW.IMG",
        "VGISS_6101/DATA/C32500XX/C3250013_RAW.IMG",
        "VGISS_6101/DATA/C32600XX/C3260011_RAW.IMG",
        "VGISS_6101/DATA/C32700XX/C3270025_RAW.IMG",
        "VGISS_6102/DATA/C32800XX/C3280031_RAW.IMG",
        "VGISS_6102/DATA/C32900XX/C3290029_RAW.IMG",
        "VGISS_6103/DATA/C33000XX/C3300043_RAW.IMG",
        "VGISS_6103/DATA/C33100XX/C3310049_RAW.IMG",
        "VGISS_6104/DATA/C33200XX/C3320047_RAW.IMG",
        "VGISS_6104/DATA/C33301XX/C3330101_RAW.IMG",
        "VGISS_6104/DATA/C33401XX/C3340107_RAW.IMG",
        "VGISS_6105/DATA/C33501XX/C3350105_RAW.IMG",
        "VGISS_6105/DATA/C33601XX/C3360119_RAW.IMG",
        "VGISS_6105/DATA/C33701XX/C3370125_RAW.IMG",
        "VGISS_6106/DATA/C33801XX/C3380123_RAW.IMG",
        "VGISS_6106/DATA/C33901XX/C3390125_RAW.IMG",
        "VGISS_6106/DATA/C34000XX/C3400051_RAW.IMG",
        "VGISS_6107/DATA/C34100XX/C3410005_RAW.IMG",
        "VGISS_6107/DATA/C34201XX/C3420155_RAW.IMG",
        "VGISS_6107/DATA/C34300XX/C3430041_RAW.IMG",
        "VGISS_6108/DATA/C34400XX/C3440004_RAW.IMG",
        "VGISS_6109/DATA/C34500XX/C3450001_RAW.IMG",
        "VGISS_6110/DATA/C34600XX/C3460002_RAW.IMG",
        "VGISS_6111/DATA/C34700XX/C3470002_RAW.IMG",
        "VGISS_6112/DATA/C34800XX/C3480032_RAW.IMG",
        "VGISS_6113/DATA/C34900XX/C3490002_RAW.IMG",
        "VGISS_6114/DATA/C35000XX/C3500002_RAW.IMG",
        "VGISS_6115/DATA/C35100XX/C3510005_RAW.IMG",
        "VGISS_6116/DATA/C35200XX/C3520002_RAW.IMG",
        "VGISS_6116/DATA/C35300XX/C3530000_RAW.IMG",
        "VGISS_6117/DATA/C35409XX/C3540904_RAW.IMG",
        "VGISS_6118/DATA/C35500XX/C3550000_RAW.IMG",
        "VGISS_6119/DATA/C35600XX/C3560003_RAW.IMG",
        "VGISS_6120/DATA/C35708XX/C3570808_RAW.IMG",
        "VGISS_6121/DATA/C35800XX/C3580000_RAW.IMG",
        "VGISS_6121/DATA/C35900XX/C3590002_RAW.IMG",
        "VGISS_6201/DATA/C38333XX/C3833325_RAW.IMG",
        "VGISS_6201/DATA/C39402XX/C3940251_RAW.IMG",
        "VGISS_6201/DATA/C40707XX/C4070710_RAW.IMG",
        "VGISS_6201/DATA/C41561XX/C4156154_RAW.IMG",
        "VGISS_6201/DATA/C41600XX/C4160003_RAW.IMG",
        "VGISS_6202/DATA/C41700XX/C4170034_RAW.IMG",
        "VGISS_6202/DATA/C41801XX/C4180108_RAW.IMG",
        "VGISS_6202/DATA/C41901XX/C4190137_RAW.IMG",
        "VGISS_6203/DATA/C42000XX/C4200001_RAW.IMG",
        "VGISS_6203/DATA/C42100XX/C4210035_RAW.IMG",
        "VGISS_6203/DATA/C42201XX/C4220125_RAW.IMG",
        "VGISS_6204/DATA/C42302XX/C4230207_RAW.IMG",
        "VGISS_6204/DATA/C42400XX/C4240002_RAW.IMG",
        "VGISS_6204/DATA/C42500XX/C4250052_RAW.IMG",
        "VGISS_6205/DATA/C42601XX/C4260134_RAW.IMG",
        "VGISS_6205/DATA/C42702XX/C4270208_RAW.IMG",
        "VGISS_6205/DATA/C42800XX/C4280019_RAW.IMG",
        "VGISS_6206/DATA/C42901XX/C4290101_RAW.IMG",
        "VGISS_6206/DATA/C43001XX/C4300135_RAW.IMG",
        "VGISS_6206/DATA/C43100XX/C4310012_RAW.IMG",
        "VGISS_6207/DATA/C43200XX/C4320016_RAW.IMG",
        "VGISS_6207/DATA/C43300XX/C4330039_RAW.IMG",
        "VGISS_6208/DATA/C43401XX/C4340101_RAW.IMG",
        "VGISS_6209/DATA/C43500XX/C4350002_RAW.IMG",
        "VGISS_6210/DATA/C43600XX/C4360001_RAW.IMG",
        "VGISS_6211/DATA/C43701XX/C4370100_RAW.IMG",
        "VGISS_6212/DATA/C43800XX/C4380000_RAW.IMG",
        "VGISS_6213/DATA/C43900XX/C4390002_RAW.IMG",
        "VGISS_6214/DATA/C44000XX/C4400001_RAW.IMG",
        "VGISS_6214/DATA/C44100XX/C4410004_RAW.IMG",
        "VGISS_6215/DATA/C44200XX/C4420002_RAW.IMG",
        "VGISS_6215/DATA/C44300XX/C4430001_RAW.IMG",
        "VGISS_7201/DATA/C24476XX/C2447654_RAW.IMG",
        "VGISS_7201/DATA/C24500XX/C2450000_RAW.IMG",
        "VGISS_7201/DATA/C24608XX/C2460835_RAW.IMG",
        "VGISS_7201/DATA/C24730XX/C2473005_RAW.IMG",
        "VGISS_7201/DATA/C24818XX/C2481850_RAW.IMG",
        "VGISS_7201/DATA/C24967XX/C2496759_RAW.IMG",
        "VGISS_7202/DATA/C25027XX/C2502759_RAW.IMG",
        "VGISS_7202/DATA/C25105XX/C2510515_RAW.IMG",
        "VGISS_7202/DATA/C25207XX/C2520759_RAW.IMG",
        "VGISS_7202/DATA/C25311XX/C2531132_RAW.IMG",
        "VGISS_7202/DATA/C25625XX/C2562535_RAW.IMG",
        "VGISS_7202/DATA/C25705XX/C2570529_RAW.IMG",
        "VGISS_7202/DATA/C25807XX/C2580729_RAW.IMG",
        "VGISS_7202/DATA/C25947XX/C2594706_RAW.IMG",
        "VGISS_7203/DATA/C26002XX/C2600227_RAW.IMG",
        "VGISS_7203/DATA/C26126XX/C2612644_RAW.IMG",
        "VGISS_7203/DATA/C26217XX/C2621754_RAW.IMG",
        "VGISS_7204/DATA/C26302XX/C2630241_RAW.IMG",
        "VGISS_7204/DATA/C26419XX/C2641959_RAW.IMG",
        "VGISS_7204/DATA/C26507XX/C2650752_RAW.IMG",
        "VGISS_7205/DATA/C26602XX/C2660252_RAW.IMG",
        "VGISS_7205/DATA/C26700XX/C2670004_RAW.IMG",
        "VGISS_7206/DATA/C26800XX/C2680006_RAW.IMG",
        "VGISS_7206/DATA/C26900XX/C2690051_RAW.IMG",
        "VGISS_7207/DATA/C27000XX/C2700000_RAW.IMG",
        "VGISS_7207/DATA/C27114XX/C2711449_RAW.IMG",
        "VGISS_7207/DATA/C27220XX/C2722013_RAW.IMG",
        "VGISS_7207/DATA/C27538XX/C2753811_RAW.IMG",
        "VGISS_7207/DATA/C27627XX/C2762708_RAW.IMG",
        "VGISS_8201/DATA/C08966XX/C0896631_RAW.IMG",
        "VGISS_8201/DATA/C09002XX/C0900213_RAW.IMG",
        "VGISS_8201/DATA/C09100XX/C0910031_RAW.IMG",
        "VGISS_8201/DATA/C09207XX/C0920723_RAW.IMG",
        "VGISS_8201/DATA/C09301XX/C0930129_RAW.IMG",
        "VGISS_8201/DATA/C09400XX/C0940000_RAW.IMG",
        "VGISS_8202/DATA/C09505XX/C0950556_RAW.IMG",
        "VGISS_8202/DATA/C09600XX/C0960001_RAW.IMG",
        "VGISS_8202/DATA/C09703XX/C0970331_RAW.IMG",
        "VGISS_8202/DATA/C09810XX/C0981043_RAW.IMG",
        "VGISS_8202/DATA/C09900XX/C0990001_RAW.IMG",
        "VGISS_8203/DATA/C10002XX/C1000247_RAW.IMG",
        "VGISS_8203/DATA/C10105XX/C1010515_RAW.IMG",
        "VGISS_8203/DATA/C10200XX/C1020032_RAW.IMG",
        "VGISS_8203/DATA/C10302XX/C1030203_RAW.IMG",
        "VGISS_8204/DATA/C10404XX/C1040440_RAW.IMG",
        "VGISS_8204/DATA/C10500XX/C1050003_RAW.IMG",
        "VGISS_8204/DATA/C10601XX/C1060119_RAW.IMG",
        "VGISS_8204/DATA/C10700XX/C1070000_RAW.IMG",
        "VGISS_8205/DATA/C10826XX/C1082620_RAW.IMG",
        "VGISS_8205/DATA/C10902XX/C1090237_RAW.IMG",
        "VGISS_8206/DATA/C11000XX/C1100005_RAW.IMG",
        "VGISS_8206/DATA/C11106XX/C1110636_RAW.IMG",
        "VGISS_8207/DATA/C11200XX/C1120000_RAW.IMG",
        "VGISS_8207/DATA/C11300XX/C1130002_RAW.IMG",
        "VGISS_8208/DATA/C11400XX/C1140002_RAW.IMG",
        "VGISS_8208/DATA/C11500XX/C1150005_RAW.IMG",
        "VGISS_8209/DATA/C11600XX/C1160006_RAW.IMG",
        "VGISS_8209/DATA/C11700XX/C1170010_RAW.IMG",
        "VGISS_8209/DATA/C11800XX/C1180040_RAW.IMG",
        "VGISS_8209/DATA/C11922XX/C1192203_RAW.IMG",
        "VGISS_8210/DATA/C12009XX/C1200927_RAW.IMG",
        "VGISS_8210/DATA/C12128XX/C1212847_RAW.IMG",
        "VGISS_8210/DATA/C12219XX/C1221938_RAW.IMG",
        "VGISS_8210/DATA/C12329XX/C1232902_RAW.IMG",
        "VGISS_8210/DATA/C12400XX/C1240005_RAW.IMG",
    ]

    for filepath in TESTS:
        logical_path = 'volumes/VGISS_' + filepath[6] + 'xxx/' + filepath
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
                for viewable_pdsf in viewset.viewables:
                    assert viewable_pdsf.abspath in opus_id_abspaths

            # Every associated product is in the product set except metadata
            for category in ('volumes', 'calibrated', 'previews', 'diagrams'):
                for abspath in pdsf.associated_abspaths(category):
                    assert abspath in opus_id_abspaths

##########################################################################################
