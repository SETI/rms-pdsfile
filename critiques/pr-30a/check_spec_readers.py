"""Check ToolSpec's per-field reader map against the code that reads the fields.

`ToolSpec` is data only: nothing in the module that defines it reads a field, and every
read happens somewhere else. Its docstring therefore states, for each field, which
function reads it, because "the spec carries this field" and "this tool acts on it" are
different claims and only the second is useful. That map is prose, and prose about which
of twenty-odd functions reads which of twenty-odd fields is exactly the kind of claim
that goes stale without anything noticing.

This derives the map from the AST and compares it against the docstring in both
directions.

Checks:

    S1  The docstring's entry for a field names a reader that does not read it.
    S2  A reader of a field is not named in the docstring's entry for it. **The unit
        depends on how widely the field is read.** For a field with more than
        `FUNCTION_LIMIT` readers the unit is the module -- `logname` has twenty readers
        and an entry listing all twenty would be unreadable, while the claim that
        matters, which shared module acts on the field and so which tools it reaches, is
        settled at module granularity. At or below that limit the unit is the function,
        so a field read in a few places must have all of them named and cannot name the
        reader that supports its story while staying silent about one that would
        contradict it.
    S3  A field is read nowhere in the package. An inert field is not necessarily a
        defect, but a docstring that describes one as if it drove something is, so
        every one is reported for a human to check against its prose.
    S4  A documented reader is written without a module qualifier, so it cannot be
        matched to one reader rather than to any function of that name.

A read is an attribute access `spec.<field>` or `SPEC.<field>` anywhere under the source
root, attributed to the function it appears in. That is a name filter, not a resolution:
a `spec` that is not a ToolSpec would be scored as one. Every `spec` under
`holdings_maintenance/` is a ToolSpec, and the filter stops at the field names ToolSpec
declares, so the two ways it could be wrong are a different object named `spec` carrying
a field of the same name, and a spec passed under a third name. Both are visible in the
output rather than silent, because S2 reports the reader it found by name.

A documented reader is a `module.name()` token inside the field's entry in the
`Attributes:` section, and **the module qualifier is required**. A bare name would match
a function of that name in any module, and this tree has several: `link_targets` exists
in `_linkshelf_common` and in both link shelf tools, and `initialize` through `update` in
all ten tool modules. An unqualified token is reported as S4 rather than matched
loosely.

**Every such token is read as a claim**, including one an entry mentions for some other
reason -- a function the value is passed on to, or one named as a counterexample. That
is deliberate rather than a limitation to work around, and it makes the parentheses
carry meaning: **an entry writes a reader with its parentheses and anything else without
them.** An entry that puts a non-reader in parentheses reads as though that function
acts on the field, which is the mistake S1 exists to catch, and it caught three of them
during this PR before the convention was written down.

**What this cannot catch, stated because a gate whose reach is unknown is worse than a
narrow one.**

1. *It checks attribution, never assertion.* An entry that names the right readers can
   still be wrong about everything else it says. Two defects found by review both lived
   inside the `handler_factories` entry, which this scored as fully correct throughout:
   where the drivers attach the factories, and how often. The entries this protects are
   exactly the entries whose interesting content it does not read.
2. *Above `FUNCTION_LIMIT` readers, one named reader per module satisfies S2.* `logname`
   has twenty readers across four modules and its entry names four, so an entry can name
   the reader that supports its story and stay silent about one that would contradict
   it.
3. *The reader detector is a name filter.* It records only `spec.<field>` and
   `SPEC.<field>` where the receiver is a bare name. A field read through `s = spec`,
   `self.spec`, `getattr(spec, name)` or a `dataclasses.replace()` copy is invisible, and
   S2 then stays silent for that module rather than reporting an unknown. No such read
   exists today, so on that point the gate rests on a property of the code rather than
   checking one.
4. *The parenthesis convention is enforced in one direction.* S1 catches a non-reader
   written with parentheses; nothing catches a genuine reader written without them,
   which would simply not be counted as a claim.

Usage:
    python check_spec_readers.py SRC_ROOT

`SRC_ROOT` is the `src/pdsfile` directory to walk. Exit status is 1 if any finding is
reported, 0 otherwise.
"""

import ast
import pathlib
import re
import sys

SPEC_MODULE = 'holdings_maintenance/_common.py'
SPEC_CLASS = 'ToolSpec'
SPEC_NAMES = ('spec', 'SPEC')

FUNCTION_LIMIT = 5          # at or below this many readers, S2's unit is the function

CALL_RE = re.compile(r'`?([A-Za-z_][\w.]*)\(\)`?')
SECTION_RE = re.compile(r'^(?P<indent>\s*)(?P<name>[A-Z][A-Za-z ]*):\s*$')
ENTRY_RE = re.compile(r'^(?P<indent>\s*)(?P<name>[A-Za-z_]\w*):')


def spec_class(root):
    """Return the ToolSpec class node and its field names, in declaration order.

    Parameters:
        root (pathlib.Path): the source root to look under.

    Returns:
        tuple: the ClassDef node, and the list of field names it declares.
    """

    tree = ast.parse((root / SPEC_MODULE).read_text(encoding='utf-8'))
    node = next(n for n in ast.walk(tree)
                if isinstance(n, ast.ClassDef) and n.name == SPEC_CLASS)
    fields = [item.target.id for item in node.body
              if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)]

    return node, fields


def documented_readers(node, fields):
    """Return the readers the class docstring names for each field.

    Only the `Attributes:` section is read, and only the entry whose leading name is the
    field's. A field with no entry, and an entry naming no function, both come back as an
    empty set, which S2 then reports against every reader found.

    Parameters:
        node (ast.ClassDef): the class whose docstring holds the map.
        fields (list): the field names to look for.

    Returns:
        dict: field name mapped to the set of reader names its entry cites.
    """

    doc = ast.get_docstring(node, clean=False) or ''
    lines = doc.split('\n')

    # Find the Attributes: section and the lines below it, which end at the first line
    # at or left of the section name's own indentation.
    body = []
    k = 0
    while k < len(lines):
        match = SECTION_RE.match(lines[k])
        if match and match.group('name') == 'Attributes':
            indent = len(match.group('indent'))
            k += 1
            while k < len(lines):
                line = lines[k]
                if line.strip() and len(line) - len(line.lstrip()) <= indent:
                    break
                body.append(line)
                k += 1
            break
        k += 1

    filled = [line for line in body if line.strip()]
    base = min((len(line) - len(line.lstrip()) for line in filled), default=0)

    entries = {}
    current = None
    for line in body:
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        match = ENTRY_RE.match(line)
        if indent == base and match and match.group('name') in fields:
            current = match.group('name')
            entries[current] = [line]
        elif current:
            entries[current].append(line)

    return {name: set(CALL_RE.findall('\n'.join(text)))
            for name, text in entries.items()}


def derived_readers(root, fields):
    """Return the functions that read each field, found by walking every module.

    A read outside any function definition is attributed to `<module>`, so a field read
    in a module body is reported rather than dropped.

    Parameters:
        root (pathlib.Path): the source root to walk.
        fields (list): the field names to look for.

    Returns:
        dict: field name mapped to the set of (module stem, function name) pairs that
        read it.
    """

    found = {name: set() for name in fields}

    for path in sorted(root.rglob('*.py')):
        tree = ast.parse(path.read_text(encoding='utf-8'))
        stem = path.stem

        def visit(node, where, stem=stem, found=found):
            """Record every spec field read below one node.

            Parameters:
                node (ast.AST): the node to search below.
                where (str): the name of the function the node sits in.
                stem (str): the module stem, bound at definition time.
                found (dict): the map being filled, bound at definition time.
            """

            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    visit(child, child.name)
                    continue
                if (isinstance(child, ast.Attribute)
                        and isinstance(child.value, ast.Name)
                        and child.value.id in SPEC_NAMES
                        and child.attr in found):
                    found[child.attr].add((stem, where))
                visit(child, where)

        visit(tree, '<module>')

    return found


def matches(documented, stem, function):
    """Report whether one documented reader name refers to one derived reader.

    The module qualifier is required; an unqualified name matches nothing here and is
    reported as S4 by the caller instead.

    Parameters:
        documented (str): the name the docstring cites, without its parentheses.
        stem (str): the module stem the read was found in.
        function (str): the function the read was found in.

    Returns:
        bool: True if the two refer to the same reader.
    """

    module, _, name = documented.rpartition('.')

    return bool(module) and name == function and module == stem


def main(argv):
    """Derive the map, compare it with the docstring, and print every finding.

    Parameters:
        argv (list): the source root to walk.

    Returns:
        int: 1 if anything was found, 0 otherwise.
    """

    root = pathlib.Path(argv[0])
    node, fields = spec_class(root)
    documented = documented_readers(node, fields)
    derived = derived_readers(root, fields)

    findings = []
    for field in fields:
        names = documented.get(field, set())
        readers = derived[field]

        for name in sorted(names):
            if '.' not in name:
                findings.append((field, f'S4: the entry names "{name}()" without a '
                                        'module qualifier'))
            elif not any(matches(name, stem, function) for stem, function in readers):
                findings.append((field, f'S1: the entry names "{name}()", which reads '
                                        'no such field'))

        if len(readers) <= FUNCTION_LIMIT:
            for stem, function in sorted(readers):
                if not any(matches(name, stem, function) for name in names):
                    findings.append((field, f'S2: read by {stem}.{function}, which the '
                                            'entry does not name, and this field has '
                                            f'{len(readers)} readers in all'))
        else:
            for stem in sorted({stem for stem, _ in readers}):
                if not any(matches(name, stem, function)
                           for name in names
                           for reader_stem, function in readers if reader_stem == stem):
                    functions = sorted(f for s, f in readers if s == stem)
                    findings.append((field, f'S2: read in {stem}.py, by '
                                            f'{", ".join(functions)}, and the entry '
                                            'names no reader there'))

        if not readers:
            findings.append((field, 'S3: read nowhere under the source root'))

    for field, message in findings:
        print(f'{SPEC_CLASS}.{field}: {message}')

    counts = {}
    for _, message in findings:
        counts[message.split(':')[0]] = counts.get(message.split(':')[0], 0) + 1

    print()
    print(f'{len(findings)} findings over {len(fields)} fields')
    for code in sorted(counts):
        print(f'  {code}: {counts[code]}')

    return 1 if findings else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
