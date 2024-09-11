##########################################################################################
# pds3file/rules/COVIMS_0xxx.py
##########################################################################################

import pdsfile.pds3file as pds3file
from pdsfile.pdsfile import abspath_for_logical_path
import translator
import re

##########################################################################################
# DESCRIPTION_AND_ICON
##########################################################################################

description_and_icon_by_regex = translator.TranslatorByRegex([
    (r'volumes/.*/data',                                         re.I, ('Data files grouped by date',  'CUBEDIR')),
    (r'volumes/.*/data/\w+',                                     re.I, ('Data files grouped by date',  'CUBEDIR')),
    (r'volumes/.*/data.*\.qub',                                  re.I, ('Spectral image cube (ISIS2)', 'CUBE')),
    (r'volumes/.*/extras',                                       re.I, ('Browse image collection',     'BROWDIR')),
    (r'volumes/.*/data/.*/extras/\w+',                           re.I, ('Browse image collection',     'BROWDIR')),
    (r'volumes/.*/data/.*/extras/.*\.(jpeg|jpeg_small|tiff)',    re.I, ('Browse image',                'BROWSE' )),
    (r'volumes/.*/software.*cube_prep/cube_prep',                re.I, ('Program binary',              'CODE'   )),
    (r'volumes/.*/software.*/PPVL_report',                       re.I, ('Program binary',              'CODE'   )),
    (r'.*/thumbnail(/\w+)*',                                     re.I, ('Small browse images',         'BROWDIR' )),
    (r'.*/thumbnail/.*\.(gif|jpg|jpeg|jpeg_small|tif|tiff|png)', re.I, ('Small browse image',          'BROWSE'  )),
    (r'.*/tiff(/\w+)*',                                          re.I, ('Full-size browse images',     'BROWDIR' )),
    (r'.*/tiff/.*\.(gif|jpg|jpeg|jpeg_small|tif|tiff|png)',      re.I, ('Full-size browse image',      'BROWSE'  )),

    (r'previews/COVIMS_0xxx/AAREADME.pdf', re.I, ('How to interpret VIMS preview images', 'INFO')),
])

##########################################################################################
# VIEWABLES
##########################################################################################

default_viewables = translator.TranslatorByRegex([
    (r'volumes/(.*/data/\w+/.*)\.(qub|lbl)', 0,
            [r'previews/\1_thumb.png',
             r'previews/\1_small.png',
             r'previews/\1_med.png',
             r'previews/\1_full.png',
            ]),
])

##########################################################################################
# ASSOCIATIONS
##########################################################################################

associations_to_volumes = translator.TranslatorByRegex([
    (r'.*/COVIMS_0xxx(|_v[0-9\.]+)/(COVIMS_....)/(data|extras/\w+)/(\w+/v[0-9]{10}_[0-9]+)(_0[0-6][0-9]|).*', 0,
            [r'volumes/COVIMS_0xxx\1/\2/data/\4\5.qub',
             r'volumes/COVIMS_0xxx\1/\2/data/\4\5.lbl',
             r'volumes/COVIMS_0xxx\1/\2/extras/thumbnail/\4\5.IMG.jpeg_small',
             r'volumes/COVIMS_0xxx\1/\2/extras/browse/\4\5.IMG.jpeg',
             r'volumes/COVIMS_0xxx\1/\2/extras/full/\4\5.IMG.png',
             r'volumes/COVIMS_0xxx\1/\2/extras/tiff/\4\5.IMG.tiff',
            ]),
    (r'.*/COVIMS_0xxx(|_v[0-9\.]+)/(COVIMS_....)/(data|extras/\w+)(|/\w+)', 0,
            [r'volumes/COVIMS_0xxx\1/\2/data\4',
             r'volumes/COVIMS_0xxx\1/\2/extras/thumbnail\4',
             r'volumes/COVIMS_0xxx\1/\2/extras/browse\4',
             r'volumes/COVIMS_0xxx\1/\2/extras/full\4',
             r'volumes/COVIMS_0xxx\1/\2/extras/tiff\4',
            ]),
    (r'.*/COVIMS_0xxx(|_v[0-9\.]+)/(COVIMS_....)/extras', 0,
            r'volumes/COVIMS_0xxx\1/\2/data'),
    (r'.*/COVIMS_0999.*', 0, r'volumes/COVIMS_0xxx'),
    (r'documents/COVIMS_0xxx.*', 0,
            r'volumes/COVIMS_0xxx'),
])

associations_to_previews = translator.TranslatorByRegex([
    (r'.*/COVIMS_0xxx(|_v[0-9\.]+)/(COVIMS_....)/(data|extras/\w+)/(\w+/v[0-9]{10}_[0-9]+)(_0[0-6][0-9]|).*', 0,
            [r'previews/COVIMS_0xxx/\2/data/\4\5_full.png',
             r'previews/COVIMS_0xxx/\2/data/\4\5_med.png',
             r'previews/COVIMS_0xxx/\2/data/\4\5_small.png',
             r'previews/COVIMS_0xxx/\2/data/\4\5_thumb.png',
            ]),
    (r'.*/COVIMS_0xxx(|_v[0-9\.]+)/(COVIMS_....)/(data|extras/\w+)(|/\w+)', 0,
            r'previews/COVIMS_0xxx/\2/data\3'),
    (r'.*/COVIMS_0xxx(|_v[0-9\.]+)/(COVIMS_....)/extras', 0,
            r'previews/COVIMS_0xxx/\2/data'),
    (r'.*/COVIMS_0999.*', 0, r'previews/COVIMS_0xxx'),
])

associations_to_metadata = translator.TranslatorByRegex([
    (r'volumes/COVIMS_0xxx(|_v[0-9\.]+)/(COVIMS_....)/(data|extras/\w+)/\w+/(v[0-9]{10}_[0-9]+)(_0[0-6][0-9]|).*', 0,
            [r'metadata/COVIMS_0xxx/\2/\2_index.tab/\4\5',
             r'metadata/COVIMS_0xxx/\2/\2_supplemental_index.tab/\4\5',
             r'metadata/COVIMS_0xxx/\2/\2_ring_summary.tab/\4\5',
             r'metadata/COVIMS_0xxx/\2/\2_moon_summary.tab/\4\5',
             r'metadata/COVIMS_0xxx/\2/\2_saturn_summary.tab/\4\5',
             r'metadata/COVIMS_0xxx/\2/\2_jupiter_summary.tab/\4\5',
            ]),
    (r'metadata/COVIMS_0xxx(|_v[0-9\.]+)/COVIMS_00..', 0,
            r'metadata/COVIMS_0xxx\1/COVIMS_0999'),
    (r'metadata/COVIMS_0xxx(|_v[0-9\.]+)/COVIMS_00../COVIMS_0..._(\w+)\.\w+', 0,
            [r'metadata/COVIMS_0xxx\1/COVIMS_0999/COVIMS_0999_\2.tab',
             r'metadata/COVIMS_0xxx\1/COVIMS_0999/COVIMS_0999_\2.csv',
             r'metadata/COVIMS_0xxx\1/COVIMS_0999/COVIMS_0999_\2.lbl',
            ]),
])

associations_to_documents = translator.TranslatorByRegex([
    (r'(volumes/COVIMS_0xxx.*/COVIMS_0...).*', 0,
            [r'volumes/\1/catalog',
             r'volumes/\1/aareadme.txt',
             r'volumes/\1/errata.txt',
             r'volumes/\1/voldesc.cat',
             r'volumes/\1/document/*',
            ]),

    (r'volumes/COVIMS_0xxx/COVIMS_0\d\d\d', 0,
            r'documents/COVIMS_0xxx/*'),
    (r'volumes/COVIMS_0xxx/COVIMS_0\d\d\d/.+', 0,
            r'documents/COVIMS_0xxx'),
    (r'previews/COVIMS_0xxx.*', 0,
            r'documents/COVIMS_0xxx/VIMS-Preview-Interpretation-Guide.pdf'),
])

##########################################################################################
# VIEW_OPTIONS (grid_view_allowed, multipage_view_allowed, continuous_view_allowed)
##########################################################################################

view_options = translator.TranslatorByRegex([
    (r'.*/COVIMS_0.../(data|extras/w+)(|/.*)', 0, (True, True, True)),
])

##########################################################################################
# NEIGHBORS
##########################################################################################

neighbors = translator.TranslatorByRegex([
    (r'(.*/COVIMS_0xxx.*)/(COVIMS_0...)/(data|extras/w+)/\w+', 0, r'\1/*/\3/*'),
    (r'(.*/COVIMS_0xxx.*)/(COVIMS_0...)/(data|extras/w+)',     0, r'\1/*/\3'),
])

##########################################################################################
# OPUS_TYPE
##########################################################################################

opus_type = translator.TranslatorByRegex([
    (r'volumes/.*\.(qub|lbl)',                      0, ('Cassini VIMS',   0, 'covims_raw',    'Raw Cube',                  True)),
    (r'volumes/.*/extras/thumbnail/.*\.jpeg_small', 0, ('Cassini VIMS', 110, 'covims_thumb',  'Extra Preview (thumbnail)', False)),
    (r'volumes/.*/extras/browse/.*\.jpeg',          0, ('Cassini VIMS', 120, 'covims_medium', 'Extra Preview (medium)',    False)),
    (r'volumes/.*/extras/(tiff|full)/.*\.\w+',      0, ('Cassini VIMS', 130, 'covims_full',   'Extra Preview (full)',      False)),
    # Documentation
    (r'documents/COVIMS_0xxx/.*',                   0, ('Cassini VIMS', 140, 'covims_documentation', 'Documentation', False)),
])

##########################################################################################
# OPUS_FORMAT
##########################################################################################

opus_format = translator.TranslatorByRegex([
    (r'.*\.qub',        0, ('Binary', 'ISIS2')),
    (r'.*\.jpeg_small', 0, ('Binary', 'JPEG')),
])

##########################################################################################
# OPUS_PRODUCTS
##########################################################################################

opus_products = translator.TranslatorByRegex([
    (r'.*/COVIMS_0xxx(|_v[0-9\.]+)/(COVIMS_0...)/(data|extras/\w+)/(\w+/v[0-9]{10}_[0-9]+)(_0[0-6][0-9]|)\..*', 0,
            [r'volumes/COVIMS_0xxx*/\2/data/\4\5.qub',
             r'volumes/COVIMS_0xxx*/\2/data/\4\5.lbl',
             r'volumes/COVIMS_0xxx*/\2/extras/thumbnail/\4\5.qub.jpeg_small',
             r'volumes/COVIMS_0xxx*/\2/extras/browse/\4\5.qub.jpeg',
             r'volumes/COVIMS_0xxx*/\2/extras/full/\4\5.qub.png',
             r'volumes/COVIMS_0xxx*/\2/extras/tiff/\4\5.qub.tiff',
             r'previews/COVIMS_0xxx/\2/data/\4\5_full.png',
             r'previews/COVIMS_0xxx/\2/data/\4\5_med.png',
             r'previews/COVIMS_0xxx/\2/data/\4\5_small.png',
             r'previews/COVIMS_0xxx/\2/data/\4\5_thumb.png',
             r'metadata/COVIMS_0xxx/\2/\2_moon_summary.tab',
             r'metadata/COVIMS_0xxx/\2/\2_moon_summary.lbl',
             r'metadata/COVIMS_0xxx/\2/\2_ring_summary.tab',
             r'metadata/COVIMS_0xxx/\2/\2_ring_summary.lbl',
             r'metadata/COVIMS_0xxx/\2/\2_saturn_summary.tab',
             r'metadata/COVIMS_0xxx/\2/\2_saturn_summary.lbl',
             r'metadata/COVIMS_0xxx/\2/\2_jupiter_summary.tab',
             r'metadata/COVIMS_0xxx/\2/\2_jupiter_summary.lbl',
             r'metadata/COVIMS_0xxx/\2/\2_inventory.csv',
             r'metadata/COVIMS_0xxx/\2/\2_inventory.lbl',
             r'metadata/COVIMS_0xxx/\2/\2_index.tab',
             r'metadata/COVIMS_0xxx/\2/\2_index.lbl',
             r'metadata/COVIMS_0xxx/\2/\2_supplemental_index.tab',
             r'metadata/COVIMS_0xxx/\2/\2_supplemental_index.lbl',
            ]),
])

##########################################################################################
# OPUS_ID
##########################################################################################

opus_id = translator.TranslatorByRegex([
    # There are up to two OPUS IDs associated with each VIMS file, one for the VIS channel and one for the IR channel.
    # This translator returns the OPUS ID without the suffix "_IR" or "_VIS" used by OPUS. That must be handled separately
    (r'.*/COVIMS_0xxx.*/(v[0-9]{10})_[0-9]+(|_[0-9]{3})\..*', 0, r'co-vims-\1\2'),
])

##########################################################################################
# OPUS_ID_TO_PRIMARY_LOGICAL_PATH
##########################################################################################

# By identifying the first three digits of the spacecraft clock with a range of volumes, we speed things up quite a bit
opus_id_to_primary_logical_path = translator.TranslatorByRegex([
    (r'co-vims-(v188.{7})(|_.{3})',     0,  r'volumes/COVIMS_0xxx/COVIMS_009[3-4]/data/*/\1_*\2.qub'),
    (r'co-vims-(v187.{7})(|_.{3})',     0,  r'volumes/COVIMS_0xxx/COVIMS_009[0-3]/data/*/\1_*\2.qub'),
    (r'co-vims-(v186.{7})(|_.{3})',     0, [r'volumes/COVIMS_0xxx/COVIMS_008[5-9]/data/*/\1_*\2.qub',
                                            r'volumes/COVIMS_0xxx/COVIMS_0090/data/*/\1_*\2.qub']),
    (r'co-vims-(v185.{7})(|_.{3})',     0,  r'volumes/COVIMS_0xxx/COVIMS_008[1-5]/data/*/\1_*\2.qub'),
    (r'co-vims-(v184.{7})(|_.{3})',     0, [r'volumes/COVIMS_0xxx/COVIMS_0079/data/*/\1_*\2.qub',
                                            r'volumes/COVIMS_0xxx/COVIMS_008[0-1]/data/*/\1_*\2.qub']),
    (r'co-vims-(v183.{7})(|_.{3})',     0,  r'volumes/COVIMS_0xxx/COVIMS_007[7-9]/data/*/\1_*\2.qub'),
    (r'co-vims-(v182.{7})(|_.{3})',     0,  r'volumes/COVIMS_0xxx/COVIMS_007[6-7]/data/*/\1_*\2.qub'),
    (r'co-vims-(v181.{7})(|_.{3})',     0,  r'volumes/COVIMS_0xxx/COVIMS_007[4-6]/data/*/\1_*\2.qub'),
    (r'co-vims-(v180.{7})(|_.{3})',     0,  r'volumes/COVIMS_0xxx/COVIMS_007[2-4]/data/*/\1_*\2.qub'),
    (r'co-vims-(v179.{7})(|_.{3})',     0,  r'volumes/COVIMS_0xxx/COVIMS_007[0-2]/data/*/\1_*\2.qub'),
    (r'co-vims-(v178.{7})(|_.{3})',     0, [r'volumes/COVIMS_0xxx/COVIMS_006[7-9]/data/*/\1_*\2.qub',
                                            r'volumes/COVIMS_0xxx/COVIMS_0070/data/*/\1_*\2.qub']),
    (r'co-vims-(v177.{7})(|_.{3})',     0,  r'volumes/COVIMS_0xxx/COVIMS_006[5-7]/data/*/\1_*\2.qub'),
    (r'co-vims-(v176.{7})(|_.{3})',     0,  r'volumes/COVIMS_0xxx/COVIMS_006[3-5]/data/*/\1_*\2.qub'),
    (r'co-vims-(v175.{7})(|_.{3})',     0,  r'volumes/COVIMS_0xxx/COVIMS_006[0-3]/data/*/\1_*\2.qub'),
    (r'co-vims-(v174.{7})(|_.{3})',     0, [r'volumes/COVIMS_0xxx/COVIMS_005[7-9]/data/*/\1_*\2.qub',
                                            r'volumes/COVIMS_0xxx/COVIMS_0060/data/*/\1_*\2.qub']),
    (r'co-vims-(v173.{7})(|_.{3})',     0,  r'volumes/COVIMS_0xxx/COVIMS_005[4-7]/data/*/\1_*\2.qub'),
    (r'co-vims-(v172.{7})(|_.{3})',     0,  r'volumes/COVIMS_0xxx/COVIMS_005[3-4]/data/*/\1_*\2.qub'),
    (r'co-vims-(v171.{7})(|_.{3})',     0,  r'volumes/COVIMS_0xxx/COVIMS_005[1-3]/data/*/\1_*\2.qub'),
    (r'co-vims-(v170.{7})(|_.{3})',     0,  r'volumes/COVIMS_0xxx/COVIMS_005[0-1]/data/*/\1_*\2.qub'),
    (r'co-vims-(v169.{7})(|_.{3})',     0, [r'volumes/COVIMS_0xxx/COVIMS_004[8-9]/data/*/\1_*\2.qub',
                                            r'volumes/COVIMS_0xxx/COVIMS_0050/data/*/\1_*\2.qub']),
    (r'co-vims-(v168.{7})(|_.{3})',     0,  r'volumes/COVIMS_0xxx/COVIMS_004[6-8]/data/*/\1_*\2.qub'),
    (r'co-vims-(v167.{7})(|_.{3})',     0,  r'volumes/COVIMS_0xxx/COVIMS_004[4-6]/data/*/\1_*\2.qub'),
    (r'co-vims-(v166.{7})(|_.{3})',     0,  r'volumes/COVIMS_0xxx/COVIMS_004[3-4]/data/*/\1_*\2.qub'),
    (r'co-vims-(v165.{7})(|_.{3})',     0,  r'volumes/COVIMS_0xxx/COVIMS_004[2-3]/data/*/\1_*\2.qub'),
    (r'co-vims-(v164.{7})(|_.{3})',     0,  r'volumes/COVIMS_0xxx/COVIMS_004[0-2]/data/*/\1_*\2.qub'),
    (r'co-vims-(v163.{7})(|_.{3})',     0, [r'volumes/COVIMS_0xxx/COVIMS_003[7-9]/data/*/\1_*\2.qub',
                                            r'volumes/COVIMS_0xxx/COVIMS_0040/data/*/\1_*\2.qub']),
    (r'co-vims-(v162.{7})(|_.{3})',     0,  r'volumes/COVIMS_0xxx/COVIMS_003[6-7]/data/*/\1_*\2.qub'),
    (r'co-vims-(v161.{7})(|_.{3})',     0,  r'volumes/COVIMS_0xxx/COVIMS_003[3-6]/data/*/\1_*\2.qub'),
    (r'co-vims-(v160.{7})(|_.{3})',     0,  r'volumes/COVIMS_0xxx/COVIMS_003[0-3]/data/*/\1_*\2.qub'),
    (r'co-vims-(v159.{7})(|_.{3})',     0, [r'volumes/COVIMS_0xxx/COVIMS_002[7-9]/data/*/\1_*\2.qub',
                                            r'volumes/COVIMS_0xxx/COVIMS_0030/data/*/\1_*\2.qub']),
    (r'co-vims-(v158.{7})(|_.{3})',     0,  r'volumes/COVIMS_0xxx/COVIMS_002[4-7]/data/*/\1_*\2.qub'),
    (r'co-vims-(v157.{7})(|_.{3})',     0,  r'volumes/COVIMS_0xxx/COVIMS_002[3-4]/data/*/\1_*\2.qub'),
    (r'co-vims-(v156.{7})(|_.{3})',     0,  r'volumes/COVIMS_0xxx/COVIMS_002[0-3]/data/*/\1_*\2.qub'),
    (r'co-vims-(v155.{7})(|_.{3})',     0, [r'volumes/COVIMS_0xxx/COVIMS_001[6-9]/data/*/\1_*\2.qub',
                                            r'volumes/COVIMS_0xxx/COVIMS_0020/data/*/\1_*\2.qub']),
    (r'co-vims-(v154.{7})(|_.{3})',     0,  r'volumes/COVIMS_0xxx/COVIMS_001[4-6]/data/*/\1_*\2.qub'),
    (r'co-vims-(v153.{7})(|_.{3})',     0,  r'volumes/COVIMS_0xxx/COVIMS_001[2-4]/data/*/\1_*\2.qub'),
    (r'co-vims-(v152.{7})(|_.{3})',     0,  r'volumes/COVIMS_0xxx/COVIMS_001[1-2]/data/*/\1_*\2.qub'),
    (r'co-vims-(v151.{7})(|_.{3})',     0, [r'volumes/COVIMS_0xxx/COVIMS_0009/data/*/\1_*\2.qub',
                                            r'volumes/COVIMS_0xxx/COVIMS_001[0-1]/data/*/\1_*\2.qub']),
    (r'co-vims-(v150.{7})(|_.{3})',     0,  r'volumes/COVIMS_0xxx/COVIMS_000[8-9]/data/*/\1_*\2.qub'),
    (r'co-vims-(v149.{7})(|_.{3})',     0,  r'volumes/COVIMS_0xxx/COVIMS_000[6-8]/data/*/\1_*\2.qub'),
    (r'co-vims-(v148.{7})(|_.{3})',     0,  r'volumes/COVIMS_0xxx/COVIMS_000[5-6]/data/*/\1_*\2.qub'),
    (r'co-vims-(v147.{7})(|_.{3})',     0,  r'volumes/COVIMS_0xxx/COVIMS_000[4-5]/data/*/\1_*\2.qub'),
    (r'co-vims-(v146.{7})(|_.{3})',     0,  r'volumes/COVIMS_0xxx/COVIMS_000[3-4]/data/*/\1_*\2.qub'),
    (r'co-vims-(v14[0-6].{7})(|_.{3})', 0,  r'volumes/COVIMS_0xxx/COVIMS_0003/data/*/\1_*\2.qub'),
    (r'co-vims-(v13[7-9].{7})(|_.{3})', 0,  r'volumes/COVIMS_0xxx/COVIMS_0003/data/*/\1_*\2.qub'),
    (r'co-vims-(v136.{7})(|_.{3})',     0,  r'volumes/COVIMS_0xxx/COVIMS_000[2-3]/data/*/\1_*\2.qub'),
    (r'co-vims-(v135.{7})(|_.{3})',     0,  r'volumes/COVIMS_0xxx/COVIMS_0002/data/*/\1_*\2.qub'),
    (r'co-vims-(v13[0-4].{7})(|_.{3})', 0,  r'volumes/COVIMS_0xxx/COVIMS_0001/data/*/\1_*\2.qub'),
    (r'co-vims-(v12..{7})(|_.{3})',     0,  r'volumes/COVIMS_0xxx/COVIMS_0001/data/*/\1_*\2.qub'),
])

##########################################################################################
# Subclass definition
##########################################################################################

BASENAME_REGEX = re.compile(r'(v?\d{10}_\d+)(_0[0-6][0-9]|).*')

class COVIMS_0xxx(pds3file.Pds3File):

    pds3file.Pds3File.VOLSET_TRANSLATOR = translator.TranslatorByRegex([('COVIMS_0xxx', re.I, 'COVIMS_0xxx')]) + \
                                          pds3file.Pds3File.VOLSET_TRANSLATOR

    DESCRIPTION_AND_ICON = description_and_icon_by_regex + pds3file.Pds3File.DESCRIPTION_AND_ICON
    VIEW_OPTIONS = view_options + pds3file.Pds3File.VIEW_OPTIONS
    NEIGHBORS = neighbors + pds3file.Pds3File.NEIGHBORS

    OPUS_TYPE = opus_type + pds3file.Pds3File.OPUS_TYPE
    OPUS_FORMAT = opus_format + pds3file.Pds3File.OPUS_FORMAT
    OPUS_PRODUCTS = opus_products + pds3file.Pds3File.OPUS_PRODUCTS
    OPUS_ID = opus_id
    OPUS_ID_TO_PRIMARY_LOGICAL_PATH = opus_id_to_primary_logical_path

    VIEWABLES = {'default': default_viewables}

    ASSOCIATIONS = pds3file.Pds3File.ASSOCIATIONS.copy()
    ASSOCIATIONS['volumes']   += associations_to_volumes
    ASSOCIATIONS['previews']  += associations_to_previews
    ASSOCIATIONS['metadata']  += associations_to_metadata
    ASSOCIATIONS['documents']  = associations_to_documents  # override, not addition, so "=" instead of "+="

    # This dictionary identifies every known case where the latest version of a VIMS cube is not identified by the
    # highest version number as embedded in the file name.
    LOWER_VERSION_PRIORITIZED = {
        'co-vims-v1465673806': 'volumes/COVIMS_0xxx/COVIMS_0004/data/2004163T121836_2004163T192848/v1465673806_2.qub',
        'co-vims-v1465680977': 'volumes/COVIMS_0xxx/COVIMS_0004/data/2004163T193015_2004164T051726/v1465680977_2.qub',
        'co-vims-v1465700253': 'volumes/COVIMS_0xxx/COVIMS_0004/data/2004163T193015_2004164T051726/v1465700253_2.qub',
        'co-vims-v1465711602': 'volumes/COVIMS_0xxx/COVIMS_0004/data/2004164T052125_2004164T083916/v1465711602_2.qub',
        'co-vims-v1471676803': 'volumes/COVIMS_0xxx/COVIMS_0004/data/2004231T031136_2004234T061028/v1471676803_2.qub',
        'co-vims-v1472712701': 'volumes/COVIMS_0xxx/COVIMS_0004/data/2004245T053141_2004248T081652/v1472712701_2.qub',
        'co-vims-v1472969272': 'volumes/COVIMS_0xxx/COVIMS_0004/data/2004245T053141_2004248T081652/v1472969272_4.qub',
        'co-vims-v1473199707': 'volumes/COVIMS_0xxx/COVIMS_0004/data/2004248T084723_2004253T183438/v1473199707_2.qub',
        'co-vims-v1475048593': 'volumes/COVIMS_0xxx/COVIMS_0004/data/2004269T215117_2004272T074311/v1475048593_2.qub',
        'co-vims-v1476574898': 'volumes/COVIMS_0xxx/COVIMS_0005/data/2004289T225942_2004292T210316/v1476574898_2.qub',
        'co-vims-v1476944152': 'volumes/COVIMS_0xxx/COVIMS_0005/data/2004292T210337_2004299T222753/v1476944152_4.qub',
        'co-vims-v1477473027': 'volumes/COVIMS_0xxx/COVIMS_0005/data/2004299T222946_2004300T120625/v1477473027_4.qub',
        'co-vims-v1480707723': 'volumes/COVIMS_0xxx/COVIMS_0005/data/2004327T224335_2004338T170407/v1480707723_2.qub',
        'co-vims-v1484867611': 'volumes/COVIMS_0xxx/COVIMS_0006/data/2005019T212432_2005030T082313/v1484867611_2.qub',
        'co-vims-v1487124681': 'volumes/COVIMS_0xxx/COVIMS_0006/data/2005046T014253_2005048T011257/v1487124681_2.qub',
        'co-vims-v1487124708': 'volumes/COVIMS_0xxx/COVIMS_0006/data/2005046T014253_2005048T011257/v1487124708_2.qub',
        'co-vims-v1487124942': 'volumes/COVIMS_0xxx/COVIMS_0006/data/2005046T014253_2005048T011257/v1487124942_2.qub',
        'co-vims-v1487124969': 'volumes/COVIMS_0xxx/COVIMS_0006/data/2005046T014253_2005048T011257/v1487124969_2.qub',
        'co-vims-v1489039632': 'volumes/COVIMS_0xxx/COVIMS_0006/data/2005067T113241_2005068T054421/v1489039632_2.qub',
        'co-vims-v1489040393': 'volumes/COVIMS_0xxx/COVIMS_0006/data/2005068T055549_2005072T012910/v1489040393_2.qub',
        'co-vims-v1489040893': 'volumes/COVIMS_0xxx/COVIMS_0006/data/2005068T055549_2005072T012910/v1489040893_2.qub',
        'co-vims-v1489041542': 'volumes/COVIMS_0xxx/COVIMS_0006/data/2005068T055549_2005072T012910/v1489041542_2.qub',
    }

    def OPUS_ID_TO_PRIMARY_LOGICAL_PATH(opus_id):

        # Check list of known exceptions first
        if opus_id in COVIMS_0xxx.LOWER_VERSION_PRIORITIZED:
            return pds3file.Pds3File.from_logical_path(COVIMS_0xxx.LOWER_VERSION_PRIORITIZED[opus_id])

        # Search using patterns
        paths = opus_id_to_primary_logical_path.all(opus_id)
        patterns = [abspath_for_logical_path(p, pds3file.Pds3File) for p in paths]
        matches = []
        for pattern in patterns:
            abspaths = pds3file.Pds3File.glob_glob(pattern, force_case_sensitive=True)
            matches += abspaths

        if len(matches) == 1:
            return pds3file.Pds3File.from_abspath(matches[0])

        if len(matches) == 0:
            raise ValueError('Unrecognized OPUS ID: ' + opus_id)

        # At this point, we have multiple matches. The one with the highest
        # version number should be returned. Note: There is no case where this
        # involves a two-digit version number, so we can use alphabetic sort.
        version_tuples = [(os.path.basename(p)[11:], p) for p in matches]
        version_tuples.sort()
        return pds3file.Pds3File.from_abspath(version_tuples[-1][1])

    def FILENAME_KEYLEN(self):
        match = BASENAME_REGEX.match(self.basename)
        if match:
            return len(match.group(1) + match.group(2))
        else:
            return 0

# Global attribute shared by all subclasses
pds3file.Pds3File.OPUS_ID_TO_SUBCLASS = translator.TranslatorByRegex([(r'co-vims-v.*', 0, COVIMS_0xxx)]) + \
                                        pds3file.Pds3File.OPUS_ID_TO_SUBCLASS

##########################################################################################
# Update the global dictionary of subclasses
##########################################################################################

pds3file.Pds3File.SUBCLASSES['COVIMS_0xxx'] = COVIMS_0xxx

##########################################################################################
# Unit tests
##########################################################################################

import pytest
from .pytest_support import *

@pytest.mark.parametrize(
    'input_path,expected',
    [
        ('volumes/COVIMS_0xxx/COVIMS_0006/data/2005088T102825_2005089T113931/v1490784910_3_001.qub',
         'COVIMS_0xxx/opus_products/v1490784910_3_001.txt')
    ]
)
def test_opus_products(request, input_path, expected):
    update = request.config.option.update
    opus_products_test(pds3file.Pds3File, input_path, TEST_RESULTS_DIR+expected, update)

@pytest.mark.parametrize(
    'input_path,category,expected',
    [
        ('volumes/COVIMS_0xxx/COVIMS_0006/data/2005088T102825_2005089T113931/v1490784910_3_001.qub',
         'volumes',
         'COVIMS_0xxx/associated_abspaths/volumes_v1490784910_3_001.txt')
    ]
)
def test_associated_abspaths(request, input_path, category, expected):
    update = request.config.option.update
    associated_abspaths_test(pds3file.Pds3File, input_path, category,
                             TEST_RESULTS_DIR+expected, update)

def test_opus_id_to_primary_logical_path():
    TESTS = [
        'COVIMS_0001/data/1999010T054026_1999010T060958/v1294638283_1.qub',
        'COVIMS_0001/data/1999017T031657_1999175T202056/v1308946681_1_001.qub',
        'COVIMS_0001/data/1999175T204004_1999230T014404/v1313631515_1_001.qub',
        'COVIMS_0001/data/1999230T021631_2000023T053859/v1327288143_1.qub',
        'COVIMS_0001/data/2000023T074222_2000175T201615/v1340482831_1_001.qub',
        'COVIMS_0002/data/2000320T054726_2000335T045651/v1352959095_3.qub',
        'COVIMS_0002/data/2001030T230448_2001037T103722/v1360147218_3.qub',
        'COVIMS_0003/data/1866163T033548_2002199T111000/v1405678932_5.qub',
        'COVIMS_0003/data/2001085T030039_2001085T035224/v1364267566_1.qub',
        'COVIMS_0003/data/2001087T092149_2001190T072621/v1373331221_1.qub',
        'COVIMS_0003/data/2001267T031111_2001267T070150/v1380001298_2.qub',
        'COVIMS_0003/data/2001312T032628_2002065T102753/v1391084505_1.qub',
        'COVIMS_0003/data/2002129T115022_2002193T092850/v1401904022_1.qub',
        'COVIMS_0003/data/2002193T173148_2002199T004210/v1405644685_3.qub',
        'COVIMS_0003/data/2002200T092607_2002279T022541/v1412536217_2.qub',
        'COVIMS_0003/data/2002338T155324_2003019T161332/v1421685141_1.qub',
        'COVIMS_0003/data/2003022T173242_2003139T090228/v1431917388_2.qub',
        'COVIMS_0003/data/2003202T042436_2003275T202430/v1443815207_1.qub',
        'COVIMS_0003/data/2003286T040831_2003289T114350/v1444713101_5.qub',
        'COVIMS_0003/data/2003335T063812_2003357T133033/v1450798321_2.qub',
        'COVIMS_0003/data/2004098T025941_2004114T021144/v1460006708_1.qub',
        'COVIMS_0004/data/2004136T030633_2004143T032556/v1463282505_1.qub',
        'COVIMS_0004/data/2004163T121836_2004163T192848/v1465673806_2.qub',
        'COVIMS_0004/data/2004163T193015_2004164T051726/v1465680977_2.qub',
        'COVIMS_0004/data/2004163T193015_2004164T051726/v1465700253_2.qub',
        'COVIMS_0004/data/2004164T052125_2004164T083916/v1465711602_2.qub',
        'COVIMS_0004/data/2004183T034717_2004183T035139/v1467346477_5_001.qub',
        'COVIMS_0004/data/2004183T040527_2004183T050825/v1467347131_4_042.qub',
        'COVIMS_0004/data/2004195T003217_2004220T203542/v1470506141_1.qub',
        'COVIMS_0004/data/2004231T031136_2004234T061028/v1471676803_2.qub',
        'COVIMS_0004/data/2004269T215117_2004272T074311/v1475048593_2.qub',
        'COVIMS_0005/data/2004275T010152_2004286T140923/v1475284725_1.qub',
        'COVIMS_0005/data/2004289T225942_2004292T210316/v1476574898_2.qub',
        'COVIMS_0005/data/2004327T224335_2004338T170407/v1480504396_1.qub',
        'COVIMS_0005/data/2004327T224335_2004338T170407/v1480707723_2.qub',
        'COVIMS_0006/data/2005015T175855_2005016T184233/v1484504505_4.qub',
        'COVIMS_0006/data/2005019T212432_2005030T082313/v1484867611_2.qub',
        'COVIMS_0006/data/2005068T055549_2005072T012910/v1489041542_2.qub',
        'COVIMS_0006/data/2005073T153624_2005087T174046/v1490680282_1.qub',
        'COVIMS_0006/data/2005088T102825_2005089T113931/v1490874598_3_001.qub',
        'COVIMS_0007/data/2005091T004738_2005098T084407/v1491009137_1.qub',
        'COVIMS_0007/data/2005104T174325_2005105T121223/v1492259003_2_001.qub',
        'COVIMS_0008/data/2005184T012146_2005194T140514/v1499045873_1.qub',
        'COVIMS_0008/data/2005194T141802_2005195T161541/v1500000259_1.qub',
        'COVIMS_0009/data/2005274T004918_2005278T015117/v1506820469_5.qub',
        'COVIMS_0009/data/2005307T010213_2005313T062943/v1510202713_1.qub',
        'COVIMS_0010/data/2006002T160435_2006011T064942/v1514910706_1.qub',
        'COVIMS_0011/data/2006041T122109_2006047T043108/v1518266879_1.qub',
        'COVIMS_0011/data/2006060T165030_2006062T051757/v1520052725_1.qub',
        'COVIMS_0012/data/2006099T144331_2006100T162855/v1523286537_1.qub',
        'COVIMS_0012/data/2006146T044321_2006177T032842/v1530000038_1.qub',
        'COVIMS_0013/data/2006182T012833_2006183T102730/v1530409854_1.qub',
        'COVIMS_0013/data/2006182T012833_2006183T102730/v1530490964_1.qub',
        'COVIMS_0014/data/2006280T203008_2006283T032145/v1538944737_1.qub',
        'COVIMS_0014/data/2006289T054324_2006296T202704/v1540001223_1.qub',
        'COVIMS_0015/data/2006321T002530_2006322T030737/v1542414882_1.qub',
        'COVIMS_0016/data/2007001T143956_2007001T184503/v1546355125_1.qub',
        'COVIMS_0016/data/2007042T164050_2007044T183005/v1550080651_1.qub',
        'COVIMS_0017/data/2007046T003311_2007046T122239/v1550192765_1.qub',
        'COVIMS_0018/data/2007069T001105_2007069T012348/v1552178188_1.qub',
        'COVIMS_0019/data/2007095T090701_2007096T081106/v1554455503_1.qub',
        'COVIMS_0020/data/2007137T054828_2007143T180509/v1558072759_1.qub',
        'COVIMS_0020/data/2007151T081546_2007160T094526/v1560055852_1.qub',
        'COVIMS_0021/data/2007182T034749_2007183T054005/v1561952683_1.qub',
        'COVIMS_0022/data/2007221T042753_2007222T110748/v1565326865_1.qub',
        'COVIMS_0023/data/2007274T195428_2007274T214716/v1569961087_1.qub',
        'COVIMS_0023/data/2007274T215310_2007275T123152/v1570012317_1.qub',
        'COVIMS_0024/data/2008001T001001_2008001T190718/v1577839173_1.qub',
        'COVIMS_0024/data/2008024T014444_2008027T193319/v1580127366_1.qub',
        'COVIMS_0025/data/2008074T063911_2008074T094636/v1584170140_1.qub',
        'COVIMS_0026/data/2008092T020043_2008092T150138/v1585708643_1.qub',
        'COVIMS_0027/data/2008126T072735_2008126T191436/v1588665206_1.qub',
        'COVIMS_0027/data/2008140T183045_2008143T172435/v1590000036_1.qub',
        'COVIMS_0028/data/2008150T001534_2008151T101955/v1590713040_1.qub',
        'COVIMS_0029/data/2008184T000411_2008184T030735/v1593650507_1.qub',
        'COVIMS_0030/data/2008216T113326_2008216T151449/v1596456682_1.qub',
        'COVIMS_0030/data/2008254T153950_2008259T035939/v1600139887_1.qub',
        'COVIMS_0031/data/2008275T003409_2008276T180353/v1601513398_1.qub',
        'COVIMS_0032/data/2008324T153928_2008324T154003/v1605802708_1_001.qub',
        'COVIMS_0033/data/2009001T000538_2009001T130114/v1609461638_1.qub',
        'COVIMS_0033/data/2009006T232902_2009009T231917/v1610054059_1.qub',
        'COVIMS_0034/data/2009024T075632_2009025T144924/v1611476358_1.qub',
        'COVIMS_0035/data/2009077T062645_2009077T110116/v1616051220_1.qub',
        'COVIMS_0036/data/2009093T105303_2009093T120526/v1617449566_1.qub',
        'COVIMS_0036/data/2009120T033211_2009125T101210/v1620205127_1.qub',
        'COVIMS_0037/data/2009183T132220_2009183T134208/v1625234636_1.qub',
        'COVIMS_0037/data/2009238T092600_2009239T084035/v1630035241_1.qub',
        'COVIMS_0038/data/2009249T070528_2009252T065256/v1630912046_17.qub',
        'COVIMS_0039/data/2009278T050728_2009282T225157/v1633412144_1.qub',
        'COVIMS_0040/data/2009339T163148_2009341T041919/v1638723713_1.qub',
        'COVIMS_0040/data/2009347T113128_2009357T002508/v1640221262_1.qub',
        'COVIMS_0041/data/2010001T144918_2010004T125922/v1641049788_1.qub',
        'COVIMS_0042/data/2010091T005626_2010095T112834/v1648776217_1.qub',
        'COVIMS_0042/data/2010099T132612_2010119T030718/v1650854868_1.qub',
        'COVIMS_0043/data/2010185T044821_2010186T001008/v1656912111_1.qub',
        'COVIMS_0043/data/2010206T213412_2010225T111352/v1660274652_1.qub',
        'COVIMS_0044/data/2010286T053632_2010288T064207/v1665639833_1.qub',
        'COVIMS_0044/data/2010335T002527_2010346T153302/v1670271625_1.qub',
        'COVIMS_0045/data/2011009T100552_2011010T215755/v1673261204_1.qub',
        'COVIMS_0046/data/2011074T134648_2011075T063308/v1678890279_1.qub',
        'COVIMS_0046/data/2011080T100255_2011090T234527/v1680115402_1.qub',
        'COVIMS_0047/data/2011091T000124_2011091T010351/v1680310140_1_001.qub',
        'COVIMS_0048/data/2011184T130731_2011190T200651/v1688392537_1.qub',
        'COVIMS_0048/data/2011193T193648_2011204T060808/v1690095410_1_001.qub',
        'COVIMS_0049/data/2011257T025518_2011259T220026/v1694663063_1.qub',
        'COVIMS_0050/data/2011274T000255_2011274T012424/v1696121510_1.qub',
        'COVIMS_0050/data/2011312T113325_2011330T125929/v1700712018_1.qub',
        'COVIMS_0051/data/2012001T010435_2012001T045908/v1704073944_3.qub',
        'COVIMS_0051/data/2012055T084704_2012070T082251/v1710055594_1.qub',
        'COVIMS_0052/data/2012093T010453_2012103T202435/v1712022868_1.qub',
        'COVIMS_0053/data/2012183T073512_2012186T122755/v1719818119_1.qub',
        'COVIMS_0053/data/2012183T073512_2012186T122755/v1720012643_3.qub',
        'COVIMS_0054/data/2012275T120155_2012287T000537/v1727787247_1.qub',
        'COVIMS_0054/data/2012293T080608_2012314T232821/v1730389121_1.qub',
        'COVIMS_0055/data/2012343T045102_2012344T065239/v1733636297_1.qub',
        'COVIMS_0056/data/2013003T130212_2013004T041759/v1735908241_1.qub',
        'COVIMS_0057/data/2013046T094020_2013046T111615/v1739615660_1.qub',
        'COVIMS_0057/data/2013048T174358_2013051T072740/v1740007627_1.qub',
        'COVIMS_0058/data/2013091T021022_2013091T051345/v1743476686_1.qub',
        'COVIMS_0059/data/2013118T175341_2013120T171012/v1745866100_1.qub',
        'COVIMS_0060/data/2013156T065432_2013156T172031/v1749109405_1.qub',
        'COVIMS_0060/data/2013165T150203_2013166T223046/v1750004131_1.qub',
        'COVIMS_0061/data/2013183T023443_2013184T171740/v1751426920_1.qub',
        'COVIMS_0062/data/2013217T114022_2013218T122144/v1754396859_1.qub',
        'COVIMS_0063/data/2013278T073410_2013281T155223/v1759652590_1.qub',
        'COVIMS_0063/data/2013281T155810_2013285T115557/v1760086475_1.qub',
        'COVIMS_0064/data/2013359T083622_2013361T044323/v1766654697_1.qub',
        'COVIMS_0065/data/2014001T025239_2014001T041901/v1767238939_1.qub',
        'COVIMS_0065/data/2014031T090354_2014033T015543/v1770000030_1.qub',
        'COVIMS_0066/data/2014067T092716_2014067T125931/v1772965488_1.qub',
        'COVIMS_0067/data/2014091T144158_2014093T173828/v1775057905_1.qub',
        'COVIMS_0067/data/2014148T133348_2014149T042907/v1780000731_2.qub',
        'COVIMS_0068/data/2014166T150437_2014167T175942/v1781539231_2.qub',
        'COVIMS_0069/data/2014183T080803_2014184T185240/v1782983152_1.qub',
        'COVIMS_0069/data/2014231T230602_2014233T084741/v1787305664_2_001.qub',
        'COVIMS_0069/data/2014233T090606_2014233T121121/v1787306770_2_044.qub',
        'COVIMS_0070/data/2014239T061435_2014241T045214/v1787814151_1.qub',
        'COVIMS_0070/data/2014262T124709_2014264T221427/v1790004104_1.qub',
        'COVIMS_0071/data/2014275T164335_2014277T100014/v1790962371_1.qub',
        'COVIMS_0072/data/2015001T225044_2015003T035332/v1798847382_1.qub',
        'COVIMS_0072/data/2015013T114033_2015015T145540/v1800001849_1.qub',
        'COVIMS_0073/data/2015072T114438_2015073T134718/v1804941502_2.qub',
        'COVIMS_0074/data/2015091T020848_2015091T101202/v1806548991_1.qub',
        'COVIMS_0074/data/2015131T001453_2015131T055526/v1810000153_1.qub',
        'COVIMS_0075/data/2015148T214932_2015149T073215/v1811544302_1.qub',
        'COVIMS_0076/data/2015184T142847_2015185T012408/v1814628218_1.qub',
        'COVIMS_0076/data/2015245T174314_2015247T023553/v1820008957_1.qub',
        'COVIMS_0077/data/2015274T104423_2015276T084529/v1822390734_1.qub',
        'COVIMS_0077/data/2015315T092754_2015316T130417/v1825945979_9.qub',
        'COVIMS_0077/data/2015359T002738_2015363T080342/v1830032101_1.qub',
        'COVIMS_0078/data/2016002T045851_2016013T043050/v1830405567_1.qub',
        'COVIMS_0079/data/2016092T001422_2016093T001509/v1838164234_1.qub',
        'COVIMS_0079/data/2016112T223342_2016115T043107/v1840000165_1.qub',
        'COVIMS_0080/data/2016150T055016_2016150T163425/v1843195446_1.qub',
        'COVIMS_0081/data/2016183T023236_2016184T025052/v1846032724_1.qub',
        'COVIMS_0081/data/2016227T192255_2016229T174101/v1850000689_1.qub',
        'COVIMS_0082/data/2016231T125604_2016231T232422/v1850219010_1.qub',
        'COVIMS_0083/data/2016259T092432_2016259T193332/v1852626266_1.qub',
        'COVIMS_0084/data/2016275T092655_2016275T153122/v1854009095_1.qub',
        'COVIMS_0085/data/2016309T175032_2016310T010612/v1856976774_1.qub',
        'COVIMS_0085/data/2016341T154413_2016350T205012/v1860474247_7.qub',
        'COVIMS_0086/data/2016361T162436_2016361T163010/v1861464712_1.qub',
        'COVIMS_0087/data/2017001T142622_2017001T194257/v1861974987_1.qub',
        'COVIMS_0088/data/2017037T214524_2017038T031815/v1865111567_1.qub',
        'COVIMS_0089/data/2017066T011232_2017066T082604/v1867544042_1.qub',
        'COVIMS_0090/data/2017091T014908_2017092T180222/v1869706036_1.qub',
        'COVIMS_0090/data/2017094T055745_2017095T005431/v1870000035_1.qub',
        'COVIMS_0091/data/2017120T174111_2017120T204434/v1872269358_1.qub',
        'COVIMS_0092/data/2017168T053422_2017169T011104/v1876372739_1.qub',
        'COVIMS_0093/data/2017182T000942_2017185T044728/v1877562607_1.qub',
        'COVIMS_0093/data/2017210T032014_2017212T183252/v1880040976_1.qub',
        'COVIMS_0094/data/2017238T104254_2017238T235735/v1882439160_1.qub',
    ]

    for file_path in TESTS:
        logical_path = 'volumes/COVIMS_0xxx/' + file_path
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
            for category in ('volumes', 'previews'):
                for abspath in pdsf.associated_abspaths(category):
                    assert abspath in opus_id_abspaths

##########################################################################################
