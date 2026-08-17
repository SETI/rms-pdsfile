##########################################################################################
# tests/pds4file/test_pds4file_bundleset_plus.py
#
# Pds4File.BUNDLESET_PLUS_REGEX, both directions.
#
# The pattern is what stands between a category listing and Pds4File.child: a
# basename it rejects raises "Illegal bundle set directory", so what it admits
# decides which archive-side products can exist at all (observation 4062 was
# its rejecting every checksums-archives-bundles/<set>_md5.txt). It appends to
# BUNDLESET_REGEX the same three groups the PDS3 pattern appends -- version,
# category suffix, archive/checksum ending -- and the consumers in pdsfile.py
# and _sorting.py index groups by position with the PDS3 arm, so the five-group
# structure is itself part of the contract and is pinned here alongside the
# accept/reject sets. The end-to-end proof that the admitted names buy the
# archive products lives in tests/holdings_maintenance/test_pds4_archive_products.py.
##########################################################################################

import pytest

from pdsfile import Pds3File, Pds4File

pytestmark = pytest.mark.holdings_free

# (basename, expected groups). Group order is (bundleset, version, combined
# tail, category suffix, ending); an empty string is a group that matched
# nothing, exactly as on the PDS3 side.
ACCEPTED = [
    # The names that were always accepted: bare bundle sets, versioned or not.
    ('uranus_occs_earthbased',
     ('uranus_occs_earthbased', '', '', '', '')),
    ('cassini_iss_v1.0',
     ('cassini_iss', '_v1.0', '', '', '')),
    ('cassini_iss_v1.0.5',
     ('cassini_iss', '_v1.0.5', '', '', '')),
    # The version group is starred, so repeats still match; the group is the
    # whole run of suffixes.
    ('cassini_iss_v1.0_v2.0',
     ('cassini_iss', '_v1.0_v2.0', '', '', '')),
    # The archive and checksum endings, which name the archive-side products.
    ('uranus_occs_earthbased_md5.txt',
     ('uranus_occs_earthbased', '', '_md5.txt', '', '_md5.txt')),
    ('uranus_occs_earthbased.tar.gz',
     ('uranus_occs_earthbased', '', '.tar.gz', '', '.tar.gz')),
    ('cassini_iss_v1.0_md5.txt',
     ('cassini_iss', '_v1.0', '_md5.txt', '', '_md5.txt')),
    # A category suffix carries the bundle type of a non-bundles category, the
    # way checksum_path_and_lskip() names those categories' checksum files.
    ('uranus_occs_earthbased_metadata_md5.txt',
     ('uranus_occs_earthbased', '', '_metadata_md5.txt', '_metadata', '_md5.txt')),
    ('uranus_occs_earthbased_diagrams_md5.txt',
     ('uranus_occs_earthbased', '', '_diagrams_md5.txt', '_diagrams', '_md5.txt')),
    ('uranus_occs_earthbased_previews.tar.gz',
     ('uranus_occs_earthbased', '', '_previews.tar.gz', '_previews', '.tar.gz')),
    # Every enumerated bundle set takes the endings, including the one whose
    # name embeds hyphens and the one that is a prefix of three others.
    ('cassini_iss_md5.txt',
     ('cassini_iss', '', '_md5.txt', '', '_md5.txt')),
    ('cassini_iss_spokes_hedman-hamilton-2024_md5.txt',
     ('cassini_iss_spokes_hedman-hamilton-2024', '', '_md5.txt', '', '_md5.txt')),
    ('cassini_iss_fring_mosaics_rsfrench2025.tar.gz',
     ('cassini_iss_fring_mosaics_rsfrench2025', '', '.tar.gz', '', '.tar.gz')),
    ('cassini_uvis_solarocc_beckerjarmak2023.tar.gz',
     ('cassini_uvis_solarocc_beckerjarmak2023', '', '.tar.gz', '', '.tar.gz')),
    ('cassini_vims_md5.txt',
     ('cassini_vims', '', '_md5.txt', '', '_md5.txt')),
]

REJECTED = [
    'uranus_occs_earthbased_foo',           # arbitrary words are not endings
    'uranus_occs_earthbased_md5.txt.extra', # nothing may follow an ending
    'uranus_occs_earthbased_volumes_md5.txt',    # volumes is PDS3's data category
    'uranus_occs_earthbased_calibrated_md5.txt', # no calibrated/ beside bundles/
    'uranus_occs_earthbased_bundles_md5.txt',    # the data category carries no suffix
    'uranus_occs_earthbased_v1_md5.txt',    # _v1 is a PDS3 version shape
    'uranus_occs_earthbased_in_prep',       # PDS3's named suffixes stay PDS3's
    'COISS_1xxx_md5.txt',                   # a PDS3 volset is not a bundle set
    'uranus_occ_u0_kao_91cm_md5.txt',       # a bundle is not a bundle set
    'cassini_iss_v1.0extra',                # a version suffix binds to the end
]


@pytest.mark.parametrize('basename,groups', ACCEPTED,
                         ids=[basename for basename, _ in ACCEPTED])
def test_accepted_with_the_expected_groups(basename, groups):
    match = Pds4File.BUNDLESET_PLUS_REGEX.match(basename)
    assert match is not None, basename
    assert match.groups() == groups


@pytest.mark.parametrize('basename', REJECTED)
def test_rejected(basename):
    assert Pds4File.BUNDLESET_PLUS_REGEX.match(basename) is None


def test_case_insensitive_twin_matches_the_same_shape():
    match = Pds4File.BUNDLESET_PLUS_REGEX_I.match('Uranus_Occs_Earthbased_MD5.txt')
    assert match is not None
    assert match.group(1) == 'Uranus_Occs_Earthbased'
    assert match.group(5) == '_MD5.txt'


def test_group_structure_matches_pds3():
    """Both classes' patterns yield five groups with the same positional roles.

    pdsfile.py's child() and from_path() and _sorting.py's split_basename() and
    sort_keys() read groups 1-5 by index through one shared code path, so the
    two class patterns must agree on what each position holds.
    """

    pds3 = Pds3File.BUNDLESET_PLUS_REGEX.match('COISS_1xxx_previews_md5.txt')
    pds4 = Pds4File.BUNDLESET_PLUS_REGEX.match(
        'uranus_occs_earthbased_previews_md5.txt')
    assert pds3 is not None and pds4 is not None
    assert len(pds3.groups()) == len(pds4.groups()) == 5
    assert pds3.groups()[1:] == pds4.groups()[1:] == \
        ('', '_previews_md5.txt', '_previews', '_md5.txt')
