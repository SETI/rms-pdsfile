##########################################################################################
# pds3file/rules/NHxxxx_xxxx.py
##########################################################################################

import pdsfile.pds3file as pds3file
import translator
import re

##########################################################################################
# Special procedure to define and prioritize OPUS_TYPES
##########################################################################################

# Define the priority among file types
FILE_CODE_PRIORITY = {

    # LORRI codes
    '630': 0,  #- LORRI High-res Lossless (CDH 1)/LOR
    '631': 2,  #- LORRI High-res Packetized (CDH 1)/LOR
    '632': 4,  #- LORRI High-res Lossy (CDH 1)/LOR
    '633': 6,  #- LORRI 4x4 Binned Lossless (CDH 1)/LOR
    '634': 8,  #- LORRI 4x4 Binned Packetized (CDH 1)/LOR
    '635': 10, #- LORRI 4x4 Binned Lossy (CDH 1)/LOR
    '636': 1,  #- LORRI High-res Lossless (CDH 2)/LOR
    '637': 3,  #- LORRI High-res Packetized (CDH 2)/LOR
    '638': 5,  #- LORRI High-res Lossy (CDH 2)/LOR
    '639': 7,  #- LORRI 4x4 Binned Lossless (CDH 2)/LOR
    '63A': 9,  #- LORRI 4x4 Binned Packetized (CDH 2)/LOR
    '63B': 11, #- LORRI 4x4 Binned Lossy (CDH 2)/LOR

    # MVIC codes
    '530': 12, #- MVIC Panchromatic TDI Lossless (CDH 1)/MP1,MP2
    '531': 18, #- MVIC Panchromatic TDI Packetized (CDH 1)/MP1,MP2
    '532': 24, #- MVIC Panchromatic TDI Lossy (CDH 1)/MP1,MP2

    '533': 30, #- MVIC Panchromatic TDI 3x3 Binned Lossless (CDH 1)/MP1,MP2
    '534': 32, #- MVIC Panchromatic TDI 3x3 Binned Packetized (CDH 1)/MP1,MP2
    '535': 34, #- MVIC Panchromatic TDI 3x3 Binned Lossy (CDH 1)/MP1,MP2

    '536': 13, #- MVIC Color TDI Lossless (CDH 1)/MC0,MC1,MC2,MC3
    '537': 19, #- MVIC Color TDI Packetized (CDH 1)/MC0,MC1,MC2,MC3
    '538': 25, #- MVIC Color TDI Lossy (CDH 1)/MC0,MC1,MC2,MC3

    '539': 14, #- MVIC Panchromatic Frame Transfer Lossless (CDH 1)/MPF
    '53A': 20, #- MVIC Panchromatic Frame Transfer Packetized (CDH 1)/MPF
    '53B': 26, #- MVIC Panchromatic Frame Transfer Lossy (CDH 1)/MPF

    '53F': 15, #- MVIC Panchromatic TDI Lossless (CDH 2)/MP1,MP2
    '540': 21, #- MVIC Panchromatic TDI Packetized (CDH 2)/MP1,MP2
    '541': 27, #- MVIC Panchromatic TDI Lossy (CDH 2)/MP1,MP2

    '542': 31, #- MVIC Panchromatic TDI 3x3 Binned Lossless (CDH 2)/MP1,MP2
    '543': 33, #- MVIC Panchromatic TDI 3x3 Binned Packetized (CDH 2)/MP1,MP2
    '544': 35, #- MVIC Panchromatic TDI 3x3 Binned Lossy (CDH 2)/MP1,MP2

    '545': 16, #- MVIC Color TDI Lossless (CDH 2)/MC0,MC1,MC2,MC3
    '546': 22, #- MVIC Color TDI Packetized (CDH 2)/MC0,MC1,MC2,MC3
    '547': 28, #- MVIC Color TDI Lossy (CDH 2)/MC0,MC1,MC2,MC3

    '548': 17, #- MVIC Panchromatic Frame Transfer Lossless (CDH 2)/MPF
    '549': 23, #- MVIC Panchromatic Frame Transfer Packetized (CDH 2)/MPF
    '54A': 29, #- MVIC Panchromatic Frame Transfer Lossy (CDH 2)/MPF
}

##########################################################################################
# DESCRIPTION_AND_ICON
##########################################################################################

description_and_icon_by_regex = translator.TranslatorByRegex([
    (r'volumes/NH.*/NH...._1.../data(|/[0-9_]+)', re.I, ('Raw images grouped by date',        'IMAGEDIR')),
    (r'volumes/NH.*/NH...._2.../data(|/[0-9_]+)', re.I, ('Calibrated images grouped by date', 'IMAGEDIR')),

    (r'volumes/NH.*0x(533|534|535|542|543|544)_eng(|_\d+)\.fit'        , re.I, ('Raw image (3x3 binned), FITS'       , 'IMAGE')),
    (r'volumes/NH.*0x(533|534|535|542|543|544)_sci(|_\d+)\.fit'        , re.I, ('Calibrated image (3x3 binned), FITS', 'IMAGE')),
    (r'volumes/NH.*0x(633|634|635|639|63A|63B)_eng(|_\d+)\.fit'        , re.I, ('Raw image (4x4 binned), FITS'       , 'IMAGE')),
    (r'volumes/NH.*0x(633|634|635|639|63A|63B)_sci(|_\d+)\.fit'        , re.I, ('Calibrated image (4x4 binned), FITS', 'IMAGE')),
    (r'volumes/NH.*0x(530|536|539|53F|545|548|630|636)_eng(|_\d+)\.fit', re.I, ('Raw image (lossless), FITS'         , 'IMAGE')),
    (r'volumes/NH.*0x(530|536|539|53F|545|548|630|636)_sci(|_\d+)\.fit', re.I, ('Calibrated image (lossless), FITS'  , 'IMAGE')),
    (r'volumes/NH.*0x(532|538|53B|541|547|54A|632|638)_eng(|_\d+)\.fit', re.I, ('Raw image (lossy), FITS'            , 'IMAGE')),
    (r'volumes/NH.*0x(532|538|53B|541|547|54A|632|638)_sci(|_\d+)\.fit', re.I, ('Calibrated image (lossy), FITS'     , 'IMAGE')),
    (r'volumes/NH.*0x(531|537|53A|540|546|549|631|637)_eng(|_\d+)\.fit', re.I, ('Raw imag, FITS'                     , 'IMAGE')),
    (r'volumes/NH.*0x(531|537|53A|540|546|549|631|637)_sci(|_\d+)\.fit', re.I, ('Calibrated imag, FITS'              , 'IMAGE')),

    (r'.*/catalog/NH.CAT'           , re.I, ('Mission description',                     'INFO'    )),
    (r'.*/catalog/NHSC.CAT'         , re.I, ('Spacecraft description',                  'INFO'    )),
    (r'.*/catalog/(LORRI|MVIC)\.CAT', re.I, ('Instrument description',                  'INFO'    )),
    (r'.*/catalog/.*RELEASE\.CAT'   , re.I, ('Release information',                     'INFO'    )),
    (r'.*/catalog/132524_apl\.cat'  , re.I, ('Target information',                      'INFO'    )),
    (r'volumes/.*/data(|\w+)'       , re.I, ('Data files organized by date',            'IMAGEDIR')),
    (r'.*/NH...._1...\.tar\.gz'     , 0,    ('Downloadable archive of raw data',        'TARBALL' )),
    (r'.*/NH...._2...\.tar\.gz'     , 0,    ('Downloadable archive of calibrated data', 'TARBALL' )),

    (r'.*/calib/sap.*\.fit'         , re.I, ('Debias image',                            'IMAGE'   )),
    (r'.*/calib/c?flat.*\.fit'      , re.I, ('Flat field image',                        'IMAGE'   )),
    (r'.*/calib/dead.*\.fit'        , re.I, ('Dead pixel image',                        'IMAGE'   )),
    (r'.*/calib/hot.*\.fit'         , re.I, ('Hot pixel image',                         'IMAGE'   )),

    (r'volumes/.*/document/lorri_ssr\.pdf', 0, ('&#11013; <b>LORRI Description (Space Science Reviews)</b>',
                                                                                        'INFO')),
    (r'volumes/.*/document/ralph_ssr\.pdf', 0, ('&#11013; <b>Ralph Description (Space Science Reviews)</b>',
                                                                                        'INFO')),
    (r'volumes/.*/document/payload_ssr\.pdf', 0, ('&#11013; <b>Payload Description (Space Science Reviews)</b>',
                                                                                        'INFO')),
])

##########################################################################################
# VIEWABLES
##########################################################################################

default_viewables = translator.TranslatorByRegex([
    (r'volumes/(NHxx.._xxxx)(|_[0-9]\.]+)/(NH...._....)/data/(\w+/\w{3}_[0-9]{10}_0x...)_(eng.*|sci.*)\..*', 0,
            [r'previews/\1/\3/data/#LOWER#\4_\5_full.jpg',
             r'previews/\1/\3/data/#LOWER#\4_\5_med.jpg',
             r'previews/\1/\3/data/#LOWER#\4_\5_small.jpg',
             r'previews/\1/\3/data/#LOWER#\4_\5_thumb.jpg',
            ]),
])

raw_viewables = translator.TranslatorByRegex([
    (r'volumes/(NHxx.._xxxx)(|_[0-9]\.]+)/(NH....)_1(...)/data/(\w+/\w{3}_[0-9]{10}_0x...)_(eng.*)\..*', 0,
           [r'previews/\1/\3_1\4/data/#LOWER#\5_\6_full.jpg',
            r'previews/\1/\3_1\4/data/#LOWER#\5_\6_med.jpg',
            r'previews/\1/\3_1\4/data/#LOWER#\5_\6_small.jpg',
            r'previews/\1/\3_1\4/data/#LOWER#\5_\6_thumb.jpg',
           ]),
])

calibrated_viewables = translator.TranslatorByRegex([
    (r'volumes/(NHxx.._xxxx)(|_[0-9]\.]+)/(NH....)_1(...)/data/(\w+/\w{3}_[0-9]{10}_0x...)_(sci.*)\..*', 0,
           [r'previews/\1/\3_2\4/data/#LOWER#\5_\6_full.jpg',
            r'previews/\1/\3_2\4/data/#LOWER#\5_\6_med.jpg',
            r'previews/\1/\3_2\4/data/#LOWER#\5_\6_small.jpg',
            r'previews/\1/\3_2\4/data/#LOWER#\5_\6_thumb.jpg',
           ]),
])

##########################################################################################
# ASSOCIATIONS
##########################################################################################

associations_to_volumes = translator.TranslatorByRegex([
    (r'.*/(NHxx.._xxxx)(|_v[0-9\.]+)/(NH....)_[12](...)/data/(\w+/[a-z0-9]{3}_[0-9]{10})_0x.*', re.I,
            [r'volumes/\1\2/\3_1\4/data/#LOWER#\5*',
             r'volumes/\1\2/\3_1\4/DATA/#UPPER#\5*',    # NHxxMV_xxxx_v1/NHJUMV_1001 is upper case
             r'volumes/\1\2/\3_2\4/data/#LOWER#\5*',
            ]),
    (r'.*/(NHxx.._xxxx)(|_v[0-9\.]+)/(NH....)_[12](...)/data(|/\w+)', re.I,
            [r'volumes/\1\2/\3_1\4/data\5',
             r'volumes/\1\2/\3_1\4/DATA\5',
             r'volumes/\1\2/\3_2\4/data\5',
            ]),
    (r'documents/(NHxx.._xxxx).*', 0, r'volumes/\1')
])

associations_to_previews = translator.TranslatorByRegex([
    (r'.*/(NHxx.._xxxx)(|_v[0-9\.]+)/(NH....)_[12](...)/data/(\w+/[a-z0-9]{3}_[0-9]{10}_0x...)_(eng|sci).*', re.I,
            [r'previews/\1/\3_1\4/data/#LOWER#\4_\5_eng_full.jpg',
             r'previews/\1/\3_1\4/data/#LOWER#\4_\5_eng_med.jpg',
             r'previews/\1/\3_1\4/data/#LOWER#\4_\5_eng_small.jpg',
             r'previews/\1/\3_1\4/data/#LOWER#\4_\5_eng_thumb.jpg',
             r'previews/\1/\3_2\4/data/#LOWER#\4_\5_sci_full.jpg',
             r'previews/\1/\3_2\4/data/#LOWER#\4_\5_sci_med.jpg',
             r'previews/\1/\3_2\4/data/#LOWER#\4_\5_sci_small.jpg',
             r'previews/\1/\3_2\4/data/#LOWER#\4_\5_sci_thumb.jpg',
            ]),
    (r'.*/(NHxx.._xxxx)(|_v[0-9\.]+)/(NH....)_[12](...)/data(|/\w+)', re.I,
            r'previews/\1/\3_1\4/data\5'),
])

associations_to_metadata = translator.TranslatorByRegex([
    (r'volumes/(NHxx.._xxxx)(|_v[0-9\.]+)/(NH...._[12]...)/data/\w+/([a-z0-9]{3}_[0-9]{10}_0x...)_(eng|sci).*', re.I,
            [r'metadata/\1/\3/\3_index.tab/#LOWER#\4_\5',
             r'metadata/\1/\3/\3_supplemental_index.tab/#LOWER#\4_\5',
             r'metadata/\1/\3/\3_moon_summary.tab/#LOWER#\4_\5',
             r'metadata/\1/\3/\3_ring_summary.tab/#LOWER#\4_\5',
             r'metadata/\1/\3/\3_charon_summary.tab/#LOWER#\4_\5',
             r'metadata/\1/\3/\3_pluto_summary.tab/#LOWER#\4_\5',
             r'metadata/\1/\3/\3_jupiter_summary.tab/#LOWER#\4_\5',
            ]),
])

associations_to_documents = translator.TranslatorByRegex([
    (r'(volumes/.*/NH...._.001).*', 0,
            [r'\1/document/lorri_ssr.pdf',
             r'\1/document/ralph_ssr.pdf',
             r'\1/document/payload_ssr.pdf',
            ]),
    (r'volumes/(NHxx.._xxxx).*', 0, r'documents/\1/*'),
])

##########################################################################################
# VERSIONS
##########################################################################################

# Sometimes NH .fits files have a numeric suffix, other times not
# Also, volume NHJUMV_1001 is in upper case
versions = translator.TranslatorByRegex([
    (r'volumes/(NHxx.._xxxx)(|_v[0-9\.]+)/(NH...._....)/(data/\w+/\w+0x\d\d\d_[a-z]{3}).*\.(.*)', re.I,
            [r'volumes/\1*/\3/#LOWER#\4*.\5',
             r'volumes/\1_v1/\3/#UPPER#\4*.\5',
            ]),
    (r'volumes/(NHxx.._xxxx)(|_v[0-9\.]+)/(NH...._....)/(.*)', re.I,
            [r'volumes/\1*/\3/#LOWER#\4',
             r'volumes/\1_v1/\3/#UPPER#\4',
            ]),
])

##########################################################################################
# VIEW_OPTIONS (grid_view_allowed, multipage_view_allowed, continuous_view_allowed)
##########################################################################################

view_options = translator.TranslatorByRegex([
    (r'(volumes|previews)/NHxx(LO|MV)_....(|_v[\.0-9]+)/NH...._..../data(|/\w+)', re.I, (True, True, True)),
])

##########################################################################################
# NEIGHBORS
##########################################################################################

neighbors = translator.TranslatorByRegex([
    (r'(volumes|previews)/(NHxx.._xxxx.*/NH)..(.._[12])...',             0,  r'\1/\2??\3*'),
    (r'(volumes|previews)/(NHxx.._xxxx.*/NH)..(.._[12]).../data',     re.I, (r'\1/\2??\3*/data',   r'\1/\2??\3*/DATA'  )),
    (r'(volumes|previews)/(NHxx.._xxxx.*/NH)..(.._[12]).../data/\w+', re.I, (r'\1/\2??\3*/data/*', r'\1/\2??\3*/DATA/*')),
])

##########################################################################################
# SORT_KEY
##########################################################################################

sort_key = translator.TranslatorByRegex([

    # Order volumes by LA, JU, PC, PE, KC, KE
    (r'NHLA(.._[0-9]{4}.*)', 0, r'NH1LA\1'),
    (r'NHJU(.._[0-9]{4}.*)', 0, r'NH2JU\1'),
    (r'NHPC(.._[0-9]{4}.*)', 0, r'NH3PC\1'),
    (r'NHPE(.._[0-9]{4}.*)', 0, r'NH4PE\1'),
    (r'NHKC(.._[0-9]{4}.*)', 0, r'NH5KC\1'),
    (r'NHKE(.._[0-9]{4}.*)', 0, r'NH6KE\1'),
    (r'(\w{3})_([0-9]{10})(.*)', re.I, r'\2\1\3'),
])

##########################################################################################
# SPLIT_RULES
##########################################################################################

split_rules = translator.TranslatorByRegex([
    # Group volumes with the same leading six characters, e.g., NHJULO_1001 and NHJULO_2001
    (r'(NH....)_([12])(\d\d\d)(|_[a-z]+)(|_md5\.txt|\.tar\.gz)', 0, (r'\1_x\3', r'_\2xxx\4', r'\5')),
])

##########################################################################################
# OPUS_TYPE
##########################################################################################

opus_type = translator.TranslatorByRegex([
    (r'volumes/.*/NH..LO_1.../data/.*\.(fit|lbl)', re.I, ('New Horizons LORRI',   0, 'nh_lorri_raw',          'Raw Image',        True)),
    (r'volumes/.*/NH..LO_2.../data/.*\.(fit|lbl)', re.I, ('New Horizons LORRI', 100, 'nh_lorri_calib',        'Calibrated Image', True)),
    (r'previews/.*/NH..LO_2.../data/.*\.jpg',      0,    ('New Horizons LORRI', 200, 'nh_lorri_calib_browse', 'Extra Preview (calibrated)', False)),

    (r'volumes/.*/NH..MV_1.../data/.*\.(fit|lbl)', re.I, ('New Horizons MVIC',   0, 'nh_mvic_raw',            'Raw Image',        True)),
    (r'volumes/.*/NH..MV_2.../data/.*\.(fit|lbl)', re.I, ('New Horizons MVIC', 100, 'nh_mvic_calib',          'Calibrated Image', True)),
    (r'previews/.*/NH..MV_2.../data/.*\.jpg',      0,    ('New Horizons MVIC', 200, 'nh_mvic_calib_browse',   'Extra Preview (calibrated)', False)),

    # Documentation
    (r'documents/NHxxLO_xxxx/.*',                  0, ('New Horizons LORRI', 300, 'nh_lorri_documentation', 'Documentation', False)),
    (r'documents/NHxxMV_xxxx/.*',                  0, ('New Horizons MVIC',  300, 'nh_mvic_documentation', 'Documentation', False)),
])

##########################################################################################
# OPUS_PRODUCTS
##########################################################################################

opus_products = translator.TranslatorByRegex([
    (r'.*/(NHxx.._xxxx)(|_v[0-9\.]+)/(NH....)_([12])(...)/data/(\w+/[a-z0-9]{3}_\d{10})_.*', re.I,
            [r'volumes/\1*/\3_1\5/data/#LOWER#\6_*',
             r'volumes/\1*/\3_2\5/data/#LOWER#\6_*',
             r'volumes/\1_v1/\3_1\5/DATA/#UPPER#\6_*',
             r'previews/\1/\3_1\5/data/#LOWER#\6_*',
             r'previews/\1/\3_2\5/data/#LOWER#\6_*',
             r'metadata/\1/\3_1\5/\3_1\5_index.tab',
             r'metadata/\1/\3_1\5/\3_1\5_index.lbl',
             r'metadata/\1/\3_1\5/\3_1\5_supplemental_index.tab',
             r'metadata/\1/\3_1\5/\3_1\5_supplemental_index.lbl',
             r'metadata/\1/\3_1\5/\3_1\5_inventory.csv',
             r'metadata/\1/\3_1\5/\3_1\5_inventory.lbl',
             r'metadata/\1/\3_1\5/\3_1\5_jupiter_summary.tab',
             r'metadata/\1/\3_1\5/\3_1\5_jupiter_summary.lbl',
             r'metadata/\1/\3_1\5/\3_1\5_moon_summary.tab',
             r'metadata/\1/\3_1\5/\3_1\5_moon_summary.lbl',
             r'metadata/\1/\3_1\5/\3_1\5_ring_summary.tab',
             r'metadata/\1/\3_1\5/\3_1\5_ring_summary.lbl',
             r'metadata/\1/\3_1\5/\3_1\5_pluto_summary.tab',
             r'metadata/\1/\3_1\5/\3_1\5_pluto_summary.lbl',
             r'metadata/\1/\3_1\5/\3_1\5_charon_summary.tab',
             r'metadata/\1/\3_1\5/\3_1\5_charon_summary.lbl',
            ]),
])

##########################################################################################
# OPUS_ID
##########################################################################################

opus_id = translator.TranslatorByRegex([
    (r'.*/NH..LO_.xxx.*/data/\w+/(lor_\d{10})_.*', re.I, r'nh-lorri-\1'),
    (r'.*/NH..MV_.xxx.*/data/\w+/(m.._\d{10})_.*', re.I, r'nh-mvic-#LOWER#\1'),
])

##########################################################################################
# OPUS_ID_TO_PRIMARY_LOGICAL_PATH
##########################################################################################

# Organized giving priority to lossless, full-resolution
opus_id_to_primary_logical_path = translator.TranslatorByRegex([
    (r'nh-lorri-lor_(00[0-2].*)', 0,
            [r'volumes/NHxxLO_xxxx/NHLALO_1001/data/*/lor_\1_0x63[06]_eng*.fit',        # High-res lossless
             r'volumes/NHxxLO_xxxx/NHLALO_1001/data/*/lor_\1_0x63[17]_eng*.fit',        # High-res packetized
             r'volumes/NHxxLO_xxxx/NHLALO_1001/data/*/lor_\1_0x63[28]_eng*.fit',        # High-res lossy
             r'volumes/NHxxLO_xxxx/NHLALO_1001/data/*/lor_\1_0x63[39]_eng*.fit',        # 4x4 lossless
             r'volumes/NHxxLO_xxxx/NHLALO_1001/data/*/lor_\1_0x63[4aA]_eng*.fit',       # 4x4 packetized
             r'volumes/NHxxLO_xxxx/NHLALO_1001/data/*/lor_\1_0x63[5bB]_eng*.fit']),     # 4x4 lossy

    (r'nh-lorri-lor_(00[3-4].*)', 0,
            [r'volumes/NHxxLO_xxxx/NHJULO_1001/data/*/lor_\1_0x63[06]_eng*.fit',        # High-res lossless
             r'volumes/NHxxLO_xxxx/NHJULO_1001/data/*/lor_\1_0x63[17]_eng*.fit',        # High-res packetized
             r'volumes/NHxxLO_xxxx/NHJULO_1001/data/*/lor_\1_0x63[28]_eng*.fit',        # High-res lossy
             r'volumes/NHxxLO_xxxx/NHJULO_1001/data/*/lor_\1_0x63[39]_eng*.fit',        # 4x4 lossless
             r'volumes/NHxxLO_xxxx/NHJULO_1001/data/*/lor_\1_0x63[4aA]_eng*.fit',       # 4x4 packetized
             r'volumes/NHxxLO_xxxx/NHJULO_1001/data/*/lor_\1_0x63[5bB]_eng*.fit']),     # 4x4 lossy

    (r'nh-lorri-lor_(00[5-9]|01|02[0-6])(.*)', 0,
            [r'volumes/NHxxLO_xxxx/NHPCLO_1001/data/*/lor_\1\2_0x63[06]_eng*.fit',      # High-res lossless
             r'volumes/NHxxLO_xxxx/NHPCLO_1001/data/*/lor_\1\2_0x63[17]_eng*.fit',      # High-res packetized
             r'volumes/NHxxLO_xxxx/NHPCLO_1001/data/*/lor_\1\2_0x63[28]_eng*.fit',      # High-res lossy
             r'volumes/NHxxLO_xxxx/NHPCLO_1001/data/*/lor_\1\2_0x63[39]_eng*.fit',      # 4x4 lossless
             r'volumes/NHxxLO_xxxx/NHPCLO_1001/data/*/lor_\1\2_0x63[4aA]_eng*.fit',     # 4x4 packetized
             r'volumes/NHxxLO_xxxx/NHPCLO_1001/data/*/lor_\1\2_0x63[5bB]_eng*.fit']),   # 4x4 lossy

    (r'nh-lorri-lor_(02[89]|03[0-3])(.*)', 0,
            [r'volumes/NHxxLO_xxxx/NHPELO_1001/data/*/lor_\1\2_0x63[06]_eng*.fit',      # High-res lossless
             r'volumes/NHxxLO_xxxx/NHPELO_1001/data/*/lor_\1\2_0x63[17]_eng*.fit',      # High-res packetized
             r'volumes/NHxxLO_xxxx/NHPELO_1001/data/*/lor_\1\2_0x63[28]_eng*.fit',      # High-res lossy
             r'volumes/NHxxLO_xxxx/NHPELO_1001/data/*/lor_\1\2_0x63[39]_eng*.fit',      # 4x4 lossless
             r'volumes/NHxxLO_xxxx/NHPELO_1001/data/*/lor_\1\2_0x63[4aA]_eng*.fit',     # 4x4 packetized
             r'volumes/NHxxLO_xxxx/NHPELO_1001/data/*/lor_\1\2_0x63[5bB]_eng*.fit']),   # 4x4 lossy

    (r'nh-lorri-lor_(03[4-8].*)', 0,
            [r'volumes/NHxxLO_xxxx/NHKCLO_1001/data/*/lor_\1_0x63[06]_eng*.fit',        # High-res lossless
             r'volumes/NHxxLO_xxxx/NHKCLO_1001/data/*/lor_\1_0x63[17]_eng*.fit',        # High-res packetized
             r'volumes/NHxxLO_xxxx/NHKCLO_1001/data/*/lor_\1_0x63[28]_eng*.fit',        # High-res lossy
             r'volumes/NHxxLO_xxxx/NHKCLO_1001/data/*/lor_\1_0x63[39]_eng*.fit',        # 4x4 lossless
             r'volumes/NHxxLO_xxxx/NHKCLO_1001/data/*/lor_\1_0x63[4aA]_eng*.fit',       # 4x4 packetized
             r'volumes/NHxxLO_xxxx/NHKCLO_1001/data/*/lor_\1_0x63[5bB]_eng*.fit']),     # 4x4 lossy

    (r'nh-lorri-lor_(039|04[0-5])(.*)', 0,
            [r'volumes/NHxxLO_xxxx/NHKELO_1001/data/*/lor_\1\2_0x63[06]_eng*.fit',      # High-res lossless
             r'volumes/NHxxLO_xxxx/NHKELO_1001/data/*/lor_\1\2_0x63[17]_eng*.fit',      # High-res packetized
             r'volumes/NHxxLO_xxxx/NHKELO_1001/data/*/lor_\1\2_0x63[28]_eng*.fit',      # High-res lossy
             r'volumes/NHxxLO_xxxx/NHKELO_1001/data/*/lor_\1\2_0x63[39]_eng*.fit',      # 4x4 lossless
             r'volumes/NHxxLO_xxxx/NHKELO_1001/data/*/lor_\1\2_0x63[4aA]_eng*.fit',     # 4x4 packetized
             r'volumes/NHxxLO_xxxx/NHKELO_1001/data/*/lor_\1\2_0x63[5bB]_eng*.fit']),   # 4x4 lossy

    (r'nh-mvic-(m..)_(00[0-2].*)', 0,
            [r'volumes/NHxxMV_xxxx/NHLAMV_1001/data/*/\1_\2_0x53[069fF]_eng*.fit',      # High-res lossless
             r'volumes/NHxxMV_xxxx/NHLAMV_1001/data/*/\1_\2_0x54[58]_eng*.fit',         # High-res lossless
             r'volumes/NHxxMV_xxxx/NHLAMV_1001/data/*/\1_\2_0x53[17aA]_eng*.fit',       # High-res packetized
             r'volumes/NHxxMV_xxxx/NHLAMV_1001/data/*/\1_\2_0x54[069]_eng*.fit',        # High-res packetized
             r'volumes/NHxxMV_xxxx/NHLAMV_1001/data/*/\1_\2_0x53[28]_eng*.fit',         # High-res lossy
             r'volumes/NHxxMV_xxxx/NHLAMV_1001/data/*/\1_\2_0x54[17aA]_eng*.fit',       # High-res lossy
             r'volumes/NHxxMV_xxxx/NHLAMV_1001/data/*/\1_\2_0x533_eng*.fit',            # 3x3 lossless
             r'volumes/NHxxMV_xxxx/NHLAMV_1001/data/*/\1_\2_0x542_eng*.fit',            # 3x3 lossless
             r'volumes/NHxxMV_xxxx/NHLAMV_1001/data/*/\1_\2_0x534_eng*.fit',            # 3x3 packetized
             r'volumes/NHxxMV_xxxx/NHLAMV_1001/data/*/\1_\2_0x543_eng*.fit',            # 3x3 packetized
             r'volumes/NHxxMV_xxxx/NHLAMV_1001/data/*/\1_\2_0x535_eng*.fit',            # 3x3 lossy
             r'volumes/NHxxMV_xxxx/NHLAMV_1001/data/*/\1_\2_0x544_eng*.fit']),          # 3x3 lossy

    (r'nh-mvic-(m..)_(00[3-4].*)', 0,
            [r'volumes/NHxxMV_xxxx/NHJUMV_1001/data/*/\1_\2_0x53[069fF]_eng*.fit',      # High-res lossless
             r'volumes/NHxxMV_xxxx/NHJUMV_1001/data/*/\1_\2_0x54[58]_eng*.fit',         # High-res lossless
             r'volumes/NHxxMV_xxxx/NHJUMV_1001/data/*/\1_\2_0x53[17aA]_eng*.fit',       # High-res packetized
             r'volumes/NHxxMV_xxxx/NHJUMV_1001/data/*/\1_\2_0x54[069]_eng*.fit',        # High-res packetized
             r'volumes/NHxxMV_xxxx/NHJUMV_1001/data/*/\1_\2_0x53[28]_eng*.fit',         # High-res lossy
             r'volumes/NHxxMV_xxxx/NHJUMV_1001/data/*/\1_\2_0x54[17aA]_eng*.fit',       # High-res lossy
             r'volumes/NHxxMV_xxxx/NHJUMV_1001/data/*/\1_\2_0x533_eng*.fit',            # 3x3 lossless
             r'volumes/NHxxMV_xxxx/NHJUMV_1001/data/*/\1_\2_0x542_eng*.fit',            # 3x3 lossless
             r'volumes/NHxxMV_xxxx/NHJUMV_1001/data/*/\1_\2_0x534_eng*.fit',            # 3x3 packetized
             r'volumes/NHxxMV_xxxx/NHJUMV_1001/data/*/\1_\2_0x543_eng*.fit',            # 3x3 packetized
             r'volumes/NHxxMV_xxxx/NHJUMV_1001/data/*/\1_\2_0x535_eng*.fit',            # 3x3 lossy
             r'volumes/NHxxMV_xxxx/NHJUMV_1001/data/*/\1_\2_0x544_eng*.fit']),          # 3x3 lossy

    (r'nh-mvic-(m..)_(00[5-9]|01|02[0-6])(.*)', 0,
            [r'volumes/NHxxMV_xxxx/NHPCMV_1001/data/*/\1_\2\3_0x53[069fF]_eng*.fit',    # High-res lossless
             r'volumes/NHxxMV_xxxx/NHPCMV_1001/data/*/\1_\2\3_0x54[58]_eng*.fit',       # High-res lossless
             r'volumes/NHxxMV_xxxx/NHPCMV_1001/data/*/\1_\2\3_0x53[17aA]_eng*.fit',     # High-res packetized
             r'volumes/NHxxMV_xxxx/NHPCMV_1001/data/*/\1_\2\3_0x54[069]_eng*.fit',      # High-res packetized
             r'volumes/NHxxMV_xxxx/NHPCMV_1001/data/*/\1_\2\3_0x53[28]_eng*.fit',       # High-res lossy
             r'volumes/NHxxMV_xxxx/NHPCMV_1001/data/*/\1_\2\3_0x54[17aA]_eng*.fit',     # High-res lossy
             r'volumes/NHxxMV_xxxx/NHPCMV_1001/data/*/\1_\2\3_0x533_eng*.fit',          # 3x3 lossless
             r'volumes/NHxxMV_xxxx/NHPCMV_1001/data/*/\1_\2\3_0x542_eng*.fit',          # 3x3 lossless
             r'volumes/NHxxMV_xxxx/NHPCMV_1001/data/*/\1_\2\3_0x534_eng*.fit',          # 3x3 packetized
             r'volumes/NHxxMV_xxxx/NHPCMV_1001/data/*/\1_\2\3_0x543_eng*.fit',          # 3x3 packetized
             r'volumes/NHxxMV_xxxx/NHPCMV_1001/data/*/\1_\2\3_0x535_eng*.fit',          # 3x3 lossy
             r'volumes/NHxxMV_xxxx/NHPCMV_1001/data/*/\1_\2\3_0x544_eng*.fit']),        # 3x3 lossy

    (r'nh-mvic-(m..)_(02[89]|03[0-3])(.*)', 0,
            [r'volumes/NHxxMV_xxxx/NHPEMV_1001/data/*/\1_\2\3_0x53[069fF]_eng*.fit',    # High-res lossless
             r'volumes/NHxxMV_xxxx/NHPEMV_1001/data/*/\1_\2\3_0x54[58]_eng*.fit',       # High-res lossless
             r'volumes/NHxxMV_xxxx/NHPEMV_1001/data/*/\1_\2\3_0x53[17aA]_eng*.fit',     # High-res packetized
             r'volumes/NHxxMV_xxxx/NHPEMV_1001/data/*/\1_\2\3_0x54[069]_eng*.fit',      # High-res packetized
             r'volumes/NHxxMV_xxxx/NHPEMV_1001/data/*/\1_\2\3_0x53[28]_eng*.fit',       # High-res lossy
             r'volumes/NHxxMV_xxxx/NHPEMV_1001/data/*/\1_\2\3_0x54[17aA]_eng*.fit',     # High-res lossy
             r'volumes/NHxxMV_xxxx/NHPEMV_1001/data/*/\1_\2\3_0x533_eng*.fit',          # 3x3 lossless
             r'volumes/NHxxMV_xxxx/NHPEMV_1001/data/*/\1_\2\3_0x542_eng*.fit',          # 3x3 lossless
             r'volumes/NHxxMV_xxxx/NHPEMV_1001/data/*/\1_\2\3_0x534_eng*.fit',          # 3x3 packetized
             r'volumes/NHxxMV_xxxx/NHPEMV_1001/data/*/\1_\2\3_0x543_eng*.fit',          # 3x3 packetized
             r'volumes/NHxxMV_xxxx/NHPEMV_1001/data/*/\1_\2\3_0x535_eng*.fit',          # 3x3 lossy
             r'volumes/NHxxMV_xxxx/NHPEMV_1001/data/*/\1_\2\3_0x544_eng*.fit']),        # 3x3 lossy

    (r'nh-mvic-(m..)_(03[6-8]|039[0-6])(.*)', 0,
            [r'volumes/NHxxMV_xxxx/NHKCMV_1001/data/*/\1_\2\3_0x53[069fF]_eng*.fit',    # High-res lossless
             r'volumes/NHxxMV_xxxx/NHKCMV_1001/data/*/\1_\2\3_0x54[58]_eng*.fit',       # High-res lossless
             r'volumes/NHxxMV_xxxx/NHKCMV_1001/data/*/\1_\2\3_0x53[17aA]_eng*.fit',     # High-res packetized
             r'volumes/NHxxMV_xxxx/NHKCMV_1001/data/*/\1_\2\3_0x54[069]_eng*.fit',      # High-res packetized
             r'volumes/NHxxMV_xxxx/NHKCMV_1001/data/*/\1_\2\3_0x53[28]_eng*.fit',       # High-res lossy
             r'volumes/NHxxMV_xxxx/NHKCMV_1001/data/*/\1_\2\3_0x54[17aA]_eng*.fit',     # High-res lossy
             r'volumes/NHxxMV_xxxx/NHKCMV_1001/data/*/\1_\2\3_0x533_eng*.fit',          # 3x3 lossless
             r'volumes/NHxxMV_xxxx/NHKCMV_1001/data/*/\1_\2\3_0x542_eng*.fit',          # 3x3 lossless
             r'volumes/NHxxMV_xxxx/NHKCMV_1001/data/*/\1_\2\3_0x534_eng*.fit',          # 3x3 packetized
             r'volumes/NHxxMV_xxxx/NHKCMV_1001/data/*/\1_\2\3_0x543_eng*.fit',          # 3x3 packetized
             r'volumes/NHxxMV_xxxx/NHKCMV_1001/data/*/\1_\2\3_0x535_eng*.fit',          # 3x3 lossy
             r'volumes/NHxxMV_xxxx/NHKCMV_1001/data/*/\1_\2\3_0x544_eng*.fit']),        # 3x3 lossy

    (r'nh-mvic-(m..)_(039[7-9]|04[0-5])(.*)', 0,
            [r'volumes/NHxxMV_xxxx/NHKEMV_1001/data/*/\1_\2\3_0x53[069fF]_eng*.fit',    # High-res lossless
             r'volumes/NHxxMV_xxxx/NHKEMV_1001/data/*/\1_\2\3_0x54[58]_eng*.fit',       # High-res lossless
             r'volumes/NHxxMV_xxxx/NHKEMV_1001/data/*/\1_\2\3_0x53[17aA]_eng*.fit',     # High-res packetized
             r'volumes/NHxxMV_xxxx/NHKEMV_1001/data/*/\1_\2\3_0x54[069]_eng*.fit',      # High-res packetized
             r'volumes/NHxxMV_xxxx/NHKEMV_1001/data/*/\1_\2\3_0x53[28]_eng*.fit',       # High-res lossy
             r'volumes/NHxxMV_xxxx/NHKEMV_1001/data/*/\1_\2\3_0x54[17aA]_eng*.fit',     # High-res lossy
             r'volumes/NHxxMV_xxxx/NHKEMV_1001/data/*/\1_\2\3_0x533_eng*.fit',          # 3x3 lossless
             r'volumes/NHxxMV_xxxx/NHKEMV_1001/data/*/\1_\2\3_0x542_eng*.fit',          # 3x3 lossless
             r'volumes/NHxxMV_xxxx/NHKEMV_1001/data/*/\1_\2\3_0x534_eng*.fit',          # 3x3 packetized
             r'volumes/NHxxMV_xxxx/NHKEMV_1001/data/*/\1_\2\3_0x543_eng*.fit',          # 3x3 packetized
             r'volumes/NHxxMV_xxxx/NHKEMV_1001/data/*/\1_\2\3_0x535_eng*.fit',          # 3x3 lossy
             r'volumes/NHxxMV_xxxx/NHKEMV_1001/data/*/\1_\2\3_0x544_eng*.fit']),        # 3x3 lossy
])

##########################################################################################
# FILESPEC_TO_BUNDLESET
##########################################################################################

filespec_to_bundleset = translator.TranslatorByRegex([
    (r'NH..(MV|LO)_\d{4}.*', 0, r'NHxx\1_xxxx'),
])

##########################################################################################
# Subclass definition
##########################################################################################

class NHxxxx_xxxx(pds3file.Pds3File):

    pds3file.Pds3File.VOLSET_TRANSLATOR = translator.TranslatorByRegex([('NHxx.._xxxx', re.I, 'NHxxxx_xxxx')]) + \
                                          pds3file.Pds3File.VOLSET_TRANSLATOR

    DESCRIPTION_AND_ICON = description_and_icon_by_regex + pds3file.Pds3File.DESCRIPTION_AND_ICON
    VIEW_OPTIONS = view_options + pds3file.Pds3File.VIEW_OPTIONS
    NEIGHBORS = neighbors + pds3file.Pds3File.NEIGHBORS
    SORT_KEY = sort_key + pds3file.Pds3File.SORT_KEY
    SPLIT_RULES = split_rules + pds3file.Pds3File.SPLIT_RULES

    OPUS_TYPE = opus_type + pds3file.Pds3File.OPUS_TYPE
    OPUS_PRODUCTS = opus_products + pds3file.Pds3File.OPUS_PRODUCTS
    OPUS_ID = opus_id
    OPUS_ID_TO_PRIMARY_LOGICAL_PATH = opus_id_to_primary_logical_path

    VIEWABLES = {
        'default'   : default_viewables,
        'raw'       : raw_viewables,
        'calibrated': calibrated_viewables,
    }

    VIEWABLE_TOOLTIPS = {
        'default'   : 'Default browse product for this file',
        'raw'       : 'Preview of the raw image',
        'calibrated': 'Preview of the calibrated image',
    }

    ASSOCIATIONS = pds3file.Pds3File.ASSOCIATIONS.copy()
    ASSOCIATIONS['volumes']   += associations_to_volumes
    ASSOCIATIONS['previews']  += associations_to_previews
    ASSOCIATIONS['metadata']  += associations_to_metadata
    ASSOCIATIONS['documents'] += associations_to_documents

    VERSIONS = versions + pds3file.Pds3File.VERSIONS

    FILENAME_KEYLEN = 14    # trim off suffixes

    def opus_prioritizer(self, pdsfile_dict):
        """Prioritize items that have been downlinked in multiple ways."""

        headers = list(pdsfile_dict.keys())     # Save keys so we can alter dict
        for header in headers:
            sublists = pdsfile_dict[header]
            if len(sublists) == 1:
                continue

            # Only prioritize data products
            if sublists[0][0].voltype_ != 'volumes/':
                continue

            # Split up the sublists by version rank
            rank_dict = {}
            for sublist in sublists:
                rank = sublist[0].version_rank
                if rank not in rank_dict:
                    rank_dict[rank] = []
                rank_dict[rank].append(sublist)

            # Sort the version ranks
            ranks = list(rank_dict.keys())
            ranks.sort()
            ranks.reverse()

            # Define the alternative header
            alt_header = (header[0], header[1] + 50,
                                     header[2] + '_alternate',
                                     header[3] + ' Alternate Downlink',
                                     True)
            pdsfile_dict[alt_header] = []
            pdsfile_dict[header] = []

            # Sort items by priority among each available version
            for rank in ranks:
                prioritizer = []    # (priority from hex code, hex code,
                                    # sublist)
                for sublist in rank_dict[rank]:
                    code = (sublist[0].basename.replace('X','x')
                            .partition('_0x')[2][:3]).upper()
                    prioritizer.append((FILE_CODE_PRIORITY[code], code,
                                        sublist))

                prioritizer.sort()

                # Update the dictionary for each rank
                pdsfile_dict[header].append(prioritizer[0][-1])
                pdsfile_dict[alt_header] += [p[-1] for p in prioritizer[1:]]

        return pdsfile_dict

# Global attribute shared by all subclasses
pds3file.Pds3File.OPUS_ID_TO_SUBCLASS = translator.TranslatorByRegex([(r'nh-.*', 0, NHxxxx_xxxx)]) + \
                                        pds3file.Pds3File.OPUS_ID_TO_SUBCLASS

pds3file.Pds3File.FILESPEC_TO_BUNDLESET = filespec_to_bundleset + pds3file.Pds3File.FILESPEC_TO_BUNDLESET

##########################################################################################
# Update the global dictionary of subclasses
##########################################################################################

pds3file.Pds3File.SUBCLASSES['NHxxxx_xxxx'] = NHxxxx_xxxx

##########################################################################################

import pytest
from .pytest_support import *

@pytest.mark.parametrize(
# 1001 is the raw volume and 2001 is the calibrated volume.
    'input_path,expected',
    [
        ('volumes/NHxxLO_xxxx/NHLALO_1001/data/20060224_000310/lor_0003103486_0x630_eng.fit',
         'NHxxLO_xxxx/opus_products/lor_0003103486_0x630_eng.txt')
    ]
)
def test_opus_products(request, input_path, expected):
    update = request.config.option.update
    opus_products_test(pds3file.Pds3File, input_path, TEST_RESULTS_DIR+expected, update)

@pytest.mark.parametrize(
    'input_path,category,expected',
    [
        ('volumes/NHxxLO_xxxx/NHLALO_1001/data/20060224_000310/lor_0003103486_0x630_eng.fit',
         'volumes',
         'NHxxLO_xxxx/associated_abspaths/volumes_lor_0003103486_0x630_eng.txt')
    ]
)
def test_associated_abspaths(request, input_path, category, expected):
    update = request.config.option.update
    associated_abspaths_test(pds3file.Pds3File, input_path, category,
                             TEST_RESULTS_DIR+expected, update)

def test_opus_id_to_primary_logical_path():
    TESTS = [
        ('volumes/NHxxLO_xxxx/NHLALO_1001/data/20060224_000310/lor_0003103486_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHLALO_1001/data/20060423_000810/lor_0008107080_0x633_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHLALO_1001/data/20060730_001657/lor_0016577910_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHLALO_1001/data/20060910_002017/lor_0020170799_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHLALO_1001/data/20061018_002350/lor_0023502654_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHJULO_1001/data/20070108_003059/lor_0030598439_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHJULO_1001/data/20070228_003498/lor_0034981642_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHJULO_1001/data/20070301_003501/lor_0035015234_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHJULO_1001/data/20070307_003558/lor_0035585520_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHJULO_1001/data/20070526_004251/lor_0042517021_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHJULO_1001/data/20070611_004389/lor_0043897321_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHPCLO_1001/data/20070929_005334/lor_0053344800_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHPCLO_1001/data/20081013_008624/lor_0086245758_0x632_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHPCLO_1001/data/20090721_011048/lor_0110487779_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHPCLO_1001/data/20100625_013981/lor_0139810087_0x632_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHPCLO_1001/data/20110523_016842/lor_0168423779_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHPCLO_1001/data/20120523_020011/lor_0200112778_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHPCLO_1001/data/20130622_023420/lor_0234206579_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHPCLO_1001/data/20130712_023593/lor_0235939200_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHPCLO_1001/data/20140705_026686/lor_0266867668_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHPCLO_1001/data/20140726_026868/lor_0268688039_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHPELO_1001/data/20150125_028445/lor_0284457178_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHPELO_1001/data/20150131_028503/lor_0285035518_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHPELO_1001/data/20150223_028702/lor_0287027527_0x633_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHPELO_1001/data/20150405_029052/lor_0290526007_0x633_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHPELO_1001/data/20150723_029999/lor_0299994502_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHPELO_1001/data/20150724_030002/lor_0300027012_0x636_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHPELO_1001/data/20160407_032236/lor_0322361528_0x633_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHPELO_1001/data/20160711_033056/lor_0330563039_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHPELO_1001/data/20160716_033096/lor_0330965068_0x633_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHKCLO_1001/data/20170128_034788/lor_0347882528_0x633_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHKCLO_1001/data/20170129_034797/lor_0347976302_0x633_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHKCLO_1001/data/20170130_034804/lor_0348045126_0x633_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHKCLO_1001/data/20170918_036804/lor_0368041919_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHKCLO_1001/data/20170923_036850/lor_0368506958_0x633_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHKCLO_1001/data/20171030_037170/lor_0371709419_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHKCLO_1001/data/20171206_037489/lor_0374894598_0x633_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHKELO_1001/data/20180816_039668/lor_0396683548_0x633_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHKELO_1001/data/20180819_039700/lor_0397002308_0x633_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHKELO_1001/data/20180824_039744/lor_0397444588_0x633_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHKELO_1001/data/20180909_039877/lor_0398776019_0x636_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHKELO_1001/data/20180921_039983/lor_0399830818_0x633_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHKELO_1001/data/20180924_040007/lor_0400078348_0x633_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHKELO_1001/data/20190713_042535/lor_0425351280_0x633_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHKELO_1001/data/20191207_043800/lor_0438001863_0x633_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHKELO_1001/data/20200423_044993/lor_0449933837_0x633_eng.fit', ''),

        ('volumes/NHxxMV_xxxx/NHLAMV_1001/data/20060321_000525/mpf_0005259637_0x539_eng_1.fit', ''),
        ('volumes/NHxxMV_xxxx/NHLAMV_1001/data/20060528_001112/mpf_0011128079_0x539_eng_1.fit', ''),
        ('volumes/NHxxMV_xxxx/NHLAMV_1001/data/20060922_002127/mp1_0021270021_0x530_eng_1.fit', ''),
        ('volumes/NHxxMV_xxxx/NHJUMV_1001/data/20070131_003252/mc0_0032528036_0x536_eng_1.fit', ''),
        ('volumes/NHxxMV_xxxx/NHJUMV_1001/data/20070225_003470/mc0_0034706398_0x536_eng_1.fit', ''),
        ('volumes/NHxxMV_xxxx/NHJUMV_1001/data/20070228_003497/mc3_0034973818_0x536_eng_1.fit', ''),
        ('volumes/NHxxMV_xxxx/NHJUMV_1001/data/20070303_003520/mc3_0035207878_0x536_eng_1.fit', ''),
        ('volumes/NHxxMV_xxxx/NHJUMV_1001/data/20070311_003590/mc0_0035903518_0x536_eng_1.fit', ''),
        ('volumes/NHxxMV_xxxx/NHJUMV_1001/data/20070526_004251/mc0_0042515578_0x536_eng_1.fit', ''),
        ('volumes/NHxxMV_xxxx/NHJUMV_1001/data/20070611_004389/mpf_0043897317_0x539_eng_1.fit', ''),
        ('volumes/NHxxMV_xxxx/NHPCMV_1001/data/20070918_005245/mc0_0052459368_0x536_eng.fit', ''),
        ('volumes/NHxxMV_xxxx/NHPCMV_1001/data/20090727_011102/mc0_0111027468_0x536_eng.fit', ''),
        ('volumes/NHxxMV_xxxx/NHPCMV_1001/data/20100625_013981/mp2_0139810012_0x530_eng.fit', ''),
        ('volumes/NHxxMV_xxxx/NHPCMV_1001/data/20120518_019968/mpf_0199685294_0x539_eng.fit', ''),
        ('volumes/NHxxMV_xxxx/NHPCMV_1001/data/20120601_020089/mpf_0200892714_0x539_eng.fit', ''),
        ('volumes/NHxxMV_xxxx/NHPCMV_1001/data/20130622_023420/mc0_0234201648_0x536_eng.fit', ''),
        ('volumes/NHxxMV_xxxx/NHPCMV_1001/data/20140723_026844/mpf_0268442094_0x539_eng.fit', ''),
        ('volumes/NHxxMV_xxxx/NHPEMV_1001/data/20150303_028769/mc0_0287692247_0x536_eng.fit', ''),
        ('volumes/NHxxMV_xxxx/NHPEMV_1001/data/20150409_029086/mc3_0290860851_0x536_eng.fit', ''),
        ('volumes/NHxxMV_xxxx/NHPEMV_1001/data/20150721_029979/mpf_0299796966_0x548_eng.fit', ''),
        ('volumes/NHxxMV_xxxx/NHPEMV_1001/data/20160630_032955/mc0_0329556649_0x536_eng.fit', ''),
        ('volumes/NHxxMV_xxxx/NHPEMV_1001/data/20160716_033093/mp2_0330935151_0x530_eng.fit', ''),
        ('volumes/NHxxMV_xxxx/NHKCMV_1001/data/20170921_036832/mc0_0368328709_0x536_eng.fit', ''),
        ('volumes/NHxxMV_xxxx/NHKCMV_1001/data/20180713_039381/mpf_0393815218_0x539_eng.fit', ''),
        ('volumes/NHxxMV_xxxx/NHKEMV_1001/data/20180831_039797/mc0_0397979512_0x536_eng.fit', ''),
        ('volumes/NHxxMV_xxxx/NHKEMV_1001/data/20181230_040849/mc0_0408494512_0x536_eng.fit', ''),
        ('volumes/NHxxMV_xxxx/NHKEMV_1001/data/20190316_041502/mpf_0415029106_0x539_eng.fit', ''),
        ('volumes/NHxxMV_xxxx/NHKEMV_1001/data/20190812_042795/mc0_0427957249_0x536_eng.fit', ''),
        ('volumes/NHxxMV_xxxx/NHKEMV_1001/data/20190902_042977/mc3_0429771832_0x536_eng.fit', ''),

        ('volumes/NHxxLO_xxxx/NHJULO_1001/data/20070611_004390/lor_0043906321_0x630_eng.fit',   '0x636'),
        ('volumes/NHxxLO_xxxx/NHPELO_1001/data/20150713_029913/lor_0299135304_0x630_eng.fit',   '0x632'),
        ('volumes/NHxxMV_xxxx/NHJUMV_1001/data/20070611_004390/mpf_0043906317_0x539_eng_1.fit', '0x548'),
        ('volumes/NHxxMV_xxxx/NHPCMV_1001/data/20130712_023593/mpf_0235933761_0x548_eng.fit',   '0x54a'),
    ]

    for (logical_path, alt_hex_code) in TESTS:
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
            # Every version of a data file is in the product set
            if pdsf.voltype_ == 'volumes/':
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

        # Alternate hex code is in the product set
        if alt_hex_code:
            hex_code = '0x' + test_pdsf.abspath.split('0x')[1][:3]
            alt_abspath = test_pdsf.abspath.replace(hex_code, alt_hex_code)
            alt_pdsf = pds3file.Pds3File.from_abspath(alt_abspath)
            for version_pdsf in alt_pdsf.all_versions().values():
                assert version_pdsf.abspath in opus_id_abspaths

##########################################################################################
