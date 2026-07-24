##########################################################################################
# crlf.py
#
# Program to validate and/or repair the CRLF line terminators in a file.
#
# Use:
#   python crlf.py --repair file(s)     # Repair any files that have invalid terminators
#   python crlf.py file(s)              # Identify any files with invalid terminators
#
# Files that are invalid are listed. Add the "--verbose" option to list all files checked,
# even if they are OK.
##########################################################################################

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
    """Test the presence of CRLF line terminators in the given file and optionally rewrite
    it.

    Parameters:
        filepath (str or pathlib.Path): path to the file.
        task (str): "test" to test the file; "repair" to rewrite it if necessary.
        threshold (float): Fraction of non-ASCII characters indicating that this is a
            binary file. If the the fraction of non-ASCII characters exceeds this value,
            the file is not modified and "binary" is returned

    Returns:
        str: "BINARY" if the file is binary; "REPAIRED" if the file was rewritten;
        "INVALID" if the file has invalid line terminators; "OK" otherwise.
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


if __name__ == '__main__':

    task = 'test'
    if '--repair' in sys.argv:
        sys.argv.remove('--repair')
        task = 'repair'

    verbose = False
    if '--verbose' in sys.argv:
        sys.argv.remove('--verbose')
        verbose = True

    repairs = 0
    invalid = 0
    for path in sys.argv[1:]:
        status = test_crlf(path, task=task)
        if verbose or status in {'REPAIRED', 'INVALID'}:
            print(path, status)
        if status == 'REPAIRED':
            repairs += 1
        if status == 'INVALID':
            invalid += 1

    nfiles = len(sys.argv[1:])
    if nfiles > 1:
        if repairs:
            if repairs == 1:
                print(f'{repairs}/{nfiles} files repaired')
        elif invalid:
                print(f'{invalid}/{nfiles} files invalid')
        else:
            print(str(nfiles), 'files tested')
