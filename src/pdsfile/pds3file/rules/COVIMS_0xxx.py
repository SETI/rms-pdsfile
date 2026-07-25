##########################################################################################
# pds3file/rules/COVIMS_0xxx.py
##########################################################################################

import pdsfile.pds3file as pds3file
from pdsfile.pdsfile import abspath_for_logical_path
import os
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
