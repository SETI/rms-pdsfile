##########################################################################################
# pds3file/tests/test_pds3file_whitebox.py
# Whitebox tests for pds3file
##########################################################################################

import os
import pdsfile.pds3file as pds3file
from pdsfile import pdsviewable
import pytest
import re

from .helper import (PDS3_HOLDINGS_DIR,
                     instantiate_target_pdsfile)

PDS_PDSDATA_PATH = PDS3_HOLDINGS_DIR[:PDS3_HOLDINGS_DIR.index('holdings')]

##########################################################################################
# Whitebox test for functions & properties in PdsFile class
##########################################################################################
class TestPdsFileWhiteBox:
    ############################################################################
    # Test for properties
    ############################################################################
    # Can only be tested with pds3file.Pds3File.use_shelves_only(False) to make sure
    # child.abspath is None for this path
    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes', True),
        ]
    )
    def test_exists(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(
            input_path, is_abspath=False)
        child = target_pdsfile.child(basename='COCIRS_0xxx')
        assert child.exists == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/ASTROM_xxxx/ASTROM_0001', False),
        ]
    )
    def test_isdir(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(
            input_path, is_abspath=False)
        # Something doesn't exist
        child = target_pdsfile.child(basename='VOLDESC.CAT')
        assert child.isdir == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            # virtual directory
            ('volumes', '/holdings/volumes'),
        ]
    )
    def test_html_path(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(
            input_path, is_abspath=False)
        assert target_pdsfile.abspath == None
        assert target_pdsfile.html_path == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes', ''),
        ]
    )
    def test_parent_logical_path(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(
            input_path, is_abspath=False)
        assert target_pdsfile.parent_logical_path == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes', ['', 'UNKNOWN']),
        ]
    )
    def test__volume_info(self, input_path, expected):
        # Same as pds3file.Pds3File()
        target_pdsfile = instantiate_target_pdsfile(
            input_path, is_abspath=False)
        print(target_pdsfile._volume_info)
        assert target_pdsfile._volume_info[0] == expected[0]
        assert target_pdsfile._volume_info[1] == expected[1]

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('previews/HSTUx_xxxx/HSTU0_5167/DATA/VISIT_04', ''),
            ('volumes/RPX_xxxx/RPX_0001/CALIB/F130LP.TAB', 'text/plain'),
        ]
    )
    def test_mime_type(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        assert target_pdsfile.mime_type == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COCIRS_6xxx/COCIRS_6004/DATA/GEODATA/GEO1004021018_699.TAB',
            'GEO1004021018_699.LBL'),
            ('volumes/COCIRS_6xxx/COCIRS_6004/DATA/GEODATA/', '')
        ]
    )
    def test_info_basename(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        assert target_pdsfile.info_basename == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            # Something that don't exist
            ('volumes/COUVIS_0xxx_v1/COUVIS_0009/DATA/D2004_274/EUV2004_274_01_39x.lbl',
            ''),
            ('volumes/COUVIS_0xxx_v1/COUVIS_0009/DATA/D2004_274/EUV2004_274_01_39x',
            '.lbl'),
            ('volumes/COUVIS_0xxx_v1/COUVIS_0009/DATA/D2004_274/EUV2004_274_01_39x.cat',
            ''),
        ]
    )
    def test_label_basename(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        assert target_pdsfile.label_basename == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            # Something that doesn't exist
            ('previews/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/HDAC1999_007_16_31_fullx.png',
            False),
        ]
    )
    def test_viewset(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        assert target_pdsfile.viewset == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes', ''),
        ]
    )
    def test_volume_publication_date(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        assert target_pdsfile.volume_publication_date == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            # The 1st case should return [], instead of None
            ('volumes/VGISS_8xxx/VGISS_8201/DATA/C08966XX/C0896631_RAW.LBL',
             [999999]),
            ('volumes/VGISS_8xxx/VGISS_8201/DATA/C08966XX/C0896631xx_RAW.LBL',
             None),
            ('volumes/VGISS_8xxx', [999999]),
            ('volumes', []),
        ]
    )
    def test_version_ranks(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        assert target_pdsfile.version_ranks == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            # nonexistent pdsfile path
            ('archives-volumes/COCIRS_xxxx/COCIRS_0012.tar.gz',
             ''),
        ]
    )
    def test_exact_checksum_url(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res1 = target_pdsfile.exact_checksum_url
        res2 = target_pdsfile.exact_checksum_url
        assert res1 == expected
        assert res1 == res2

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('diagrams/COCIRS_5xxx/COCIRS_5401/BROWSE/TARGETS/IMG0401130240_FP1_x.jpg',
             False),
        ]
    )
    def test_grid_view_allowed(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.grid_view_allowed
        assert res == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COVIMS_0xxx/COVIMS_0006/data/2005088T102825_2005089T113931/v1490784910_3_001.qub',
             17),
            ('volumes/COISS_3xxx/COISS_3001/data/images/SP_1M_90N_0_STEREO.IMG', 0),
            ('volumes/COISS_0xxx/COISS_0001/data/nacfm/bias/121811.img', 11),
            ('volumes/COVIMS_0xxx/COVIMS_0001/data/1999010T054026_1999010T060958/v1294638283_1.qub',
             13),
            ('volumes/COVIMS_0xxx/COVIMS_0001/data/1999010T054026_1999010T060958', 0),
            ('volumes/RPX_xxxx/RPX_0001/199410XX/U2IQXXXX/BROWSEU2IQ0101T.LBL', 9),
            ('volumes/RPX_xxxx/RPX_0301/DATA/19950809_S_RINGS/PROCIMAGE/T0809_F0217_PROC.LBL',
             0),
        ]
    )
    def test_filename_keylen(self, input_path, expected):
        """filename_keylen: return self._filename_keylen_filled"""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        assert target_pdsfile.filename_keylen == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('previews/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/HDAC1999_007_16_31_thumb.png',
             'HDAC1999_007_16_31'),
            ('volumes/COUVIS_8xxx/COUVIS_8001/data/UVIS_HSP_2017_228_BETORI_I_TAU10KM.lbl',
             'UVIS_HSP_2017_228_BETORI_I'),
        ]
    )
    def test_anchor1(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        assert target_pdsfile.anchor == expected

    @pytest.mark.parametrize(
        'input_path,selection,flag,expected',
        [

            ('metadata/HSTUx_xxxx/HSTU0_5167/HSTU0_5167_index.tab',
             'u2no0403t', '', 'HSTU0_5167_index-U2NO0403T'),
        ]
    )
    def test_anchor2(self, input_path, selection, flag, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        index_row = target_pdsfile.child_of_index(selection, flag)
        assert index_row.anchor == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('diagrams/COCIRS_6xxx/COCIRS_6004',
             'Diagrams for Cassini CIRS data, re-formatted, 2010-04-01 to 2010-04-30 (SC clock 1648773882-1651332653)'),
            ('calibrated/COISS_1xxx/COISS_1001',
             'RMS-curated ISS Jupiter calibrated images 1999-01-09 to 2000-10-31 (SC clock 1294562621-1351672562)')
        ]
    )
    def test_description1(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        assert target_pdsfile.description == expected

    @pytest.mark.parametrize(
        'input_path,selection,flag,expected',
        [
            ('metadata/HSTUx_xxxx/HSTU0_5167/HSTU0_5167_index.tab',
             'u2no0403t', '', 'Selected row of index'),
            ('metadata/HSTUx_xxxx/HSTU0_5167/HSTU0_5167_index.tab',
             'u2no04', '', 'Selected rows of index'),
        ]
    )
    def test_description2(self, input_path, selection, flag, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        index_row = target_pdsfile.child_of_index(selection, flag)
        assert index_row.description == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/Cxxx_123x', ''),
        ]
    )
    def test_description3(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.description
        assert res == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COCIRS_0xxx/COCIRS_0010',
              '/holdings/archives-volumes/COCIRS_0xxx/COCIRS_0010.tar.gz'),
        ]
    )
    def test_exact_archive_url1(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.exact_archive_url
        assert res == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            # nonexistent pdsfile path
            ('archives-volumes/COCIRS_xxxx/COCIRS_0010.tar.gz',''),
        ]
    )
    def test_exact_archive_url2(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res1 = target_pdsfile.exact_archive_url
        res2 = target_pdsfile.exact_archive_url
        assert res1 == expected
        assert res1 == res2


    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/HDAC1999_007_16_31x.DAT', '')
        ]
    )
    def test_data_set_id_non_existence(self, input_path, expected):
        """lid: return self._lid_filled"""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res1 = target_pdsfile.data_set_id
        assert res1 == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COUVIS_0xxx/COUVIS_0001/DATA/DATAINFO.TXT', 'Undefined DATA_SET_ID')
        ]
    )
    def test_data_set_id_exception(self, input_path, expected):
        """lid: return self._lid_filled"""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        try:
            res1 = target_pdsfile.data_set_id
        except ValueError as e:
            assert expected in str(e)


    ############################################################################
    # Test for class functions
    ############################################################################
    @pytest.mark.parametrize(
        'input_suffix,expected',
        [
            ('_in_prep', (990100, 'In preparation', '')),
            ('_lien_resolution', (990400, 'In lien resolution', '')),
        ]
    )
    def test_version_info(self, input_suffix, expected):
        res = pds3file.Pds3File.version_info(suffix=input_suffix)
        assert res == expected

    ############################################################################
    # Test for functions
    ############################################################################
    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes',
             'Pds3File.COCIRS_xxxx("' + PDS3_HOLDINGS_DIR + '/volumes/COCIRS_0xxx")'),
            # ('volumes/ASTROM_xxxx/ASTROM_0001',
            #  'Pds3File.ASTROM_xxxx("' + PDS3_HOLDINGS_DIR + '/volumes/ASTROM_xxxx/ASTROM_0001/VOLDESC.CAT")'),
        ]
    )
    def test__repr__(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(
            input_path, is_abspath=False)
        child = target_pdsfile.child(basename='COCIRS_0xxx')
        res = child.__repr__()
        assert res == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('previews/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007',
             [
                '/holdings/previews/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/HDAC1999_007_16_31_thumb.png',
                '/holdings/previews/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/HDAC1999_007_16_31_full.png',
                '/holdings/previews/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/HDAC1999_007_16_31_small.png',
                '/holdings/previews/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/HDAC1999_007_16_31_med.png'
             ]),
            ('archives-volumes/COCIRS_0xxx/', None),
            ('metadata/HSTUx_xxxx/HSTU0_5167/HSTU0_5167_index.tab', []),
        ]
    )
    def test_viewset_lookup(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.viewset_lookup()

        if expected is not None:
            assert isinstance(res, pdsviewable.PdsViewSet)
            viewables = res.to_dict()['viewables']
            print(viewables)
            for viewable in viewables:
                assert viewable['url'] in expected
        else:
            assert res == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('/volumes/pdsdata/holdings/volumes/COUVIS_0xxx_v1',
             'volumes/COUVIS_0xxx_v1'),
            ('volumes/VGIRIS_xxxx_peer_review/VGIRIS_0001/DATA/JUPITER_VG1/C1547XXX.LBL',
             'volumes/VGIRIS_xxxx_peer_review/VGIRIS_0001/DATA/JUPITER_VG1/C1547XXX.LBL'),
            ('volumes/VGIRIS_xxxx_in_prep/VGIRIS_0001/DATA/JUPITER_VG1/C1547XXX.LBL',
             'volumes/VGIRIS_xxxx_peer_review/VGIRIS_0001/DATA/JUPITER_VG1/C1547XXX.LBL'),
            ('checksums/archives', 'checksums-archives-volumes'),
            ('diagrams/checksums', 'checksums-diagrams'),
            ('COISS_2001.targz', 'archives-volumes/COISS_2xxx/COISS_2001.tar.gz'),
            ('COISS_2001_previews.targz', 'archives-previews/COISS_2xxx/COISS_2001_previews.tar.gz'),
            ('COUVIS_0xxx/v1', 'volumes/COUVIS_0xxx_v1'),
            ('checksums-archives-volumes', 'checksums-archives-volumes'),
            ('checksums-archives-previews', 'checksums-archives-previews'),
            ('archives/', 'archives-volumes'),
            ('md5/', 'checksums-volumes'),
            ('diagrams/', 'diagrams'),
            ('peer_review/', 'volumes'),
            ('COISS_0xxx_v1_md5.txt', 'checksums-volumes/COISS_0xxx_v1'),
        ]
    )
    def test_from_path1(self, input_path, expected):
        res = pds3file.Pds3File.from_path(path=input_path)
        assert isinstance(res, pds3file.Pds3File)
        assert res.logical_path == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            # this one doesn't exist
            ('COUVIS_4xxx_v1', '"_v1" not found: COUVIS_4xxx_v1'),

        ]
    )
    def test_from_path2(self, input_path, expected):
        try:
            res = pds3file.Pds3File.from_path(path=input_path)
        except ValueError as e:
            assert expected in str(e)

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('diagrams/checksums/CORSS_8xxx', 'checksums-diagrams/CORSS_8xxx'),
            ('COISS_2002', 'volumes/COISS_2xxx/COISS_2002'),
        ]
    )
    def test_from_path3(self, input_path, expected):
        if pds3file.Pds3File.SHELVES_ONLY:
            res = pds3file.Pds3File.from_path(path=input_path)
            assert isinstance(res, pds3file.Pds3File)
            print(res.logical_path)
            assert res.logical_path == expected
        else:
            assert True

    @pytest.mark.parametrize(
        'input_id,expected',
        [
            ('co-vims-v1490784910_00x', 'Unrecognized OPUS ID'),
        ]
    )
    def test_from_opus_id_with_wrong_id(self, input_id, expected):
        try:
            pds3file.Pds3File.from_opus_id(input_id)
        except ValueError as e:
            assert expected in str(e)


    ############################################################################
    # Test for associated volumes and volsets
    ############################################################################
    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('archives-volumes/COUVIS_0xxx/COUVIS_0001.tar.gz',
             PDS3_HOLDINGS_DIR + '/archives-volumes/COUVIS_0xxx/COUVIS_0001.tar.gz'),

        ]
    )
    def test_volume_abspath(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        assert target_pdsfile.volume_abspath() == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('checksums-archives-volumes/ASTROM_xxxx_md5.txt',
             PDS3_HOLDINGS_DIR + '/checksums-archives-volumes/ASTROM_xxxx_md5.txt'),
        ]
    )
    def test_volset_abspath(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        assert target_pdsfile.volset_abspath() == expected

    ############################################################################
    # Test for support for PdsFile objects representing index rows
    ############################################################################
    def test_absolute_or_logical_path(self):
        """absolute_or_logical_path: get logical path."""
        target_pdsfile = instantiate_target_pdsfile('volumes', is_abspath=False)
        expected = 'volumes'
        assert target_pdsfile.absolute_or_logical_path == expected

    @pytest.mark.parametrize(
        'input_path,selection,flag,expected',
        [
            ('metadata/HSTUx_xxxx/HSTU0_5167/HSTU0_5167_index.tab',
             'u2no0403t', '', 'U2NO0403T'),
            ('metadata/HSTUx_xxxx/HSTU0_5167/HSTU0_5167_index.tab',
             'U2nO0404', '', 'U2NO0404T'),
            ('metadata/HSTUx_xxxx/HSTU0_5167/HSTU0_5167_index.tab',
             'U2nO040', '', 'U2nO040'),
        ]
    )
    def test_find_selected_row_key1(self, input_path, selection, flag, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.find_selected_row_key(selection, flag)
        assert res == expected

    @pytest.mark.parametrize(
        'input_path,selection,flag,expected',
        [
            ('metadata/HSTUx_xxxx/HSTU0_5167/HSTU0_5167_index.tab',
             'U2nO040', '=', 'Index selection is ambiguous'),
        ]
    )
    def test_find_selected_row_key2(self, input_path, selection, flag, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        try:
            res = target_pdsfile.find_selected_row_key(selection, flag)
        except OSError as e:
            assert expected in str(e)

    @pytest.mark.parametrize(
        'input_path,selection,flag,expected',
        [
            ('metadata/HSTUx_xxxx/HSTU0_5167/HSTU0_5167_index.tab',
             'U2nO040', '',
             'metadata/HSTUx_xxxx/HSTU0_5167/HSTU0_5167_index.tab/U2nO040'),
        ]
    )
    def test_child_of_index(self, input_path, selection, flag, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.child_of_index(selection, flag)
        assert isinstance(res, pds3file.Pds3File)
        # The path doesn't point to an actual file.
        assert res.logical_path == expected

    @pytest.mark.parametrize(
        'input_path,selection,flag,expected',
        [
            ('metadata/HSTUx_xxxx/HSTU0_5167/HSTU0_5167_index.tab',
             'U2NO04', '',
             'Index selection is ambiguous'),
        ]
    )
    def test_data_abspath_associated_with_index_row1(self, input_path,
                                                    selection, flag,
                                                    expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        index_row = target_pdsfile.child_of_index(selection, flag)
        try:
            res = index_row.data_abspath_associated_with_index_row()
        except OSError as e:
            assert expected in str(e)

    @pytest.mark.parametrize(
        'input_path,selection,flag,expected',
        [
            # The following case shouldn't exist in real word. (index row exists
            # but data file doesn't)
            # '/volumes/HSTUx_xxxx/HSTU0_5167/DATA/VISIT_04/U2NO0403T.LBL'
            # doesn't exist.
            ('metadata/HSTUx_xxxx/HSTU0_5167/HSTU0_5167_index.tab',
             'U2NO0403T', '',
             ''),
            ('metadata/HSTUx_xxxx/HSTU0_5167/HSTU0_5167_index.tab',
             'U2NO0405T', '',
             ''),
        ]
    )
    def test_data_abspath_associated_with_index_row2(self, input_path,
                                                    selection, flag,
                                                    expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        index_row = target_pdsfile.new_index_row_pdsfile(filename_key=selection,
                                                         row_dicts=[])
        res = index_row.data_abspath_associated_with_index_row()
        assert res == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/HSTNx_xxxx/HSTN0_7176', ''),
        ]
    )
    def test_data_abspath_associated_with_index_row3(self, input_path,
                                                     expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.data_abspath_associated_with_index_row()
        assert res == expected


    ############################################################################
    # Test for transformations
    ############################################################################
    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ([
                'volumes/COISS_1xxx/COISS_1001/data/1294561143_1295221348/W1294561202_1.LBL',
                'volumes/HSTNx_xxxx/HSTN0_7176/DATA/VISIT_01/N4BI01L4Q.LBL'
             ],
             [
                 PDS3_HOLDINGS_DIR + '/volumes/COISS_1xxx/COISS_1001/data/1294561143_1295221348/W1294561202_1.LBL',
                 PDS3_HOLDINGS_DIR + '/volumes/HSTNx_xxxx/HSTN0_7176/DATA/VISIT_01/N4BI01L4Q.LBL'
             ])
        ]
    )
    def test_abspaths_for_pdsfiles(self, input_path, expected):
        pdsfiles = []
        for path in input_path:
            pdsfiles.append(instantiate_target_pdsfile(path))

        res = pds3file.Pds3File.abspaths_for_pdsfiles(
            pdsfiles=pdsfiles, must_exist=False)

        print(res)
        for path in res:
            assert path in expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ([
                'volumes/COISS_1xxx/COISS_1001/data/1294561143_1295221348/W1294561202_1.LBL',
                'volumes/HSTNx_xxxx/HSTN0_7176/DATA/VISIT_01/N4BI01L4Q.LBL'
             ],
             [
                'volumes/COISS_1xxx/COISS_1001/data/1294561143_1295221348/W1294561202_1.LBL',
                'volumes/HSTNx_xxxx/HSTN0_7176/DATA/VISIT_01/N4BI01L4Q.LBL'
             ])
        ]
    )
    def test_logicals_for_pdsfiles(self, input_path, expected):
        pdsfiles = []
        for path in input_path:
            pdsfiles.append(instantiate_target_pdsfile(path, is_abspath=False))

        res = pds3file.Pds3File.logicals_for_pdsfiles(pdsfiles=pdsfiles,
                                                    must_exist=True)

        for path in res:
            assert path in expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ([
                'volumes/COISS_1xxx/COISS_1001/data/1294561143_1295221348/W1294561202_1.LBL',
                'volumes/HSTNx_xxxx/HSTN0_7176/DATA/VISIT_01/N4BI01L4Q.LBL'
             ],
             ['W1294561202_1.LBL', 'N4BI01L4Q.LBL'])
        ]
    )
    def test_basenames_for_pdsfiles(self, input_path, expected):
        pdsfiles = []
        for path in input_path:
            pdsfiles.append(instantiate_target_pdsfile(path, is_abspath=False))

        res = pds3file.Pds3File.basenames_for_pdsfiles(pdsfiles=pdsfiles,
                                                     must_exist=True)

        for basename in res:
            assert basename in expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ([
                PDS3_HOLDINGS_DIR + '/volumes/COISS_1xxx/COISS_1001/data/1294561143_1295221348/W1294561202_1.LBL',
                PDS3_HOLDINGS_DIR + '/volumes/HSTNx_xxxx/HSTN0_7176/DATA/VISIT_01/N4BI01L4Q.LBL'
             ],
             ['W1294561202_1.LBL', 'N4BI01L4Q.LBL'])
        ]
    )
    def test_basenames_for_abspaths(self, input_path, expected):
        res = pds3file.Pds3File.basenames_for_abspaths(abspaths=input_path,
                                                     must_exist=True)

        for basename in res:
            assert basename in expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ([
                'volumes/COISS_1xxx/COISS_1001/data/1294561143_1295221348/W1294561202_1.LBL',
                'volumes/HSTNx_xxxx/HSTN0_7176/DATA/VISIT_01/N4BI01L4Q.LBL'
             ],
             [
                 'volumes/COISS_1xxx/COISS_1001/data/1294561143_1295221348/W1294561202_1.LBL',
                 'volumes/HSTNx_xxxx/HSTN0_7176/DATA/VISIT_01/N4BI01L4Q.LBL'
             ])
        ]
    )
    def test_pdsfiles_for_logicals(self, input_path, expected):
        res = pds3file.Pds3File.pdsfiles_for_logicals(logical_paths=input_path,
                                                    must_exist=True)
        for pdsf in res:
            assert isinstance(pdsf, pds3file.Pds3File)
            assert pdsf.logical_path in expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ([
                'volumes/COISS_1xxx/COISS_1001/data/1294561143_1295221348/W1294561202_1.LBL',
                'volumes/HSTNx_xxxx/HSTN0_7176/DATA/VISIT_01/N4BI01L4Q.LBL'
             ],
             ['W1294561202_1.LBL', 'N4BI01L4Q.LBL'])
        ]
    )
    def test_basenames_for_logicals(self, input_path, expected):
        res = pds3file.Pds3File.basenames_for_logicals(logical_paths=input_path,
                                                     must_exist=True)

        for basename in res:
            assert basename in expected

    @pytest.mark.parametrize(
        'input_path,basenames,expected',
        [
            ('volumes/COISS_0xxx/COISS_0001/data/wacfm/bit_wght/13302',
             ['133020.lbl'],
             [PDS3_HOLDINGS_DIR + '/volumes/COISS_0xxx/COISS_0001/data/wacfm/bit_wght/13302/133020.lbl'])
        ]
    )
    def test_abspaths_for_basenames(self, input_path, basenames, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.abspaths_for_basenames(basenames=basenames,
                                                    must_exist=True)

        for path in res:
            assert path in expected

    @pytest.mark.parametrize(
        'input_path,basenames,expected',
        [
            ('volumes/COCIRS_6xxx/COCIRS_6004/DATA/GEODATA/',
             ['GEO1004021018_699.LBL'],
             ['volumes/COCIRS_6xxx/COCIRS_6004/DATA/GEODATA/GEO1004021018_699.LBL'])
        ]
    )
    def test_logicals_for_basenames(self, input_path, basenames, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path, is_abspath=False)
        res = target_pdsfile.logicals_for_basenames(basenames=basenames,
                                                    must_exist=True)

        for path in res:
            assert path in expected

    ############################################################################
    # Test for path associations
    ############################################################################
    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57.DAT',
             'volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57.DAT'),
            ('metadata/HSTUx_xxxx/HSTU0_5167/HSTU0_5167_index.tab',
             'metadata/HSTUx_xxxx_v1.2/HSTU0_5167/HSTU0_5167_index.tab'),
            ('volumes/COUVIS_0xxx/COUVIS_0009/DATA/D2004_274/EUV2004_274_01_39.DAT',
             'volumes/COUVIS_0xxx_v1/COUVIS_0009/DATA/D2004_274/EUV2004_274_01_39.DAT')
        ]
    )
    def test_associated_parallel2(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.associated_parallel(rank='previous')
        print(res)
        if res: # pragma: no cover
            assert res.logical_path == expected
        else: # pragma: no cover
            assert res == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57.DAT',
             'volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57.DAT'),
            ('volumes/COUVIS_0xxx_v1/COUVIS_0009/DATA/D2004_274/EUV2004_274_01_39.DAT',
             'volumes/COUVIS_0xxx/COUVIS_0009/DATA/D2004_274/EUV2004_274_01_39.DAT')
        ]
    )
    def test_associated_parallel3(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.associated_parallel(rank='next')
        if res: # pragma: no cover
            assert res.logical_path == expected
        else: # pragma: no cover
            assert res == expected

    ############################################################################
    # Test for split and sort filenames
    ############################################################################
    @pytest.mark.parametrize(
        'input_path,basenames,expected',
        [
            ('volumes/COCIRS_0xxx',
             ['COCIRS_0xxx_v3', 'COCIRS_0xxx', 'COCIRS_0xxx_v2'],
             #  Sort by version number
             ['COCIRS_0xxx', 'COCIRS_0xxx_v3', 'COCIRS_0xxx_v2']),
        ]
    )
    def test_sort_basenames1(self, input_path, basenames, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.sort_basenames(basenames=basenames, dirs_first=True)
        assert res == expected

    @pytest.mark.parametrize(
        'input_path,basenames,expected',
        [
            ('volumes/COCIRS_0xxx',
             ['COCIRS_0xxx_v3', 'COCIRS_0xxx', 'COCIRS_0xxx_v2'],
             #  Sort by version number
             ['COCIRS_0xxx', 'COCIRS_0xxx_v3', 'COCIRS_0xxx_v2']),
        ]
    )
    def test_sort_basenames2(self, input_path, basenames, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.sort_basenames(basenames=basenames, dirs_last=True)
        assert res == expected

    ############################################################################
    # Test for associations
    ############################################################################
    @pytest.mark.parametrize(
        'input_path,rank,category,expected',
        [
            ('checksums-volumes/COUVIS_0xxx/COUVIS_0001_md5.txt',
             None, 'checksums-volumes', 'checksums-volumes/COUVIS_0xxx/COUVIS_0001_md5.txt'),
            ('volumes', None, None, 'volumes'),
            ('metadata', "latestx", 'metadata', 'metadata'),
            ('volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57.DAT',
             'latest', 'volumes',
             'volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57.DAT'),
            ('volumes/COUVIS_0xxx/COUVIS_0001',
             'previous', 'volumes', 'volumes/COUVIS_0xxx/COUVIS_0001'),
            ('volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57.DAT',
             'next', 'volumes', 'volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57.DAT'),
            ('volumes/COUVIS_0xxx', 'latest', 'volumes', 'volumes/COUVIS_0xxx'),
        ]
    )
    def test_associated_parallel1(self, input_path, rank, category, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        target_associated_parallel = target_pdsfile.associated_parallel(
                                        rank=rank ,category=category)
        if target_associated_parallel: # pragma: no cover
            assert target_associated_parallel.logical_path == expected
        else: # pragma: no cover
            assert target_associated_parallel == expected

    @pytest.mark.parametrize(
        'input_path,rank,category,expected',
        [
            ('volumes', None, 'volumes', 'volumes'),
            ('volumes', 999999, 'volumes', 'volumes')
        ]
    )
    def test_associated_parallel2_volumes(self, input_path, rank, category, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        target_pdsfile.associated_parallel(rank=rank ,category=category)
        target_associated_parallel = target_pdsfile.associated_parallel(
                                        rank=rank ,category=category)
        if target_associated_parallel: # pragma: no cover
            assert target_associated_parallel.logical_path == expected
        else: # pragma: no cover
            assert target_associated_parallel == expected

    @pytest.mark.parametrize(
        'input_path,rank,category,expected',
        [
            ('volumes/COUVIS_0xxx', 'latest', 'volumes', 'volumes/COUVIS_0xxx'),
        ]
    )
    def test_associated_parallel3_volumes(self, input_path, rank, category, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        target_pdsfile.associated_parallel(rank=None ,category=category)
        target_associated_parallel = target_pdsfile.associated_parallel(
                                        rank=rank ,category=category)
        if target_associated_parallel: # pragma: no cover
            assert target_associated_parallel.logical_path == expected
        else: # pragma: no cover
            assert target_associated_parallel == expected

    ############################################################################
    # Test for alternative constructors
    ############################################################################
    @pytest.mark.parametrize(
        'input_path,basename,expected',
        [
            ('',
             'volumexs',
             ['Invalid category', 'directory no found', 'Unrecognized volume type']),
        ]
    )
    # For path 2776-2779, self.category_ is only empty when pdsFile is empty,
    # when preload is called, all self.category_ is not empty.
    def test_child(self, input_path, basename, expected):
        with pytest.raises(ValueError) as e:
            target_pdsfile = pds3file.Pds3File()
            res = target_pdsfile.child(basename=basename, fix_case=True)
        res = False
        for error_msg in expected:
            if error_msg in str(e.value):
                res = True
        assert res

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COISS_0xxx/COISS_0001',
             PDS3_HOLDINGS_DIR + '/volumes/COISS_0xxx/COISS_0001'),
            ('documents/coiss_0xxx',
             PDS3_HOLDINGS_DIR + '/documents/COISS_0xxx'),
        ]
    )
    def test_from_abspath(self, input_path, expected):
        if input_path in pds3file.Pds3File.CACHE:
            del pds3file.Pds3File.CACHE[input_path]
        input_path = PDS3_HOLDINGS_DIR + f'/{input_path}'
        res = pds3file.Pds3File.from_abspath(abspath=input_path,
                                           fix_case=True)
        assert isinstance(res, pds3file.Pds3File)
        assert res.abspath == expected
