#!/usr/bin/env python3
import argparse
from ast import literal_eval
from json import loads, dumps
from pdsfile import (Pds3File,
                     Pds4File)
from pdsfile.pds3file.tests.helper import PDS3_HOLDINGS_DIR
from pdsfile.pds4file.tests.helper import PDS4_HOLDINGS_DIR
import pprint
import sys

# Set up parser
parser = argparse.ArgumentParser(
    description="""show_opus_products: show the output of opus products for the given
                absolute path of the file.""")

parser.add_argument('--abspath', type=str, default='', required=True,
    help='The absolute path of the file')

parser.add_argument('--raw', '-r', action='store_true',
    help='Show the raw output of opus products.')

args = parser.parse_args()
abspath = args.abspath
display_raw = args.raw

# print help screen if no abspath is given
if len(sys.argv) == 1 or not abspath or 'holdings' not in abspath:
    parser.print_help()
    parser.exit()

is_pds3 = True
if '/holdings/' in abspath:
    Pds3File.use_shelves_only(True)
    Pds3File.preload(PDS3_HOLDINGS_DIR)
else:
    Pds4File.use_shelves_only(False)
    Pds4File.preload(PDS4_HOLDINGS_DIR)
    is_pds3 = False

if is_pds3:
    pdsf_inst = Pds3File.from_abspath(abspath)

else:
    pdsf_inst = Pds4File.from_abspath(abspath)

if not pdsf_inst.exists:
    print(f"The istantiated pdsfile doesn't exist! Please double check the path.")
    parser.exit()

opus_prod = pdsf_inst.opus_products()
res = {}

for prod_category, prod_list in opus_prod.items():
    pdsf_list = []
    for pdsf in prod_list:
        pdsf_list.append(pdsf[0].logical_path)

    if not display_raw:
        opus_type = prod_category[2]
        res[opus_type] = pdsf_list
    else:
        res[prod_category] = pdsf_list
        json_format_res = dumps({str(k): v for k, v in res.items()}, indent=2)

print('======= OPUS PRODUCTS OUTPUT =======')
if not display_raw:
    # pprint dictionary with opus type as the key and its corresponding product list as
    # the value
    pprint.pp(res, width=90)
else:
    # print raw opus products ouput with cusomized format
    print('{')
    for prod_category, prod_list in res.items():
        print(f" ('{prod_category[0]}',")
        print(' ',f'{prod_category[1]},')
        print(' ',f"'{prod_category[2]}',")
        print(' ',f"'{prod_category[3]}',")
        print(' ',f'{prod_category[4]}): [')
        for prod in prod_list:
            print('  ',f"'{prod}',")
        print('  ],')
    print('}')
