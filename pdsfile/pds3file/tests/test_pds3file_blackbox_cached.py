##########################################################################################
# pds3file/tests/test_pds3file_blackbox_cached.py
# Blackbox tests for pds3file cached
##########################################################################################

import datetime
import os
import pdsfile.pds3file as pds3file
from pdsfile import pdsviewable
import pytest

from .helper import (PDS3_HOLDINGS_DIR,
                     instantiate_target_pdsfile)

try:
    PDS_TESTING_ROOT = PDS3_HOLDINGS_DIR[:PDS3_HOLDINGS_DIR.rindex('pdsdata')]
except ValueError: # pragma: no cover
    PDS_TESTING_ROOT = '/Library/WebServer/Documents/'

##########################################################################################
# Blackbox test for internal cached in PdsFile class
##########################################################################################
class TestPdsFileBlackBox:
    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/VGISS_6xxx/VGISS_6101/DATA/C27830XX/C2783018_RAW.IMG',
             False),
            ('volumes/VGISS_6xxx/VGISS_6101/DATA/C27830XX', True),
            ('volumes/RES_xxxx_prelim/RES_0001/data/601_cas.tab', False)
        ]
    )
    def test_isdir(self, input_path, expected):
        """isdir: return self._isdir_filled"""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res1 = target_pdsfile.isdir
        res2 = target_pdsfile.isdir
        assert res1 == expected
        assert res1 == res2

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/RES_xxxx_prelim/RES_0001/data/601_cas.lbl', True),
            ('volumes/VGISS_7xxx/VGISS_7201/DATA/C24476XX/C2447654_RAW.lbl',
             True),
            ('previews/VGISS_6xxx/VGISS_6101/DATA/C27830XX/C2783018_med.jpg',
             False)
        ]
    )
    def test_islabel(self, input_path, expected):
        """islabel: return self._islabel_filled"""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res1 = target_pdsfile.islabel
        res2 = target_pdsfile.islabel
        assert res1 == expected
        assert res1 == res2

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('previews/NHxxLO_xxxx/NHLALO_1001/data/20060224_000310/'
             + 'lor_0003103486_0x630_eng_thumb.jpg', True),
            ('volumes/NHxxLO_xxxx/NHLALO_1001/data/20060224_000310/'
             + 'lor_0003103486_0x630_eng.fit', False),
            ('volumes/HSTUx_xxxx/HSTU0_5167/DATA/VISIT_04/U2NO0404T.asc', False)
        ]
    )
    def test_is_viewable(self, input_path, expected):
        """is_viewable: return self._is_viewable_filled"""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res1 = target_pdsfile.is_viewable
        res2 = target_pdsfile.is_viewable
        assert res1 == expected
        assert res1 == res2

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('metadata/VGISS_7xxx/VGISS_7201/VGISS_7201_inventory.tab',
             ('VGISS_7201_inventory', '', '.tab')),
            ('previews/NHxxMV_xxxx/NHLAMV_1001/data/20060321_000526/mc1_0005261846_0x536_eng_1_thumb.jpg',
             ('mc1_0005261846_0x536_eng_1', '_thumb', '.jpg')),
            ('previews/VGISS_7xxx/VGISS_7201/DATA/C24476XX/C2447654_small.jpg',
             ('C2447654', '_small', '.jpg')),
        ]
    )
    def test_split(self, input_path, expected):
        """split: return self._split_filled"""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res1 = target_pdsfile.split
        res2 = target_pdsfile.split
        assert res1 == expected
        assert res1 == res2

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/RPX_xxxx/RPX_0001/CALIB/F130LP.lbl',
             'volumes-RPX_xxxx-RPX_0001-CALIB-F130LP'),
            ('volumes/VGIRIS_xxxx_peer_review/VGIRIS_0001/DATA/JUPITER_VG1/C1547XXX.tab',
             'volumes-VGIRIS_xxxx_peer_review-VGIRIS_0001-DATA-JUPITER_VG1-C1547XXX'),
        ]
    )
    def test_global_anchor(self, input_path, expected):
        """global_anchor: return self._global_anchor_filled"""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res1 = target_pdsfile.global_anchor
        res2 = target_pdsfile.global_anchor
        assert res1 == expected
        assert res1 == res2

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/RPX_xxxx/RPX_0001/CALIB/F130LP.LBL', []),
            ('previews/VGISS_5xxx/VGISS_5101/DATA/C13854XX',
             [
                'C1385455_full.jpg', 'C1385455_med.jpg',
                'C1385455_small.jpg', 'C1385455_thumb.jpg'
             ])
        ]
    )
    def test_childnames(self, input_path, expected):
        """childnames: return self._childnames_filled"""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res1 = target_pdsfile.childnames
        res2 = target_pdsfile.childnames
        for child in expected:
            assert child in res1
        for child in res1:
            assert child in res2

    @pytest.mark.parametrize(
        'input_path',
        [
            ('volumes/VGISS_8xxx/VGISS_8201/DATA/C08966XX'),
            ('volumes/VGISS_8xxx/VGISS_8201/DATA/C08966XXx'),
            ('volumes/COISS_0xxx'),
            ('volumes/VGISS_8xxx'),
        ]
    )
    def test__info(self, input_path):
        """_info: return self._info_filled"""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res1 = target_pdsfile._info
        res2 = target_pdsfile._info
        assert res1 == res2

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/VG_20xx/VG_2001/JUPITER/CALIB/VG1PREJT.DAT',
             '2011-05-05 10:43:33')
        ]
    )
    def test_date(self, input_path, expected):
        """date: return self._date_filled"""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res1 = target_pdsfile.date
        res2 = target_pdsfile.date
        assert res1 == expected
        assert res1 == res2

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/VG_20xx/VG_2001/JUPITER/CALIB/VG1PREJT.LBL', '33 KB'),
            ('volumes/VG_28xx/VG_2801/EDITDATA/PN1D01.DAT', '610 KB'),
        ]
    )
    def test_formatted_size(self, input_path, expected):
        """formatted_size: return self._formatted_size_filled"""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res1 = target_pdsfile.formatted_size
        res2 = target_pdsfile.formatted_size
        assert res1 == expected
        assert res1 == res2

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460960868_1.LBL',
             (
                'Cassini ISS Saturn images 2004-04-18 to 2004-05-18 (SC clock 1460960653-1463538454)',
                None, '1.0', '2005-07-01', ['CO-S-ISSNA/ISSWA-2-EDR-V1.0'], ''
             )),
            ('metadata/COVIMS_0xxx/COVIMS_0001',
             (
                'Cassini VIMS metadata 1999-01-10 to 2000-09-18 (SC clock 1294638283-1347975444)',
                None, '1.2', '2020-10-13', ['CO-E/V/J/S-VIMS-2-QUBE-V1.0'], ''
             )),
        ]
    )
    def test__volume_info(self, input_path, expected):
        """_volume_info: return self._volume_info_filled"""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res1 = target_pdsfile._volume_info
        res2 = target_pdsfile._volume_info
        assert res1 == expected
        assert res1 == res2

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/VGIRIS_xxxx_peer_review/VGIRIS_0001/DATA/JUPITER_VG1/C1547XXX.lbl', 'PDS3 label'),
            ('previews/NHxxMV_xxxx/NHLAMV_1001/data/20060321_000526/mc1_0005261846_0x536_eng_1_thumb.jpg', 'Thumbnail preview image'),
        ]
    )
    def test_description(self, input_path, expected):
        """description: return part of self._description_and_icon_filled"""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res1 = target_pdsfile.description
        res2 = target_pdsfile.description
        assert res1 == expected
        assert res1 == res2

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('metadata/VGISS_5xxx/VGISS_5101/VGISS_5101_supplemental_index.tab',
             'INDEX')
        ]
    )
    def test_icon_type(self, input_path, expected):
        """icon_type: return part of self._description_and_icon_filled"""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res1 = target_pdsfile.icon_type
        res2 = target_pdsfile.icon_type
        assert res1 == expected
        assert res1 == res2

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/NHxxMV_xxxx/NHLAMV_1001/data/20060321_000526/mc0_0005261846_0x536_eng_1.fit', 'image/fits'),
            ('volumes/RPX_xxxx/RPX_0001/CALIB/F130LP.TAB', 'text/plain'),
            ('previews/HSTUx_xxxx/HSTU0_5167/DATA/VISIT_04/U2NO0401T_thumb.jpg',
             'image/jpg')
        ]
    )
    def test_mime_type(self, input_path, expected):
        """mime_type: return self._mime_type_filled"""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res1 = target_pdsfile.mime_type
        res2 = target_pdsfile.mime_type
        assert res1 == expected
        assert res1 == res2

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COVIMS_0xxx/COVIMS_0001/data/1999010T054026_1999010T060958/v1294638283_1.qub',
             'co-vims-v1294638283')
        ]
    )
    def test_opus_id(self, input_path, expected):
        """opus_id: return self._opus_id_filled"""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res1 = target_pdsfile.opus_id
        res2 = target_pdsfile.opus_id
        assert res1 == expected
        assert res1 == res2

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('metadata/COUVIS_0xxx/COUVIS_0001/COUVIS_0001_index.tab',
             ('ASCII', 'Table')),
            ('volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/HDAC1999_007_16_31.LBL',
             ('ASCII', 'PDS3 Label')),
            ('previews/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460960908_1_thumb.jpg',
             ('Binary', 'JPEG')),
        ]
    )
    def test_opus_format(self, input_path, expected):
        """opus_format: return self._opus_format_filled"""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res1 = target_pdsfile.opus_format
        res2 = target_pdsfile.opus_format
        assert res1 == expected
        assert res1 == res2

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COCIRS_6xxx/COCIRS_6004/DATA/GEODATA/GEO1004021018_699.TAB',
             ('Cassini CIRS', 110, 'cocirs_geo',  'System Geometry', True)),
            ('previews/VGISS_8xxx/VGISS_8201/DATA/C08966XX/C0896631_thumb.jpg',
             ('browse', 10, 'browse_thumb', 'Browse Image (thumbnail)', False)),
            ('metadata/HSTUx_xxxx/HSTU0_5167/HSTU0_5167_index.tab',
             ('metadata', 5, 'rms_index', 'RMS Node Augmented Index', False)),
            ('documents/COISS_0xxx/CISSCAL-Users-Guide.pdf',
             ('Cassini ISS', 140, 'coiss_documentation', 'Documentation', False)),
        ]
    )
    def test_opus_type(self, input_path, expected):
        """opus_type: return self._opus_type_filled"""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res1 = target_pdsfile.opus_type
        res2 = target_pdsfile.opus_type
        assert res1 == expected
        assert res1 == res2

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/VGISS_8xxx/VGISS_8201', 'VOLDESC.CAT'),
            ('volumes/VG_28xx/VG_2801/EDITDATA/PN1D01.LBL', 'PN1D01.LBL'),
        ]
    )
    def test_info_basename(self, input_path, expected):
        """info_basename: return self._info_basename_filled"""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res1 = target_pdsfile.info_basename
        res2 = target_pdsfile.info_basename
        assert res1 == expected
        assert res1 == res2

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COUVIS_0xxx_v1/COUVIS_0009/DATA/D2004_274/EUV2004_274_01_39.LBL',
             [
                (58, 'EUV2004_274_01_39.DAT', PDS3_HOLDINGS_DIR + '/volumes/COUVIS_0xxx_v1/COUVIS_0009/DATA/D2004_274/EUV2004_274_01_39.DAT'),
             ]),
            ('volumes/COCIRS_0xxx/COCIRS_0012/DATA', []),
            ('previews/COISS_1xxx/COISS_1001/data/1294561143_1295221348/W1294561261_1_thumb.jpg', []),
            ('volumes/COCIRS_0xxx/COCIRS_0012/DATA/NAV_DATA/GEO00120100.LBL',
             [
                (24, 'GEO00120100.DAT', PDS3_HOLDINGS_DIR + '/volumes/COCIRS_0xxx/COCIRS_0012/DATA/NAV_DATA/GEO00120100.DAT'),
                (25, 'GEO00120100.DAT', PDS3_HOLDINGS_DIR + '/volumes/COCIRS_0xxx/COCIRS_0012/DATA/NAV_DATA/GEO00120100.DAT'),
                (32, 'GEO.FMT', PDS3_HOLDINGS_DIR + '/volumes/COCIRS_0xxx/COCIRS_0012/DATA/NAV_DATA/GEO.FMT')
             ])
        ]
    )
    def test_internal_link_info(self, input_path, expected):
        """internal_link_info: return self._internal_links_filled"""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res1 = target_pdsfile.internal_link_info
        res2 = target_pdsfile.internal_link_info
        assert res1 == expected
        assert res1 == res2

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COUVIS_8xxx/COUVIS_8001/data/UVIS_HSP_2017_228_BETORI_I_TAU10KM.TAB',
             'UVIS_HSP_2017_228_BETORI_I_TAU10KM.LBL')
        ]
    )
    def test_label_basename(self, input_path, expected):
        """label_basename: return self._label_basename_filled"""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res1 = target_pdsfile.label_basename
        res2 = target_pdsfile.label_basename
        assert res1 == expected
        assert res1 == res2

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('previews/COCIRS_1xxx/COCIRS_1001/DATA/CUBE/EQUIRECTANGULAR/123RI_EQLBS002_____CI____699_F1_039E_thumb.jpg',
             [
                '/holdings/previews/COCIRS_1xxx/COCIRS_1001/DATA/CUBE/EQUIRECTANGULAR/123RI_EQLBS002_____CI____699_F1_039E_full.jpg',
                '/holdings/previews/COCIRS_1xxx/COCIRS_1001/DATA/CUBE/EQUIRECTANGULAR/123RI_EQLBS002_____CI____699_F1_039E_thumb.jpg',
                '/holdings/previews/COCIRS_1xxx/COCIRS_1001/DATA/CUBE/EQUIRECTANGULAR/123RI_EQLBS002_____CI____699_F1_039E_med.jpg',
                '/holdings/previews/COCIRS_1xxx/COCIRS_1001/DATA/CUBE/EQUIRECTANGULAR/123RI_EQLBS002_____CI____699_F1_039E_small.jpg',
             ]
            )
        ]
    )
    def test_viewset(self, input_path, expected):
        """viewset: return self._viewset_filled"""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res1 = target_pdsfile.viewset
        res2 = target_pdsfile.viewset
        assert isinstance(res1, pdsviewable.PdsViewSet)
        assert res1 == res2
        viewables = res1.to_dict()['viewables']
        for viewable in viewables:
            assert viewable['url'] in expected

    @pytest.mark.parametrize(
        'input_path,expected_pdsviewset,expected_path',
        [
            ('previews/HSTIx_xxxx/HSTI1_1556/DATA/VISIT_01/IB4W01I5Q_thumb.jpg',
             True,
             ['/holdings/previews/HSTIx_xxxx/HSTI1_1556/DATA/VISIT_01/IB4W01I5Q_thumb.jpg']),
            ('volumes/HSTIx_xxxx/HSTI1_1556/DATA/VISIT_01/IB4W01I5Q.asc', False, [])
        ]
    )
    def test_local_viewset(self, input_path, expected_pdsviewset, expected_path):
        """local_viewset: return self._local_viewset_filled"""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res1 = target_pdsfile.local_viewset
        res2 = target_pdsfile.local_viewset
        is_pdsviewset = isinstance(res1, pdsviewable.PdsViewSet)
        assert is_pdsviewset == expected_pdsviewset
        assert res1 == res2
        if is_pdsviewset:
            viewables = res1.to_dict()['viewables']
            for viewable in viewables:
                assert viewable['url'] in expected_path

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('previews/HSTJx_xxxx/HSTJ0_9296/DATA/VISIT_B1/', '2018-03-25'),
        ]
    )
    def test_volume_publication_date(self, input_path, expected):
        """volume_publication_date: return self._volume_publication_date_filled"""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res1 = target_pdsfile.volume_publication_date
        res2 = target_pdsfile.volume_publication_date
        assert res1 == expected
        assert res1 == res2

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COUVIS_0xxx_v1/COUVIS_0009/DATA/D2004_274/EUV2004_274_01_39.lbl', '1.0'),
            ('volumes/COCIRS_1xxx/COCIRS_1001/DATA/TSDR/NAV_DATA/TAR10013100.DAT'
             , '4.0'),
            ('volumes/COCIRS_0xxx_v3/COCIRS_0401/DATA/TSDR/NAV_DATA/TAR04012400.DAT', '3.0'),
        ]
    )
    def test_volume_version_id(self, input_path, expected):
        """volume_version_id: return self._volume_version_id_filled"""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res1 = target_pdsfile.volume_version_id
        res2 = target_pdsfile.volume_version_id
        assert res1 == expected
        assert res1 == res2

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/VGISS_7xxx/VGISS_7201/DATA/C24476XX/C2447654_RAW.IMG',
             ['VG2-U-ISS-2/3/4/6-PROCESSED-V1.0']),
        ]
    )
    def test_volume_data_set_ids(self, input_path, expected):
        """volume_data_set_ids: return self._volume_data_set_ids_filled"""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res1 = target_pdsfile.volume_data_set_ids
        res2 = target_pdsfile.volume_data_set_ids
        assert res1 == expected
        assert res1 == res2

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/VGISS_8xxx/VGISS_8201/DATA/C08966XX/C0896631_RAW.LBL',
             [999999]),
        ]
    )
    def test_version_ranks(self, input_path, expected):
        """version_ranks: return self._version_ranks_filled"""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res1 = target_pdsfile.version_ranks
        res2 = target_pdsfile.version_ranks
        assert res1 == expected
        assert res1 == res2

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('metadata/VGISS_7xxx/VGISS_7201/VGISS_7201_inventory.tab', 8),
            ('metadata/HSTJx_xxxx/HSTJ0_9296/HSTJ0_9296_index.tab', 9),
        ]
    )
    def test_filename_keylen(self, input_path, expected):
        """filename_keylen: return self._filename_keylen_filled"""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res1 = target_pdsfile.filename_keylen
        res2 = target_pdsfile.filename_keylen
        assert res1 == expected
        assert res1 == res2

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('previews/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007',
             [
                '/holdings/_icons/blue/png-200/folder_previews.png',
                '/holdings/_icons/blue/png-500/folder_previews.png',
                '/holdings/_icons/blue/png-30/folder_previews.png',
                '/holdings/_icons/blue/png-100/folder_previews.png',
                '/holdings/_icons/blue/png-50/folder_previews.png',
             ]
            )
        ]
    )
    def test__iconset(self, input_path, expected):
        """filename_keylen: return self._iconset_filled[0]"""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res1 = target_pdsfile._iconset
        res2 = target_pdsfile._iconset
        assert isinstance(res1, pdsviewable.PdsViewSet)
        assert res1 == res2
        viewables = res1.to_dict()['viewables']
        for viewable in viewables:
            assert viewable['url'] in expected


    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('previews/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007',
             [
                '/holdings/_icons/blue/png-200/folder_previews_open.png',
                '/holdings/_icons/blue/png-500/folder_previews_open.png',
                '/holdings/_icons/blue/png-30/folder_previews_open.png',
                '/holdings/_icons/blue/png-100/folder_previews_open.png',
                '/holdings/_icons/blue/png-50/folder_previews_open.png',
             ]
            )
        ]
    )

    def test_iconset_open(self, input_path, expected):
        """filename_keylen: return self._iconset_filled[0]"""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res1 = target_pdsfile.iconset_open
        res2 = target_pdsfile.iconset_open
        assert isinstance(res1, pdsviewable.PdsViewSet)
        assert res1 == res2
        viewables = res1.to_dict()['viewables']
        for viewable in viewables:
            assert viewable['url'] in expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('previews/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007',
             [
                '/holdings/_icons/blue/png-200/folder_previews.png',
                '/holdings/_icons/blue/png-500/folder_previews.png',
                '/holdings/_icons/blue/png-30/folder_previews.png',
                '/holdings/_icons/blue/png-100/folder_previews.png',
                '/holdings/_icons/blue/png-50/folder_previews.png',
             ]
            )
        ]
    )

    def test_iconset_closed(self, input_path, expected):
        """filename_keylen: return self._iconset_filled[0]"""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res1 = target_pdsfile.iconset_closed
        res2 = target_pdsfile.iconset_closed
        assert isinstance(res1,  pdsviewable.PdsViewSet)
        assert res1 == res2
        assert res1 == res2
        viewables = res1.to_dict()['viewables']
        for viewable in viewables:
            assert viewable['url'] in expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460960868_1.IMG',
             'CO-S-ISSNA/ISSWA-2-EDR-V1.0:COISS_2002:data/1460960653_1461048959:N1460960868_1.IMG'),
            ('volumes/COISS_1xxx/COISS_1001/data/1294561143_1295221348/W1294561202_1.LBL',
             'CO-E/V/J-ISSNA/ISSWA-2-EDR-V1.0:COISS_1001:data/1294561143_1295221348:W1294561202_1.LBL'),
            ('volumes/COISS_2xxx/COISS_2002/extras/thumbnail/1460960653_1461048959/N1460960868_1.IMG.jpeg_small',
             'CO-S-ISSNA/ISSWA-2-EDR-V1.0:COISS_2002:extras/thumbnail/1460960653_1461048959:N1460960868_1.IMG.jpeg_small'),
            ('volumes/COVIMS_0xxx/COVIMS_0001/data/1999010T054026_1999010T060958/v1294638283_1.qub',
             'CO-E/V/J/S-VIMS-2-QUBE-V1.0:COVIMS_0001:data/1999010T054026_1999010T060958:v1294638283_1.qub'),
            ('volumes/COVIMS_0xxx/COVIMS_0006/INDEX/index.tab',
             'CO-E/V/J/S-VIMS-2-QUBE-V1.0:COVIMS_0006:INDEX:index.tab'),
            ('volumes/COISS_2xxx/COISS_2002/label/prefix.fmt',
             'CO-S-ISSNA/ISSWA-2-EDR-V1.0:COISS_2002:label:prefix.fmt'),
            ('volumes/COCIRS_0xxx/COCIRS_0012/DATA/NAV_DATA/GEO00120100.DAT',
             'CO-J-CIRS-2/3/4-TSDR-V2.0:COCIRS_0012:DATA/NAV_DATA:GEO00120100.DAT'),
            ('volumes/EBROCC_xxxx/EBROCC_0001/DATA/ESO1M/ES1_EPD.LBL',
             'ESO1M-SR-APPH-4-OCC-V1.0:EBROCC_0001:DATA/ESO1M:ES1_EPD.LBL'),
            ('volumes/EBROCC_xxxx/EBROCC_0001/CATALOG/ESO22M_DATASET.CAT',
             'ESO22M-SR-APPH-4-OCC-V1.0:EBROCC_0001:CATALOG:ESO22M_DATASET.CAT'),
            ('volumes/EBROCC_xxxx/EBROCC_0001/GEOMETRY/IRTF/IRT_IGD.TAB',
             'IRTF-SR-URAC-4-OCC-V1.0:EBROCC_0001:GEOMETRY/IRTF:IRT_IGD.TAB'),
            ('volumes/EBROCC_xxxx/EBROCC_0001/INDEX/LIC_INDEX.LBL',
             'LICK1M-SR-CCDC-4-OCC-V1.0:EBROCC_0001:INDEX:LIC_INDEX.LBL'),
            ('volumes/EBROCC_xxxx/EBROCC_0001/DATA/MCD27M/MCD_IPD.TAB',
             'MCD27M-SR-IIRAR-4-OCC-V1.0:EBROCC_0001:DATA/MCD27M:MCD_IPD.TAB'),
            ('volumes/EBROCC_xxxx/EBROCC_0001/DATA/PAL200/PAL_EPD.LBL',
             'PAL200-SR-CIRC-4-OCC-V1.0:EBROCC_0001:DATA/PAL200:PAL_EPD.LBL'),
            # The file has no LID.
            ('previews/COUVIS_0xxx/COUVIS_0001/DATA/D1999_010/HDAC1999_010_05_01_thumb.png',
             ''),
        ]
    )
    def test_lid(self, input_path, expected):
        """lid: return self._lid_filled"""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res1 = target_pdsfile.lid
        res2 = target_pdsfile.lid
        assert res1 == expected
        assert res1 == res2

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460960868_1.IMG',
             'CO-S-ISSNA/ISSWA-2-EDR-V1.0:COISS_2002:data/1460960653_1461048959:N1460960868_1.IMG::1.0'),
            ('volumes/COISS_1xxx/COISS_1001/data/1294561143_1295221348/W1294561202_1.LBL',
             'CO-E/V/J-ISSNA/ISSWA-2-EDR-V1.0:COISS_1001:data/1294561143_1295221348:W1294561202_1.LBL::1.0'),
            ('volumes/COISS_2xxx/COISS_2002/extras/thumbnail/1460960653_1461048959/N1460960868_1.IMG.jpeg_small',
             'CO-S-ISSNA/ISSWA-2-EDR-V1.0:COISS_2002:extras/thumbnail/1460960653_1461048959:N1460960868_1.IMG.jpeg_small::1.0'),
            ('volumes/COVIMS_0xxx/COVIMS_0001/data/1999010T054026_1999010T060958/v1294638283_1.qub',
             'CO-E/V/J/S-VIMS-2-QUBE-V1.0:COVIMS_0001:data/1999010T054026_1999010T060958:v1294638283_1.qub::1.0'),
            ('volumes/COCIRS_0xxx/COCIRS_0012/DATA/NAV_DATA/GEO00120100.DAT',
             'CO-J-CIRS-2/3/4-TSDR-V2.0:COCIRS_0012:DATA/NAV_DATA:GEO00120100.DAT::1.0'),
            # The file has no LID.
            ('metadata/COISS_2xxx/COISS_2002/COISS_2002_index.ta',
             ''),
        ]
    )
    def test_lidvid(self, input_path, expected):
        """lid: return self._lid_filled"""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res1 = target_pdsfile.lidvid
        res2 = target_pdsfile.lidvid
        assert res1 == expected
        assert res1 == res2

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460960868_1.IMG',
             'CO-S-ISSNA/ISSWA-2-EDR-V1.0'),
            ('volumes/COISS_1xxx/COISS_1001/data/1294561143_1295221348/W1294561202_1.LBL',
             'CO-E/V/J-ISSNA/ISSWA-2-EDR-V1.0'),
            ('volumes/COISS_2xxx/COISS_2002/extras/thumbnail/1460960653_1461048959/N1460960868_1.IMG.jpeg_small',
             'CO-S-ISSNA/ISSWA-2-EDR-V1.0'),
            ('volumes/COVIMS_0xxx/COVIMS_0001/data/1999010T054026_1999010T060958/v1294638283_1.qub',
             'CO-E/V/J/S-VIMS-2-QUBE-V1.0'),
            ('volumes/EBROCC_xxxx/EBROCC_0001/DATA/ESO1M/ES1_EPD.LBL',
             'ESO1M-SR-APPH-4-OCC-V1.0'),
            ('volumes/EBROCC_xxxx/EBROCC_0001/CATALOG/ESO22M_DATASET.CAT',
             'ESO22M-SR-APPH-4-OCC-V1.0'),
            ('volumes/EBROCC_xxxx/EBROCC_0001/GEOMETRY/IRTF/IRT_IGD.TAB',
             'IRTF-SR-URAC-4-OCC-V1.0'),
            ('volumes/EBROCC_xxxx/EBROCC_0001/INDEX/LIC_INDEX.LBL',
             'LICK1M-SR-CCDC-4-OCC-V1.0'),
            ('volumes/EBROCC_xxxx/EBROCC_0001/DATA/MCD27M/MCD_IPD.TAB',
             'MCD27M-SR-IIRAR-4-OCC-V1.0'),
            ('volumes/EBROCC_xxxx/EBROCC_0001/DATA/PAL200/PAL_EPD.LBL',
             'PAL200-SR-CIRC-4-OCC-V1.0'),
        ]
    )
    def test_data_set_id(self, input_path, expected):
        """lid: return self._lid_filled"""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res1 = target_pdsfile.data_set_id
        res2 = target_pdsfile.data_set_id
        assert res1 == expected
        assert res1 == res2

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            # Return '' for COUVIS_0xxx (multiple data set ids) since
            # we don't have a properly defined DATA_SET_ID rule for it.
            ('volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/HDAC1999_007_16_31.DAT',
             'CO-J-UVIS-2-SSB-V1.2'),
            # Return '' for files under volume that have multiple data
            # set ids.
            ('volumes/EBROCC_xxxx/EBROCC_0001/DATA/DATAINFO.TXT',
             ''),
        ]
    )
    def test_data_set_id_multi_data_set_id(self, input_path, expected):
        """lid: return self._data_set_id_filled"""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        # When SHELVES_ONLY is True, there is no metadata tree for COUVIS and
        # it will have empty row_dicts in DATA_SET_ID of COUVIS_0xxx.py rules.
        if not pds3file.Pds3File.SHELVES_ONLY:
            res1 = target_pdsfile.data_set_id
            res2 = target_pdsfile.data_set_id
            assert res1 == expected
            assert res1 == res2

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COCIRS_0xxx/COCIRS_0012/DATA/NAV_DATA/GEO00120100.DAT',
             'CO-J-CIRS-2/3/4-TSDR-V2.0:COCIRS_0012:DATA/NAV_DATA:GEO00120100.DAT'),
            ('volumes/EBROCC_xxxx/EBROCC_0001/DATA/DATAINFO.TXT',
             ''),
        ]
    )
    def test_lid_no_data_set_id(self, input_path, expected):
        """lid: return self._data_set_id_filled"""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res1 = target_pdsfile.lid
        res2 = target_pdsfile.lid
        assert res1 == expected
        assert res1 == res2

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COCIRS_0xxx/COCIRS_0012/DATA/NAV_DATA/GEO00120100.DAT',
             'CO-J-CIRS-2/3/4-TSDR-V2.0:COCIRS_0012:DATA/NAV_DATA:GEO00120100.DAT::1.0'),
            ('volumes/EBROCC_xxxx/EBROCC_0001/DATA/DATAINFO.TXT',
             ''),
        ]
    )
    def test_lidvid_no_data_set_id(self, input_path, expected):
        """lid: return self._data_set_id_filled"""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res1 = target_pdsfile.lidvid
        res2 = target_pdsfile.lidvid
        assert res1 == expected
        assert res1 == res2
