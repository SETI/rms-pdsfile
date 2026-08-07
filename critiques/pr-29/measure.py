"""Measure docstring coverage over a set of Python files.

It reports, per file, the line count, whether the module has a docstring, and how many
classes and functions do not; and, over all the files together, how many docstrings exist
and how many carry a Google-style section.

A section is counted only if a whole line of the docstring is one of the Google section
names. Two things that rules out. `Note:`, `Example:` and `Format:` are not sections for
this purpose: they appear in this package's older docstrings as ordinary prose headings,
and counting them would inflate the "already sectioned" figure without any parameter
having been documented. And a section name written mid-sentence -- prose that happens to
contain the word `Returns:` -- is not a section either, which a substring test would
miscount.

Usage:
    python measure.py FILE [FILE ...]
"""

import ast
import pathlib
import sys

SECTIONS = ('Parameters:', 'Args:', 'Arguments:', 'Returns:', 'Return:', 'Yields:',
            'Raises:', 'Input:')


def sections_in(doc):
    """Return the Google section names a docstring uses.

    A name counts only when it is the whole of a line, apart from indentation.

    Parameters:
        doc (str): the docstring text.

    Returns:
        set: the section names found.
    """

    return {line.strip() for line in doc.split('\n')} & set(SECTIONS)


def definitions(path):
    """Return the module docstring and the classes and functions of one file.

    Parameters:
        path (pathlib.Path): the file to parse.

    Returns:
        tuple: the module docstring or None, the list of class docstrings, and the list
        of pairs of function docstring and parameter-name list.
    """

    tree = ast.parse(path.read_text())
    classes = []
    functions = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes.append(ast.get_docstring(node))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = node.args
            names = [a.arg for a in args.posonlyargs + args.args + args.kwonlyargs]
            if args.vararg:
                names.append('*' + args.vararg.arg)
            if args.kwarg:
                names.append('**' + args.kwarg.arg)
            names = [n for n in names if n not in ('self', 'cls')]
            functions.append((ast.get_docstring(node), names))

    return ast.get_docstring(tree), classes, functions


def main(argv):
    """Measure every file named on the command line and print the totals.

    Parameters:
        argv (list): the file paths to measure.

    Returns:
        int: zero.
    """

    docstrings = []
    parameters = 0

    for name in argv:
        path = pathlib.Path(name)
        module_doc, classes, functions = definitions(path)
        count = sum(len(names) for _, names in functions)
        parameters += count
        docstrings.append(module_doc)
        docstrings.extend(classes)
        docstrings.extend(doc for doc, _ in functions)

        print(f'{path.name:24s} lines={len(path.read_text().splitlines()):5d} '
              f'moddoc={"Y" if module_doc else "N"} '
              f'classes={len(classes):3d} '
              f'undocumented={sum(1 for d in classes if not d):3d} '
              f'funcs={len(functions):4d} '
              f'undocumented={sum(1 for d, _ in functions if not d):4d} '
              f'params={count:4d}')

    present = [d for d in docstrings if d]
    sectioned = [d for d in present if sections_in(d)]

    print()
    print(f'docstrings that exist            : {len(present)}')
    print(f'  carrying a Google section      : {len(sectioned)}')
    print(f'  carrying none                  : {len(present) - len(sectioned)}')
    for word in SECTIONS:
        count = sum(1 for d in present if word in sections_in(d))
        if count:
            print(f'  using {word:16s}         : {count}')
    print(f'parameters, excluding self/cls   : {parameters}')

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
