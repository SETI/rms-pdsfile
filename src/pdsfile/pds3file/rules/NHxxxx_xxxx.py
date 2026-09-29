##########################################################################################
# pds3file/rules/NHxxxx_xxxx.py
##########################################################################################

"""Rules for the New Horizons LORRI and MVIC volume sets, served by NHxxxx_xxxx.

`NHxxxx_xxxx.py` serves two volume sets through one subclass, matched by the pattern
NHxx.._xxxx: NHxxLO_xxxx, the New Horizons LORRI image collection, and NHxxMV_xxxx,
the New Horizons MVIC image collection (``_volinfo/NHxxLO_xxxx.txt`` and
``_volinfo/NHxxMV_xxxx.txt``). A volume name encodes the mission phase and the
instrument, as in NHJULO_1001 for the Jupiter flyby with LORRI and NHKEMV_1001 for
the Arrokoth flyby with MVIC. A raw volume is numbered 1nnn and its calibrated
counterpart 2nnn, which is why the association and viewable tables here rewrite that
digit rather than switching trees. A data file is FITS.

One observation can be downlinked more than once, in different binnings and with
different compression, and the downlink is recorded as a hexadecimal code in the
file name. That is what shapes this module:

* ``FILE_CODE_PRIORITY`` -- the hexadecimal file codes mapped to a sort priority,
  36 of them: the twelve contiguous LORRI codes 630 through 63B, and 24 MVIC codes
  between 530 and 54A, which are not contiguous. The comment on each entry names the
  mode it stands for. For LORRI that is lossless, packetized or lossy, high-resolution
  or 4x4 binned; for MVIC it is panchromatic TDI, panchromatic TDI 3x3 binned, color
  TDI or panchromatic frame transfer, each again lossless, packetized or lossy. Each
  comment also records which of the two CDH units produced it. This table is defined
  by no other rule module.

The remaining rule tables:

* ``description_and_icon_by_regex`` -- distinguishes raw from calibrated FITS and
  names the binning and compression of each, names the date-grouped directories, the
  calibration frames (debias, flat field, dead pixel, hot pixel) and the PDS3
  catalog files, and points at the instrument and payload descriptions in each
  volume's own document directory.
* ``default_viewables``, ``raw_viewables`` and ``calibrated_viewables`` -- the
  previews for a product, for its raw form and for its calibrated form. The class
  offers the last two as the "raw" and "calibrated" viewable sets with tooltips of
  their own.
* ``associations_to_volumes``, ``associations_to_previews``,
  ``associations_to_metadata`` and ``associations_to_documents`` -- cross the
  volumes, previews, metadata and documents trees for one observation.
* ``versions`` -- the paths of the same product in the other versions of these
  volume sets.
* ``view_options``, ``neighbors``, ``sort_key`` and ``split_rules`` -- the view
  flags, the corresponding directories in sibling volumes, the basename sort order
  and the basename grouping.
* ``opus_type`` and ``opus_products`` -- file products under the "New Horizons
  LORRI" and "New Horizons MVIC" OPUS categories and list what OPUS offers with
  each.
* ``opus_id`` and ``opus_id_to_primary_logical_path`` -- the OPUS ID and its
  inverse.
* ``filespec_to_bundleset`` -- maps a file specification beginning with a volume ID
  of the form NH, two characters for the mission phase, the letters LO or MV, an
  underscore and four digits, to NHxxLO_xxxx or NHxxMV_xxxx. The default rule cannot
  do it because it replaces only the last three characters and leaves the mission
  phase in place.

The class body sets ``NHxxxx_xxxx.FILENAME_KEYLEN`` to 14 so that the several
downlinks of one observation group together, and defines
``NHxxxx_xxxx.opus_prioritizer``, which uses ``FILE_CODE_PRIORITY`` to keep the
best downlink of a product under its original OPUS heading and move the rest to an
"Alternate Downlink" heading. `GO_0xxx.py` is the only other rule module that
defines a prioritizer.
"""

import re

import translator

import pdsfile.pds3file as pds3file

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
    """The ``Pds3File`` subclass for NHxxxx_xxxx.

    The class body and the module tail install this module's rule tables on the class
    attributes ``Pds3File`` reads. `pds3file/rules/__init__.py` sets out the routes a
    table takes and which of them leaves the inherited rules in front. The class
    is registered in ``Pds3File.SUBCLASSES`` under the key
    "NHxxxx_xxxx".
    The module docstring describes the volume set and every table.

    It also sets ``FILENAME_KEYLEN`` to 14, so that the several downlinks of one
    observation group together, and defines ``opus_prioritizer``.
    """

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
        """Split the best downlink of a product from its alternatives.

        One New Horizons observation can be downlinked more than once, in different
        binnings and with different compression, and the mode is recorded as three
        hexadecimal characters after "_0x" in the file name. Where an OPUS heading
        holds more than one copy of a data product, this keeps the copy whose file
        code ranks best in ``FILE_CODE_PRIORITY`` under that heading and moves the
        rest to a heading in the same category whose rank is 50 higher, whose slug
        gains "_alternate", whose title gains " Alternate Downlink" and whose
        default-selected flag is True whatever the original heading carried. The
        copies are grouped by version rank first, so one copy per rank survives
        under the original heading.

        A heading holding a single copy is left alone, and so is one whose copies are
        not in the volumes tree.

        The dictionary is modified in place as well as returned: the two headings it
        touches are rewritten and the alternative heading is added.

        Parameters:
            pdsfile_dict (dict): the OPUS product dictionary. A key is a
                (category, rank, slug, title, selected) tuple, or the empty string
                for a product whose type no rule matched; a value is a list of lists
                of PdsFile objects.

        Returns:
            dict: the same dictionary.

        Raises:
            IndexError: raised by the item read ``__getitem__()`` on the heading,
                where the heading is the empty-string key and it holds more than one
                copy of a product in the volumes tree.
            KeyError: raised by the priority lookup, the item read
                ``__getitem__()`` on ``FILE_CODE_PRIORITY``, for a file code the
                table does not list.
            TypeError: raised by ``sort()`` wherever two copies at one version rank
                are given the same priority and the same file code, which here means
                the same file code, since the priority is looked up from it. The
                comparison then falls through to the lists of PdsFile objects, which
                have no ordering.
        """

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
