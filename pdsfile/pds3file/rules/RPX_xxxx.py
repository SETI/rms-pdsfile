##########################################################################################
# pds3file/rules/RPX_xxxx.py
##########################################################################################

import pdsfile.pds3file as pds3file
import translator
import re

##########################################################################################
# DESCRIPTION_AND_ICON
##########################################################################################

description_and_icon_by_regex = translator.TranslatorByRegex([
    (r'volumes/.*/RPX_00.*/BROWSE',   re.I, ('Browse GIFs',                   'BROWDIR' )),
    (r'volumes/.*/RPX_00.*/CALIMAGE', re.I, ('Calibrated images',             'IMAGEDIR')),
    (r'volumes/.*/RPX_00.*/CALMASK',  re.I, ('Calibrated image masks',        'DATADIR' )),
    (r'volumes/.*/RPX_00.*/ENGDATA',  re.I, ('Engineering data',              'DATADIR' )),
    (r'volumes/.*/RPX_00.*/ENGMASK',  re.I, ('Engineering data masks',        'DATADIR' )),
    (r'volumes/.*/RPX_00.*/HEADER',   re.I, ('HST header files',              'DATADIR' )),
    (r'volumes/.*/RPX_00.*/RAWIMAGE', re.I, ('Raw images',                    'IMAGEDIR')),
    (r'volumes/.*/RPX_00.*/RAWMASK',  re.I, ('Raw image masks',               'DATADIR' )),
    (r'volumes/.*/RPX_00.*/CALIMAGE/.*\.IMG',  re.I, ('Calibrated image, FITS',         'IMAGE'   )),
    (r'volumes/.*/RPX_00.*/CALIMAGE/.*\.FITS', re.I, ('Calibrated image, FITS',         'IMAGE'   )),
    (r'volumes/.*/RPX_00.*/CALMASK/.*\.ZIP',   re.I, ('Image mask, zipped FITS',        'DATA'    )),
    (r'volumes/.*/RPX_00.*/CALMASK/.*\.FITS',  re.I, ('Image mask, FITS',               'DATA'    )),
    (r'volumes/.*/RPX_00.*/ENGDATA/.*\.ZIP',   re.I, ('Engineering data, zipped FITS',  'DATA'    )),
    (r'volumes/.*/RPX_00.*/ENGDATA/.*\.FITS',  re.I, ('Engineering data, FITS',         'DATA'    )),
    (r'volumes/.*/RPX_00.*/ENGMASK/.*\.ZIP',   re.I, ('Engineering mask, zipped FITS',  'DATA'    )),
    (r'volumes/.*/RPX_00.*/ENGMASK/.*\.FITS',  re.I, ('Engineering mask, FITS',         'DATA'    )),
    (r'volumes/.*/RPX_00.*/HEADER/.*\.ZIP',    re.I, ('HST header file, zipped FITS',   'DATA'    )),
    (r'volumes/.*/RPX_00.*/HEADER/.*\.FITS',   re.I, ('HST header file, FITS',          'DATA'    )),
    (r'volumes/.*/RPX_00.*/RAWIMAGE/.*\.ZIP',  re.I, ('Raw image, zipped FITS',         'IMAGE'   )),
    (r'volumes/.*/RPX_00.*/RAWIMAGE/.*\.FITS', re.I, ('Raw image, FITS',                'IMAGE'   )),
    (r'volumes/.*/RPX_00.*/RAWMASK/.*\.ZIP',   re.I, ('Raw image mask, zipped FITS',    'DATA'    )),
    (r'volumes/.*/RPX_00.*/RAWMASK/.*\.FITS',  re.I, ('Raw image mask, FITS',           'DATA'    )),
    (r'volumes/.*/RPX_00.*/[0-9]{6}XX',        re.I, ('Data files by year and month',   'IMAGEDIR')),

    (r'volumes/.*/RPX_00.*/U2IQXXXX(|/\w+)', re.I, ('Data from proposal 5219, PI Trauger  ', 'IMAGEDIR')),
    (r'volumes/.*/RPX_00.*/U2IZXXXX(|/\w+)', re.I, ('Data from proposal 5508, PI Smith    ', 'IMAGEDIR')),
    (r'volumes/.*/RPX_00.*/U2KRXXXX(|/\w+)', re.I, ('Data from proposal 5776, PI Beebe    ', 'IMAGEDIR')),
    (r'volumes/.*/RPX_00.*/U2ONXXXX(|/\w+)', re.I, ('Data from proposal 5782, PI Bosh     ', 'IMAGEDIR')),
    (r'volumes/.*/RPX_00.*/U2TFXXXX(|/\w+)', re.I, ('Data from proposal 5836, PI Nicholson', 'IMAGEDIR')),
    (r'volumes/.*/RPX_00.*/U2QEXXXX(|/\w+)', re.I, ('Data from proposal 6030, PI Tomasko  ', 'IMAGEDIR')),
    (r'volumes/.*/RPX_00.*/U2WCXXXX(|/\w+)', re.I, ('Data from proposal 6215, PI Trauger  ', 'IMAGEDIR')),
    (r'volumes/.*/RPX_00.*/U2OOXXXX(|/\w+)', re.I, ('Data from proposal 6216, PI Trauger  ', 'IMAGEDIR')),
    (r'volumes/.*/RPX_00.*/U2VIXXXX(|/\w+)', re.I, ('Data from proposal 6295, PI Caldwell ', 'IMAGEDIR')),
    (r'volumes/.*/RPX_00.*/U2ZNXXXX(|/\w+)', re.I, ('Data from proposal 6328, PI Caldwell ', 'IMAGEDIR')),
])

##########################################################################################
# VIEWABLES
##########################################################################################

default_viewables = translator.TranslatorByRegex([
    (r'volumes/(RPX_xxxx/RPX_000./199...XX/U...XXXX)/(BROWSE|.*IMAGE)/(U[^_]+)(|_\w\w\w)\.(FITS|IMG|DAT|ZIP|LBL)', 0,
            [r'previews/\1/\3_full.jpg',
             r'previews/\1/\3_med.jpg',
             r'previews/\1/\3_small.jpg',
             r'previews/\1/\3_thumb.jpg',
            ]),
    (r'volumes/RPX_xxxx_v1/(RPX_000./199...XX)/(U...)XXXX/(BROWSE|.*IMAGE)/([^_]+)(|_\w\w\w)\.(FITS|IMG|DAT|ZIP|LBL)', 0,
            r'previews/RPX_xxxx/\1/\2XXXX/\2\4?_*.jpg'),
    (r'volumes/(RPX_xxxx/.*)\.(GIF|IMG|LBL)', 0,
            [r'previews/\1_full.jpg',
             r'previews/\1_med.jpg',
             r'previews/\1_small.jpg',
             r'previews/\1_thumb.jpg',
            ]),
])

##########################################################################################
# ASSOCIATIONS
##########################################################################################

associations_to_volumes = translator.TranslatorByRegex([
    (r'.*/RPX_xxxx(|_v[0-9\.]+)/(RPX_000./199...XX/U...XXXX)/(|\w+/)([A-Z0-9]+)(|_\w+)\..*', 0,
            [r'volumes/RPX_xxxx\1/\2/BROWSE//\4.GIF',
             r'volumes/RPX_xxxx\1/\2/BROWSE/\4.LBL',
             r'volumes/RPX_xxxx\1/\2/CALIMAGE/\4_C0F.FITS',
             r'volumes/RPX_xxxx\1/\2/CALIMAGE/\4_C0F.LBL',
             r'volumes/RPX_xxxx\1/\2/CALMASK/\4_C1F.FITS',
             r'volumes/RPX_xxxx\1/\2/CALMASK/\4_C1F.LBL',
             r'volumes/RPX_xxxx\1/\2/ENGDATA/\4_X0F.FITS',
             r'volumes/RPX_xxxx\1/\2/ENGDATA/\4_X0F.LBL',
             r'volumes/RPX_xxxx\1/\2/ENGMASK/\4_Q1F.FITS',
             r'volumes/RPX_xxxx\1/\2/ENGMASK/\4_Q1F.LBL',
             r'volumes/RPX_xxxx\1/\2/HEADER/\4_SHF.FITS',
             r'volumes/RPX_xxxx\1/\2/HEADER/\4_SHF.LBL',
             r'volumes/RPX_xxxx\1/\2/RAWIMAGE/\4_D0F.FITS',
             r'volumes/RPX_xxxx\1/\2/RAWIMAGE/\4_D0F.LBL',
             r'volumes/RPX_xxxx\1/\2/RAWMASK/\4_Q0F.FITS',
             r'volumes/RPX_xxxx\1/\2/RAWMASK/\4_Q0F.LBL',
            ]),
    (r'.*/RPX_xxxx(|_v[0-9\.]+)/(RPX_000./199...XX/U...XXXX/\w+)', 0,
            [r'volumes/RPX_xxxx\1/\2/BROWSE',
             r'volumes/RPX_xxxx\1/\2/CALIMAGE',
             r'volumes/RPX_xxxx\1/\2/CALMASK',
             r'volumes/RPX_xxxx\1/\2/ENGDATA',
             r'volumes/RPX_xxxx\1/\2/ENGMASK',
             r'volumes/RPX_xxxx\1/\2/HEADER',
             r'volumes/RPX_xxxx\1/\2/RAWIMAGE',
             r'volumes/RPX_xxxx\1/\2/RAWMASK',
                ]),
    (r'metadata/RPX_xxxx/(RPX_000.)/RPX_...._index.tab/(U...)([^_\.]+).*', 0,
            r'volumes/RPX_xxxx/\1/199*/\2XXXX/*/\2\3.*'),
    (r'volumes/(\w+/\w+)/199.*', 0,
            [r'volumes/\1/DOCUMENT',
             r'volumes/\1/CATALOG',
             r'volumes/\1/AAREADME.TXT',
             r'volumes/\1/ERRATA.TXT',
             r'volumes/\1/VOLDESC.CAT',
            ]),

    (r'.*/(RPX_xxxx/RPX_0[1-9].*)_([a-z]+).jpg', 0,
            r'volumes/\1.*'),
])

associations_to_previews = translator.TranslatorByRegex([
    (r'.*/(RPX_xxxx/RPX_000./199...XX/U...XXXX)/(|\w+/)(U[^_]+)(|_\w\w\w)\.(FITS|IMG|DAT|ZIP)', 0,
            [r'previews/\1/\3_full.jpg',
             r'previews/\1/\3_med.jpg',
             r'previews/\1/\3_small.jpg',
             r'previews/\1/\3_thumb.jpg',
            ]),
    (r'.*/RPX_xxxx_v1/(RPX_000./199...XX)/(U...)XXXX/(|\w+/)([^_]+)(|_\w\w\w)\.(FITS|IMG|DAT|ZIP)', 0,
            r'previews/RPX_xxxx/\1/\2XXXX/\2\3?_*.jpg'),
    (r'.*/RPX_xxxx(|_v[0-9\.]+)/(RPX_000./199...XX/U...XXXX)(|/\w+)', 0,
            r'previews/RPX_xxxx/\2'),

    (r'.*/(RPX_xxxx/.*)\.(IMG|GIF)', 0,
            r'previews/\1_*.jpg'),
])

associations_to_metadata = translator.TranslatorByRegex([
    (r'.*/RPX_xxxx/(RPX_000.)/199...XX/U...XXXX/(|\w+/)(U[^_]+)(|_\w\w\w)\..*', 0,
            [r'metadata/RPX_xxxx/\1/\1_index.tab/\3',
             r'metadata/RPX_xxxx/\1/\1_obsindex.tab/\3',
            ]),
    (r'.*/RPX_xxxx_v1/(RPX_000.)/199...XX/(U...)XXXX/(|\w+/)([^_]+)(|_\w\w\w)\..*', 0,
            r'metadata/RPX_xxxx/\1/\1_index.tab/\2\4'),
    (r'metadata/RPX_xxxx/(RPX_000.)/RPX_...._index.tab/(U[^_\.]+).*', 0,
            r'metadata/RPX_xxxx/\1/\1_obsindex.tab/\2'),
    (r'metadata/RPX_xxxx/(RPX_000.)/RPX_...._obsindex.tab/(U[^_\.]+).*', 0,
            r'metadata/RPX_xxxx/\1/\1_index.tab/\3'),

    (r'.*/RPX_xxxx/(RPX_0[1-9]..)/.*/(\w+)\.IMG', 0,
            r'metadata/RPX_xxxx/\1/\1_index.tab/\2'),
])

##########################################################################################
# VERSIONS
##########################################################################################

versions = translator.TranslatorByRegex([
    (r'volumes/RPX_xxxx_v1/(RPX_00../199...XX)/(U...)XXXX/BROWSE/(\w{4})\.(\w+)', 0,
            r'volumes/RPX_xxxx*/\1/\2XXXX/BROWSE/\2\3?.\4'),
    (r'volumes/RPX_xxxx.*/(RPX_00../199...XX)/(U...)XXXX/BROWSE/\2(\w{4}).\.(\w+)', 0,
            r'volumes/RPX_xxxx_v1/\1/\2XXXX/BROWSE/\3.\4'),
    (r'volumes/RPX_xxxx_v1/(RPX_00../199...XX)/(U...)XXXX/([A-Z]+)/(\w{4})_(\w{3})\.(ZIP|GIF|IMG)', 0,
            r'volumes/RPX_xxxx*/\1/\2XXXX/\3/\2\4?_\5.FITS'),
    (r'volumes/RPX_xxxx_v1/(RPX_00../199...XX)/(U...)XXXX/([A-Z]+)/(\w{4})_(\w{3})\.LBL', 0,
            r'volumes/RPX_xxxx*/\1/\2XXXX/\3/\2\4?_\5.LBL'),
    (r'volumes/RPX_xxxx*/(RPX_00../199...XX)/(U...)XXXX/([A-Z]+)/\2(\w{4})._(\w{3})\.FITS', 0,
            [r'volumes/RPX_xxxx_v1/\1/\2XXXX/\3/\4_\5.ZIP',
             r'volumes/RPX_xxxx_v1/\1/\2XXXX/\3/\4_\5.IMG'
            ]),
    (r'volumes/RPX_xxxx*/(RPX_00../199...XX)/(U...)XXXX/([A-Z]+)/\2(\w{4})._(\w{3})\.LBL', 0,
            r'volumes/RPX_xxxx_v1/\1/\2XXXX/\3/\4_\5.LBL'),
])

##########################################################################################
# VIEW_OPTIONS (grid_view_allowed, multipage_view_allowed, continuous_view_allowed)
##########################################################################################

view_options = translator.TranslatorByRegex([
    (r'volumes/RPX_.*/199...XX/U...XXXX/(BROWSE|.*IMAGE)', 0, (True, True,  True )),
    (r'previews/RPX_.*/199...XX/U...XXXX',                 0, (True, True,  True )),
    (r'.*/RPX_xxxx/RPX_0.../(DATA|CALIB)/.*',              0, (True, False, False)),
])

##########################################################################################
# FILESPEC_TO_BUNDLESET
##########################################################################################

filespec_to_bundleset = translator.TranslatorByRegex([
    (r'RPX_\d{4}.*', 0, r'RPX_xxxx'),
])

##########################################################################################
# NEIGHBORS
##########################################################################################

neighbors = translator.TranslatorByRegex([
    (r'(.*/RPX_xxxx.*)/RPX_000./199...XX',                0, r'\1/*/199*'),
    (r'(.*/RPX_xxxx.*)/RPX_000./199...XX/U...XXXX',       0, r'\1/*/199*/*'),
    (r'(.*/RPX_xxxx.*)/RPX_000./199...XX/U...XXXX/(\w+)', 0, r'\1/*/199*/*/\2'),
    (r'(.*/RPX_xxxx/RPX_0...)/(DATA|CALIB)/199.*/(\w+)',  0, r'\1/\2/199*/\3'),
])

##########################################################################################
# Subclass definition
##########################################################################################

class RPX_xxxx(pds3file.Pds3File):

    pds3file.Pds3File.VOLSET_TRANSLATOR = translator.TranslatorByRegex([('RPX_xxxx', re.I, 'RPX_xxxx')]) + \
                                          pds3file.Pds3File.VOLSET_TRANSLATOR

    DESCRIPTION_AND_ICON = description_and_icon_by_regex + pds3file.Pds3File.DESCRIPTION_AND_ICON
    VIEW_OPTIONS = view_options + pds3file.Pds3File.VIEW_OPTIONS
    NEIGHBORS = neighbors + pds3file.Pds3File.NEIGHBORS

    VIEWABLES = {'default': default_viewables}

    ASSOCIATIONS = pds3file.Pds3File.ASSOCIATIONS.copy()
    ASSOCIATIONS['volumes']  += associations_to_volumes
    ASSOCIATIONS['previews'] += associations_to_previews
    ASSOCIATIONS['metadata'] += associations_to_metadata

    VERSIONS = versions + pds3file.Pds3File.VERSIONS

    def FILENAME_KEYLEN(self):
        """9 for files in the RPX series RPX_0001-5; 0 otherwise."""

        # Use the length of the HST group ID for the new version of RPX_0001-5
        if '/RPX_000' in self.abspath:
            return 9

        return 0

pds3file.Pds3File.FILESPEC_TO_BUNDLESET = filespec_to_bundleset + pds3file.Pds3File.FILESPEC_TO_BUNDLESET

##########################################################################################
# Update the global dictionary of subclasses
##########################################################################################

pds3file.Pds3File.SUBCLASSES['RPX_xxxx'] = RPX_xxxx

##########################################################################################
