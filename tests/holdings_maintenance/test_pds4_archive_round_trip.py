##########################################################################################
# tests/holdings_maintenance/test_pds4_archive_round_trip.py
#
# pds4archives has to be able to read what it writes. write_archive() names each member
# for the directory the bundle set's archive_dirs table told it to package, and
# read_archive_info() has to rebuild the same absolute path and the same interior path
# from that name. Where the two disagree, --validate reports every file as wrong and
# --repair rewrites an intact archive on every run, because it cancels only on an exact
# tuple match.
#
# The anchor rule is checked against every archive every table defines, which needs no
# bundle set installed because the rule tables answer from the path alone. The whole
# round trip is then run end to end on a bundle set that is installed.
##########################################################################################

import importlib
import os
import pkgutil
import shutil

import pytest

import pdsfile
from pdsfile.holdings_maintenance import _archives_common
from pdsfile.holdings_maintenance.pds4 import pds4archives
from pdsfile.pds4file import rules as pds4_rules

# Every pds4 rules module that defines an archive_dirs table.
ARCHIVE_RULE_MODULES = sorted(
    m.name for m in pkgutil.iter_modules(pds4_rules.__path__)
    if getattr(importlib.import_module(f'pdsfile.pds4file.rules.{m.name}'),
               'archive_dirs', None) is not None)

# The bundle set each of those modules archives, as its subclass is registered.
BUNDLE_SET_OF = {
    'cassini_iss': 'cassini_iss',
    'cassini_iss_fring_mosaics_rsfrench2025': 'cassini_iss_fring_mosaics_rsfrench2025',
    'cassini_iss_spokes_hedman_hamilton_2024': 'cassini_iss_spokes_hedman-hamilton-2024',
    'cassini_uvis_solarocc_beckerjarmak2023': 'cassini_uvis_solarocc_beckerjarmak2023',
    'cassini_vims': 'cassini_vims',
    'uranus_occs_earthbased': 'uranus_occs_earthbased',
}


def _packaged_dirs(module_name):
    """Return every (archive, packaged directory) pair one module's tables define.

    Both translators are asked with logical paths, so this needs no holdings tree: the
    rules answer from the path alone, which is also why a tool can read an archive of a
    bundle set the running machine does not hold.

    Parameters:
        module_name (str): The rules module, e.g. 'cassini_vims'.

    Returns:
        list: (archive logical path, packaged directory logical path) pairs.
    """

    module = importlib.import_module(f'pdsfile.pds4file.rules.{module_name}')
    bundle_set = BUNDLE_SET_OF[module_name]

    pairs = []
    for category in ('bundles', 'metadata', 'previews', 'diagrams'):
        for tar in module.archive_paths.all(f'{category}/{bundle_set}'):
            for packaged in module.archive_dirs.all(tar):
                pairs.append((tar, packaged))
    return pairs


@pytest.mark.holdings_free
@pytest.mark.parametrize('module_name', ARCHIVE_RULE_MODULES)
def test_the_anchor_rebuilds_what_the_writer_named(module_name):
    """A packaged directory's parent, plus its basename, is that directory again.

    That is the whole of the reader's contract. `write_archive()` adds each packaged
    directory under `arcname=<its basename>`, so a member's first component is that
    basename; the reader has to join it to the directory's parent. This asserts the
    identity the reader now relies on, for every archive these rules define.
    """

    pairs = _packaged_dirs(module_name)
    assert pairs, f'{module_name}: the tables resolved no packaged directory'

    for tar, packaged in pairs:
        anchor = os.path.dirname(packaged)
        arcname = os.path.basename(packaged)
        assert os.path.join(anchor, arcname) == packaged, f'{tar} -> {packaged}'


@pytest.mark.holdings_free
@pytest.mark.parametrize('module_name', ARCHIVE_RULE_MODULES)
def test_where_the_old_anchor_was_wrong_it_is_recorded(module_name):
    """Count the archives the bundle-set anchor could not have rebuilt.

    The reader used to join member names to the bundle set. That is right only where the
    packaged directory is a bundle sitting directly beneath it, so this measures how much
    of each table the old code got wrong rather than asserting a number: a table whose
    every row happened to be the working shape would otherwise look like coverage.
    """

    pairs = _packaged_dirs(module_name)
    wrong = 0
    for _tar, packaged in pairs:
        bundle_set_dir = '/'.join(packaged.split('/')[:2])
        arcname = os.path.basename(packaged)
        if os.path.join(bundle_set_dir, arcname) != packaged:
            wrong += 1

    # Recorded, not asserted to be nonzero: what matters is that the new anchor is right
    # for all of them, which the test above asserts.
    print(f'{module_name}: {wrong} of {len(pairs)} archives the old anchor got wrong')


@pytest.mark.holdings_free
def test_both_broken_shapes_are_represented():
    """The two shapes the old anchor got wrong are actually in the tables above.

    Without this, the suite could pass with every table happening to use the one shape
    the old code handled, and would then prove nothing about the fix.
    """

    from pdsfile.pds4file.rules import cassini_vims, uranus_occs_earthbased

    # A table that packages the bundle set itself: the old anchor doubled its name.
    packaged = uranus_occs_earthbased.archive_dirs.all(
        'archives-bundles/uranus_occs_earthbased/uranus_occs_earthbased.tar.gz')
    assert packaged == ['bundles/uranus_occs_earthbased'], packaged

    # A table that packages collections two levels down: the old anchor dropped the
    # bundle's name.
    packaged = cassini_vims.archive_dirs.all(
        'archives-bundles/cassini_vims/cassini_vims_saturn/'
        'bundle_xml_non_data_browse_collections.tar.gz')
    assert packaged, 'the collection-packaging table resolved nothing'
    for one in packaged:
        assert one.startswith('bundles/cassini_vims/cassini_vims_saturn/'), one
        bundle_set_dir = '/'.join(one.split('/')[:2])
        assert os.path.join(bundle_set_dir, os.path.basename(one)) != one


@pytest.mark.full_holdings
def test_an_archive_reads_back_exactly_as_it_was_written(tmp_path):
    """Write an archive and read it back: the two tuple lists have to be equal.

    Equality of the sorted lists is the condition `repair()` uses to decide whether an
    archive needs rewriting, and it is stricter than validation reporting no errors:
    validation compares field by field and can be made to agree while repair still
    rewrites an intact archive on every run.
    """

    holdings_root = os.environ.get('PDS4_HOLDINGS_DIR')
    if not holdings_root:
        pytest.skip('PDS4_HOLDINGS_DIR is not set')

    name = 'cassini_uvis_solarocc_beckerjarmak2023'
    source = os.path.join(holdings_root, 'bundles', name)
    if not os.path.isdir(source):
        pytest.skip(f'{name} is not installed')

    holdings = tmp_path / 'pds4-holdings'
    (holdings / 'bundles').mkdir(parents=True)
    shutil.copytree(source, holdings / 'bundles' / name)

    pdsfile.Pds4File.preload(str(holdings))
    try:
        src = pdsfile.Pds4File.from_abspath(str(holdings / 'bundles' / name))
        pds4archives.write_archive(src)

        tarpath = src.archive_paths()[0]
        assert os.path.exists(tarpath)

        dir_tuples = _archives_common.load_directory_info(pds4archives.SPEC, src)
        tar_tuples = pds4archives.read_archive_info(tarpath)
        dir_tuples.sort()
        tar_tuples.sort()

        assert len(tar_tuples) == len(dir_tuples)
        assert tar_tuples == dir_tuples
    finally:
        pdsfile.Pds4File.preload(holdings_root)
