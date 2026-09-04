import pytest

import pdsfile.pds3file as pds3file
from tests.rules.support import (
    PDS3_TEST_RESULTS_DIR as TEST_RESULTS_DIR,
)
from tests.rules.support import (
    associated_abspaths_test,
    opus_products_test,
)


@pytest.mark.parametrize(
    ('input_path', 'expected'),
    [
        ('volumes/GO_0xxx/GO_0017/J0/OPNAV/C0346405900R.IMG',
         'GO_0xxx/opus_products/C0346405900R.txt')
    ]
)
def test_opus_products(request, input_path, expected):
    update = request.config.option.update
    opus_products_test(pds3file.Pds3File, input_path, TEST_RESULTS_DIR+expected, update)


@pytest.mark.parametrize(
    ('input_path', 'category', 'expected'),
    [
        ('volumes/GO_0xxx/GO_0017/J0/OPNAV/C0346405900R.IMG',
         'volumes',
         'GO_0xxx/associated_abspaths/C0346405900R.txt')
    ]
)
def test_associated_abspaths(request, input_path, category, expected):
    update = request.config.option.update
    associated_abspaths_test(pds3file.Pds3File, input_path, category,
                             TEST_RESULTS_DIR+expected, update)

def test_opus_id_to_primary_logical_path():
    test_cases = [
        'volumes/GO_0xxx/GO_0002/RAW_CAL/C0003061100R.LBL',
        'volumes/GO_0xxx/GO_0002/RAW_CAL/C0011890900R.LBL',
        'volumes/GO_0xxx/GO_0002/RAW_CAL/C0011895526R.LBL',
        'volumes/GO_0xxx/GO_0002/RAW_CAL/C0059335800R.LBL',
        'volumes/GO_0xxx/GO_0002/RAW_CAL/C0059469900R.LBL',
        'volumes/GO_0xxx/GO_0002/VENUS/C0018062600R.LBL',
        'volumes/GO_0xxx/GO_0002/VENUS/C0018077000R.LBL',
        'volumes/GO_0xxx/GO_0002/VENUS/C0018088800R.LBL',
        'volumes/GO_0xxx/GO_0002/VENUS/C0018217000R.LBL',
        'volumes/GO_0xxx/GO_0002/VENUS/C0018244700R.LBL',
        'volumes/GO_0xxx/GO_0002/VENUS/C0019064100R.LBL',
        'volumes/GO_0xxx/GO_0003/EARTH/C0061026045R.LBL',
        'volumes/GO_0xxx/GO_0003/EARTH/C0061026245R.LBL',
        'volumes/GO_0xxx/GO_0003/EARTH/C0061039400R.LBL',
        'volumes/GO_0xxx/GO_0003/EARTH/C0061042645R.LBL',
        'volumes/GO_0xxx/GO_0003/EARTH/C0061042700R.LBL',
        'volumes/GO_0xxx/GO_0003/MOON/C0060959300R.LBL',
        'volumes/GO_0xxx/GO_0003/MOON/C0060997000R.LBL',
        'volumes/GO_0xxx/GO_0003/MOON/C0061000300R.LBL',
        'volumes/GO_0xxx/GO_0003/MOON/C0061030945R.LBL',
        'volumes/GO_0xxx/GO_0003/MOON/C0061043300R.LBL',
        'volumes/GO_0xxx/GO_0003/RAW_CAL/C0059905000R.LBL',
        'volumes/GO_0xxx/GO_0003/RAW_CAL/C0060959145R.LBL',
        'volumes/GO_0xxx/GO_0003/RAW_CAL/C0061026100R.LBL',
        'volumes/GO_0xxx/GO_0003/RAW_CAL/C0061039445R.LBL',
        'volumes/GO_0xxx/GO_0003/RAW_CAL/C0061042600R.LBL',
        'volumes/GO_0xxx/GO_0003/RAW_CAL/C0061042800R.LBL',
        'volumes/GO_0xxx/GO_0004/MOON/C0061399900R.LBL',
        'volumes/GO_0xxx/GO_0004/MOON/C0061400000R.LBL',
        'volumes/GO_0xxx/GO_0005/EARTH/C0061469200R.LBL',
        'volumes/GO_0xxx/GO_0005/EARTH/C0061499900R.LBL',
        'volumes/GO_0xxx/GO_0005/EARTH/C0061500000R.LBL',
        'volumes/GO_0xxx/GO_0006/EARTH/C0061614600R.LBL',
        'volumes/GO_0xxx/GO_0006/MOON/C0061560900R.LBL',
        'volumes/GO_0xxx/GO_0006/MOON/C0061999900R.LBL',
        'volumes/GO_0xxx/GO_0006/MOON/C0062000000R.LBL',
        'volumes/GO_0xxx/GO_0006/RAW_CAL/C0062303500R.LBL',
        'volumes/GO_0xxx/GO_0006/REDO/C0018062639R.LBL',
        'volumes/GO_0xxx/GO_0006/REDO/C0018241745R.LBL',
        'volumes/GO_0xxx/GO_0006/REDO/C0018353518R.LBL',
        'volumes/GO_0xxx/GO_0006/REDO/C0018518445R.LBL',
        'volumes/GO_0xxx/GO_0006/REDO/C0059469700R.LBL',
        'volumes/GO_0xxx/GO_0006/REDO/C0059471700R.LBL',
        'volumes/GO_0xxx/GO_0006/REDO/C0060964000R.LBL',
        'volumes/GO_0xxx/GO_0006/REDO/C0061078900R.LBL',
        'volumes/GO_0xxx/GO_0006/REDO/C0061116600R.LBL',
        'volumes/GO_0xxx/GO_0006/REDO/C0061424500R.LBL',
        'volumes/GO_0xxx/GO_0006/REDO/C0061469100R.LBL',
        'volumes/GO_0xxx/GO_0006/REDO/C0061508200R.LBL',
        'volumes/GO_0xxx/GO_0006/REDO/C0061542500R.LBL',
        'volumes/GO_0xxx/GO_0007/GASPRA/C0107271600R.LBL',
        'volumes/GO_0xxx/GO_0007/GASPRA/C0107318513R.LBL',
        'volumes/GO_0xxx/GO_0007/RAW_CAL/C0099757945R.LBL',
        'volumes/GO_0xxx/GO_0007/RAW_CAL/C0102786545R.LBL',
        'volumes/GO_0xxx/GO_0007/RAW_CAL/C0163288400R.LBL',
        'volumes/GO_0xxx/GO_0007/RAW_CAL/C0163308225R.LBL',
        'volumes/GO_0xxx/GO_0007/RAW_CAL/C0164005700R.LBL',
        'volumes/GO_0xxx/GO_0007/REDO/C0059466445R.LBL',
        'volumes/GO_0xxx/GO_0008/RAW_CAL/C0164532045R.LBL',
        'volumes/GO_0xxx/GO_0009/MOON/C0164997400R.LBL',
        'volumes/GO_0xxx/GO_0009/MOON/C0164999945R.LBL',
        'volumes/GO_0xxx/GO_0009/MOON/C0165000000R.LBL',
        'volumes/GO_0xxx/GO_0010/EARTH/C0165100313R.LBL',
        'volumes/GO_0xxx/GO_0010/EARTH/C0165140700R.LBL',
        'volumes/GO_0xxx/GO_0010/RAW_CAL/C0165099345R.LBL',
        'volumes/GO_0xxx/GO_0011/EARTH/C0165199945R.LBL',
        'volumes/GO_0xxx/GO_0011/EARTH/C0165200000R.LBL',
        'volumes/GO_0xxx/GO_0011/RAW_CAL/C0165162500R.LBL',
        'volumes/GO_0xxx/GO_0012/EARTH/C0165210945R.LBL',
        'volumes/GO_0xxx/GO_0012/EARTH/C0165211000R.LBL',
        'volumes/GO_0xxx/GO_0012/EARTH/C0165239945R.LBL',
        'volumes/GO_0xxx/GO_0012/EARTH/C0165240000R.LBL',
        'volumes/GO_0xxx/GO_0012/GOPEX/C0165233545R.LBL',
        'volumes/GO_0xxx/GO_0013/EARTH/C0165249945R.LBL',
        'volumes/GO_0xxx/GO_0013/EARTH/C0165250000R.LBL',
        'volumes/GO_0xxx/GO_0013/EARTH/C0165299900R.LBL',
        'volumes/GO_0xxx/GO_0013/EARTH/C0165300000R.LBL',
        'volumes/GO_0xxx/GO_0013/EARTH/C0165319900R.LBL',
        'volumes/GO_0xxx/GO_0013/EARTH/C0165320000R.LBL',
        'volumes/GO_0xxx/GO_0013/RAW_CAL/C0165257300R.LBL',
        'volumes/GO_0xxx/GO_0014/EARTH/C0165329900R.LBL',
        'volumes/GO_0xxx/GO_0014/EARTH/C0165330000R.LBL',
        'volumes/GO_0xxx/GO_0014/EARTH/C0165399900R.LBL',
        'volumes/GO_0xxx/GO_0014/EARTH/C0165400000R.LBL',
        'volumes/GO_0xxx/GO_0015/EARTH/C0165470845R.LBL',
        'volumes/GO_0xxx/GO_0015/EMCONJ/C0166236100R.LBL',
        'volumes/GO_0xxx/GO_0015/EMCONJ/C0166318700R.LBL',
        'volumes/GO_0xxx/GO_0015/GOPEX/C0165500300R.LBL',
        'volumes/GO_0xxx/GO_0015/GOPEX/C0165638300R.LBL',
        'volumes/GO_0xxx/GO_0015/GOPEX/C0165930300R.LBL',
        'volumes/GO_0xxx/GO_0015/GOPEX/C0166067000R.LBL',
        'volumes/GO_0xxx/GO_0015/GOPEX/C0166212900R.LBL',
        'volumes/GO_0xxx/GO_0015/RAW_CAL/C0165591200R.LBL',
        'volumes/GO_0xxx/GO_0015/RAW_CAL/C0166324700R.LBL',
        'volumes/GO_0xxx/GO_0015/REDO/C0165242700R.LBL',
        'volumes/GO_0xxx/GO_0016/IDA/C0202530700R.LBL',
        'volumes/GO_0xxx/GO_0016/IDA/C0202562800R.LBL',
        'volumes/GO_0xxx/GO_0016/RAW_CAL/C0197327200R.LBL',
        'volumes/GO_0xxx/GO_0016/RAW_CAL/C0201018800R.LBL',
        'volumes/GO_0xxx/GO_0016/SL9/C0248806645R.LBL',
        'volumes/GO_0xxx/GO_0016/SL9/C0248950600R.LBL',
        'volumes/GO_0xxx/GO_0016/SL9/C0249221800R.LBL',
        'volumes/GO_0xxx/GO_0017/C3/CALLISTO/C0368211900R.LBL',
        'volumes/GO_0xxx/GO_0017/C3/EUROPA/C0368639400R.LBL',
        'volumes/GO_0xxx/GO_0017/C3/IO/C0368558239R.LBL',
        'volumes/GO_0xxx/GO_0017/C3/JUPITER/C0368369200R.LBL',
        'volumes/GO_0xxx/GO_0017/C3/OPNAV/C0372343200R.LBL',
        'volumes/GO_0xxx/GO_0017/C3/RINGS/C0368974113R.LBL',
        'volumes/GO_0xxx/GO_0017/C3/SML_SATS/C0368495800R.LBL',
        'volumes/GO_0xxx/GO_0017/G1/EUROPA/C0349875100R.LBL',
        'volumes/GO_0xxx/GO_0017/G1/GANYMEDE/C0349632000R.LBL',
        'volumes/GO_0xxx/GO_0017/G1/IO/C0349542152R.LBL',
        'volumes/GO_0xxx/GO_0017/G1/IO/C0350013800R.LBL',
        'volumes/GO_0xxx/GO_0017/G1/JUPITER/C0349605600R.LBL',
        'volumes/GO_0xxx/GO_0017/G1/OPNAV/C0356000600R.LBL',
        'volumes/GO_0xxx/GO_0017/G2/CALLISTO/C0360198468R.LBL',
        'volumes/GO_0xxx/GO_0017/G2/EUROPA/C0360063900R.LBL',
        'volumes/GO_0xxx/GO_0017/G2/GANYMEDE/C0359942400R.LBL',
        'volumes/GO_0xxx/GO_0017/G2/IO/C0359402500R.LBL',
        'volumes/GO_0xxx/GO_0017/G2/JUPITER/C0359509200R.LBL',
        'volumes/GO_0xxx/GO_0017/G2/OPNAV/C0359251000R.LBL',
        'volumes/GO_0xxx/GO_0017/G2/OPNAV/C0364621700R.LBL',
        'volumes/GO_0xxx/GO_0017/G2/RAW_CAL/C0360361122R.LBL',
        'volumes/GO_0xxx/GO_0017/G2/SML_SATS/C0360025813R.LBL',
        'volumes/GO_0xxx/GO_0017/J0/OPNAV/C0346405900R.LBL',
        'volumes/GO_0xxx/GO_0018/E4/EUROPA/C0374649000R.LBL',
        'volumes/GO_0xxx/GO_0018/E4/IO/C0374478045R.LBL',
        'volumes/GO_0xxx/GO_0018/E4/JUPITER/C0374456522R.LBL',
        'volumes/GO_0xxx/GO_0018/E4/OPNAV/C0382058200R.LBL',
        'volumes/GO_0xxx/GO_0018/E4/SML_SATS/C0374546000R.LBL',
        'volumes/GO_0xxx/GO_0018/E6/CALLISTO/C0383944100R.LBL',
        'volumes/GO_0xxx/GO_0018/E6/EUROPA/C0383694600R.LBL',
        'volumes/GO_0xxx/GO_0018/E6/GANYMEDE/C0383768868R.LBL',
        'volumes/GO_0xxx/GO_0018/E6/IO/C0383490245R.LBL',
        'volumes/GO_0xxx/GO_0018/E6/JUPITER/C0383548622R.LBL',
        'volumes/GO_0xxx/GO_0018/E6/OPNAV/C0388834700R.LBL',
        'volumes/GO_0xxx/GO_0018/E6/SML_SATS/C0383612800R.LBL',
        'volumes/GO_0xxx/GO_0018/G7/CALLISTO/C0389556200R.LBL',
        'volumes/GO_0xxx/GO_0018/G7/EUROPA/C0389522100R.LBL',
        'volumes/GO_0xxx/GO_0018/G7/GANYMEDE/C0389917900R.LBL',
        'volumes/GO_0xxx/GO_0018/G7/IO/C0389608268R.LBL',
        'volumes/GO_0xxx/GO_0018/G7/JUPITER/C0389557000R.LBL',
        'volumes/GO_0xxx/GO_0018/G7/OPNAV/C0389266100R.LBL',
        'volumes/GO_0xxx/GO_0018/G7/SML_SATS/C0389705600R.LBL',
        'volumes/GO_0xxx/GO_0018/REDO/C3/JUPITER/C0368977800R.LBL',
        'volumes/GO_0xxx/GO_0019/C10/CALLISTO/C0413382800R.LBL',
        'volumes/GO_0xxx/GO_0019/C9/CALLISTO/C0401505300R.LBL',
        'volumes/GO_0xxx/GO_0019/C9/EUROPA/C0401727700R.LBL',
        'volumes/GO_0xxx/GO_0019/C9/GANYMEDE/C0401668900R.LBL',
        'volumes/GO_0xxx/GO_0019/C9/IO/C0401704700R.LBL',
        'volumes/GO_0xxx/GO_0019/C9/JUPITER/C0401571845R.LBL',
        'volumes/GO_0xxx/GO_0019/C9/RAW_CAL/C0404187800R.LBL',
        'volumes/GO_0xxx/GO_0019/C9/SML_SATS/C0401604400R.LBL',
        'volumes/GO_0xxx/GO_0019/G8/CALLISTO/C0394364268R.LBL',
        'volumes/GO_0xxx/GO_0019/G8/GANYMEDE/C0394517800R.LBL',
        'volumes/GO_0xxx/GO_0019/G8/IO/C0394394100R.LBL',
        'volumes/GO_0xxx/GO_0019/G8/JUPITER/C0394455245R.LBL',
        'volumes/GO_0xxx/GO_0019/G8/SML_SATS/C0394449168R.LBL',
        'volumes/GO_0xxx/GO_0019/REDO/C3/EUROPA/C0368976678R.LBL',
        'volumes/GO_0xxx/GO_0019/REDO/C3/JUPITER/C0368369268R.LBL',
        'volumes/GO_0xxx/GO_0019/REDO/E4/EUROPA/C0374667300R.LBL',
        'volumes/GO_0xxx/GO_0019/REDO/E6/IO/C0383655111R.LBL',
        'volumes/GO_0xxx/GO_0020/E11/CALLISTO/C0420426068R.LBL',
        'volumes/GO_0xxx/GO_0020/E11/EUROPA/C0420617200R.LBL',
        'volumes/GO_0xxx/GO_0020/E11/IO/C0420361523R.LBL',
        'volumes/GO_0xxx/GO_0020/E11/JUPITER/C0420458568R.LBL',
        'volumes/GO_0xxx/GO_0020/E11/RINGS/C0420809545R.LBL',
        'volumes/GO_0xxx/GO_0020/E11/SML_SATS/C0420644201R.LBL',
        'volumes/GO_0xxx/GO_0020/E12/EUROPA/C0426234600R.LBL',
        'volumes/GO_0xxx/GO_0020/E12/GANYMEDE/C0426117300R.LBL',
        'volumes/GO_0xxx/GO_0020/E12/IO/C0426152100R.LBL',
        'volumes/GO_0xxx/GO_0020/E12/TIRETRACK/C0426272849S.LBL',
        'volumes/GO_0xxx/GO_0020/E14/EUROPA/C0440948000R.LBL',
        'volumes/GO_0xxx/GO_0020/E14/GANYMEDE/C0441013078R.LBL',
        'volumes/GO_0xxx/GO_0020/E14/IO/C0440873539R.LBL',
        'volumes/GO_0xxx/GO_0020/E15/EUROPA/C0449961800R.LBL',
        'volumes/GO_0xxx/GO_0020/E15/IO/C0449841900R.LBL',
        'volumes/GO_0xxx/GO_0020/E15/IO/C0450095900R.LBL',
        'volumes/GO_0xxx/GO_0020/E17/EUROPA/C0466581865R.LBL',
        'volumes/GO_0xxx/GO_0020/E17/JUPITER/C0466580845R.LBL',
        'volumes/GO_0xxx/GO_0020/E17/RINGS/C0466612545R.LBL',
        'volumes/GO_0xxx/GO_0021/C20/CALLISTO/C0498206600R.LBL',
        'volumes/GO_0xxx/GO_0021/C21/CALLISTO/C0506142900R.LBL',
        'volumes/GO_0xxx/GO_0021/C22/IO/C0512323300R.LBL',
        'volumes/GO_0xxx/GO_0021/E18/RAW_CAL/C0477421600R.LBL',
        'volumes/GO_0xxx/GO_0021/E19/EUROPA/C0484864900R.LBL',
        'volumes/GO_0xxx/GO_0022/I24/IO/C0520792800R.LBL',
        'volumes/GO_0xxx/GO_0022/I24/IO/GARBLED/C0520792749R.LBL',
        'volumes/GO_0xxx/GO_0022/I24/IO/REPAIRED/C0520792767S.LBL',
        'volumes/GO_0xxx/GO_0022/I24/IO/REPAIRED/C0520806300S.LBL',
        'volumes/GO_0xxx/GO_0022/I25/EUROPA/C0527272700R.LBL',
        'volumes/GO_0xxx/GO_0022/I25/IO/C0527345000R.LBL',
        'volumes/GO_0xxx/GO_0022/I25/SML_SATS/C0527365601R.LBL',
        'volumes/GO_0xxx/GO_0023/C30/CALLISTO/C0605145126R.LBL',
        'volumes/GO_0xxx/GO_0023/E26/EUROPA/C0532836239R.LBL',
        'volumes/GO_0xxx/GO_0023/E26/IO/C0532939900R.LBL',
        'volumes/GO_0xxx/GO_0023/E26/SML_SATS/C0532888100R.LBL',
        'volumes/GO_0xxx/GO_0023/G28/EUROPA/C0552809300R.LBL',
        'volumes/GO_0xxx/GO_0023/G28/GANYMEDE/C0552443500R.LBL',
        'volumes/GO_0xxx/GO_0023/G28/GARBLED/C0552447568R.LBL',
        'volumes/GO_0xxx/GO_0023/G28/JUPITER/C0552766100R.LBL',
        'volumes/GO_0xxx/GO_0023/G28/OPNAV/C0566856700R.LBL',
        'volumes/GO_0xxx/GO_0023/G28/REPAIRED/C0552447569S.LBL',
        'volumes/GO_0xxx/GO_0023/G28/RINGS/C0552599400R.LBL',
        'volumes/GO_0xxx/GO_0023/G29/GANYMEDE/C0584054600R.LBL',
        'volumes/GO_0xxx/GO_0023/G29/IO/C0584260700R.LBL',
        'volumes/GO_0xxx/GO_0023/G29/JUPITER/C0584478200R.LBL',
        'volumes/GO_0xxx/GO_0023/G29/RAW_CAL/C0600486513R.LBL',
        'volumes/GO_0xxx/GO_0023/G29/REPAIRED/C0600491113S.LBL',
        'volumes/GO_0xxx/GO_0023/G29/RINGS/C0584346700R.LBL',
        'volumes/GO_0xxx/GO_0023/I27/IO/C0539931265R.LBL',
        'volumes/GO_0xxx/GO_0023/I27/IO/C0540090500R.LBL',
        'volumes/GO_0xxx/GO_0023/I31/CALLISTO/C0615354300R.LBL',
        'volumes/GO_0xxx/GO_0023/I31/IO/C0615325145R.LBL',
        'volumes/GO_0xxx/GO_0023/I31/JUPITER/C0615698700R.LBL',
        'volumes/GO_0xxx/GO_0023/I31/OPNAV/C0624540800R.LBL',
        'volumes/GO_0xxx/GO_0023/I32/IO/C0625566400R.LBL',
        'volumes/GO_0xxx/GO_0023/I32/JUPITER/C0625967145R.LBL',
        'volumes/GO_0xxx/GO_0023/I32/OPNAV/C0625709200R.LBL',
        'volumes/GO_0xxx/GO_0023/I32/RINGS/C0626030645R.LBL',
        'volumes/GO_0xxx/GO_0023/I32/SML_SATS/C0625614500R.LBL',
        'volumes/GO_0xxx/GO_0023/I33/EUROPA/C0639063400R.LBL',
        'volumes/GO_0xxx/GO_0023/I33/JUPITER/C0639371300R.LBL',
        'volumes/GO_0xxx/GO_0023/I33/OPNAV/C0639004613R.LBL',
        'volumes/GO_0xxx/GO_0023/I33/RAW_CAL/C0647529700R.LBL',
        'volumes/GO_0xxx/GO_0023/REDO/E11/IO/C0420361500R.LBL',
    ]

    for logical_path in test_cases:
        test_pdsf = pds3file.Pds3File.from_logical_path(logical_path)
        opus_id = test_pdsf.opus_id
        opus_id_pdsf = pds3file.Pds3File.from_opus_id(opus_id)
        assert opus_id_pdsf.logical_path == logical_path, (opus_id_pdsf.logical_path, logical_path)

        # Make sure _v1 exists
        versions = test_pdsf.all_versions()
        assert 10000 in versions
        v1_path = versions[10000].abspath
        v1_path = v1_path.replace('_v1/', '/')
        parts = v1_path.rpartition('/')
        v1_path = parts[0] + parts[2]
        assert v1_path == test_pdsf.abspath, (v1_path, test_pdsf.abspath)

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
            # Every viewset is in the product set
            for viewset in pdsf.all_viewsets.values():
                for viewable in viewset.viewables:
                    assert viewable.abspath in opus_id_abspaths, (viewable.abspath,
                                                                  opus_id_abspaths)

            # Every associated product is in the product set except metadata
            for category in ('volumes', 'previews'):
                for abspath in pdsf.associated_abspaths(category):
                    assert abspath in opus_id_abspaths, (abspath, opus_id_abspaths)

def test_duplicated_products():

    test_cases = [
        ('GO_0006/REDO/C0018062639R.LBL'           , 'GO_0002/VENUS/C0018062639R.LBL'         ),
        ('GO_0006/REDO/C0018518445R.LBL'           , 'GO_0002/VENUS/C0018518445R.LBL'         ),
        ('GO_0006/REDO/C0059469700R.LBL'           , 'GO_0002/RAW_CAL/C0059469700R.LBL'       ),
        ('GO_0006/REDO/C0060964000R.LBL'           , 'GO_0003/MOON/C0060964000R.LBL'          ),
        ('GO_0006/REDO/C0061078900R.LBL'           , 'GO_0004/EARTH/C0061078900R.LBL'         ),
        ('GO_0006/REDO/C0061116600R.LBL'           , 'GO_0004/MOON/C0061116600R.LBL'          ),
        ('GO_0006/REDO/C0061424500R.LBL'           , 'GO_0004/EARTH/C0061424500R.LBL'         ),
        ('GO_0006/REDO/C0061508200R.LBL'           , 'GO_0005/EARTH/C0061508200R.LBL'         ),
        ('GO_0006/REDO/C0061522100R.LBL'           , 'GO_0005/EARTH/C0061522100R.LBL'         ),
        ('GO_0006/REDO/C0061542500R.LBL'           , 'GO_0006/EARTH/C0061542500R.LBL'         ),
        ('GO_0015/REDO/C0165242700R.LBL'           , 'GO_0012/EARTH/C0165242700R.LBL'         ),
        ('GO_0018/REDO/C3/JUPITER/C0368976900R.LBL', 'GO_0017/C3/JUPITER/C0368976900R.LBL'    ),
        ('GO_0019/REDO/C3/JUPITER/C0368441600R.LBL', 'GO_0017/C3/JUPITER/C0368441600R.LBL'    ),
        ('GO_0019/REDO/C3/JUPITER/C0368441600R.LBL', 'GO_0017/C3/JUPITER/C0368441600R.LBL'    ),
        ('GO_0019/REDO/E6/IO/C0383655111R.LBL'     , 'GO_0018/E6/IO/C0383655111R.LBL'         ),
        ('GO_0019/REDO/E6/IO/C0383655111R.LBL'     , 'GO_0018/E6/IO/C0383655111R.LBL'         ),
        ('GO_0020/E12/TIRETRACK/C0426272849S.LBL'  , 'GO_0020/E12/EUROPA/C0426272849R.LBL'    ),
        ('GO_0022/I24/IO/REPAIRED/C0520792949S.LBL', 'GO_0022/I24/IO/GARBLED/C0520792949R.LBL'),
        ('GO_0023/G28/REPAIRED/C0552447569S.LBL'   , 'GO_0023/G28/GARBLED/C0552447569R.LBL'   ),
        ('GO_0023/G29/REPAIRED/C0600660969S.LBL'   , 'GO_0023/G29/GARBLED/C0600660969R.LBL'   ),
    ]

    for (file1, file2) in test_cases:
        pdsf1 = pds3file.Pds3File.from_logical_path('volumes/GO_0xxx/' + file1)
        pdsf2 = pds3file.Pds3File.from_logical_path('volumes/GO_0xxx/' + file2)
        assert pdsf1.opus_id == pdsf2.opus_id, (pdsf1.opus_id, pdsf2.opus_id)

        test_pdsf = pds3file.Pds3File.from_opus_id(pdsf1.opus_id)
        assert test_pdsf.abspath == pdsf1.abspath, (test_pdsf.abspath, pdsf1.abspath)

        products1 = pdsf1.opus_products()
        products2 = pdsf2.opus_products()

        for key in products1:
            assert key in products2, 'Missing key in products2: ' + str(key)
        for key in products2:
            assert key in products1, 'Missing key in products1: ' + str(key)
        for (key,value1) in products1.items():
            value2 = products2[key]
            assert str(value1) == str(value2), \
                    f'Mismatch {file1}, {file2} @ {key}: {value1} ||| {value2}'

##########################################################################################
