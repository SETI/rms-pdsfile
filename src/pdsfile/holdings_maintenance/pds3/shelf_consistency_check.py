#!/usr/bin/env python3
################################################################################
# pdsfile/holdings_maintenance/pds3/shelf_consistency_check.py
################################################################################

"""Report every shelf file that has nothing left in holdings to describe.

A shelf file summarizes a directory or an index table so that the rest of this package
can answer questions about it without opening it. When the thing a shelf describes is
deleted or renamed, nothing deletes the shelf, and the stale file goes on being loaded.
This tool walks one or more directory trees, works out what each shelf file it finds
would have to describe, and reports the ones for which that no longer exists.

Run it as::

    python -m pdsfile.holdings_maintenance.pds3.shelf_consistency_check \\
        [--verbose] shelf_root [shelf_root ...]

**The layout it looks for is not the one this repository's holdings trees use.** A
directory is examined only if ``shelves`` appears anywhere in its path -- as a substring
of the whole path string, so ``myshelves-backup`` matches as surely as ``shelves`` does
-- and only if the first component after ``shelves/`` is ``info``, ``links`` or
``index``. A holdings tree that keeps its shelves in ``_infoshelf-volumes/``,
``_linkshelf-volumes/`` and ``_indexshelf-metadata/`` -- which is what the trees here do
-- contains no such substring anywhere, so a run over one walks every directory, examines
nothing, and reports ``Tests performed: 0`` and ``Errors found: 0``. That is a clean
report about an empty search rather than about the shelves. Name a root that happens to
have ``shelves`` in its own path, though, and every directory under it is reported
instead.

Where the layout does match, the counterpart is derived by textual substitution:
``shelves/`` and the kind is replaced by ``holdings`` wherever it occurs in the shelf's
path, and the extension is dropped. For ``index``, what must then exist is that path plus
``.lbl``, the label of the index table. For ``info`` and ``links``, everything after the
last underscore goes too -- which is the ``_info`` or ``_links`` on a shelf named the way
these tools name them, and is whatever else follows an underscore on one that is not --
and what must exist is that path, as a file or a directory alike, since only existence is
asked.

Three things are reported as errors: a directory under ``shelves/`` that is none of the
three kinds, a file that is neither a ``.py`` nor a ``.pickle``, and a shelf whose
counterpart is missing. A ``.DS_Store`` is counted and passed over. The run prints how
many things it examined -- files, plus one for each directory of an unrecognized kind --
and how many errors it found, and exits 1 if it found any.

This module imports nothing from the rest of the package and reads no holdings root: the
trees to walk are the ones named on the command line, and the mapping above is done on
the path strings alone.
"""

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

    Two summary lines are always printed, whatever was found and whether or not any root
    was named: the number of things examined, and the number of errors. The first counts
    files, one per file inside a directory of a recognized kind, plus one for each
    directory of an unrecognized kind; directories of a recognized kind are not counted,
    so a ``shelves/info`` subtree of four directories holding no files reports zero. Both
    counts run across every root of the run rather than being reset per root, and both
    are zero for a tree whose paths never contain ``shelves``, which is the case for the
    holdings trees this repository is built against.

    A directory under ``shelves/`` whose kind is none of the three is reported without
    its files being examined, but the walk is not pruned, so every directory below it is
    visited and reported in the same way -- the kind is read from the one component just
    below ``shelves/``, which the whole subtree shares. One misnamed kind therefore
    costs one error per directory in it, not one error.

    Parameters:
        argv (list): The full command line, its first element the program name.
            Defaults to sys.argv.

    Returns:
        int: 1 if any error was reported, 0 otherwise. A root that does not exist
        reports nothing and contributes nothing to either count, because os.walk yields
        nothing for it and raises nothing.

    Raises:
        SystemExit: from ``parse_intermixed_args()``, with status 2 for a command line
            argparse cannot classify and status 0 for ``--help``. A command line it
            accepts returns rather than exiting.
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
