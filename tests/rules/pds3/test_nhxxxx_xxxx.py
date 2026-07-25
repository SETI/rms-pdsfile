import pytest

import pdsfile.pds3file as pds3file

from tests.rules.support import (
    PDS3_TEST_RESULTS_DIR as TEST_RESULTS_DIR,
    associated_abspaths_test,
    opus_products_test,
)


@pytest.mark.parametrize(
# 1001 is the raw volume and 2001 is the calibrated volume.
    'input_path,expected',
    [
        ('volumes/NHxxLO_xxxx/NHLALO_1001/data/20060224_000310/lor_0003103486_0x630_eng.fit',
         'NHxxLO_xxxx/opus_products/lor_0003103486_0x630_eng.txt')
    ]
)
def test_opus_products(request, input_path, expected):
    update = request.config.option.update
    opus_products_test(pds3file.Pds3File, input_path, TEST_RESULTS_DIR+expected, update)

@pytest.mark.parametrize(
    'input_path,category,expected',
    [
        ('volumes/NHxxLO_xxxx/NHLALO_1001/data/20060224_000310/lor_0003103486_0x630_eng.fit',
         'volumes',
         'NHxxLO_xxxx/associated_abspaths/volumes_lor_0003103486_0x630_eng.txt')
    ]
)
def test_associated_abspaths(request, input_path, category, expected):
    update = request.config.option.update
    associated_abspaths_test(pds3file.Pds3File, input_path, category,
                             TEST_RESULTS_DIR+expected, update)

def test_opus_id_to_primary_logical_path():
    TESTS = [
        ('volumes/NHxxLO_xxxx/NHLALO_1001/data/20060224_000310/lor_0003103486_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHLALO_1001/data/20060423_000810/lor_0008107080_0x633_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHLALO_1001/data/20060730_001657/lor_0016577910_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHLALO_1001/data/20060910_002017/lor_0020170799_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHLALO_1001/data/20061018_002350/lor_0023502654_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHJULO_1001/data/20070108_003059/lor_0030598439_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHJULO_1001/data/20070228_003498/lor_0034981642_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHJULO_1001/data/20070301_003501/lor_0035015234_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHJULO_1001/data/20070307_003558/lor_0035585520_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHJULO_1001/data/20070526_004251/lor_0042517021_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHJULO_1001/data/20070611_004389/lor_0043897321_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHPCLO_1001/data/20070929_005334/lor_0053344800_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHPCLO_1001/data/20081013_008624/lor_0086245758_0x632_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHPCLO_1001/data/20090721_011048/lor_0110487779_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHPCLO_1001/data/20100625_013981/lor_0139810087_0x632_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHPCLO_1001/data/20110523_016842/lor_0168423779_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHPCLO_1001/data/20120523_020011/lor_0200112778_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHPCLO_1001/data/20130622_023420/lor_0234206579_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHPCLO_1001/data/20130712_023593/lor_0235939200_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHPCLO_1001/data/20140705_026686/lor_0266867668_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHPCLO_1001/data/20140726_026868/lor_0268688039_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHPELO_1001/data/20150125_028445/lor_0284457178_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHPELO_1001/data/20150131_028503/lor_0285035518_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHPELO_1001/data/20150223_028702/lor_0287027527_0x633_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHPELO_1001/data/20150405_029052/lor_0290526007_0x633_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHPELO_1001/data/20150723_029999/lor_0299994502_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHPELO_1001/data/20150724_030002/lor_0300027012_0x636_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHPELO_1001/data/20160407_032236/lor_0322361528_0x633_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHPELO_1001/data/20160711_033056/lor_0330563039_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHPELO_1001/data/20160716_033096/lor_0330965068_0x633_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHKCLO_1001/data/20170128_034788/lor_0347882528_0x633_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHKCLO_1001/data/20170129_034797/lor_0347976302_0x633_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHKCLO_1001/data/20170130_034804/lor_0348045126_0x633_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHKCLO_1001/data/20170918_036804/lor_0368041919_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHKCLO_1001/data/20170923_036850/lor_0368506958_0x633_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHKCLO_1001/data/20171030_037170/lor_0371709419_0x630_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHKCLO_1001/data/20171206_037489/lor_0374894598_0x633_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHKELO_1001/data/20180816_039668/lor_0396683548_0x633_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHKELO_1001/data/20180819_039700/lor_0397002308_0x633_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHKELO_1001/data/20180824_039744/lor_0397444588_0x633_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHKELO_1001/data/20180909_039877/lor_0398776019_0x636_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHKELO_1001/data/20180921_039983/lor_0399830818_0x633_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHKELO_1001/data/20180924_040007/lor_0400078348_0x633_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHKELO_1001/data/20190713_042535/lor_0425351280_0x633_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHKELO_1001/data/20191207_043800/lor_0438001863_0x633_eng.fit', ''),
        ('volumes/NHxxLO_xxxx/NHKELO_1001/data/20200423_044993/lor_0449933837_0x633_eng.fit', ''),

        ('volumes/NHxxMV_xxxx/NHLAMV_1001/data/20060321_000525/mpf_0005259637_0x539_eng_1.fit', ''),
        ('volumes/NHxxMV_xxxx/NHLAMV_1001/data/20060528_001112/mpf_0011128079_0x539_eng_1.fit', ''),
        ('volumes/NHxxMV_xxxx/NHLAMV_1001/data/20060922_002127/mp1_0021270021_0x530_eng_1.fit', ''),
        ('volumes/NHxxMV_xxxx/NHJUMV_1001/data/20070131_003252/mc0_0032528036_0x536_eng_1.fit', ''),
        ('volumes/NHxxMV_xxxx/NHJUMV_1001/data/20070225_003470/mc0_0034706398_0x536_eng_1.fit', ''),
        ('volumes/NHxxMV_xxxx/NHJUMV_1001/data/20070228_003497/mc3_0034973818_0x536_eng_1.fit', ''),
        ('volumes/NHxxMV_xxxx/NHJUMV_1001/data/20070303_003520/mc3_0035207878_0x536_eng_1.fit', ''),
        ('volumes/NHxxMV_xxxx/NHJUMV_1001/data/20070311_003590/mc0_0035903518_0x536_eng_1.fit', ''),
        ('volumes/NHxxMV_xxxx/NHJUMV_1001/data/20070526_004251/mc0_0042515578_0x536_eng_1.fit', ''),
        ('volumes/NHxxMV_xxxx/NHJUMV_1001/data/20070611_004389/mpf_0043897317_0x539_eng_1.fit', ''),
        ('volumes/NHxxMV_xxxx/NHPCMV_1001/data/20070918_005245/mc0_0052459368_0x536_eng.fit', ''),
        ('volumes/NHxxMV_xxxx/NHPCMV_1001/data/20090727_011102/mc0_0111027468_0x536_eng.fit', ''),
        ('volumes/NHxxMV_xxxx/NHPCMV_1001/data/20100625_013981/mp2_0139810012_0x530_eng.fit', ''),
        ('volumes/NHxxMV_xxxx/NHPCMV_1001/data/20120518_019968/mpf_0199685294_0x539_eng.fit', ''),
        ('volumes/NHxxMV_xxxx/NHPCMV_1001/data/20120601_020089/mpf_0200892714_0x539_eng.fit', ''),
        ('volumes/NHxxMV_xxxx/NHPCMV_1001/data/20130622_023420/mc0_0234201648_0x536_eng.fit', ''),
        ('volumes/NHxxMV_xxxx/NHPCMV_1001/data/20140723_026844/mpf_0268442094_0x539_eng.fit', ''),
        ('volumes/NHxxMV_xxxx/NHPEMV_1001/data/20150303_028769/mc0_0287692247_0x536_eng.fit', ''),
        ('volumes/NHxxMV_xxxx/NHPEMV_1001/data/20150409_029086/mc3_0290860851_0x536_eng.fit', ''),
        ('volumes/NHxxMV_xxxx/NHPEMV_1001/data/20150721_029979/mpf_0299796966_0x548_eng.fit', ''),
        ('volumes/NHxxMV_xxxx/NHPEMV_1001/data/20160630_032955/mc0_0329556649_0x536_eng.fit', ''),
        ('volumes/NHxxMV_xxxx/NHPEMV_1001/data/20160716_033093/mp2_0330935151_0x530_eng.fit', ''),
        ('volumes/NHxxMV_xxxx/NHKCMV_1001/data/20170921_036832/mc0_0368328709_0x536_eng.fit', ''),
        ('volumes/NHxxMV_xxxx/NHKCMV_1001/data/20180713_039381/mpf_0393815218_0x539_eng.fit', ''),
        ('volumes/NHxxMV_xxxx/NHKEMV_1001/data/20180831_039797/mc0_0397979512_0x536_eng.fit', ''),
        ('volumes/NHxxMV_xxxx/NHKEMV_1001/data/20181230_040849/mc0_0408494512_0x536_eng.fit', ''),
        ('volumes/NHxxMV_xxxx/NHKEMV_1001/data/20190316_041502/mpf_0415029106_0x539_eng.fit', ''),
        ('volumes/NHxxMV_xxxx/NHKEMV_1001/data/20190812_042795/mc0_0427957249_0x536_eng.fit', ''),
        ('volumes/NHxxMV_xxxx/NHKEMV_1001/data/20190902_042977/mc3_0429771832_0x536_eng.fit', ''),

        ('volumes/NHxxLO_xxxx/NHJULO_1001/data/20070611_004390/lor_0043906321_0x630_eng.fit',   '0x636'),
        ('volumes/NHxxLO_xxxx/NHPELO_1001/data/20150713_029913/lor_0299135304_0x630_eng.fit',   '0x632'),
        ('volumes/NHxxMV_xxxx/NHJUMV_1001/data/20070611_004390/mpf_0043906317_0x539_eng_1.fit', '0x548'),
        ('volumes/NHxxMV_xxxx/NHPCMV_1001/data/20130712_023593/mpf_0235933761_0x548_eng.fit',   '0x54a'),
    ]

    for (logical_path, alt_hex_code) in TESTS:
        test_pdsf = pds3file.Pds3File.from_logical_path(logical_path)
        opus_id = test_pdsf.opus_id
        opus_id_pdsf = pds3file.Pds3File.from_opus_id(opus_id)
        assert opus_id_pdsf.logical_path == logical_path

        # Gather all the associated OPUS products
        product_dict = test_pdsf.opus_products()
        product_pdsfiles = []
        for pdsf_lists in product_dict.values():
            for pdsf_list in pdsf_lists:
                product_pdsfiles += pdsf_list

        # Filter out the metadata/documents products and format files
        product_pdsfiles = [pdsf for pdsf in product_pdsfiles
                                 if pdsf.voltype_ != 'metadata/'
                                 and pdsf.voltype_ != 'documents/']
        product_pdsfiles = [pdsf for pdsf in product_pdsfiles
                                 if pdsf.extension.lower() != '.fmt']

        # Gather the set of absolute paths
        opus_id_abspaths = set()
        for pdsf in product_pdsfiles:
            opus_id_abspaths.add(pdsf.abspath)

        for pdsf in product_pdsfiles:
            # Every version of a data file is in the product set
            if pdsf.voltype_ == 'volumes/':
                for version_pdsf in pdsf.all_versions().values():
                    assert version_pdsf.abspath in opus_id_abspaths

            # Every viewset is in the product set
            for viewset in pdsf.all_viewsets.values():
                for viewable in viewset.viewables:
                    assert viewable.abspath in opus_id_abspaths

            # Every associated product is in the product set except metadata
            for category in ('volumes', 'calibrated', 'previews'):
                for abspath in pdsf.associated_abspaths(category):
                    assert abspath in opus_id_abspaths

        # Alternate hex code is in the product set
        if alt_hex_code:
            hex_code = '0x' + test_pdsf.abspath.split('0x')[1][:3]
            alt_abspath = test_pdsf.abspath.replace(hex_code, alt_hex_code)
            alt_pdsf = pds3file.Pds3File.from_abspath(alt_abspath)
            for version_pdsf in alt_pdsf.all_versions().values():
                assert version_pdsf.abspath in opus_id_abspaths

##########################################################################################
