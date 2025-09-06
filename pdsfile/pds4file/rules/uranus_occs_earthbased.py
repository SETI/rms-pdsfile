##########################################################################################
# pds4file/rules/uranus_occs_earthbased.py
##########################################################################################

import pdsfile.pds4file as pds4file
import translator
import re

from .uranus_occs_earthbased_primary_filespec import PRIMARY_FILESPEC_LIST

##########################################################################################
# DESCRIPTION_AND_ICON
##########################################################################################

description_and_icon_by_regex = translator.TranslatorByRegex([
    (r'volumes/.*/data/.*/N[0-9_]+\.IMG',                        0, ('Narrow-angle image, VICAR',      'IMAGE'   )),
    (r'volumes/.*/data/.*/W[0-9_]+\.IMG',                        0, ('Wide-angle image, VICAR',        'IMAGE'   )),
    (r'volumes/.*/data/.*/extras(/\w+)*(|/)',                    0, ('Preview image collection',       'BROWDIR' )),
    (r'volumes/.*/data/.*/extras/.*\.(jpeg|jpeg_small|tiff)',    0, ('Preview image',                  'BROWSE'  )),
    (r'volumes/.*/COISS_0011/document/.*/[0-9]+\.[0-9]+(|/)',    0, ('Calibration report',             'INFODIR' )),
    (r'volumes/.*/data(|/\w*)',                                  0, ('Images grouped by SC clock',     'IMAGEDIR')),
    (r'calibrated/.*_calib\.img',                                0, ('Calibrated image, VICAR',        'IMAGE'   )),
    (r'calibrated/.*/data(|/\w+)',                               0, ('Calibrated images by SC clock',  'IMAGEDIR')),
    (r'calibrated/\w+(|/\w+)',                                   0, ('Calibrated image collection',    'IMAGEDIR')),
    (r'.*/thumbnail(/\w+)*',                                     0, ('Small browse images',            'BROWDIR' )),
    (r'.*/thumbnail/.*\.(gif|jpg|jpeg|jpeg_small|tif|tiff|png)', 0, ('Small browse image',             'BROWSE'  )),
    (r'.*/(tiff|full)(/\w+)*',                                   0, ('Full-size browse images',        'BROWDIR' )),
    (r'.*/(tiff|full)/.*\.(tif|tiff|png)',                       0, ('Full-size browse image',         'BROWSE'  )),
    (r'volumes/COISS_0xxx.*/COISS_0011/document/report',         0, ('&#11013; <b>ISS Calibration Report</b>',
                                                                                                       'INFO')),
    (r'(volumes/COISS_0xxx.*/COISS_0011/document/report/index.html)', 0,
            ('&#11013; <b>CLICK "index.html"</b> to view the ISS Calibration Report', 'INFO')),
    (r'volumes/COISS_0xxx.*/COISS_0011/document/.*user_guide.*\.pdf',
                                                                 0, ('&#11013; <b>ISS User Guide</b>', 'INFO')),
    (r'volumes/COISS_0xxx.*/COISS_0011/extras',                  0, ('CISSCAL calibration software',   'CODE')),
    (r'volumes/COISS_0xxx.*/COISS_0011/extras/cisscal',          0, ('CISSCAL source code (IDL)',      'CODE')),
    (r'volumes/COISS_0xxx.*/COISS_0011/extras/cisscal\.tar\.gz', 0, ('CISSCAL source code (download)', 'TARBALL')),
])

##########################################################################################
# VIEWABLES
##########################################################################################

default_viewables = translator.TranslatorByRegex([
    (r'.*/(uranus_occs_earthbased/uranus_occ_u.*/data/atmosphere/.*-v-.*)\.[a-z]{3}', 0,
        [r'diagrams/\1_diagram_full.png',
         r'diagrams/\1_diagram_med.png',
         r'diagrams/\1_diagram_small.png',
         r'diagrams/\1_diagram_thumb.png',
    ]),
    (r'.*/(uranus_occs_earthbased/uranus_occ_u.*/data/(rings|global))/(.*)_\d+m\.[a-z]{3}', 0,
        [r'diagrams/\1/\3_diagram_full.png',
         r'diagrams/\1/\3_diagram_med.png',
         r'diagrams/\1/\3_diagram_small.png',
         r'diagrams/\1/\3_diagram_thumb.png',
    ]),
])

##########################################################################################
# ASSOCIATIONS
##########################################################################################

associations_to_bundles = translator.TranslatorByRegex([
    (r'.*/(uranus_occs_earthbased/uranus_occ_u.*)/(data|browse)(.*|_[a-z]*]/.*)\.[a-z]{3}', 0,
        [r'bundles/\1/data\3.tab',
         r'bundles/\1/data\3.xml',
         r'bundles/\1/data\3.txt',
         r'bundles/\1/data\3.pdf',
         r'bundles/\1/browse\3.pdf',
         r'bundles/\1/browse\3.xml',
        ]),
    (r'documents/uranus_occs_earthbased.*', 0,
        r'bundles/uranus_occs_earthbased'),
])

associations_to_previews = translator.TranslatorByRegex([
    (r'.*/(uranus_occs_earthbased/uranus_occ_u.*/(data|browse)/atmosphere/.*-v-.*)\.[a-z]{3}', 0,
        [r'previews/\1_preview_full.png',
         r'previews/\1_preview_med.png',
         r'previews/\1_preview_small.png',
         r'previews/\1_preview_thumb.png',
    ]),
    (r'.*/(uranus_occs_earthbased/uranus_occ_u.*/(data|browse)/(rings|global))/(.*)_\d+m\.[a-z]{3}', 0,
        [r'previews/\1/\4_preview_full.png',
         r'previews/\1/\4_preview_med.png',
         r'previews/\1/\4_preview_small.png',
         r'previews/\1/\4_preview_thumb.png',
    ]),

])

associations_to_diagrams = translator.TranslatorByRegex([
    (r'.*/(uranus_occs_earthbased/uranus_occ_u.*/(data|browse)/atmosphere/.*-v-.*)\.[a-z]{3}', 0,
        [r'diagrams/\1_diagram_full.png',
         r'diagrams/\1_diagram_med.png',
         r'diagrams/\1_diagram_small.png',
         r'diagrams/\1_diagram_thumb.png',
    ]),
    (r'.*/(uranus_occs_earthbased/uranus_occ_u.*/(data|browse)/(rings|global))/(.*)_\d+m\.[a-z]{3}', 0,
        [r'diagrams/\1/\4_diagram_full.png',
         r'diagrams/\1/\4_diagram_med.png',
         r'diagrams/\1/\4_diagram_small.png',
         r'diagrams/\1/\4_diagram_thumb.png',
    ]),
])

associations_to_metadata = translator.TranslatorByRegex([
    (r'.*/(uranus_occs_earthbased)/*', 0,
        r'metadata/\1'),
    (r'.*/(uranus_occs_earthbased/uranus_occ_u[a-z0-9\_]*)/*', 0,
        r'metadata/\1'),
    (r'.*/(uranus_occs_earthbased)/(uranus_occ_u[a-z0-9\_]*)/(data|browse)(.*|_[a-z]*])/(rings|global|atmos).*/(.*)\.[a-z]{3}', 0,
        r'metadata/\1/\2/\2_\5_index.csv/\6'),
])

associations_to_documents = translator.TranslatorByRegex([
    (r'bundles/uranus_occs_earthbased/.*', 0,
        r'documents/uranus_occs_earthbased/*'),
    (r'bundles/uranus_occs_earthbased', 0,
        r'documents/uranus_occs_earthbased'),
])

##########################################################################################
# VIEW_OPTIONS (grid_view_allowed, multipage_view_allowed, continuous_view_allowed)
##########################################################################################

view_options = translator.TranslatorByRegex([
    (r'.*/COISS_[12].../(data|extras/w+)(|/\w+)',     0, (True, True,  True )),
    (r'.*/COISS_3.../(data|extras/w+)/(images|maps)', 0, (True, False, False)),
])

##########################################################################################
# NEIGHBORS
##########################################################################################

neighbors = translator.TranslatorByRegex([
    (r'(.*)/COISS_[12]xxx(.*)/COISS_..../(data|extras/\w+)/\w+', 0, r'\1/COISS_[12]xxx\2/*/\3/*'),
    (r'(.*)/COISS_[12]xxx(.*)/COISS_..../(data|extras/\w+)',     0, r'\1/COISS_[12]xxx\2/*/\3'),
    (r'(.*)/COISS_[12]xxx(.*)/COISS_....',                       0, r'\1/COISS_[12]xxx\2/*'),

    (r'volumes/COISS_0xxx(|_v[0-9\.]+)/COISS_..../data',               0, r'volumes/COISS_0xxx\1/*/data'),
    (r'volumes/COISS_0xxx(|_v[0-9\.]+)/COISS_..../data/(\w+)',         0, r'volumes/COISS_0xxx\1/*/data/\2'),
    (r'volumes/COISS_0xxx(|_v[0-9\.]+)/COISS_..../data/(\w+/\w+)',     0, r'volumes/COISS_0xxx\1/*/data/\2'),
    (r'volumes/COISS_0xxx(|_v[0-9\.]+)/COISS_..../data/(\w+/\w+)/\w+', 0, r'volumes/COISS_0xxx\1/*/data/\2/*'),
])

##########################################################################################
# SORT_KEY
##########################################################################################

sort_key = translator.TranslatorByRegex([

    # Skips over N or W, placing files into chronological order
    (r'([NW])([0-9]{10})(.*)_full.png',  0, r'\2\1\3_1full.jpg'),
    (r'([NW])([0-9]{10})(.*)_med.jpg',   0, r'\2\1\3_2med.jpg'),
    (r'([NW])([0-9]{10})(.*)_small.jpg', 0, r'\2\1\3_3small.jpg'),
    (r'([NW])([0-9]{10})(.*)_thumb.jpg', 0, r'\2\1\3_4thumb.jpg'),
    (r'([NW])([0-9]{10})(.*)', 0, r'\2\1\3'),

    # Used inside COISS_0011/document/report
    ('index.html', 0, '000index.html'),
])

##########################################################################################
# OPUS_TYPE
##########################################################################################

opus_type = translator.TranslatorByRegex([
    # Rings
    (r'bundles/uranus_occs.*/.*/data/rings/.*_radius_.*_100m\.(tab|xml)',                      0, ('Uranus Earth-based Occultations', 10,  'ebur_occ_ring_0100', 'Occultation Ring Profile (100 m)', True)),
    (r'bundles/uranus_occs.*/.*/data/rings/.*_radius_.*_500m\.(tab|xml)',                      0, ('Uranus Earth-based Occultations', 20,  'ebur_occ_ring_0500', 'Occultation Ring Profile (500 m)', True)),
    (r'bundles/uranus_occs.*/.*/data/rings/.*_radius_.*_1000m\.(tab|xml)',                     0, ('Uranus Earth-based Occultations', 30,  'ebur_occ_ring_1000', 'Occultation Ring Profile (1 km)', True)),
    (r'bundles/uranus_occs.*/.*/data/rings/.*_counts-v-time_rings_.*\.(tab|xml)',              0, ('Uranus Earth-based Occultations', 40,  'ebur_occ_ring_time', 'Occultation Ring Time Series', False)),
    (r'bundles/uranus_occs.*/.*/data/ring_models/.*_ring_.*_sqw.*\.(pdf|tab|txt|xml)',         0, ('Uranus Earth-based Occultations', 50,  'ebur_occ_ring_sqw_model', 'Occultation Ring Model', False)),
    (r'bundles/uranus_occs.*/.*/data/ring_models/.*(fitted|predicted)_.*\.(pdf|tab|xml|txt|)', 0, ('Uranus Earth-based Occultations', 50,  'ebur_occ_ring_sqw_model', 'Occultation Ring Model', False)),
    (r'bundles/uranus_occs.*/.*/data/ring_models/.*_wavelengths\.(csv|xml)',                   0, ('Uranus Earth-based Occultations', 50,  'ebur_occ_ring_sqw_model', 'Occultation Ring Model', False)),

    # Atmosphere
    (r'bundles/uranus_occs.*/.*/data/atmosphere/.*_counts-v-time_atmos.*\.(tab|xml)',          0, ('Uranus Earth-based Occultations', 60,  'ebur_occ_atmos', 'Occultation Atmosphere Time Series', True)),

    # Global
    (r'bundles/uranus_occs.*/.*/data/global/.*_radius_equator_.*_100m\.(tab|xml)',             0, ('Uranus Earth-based Occultations', 70,  'ebur_occ_global_0100', 'Occultation Ring-Plane Profile (100 m)', True)),
    (r'bundles/uranus_occs.*/.*/data/global/.*_radius_equator_.*_500m\.(tab|xml)',             0, ('Uranus Earth-based Occultations', 80,  'ebur_occ_global_0500', 'Occultation Ring-Plane Profile (500 m)', True)),
    (r'bundles/uranus_occs.*/.*/data/global/.*_radius_equator_.*_1000m\.(tab|xml)',            0, ('Uranus Earth-based Occultations', 90,  'ebur_occ_global_1000', 'Occultation Ring-Plane Profile (1 km)', True)),
    (r'bundles/uranus_occs.*/.*/data/global/.*_counts-v-time_occult.*\.(tab|xml)',             0, ('Uranus Earth-based Occultations', 100, 'ebur_occ_global_time', 'Occultation Ring-Plane Time Series', False)),

    # Uranus occ support
    (r'.*uranus_occ_support/data/.*_ring_fit_rfrench.*\.(csv|tab|txt|xml)',                    0, ('Uranus Earth-based Occultations', 110, 'ebur_occ_global_ring_fit', 'Global Ring Orbital Fit', False)),
    (r'.*uranus_occ_support/document/supplemental_docs/uranus_occ.*_index\.(tab|xml)',         0, ('Uranus Earth-based Occultations', 120, 'ebur_occ_orig_index', 'Original Index', False)),
    (r'.*uranus_occ_support/document/supplemental_docs/uranus_ringocc.*_rating\.(csv|xml)',    0, ('Uranus Earth-based Occultations', 130, 'ebur_occ_quality_rating', 'Quality Ratings', False)),
    (r'.*uranus_occ_support/document/supplemental_docs/rings.*\.(txt|xml)',                    0, ('Uranus Earth-based Occultations', 140, 'ebur_occ_rings_definitions', 'Ring Dictionary Definitions', False)),
    (r'.*uranus_occ_support/document/user_guide/.*occultation-user-guide\.(pdf|xml)',          0, ('Uranus Earth-based Occultations', 150, 'ebur_occ_documentation', 'Documentation', False)),
    (r'.*uranus_occ_support/document/user_guide/.*\.(pro|py)',                                 0, ('Uranus Earth-based Occultations', 160, 'ebur_occ_software', 'Software', False)),
    (r'.*uranus_occ_support/document/user_guide/plot.*\.pdf',                                  0, ('Uranus Earth-based Occultations', 160, 'ebur_occ_software', 'Software', False)),
    (r'.*uranus_occ_support/spice_kernels/fk/.*\.(tf|xml)',                                    0, ('Uranus Earth-based Occultations', 170, 'ebur_occ_kernels', 'SPICE Kernels', False)),
    (r'.*uranus_occ_support/spice_kernels/spk/.*\.(bsp|xml)',                                  0, ('Uranus Earth-based Occultations', 170, 'ebur_occ_kernels', 'SPICE Kernels', False)),

    # rms_index
    (r'metadata/uranus_occs.*/.*/.*_index.csv',                                                0, ('metadata', 5, 'rms_index', 'RMS Node Augmented Index',     False)),
])

##########################################################################################
# OPUS_FORMAT
##########################################################################################

opus_format = translator.TranslatorByRegex([
    (r'.*\.IMG',        0, ('Binary', 'VICAR')),
    (r'.*\.jpeg_small', 0, ('Binary', 'JPEG')),
])

##########################################################################################
# OPUS_PRODUCTS
##########################################################################################
# call .opus_products() on primary filespec
opus_products = translator.TranslatorByRegex([
    # Rings-specific products
    (r'.*/(uranus_occs_earthbased/uranus_occ_([a-zA-Z0-9\_]+))/(data/rings)/.*_radius_(.*)_(egress|ingress)([\_0-9m]*)\.[a-z]{3}', 0,
        [r'bundles/\1/\3/\2*_radius_\4_\5_*.tab',
         r'bundles/\1/\3/\2*_radius_\4_\5_*.xml',
         r'bundles/\1/\3/\2*_counts-v-time_rings_\5.tab',
         r'bundles/\1/\3/\2*_counts-v-time_rings_\5.xml',
         r'bundles/\1/data/ring_models/\2*_ring_\4_\5_sqw*.pdf',
         r'bundles/\1/data/ring_models/\2*_ring_\4_\5_sqw*.tab',
         r'bundles/\1/data/ring_models/\2*_ring_\4_\5_sqw*.txt',
         r'bundles/\1/data/ring_models/\2*_ring_\4_\5_sqw*.xml',
         r'bundles/\1/data/ring_models/\2*_fitted_*.pdf',
         r'bundles/\1/data/ring_models/\2*_fitted_*.tab',
         r'bundles/\1/data/ring_models/\2*_fitted_*.xml',
         r'bundles/\1/data/ring_models/\2*_predicted_*.pdf',
         r'bundles/\1/data/ring_models/\2*_predicted_*.tab',
         r'bundles/\1/data/ring_models/\2*_predicted_*.xml',
         r'bundles/\1/data/ring_models/\2*_wavelengths.csv',
         r'bundles/\1/data/ring_models/\2*_wavelengths.xml',
         r'metadata/\1/uranus_occ_\2_rings_index.csv',
         ]
    ),
    # Atmosphere-specific products
    (r'.*/(uranus_occs_earthbased/uranus_occ_([a-zA-Z0-9\_]+))/(data/atmosphere)/.*_counts-v-time_atmos_(egress|ingress)\.[a-z]{3}', 0,
        [r'bundles/\1/\3/\2*_counts-v-time_atmos_\4.tab',
         r'bundles/\1/\3/\2*_counts-v-time_atmos_\4.xml',
         r'metadata/\1/uranus_occ_\2_atmos*_index.csv']
    ),
    # Global-specific products, include all "Occultation Ring Model" products
    (r'.*/(uranus_occs_earthbased/uranus_occ_([a-zA-Z0-9\_]+))/data/global/.*(egress|ingress)([\_0-9m]*)\.[a-z]{3}', 0,
        [r'bundles/\1/data/global/\2*_radius_equator_\3_*.tab',
         r'bundles/\1/data/global/\2*_radius_equator_\3_*.xml',
         r'bundles/\1/data/global/\2*_counts-v-time_occult.tab',
         r'bundles/\1/data/global/\2*_counts-v-time_occult.xml',
         r'metadata/\1/uranus_occ_\2_global_index.csv']
    ),
    # Uranus occ support
    # Only available for rings & global occs
    (r'.*/(uranus_occs_earthbased)/uranus_occ_.*/data/(rings|global)/.*\.[a-z]{3}', 0,
        [r'bundles/\1/uranus_occ_support/data/*_ring_fit_rfrench*.csv',
         r'bundles/\1/uranus_occ_support/data/*_ring_fit_rfrench*.tab',
         r'bundles/\1/uranus_occ_support/data/*_ring_fit_rfrench*.txt',
         r'bundles/\1/uranus_occ_support/data/*_ring_fit_rfrench*.xml',]
    ),
    # Available for all occs
    (r'.*/(uranus_occs_earthbased)/uranus_occ_.*\.[a-z]{3}', 0,
        [r'bundles/\1/uranus_occ_support/document/supplemental_docs/*_index.tab',
         r'bundles/\1/uranus_occ_support/document/supplemental_docs/*_index.xml',
         r'bundles/\1/uranus_occ_support/document/supplemental_docs/*_quality_rating.csv',
         r'bundles/\1/uranus_occ_support/document/supplemental_docs/*_quality_rating.xml',
         r'bundles/\1/uranus_occ_support/document/user_guide/*-user-guide.pdf',
         r'bundles/\1/uranus_occ_support/document/user_guide/*-user-guide.xml',
         r'bundles/\1/uranus_occ_support/document/user_guide/*.pro',
         r'bundles/\1/uranus_occ_support/document/user_guide/*.py',
         r'bundles/\1/uranus_occ_support/document/user_guide/plot*.pdf',
         r'bundles/\1/uranus_occ_support/spice_kernels/fk/*.tf',
         r'bundles/\1/uranus_occ_support/spice_kernels/fk/*.xml',
         r'bundles/\1/uranus_occ_support/spice_kernels/spk/*.bsp',
         r'bundles/\1/uranus_occ_support/spice_kernels/spk/*.xml']
    ),
    # Previews and diagrams
    (r'.*/(uranus_occs_earthbased/uranus_occ_u.*/data/atmosphere/.*-v-.*)\.[a-z]{3}', 0,
        [r'previews/\1_preview_full.png',
         r'previews/\1_preview_med.png',
         r'previews/\1_preview_small.png',
         r'previews/\1_preview_thumb.png']
    ),
    (r'.*/(uranus_occs_earthbased/uranus_occ_u.*/data/(rings|global))/(.*)_\d+m\.[a-z]{3}', 0,
        [r'previews/\1/\3_preview_full.png',
         r'previews/\1/\3_preview_med.png',
         r'previews/\1/\3_preview_small.png',
         r'previews/\1/\3_preview_thumb.png']
    ),
    (r'.*/(uranus_occs_earthbased/uranus_occ_u.*/data/atmosphere/.*-v-.*)\.[a-z]{3}', 0,
        [r'diagrams/\1_diagram_full.png',
         r'diagrams/\1_diagram_med.png',
         r'diagrams/\1_diagram_small.png',
         r'diagrams/\1_diagram_thumb.png']
    ),
    (r'.*/(uranus_occs_earthbased/uranus_occ_u.*/data/(rings|global))/(.*)_\d+m\.[a-z]{3}', 0,
        [r'diagrams/\1/\3_diagram_full.png',
         r'diagrams/\1/\3_diagram_med.png',
         r'diagrams/\1/\3_diagram_small.png',
         r'diagrams/\1/\3_diagram_thumb.png']
    ),
])

##########################################################################################
# OPUS_ID
##########################################################################################
# OPUS ID Abbrev is based on the telescope name from the collection_context.csv
# Detector:
# 'ir':   'Generic IR High Speed Photometer'
# 'vis':  'Generic Visual High Speed Photometer'
# 'insb': 'Generic InSb High Speed Photometer'
# 'gaas': 'Generic GaAs High Speed Photometer'
# 'ccd': 'Generic CCD Camera'

# prefix_mapping: (
#   bundle prefix,
#   opus id prefix for egress, under rings & global,
#   opus id prefix for egress, under rings & global,
#   opus id prefix for egress and ingress under atmosphere
# )
# if opus id prefix for ingress & atomsphere are None, it's the same as the opus id prefix
# for egress (same start date) or None.
prefix_mapping = {
    ('u0_kao_91cm',         'kao0m91-vis-occ-1977-069-u0',       None,                               None),
    ('u0201_palomar_508cm', 'pal5m08-insb-occ-2002-210-u0201',   None,                               None),
    ('u2_teide_155cm',      'tei1m55-ir-occ-1977-357-u2',        None,                               None),
    ('u5_lco_250cm',        'lascam2m5-insb-occ-1978-100-u5',    None,                               None),
    ('u9_lco_250cm',        'lascam2m5-insb-occ-1979-161-u9',    None,                               None),
    ('u11_ctio_400cm',      'ctio4m0-insb-occ-1980-080-u11',     None,                               None),
    ('u12_ctio_400cm',      'ctio4m0-insb-occ-1980-229-u12',     'ctio4m0-insb-occ-1980-228-u12',    'ctio4m0-insb-occ-1980-228-u12'),
    ('u12_eso_360cm',       'esosil3m6-insb-occ-1980-229-u12',   'esosil3m6-insb-occ-1980-228-u12',  'esosil3m6-insb-occ-1980-229-u12'),
    ('u12_lco_250cm',       'lascam2m5-insb-occ-1980-229-u12',   'lascam2m5-insb-occ-1980-228-u12',  None),
    ('u13_sso_390cm',       'sso3m9-insb-occ-1981-116-u13',      None,                               None),
    ('u14_ctio_150cm',      'ctio1m50-insb-occ-1982-112-u14',    None,                               None),
    ('u14_ctio_400cm',      'ctio4m0-ir-occ-1982-112-u14',       None,                               None),
    ('u14_eso_104cm',       'esosil1m04-insb-occ-1982-112-u14',  None,                               None),
    ('u14_lco_100cm',       'lascam1m0-ir-occ-1982-112-u14',     None,                               None),
    ('u14_lco_250cm',       'lascam2m5-insb-occ-1982-112-u14',   None,                               None),
    ('u14_opmt_106cm',      'pic1m06-gaas-occ-1982-112-u14',     None,                               None),
    ('u14_opmt_200cm',      'pic2m0-insb-occ-1982-112-u14',      None,                               None),
    ('u14_teide_155cm',     'tei1m55-ir-occ-1982-112-u14',       None,                               None),
    ('u15_mso_190cm',       'mtstr1m9-insb-occ-1982-121-u15',    None,                               None),
    ('u16_palomar_508cm',   'pal5m08-insb-occ-1982-155-u16',     None,                               None),
    ('u17b_saao_188cm',     'saao1m88-insb-occ-1983-084-u17b',   None,                               None),
    ('u23_ctio_400cm',      'ctio4m0-insb-occ-1985-124-u23',     None,                               None),
    ('u23_mcdonald_270cm',  'mcd2m7-insb-occ-1985-124-u23',      None,                               None),
    ('u23_teide_155cm',     'tei1m55-insb-occ-1985-124-u23',     None,                               None),
    ('u25_ctio_400cm',      'ctio4m0-insb-occ-1985-144-u25',     None,                               None),
    ('u25_mcdonald_270cm',  'mcd2m7-insb-occ-1985-144-u25',      None,                               None),
    ('u25_palomar_508cm',   'pal5m08-insb-occ-1985-144-u25',     None,                               None),
    ('u28_irtf_320cm',      'irtf3m2-insb-occ-1986-116-u28',     None,                               None),
    ('u34_irtf_320cm',      'irtf3m2-insb-occ-1987-057-u34',     None,                               None),
    ('u36_ctio_400cm',      'ctio4m0-insb-occ-1987-092-u36',     None,                               None),
    ('u36_irtf_320cm',      'irtf3m2-insb-occ-1987-092-u36',     'irtf3m2-insb-occ-1987-089-u36',    None),
    ('u36_maunakea_380cm',  'mk3m8-insb-occ-1987-092-u36',       'mk3m8-insb-occ-1987-089-u36',      None),
    ('u36_sso_230cm',       'sso2m3-insb-occ-1987-092-u36',      None,                               None),
    ('u36_sso_390cm',       'sso3m9-insb-occ-1987-092-u36',      None,                               None),
    ('u65_irtf_320cm',      'irtf3m2-insb-occ-1990-172-u65',     None,                               None),
    ('u83_irtf_320cm',      'irtf3m2-insb-occ-1991-176-u83',     None,                               None),
    ('u84_irtf_320cm',      'irtf3m2-insb-occ-1991-179-u84',     None,                               None),
    ('u102a_irtf_320cm',    'irtf3m2-insb-occ-1992-190-u102a',   None,                               None),
    ('u102b_irtf_320cm',    'irtf3m2-insb-occ-1992-190-u102b',   None,                               None),
    ('u103_eso_220cm',      'esosil2m2-insb-occ-1992-193-u103',  None,                               None),
    ('u103_palomar_508cm',  'pal5m08-insb-occ-1992-193-u103',    None,                               None),
    ('u134_saao_188cm',     'saao1m88-insb-occ-1995-252-u134',   None,                               None),
    ('u137_hst_fos',        'hst-fos-occ-1996-076-u137',         None,                               None),
    ('u137_irtf_320cm',     'irtf3m2-insb-occ-1996-076-u137',    None,                               None),
    ('u138_hst_fos',        'hst-fos-occ-1996-101-u138',         None,                               None),
    ('u138_palomar_508cm',  'pal5m08-insb-occ-1996-101-u138',    None,                               None),
    ('u144_caha_123cm',     'caha1m23-nicmos-occ-1997-273-u144', None,                               None),
    ('u144_saao_188cm',     'saao1m88-insb-occ-1997-273-u144',   None,                               None),
    ('u149_irtf_320cm',     'irtf3m2-insb-occ-1998-310-u149',    None,                               None),
    ('u149_lowell_180cm',   'low1m83-ccd-occ-1998-310-u149',     None,                               None),
    ('u1052_irtf_320cm',    'irtf3m2-insb-occ-1988-133-u1052',   None,                               None),
    ('u9539_ctio_400cm',    'ctio4m0-insb-occ-1993-181-u9539',   None,                               None),
}
opus_id_list = []
for bundle_prefix, opus_id_prefix_e, opus_id_prefix_i, opus_id_prefix_a in prefix_mapping:
    if opus_id_prefix_i is None:
        opus_id_list += [
            (rf'.*/uranus_occs_earthbased/uranus_occ_{bundle_prefix}/data/atmosphere/{bundle_prefix}_\d+nm_counts-v-time_atmos_([ei])(gress|ngress)\.[a-z]{{3}}', 0, fr'{opus_id_prefix_e}-uranus-\1'),
            (rf'.*/uranus_occs_earthbased/uranus_occ_{bundle_prefix}/data/global/{bundle_prefix}_\d+nm_radius_equator_([ei])(gress|ngress)_\d{{3,4}}m\.[a-z]{{3}}', 0, rf'{opus_id_prefix_e}-ringpl-\1'),
            (rf'.*/uranus_occs_earthbased/uranus_occ_{bundle_prefix}/data/rings/{bundle_prefix}_\d+nm_radius_([a-z]+)_([ei])(gress|ngress)_\d{{3,4}}m\.[a-z]{{3}}', 0, rf'{opus_id_prefix_e}-\1-\2')
        ]
    else:
        if opus_id_prefix_a is not None:
            opus_id_list += [
                (rf'.*/uranus_occs_earthbased/uranus_occ_{bundle_prefix}/data/atmosphere/{bundle_prefix}_\d+nm_counts-v-time_atmos_([ei])(gress|ngress)\.[a-z]{{3}}', 0, fr'{opus_id_prefix_a}-uranus-\1'),
            ]
        opus_id_list += [
            (rf'.*/uranus_occs_earthbased/uranus_occ_{bundle_prefix}/data/global/{bundle_prefix}_\d+nm_radius_equator_(e)gress_\d{{3,4}}m\.[a-z]{{3}}', 0, rf'{opus_id_prefix_e}-ringpl-\1'),
            (rf'.*/uranus_occs_earthbased/uranus_occ_{bundle_prefix}/data/global/{bundle_prefix}_\d+nm_radius_equator_(i)ngress_\d{{3,4}}m\.[a-z]{{3}}', 0, rf'{opus_id_prefix_i}-ringpl-\1'),
            (rf'.*/uranus_occs_earthbased/uranus_occ_{bundle_prefix}/data/rings/{bundle_prefix}_\d+nm_radius_([a-z]+)_(e)gress_\d{{3,4}}m\.[a-z]{{3}}', 0, rf'{opus_id_prefix_e}-\1-\2'),
            (rf'.*/uranus_occs_earthbased/uranus_occ_{bundle_prefix}/data/rings/{bundle_prefix}_\d+nm_radius_([a-z]+)_(i)ngress_\d{{3,4}}m\.[a-z]{{3}}', 0, rf'{opus_id_prefix_i}-\1-\2')
        ]
opus_id = translator.TranslatorByRegex(opus_id_list)

##########################################################################################
# FILESPEC_TO_BUNDLESET
##########################################################################################

filespec_to_bundleset = translator.TranslatorByRegex([
    (r'(uranus_occ)_.*', 0, r'\1s_earthbased'),
])

##########################################################################################
# OPUS_ID_TO_PRIMARY_LOGICAL_PATH
##########################################################################################
# highest resolution is primary filespec
opus_id_to_primary_filespec_list = []
for bundle_prefix, opus_id_prefix_e, opus_id_prefix_i, opus_id_prefix_a in prefix_mapping:
    if opus_id_prefix_i is None:
        opus_id_to_primary_filespec_list += [
            (rf'{opus_id_prefix_e}-uranus-([ei])', 0, rf'bundles/uranus_occs_earthbased/uranus_occ_{bundle_prefix}/data/atmosphere/{bundle_prefix}_*nm_counts-v-time_atmos_\1*gress.xml'),
            (rf'{opus_id_prefix_e}-ringpl-([ei])', 0, rf'bundles/uranus_occs_earthbased/uranus_occ_{bundle_prefix}/data/global/{bundle_prefix}_*nm_radius_equator_\1*gress_100m.xml'),
            (rf'{opus_id_prefix_e}-([a-z]*)-([ei])', 0, rf'bundles/uranus_occs_earthbased/uranus_occ_{bundle_prefix}/data/rings/{bundle_prefix}_*nm_radius_\1_\2*_100m.xml'),
        ]
    else:
        if opus_id_prefix_a is not None:
            opus_id_to_primary_filespec_list += [
                (rf'{opus_id_prefix_a}-uranus-([ei])', 0, rf'bundles/uranus_occs_earthbased/uranus_occ_{bundle_prefix}/data/atmosphere/{bundle_prefix}_*nm_counts-v-time_atmos_\1*gress.xml'),
            ]
        opus_id_to_primary_filespec_list += [
            (rf'{opus_id_prefix_e}-ringpl-(e)', 0, rf'bundles/uranus_occs_earthbased/uranus_occ_{bundle_prefix}/data/global/{bundle_prefix}_*nm_radius_equator_\1*gress_100m.xml'),
            (rf'{opus_id_prefix_i}-ringpl-(i)', 0, rf'bundles/uranus_occs_earthbased/uranus_occ_{bundle_prefix}/data/global/{bundle_prefix}_*nm_radius_equator_\1*gress_100m.xml'),
            (rf'{opus_id_prefix_e}-([a-z]*)-(e)', 0, rf'bundles/uranus_occs_earthbased/uranus_occ_{bundle_prefix}/data/rings/{bundle_prefix}_*nm_radius_\1_\2*_100m.xml'),
            (rf'{opus_id_prefix_i}-([a-z]*)-(i)', 0, rf'bundles/uranus_occs_earthbased/uranus_occ_{bundle_prefix}/data/rings/{bundle_prefix}_*nm_radius_\1_\2*_100m.xml'),
        ]

opus_id_to_primary_logical_path = translator.TranslatorByRegex(opus_id_to_primary_filespec_list)

##########################################################################################
# Subclass definition
##########################################################################################

class uranus_occs_earthbased(pds4file.Pds4File):
    volset_list = []
    for bundle_prefix, _, _, _ in prefix_mapping:
        volset_list += [(f'uranus_occ_{bundle_prefix}', re.I, 'uranus_occs_earthbased')]
    pds4file.Pds4File.VOLSET_TRANSLATOR = translator.TranslatorByRegex(volset_list) + \
                                          pds4file.Pds4File.VOLSET_TRANSLATOR

    DESCRIPTION_AND_ICON = description_and_icon_by_regex + \
                           pds4file.Pds4File.DESCRIPTION_AND_ICON
    VIEW_OPTIONS = view_options + pds4file.Pds4File.VIEW_OPTIONS
    NEIGHBORS = neighbors + pds4file.Pds4File.NEIGHBORS
    SORT_KEY = sort_key + pds4file.Pds4File.SORT_KEY

    OPUS_TYPE = opus_type + pds4file.Pds4File.OPUS_TYPE
    OPUS_FORMAT = opus_format + pds4file.Pds4File.OPUS_FORMAT
    OPUS_PRODUCTS = opus_products + pds4file.Pds4File.OPUS_PRODUCTS
    OPUS_ID = opus_id
    OPUS_ID_TO_PRIMARY_LOGICAL_PATH = opus_id_to_primary_logical_path

    VIEWABLES = {'default': default_viewables}

    ASSOCIATIONS = pds4file.Pds4File.ASSOCIATIONS.copy()
    ASSOCIATIONS['bundles']    += associations_to_bundles
    ASSOCIATIONS['previews']   += associations_to_previews
    ASSOCIATIONS['diagrams'] += associations_to_diagrams
    ASSOCIATIONS['metadata']   += associations_to_metadata
    ASSOCIATIONS['documents']  += associations_to_documents

    pds4file.Pds4File.FILESPEC_TO_BUNDLESET = filespec_to_bundleset + \
                                              pds4file.Pds4File.FILESPEC_TO_BUNDLESET
# Global attribute shared by all subclasses
opus_id_to_subclass_set = set()
for bundle_prefix, opus_id_prefix_e, opus_id_prefix_i, opus_id_prefix_a in prefix_mapping:
    opus_id_to_subclass_set.add((rf'{opus_id_prefix_e}.*', 0, uranus_occs_earthbased))
    if opus_id_prefix_i is not None:
        opus_id_to_subclass_set.add((rf'{opus_id_prefix_i}.*', 0, uranus_occs_earthbased))
    if opus_id_prefix_a is not None:
        opus_id_to_subclass_set.add((rf'{opus_id_prefix_a}.*', 0, uranus_occs_earthbased))
pds4file.Pds4File.OPUS_ID_TO_SUBCLASS = (
    translator.TranslatorByRegex(list(opus_id_to_subclass_set)) +
    pds4file.Pds4File.OPUS_ID_TO_SUBCLASS
)

##########################################################################################
# Update the global dictionary of subclasses
##########################################################################################

pds4file.Pds4File.SUBCLASSES['uranus_occs_earthbased'] = uranus_occs_earthbased

##########################################################################################
# Unit tests
##########################################################################################

import pytest
from .pytest_support import *

@pytest.mark.parametrize(
    'input_path,expected',
    [
        # rings
        ('bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_delta_egress_100m.xml',
         'uranus_occs_earthbased/opus_products/u0_kao_91cm_734nm_radius_delta_egress_100m.txt'),
        # atmosphere
        ('bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/atmosphere/u0_kao_91cm_734nm_counts-v-time_atmos_ingress.xml',
         'uranus_occs_earthbased/opus_products/u0_kao_91cm_734nm_counts-v-time_atmos_ingress.txt'),
        # global
        ('bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/global/u0_kao_91cm_734nm_radius_equator_ingress_100m.xml',
         'uranus_occs_earthbased/opus_products/u0_kao_91cm_734nm_radius_equator_ingress_100m.txt')
    ]
)
def test_opus_products(request, input_path, expected):
    update = request.config.option.update
    opus_products_test(pds4file.Pds4File, input_path, TEST_RESULTS_DIR+expected, update)

@pytest.mark.parametrize(
    'input_path,category,expected',
    [
        ('bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/atmosphere/u0_kao_91cm_734nm_counts-v-time_atmos_egress.xml',
         'bundles',
         'uranus_occs_earthbased/associated_abspaths/bundles_u0_kao_91cm_734nm_counts-v-time_atmos_egress.txt'),
        ('bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/atmosphere/u0_kao_91cm_734nm_counts-v-time_atmos_egress.xml',
         'diagrams',
         'uranus_occs_earthbased/associated_abspaths/diagrams_u0_kao_91cm_734nm_counts-v-time_atmos_egress.txt'),
        # TODO: when we have index shelf files available, we can test the following cases
        # ('uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings/u0_kao_91cm_734nm_radius_alpha_egress_100m.xml',
        #  'metadata',
        #  [
        #     'metadata/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/uranus_occ_u0_kao_91cm_rings_index.csv/u0_kao_91cm_734nm_radius_alpha_egress_100m',
        #  ]),
        # ('uranus_occs_earthbased/data/rings/u0_kao_91cm_734nm_radius_delta_ingress_1000m.tab',
        #  'metadata',
        #  [
        #     'metadata/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/uranus_occ_u0_kao_91cm_rings_index.csv/u0_kao_91cm_734nm_radius_delta_ingress_1000ms',
        #  ]),
        # ('uranus_occs_earthbased/data/global/u0_kao_91cm_734nm_radius_equator_ingress_500m.tab',
        #  'metadata',
        #  [
        #     'metadata/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/uranus_occ_u0_kao_91cm_global_index.csv/u0_kao_91cm_734nm_radius_equator_ingress_500m',
        #  ]),
        # ('uranus_occs_earthbased/data/global/u0_kao_91cm_734nm_radius_equator_egress_100m.xml',
        #  'metadata',
        #  [
        #     'metadata/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/uranus_occ_u0_kao_91cm_global_index.csv/u0_kao_91cm_734nm_radius_equator_egress_100m',
        #  ]),
        # TODO: add test case for documents when correct document files are added
    ]
)

def test_associated_abspaths(request, input_path, category, expected):
    update = request.config.option.update
    associated_abspaths_test(pds4file.Pds4File, input_path, category,
                             TEST_RESULTS_DIR+expected, update)

def test_opus_id_to_primary_logical_path():
    for logical_path in PRIMARY_FILESPEC_LIST:
        test_pdsf = pds4file.Pds4File.from_logical_path(logical_path)
        opus_id = test_pdsf.opus_id
        opus_id_pdsf = pds4file.Pds4File.from_opus_id(opus_id)
        assert opus_id_pdsf.logical_path == logical_path
        # Temporarily, before writing OPUS products code, comment out remaining code below

        # Gather all the associated OPUS products
        #product_dict = test_pdsf.opus_products()
        #product_pds4files = []
        #for pdsf_lists in product_dict.values():
        #    for pdsf_list in pdsf_lists:
        #        product_pdsfiles += pdsf_list

        # Filter out the metadata/documents products and format files
        #product_pdsfiles = [pdsf for pdsf in product_pdsfiles
        #                         if pdsf.voltype_ != 'metadata/'
        #                         and pdsf.voltype_ != 'documents/']
        #product_pdsfiles = [pdsf for pdsf in product_pdsfiles
        #                         if pdsf.extension.lower() != '.fmt']

        # Gather the set of absolute paths
        #opus_id_abspaths = set()
        #for pdsf in product_pdsfiles:
        #    opus_id_abspaths.add(pdsf.abspath)

        #for pdsf in product_pdsfiles:
            # Every version is in the product set
        #    for version_pdsf in pdsf.all_versions().values():
        #        assert version_pdsf.abspath in opus_id_abspaths

            # Every viewset is in the product set
        #    for viewset in pdsf.all_viewsets.values():
        #        for viewable in viewset.viewables:
        #            assert viewable.abspath in opus_id_abspaths

            # Every associated product is in the product set except metadata
        #    for category in ('volumes', 'calibrated', 'previews'):
        #        for abspath in pdsf.associated_abspaths(category):
        #            assert abspath in opus_id_abspaths

##########################################################################################
