"""Measure a module against the two length limits: code lines and total lines.

A docstring adds no complexity, so counting it against a complexity budget makes
documenting a module a reason to split it. The two budgets are therefore measured
separately:

    code lines   total lines minus the lines occupied by module, class and function
                 docstrings, taken from the AST rather than from a text scan, so a
                 string that is not a docstring is not deducted.
    total lines  what a reader or a tool has to ingest to reach the end of the file.

A docstring's line span is its constant node's `lineno` through `end_lineno`, which is
the whole of the triple-quoted literal including both delimiter lines. The expression
statement wrapping it occupies no line the constant does not.

Usage:
    python measure_module_lines.py FILE [FILE ...]
"""

import ast
import pathlib
import sys

CODE_LIMIT = 1000
TOTAL_LIMIT = 2000


def docstring_lines(tree):
    """Return the set of line numbers occupied by docstrings in one module.

    Parameters:
        tree (ast.Module): the parsed module.

    Returns:
        set: the one-based line numbers.
    """

    occupied = set()

    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                                 ast.AsyncFunctionDef)):
            continue

        body = node.body
        if (body and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)):
            constant = body[0].value
            occupied.update(range(constant.lineno, constant.end_lineno + 1))

    return occupied


def measure(path):
    """Measure one file.

    Parameters:
        path (pathlib.Path): the file to measure.

    Returns:
        tuple: total lines, docstring lines, and code lines.
    """

    text = path.read_text(encoding='utf-8')
    total = len(text.splitlines())
    docstring = len(docstring_lines(ast.parse(text)))

    return (total, docstring, total - docstring)


def main(argv):
    """Measure every file named on the command line and print a verdict for each.

    Parameters:
        argv (list): the file paths to measure.

    Returns:
        int: the number of files over either limit.
    """

    over = 0
    print(f'{"file":56s} {"total":>6s} {"docstr":>7s} {"code":>6s}  verdict')

    for name in argv:
        path = pathlib.Path(name)
        total, docstring, code = measure(path)

        breaches = []
        if code > CODE_LIMIT:
            breaches.append(f'code > {CODE_LIMIT}')
        if total > TOTAL_LIMIT:
            breaches.append(f'total > {TOTAL_LIMIT}')
        if breaches:
            over += 1

        verdict = ' and '.join(breaches) if breaches else 'passes both'
        print(f'{name:56s} {total:6d} {docstring:7d} {code:6d}  {verdict}')

    print()
    print(f'{over} of {len(argv)} files are over a limit')

    return over


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
