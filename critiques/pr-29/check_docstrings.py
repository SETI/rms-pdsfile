"""Check Google-style docstrings against the signatures and bodies they describe.

The rules enforced here are the mechanically checkable half of `doc_python.mdc` section
4. Semantic accuracy -- whether a description is true of the code -- is not checkable and
is not attempted.

Checks:

    P1  Every name in a `Parameters:` block is a real parameter of the signature.
    P2  Every parameter other than `self` and `cls` appears in `Parameters:` exactly
        once. `*args` and `**kwargs` count as parameters.
    P3  The section is spelled `Parameters:`; `Args:`, `Arguments:` and
        `Keyword arguments:` are rejected.
    R1  `Returns:` is present if and only if the body has a `return <expr>`, a `yield`
        or a `yield from`. A bare `return` does not count.
    E1  Every class named in a `Raises:` block is raised directly in the body, or its
        description attributes it to a mechanism the body demonstrably contains: a call
        it makes, item syntax (which counts as the corresponding dunder method), or
        tuple unpacking. The attribution is checked against the AST, so naming a
        mechanism the body does not use fails.
    E2  Every class raised directly in the body appears in `Raises:`.
    D1  No docstring line exceeds 90 columns.
    U1  No unicode smart quote, em-dash, en-dash or arrow anywhere in the file.
    M1  Every module, class and function has a docstring.

Usage:
    python check_docstrings.py FILE [FILE ...]

Exit status is 1 if any finding is reported, 0 otherwise.
"""

import ast
import pathlib
import re
import sys

MAX_DOC_COLUMNS = 90

SECTION_RE = re.compile(r'^(?P<indent>\s*)(?P<name>[A-Z][A-Za-z ]*):\s*$')
PARAM_ENTRY_RE = re.compile(r'^(?P<indent>\s*)(?P<name>\*{0,2}[A-Za-z_]\w*)'
                            r'(?P<type>\s*\([^)]*\))?:')
RAISE_ENTRY_RE = re.compile(r'^(?P<indent>\s*)(?P<name>[A-Za-z_][\w.]*)'
                            r'(?P<extra>\s*\([^)]*\))?:')
CALL_RE = re.compile(r'`?([A-Za-z_][\w.]*)\(\)`?|\b(unpacking)\b')

BANNED_SECTIONS = ('Args', 'Arguments', 'Keyword arguments', 'Keyword Arguments',
                   'Input', 'Inputs')

# The characters `doc_python.mdc` section 2 bans from .py files. They are written as
# escapes so that this file is itself free of them and can be checked by itself.
BANNED_CHARS = {
    '\u2018': 'left single quote',
    '\u2019': 'right single quote',
    '\u201c': 'left double quote',
    '\u201d': 'right double quote',
    '\u2013': 'en-dash',
    '\u2014': 'em-dash',
    '\u2192': 'rightwards arrow',
    '\u2190': 'leftwards arrow',
    '\u21d2': 'rightwards double arrow',
}


def sections_of(doc):
    """Split a docstring into its Google-style sections.

    A section starts at a line that is nothing but a capitalized name and a colon, and
    runs until the next line at or left of that name's indentation.

    Parameters:
        doc (str): the docstring text.

    Returns:
        dict: section name mapped to the list of lines that make up its body.
    """

    lines = doc.split('\n')
    result = {}
    k = 0
    while k < len(lines):
        match = SECTION_RE.match(lines[k])
        if not match:
            k += 1
            continue

        indent = len(match.group('indent'))
        body = []
        k += 1
        while k < len(lines):
            line = lines[k]
            if line.strip() and len(line) - len(line.lstrip()) <= indent:
                break
            body.append(line)
            k += 1

        result.setdefault(match.group('name'), []).extend(body)

    return result


def entries_of(body, pattern):
    """Return the leading names of the top-level entries in a section body.

    An entry starts at the smallest indentation present in the body; more deeply
    indented lines are continuations of the entry above them.

    Parameters:
        body (list): the lines making up the section body.
        pattern (re.Pattern): the regular expression that matches an entry's first line.

    Returns:
        list: pairs of entry name and the entry's full text.
    """

    filled = [line for line in body if line.strip()]
    if not filled:
        return []

    base = min(len(line) - len(line.lstrip()) for line in filled)

    result = []
    for line in body:
        if not line.strip():
            if result:
                result[-1][1].append(line)
            continue

        indent = len(line) - len(line.lstrip())
        match = pattern.match(line)
        if indent == base and match:
            result.append([match.group('name'), [line]])
        elif result:
            result[-1][1].append(line)

    return [(name, '\n'.join(text)) for name, text in result]


def signature_names(node):
    """Return the parameter names of a function definition, in order.

    `*args` and `**kwargs` are returned with their stars attached. `self` and `cls` are
    omitted.

    Parameters:
        node (ast.FunctionDef): the function definition.

    Returns:
        list: the parameter names.
    """

    args = node.args
    names = [a.arg for a in args.posonlyargs + args.args + args.kwonlyargs]
    if args.vararg:
        names.append('*' + args.vararg.arg)
    if args.kwarg:
        names.append('**' + args.kwarg.arg)

    return [n for n in names if n not in ('self', 'cls')]


def returns_a_value(node):
    """Report whether a function body returns a value or yields.

    Nested function and class definitions are not searched, because their returns belong
    to them and not to the enclosing function.

    Parameters:
        node (ast.FunctionDef): the function definition.

    Returns:
        bool: True if the body has a `return <expr>`, a `yield` or a `yield from`.
    """

    stack = list(node.body)
    while stack:
        item = stack.pop()
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(item, ast.Return) and item.value is not None:
            return True
        if isinstance(item, (ast.Yield, ast.YieldFrom)):
            return True
        stack.extend(ast.iter_child_nodes(item))

    return False


def raised_names(node):
    """Return the exception class names raised directly in a function body.

    A bare `raise` re-raises whatever is being handled and names nothing, so it
    contributes no name. Nested definitions are not searched.

    Parameters:
        node (ast.FunctionDef): the function definition.

    Returns:
        set: the class names appearing in `raise` statements.
    """

    names = set()
    stack = list(node.body)
    while stack:
        item = stack.pop()
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(item, ast.Raise) and item.exc is not None:
            exc = item.exc
            if isinstance(exc, ast.Call):
                exc = exc.func
            if isinstance(exc, ast.Name):
                names.add(exc.id)
            elif isinstance(exc, ast.Attribute):
                names.add(exc.attr)
        stack.extend(ast.iter_child_nodes(item))

    return names


def unpack_targets(node):
    """Return the binding targets of a node, wherever a node can bind names.

    Unpacking is not confined to assignment: a `for` target, a comprehension target and a
    `with ... as` all bind, and all raise the same way on a value of the wrong shape.

    Parameters:
        node (ast.AST): the node to inspect.

    Returns:
        list: the target nodes it binds, which may be empty.
    """

    if isinstance(node, ast.Assign):
        return list(node.targets)
    if isinstance(node, (ast.For, ast.AsyncFor, ast.comprehension)):
        return [node.target]
    if isinstance(node, (ast.withitem,)):
        return [node.optional_vars] if node.optional_vars else []

    return []


def called_names(node):
    """Return the mechanisms a function body uses that an exception can be blamed on.

    A call contributes the name it names: the identifier for a plain call, the attribute
    for a method call. Item syntax contributes the dunder method the interpreter reaches
    for, so an exception a docstring attributes to `__getitem__()` is recognized in a
    body that writes `self[key]`. Unpacking contributes `unpacking` wherever it binds --
    an assignment, a `for` target, a comprehension target, a `with ... as` -- because the
    `TypeError` from unpacking a value that is not iterable, and the `ValueError` from
    unpacking one of the wrong length, are raised by no call and by no `raise`, and are
    exactly the kind of failure a caller needs told about.

    Nested definitions are not searched.

    Parameters:
        node (ast.FunctionDef): the function definition.

    Returns:
        set: the mechanisms found.
    """

    names = set()
    stack = list(node.body)
    while stack:
        item = stack.pop()
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(item, ast.Call):
            func = item.func
            if isinstance(func, ast.Name):
                names.add(func.id)
            elif isinstance(func, ast.Attribute):
                names.add(func.attr)
        elif isinstance(item, ast.Subscript):
            if isinstance(item.ctx, ast.Store):
                names.add('__setitem__')
            elif isinstance(item.ctx, ast.Del):
                names.add('__delitem__')
            else:
                names.add('__getitem__')
        else:
            for target in unpack_targets(item):
                if isinstance(target, (ast.Tuple, ast.List)):
                    names.add('unpacking')
        stack.extend(ast.iter_child_nodes(item))

    return names


def definitions(tree):
    """Walk a module and yield each thing that needs a docstring.

    Parameters:
        tree (ast.Module): the parsed module.

    Returns:
        list: triples of qualified name, node, and node kind.
    """

    found = [('<module>', tree, 'module')]

    def walk(node, prefix):
        """Append every definition below one node, qualifying its name with a prefix.

        Parameters:
            node (ast.AST): the node to search below.
            prefix (str): the dotted prefix to put in front of each name found.
        """

        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                name = prefix + child.name
                found.append((name, child, 'class'))
                walk(child, name + '.')
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = prefix + child.name
                found.append((name, child, 'function'))
                walk(child, name + '.')
            else:
                walk(child, prefix)

    walk(tree, '')

    return found


def check_file(path, findings):
    """Run every check over one file and append its findings.

    Parameters:
        path (str): the file to check.
        findings (list): the list that findings are appended to, as triples of file,
            location and message.
    """

    text = pathlib.Path(path).read_text(encoding='utf-8')
    lines = text.split('\n')

    for number, line in enumerate(lines, start=1):
        for char, description in BANNED_CHARS.items():
            if char in line:
                findings.append((path, f'line {number}',
                                 f'U1: {description} ({char!r}) in a .py file'))

    tree = ast.parse(text)

    for name, node, kind in definitions(tree):
        doc = ast.get_docstring(node, clean=False)
        where = f'{name} (line {getattr(node, "lineno", 1)})'

        if doc is None:
            findings.append((path, where, f'M1: {kind} has no docstring'))
            continue

        # The first line of a docstring reaches the parser without the indentation and
        # the opening quotes that precede it in the file, so its width is restored from
        # the column the string constant starts at.
        opener = node.body[0].value.col_offset + 3

        for offset, line in enumerate(doc.split('\n')):
            column = len(line) if offset else len(line) + opener
            if column > MAX_DOC_COLUMNS:
                findings.append((path, where,
                                 f'D1: docstring line {offset + 1} is {column} columns'))

        found = sections_of(doc)

        for banned in BANNED_SECTIONS:
            if banned in found:
                findings.append((path, where, f'P3: section "{banned}:" is not '
                                              'Google style; use "Parameters:"'))

        if kind != 'function':
            if 'Parameters' in found:
                findings.append((path, where,
                                 'P1: a Parameters: section on a ' + kind))
            continue

        expected = signature_names(node)
        documented = [n for n, _ in entries_of(found.get('Parameters', []),
                                               PARAM_ENTRY_RE)]

        for entry in documented:
            if entry not in expected:
                findings.append((path, where,
                                 f'P1: "{entry}" is not a parameter of this signature'))

        for want in expected:
            count = documented.count(want)
            if count != 1:
                findings.append((path, where,
                                 f'P2: parameter "{want}" appears {count} times in '
                                 'Parameters:'))

        has_returns = 'Returns' in found or 'Yields' in found
        if returns_a_value(node) and not has_returns:
            findings.append((path, where, 'R1: body returns a value but there is no '
                                          'Returns: section'))
        if has_returns and not returns_a_value(node):
            findings.append((path, where, 'R1: Returns: section but the body returns '
                                          'no value'))

        raised = raised_names(node)
        called = called_names(node)
        documented_raises = entries_of(found.get('Raises', []), RAISE_ENTRY_RE)

        for entry, entry_text in documented_raises:
            short = entry.rpartition('.')[2]
            if short in raised:
                continue
            mentioned = [name for pair in CALL_RE.findall(entry_text)
                         for name in pair if name]
            attributed = [name for name in mentioned
                          if name.rpartition('.')[2] in called]
            if not attributed:
                findings.append((path, where,
                                 f'E1: Raises: names "{entry}", which the body neither '
                                 'raises nor attributes to a call it makes'))

        for want in sorted(raised):
            if not any(entry.rpartition('.')[2] == want
                       for entry, _ in documented_raises):
                findings.append((path, where,
                                 f'E2: body raises {want} but Raises: does not name it'))


def main(argv):
    """Check every file named on the command line.

    Parameters:
        argv (list): the file paths to check.

    Returns:
        int: 1 if anything was found, 0 otherwise.
    """

    findings = []
    for path in argv:
        check_file(path, findings)

    for path, where, message in findings:
        print(f'{path}: {where}: {message}')

    counts = {}
    for _, _, message in findings:
        counts[message.split(':')[0]] = counts.get(message.split(':')[0], 0) + 1

    print()
    print(f'{len(findings)} findings over {len(argv)} files')
    for code in sorted(counts):
        print(f'  {code}: {counts[code]}')

    return 1 if findings else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
