#!/usr/bin/env python3
################################################################################
# shelf_consistency_check.py
#
# Syntax:
#   python -m pdsfile.holdings_maintenance.pds3.shelf_consistency_check \
#       [--verbose] shelf_root [shelf_root ...]
#
# Confirm that every info shelf file has a corresponding directory in holdings/.
################################################################################

import argparse
import os
import sys


def build_arg_parser():
    """Return the argument parser for this tool.

    Returns:
        argparse.ArgumentParser: The parser, holding the shelf roots to walk and
        --verbose.
    """

    # No abbreviations: an option has to be spelled out, so that a misspelling is
    # rejected rather than quietly turning --verbose on.
    parser = argparse.ArgumentParser(
        allow_abbrev=False,
        description='shelf_consistency_check: Confirm that every shelf file has a '
                    'corresponding file or directory in holdings/.')

    parser.add_argument('shelf_root', nargs='*', type=str,
                        help='The path to a directory tree to walk. Any number may be '
                             'given; each is searched for a "shelves" directory.')

    parser.add_argument('--verbose', action='store_true',
                        help='Also print the holdings path that each shelf maps to.')

    return parser


def main(argv=None):
    """Walk each shelf root and report every shelf with no counterpart in holdings.

    Args:
        argv: The full command line, defaulting to sys.argv.

    Returns:
        int: 1 if anything was reported, 0 otherwise.
    """

    if argv is None:
        argv = sys.argv

    parser = build_arg_parser()
    # Intermixed, so that --verbose is accepted anywhere among the shelf roots.
    args = parser.parse_intermixed_args(argv[1:])

    paths = args.shelf_root
    verbose = args.verbose

    # Traverse each directory tree...
    errors = 0
    tests = 0
    for path in paths:
        for root, _dirs, files in os.walk(path):

            # Ignore anything not inside a shelves directory
            if 'shelves' not in root:
                continue
            if root.endswith('shelves'):
                continue

            # Confirm it is one of the expected subdirectories
            tail = root.partition('shelves/')[-1]
            tail = tail.partition('/')[0]
            if tail not in ('info', 'links', 'index'):
                print('*** Not a valid shelves directory: ' + root)
                errors += 1
                tests += 1
                continue

            # Check each file...
            for name in files:
                shelf_path = os.path.join(root, name)
                tests += 1

                if name == '.DS_Store':
                    continue

                # Check the file extension
                if not (name.endswith('.py') or name.endswith('.pickle')):
                    print('*** Extraneous file found: ' + shelf_path)
                    errors += 1
                    continue

                # Convert to the associated holdings path
                holdings_path = shelf_path.replace('shelves/' + tail, 'holdings')
                holdings_path = holdings_path.rpartition('.')[0]

                # For index shelves, make sure the holdings label file exists
                if tail == 'index':
                    if not os.path.exists(holdings_path + '.lbl'):
                        print('*** Extraneous shelf: ' + shelf_path)
                        errors += 1
                        continue

                    if verbose:
                        print(holdings_path)

                # For info and link shelves, make sure the holdings directory exists
                else:
                    holdings_path = holdings_path.rpartition('_')[0]
                    if not os.path.exists(holdings_path):
                        print('*** Extraneous shelf: ' + shelf_path)
                        errors += 1
                        continue

                    if verbose:
                        print(holdings_path)

    # Summarize
    print(f'Tests performed: {tests}')
    print(f'Errors found: {errors}')

    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())

################################################################################
