#!/usr/bin/env python3
"""Show the OPUS products of the paths named on the command line.

For each path it is given, this instantiates a Pds3File or a Pds4File and prints what
``opus_products()`` returns for it: the files OPUS would offer alongside that one,
grouped by OPUS type. There are three output forms -- a table, a pprint dump and the raw
dictionary -- and a fourth option, --narrow-table, that changes the shape of the table
rather than selecting a form of its own. The table is the default. The pprint form exists
to be compared against the OPUS-products golden files in this package's tests.

Both holdings roots are read straight from the environment, PDS3_HOLDINGS_DIR and
PDS4_HOLDINGS_DIR, and both are required whichever kind of path is asked about.

**It is a process, not a library call, and its tests treat it as one.** Running
``main()`` changes state that belongs to the whole interpreter and does not change back:
it turns shelves-only mode on for ``Pds3File`` and off for ``Pds4File``, and it preloads
both trees into the caches those classes hold as class attributes. Those caches are keyed
by logical path, so a session that has preloaded one tree resolves a logical path to that
tree whatever root a later caller has in mind. Calling this in process therefore changes
how every later call in the same interpreter resolves a path, which is why the tests
under ``tests/holdings_maintenance/`` drive every run that reads a holdings tree with
``python -m`` in a subprocess, against a disposable copy. They do import ``main()`` and
call it, but only for command lines argparse rejects before either root is read.
"""

import argparse
import os
import pprint
import sys
import traceback

import tabulate

from pdsfile import Pds3File, Pds4File


def opus_type_of(prod_category):
    """Return the OPUS type a product-category key carries, or None if it carries none.

    A key is normally the five-element tuple ``opus_products()`` documents, whose third
    element is the short OPUS type. **Not every key is**: the contract admits the empty
    string, which carries a unit set's ``documents/`` products, and four paths in the
    reference holdings return it. Asking rather than subscripting is what keeps such a
    key from ending the run in ``IndexError``.

    The whole five-element shape is required, not just an element at index 2, because
    the ``--raw`` form prints all five and a shorter key would reach that branch alone.

    Parameters:
        prod_category: One key of an ``opus_products()`` result.

    Returns:
        str: The OPUS type, or None for any key that is not the documented five-element
        tuple.
    """

    if isinstance(prod_category, tuple) and len(prod_category) == 5:
        return prod_category[2]

    return None


def build_arg_parser():
    """Return the argument parser for this tool.

    Returns:
        argparse.ArgumentParser: The parser. It holds --paths, which is required and
        takes one or more paths; --opus-types, which narrows what is printed; the three
        output forms --table, --pprint and --raw, plus --narrow-table, which reshapes
        the table form; and --debug. The four are independent flags rather than a
        mutually exclusive group.
    """

    # Set up parser
    parser = argparse.ArgumentParser(
        description="""show_opus_products: show the output of opus products for the given
                    files. If only abspaths/logical-paths are given, with no other options,
                    it will instantiate Pds3File or Pds4File instances and display the opus
                    products output in a table by default.""")

    parser.add_argument('--paths', nargs='+', type=str, default='', required=True,
        help='The abspaths or logical paths of the files')

    parser.add_argument('--opus-types', nargs='+', type=str, default='',
        help='Display only the output of opus products belonging to the given opus types')

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

    return parser


def main(argv=None):
    """Print the OPUS products of every path named on the command line.

    Each path is tried as a Pds3File first and as a Pds4File second, and each of those
    as an absolute path first and as a logical path second. A path that resolves under
    none of the four is reported and skipped, and so is one that resolves to a file that
    does not exist. Either one fails the run: the remaining paths are still printed, and
    the exit status is 1 because the tool did not do what it was asked for one of them.

    Every path is resolved before any output is printed, so the warnings about paths
    come first and the per-file output follows in the order the paths were given.

    An OPUS type named with --opus-types that this file has none of is reported and
    dropped; that alone does not fail the run, because the file's other types are still
    printed. Where every named type is dropped the file's output is skipped entirely
    rather than printed unfiltered, and that does fail the run.

    There are three output forms and the first true flag in the order table, pprint, raw
    picks among them; --narrow-table only changes the shape of the table form. Giving
    none of --table, --pprint and --raw turns the table form on, and giving
    --narrow-table alone does the same, because --narrow-table is not one of the three
    that test looks at.

    **The table form is keyed by the OPUS type rather than by the whole product
    category, and the collision that invites is real.** Two categories differing only in
    their rank can carry one type -- VG_2803's Uranus ring occultations give two "200 m
    inversion, old pole" categories the type "vgrss_occ_inv0_2" -- and the table then
    prints one row, the later category's. The pprint and raw forms key on the whole
    category tuple and show both.

    Both holdings roots are read from the environment and both trees are preloaded,
    whatever kinds of path were asked for.

    Parameters:
        argv (list): The full command line, defaulting to sys.argv.

    Returns:
        int: 1 if any path could not be resolved, did not exist, or had all of its
        named OPUS types dropped, and 0 otherwise.

    Raises:
        SystemExit: raised by ``parse_args()`` for a command line it cannot classify,
            with status 2, and for --help with status 0. This is the first thing that
            can go wrong, before either holdings root is read.
        KeyError: from the item read ``__getitem__()`` on the environment, if either
            PDS3_HOLDINGS_DIR or PDS4_HOLDINGS_DIR is unset.
    """

    if argv is None:
        argv = sys.argv

    parser = build_arg_parser()
    args = parser.parse_args(argv[1:])
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

    # Holdings roots read straight from the environment. The test helpers that also
    # expose these live in the tests package (not the distribution), so this tool
    # reads the env vars directly.
    pds3_holdings_dir = os.environ['PDS3_HOLDINGS_DIR']
    pds4_holdings_dir = os.environ['PDS4_HOLDINGS_DIR']

    Pds3File.use_shelves_only(True)
    Pds3File.preload(pds3_holdings_dir)
    Pds4File.use_shelves_only(False)
    Pds4File.preload(pds4_holdings_dir)

    pdsf_inst_list = []
    failures = 0
    for path in paths:
        pdsf_inst = None
        # Instantiate Pds3File first. If there is an exception, try to instantiate
        # a Pds4File
        for class_name in [Pds3File, Pds4File]:
            try:
                pdsf_inst = class_name.from_abspath(path)
            except ValueError:
                try:
                    pdsf_inst = class_name.from_logical_path(path)
                except ValueError:
                    continue
            break

        if pdsf_inst is None:
            if debug:
                traceback.print_exc()
            print("WARNING: Can't instantiate a Pds3File or Pds4File instance with the " +
                  f'given path: {path}')
            failures += 1
            continue

        if not pdsf_inst.exists:
            print(f"WARNING: The instantiated PdsFile doesn't exist! Path: {path}")
            failures += 1
            continue

        pdsf_inst_list.append(pdsf_inst)

    for pdsf_inst in pdsf_inst_list:
        opus_prod = pdsf_inst.opus_products()
        res = {}

        # A key that is not a five-element tuple carries no OPUS type. The contract
        # opus_products() states admits one -- the empty string, for a unit set's
        # documents -- and real paths do return it, so every key is asked rather than
        # subscribed to.
        unkeyed = [category for category in opus_prod if not opus_type_of(category)]
        for category in unkeyed:
            print(f'WARNING: {len(opus_prod[category])} product group(s) under a key '
                  f'with no OPUS type ({category!r}) are not shown for '
                  f'{pdsf_inst.logical_path}')

        golden_opus_types = [opus_type_of(prod_category) for prod_category in opus_prod
                             if opus_type_of(prod_category)]
        valid_opus_types = []
        for opus_type in given_opus_types:
            if opus_type not in golden_opus_types:
                print(f'WARNING: {opus_type} is not valid for {pdsf_inst.logical_path}')
            elif opus_type not in valid_opus_types:
                valid_opus_types.append(opus_type)

        # If all the give opus types are wrong, let the user know and don't display output
        # for this pdsfile instance
        if given_opus_types and not valid_opus_types:
            print(f"None of the given opus types exist; valid values: {golden_opus_types}")
            print(f'WARNING: bypassing output for {pdsf_inst.logical_path}')
            failures += 1
            continue

        for prod_category, prod_list in opus_prod.items():
            pdsf_list = []
            for pdsf_li in prod_list:
                for pdsf in pdsf_li:
                    pdsf_list.append(pdsf.logical_path)

            opus_type = opus_type_of(prod_category)
            if not opus_type:
                continue

            if valid_opus_types and opus_type not in valid_opus_types:
                continue

            if display_table:
                res[opus_type] = pdsf_list
            else:
                res[prod_category] = pdsf_list

        print('#' * 90)
        print(f'Pdsfile: {pdsf_inst.logical_path}')
        print('#' * 90)
        if display_table:
            # print the table with opus type in the first column and its corresponding
            # products list in the second column. Each file of the same opus type will be in
            # its own row.
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
                print(f'  {prod_category[1]},')
                print(f"  '{prod_category[2]}',")
                print(f"  '{prod_category[3]}',")
                print(f'  {prod_category[4]}): [')
                for prod in prod_list:
                    print(f"    '{prod}',")
                print('  ],')
            print('}')

    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
