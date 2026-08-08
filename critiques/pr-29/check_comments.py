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
    """Return the comments of one file, each paired with the code it is attached to.

    A comment's text alone does not say where it sits, so a comment moved to a different
    block could keep its position in the sequence and compare equal. Each comment is
    therefore paired with the nearest preceding line of code and with its own column, so
    a comment that moves, or that is re-indented, reads as changed.

    String tokens are not anchors. A docstring is a string statement, and rewriting one
    is the whole point of the change this is used to check, so anchoring on it would
    report every comment below a rewritten docstring as moved. Anchoring on the code
    around it is what makes the check specific: the code cannot move without the AST
    hash noticing, so a stable code anchor plus a stable column is a stable position.

    The comment text is compared exactly, trailing whitespace included, so a whitespace
    edit is a change like any other.

    Parameters:
        path (pathlib.Path): the file to tokenize.

    Returns:
        list: triples of anchor, column and comment text.
    """

    skip = (tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT,
            tokenize.ENCODING, tokenize.ENDMARKER, tokenize.STRING, tokenize.COMMENT)

    found = []
    anchor = '<start of file>'
    with open(path, 'rb') as handle:
        for token in tokenize.tokenize(handle.readline):
            if token.type == tokenize.COMMENT:
                found.append((anchor, token.start[1], token.string))
            elif token.type not in skip:
                anchor = token.line.rstrip()

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
            for anchor, column, text in before[i1:i2]:
                print(f'   REMOVED: col {column} after {anchor!r}: {text}')
                removed += 1
            for anchor, column, text in after[j1:j2]:
                print(f'   ADDED  : col {column} after {anchor!r}: {text}')
                added += 1

    print()
    print(f'{removed} comment lines removed, {added} added')

    return 1 if (removed or added) else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
