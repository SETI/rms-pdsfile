##########################################################################################
# tests/holdings_maintenance/subsets.py
#
# The explicit source subsets the maintenance-tool tests copy out of real holdings.
#
# Each test module declares its own module-level SOURCE_PATHS / SOURCE_MTIMES from
# the tables below; nothing is discovered by globbing or walking. The tables live
# in one module so that the audited list of source files is reviewable in one
# place and cannot drift between test modules.
#
# Every entry records the file's size and md5 as well as its path. The module
# fixture verifies all three and skips the module if anything is missing or
# differs (see conftest.py). That matters because the two real holdings roots are
# NOT byte-identical: the limited testing copy stores most large binary products
# as zero-byte placeholders. The subsets below were chosen so that every declared
# file is byte-identical in both roots (verified file by file), and the
# fingerprint check keeps it that way.
#
# Budget: under ~50 files and ~50 MB per module. PDS3 subset = 11 files / ~1.1 MB;
# PDS4 subset = 9 files / ~0.5 MB.
##########################################################################################

# Pinned modification times, POSIX epoch seconds. Tool subprocesses run with
# TZ=UTC (conftest.py), so the info-shelf sidecars -- which format mtimes with
# datetime.fromtimestamp().strftime() -- render identically on every machine.
# _EPOCH is 2020-09-13 12:26:40 UTC; the per-file offsets are arbitrary but fixed,
# and are deliberately distinct so that "latest modification date" reporting and
# directory-mtime rollup are exercised rather than degenerate.
_EPOCH = 1600000000


##########################################################################################
# PDS3: volumes/HSTNx_xxxx/HSTN0_7176 plus its metadata
#
# Chosen as the smallest volume in the goldens' reference root that has all of:
# a detached PDS3 label with internal links to five siblings, viewable products
# (so the info shelf records image dimensions), and labelled metadata index
# tables that pdsindexshelf can shelve.
##########################################################################################

PDS3_VOLSET = 'HSTNx_xxxx'
PDS3_VOLUME = 'HSTN0_7176'

# (holdings-relative path, size in bytes, md5)
PDS3_VOLUME_SOURCES = (
    ('volumes/HSTNx_xxxx/HSTN0_7176/DATA/VISIT_01/N4BI01L4Q.ASC',
     746315, '8c31237eb5a092bc9a23d7d3b3016fae'),
    ('volumes/HSTNx_xxxx/HSTN0_7176/DATA/VISIT_01/N4BI01L4Q.LBL',
     12058, '56e77a10140cd75b767a2054b1a7340e'),
    ('volumes/HSTNx_xxxx/HSTN0_7176/DATA/VISIT_01/N4BI01L4Q_CAL.JPG',
     27925, '834f6467d93e433344167dc1b7b34d92'),
    ('volumes/HSTNx_xxxx/HSTN0_7176/DATA/VISIT_01/N4BI01L4Q_IMA.JPG',
     24829, '9b4089137daad0811bdc8d97a39c0648'),
    ('volumes/HSTNx_xxxx/HSTN0_7176/DATA/VISIT_01/N4BI01L4Q_RAW.JPG',
     40505, '2a9692014380bf29b47afbd52ac00e73'),
    ('volumes/HSTNx_xxxx/HSTN0_7176/DATA/VISIT_01/N4BI01L4Q_RAW.TIF',
     131234, 'ba774875a6bbc2147ea3d263147fee27'),
)

PDS3_METADATA_SOURCES = (
    ('metadata/HSTNx_xxxx/HSTN0_7176/HSTN0_7176_hstfiles.lbl',
     5183, '99338291080d02c47c75291e53acdd40'),
    ('metadata/HSTNx_xxxx/HSTN0_7176/HSTN0_7176_hstfiles.tab',
     55328, 'c31f94c2e9c365a3967e8304fcb58ac1'),
    ('metadata/HSTNx_xxxx/HSTN0_7176/HSTN0_7176_index.lbl',
     17804, 'dc092fbede92a146c740d8c1a3a7c96a'),
    ('metadata/HSTNx_xxxx/HSTN0_7176/HSTN0_7176_index.tab',
     40508, '8c6fff3739b6b3d8c098ef625004da35'),
)

# Pds3File.preload() reads every volume-set description in _volinfo/, so any test
# that preloads (rather than just resolving paths) needs this file too.
PDS3_VOLINFO_SOURCES = (
    ('_volinfo/HSTNx_xxxx.txt', 20688, '63e3b89fb84e8bbe6a467c41b0de8f88'),
)

PDS3_SOURCES = PDS3_VOLUME_SOURCES + PDS3_METADATA_SOURCES

PDS3_VOLUME_MTIMES = {
    'volumes/HSTNx_xxxx/HSTN0_7176/DATA/VISIT_01/N4BI01L4Q.ASC':     _EPOCH + 10,
    'volumes/HSTNx_xxxx/HSTN0_7176/DATA/VISIT_01/N4BI01L4Q.LBL':     _EPOCH + 20,
    'volumes/HSTNx_xxxx/HSTN0_7176/DATA/VISIT_01/N4BI01L4Q_CAL.JPG': _EPOCH + 30,
    'volumes/HSTNx_xxxx/HSTN0_7176/DATA/VISIT_01/N4BI01L4Q_IMA.JPG': _EPOCH + 40,
    'volumes/HSTNx_xxxx/HSTN0_7176/DATA/VISIT_01/N4BI01L4Q_RAW.JPG': _EPOCH + 50,
    'volumes/HSTNx_xxxx/HSTN0_7176/DATA/VISIT_01/N4BI01L4Q_RAW.TIF': _EPOCH + 60,
}

PDS3_METADATA_MTIMES = {
    'metadata/HSTNx_xxxx/HSTN0_7176/HSTN0_7176_hstfiles.lbl': _EPOCH + 70,
    'metadata/HSTNx_xxxx/HSTN0_7176/HSTN0_7176_hstfiles.tab': _EPOCH + 80,
    'metadata/HSTNx_xxxx/HSTN0_7176/HSTN0_7176_index.lbl':    _EPOCH + 90,
    'metadata/HSTNx_xxxx/HSTN0_7176/HSTN0_7176_index.tab':    _EPOCH + 100,
}

PDS3_VOLINFO_MTIMES = {
    '_volinfo/HSTNx_xxxx.txt': _EPOCH + 105,
}

PDS3_MTIMES = dict(PDS3_VOLUME_MTIMES)
PDS3_MTIMES.update(PDS3_METADATA_MTIMES)
PDS3_MTIMES.update(PDS3_VOLINFO_MTIMES)


##########################################################################################
# PDS4: bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm plus metadata
#
# Three matched label/table pairs from one collection, plus the bundle's three
# metadata index tables. The pairs matter: a PDS4 label links to its data file by
# name, so a subset of labels alone would shelve an empty link graph and the
# pds4linkshelf tests would assert nothing. These three 1000 m ring profiles are
# the smallest matched pairs in the goldens' reference root (82 KB tables).
#
# The other candidate bundles are unusable: uranus_occ_u0201_palomar_508cm holds
# labels but no tables in the reference root, and
# cassini_uvis_solarocc_beckerjarmak2023 is a single 212 MB bundle, far over the
# per-module budget.
##########################################################################################

PDS4_BUNDLESET = 'uranus_occs_earthbased'
PDS4_BUNDLE = 'uranus_occ_u0_kao_91cm'

_B = 'bundles/uranus_occs_earthbased/uranus_occ_u0_kao_91cm/data/rings'
_M = 'metadata/uranus_occs_earthbased/uranus_occ_u0_kao_91cm'

PDS4_BUNDLE_SOURCES = (
    (f'{_B}/u0_kao_91cm_734nm_radius_alpha_egress_1000m.xml',
     31489, '369fafe6d3ec1d472cbfea562caf8673'),
    (f'{_B}/u0_kao_91cm_734nm_radius_alpha_egress_1000m.tab',
     82467, '497f1c868ec720671fd4bfc5f194827b'),
    (f'{_B}/u0_kao_91cm_734nm_radius_beta_egress_1000m.xml',
     31475, 'bb063a2925a9a8d4227eec44a5f20aee'),
    (f'{_B}/u0_kao_91cm_734nm_radius_beta_egress_1000m.tab',
     82467, 'd8a87288fca409cf5f7e233e7bac7400'),
    (f'{_B}/u0_kao_91cm_734nm_radius_gamma_egress_1000m.xml',
     31489, 'd3870a120302e2bd783fecb132749c15'),
    (f'{_B}/u0_kao_91cm_734nm_radius_gamma_egress_1000m.tab',
     82467, 'e13092a1fb7fcafda5347a6bc418687f'),
)

PDS4_METADATA_SOURCES = (
    (f'{_M}/uranus_occ_u0_kao_91cm_atmosphere_index.csv',
     5734, '1c7d8588c4c77797bfea007dab848781'),
    (f'{_M}/uranus_occ_u0_kao_91cm_global_index.csv',
     16731, '5748a583ae5694f6a1a2e1d39e0d5482'),
    (f'{_M}/uranus_occ_u0_kao_91cm_rings_index.csv',
     134225, 'a8165f8ed270cf3332ff0e652fab7f4b'),
)

PDS4_SOURCES = PDS4_BUNDLE_SOURCES + PDS4_METADATA_SOURCES

PDS4_BUNDLE_MTIMES = {
    f'{_B}/u0_kao_91cm_734nm_radius_alpha_egress_1000m.xml': _EPOCH + 110,
    f'{_B}/u0_kao_91cm_734nm_radius_alpha_egress_1000m.tab': _EPOCH + 120,
    f'{_B}/u0_kao_91cm_734nm_radius_beta_egress_1000m.xml':  _EPOCH + 130,
    f'{_B}/u0_kao_91cm_734nm_radius_beta_egress_1000m.tab':  _EPOCH + 140,
    f'{_B}/u0_kao_91cm_734nm_radius_gamma_egress_1000m.xml': _EPOCH + 150,
    f'{_B}/u0_kao_91cm_734nm_radius_gamma_egress_1000m.tab': _EPOCH + 160,
}

PDS4_METADATA_MTIMES = {
    f'{_M}/uranus_occ_u0_kao_91cm_atmosphere_index.csv': _EPOCH + 170,
    f'{_M}/uranus_occ_u0_kao_91cm_global_index.csv':     _EPOCH + 180,
    f'{_M}/uranus_occ_u0_kao_91cm_rings_index.csv':      _EPOCH + 190,
}

PDS4_MTIMES = dict(PDS4_BUNDLE_MTIMES)
PDS4_MTIMES.update(PDS4_METADATA_MTIMES)


def paths_of(sources):
    """Return the holdings-relative paths of a source table.

    Args:
        sources: A sequence of (relpath, size, md5) tuples.

    Returns:
        tuple[str, ...]: The relative paths, in table order.
    """

    return tuple(relpath for relpath, _, _ in sources)
