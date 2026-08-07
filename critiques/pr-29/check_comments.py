"""Diff the comment lines of the in-scope modules between two trees.

The AST hash in `strip_docstrings.py` proves that no executable statement changed, but
comments are not AST nodes, so a comment deleted or reworded is invisible to it. This
closes that blind spot: it tokenizes each file in both trees, keeps the comment tokens,
and reports every one that was removed or added.

Usage:
    python check_comments.py BASE_TREE HEAD_TREE

Each argument is a directory holding `src/pdsfile/`. Exit status is 1 if any comment
line differs, 0 otherwise.
"""

import difflib
import pathlib
import sys
import tokenize

FILES = ('pdsfile.py', 'pdscache.py', 'pdsviewable.py', '__init__.py',
         'preload_and_cache.py')


def comments(path):
    """Return the comment lines of one file, in order.

    Trailing whitespace is stripped so that a difference in it does not read as a
    changed comment.

    Parameters:
        path (pathlib.Path): the file to tokenize.

    Returns:
        list: the comment token texts.
    """

    found = []
    with open(path, 'rb') as handle:
        for token in tokenize.tokenize(handle.readline):
            if token.type == tokenize.COMMENT:
                found.append(token.string.rstrip())

    return found


def main(argv):
    """Compare the two trees and print the per-file table and every difference.

    Parameters:
        argv (list): the base tree and the head tree, in that order.

    Returns:
        int: 1 if any comment line differs, 0 otherwise.
    """

    base, head = pathlib.Path(argv[0]), pathlib.Path(argv[1])
    removed = added = 0

    for name in FILES:
        before = comments(base / 'src' / 'pdsfile' / name)
        after = comments(head / 'src' / 'pdsfile' / name)
        print(f'{name:24s} base {len(before):4d}  head {len(after):4d}')

        matcher = difflib.SequenceMatcher(None, before, after, autojunk=False)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                continue
            for line in before[i1:i2]:
                print('   REMOVED:', line)
                removed += 1
            for line in after[j1:j2]:
                print('   ADDED  :', line)
                added += 1

    print()
    print(f'{removed} comment lines removed, {added} added')

    return 1 if (removed or added) else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
