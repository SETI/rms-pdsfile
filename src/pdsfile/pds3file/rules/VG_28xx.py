##########################################################################################
# pds3file/rules/VG_28xx.py
##########################################################################################

import pdsfile.pds3file as pds3file
import translator
import re

##########################################################################################
# DESCRIPTION_AND_ICON
##########################################################################################

SUN_DICT = """{
"N1": "Neptune",
"S1": "Saturn",
"U1": "Uranus sigma Sgr",
"U2": "Uranus beta Per"}""".replace('\n','')

SU_DICT = """{
"S": "Saturn",
"U": "Uranus"}""".replace('\n','')

URING_DICT = """{
"6": "six",
"5": "five",
"4": "four",
"A": "alpha",
"B": "beta",
"N": "eta",
"G": "gamma",
"D": "delta",
"L": "lambda",
"E": "epsilon",
"X": "ringpl"}""".replace('\n','')

IE_DICT = """{
"I": " ingress",
"E": " egress"}""".replace('\n','')

KIND = """{
"C": "calibration model",
"D": "edited raw data",
"F": "sub-sampled profile",
"G": "geometry model",
"J": "jitter data",
"N": "stellar background data",
"P": "calibrated profile",
"R": "raw data",
"T": "trajectory data",
"V": "vectors",
"W": "spectral time series"}""".replace('\n','')

KIND_UC = """{
"C": "Calibration model",
"D": "Edited raw data",
"F": "Sub-sampled profile",
"G": "Geometry model",
"J": "Jitter data",
"N": "Stellar background data",
"P": "Calibrated profile",
"R": "Raw data",
"T": "Trajectory data",
"V": "Vectors",
"W": "Spectral time series"}""".replace('\n','')

ICON = """{
"C": "SERIES",
"D": "SERIES",
"F": "SERIES",
"G": "GEOM",
"J": "GEOM",
"N": "SERIES",
"R": "SERIES",
"T": "GEOM",
"V": "GEOM",
"W": "SERIES"}""".replace('\n','')

NEXT = """{
5: "6",
6: "7",
7: "8",
8: "9",
9: "10",
10: "11",
11: "12",
12: "13",
13: "14"}""".replace('\n','')

SRSS_DICT = """{
1: "400-m",
2: "400-m",
3: "1-km",
4: "5-km"}""".replace('\n','')

URSS_DICT = """{
1: "50-m",
2: "200-m",
3: "200-m",
4: "500-m",
5: "1-km"}""".replace('\n','')

FRAME_DICT = """{
1: "B1950",
2: "J2000""".replace('\n','')

COORD_DICT = """{
"C": "celestial",
"E": "ring",
"R": "ring",
"A": "inclined ring"}""".replace('\n','')

CU_DICT = """{
"C": "corrected",
"U": "un-corrected"}""".replace('\n','')

VIP_DICT = """{
"V": "Vax",
"I": "IEEE",
"P": "PC"}""".replace('\n','')

POLE_DICT = """{
1: "original",
2: "updated"}""".replace('\n','')

US23_DICT = """{
3:"Voyager 1 iota Her C ring egress",
2:"Saturn delta Sco ingress"}""".replace('\n','')

description_and_icon_by_regex = translator.TranslatorByRegex([
    (r'.*/VG_2803/S_RINGS',         0, ('Voyager 1 RSS Ring Occultation at Saturn',     'SERIESDIR')),
    (r'.*/VG_2803/U_RINGS',         0, ('Voyager 2 RSS Ring Occultation at Uranus',     'SERIESDIR')),
    (r'.*/VG_2803/.*/LOWDATA',      0, ('Low-level opacity/phase data',                 'SERIESDIR')),
    (r'.*/VG_2803/.*/EDITDATA',     0, ('Data as complex transmissivities',             'SERIESDIR')),
    (r'.*/VG_280[12]/EDITDATA',     0, ('Raw data with anomalies identifed',            'SERIESDIR')),

    (r'.*/EASYDATA',                0, ('Easy-to-use calibrated ring profiles',         'SERIESDIR')),
    (r'.*/CALIB',                   0, ('Calibration models',                           'DATADIR'  )),
    (r'.*/NOISDATA',                0, ('Stellar background data',                      'DATADIR'  )),
    (r'.*/RAWDATA',                 0, ('Raw data',                                     'DATADIR'  )),
    (r'.*/SORCDATA',                0, ('Source data as received by Node',              'DATADIR'  )),
    (r'.*/SORCDATA/.*\.(TAB|DAT|GS3|SCO|SGR|LIS|VOY)',
                                    0, ('Source data as received by Node',              'DATA'     )),
    (r'.*/SORCDATA/SIGSGR2\.TXT',   0, ('Source data as received by Node',              'DATA'     )),

    (r'.*/GEOMETRY',                0, ('Ring intercept geomemtry',                     'GEOMDIR'  )),
    (r'.*/JITTER',                  0, ('Pointing variation data',                      'GEOMDIR'  )),
    (r'.*/TRAJECT',                 0, ('Trajectory data',                              'GEOMDIR'  )),
    (r'.*/VECTORS',                 0, ('Vector position files',                        'GEOMDIR'  )),
    (r'.*/VECTORS/B1950',           0, ('B1950 geometry reconstruction',                'GEOMDIR'  )),
    (r'.*/VECTORS/J2000',           0, ('J2000 geometry reconstruction',                'GEOMDIR'  )),
    (r'.*/VECTORS/RINGANOM',        0, ('Inclined ring coordinates',                    'GEOMDIR'  )),

    (r'.*/FOVMAPS',                 0, ('Field-of-view maps',                           'IMAGEDIR' )),
    (r'.*/VG_280[12]/IMAGES',       0, ('Star reference images',                        'IMAGEDIR' )),
    (r'.*/ANNOTATED',               0, ('TIFF images with annotations',                 'BROWDIR'  )),
    (r'.*/CLEANED',                 0, ('Cleaned images',                               'IMAGEDIR' )),
    (r'.*/GEOMED',                  0, ('Calibrated, de-distorted images',              'IMAGEDIR' )),
    (r'.*/GEOMTIFF',                0, ('TIFFs of GEOMED images',                       'BROWDIR'  )),
    (r'.*/RAW',                     0, ('Raw Voyager images',                           'IMAGEDIR' )),
    (r'.*/RAWTIFF',                 0, ('TIFFs of RAW images',                          'BROWDIR'  )),
    (r'.*/SCANS',                   0, ('Ring profiles from single images',             'SERIESDIR')),
    (r'.*/SOURCE',                  0, ('Compressed EDR images',                        'IMAGEDIR' )),
    (r'.*/C\d{7}_ANNOTATED.TIF',    0, ('TIFF Image with annotations',                  'BROWSE'   )),
    (r'.*/C\d{7}_CLEANED.IMG',      0, ('Cleaned image, VICAR',                         'IMAGE'    )),
    (r'.*/C\d{7}_GEOMED.IMG',       0, ('Calibrated, de-distorted image, VICAR',        'IMAGE'    )),
    (r'.*/C\d{7}_GEOMED.TIF',       0, ('TIFF of calibrated, de-distorted image',       'IMAGE'    )),
    (r'.*/C\d{7}_RAW.IMG',          0, ('Raw image, VICAR',                             'IMAGE'    )),
    (r'.*/C\d{7}_RAW.TIF',          0, ('TIFF of raw image',                            'IMAGE'    )),
    (r'.*/C\d{7}.IMQ',              0, ('Compressed Voyager ISS EDR',                   'IMAGE'    )),
    (r'.*/C\d{7}_SCAN.TAB',         0, ('Radial scan from one image',                   'SERIES'   )),
    (r'.*/IS(1|2)_\w+_IMAGES',      0, (r'Voyager \1 source images',                    'IMAGEDIR')),

    (r'.*/KM0+_(\d+)',              0, (r'Ring profiles, 0.\1 km sampling',             'SERIESDIR')),
    (r'.*/KM0*(\d+)',               0, (r'Ring profiles, \1 km sampling',               'SERIESDIR')),
    (r'.*/KM0*(\d+)_(\d+)*',        0, (r'Ring profiles, \1.\2 km sampling',            'SERIESDIR')),
    (r'.*/FILTER01',                0, (r'Ring profiles at full resolution',            'SERIESDIR')),
    (r'.*/FILTER0\d',               0, (r'Sub-sampled ring profiles',                   'SERIESDIR')),

    (r'.*/[PU]N1C..A\.TAB',         0, (r'Neptune Adams ring calibration model',        'SERIES')),
    (r'.*/[PU]N1C..L\.TAB',         0, (r'Neptune LeVerrier ring calibration model',    'SERIES')),

    (r'.*/[PU]N1P..\.TAB',          0, (r'Neptune sigma Sgr ring profile',                    'SERIES')),
    (r'.*/[PU]N1P..04\.TAB',        0, (r'Neptune sigma Sgr ring profile, 42,500-50,000 km',  'SERIES')),
    (r'.*/[PU]N1P..07\.TAB',        0, (r'Neptune sigma Sgr ring profile, 70,000-76,000 km',  'SERIES')),
    (r'.*/[PU]N1P..0(\d)\.TAB',     0, (r'Neptune sigma Sgr ring profile, \g<1>0,000-' + NEXT + r'[\1]0,000 km', 'SERIES')),
    (r'.*/[PU]S1P..\.TAB',          0, (r'Saturn delta Sco ring profile',                     'SERIES')),
    (r'.*/[PU]S1P..07\.TAB',        0, (r'Saturn delta Sco ring profile, 72,000-80,000 km',   'SERIES')),
    (r'.*/[PU]S1P..14\.TAB',        0, (r'Saturn delta Sco ring profile, 140,000-142,500 km', 'SERIES')),
    (r'.*/[PU]S1P..0*(\d+)\.TAB',   0, (r'Saturn delta Sco ring profile, \g<1>0,000-' + NEXT + r'[\1]0,000 km', 'SERIES')),
    (r'.*/[PU]S1P..\.TAB',          0, (r'Saturn delta Sco ring profile',                     'SERIES')),

    (r'.*/[PU](U[12])P..X(I|E)\.(TAB|DAT)', 0,
            (SUN_DICT   + r'["\1"]' +
             IE_DICT    + r'["\2"] profile for the equator plane', 'SERIES')),
    (r'.*/[PU](U1|U2)P..([654ABNGDLE])(I|E)\.(TAB|DAT)', 0,
            (SUN_DICT   + r'["\1"]' +
             IE_DICT    + r'["\3"] profile for ring ' +
             URING_DICT + r'["\2"]',                        'SERIES')),
    (r'.*/PS2([CDGR])\w+\.(TAB|DAT)', 0,
            (KIND_UC +  r'["\1"] for the Saturn ring occultation, ' +
            'low-rate extension',                           ICON + r'["\1"]')),
    (r'.*/P(S|U)[3-9](D|R)\w+\.(TAB|DAT)', 0,
            ('Un-occulted star ' +
             KIND    + r'["\2"] from the ' +
             SU_DICT + r'["\1"] flyby',                     'SERIES')),
    (r'.*/FILTER01/[PU](U[12])(F)..([654ABNGDLE])(I|E)\.(TAB|DAT)', 0,
            ('Full-resolution profiles for the ' +
             SUN_DICT   + r'["\1"] occultation, ring ' +
             URING_DICT + r'["\3"]' +
             IE_DICT    + r'["\4"]',                        'SERIES')),
    (r'.*/[PU](U[12])(V)([CER])(1)([654ABNGDLE])(I|E)\.(TAB|DAT)', 0,
            ('Vectors for the ' +
             SUN_DICT   + r'["\1"] occultation, ring ' +
             URING_DICT + r'["\5"]' +
             IE_DICT    + r'["\6"], ' +
             COORD_DICT + r'["\3"] coordinates',            ICON + r'["\2"]')),
    (r'.*/[PU](U[12])([CDFGJNRTVW])..([654ABNGDLE])(I|E)\.(TAB|DAT)', 0,
            (KIND_UC    + r'["\2"] for the ' +
             SUN_DICT   + r'["\1"] occultation, ring ' +
             URING_DICT + r'["\3"]' +
             IE_DICT    + r'["\4"]',                        ICON + r'["\2"]')),
    (r'.*/FILTER01/[PU]([SN]1|U[12])(F)\w+\.(TAB|DAT)', 0,
            ('Full-resolution profiles for the ' +
             SUN_DICT   + r'["\1"] ring occultation',       'SERIES')),
    (r'.*/[PU]([SN]1|U[12])(V)([CER])([12])\.(TAB|DAT)', 0,
            ('Vectors for the ' +
             SUN_DICT   + r'["\1"] ring occultation, ' +
             COORD_DICT + r'["\3"] coordinates, ' +
             POLE_DICT  + r'[\4] pole',                     'GEOM')),
    (r'.*/[PU]([SN]1|U[12])([CDFGJNRTVW])\w+\.(TAB|DAT)', 0,
            (KIND_UC    + r'["\2"] for the ' +
             SUN_DICT   + r'["\1"] ring occultation',       ICON + r'["\2"]')),

    (r'.*/US(2|3)(V)([CER])([12]).(DAT|TAB)', 0,
            ('Vectors for the ' +
             US23_DICT  + r'[\1], ' +
             COORD_DICT + r'["\3"] coordinates, ' +
             POLE_DICT  + r'[\4] pole',                     'GEOM')),
    (r'.*/US(2|3)([CDFGJNRTVW])\w+\.(DAT|TAB)', 0,
            (KIND_UC + r'["\2"] for the ' +
             US23_DICT + r'[\1]',                           ICON + r'["\2"]')),

    (r'.*/RS(\d)P(1|2)(S|X)14\.TAB', 0,
            (r'\3-band profile, ' +
             SRSS_DICT  + r'[\1] inversion, ' +
             POLE_DICT + r'[\2] pole, 140,000-145,000 km, ','SERIES')),
    (r'.*/RS(\d)P(1|2)(S|X)0*(\d+)\.TAB', 0,
            (r'\3-band profile, ' +
             SRSS_DICT  + r'[\1] inversion, ' +
             POLE_DICT  + r'[\2] pole, \g<1>0,000-' +
             NEXT       + r'[\4]0,000 km',                  'SERIES')),
    (r'.*/RS(\d)P(1|2)(S|X)\.TAB', 0,
            (r'\3-band profile, ' +
             SRSS_DICT  + r'[\1] inversion, ' +
             POLE_DICT  + r'[\2] pole',                     'SERIES')),
    (r'.*/RS(\d)D.(S|X)(C|U)([VIP])\.(TAB|DAT)', 0,
            (r'\2-band data, ' +
             CU_DICT    + r'["\3"] for diffraction, ' +
             SRSS_DICT  + r'[\1] inversion, ' +
             VIP_DICT   + r'["\4"] binary',                 'SERIES')),
    (r'.*/RS0G(1|2)B\.TAB', 0,
            (r'Geometry model, ' +
             POLE_DICT + r'[\1] Saturn pole',               'GEOM')),
    (r'.*/RS(\d)C1(S|X)\.TAB', 0,
            (r'\2-band calibration model, ' +
             SRSS_DICT + r'[\1] inversion',                 'SERIES')),
    (r'.*/RS(\d)R1B([12DFH])([VIP])\.DAT', 0,
            (r'Low-level data from ' +
             SRSS_DICT + r'[\1] inversion, ' +
             VIP_DICT  + r'["\3"] binary',                  'SERIES')),
    (r'.*/RS(\d)R1B([12DFH])T\.TXT', 0,
            (r'Low-level data from ' +
             SRSS_DICT + r'[\1] inversion, ASCII text',     'INFO')),
    (r'.*/RS(\d)R1B([12DFH])T\.TAB', 0,
            (r'Low-level data from ' +
             SRSS_DICT + r'[\1] inversion, ASCII table',    'TABLE')),
    (r'.*/RS(\d)S1B(\d)\.DAT', 0,
            (r'File \2 tape dump from ' +
             SRSS_DICT + r'[\1] inversion',                 'DATA')),

    (r'.*/RU(\d)P1(S|X)([654ABNGDLE])(I|E)\.TAB', 0,
            (r'\2-band profile of ring ' +
             URING_DICT + r'["\3"]' +
             IE_DICT    + r'["\4"], ' +
             URSS_DICT  + r'[\1] inversion',                'SERIES')),
    (r'.*/RU(\d)P2(S|X)([654ABNGDLE])(I|E)\.TAB', 0,
            (r'\2-band profile of ring ' +
             URING_DICT + r'["\3"]' +
             IE_DICT    + r'["\4"], ' +
             URSS_DICT  + r'[\1] inversion, resampled',     'SERIES')),
    (r'.*/RU0G(1|2)B([654ABNGDLE])(I|E)\.TAB', 0,
            (r'Geometry model for ring ' +
             URING_DICT + r'["\2"]' +
             IE_DICT    + r'["\3"], ' +
             POLE_DICT  + r'[\1] Uranus pole',              'GEOM')),
    (r'.*/RU(\d)C1(X|S)\.TAB', 0,
            (r'\2-band calibration model for ' +
             URSS_DICT  + r'[\1] inversion',                'SERIES')),
    (r'.*/RU(\d)D(1|2)(X|S)([654ABNGDLE])(I|E)\.TAB', 0,
            (r'\3-band complex transmissivities for ring ' +
             URING_DICT + r'["\4"]' +
             IE_DICT    + r'["\5"], ' +
             URSS_DICT  + r'[\1] inversion, ' +
             POLE_DICT  + r'[\2] pole',                     'SERIES')),
    (r'.*/RU(\d)R(1|2)(X|S)([654ABNGDLE])(I|E)\.TAB', 0,
            (r'\3-band amplitude/phase data for ring ' +
             URING_DICT + r'["\4"]' +
             IE_DICT    + r'["\5"], ' +
             URSS_DICT  + r'[\1] inversion, ' +
             POLE_DICT  + r'[\2] pole',                     'SERIES')),
    (r'.*/RU(\d)S1(X|S)([654ABNGDLE])(I|E)\.TXT', 0,
            (r'\2-band source data file for ring ' +
             URING_DICT + r'["\3"]' +
             IE_DICT    + r'["\4"], ' +
             URSS_DICT  + r'[\1] inversion',                'SERIES')),

    (r'.*/IS(1|2)_\w+_KM0*(\d+)\.TAB', 0,
            (r'Voyager \1 ring profile, \2-km sampling',    'SERIES')),
])

##########################################################################################
# VIEWABLES
##########################################################################################

default_viewables = translator.TranslatorByRegex([
    (r'.*/VG_28xx(|_v[0-9\.]+)/(VG_280[12])/EASYDATA/\w+/([PU][NS][123]).*', 0,
            [r'diagrams/VG_28xx/\2/\3xxx_diagram_full.png',
             r'diagrams/VG_28xx/\2/\3xxx_diagram_med.png',
             r'diagrams/VG_28xx/\2/\3xxx_diagram_small.png',
             r'diagrams/VG_28xx/\2/\3xxx_diagram_thumb.png',
             r'previews/VG_28xx/\2/\3xxx_preview_full.png',
             r'previews/VG_28xx/\2/\3xxx_preview_med.png',
             r'previews/VG_28xx/\2/\3xxx_preview_small.png',
             r'previews/VG_28xx/\2/\3xxx_preview_thumb.png',
            ]),
    (r'.*/VG_28xx(|_v[0-9\.]+)/(VG_280[12])/EASYDATA/\w+/([PU]U[12])...(\w[IE]).*', 0,
            [r'diagrams/VG_28xx/\2/\3xxx\4_diagram_full.png',
             r'diagrams/VG_28xx/\2/\3xxx\4_diagram_med.png',
             r'diagrams/VG_28xx/\2/\3xxx\4_diagram_small.png',
             r'diagrams/VG_28xx/\2/\3xxx\4_diagram_thumb.png',
             r'previews/VG_28xx/\2/\3xxx\4_preview_full.png',
             r'previews/VG_28xx/\2/\3xxx\4_preview_med.png',
             r'previews/VG_28xx/\2/\3xxx\4_preview_small.png',
             r'previews/VG_28xx/\2/\3xxx\4_preview_thumb.png',
            ]),
    (r'.*/VG_28xx(|_v[0-9\.]+)/(VG_2803)/[SU]_RINGS/EASYDATA/\w+/(RS)...([SX]).*', 0,
            [r'diagrams/VG_28xx/\2/\3xxx\4_diagram_full.png',
             r'diagrams/VG_28xx/\2/\3xxx\4_diagram_med.png',
             r'diagrams/VG_28xx/\2/\3xxx\4_diagram_small.png',
             r'diagrams/VG_28xx/\2/\3xxx\4_diagram_thumb.png',
             r'previews/VG_28xx/\2/\3xxx\4_preview_full.png',
             r'previews/VG_28xx/\2/\3xxx\4_preview_med.png',
             r'previews/VG_28xx/\2/\3xxx\4_preview_small.png',
             r'previews/VG_28xx/\2/\3xxx\4_preview_thumb.png',
            ]),
    (r'.*/VG_28xx(|_v[0-9\.]+)/(VG_2803)/[SU]_RINGS/EASYDATA/\w+/(RU)...([SX]\w[IE]).*', 0,
            [r'diagrams/VG_28xx/\2/\3xxx\4_diagram_full.png',
             r'diagrams/VG_28xx/\2/\3xxx\4_diagram_med.png',
             r'diagrams/VG_28xx/\2/\3xxx\4_diagram_small.png',
             r'diagrams/VG_28xx/\2/\3xxx\4_diagram_thumb.png',
             r'previews/VG_28xx/\2/\3xxx\4_preview_full.png',
             r'previews/VG_28xx/\2/\3xxx\4_preview_med.png',
             r'previews/VG_28xx/\2/\3xxx\4_preview_small.png',
             r'previews/VG_28xx/\2/\3xxx\4_preview_thumb.png',
            ]),
    (r'.*/VG_28xx(|_v[0-9\.]+)/(VG_2810)/DATA/(IS[12]_P0001).*', 0,
            [r'diagrams/VG_28xx/\2/\3_diagram_full.png',
             r'diagrams/VG_28xx/\2/\3_diagram_med.png',
             r'diagrams/VG_28xx/\2/\3_diagram_small.png',
             r'diagrams/VG_28xx/\2/\3_diagram_thumb.png',
             r'previews/VG_28xx/\2/\3_preview_full.png',
             r'previews/VG_28xx/\2/\3_preview_med.png',
             r'previews/VG_28xx/\2/\3_preview_small.png',
             r'previews/VG_28xx/\2/\3_preview_thumb.png',
            ]),
])

##########################################################################################
# ASSOCIATIONS
##########################################################################################

associations_to_volumes = translator.TranslatorByRegex([

    (r'volumes/VG_28xx/VG_2801/[^D].*/P([SUN]\d)[A-Z]\d\d(\w*)\.\w+', 0,
            [r'volumes/VG_28xx/VG_2801/[^D]*/P\1???\2.*',
             r'volumes/VG_28xx/VG_2801/[^D]*/*/P\1???\2.*',
            ]),
    (r'volumes/VG_28xx/VG_2801/[^D].*/P([SUN]\d)[A-Z]\d\d(\d\d)\.\w+', 0,
            [r'volumes/VG_28xx/VG_2801/[^D]*/P\1???.*',
             r'volumes/VG_28xx/VG_2801/[^D]*/*/P\1???.*',
            ]),
    (r'volumes/VG_28xx/VG_2801/[^D].*/P([SUN]\d)[A-Z]\d\d\.\w+', 0,
            [r'volumes/VG_28xx/VG_2801/[^D]*/P\1???[01][0-9].*',
             r'volumes/VG_28xx/VG_2801/[^D]*/*/P\1???[01][0-9].*',
            ]),
    (r'volumes/VG_28xx/VG_2801/[^D].*/P(U\d)[A-Z]\d\d([A-Z][IE]?)\.\w+', 0,
            [r'volumes/VG_28xx/VG_2801/[^D]*/P\1???.*',
             r'volumes/VG_28xx/VG_2801/[^D]*/*/P\1???.*',
            ]),
    (r'volumes/VG_28xx/VG_2801/[^D].*/P([SUN]\d)[A-Z]\d\d\.\w+', 0,
            [r'volumes/VG_28xx/VG_2801/[^D]*/P\1\2???[A-Z][IE].*',
             r'volumes/VG_28xx/VG_2801/[^D]*/P\1\2???[A-Z].*',
            ]),

    (r'volumes/VG_28xx/VG_2802/[^D].*/U([SUN]\d)[A-Z]\d\d(\w*)\.\w+', 0,
            [r'volumes/VG_28xx/VG_2802/[^D]*/U\1???\2.*',
             r'volumes/VG_28xx/VG_2802/[^D]*/*/U\1???\2.*',
            ]),
    (r'volumes/VG_28xx/VG_2802/[^D].*/U(U\d)[A-Z]\d\d([A-Z][IE]?)\.\w+', 0,
            [r'volumes/VG_28xx/VG_2802/[^D]*/U\1???.*',
             r'volumes/VG_28xx/VG_2802/[^D]*/*/U\1???.*',
            ]),
    (r'volumes/VG_28xx/VG_2802/[^D].*/U(U\d)[A-Z]\d\d\.\w+', 0,
            [r'volumes/VG_28xx/VG_2802/[^D]*/U\1???[A-Z][IE].*',
             r'volumes/VG_28xx/VG_2802/[^D]*/U\1???[A-Z].*',
            ]),

    (r'volumes/VG_28xx(|_v[\d\.]+)/VG_2803/([SU]_RINGS)/\w+(|/\w+)/(R[SU]\d)[A-Z]\d(S|U)(\w+)\.\w+', 0,
            [r'volumes/VG_28xx\1/VG_2803/\2/*/\4..\5\6.*',
             r'volumes/VG_28xx\1/VG_2803/\2/*/*/\4..\5\6.*',
            ]),
    (r'volumes/VG_28xx(|_v[\d\.]+)/VG_2803/([SU]_RINGS)/\w+(|/\w+)/(R[SU]\d)[A-Z]\d(S|U)\.\w+', 0,
            [r'volumes/VG_28xx\1/VG_2803/\2/*/\4..\5*.*',
             r'volumes/VG_28xx\1/VG_2803/\2/*/*/\4..\5*.*',
            ]),
    (r'volumes/VG_28xx(|_v[\d\.]+)/VG_2803/([SU]_RINGS)/\w+(|/\w+)/(R[SU]\d)[A-Z]\d(S|U)(\w+)\.\w+', 0,
            [r'volumes/VG_28xx\1/VG_2803/\2/*/\4..\5.*',
             r'volumes/VG_28xx\1/VG_2803/\2/*/*/\4..\5.*',
            ]),
])

associations_to_metadata = translator.TranslatorByRegex([
    (r'volumes/VG_28xx(|_v[\d\.]+)/(VG_28..)/[^D].*/([PUR][SUN]\d[A-Z]\d[SX\d]\w*)\.(TAB|DAT|LBL)', 0,
            r'metadata/VG_28xx\1/\2/*.TAB\3'),
])

associations_to_documents = translator.TranslatorByRegex([
    (r'volumes/VG_28xx(|_v[\d\.]+)/(VG_28..)/\w+/.+', 0,
            r'volumes/VG_28xx\1/\2/DOCUMENT/TUTORIAL.TXT'),
])

##########################################################################################
# VERSIONS
##########################################################################################

versions = translator.TranslatorByRegex([
    (r'volumes/VG_28xx(|_v[\d\.]+)/VG_2803/([US]_RINGS)/[LR][OA]WDATA(|/.*)',
            [r'volumes/VG_28xx*/VG_2803/\2/LOWDATA\3',
             r'volumes/VG_28xx*/VG_2803/\2/RAWDATA\3',
            ]),
    (r'volumes/VG_28xx(|_v[\d\.]+)/VG_2803/DOCUMENT/CAL\w+/S\w+DATA(|/.*)',
            [r'volumes/VG_28xx*/VG_2803/DOCUMENT/CALDOC/SCALDATA\2',
             r'volumes/VG_28xx*/VG_2803/DOCUMENT/CALIB/SDATA\2',
            ]),
    (r'volumes/VG_28xx(|_v[\d\.]+)/VG_2803/DOCUMENT/CAL\w+(|/.*)',
            [r'volumes/VG_28xx*/VG_2803/DOCUMENT/CALDOC\2',
             r'volumes/VG_28xx*/VG_2803/DOCUMENT/CALIB\2',
            ]),
    (r'volumes/VG_28xx(|_v[\d\.]+)/VG_2803/DOCUMENT/GEO\w+/(U|S)\w+DATA(|/.*)',
            [r'volumes/VG_28xx*/VG_2803/DOCUMENT/GEODOC/\2GEODATA\3',
             r'volumes/VG_28xx*/VG_2803/DOCUMENT/GEOMETRY/\2DATA\3',
            ]),
    (r'volumes/VG_28xx(|_v[\d\.]+)/VG_2803/DOCUMENT/GEO\w+(|/.*)',
            [r'volumes/VG_28xx*/VG_2803/DOCUMENT/GEODOC\2',
             r'volumes/VG_28xx*/VG_2803/DOCUMENT/GEOMETRY\2',
            ]),
])

##########################################################################################
# OPUS_FORMAT
##########################################################################################

opus_format = translator.TranslatorByRegex([
    (r'.*\.IMG', 0, ('Binary', 'VICAR')),
])

##########################################################################################
# SPLIT_RULES
##########################################################################################

split_rules = translator.TranslatorByRegex([
    # VG_2810
    (r'(IS[12]_....._...)_(\w+)\.(.*)$', 0, (r'\1', r'_\2', r'.\3')),
])

##########################################################################################
# SORT_KEY
##########################################################################################

sort_key = translator.TranslatorByRegex([

    # Sort folders into increasing bin sizes
    (r'KM0*(\d\d)$',          0, r'KM0\1_000'    ),
    (r'KM0*(\d\d)_(\d)$',     0, r'KM0\1_\g<2>00'),
    (r'KM0*(\d\d)_(\d\d)$',   0, r'KM0\1_\g<2>0' ),
    (r'KM0*(\d\d)_(\d\d\d)$', 0, r'KM0\1_\g<2>'  ),
])

##########################################################################################
# OPUS_TYPE
##########################################################################################

opus_type = translator.TranslatorByRegex([
    # VG_2801
    (r'volumes/.*/VG_2801/EASYDATA/KM00(0_2/PS1|0_1/PU1|1/PU2|1/PN1).*', 0,
                                                     ('Voyager PPS', 10, 'vgpps_occ_best',  'Calibrated Profile (finest resolution)', True)),
    (r'volumes/.*/VG_2801/EASYDATA/KM00(5/PS1|2/PN1).*', 0,
                                                     ('Voyager PPS', 11, 'vgpps_occ_all',   'Calibrated Profile (overview)', True)),
    (r'volumes/.*/VG_2801/EASYDATA/KM000_2/.*',   0, ('Voyager PPS', 20, 'vgpps_occ_0_2',   'Calibrated Profile (200 m)',    False)),
    (r'volumes/.*/VG_2801/EASYDATA/KM000_5/.*',   0, ('Voyager PPS', 21, 'vgpps_occ_0_5',   'Calibrated Profile (500 m)',    False)),
    (r'volumes/.*/VG_2801/EASYDATA/KM001/.*',     0, ('Voyager PPS', 22, 'vgpps_occ_01',    'Calibrated Profile (1 km)',     False)),
    (r'volumes/.*/VG_2801/EASYDATA/KM002/.*',     0, ('Voyager PPS', 23, 'vgpps_occ_02',    'Calibrated Profile (2 km)',     False)),
    (r'volumes/.*/VG_2801/EASYDATA/KM005/.*',     0, ('Voyager PPS', 24, 'vgpps_occ_05',    'Calibrated Profile (5 km)',     False)),
    (r'volumes/.*/VG_2801/EASYDATA/KM010/.*',     0, ('Voyager PPS', 25, 'vgpps_occ_10',    'Calibrated Profile (10 km)',    False)),
    (r'volumes/.*/VG_2801/EASYDATA/KM020/.*',     0, ('Voyager PPS', 26, 'vgpps_occ_20',    'Calibrated Profile (20 km)',    False)),
    (r'volumes/.*/VG_2801/EASYDATA/KM050/.*',     0, ('Voyager PPS', 27, 'vgpps_occ_50',    'Calibrated Profile (50 km)',    False)),
    (r'volumes/.*/VG_2801/EDITDATA/P[SU][3-9].*', 0, ('Voyager PPS', 90, 'vgpps_occ_test',  'Additional Star Tests',         False)),
    (r'volumes/.*/VG_2801/EDITDATA/.*',           0, ('Voyager PPS', 30, 'vgpps_occ_raw',   'Raw Data',                      True )),
    (r'volumes/.*/VG_2801/CALIB/.*',              0, ('Voyager PPS', 40, 'vgpps_occ_cal',   'Calibration Model',             False)),
    (r'volumes/.*/VG_2801/GEOMETRY/.*',           0, ('Voyager PPS', 50, 'vgpps_occ_geo',   'Geometry Model',                False)),
    (r'volumes/.*/VG_2801/IMAGES/.*',             0, ('Voyager PPS', 60, 'vgpps_occ_img',   'Support Image',                 False)),
    (r'volumes/.*/VG_2801/JITTER/.*',             0, ('Voyager PPS', 70, 'vgpps_occ_jit',   'Jitter File',                   False)),
    (r'volumes/.*/VG_2801/VECTORS/J2000/...VC.*', 0, ('Voyager PPS', 80, 'vgpps_occ_j2000', 'Vector Tables (J2000 frame)',   False)),
    (r'volumes/.*/VG_2801/VECTORS/J2000/...VE.*', 0, ('Voyager PPS', 81, 'vgpps_occ_ring',  'Vector Tables (ring frame)',    False)),

    # VG_2802
    (r'volumes/.*/VG_2802/EASYDATA/FILTER01/.*',  0, ('Voyager UVS', 10, 'vguvs_occ_full_res',  'Calibrated Profile (full resolution)', True)),
    (r'volumes/.*/VG_2802/EASYDATA/FILTER02/.*',  0, ('Voyager UVS', 11, 'vguvs_occ_sampled_2', 'Calibrated Profile (2x subsampled)',   False)),
    (r'volumes/.*/VG_2802/EASYDATA/FILTER03/.*',  0, ('Voyager UVS', 12, 'vguvs_occ_sampled_3', 'Calibrated Profile (3x subsampled)',   False)),
    (r'volumes/.*/VG_2802/EASYDATA/FILTER04/.*',  0, ('Voyager UVS', 13, 'vguvs_occ_sampled_4', 'Calibrated Profile (4x subsampled)',   False)),
    (r'volumes/.*/VG_2802/EASYDATA/FILTER05/.*',  0, ('Voyager UVS', 14, 'vguvs_occ_sampled_5', 'Calibrated Profile (5x subsampled)',   False)),
    (r'volumes/.*/VG_2802/EASYDATA/KM000_2/.*',   0, ('Voyager UVS', 20, 'vguvs_occ_0_2',       'Calibrated Profile (200 m binned)',    False)),
    (r'volumes/.*/VG_2802/EASYDATA/KM000_5/.*',   0, ('Voyager UVS', 21, 'vguvs_occ_0_5',       'Calibrated Profile (500 m binned)',    False)),
    (r'volumes/.*/VG_2802/EASYDATA/KM001/.*',     0, ('Voyager UVS', 22, 'vguvs_occ_01',        'Calibrated Profile (1 km binned)',     False)),
    (r'volumes/.*/VG_2802/EASYDATA/KM002/.*',     0, ('Voyager UVS', 23, 'vguvs_occ_02',        'Calibrated Profile (2 km binned)',     False)),
    (r'volumes/.*/VG_2802/EASYDATA/KM005/.*',     0, ('Voyager UVS', 24, 'vguvs_occ_05',        'Calibrated Profile (5 km binned)',     False)),
    (r'volumes/.*/VG_2802/EASYDATA/KM010/.*',     0, ('Voyager UVS', 25, 'vguvs_occ_10',        'Calibrated Profile (10 km binned)',    False)),
    (r'volumes/.*/VG_2802/EASYDATA/KM020/.*',     0, ('Voyager UVS', 26, 'vguvs_occ_20',        'Calibrated Profile (20 km binned)',    False)),
    (r'volumes/.*/VG_2802/EASYDATA/KM050/.*',     0, ('Voyager UVS', 27, 'vguvs_occ_50',        'Calibrated Profile (50 km binned)',    False)),
    (r'volumes/.*/VG_2802/EDITDATA/U..D.*',       0, ('Voyager UVS', 30, 'vguvs_occ_coadd',     'Raw Coadded Spectra',         False)),
    (r'volumes/.*/VG_2802/EDITDATA/U..W..P.*',    0, ('Voyager UVS', 35, 'vguvs_occ_spec',      'Raw Spectra',                 False)),
    (r'volumes/.*/VG_2802/CALIB/.*',              0, ('Voyager UVS', 40, 'vguvs_occ_cal',       'Calibration Model',           False)),
    (r'volumes/.*/VG_2802/GEOMETRY/.*',           0, ('Voyager UVS', 50, 'vguvs_occ_geo',       'Geometry Model',              False)),
    (r'volumes/.*/VG_2802/IMAGES/.*',             0, ('Voyager UVS', 60, 'vguvs_occ_img',       'Support Image',               False)),
    (r'volumes/.*/VG_2802/VECTORS/J2000/...VC.*', 0, ('Voyager UVS', 80, 'vguvs_occ_j2000',     'Vector Tables (J2000 frame)', False)),
    (r'volumes/.*/VG_2802/VECTORS/J2000/...VE.*', 0, ('Voyager UVS', 81, 'vguvs_occ_ring',      'Vector Tables (ring frame)',  False)),

    # VG_2803
    (r'volumes/.*/VG_2803/U_RINGS/EASYDATA/KM00_025/RU1P1.*', 0, ('Voyager RSS', 10, 'vgrss_occ_inv0_05',   '50 m inversion, old pole', True )),
    (r'volumes/.*/VG_2803/U_RINGS/EASYDATA/KM00_025/RU2P1.*', 0, ('Voyager RSS', 11, 'vgrss_occ_inv0_2',   '200 m inversion, old pole', True )),
    (r'volumes/.*/VG_2803/U_RINGS/EASYDATA/KM00_05/RU3P1.*',  0, ('Voyager RSS', 12, 'vgrss_occ_inv0_2',   '200 m inversion, old pole', True )),
    (r'volumes/.*/VG_2803/U_RINGS/EASYDATA/KM00_25/RU4P1.*',  0, ('Voyager RSS', 13, 'vgrss_occ_inv0_5',   '500 m inversion, old pole', True )),
    (r'volumes/.*/VG_2803/U_RINGS/EASYDATA/KM00_05/RU5P1.*',  0, ('Voyager RSS', 14, 'vgrss_occ_inv01',     '1 km inversion, old pole', True )),

    (r'volumes/.*/VG_2803/S_RINGS/EASYDATA/KM000_2/RS1P1.*',  0, ('Voyager RSS', 10, 'vgrss_occ_inv0_4',   '400 m inversion, old pole', True )),
    (r'volumes/.*/VG_2803/S_RINGS/EASYDATA/KM000_5/RS3P1.*',  0, ('Voyager RSS', 11, 'vgrss_occ_inv01',     '1 km inversion, old pole', True )),
    (r'volumes/.*/VG_2803/S_RINGS/EASYDATA/KM002_5/RS4P1.*',  0, ('Voyager RSS', 12, 'vgrss_occ_inv05',     '5 km inversion, old pole', True )),

    (r'volumes/.*/VG_2803/._RINGS/EASYDATA/KM0+_025/R.*',     0, ('Voyager RSS', 20, 'vgrss_occ_sam0_025',  '25 m resampled, new pole', False)),
    (r'volumes/.*/VG_2803/._RINGS/EASYDATA/KM0+_05/R.*',      0, ('Voyager RSS', 21, 'vgrss_occ_sam0_05',   '50 m resampled, new pole', False)),
    (r'volumes/.*/VG_2803/._RINGS/EASYDATA/KM0+_1/R.*',       0, ('Voyager RSS', 22, 'vgrss_occ_sam0_1',   '100 m resampled, new pole', False)),
    (r'volumes/.*/VG_2803/._RINGS/EASYDATA/KM0+_2/R.*',       0, ('Voyager RSS', 23, 'vgrss_occ_sam0_2',   '200 m resampled, new pole', False)),
    (r'volumes/.*/VG_2803/._RINGS/EASYDATA/KM0+_25/R.*',      0, ('Voyager RSS', 24, 'vgrss_occ_sam0_25',  '250 m resampled, new pole', False)),
    (r'volumes/.*/VG_2803/._RINGS/EASYDATA/KM0+_5/R.*',       0, ('Voyager RSS', 25, 'vgrss_occ_sam0_5',   '500 m resampled, new pole', False)),
    (r'volumes/.*/VG_2803/._RINGS/EASYDATA/KM0+1/R.*',        0, ('Voyager RSS', 26, 'vgrss_occ_sam01',     '1 km resampled, new pole', False)),
    (r'volumes/.*/VG_2803/._RINGS/EASYDATA/KM0+2/R.*',        0, ('Voyager RSS', 27, 'vgrss_occ_sam02',     '2 km resampled, new pole', False)),
    (r'volumes/.*/VG_2803/._RINGS/EASYDATA/KM0+2_5/R.*',      0, ('Voyager RSS', 28, 'vgrss_occ_sam02_5', '2.5 km resampled, new pole', False)),
    (r'volumes/.*/VG_2803/._RINGS/EASYDATA/KM0+5/R.*',        0, ('Voyager RSS', 29, 'vgrss_occ_sam05',     '5 km resampled, new pole', False)),
    (r'volumes/.*/VG_2803/._RINGS/EASYDATA/KM0*10/R.*',       0, ('Voyager RSS', 30, 'vgrss_occ_sam10',    '10 km resampled, new pole', False)),
    (r'volumes/.*/VG_2803/._RINGS/EASYDATA/KM0*20/R.*',       0, ('Voyager RSS', 31, 'vgrss_occ_sam20',    '20 km resampled, new pole', False)),
    (r'volumes/.*/VG_2803/._RINGS/EASYDATA/KM0*50/R.*',       0, ('Voyager RSS', 32, 'vgrss_occ_sam50',    '50 km resampled, new pole', False)),

    # VG_2810
    (r'volumes/.*/VG_2810/DATA/.*KM002\.(TAB|LBL)', 0, ('Voyager ISS', 10, 'vgiss_prof_02',      'Intensity Profile (2 km)',   True)),
    (r'volumes/.*/VG_2810/DATA/.*KM004\.(TAB|LBL)', 0, ('Voyager ISS', 11, 'vgiss_prof_04',      'Intensity Profile (4 km)',   True)),
    (r'volumes/.*/VG_2810/DATA/.*KM010\.(TAB|LBL)', 0, ('Voyager ISS', 12, 'vgiss_prof_10',      'Intensity Profile (10 km)',  True)),
    (r'volumes/.*/VG_2810/DATA/.*KM020\.(TAB|LBL)', 0, ('Voyager ISS', 13, 'vgiss_prof_20',      'Intensity Profile (20 km)',  True)),
    (r'volumes/.*/VG_2810/DATA/\w+/ANNOTATED/.+',   0, ('Voyager ISS', 20, 'vgiss_prof_img_ann', 'Source Images (annotated)',  False)),
    (r'volumes/.*/VG_2810/DATA/\w+/RAW.*/.+',       0, ('Voyager ISS', 21, 'vgiss_prof_img_raw', 'Source Images (raw)',        False)),
    (r'volumes/.*/VG_2810/DATA/\w+/GEOM.*/.+',      0, ('Voyager ISS', 20, 'vgiss_prof_img_cal', 'Source Images (calibrated)', False)),
])

##########################################################################################
# OPUS_PRODUCTS
##########################################################################################

# Use of explicit file names means we don't need to invoke glob.glob(); this goes much faster
opus_products = translator.TranslatorByRegex([
    # VG_2801
    (r'.*/VG_28xx/(VG_2801)/.*/(PS[12]).*', 0,
            [r'volumes/VG_28xx/\1/EASYDATA/KM*/\2*',            # all resolutions
             r'volumes/VG_28xx/\1/CALIB/\2C01.TAB',
             r'volumes/VG_28xx/\1/CALIB/\2C01.LBL',
             r'volumes/VG_28xx/\1/GEOMETRY/\2G02.TAB',
             r'volumes/VG_28xx/\1/GEOMETRY/\2G02.LBL',
             r'volumes/VG_28xx/\1/JITTER/\2J02.TAB',
             r'volumes/VG_28xx/\1/JITTER/\2J02.LBL',
             r'volumes/VG_28xx/\1/EDITDATA/PS[3-9]*',
             r'volumes/VG_28xx/\1/IMAGES/C4400349.IMG',
             r'volumes/VG_28xx/\1/IMAGES/C4400349.LBL',
             r'volumes/VG_28xx/\1/VECTORS/J2000/\2VC2.TAB',
             r'volumes/VG_28xx/\1/VECTORS/J2000/\2VC2.LBL',
             r'volumes/VG_28xx/\1/VECTORS/J2000/\2VE2.TAB',
             r'volumes/VG_28xx/\1/VECTORS/J2000/\2VE2.LBL',
             r'diagrams/VG_28xx/\1/\2xxx_diagram_full.png',
             r'diagrams/VG_28xx/\1/\2xxx_diagram_med.png',
             r'diagrams/VG_28xx/\1/\2xxx_diagram_small.png',
             r'diagrams/VG_28xx/\1/\2xxx_diagram_thumb.png',
             r'previews/VG_28xx/\1/\2xxx_preview_full.png',
             r'previews/VG_28xx/\1/\2xxx_preview_med.png',
             r'previews/VG_28xx/\1/\2xxx_preview_small.png',
             r'previews/VG_28xx/\1/\2xxx_preview_thumb.png',
            ]),
    (r'.*/VG_28xx/(VG_2801)/.*/(PS2).*', 0,
            [r'volumes/VG_28xx/\1/GEOMETRY/\2G01.TAB',
             r'volumes/VG_28xx/\1/GEOMETRY/\2G01.LBL',
             r'volumes/VG_28xx/\1/VECTORS/J2000/PS1VC2.TAB',
             r'volumes/VG_28xx/\1/VECTORS/J2000/PS1VC2.LBL',
             r'volumes/VG_28xx/\1/VECTORS/J2000/PS1VE2.TAB',
             r'volumes/VG_28xx/\1/VECTORS/J2000/PS1VE2.LBL',
            ]),
    (r'.*/VG_28xx/(VG_2801)/.*/(PU[12]).*([654ABNGDLEX][IE])\..*', 0,
            [r'volumes/VG_28xx/\1/EASYDATA/KM*/\2*\3.*',        # all resolutions
             r'volumes/VG_28xx/\1/CALIB/\2C01\3.TAB',
             r'volumes/VG_28xx/\1/CALIB/\2C01\3.LBL',
             r'volumes/VG_28xx/\1/EDITDATA/PU[3-9]*',
             r'volumes/VG_28xx/\1/GEOMETRY/\2G01\3.TAB',
             r'volumes/VG_28xx/\1/GEOMETRY/\2G01\3.LBL',
             r'volumes/VG_28xx/\1/VECTORS/J2000/\2VC1\3.TAB',
             r'volumes/VG_28xx/\1/VECTORS/J2000/\2VC1\3.LBL',
             r'volumes/VG_28xx/\1/VECTORS/J2000/\2VE1\3.TAB',
             r'volumes/VG_28xx/\1/VECTORS/J2000/\2VE1\3.LBL',
             r'diagrams/VG_28xx/\1/\2xxx\3_diagram_full.png',
             r'diagrams/VG_28xx/\1/\2xxx\3_diagram_med.png',
             r'diagrams/VG_28xx/\1/\2xxx\3_diagram_small.png',
             r'diagrams/VG_28xx/\1/\2xxx\3_diagram_thumb.png',
             r'previews/VG_28xx/\1/\2xxx\3_preview_full.png',
             r'previews/VG_28xx/\1/\2xxx\3_preview_med.png',
             r'previews/VG_28xx/\1/\2xxx\3_preview_small.png',
             r'previews/VG_28xx/\1/\2xxx\3_preview_thumb.png',
            ]),
    (r'.*/VG_28xx/(VG_2801)/.*/(PU[12]).*(X[IE])\..*', 0,       # ring-plane geometry uses no suffix
            [r'volumes/VG_28xx/\1/GEOMETRY/\2G01.TAB',
             r'volumes/VG_28xx/\1/GEOMETRY/\2G01.LBL',
             r'volumes/VG_28xx/\1/VECTORS/J2000/\2VC1.TAB',
             r'volumes/VG_28xx/\1/VECTORS/J2000/\2VC1.LBL',
             r'volumes/VG_28xx/\1/VECTORS/J2000/\2VE1.TAB',
             r'volumes/VG_28xx/\1/VECTORS/J2000/\2VE1.LBL',
            ]),
    (r'.*/VG_28xx/(VG_2801)/.*/(PU1).*', 0,
            [r'volumes/VG_28xx/\1/JITTER/\2J01.TAB',
             r'volumes/VG_28xx/\1/JITTER/\2J01.LBL',
             r'volumes/VG_28xx/\1/IMAGES/C2683058.IMG',
             r'volumes/VG_28xx/\1/IMAGES/C2683058.LBL',
            ]),
    (r'.*/VG_28xx/(VG_2801)/.*/(PU2).*', 0,
            [r'volumes/VG_28xx/\1/JITTER/\2J02.TAB',
             r'volumes/VG_28xx/\1/JITTER/\2J02.LBL',
             r'volumes/VG_28xx/\1/IMAGES/C2684902.IMG',
             r'volumes/VG_28xx/\1/IMAGES/C2684902.LBL',
            ]),
    (r'.*/VG_28xx/(VG_2801)/.*/(PN1).*', 0,
            [r'volumes/VG_28xx/\1/EASYDATA/KM*/\2*',            # all resolutions
             r'volumes/VG_28xx/\1/CALIB/\2C02.TAB',
             r'volumes/VG_28xx/\1/CALIB/\2C02.LBL',
             r'volumes/VG_28xx/\1/GEOMETRY/\2G02.TAB',
             r'volumes/VG_28xx/\1/GEOMETRY/\2G02.LBL',
             r'volumes/VG_28xx/\1/JITTER/\2J01.TAB',
             r'volumes/VG_28xx/\1/JITTER/\2J01.LBL',
             r'volumes/VG_28xx/\1/IMAGES/C11*',
             r'volumes/VG_28xx/\1/VECTORS/J2000/\2VC2.TAB',
             r'volumes/VG_28xx/\1/VECTORS/J2000/\2VC2.LBL',
             r'volumes/VG_28xx/\1/VECTORS/J2000/\2VE2.TAB',
             r'volumes/VG_28xx/\1/VECTORS/J2000/\2VE2.LBL',
             r'diagrams/VG_28xx/\1/\2xxx_diagram_full.png',
             r'diagrams/VG_28xx/\1/\2xxx_diagram_med.png',
             r'diagrams/VG_28xx/\1/\2xxx_diagram_small.png',
             r'diagrams/VG_28xx/\1/\2xxx_diagram_thumb.png',
             r'previews/VG_28xx/\1/\2xxx_preview_full.png',
             r'previews/VG_28xx/\1/\2xxx_preview_med.png',
             r'previews/VG_28xx/\1/\2xxx_preview_small.png',
             r'previews/VG_28xx/\1/\2xxx_preview_thumb.png',
            ]),
    (r'.*/VG_28xx/(VG_2801)/.*/(PS[12]|PU[12]|PN1).*', 0,
            [r'volumes/VG_28xx/\1/EDITDATA/\2D01.DAT',
             r'volumes/VG_28xx/\1/EDITDATA/\2D01.LBL',
             r'metadata/VG_28xx/\1/\1_index.lbl',
             r'metadata/VG_28xx/\1/\1_index.tab',
             r'metadata/VG_28xx/\1/\1_supplemental_index.lbl',
             r'metadata/VG_28xx/\1/\1_supplemental_index.tab',
            ]),

    # VG_2802
    (r'.*/VG_28xx/(VG_2802)/.*/(US1).*', 0,
            [r'volumes/VG_28xx/\1/EASYDATA/*/\2*',
             r'volumes/VG_28xx/\1/EDITDATA/\2D02T.TAB',
             r'volumes/VG_28xx/\1/EDITDATA/\2D02T.LBL',
             r'volumes/VG_28xx/\1/GEOMETRY/\2G02.TAB',
             r'volumes/VG_28xx/\1/GEOMETRY/\2G02.LBL',
             r'volumes/VG_28xx/\1/VECTORS/J2000/\2VC2.TAB',
             r'volumes/VG_28xx/\1/VECTORS/J2000/\2VC2.LBL',
             r'volumes/VG_28xx/\1/VECTORS/J2000/\2VE2.TAB',
             r'volumes/VG_28xx/\1/VECTORS/J2000/\2VE2.LBL',
             r'volumes/VG_28xx/\1/IMAGES/C4400349.IMG',
             r'volumes/VG_28xx/\1/IMAGES/C4400349.LBL',
             r'volumes/VG_28xx/\1/IMAGES/C4400349.TIF',
             r'diagrams/VG_28xx/\1/\2xxx_diagram_full.png',
             r'diagrams/VG_28xx/\1/\2xxx_diagram_med.png',
             r'diagrams/VG_28xx/\1/\2xxx_diagram_small.png',
             r'diagrams/VG_28xx/\1/\2xxx_diagram_thumb.png',
             r'previews/VG_28xx/\1/\2xxx_preview_full.png',
             r'previews/VG_28xx/\1/\2xxx_preview_med.png',
             r'previews/VG_28xx/\1/\2xxx_preview_small.png',
             r'previews/VG_28xx/\1/\2xxx_preview_thumb.png',
            ]),
    (r'.*/VG_28xx/(VG_2802)/.*/(US[23]).*', 0,
            [r'volumes/VG_28xx/\1/EASYDATA/*/\2*',
             r'volumes/VG_28xx/\1/EDITDATA/\2D01T.TAB',
             r'volumes/VG_28xx/\1/EDITDATA/\2D01T.LBL',
             r'volumes/VG_28xx/\1/GEOMETRY/\2G01.TAB',
             r'volumes/VG_28xx/\1/GEOMETRY/\2G01.LBL',
             r'volumes/VG_28xx/\1/VECTORS/J2000/\2VC1.TAB',
             r'volumes/VG_28xx/\1/VECTORS/J2000/\2VC1.LBL',
             r'volumes/VG_28xx/\1/VECTORS/J2000/\2VE1.TAB',
             r'volumes/VG_28xx/\1/VECTORS/J2000/\2VE1.LBL',
             r'diagrams/VG_28xx/\1/\2xxx_diagram_full.png',
             r'diagrams/VG_28xx/\1/\2xxx_diagram_med.png',
             r'diagrams/VG_28xx/\1/\2xxx_diagram_small.png',
             r'diagrams/VG_28xx/\1/\2xxx_diagram_thumb.png',
             r'previews/VG_28xx/\1/\2xxx_preview_full.png',
             r'previews/VG_28xx/\1/\2xxx_preview_med.png',
             r'previews/VG_28xx/\1/\2xxx_preview_small.png',
             r'previews/VG_28xx/\1/\2xxx_preview_thumb.png',
            ]),
    (r'.*/VG_28xx/(VG_2802)/.*/(UU[12])...([654ABNGDLEX][IE])\..*', 0,
            [r'volumes/VG_28xx/\1/EASYDATA/*/\2*\3.*',
             r'volumes/VG_28xx/\1/EDITDATA/\2D01T.TAB',
             r'volumes/VG_28xx/\1/EDITDATA/\2D01T.LBL',
             r'volumes/VG_28xx/\1/GEOMETRY/\2G01\3.TAB',
             r'volumes/VG_28xx/\1/GEOMETRY/\2G01\3.LBL',
             r'volumes/VG_28xx/\1/VECTORS/J2000/\2VC1\3.TAB',
             r'volumes/VG_28xx/\1/VECTORS/J2000/\2VC1\3.LBL',
             r'volumes/VG_28xx/\1/VECTORS/J2000/\2VE1\3.TAB',
             r'volumes/VG_28xx/\1/VECTORS/J2000/\2VE1\3.LBL',
             r'diagrams/VG_28xx/\1/\2xxx\3_diagram_full.png',
             r'diagrams/VG_28xx/\1/\2xxx\3_diagram_med.png',
             r'diagrams/VG_28xx/\1/\2xxx\3_diagram_small.png',
             r'diagrams/VG_28xx/\1/\2xxx\3_diagram_thumb.png',
             r'previews/VG_28xx/\1/\2xxx\3_preview_full.png',
             r'previews/VG_28xx/\1/\2xxx\3_preview_med.png',
             r'previews/VG_28xx/\1/\2xxx\3_preview_small.png',
             r'previews/VG_28xx/\1/\2xxx\3_preview_thumb.png',
            ]),
    (r'.*/VG_28xx/(VG_2802)/.*/(UU[12])...(X[IE])\..*', 0,  # ring-plane geometry uses no suffix
            [r'volumes/VG_28xx/\1/GEOMETRY/\2G01.TAB',
             r'volumes/VG_28xx/\1/GEOMETRY/\2G01.LBL',
             r'volumes/VG_28xx/\1/VECTORS/J2000/\2VC1.TAB',
             r'volumes/VG_28xx/\1/VECTORS/J2000/\2VC1.LBL',
             r'volumes/VG_28xx/\1/VECTORS/J2000/\2VE1.TAB',
             r'volumes/VG_28xx/\1/VECTORS/J2000/\2VE1.LBL',
             r'diagrams/VG_28xx/\1/\2xxx\3_diagram_full.png',
             r'diagrams/VG_28xx/\1/\2xxx\3_diagram_med.png',
             r'diagrams/VG_28xx/\1/\2xxx\3_diagram_small.png',
             r'diagrams/VG_28xx/\1/\2xxx\3_diagram_thumb.png',
             r'previews/VG_28xx/\1/\2xxx\3_preview_full.png',
             r'previews/VG_28xx/\1/\2xxx\3_preview_med.png',
             r'previews/VG_28xx/\1/\2xxx\3_preview_small.png',
             r'previews/VG_28xx/\1/\2xxx\3_preview_thumb.png',
            ]),
    (r'.*/VG_28xx/(VG_2802)/.*/(UU1).*', 0,
            [r'volumes/VG_28xx/\1/IMAGES/C2683058.IMG',
             r'volumes/VG_28xx/\1/IMAGES/C2683058.LBL',
             r'volumes/VG_28xx/\1/IMAGES/C2683058.TIF',
            ]),
    (r'.*/VG_28xx/(VG_2802)/.*/(UU2).*', 0,
            [r'volumes/VG_28xx/\1/IMAGES/C2684902.IMG',
             r'volumes/VG_28xx/\1/IMAGES/C2684902.LBL',
             r'volumes/VG_28xx/\1/IMAGES/C2684902.TIF',
            ]),
    (r'.*/VG_28xx/(VG_2802)/.*/(UN1).*', 0,
            [r'volumes/VG_28xx/\1/EASYDATA/*/\2*',
             r'volumes/VG_28xx/\1/EDITDATA/\2D01T.TAB',
             r'volumes/VG_28xx/\1/EDITDATA/\2D01T.LBL',
             r'volumes/VG_28xx/\1/GEOMETRY/\2G02.TAB',
             r'volumes/VG_28xx/\1/GEOMETRY/\2G02.LBL',
             r'volumes/VG_28xx/\1/VECTORS/J2000/\2VC2.TAB',
             r'volumes/VG_28xx/\1/VECTORS/J2000/\2VC2.LBL',
             r'volumes/VG_28xx/\1/VECTORS/J2000/\2VE2.TAB',
             r'volumes/VG_28xx/\1/VECTORS/J2000/\2VE2.LBL',
             r'volumes/VG_28xx/\1/IMAGES/C11*',
             r'diagrams/VG_28xx/\1/\2xxx_diagram_full.png',
             r'diagrams/VG_28xx/\1/\2xxx_diagram_med.png',
             r'diagrams/VG_28xx/\1/\2xxx_diagram_small.png',
             r'diagrams/VG_28xx/\1/\2xxx_diagram_thumb.png',
             r'previews/VG_28xx/\1/\2xxx_preview_full.png',
             r'previews/VG_28xx/\1/\2xxx_preview_med.png',
             r'previews/VG_28xx/\1/\2xxx_preview_small.png',
             r'previews/VG_28xx/\1/\2xxx_preview_thumb.png',
            ]),
    (r'.*/VG_28xx/(VG_2802)/.*/(US[123]|UU[12]|UN1).*', 0,
            [r'volumes/VG_28xx/\1/CALIB/\2C01.TAB',
             r'volumes/VG_28xx/\1/CALIB/\2C01.LBL',
             r'volumes/VG_28xx/\1/EDITDATA/\2W01P*',
             r'metadata/VG_28xx/\1/\1_index.lbl',
             r'metadata/VG_28xx/\1/\1_index.tab',
             r'metadata/VG_28xx/\1/\1_supplemental_index.lbl',
             r'metadata/VG_28xx/\1/\1_supplemental_index.tab',
            ]),

    # VG_2803, best of old pole (RxxP1) and all of new pole (RxxP2)
    (r'.*/VG_28xx/(VG_2803)/S_RINGS/.*/(RS)...(S|X).*', 0,
            [r'volumes/VG_28xx/\1/S_RINGS/EASYDATA/KM000_2/RS1P1\3*',
             r'volumes/VG_28xx/\1/S_RINGS/EASYDATA/KM000_5/RS3P1\3*',
             r'volumes/VG_28xx/\1/S_RINGS/EASYDATA/KM002_5/RS4P1\3*',
             r'volumes/VG_28xx/\1/S_RINGS/EASYDATA/KM*/RS?P2\3*',
             r'diagrams/VG_28xx/\1/\2xxx\3_diagram_full.png',
             r'diagrams/VG_28xx/\1/\2xxx\3_diagram_med.png',
             r'diagrams/VG_28xx/\1/\2xxx\3_diagram_small.png',
             r'diagrams/VG_28xx/\1/\2xxx\3_diagram_thumb.png',
             r'previews/VG_28xx/\1/\2xxx\3_preview_full.png',
             r'previews/VG_28xx/\1/\2xxx\3_preview_med.png',
             r'previews/VG_28xx/\1/\2xxx\3_preview_small.png',
             r'previews/VG_28xx/\1/\2xxx\3_preview_thumb.png',
            ]),
    (r'.*/VG_28xx/(VG_2803)/U_RINGS/.*/(RU)...([SX]\w[IE]).*', 0,
            [r'volumes/VG_28xx/\1/U_RINGS/EASYDATA/KM00_025/RU[12]P1\3*',
             r'volumes/VG_28xx/\1/U_RINGS/EASYDATA/KM00_05/RU[35]P1\3*',
             r'volumes/VG_28xx/\1/U_RINGS/EASYDATA/KM00_25/RU4P1\3*',
             r'volumes/VG_28xx/\1/U_RINGS/EASYDATA/*/RU?P2\3*',
             r'diagrams/VG_28xx/\1/\2xxx\3_diagram_full.png',
             r'diagrams/VG_28xx/\1/\2xxx\3_diagram_med.png',
             r'diagrams/VG_28xx/\1/\2xxx\3_diagram_small.png',
             r'diagrams/VG_28xx/\1/\2xxx\3_diagram_thumb.png',
             r'previews/VG_28xx/\1/\2xxx\3_preview_full.png',
             r'previews/VG_28xx/\1/\2xxx\3_preview_med.png',
             r'previews/VG_28xx/\1/\2xxx\3_preview_small.png',
             r'previews/VG_28xx/\1/\2xxx\3_preview_thumb.png',
            ]),
    (r'.*/VG_28xx.*/(VG_2803)/[SU]_RINGS/.*', 0,
            [r'metadata/VG_28xx/\1/\1_index.lbl',
             r'metadata/VG_28xx/\1/\1_index.tab',
             r'metadata/VG_28xx/\1/\1_supplemental_index.lbl',
             r'metadata/VG_28xx/\1/\1_supplemental_index.tab',
            ]),

    # VG_2810
    (r'.*/VG_28xx/(VG_2810)/DATA/(IS[12]).*', 0,
            [r'volumes/VG_28xx/\1/DATA/\2_*.*',
             r'volumes/VG_28xx/\1/DATA/\2_P0001_IMAGES/ANNOTATED/*',
             r'volumes/VG_28xx/\1/DATA/\2_P0001_IMAGES/RAW*/*',
             r'volumes/VG_28xx/\1/DATA/\2_P0001_IMAGES/GEOM*/*',
             r'metadata/VG_28xx/\1/\1_index.lbl',
             r'metadata/VG_28xx/\1/\1_index.tab',
             r'metadata/VG_28xx/\1/\1_supplemental_index.lbl',
             r'metadata/VG_28xx/\1/\1_supplemental_index.tab',
             r'diagrams/VG_28xx/\1/\2_P0001_diagram_full.png',
             r'diagrams/VG_28xx/\1/\2_P0001_diagram_med.png',
             r'diagrams/VG_28xx/\1/\2_P0001_diagram_small.png',
             r'diagrams/VG_28xx/\1/\2_P0001_diagram_thumb.png',
             r'previews/VG_28xx/\1/\2_P0001_preview_full.png',
             r'previews/VG_28xx/\1/\2_P0001_preview_med.png',
             r'previews/VG_28xx/\1/\2_P0001_preview_small.png',
             r'previews/VG_28xx/\1/\2_P0001_preview_thumb.png',
            ]),
])

##########################################################################################
# OPUS_ID
##########################################################################################

USTAR_DICT = """{
1: "sigsgr",
2: "betper"}""".replace('\n','').replace(' ','')

opus_id = translator.TranslatorByRegex([
    # VG_2801
    # S RINGS (1981-08-26, egress):
    # 'mission'-'inst'-'inst host'-planet-occ-'year'-'day of year'-'star name'-'direction'
    (r'.*/VG_28xx/VG_2801/[^D].*/PS1.*\..*', 0, r'vg-pps-2-s-occ-1981-238-delsco-e'),
    (r'.*/VG_28xx/VG_2801/[^D].*/PS2.*\..*', 0, r'vg-pps-2-s-occ-1981-238-delsco-e2'),

    # U RINGS (1986-01-24):
    # 'mission'-'inst'-'inst host'-planet-occ-'year'-'day of year'-'star name'-'ring name'-'direction'
    (r'.*/VG_28xx/VG_2801/[^D].*/PU(1|2)...([654ABNGDLEX])(I|E)\..*', 0,
            r'vg-pps-2-u-occ-1986-024-' + USTAR_DICT + r'[\1]-' + URING_DICT + r'["\2"]-#LOWER#\3'),

    # N RINGS (1989-08-24, ingress):
    # 'mission'-'inst'-'inst host'-planet-occ-'year'-'day of year'-'star name'-'direction'
    (r'.*/VG_28xx/VG_2801/[^D].*/PN1.*', 0, r'vg-pps-2-n-occ-1989-236-sigsgr-i'),

    # VG_2802
    # S RINGS:
    # 'mission'-'inst'-'inst host'-planet-occ-'year'-'day of year'-'star name'-'direction'
    # US1 (1981-08-26, egress), US2 (1981-08-25, ingress), US3 (1980-11-12, egress)
    (r'.*/VG_28xx/VG_2802/[^D].*/US1.*', 0, r'vg-uvs-2-s-occ-1981-238-delsco-e'),
    (r'.*/VG_28xx/VG_2802/[^D].*/US2.*', 0, r'vg-uvs-2-s-occ-1981-237-delsco-i'),
    (r'.*/VG_28xx/VG_2802/[^D].*/US3.*', 0, r'vg-uvs-1-s-occ-1980-317-iother-e'),

    # U RINGS (1986-01-24):
    # 'mission'-'inst'-'inst host'-planet-occ-'year'-'day of year'-'star name'-'ring name'-'direction'
    (r'.*/VG_28xx/VG_2802/[^D].*/UU(1|2)...([654ABNGDLEX])(I|E)\..*', 0,
            r'vg-uvs-2-u-occ-1986-024-' + USTAR_DICT + r'[\1]-' + URING_DICT + r'["\2"]-#LOWER#\3'),

    # N RINGS (1989-08-24):
    # 'mission'-'inst'-'inst host'-planet-occ-'year'-'day of year'-'star name'-'direction'
    (r'.*/VG_28xx/VG_2802/[^D].*/UN1.*', 0, r'vg-uvs-2-n-occ-1989-236-sigsgr-i'),

    # VG_2803
    # S RINGS (1980-11-13, egress):
    # 'mission'-'inst'-'inst host'-planet-occ-'year'-'day of year'-'band name + 2-digit DSN'-'direction'
    # NOTE: replace matched group from \n to \g<n> to make sure match_obj.expand
    # return the correct result when numbers are right after the matched group.
    (r'.*/VG_28xx.*/VG_2803/S_RINGS/.*/RS...(S|X).*', 0, r'vg-rss-1-s-occ-1980-318-#LOWER#\g<1>63-e'),

    # U RINGS (1986-01-24):
    # 'mission'-'inst'-'inst host'-planet-occ-'year'-'day of year'-'band name + 2-digit DSN'-'ring name'-'direction'
    (r'.*/VG_28xx.*/VG_2803/U_RINGS/.*/RU...(S|X)([654ABNGDLE])(I|E)\..*', 0,
            r'vg-rss-2-u-occ-1986-024-#LOWER#\g<1>43-' + URING_DICT + r'["\2"]-\3'),

    # VG_2810
    # 'mission'-'inst'-'inst host'-prof
    (r'.*/VG_28xx/VG_2810/DATA/IS(\d)_P.*\..*', 0, r'vg-iss-\1-s-prof'),
])

##########################################################################################
# FILESPEC_TO_BUNDLESET
##########################################################################################

filespec_to_bundleset = translator.TranslatorByRegex([
    (r'VG_28\d{2}.*', 0, r'VG_28xx'),
])

##########################################################################################
# OPUS_ID_TO_PRIMARY_LOGICAL_PATH
##########################################################################################

URING_INV_DICT = """{
"six"    : "6",
"five"   : "5",
"four"   : "4",
"alpha"  : "A",
"beta"   : "B",
"eta"    : "N",
"gamma"  : "G",
"delta"  : "D",
"lambda" : "L",
"epsilon": "E",
"ringpl" : "X"}""".replace('\n','').replace(' ','')

opus_id_to_primary_logical_path = translator.TranslatorByRegex([
    # VG_2801, Saturn: PS1 in KM000_2, Uranus: PU1 in KM000_1, PU2 in KM001
    # Neptune: PN1 in KM002
    (r'vg-pps-2-s-occ-1981-238-(.*)-e',  0, r'volumes/VG_28xx/VG_2801/EASYDATA/KM005/PS1P01.TAB'),
    (r'vg-pps-2-s-occ-1981-238-(.*)-e2', 0, r'volumes/VG_28xx/VG_2801/EDITDATA/PS2D01.DAT'),
    (r'vg-pps-2-u-occ-1986-024-sigsgr-(\w+)-([ie])', 0,
            r'volumes/VG_28xx/VG_2801/EASYDATA/KM000_1/PU1P01' + URING_INV_DICT + r'["\1"]' + r'#UPPER#\2.TAB'),
    (r'vg-pps-2-u-occ-1986-024-betper-(\w+)-([ie])', 0,
            r'volumes/VG_28xx/VG_2801/EASYDATA/KM001/PU2P01' + URING_INV_DICT + r'["\1"]' + r'#UPPER#\2.TAB'),
    (r'vg-pps-2-n-occ-1989-236-(.*)-i', 0, r'volumes/VG_28xx/VG_2801/EASYDATA/KM002/PN1P01.TAB'),

    # VG_2802, Saturn: FILTER01, Uranus: FILTER01, Neptune: FILTER01
    (r'vg-uvs-2-s-occ-1981-238-delsco-e', 0, r'volumes/VG_28xx/VG_2802/EASYDATA/FILTER01/US1F01.TAB'),
    (r'vg-uvs-2-s-occ-1981-237-delsco-i', 0, r'volumes/VG_28xx/VG_2802/EASYDATA/FILTER01/US2F01.TAB'),
    (r'vg-uvs-1-s-occ-1980-317-iother-e', 0, r'volumes/VG_28xx/VG_2802/EASYDATA/FILTER01/US3F01.TAB'),
    (r'vg-uvs-2-u-occ-1986-024-sigsgr-(\w+)-([ie])', 0,
            r'volumes/VG_28xx/VG_2802/EASYDATA/FILTER01/UU1F01' + URING_INV_DICT + r'["\1"]' + r'#UPPER#\2.TAB'),
    (r'vg-uvs-2-n-occ-1989-236-sigsgr-i', 0, r'volumes/VG_28xx/VG_2802/EASYDATA/FILTER01/UN1F01.TAB'),

    # VG_2803
    # "Best" Saturn solution KM002_5/RS3P2 (5-km inversion, 2.5-km sampling, new pole, full ring system)
    # "Best" Uranus solutions are KM00_25/RU4P2 (500-m inversion, 250-m sampling, new pole)
    (r'vg-rss-1-s-occ-1980-318-(.*)63-e', 0, r'volumes/VG_28xx/VG_2803/S_RINGS/EASYDATA/KM002_5/RS3P2#UPPER#\1.TAB'),
    (r'vg-rss-2-u-occ-1986-024-(.*)43-(\w+)-([ie])',0,
            r'volumes/VG_28xx/VG_2803/U_RINGS/EASYDATA/KM00_25/RU4P2#UPPER#\g<1>' + URING_INV_DICT + r'["\2"]' + r'\3.TAB'),

    # VG_2810, pick the smallest resolutions
    (r'vg-iss-([12])-s-prof', 0, r'volumes/VG_28xx/VG_2810/DATA/IS\1_*_KM002.TAB'),
])

##########################################################################################
# Subclass definition
##########################################################################################

class VG_28xx(pds3file.Pds3File):

    pds3file.Pds3File.VOLSET_TRANSLATOR = translator.TranslatorByRegex([('VG_28xx', re.I, 'VG_28xx')]) + \
                                          pds3file.Pds3File.VOLSET_TRANSLATOR

    DESCRIPTION_AND_ICON = description_and_icon_by_regex + pds3file.Pds3File.DESCRIPTION_AND_ICON

    OPUS_TYPE = opus_type + pds3file.Pds3File.OPUS_TYPE
    OPUS_FORMAT = opus_format + pds3file.Pds3File.OPUS_FORMAT
    OPUS_PRODUCTS = opus_products
    OPUS_ID = opus_id
    OPUS_ID_TO_PRIMARY_LOGICAL_PATH = opus_id_to_primary_logical_path

    VIEWABLES = {'default': default_viewables}

    ASSOCIATIONS = pds3file.Pds3File.ASSOCIATIONS.copy()
    ASSOCIATIONS['volumes']   += associations_to_volumes
    ASSOCIATIONS['metadata']  += associations_to_metadata
    ASSOCIATIONS['documents'] += associations_to_documents

    VERSIONS = versions + pds3file.Pds3File.VERSIONS

# Global attribute shared by all subclasses
pds3file.Pds3File.OPUS_ID_TO_SUBCLASS = translator.TranslatorByRegex([
                                            (r'vg-(pps|uvs|rss)-.*occ-.*', 0, VG_28xx),
                                            (r'vg-iss.*prof', 0, VG_28xx)]) + pds3file.Pds3File.OPUS_ID_TO_SUBCLASS

pds3file.Pds3File.FILESPEC_TO_BUNDLESET = filespec_to_bundleset + pds3file.Pds3File.FILESPEC_TO_BUNDLESET

##########################################################################################
# Update the global dictionary of subclasses
##########################################################################################

pds3file.Pds3File.SUBCLASSES['VG_28xx'] = VG_28xx

##########################################################################################
# Unit tests
##########################################################################################

import pytest
from .pytest_support import *

@pytest.mark.parametrize(
    'input_path,expected',
    [
        # VG_2801
        ('volumes/VG_28xx/VG_2801/EASYDATA/KM000_2/PS1P0107.TAB',
         'VG_28xx/opus_products/PS1P0107.txt'),
        ('volumes/VG_28xx/VG_2801/EASYDATA/KM000_1/PU1P01DE.TAB',
         'VG_28xx/opus_products/PU1P01DE.txt'),
        # VG_2802
        ('volumes/VG_28xx/VG_2802/EASYDATA/FILTER01/US1F01.TAB',
         'VG_28xx/opus_products/US1F01.txt'),
        ('volumes/VG_28xx/VG_2802/EASYDATA/FILTER01/UU1F01EE.TAB',
         'VG_28xx/opus_products/UU1F01EE.txt'),
        ('volumes/VG_28xx/VG_2802/EASYDATA/FILTER01/UN1F01.TAB',
         'VG_28xx/opus_products/UN1F01.txt'),
        # VG_2803
        ('volumes/VG_28xx/VG_2803/S_RINGS/EASYDATA/KM000_2/RS1P2X07.LBL',
         'VG_28xx/opus_products/RS1P2X07.txt'),
        ('volumes/VG_28xx/VG_2803/U_RINGS/EASYDATA/KM00_2/RU1P2X4I.TAB',
         'VG_28xx/opus_products/RU1P2X4I.txt'),
        # VG_2810
        ('volumes/VG_28xx/VG_2810/DATA/IS2_P0001_V01_KM002.TAB',
         'VG_28xx/opus_products/IS2_P0001_V01_KM002.txt')
    ]
)
def test_opus_products(request, input_path, expected):
    update = request.config.option.update
    opus_products_test(pds3file.Pds3File, input_path, TEST_RESULTS_DIR+expected, update)

@pytest.mark.parametrize(
    'input_path,category,expected',
    [
        ('volumes/VG_28xx/VG_2801/EASYDATA/KM000_2/PS1P0107.TAB',
         'volumes',
         'VG_28xx/associated_abspaths/volumes_PS1P0107.txt'),
        ('volumes/VG_28xx/VG_2801/EASYDATA/KM000_2/PU1P01DE.TAB',
         'volumes',
         'VG_28xx/associated_abspaths/volumes_PU1P01DE.txt'),
        ('volumes/VG_28xx/VG_2802/EASYDATA/FILTER01/US1F01.TAB',
         'volumes',
         'VG_28xx/associated_abspaths/volumes_US1F01.txt'),
        ('volumes/VG_28xx/VG_2802/EASYDATA/FILTER01/UU1F01EE.TAB',
         'volumes',
         'VG_28xx/associated_abspaths/volumes_UU1F01EE.txt'),
        ('volumes/VG_28xx/VG_2802/EASYDATA/FILTER01/UN1F01.TAB',
         'volumes',
         'VG_28xx/associated_abspaths/volumes_UN1F01.txt'),
        ('volumes/VG_28xx/VG_2803/S_RINGS/EASYDATA/KM000_2/RS1P2X07.LBL',
         'volumes',
         'VG_28xx/associated_abspaths/volumes_RS1P2X07.txt'),
        ('volumes/VG_28xx/VG_2803/U_RINGS/EASYDATA/KM00_2/RU1P2X4I.TAB',
         'volumes',
         'VG_28xx/associated_abspaths/volumes_RU1P2X4I.txt'),
        ('volumes/VG_28xx/VG_2810/DATA/IS2_P0001_V01_KM002.TAB',
         'volumes',
         'VG_28xx/associated_abspaths/volumes_IS2_P0001_V01_KM002.txt'),
    ]
)
def test_associated_abspaths(request, input_path, category, expected):
    update = request.config.option.update
    associated_abspaths_test(pds3file.Pds3File, input_path, category,
                             TEST_RESULTS_DIR+expected, update)

def test_opus_id_to_primary_logical_path():
    TESTS = [
        'VG_2803/U_RINGS/EASYDATA/KM00_25/RU4P2XEI.TAB',
        'VG_2801/EASYDATA/KM000_1/PU1P01LI.TAB',
        'VG_2802/EASYDATA/FILTER01/UN1F01.TAB',
        'VG_2802/EASYDATA/FILTER01/US3F01.TAB',
        'VG_2803/S_RINGS/EASYDATA/KM002_5/RS3P2S.TAB',
        'VG_2803/U_RINGS/EASYDATA/KM00_25/RU4P2XEI.TAB',
        'VG_2810/DATA/IS1_P0001_V01_KM002.TAB',
    ]

    for filepath in TESTS:
        logical_path = 'volumes/VG_28xx/' + filepath
        test_pdsf = pds3file.Pds3File.from_logical_path(logical_path)
        opus_id = test_pdsf.opus_id
        opus_id_pdsf = pds3file.Pds3File.from_opus_id(opus_id)
        assert opus_id_pdsf.logical_path == logical_path
