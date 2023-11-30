##########################################################################################
# pds3file/rules/VG_0xxx.py
##########################################################################################

import pdsfile.pds3file as pds3file
import translator
import re

##########################################################################################
# DESCRIPTION_AND_ICON
##########################################################################################

description_and_icon_by_regex = translator.TranslatorByRegex([
    (r'volumes/.*\.IBG',               re.I,   ('Compressed browse image',            'IMAGE'   )),
    (r'volumes/.*\.IMQ',               re.I,   ('Compressed raw image, VICAR',        'IMAGE'   )),
    (r'volumes/.*/BROWSE(|/w+)',       re.I,   ('Compressed browse images',           'IMAGEDIR')),
    (r'volumes/VG_0xxx/VG_0.../(?!DOCUMENT)(?!INDEX)(?!LABEL)(?!SOFTWARE).*/C[0-9]+X+',
                                       re.I,   ('Image files grouped by SC clock',    'IMAGEDIR')),
    (r'volumes/VG_0xxx/VG_0.../(?!DOCUMENT)(?!INDEX)(?!LABEL)(?!SOFTWARE)\w+',
                                       re.I,   ('Image files grouped by target',      'IMAGEDIR')),
])

##########################################################################################
# VIEWABLES
##########################################################################################

default_viewables = translator.TranslatorByRegex([
    (r'volumes/VG_0xxx/VG_000[1-3]/.*/(C[0-9]{5})([0-9]{2})\.(IMQ|IBG)', 0, r'previews/VGISS_7xxx/VGISS_7???/DATA/\1XX/\1\2_*.jpg'),
    (r'volumes/VG_0xxx/VG_000[45]/.*/(C[0-9]{5})([0-9]{2})\.(IMQ|IBG)',  0, r'previews/VGISS_6xxx/VGISS_6???/DATA/\1XX/\1\2_*.jpg'),
    (r'volumes/VG_0xxx/VG_000[6-8]/.*/(C[0-9]{5})([0-9]{2})\.(IMQ|IBG)', 0, r'previews/VGISS_5xxx/VGISS_5???/DATA/\1XX/\1\2_*.jpg'),
    (r'volumes/VG_0xxx/VG_0009/.*/(C[0-9]{5})([0-9]{2})\.(IMQ|IBG)',     0, r'previews/VGISS_8xxx/VGISS_8???/DATA/\1XX/\1\2_*.jpg'),
    (r'volumes/VG_0xxx/VG_001[0-2]/.*/(C[0-9]{5})([0-9]{2})\.(IMQ|IBG)', 0, r'previews/VGISS_8xxx/VGISS_8???/DATA/\1XX/\1\2_*.jpg'),
    (r'volumes/VG_0xxx/VG_001[3-9]/.*/(C[0-9]{5})([0-9]{2})\.(IMQ|IBG)', 0, r'previews/VGISS_5xxx/VGISS_51??/DATA/\1XX/\1\2_*.jpg'),
    (r'volumes/VG_0xxx/VG_0020/.*/(C[0-9]{5})([0-9]{2})\.(IMQ|IBG)',     0, r'previews/VGISS_5xxx/VGISS_5???/DATA/\1XX/\1\2_*.jpg'),
    (r'volumes/VG_0xxx/VG_002[1-5]/.*/(C[0-9]{5})([0-9]{2})\.(IMQ|IBG)', 0, r'previews/VGISS_5xxx/VGISS_52??/DATA/\1XX/\1\2_*.jpg'),
    (r'volumes/VG_0xxx/VG_002[6-9]/.*/(C[0-9]{5})([0-9]{2})\.(IMQ|IBG)', 0, r'previews/VGISS_6xxx/VGISS_61??/DATA/\1XX/\1\2_*.jpg'),
    (r'volumes/VG_0xxx/VG_003[0-2]/.*/(C[0-9]{5})([0-9]{2})\.(IMQ|IBG)', 0, r'previews/VGISS_6xxx/VGISS_61??/DATA/\1XX/\1\2_*.jpg'),
    (r'volumes/VG_0xxx/VG_0033/.*/(C[0-9]{5})([0-9]{2})\.(IMQ|IBG)',     0, r'previews/VGISS_6xxx/VGISS_6???/DATA/\1XX/\1\2_*.jpg'),
    (r'volumes/VG_0xxx/VG_003[4-8]/.*/(C[0-9]{5})([0-9]{2})\.(IMQ|IBG)', 0, r'previews/VGISS_6xxx/VGISS_62??/DATA/\1XX/\1\2_*.jpg'),
])

##########################################################################################
# ASSOCIATIONS
##########################################################################################

associations_to_volumes = translator.TranslatorByRegex([
    (r'volumes/VG_0xxx/VG_000[1-3]/(.*)\.IMQ', 0, r'volumes/VG_0xxx/VG_0003/BROWSE/\1.IBG'),
    (r'volumes/VG_0xxx/VG_000[4-5]/(.*)\.IMQ', 0, r'volumes/VG_0xxx/VG_0005/BROWSE/\1.IBG'),
    (r'volumes/VG_0xxx/VG_000[6-8]/(.*)\.IMQ', 0, r'volumes/VG_0xxx/VG_0008/BROWSE/\1.IBG'),
    (r'volumes/VG_0xxx/(VG_00..)/(.*)\.IMQ',   0, r'volumes/VG_0xxx/\1/BROWSE/\2.IBG'),

    (r'volumes/VG_0xxx/VG_0003/BROWSE/(.*)\.IBG',   0, r'volumes/VG_0xxx/VG_000[123]/\1.IMQ'),
    (r'volumes/VG_0xxx/VG_0005/BROWSE/(.*)\.IBG',   0, r'volumes/VG_0xxx/VG_000[45]/\1.IMQ'),
    (r'volumes/VG_0xxx/VG_0008/BROWSE/(.*)\.IBG',   0, r'volumes/VG_0xxx/VG_000[678]/\1.IMQ'),
    (r'volumes/VG_0xxx/(VG_00..)/BROWSE/(.*)\.IBG', 0, r'volumes/VG_0xxx/\1/\2.IBG'),

    (r'volumes/VG_0xxx/VG_000[1-3]/.*/(C[0-9]{5})([0-9]{2})\.(IMQ|IBG)', 0, r'volumes/VGISS_7xxx/VGISS_7???/DATA/\1XX/\1\2_*'),
    (r'volumes/VG_0xxx/VG_000[45]/.*/(C[0-9]{5})([0-9]{2})\.(IMQ|IBG)',  0, r'volumes/VGISS_6xxx/VGISS_6???/DATA/\1XX/\1\2_*'),
    (r'volumes/VG_0xxx/VG_000[6-8]/.*/(C[0-9]{5})([0-9]{2})\.(IMQ|IBG)', 0, r'volumes/VGISS_5xxx/VGISS_5???/DATA/\1XX/\1\2_*'),
    (r'volumes/VG_0xxx/VG_0009/.*/(C[0-9]{5})([0-9]{2})\.(IMQ|IBG)',     0, r'volumes/VGISS_8xxx/VGISS_8???/DATA/\1XX/\1\2_*'),
    (r'volumes/VG_0xxx/VG_001[0-2]/.*/(C[0-9]{5})([0-9]{2})\.(IMQ|IBG)', 0, r'volumes/VGISS_8xxx/VGISS_8???/DATA/\1XX/\1\2_*'),
    (r'volumes/VG_0xxx/VG_001[3-9]/.*/(C[0-9]{5})([0-9]{2})\.(IMQ|IBG)', 0, r'volumes/VGISS_5xxx/VGISS_51??/DATA/\1XX/\1\2_*'),
    (r'volumes/VG_0xxx/VG_0020/.*/(C[0-9]{5})([0-9]{2})\.(IMQ|IBG)',     0, r'volumes/VGISS_5xxx/VGISS_5???/DATA/\1XX/\1\2_*'),
    (r'volumes/VG_0xxx/VG_002[1-5]/.*/(C[0-9]{5})([0-9]{2})\.(IMQ|IBG)', 0, r'volumes/VGISS_5xxx/VGISS_52??/DATA/\1XX/\1\2_*'),
    (r'volumes/VG_0xxx/VG_002[6-9]/.*/(C[0-9]{5})([0-9]{2})\.(IMQ|IBG)', 0, r'volumes/VGISS_6xxx/VGISS_61??/DATA/\1XX/\1\2_*'),
    (r'volumes/VG_0xxx/VG_003[0-2]/.*/(C[0-9]{5})([0-9]{2})\.(IMQ|IBG)', 0, r'volumes/VGISS_6xxx/VGISS_61??/DATA/\1XX/\1\2_*'),
    (r'volumes/VG_0xxx/VG_0033/.*/(C[0-9]{5})([0-9]{2})\.(IMQ|IBG)',     0, r'volumes/VGISS_6xxx/VGISS_6???/DATA/\1XX/\1\2_*'),
    (r'volumes/VG_0xxx/VG_003[4-8]/.*/(C[0-9]{5})([0-9]{2})\.(IMQ|IBG)', 0, r'volumes/VGISS_6xxx/VGISS_62??/DATA/\1XX/\1\2_*'),
])

associations_to_previews = translator.TranslatorByRegex([
    (r'volumes/VG_0xxx/VG_000[1-3]/.*/(C[0-9]{5})([0-9]{2})\.(IMQ|IBG)', 0, r'previews/VGISS_7xxx/VGISS_7???/DATA/\1XX/\1\2_*'),
    (r'volumes/VG_0xxx/VG_000[45]/.*/(C[0-9]{5})([0-9]{2})\.(IMQ|IBG)',  0, r'previews/VGISS_6xxx/VGISS_6???/DATA/\1XX/\1\2_*'),
    (r'volumes/VG_0xxx/VG_000[6-8]/.*/(C[0-9]{5})([0-9]{2})\.(IMQ|IBG)', 0, r'previews/VGISS_5xxx/VGISS_5???/DATA/\1XX/\1\2_*'),
    (r'volumes/VG_0xxx/VG_0009/.*/(C[0-9]{5})([0-9]{2})\.(IMQ|IBG)',     0, r'previews/VGISS_8xxx/VGISS_8???/DATA/\1XX/\1\2_*'),
    (r'volumes/VG_0xxx/VG_001[0-2]/.*/(C[0-9]{5})([0-9]{2})\.(IMQ|IBG)', 0, r'previews/VGISS_8xxx/VGISS_8???/DATA/\1XX/\1\2_*'),
    (r'volumes/VG_0xxx/VG_001[3-9]/.*/(C[0-9]{5})([0-9]{2})\.(IMQ|IBG)', 0, r'previews/VGISS_5xxx/VGISS_51??/DATA/\1XX/\1\2_*'),
    (r'volumes/VG_0xxx/VG_0020/.*/(C[0-9]{5})([0-9]{2})\.(IMQ|IBG)',     0, r'previews/VGISS_5xxx/VGISS_5???/DATA/\1XX/\1\2_*'),
    (r'volumes/VG_0xxx/VG_002[1-5]/.*/(C[0-9]{5})([0-9]{2})\.(IMQ|IBG)', 0, r'previews/VGISS_5xxx/VGISS_52??/DATA/\1XX/\1\2_*'),
    (r'volumes/VG_0xxx/VG_002[6-9]/.*/(C[0-9]{5})([0-9]{2})\.(IMQ|IBG)', 0, r'previews/VGISS_6xxx/VGISS_61??/DATA/\1XX/\1\2_*'),
    (r'volumes/VG_0xxx/VG_003[0-2]/.*/(C[0-9]{5})([0-9]{2})\.(IMQ|IBG)', 0, r'previews/VGISS_6xxx/VGISS_61??/DATA/\1XX/\1\2_*'),
    (r'volumes/VG_0xxx/VG_0033/.*/(C[0-9]{5})([0-9]{2})\.(IMQ|IBG)',     0, r'previews/VGISS_6xxx/VGISS_6???/DATA/\1XX/\1\2_*'),
    (r'volumes/VG_0xxx/VG_003[4-8]/.*/(C[0-9]{5})([0-9]{2})\.(IMQ|IBG)', 0, r'previews/VGISS_6xxx/VGISS_62??/DATA/\1XX/\1\2_*'),
])

##########################################################################################
# VIEW_OPTIONS (grid_view_allowed, multipage_view_allowed, continuous_view_allowed)
##########################################################################################

view_options = translator.TranslatorByRegex([
    (r'volumes/VG_0xxx/VG_..../(?!DOCUMENT)(?!INDEX)(?!LABEL)(?!SOFTWARE)(.*)/C[0-9]{5}XX', re.I, (True, True, True)),
    (r'volumes/VG_0xxx/VG_..../(?!DOCUMENT)(?!INDEX)(?!LABEL)(?!SOFTWARE)\w+',              re.I, (True, True, True)),
])

##########################################################################################
# NEIGHBORS
##########################################################################################

neighbors = translator.TranslatorByRegex([
    (r'volumes/VG_0xxx/\w+/(?!DOCUMENT)(?!INDEX)(?!LABEL)(?!SOFTWARE)(\w+)',             re.I, r'volumes/VG_0xxx/*/\1'),
    (r'volumes/VG_0xxx/\w+/(?!DOCUMENT)(?!INDEX)(?!LABEL)(?!SOFTWARE)(\w+)/C[0-9]{5}XX', re.I, r'volumes/VG_0xxx/*/\1/*'),
    (r'volumes/VG_0xxx/\w+/(?!DOCUMENT)(?!INDEX)(?!LABEL)(?!SOFTWARE)(\w+)/\w+',         re.I, r'volumes/VG_0xxx/*/\1/*'),
])

##########################################################################################
# OPUS_TYPE
##########################################################################################

opus_type = translator.TranslatorByRegex([
    (r'volumes/.*/C[0-9]{7}\.IMQ', 0, ('Voyager ISS', 110, 'vgiss_imq', 'Compressed Raw (IMQ)', True)),
    (r'volumes/.*/C[0-9]{7}\.IBQ', 0, ('Voyager ISS', 120, 'vgiss_ibq', 'Small Preview (IBQ)',  True)),
])

##########################################################################################
# OPUS_FORMAT
##########################################################################################

opus_format = translator.TranslatorByRegex([
    (r'.*\.IBG', 0, ('Binary', 'Compressed Voyager browse')),
    (r'.*\.IMQ', 0, ('Binary', 'Compressed Voyager EDR')),
])

##########################################################################################
# OPUS_ID
##########################################################################################

opus_id = translator.TranslatorByRegex([
    (r'.*/VG_000[1-3]/.*/C([0-9]{7})\..*',       0, r'vg-iss-2-u-c\1'),
    (r'.*/VG_000[45]/.*/C(3[0-9]{6})\..*',       0, r'vg-iss-1-s-c\1'),
    (r'.*/VG_000[45]/.*/C(4[0-9]{6})\..*',       0, r'vg-iss-2-s-c\1'),
    (r'.*/VG_000[6-8]/.*/C(1[0-7][0-9]{5})\..*', 0, r'vg-iss-1-j-c\1'),
    (r'.*/VG_000[6-8]/.*/C(1[8-9][0-9]{5})\..*', 0, r'vg-iss-2-j-c\1'),
    (r'.*/VG_000[6-8]/.*/C(2[0-9]{6})\..*',      0, r'vg-iss-2-j-c\1'),
    (r'.*/VG_0009/.*/C([0-9]{7})\..*',           0, r'vg-iss-2-n-c\1'),
    (r'.*/VG_001[0-2]/.*/C([0-9]{7})\..*',       0, r'vg-iss-2-n-c\1'),
    (r'.*/VG_001[3-9]/.*/C([0-9]{7})\..*',       0, r'vg-iss-1-j-c\1'),
    (r'.*/VG_0020/.*/C(1[0-7][0-9]{5})\..*',     0, r'vg-iss-1-j-c\1'),
    (r'.*/VG_0020/.*/C(1[8-9][0-9]{5})\..*',     0, r'vg-iss-2-j-c\1'),
    (r'.*/VG_002[1-5]/.*/C([0-9]{7})\..*',       0, r'vg-iss-2-j-c\1'),
    (r'.*/VG_002[6-9]/.*/C([0-9]{7})\..*',       0, r'vg-iss-1-s-c\1'),
    (r'.*/VG_003[0-2]/.*/C([0-9]{7})\..*',       0, r'vg-iss-1-s-c\1'),
    (r'.*/VG_0033/.*/C(3[0-9]{6})\..*',          0, r'vg-iss-1-s-c\1'),
    (r'.*/VG_0033/.*/C(4[0-9]{6})\..*',          0, r'vg-iss-2-s-c\1'),
    (r'.*/VG_003[4-8]/.*/C([0-9]{7})\..*',       0, r'vg-iss-2-s-c\1'),
])

##########################################################################################
# Subclass definition
##########################################################################################

class VG_0xxx(pds3file.Pds3File):

    pds3file.Pds3File.VOLSET_TRANSLATOR = translator.TranslatorByRegex([('VG_0xxx', re.I, 'VG_0xxx')]) + \
                                          pds3file.Pds3File.VOLSET_TRANSLATOR

    DESCRIPTION_AND_ICON = description_and_icon_by_regex + pds3file.Pds3File.DESCRIPTION_AND_ICON
    VIEW_OPTIONS = view_options + pds3file.Pds3File.VIEW_OPTIONS
    NEIGHBORS = neighbors + pds3file.Pds3File.NEIGHBORS

    OPUS_TYPE = opus_type + pds3file.Pds3File.OPUS_TYPE
    OPUS_FORMAT = opus_format + pds3file.Pds3File.OPUS_FORMAT
    OPUS_ID = opus_id

    VIEWABLES = {'default': default_viewables}

    ASSOCIATIONS = pds3file.Pds3File.ASSOCIATIONS.copy()
    ASSOCIATIONS['volumes']  += associations_to_volumes
    ASSOCIATIONS['previews'] += associations_to_previews

    FILENAME_KEYLEN = 8     # trim off suffixes

##########################################################################################
# Update the global dictionary of subclasses
##########################################################################################

pds3file.Pds3File.SUBCLASSES['VG_0xxx'] = VG_0xxx

##########################################################################################
