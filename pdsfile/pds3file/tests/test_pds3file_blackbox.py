import pdsfile.pds3file as pds3file
from pdsfile import pdsviewable
import pdsfile.pds3file.rules as rules
from pdsfile.pdsfile import (logical_path_from_abspath,
                             repair_case,
                             selected_path_from_path)

import pytest
import re

from .helper import (PDS3_HOLDINGS_DIR,
                     instantiate_target_pdsfile)

PDS_PDSDATA_PATH = PDS3_HOLDINGS_DIR[:PDS3_HOLDINGS_DIR.index('holdings')]

##########################################################################################
# Blackbox test for functions & properties in Pds3File class
##########################################################################################
class TestPds3FileBlackBox:
    ############################################################################
    # Test on SUBCLASS, make sure rules all exist in the dictionary
    ############################################################################
    @pytest.mark.parametrize(
        'expected',
        [
            ({
                'default': pds3file.Pds3File,
                'ASTROM_xxxx': pds3file.rules.ASTROM_xxxx.ASTROM_xxxx,
                'COCIRS_xxxx': pds3file.rules.COCIRS_xxxx.COCIRS_xxxx,
                'COISS_xxxx': pds3file.rules.COISS_xxxx.COISS_xxxx,
                'CORSS_8xxx': pds3file.rules.CORSS_8xxx.CORSS_8xxx,
                'COSP_xxxx': pds3file.rules.COSP_xxxx.COSP_xxxx,
                'COUVIS_0xxx': pds3file.rules.COUVIS_0xxx.COUVIS_0xxx,
                'COUVIS_8xxx': pds3file.rules.COUVIS_8xxx.COUVIS_8xxx,
                'COVIMS_0xxx': pds3file.rules.COVIMS_0xxx.COVIMS_0xxx,
                'COVIMS_8xxx': pds3file.rules.COVIMS_8xxx.COVIMS_8xxx,
                'EBROCC_xxxx': pds3file.rules.EBROCC_xxxx.EBROCC_xxxx,
                'GO_0xxx': pds3file.rules.GO_0xxx.GO_0xxx,
                'HSTxx_xxxx': pds3file.rules.HSTxx_xxxx.HSTxx_xxxx,
                'JNOJIR_xxxx': pds3file.rules.JNOJIR_xxxx.JNOJIR_xxxx,
                'JNOJNC_xxxx': pds3file.rules.JNOJNC_xxxx.JNOJNC_xxxx,
                'JNOSP_xxxx': pds3file.rules.JNOSP_xxxx.JNOSP_xxxx,
                'NHSP_xxxx': pds3file.rules.NHSP_xxxx.NHSP_xxxx,
                'NHxxxx_xxxx': pds3file.rules.NHxxxx_xxxx.NHxxxx_xxxx,
                'RES_xxxx': pds3file.rules.RES_xxxx.RES_xxxx,
                'RPX_xxxx': pds3file.rules.RPX_xxxx.RPX_xxxx,
                'VG_0xxx': pds3file.rules.VG_0xxx.VG_0xxx,
                'VG_20xx': pds3file.rules.VG_20xx.VG_20xx,
                'VG_28xx': pds3file.rules.VG_28xx.VG_28xx,
                'VGIRIS_xxxx': pds3file.rules.VGIRIS_xxxx.VGIRIS_xxxx,
                'VGISS_xxxx': pds3file.rules.VGISS_xxxx.VGISS_xxxx
             }),
        ]
    )
    def test_subclasses_dict(self, expected):
        res_dict = pds3file.Pds3File.SUBCLASSES
        print(res_dict.keys())
        assert len(res_dict) == len(expected), "Mismatch on the list of SUBCLASSES"
        for key in res_dict:
            current_class = res_dict[key]
            assert key in expected, f"{key} is not in the SUBCLASSES dictionary"
            expected_class = expected[key]
            assert current_class != None, f"Rules is not loaded on {key} in the SUBCLASSES"
            assert current_class == expected_class, f"Mismatch on {key} in the SUBCLASSES"
            assert (f"{current_class.__module__ + current_class.__name__}"
                    == f"{expected_class.__module__ + expected_class.__name__}")

    ############################################################################
    # Local implementations of basic filesystem operations
    ############################################################################
    @pytest.mark.parametrize(
        'input_path,expected',
        [
            (PDS3_HOLDINGS_DIR + '/volumes/COISS_2xxx',
             [
                'COISS_2090', 'COISS_2025', 'COISS_2055', 'COISS_2058',
                'COISS_2086', 'COISS_2105', 'COISS_2067', 'COISS_2017',
                'COISS_2049', 'COISS_2011', 'COISS_2026', 'COISS_2039',
                'COISS_2073', 'COISS_2044', 'COISS_2062', 'COISS_2037',
                'COISS_2114', 'COISS_2110', 'COISS_2072', 'COISS_2002',
                'COISS_2108', 'COISS_2093', 'COISS_2030', 'COISS_2081',
                'COISS_2040', 'COISS_2007', 'COISS_2098', 'COISS_2077',
                'COISS_2115', 'COISS_2029', 'COISS_2050', 'COISS_2111',
                'COISS_2059', 'COISS_2005', 'COISS_2032', 'COISS_2045',
                'COISS_2035', 'COISS_2084', 'COISS_2109', 'COISS_2096',
                'COISS_2019', 'COISS_2083', 'COISS_2008', 'COISS_2095',
                'COISS_2020', 'COISS_2023', 'COISS_2014', 'COISS_2100',
                'COISS_2041', 'COISS_2076', 'COISS_2012', 'COISS_2089',
                'COISS_2103', 'COISS_2061', 'COISS_2107', 'COISS_2024',
                'COISS_2013', 'COISS_2046', 'COISS_2071', 'COISS_2053',
                'COISS_2092', 'COISS_2038', 'COISS_2080', 'COISS_2068',
                'COISS_2018', 'COISS_2036', 'COISS_2060', 'COISS_2057',
                'COISS_2116', 'COISS_2004', 'COISS_2074', 'COISS_2033',
                'COISS_2043', 'COISS_2079', 'COISS_2113', 'COISS_2001',
                'COISS_2052', 'COISS_2065', 'COISS_2016', 'COISS_2021',
                'COISS_2102', 'COISS_2064', 'COISS_2099', 'COISS_2106',
                'COISS_2085', 'COISS_2078', 'COISS_2097', 'COISS_2056',
                'COISS_2066', 'COISS_2051', 'COISS_2101', 'COISS_2063',
                'COISS_2082', 'COISS_2094', 'COISS_2034', 'COISS_2009',
                'COISS_2088', 'COISS_2006', 'COISS_2022', 'COISS_2015',
                'COISS_2028', 'COISS_2091', 'COISS_2031', 'COISS_2104',
                'COISS_2010', 'COISS_2027', 'COISS_2003', 'COISS_2054',
                'COISS_2048', 'COISS_2087', 'COISS_2112', 'COISS_2070',
                'COISS_2075', 'COISS_2042', 'COISS_2069', 'COISS_2047'
            ]
           ),
        ]
    )
    def test_os_listdir(self, input_path, expected):
        res = pds3file.Pds3File.os_listdir(abspath=input_path)
        assert len(res) == len(expected)
        assert res.sort() == expected.sort()

    ############################################################################
    # Test for DEFAULT FILE SORT ORDER
    ############################################################################
    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/HDAC1999_007_16_31.DAT',
             True),
            ('volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/HDAC1999_007_16_31.DAT',
             False),
        ]
    )
    def test_sort_labels_after(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        target_pdsfile.sort_labels_after(labels_after=expected)
        assert target_pdsfile.SORT_ORDER['labels_after'] == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/HDAC1999_007_16_31.DAT',
             True),
            ('volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/HDAC1999_007_16_31.DAT',
             False),
        ]
    )
    def test_sort_dirs_first(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        target_pdsfile.sort_dirs_first(dirs_first=expected)
        assert target_pdsfile.SORT_ORDER['dirs_first'] == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/HDAC1999_007_16_31.DAT',
             True),
            ('volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/HDAC1999_007_16_31.DAT',
             False),
        ]
    )
    def test_sort_dirs_last(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        target_pdsfile.sort_dirs_last(dirs_last=expected)
        assert target_pdsfile.SORT_ORDER['dirs_last'] == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/HDAC1999_007_16_31.DAT',
             True),
            ('volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/HDAC1999_007_16_31.DAT',
             False),
        ]
    )
    def test_sort_info_first(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        target_pdsfile.sort_info_first(info_first=expected)
        assert target_pdsfile.SORT_ORDER['info_first'] == expected

    ############################################################################
    # Test for properties
    ############################################################################
    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COCIRS_0xxx/COCIRS_0012/DATA/NAV_DATA/GEO00120100.DAT',
             True),
            ('volumes/COCIRS_0xxx/COCIRS_0012/DATA/NAV_DATA/GEO00120100.IMG',
             False)
        ]
    )
    def test_exists(self, input_path, expected):
        """exists: test on one existing and one non exising file."""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        assert target_pdsfile.exists == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('diagrams/COCIRS_5xxx/COCIRS_5401/BROWSE/TARGETS/IMG0401130240_FP1_thumb.jpg',
             'COCIRS_5401/BROWSE/TARGETS/IMG0401130240_FP1_thumb.jpg'),
            ('volumes/COISS_0xxx/COISS_0001', 'COISS_0001'),
            ('volumes/COISS_0xxx', '')
        ]
    )
    def test_filespec(self, input_path, expected):
        """filespec: test on a file and one directory."""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        assert target_pdsfile.filespec == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COCIRS_1xxx/COCIRS_1001/DATA/TSDR/NAV_DATA/TAR10013100.lbl',
             True),
            ('volumes/COCIRS_5xxx/COCIRS_5401/DATA/GEODATA/GEO0401130240_699.tab',
             False)
        ]
    )
    def test_islabel(self, input_path, expected):
        """islabel: test on one label and one non label files."""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        assert target_pdsfile.islabel == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('diagrams/COCIRS_5xxx/COCIRS_5401/BROWSE/TARGETS/IMG0401130240_FP1_thumb.jpg',
             PDS3_HOLDINGS_DIR + '/diagrams/COCIRS_5xxx/COCIRS_5401/BROWSE/TARGETS/IMG0401130240_FP1_thumb.jpg'),
            ('volumes', PDS3_HOLDINGS_DIR + '/volumes')
        ]
    )
    def test_absolute_or_logical_path(self, input_path, expected):
        """absolute_or_logical_path: get abspath."""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        if expected is None: # pragma: no cover
            expected = PDS3_HOLDINGS_DIR + '/' + input_path
        assert target_pdsfile.absolute_or_logical_path == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('diagrams/COCIRS_6xxx/COCIRS_6004/BROWSE/SATURN/POI1004010000_FP1_small.jpg',
             '/holdings/diagrams/COCIRS_6xxx/COCIRS_6004/BROWSE/SATURN/POI1004010000_FP1_small.jpg'),
            ('volumes/COISS_1xxx/COISS_1001', '/holdings/volumes/COISS_1xxx/COISS_1001')
        ]
    )
    def test_html_path(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        expected = '/holdings/' + input_path if expected is None else expected
        assert target_pdsfile.html_path == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COISS_3xxx/COISS_3002/data/maps/SE_400K_90S_0_SMN.lbl',
             '.lbl'),
            ('volumes/COISS_3xxx/COISS_3002/data/maps/', '')
        ]
    )
    def test_extension(self, input_path, expected):
        """extension: test on one file and one directory."""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        try:
            dot_idx = input_path.rindex('.')
        except ValueError:
            dot_idx = None

        if expected is None: # pragma: no cover
            expected = input_path[dot_idx:] if dot_idx else ''
        assert target_pdsfile.extension == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COISS_3xxx/COISS_3002/data',
             'volumes/COISS_3xxx/COISS_3002'),
            ('volumes/COISS_2xxx/COISS_2002/data/1460960653_1461048959/N1460960868_1.IMG',
             'volumes/COISS_2xxx/COISS_2002/data/1460960653_1461048959')
        ]
    )
    def test_parent_logical_path(self, input_path, expected):
        """parent_logical_path: test on one file and one directory."""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        input_path = input_path[:-1] if input_path[-1] == '/' else input_path
        try:
            slash_idx = input_path.rindex('/')
        except ValueError: # pragma: no cover
            slash_idx = None

        if expected is None: # pragma: no cover
            expected = input_path[:slash_idx] if slash_idx else ''
        assert target_pdsfile.parent_logical_path == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('previews/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/HDAC1999_007_16_31_thumb.png',
             'HDAC1999_007_16_31'),
            ('volumes/COUVIS_8xxx/COUVIS_8001/data/UVIS_HSP_2017_228_BETORI_I_TAU10KM.LBL',
             'UVIS_HSP_2017_228_BETORI_I'),
        ]
    )
    def test_anchor(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        assert target_pdsfile.anchor == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COVIMS_0xxx/COVIMS_0001/data/1999010T054026_1999010T060958/v1294638283_1.lbl',
             'PDS3 label'),
            ('previews/COVIMS_0xxx/COVIMS_0001/data/1999010T054026_1999010T060958/v1294638283_1_thumb.png',
             'Thumbnail preview image')
        ]
    )
    def test_description(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        assert target_pdsfile.description == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COVIMS_8xxx/COVIMS_8001/data/VIMS_2017_251_GAMCRU_I_TAU_10KM.lbl', 'LABEL'),
            ('volumes/COVIMS_8xxx/COVIMS_8001/data/VIMS_2017_251_GAMCRU_I_TAU_10KM.tab', 'TABLE'),
            ('volumes/COVIMS_8xxx', 'VOLDIR'),
            ('volumes/COVIMS_0xxx/COVIMS_0001', 'VOLUME'),
            ('metadata/COVIMS_0xxx/COVIMS_0001/COVIMS_0001_index.tab', 'INDEX'),
            ('previews/COVIMS_0xxx', 'BROWDIR'),
            ('previews/COVIMS_0xxx/COVIMS_0001', 'BROWDIR'),
            ('previews/COVIMS_0xxx/COVIMS_0001/data1999010T054026_1999010T060958/v1294638283_1_thumb.png',
             'BROWSE'),
            ('metadata/COVIMS_0xxx/COVIMS_0001', 'INDEXDIR')
        ]
    )
    def test_icon_type(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        assert target_pdsfile.icon_type == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/EBROCC_xxxx/EBROCC_0001/DATA/ESO1M/ES1_EPD.TAB',
             'ES1_EPD.LBL'),
            ('volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/HDAC1999_007_16_31.dat',
             'HDAC1999_007_16_31.LBL'),
            ('previews/COISS_3xxx/COISS_3002/data/maps/SE_400K_0_108_SMN_thumb.png', '')
        ]
    )
    def test_label_basename(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        assert target_pdsfile.label_basename == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/GO_0xxx/GO_0017/J0/OPNAV/C0346405900R.IMG',
             PDS3_HOLDINGS_DIR + '/volumes/GO_0xxx/GO_0017/J0/OPNAV/C0346405900R.LBL'),
            ('volumes/GO_0xxx/GO_0017/J0/OPNAV', ''),
            ('metadata/GO_0xxx/GO_0017/GO_0017_index.tab',
             PDS3_HOLDINGS_DIR + '/metadata/GO_0xxx/GO_0017/GO_0017_index.lbl'),
            ('previews/GO_0xxx/GO_0017/J0/OPNAV/C0346405900R_med.jpg', '')
        ]
    )
    def test_label_abspath(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        assert target_pdsfile.label_abspath == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/HSTIx_xxxx/HSTI1_1556/DATA/VISIT_01/IB4W01I5Q.lbl',
             [
                'HST WFC3 images of the Pluto system 2010-04-24 to 2010-09-06',
                None
             ]),
            ('previews/GO_0xxx/GO_0017/J0/OPNAV/C0346405900R_med.jpg',
             [
                'Galileo Jupiter preview images 1996-06-03 to 1996-12-14 (SC clock 03464059-03740374)',
                None
             ]),
            ('metadata/COVIMS_0xxx/COVIMS_0001',
             [
                'Cassini VIMS metadata 1999-01-10 to 2000-09-18 (SC clock 1294638283-1347975444)',
                None
             ])
        ]
    )
    def test__volume_info(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        # remove duplicated blanks before this comparison
        assert ' '.join(target_pdsfile._volume_info[0].split()) == expected[0]
        assert target_pdsfile._volume_info[1] == expected[1]

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/HSTNx_xxxx/HSTN0_7176/DATA/VISIT_01/N4BI01L4Q.LBL',
             'hst-07176-nicmos-n4bi01l4q'),
            ('volumes/HSTJx_xxxx/HSTJ0_9296/DATA/VISIT_B1/J8M3B1021.lbl',
             'hst-09296-acs-j8m3b1021'),
            ('volumes/GO_0xxx/GO_0017/J0/OPNAV/C0346405900R.LBL',
             'go-ssi-c0346405900')
        ]
    )
    def test_opus_id(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        assert target_pdsfile.opus_id == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/HSTJx_xxxx/HSTJ0_9296/DATA/VISIT_B1/J8M3B1021.asc', False),
            ('previews/HSTJx_xxxx/HSTJ0_9296/DATA/VISIT_B1/J8M3B1021_thumb.jpg',
             True)
        ]
    )
    def test_is_viewable(self, input_path, expected):
        """is_viewable: test on one image and one non image files."""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        assert target_pdsfile.is_viewable == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('previews/HSTOx_xxxx/HSTO0_7308/DATA/VISIT_05/O43B05C1Q_small.jpg',
             'O43B05C1Q_small.jpg'),
            ('volumes/HSTOx_xxxx/HSTO0_7308/DATA/VISIT_05/O43B05C1Q.LBL',
             'O43B05C1Q.LBL')
        ]
    )
    def test_alt(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        assert target_pdsfile.alt == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('previews/HSTOx_xxxx/HSTO0_7308/DATA/VISIT_05/O43B05C1Q_small.jpg',
             [
                 '/holdings/previews/HSTOx_xxxx/HSTO0_7308/DATA/VISIT_05/O43B05C1Q_small.jpg',
                 '/holdings/previews/HSTOx_xxxx/HSTO0_7308/DATA/VISIT_05/O43B05C1Q_thumb.jpg',
                 '/holdings/previews/HSTOx_xxxx/HSTO0_7308/DATA/VISIT_05/O43B05C1Q_full.jpg',
                 '/holdings/previews/HSTOx_xxxx/HSTO0_7308/DATA/VISIT_05/O43B05C1Q_med.jpg',
             ]
            ),
            ('volumes/HSTOx_xxxx/HSTO0_7308/DATA/VISIT_05/O43B05C1Q.LBL',
             [
                '/holdings/previews/HSTOx_xxxx/HSTO0_7308/DATA/VISIT_05/O43B05C1Q_small.jpg',
                '/holdings/previews/HSTOx_xxxx/HSTO0_7308/DATA/VISIT_05/O43B05C1Q_thumb.jpg',
                '/holdings/previews/HSTOx_xxxx/HSTO0_7308/DATA/VISIT_05/O43B05C1Q_full.jpg',
                '/holdings/previews/HSTOx_xxxx/HSTO0_7308/DATA/VISIT_05/O43B05C1Q_med.jpg',
             ]
            ),
        ]
    )
    def test_viewset(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.viewset
        assert isinstance(res, pdsviewable.PdsViewSet)
        viewables = res.to_dict()['viewables']
        for viewable in viewables:
            assert viewable['url'] in expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/HSTUx_xxxx/HSTU0_5167/DATA/VISIT_04', True),
            ('volumes/EBROCC_xxxx/EBROCC_0001/CATALOG/ESO22M_DATASET.CAT',
             False)
        ]
    )
    def test_isdir(self, input_path, expected):
        """isdir: test on one directory and one label file."""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        assert target_pdsfile.isdir == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('metadata/HSTUx_xxxx/HSTU0_5167/HSTU0_5167_index.tab',
             PDS_PDSDATA_PATH + 'holdings/_indexshelf-metadata/HSTUx_xxxx/HSTU0_5167/HSTU0_5167_index.pickle')
        ]
    )
    def test_indexshelf_abspath(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        assert target_pdsfile.indexshelf_abspath == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('metadata/HSTUx_xxxx/HSTU0_5167/HSTU0_5167_index.tab',
             True)
        ]
    )
    def test_is_index(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        assert target_pdsfile.is_index == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('metadata/HSTUx_xxxx/HSTU0_5167/HSTU0_5167_index.tab',
             'HSTU0_5167_label.txt')
        ]
    )
    def test_index_pdslabel(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.index_pdslabel
        assert res != None
        assert res != 'failed'

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/NHxxLO_xxxx/NHLALO_1001/data/20060224_000310/'
             + 'lor_0003103486_0x630_eng.lbl', []),
            ('volumes/NHxxLO_xxxx/NHLALO_1001',
             [
                'aareadme.txt', 'calib', 'catalog', 'data',
                'document', 'index', 'voldesc.cat'
             ])
        ]
    )
    def test_childnames(self, input_path, expected):
        """childnames: test on one directory and one label file."""
        target_pdsfile = instantiate_target_pdsfile(input_path)
        assert target_pdsfile.childnames == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COCIRS_6xxx/COCIRS_6004/DATA/GEODATA/GEO1004021018_699.LBL',
             [
                PDS3_HOLDINGS_DIR + '/volumes/COCIRS_6xxx/COCIRS_6004/DATA/GEODATA/GEO1004021018_699.TAB'
             ])
        ]
    )
    def test_data_abspaths(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.data_abspaths

        for path in res:
            assert path in expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            # Need to revisit and find a proper case for this one
            ('archives-volumes/COCIRS_0xxx/COCIRS_0010.tar.gz',
             '')
        ]
    )
    def test_exact_archive_url(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.exact_archive_url
        assert res == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('archives-volumes/COCIRS_0xxx',
             '/holdings/checksums-archives-volumes/COCIRS_0xxx_md5.txt'),
            ('volumes/COCIRS_0xxx/COCIRS_0012/DATA/NAV_DATA/GEO00120100.DAT', ''),
            ('volumes/COCIRS_0xxx/COCIRS_0012/CALIB', ''),
            ('volumes/COCIRS_0xxx/COCIRS_0012',
             '/holdings/checksums-volumes/COCIRS_0xxx/COCIRS_0012_md5.txt')
        ]
    )
    def test_exact_checksum_url(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.exact_checksum_url
        assert res == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('diagrams/COCIRS_5xxx/COCIRS_5401/BROWSE/TARGETS/IMG0401130240_FP1_thumb.jpg',
             False),
            ('diagrams/COCIRS_5xxx/COCIRS_5401/BROWSE/TARGETS/',
             True),
        ]
    )
    def test_grid_view_allowed(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.grid_view_allowed
        assert res == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('diagrams/COCIRS_5xxx/COCIRS_5401/BROWSE/TARGETS/IMG0401130240_FP1_thumb.jpg',
             False),
            ('diagrams/COCIRS_5xxx/COCIRS_5401/BROWSE/TARGETS/',
             True),
        ]
    )
    def test_multipage_view_allowed(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.multipage_view_allowed
        assert res == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('diagrams/COCIRS_5xxx/COCIRS_5401/BROWSE/TARGETS/IMG0401130240_FP1_thumb.jpg',
             False),
            ('diagrams/COCIRS_5xxx/COCIRS_5401/BROWSE/TARGETS/',
             True),
        ]
    )
    def test_continuous_view_allowed(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.continuous_view_allowed
        assert res == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('diagrams/COCIRS_5xxx/COCIRS_5401/BROWSE/TARGETS/IMG0401130240_FP1_thumb.jpg',
             False),
            ('diagrams/COCIRS_5xxx/COCIRS_5401/BROWSE/TARGETS/',
             True),
        ]
    )
    def test_continuous_view_allowed2(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.continuous_view_allowed
        assert res == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COUVIS_0xxx/COUVIS_0001/DATA/', True),
            ('volumes/COUVIS_0xxx', False)
        ]
    )
    def test_has_neighbor_rule(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.has_neighbor_rule
        assert res == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('previews/COUVIS_0xxx/COUVIS_0009/DATA/D2004_274/EUV2004_274_01_39_thumb.png',
             'f43e6fe3d9eb02ed72e0aba47be443f2'),
            ('documents/COCIRS_0xxx', ''),
            ('documents/COCIRS_5xxx', ''),
            ('documents/COCISS_0xxx', ''),
            ('documents/COUVIS_0xxx', ''),
            ('documents/COUVIS_8xxx', ''),
            ('documents/COVIMS_0xxx', ''),
            ('documents/COVIMS_8xxx', ''),
        ]
    )
    def test_checksum(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.checksum
        assert res == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/HDAC1999_007_16_31.LBL',
             (PDS_PDSDATA_PATH + 'holdings/_infoshelf-volumes/COUVIS_0xxx/COUVIS_0001_info.pickle',
              'DATA/D1999_007/HDAC1999_007_16_31.LBL'))
        ]
    )
    def test_infoshelf_path_and_key(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.infoshelf_path_and_key
        assert res == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/HSTNx_xxxx/HSTN0_7176/DATA/VISIT_01/N4BI01L4Q.lbl', False),
            ('volumes/HSTNx_xxxx/HSTN0_7176', True)
        ]
    )
    def test_is_volume_dir(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.is_volume_dir
        assert res == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('checksums-volumes/COCIRS_0xxx/COCIRS_0010_md5.txt', True),
            ('archives-volumes/COCIRS_0xxx/COCIRS_0010.tar.gz', True),
            ('volumes/HSTNx_xxxx/HSTN0_7176', False)
        ]
    )
    def test_is_volume_file(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.is_volume_file
        assert res == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('checksums-volumes/COCIRS_0xxx/COCIRS_0010_md5.txt', True),
            ('archives-volumes/COCIRS_0xxx/COCIRS_0010.tar.gz', True),
            ('volumes/HSTNx_xxxx/HSTN0_7176', True),
            ('volumes/HSTNx_xxxx/HSTN0_7176/DATA/VISIT_01/N4BI01L4Q.lbl', False)
        ]
    )
    def test_is_volume(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.is_volume
        assert res == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('checksums-volumes/COCIRS_0xxx', True),
            ('archives-volumes/COCIRS_0xxx', True),
            ('volumes/HSTNx_xxxx', True),
            ('volumes/HSTNx_xxxx/HSTN0_7176', False)
        ]
    )
    def test_is_volset_dir(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.is_volset_dir
        assert res == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('checksums-volumes/COCIRS_0xxx/COCIRS_0010_md5.txt', False),
            ('archives-volumes/COCIRS_0xxx/COCIRS_0010.tar.gz', False),
            ('volumes/HSTNx_xxxx', False),
            ('volumes/HSTNx_xxxx/HSTN0_7176', False),
            ('volumes/COISS_1xxx/AAREADME.txt', True),
        ]
    )
    def test_is_volset_file(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.is_volset_file
        assert res == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('checksums-volumes/COCIRS_0xxx', True),
            ('archives-volumes/COCIRS_0xxx', True),
            ('volumes/HSTNx_xxxx', True),
            ('volumes/HSTNx_xxxx/HSTN0_7176', False),
            ('archives-volumes/COCIRS_0xxx/COCIRS_0010.tar.gz', False),
            ('volumes/COISS_1xxx/AAREADME.txt', True),
        ]
    )
    def test_is_volset(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.is_volset
        assert res == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/HSTNx_xxxx', False),
            ('volumes', True)
        ]
    )
    def test_is_category_dir(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.is_category_dir
        assert res == expected

    ############################################################################
    # Test for functions
    ############################################################################
    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('previews/VGISS_5xxx/VGISS_5101/DATA/C13854XX/C1385455_small.jpg',
             [
                '/holdings/previews/VGISS_5xxx/VGISS_5101/DATA/C13854XX/C1385455_small.jpg',
                '/holdings/previews/VGISS_5xxx/VGISS_5101/DATA/C13854XX/C1385455_med.jpg',
                '/holdings/previews/VGISS_5xxx/VGISS_5101/DATA/C13854XX/C1385455_full.jpg',
                '/holdings/previews/VGISS_5xxx/VGISS_5101/DATA/C13854XX/C1385455_thumb.jpg',
             ]
            ),
            ('previews/VGISS_5xxx/VGISS_5101/DATA/C13854XX',
             [
                '/holdings/previews/VGISS_5xxx/VGISS_5101/DATA/C13854XX/C1385455_small.jpg',
                '/holdings/previews/VGISS_5xxx/VGISS_5101/DATA/C13854XX/C1385455_med.jpg',
                '/holdings/previews/VGISS_5xxx/VGISS_5101/DATA/C13854XX/C1385455_full.jpg',
                '/holdings/previews/VGISS_5xxx/VGISS_5101/DATA/C13854XX/C1385455_thumb.jpg',
             ]
            ),
            ('volumes/VGISS_5xxx/VGISS_5101/DATA/C13854XX',
             [
                '/holdings/previews/VGISS_5xxx/VGISS_5101/DATA/C13854XX/C1385455_small.jpg',
                '/holdings/previews/VGISS_5xxx/VGISS_5101/DATA/C13854XX/C1385455_med.jpg',
                '/holdings/previews/VGISS_5xxx/VGISS_5101/DATA/C13854XX/C1385455_full.jpg',
                '/holdings/previews/VGISS_5xxx/VGISS_5101/DATA/C13854XX/C1385455_thumb.jpg',
             ]
            ),
            ('volumes/NHxxMV_xxxx/NHJUMV_1001/data/20070131_003252/mc0_0032528036_0x536_eng_1.fit',
             [
                '/holdings/previews/NHxxMV_xxxx/NHJUMV_1001/data/20070131_003252/mc0_0032528036_0x536_eng_1_small.jpg',
                '/holdings/previews/NHxxMV_xxxx/NHJUMV_1001/data/20070131_003252/mc0_0032528036_0x536_eng_1_med.jpg',
                '/holdings/previews/NHxxMV_xxxx/NHJUMV_1001/data/20070131_003252/mc0_0032528036_0x536_eng_1_full.jpg',
                '/holdings/previews/NHxxMV_xxxx/NHJUMV_1001/data/20070131_003252/mc0_0032528036_0x536_eng_1_thumb.jpg',
             ]
            ),
            ('volumes/NHxxLO_xxxx/NHJULO_1001/data/20070108_003059/lor_0030598439_0x630_eng.fit',
             [
                '/holdings/previews/NHxxLO_xxxx/NHJULO_1001/data/20070108_003059/lor_0030598439_0x630_eng_small.jpg',
                '/holdings/previews/NHxxLO_xxxx/NHJULO_1001/data/20070108_003059/lor_0030598439_0x630_eng_med.jpg',
                '/holdings/previews/NHxxLO_xxxx/NHJULO_1001/data/20070108_003059/lor_0030598439_0x630_eng_full.jpg',
                '/holdings/previews/NHxxLO_xxxx/NHJULO_1001/data/20070108_003059/lor_0030598439_0x630_eng_thumb.jpg',
             ]
            ),
        ]
    )
    def test_viewset_lookup(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.viewset_lookup()
        assert isinstance(res, pdsviewable.PdsViewSet)
        viewables = res.to_dict()['viewables']
        for viewable in viewables:
            assert viewable['url'] in expected

    @pytest.mark.parametrize(
        'input_suffix,expected',
        [
            ('_v2.1.3', (20103, 'Version 2.1.3 (superseded)', '2.1.3')),
        ]
    )
    def test_version_info(self, input_suffix, expected):
        res = pds3file.Pds3File.version_info(suffix=input_suffix)
        assert res == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('previews/VGISS_5xxx/VGISS_5101/DATA/C13854XX/C1385455_small.jpg',
             'Pds3File.VGISS_xxxx("' + PDS3_HOLDINGS_DIR + '/previews/VGISS_5xxx/VGISS_5101/DATA/C13854XX/C1385455_small.jpg")'),
        ]
    )
    def test___repr__1(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.__repr__()
        assert res == expected

    def test___repr__2(self):
        target_pdsfile = pds3file.Pds3File()
        res = target_pdsfile.__repr__()
        assert res == 'Pds3File("")'

    ############################################################################
    # Test for alternative constructors
    ############################################################################
    @pytest.mark.parametrize(
        'input_path,basename,expected',
        [
            ('volumes/COCIRS_6xxx/COCIRS_6004/DATA/GEODATA/',
             'GEO1004021018_699.LBL',
             PDS3_HOLDINGS_DIR + '/volumes/COCIRS_6xxx/COCIRS_6004/DATA/GEODATA/GEO1004021018_699.LBL'),
            ('metadata/COISS_1xxx/COISS_1001',
             'COISS_1001_inventory.tab',
             PDS3_HOLDINGS_DIR + '/metadata/COISS_1xxx/COISS_1001/COISS_1001_inventory.tab'),
        ]
    )
    def test_child(self, input_path, basename, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        print(target_pdsfile.category_)
        res = target_pdsfile.child(basename=basename)
        assert isinstance(res, pds3file.Pds3File)
        assert res.abspath == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COCIRS_0xxx_v3/COCIRS_0401/DATA/TSDR/NAV_DATA/TAR04012400.LBL',
             PDS3_HOLDINGS_DIR + '/volumes/COCIRS_0xxx_v3/COCIRS_0401/DATA/TSDR/NAV_DATA'),
            ('volumes/COCIRS_1xxx/COCIRS_1001/DATA/TSDR/NAV_DATA/TAR10013100.DAT',
             PDS3_HOLDINGS_DIR + '/volumes/COCIRS_1xxx/COCIRS_1001/DATA/TSDR/NAV_DATA'),
        ]
    )
    def test_parent(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.parent()
        assert isinstance(res, pds3file.Pds3File)
        assert res.abspath == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COISS_0xxx/COISS_0001/data/wacfm/bit_wght/13302/133020.lbl',
             'volumes/COISS_0xxx/COISS_0001/data/wacfm/bit_wght/13302/133020.lbl')
        ]
    )
    def test_from_logical_path(self, input_path, expected):
        res = pds3file.Pds3File.from_logical_path(path=input_path)
        assert isinstance(res, pds3file.Pds3File)
        assert res.logical_path == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COISS_0xxx/COISS_0001/data/wacfm/bit_wght/13302/133020.lbl',
             True),
            (PDS3_HOLDINGS_DIR + '/volumes/COISS_1xxx/COISS_1001/data/1294561143_1295221348/W1294561202_1.LBL',
             PDS3_HOLDINGS_DIR + '/volumes/COISS_1xxx/COISS_1001/data/1294561143_1295221348/W1294561202_1.LBL'),
        ]
    )
    def test_from_abspath(self, input_path, expected):
        try:
            res = pds3file.Pds3File.from_abspath(abspath=input_path)
            assert isinstance(res, pds3file.Pds3File)
            assert res.abspath == expected
        except ValueError as e:
            assert True # input path is not an absolute path

    @pytest.mark.parametrize(
        'input_lid,expected',
        [
            ('CO-S-ISSNA/ISSWA-2-EDR-V1.0:COISS_2002:data/1460960653_1461048959:N1460960868_1.IMG',
             ['CO-S-ISSNA/ISSWA-2-EDR-V1.0', 'N1460960868_1.IMG']),
            ('CO-E/V/J-ISSNA/ISSWA-2-EDR-V1.0:COISS_1001:data/1294561143_1295221348:W1294561202_1.LBL',
             ['CO-E/V/J-ISSNA/ISSWA-2-EDR-V1.0', 'W1294561202_1.LBL']),
            ('CO-E/V/J/S-VIMS-2-QUBE-V1.0:COVIMS_0001:data/1999010T054026_1999010T060958:v1294638283_1.qub',
             ['CO-E/V/J/S-VIMS-2-QUBE-V1.0', 'v1294638283_1.qub']),
            ('ESO1M-SR-APPH-4-OCC-V1.0:EBROCC_0001:DATA/ESO1M:ES1_EPD.LBL',
             ['ESO1M-SR-APPH-4-OCC-V1.0', 'ES1_EPD.LBL']),
            ('ESO22M-SR-APPH-4-OCC-V1.0:EBROCC_0001:CATALOG:ESO22M_DATASET.CAT',
             ['ESO22M-SR-APPH-4-OCC-V1.0', 'ESO22M_DATASET.CAT']),
            ('IRTF-SR-URAC-4-OCC-V1.0:EBROCC_0001:GEOMETRY/IRTF:IRT_IGD.TAB',
             ['IRTF-SR-URAC-4-OCC-V1.0', 'IRT_IGD.TAB']),
            ('LICK1M-SR-CCDC-4-OCC-V1.0:EBROCC_0001:INDEX:LIC_INDEX.LBL',
             ['LICK1M-SR-CCDC-4-OCC-V1.0', 'LIC_INDEX.LBL']),
            ('MCD27M-SR-IIRAR-4-OCC-V1.0:EBROCC_0001:DATA/MCD27M:MCD_IPD.TAB',
             ['MCD27M-SR-IIRAR-4-OCC-V1.0', 'MCD_IPD.TAB']),
            ('PAL200-SR-CIRC-4-OCC-V1.0:EBROCC_0001:DATA/PAL200:PAL_EPD.LBL',
             ['PAL200-SR-CIRC-4-OCC-V1.0', 'PAL_EPD.LBL']),

        ]
    )
    def test_from_lid_valid_lid(self, input_lid, expected):
        res = pds3file.Pds3File.from_lid(input_lid)
        assert isinstance(res, pds3file.Pds3File)
        assert res.data_set_id == expected[0]
        assert res.basename == expected[1]

    @pytest.mark.parametrize(
        'input_lid,expected',
        [
            ('CO-E/V/J/S-VIMS-2-QUBE-V2.0:COVIMS_0001:data/1999010T054026_1999010T060958:v1294638283_1.qub',
             'CO-E/V/J/S-VIMS-2-QUBE-V1.0'),
        ]
    )
    def test_from_lid_mismatched_lid(self, input_lid, expected):
        try:
            res = pds3file.Pds3File.from_lid(input_lid) # Must raise an exception
            assert False # pragma: no cover
        except ValueError as e:
            # input LID data set id doesn't match the one from res
            assert 'does not match the one from pdsfile:' in str(e)

    @pytest.mark.parametrize(
        'input_lid,expected',
        [
            ('CO-E/V/J/S-VIMS-2-QUBE-V2.0:data/1999010T054026_1999010T060958:v1294638283_1.qub',
             'CO-E/V/J/S-VIMS-2-QUBE-V1.0'),
        ]
    )
    def test_from_lid_invalid_lid(self, input_lid, expected):
        try:
            res = pds3file.Pds3File.from_lid(input_lid) # Must raise an exception
            assert False # pragma: no cover
        except ValueError as e:
            # input LID is not a valid LID
            assert 'is not a valid LID' in str(e)

    @pytest.mark.parametrize(
        'input_path,relative_path,expected',
        [
            ('previews/COUVIS_0xxx_v1/COUVIS_0009/DATA',
             '/D2004_274/EUV2004_274_01_39_thumb.png',
             'previews/COUVIS_0xxx_v1/COUVIS_0009/DATA/D2004_274/EUV2004_274_01_39_thumb.png'),
            ('volumes/COUVIS_0xxx/COUVIS_0001',
             '/DATA/D1999_007/FUV1999_007_16_57.LBL',
             'volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57.LBL'),
            ('volumes/COUVIS_0xxx/COUVIS_0001',
             '/DATAx/D1999_007/FUV1999_007_16_57.LBL',
             'volumes/COUVIS_0xxx/COUVIS_0001/DATAx/D1999_007/FUV1999_007_16_57.LBL'),
        ]
    )
    def test_from_relative_path(self, input_path, relative_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.from_relative_path(path=relative_path)
        assert isinstance(res, pds3file.Pds3File)
        assert res.logical_path == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/CORSS_8xxx/CORSS_8001/data/Rev007/Rev007E/Rev007E_RSS_2005_123_K34_E/RSS_2005_123_K34_E_CAL.LBL',
             PDS3_HOLDINGS_DIR + '/volumes/CORSS_8xxx/CORSS_8001/data/Rev007/Rev007E/Rev007E_RSS_2005_123_K34_E/RSS_2005_123_K34_E_CAL.LBL'),
            (PDS3_HOLDINGS_DIR + '/volumes/COISS_1xxx/COISS_1001/data/1294561143_1295221348/W1294561202_1.LBL',
             PDS3_HOLDINGS_DIR + '/volumes/COISS_1xxx/COISS_1001/data/1294561143_1295221348/W1294561202_1.LBL'),
        ]
    )
    def test__from_absolute_or_logical_path(self, input_path, expected):
        res = pds3file.Pds3File._from_absolute_or_logical_path(path=input_path)
        assert isinstance(res, pds3file.Pds3File)
        assert res.abspath == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('holdings/volumes/COUVIS_0xxx_v1/COUVIS_0009/DATA/D2004_274/EUV2004_274_01_39.DAT',
             PDS3_HOLDINGS_DIR + '/volumes/COUVIS_0xxx_v1/COUVIS_0009/DATA/D2004_274/EUV2004_274_01_39.DAT'),
            ('volumes/COCIRS_0xxx/COCIRS_0012/DATA/NAV_DATA/GEO00120100.DAT',
             PDS3_HOLDINGS_DIR + '/volumes/COCIRS_0xxx/COCIRS_0012/DATA/NAV_DATA/GEO00120100.DAT'),
            ('COVIMS_0xxx/COVIMS_0001/data/1999010T054026_1999010T060958',
             PDS3_HOLDINGS_DIR + '/volumes/COVIMS_0xxx/COVIMS_0001/data/1999010T054026_1999010T060958'),
            ('metadata/HSTOx_xxxx/HSTO0_7308',
             PDS3_HOLDINGS_DIR + '/metadata/HSTOx_xxxx/HSTO0_7308'),
            ('HSTOx_xxxx', PDS3_HOLDINGS_DIR + '/volumes/HSTOx_xxxx'),
            ('volumes/VGIRIS_xxxx_peer_review/VGIRIS_0001/DATA/JUPITER_VG1/C1547XXX.LBL',
             PDS3_HOLDINGS_DIR + '/volumes/VGIRIS_xxxx_peer_review/VGIRIS_0001/DATA/JUPITER_VG1/C1547XXX.LBL'),
            ('COCIRS_1001/DATA/CUBE/EQUIRECTANGULAR/123RI_EQLBS002_____CI____699_F1_039E.tar.gz',
             PDS3_HOLDINGS_DIR + '/volumes/COCIRS_1xxx/COCIRS_1001/DATA/CUBE/EQUIRECTANGULAR/123RI_EQLBS002_____CI____699_F1_039E.tar.gz'),
        ]
    )
    def test_from_path(self, input_path, expected):
        res = pds3file.Pds3File.from_path(path=input_path)
        assert isinstance(res, pds3file.Pds3File)
        assert res.abspath == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COVIMS_0xxx/COVIMS_0001/data/1999017T031657_1999175T202056/v1308946681_1_002.qub',
             True),
            ('documents/COCIRS_0xxx/Chan-etal-2015.link',
             None),
        ]
    )
    def test_shelf_exists_if_expected(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.shelf_exists_if_expected()
        assert res == expected

    ############################################################################
    # Test for OPUS support methods
    ############################################################################
    # from_filespec will only work with files under /volumes
    @pytest.mark.parametrize(
        'filespec,expected',
        [
            ('COISS_0001', PDS3_HOLDINGS_DIR + '/volumes/COISS_0xxx/COISS_0001'),
            ('COISS_1001/data/1294561143_1295221348/W1294561202_1.IMG',
             PDS3_HOLDINGS_DIR + '/volumes/COISS_1xxx/COISS_1001/data/1294561143_1295221348/W1294561202_1.IMG'),
            ('HSTI1_3667/DATA/VISIT_01/ICOK01H9Q.LBL',
             PDS3_HOLDINGS_DIR + '/volumes/HSTIx_xxxx/HSTI1_3667/DATA/VISIT_01/ICOK01H9Q.LBL'),
        ]
    )
    def test_from_filespec(self, filespec, expected):
        res = pds3file.Pds3File.from_filespec(filespec=filespec)
        assert isinstance(res, pds3file.Pds3File)
        assert res.abspath == expected

    @pytest.mark.parametrize(
        'input_id,expected',
        [
            ('co-cirs-0408010000-fp1',
             'volumes/COCIRS_5xxx/COCIRS_5408/DATA/APODSPEC/SPEC0408010000_FP1.DAT'),
            ('co-iss-w1294561143',
             'volumes/COISS_1xxx/COISS_1001/data/1294561143_1295221348/W1294561143_1.IMG'),
            ('co-uvis-hdac1999_007_16_33',
             'volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/HDAC1999_007_16_33.DAT'),
            ('co-vims-v1490784910_001',
             'volumes/COVIMS_0xxx/COVIMS_0006/data/2005088T102825_2005089T113931/v1490784910_3_001.qub'),
            ('go-ssi-c0346405900',
             'volumes/GO_0xxx/GO_0017/J0/OPNAV/C0346405900R.IMG'),
            ('vg-iss-1-j-c1385455',
             'volumes/VGISS_5xxx/VGISS_5101/DATA/C13854XX/C1385455_RAW.IMG'),
            ('hst-09296-acs-j8m3b1021',
             'volumes/HSTJx_xxxx/HSTJ0_9296/DATA/VISIT_B1/J8M3B1021.LBL'),
            ('hst-11559-wfc3-ib4v11mnq',
             'volumes/HSTIx_xxxx/HSTI1_1559/DATA/VISIT_11/IB4V11MNQ.LBL'),
            ('hst-07176-nicmos-n4bi01l4q',
             'volumes/HSTNx_xxxx/HSTN0_7176/DATA/VISIT_01/N4BI01L4Q.LBL'),
            ('hst-07308-stis-o43b05c1q',
             'volumes/HSTOx_xxxx/HSTO0_7308/DATA/VISIT_05/O43B05C1Q.LBL'),
            ('hst-05167-wfpc2-u2no0404t',
             'volumes/HSTUx_xxxx/HSTU0_5167/DATA/VISIT_04/U2NO0404T.LBL'),
            ('nh-lorri-lor_0003103486',
             'volumes/NHxxLO_xxxx/NHLALO_1001/data/20060224_000310/lor_0003103486_0x630_eng.fit'),
            ('esosil1m04-apph-occ-1989-184-28sgr-e',
             'volumes/EBROCC_xxxx/EBROCC_0001/DATA/ESO1M/ES1_EPD.TAB'),
            ('esosil2m2-apph-occ-1989-184-28sgr-i',
             'volumes/EBROCC_xxxx/EBROCC_0001/DATA/ESO22M/ES2_IPD.TAB'),
            ('lick1m-ccdc-occ-1989-184-28sgr-e',
             'volumes/EBROCC_xxxx/EBROCC_0001/DATA/LICK1M/LIC_EPD.TAB'),
            ('irtf3m2-urac-occ-1989-184-28sgr-i',
             'volumes/EBROCC_xxxx/EBROCC_0001/DATA/IRTF/IRT_IPD.TAB'),
            ('pal5m08-circ-occ-1989-184-28sgr-i',
             'volumes/EBROCC_xxxx/EBROCC_0001/DATA/PAL200/PAL_IPD.TAB'),
            ('mcd2m7-iirar-occ-1989-184-28sgr-i',
             'volumes/EBROCC_xxxx/EBROCC_0001/DATA/MCD27M/MCD_IPD.TAB'),
            ('co-rss-occ-2005-159-rev009-k55-e',
             'volumes/CORSS_8xxx/CORSS_8001/data/Rev009/Rev009E/Rev009E_RSS_2005_159_K55_E/RSS_2005_159_K55_E_TAU_01KM.TAB'),

            # ('nh-mvic-mc0_0032528036',
            # 'volumes/NHxxMV_xxxx/NHJUMV_1001/data/20070131_003252/mc0_0032528036_0x536_eng_1.fit'),
            # ('nh-mvic-mc0_0005261846',
            # 'volumes/NHxxMV_xxxx/NHLAMV_1001/data/20060321_000526/mc0_0005261846_0x536_eng_1.fit'),

        ]
    )
    def test_from_opus_id1(self, input_id, expected):
        target_pdsfile1 = pds3file.Pds3File.from_opus_id(input_id)
        logical_path1 = target_pdsfile1.logical_path
        target_pdsfile2 = instantiate_target_pdsfile(
            logical_path1, is_abspath=False)
        assert logical_path1 == expected
        assert target_pdsfile1.opus_id == input_id
        assert target_pdsfile2.opus_id == input_id

    @pytest.mark.parametrize(
        'opus_id,expected',
        [
            ('hst-07176-nicmos-n4bi01l4q',
             PDS3_HOLDINGS_DIR + '/volumes/HSTNx_xxxx/HSTN0_7176/DATA/VISIT_01/N4BI01L4Q.LBL')
        ]
    )
    def test_from_opus_id2(self, opus_id, expected):
        res = pds3file.Pds3File.from_opus_id(opus_id=opus_id)
        assert isinstance(res, pds3file.Pds3File)
        assert res.abspath == expected


    ############################################################################
    # Test for associated volumes and volsets
    ############################################################################
    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COVIMS_0xxx/COVIMS_0001/data/1999010T054026_1999010T060958/v1294638283_1.lbl',
             'volumes/COVIMS_0xxx/COVIMS_0001'),
        ]
    )
    def test_volume_pdsfile(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.volume_pdsfile()
        assert isinstance(res, pds3file.Pds3File)
        assert res.logical_path == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/EBROCC_xxxx/EBROCC_0001/CATALOG/ESO22M_DATASET.CAT',
             'volumes/EBROCC_xxxx'),
        ]
    )
    def test_volset_pdsfile(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.volset_pdsfile()
        assert isinstance(res, pds3file.Pds3File)
        assert res.logical_path == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('metadata/VGISS_8xxx/VGISS_8201/VGISS_8201_inventory.tab',
             PDS3_HOLDINGS_DIR + '/metadata/VGISS_8xxx/VGISS_8201'),
            ('metadata/VGISS_6xxx/VGISS_6101',
             PDS3_HOLDINGS_DIR + '/metadata/VGISS_6xxx/VGISS_6101'),
            ('volumes/VGISS_7xxx/VGISS_7201/DATA/C24476XX/C2447654_RAW.lbl',
             PDS3_HOLDINGS_DIR + '/volumes/VGISS_7xxx/VGISS_7201')
        ]
    )
    def test_volume_abspath(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        assert target_pdsfile.volume_abspath() == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/HSTOx_xxxx/HSTO0_7308/DATA/VISIT_05/O43B05C1Q.ASC',
             PDS3_HOLDINGS_DIR + '/volumes/HSTOx_xxxx'),
            ('previews/HSTNx_xxxx/HSTN0_7176/DATA/VISIT_01/N4BI01L4Q_thumb.jpg',
             PDS3_HOLDINGS_DIR + '/previews/HSTNx_xxxx')
        ]
    )
    def test_volset_abspath(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        assert target_pdsfile.volset_abspath() == expected

    ############################################################################
    # Test for support for Pds3File objects representing index rows
    ############################################################################
    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('metadata/HSTUx_xxxx/HSTU0_5167/HSTU0_5167_index.tab',
             {'U2NO0401T': [0], 'U2NO0402T': [1], 'U2NO0403T': [2], 'U2NO0404T': [3]}),
        ]
    )
    def test_get_indexshelf(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.get_indexshelf()
        assert res == expected

    @pytest.mark.parametrize(
        'input_path,selection,flag,expected',
        [
            ('metadata/HSTUx_xxxx/HSTU0_5167/HSTU0_5167_index.tab',
             'U2NO0403T', '', 'U2NO0403T'),
            ('metadata/HSTUx_xxxx/HSTU0_5167/HSTU0_5167_index.tab',
             'U2NO0404Tx', '<', 'U2NO0404T'),
            ('metadata/HSTUx_xxxx/HSTU0_5167/HSTU0_5167_index.tab',
             'U2NO0404T', '<', 'U2NO0404T'),
            ('metadata/HSTUx_xxxx/HSTU0_5167/HSTU0_5167_index.tab',
             'U2NO0402Tx', '>', 'U2NO0402T'),
            ('metadata/HSTUx_xxxx/HSTU0_5167/HSTU0_5167_index.tab',
             'U2NO0402T', '>', 'U2NO0402T'),
            ('metadata/HSTUx_xxxx/HSTU0_5167/HSTU0_5167_index.tab',
             'U2NO0401T', '=', 'U2NO0401T'),
        ]
    )
    def test_find_selected_row_key(self, input_path, selection, flag, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        print(target_pdsfile.childnames)
        res = target_pdsfile.find_selected_row_key(selection, flag)
        assert res == expected

    @pytest.mark.parametrize(
        'input_path,selection,flag,expected',
        [
            ('metadata/HSTUx_xxxx/HSTU0_5167/HSTU0_5167_index.tab',
             'U2NO0404T', '=',
             'metadata/HSTUx_xxxx/HSTU0_5167/HSTU0_5167_index.tab/U2NO0404T'),
            ('metadata/HSTUx_xxxx/HSTU0_5167/HSTU0_5167_index.tab',
             'U2NO0403Tx', '>',
             'metadata/HSTUx_xxxx/HSTU0_5167/HSTU0_5167_index.tab/U2NO0403T'),
            ('metadata/HSTUx_xxxx/HSTU0_5167/HSTU0_5167_index.tab',
             'U2NO0403T', '>',
             'metadata/HSTUx_xxxx/HSTU0_5167/HSTU0_5167_index.tab/U2NO0403T'),
            ('metadata/HSTUx_xxxx/HSTU0_5167/HSTU0_5167_index.tab',
             'U2NO0401Tx', '<',
             'metadata/HSTUx_xxxx/HSTU0_5167/HSTU0_5167_index.tab/U2NO0401T'),
            ('metadata/HSTUx_xxxx/HSTU0_5167/HSTU0_5167_index.tab',
             'U2NO0401T', '<',
             'metadata/HSTUx_xxxx/HSTU0_5167/HSTU0_5167_index.tab/U2NO0401T'),
            ('metadata/HSTUx_xxxx/HSTU0_5167/HSTU0_5167_index.tab',
             'U2NO0402T', '',
             'metadata/HSTUx_xxxx/HSTU0_5167/HSTU0_5167_index.tab/U2NO0402T'),
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
             'U2NO0404T', '',
             PDS3_HOLDINGS_DIR + '/volumes/HSTUx_xxxx/HSTU0_5167/DATA/VISIT_04/U2NO0404T.LBL'),
        ]
    )
    def test_data_abspath_associated_with_index_row(self, input_path,
                                                    selection, flag,
                                                    expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        index_row = target_pdsfile.child_of_index(selection, flag)
        res = index_row.data_abspath_associated_with_index_row()
        assert res == expected

    ############################################################################
    # Test for checksum path associations
    ############################################################################
    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COUVIS_0xxx_v1/COUVIS_0009/DATA/D2004_274/EUV2004_274_01_39.lbl',
             PDS3_HOLDINGS_DIR + '/checksums-volumes/COUVIS_0xxx_v1/COUVIS_0009_md5.txt'),
            ('metadata/VGISS_5xxx/VGISS_5101/VGISS_5101_supplemental_index.tab',
             PDS3_HOLDINGS_DIR + '/checksums-metadata/VGISS_5xxx/VGISS_5101_metadata_md5.txt'),
            ('archives-volumes/COCIRS_0xxx',
             PDS3_HOLDINGS_DIR + '/checksums-archives-volumes/COCIRS_0xxx_md5.txt')
        ]
    )
    def test_checksum_path_and_lskip(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        if target_pdsfile.archives_:
            lskip = (len(target_pdsfile.root_) + len('checksums_')
                     + len(target_pdsfile.category_))
        else:
            lskip = (len(target_pdsfile.root_) + len('checksums_')
                     + len(target_pdsfile.category_)
                     + len(target_pdsfile.bundleset_))
        expected = (expected, lskip)
        assert target_pdsfile.checksum_path_and_lskip() == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('archives-volumes/COCIRS_0xxx',
             PDS3_HOLDINGS_DIR + '/checksums-archives-volumes/COCIRS_0xxx_md5.txt'),
            ('volumes/COCIRS_0xxx/COCIRS_0010',
             PDS3_HOLDINGS_DIR + '/checksums-volumes/COCIRS_0xxx/COCIRS_0010_md5.txt'),
            ('checksums-volumes/COCIRS_0xxx/COCIRS_0010_md5.txt', '')
        ]
    )
    def test_checksum_path_if_exact(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.checksum_path_if_exact()
        assert res == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            # ('archives-volumes/COCIRS_0xxx/COCIRS_0010.tar.gz',
            #  (
            #     PDS3_HOLDINGS_DIR + '/archives-volumes/COCIRS_0xxx',
            #     PDS3_HOLDINGS_DIR + '/archives-volumes/COCIRS_0xxx/')),
            ('checksums-volumes/COCIRS_0xxx/COCIRS_0010_md5.txt',
             (
                PDS3_HOLDINGS_DIR + '/volumes/COCIRS_0xxx/COCIRS_0010',
                PDS3_HOLDINGS_DIR + '/volumes/COCIRS_0xxx/')),
        ]
    )
    def test_dirpath_and_prefix_for_checksum(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.dirpath_and_prefix_for_checksum()
        assert res == expected

    ############################################################################
    # Test for archive path associations
    ############################################################################
    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('metadata/HSTUx_xxxx/HSTU0_5167/HSTU0_5167_index.tab',
             PDS3_HOLDINGS_DIR + '/archives-metadata/HSTUx_xxxx/HSTU0_5167_metadata.tar.gz'),
            ('volumes/EBROCC_xxxx/EBROCC_0001/DATA/ESO1M/ES1_EPD.LBL',
             PDS3_HOLDINGS_DIR + '/archives-volumes/EBROCC_xxxx/EBROCC_0001.tar.gz')
        ]
    )
    def test_archive_path_and_lskip(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        lskip = (len(target_pdsfile.root_) + len(target_pdsfile.category_)
                 + len(target_pdsfile.bundleset_))
        expected = (expected, lskip)
        assert target_pdsfile.archive_path_and_lskip() == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('archives-volumes/COCIRS_0xxx/COCIRS_0010.tar.gz', ''),
            ('volumes/COCIRS_0xxx/COCIRS_0010',
             PDS3_HOLDINGS_DIR + '/archives-volumes/COCIRS_0xxx/COCIRS_0010.tar.gz'),
        ]
    )
    def test_archive_path_if_exact(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.archive_path_if_exact()
        assert res == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('archives-volumes/COCIRS_0xxx/COCIRS_0010.tar.gz',
             (PDS3_HOLDINGS_DIR + '/volumes/COCIRS_0xxx/COCIRS_0010',
              PDS3_HOLDINGS_DIR + '/volumes/COCIRS_0xxx/')),
        ]
    )
    def test_dirpath_and_prefix_for_archive(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.dirpath_and_prefix_for_archive()
        assert res == expected

    @pytest.mark.parametrize(
        'input_path,task,expected',
        [
            ('archives-volumes/COCIRS_0xxx/COCIRS_0012.tar.gz', '',
             PDS_PDSDATA_PATH + 'logs/archives/volumes/COCIRS_0xxx/COCIRS_0012_targz_.*.log')
        ]
    )
    def test_archive_logpath(self, input_path, task, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.archive_logpath(task=task)
        # escape possible "(" & ")" if that exists in PDS_PDSDATA_PATH
        expected = expected.replace('(', '\\(')
        expected = expected.replace(')', '\\)')
        assert re.match(expected, res)

    ############################################################################
    # Test for shelf support
    ############################################################################
    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/VGISS_5xxx/VGISS_5101/DATA/C13854XX/C1385455_RAW.lbl',
             PDS_PDSDATA_PATH + 'holdings/_infoshelf-volumes/VGISS_5xxx/VGISS_5101_info.pickle'),
            ('metadata/NHxxLO_xxxx/NHLALO_1001/NHLALO_1001_inventory.tab',
             PDS_PDSDATA_PATH + 'holdings/_infoshelf-metadata/NHxxLO_xxxx/NHLALO_1001_info.pickle'),
            ('archives-volumes/EBROCC_xxxx/EBROCC_0001.tar.gz',
             PDS_PDSDATA_PATH + 'holdings/_infoshelf-archives-volumes/EBROCC_xxxx_info.pickle')
        ]
    )
    def test_shelf_path_and_lskip(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        if target_pdsfile.archives_:
            lskip = (len(target_pdsfile.root_) + len(target_pdsfile.category_)
                     + len(target_pdsfile.bundleset_))
        else:
            lskip = (len(target_pdsfile.root_) + len(target_pdsfile.category_)
                     + len(target_pdsfile.bundleset_) + len(target_pdsfile.bundlename)
                     + 1)
        expected = (expected, lskip)
        assert target_pdsfile.shelf_path_and_lskip() == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            (PDS_PDSDATA_PATH + 'holdings/_infoshelf-volumes/VGISS_5xxx/VGISS_5101_info.pickle',
             None),
        ]
    )
    def test__get_shelf(self, input_path, expected):
        assert pds3file.Pds3File._get_shelf(input_path) != expected

    ############################################################################
    # Test for log path associations
    ############################################################################
    @pytest.mark.parametrize(
        'input_path,suffix,task,dir,place,logroot,expected',
        [
            ('volumes/HSTIx_xxxx/HSTI1_1556', '', '', '', 'default', None,
             PDS_PDSDATA_PATH + r'logs/volumes/HSTIx_xxxx/HSTI1_1556_20..-..-..T..-..-..\.log'),
            ('volumes/HSTIx_xxxx/HSTI1_1556', '', '', '', 'parallel', None,
             PDS_PDSDATA_PATH + r'logs/volumes/HSTIx_xxxx/HSTI1_1556_20..-..-..T..-..-..\.log'),
            ('volumes/HSTIx_xxxx/HSTI1_1556', 'alligator', '', '', 'default', None,
             PDS_PDSDATA_PATH + r'logs/volumes/HSTIx_xxxx/HSTI1_1556_alligator_20..-..-..T..-..-..\.log'),
            ('volumes/HSTIx_xxxx/HSTI1_1556', 'alligator', '', '', 'parallel', None,
             PDS_PDSDATA_PATH + r'logs/volumes/HSTIx_xxxx/HSTI1_1556_alligator_20..-..-..T..-..-..\.log'),

            ('volumes/HSTIx_xxxx/HSTI1_1556', '', 'wrestle', '', 'default', None,
             PDS_PDSDATA_PATH + r'logs/volumes/HSTIx_xxxx/HSTI1_1556_20..-..-..T..-..-.._wrestle\.log'),
            ('volumes/HSTIx_xxxx/HSTI1_1556', '', 'wrestle', '', 'parallel', None,
             PDS_PDSDATA_PATH + r'logs/volumes/HSTIx_xxxx/HSTI1_1556_20..-..-..T..-..-.._wrestle\.log'),
            ('volumes/HSTIx_xxxx/HSTI1_1556', 'alligator', 'wrestle', '', 'default', None,
             PDS_PDSDATA_PATH + r'logs/volumes/HSTIx_xxxx/HSTI1_1556_alligator_20..-..-..T..-..-.._wrestle\.log'),
            ('volumes/HSTIx_xxxx/HSTI1_1556', 'alligator', 'wrestle', '', 'parallel', None,
             PDS_PDSDATA_PATH + r'logs/volumes/HSTIx_xxxx/HSTI1_1556_alligator_20..-..-..T..-..-.._wrestle\.log'),

            ('volumes/HSTIx_xxxx/HSTI1_1556', '', 'wrestle', 'tallahassee', 'default', None,
             PDS_PDSDATA_PATH + r'logs/tallahassee/volumes/HSTIx_xxxx/HSTI1_1556_20..-..-..T..-..-.._wrestle\.log'),
            ('volumes/HSTIx_xxxx/HSTI1_1556', '', 'wrestle', 'tallahassee', 'parallel', None,
             PDS_PDSDATA_PATH + r'logs/tallahassee/volumes/HSTIx_xxxx/HSTI1_1556_20..-..-..T..-..-.._wrestle\.log'),
            ('volumes/HSTIx_xxxx/HSTI1_1556', 'alligator', 'wrestle', 'tallahassee', 'default', None,
             PDS_PDSDATA_PATH + r'logs/tallahassee/volumes/HSTIx_xxxx/HSTI1_1556_alligator_20..-..-..T..-..-.._wrestle\.log'),
            ('volumes/HSTIx_xxxx/HSTI1_1556', 'alligator', 'wrestle', 'tallahassee', 'parallel', None,
             PDS_PDSDATA_PATH + r'logs/tallahassee/volumes/HSTIx_xxxx/HSTI1_1556_alligator_20..-..-..T..-..-.._wrestle\.log'),

            ('volumes/HSTIx_xxxx/HSTI1_1556', '', 'wrestle', 'tallahassee', 'default', '/florida',
             r'/florida/tallahassee/volumes/HSTIx_xxxx/HSTI1_1556_20..-..-..T..-..-.._wrestle\.log'),
            ('volumes/HSTIx_xxxx/HSTI1_1556', '', 'wrestle', 'tallahassee', 'parallel', '/florida',
             PDS_PDSDATA_PATH + r'logs/tallahassee/volumes/HSTIx_xxxx/HSTI1_1556_20..-..-..T..-..-.._wrestle\.log'),
            ('volumes/HSTIx_xxxx/HSTI1_1556', 'alligator', 'wrestle', 'tallahassee', 'default', '/florida',
             r'/florida/tallahassee/volumes/HSTIx_xxxx/HSTI1_1556_alligator_20..-..-..T..-..-.._wrestle\.log'),
            ('volumes/HSTIx_xxxx/HSTI1_1556', 'alligator', 'wrestle', 'tallahassee', 'parallel', '/florida',
             PDS_PDSDATA_PATH + r'logs/tallahassee/volumes/HSTIx_xxxx/HSTI1_1556_alligator_20..-..-..T..-..-.._wrestle\.log'),
        ]
    )
    def test_log_path_for_volume(self, input_path, suffix, task, dir, place, logroot, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        pds3file.Pds3File.set_log_root(logroot)
        res = target_pdsfile.log_path_for_volume(suffix, task, dir, place)
        pds3file.Pds3File.set_log_root()
        # escape possible "(" & ")" if that exists in PDS_PDSDATA_PATH
        expected = expected.replace('(', '\\(')
        expected = expected.replace(')', '\\)')
        assert re.match(expected, res)

    @pytest.mark.parametrize(
        'input_path,suffix,task,dir,place,logroot,expected',
        [
            ('volumes/HSTIx_xxxx/HSTI1_1556', '', '', '', 'default', None,
             PDS_PDSDATA_PATH + r'logs/volumes/HSTIx_xxxx_20..-..-..T..-..-..\.log'),
            ('volumes/HSTIx_xxxx/HSTI1_1556', '', '', '', 'parallel', None,
             PDS_PDSDATA_PATH + r'logs/volumes/HSTIx_xxxx_20..-..-..T..-..-..\.log'),
            ('volumes/HSTIx_xxxx/HSTI1_1556', 'alligator', '', '', 'default', None,
             PDS_PDSDATA_PATH + r'logs/volumes/HSTIx_xxxx_alligator_20..-..-..T..-..-..\.log'),
            ('volumes/HSTIx_xxxx/HSTI1_1556', 'alligator', '', '', 'parallel', None,
             PDS_PDSDATA_PATH + r'logs/volumes/HSTIx_xxxx_alligator_20..-..-..T..-..-..\.log'),

            ('volumes/HSTIx_xxxx/HSTI1_1556', '', 'wrestle', '', 'default', None,
             PDS_PDSDATA_PATH + r'logs/volumes/HSTIx_xxxx_20..-..-..T..-..-.._wrestle\.log'),
            ('volumes/HSTIx_xxxx/HSTI1_1556', '', 'wrestle', '', 'parallel', None,
             PDS_PDSDATA_PATH + r'logs/volumes/HSTIx_xxxx_20..-..-..T..-..-.._wrestle\.log'),
            ('volumes/HSTIx_xxxx/HSTI1_1556', 'alligator', 'wrestle', '', 'default', None,
             PDS_PDSDATA_PATH + r'logs/volumes/HSTIx_xxxx_alligator_20..-..-..T..-..-.._wrestle\.log'),
            ('volumes/HSTIx_xxxx/HSTI1_1556', 'alligator', 'wrestle', '', 'parallel', None,
             PDS_PDSDATA_PATH + r'logs/volumes/HSTIx_xxxx_alligator_20..-..-..T..-..-.._wrestle\.log'),

            ('volumes/HSTIx_xxxx/HSTI1_1556', '', 'wrestle', 'tallahassee', 'default', None,
             PDS_PDSDATA_PATH + r'logs/tallahassee/volumes/HSTIx_xxxx_20..-..-..T..-..-.._wrestle\.log'),
            ('volumes/HSTIx_xxxx/HSTI1_1556', '', 'wrestle', 'tallahassee', 'parallel', None,
             PDS_PDSDATA_PATH + r'logs/tallahassee/volumes/HSTIx_xxxx_20..-..-..T..-..-.._wrestle\.log'),
            ('volumes/HSTIx_xxxx/HSTI1_1556', 'alligator', 'wrestle', 'tallahassee', 'default', None,
             PDS_PDSDATA_PATH + r'logs/tallahassee/volumes/HSTIx_xxxx_alligator_20..-..-..T..-..-.._wrestle\.log'),
            ('volumes/HSTIx_xxxx/HSTI1_1556', 'alligator', 'wrestle', 'tallahassee', 'parallel', None,
             PDS_PDSDATA_PATH + r'logs/tallahassee/volumes/HSTIx_xxxx_alligator_20..-..-..T..-..-.._wrestle\.log'),

            ('volumes/HSTIx_xxxx/HSTI1_1556', '', 'wrestle', 'tallahassee', 'default', '/florida',
             r'/florida/tallahassee/volumes/HSTIx_xxxx_20..-..-..T..-..-.._wrestle\.log'),
            ('volumes/HSTIx_xxxx/HSTI1_1556', '', 'wrestle', 'tallahassee', 'parallel', '/florida',
             PDS_PDSDATA_PATH + r'logs/tallahassee/volumes/HSTIx_xxxx_20..-..-..T..-..-.._wrestle\.log'),
            ('volumes/HSTIx_xxxx/HSTI1_1556', 'alligator', 'wrestle', 'tallahassee', 'default', '/florida',
             r'/florida/tallahassee/volumes/HSTIx_xxxx_alligator_20..-..-..T..-..-.._wrestle\.log'),
            ('volumes/HSTIx_xxxx/HSTI1_1556', 'alligator', 'wrestle', 'tallahassee', 'parallel', '/florida',
             PDS_PDSDATA_PATH + r'logs/tallahassee/volumes/HSTIx_xxxx_alligator_20..-..-..T..-..-.._wrestle\.log'),
        ]
    )
    def test_log_path_for_volset(self, input_path, suffix, task, dir, place, logroot, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        pds3file.Pds3File.set_log_root(logroot)
        res = target_pdsfile.log_path_for_volset(suffix, task, dir, place)
        pds3file.Pds3File.set_log_root()
        # escape possible "(" & ")" if that exists in PDS_PDSDATA_PATH
        expected = expected.replace('(', '\\(')
        expected = expected.replace(')', '\\)')
        assert re.match(expected, res)

    @pytest.mark.parametrize(
        'input_path,task,dir,place,logroot,expected',
        [
            ('metadata/HSTIx_xxxx/HSTI1_1556/HSTI1_1556_hstfiles.tab', '', '', 'default', None,
             PDS_PDSDATA_PATH + r'logs/metadata/HSTIx_xxxx/HSTI1_1556/HSTI1_1556_hstfiles_20..-..-..T..-..-..\.log'),
            ('metadata/HSTIx_xxxx/HSTI1_1556/HSTI1_1556_hstfiles.tab', '', '', 'parallel', None,
             PDS_PDSDATA_PATH + r'logs/metadata/HSTIx_xxxx/HSTI1_1556/HSTI1_1556_hstfiles_20..-..-..T..-..-..\.log'),
            ('metadata/HSTIx_xxxx/HSTI1_1556/HSTI1_1556_hstfiles.tab', 'scramble', '', 'default', None,
             PDS_PDSDATA_PATH + r'logs/metadata/HSTIx_xxxx/HSTI1_1556/HSTI1_1556_hstfiles_20..-..-..T..-..-.._scramble\.log'),
            ('metadata/HSTIx_xxxx/HSTI1_1556/HSTI1_1556_hstfiles.tab', 'scramble', '', 'parallel', None,
             PDS_PDSDATA_PATH + r'logs/metadata/HSTIx_xxxx/HSTI1_1556/HSTI1_1556_hstfiles_20..-..-..T..-..-.._scramble\.log'),

            ('metadata/HSTIx_xxxx/HSTI1_1556/HSTI1_1556_hstfiles.tab', 'scramble', 'eggs', 'default', None,
             PDS_PDSDATA_PATH + r'logs/eggs/metadata/HSTIx_xxxx/HSTI1_1556/HSTI1_1556_hstfiles_20..-..-..T..-..-.._scramble\.log'),
            ('metadata/HSTIx_xxxx/HSTI1_1556/HSTI1_1556_hstfiles.tab', 'scramble', 'eggs', 'parallel', None,
             PDS_PDSDATA_PATH + r'logs/eggs/metadata/HSTIx_xxxx/HSTI1_1556/HSTI1_1556_hstfiles_20..-..-..T..-..-.._scramble\.log'),
            ('metadata/HSTIx_xxxx/HSTI1_1556/HSTI1_1556_hstfiles.tab', 'scramble', 'eggs', 'default', '/green',
             r'/green/eggs/metadata/HSTIx_xxxx/HSTI1_1556/HSTI1_1556_hstfiles_20..-..-..T..-..-.._scramble\.log'),
            ('metadata/HSTIx_xxxx/HSTI1_1556/HSTI1_1556_hstfiles.tab', 'scramble', 'eggs', 'parallel', '/green',
             PDS_PDSDATA_PATH + r'logs/eggs/metadata/HSTIx_xxxx/HSTI1_1556/HSTI1_1556_hstfiles_20..-..-..T..-..-.._scramble\.log'),
        ]
    )
    def test_log_path_for_index(self, input_path, task, dir, place, logroot, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        pds3file.Pds3File.set_log_root(logroot)
        res = target_pdsfile.log_path_for_index(task, dir, place)
        pds3file.Pds3File.set_log_root()
        # escape possible "(" & ")" if that exists in PDS_PDSDATA_PATH
        expected = expected.replace('(', '\\(')
        expected = expected.replace(')', '\\)')
        assert re.match(expected, res)

    ############################################################################
    # Test for split and sort filenames
    ############################################################################
    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COCIRS_5xxx/COCIRS_5401/DATA/GEODATA/GEO0401130240_699.lbl',
             ('GEO0401130240_699', '', '.lbl')),
            ('diagrams/COCIRS_6xxx/COCIRS_6004/BROWSE/SATURN/POI1004010000_FP1_small.jpg',
             ('POI1004010000_FP1', '_small', '.jpg'))
        ]
    )
    def test_split_basename(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        assert target_pdsfile.split_basename() == expected

    @pytest.mark.parametrize(
        'input_path,basenames,expected',
        [
            ('volumes/COCIRS_0xxx/COCIRS_0410',
             ['COCIRS_0xxx_v3', 'COCIRS_0xxx', 'COCIRS_0xxx_v2'],
             #  Sort by version number
             ['COCIRS_0xxx', 'COCIRS_0xxx_v3', 'COCIRS_0xxx_v2']),
        ]
    )
    def test_sort_basenames(self, input_path, basenames, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        assert target_pdsfile.sort_basenames(basenames=basenames) == expected

    @pytest.mark.parametrize(
        'input_path,logical_paths,expected',
        [
            ('previews/COUVIS_0xxx_v1/COUVIS_0009/DATA/D2004_274',
             [
                'previews/COUVIS_0xxx_v1/COUVIS_0009/DATA/D2004_274/EUV2004_274_09_50_small.png',
                'previews/COUVIS_0xxx_v1/COUVIS_0009/DATA/D2004_274/EUV2004_274_01_39_thumb.png',
                'previews/COUVIS_0xxx_v1/COUVIS_0009/DATA/D2004_274/EUV2004_274_07_10_full.png',
                'previews/COUVIS_0xxx_v1/COUVIS_0009/DATA/D2004_274/EUV2004_274_02_25_med.png',
             ],
             #  Sort by logical_path
             [
                'previews/COUVIS_0xxx_v1/COUVIS_0009/DATA/D2004_274/EUV2004_274_01_39_thumb.png',
                'previews/COUVIS_0xxx_v1/COUVIS_0009/DATA/D2004_274/EUV2004_274_02_25_med.png',
                'previews/COUVIS_0xxx_v1/COUVIS_0009/DATA/D2004_274/EUV2004_274_07_10_full.png',
                'previews/COUVIS_0xxx_v1/COUVIS_0009/DATA/D2004_274/EUV2004_274_09_50_small.png',
             ]),
        ]
    )
    def test_sort_logical_paths(self, input_path, logical_paths, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.sort_logical_paths(logical_paths=logical_paths)
        assert res == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('previews/COUVIS_0xxx/COUVIS_0009/DATA/D2004_274',
             [
                # Sorted order
                'EUV2004_274_01_39_thumb.png',
                'EUV2004_274_02_25_med.png',
                'EUV2004_274_07_10_full.png',
                'EUV2004_274_09_50_small.png',
             ]),
        ]
    )
    def test_sort_childnames(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.sort_childnames()
        li = []
        for child in res:
            if child in expected:
                li.append(child)
        assert li == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('previews/COUVIS_0xxx/COUVIS_0009/DATA/D2004_274',
             [
                # Sorted order
                'EUV2004_274_01_39_thumb.png',
                'EUV2004_274_02_25_med.png',
                'EUV2004_274_07_10_full.png',
                'EUV2004_274_09_50_small.png',
             ]),
        ]
    )
    def test_viewable_childnames(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.viewable_childnames()
        li = []
        for child in res:
            if child in expected:
                li.append(child)
        assert li == expected

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
            pdsfiles=pdsfiles, must_exist=True)

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

        res = pds3file.Pds3File.logicals_for_pdsfiles(pdsfiles=pdsfiles)

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

        res = pds3file.Pds3File.basenames_for_pdsfiles(pdsfiles=pdsfiles)

        for basename in res:
            assert basename in expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ([
                PDS3_HOLDINGS_DIR + '/volumes/COISS_1xxx/COISS_1001/data/1294561143_1295221348/W1294561202_1.LBL',
                PDS3_HOLDINGS_DIR + '/volumes/HSTNx_xxxx/HSTN0_7176/DATA/VISIT_01/N4BI01L4Q.LBL'
             ],
             [
                'volumes/COISS_1xxx/COISS_1001/data/1294561143_1295221348/W1294561202_1.LBL',
                'volumes/HSTNx_xxxx/HSTN0_7176/DATA/VISIT_01/N4BI01L4Q.LBL',
             ])
        ]
    )
    def test_logicals_for_abspaths(self, input_path, expected):
        res = pds3file.Pds3File.logicals_for_abspaths(abspaths=input_path,
                                                    must_exist=True)

        for path in res:
            assert path in expected

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
        res = pds3file.Pds3File.basenames_for_abspaths(abspaths=input_path)

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
        res = pds3file.Pds3File.pdsfiles_for_logicals(logical_paths=input_path)

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
             [
                PDS3_HOLDINGS_DIR + '/volumes/COISS_1xxx/COISS_1001/data/1294561143_1295221348/W1294561202_1.LBL',
                PDS3_HOLDINGS_DIR + '/volumes/HSTNx_xxxx/HSTN0_7176/DATA/VISIT_01/N4BI01L4Q.LBL',
             ])
        ]
    )
    def test_abspaths_for_logicals(self, input_path, expected):
        res = pds3file.Pds3File.abspaths_for_logicals(logical_paths=input_path,
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
    def test_basenames_for_logicals(self, input_path, expected):
        res = pds3file.Pds3File.basenames_for_logicals(logical_paths=input_path)

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
        res = target_pdsfile.abspaths_for_basenames(basenames=basenames)

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
        res = target_pdsfile.logicals_for_basenames(basenames=basenames)

        for path in res:
            assert path in expected

    ############################################################################
    # Test for associations
    ############################################################################
    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57.DAT',
             'volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57.DAT'),
            ('volumes', 'volumes')
        ]
    )
    def test_associated_parallel(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        print(target_pdsfile.category_.rstrip('/'))
        print(target_pdsfile.bundleset)
        target_associated_parallel = target_pdsfile.associated_parallel()
        print(target_associated_parallel.logical_path)
        assert target_associated_parallel.logical_path == expected

    @pytest.mark.parametrize(
        'input_path,expected_path',
        [
            ('volumes/COCIRS_0xxx/COCIRS_0012/DATA/NAV_DATA/GEO00120100.DAT',
             [PDS3_HOLDINGS_DIR + '/volumes/COCIRS_0xxx/COCIRS_0012/DATA/NAV_DATA/GEO00120100.DAT']),

        ]
    )
    def test_copy(self, input_path, expected_path):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        pdsf_copy = target_pdsfile.copy()
        assert pdsf_copy.abspath in expected_path

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('previews/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/HDAC1999_007_16_31_thumb.png',
             'previews-COUVIS_0xxx-COUVIS_0001-DATA-D1999_007-HDAC1999_007_16_31'),
            ('previews/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/',
             'previews-COUVIS_0xxx-COUVIS_0001-DATA-D1999_007')
        ]
    )
    def test_global_anchor(self, input_path, expected):
        target_pdsfile = instantiate_target_pdsfile(input_path)
        res = target_pdsfile.global_anchor
        assert res == expected

##########################################################################################
# Blackbox test for helper functions in pds3file.py
##########################################################################################
class TestPds3FileHelperBlackBox:
    @pytest.mark.parametrize(
        'input_path,expected',
        [
            ('volumes/COVIMS_8xxx/COVIMS_8001/data/VIMS_2017_251_GAMCRU_I_TAU_10KM.tab',
             True),
            (PDS3_HOLDINGS_DIR + '/metadata/COVIMS_0xxx/COVIMS_0001',
             False),
        ]
    )
    def test_is_logical_path(self, input_path, expected):
        res = pds3file.Pds3File.is_logical_path(path=input_path)
        assert res == expected

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            (PDS3_HOLDINGS_DIR + '/volumes/COUVIS_0xxx/COUVIS_0058/DATA/D2017_001/EUV2017_001_03_49.dat',
             'volumes/COUVIS_0xxx/COUVIS_0058/DATA/D2017_001/EUV2017_001_03_49.dat'),
            ('volumes/COUVIS_0xxx/COUVIS_0058/DATA/D2017_001/EUV2017_001_03_49.dat',
             'volumes/COUVIS_0xxx/COUVIS_0058/DATA/D2017_001/EUV2017_001_03_49.dat'),
        ]
    )
    def test_logical_path_from_abspath(self, input_path, expected):
        try:
            res = logical_path_from_abspath(input_path, pds3file.Pds3File)
            assert res == expected
        except ValueError as err:
            assert True # Not an absolute path

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            (PDS3_HOLDINGS_DIR + '/volumes/COUVIS_0xxx/COUVIS_0058/DATA/D2017_001/EUV2017_001_03_49.DAT',
             PDS3_HOLDINGS_DIR + '/volumes/COUVIS_0xxx/COUVIS_0058/DATA/D2017_001/EUV2017_001_03_49.DAT')
        ]
    )
    def test_repair_case(self, input_path, expected):
        res = repair_case(input_path, pds3file.Pds3File)
        assert res.lower() == expected.lower()

    @pytest.mark.parametrize(
        'input_path,expected',
        [
            (PDS3_HOLDINGS_DIR + '/volumes/COUVIS_0xxx/COUVIS_0058/DATA/D2017_001/EUV2017_001_03_49.dat',
             PDS3_HOLDINGS_DIR + '/volumes/COUVIS_0xxx/COUVIS_0058/DATA/D2017_001/EUV2017_001_03_49.dat'),
            ('volumes/COISS_0xxx/COISS_0001/data/wacfm/bit_wght/13302/133020.lbl',
             PDS3_HOLDINGS_DIR + '/volumes/COISS_0xxx/COISS_0001/data/wacfm/bit_wght/13302/133020.lbl'),
        ]
    )
    def test_selected_path_from_path(self, input_path, expected):
        res = selected_path_from_path(input_path, pds3file.Pds3File)
        assert res == expected
