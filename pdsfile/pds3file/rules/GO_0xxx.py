##########################################################################################
# pds3file/rules/GO_0xxx.py
##########################################################################################

import pdsfile.pds3file as pds3file
import translator
import re

# This is a complete list of all images that appear under REDO/REPAIRED/TIRETRACK, along with the images they supersede:
# GO_0006/REDO/C0018062639R.IMG             GO_0002/VENUS/C0018062639R.IMG
# GO_0006/REDO/C0018241745R.IMG             GO_0002/VENUS/C0018241745R.IMG
# GO_0006/REDO/C0018353518R.IMG             GO_0002/VENUS/C0018353518R.IMG
# GO_0006/REDO/C0018518445R.IMG             GO_0002/VENUS/C0018518445R.IMG
# GO_0006/REDO/C0059469700R.IMG             GO_0002/RAW_CAL/C0059469700R.IMG
# GO_0006/REDO/C0059471700R.IMG             GO_0002/RAW_CAL/C0059471700R.IMG
# GO_0006/REDO/C0060964000R.IMG             GO_0003/MOON/C0060964000R.IMG
# GO_0006/REDO/C0061078900R.IMG             GO_0004/EARTH/C0061078900R.IMG
# GO_0006/REDO/C0061116300R.IMG             GO_0004/MOON/C0061116300R.IMG
# GO_0006/REDO/C0061116600R.IMG             GO_0004/MOON/C0061116600R.IMG
# GO_0006/REDO/C0061424500R.IMG             GO_0004/EARTH/C0061424500R.IMG
# GO_0006/REDO/C0061441500R.IMG             GO_0004/EARTH/C0061441500R.IMG
# GO_0006/REDO/C0061469100R.IMG             GO_0005/EARTH/C0061469100R.IMG
# GO_0006/REDO/C0061508200R.IMG             GO_0005/EARTH/C0061508200R.IMG
# GO_0006/REDO/C0061509700R.IMG             GO_0005/EARTH/C0061509700R.IMG
# GO_0006/REDO/C0061510400R.IMG             GO_0005/EARTH/C0061510400R.IMG
# GO_0006/REDO/C0061510800R.IMG             GO_0005/EARTH/C0061510800R.IMG
# GO_0006/REDO/C0061512600R.IMG             GO_0005/EARTH/C0061512600R.IMG
# GO_0006/REDO/C0061516300R.IMG             GO_0005/EARTH/C0061516300R.IMG
# GO_0006/REDO/C0061516400R.IMG             GO_0005/EARTH/C0061516400R.IMG
# GO_0006/REDO/C0061516700R.IMG             GO_0005/EARTH/C0061516700R.IMG
# GO_0006/REDO/C0061522100R.IMG             GO_0005/EARTH/C0061522100R.IMG
# GO_0006/REDO/C0061525200R.IMG             GO_0005/EARTH/C0061525200R.IMG
# GO_0006/REDO/C0061526200R.IMG             GO_0005/EARTH/C0061526200R.IMG
# GO_0006/REDO/C0061530600R.IMG             GO_0005/EARTH/C0061530600R.IMG
# GO_0006/REDO/C0061531400R.IMG             GO_0005/EARTH/C0061531400R.IMG
# GO_0006/REDO/C0061531700R.IMG             GO_0005/EARTH/C0061531700R.IMG
# GO_0006/REDO/C0061533800R.IMG             GO_0005/EARTH/C0061533800R.IMG
# GO_0006/REDO/C0061535500R.IMG             GO_0005/EARTH/C0061535500R.IMG
# GO_0006/REDO/C0061539600R.IMG             GO_0006/EARTH/C0061539600R.IMG
# GO_0006/REDO/C0061542500R.IMG             GO_0006/EARTH/C0061542500R.IMG
# GO_0007/REDO/C0059466445R.IMG             (no counterpart)
# GO_0015/REDO/C0165242700R.IMG             GO_0012/EARTH/C0165242700R.IMG
# GO_0018/REDO/C3/JUPITER/C0368976900R.IMG  GO_0017/C3/JUPITER/C0368976900R.IMG
# GO_0018/REDO/C3/JUPITER/C0368977500R.IMG  GO_0017/C3/JUPITER/C0368977500R.IMG
# GO_0018/REDO/C3/JUPITER/C0368977800R.IMG  GO_0017/C3/JUPITER/C0368977800R.IMG
# GO_0018/REDO/C3/JUPITER/C0368978100R.IMG  GO_0017/C3/JUPITER/C0368978100R.IMG
# GO_0018/REDO/C3/JUPITER/C0368978700R.IMG  GO_0017/C3/JUPITER/C0368978700R.IMG
# GO_0018/REDO/C3/JUPITER/C0368979000R.IMG  GO_0017/C3/JUPITER/C0368979000R.IMG
# GO_0018/REDO/C3/JUPITER/C0368979400R.IMG  GO_0017/C3/JUPITER/C0368979400R.IMG
# GO_0018/REDO/C3/JUPITER/C0368979900R.IMG  GO_0017/C3/JUPITER/C0368979900R.IMG
# GO_0018/REDO/C3/JUPITER/C0368980400R.IMG  GO_0017/C3/JUPITER/C0368980400R.IMG
# GO_0018/REDO/C3/JUPITER/C0368980900R.IMG  GO_0017/C3/JUPITER/C0368980900R.IMG
# GO_0018/REDO/C3/JUPITER/C0368990100R.IMG  GO_0017/C3/JUPITER/C0368990100R.IMG
# GO_0018/REDO/C3/JUPITER/C0368990300R.IMG  GO_0017/C3/JUPITER/C0368990300R.IMG
# GO_0019/REDO/C3/EUROPA/C0368976678R.IMG   GO_0017/C3/EUROPA/C0368976678R.IMG
# GO_0019/REDO/C3/EUROPA/C0368976713R.IMG   GO_0017/C3/EUROPA/C0368976713R.IMG
# GO_0019/REDO/C3/EUROPA/C0368976739R.IMG   GO_0017/C3/EUROPA/C0368976739R.IMG
# GO_0019/REDO/C3/EUROPA/C0368976765R.IMG   GO_0017/C3/EUROPA/C0368976765R.IMG
# GO_0019/REDO/C3/EUROPA/C0368976800R.IMG   GO_0017/C3/EUROPA/C0368976800R.IMG
# GO_0019/REDO/C3/EUROPA/C0368976826R.IMG   GO_0017/C3/EUROPA/C0368976826R.IMG
# GO_0019/REDO/C3/JUPITER/C0368369268R.IMG  GO_0017/C3/JUPITER/C0368369268R.IMG
# GO_0019/REDO/C3/JUPITER/C0368441600R.IMG  GO_0017/C3/JUPITER/C0368441600R.IMG
# GO_0019/REDO/E4/EUROPA/C0374667300R.IMG   GO_0018/E4/EUROPA/C0374667300R.IMG
# GO_0019/REDO/E6/IO/C0383655111R.IMG       GO_0018/E6/IO/C0383655111R.IMG
# GO_0020/E12/TIRETRACK/C0426272849S.IMG    GO_0020/E12/EUROPA/C0426272849R.IMG
# GO_0020/E12/TIRETRACK/C0426272853S.IMG    GO_0020/E12/EUROPA/C0426272853R.IMG
# GO_0020/E12/TIRETRACK/C0426272856S.IMG    GO_0020/E12/EUROPA/C0426272856R.IMG
# GO_0022/I24/IO/REPAIRED/C0520792767S.IMG  GO_0022/I24/IO/GARBLED/C0520792767R.IMG
# GO_0022/I24/IO/REPAIRED/C0520792770S.IMG  GO_0022/I24/IO/GARBLED/C0520792770R.IMG
# GO_0022/I24/IO/REPAIRED/C0520792771S.IMG  GO_0022/I24/IO/GARBLED/C0520792771R.IMG
# GO_0022/I24/IO/REPAIRED/C0520792774S.IMG  GO_0022/I24/IO/GARBLED/C0520792774R.IMG
# GO_0022/I24/IO/REPAIRED/C0520792778S.IMG  GO_0022/I24/IO/GARBLED/C0520792778R.IMG
# GO_0022/I24/IO/REPAIRED/C0520792782S.IMG  GO_0022/I24/IO/GARBLED/C0520792782R.IMG
# GO_0022/I24/IO/REPAIRED/C0520792784S.IMG  GO_0022/I24/IO/GARBLED/C0520792784R.IMG
# GO_0022/I24/IO/REPAIRED/C0520792788S.IMG  GO_0022/I24/IO/GARBLED/C0520792788R.IMG
# GO_0022/I24/IO/REPAIRED/C0520792949S.IMG  GO_0022/I24/IO/GARBLED/C0520792949R.IMG
# GO_0022/I24/IO/REPAIRED/C0520792953S.IMG  GO_0022/I24/IO/GARBLED/C0520792953R.IMG
# GO_0022/I24/IO/REPAIRED/C0520792956S.IMG  GO_0022/I24/IO/GARBLED/C0520792956R.IMG
# GO_0022/I24/IO/REPAIRED/C0520792960S.IMG  GO_0022/I24/IO/GARBLED/C0520792960R.IMG
# GO_0022/I24/IO/REPAIRED/C0520792963S.IMG  GO_0022/I24/IO/GARBLED/C0520792963R.IMG
# GO_0022/I24/IO/REPAIRED/C0520792967S.IMG  GO_0022/I24/IO/GARBLED/C0520792967R.IMG
# GO_0022/I24/IO/REPAIRED/C0520792970S.IMG  GO_0022/I24/IO/GARBLED/C0520792970R.IMG
# GO_0022/I24/IO/REPAIRED/C0520792974S.IMG  GO_0022/I24/IO/GARBLED/C0520792974R.IMG
# GO_0022/I24/IO/REPAIRED/C0520792977S.IMG  GO_0022/I24/IO/GARBLED/C0520792977R.IMG
# GO_0022/I24/IO/REPAIRED/C0520792981S.IMG  GO_0022/I24/IO/GARBLED/C0520792981R.IMG
# GO_0022/I24/IO/REPAIRED/C0520792984S.IMG  GO_0022/I24/IO/GARBLED/C0520792984R.IMG
# GO_0022/I24/IO/REPAIRED/C0520792988S.IMG  GO_0022/I24/IO/GARBLED/C0520792988R.IMG
# GO_0022/I24/IO/REPAIRED/C0520793256S.IMG  GO_0022/I24/IO/GARBLED/C0520793256R.IMG
# GO_0022/I24/IO/REPAIRED/C0520793260S.IMG  GO_0022/I24/IO/GARBLED/C0520793260R.IMG
# GO_0022/I24/IO/REPAIRED/C0520793267S.IMG  GO_0022/I24/IO/GARBLED/C0520793267R.IMG
# GO_0022/I24/IO/REPAIRED/C0520793270S.IMG  GO_0022/I24/IO/GARBLED/C0520793270R.IMG
# GO_0022/I24/IO/REPAIRED/C0520793274S.IMG  GO_0022/I24/IO/GARBLED/C0520793274R.IMG
# GO_0022/I24/IO/REPAIRED/C0520793277S.IMG  GO_0022/I24/IO/GARBLED/C0520793277R.IMG
# GO_0022/I24/IO/REPAIRED/C0520793281S.IMG  GO_0022/I24/IO/GARBLED/C0520793281R.IMG
# GO_0022/I24/IO/REPAIRED/C0520793284S.IMG  GO_0022/I24/IO/GARBLED/C0520793284R.IMG
# GO_0022/I24/IO/REPAIRED/C0520793288S.IMG  GO_0022/I24/IO/GARBLED/C0520793288R.IMG
# GO_0022/I24/IO/REPAIRED/C0520793649S.IMG  GO_0022/I24/IO/GARBLED/C0520793649R.IMG
# GO_0022/I24/IO/REPAIRED/C0520793653S.IMG  GO_0022/I24/IO/GARBLED/C0520793653R.IMG
# GO_0022/I24/IO/REPAIRED/C0520793656S.IMG  GO_0022/I24/IO/GARBLED/C0520793656R.IMG
# GO_0022/I24/IO/REPAIRED/C0520793660S.IMG  GO_0022/I24/IO/GARBLED/C0520793660R.IMG
# GO_0022/I24/IO/REPAIRED/C0520793663S.IMG  GO_0022/I24/IO/GARBLED/C0520793663R.IMG
# GO_0022/I24/IO/REPAIRED/C0520793667S.IMG  GO_0022/I24/IO/GARBLED/C0520793667R.IMG
# GO_0022/I24/IO/REPAIRED/C0520793670S.IMG  GO_0022/I24/IO/GARBLED/C0520793670R.IMG
# GO_0022/I24/IO/REPAIRED/C0520793674S.IMG  GO_0022/I24/IO/GARBLED/C0520793674R.IMG
# GO_0022/I24/IO/REPAIRED/C0520793677S.IMG  GO_0022/I24/IO/GARBLED/C0520793677R.IMG
# GO_0022/I24/IO/REPAIRED/C0520793681S.IMG  GO_0022/I24/IO/GARBLED/C0520793681R.IMG
# GO_0022/I24/IO/REPAIRED/C0520793684S.IMG  GO_0022/I24/IO/GARBLED/C0520793684R.IMG
# GO_0022/I24/IO/REPAIRED/C0520793688S.IMG  GO_0022/I24/IO/GARBLED/C0520793688R.IMG
# GO_0022/I24/IO/REPAIRED/C0520794063S.IMG  GO_0022/I24/IO/GARBLED/C0520794063R.IMG
# GO_0022/I24/IO/REPAIRED/C0520794067S.IMG  GO_0022/I24/IO/GARBLED/C0520794067R.IMG
# GO_0022/I24/IO/REPAIRED/C0520794070S.IMG  GO_0022/I24/IO/GARBLED/C0520794070R.IMG
# GO_0022/I24/IO/REPAIRED/C0520794074S.IMG  GO_0022/I24/IO/GARBLED/C0520794074R.IMG
# GO_0022/I24/IO/REPAIRED/C0520794077S.IMG  GO_0022/I24/IO/GARBLED/C0520794077R.IMG
# GO_0022/I24/IO/REPAIRED/C0520794081S.IMG  GO_0022/I24/IO/GARBLED/C0520794081R.IMG
# GO_0022/I24/IO/REPAIRED/C0520794084S.IMG  GO_0022/I24/IO/GARBLED/C0520794084R.IMG
# GO_0022/I24/IO/REPAIRED/C0520794088S.IMG  GO_0022/I24/IO/GARBLED/C0520794088R.IMG
# GO_0022/I24/IO/REPAIRED/C0520794470S.IMG  GO_0022/I24/IO/GARBLED/C0520794470R.IMG
# GO_0022/I24/IO/REPAIRED/C0520794474S.IMG  GO_0022/I24/IO/GARBLED/C0520794474R.IMG
# GO_0022/I24/IO/REPAIRED/C0520794477S.IMG  GO_0022/I24/IO/GARBLED/C0520794477R.IMG
# GO_0022/I24/IO/REPAIRED/C0520794481S.IMG  GO_0022/I24/IO/GARBLED/C0520794481R.IMG
# GO_0022/I24/IO/REPAIRED/C0520794484S.IMG  GO_0022/I24/IO/GARBLED/C0520794484R.IMG
# GO_0022/I24/IO/REPAIRED/C0520794488S.IMG  GO_0022/I24/IO/GARBLED/C0520794488R.IMG
# GO_0022/I24/IO/REPAIRED/C0520794911S.IMG  GO_0022/I24/IO/GARBLED/C0520794911R.IMG
# GO_0022/I24/IO/REPAIRED/C0520795249S.IMG  GO_0022/I24/IO/GARBLED/C0520795249R.IMG
# GO_0022/I24/IO/REPAIRED/C0520795253S.IMG  GO_0022/I24/IO/GARBLED/C0520795253R.IMG
# GO_0022/I24/IO/REPAIRED/C0520795256S.IMG  GO_0022/I24/IO/GARBLED/C0520795256R.IMG
# GO_0022/I24/IO/REPAIRED/C0520795384S.IMG  GO_0022/I24/IO/GARBLED/C0520795384R.IMG
# GO_0022/I24/IO/REPAIRED/C0520795388S.IMG  GO_0022/I24/IO/GARBLED/C0520795388R.IMG
# GO_0022/I24/IO/REPAIRED/C0520795400S.IMG  GO_0022/I24/IO/GARBLED/C0520795400R.IMG
# GO_0022/I24/IO/REPAIRED/C0520795742S.IMG  GO_0022/I24/IO/GARBLED/C0520795742R.IMG
# GO_0022/I24/IO/REPAIRED/C0520795746S.IMG  GO_0022/I24/IO/GARBLED/C0520795746R.IMG
# GO_0022/I24/IO/REPAIRED/C0520795881S.IMG  GO_0022/I24/IO/GARBLED/C0520795881R.IMG
# GO_0022/I24/IO/REPAIRED/C0520795884S.IMG  GO_0022/I24/IO/GARBLED/C0520795884R.IMG
# GO_0022/I24/IO/REPAIRED/C0520795888S.IMG  GO_0022/I24/IO/GARBLED/C0520795888R.IMG
# GO_0022/I24/IO/REPAIRED/C0520797284S.IMG  GO_0022/I24/IO/GARBLED/C0520797284R.IMG
# GO_0022/I24/IO/REPAIRED/C0520797288S.IMG  GO_0022/I24/IO/GARBLED/C0520797288R.IMG
# GO_0022/I24/IO/REPAIRED/C0520797300S.IMG  GO_0022/I24/IO/GARBLED/C0520797300R.IMG
# GO_0022/I24/IO/REPAIRED/C0520797304S.IMG  GO_0022/I24/IO/GARBLED/C0520797304R.IMG
# GO_0022/I24/IO/REPAIRED/C0520797307S.IMG  GO_0022/I24/IO/GARBLED/C0520797307R.IMG
# GO_0022/I24/IO/REPAIRED/C0520797311S.IMG  GO_0022/I24/IO/GARBLED/C0520797311R.IMG
# GO_0022/I24/IO/REPAIRED/C0520797442S.IMG  GO_0022/I24/IO/GARBLED/C0520797442R.IMG
# GO_0022/I24/IO/REPAIRED/C0520797446S.IMG  GO_0022/I24/IO/GARBLED/C0520797446R.IMG
# GO_0022/I24/IO/REPAIRED/C0520797449S.IMG  GO_0022/I24/IO/GARBLED/C0520797449R.IMG
# GO_0022/I24/IO/REPAIRED/C0520797453S.IMG  GO_0022/I24/IO/GARBLED/C0520797453R.IMG
# GO_0022/I24/IO/REPAIRED/C0520797970S.IMG  GO_0022/I24/IO/GARBLED/C0520797970R.IMG
# GO_0022/I24/IO/REPAIRED/C0520797974S.IMG  GO_0022/I24/IO/GARBLED/C0520797974R.IMG
# GO_0022/I24/IO/REPAIRED/C0520797977S.IMG  GO_0022/I24/IO/GARBLED/C0520797977R.IMG
# GO_0022/I24/IO/REPAIRED/C0520797981S.IMG  GO_0022/I24/IO/GARBLED/C0520797981R.IMG
# GO_0022/I24/IO/REPAIRED/C0520798328S.IMG  GO_0022/I24/IO/GARBLED/C0520798328R.IMG
# GO_0022/I24/IO/REPAIRED/C0520798332S.IMG  GO_0022/I24/IO/GARBLED/C0520798332R.IMG
# GO_0022/I24/IO/REPAIRED/C0520798335S.IMG  GO_0022/I24/IO/GARBLED/C0520798335R.IMG
# GO_0022/I24/IO/REPAIRED/C0520798339S.IMG  GO_0022/I24/IO/GARBLED/C0520798339R.IMG
# GO_0022/I24/IO/REPAIRED/C0520798342S.IMG  GO_0022/I24/IO/GARBLED/C0520798342R.IMG
# GO_0022/I24/IO/REPAIRED/C0520798346S.IMG  GO_0022/I24/IO/GARBLED/C0520798346R.IMG
# GO_0022/I24/IO/REPAIRED/C0520798477S.IMG  GO_0022/I24/IO/GARBLED/C0520798477R.IMG
# GO_0022/I24/IO/REPAIRED/C0520798481S.IMG  GO_0022/I24/IO/GARBLED/C0520798481R.IMG
# GO_0022/I24/IO/REPAIRED/C0520798484S.IMG  GO_0022/I24/IO/GARBLED/C0520798484R.IMG
# GO_0022/I24/IO/REPAIRED/C0520798488S.IMG  GO_0022/I24/IO/GARBLED/C0520798488R.IMG
# GO_0022/I24/IO/REPAIRED/C0520798500S.IMG  GO_0022/I24/IO/GARBLED/C0520798500R.IMG
# GO_0022/I24/IO/REPAIRED/C0520798504S.IMG  GO_0022/I24/IO/GARBLED/C0520798504R.IMG
# GO_0022/I24/IO/REPAIRED/C0520798635S.IMG  GO_0022/I24/IO/GARBLED/C0520798635R.IMG
# GO_0022/I24/IO/REPAIRED/C0520798639S.IMG  GO_0022/I24/IO/GARBLED/C0520798639R.IMG
# GO_0022/I24/IO/REPAIRED/C0520798642S.IMG  GO_0022/I24/IO/GARBLED/C0520798642R.IMG
# GO_0022/I24/IO/REPAIRED/C0520798646S.IMG  GO_0022/I24/IO/GARBLED/C0520798646R.IMG
# GO_0022/I24/IO/REPAIRED/C0520798649S.IMG  GO_0022/I24/IO/GARBLED/C0520798649R.IMG
# GO_0022/I24/IO/REPAIRED/C0520798653S.IMG  GO_0022/I24/IO/GARBLED/C0520798653R.IMG
# GO_0022/I24/IO/REPAIRED/C0520799170S.IMG  GO_0022/I24/IO/GARBLED/C0520799170R.IMG
# GO_0022/I24/IO/REPAIRED/C0520799174S.IMG  GO_0022/I24/IO/GARBLED/C0520799174R.IMG
# GO_0022/I24/IO/REPAIRED/C0520799177S.IMG  GO_0022/I24/IO/GARBLED/C0520799177R.IMG
# GO_0022/I24/IO/REPAIRED/C0520799181S.IMG  GO_0022/I24/IO/GARBLED/C0520799181R.IMG
# GO_0022/I24/IO/REPAIRED/C0520799184S.IMG  GO_0022/I24/IO/GARBLED/C0520799184R.IMG
# GO_0022/I24/IO/REPAIRED/C0520799188S.IMG  GO_0022/I24/IO/GARBLED/C0520799188R.IMG
# GO_0022/I24/IO/REPAIRED/C0520806300S.IMG  GO_0022/I24/IO/GARBLED/C0520806300R.IMG
# GO_0022/I24/IO/REPAIRED/C0520806304S.IMG  GO_0022/I24/IO/GARBLED/C0520806304R.IMG
# GO_0023/G28/REPAIRED/C0552447569S.IMG     GO_0023/G28/GARBLED/C0552447569R.IMG
# GO_0023/G29/REPAIRED/C0600491113S.IMG     GO_0023/G29/GARBLED/C0600491113R.IMG
# GO_0023/G29/REPAIRED/C0600491185S.IMG     GO_0023/G29/GARBLED/C0600491185R.IMG
# GO_0023/G29/REPAIRED/C0600492445S.IMG     GO_0023/G29/GARBLED/C0600492445R.IMG
# GO_0023/G29/REPAIRED/C0600492468S.IMG     GO_0023/G29/GARBLED/C0600492468R.IMG
# GO_0023/G29/REPAIRED/C0600492500S.IMG     GO_0023/G29/GARBLED/C0600492500R.IMG
# GO_0023/G29/REPAIRED/C0600492522S.IMG     GO_0023/G29/GARBLED/C0600492522R.IMG
# GO_0023/G29/REPAIRED/C0600492523S.IMG     GO_0023/G29/GARBLED/C0600492523R.IMG
# GO_0023/G29/REPAIRED/C0600492545S.IMG     GO_0023/G29/GARBLED/C0600492545R.IMG
# GO_0023/G29/REPAIRED/C0600660200S.IMG     GO_0023/G29/GARBLED/C0600660200R.IMG
# GO_0023/G29/REPAIRED/C0600660201S.IMG     GO_0023/G29/GARBLED/C0600660201R.IMG
# GO_0023/G29/REPAIRED/C0600660222S.IMG     GO_0023/G29/GARBLED/C0600660222R.IMG
# GO_0023/G29/REPAIRED/C0600660223S.IMG     GO_0023/G29/GARBLED/C0600660223R.IMG
# GO_0023/G29/REPAIRED/C0600660245S.IMG     GO_0023/G29/GARBLED/C0600660245R.IMG
# GO_0023/G29/REPAIRED/C0600660246S.IMG     GO_0023/G29/GARBLED/C0600660246R.IMG
# GO_0023/G29/REPAIRED/C0600660368S.IMG     GO_0023/G29/GARBLED/C0600660368R.IMG
# GO_0023/G29/REPAIRED/C0600660369S.IMG     GO_0023/G29/GARBLED/C0600660369R.IMG
# GO_0023/G29/REPAIRED/C0600660522S.IMG     GO_0023/G29/GARBLED/C0600660522R.IMG
# GO_0023/G29/REPAIRED/C0600660523S.IMG     GO_0023/G29/GARBLED/C0600660523R.IMG
# GO_0023/G29/REPAIRED/C0600660668S.IMG     GO_0023/G29/GARBLED/C0600660668R.IMG
# GO_0023/G29/REPAIRED/C0600660669S.IMG     GO_0023/G29/GARBLED/C0600660669R.IMG
# GO_0023/G29/REPAIRED/C0600660822S.IMG     GO_0023/G29/GARBLED/C0600660822R.IMG
# GO_0023/G29/REPAIRED/C0600660823S.IMG     GO_0023/G29/GARBLED/C0600660823R.IMG
# GO_0023/G29/REPAIRED/C0600660968S.IMG     GO_0023/G29/GARBLED/C0600660968R.IMG
# GO_0023/G29/REPAIRED/C0600660969S.IMG     GO_0023/G29/GARBLED/C0600660969R.IMG
# GO_0023/REDO/E11/IO/C0420361500R.IMG      (no counterpart)

##########################################################################################
# DESCRIPTION_AND_ICON
##########################################################################################

description_and_icon_by_regex = translator.TranslatorByRegex([
    (r'volumes/\w+/\w+(|/REDO)/[CEGIJ]\d\d?',            0, ('Images grouped by orbit',  'IMAGEDIR')),
    (r'volumes/\w+/\w+(|/REDO)/[CEGIJ]\d\d?/\w+',        0, ('Images grouped by target', 'IMAGEDIR')),
    (r'volumes/\w+/(MOON|EARTH|VENUS|IDA|GASPRA|SL9)',   0, ('Images grouped by target', 'IMAGEDIR')),
    (r'volumes/\w+/RAW_CAL',                             0, ('Calibration images',       'IMAGEDIR')),
    (r'volumes/\w+/EMCONJ',                              0, ('Images targeted at the Earth-Moon conjunction', 'IMAGEDIR')),
    (r'volumes/\w+/GOPEX',                               0, ('Images for the Galileo Optical Experiment',     'IMAGEDIR')),
    (r'volumes/\w+/\w+(|/REDO)/[CEGIJ]\d\d?/\w+/C\d{6}', 0, ('Images grouped by SC clock',           'IMAGEDIR')),
    (r'volumes/\w+/GO_00(0\d|1[0-6])\w+/REDO',           0, ('Re-processed images',                  'IMAGEDIR')),
    (r'volumes/\w+/GO_00(1[789]|2\d)REDO',               0, ('Re-processed images grouped by orbit', 'IMAGEDIR')),

    (r'volumes/.*/REDO/.*R\.IMG', 0, ('Repaired raw image, VICAR'             , 'IMAGE')),
    (r'volumes/.*S\.IMG',         0, ('Repaired raw image, VICAR'             , 'IMAGE')),
    (r'volumes/.*R\.IMG',         0, ('Raw image, VICAR'                      , 'IMAGE')),
    (r'volumes/.*G\.IMG',         0, ('Image with SL9 graphics overlay, VICAR', 'IMAGE')),

    (r'metadata/GO_0xxx/GO_0016/GO_0016_sl9_index.tab', 0, ('Index for SL9 multiple exposures', 'INDEX')),
])

##########################################################################################
# VIEWABLES
##########################################################################################

default_viewables = translator.TranslatorByRegex([
    (r'volumes/(.*/C\d{10}[A-Z])\.(IMG|LBL)', 0,
            [r'previews/\1_full.jpg',
             r'previews/\1_med.jpg',
             r'previews/\1_small.jpg',
             r'previews/\1_thumb.jpg',
            ]),
    (r'volumes/(GO_0xxx_v1/.*/C\d{6}/.*)\.(IMG|LBL)', 0,
            [r'previews/\1_full.jpg',
             r'previews/\1_med.jpg',
             r'previews/\1_small.jpg',
             r'previews/\1_thumb.jpg',
            ]),
])

##########################################################################################
# ASSOCIATIONS
##########################################################################################

associations_to_volumes = translator.TranslatorByRegex([
    (r'.*/(GO_0xxx/GO_..../.*/C\d{10}[A-Z]).*', 0,
            [r'volumes/\1.IMG',
             r'volumes/\1.LBL',
            ]),
    (r'.*/GO_0xxx_v1/(GO_..../.*/C\d{6})/(\d{4}[A-Z]).*', 0,
            [r'volumes/GO_0xxx_v1/\1/\2.IMG',
             r'volumes/GO_0xxx_v1/\1/\2.LBL',
             r'volumes/GO_0xxx/\1\2.IMG',
             r'volumes/GO_0xxx/\1\2.LBL'
            ]),
    (r'previews/(GO_0..._v1/.*)_[a-z]+\.jpg', 0,
            [r'volumes/\1.IMG',
             r'volumes/\1.LBL',
            ]),
    (r'metadata/GO_0xxx/GO_0999.*', 0,
            r'volumes/GO_0xxx'),
    (r'metadata/GO_0xxx_v1/GO_0999.*', 0,
            r'volumes/GO_0xxx_v1'),

    # SL9 "graphics" file associations
    (r'volumes/GO_0xxx/GO_0016/SL9/(C\d{10})R\.(IMG|LBL)', 0,
            [r'volumes/GO_0xxx/GO_0016/SL9/\1G.IMG',
             r'volumes/GO_0xxx/GO_0016/SL9/\1G.LBL',
            ]),

    (r'volumes/GO_0xxx/GO_0016/SL9/(C\d{10})G\.(IMG|LBL)', 0,
            [r'volumes/GO_0xxx/GO_0016/SL9/\1R.IMG',
             r'volumes/GO_0xxx/GO_0016/SL9/\1R.LBL',
            ]),

    # Known duplicates...
    (r'volumes/GO_0xxx/GO_0006/REDO/(C0018062639R).*'   , 0, r'volumes/GO_0xxx/GO_0002/VENUS/\1.*'),
    (r'volumes/GO_0xxx/GO_0006/REDO/(C0018241745R).*'   , 0, r'volumes/GO_0xxx/GO_0002/VENUS/\1.*'),
    (r'volumes/GO_0xxx/GO_0006/REDO/(C0018353518R).*'   , 0, r'volumes/GO_0xxx/GO_0002/VENUS/\1.*'),
    (r'volumes/GO_0xxx/GO_0006/REDO/(C0018518445R).*'   , 0, r'volumes/GO_0xxx/GO_0002/VENUS/\1.*'),
    (r'volumes/GO_0xxx/GO_0006/REDO/(C0059469700R).*'   , 0, r'volumes/GO_0xxx/GO_0002/RAW_CAL/\1.*'),
    (r'volumes/GO_0xxx/GO_0006/REDO/(C0059471700R).*'   , 0, r'volumes/GO_0xxx/GO_0002/RAW_CAL/\1.*'),
    (r'volumes/GO_0xxx/GO_0006/REDO/(C0060964000R).*'   , 0, r'volumes/GO_0xxx/GO_0003/MOON/\1.*'),
    (r'volumes/GO_0xxx/GO_0006/REDO/(C0061078900R).*'   , 0, r'volumes/GO_0xxx/GO_0004/EARTH/\1.*'),
    (r'volumes/GO_0xxx/GO_0006/REDO/(C0061116.00R).*'   , 0, r'volumes/GO_0xxx/GO_0004/MOON/\1.*'),
    (r'volumes/GO_0xxx/GO_0006/REDO/(C0061424500R).*'   , 0, r'volumes/GO_0xxx/GO_0004/EARTH/\1.*'),
    (r'volumes/GO_0xxx/GO_0006/REDO/(C0061441500R).*'   , 0, r'volumes/GO_0xxx/GO_0004/EARTH/\1.*'),
    (r'volumes/GO_0xxx/GO_0006/REDO/(C0061469100R).*'   , 0, r'volumes/GO_0xxx/GO_0005/EARTH/\1.*'),
    (r'volumes/GO_0xxx/GO_0006/REDO/(C006150..00R).*'   , 0, r'volumes/GO_0xxx/GO_0005/EARTH/\1.*'),
    (r'volumes/GO_0xxx/GO_0006/REDO/(C006151..00R).*'   , 0, r'volumes/GO_0xxx/GO_0005/EARTH/\1.*'),
    (r'volumes/GO_0xxx/GO_0006/REDO/(C006152..00R).*'   , 0, r'volumes/GO_0xxx/GO_0005/EARTH/\1.*'),
    (r'volumes/GO_0xxx/GO_0006/REDO/(C006153..00R).*'   , 0, r'volumes/GO_0xxx/GO_0006/EARTH/\1.*'),
    (r'volumes/GO_0xxx/GO_0006/REDO/(C0061542500R).*'   , 0, r'volumes/GO_0xxx/GO_0006/EARTH/\1.*'),
    (r'volumes/GO_0xxx/GO_0015/REDO/(C0165242700R).*'   , 0, r'volumes/GO_0xxx/GO_0012/EARTH/\1.*'),

    (r'volumes/GO_0xxx/GO_0002/VENUS/(C0018062639R).*'  , 0, r'volumes/GO_0xxx/GO_0006/REDO/\1.*'),
    (r'volumes/GO_0xxx/GO_0002/VENUS/(C0018241745R).*'  , 0, r'volumes/GO_0xxx/GO_0006/REDO/\1.*'),
    (r'volumes/GO_0xxx/GO_0002/VENUS/(C0018353518R).*'  , 0, r'volumes/GO_0xxx/GO_0006/REDO/\1.*'),
    (r'volumes/GO_0xxx/GO_0002/VENUS/(C0018518445R).*'  , 0, r'volumes/GO_0xxx/GO_0006/REDO/\1.*'),
    (r'volumes/GO_0xxx/GO_0002/RAW_CAL/(C0059469700R).*', 0, r'volumes/GO_0xxx/GO_0006/REDO/\1.*'),
    (r'volumes/GO_0xxx/GO_0002/RAW_CAL/(C0059471700R).*', 0, r'volumes/GO_0xxx/GO_0006/REDO/\1.*'),
    (r'volumes/GO_0xxx/GO_0003/MOON/(C0060964000R).*'   , 0, r'volumes/GO_0xxx/GO_0006/REDO/\1.*'),
    (r'volumes/GO_0xxx/GO_0004/EARTH/(C0061078900R).*'  , 0, r'volumes/GO_0xxx/GO_0006/REDO/\1.*'),
    (r'volumes/GO_0xxx/GO_0004/MOON/(C0061116.00R).*'   , 0, r'volumes/GO_0xxx/GO_0006/REDO/\1.*'),
    (r'volumes/GO_0xxx/GO_0004/EARTH/(C0061424500R).*'  , 0, r'volumes/GO_0xxx/GO_0006/REDO/\1.*'),
    (r'volumes/GO_0xxx/GO_0004/EARTH/(C0061441500R).*'  , 0, r'volumes/GO_0xxx/GO_0006/REDO/\1.*'),
    (r'volumes/GO_0xxx/GO_0005/EARTH/(C0061469100R).*'  , 0, r'volumes/GO_0xxx/GO_0006/REDO/\1.*'),
    (r'volumes/GO_0xxx/GO_0005/EARTH/(C006150..00R).*'  , 0, r'volumes/GO_0xxx/GO_0006/REDO/\1.*'),
    (r'volumes/GO_0xxx/GO_0005/EARTH/(C006151..00R).*'  , 0, r'volumes/GO_0xxx/GO_0006/REDO/\1.*'),
    (r'volumes/GO_0xxx/GO_0005/EARTH/(C006152..00R).*'  , 0, r'volumes/GO_0xxx/GO_0006/REDO/\1.*'),
    (r'volumes/GO_0xxx/GO_0005/EARTH/(C006153..00R).*'  , 0, r'volumes/GO_0xxx/GO_0006/REDO/\1.*'),
    (r'volumes/GO_0xxx/GO_0006/EARTH/(C0061542500R).*'  , 0, r'volumes/GO_0xxx/GO_0006/REDO/\1.*'),
    (r'volumes/GO_0xxx/GO_0012/EARTH/(C0165242700R).*'  , 0, r'volumes/GO_0xxx/GO_0015/REDO/\1.*'),

    (r'volumes/GO_0xxx/GO_0018/REDO/(C3/JUPITER/C036897..00R).*', 0, r'volumes/GO_0xxx/GO_0017/\1.*'),
    (r'volumes/GO_0xxx/GO_0018/REDO/(C3/JUPITER/C036898..00R).*', 0, r'volumes/GO_0xxx/GO_0017/\1.*'),
    (r'volumes/GO_0xxx/GO_0018/REDO/(C3/JUPITER/C036899..00R).*', 0, r'volumes/GO_0xxx/GO_0017/\1.*'),
    (r'volumes/GO_0xxx/GO_0019/REDO/(C3/EUROPA/C0368976...R).*' , 0, r'volumes/GO_0xxx/GO_0017/\1.*'),
    (r'volumes/GO_0xxx/GO_0019/REDO/(C3/JUPITER/C0368369268R).*', 0, r'volumes/GO_0xxx/GO_0017/\1.*'),
    (r'volumes/GO_0xxx/GO_0019/REDO/(C3/JUPITER/C0368441600R).*', 0, r'volumes/GO_0xxx/GO_0017/\1.*'),
    (r'volumes/GO_0xxx/GO_0019/REDO/(E4/EUROPA/C0374667300R).*' , 0, r'volumes/GO_0xxx/GO_0018/\1.*'),
    (r'volumes/GO_0xxx/GO_0019/REDO/(E6/IO/C0383655111R).*'     , 0, r'volumes/GO_0xxx/GO_0018/\1.*'),

    (r'volumes/GO_0xxx/GO_0017/(C3/JUPITER/C036897..00R).*'     , 0, r'volumes/GO_0xxx/GO_0018/REDO/\1.*'),
    (r'volumes/GO_0xxx/GO_0017/(C3/JUPITER/C036898..00R).*'     , 0, r'volumes/GO_0xxx/GO_0018/REDO/\1.*'),
    (r'volumes/GO_0xxx/GO_0017/(C3/JUPITER/C036899..00R).*'     , 0, r'volumes/GO_0xxx/GO_0018/REDO/\1.*'),
    (r'volumes/GO_0xxx/GO_0017/(C3/EUROPA/C0368976...R).*'      , 0, r'volumes/GO_0xxx/GO_0019/REDO/\1.*'),
    (r'volumes/GO_0xxx/GO_0017/(C3/JUPITER/C0368369268R).*'     , 0, r'volumes/GO_0xxx/GO_0019/REDO/\1.*'),
    (r'volumes/GO_0xxx/GO_0017/(C3/JUPITER/C0368441600R).*'     , 0, r'volumes/GO_0xxx/GO_0019/REDO/\1.*'),
    (r'volumes/GO_0xxx/GO_0018/(E4/EUROPA/C0374667300R).*'      , 0, r'volumes/GO_0xxx/GO_0019/REDO/\1.*'),
    (r'volumes/GO_0xxx/GO_0018/(E6/IO/C0383655111R).*'          , 0, r'volumes/GO_0xxx/GO_0019/REDO/\1.*'),

    (r'volumes/GO_0xxx/GO_0020/E12/TIRETRACK/(C04262728..)S.*'  , 0, r'volumes/GO_0xxx/GO_0020/E12/EUROPA/\1R.*'),
    (r'volumes/GO_0xxx/GO_0022/I24/IO/REPAIRED/(C052079....)S.*', 0, r'volumes/GO_0xxx/GO_0022/I24/IO/GARBLED/\1R.*'),
    (r'volumes/GO_0xxx/GO_0022/I24/IO/REPAIRED/(C052080630.)S.*', 0, r'volumes/GO_0xxx/GO_0022/I24/IO/GARBLED/\1R.*'),
    (r'volumes/GO_0xxx/GO_0023/G28/REPAIRED/(C0552447569)S.*'   , 0, r'volumes/GO_0xxx/GO_0023/G28/GARBLED/\1R.*'),
    (r'volumes/GO_0xxx/GO_0023/G29/REPAIRED/(C060049.*)S.*'     , 0, r'volumes/GO_0xxx/GO_0023/G29/GARBLED/\1R.*'),
    (r'volumes/GO_0xxx/GO_0023/G29/REPAIRED/(C060066.*)S.*'     , 0, r'volumes/GO_0xxx/GO_0023/G29/GARBLED/\1R.*'),

    (r'volumes/GO_0xxx/GO_0020/E12/EUROPA/(C04262728..)R.*'     , 0, r'volumes/GO_0xxx/GO_0020/E12/TIRETRACK/\1S.*'),
    (r'volumes/GO_0xxx/GO_0022/I24/IO/GARBLED/(C052079....)R.*' , 0, r'volumes/GO_0xxx/GO_0022/I24/IO/REPAIRED/\1S.*'),
    (r'volumes/GO_0xxx/GO_0022/I24/IO/GARBLED/(C052080630.)R.*' , 0, r'volumes/GO_0xxx/GO_0022/I24/IO/REPAIRED/\1S.*'),
    (r'volumes/GO_0xxx/GO_0023/G28/GARBLED/(C0552447569)R.*'    , 0, r'volumes/GO_0xxx/GO_0023/G28/REPAIRED/\1S.*'),
    (r'volumes/GO_0xxx/GO_0023/G29/GARBLED/(C060049.*)R.*'      , 0, r'volumes/GO_0xxx/GO_0023/G29/REPAIRED/\1S.*'),
    (r'volumes/GO_0xxx/GO_0023/G29/GARBLED/(C060066.*)R.*'      , 0, r'volumes/GO_0xxx/GO_0023/G29/REPAIRED/\1S.*'),

    (r'documents/GO_0xxx.*'                                     , 0, r'volumes/GO_0xxx'),
])

associations_to_previews = translator.TranslatorByRegex([
    (r'.*/(GO_0xxx/GO_..../.*/C\d{10}[A-Z]).*', 0,
            [r'previews/\1_full.jpg',
             r'previews/\1_med.jpg',
             r'previews/\1_small.jpg',
             r'previews/\1_thumb.jpg',
            ]),
    (r'.*/GO_0xxx_v1/(GO_..../.*/C\d{6})/(\d{4}[A-Z]).*', 0,
            [r'previews/GO_0xxx_v1/\1/\2_full.jpg',
             r'previews/GO_0xxx_v1/\1/\2_med.jpg',
             r'previews/GO_0xxx_v1/\1/\2_small.jpg',
             r'previews/GO_0xxx_v1/\1/\2_thumb.jpg',
             r'previews/GO_0xxx/\1\2_full.jpg',
             r'previews/GO_0xxx/\1\2_med.jpg',
             r'previews/GO_0xxx/\1\2_small.jpg',
             r'previews/GO_0xxx/\1\2_thumb.jpg',
            ]),
    (r'.*/metadata/GO_0xxx/GO_0999.*', 0,
            r'previews/GO_0xxx'),
    (r'.*/metadata/GO_0xxx_v1/GO_0999.*', 0,
            r'previews/GO_0xxx_v1'),
])

associations_to_metadata = translator.TranslatorByRegex([
    (r'volumes/(GO_0xxx)/(GO_....)/.*/(C\d{10})[RS].*', 0,
            [r'metadata/\1/\2/\2_index.tab/\3',
             r'metadata/\1/\2/\2_supplemental_index.tab/\3',
             r'metadata/\1/\2/\2_ring_summary.tab/\3',
             r'metadata/\1/\2/\2_moon_summary.tab/\3',
             r'metadata/\1/\2/\2_jupiter_summary.tab/\3',
             r'metadata/\1/\2/\2_body_summary.tab/\3',
             r'metadata/\1/\2/\2_sky_summary.tab/\3',
            ]),
    (r'volumes/(GO_0xxx_v1)/(GO_....).*', 0,
            r'metadata/\1/\2'),
    (r'metadata/GO_0xxx(|_v[\d\.]+)/GO_00..', 0,
            r'metadata/GO_0xxx/GO_0999'),
    (r'metadata/GO_0xxx(|_v[\d\.]+)/GO_00../GO_00.._(.*)\..*', 0,
            [r'metadata/GO_0xxx/GO_0999/GO_0999_\2.tab',
             r'metadata/GO_0xxx/GO_0999/GO_0999_\2.lbl',
            ]),
    (r'volumes/GO_0xxx/GO_0016/SL9/(C\d{10})[RG].*', 0,
            r'metadata/GO_0xxx/GO_0016/GO_0016_sl9_index.tab/\1'),
])

associations_to_documents = translator.TranslatorByRegex([
    (r'volumes/GO_0xxx(|_[^/]+)/GO_0\d\d\d',    0, r'documents/GO_0xxx/*'),
    (r'volumes/GO_0xxx(|_[^/]+)/GO_0\d\d\d/.+', 0, r'documents/GO_0xxx'),
])

##########################################################################################
# VERSIONS
##########################################################################################

# File names are split in _v1, merged afterward
versions = translator.TranslatorByRegex([
    (r'volumes/GO_0xxx.*/(GO_0.../.*/C\d{6})/?(\d{4}[A-Z]\..*)', 0,
            [r'volumes/GO_0xxx/\1\2',
             r'volumes/GO_0xxx_v1/\1/\2',
            ]),
])

##########################################################################################
# VIEW_OPTIONS (grid_view_allowed, multipage_view_allowed, continuous_view_allowed)
##########################################################################################

view_options = translator.TranslatorByRegex([
    (r'(volumes|previews)/GO_0xxx/GO_....(|/BROWSE)/([CEGIJ]\d\d?|REDO)/.*',            0, (True, True, True)),
    (r'(volumes|previews)/GO_0xxx_v1/GO_....(|/BROWSE)/([CEGIJ]\d\d?|REDO)/.*/C\d{6}',  0, (True, True, False)),
    (r'(volumes|previews)/GO_0xxx_v1/GO_....(|/BROWSE)/([CEGIJ]\d\d?|REDO)/.*',         0, (True, True, True)),
])

##########################################################################################
# NEIGHBORS
##########################################################################################

neighbors = translator.TranslatorByRegex([
    (r'(volumes|previews)/GO_0xxx(|_v[\d\.]+)/GO_00../(MOON|EARTH|VENUS|IDA|GASPRA|SL9|GOPEX|EMCONJ|RAW_CAL)', 0, r'\1/GO_0xxx\2/GO_00??/\3'),
    (r'(volumes|previews)/GO_0xxx/GO_0016/SL9/(C\d{10})([RG])(.*)', 0, r'\1/GO_0xxx/GO_0016/SL9/C*\3\4'),
    (r'(volumes|previews)/GO_0xxx(_v[\d\.]+)/GO_0016/SL9/(C\d{6})/(\d{4})([RG])(.*)', 0, r'\1/GO_0xxx\2/GO_0016/SL9/C*/*\5\6'),

    (r'(volumes|previews)/GO_0xxx(|_v[\d\.]+)/\w+(|/REDO)/([CEGIJ]\d\d?)', 0,
            [r'\1/GO_0xxx\2/*/\4',
             r'\1/GO_0xxx\2/*/REDO/\4'
            ]),
    (r'(volumes|previews)/GO_0xxx(|_v[\d\.]+)/\w+(|/REDO)/[CEGIJ]\d\d?/(\w+)', 0,
            [r'\1/GO_0xxx\2/*/*/\4',
             r'\1/GO_0xxx\2/*/REDO/*/\4',
            ]),
    (r'(volumes|previews)/GO_0xxx(|_v[\d\.]+)/\w+(|/REDO)/[CEGIJ]\d\d?/(\w+)/C\d{6}', 0,
            [r'\1/GO_0xxx\2/*/*/\4/*',
             r'\1/GO_0xxx\2/*/REDO/*/\4/*',
            ]),
])

##########################################################################################
# SORT_KEY
##########################################################################################

sort_key = translator.TranslatorByRegex([

    # Puts encounters in chronological order, after AAREADME, in root directory
    (r'([CEGIJ])(\d)',   0, r'AAZ0\2\1'),
    (r'([CEGIJ])(\d\d)', 0, r'AAZ\2\1'),
    (r'(AAREADME.TXT)',  0, r'\1'),
    (r'(CATALOG)',       0, r'\1'),
    (r'(DOCUMENT)',      0, r'\1'),
    (r'(ERRATA.TXT)',    0, r'\1'),
    (r'(INDEX)',         0, r'\1'),
    (r'(LABEL)',         0, r'\1'),
    (r'(REDO)',          0, r'\1'),
    (r'(VOLDESC.CAT)',   0, r'\1'),
])

##########################################################################################
# SPLIT_RULES
##########################################################################################

split_rules = translator.TranslatorByRegex([
    (r'(C\d{10})([A-Z])\.(.*)', 0, (r'\1', r'\2', r'.\3')),
])

##########################################################################################
# OPUS_TYPE
##########################################################################################

opus_type = translator.TranslatorByRegex([
    (r'volumes/GO_0xxx/GO_0.../(?!CATALOG|DOCUMENT|INDEX|LABEL).*[^G]\.(IMG|LBL)', 0, ('Galileo SSI', 10, 'gossi_raw', 'Raw Image', True)),
    (r'volumes/GO_0xxx/GO_0016/SL9/.*G.(IMG|LBL)',                                 0, ('Galileo SSI', 12, 'gossi_sl9', 'Image with SL9 graphics overlay', True)),
    # Documentation
    (r'documents/GO_0xxx/.*',                                                      0, ('Galileo SSI', 20, 'gossi_documentation', 'Documentation', False)),
])

##########################################################################################
# OPUS_FORMAT
##########################################################################################

opus_format = translator.TranslatorByRegex([
    (r'.*\.IMG', 0, ('Binary', 'VICAR')),
])

##########################################################################################
# OPUS_PRODUCTS
##########################################################################################

# NOTE: _v1 files have been intentionally removed
opus_products = translator.TranslatorByRegex([

    # Default handling of all product file paths
    (r'volumes/GO_0xxx/(GO_0...)/(.*/C\d{10}[RSG])\.(IMG|LBL)', 0,
            [r'volumes/GO_0xxx/\1/\2.IMG',
             r'volumes/GO_0xxx/\1/\2.LBL',
             r'previews/GO_0xxx/\1/\2_full.jpg',
             r'previews/GO_0xxx/\1/\2_med.jpg',
             r'previews/GO_0xxx/\1/\2_small.jpg',
             r'previews/GO_0xxx/\1/\2_thumb.jpg',
             r'metadata/GO_0xxx/\1/\1_moon_summary.tab',
             r'metadata/GO_0xxx/\1/\1_moon_summary.lbl',
             r'metadata/GO_0xxx/\1/\1_ring_summary.tab',
             r'metadata/GO_0xxx/\1/\1_ring_summary.lbl',
             r'metadata/GO_0xxx/\1/\1_jupiter_summary.tab',
             r'metadata/GO_0xxx/\1/\1_jupiter_summary.lbl',
             r'metadata/GO_0xxx/\1/\1_body_summary.tab',
             r'metadata/GO_0xxx/\1/\1_body_summary.lbl',
             r'metadata/GO_0xxx/\1/\1_sky_summary.tab',
             r'metadata/GO_0xxx/\1/\1_sky_summary.lbl',
             r'metadata/GO_0xxx/\1/\1_inventory.csv',
             r'metadata/GO_0xxx/\1/\1_inventory.lbl',
             r'metadata/GO_0xxx/\1/\1_index.tab',
             r'metadata/GO_0xxx/\1/\1_index.lbl',
             r'metadata/GO_0xxx/\1/\1_supplemental_index.tab',
             r'metadata/GO_0xxx/\1/\1_supplemental_index.lbl',
             r'documents/GO_0xxx/*.[!lz]*'
            ]),

    # SL9 "graphics" file associations
    (r'.*volumes/GO_0xxx/GO_0016/SL9/(C\d{10})R\.(IMG|LBL)', 0,
            [r'volumes/GO_0xxx/GO_0016/SL9/\1G.IMG',
             r'volumes/GO_0xxx/GO_0016/SL9/\1G.LBL',
             r'previews/GO_0xxx/GO_0016/SL9/\1G_full.jpg',
             r'previews/GO_0xxx/GO_0016/SL9/\1G_med.jpg',
             r'previews/GO_0xxx/GO_0016/SL9/\1G_small.jpg',
             r'previews/GO_0xxx/GO_0016/SL9/\1G_thumb.jpg',
             r'documents/GO_0xxx/*.[!lz]*'
            ]),

    (r'.*volumes/GO_0xxx/GO_0016/SL9/(C\d{10})G\.(IMG|LBL)', 0,
            [r'volumes/GO_0xxx/GO_0016/SL9/\1R.IMG',
             r'volumes/GO_0xxx/GO_0016/SL9/\1R.LBL',
             r'previews/GO_0xxx/GO_0016/SL9/\1R_full.jpg',
             r'previews/GO_0xxx/GO_0016/SL9/\1R_med.jpg',
             r'previews/GO_0xxx/GO_0016/SL9/\1R_small.jpg',
             r'previews/GO_0xxx/GO_0016/SL9/\1R_thumb.jpg',
            ]),

    # Known duplicates...
    (r'.*/GO_0006/REDO/(C0018062639R).*'   , 0, [r'volumes/GO_0xxx/GO_0002/VENUS/\1.*'  , r'previews/GO_0xxx/GO_0002/VENUS/\1*.jpg'  , r'metadata/GO_0xxx/GO_0002/GO_0???_*.*']),
    (r'.*/GO_0006/REDO/(C0018241745R).*'   , 0, [r'volumes/GO_0xxx/GO_0002/VENUS/\1.*'  , r'previews/GO_0xxx/GO_0002/VENUS/\1*.jpg'  , r'metadata/GO_0xxx/GO_0002/GO_0???_*.*']),
    (r'.*/GO_0006/REDO/(C0018353518R).*'   , 0, [r'volumes/GO_0xxx/GO_0002/VENUS/\1.*'  , r'previews/GO_0xxx/GO_0002/VENUS/\1*.jpg'  , r'metadata/GO_0xxx/GO_0002/GO_0???_*.*']),
    (r'.*/GO_0006/REDO/(C0018518445R).*'   , 0, [r'volumes/GO_0xxx/GO_0002/VENUS/\1.*'  , r'previews/GO_0xxx/GO_0002/VENUS/\1*.jpg'  , r'metadata/GO_0xxx/GO_0002/GO_0???_*.*']),
    (r'.*/GO_0006/REDO/(C0059469700R).*'   , 0, [r'volumes/GO_0xxx/GO_0002/RAW_CAL/\1.*', r'previews/GO_0xxx/GO_0002/RAW_CAL/\1*.jpg', r'metadata/GO_0xxx/GO_0002/GO_0???_*.*']),
    (r'.*/GO_0006/REDO/(C0059471700R).*'   , 0, [r'volumes/GO_0xxx/GO_0002/RAW_CAL/\1.*', r'previews/GO_0xxx/GO_0002/RAW_CAL/\1*.jpg', r'metadata/GO_0xxx/GO_0002/GO_0???_*.*']),
    (r'.*/GO_0006/REDO/(C0060964000R).*'   , 0, [r'volumes/GO_0xxx/GO_0003/MOON/\1.*'   , r'previews/GO_0xxx/GO_0003/MOON/\1*.jpg'   , r'metadata/GO_0xxx/GO_0003/GO_0???_*.*']),
    (r'.*/GO_0006/REDO/(C0061078900R).*'   , 0, [r'volumes/GO_0xxx/GO_0004/EARTH/\1.*'  , r'previews/GO_0xxx/GO_0004/EARTH/\1*.jpg'  , r'metadata/GO_0xxx/GO_0004/GO_0???_*.*']),
    (r'.*/GO_0006/REDO/(C0061116.00R).*'   , 0, [r'volumes/GO_0xxx/GO_0004/MOON/\1.*'   , r'previews/GO_0xxx/GO_0004/MOON/\1*.jpg'   , r'metadata/GO_0xxx/GO_0004/GO_0???_*.*']),
    (r'.*/GO_0006/REDO/(C0061424500R).*'   , 0, [r'volumes/GO_0xxx/GO_0004/EARTH/\1.*'  , r'previews/GO_0xxx/GO_0004/EARTH/\1*.jpg'  , r'metadata/GO_0xxx/GO_0004/GO_0???_*.*']),
    (r'.*/GO_0006/REDO/(C0061441500R).*'   , 0, [r'volumes/GO_0xxx/GO_0004/EARTH/\1.*'  , r'previews/GO_0xxx/GO_0004/EARTH/\1*.jpg'  , r'metadata/GO_0xxx/GO_0004/GO_0???_*.*']),
    (r'.*/GO_0006/REDO/(C0061469100R).*'   , 0, [r'volumes/GO_0xxx/GO_0005/EARTH/\1.*'  , r'previews/GO_0xxx/GO_0005/EARTH/\1*.jpg'  , r'metadata/GO_0xxx/GO_0005/GO_0???_*.*']),
    (r'.*/GO_0006/REDO/(C006150..00R).*'   , 0, [r'volumes/GO_0xxx/GO_0005/EARTH/\1.*'  , r'previews/GO_0xxx/GO_0005/EARTH/\1*.jpg'  , r'metadata/GO_0xxx/GO_0005/GO_0???_*.*']),
    (r'.*/GO_0006/REDO/(C006151..00R).*'   , 0, [r'volumes/GO_0xxx/GO_0005/EARTH/\1.*'  , r'previews/GO_0xxx/GO_0005/EARTH/\1*.jpg'  , r'metadata/GO_0xxx/GO_0005/GO_0???_*.*']),
    (r'.*/GO_0006/REDO/(C006152..00R).*'   , 0, [r'volumes/GO_0xxx/GO_0005/EARTH/\1.*'  , r'previews/GO_0xxx/GO_0005/EARTH/\1*.jpg'  , r'metadata/GO_0xxx/GO_0005/GO_0???_*.*']),
    (r'.*/GO_0006/REDO/(C006153..00R).*'   , 0, [r'volumes/GO_0xxx/GO_0005/EARTH/\1.*'  , r'previews/GO_0xxx/GO_0005/EARTH/\1*.jpg'  , r'metadata/GO_0xxx/GO_0005/GO_0???_*.*']),
    (r'.*/GO_0006/REDO/(C0061542500R).*'   , 0, [r'volumes/GO_0xxx/GO_0006/EARTH/\1.*'  , r'previews/GO_0xxx/GO_0006/EARTH/\1*.jpg'  , r'metadata/GO_0xxx/GO_0006/GO_0???_*.*']),
    (r'.*/GO_0015/REDO/(C0165242700R).*'   , 0, [r'volumes/GO_0xxx/GO_0012/EARTH/\1.*'  , r'previews/GO_0xxx/GO_0012/EARTH/\1*.jpg'  , r'metadata/GO_0xxx/GO_0012/GO_0???_*.*']),

    (r'.*/GO_0002/VENUS/(C0018062639R).*'  , 0, [r'volumes/GO_0xxx/GO_0006/REDO/\1.*', r'previews/GO_0xxx/GO_0006/REDO/\1*.jpg', r'metadata/GO_0xxx/GO_0006/GO_0???_*.*']),
    (r'.*/GO_0002/VENUS/(C0018241745R).*'  , 0, [r'volumes/GO_0xxx/GO_0006/REDO/\1.*', r'previews/GO_0xxx/GO_0006/REDO/\1*.jpg', r'metadata/GO_0xxx/GO_0006/GO_0???_*.*']),
    (r'.*/GO_0002/VENUS/(C0018353518R).*'  , 0, [r'volumes/GO_0xxx/GO_0006/REDO/\1.*', r'previews/GO_0xxx/GO_0006/REDO/\1*.jpg', r'metadata/GO_0xxx/GO_0006/GO_0???_*.*']),
    (r'.*/GO_0002/VENUS/(C0018518445R).*'  , 0, [r'volumes/GO_0xxx/GO_0006/REDO/\1.*', r'previews/GO_0xxx/GO_0006/REDO/\1*.jpg', r'metadata/GO_0xxx/GO_0006/GO_0???_*.*']),
    (r'.*/GO_0002/RAW_CAL/(C0059469700R).*', 0, [r'volumes/GO_0xxx/GO_0006/REDO/\1.*', r'previews/GO_0xxx/GO_0006/REDO/\1*.jpg', r'metadata/GO_0xxx/GO_0006/GO_0???_*.*']),
    (r'.*/GO_0002/RAW_CAL/(C0059471700R).*', 0, [r'volumes/GO_0xxx/GO_0006/REDO/\1.*', r'previews/GO_0xxx/GO_0006/REDO/\1*.jpg', r'metadata/GO_0xxx/GO_0006/GO_0???_*.*']),
    (r'.*/GO_0003/MOON/(C0060964000R).*'   , 0, [r'volumes/GO_0xxx/GO_0006/REDO/\1.*', r'previews/GO_0xxx/GO_0006/REDO/\1*.jpg', r'metadata/GO_0xxx/GO_0006/GO_0???_*.*']),
    (r'.*/GO_0004/EARTH/(C0061078900R).*'  , 0, [r'volumes/GO_0xxx/GO_0006/REDO/\1.*', r'previews/GO_0xxx/GO_0006/REDO/\1*.jpg', r'metadata/GO_0xxx/GO_0006/GO_0???_*.*']),
    (r'.*/GO_0004/MOON/(C0061116.00R).*'   , 0, [r'volumes/GO_0xxx/GO_0006/REDO/\1.*', r'previews/GO_0xxx/GO_0006/REDO/\1*.jpg', r'metadata/GO_0xxx/GO_0006/GO_0???_*.*']),
    (r'.*/GO_0004/EARTH/(C0061424500R).*'  , 0, [r'volumes/GO_0xxx/GO_0006/REDO/\1.*', r'previews/GO_0xxx/GO_0006/REDO/\1*.jpg', r'metadata/GO_0xxx/GO_0006/GO_0???_*.*']),
    (r'.*/GO_0004/EARTH/(C0061441500R).*'  , 0, [r'volumes/GO_0xxx/GO_0006/REDO/\1.*', r'previews/GO_0xxx/GO_0006/REDO/\1*.jpg', r'metadata/GO_0xxx/GO_0006/GO_0???_*.*']),
    (r'.*/GO_0005/EARTH/(C0061469100R).*'  , 0, [r'volumes/GO_0xxx/GO_0006/REDO/\1.*', r'previews/GO_0xxx/GO_0006/REDO/\1*.jpg', r'metadata/GO_0xxx/GO_0006/GO_0???_*.*']),
    (r'.*/GO_0005/EARTH/(C006150..00R).*'  , 0, [r'volumes/GO_0xxx/GO_0006/REDO/\1.*', r'previews/GO_0xxx/GO_0006/REDO/\1*.jpg', r'metadata/GO_0xxx/GO_0006/GO_0???_*.*']),
    (r'.*/GO_0005/EARTH/(C006151..00R).*'  , 0, [r'volumes/GO_0xxx/GO_0006/REDO/\1.*', r'previews/GO_0xxx/GO_0006/REDO/\1*.jpg', r'metadata/GO_0xxx/GO_0006/GO_0???_*.*']),
    (r'.*/GO_0005/EARTH/(C006152..00R).*'  , 0, [r'volumes/GO_0xxx/GO_0006/REDO/\1.*', r'previews/GO_0xxx/GO_0006/REDO/\1*.jpg', r'metadata/GO_0xxx/GO_0006/GO_0???_*.*']),
    (r'.*/GO_0005/EARTH/(C006153..00R).*'  , 0, [r'volumes/GO_0xxx/GO_0006/REDO/\1.*', r'previews/GO_0xxx/GO_0006/REDO/\1*.jpg', r'metadata/GO_0xxx/GO_0006/GO_0???_*.*']),
    (r'.*/GO_0006/EARTH/(C0061542500R).*'  , 0, [r'volumes/GO_0xxx/GO_0006/REDO/\1.*', r'previews/GO_0xxx/GO_0006/REDO/\1*.jpg', r'metadata/GO_0xxx/GO_0006/GO_0???_*.*']),
    (r'.*/GO_0012/EARTH/(C0165242700R).*'  , 0, [r'volumes/GO_0xxx/GO_0015/REDO/\1.*', r'previews/GO_0xxx/GO_0015/REDO/\1*.jpg', r'metadata/GO_0xxx/GO_0015/GO_0???_*.*']),

    (r'.*/GO_0018/REDO/(C3/JUPITER/C036897..00R).*', 0, [r'volumes/GO_0xxx/GO_0017/\1.*', r'previews/GO_0xxx/GO_0017/\1*.jpg', r'metadata/GO_0xxx/GO_0017/GO_0???_*.*']),
    (r'.*/GO_0018/REDO/(C3/JUPITER/C036898..00R).*', 0, [r'volumes/GO_0xxx/GO_0017/\1.*', r'previews/GO_0xxx/GO_0017/\1*.jpg', r'metadata/GO_0xxx/GO_0017/GO_0???_*.*']),
    (r'.*/GO_0018/REDO/(C3/JUPITER/C036899..00R).*', 0, [r'volumes/GO_0xxx/GO_0017/\1.*', r'previews/GO_0xxx/GO_0017/\1*.jpg', r'metadata/GO_0xxx/GO_0017/GO_0???_*.*']),
    (r'.*/GO_0019/REDO/(C3/EUROPA/C0368976...R).*' , 0, [r'volumes/GO_0xxx/GO_0017/\1.*', r'previews/GO_0xxx/GO_0017/\1*.jpg', r'metadata/GO_0xxx/GO_0017/GO_0???_*.*']),
    (r'.*/GO_0019/REDO/(C3/JUPITER/C0368369268R).*', 0, [r'volumes/GO_0xxx/GO_0017/\1.*', r'previews/GO_0xxx/GO_0017/\1*.jpg', r'metadata/GO_0xxx/GO_0017/GO_0???_*.*']),
    (r'.*/GO_0019/REDO/(C3/JUPITER/C0368441600R).*', 0, [r'volumes/GO_0xxx/GO_0017/\1.*', r'previews/GO_0xxx/GO_0017/\1*.jpg', r'metadata/GO_0xxx/GO_0017/GO_0???_*.*']),
    (r'.*/GO_0019/REDO/(E4/EUROPA/C0374667300R).*' , 0, [r'volumes/GO_0xxx/GO_0018/\1.*', r'previews/GO_0xxx/GO_0018/\1*.jpg', r'metadata/GO_0xxx/GO_0018/GO_0???_*.*']),
    (r'.*/GO_0019/REDO/(E6/IO/C0383655111R).*'     , 0, [r'volumes/GO_0xxx/GO_0018/\1.*', r'previews/GO_0xxx/GO_0018/\1*.jpg', r'metadata/GO_0xxx/GO_0018/GO_0???_*.*']),

    (r'.*/GO_0017/(C3/JUPITER/C036897..00R).*'     , 0, [r'volumes/GO_0xxx/GO_0018/REDO/\1.*', r'previews/GO_0xxx/GO_0018/REDO/\1*.jpg', r'metadata/GO_0xxx/GO_0018/GO_0???_*.*']),
    (r'.*/GO_0017/(C3/JUPITER/C036898..00R).*'     , 0, [r'volumes/GO_0xxx/GO_0018/REDO/\1.*', r'previews/GO_0xxx/GO_0018/REDO/\1*.jpg', r'metadata/GO_0xxx/GO_0018/GO_0???_*.*']),
    (r'.*/GO_0017/(C3/JUPITER/C036899..00R).*'     , 0, [r'volumes/GO_0xxx/GO_0018/REDO/\1.*', r'previews/GO_0xxx/GO_0018/REDO/\1*.jpg', r'metadata/GO_0xxx/GO_0018/GO_0???_*.*']),
    (r'.*/GO_0017/(C3/EUROPA/C0368976...R).*'      , 0, [r'volumes/GO_0xxx/GO_0019/REDO/\1.*', r'previews/GO_0xxx/GO_0019/REDO/\1*.jpg', r'metadata/GO_0xxx/GO_0019/GO_0???_*.*']),
    (r'.*/GO_0017/(C3/JUPITER/C0368369268R).*'     , 0, [r'volumes/GO_0xxx/GO_0019/REDO/\1.*', r'previews/GO_0xxx/GO_0019/REDO/\1*.jpg', r'metadata/GO_0xxx/GO_0019/GO_0???_*.*']),
    (r'.*/GO_0017/(C3/JUPITER/C0368441600R).*'     , 0, [r'volumes/GO_0xxx/GO_0019/REDO/\1.*', r'previews/GO_0xxx/GO_0019/REDO/\1*.jpg', r'metadata/GO_0xxx/GO_0019/GO_0???_*.*']),
    (r'.*/GO_0018/(E4/EUROPA/C0374667300R).*'      , 0, [r'volumes/GO_0xxx/GO_0019/REDO/\1.*', r'previews/GO_0xxx/GO_0019/REDO/\1*.jpg', r'metadata/GO_0xxx/GO_0019/GO_0???_*.*']),
    (r'.*/GO_0018/(E6/IO/C0383655111R).*'          , 0, [r'volumes/GO_0xxx/GO_0019/REDO/\1.*', r'previews/GO_0xxx/GO_0019/REDO/\1*.jpg', r'metadata/GO_0xxx/GO_0019/GO_0???_*.*']),

    (r'.*/GO_0020/E12/TIRETRACK/(C04262728..)S.*'  , 0, [r'volumes/GO_0xxx/GO_0020/E12/EUROPA/\1R.*'    , r'previews/GO_0xxx/GO_0020/E12/EUROPA/\1*.jpg'    , r'metadata/GO_0xxx/GO_0020/GO_0???_*.*']),
    (r'.*/GO_0022/I24/IO/REPAIRED/(C052079....)S.*', 0, [r'volumes/GO_0xxx/GO_0022/I24/IO/GARBLED/\1R.*', r'previews/GO_0xxx/GO_0022/I24/IO/GARBLED/\1*.jpg', r'metadata/GO_0xxx/GO_0022/GO_0???_*.*']),
    (r'.*/GO_0022/I24/IO/REPAIRED/(C052080630.)S.*', 0, [r'volumes/GO_0xxx/GO_0022/I24/IO/GARBLED/\1R.*', r'previews/GO_0xxx/GO_0022/I24/IO/GARBLED/\1*.jpg', r'metadata/GO_0xxx/GO_0022/GO_0???_*.*']),
    (r'.*/GO_0023/G28/REPAIRED/(C0552447569)S.*'   , 0, [r'volumes/GO_0xxx/GO_0023/G28/GARBLED/\1R.*'   , r'previews/GO_0xxx/GO_0023/G28/GARBLED/\1*.jpg'   , r'metadata/GO_0xxx/GO_0023/GO_0???_*.*']),
    (r'.*/GO_0023/G29/REPAIRED/(C060049....)S.*'   , 0, [r'volumes/GO_0xxx/GO_0023/G29/GARBLED/\1R.*'   , r'previews/GO_0xxx/GO_0023/G29/GARBLED/\1*.jpg'   , r'metadata/GO_0xxx/GO_0023/GO_0???_*.*']),
    (r'.*/GO_0023/G29/REPAIRED/(C060066....)S.*'   , 0, [r'volumes/GO_0xxx/GO_0023/G29/GARBLED/\1R.*'   , r'previews/GO_0xxx/GO_0023/G29/GARBLED/\1*.jpg'   , r'metadata/GO_0xxx/GO_0023/GO_0???_*.*']),

    (r'.*/GO_0020/E12/EUROPA/(C04262728..)R.*'     , 0, [r'volumes/GO_0xxx/GO_0020/E12/TIRETRACK/\1S.*'  , r'previews/GO_0xxx/GO_0020/E12/TIRETRACK/\1*.jpg'  , r'metadata/GO_0xxx/GO_0020/GO_0???_*.*']),
    (r'.*/GO_0022/I24/IO/GARBLED/(C052079....)R.*' , 0, [r'volumes/GO_0xxx/GO_0022/I24/IO/REPAIRED/\1S.*', r'previews/GO_0xxx/GO_0022/I24/IO/REPAIRED/\1*.jpg', r'metadata/GO_0xxx/GO_0022/GO_0???_*.*']),
    (r'.*/GO_0022/I24/IO/GARBLED/(C052080630.)R.*' , 0, [r'volumes/GO_0xxx/GO_0022/I24/IO/REPAIRED/\1S.*', r'previews/GO_0xxx/GO_0022/I24/IO/REPAIRED/\1*.jpg', r'metadata/GO_0xxx/GO_0022/GO_0???_*.*']),
    (r'.*/GO_0023/G28/GARBLED/(C0552447569)R.*'    , 0, [r'volumes/GO_0xxx/GO_0023/G28/REPAIRED/\1S.*'   , r'previews/GO_0xxx/GO_0023/G28/REPAIRED/\1*.jpg'   , r'metadata/GO_0xxx/GO_0023/GO_0???_*.*']),
    (r'.*/GO_0023/G29/GARBLED/(C060049....)R.*'    , 0, [r'volumes/GO_0xxx/GO_0023/G29/REPAIRED/\1S.*'   , r'previews/GO_0xxx/GO_0023/G29/REPAIRED/\1*.jpg'   , r'metadata/GO_0xxx/GO_0023/GO_0???_*.*']),
    (r'.*/GO_0023/G29/GARBLED/(C060066....)R.*'    , 0, [r'volumes/GO_0xxx/GO_0023/G29/REPAIRED/\1S.*'   , r'previews/GO_0xxx/GO_0023/G29/REPAIRED/\1*.jpg'   , r'metadata/GO_0xxx/GO_0023/GO_0???_*.*']),
])

##########################################################################################
# OPUS_ID
##########################################################################################

opus_id = translator.TranslatorByRegex([
    (r'.*/GO_0xxx/GO_00../.*/C(\d{10})[A-Z]\.(IMG|LBL)', 0, r'go-ssi-c\1'),
])

##########################################################################################
# OPUS_ID_TO_PRIMARY_LOGICAL_PATH
##########################################################################################

# Note: Lists are sorted to make sure that the preferred REDO/REPAIRED/TIRETRACK match comes first
opus_id_to_primary_logical_path = translator.TranslatorByRegex([
    (r'go-ssi-c(000.*)'       , 0,  r'volumes/GO_0xxx/GO_0002/*/C\1R.IMG'),
    (r'go-ssi-c(001.*)'       , 0, [r'volumes/GO_0xxx/GO_0006/REDO/C\1R.IMG',
                                    r'volumes/GO_0xxx/GO_0002/*/C\1R.IMG']),
    (r'go-ssi-c(005.*)'       , 0, [r'volumes/GO_0xxx/GO_000[67]/REDO/C\1R.IMG',
                                    r'volumes/GO_0xxx/GO_000[23]/*/C\1R.IMG']),
    (r'go-ssi-c(0060.*)'      , 0, [r'volumes/GO_0xxx/GO_0006/REDO/C\1R.IMG',
                                    r'volumes/GO_0xxx/GO_0003/*/C\1R.IMG']),
    (r'go-ssi-c(0061[0-3].*)' , 0, [r'volumes/GO_0xxx/GO_0006/REDO/C\1R.IMG',
                                    r'volumes/GO_0xxx/GO_000[34]/*/C\1R.IMG']),
    (r'go-ssi-c(00614.*)'     , 0, [r'volumes/GO_0xxx/GO_0006/REDO/C\1R.IMG',
                                    r'volumes/GO_0xxx/GO_000[45]/*/C\1R.IMG']),
    (r'go-ssi-c(00615[0-2].*)', 0, [r'volumes/GO_0xxx/GO_0006/REDO/C\1R.IMG',
                                    r'volumes/GO_0xxx/GO_0005/*/C\1R.IMG']),
    (r'go-ssi-c(006153.*)'    , 0, [r'volumes/GO_0xxx/GO_0006/REDO/C\1R.IMG',
                                    r'volumes/GO_0xxx/GO_0005/*/C\1R.IMG',
                                    r'volumes/GO_0xxx/GO_0006/EARTH/C\1R.IMG']),
    (r'go-ssi-c(006154.*)'    , 0, [r'volumes/GO_0xxx/GO_0006/REDO/C\1R.IMG',
                                    r'volumes/GO_0xxx/GO_0006/EARTH/C\1R.IMG']),
    (r'go-ssi-c(00615[5-9].*)', 0,  r'volumes/GO_0xxx/GO_0006/*/C\1R.IMG'),
    (r'go-ssi-c(0061[6-9].*)' , 0,  r'volumes/GO_0xxx/GO_0006/*/C\1R.IMG'),
    (r'go-ssi-c(006[2-9].*)'  , 0,  r'volumes/GO_0xxx/GO_0006/*/C\1R.IMG'),
    (r'go-ssi-c(00[7-9].*)'   , 0,  r'volumes/GO_0xxx/GO_0007/*/C\1R.IMG'),
    (r'go-ssi-c(01[0-5].*)'   , 0,  r'volumes/GO_0xxx/GO_0007/*/C\1R.IMG'),
    (r'go-ssi-c(0163.*)'      , 0,  r'volumes/GO_0xxx/GO_0007/*/C\1R.IMG'),
    (r'go-ssi-c(0164.*)'      , 0,  r'volumes/GO_0xxx/GO_000[789]/*/C\1R.IMG'),
    (r'go-ssi-c(01650.*)'     , 0, [r'volumes/GO_0xxx/GO_0009/*/C\1R.IMG',
                                    r'volumes/GO_0xxx/GO_0010/*/C\1R.IMG']),
    (r'go-ssi-c(01651.*)'     , 0,  r'volumes/GO_0xxx/GO_001[01]/*/C\1R.IMG'),
    (r'go-ssi-c(016520.*)'    , 0,  r'volumes/GO_0xxx/GO_001[12]/*/C\1R.IMG'),
    (r'go-ssi-c(01652[1-3].*)', 0,  r'volumes/GO_0xxx/GO_0012/*/C\1R.IMG'),
    (r'go-ssi-c(016524.*)'    , 0, [r'volumes/GO_0xxx/GO_0015/REDO/C\1R.IMG',
                                    r'volumes/GO_0xxx/GO_001[23]/*/C\1R.IMG']),
    (r'go-ssi-c(01652[5-9].*)', 0,  r'volumes/GO_0xxx/GO_0013/*/C\1R.IMG'),
    (r'go-ssi-c(01653[01].*)' , 0,  r'volumes/GO_0xxx/GO_0013/*/C\1R.IMG'),
    (r'go-ssi-c(016532.*)'    , 0,  r'volumes/GO_0xxx/GO_001[34]/*/C\1R.IMG'),
    (r'go-ssi-c(01653[3-9].*)', 0,  r'volumes/GO_0xxx/GO_0014/*/C\1R.IMG'),
    (r'go-ssi-c(016540.*)'    , 0,  r'volumes/GO_0xxx/GO_0014/*/C\1R.IMG'),
    (r'go-ssi-c(016541.*)'    , 0,  r'volumes/GO_0xxx/GO_001[45]/*/C\1R.IMG'),
    (r'go-ssi-c(01654[2-9].*)', 0,  r'volumes/GO_0xxx/GO_0015/*/C\1R.IMG'),
    (r'go-ssi-c(0165[5-9].*)' , 0,  r'volumes/GO_0xxx/GO_0015/*/C\1R.IMG'),
    (r'go-ssi-c(016[6-9].*)'  , 0,  r'volumes/GO_0xxx/GO_0015/*/C\1R.IMG'),
    (r'go-ssi-c(01[7-9].*)'   , 0,  r'volumes/GO_0xxx/GO_0016/*/C\1R.IMG'),
    (r'go-ssi-c(02.*)'        , 0,  r'volumes/GO_0xxx/GO_0016/*/C\1R.IMG'),

    (r'go-ssi-c(03[0-5].*)'   , 0, [r'volumes/GO_0xxx/GO_0017/??/*/C\1R.IMG']),
    (r'go-ssi-c(036.*)'       , 0, [r'volumes/GO_0xxx/GO_0019/REDO/??/*/C\1R.IMG',
                                    r'volumes/GO_0xxx/GO_0018/REDO/??/*/C\1R.IMG',
                                    r'volumes/GO_0xxx/GO_0017/??/*/C\1R.IMG',
                                    r'volumes/GO_0xxx/GO_0018/??/*/C\1R.IMG']),
    (r'go-ssi-c(037.*)'       , 0, [r'volumes/GO_0xxx/GO_0019/REDO/??/*/C\1R.IMG',
                                    r'volumes/GO_0xxx/GO_0018/REDO/??/*/C\1R.IMG',
                                    r'volumes/GO_0xxx/GO_0017/??/*/C\1R.IMG',
                                    r'volumes/GO_0xxx/GO_0018/??/*/C\1R.IMG']),
    (r'go-ssi-c(038.*)'       , 0, [r'volumes/GO_0xxx/GO_0019/REDO/??/*/C\1R.IMG',
                                    r'volumes/GO_0xxx/GO_0018/REDO/??/*/C\1R.IMG',
                                    r'volumes/GO_0xxx/GO_0018/??/*/C\1R.IMG']),
    (r'go-ssi-c(039.*)'       , 0, [r'volumes/GO_0xxx/GO_0019/??/*/C\1R.IMG']),
    (r'go-ssi-c(040.*)'       , 0, [r'volumes/GO_0xxx/GO_0019/??/*/C\1R.IMG',
                                    r'volumes/GO_0xxx/GO_0019/???/*/C\1R.IMG']),
    (r'go-ssi-c(041.*)'       , 0, [r'volumes/GO_0xxx/GO_0019/???/*/C\1R.IMG']),
    (r'go-ssi-c(04[2-6].*)'   , 0, [r'volumes/GO_0xxx/GO_0023/REDO/E11/*/C\1R.IMG',
                                    r'volumes/GO_0xxx/GO_0020/???/TIRETRACK/C\1S.IMG',
                                    r'volumes/GO_0xxx/GO_0020/???/[A-SU-Z]*/C\1R.IMG']),
    (r'go-ssi-c(04[7-9].*)'   , 0, [r'volumes/GO_0xxx/GO_0021/???/*/C\1R.IMG']),
    (r'go-ssi-c(05[0-1].*)'   , 0, [r'volumes/GO_0xxx/GO_0021/???/*/C\1R.IMG']),
    (r'go-ssi-c(052.*)'       , 0, [r'volumes/GO_0xxx/GO_0022/???/*/REPAIRED/C\1S.IMG',
                                    r'volumes/GO_0xxx/GO_0022/???/*/C\1R.IMG',
                                    r'volumes/GO_0xxx/GO_0022/???/*/GARBLED/C\1R.IMG']),
    (r'go-ssi-c(05[3-9].*)'   , 0, [r'volumes/GO_0xxx/GO_0023/G28/REPAIRED/C\1S.IMG',
                                    r'volumes/GO_0xxx/GO_0023/???/*/C\1R.IMG']),
    (r'go-ssi-c(06.*)'        , 0, [r'volumes/GO_0xxx/GO_0023/???/REPAIRED/C\1S.IMG',
                                    r'volumes/GO_0xxx/GO_0023/???/[A-FH-QS-Z]*/C\1R.IMG',
                                    r'volumes/GO_0xxx/GO_0023/???/R[AIOU]*/C\1R.IMG',
                                    r'volumes/GO_0xxx/GO_0023/???/GANYMEDE/C\1R.IMG',
                                    r'volumes/GO_0xxx/GO_0023/???/GARBLED/C\1R.IMG']),
])

##########################################################################################
# Subclass definition
##########################################################################################

class GO_0xxx(pds3file.Pds3File):

    pds3file.Pds3File.VOLSET_TRANSLATOR = translator.TranslatorByRegex([('GO_0xxx', re.I, 'GO_0xxx')]) + \
                                          pds3file.Pds3File.VOLSET_TRANSLATOR

    DESCRIPTION_AND_ICON = description_and_icon_by_regex + pds3file.Pds3File.DESCRIPTION_AND_ICON
    VIEW_OPTIONS = view_options + pds3file.Pds3File.VIEW_OPTIONS
    NEIGHBORS = neighbors + pds3file.Pds3File.NEIGHBORS
    SORT_KEY = sort_key + pds3file.Pds3File.SORT_KEY
    SPLIT_RULES = split_rules + pds3file.Pds3File.SPLIT_RULES

    OPUS_TYPE = opus_type + pds3file.Pds3File.OPUS_TYPE
    OPUS_FORMAT = opus_format + pds3file.Pds3File.OPUS_FORMAT
    OPUS_PRODUCTS = opus_products + pds3file.Pds3File.OPUS_PRODUCTS
    OPUS_ID = opus_id
    OPUS_ID_TO_PRIMARY_LOGICAL_PATH = opus_id_to_primary_logical_path

    VIEWABLES = {'default': default_viewables}

    ASSOCIATIONS = pds3file.Pds3File.ASSOCIATIONS.copy()
    ASSOCIATIONS['volumes']  += associations_to_volumes
    ASSOCIATIONS['previews'] += associations_to_previews
    ASSOCIATIONS['metadata'] += associations_to_metadata
    ASSOCIATIONS['documents'] += associations_to_documents

    VERSIONS = versions + pds3file.Pds3File.VERSIONS

    FILENAME_KEYLEN = 11    # trim off suffixes

    # Given a metadata path, this returns the same path but with "$" replacing
    # the volume IDs. Used by opus_prioritizer.
    METADATA_PATH_TRANSLATOR = translator.TranslatorByRegex([
        (r'(.*metadata/GO_0xxx)(|_v[0-9\.]+)/(GO_00..)/\3_(.*)', 0, r'\1\2/$/$_\4')
    ])

    def opus_prioritizer(self, pdsfile_dict):
        """Prioritize products that have been processed more than once."""

        headers = list(pdsfile_dict.keys())     # Save keys so we can alter dict
        for header in headers:
            sublists = pdsfile_dict[header]
            if len(sublists) == 1:
                continue

            # Only prioritize data products
            if sublists[0][0].voltype_ != 'volumes/':
                continue

            # Split up the sublists by version rank (not currently needed)
            rank_dict = {}
            for sublist in sublists:
                rank = sublist[0].version_rank
                if rank not in rank_dict:
                    rank_dict[rank] = []
                rank_dict[rank].append(sublist)

            # Sort the version ranks
            ranks = list(rank_dict.keys())
            ranks.sort()
            ranks.reverse()

            # Define the alternative header
            alt_header = (header[0], header[1] + 10,
                                     header[2] + '_alternate',
                                     header[3] + ' (Superseded Processing)',
                                     True)
            pdsfile_dict[alt_header] = []
            pdsfile_dict[header] = []

            # Sort items by priority among each available version
            for rank in ranks:
                prioritizer = []    # (priority from path, sublist)

                for sublist in rank_dict[rank]:
                    abspath = sublist[0].abspath
                    prio = 1
                    if 'TIRETRACK' in abspath: prio = 0
                    if 'REPAIRED' in abspath: prio = 0
                    if 'REDO' in abspath: prio = 0

                    prioritizer.append((prio, sublist))

                prioritizer.sort()

                # Update the dictionary for each rank
                pdsfile_dict[header].append(prioritizer[0][-1])
                pdsfile_dict[alt_header] += [p[-1] for p in prioritizer[1:]]

        return pdsfile_dict

# Global attribute shared by all subclasses
pds3file.Pds3File.OPUS_ID_TO_SUBCLASS = translator.TranslatorByRegex([(r'go-ssi-.*', 0, GO_0xxx)]) + \
                                        pds3file.Pds3File.OPUS_ID_TO_SUBCLASS

##########################################################################################
# Update the global dictionary of subclasses
##########################################################################################

pds3file.Pds3File.SUBCLASSES['GO_0xxx'] = GO_0xxx

##########################################################################################
# Unit tests
##########################################################################################

import pytest
from .pytest_support import *

@pytest.mark.parametrize(
    'input_path,expected',
    [
        ('volumes/GO_0xxx/GO_0017/J0/OPNAV/C0346405900R.IMG',
         'GO_0xxx/opus_products/C0346405900R.txt')
    ]
)
def test_opus_products(request, input_path, expected):
    update = request.config.option.update
    opus_products_test(pds3file.Pds3File, input_path, TEST_RESULTS_DIR+expected, update)


@pytest.mark.parametrize(
    'input_path,category,expected',
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
    TESTS = [
        'volumes/GO_0xxx/GO_0002/RAW_CAL/C0003061100R.IMG',
        'volumes/GO_0xxx/GO_0002/RAW_CAL/C0011890900R.IMG',
        'volumes/GO_0xxx/GO_0002/RAW_CAL/C0011895526R.IMG',
        'volumes/GO_0xxx/GO_0002/RAW_CAL/C0059335800R.IMG',
        'volumes/GO_0xxx/GO_0002/RAW_CAL/C0059469900R.IMG',
        'volumes/GO_0xxx/GO_0002/VENUS/C0018062600R.IMG',
        'volumes/GO_0xxx/GO_0002/VENUS/C0018077000R.IMG',
        'volumes/GO_0xxx/GO_0002/VENUS/C0018088800R.IMG',
        'volumes/GO_0xxx/GO_0002/VENUS/C0018217000R.IMG',
        'volumes/GO_0xxx/GO_0002/VENUS/C0018244700R.IMG',
        'volumes/GO_0xxx/GO_0002/VENUS/C0019064100R.IMG',
        'volumes/GO_0xxx/GO_0003/EARTH/C0061026045R.IMG',
        'volumes/GO_0xxx/GO_0003/EARTH/C0061026245R.IMG',
        'volumes/GO_0xxx/GO_0003/EARTH/C0061039400R.IMG',
        'volumes/GO_0xxx/GO_0003/EARTH/C0061042645R.IMG',
        'volumes/GO_0xxx/GO_0003/EARTH/C0061042700R.IMG',
        'volumes/GO_0xxx/GO_0003/MOON/C0060959300R.IMG',
        'volumes/GO_0xxx/GO_0003/MOON/C0060997000R.IMG',
        'volumes/GO_0xxx/GO_0003/MOON/C0061000300R.IMG',
        'volumes/GO_0xxx/GO_0003/MOON/C0061030945R.IMG',
        'volumes/GO_0xxx/GO_0003/MOON/C0061043300R.IMG',
        'volumes/GO_0xxx/GO_0003/RAW_CAL/C0059905000R.IMG',
        'volumes/GO_0xxx/GO_0003/RAW_CAL/C0060959145R.IMG',
        'volumes/GO_0xxx/GO_0003/RAW_CAL/C0061026100R.IMG',
        'volumes/GO_0xxx/GO_0003/RAW_CAL/C0061039445R.IMG',
        'volumes/GO_0xxx/GO_0003/RAW_CAL/C0061042600R.IMG',
        'volumes/GO_0xxx/GO_0003/RAW_CAL/C0061042800R.IMG',
        'volumes/GO_0xxx/GO_0004/MOON/C0061399900R.IMG',
        'volumes/GO_0xxx/GO_0004/MOON/C0061400000R.IMG',
        'volumes/GO_0xxx/GO_0005/EARTH/C0061469200R.IMG',
        'volumes/GO_0xxx/GO_0005/EARTH/C0061499900R.IMG',
        'volumes/GO_0xxx/GO_0005/EARTH/C0061500000R.IMG',
        'volumes/GO_0xxx/GO_0006/EARTH/C0061614600R.IMG',
        'volumes/GO_0xxx/GO_0006/MOON/C0061560900R.IMG',
        'volumes/GO_0xxx/GO_0006/MOON/C0061999900R.IMG',
        'volumes/GO_0xxx/GO_0006/MOON/C0062000000R.IMG',
        'volumes/GO_0xxx/GO_0006/RAW_CAL/C0062303500R.IMG',
        'volumes/GO_0xxx/GO_0006/REDO/C0018062639R.IMG',
        'volumes/GO_0xxx/GO_0006/REDO/C0018241745R.IMG',
        'volumes/GO_0xxx/GO_0006/REDO/C0018353518R.IMG',
        'volumes/GO_0xxx/GO_0006/REDO/C0018518445R.IMG',
        'volumes/GO_0xxx/GO_0006/REDO/C0059469700R.IMG',
        'volumes/GO_0xxx/GO_0006/REDO/C0059471700R.IMG',
        'volumes/GO_0xxx/GO_0006/REDO/C0060964000R.IMG',
        'volumes/GO_0xxx/GO_0006/REDO/C0061078900R.IMG',
        'volumes/GO_0xxx/GO_0006/REDO/C0061116600R.IMG',
        'volumes/GO_0xxx/GO_0006/REDO/C0061424500R.IMG',
        'volumes/GO_0xxx/GO_0006/REDO/C0061469100R.IMG',
        'volumes/GO_0xxx/GO_0006/REDO/C0061508200R.IMG',
        'volumes/GO_0xxx/GO_0006/REDO/C0061542500R.IMG',
        'volumes/GO_0xxx/GO_0007/GASPRA/C0107271600R.IMG',
        'volumes/GO_0xxx/GO_0007/GASPRA/C0107318513R.IMG',
        'volumes/GO_0xxx/GO_0007/RAW_CAL/C0099757945R.IMG',
        'volumes/GO_0xxx/GO_0007/RAW_CAL/C0102786545R.IMG',
        'volumes/GO_0xxx/GO_0007/RAW_CAL/C0163288400R.IMG',
        'volumes/GO_0xxx/GO_0007/RAW_CAL/C0163308225R.IMG',
        'volumes/GO_0xxx/GO_0007/RAW_CAL/C0164005700R.IMG',
        'volumes/GO_0xxx/GO_0007/REDO/C0059466445R.IMG',
        'volumes/GO_0xxx/GO_0008/RAW_CAL/C0164532045R.IMG',
        'volumes/GO_0xxx/GO_0009/MOON/C0164997400R.IMG',
        'volumes/GO_0xxx/GO_0009/MOON/C0164999945R.IMG',
        'volumes/GO_0xxx/GO_0009/MOON/C0165000000R.IMG',
        'volumes/GO_0xxx/GO_0010/EARTH/C0165100313R.IMG',
        'volumes/GO_0xxx/GO_0010/EARTH/C0165140700R.IMG',
        'volumes/GO_0xxx/GO_0010/RAW_CAL/C0165099345R.IMG',
        'volumes/GO_0xxx/GO_0011/EARTH/C0165199945R.IMG',
        'volumes/GO_0xxx/GO_0011/EARTH/C0165200000R.IMG',
        'volumes/GO_0xxx/GO_0011/RAW_CAL/C0165162500R.IMG',
        'volumes/GO_0xxx/GO_0012/EARTH/C0165210945R.IMG',
        'volumes/GO_0xxx/GO_0012/EARTH/C0165211000R.IMG',
        'volumes/GO_0xxx/GO_0012/EARTH/C0165239945R.IMG',
        'volumes/GO_0xxx/GO_0012/EARTH/C0165240000R.IMG',
        'volumes/GO_0xxx/GO_0012/GOPEX/C0165233545R.IMG',
        'volumes/GO_0xxx/GO_0013/EARTH/C0165249945R.IMG',
        'volumes/GO_0xxx/GO_0013/EARTH/C0165250000R.IMG',
        'volumes/GO_0xxx/GO_0013/EARTH/C0165299900R.IMG',
        'volumes/GO_0xxx/GO_0013/EARTH/C0165300000R.IMG',
        'volumes/GO_0xxx/GO_0013/EARTH/C0165319900R.IMG',
        'volumes/GO_0xxx/GO_0013/EARTH/C0165320000R.IMG',
        'volumes/GO_0xxx/GO_0013/RAW_CAL/C0165257300R.IMG',
        'volumes/GO_0xxx/GO_0014/EARTH/C0165329900R.IMG',
        'volumes/GO_0xxx/GO_0014/EARTH/C0165330000R.IMG',
        'volumes/GO_0xxx/GO_0014/EARTH/C0165399900R.IMG',
        'volumes/GO_0xxx/GO_0014/EARTH/C0165400000R.IMG',
        'volumes/GO_0xxx/GO_0015/EARTH/C0165470845R.IMG',
        'volumes/GO_0xxx/GO_0015/EMCONJ/C0166236100R.IMG',
        'volumes/GO_0xxx/GO_0015/EMCONJ/C0166318700R.IMG',
        'volumes/GO_0xxx/GO_0015/GOPEX/C0165500300R.IMG',
        'volumes/GO_0xxx/GO_0015/GOPEX/C0165638300R.IMG',
        'volumes/GO_0xxx/GO_0015/GOPEX/C0165930300R.IMG',
        'volumes/GO_0xxx/GO_0015/GOPEX/C0166067000R.IMG',
        'volumes/GO_0xxx/GO_0015/GOPEX/C0166212900R.IMG',
        'volumes/GO_0xxx/GO_0015/RAW_CAL/C0165591200R.IMG',
        'volumes/GO_0xxx/GO_0015/RAW_CAL/C0166324700R.IMG',
        'volumes/GO_0xxx/GO_0015/REDO/C0165242700R.IMG',
        'volumes/GO_0xxx/GO_0016/IDA/C0202530700R.IMG',
        'volumes/GO_0xxx/GO_0016/IDA/C0202562800R.IMG',
        'volumes/GO_0xxx/GO_0016/RAW_CAL/C0197327200R.IMG',
        'volumes/GO_0xxx/GO_0016/RAW_CAL/C0201018800R.IMG',
        'volumes/GO_0xxx/GO_0016/SL9/C0248806645R.IMG',
        'volumes/GO_0xxx/GO_0016/SL9/C0248950600R.IMG',
        'volumes/GO_0xxx/GO_0016/SL9/C0249221800R.IMG',
        'volumes/GO_0xxx/GO_0017/C3/CALLISTO/C0368211900R.IMG',
        'volumes/GO_0xxx/GO_0017/C3/EUROPA/C0368639400R.IMG',
        'volumes/GO_0xxx/GO_0017/C3/IO/C0368558239R.IMG',
        'volumes/GO_0xxx/GO_0017/C3/JUPITER/C0368369200R.IMG',
        'volumes/GO_0xxx/GO_0017/C3/OPNAV/C0372343200R.IMG',
        'volumes/GO_0xxx/GO_0017/C3/RINGS/C0368974113R.IMG',
        'volumes/GO_0xxx/GO_0017/C3/SML_SATS/C0368495800R.IMG',
        'volumes/GO_0xxx/GO_0017/G1/EUROPA/C0349875100R.IMG',
        'volumes/GO_0xxx/GO_0017/G1/GANYMEDE/C0349632000R.IMG',
        'volumes/GO_0xxx/GO_0017/G1/IO/C0349542152R.IMG',
        'volumes/GO_0xxx/GO_0017/G1/IO/C0350013800R.IMG',
        'volumes/GO_0xxx/GO_0017/G1/JUPITER/C0349605600R.IMG',
        'volumes/GO_0xxx/GO_0017/G1/OPNAV/C0356000600R.IMG',
        'volumes/GO_0xxx/GO_0017/G2/CALLISTO/C0360198468R.IMG',
        'volumes/GO_0xxx/GO_0017/G2/EUROPA/C0360063900R.IMG',
        'volumes/GO_0xxx/GO_0017/G2/GANYMEDE/C0359942400R.IMG',
        'volumes/GO_0xxx/GO_0017/G2/IO/C0359402500R.IMG',
        'volumes/GO_0xxx/GO_0017/G2/JUPITER/C0359509200R.IMG',
        'volumes/GO_0xxx/GO_0017/G2/OPNAV/C0359251000R.IMG',
        'volumes/GO_0xxx/GO_0017/G2/OPNAV/C0364621700R.IMG',
        'volumes/GO_0xxx/GO_0017/G2/RAW_CAL/C0360361122R.IMG',
        'volumes/GO_0xxx/GO_0017/G2/SML_SATS/C0360025813R.IMG',
        'volumes/GO_0xxx/GO_0017/J0/OPNAV/C0346405900R.IMG',
        'volumes/GO_0xxx/GO_0018/E4/EUROPA/C0374649000R.IMG',
        'volumes/GO_0xxx/GO_0018/E4/IO/C0374478045R.IMG',
        'volumes/GO_0xxx/GO_0018/E4/JUPITER/C0374456522R.IMG',
        'volumes/GO_0xxx/GO_0018/E4/OPNAV/C0382058200R.IMG',
        'volumes/GO_0xxx/GO_0018/E4/SML_SATS/C0374546000R.IMG',
        'volumes/GO_0xxx/GO_0018/E6/CALLISTO/C0383944100R.IMG',
        'volumes/GO_0xxx/GO_0018/E6/EUROPA/C0383694600R.IMG',
        'volumes/GO_0xxx/GO_0018/E6/GANYMEDE/C0383768868R.IMG',
        'volumes/GO_0xxx/GO_0018/E6/IO/C0383490245R.IMG',
        'volumes/GO_0xxx/GO_0018/E6/JUPITER/C0383548622R.IMG',
        'volumes/GO_0xxx/GO_0018/E6/OPNAV/C0388834700R.IMG',
        'volumes/GO_0xxx/GO_0018/E6/SML_SATS/C0383612800R.IMG',
        'volumes/GO_0xxx/GO_0018/G7/CALLISTO/C0389556200R.IMG',
        'volumes/GO_0xxx/GO_0018/G7/EUROPA/C0389522100R.IMG',
        'volumes/GO_0xxx/GO_0018/G7/GANYMEDE/C0389917900R.IMG',
        'volumes/GO_0xxx/GO_0018/G7/IO/C0389608268R.IMG',
        'volumes/GO_0xxx/GO_0018/G7/JUPITER/C0389557000R.IMG',
        'volumes/GO_0xxx/GO_0018/G7/OPNAV/C0389266100R.IMG',
        'volumes/GO_0xxx/GO_0018/G7/SML_SATS/C0389705600R.IMG',
        'volumes/GO_0xxx/GO_0018/REDO/C3/JUPITER/C0368977800R.IMG',
        'volumes/GO_0xxx/GO_0019/C10/CALLISTO/C0413382800R.IMG',
        'volumes/GO_0xxx/GO_0019/C9/CALLISTO/C0401505300R.IMG',
        'volumes/GO_0xxx/GO_0019/C9/EUROPA/C0401727700R.IMG',
        'volumes/GO_0xxx/GO_0019/C9/GANYMEDE/C0401668900R.IMG',
        'volumes/GO_0xxx/GO_0019/C9/IO/C0401704700R.IMG',
        'volumes/GO_0xxx/GO_0019/C9/JUPITER/C0401571845R.IMG',
        'volumes/GO_0xxx/GO_0019/C9/RAW_CAL/C0404187800R.IMG',
        'volumes/GO_0xxx/GO_0019/C9/SML_SATS/C0401604400R.IMG',
        'volumes/GO_0xxx/GO_0019/G8/CALLISTO/C0394364268R.IMG',
        'volumes/GO_0xxx/GO_0019/G8/GANYMEDE/C0394517800R.IMG',
        'volumes/GO_0xxx/GO_0019/G8/IO/C0394394100R.IMG',
        'volumes/GO_0xxx/GO_0019/G8/JUPITER/C0394455245R.IMG',
        'volumes/GO_0xxx/GO_0019/G8/SML_SATS/C0394449168R.IMG',
        'volumes/GO_0xxx/GO_0019/REDO/C3/EUROPA/C0368976678R.IMG',
        'volumes/GO_0xxx/GO_0019/REDO/C3/JUPITER/C0368369268R.IMG',
        'volumes/GO_0xxx/GO_0019/REDO/E4/EUROPA/C0374667300R.IMG',
        'volumes/GO_0xxx/GO_0019/REDO/E6/IO/C0383655111R.IMG',
        'volumes/GO_0xxx/GO_0020/E11/CALLISTO/C0420426068R.IMG',
        'volumes/GO_0xxx/GO_0020/E11/EUROPA/C0420617200R.IMG',
        'volumes/GO_0xxx/GO_0020/E11/IO/C0420361523R.IMG',
        'volumes/GO_0xxx/GO_0020/E11/JUPITER/C0420458568R.IMG',
        'volumes/GO_0xxx/GO_0020/E11/RINGS/C0420809545R.IMG',
        'volumes/GO_0xxx/GO_0020/E11/SML_SATS/C0420644201R.IMG',
        'volumes/GO_0xxx/GO_0020/E12/EUROPA/C0426234600R.IMG',
        'volumes/GO_0xxx/GO_0020/E12/GANYMEDE/C0426117300R.IMG',
        'volumes/GO_0xxx/GO_0020/E12/IO/C0426152100R.IMG',
        'volumes/GO_0xxx/GO_0020/E12/TIRETRACK/C0426272849S.IMG',
        'volumes/GO_0xxx/GO_0020/E14/EUROPA/C0440948000R.IMG',
        'volumes/GO_0xxx/GO_0020/E14/GANYMEDE/C0441013078R.IMG',
        'volumes/GO_0xxx/GO_0020/E14/IO/C0440873539R.IMG',
        'volumes/GO_0xxx/GO_0020/E15/EUROPA/C0449961800R.IMG',
        'volumes/GO_0xxx/GO_0020/E15/IO/C0449841900R.IMG',
        'volumes/GO_0xxx/GO_0020/E15/IO/C0450095900R.IMG',
        'volumes/GO_0xxx/GO_0020/E17/EUROPA/C0466581865R.IMG',
        'volumes/GO_0xxx/GO_0020/E17/JUPITER/C0466580845R.IMG',
        'volumes/GO_0xxx/GO_0020/E17/RINGS/C0466612545R.IMG',
        'volumes/GO_0xxx/GO_0021/C20/CALLISTO/C0498206600R.IMG',
        'volumes/GO_0xxx/GO_0021/C21/CALLISTO/C0506142900R.IMG',
        'volumes/GO_0xxx/GO_0021/C22/IO/C0512323300R.IMG',
        'volumes/GO_0xxx/GO_0021/E18/RAW_CAL/C0477421600R.IMG',
        'volumes/GO_0xxx/GO_0021/E19/EUROPA/C0484864900R.IMG',
        'volumes/GO_0xxx/GO_0022/I24/IO/C0520792800R.IMG',
        'volumes/GO_0xxx/GO_0022/I24/IO/GARBLED/C0520792749R.IMG',
        'volumes/GO_0xxx/GO_0022/I24/IO/REPAIRED/C0520792767S.IMG',
        'volumes/GO_0xxx/GO_0022/I24/IO/REPAIRED/C0520806300S.IMG',
        'volumes/GO_0xxx/GO_0022/I25/EUROPA/C0527272700R.IMG',
        'volumes/GO_0xxx/GO_0022/I25/IO/C0527345000R.IMG',
        'volumes/GO_0xxx/GO_0022/I25/SML_SATS/C0527365601R.IMG',
        'volumes/GO_0xxx/GO_0023/C30/CALLISTO/C0605145126R.IMG',
        'volumes/GO_0xxx/GO_0023/E26/EUROPA/C0532836239R.IMG',
        'volumes/GO_0xxx/GO_0023/E26/IO/C0532939900R.IMG',
        'volumes/GO_0xxx/GO_0023/E26/SML_SATS/C0532888100R.IMG',
        'volumes/GO_0xxx/GO_0023/G28/EUROPA/C0552809300R.IMG',
        'volumes/GO_0xxx/GO_0023/G28/GANYMEDE/C0552443500R.IMG',
        'volumes/GO_0xxx/GO_0023/G28/GARBLED/C0552447568R.IMG',
        'volumes/GO_0xxx/GO_0023/G28/JUPITER/C0552766100R.IMG',
        'volumes/GO_0xxx/GO_0023/G28/OPNAV/C0566856700R.IMG',
        'volumes/GO_0xxx/GO_0023/G28/REPAIRED/C0552447569S.IMG',
        'volumes/GO_0xxx/GO_0023/G28/RINGS/C0552599400R.IMG',
        'volumes/GO_0xxx/GO_0023/G29/GANYMEDE/C0584054600R.IMG',
        'volumes/GO_0xxx/GO_0023/G29/IO/C0584260700R.IMG',
        'volumes/GO_0xxx/GO_0023/G29/JUPITER/C0584478200R.IMG',
        'volumes/GO_0xxx/GO_0023/G29/RAW_CAL/C0600486513R.IMG',
        'volumes/GO_0xxx/GO_0023/G29/REPAIRED/C0600491113S.IMG',
        'volumes/GO_0xxx/GO_0023/G29/RINGS/C0584346700R.IMG',
        'volumes/GO_0xxx/GO_0023/I27/IO/C0539931265R.IMG',
        'volumes/GO_0xxx/GO_0023/I27/IO/C0540090500R.IMG',
        'volumes/GO_0xxx/GO_0023/I31/CALLISTO/C0615354300R.IMG',
        'volumes/GO_0xxx/GO_0023/I31/IO/C0615325145R.IMG',
        'volumes/GO_0xxx/GO_0023/I31/JUPITER/C0615698700R.IMG',
        'volumes/GO_0xxx/GO_0023/I31/OPNAV/C0624540800R.IMG',
        'volumes/GO_0xxx/GO_0023/I32/IO/C0625566400R.IMG',
        'volumes/GO_0xxx/GO_0023/I32/JUPITER/C0625967145R.IMG',
        'volumes/GO_0xxx/GO_0023/I32/OPNAV/C0625709200R.IMG',
        'volumes/GO_0xxx/GO_0023/I32/RINGS/C0626030645R.IMG',
        'volumes/GO_0xxx/GO_0023/I32/SML_SATS/C0625614500R.IMG',
        'volumes/GO_0xxx/GO_0023/I33/EUROPA/C0639063400R.IMG',
        'volumes/GO_0xxx/GO_0023/I33/JUPITER/C0639371300R.IMG',
        'volumes/GO_0xxx/GO_0023/I33/OPNAV/C0639004613R.IMG',
        'volumes/GO_0xxx/GO_0023/I33/RAW_CAL/C0647529700R.IMG',
        'volumes/GO_0xxx/GO_0023/REDO/E11/IO/C0420361500R.IMG',
    ]

    for logical_path in TESTS:
        test_pdsf = pds3file.Pds3File.from_logical_path(logical_path)
        opus_id = test_pdsf.opus_id
        opus_id_pdsf = pds3file.Pds3File.from_opus_id(opus_id)
        assert opus_id_pdsf.logical_path == logical_path

        # Make sure _v1 exists
        versions = test_pdsf.all_versions()
        assert 10000 in versions
        v1_path = versions[10000].abspath
        v1_path = v1_path.replace('_v1/', '/')
        parts = v1_path.rpartition('/')
        v1_path = parts[0] + parts[2]
        assert v1_path == test_pdsf.abspath

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
                    assert viewable.abspath in opus_id_abspaths

            # Every associated product is in the product set except metadata
            for category in ('volumes', 'previews'):
                for abspath in pdsf.associated_abspaths(category):
                    assert abspath in opus_id_abspaths

def test_duplicated_products():

    TESTS = [
        ('GO_0006/REDO/C0018062639R.IMG'           , 'GO_0002/VENUS/C0018062639R.IMG'         ),
        ('GO_0006/REDO/C0018518445R.IMG'           , 'GO_0002/VENUS/C0018518445R.IMG'         ),
        ('GO_0006/REDO/C0059469700R.IMG'           , 'GO_0002/RAW_CAL/C0059469700R.IMG'       ),
        ('GO_0006/REDO/C0060964000R.IMG'           , 'GO_0003/MOON/C0060964000R.IMG'          ),
        ('GO_0006/REDO/C0061078900R.IMG'           , 'GO_0004/EARTH/C0061078900R.IMG'         ),
        ('GO_0006/REDO/C0061116600R.IMG'           , 'GO_0004/MOON/C0061116600R.IMG'          ),
        ('GO_0006/REDO/C0061424500R.IMG'           , 'GO_0004/EARTH/C0061424500R.IMG'         ),
        ('GO_0006/REDO/C0061508200R.IMG'           , 'GO_0005/EARTH/C0061508200R.IMG'         ),
        ('GO_0006/REDO/C0061522100R.IMG'           , 'GO_0005/EARTH/C0061522100R.IMG'         ),
        ('GO_0006/REDO/C0061542500R.IMG'           , 'GO_0006/EARTH/C0061542500R.IMG'         ),
        ('GO_0015/REDO/C0165242700R.IMG'           , 'GO_0012/EARTH/C0165242700R.IMG'         ),
        ('GO_0018/REDO/C3/JUPITER/C0368976900R.IMG', 'GO_0017/C3/JUPITER/C0368976900R.IMG'    ),
        ('GO_0019/REDO/C3/JUPITER/C0368441600R.IMG', 'GO_0017/C3/JUPITER/C0368441600R.IMG'    ),
        ('GO_0019/REDO/C3/JUPITER/C0368441600R.IMG', 'GO_0017/C3/JUPITER/C0368441600R.IMG'    ),
        ('GO_0019/REDO/E6/IO/C0383655111R.IMG'     , 'GO_0018/E6/IO/C0383655111R.IMG'         ),
        ('GO_0019/REDO/E6/IO/C0383655111R.IMG'     , 'GO_0018/E6/IO/C0383655111R.IMG'         ),
        ('GO_0020/E12/TIRETRACK/C0426272849S.IMG'  , 'GO_0020/E12/EUROPA/C0426272849R.IMG'    ),
        ('GO_0022/I24/IO/REPAIRED/C0520792949S.IMG', 'GO_0022/I24/IO/GARBLED/C0520792949R.IMG'),
        ('GO_0023/G28/REPAIRED/C0552447569S.IMG'   , 'GO_0023/G28/GARBLED/C0552447569R.IMG'   ),
        ('GO_0023/G29/REPAIRED/C0600660969S.IMG'   , 'GO_0023/G29/GARBLED/C0600660969R.IMG'   ),
    ]

    for (file1, file2) in TESTS:
        pdsf1 = pds3file.Pds3File.from_logical_path('volumes/GO_0xxx/' + file1)
        pdsf2 = pds3file.Pds3File.from_logical_path('volumes/GO_0xxx/' + file2)
        assert pdsf1.opus_id == pdsf2.opus_id

        test_pdsf = pds3file.Pds3File.from_opus_id(pdsf1.opus_id)
        assert test_pdsf.abspath == pdsf1.abspath

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
