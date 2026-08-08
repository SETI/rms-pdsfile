"""Check each rule module's docstring against the rule tables that module defines.

The 36 rule modules share one vocabulary. `description_and_icon_by_regex` is defined in
26 of them, `associations_to_metadata` in 22, `default_viewables` in 22, `opus_products`
in 18; and a few tables belong to exactly one module, such as `s_rings_viewables`,
`spice_lookup`, `dsntrack_viewables` and `_f_ring_cross_products_list`. Writing 36
near-identical headers is therefore the task where a header lands on the wrong file,
names a table the module does not define, or omits the one table that makes the module
different. This script is the mechanical half of that problem. It cannot tell whether a
docstring describes the right mission; it can tell whether it describes the right tables.

Checks:

    T0  The module has no docstring, so nothing else can be evaluated.
    T1  The docstring names a rule table that this module does not define and that a
        sibling rule module does. This is the copy-paste defect stated exactly.
    T2  The module defines a top-level rule table that its docstring does not name.
    T3  The docstring backquotes an identifier that no rule module defines, that this
        module does not import, and that is not in ALLOWED. A misspelled table name
        lands here rather than in T1.
    T4  The docstring's summary line does not name the module it documents.

T1 and T2 are the two directions the plan asks for. T3 closes T1's gap: T1 only fires on
a name some module really defines, so a typo would pass it. T4 closes the remaining gap,
which is a docstring copied wholesale between two modules that define the same tables:
`COUVIS_8xxx.py` and `COVIMS_8xxx.py` define identical sets of 15 tables, so T1 and T2
are both silent on a straight swap between them and only T4 fires.

T4 reads the **summary line** and not the whole docstring, because these docstrings
cross-reference one another and a whole-docstring test passes vacuously on exactly the
copy it exists to catch: `COVIMS_8xxx.py`'s docstring names `COUVIS_8xxx.py` in its last
paragraph, so pasting the whole of it onto `COUVIS_8xxx.py` satisfies a
whole-docstring test and fails a summary-line one. The check has one remaining hole,
stated rather than left to be found: a module key that is a prefix of another key is
satisfied by the longer one, so a docstring copied from
`cassini_iss_fring_mosaics_rsfrench2025.py` onto `cassini_iss.py` passes T4. T1 and T2
both fire on that pair, which is why the hole is left open rather than closed with a
special case.

Conventions this script assumes, and which the docstrings it checks follow:

    * A rule table is named in backquotes and nothing else is, except file and
      directory paths, which contain a slash or a dot and so are not identifiers. A
      directory is written with a trailing slash for that reason.
    * A class attribute or method is written with its class, as
      `COUVIS_0xxx.DATA_SET_ID`, so the dot keeps it out of the identifier tests.
    * A dictionary key is written in double quotes rather than backquotes, so that
      the viewable-set and category names are not mistaken for rule tables.
    * Volume set and bundle set identifiers, mission names and instrument names are
      written as plain text.

A "rule table" here is any top-level assignment to a plain name. That includes the
lookup dictionaries `VG_28xx.py` builds its regular expressions from and the
`PRIMARY_FILESPEC_LIST` of the three `_primary_filespec.py` modules, which are not
translator objects. Drawing the line anywhere else would need a judgment about which
assignments matter, and a check that exercises judgment is a check that can be argued
with. Dunder names are permitted but not required, so a docstring may mention `__all__`
and does not have to.

Usage:
    python check_rule_tables.py FILE [FILE ...]

Exit status is 1 if any finding is reported, 0 otherwise.
"""

import ast
import pathlib
import re
import sys

# Identifiers a docstring may backquote although no rule module assigns them. Every
# entry needs a reason, and the list is printed with the findings so that it cannot grow
# silently.
ALLOWED = {
    # The three PdsFile classes. A rule module's docstring names the class its tables
    # are wired onto, and no rule module assigns these names at the top level: the
    # subclasses arrive by import and the base classes live one package up.
    'PdsFile', 'Pds3File', 'Pds4File',
}

IDENTIFIER = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
BACKQUOTED = re.compile(r'`+([^`]+)`+')


def top_level_names(tree):
    """Return the set of names assigned at the top level of a module.

    Parameters:
        tree (ast.Module): the parsed module.

    Returns:
        set: the assigned names, including dunder names.
    """

    names = set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)

    return names


def imported_names(tree):
    """Return the set of names one module binds by importing them.

    Parameters:
        tree (ast.Module): the parsed module.

    Returns:
        set: the bound names, taking the alias where one is given and the first
        component of a dotted module name otherwise.
    """

    names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                names.add(alias.asname or alias.name.split('.')[0])

    return names


def backquoted_identifiers(doc):
    """Return the identifiers a docstring writes in backquotes.

    A backquoted span that is not a bare identifier, such as a path or a dotted
    attribute, is skipped.

    Parameters:
        doc (str): the docstring text.

    Returns:
        set: the identifiers found.
    """

    return {span for span in BACKQUOTED.findall(doc) if IDENTIFIER.match(span)}


def module_key(path):
    """Return the name a module's own docstring has to contain.

    Parameters:
        path (pathlib.Path): the module file.

    Returns:
        str: the stem for a named module, and the package-qualified file name for an
        `__init__.py`, which has no distinguishing stem of its own.
    """

    if path.stem == '__init__':
        return f'{path.parent.parent.name}/{path.parent.name}/__init__.py'

    return path.stem


def main(argv):
    """Run every check over every file named on the command line.

    Parameters:
        argv (list): the file paths to check.

    Returns:
        int: 1 if any finding was reported, 0 otherwise.
    """

    paths = [pathlib.Path(name) for name in argv]
    trees = {path: ast.parse(path.read_text()) for path in paths}
    defined = {path: top_level_names(tree) for path, tree in trees.items()}

    vocabulary = {}
    for path, names in defined.items():
        for name in names:
            vocabulary.setdefault(name, []).append(path.name)

    keys = {module_key(path): path.name for path in paths}

    findings = []
    counts = {}

    def report(path, code, text):
        """Record one finding and count it under its code.

        Parameters:
            path (pathlib.Path): the file the finding is about.
            code (str): the check that produced it.
            text (str): the description printed after the code.
        """

        findings.append(f'{path}: {code}: {text}')
        counts[code] = counts.get(code, 0) + 1

    for path in paths:
        doc = ast.get_docstring(trees[path])

        if not doc:
            report(path, 'T0', 'module has no docstring')
            continue

        named = backquoted_identifiers(doc)
        imports = imported_names(trees[path])

        for name in sorted(named - defined[path]):
            if name in vocabulary:
                owners = ', '.join(sorted(vocabulary[name]))
                report(path, 'T1', f'docstring names "{name}", which this module does '
                                   f'not define; defined by {owners}')
            elif name not in imports and name not in ALLOWED:
                report(path, 'T3', f'docstring backquotes "{name}", which no rule '
                                   f'module defines and this module does not import')

        for name in sorted(defined[path] - named):
            if not name.startswith('__'):
                report(path, 'T2', f'module defines "{name}", which the docstring '
                                   f'does not name')

        key = module_key(path)
        if key not in doc.split('\n')[0]:
            report(path, 'T4', f'summary line does not name "{key}"')

        for other in sorted(keys):
            if other != key and other in doc:
                findings.append(f'{path}: --: docstring also names {other}')

    for line in findings:
        print(line)

    total = sum(counts.values())
    print()
    print(f'{total} findings over {len(paths)} files')
    for code in sorted(counts):
        print(f'  {code}: {counts[code]}')
    print()
    print(f'ALLOWED: {", ".join(sorted(ALLOWED))}')

    return 1 if total else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
