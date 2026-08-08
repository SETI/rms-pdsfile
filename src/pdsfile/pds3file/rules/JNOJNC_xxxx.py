##########################################################################################
# pds3file/rules/JNOJNC_xxxx.py
##########################################################################################

"""Rules for the JunoCam volume set: Jupiter images from JunoCam.

The volume set on disk is JNOJNC_0xxx, described in the holdings as the JunoCam
Jupiter image collection; its volumes are numbered by orbit and carry data set IDs
JUNO-J-JUNOCAM-2-EDR-L0-V1.0, JUNO-J-JUNOCAM-3-RDR-L1A-V1.0 and, from JNOJNC_0007
on, JUNO-J-JUNOCAM-4-RDR-L1B-V1.0 (``_volinfo/JNOJNC_0xxx.txt``). The subclass and
this module are named JNOJNC_xxxx, and the volume set translator is what maps the
volume set name JNOJNC_0xxx onto that subclass; the two names are not the same
string, which is unusual among these modules.

A product is a raw or calibrated binary image, either RGB or methane-band, and
volumes hold derived global maps as well as the images themselves.

The rule tables:

* ``description_and_icon_by_regex`` -- distinguishes raw from calibrated and RGB
  from methane-band, for both the images and the derived global maps; names the
  directories that organize images by target and by orbit; and names the small,
  medium and full-resolution browse directories and their PNGs.
* ``default_viewables`` -- points an image at its browse PNGs.
* ``associations_to_volumes`` and ``associations_to_metadata`` -- cross the volumes
  and metadata trees for one image.
* ``neighbors`` -- the corresponding directories in sibling volumes.

This module defines no OPUS tables, so OPUS behavior comes from the defaults in
`pds3file/rules/__init__.py`.
"""

import re

import translator

import pdsfile.pds3file as pds3file

##########################################################################################
# DESCRIPTION_AND_ICON
##########################################################################################

description_and_icon_by_regex = translator.TranslatorByRegex([
    (r'volumes/.*/DATA',                                0, ('Image files',                                 'IMAGEDIR')),
    (r'volumes/.*/DATA/GLOBAL_MAPS',                    0, ('Derived global maps ordered by date',         'IMAGEDIR')),
    (r'volumes/.*/DATA/GLOBAL_MAPS/\w+_\d\dH\w+\.IMG',  0, ('Methane-band binary map',                     'IMAGE'   )),
    (r'volumes/.*/DATA/GLOBAL_MAPS/\w+_\d\dP\w+\.IMG',  0, ('RGB binary map',                              'IMAGE'   )),
    (r'volumes/.*/DATA/EDR',                            0, ('Raw image files organized by target',         'IMAGEDIR')),
    (r'volumes/.*/DATA/RDR',                            0, ('Calibrated image files organized by target',  'IMAGEDIR')),
    (r'volumes/.*/DATA/EDR/\w+',                        0, ('Raw image files organized by orbit',          'IMAGEDIR')),
    (r'volumes/.*/DATA/RDR/\w+',                        0, ('Calibrated image files organized by orbit',   'IMAGEDIR')),
    (r'volumes/.*/DATA/EDR/\w+/\w+_\d\dC\w+\.IMG',      0, ('Raw binary RGB image file',                   'IMAGE'   )),
    (r'volumes/.*/DATA/EDR/\w+/\w+_\d\dM\w+\.IMG',      0, ('Raw binary methane-band image file',          'IMAGE'   )),
    (r'volumes/.*/DATA/RDR/\w+/\w+_\d\dC\w+\.IMG',      0, ('Calibrated binary RGB image file',            'IMAGE'   )),
    (r'volumes/.*/DATA/RDR/\w+/\w+_\d\dM\w+\.IMG',      0, ('Calibrated binary methane-band image file',   'IMAGE'   )),
    (r'volumes/.*/DATA/RDR/\w+/\w+\.IMG',               0, ('Calibrated binary RGB image file',            'IMAGE'   )),

    (r'volumes/.*/EXTRAS',                              0, ('Browse images',                               'BROWDIR')),
    (r'volumes/.*/EXTRAS/THUMBNAIL',                    0, ('Small browse images (up to 256x256)',         'BROWDIR')),
    (r'volumes/.*/EXTRAS/BROWSE',                       0, ('Medium browse images (up to 2048x2048)',      'BROWDIR')),
    (r'volumes/.*/EXTRAS/FULL',                         0, ('Full-resolution browse images',               'BROWDIR')),

    (r'volumes/.*/EXTRAS/THUMBNAIL/GLOBAL_MAPS',        0, ('Small browse maps ordered by date',           'BROWDIR')),
    (r'volumes/.*/EXTRAS/THUMBNAIL/.DR',                0, ('Small browse images organized by target',     'BROWDIR')),
    (r'volumes/.*/EXTRAS/THUMBNAIL/.DR/\w+',            0, ('Small browse images organized by orbit',      'BROWDIR')),

    (r'volumes/.*/EXTRAS/BROWSE/GLOBAL_MAPS',           0, ('Medium browse maps ordered by date',          'BROWDIR')),
    (r'volumes/.*/EXTRAS/BROWSE/.DR',                   0, ('Medium browse images organized by target',    'BROWDIR')),
    (r'volumes/.*/EXTRAS/BROWSE/.DR/\w+',               0, ('Medium browse images organized by orbit',     'BROWDIR')),

    (r'volumes/.*/EXTRAS/FULL/GLOBAL_MAPS',             0, ('Full-size browse maps ordered by date',       'BROWDIR')),
    (r'volumes/.*/EXTRAS/FULL/.DR',                     0, ('Full-size browse images organized by target', 'BROWDIR')),
    (r'volumes/.*/EXTRAS/FULL/.DR/\w+',                 0, ('Full-size browse images organized by orbit',  'BROWDIR')),

    (r'volumes/.*/EXTRAS/THUMBNAIL/.*\.PNG',            0, ('Small browse PNG',                            'BROWSE' )),
    (r'volumes/.*/EXTRAS/BROWSE/.*\.PNG',               0, ('Medium browse PNG',                           'BROWSE' )),
    (r'volumes/.*/EXTRAS/FULL/.*\.PNG',                 0, ('Full-size browse PNG',                        'BROWSE' )),
])

##########################################################################################
# ASSOCIATIONS
##########################################################################################

associations_to_volumes = translator.TranslatorByRegex([
    # associate raw and calibrated files and browse products of (almost) the same name
    (r'volumes/(JNOJNC_0xxx/JNOJNC_0\d\d\d)/(DATA|EXTRAS/\w+)/(E|R)DR/(.*/JNC)[ER]_(\w+)\.(IMG|PNG)', 0,
            [r'volumes/\1/DATA/EDR/\4E_\5.IMG',
             r'volumes/\1/DATA/RDR/\4R_\5.IMG',
             r'volumes/\1/EXTRAS/THUMBNAIL/\3DR/\4\3_\5.PNG',
             r'volumes/\1/EXTRAS/BROWSE/\3DR/\4\3_\5.PNG',
             r'volumes/\1/EXTRAS/FULL/\3DR/\4\3_\5.PNG',
            ]),
    # associate global maps with browse products
    (r'volumes/(JNOJNC_0xxx/JNOJNC _0\d\d\d)/(DATA|EXTRAS/\w+)/(GLOBAL_MAPS/JNCR_\w+)\.(IMG|PNG)', 0,
            [r'volumes/\1/DATA/\3.IMG',
             r'volumes/\1/EXTRAS/THUMBNAIL/\3.PNG',
             r'volumes/\1/EXTRAS/BROWSE/\3.PNG',
             r'volumes/\1/EXTRAS/FULL/\3.PNG',
            ]),
])

associations_to_metadata = translator.TranslatorByRegex([
    (r'volumes/(JNOJNC_0xxx)/(JNOJNC_0\d\d\d)/DATA/.*/(JNC\w+\.IMG)', 0,
            r'metadata/\1/\2/\2_index.tab/\3',
            ),
])

##########################################################################################
# VIEWABLES
##########################################################################################

default_viewables = translator.TranslatorByRegex([
    (r'.*\.LBL', re.I, ''),
    (r'volumes/(JNOJNC_0xxx/JNOJNC_0\d\d\d)/(DATA|EXTRAS/\w+)/(.*/JNC\w+)\.(IMG|PNG)', 0,
            [r'volumes/\1/EXTRAS/THUMBNAIL/\3.PNG',
            ]),                 # the internal previews can work for now
])

##########################################################################################
# NEIGHBORS
##########################################################################################

neighbors = translator.TranslatorByRegex([
    (r'volumes/(JNOJNC_0xxx/JNOJNC_0)\d\d\d',                                0, r'volumes/\1???'),
    (r'volumes/(JNOJNC_0xxx/JNOJNC_0)\d\d\d/DATA',                           0, r'volumes/\1???/DATA'),
    (r'volumes/(JNOJNC_0xxx/JNOJNC_0)\d\d\d/(DATA/\w)',                      0, r'volumes/\1???/\2'),
    (r'volumes/(JNOJNC_0xxx/JNOJNC_0)\d\d\d/(DATA/[ER]DR)/\w+',              0, r'volumes/\1???/\2/*'),
    (r'volumes/(JNOJNC_0xxx/JNOJNC_0)\d\d\d/(DATA/[ER]DR)/\w+/(ORBIT_\d\d)', 0, r'volumes/\1???/\2/*/ORBIT_??'),
])

##########################################################################################
# Subclass definition
##########################################################################################

class JNOJNC_xxxx(pds3file.Pds3File):
    """The ``Pds3File`` subclass for JNOJNC_xxxx.

    The class body puts this module's rule tables in front of the class attributes
    ``Pds3File`` reads, and the module tail registers the class in
    ``Pds3File.SUBCLASSES`` under the key "JNOJNC_xxxx".
    The module docstring describes the volume set and every table.
    """

    pds3file.Pds3File.VOLSET_TRANSLATOR = translator.TranslatorByRegex([('JNOJNC_0xxx', re.I, 'JNOJNC_xxxx')]) + \
                                          pds3file.Pds3File.VOLSET_TRANSLATOR

    DESCRIPTION_AND_ICON = description_and_icon_by_regex + pds3file.Pds3File.DESCRIPTION_AND_ICON
    NEIGHBORS = neighbors + pds3file.Pds3File.NEIGHBORS

    ASSOCIATIONS = pds3file.Pds3File.ASSOCIATIONS.copy()
    ASSOCIATIONS['volumes'] += associations_to_volumes
    ASSOCIATIONS['metadata'] += associations_to_metadata

    VIEWABLES = {'default': default_viewables}

##########################################################################################
# Update the global dictionary of subclasses
##########################################################################################

pds3file.Pds3File.SUBCLASSES['JNOJNC_xxxx'] = JNOJNC_xxxx

##########################################################################################
