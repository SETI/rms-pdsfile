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

parser.add_argument('--paths', nargs='+', type=str, default='', required=True,
    help='The paths of the files, can be either abspath or logical path')

parser.add_argument('--opus-types', nargs='+', type=str, default='',
    help='Display the output of opus products belong to the given opus types')

parser.add_argument('--table', '-t', action='store_true',
    help='Display the output of opus products in a table. (Default)')

parser.add_argument('--narrow-table', action='store_true',
    help='Display the output of opus products in a narrower table.')

parser.add_argument('--pprint', '-p', action='store_true',
    help="""Display the output of opus products using pprint. The results can be used
         to compare with the opus products golden copies in pdsfile.""")

parser.add_argument('--raw', '-r', action='store_true',
    help='Display the raw (dictionary) output of opus products.')

parser.add_argument('--debug', action='store_true',
    help='Print traceback when there is an exception during pdsfile instantiation')

args = parser.parse_args()
paths = args.paths
given_opus_types = args.opus_types

display_table = args.table
display_narrow_table = args.narrow_table
display_pprint = args.pprint
display_raw = args.raw

debug = args.debug

# If no display option is specified, display the output in a table
if not display_table and not display_pprint and not display_raw:
    display_table = True

Pds3File.use_shelves_only(True)
Pds3File.preload(PDS3_HOLDINGS_DIR)
Pds4File.use_shelves_only(False)
Pds4File.preload(PDS4_HOLDINGS_DIR)

pdsf_inst_list = []
for path in paths:
    bypass_current_path = False
    try:
        # Instantiate pds3file first, if there is an exception, try to instantiate
        # pds4file
        for class_name in [Pds3File, Pds4File]:
            try:
                pdsf_inst = class_name.from_abspath(path)
            except:
                try:
                    pdsf_inst = class_name.from_logical_path(path)
                except:
                    continue
            break
    except:
        if debug:
            traceback.print_exc()
        print("WARNING: Can't instantiate a pds3file & pds4file instance with the " +
              f'given path: {path}')
        bypass_current_path = True

    if not pdsf_inst.exists:
        print(f"WARNING: The istantiated pdsfile doesn't exist! Path: {path}")
        bypass_current_path = True

    if not bypass_current_path:
        pdsf_inst_list.append(pdsf_inst)

for pdsf_inst in pdsf_inst_list:
    opus_prod = pdsf_inst.opus_products()
    res = {}

    golden_opus_type_li = [prod_category[2] for prod_category, _ in opus_prod.items()]
    valid_opus_types = []
    for type in given_opus_types:
        if type not in golden_opus_type_li:
            print(f'WARNING: {type} is not valid for {pdsf_inst.logical_path}')
        elif type not in valid_opus_types:
            valid_opus_types.append(type)

    # If all the give opus types are wrong, let the user knows and don't display output
    # for this pdsfile instance
    if given_opus_types and not valid_opus_types:
        print(f"The given opus types don't exist, valid values: {golden_opus_type_li}")
        print(f'WARNING: bypass output for {pdsf_inst.logical_path}')
        continue

    for prod_category, prod_list in opus_prod.items():
        pdsf_list = []
        for pdsf_li in prod_list:
            for pdsf in pdsf_li:
                pdsf_list.append(pdsf.logical_path)

        opus_type = prod_category[2]
        if valid_opus_types and opus_type not in valid_opus_types:
            continue

        if display_table:
            res[opus_type] = pdsf_list
        else:
            res[prod_category] = pdsf_list

    print('#'*90)
    print(f'Pdsfile: {pdsf_inst.logical_path}')
    print('#'*90)
    if display_table:
        # print the table with opus type in the first column and its corresponding products
        # list in the second column. Each file of the same opus type will be in its own row.
        rows = []
        if not display_narrow_table:
            header = ['opus_type', 'opus_products']
            for opus_type, prod_list in res.items():
                rows.append([opus_type, '\n'.join(prod_list)])
        else:
            header = ['opus_type and its corresponding opus_products']
            for opus_type, prod_list in res.items():
                if opus_type not in rows:
                    rows.append([opus_type])
                rows.append(['\n'.join(prod_list)])

        print(tabulate.tabulate(rows, header, tablefmt="grid"))
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
