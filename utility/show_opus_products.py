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
import tabulate
import traceback

# Set up parser
parser = argparse.ArgumentParser(
    description="""show_opus_products: show the output of opus products for the given
                absolute path of the file. If only abspath or logical-path is given,
                and no other options are set, it will instantiate a Pds3File instance and
                display opus products output in table by default.""")

parser.add_argument('--abspath', type=str, default='',
    help='The absolute path of the file')

parser.add_argument('--logical-path', type=str, default='',
    help='The logical path of the file')

parser.add_argument('--pds3', action='store_true',
    help='Instantiate a Pds3File instance. (Default)')

parser.add_argument('--pds4', action='store_true',
    help='Instantiate a Pds4File instance.')

parser.add_argument('--table', '-t', action='store_true',
    help='Display the output of opus products in a table. (Default)')

parser.add_argument('--pprint', '-p', action='store_true',
    help="""Display the output of opus products using pprint. The results can be used
         to compare with the opus products golden copies in pdsfile.""")

parser.add_argument('--raw', '-r', action='store_true',
    help='Display the raw (dictionary) output of opus products.')

args = parser.parse_args()
abspath = args.abspath
logical_path = args.logical_path
display_table = args.table
display_pprint = args.pprint
display_raw = args.raw
# If no pdsfile class is specified, instantiate a Pds3File instance
is_pds3 = args.pds3 or not args.pds4

# If no display option is specified, display the output in a table
if not display_table and not display_pprint and not display_raw:
    display_table = True

# print help screen if no abspath is given
if (len(sys.argv) == 1 or (not abspath and not logical_path)):
    parser.print_help()
    parser.exit()

try:
    if is_pds3:
        Pds3File.use_shelves_only(True)
        Pds3File.preload(PDS3_HOLDINGS_DIR)
        if abspath:
            pdsf_inst = Pds3File.from_abspath(abspath)
        else:
            pdsf_inst = Pds3File.from_logical_path(logical_path)
    else:
        Pds4File.use_shelves_only(False)
        Pds4File.preload(PDS4_HOLDINGS_DIR)
        if abspath:
            pdsf_inst = Pds4File.from_abspath(abspath)
        else:
            pdsf_inst = Pds4File.from_logical_path(logical_path)
except:
    traceback.print_exc()
    print("Can't instantiate a pds3file & pds4file instance with the given path. " +
          "Please double check the input path.")
    parser.exit()

if not pdsf_inst.exists:
    print(f"The istantiated pdsfile doesn't exist! Please double check the path.")
    parser.exit()

opus_prod = pdsf_inst.opus_products()
res = {}

for prod_category, prod_list in opus_prod.items():
    pdsf_list = []
    for pdsf_li in prod_list:
        for pdsf in pdsf_li:
            pdsf_list.append(pdsf.logical_path)

    if display_table:
        opus_type = prod_category[2]
        res[opus_type] = pdsf_list
    else:
        res[prod_category] = pdsf_list

print('======= OPUS PRODUCTS OUTPUT =======')
if display_table:
    # print the table with opus type in the first column and its corresponding products
    # list in the second column. Each file of the same opus type will be in its own row.
    header = ['opus_type', 'opus_products']
    rows = []
    for opus_type, prod_list in res.items():
        # Use this flag to show each distinct opus_type onces in the table row
        opus_type_shown = False
        for prod in prod_list:
            if not opus_type_shown:
                rows.append([opus_type, prod])
                opus_type_shown = True
            else:
                rows.append(['', prod])
    print(tabulate.tabulate(rows, header,tablefmt="grid"))
elif display_pprint:
    pprint.pp(res, width=90)
elif display_raw:
    # print the raw opus products output
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
