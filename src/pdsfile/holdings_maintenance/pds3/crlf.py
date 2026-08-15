##########################################################################################
# pdsfile/holdings_maintenance/pds3/crlf.py
##########################################################################################

"""Report, and optionally repair, the line terminators of PDS3 text files.

The PDS3 standard requires every record of a text file to end in a carriage return
followed by a line feed, and requires the last record to be terminated like the rest. A
file edited on a system that terminates with a bare line feed, or saved without a final
newline, no longer conforms. This tool classifies files as conforming or not, and can
rewrite the ones that are not.

Run it as::

    python -m pdsfile.holdings_maintenance.pds3.crlf file [file ...]
    python -m pdsfile.holdings_maintenance.pds3.crlf --repair file [file ...]

The first form only reports; the second rewrites. Any number of files may be named, and
the two options may appear anywhere among them. Only files that are invalid or were
repaired are listed, unless ``--verbose`` is given, which lists every file examined.

A binary file has no line terminators to be wrong about, so one is recognized and left
alone rather than being rewritten into nonsense. The recognition is a fraction: the file
is read as bytes and decoded with a single-byte codec, so every byte is one character,
and a file is treated as binary when more than one percent of its characters are counted
as non-ASCII. What is counted is everything below byte 32 and everything from 128 up,
less carriage return, line feed and tab. Byte 127, delete, is in neither range and so is
counted as text, which is the one place the rule and the phrase "printable ASCII" part
company.

The classifier is ``test_crlf()``, which is what a caller wanting one file's verdict
should use; ``main()`` is the loop over a command line, and its summary line counts only
the cases described in its own docstring.

This module imports nothing from the rest of the package and reads no holdings root. The
files it works on are the ones named on the command line, and it never looks for their
place in a holdings tree.
"""

import argparse
import sys

# Create a dictionary identifying non-ASCII characters with an "x"
NON_ASCIIS = {}
for c in range(32):
    NON_ASCIIS[c] = 'x'
for c in range(32, 128):
    NON_ASCIIS[c] = None
for c in range(128, 256):
    NON_ASCIIS[c] = 'x'
NON_ASCIIS[ord('\r')] = None
NON_ASCIIS[ord('\n')] = None
NON_ASCIIS[ord('\t')] = None


def test_crlf(filepath, task='test', threshold=0.01):
    """Classify one file's line terminators, and rewrite them when asked to.

    A file conforms when every record ends in a carriage return before its line feed and
    the last record is terminated as well. Two things make it fail: a line feed with no
    carriage return in front of it, which includes an empty line, and a final record with
    no terminator at all. Repairing means supplying exactly what is missing, so the
    number of records and their content are unchanged and no other byte moves.

    Both tasks read the whole file and reach the same verdict; they differ only in what
    is done about it. A file that needs nothing is left alone under either task and no
    file is opened for writing unless it is going to change.

    Records are found by splitting on the line feed alone, so a file whose records are
    separated by carriage returns and nothing else is one record to this function: it is
    reported as invalid, and repairing it appends one terminator at the end and leaves
    the interior carriage returns where they are.

    Parameters:
        filepath (str or pathlib.Path): Path to the file, passed to ``open()`` as given.
        task (str): "test" to report the verdict, "repair" to rewrite a file that needs
            it. Any other value is rejected before the file is opened.
        threshold (float): The fraction of non-ASCII characters above which the file is
            taken to be binary and is neither classified nor rewritten. A character
            counts as non-ASCII when its byte is below 32 or 128 or above, and is not a
            carriage return, a line feed or a tab; byte 127 is in neither range and does
            not count. The test is strict, so a file exactly at the threshold is still
            treated as text.

    Returns:
        str: "BINARY" if the non-ASCII fraction is above the threshold; "REPAIRED" if
        the file needed repair and the task was "repair"; "INVALID" if it needed repair
        and the task was "test"; "OK" if it needed none. "INVALID" is therefore never
        returned by a repair run, and "REPAIRED" never by a test run.

    Raises:
        ValueError: if ``task`` is neither "test" nor "repair", or if ``threshold`` is
            outside the closed interval from 0 to 1. Both are checked before the file is
            touched, so a bad argument costs no read.
        ZeroDivisionError: for a zero-byte file, whose non-ASCII fraction divides by a
            ``len()`` of zero. Nothing guards it, so an empty file ends the call rather
            than being classified.
        OSError: from the ``open()`` of a file that does not exist or cannot be read,
            and from the ``open()`` for writing of one that cannot be rewritten.
    """

    if task not in {'test', 'repair'}:
        raise ValueError('invalid task')

    if not 0. <= threshold <= 1.:
        raise ValueError('invalid threshold')

    # Read the file as a byte string
    with open(filepath, 'rb') as f:
        content = f.read()

    # Count the non-ASCII characters
    content = content.decode('latin8')
    non_asciis = len(content.translate(NON_ASCIIS))

    # If the non-ASCII fraction is above the threshold, it's a binary file
    if non_asciis/len(content) > threshold:
        return 'BINARY'

    # Split the file content into records
    recs = content.split('\n')

    # For each record not ending in CR, append the CR
    repaired = False
    for k, rec in enumerate(recs[:-1]):
        if len(rec) == 0 or rec[-1] != '\r':
            recs[k] = rec + '\r'
            repaired = True

    # Append CRLF at the end if it's missing
    if recs[-1]:
        recs[-1] += '\r\n'
        repaired = True

    # If the content has changed, rewrite the file
    if repaired:
        if task == 'repair':
            content = '\n'.join(recs).encode('latin8')
            with open(filepath, 'wb') as f:
                f.write(content)
            return 'REPAIRED'
        return 'INVALID'

    return 'OK'


def build_arg_parser():
    """Return the argument parser for this tool.

    Returns:
        argparse.ArgumentParser: The parser, holding the file paths, --repair and
        --verbose.
    """

    # No abbreviations: an option has to be spelled out, so that a misspelled
    # --repair is rejected rather than read as a request to rewrite files.
    parser = argparse.ArgumentParser(
        allow_abbrev=False,
        description='crlf: Validate, and optionally repair, the CRLF line terminators '
                    'of one or more files. Files with invalid terminators are listed.')

    parser.add_argument('file', nargs='*', type=str,
                        help='The path to a file to check. Any number may be given.')

    parser.add_argument('--repair', action='store_true',
                        help='Rewrite every file whose line terminators are invalid. '
                             'Without this option, files are only reported.')

    parser.add_argument('--verbose', action='store_true',
                        help='List every file checked, not just the ones that are '
                             'invalid or were repaired.')

    return parser


def main(argv=None):
    """Check the files named on the command line and report on each one.

    One line is printed per file whose verdict is "REPAIRED" or "INVALID", and per file
    of any verdict when ``--verbose`` is given. A summary line follows only when two or
    more files were named; naming one file, or none, prints no summary whatever the
    verdicts were.

    The summary reports repairs when there was exactly one, invalid files when there
    were no repairs, and the number of files tested when there was neither. The three
    are exclusive, and one case falls through all of them: a run that repairs two or
    more files prints no summary at all. A repair run never reports an invalid file,
    because a file needing repair is repaired and so is counted as a repair; the invalid
    count can only be nonzero in a run without ``--repair``, where the repair count is
    always zero.

    Parameters:
        argv (list): The full command line, its first element the program name.
            Defaults to sys.argv.

    Returns:
        int: 1 if any file was left INVALID, and 0 otherwise. A repaired file is not a
        failure: the repair is what was asked for and it happened.

    Raises:
        SystemExit: from ``parse_intermixed_args()``, with status 2 for a command line
            argparse cannot classify and status 0 for ``--help``. A command line it
            accepts returns rather than exiting.
        ZeroDivisionError: from ``test_crlf()`` on the first zero-byte file named, which
            ends the run with the remaining files unexamined and nothing summarized.
        OSError: from ``test_crlf()`` on the first file that cannot be read or, under
            ``--repair``, cannot be rewritten, likewise ending the run.
    """

    if argv is None:
        argv = sys.argv

    parser = build_arg_parser()
    # Intermixed, so that the flags are accepted anywhere among the file paths.
    args = parser.parse_intermixed_args(argv[1:])

    task = 'repair' if args.repair else 'test'

    repairs = 0
    invalid = 0
    for path in args.file:
        status = test_crlf(path, task=task)
        if args.verbose or status in {'REPAIRED', 'INVALID'}:
            print(path, status)
        if status == 'REPAIRED':
            repairs += 1
        if status == 'INVALID':
            invalid += 1

    nfiles = len(args.file)
    if nfiles > 1:
        if repairs:
            # A run that repairs two or more files prints no summary at all: the
            # count is only reported when it is exactly one.
            if repairs == 1:
                print(f'{repairs}/{nfiles} files repaired')
        elif invalid:
            print(f'{invalid}/{nfiles} files invalid')
        else:
            print(str(nfiles), 'files tested')

    # A file left INVALID is one the run could not make right: in test mode nothing was
    # asked of it beyond the verdict, and in repair mode the repair did not happen.
    # Either way the tree is not clean, which is what a caller branches on.
    return 1 if invalid else 0


if __name__ == '__main__':
    sys.exit(main())
