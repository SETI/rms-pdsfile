"""Hash a module's AST with every docstring removed.

Two revisions of a file that differ only in docstrings produce the same hash, so a
matching pair of hashes proves that no executable statement changed. Line and column
attributes are excluded from the dump, so the line shifts a longer docstring causes do
not register either.

The check has one blind spot: comments are not part of the AST, so a comment that is
deleted or reworded is invisible here and has to be accounted for separately.

Usage:
    python strip_docstrings.py FILE [FILE ...]
"""

import ast
import hashlib
import pathlib
import sys


def strip(tree):
    """Remove the docstring node from every module, class and function in a tree.

    A body left empty by the removal is replaced with a single `pass` statement so the
    tree stays valid.

    Parameters:
        tree (ast.Module): the parsed module to modify in place.

    Returns:
        ast.Module: the same tree, with docstring nodes removed.
    """

    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)):
            body = node.body
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                node.body = body[1:] or [ast.Pass()]

    return tree


def hash_of(path):
    """Return the 16-character hash of one file's docstring-stripped AST.

    Parameters:
        path (pathlib.Path): the file to parse.

    Returns:
        str: the first 16 hex digits of the SHA-256 of the dumped tree.
    """

    tree = strip(ast.parse(path.read_text()))
    dump = ast.dump(tree, annotate_fields=True, include_attributes=False)

    return hashlib.sha256(dump.encode()).hexdigest()[:16]


def main(argv):
    """Print one hash and file name per argument.

    Parameters:
        argv (list): the file paths to hash.

    Returns:
        int: zero.
    """

    for arg in argv:
        path = pathlib.Path(arg)
        print(hash_of(path), path.name)

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
