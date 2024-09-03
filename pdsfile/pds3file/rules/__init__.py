##########################################################################################
# pds3file/rules/__init__.py
#
# Definitions of Translator objects used by the PdsFile class.
##########################################################################################

import re
import translator

__all__ = [
    "ASTROM_xxxx",
    "COCIRS_xxxx",
    "COISS_xxxx" ,
    "CORSS_8xxx" ,
    "COSP_xxxx"  ,
    "COUVIS_0xxx",
    "COUVIS_8xxx",
    "COVIMS_0xxx",
    "COVIMS_8xxx",
    "EBROCC_xxxx",
    "GO_0xxx"    ,
    "HSTxx_xxxx" ,
    "JNOJIR_xxxx",
    "JNOJNC_xxxx",
    "JNOSP_xxxx" ,
    "NHSP_xxxx"  ,
    "NHxxxx_xxxx",
    "RES_xxxx"   ,
    "RPX_xxxx"   ,
    "VG_0xxx"    ,
    "VG_20xx"    ,
    "VG_28xx"    ,
    "VGIRIS_xxxx",
    "VGISS_xxxx" ,
]

GENERIC_VOLUME_DESC = 'Data volume'
GENERIC_VOLSET_DESC = 'Volume collection'

DESCRIPTION_AND_ICON = translator.TranslatorByRegex([

    # PDS3 labels
    (r'.*\.lbl', re.I, ('PDS3 label', 'LABEL')),

    # Checksums
    (r'checksums-archives-\w+', 0, ('<em>Checksums</em> of downloadable archives', 'CHECKDIR')),
    (r'checksums-calibrated',   0, ('<em>Checksums</em> of calibrated products',   'CHECKDIR')),
    (r'checksums-diagrams',     0, ('<em>Checksums</em> of observation diagrams',  'CHECKDIR')),
    (r'checksums-metadata',     0, ('<em>Checksums</em> of indices and metadata',  'CHECKDIR')),
    (r'checksums-previews',     0, ('<em>Checksums</em> of preview images',        'CHECKDIR')),
    (r'checksums-volumes',      0, ('<em>Checksums</em> of PDS volumes',           'CHECKDIR')),

    (r'checksums-archives-\w+/.*_md5\.txt', 0, ('Checksum index of downloadable archives', 'CHECKSUM')),
    (r'checksums-calibrated/.*_md5\.txt',   0, ('Checksum index of calibrated products',   'CHECKSUM')),
    (r'checksums-diagrams/.*_md5\.txt',     0, ('Checksum index of observation diagrams',  'CHECKSUM')),
    (r'checksums-metadata/.*_md5\.txt',     0, ('Checksum index of indices and metadatas', 'CHECKSUM')),
    (r'checksums-previews/.*_md5\.txt',     0, ('Checksum index of preview images',        'CHECKSUM')),
    (r'checksums-volumes/.*_md5\.txt',      0, ('Checksum index of entire volume',         'CHECKSUM')),

    # Archives
    (r'archives-calibrated', 0, ('<em>Downloadable archives</em> of calibrated products',  'ROOT')),
    (r'archives-diagrams',   0, ('<em>Downloadable archives</em> of observation diagrams', 'ROOT')),
    (r'archives-metadata',   0, ('<em>Downloadable archives</em> of indices and metadata', 'ROOT')),
    (r'archives-previews',   0, ('<em>Downloadable archives</em> of preview images',       'ROOT')),
    (r'archives-volumes',    0, ('<em>Downloadable archives</em> of PDS volumes',          'ROOT')),

    (r'archives-calibrated/[^/]+', 0, ('Downloadable archives of calibrated products',  'TARDIR')),
    (r'archives-diagrams/[^/]+',   0, ('Downloadable archives of observation diagrams', 'TARDIR')),
    (r'archives-metadata/[^/]+',   0, ('Downloadable archives of indices and metadata', 'TARDIR')),
    (r'archives-previews/[^/]+',   0, ('Downloadable archives of preview images',       'TARDIR')),
    (r'archives-volumes/[^/]+',    0, ('Downloadable archives of PDS volumes',          'TARDIR')),

    (r'archives-calibrated/[^/]+/.*\.tar\.gz', 0, ('Downloadable archive of calibrated products',  'TARBALL')),
    (r'archives-diagrams/[^/]+/.*\.tar\.gz',   0, ('Downloadable archive of observation diagrams', 'TARBALL')),
    (r'archives-metadata/[^/]+/.*\.tar\.gz',   0, ('Downloadable archive of indices and metadata', 'TARBALL')),
    (r'archives-previews/[^/]+/.*\.tar\.gz',   0, ('Downloadable archive of preview images',       'TARBALL')),
    (r'archives-volumes/[^/]+/.*\.tar\.gz',    0, ('Downloadable archive of entire PDS volume',    'TARBALL')),

    # Volume types
    (r'volumes',                0, ('<em>PDS volumes</em> in Viewmaster', 'ROOT')),
    (r'volumes/[^/]+',          0, (GENERIC_VOLSET_DESC, 'VOLDIR')),
    (r'volumes/[^/]+',          0, (GENERIC_VOLSET_DESC, 'VOLDIR')),
    (r'volumes/[^/]+/[^/]+',    0, (GENERIC_VOLUME_DESC, 'VOLUME')),

    (r'calibrated',       0, ('<em>Calibrated products</em> created by the RMS Node',   'ROOT')),
    (r'diagrams',         0, ('<em>Observation diagrams</em> created by the RMS Node',  'ROOT')),
    (r'metadata',         0, ('<em>Supplemental metadata</em> curated by the RMS Node', 'ROOT')),
    (r'previews',         0, ('<em>Preview images</em> created by the RMS Node',        'ROOT')),
    (r'documents',        0, ('<em>Documentation</em> curated by the RMS Node',         'ROOT')),

    (r'calibrated/[^/]+', 0, ('Calibrated products created by the RMS Node',        'DATADIR' )),
    (r'diagrams/[^/]+',   0, ('Observation diagrams created by the RMS Node',       'DIAGDIR' )),
    (r'metadata/[^/]+',   0, ('Supplemental metadata curated by the RMS Node',      'INDEXDIR')),
    (r'previews/[^/]+',   0, ('Preview images created by the RMS Node',             'IMAGEDIR')),
    (r'documents/[^/]+',  0, ('Supplemental documentation curated by the RMS Node', 'INFODIR' )),

    (r'calibrated/[^/]+/[^/]+',    0, ('Calibrated products for volume',               'DATADIR' )),
    (r'diagrams/[^/]+/[^/]+',      0, ('Observation diagrams for volume',              'DIAGDIR' )),
    (r'metadata/[^/]+/AAREADME.*', 0, ('Information about this metadata collection',   'INFO'    )),
    (r'metadata/[^/]+/[^/]+999',   0, ('Cumulative supplemental metadata for volumes', 'INDEXDIR')),
    (r'metadata/[^/]+/[^/]+',      0, ('Supplemental metadata for volume',             'INDEXDIR')),
    (r'previews/[^/]+/[^/]+',      0, ('Preview images for volume',                    'IMAGEDIR')),

    # Metadata directory file names
    (r'metadata/.*999.*_index\.tab',           0, ('Cumulative product index with RMS Node updates',   'INDEX')),
    (r'metadata/.*999.*_inventory\.(csv|tab)', 0, ('Cumulative list of observed bodies by product',    'INDEX')),
    (r'metadata/.*999.*_moon_summary\.tab',    0, ('Cumulative list of observed geometry on moons',    'INDEX')),
    (r'metadata/.*999.*_ring_summary\.tab',    0, ('Cumulative list of observed geometry on rings',    'INDEX')),
    (r'metadata/.*999.*_saturn_summary\.tab',  0, ('Cumulative list of observed geometry on Saturn',   'INDEX')),
    (r'metadata/.*999.*_jupiter_summary\.tab', 0, ('Cumulative list of observed geometry on Jupiter',  'INDEX')),
    (r'metadata/.*999.*_uranus_summary\.tab',  0, ('Cumulative list of observed geometry on Uranus',   'INDEX')),
    (r'metadata/.*999.*_neptune_summary\.tab', 0, ('Cumulative list of observed geometry on Neptune',  'INDEX')),
    (r'metadata/.*999.*_pluto_summary\.tab',   0, ('Cumulative list of observed geometry on Pluto',    'INDEX')),
    (r'metadata/.*999.*_charon_summary\.tab',  0, ('Cumulative list of observed geometry on Charon',   'INDEX')),
    (r'metadata/.*999.*_body_summary\.tab',    0, ('Cumulative observed geometry on planetary bodies', 'INDEX')),
    (r'metadata/.*999.*_sky_summary\.tab',     0, ('Cumulative observed sky coordinate geometry',      'INDEX')),

    (r'metadata/.*_index\.tab',           0, ('Product index with RMS Node updates',            'INDEX')),
    (r'metadata/.*_inventory\.(csv|tab)', 0, ('List of observed bodies by product',             'INDEX')),
    (r'metadata/.*_moon_summary\.tab',    0, ('Index of observed geometry on moons',            'INDEX')),
    (r'metadata/.*_ring_summary\.tab',    0, ('Index of observed geometry on rings',            'INDEX')),
    (r'metadata/.*_saturn_summary\.tab',  0, ('Index of observed geometry on Saturn',           'INDEX')),
    (r'metadata/.*_jupiter_summary\.tab', 0, ('Index of observed geometry on Jupiter',          'INDEX')),
    (r'metadata/.*_uranus_summary\.tab',  0, ('Index of observed geometry on Uranus',           'INDEX')),
    (r'metadata/.*_neptune_summary\.tab', 0, ('Index of observed geometry on Neptune',          'INDEX')),
    (r'metadata/.*_pluto_summary\.tab',   0, ('Index of observed geometry on Pluto',            'INDEX')),
    (r'metadata/.*_charon_summary\.tab',  0, ('Index of observed geometry on Charon',           'INDEX')),
    (r'metadata/.*_body_summary\.tab',    0, ('Index of observed geometry on planetary bodies', 'INDEX')),
    (r'metadata/.*_sky_summary\.tab',     0, ('Index of observed sky coordinate geometry',      'INDEX')),

    # Previews
    (r'previews/.*_thumb\.(jpg|png)',     0, ('Thumbnail preview image',        'BROWSE')),
    (r'previews/.*_small\.(jpg|png)',     0, ('Small preview image',            'BROWSE')),
    (r'previews/.*_med\.(jpg|png)',       0, ('Medium preview image',           'BROWSE')),
    (r'previews/.*_full\.(jpg|png)',      0, ('Full-resolution preview image',  'BROWSE')),
    (r'previews/.*',                      0, ('Preview images',                 'BROWDIR')),

    # Diagrams
    (r'diagrams/.*_thumb\.(jpg|png)',     0, ('Thumbnail observation diagram',  'DIAGRAM')),
    (r'diagrams/.*_small\.(jpg|png)',     0, ('Small observation diagram',      'DIAGRAM')),
    (r'diagrams/.*_med\.(jpg|png)',       0, ('Medium observation diagram',     'DIAGRAM')),
    (r'diagrams/.*_full\.(jpg|png)',      0, ('Large observation diagram',      'DIAGRAM')),
    (r'diagrams/.*',                      0, ('Observation diagrams',           'DIAGDIR')),

    # Standard information files
    (r'.*/aareadme\.(txt|vms)',         re.I, ('Read Me First!',                'INFO'    )),
    (r'.*/voldesc\.(cat|sfd)',          re.I, ('PDS3 volume description',       'INFO'    )),
    (r'.*/errata\.txt',                 re.I, ('Volume errata',                 'INFO'    )),
    (r'.*info\.txt',                    re.I, ('Info about this directory',     'INFO'    )),
    (r'.*/vicar2.txt',                  re.I, ('VICAR documentation',           'TECHINFO')),
    (r'.*/fitsinfo\..*',                re.I, ('FITS documentation',            'TECHINFO')),

    # Data file types, misc.
    (r'.*/easydata(/\w+)*',             re.I, ('Easy-to-use data',              'DATADIR' )),
    (r'.*/sorcdata(/\w+)*',             re.I, ('Original source data',          'DATADIR' )),
    (r'.*/spice(/\w+)*',                re.I, ('SPICE kernels',                 'GEOMDIR' )),

    # Browse directories
    (r'.*/browse(/\w+)*',               re.I, ('Browse image collection',       'BROWDIR' )),
    (r'.*/browse/.*\.(gif|jpg|jpeg|jpeg_small|tif|tiff|png)',
                                        re.I, ('Browse image',                  'BROWSE'  )),

    # Extras directories
    (r'.*/extras(/\w+)*',               re.I, ('Supplemental files',            'EXTRADIR')),

    # Document directories
    (r'.*/document/data.*sis\.[^L].*',  re.I, ('Data Format Description',       'TECHINFO')),
    (r'.*/document/dp.*sis\.[^L].*',    re.I, ('Data Format Description',       'TECHINFO')),
    (r'.*/document/.*edr.*sis\.[^L].*', re.I, ('Data Format Description',       'TECHINFO')),
    (r'.*/document/ar.*sis\.[^L].*',    re.I, ('PDS3 Archive Description',      'TECHINFO')),
    (r'.*/document/vol.*sis\.[^L].*',   re.I, ('PDS3 Archive Description',      'TECHINFO')),
    (r'.*/document/cd.*sis\.[^L].*',    re.I, ('PDS3 Archive Description',      'TECHINFO')),
    (r'.*/document/.*basis.*(txt|asc)', re.I, ('Text document',                 'TXTDOC'  )),
    (r'.*/document/.*basis.*\.pdf',     re.I, ('PDF document',                  'PDFDOC'  )),
    (r'.*/document/.*sis(|_.*)\.[^L].*',re.I, ('PDS3 Archive Description',      'TECHINFO')), # contains "sis_" or "sis.", but not "basis"
    (r'.*/document/.*\.(txt|asc)',      re.I, ('Text document',                 'TXTDOC'  )),
    (r'.*/document',                    re.I, ('Volume documentation',          'INFODIR' )),
    (r'.*/document(/\w+)+',             re.I, ('Documentation',                 'INFODIR' )),
    (r'.*/document/.*\.(gif|jpg|jpeg|tif|tiff|png)',
                                        re.I, ('Documentation figure',          'BROWSE'  )),

    # Software directories
    (r'.*/software(.*)/bin/\w+',        re.I, ('Program binary',                'CODE'    )),
    (r'.*/software(.*)README',          re.I, ('Software documentation',        'INFO'    )),
    (r'.*/software(.*)CHANGES',         re.I, ('Software documentation',        'INFO'    )),
    (r'.*/software(.*)Makefile.*',      re.I, ('Source code',                   'CODE'    )),
    (r'.*/software(/\w+)*',             re.I, ('Software directory',            'CODEDIR' )),
    (r'.*/software/.*\.(TXT|ASC)',      re.I, ('Software documentation',        'TXTDOC'  )),
    (r'.*/software/.*\.PDF',            re.I, ('Software documentation',        'PDFDOC'  )),
    (r'.*/software/.*\.(PS|EPS|HTM|HTML|DOC)',
                                        re.I, ('Software documentation',        'INFO'    )),

    # Catalog file names gleaned from the archives
    (r'.*/catalog(|/)',                 re.I, ('PDS3 Catalog files',            'INFODIR' )),
    (r'.*/catalog/DATASET\.CAT',        re.I, ('Data set description',          'PDSINFO' )),
    (r'.*/catalog/.*DS\.CAT',           re.I, ('Data set description',          'PDSINFO' )),
    (r'.*/catalog/.*DSCOLL\.CAT',       re.I, ('Collection description',        'PDSINFO' )),
    (r'.*/catalog/DS.*\.CAT',           re.I, ('Data set description',          'PDSINFO' )),
    (r'.*/catalog/.*(HOST|SC)\.CAT',    re.I, ('Instrument host description',   'PDSINFO' )),
    (r'.*/catalog/PERS\w*\.CAT',        re.I, ('Personnel summary',             'PDSINFO' )),
    (r'.*/catalog/.*_PERS\w*\.CAT',     re.I, ('Personnel summary',             'PDSINFO' )),
    (r'.*/catalog/MISSION\.CAT',        re.I, ('Mission description',           'PDSINFO' )),
    (r'.*/catalog/.*_MISSION\.CAT',     re.I, ('Mission description',           'PDSINFO' )),
    (r'.*/catalog/.*REF\.CAT',          re.I, ('Reference list',                'PDSINFO' )),
    (r'.*/catalog/.*INST\.CAT',         re.I, ('Instrument description',        'PDSINFO' )),
    (r'.*/catalog/.*RELEASE\.CAT',      re.I, ('Release information',           'PDSINFO' )),
    (r'.*/catalog/CALIBRATION\.CAT',    re.I, ('Calibration information',       'PDSINFO' )),
    (r'.*/catalog/.*TARGET\.CAT',       re.I, ('Target information',            'PDSINFO' )),
    (r'.*/catalog/SOFTWARE\.CAT',       re.I, ('Software information',          'PDSINFO' )),

    # Index files
    (r'.*/index/cum.*\.tab',            re.I, ('Cumulative index of data products',     'INDEX')),
    (r'.*/index/(img|)index\.tab',      re.I, ('Index of data products on this volume', 'INDEX')),

    # SPICE kernels
    (r'.*\.(bsp|xsp|spk)',              re.I, ('SPICE trajectory kernel',       'GEOM'    )),
    (r'.*\.(ck|bc)',                    re.I, ('SPICE pointing kernel',         'GEOM'    )),
    (r'.*\.(pck|tpc)',                  re.I, ('SPICE constants kernel',        'GEOM'    )),
    (r'.*\.tf',                         re.I, ('SPICE frames kernel',           'GEOM'    )),
    (r'.*\.ti',                         re.I, ('SPICE instrument kernel',       'GEOM'    )),
    (r'.*\.(lsk|tls)',                  re.I, ('SPICE leapseconds kernel',      'GEOM'    )),
    (r'.*\.tsc',                        re.I, ('SPICE spacecraft clock kernel', 'GEOM'    )),

    (r'.*/ck',                          re.I, ('SPICE pointing kernels',        'GEOMDIR' )),
    (r'.*/ek',                          re.I, ('SPICE events kernels',          'GEOMDIR' )),
    (r'.*/fk',                          re.I, ('SPICE frames kernels',          'GEOMDIR' )),
    (r'.*/ik',                          re.I, ('SPICE instrument kernels',      'GEOMDIR' )),
    (r'.*/lsk',                         re.I, ('SPICE leap seconds kernels',    'GEOMDIR' )),
    (r'.*/pck',                         re.I, ('SPICE constants kernels',       'GEOMDIR' )),
    (r'.*/sclk',                        re.I, ('SPICE SC clock kernels',        'GEOMDIR' )),
    (r'.*/spk',                         re.I, ('SPICE trajectory kernels',      'GEOMDIR' )),

    # Other standard directories
    (r'.*/calib(/\w+)*',                re.I, ('Calibration files',             'DATADIR' )),
    (r'.*/geometry(/\w+)*',             re.I, ('Geometry files',                'GEOMDIR' )),
    (r'.*/index',                       re.I, ('Index files',                   'INDEXDIR')),
    (r'.*/label',                       re.I, ('PDS3 label include files',      'LABELDIR')),
    (r'.*/data(/\w+)*',                 re.I, ('Data files',                    'DATADIR' )),

    # Standard file extensions, if nothing else worked
    (r'.*\.img',                        re.I, ('Binary image file',             'IMAGE'   )),
    (r'.*\.(tab|csv)',                  re.I, ('ASCII table',                   'TABLE'   )),
    (r'.*\.dat',                        re.I, ('Binary data file',              'DATA'    )),
    (r'.*\.fits{0,1}',                  re.I, ('FITS data file',                'DATA'    )),
    (r'.*\.(c|q)ub',                    re.I, ('Spectral image cube',           'CUBE'    )),
    (r'.*\.fmt',                        re.I, ('PDS3 label include file',       'LABEL'   )),
    (r'.*\.txt',                        re.I, ('Text file',                     'INFO'    )),
    (r'.*\.tar\.gz',                    re.I, ('Compressed tar archive',        'TARBALL' )),
    (r'.*\.tar',                        re.I, ('Tar archive',                   'TARBALL' )),
    (r'.*\.zip',                        re.I, ('Zip archive',                   'TARBALL' )),
    (r'.*\.(jpg|jpeg|jpeg_small)',      re.I, ('JPEG viewable image',           'BROWSE'  )),
    (r'.*\.gif',                        re.I, ('GIF vewable image',             'BROWSE'  )),
    (r'.*\.(tif|tiff)',                 re.I, ('TIFF viewable image',           'BROWSE'  )),
    (r'.*\.png',                        re.I, ('PNG viewable image',            'BROWSE'  )),
    (r'.*\.sav',                        re.I, ('IDL save file',                 'DATA'    )),

    (r'.*\.(f|for|f77|inc)',            re.I, ('FORTRAN source code',           'CODE'    )),
    (r'.*\.(c|h)',                      re.I, ('C source code',                 'CODE'    )),
    (r'.*\.cpp',                        re.I, ('C++ source code',               'CODE'    )),
    (r'.*\.py',                         re.I, ('Python source code',            'CODE'    )),
    (r'.*\.(sh|com|csh)',               re.I, ('Shell script',                  'CODE'    )),
    (r'.*\.(pro|idl)',                  re.I, ('IDL source code',               'CODE'    )),
    (r'.*\.(jar|java)',                 re.I, ('Java source code',              'CODE'    )),
    (r'.*\.(pl|pm)',                    re.I, ('Perl source code',              'CODE'    )),
    (r'.*\.a',                          re.I, ('Unix object library',           'CODE'    )),
    (r'.*\.o',                          re.I, ('Unix object file',              'CODE'    )),

    (r'.*\.asc',                        re.I, ('ASCII document',                'TXTDOC'  )),
    (r'.*\.pdf',                        re.I, ('PDF document',                  'PDFDOC'  )),
    (r'.*\.(eps|ps)',                   re.I, ('Postscript document',           'INFO'    )),
    (r'.*\.(htm|html)',                 re.I, ('HTML document',                 'INFO'    )),
    (r'.*\.doc',                        re.I, ('Word document',                 'INFO'    )),

    (r'',                               0,    ('Root directory',                'FOLDER'  )),
    (r'.*/[^\.]+',                      0,    ('Directory',                     'FOLDER'  )),
    (r'.*\..*',                         0,    ('Document',                      'UNKNOWN' )),
])

##########################################################################################
# ASSOCIATIONS
#
# Defines files associated with a given file. A dictionary of Translators keyed by 'volumes', 'calibrated', 'browse', 'diagrams',
# or 'metadata'.
#
# These Translators take a logical path and return logical paths of associated files based on the key.
##########################################################################################

ASSOCIATIONS = {
    'volumes'   : translator.TranslatorByRegex([
                        (r'documents/([A-Z][A-Z0-9x]{1,5}_....).*', 0, r'volumes/\1'),
                    ]),
    'previews'  : translator.NullTranslator(),
    'calibrated': translator.NullTranslator(),
    'diagrams'  : translator.NullTranslator(),
    'metadata'  : translator.TranslatorByRegex([
                        (r'metadata/([\w\.]+)/.*', 0, r'metadata/\1/AAREADME.txt'),
                        (r'volumes/([A-Z][A-Z0-9x]{1,5}_....)(|_[\w\.]+)/([\w]+)/index', re.I,
                            r'metadata/\1/\3'),
                        (r'volumes/([A-Z][A-Z0-9x]{1,5}_....)(|_[\w\.]+)/([\w]+)/index/(img|)index\..*', re.I,
                            [r'metadata/\1/\3/\3_index.tab',
                             r'metadata/\1/\3/\3_index.lbl',
                            ]),
                        (r'volumes/([A-Z][A-Z0-9x]{1,5}_....)(|_[\w\.]+)/([\w]+)\d\d\d/index/cumindex\..*', re.I,
                            [r'metadata/\1/\g<3>999/\g<3>999_index.tab',
                             r'metadata/\1/\g<3>999/\g<3>999_index.lbl',
                            ]),
                    ]),
    'documents' : translator.TranslatorByRegex([
                        (r'(volumes|calibrated)/(\w+)(|\.[\w\.]+)', 0,
                            r'documents/\2/*'),
                        (r'(volumes|calibrated)/(\w+)(|\.[\w\.]+)/\w+', 0,
                            r'documents/\2/*'),
                        (r'(volumes|calibrated)/(\w+)(|\.[\w\.]+)/\w+/.+', 0,
                            r'documents/\2'),
                        (r'volumes/([\w\.]+/\w+)(|/.*)', 0,
                            [r'volumes/\1/document',
                             r'volumes/\1/catalog',
                             r'volumes/\1/aareadme.txt',
                             r'volumes/\1/errata.txt',
                             r'volumes/\1/voldesc.cat',
                             r'volumes/\1/DOCUMENT',
                             r'volumes/\1/CATALOG',
                             r'volumes/\1/AAREADME.TXT',
                             r'volumes/\1/ERRATA.TXT',
                             r'volumes/\1/VOLDESC.CAT',
                             r'volumes/\1/VOLDESC.SFD',
                            ]),
                        (r'previews/([\w\.]+)(|/.*)', 0,
                            [r'previews/\1/AAREADME.pdf',
                             r'previews/\1/AAREADME.txt',
                            ]),
                    ]),
}

##########################################################################################
# VERSIONS
#
# Defines a list of files defining all the versions of a given product, given the product's logical path.
##########################################################################################

VERSIONS = translator.TranslatorByRegex([

    # Match any file with the same path , ignoring for the version number suffix on the volset ID
    (r'([a-z-]+/[A-Z][A-Z0-9x]{1,5}_[0-9x]{4})(|_[\w\.]+)(|/.*)', 0, r'\1*\3'),
    (r'(checksums-archives)-([a-z]+)/([A-Z][A-Z0-9x]{1,5}_[0-9x]{4})(|_[\w\.]+)_\2(_md5\.txt|\.tar\.gz)', 0, r'\1-\2/\3*_\2\5'),
    (r'(checksums-archives-volumes/[A-Z][A-Z0-9x]{1,5}_[0-9x]{4})(|_[\w\.]+)(_md5\.txt|\.tar\.gz)', 0, r'\1*\3'),

    # For category-level directories
    (r'([a-z-]+)', 0, r'\1'),

    # Match *inventory.csv with *inventory.tab inside a metadata tree
    (r'(metadata/[A-Z][A-Z0-9x]{1,5}_[0-9x]{4})(|_v[0-9\.]+)/(.*inventory)\.(tab|csv)', 0,
            [r'\1*\3.tab',
             r'\1*\3.csv',
            ]),
])

##########################################################################################
# VIEWABLES
#
# A dictionary of translators, each of which translates a file path to a set of viewables. The key 'default' defines the viewable
# used by default.
##########################################################################################

VIEWABLES = {'default': translator.NullTranslator()}

VIEWABLE_TOOLTIPS = {
    'default': 'Default browse product for this observation',
}

##########################################################################################
# VIEW_OPTIONS
#
# Given a file path, returns (grid_flag, multipage_flag, continuous_flag). Each flag indicates True if that particular options is
# allowed for this directory.
##########################################################################################

VIEW_OPTIONS = translator.TranslatorByRegex([
    (r'.*', 0, (False, False, False)),       # default is for single-page viewing
])

##########################################################################################
# NEIGHBORS
#
# Given a directory path, return the file fnmatch pattern to indicate other logical paths to directories to be treated as adjacent.
##########################################################################################

NEIGHBORS = translator.TranslatorByRegex([
    (r'(.*)/[^/]+', 0, r'\1/*'),
])

##########################################################################################
# SIBLINGS
#
# Given a logical file path, return the fnmatch pattern to match other basenames to be treated as adjacent within the same
# directory. If a SIBLINGS rule is unspecified, default behavior is to use a match pattern defined by the concatenation of "*" and
# the second and third results of the SPLIT_RULE.
##########################################################################################

SIBLINGS = translator.TranslatorByRegex([
    # In document/, calib/, catalog/, index/, label/, and root, all files are siblings
    (r'(volumes|calibrated)/[^/]+/[^/]+/(document|calib|catalog|index|label)/.*', re.I, '*'),
    (r'(\w+-?\w+-?\w+)/[^/]+/[^/]+/[^/]+', re.I, '*'),
    (r'(\w+-?\w+-?\w+)/[^/]+/[^/]+',       re.I, '*'),
    (r'(\w+-?\w+-?\w+)/[^/]+',             re.I, '*'),
])

##########################################################################################
# INFO_FILE_BASENAMES
#
# Translates a file basename it itself if it is a suitable information file about the directory in which it is found.
##########################################################################################

INFO_FILE_BASENAMES = translator.TranslatorByRegex([
    (r'(voldesc\.(?:cat|sfd))', re.I, r'\1'),
    (r'(\w+INFO\.txt)',         re.I, r'\1'),
    (r'(\w+INF\.txt)',          re.I, r'\1'),
    (r'(\w+DOC\.txt)',          re.I, r'\1'),
    (r'(AAREADME\.txt)',        re.I, r'\1'),
    (r'(README\.txt)',          re.I, r'\1'),
])

##########################################################################################
# SORT_KEY
#
# Translates a file basename into a key used for sorting. For example, this is used to force COISS data files to sort
# chronologically, by ignoring the leading "N" or "W".
##########################################################################################

SORT_KEY = translator.TranslatorByRegex([

    # Previews sort into increasing size
    (r'(.*)_thumb\.(jpg|png)', 0, r'\1_4thumb.\2'),
    (r'(.*)_small\.(jpg|png)', 0, r'\1_3small.\2'),
    (r'(.*)_med\.(jpg|png)',   0, r'\1_2med.\2'  ),
    (r'(.*)_full\.(jpg|png)',  0, r'\1_1full.\2' ),

    # Sort volume sets with version numbers decreasing
    (r'([A-Z0-9x]+_[0-9x]{3}x)(_lien_resolution)', 0, r'\1_002\2'),
    (r'([A-Z0-9x]+_[0-9x]{3}x)(_peer_review)',     0, r'\1_003\2'),
    (r'([A-Z0-9x]+_[0-9x]{3}x)(_prelim)',          0, r'\1_004\2'),
    (r'([A-Z0-9x]+_[0-9x]{3}x)(_in_prep)',         0, r'\1_005\2'),
    (r'([A-Z0-9x]+_[0-9x]{3}x)(_v1|_v1\.0)',       0, r'\1_900\2'),
    (r'([A-Z0-9x]+_[0-9x]{3}x)(_v2|_v2\.0)',       0, r'\1_800\2'),
    (r'([A-Z0-9x]+_[0-9x]{3}x)(_v3|_v3\.0)',       0, r'\1_700\2'),
    (r'([A-Z0-9x]+_[0-9x]{3}x)(_v4|_v4\.0)',       0, r'\1_600\2'),
    (r'([A-Z0-9x]+_[0-9x]{3}x)(_v5|_v5\.0)',       0, r'\1_500\2'),

    (r'([A-Z0-9x]+_[0-9x]{3}x)(_v1\.1)',           0, r'\1_890\2'),
    (r'([A-Z0-9x]+_[0-9x]{3}x)(_v1\.2)',           0, r'\1_880\2'),
    (r'([A-Z0-9x]+_[0-9x]{3}x)(_v1\.3)',           0, r'\1_870\2'),
    (r'([A-Z0-9x]+_[0-9x]{3}x)(_v2\.1)',           0, r'\1_790\2'),
    (r'([A-Z0-9x]+_[0-9x]{3}x)(_v2\.2)',           0, r'\1_780\2'),
    (r'([A-Z0-9x]+_[0-9x]{3}x)(_v2\.3)',           0, r'\1_770\2'),

    # PDS links sort first
    (r'(PDS.*)\.link', 0, r'  \1.link'),    # space is the lowest ASCII char

    # If all else fails, sort alphabetically
    (r'(.*)', 0, r'\1'),
])

##########################################################################################
# SPLIT_RULES
#
# Used for defining how to group files by separating a leading anchor, which is possibly shared among multiple files, with an
# optional middle part and an extension.
#
# These translations take a file basename and return a tuple of three strings that concatenate to the original basename.
#
# Note that they must also work for the sort keys of basenames.
##########################################################################################

SPLIT_RULES = translator.TranslatorByRegex([

    # Preview files (before and after SORT_RULES were applied)
    (r'(.*)_(thumb|small|med|full)\.(jpg|png)',     0, (r'\1', r'_\2', r'.\3')),
    (r'(.*)_(1thumb|2small|3med|9full)\.(jpg|png)', 0, (r'\1', r'_\2', r'.\3')),

    # Calibrated images
    (r'(.*)(_CALIB)\.(IMG|LBL)', re.I, (r'\1', r'\2', r'.\3')),

    # If all else fails, split at last period
    (r'(.*)(\..*)', 0, (r'\1', '', r'\2')),
    (r'(.*)',       0, (r'\1', '', '')),
])

##########################################################################################
# OPUS_TYPE
#
# Used for indicating the type of a data file as it will appear in OPUS, e.g., "Raw Data", "Calibrated Data", etc. The tuple
# returned is (category, rank, slug, title) where:
#   category is 'browse', 'diagram', or a meaningful header for special cases like 'Voyager ISS', 'Cassini CIRS'
#   rank is the sort order within the category
#   slug is a short string that will appear in URLs
#   title is a meaning title for product, e.g., 'Raw Data (when calibrated is unavailable)'
#
# These translations take a file's logical path and return a string indicating the file's OPUS_TYPE.
##########################################################################################

OPUS_TYPE = translator.TranslatorByRegex([

    # Previews
    (r'test/.*\_thumb\..*',     0, ('browse', 10, 'browse_thumb',  'Browse Image (thumbnail)', False)),
    (r'previews/.*\_thumb\..*', 0, ('browse', 10, 'browse_thumb',  'Browse Image (thumbnail)', False)),
    (r'previews/.*\_small\..*', 0, ('browse', 20, 'browse_small',  'Browse Image (small)',     False)),
    (r'previews/.*\_med\..*',   0, ('browse', 30, 'browse_medium', 'Browse Image (medium)',    False)),
    (r'previews/.*\_full\..*',  0, ('browse', 40, 'browse_full',   'Browse Image (full)',      True)),

    # Diagrams
    (r'diagrams/.*\_thumb\..*', 0, ('diagram', 10, 'diagram_thumb',  'Browse Diagram (thumbnail)', False)),
    (r'diagrams/.*\_small\..*', 0, ('diagram', 20, 'diagram_small',  'Browse Diagram (small)',     False)),
    (r'diagrams/.*\_med\..*',   0, ('diagram', 30, 'diagram_medium', 'Browse Diagram (medium)',    False)),
    (r'diagrams/.*\_full\..*',  0, ('diagram', 40, 'diagram_full',   'Browse Diagram (full)',      True)),

    # Metadata
    (r'metadata/.*_inventory\..*',             0, ('metadata', 10, 'inventory',       'Target Body Inventory', False)),
    (r'metadata/.*_(jupiter|saturn|uranus|neptune|pluto)_summary\..*',
                                               0, ('metadata', 20, 'planet_geometry', 'Planet Geometry Index', False)),
    (r'metadata/.*_(moon|charon)_summary\..*', 0, ('metadata', 30, 'moon_geometry',   'Moon Geometry Index',   False)),
    (r'metadata/.*_body_summary\..*',          0, ('metadata', 40, 'body_geometry',   'Body Geometry Index',   False)),
    (r'metadata/.*_ring_summary\..*',          0, ('metadata', 50, 'ring_geometry',   'Ring Geometry Index',   False)),
    (r'metadata/.*_sky_summary\..*',           0, ('metadata', 60, 'sky_geometry',    'Sky Geometry Index',   False)),

    # Metadata index
    (r'metadata/.*_\d+_index\..*',         0, ('metadata', 5, 'rms_index',          'RMS Node Augmented Index',     False)),
    (r'metadata/.*_hstfiles\..*',          0, ('metadata', 6, 'hstfiles_index',     'HST Files Associations Index', False)),
    (r'metadata/.*raw_image_index\..*',    0, ('metadata', 7, 'raw_image_index',    'Raw Image Index',              False)),
    (r'metadata/.*supplemental_index\..*', 0, ('metadata', 8, 'supplemental_index', 'Supplemental Index',           False)),
])

##########################################################################################
# OPUS_FORMAT
#
# Returns a tuple (interchange format, file format) where the first is 'Binary', 'ASCII' or 'UTF-8' and the latter is the format
# of the file, e.g., 'Vicar', 'FITS', 'Table', 'PDS3 Label', etc.
##########################################################################################

OPUS_FORMAT = translator.TranslatorByRegex([
    (r'.*\.LBL',   re.I, ('ASCII',  'PDS3 Label')),
    (r'.*\.TAB',   re.I, ('ASCII',  'Table')),
    (r'.*\.FMT',   re.I, ('ASCII',  'PDS3 Format File')),
    (r'.*\.CSV',   re.I, ('ASCII',  'Comma-Separated Values')),
    (r'.*\.TXT',   re.I, ('ASCII',  'Text')),
    (r'.*\.ASC',   re.I, ('ASCII',  'Text')),
    (r'.*\.FITS?', re.I, ('Binary', 'FITS')),
    (r'.*\.TIFF?', re.I, ('Binary', 'TIFF')),
    (r'.*\.JPE?G', re.I, ('Binary', 'JPEG')),
    (r'.*\.GIF',   re.I, ('Binary', 'GIF')),
    (r'.*\.PNG',   re.I, ('Binary', 'PNG')),
    (r'.*\.PDF',   re.I, ('Binary', 'PDF')),
    (r'.*\.E?PS',  re.I, ('Binary', 'Postscript')),
    (r'.*\.BSP',   re.I, ('Binary', 'SPICE SPK')),
    (r'.*\.BC',    re.I, ('Binary', 'SPICE CK')),
    (r'.*\.TPC',   re.I, ('ASCII',  'SPICE PCK')),
    (r'.*\.TLS',   re.I, ('ASCII',  'SPICE LSK')),
    (r'.*\.TI',    re.I, ('ASCII',  'SPICE IK')),
])

##########################################################################################
# OPUS_PRODUCTS
#
# Returns a list of glob.glob() patterns that match the absolute paths to the all associated files for an OPUS
# query, given the logical path to the primary data file or its label.
##########################################################################################

# Default is to return an empty list
OPUS_PRODUCTS = translator.TranslatorByRegex([
    # (r'.*', 0, []),
    (r'volumes/([A-Z0-9a-z]+_[A-Z0-9a-z]+).*', 0, [r'documents/\1/*.[!lz]*'])
])

##########################################################################################
# OPUS_ID
#
# Translates an absolute or logical path to an OPUS ID.
##########################################################################################

OPUS_ID = translator.TranslatorByRegex([])

##########################################################################################
# OPUS_ID_TO_SUBCLASS
#
# Translates an OPUS ID to a PdsFile subclass.
##########################################################################################

OPUS_ID_TO_SUBCLASS = translator.TranslatorByRegex([])

##########################################################################################
# OPUS_ID_TO_PRIMARY_LOGICAL_PATH
#
# Translates an OPUS ID to a regular expression that matches the path (absolute or logical) of the primary data file.
# Note: This is a class attribute, not an object attribute. It is shared by all subclasses.
##########################################################################################

OPUS_ID_TO_PRIMARY_LOGICAL_PATH = translator.TranslatorByRegex([])

##########################################################################################
# FILESPEC_TO_BUNDLESET
#
# Translates a file specification, starting from the volume ID, to a logical path. It is shared by all subclasses. Default behavior
# is to replace the last three characters of the volume name by "xxx". This needs to be overridden for volsets that have a different
# number of x's in their names.
##########################################################################################

FILESPEC_TO_BUNDLESET = translator.TranslatorByRegex([
    (r'([A-Z0-9]{2,6}_\d)\d{3}.*', 0, r'\1xxx'),
])

##########################################################################################
# LID_AFTER_DSID
# Translates a PDS3 file path (absolute or logical) to a PDS4 LID starting after the data set ID. The returned format is:
#       volume_id:directory_tree:filename
##########################################################################################

LID_AFTER_DSID = translator.TranslatorByRegex([
    (r'.*volumes/(\w+)/(\w+)/(.*)/(\w+\..*)',  0, r'\2:\3:\4'),
])

##########################################################################################
# DATA_SET_ID
# Translates a file path (absolute or logical) to a data set ID.
##########################################################################################

DATA_SET_ID = translator.NullTranslator()

##########################################################################################
