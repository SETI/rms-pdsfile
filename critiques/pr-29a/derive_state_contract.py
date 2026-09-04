"""Derive, from the AST, the PdsFile-side names a mixin module's bodies reach.

Each mixin class opens with a paragraph naming every PdsFile attribute, property and
sibling-mixin method its bodies read or write. That paragraph is prose, so nothing
checks it and it drifts. This script derives the same list from the code and compares it
against the docstring in both directions.

How a name is derived
---------------------

Every `ast.Attribute` node in the module is examined. What decides whether it counts is
the **receiver**, not the attribute name, because several PdsFile members share a name
with a builtin method: `split` and `copy` are PdsFile members and also `str.split` and
`list.copy`, and `abspath`, `basename`, `exists` and `isdir` are PdsFile members and also
`os.path` functions. Matching on the name alone scores every `str.split(...)` in a mixin
as a PdsFile read.

A receiver is classified as one of three things:

    PDSFILE      `self`, `cls`, `type(self)`, `type(cls)`, or one of the class objects
                 `PdsFile`, `Pds3File` and `Pds4File` by name. The attribute is a PdsFile
                 member whatever it is called, so it counts unconditionally.
    NOT_PDSFILE  a module bound by an `import` statement; a literal, an f-string, a
                 display or a comprehension; a call to a builtin constructor; the result
                 of a str, list, dict or set method called on something that is not a
                 PdsFile; or a local name every binding of which is one of those.
    UNKNOWN      anything else -- a parameter, a subscript, the result of a call. The
                 attribute counts only if its name is in the PdsFile-side universe.

The universe is every name defined in a class body of `pdsfile.py`, of the ten `_*.py`
modules or of the two subclass initializers, plus every `self.X` and `cls.X` that is
assigned in one of those files. It exists to keep the UNKNOWN branch from scoring
`pdstable` and `pdslogger` calls as PdsFile reads, and it stops at the classes a mixin
can reach through `self`: widening it to the rule modules would admit a name as ordinary
as `name`.

Names the module itself defines are dropped: a mixin's methods call each other, and
those calls are not external dependencies. A `self.X` the module assigns is **not**
dropped, because writing a slot that PdsFile created is a dependency on PdsFile, not a
definition of anything.

How the docstring is read
-------------------------

Two directions, and they are deliberately asymmetric.

    MISSING    a derived name that appears nowhere in the class docstring. The whole
               docstring is searched, prose included, because a sibling-mixin reach is
               often named in a sentence rather than in the list.
    UNCLAIMED  a name listed in an enumerated contract block that the bodies do not
               reach. Only the blocks are searched, not the prose, because a docstring
               legitimately names a member in order to say it is *not* a dependency.

An enumerated block is the run of indented lines that follows a paragraph ending in
`not in scope:` or in `sibling mixins:`, up to the next blank line.

A third report, STRANDED, lists attributes read off `self` or `cls` whose names are in
no class body anywhere in the package. That is the failure the "class attributes stay on
PdsFile" rule exists to prevent, and it is what makes this more than a docstring check.

A fourth, VACUOUS, fires when a module reaches PdsFile-side names but its docstring
carries no enumerated block at all. Without one the UNCLAIMED direction has nothing to
read and cannot report anything, so a file in that state would pass by running half the
check. It is reported rather than passed.

Usage:
    python derive_state_contract.py SRC_DIR FILE [FILE ...]

Exit status is 1 if any file reports a finding, 0 otherwise.
"""

import ast
import pathlib
import re
import sys

UNIVERSE_FILES = ('pdsfile.py', '_associations.py', '_derived_paths.py', '_index_rows.py',
                  '_local_fs.py', '_opus.py', '_path_utils.py', '_preload.py',
                  '_properties.py', '_shelves.py', '_sorting.py',
                  'pds3file/__init__.py', 'pds4file/__init__.py')

ANYWHERE_GLOBS = ('*.py', 'pds3file/*.py', 'pds4file/*.py', 'pds3file/rules/*.py',
                  'pds4file/rules/*.py')

SELF_NAMES = ('self', 'cls')

# The class objects themselves, which `_opus.py` reaches through a deferred import so that
# it can enumerate the direct subclasses of PdsFile. An attribute read off one of these is
# a PdsFile read as surely as one read off `cls`.
CLASS_NAMES = ('PdsFile', 'Pds3File', 'Pds4File')

BUILTIN_CONSTRUCTORS = frozenset((
    'str', 'bytes', 'list', 'tuple', 'set', 'frozenset', 'dict', 'int', 'float', 'bool',
    'sorted', 'reversed', 'enumerate', 'zip', 'range', 'len', 'open', 'repr', 'format',
    'abs', 'min', 'max', 'sum', 'round',
))

# Methods of str, list, dict, set and tuple whose result is a builtin value. A call to
# one of these on a receiver that is not a PdsFile yields a builtin, so attributes read
# off the result are not PdsFile reads.
BUILTIN_METHODS = frozenset((
    'capitalize', 'casefold', 'center', 'count', 'encode', 'endswith', 'expandtabs',
    'find', 'format_map', 'index', 'isalnum', 'isalpha', 'isascii', 'isdecimal',
    'isdigit', 'isidentifier', 'islower', 'isnumeric', 'isprintable', 'isspace',
    'istitle', 'isupper', 'join', 'ljust', 'lower', 'lstrip', 'partition', 'removeprefix',
    'removesuffix', 'replace', 'rfind', 'rindex', 'rjust', 'rpartition', 'rsplit',
    'rstrip', 'split', 'splitlines', 'startswith', 'strip', 'swapcase', 'title',
    'translate', 'upper', 'zfill',
    'append', 'extend', 'insert', 'pop', 'remove', 'reverse', 'sort',
    'keys', 'values', 'items', 'get', 'setdefault', 'update',
    'union', 'intersection', 'difference', 'symmetric_difference', 'add', 'discard',
    'copy',
))

BLOCK_MARKERS = ('not in scope', 'sibling mixin')

IDENTIFIER_RE = re.compile(r'[A-Za-z_]\w*')

# A block entry names a member unqualified. A dotted reference such as `PdsFile.__init__`
# is prose about where the member lives, not a claim that this module reaches it, so the
# lookbehind drops the part after the dot.
BLOCK_NAME_RE = re.compile(r'(?<![.\w])([A-Za-z_]\w*)')

# Words that appear in an enumerated block as prose rather than as a member name. The
# blocks read as sentences where the entry needs a qualification, so the harvest has to
# drop ordinary English; anything that is not in the universe is dropped anyway, and
# these are the words that collide with a real member name.
BLOCK_PROSE_WORDS = frozenset((
    'none', 'and', 'the', 'on', 'in', 'of', 'to', 'a', 'an', 'is', 'it', 'its', 'or',
    'plus', 'which', 'that', 'when', 'each', 'every', 'from', 'with', 'for', 'first',
    'use', 'then', 'fills', 'writes', 'object', 'back', 'cache', 'afterwards', 'below',
    'slots', 'lazy', 'value', 'see', 'read', 'written', 'class', 'attribute',
    'attributes', 'instance', 'other', 'methods', 'called', 'properties', 'property',
    'interpreter', 'supplies', 'two', 'one', 'three', 'four', 'self', 'cls', 'still',
    'empty', 'own', 'column', 'info', 'table', 'newly', 'built', 'row', 'filled',
    'directory', 'visits', 'list', 'mutated', 'place', 'child', 'turns', 'out', 'be',
    'optional', 'hook', 'rule', 'modules', 'supply', 'translators', 'up', 'not',
))


def universe_names(src):
    """Return every attribute name a PdsFile-side class body defines or assigns.

    The set is deliberately confined to the classes a mixin can reach through `self`:
    `PdsFile`, the nine other mixins, and the `Pds3File` and `Pds4File` subclasses. It is
    the filter applied to attributes whose receiver could not be resolved, so widening it
    to every rule module would let ordinary names such as `name` through.

    Parameters:
        src (pathlib.Path): the `src/pdsfile` directory.

    Returns:
        set: the names.
    """

    names = set()
    for relative in UNIVERSE_FILES:
        names |= defined_names(ast.parse((src / relative).read_text(encoding='utf-8')))

    return names


def anywhere_names(src):
    """Return every attribute name any class in the package defines or assigns.

    This is the wider set the STRANDED report is measured against, so that a hook such as
    `opus_prioritizer`, which only the rule modules define, is not reported as belonging
    to nothing.

    Parameters:
        src (pathlib.Path): the `src/pdsfile` directory.

    Returns:
        set: the names.
    """

    names = set()
    for pattern in ANYWHERE_GLOBS:
        for path in sorted(src.glob(pattern)):
            names |= defined_names(ast.parse(path.read_text(encoding='utf-8')))

    return names


def defined_names(tree):
    """Return the names one module's class bodies define, plus its `self.X` writes.

    A class body contributes its methods and its assignments. A `self.X` or `cls.X` on
    the left of an assignment contributes `X` from anywhere in the module, because that
    is how the lazy-property slots come into existence.

    Parameters:
        tree (ast.Module): the parsed module.

    Returns:
        set: the names.
    """

    names = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    names.add(item.name)
                elif isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            names.add(target.id)
                elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    names.add(item.target.id)

        if isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            stack = list(targets)
            while stack:
                target = stack.pop()
                if (isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name)
                        and target.value.id in SELF_NAMES):
                    names.add(target.attr)
                elif isinstance(target, (ast.Tuple, ast.List)):
                    stack.extend(target.elts)

    return names


def class_members(tree):
    """Return the names one module's class bodies define.

    Only definitions: a method, or an assignment in a class body. A `self.X` write is
    deliberately excluded, because assigning a slot that `PdsFile.__init__` created is a
    use of PdsFile's state rather than a definition of the module's own.

    Parameters:
        tree (ast.Module): the parsed module.

    Returns:
        set: the names.
    """

    names = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                names.add(item.name)
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        names.add(target.id)
            elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                names.add(item.target.id)

    return names


def imported_modules(tree):
    """Return the names an `import` statement binds at module level.

    `import os.path` binds `os`, so the root of `os.path.exists(...)` resolves here.

    Parameters:
        tree (ast.Module): the parsed module.

    Returns:
        set: the bound names.
    """

    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.asname or alias.name.split('.')[0])

    return names


class Scope:
    """One function body's view of which local names hold builtin values.

    A name is treated as holding a builtin value if **any** binding of it in the body is
    a builtin-valued expression. The asymmetry is deliberate: a name that ever holds a
    string is a string for the purpose of this check, and these bodies do not rebind a
    name from a string to a PdsFile.

    Parameters:
        modules (set): the names bound by an `import` in the enclosing module.
    """

    def __init__(self, modules):
        self.modules = modules
        self.builtin_locals = set()

    def is_builtin(self, node):
        """Report whether an expression provably yields a builtin value.

        Parameters:
            node (ast.AST): the expression.

        Returns:
            bool: True if it does.
        """

        # None, True and False are sentinels rather than values of a builtin container
        # type: `pdsf = None` is how a PdsFile-valued name is cleared, so treating it as
        # a binding to a builtin would lose every attribute read through that name.
        if isinstance(node, ast.Constant):
            return not isinstance(node.value, (bool, type(None)))

        if isinstance(node, (ast.JoinedStr, ast.List, ast.Tuple, ast.Dict, ast.Set,
                             ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp,
                             ast.Compare)):
            return True

        if isinstance(node, ast.BoolOp):
            return all(self.is_builtin(value) for value in node.values)

        if isinstance(node, ast.BinOp):
            return self.is_builtin(node.left) or self.is_builtin(node.right)

        if isinstance(node, ast.Name):
            return node.id in self.modules or node.id in self.builtin_locals

        if isinstance(node, ast.Attribute):
            root, _ = chain_root(node)
            return isinstance(root, ast.Name) and root.id in self.modules

        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in BUILTIN_CONSTRUCTORS:
                return True
            if isinstance(func, ast.Attribute):
                if self.is_builtin(func.value):
                    return True
                return func.attr in BUILTIN_METHODS and not self.is_pdsfile(func.value)

        return False

    def is_pdsfile(self, node):
        """Report whether an expression is certainly a PdsFile object or class.

        Parameters:
            node (ast.AST): the expression.

        Returns:
            bool: True for `self`, `cls`, `type(self)`, `type(cls)` and a class by name.
        """

        if isinstance(node, ast.Name):
            return node.id in SELF_NAMES or node.id in CLASS_NAMES

        return _type_call_of_self(node)


def _type_call_of_self(node):
    """Report whether a node is `type(self)` or `type(cls)`.

    Parameters:
        node (ast.AST): the expression.

    Returns:
        bool: True if it is.
    """

    return (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id == 'type' and len(node.args) == 1
            and isinstance(node.args[0], ast.Name) and node.args[0].id in SELF_NAMES)


def chain_root(node):
    """Return the innermost expression of an attribute chain, and whether it is pure.

    A chain is pure when every link is an attribute access, so `os.path.exists` is pure
    with root `os` and `self.parent().basename` is not.

    Parameters:
        node (ast.AST): the expression.

    Returns:
        tuple: the root expression, and True if every link was an attribute access.
    """

    pure = True
    while True:
        if isinstance(node, ast.Attribute):
            node = node.value
        elif isinstance(node, ast.Subscript):
            node = node.value
            pure = False
        elif isinstance(node, ast.Call):
            node = node.func
            pure = False
        else:
            return (node, pure)


class Deriver(ast.NodeVisitor):
    """Walk one module and collect the PdsFile-side names its bodies reach.

    Parameters:
        modules (set): the names bound by an `import` in this module.
        universe (set): every name a PdsFile-side class body defines.
        anywhere (set): every name any class body in the package defines.
    """

    def __init__(self, modules, universe, anywhere):
        self.modules = modules
        self.universe = universe
        self.anywhere = anywhere
        self.reads = {}
        self.writes = {}
        self.stranded = {}
        self.scope = Scope(modules)

    def is_pdsfile(self, node):
        """Report whether an expression is certainly a PdsFile object or class.

        Parameters:
            node (ast.AST): the expression.

        Returns:
            bool: True for `self`, `cls`, `type(self)`, `type(cls)` and a class by name.
        """

        if isinstance(node, ast.Name):
            return node.id in SELF_NAMES or node.id in CLASS_NAMES

        return _type_call_of_self(node)

    def classify(self, node):
        """Classify a receiver expression.

        Parameters:
            node (ast.AST): the expression an attribute is read off.

        Returns:
            str: one of `pdsfile`, `not_pdsfile` or `unknown`.
        """

        if self.is_pdsfile(node):
            return 'pdsfile'

        root, pure = chain_root(node)
        if isinstance(root, ast.Name) and pure and self.is_pdsfile(root):
            # An attribute of a PdsFile holds some other kind of value, so a second
            # attribute read off it is not a PdsFile read. This is what stops
            # `self.abspath.split('/')` scoring `split`. The chain has to be pure: the
            # result of calling a PdsFile method can be another PdsFile.
            return 'not_pdsfile'

        if self.scope.is_builtin(node):
            return 'not_pdsfile'

        return 'unknown'

    def collect_builtin_locals(self, node):
        """Record which of one function's local names hold builtin values.

        The pass runs to a fixed point, because a name can be bound from another local.

        Parameters:
            node (ast.FunctionDef): the function definition.
        """

        self.scope = Scope(self.modules)
        bindings = []
        for item in ast.walk(node):
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    bindings.append((target, item.value))
            elif ((isinstance(item, ast.AnnAssign) and item.value is not None)
                  or isinstance(item, ast.AugAssign)):
                bindings.append((item.target, item.value))
            elif isinstance(item, (ast.For, ast.AsyncFor, ast.comprehension)):
                # A binding whose value is the iterable, not an element of it: a list is
                # a builtin but its elements can be anything, so an iteration never
                # marks its target.
                bindings.append((item.target, None))
            elif isinstance(item, ast.withitem) and item.optional_vars is not None:
                bindings.append((item.optional_vars, item.context_expr))

        for _ in range(4):
            before = set(self.scope.builtin_locals)
            for target, value in bindings:
                if value is None or not self.scope.is_builtin(value):
                    continue
                stack = [target]
                while stack:
                    item = stack.pop()
                    if isinstance(item, ast.Name):
                        self.scope.builtin_locals.add(item.id)
                    elif isinstance(item, (ast.Tuple, ast.List, ast.Starred)):
                        stack.extend(getattr(item, 'elts', [])
                                     or [getattr(item, 'value', None)])
            if self.scope.builtin_locals == before:
                break

    def record(self, node):
        """Classify one attribute node and record it if it is a PdsFile-side reach.

        Parameters:
            node (ast.Attribute): the attribute node.
        """

        kind = self.classify(node.value)
        if kind == 'not_pdsfile':
            return

        written = isinstance(node.ctx, (ast.Store, ast.Del))

        if kind == 'unknown':
            if node.attr not in self.universe:
                return
            if node.attr in BUILTIN_METHODS:
                # `split` and `copy` are PdsFile members and also `str.split` and
                # `list.copy`. A name that is both counts only where the receiver is
                # provably a PdsFile, which an unknown receiver is not.
                return
        elif node.attr not in self.anywhere and not node.attr.startswith('__'):
            self.stranded.setdefault(node.attr, []).append(node.lineno)

        table = self.writes if written else self.reads
        table.setdefault(node.attr, []).append(node.lineno)

    def run(self, tree):
        """Walk a whole module, one function scope at a time.

        A nested definition is a scope of its own and is walked separately, not as part
        of the function that encloses it.

        Parameters:
            tree (ast.Module): the parsed module.
        """

        # Every function is walked on its own, with its own scope, and a nested definition
        # is not walked as part of the function that encloses it. A closure has its own
        # local names, so sharing a scope would let one function's string-valued local
        # decide how the other's attribute reads are classified. Measured over every
        # module in this package the two give the same answer, so this is a statement
        # about what the derivation means rather than a correction to a result.
        functions = [n for n in ast.walk(tree)
                     if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]

        for function in functions:
            self.collect_builtin_locals(function)
            stack = list(function.body)
            while stack:
                item = stack.pop()
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef,
                                     ast.ClassDef)):
                    continue
                if isinstance(item, ast.Attribute):
                    self.record(item)
                stack.extend(ast.iter_child_nodes(item))

        # Module-level code outside any function.
        self.scope = Scope(self.modules)
        for item in tree.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            for child in ast.walk(item):
                if isinstance(child, ast.Attribute):
                    self.record(child)


def paragraphs_of(doc):
    """Split a docstring into paragraphs at its blank lines.

    Parameters:
        doc (str): the class docstring.

    Returns:
        list: one list of lines per paragraph, in order.
    """

    found = []
    current = []
    for line in doc.split('\n'):
        if line.strip():
            current.append(line)
        elif current:
            found.append(current)
            current = []

    if current:
        found.append(current)

    return found


def contract_blocks(doc):
    """Return the names listed in a docstring's enumerated contract blocks.

    A block is the paragraph that follows one whose text, unwrapped, ends in a colon and
    carries one of the block markers.

    Parameters:
        doc (str): the class docstring.

    Returns:
        set: the names the blocks list.
    """

    found = paragraphs_of(doc)
    names = set()

    for k, paragraph in enumerate(found[:-1]):
        text = ' '.join(line.strip() for line in paragraph)
        if not text.endswith(':'):
            continue
        if not any(marker in text for marker in BLOCK_MARKERS):
            continue

        for line in found[k + 1]:
            for word in BLOCK_NAME_RE.findall(line):
                if word.lower() not in BLOCK_PROSE_WORDS:
                    names.add(word)

    return names


def mentioned_names(doc):
    """Return every identifier-shaped token in a docstring.

    Parameters:
        doc (str): the class docstring.

    Returns:
        set: the tokens.
    """

    return set(IDENTIFIER_RE.findall(doc))


def class_of(tree):
    """Return the module's single top-level class definition, or None.

    Parameters:
        tree (ast.Module): the parsed module.

    Returns:
        ast.ClassDef: the class, or None if the module defines none.
    """

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            return node

    return None


def check_file(path, universe, anywhere):
    """Derive one module's contract and compare it against the class docstring.

    Parameters:
        path (pathlib.Path): the module to check.
        universe (set): every name a PdsFile-side class body defines.
        anywhere (set): every name any class body in the package defines.

    Returns:
        tuple: the report lines, and the number of findings.
    """

    tree = ast.parse(path.read_text(encoding='utf-8'))
    own = class_members(tree)
    module_functions = {node.name for node in tree.body
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}

    deriver = Deriver(imported_modules(tree), universe, anywhere)
    deriver.run(tree)

    reads = {n for n in deriver.reads if n not in own and n not in module_functions}
    writes = {n for n in deriver.writes if n not in module_functions}
    stranded = {n: v for n, v in deriver.stranded.items() if n not in own}

    # A module of free functions carries its contract in the module docstring, because
    # there is no class for it to sit on. `_path_utils.py` is that module: its functions
    # take the class as an argument and reach the same PdsFile-side names a mixin does.
    node = class_of(tree)
    doc = ast.get_docstring(node or tree, clean=False)
    if doc is None:
        where = 'class' if node else 'module'
        return ([f'{path.name}: no {where} docstring to check'], 1)

    mentioned = mentioned_names(doc)
    listed = contract_blocks(doc) & universe

    derived = reads | writes
    missing = sorted(derived - mentioned)
    unclaimed = sorted(listed - derived - own)

    report = [f'{path.name}: {len(derived)} reached ({len(reads)} read, '
              f'{len(writes)} written), {len(listed)} listed in the contract block']
    if derived and not listed:
        # The UNCLAIMED direction reads only the enumerated blocks, so a docstring that
        # carries none silently exercises half the check. Say so rather than pass.
        report.append('  VACUOUS   the docstring has no enumerated contract block, so '
                      'nothing can be reported UNCLAIMED')
    for name in missing:
        lines = sorted(set(deriver.reads.get(name, []) + deriver.writes.get(name, [])))
        report.append(f'  MISSING   {name} (line {lines[0]}) is reached but the '
                      'docstring never names it')
    for name in unclaimed:
        report.append(f'  UNCLAIMED {name} is listed in the contract block but no body '
                      'reaches it')
    for name, lines in sorted(stranded.items()):
        report.append(f'  STRANDED  {name} (line {lines[0]}) is read off self or cls but '
                      'no class body defines it')

    vacuous = 1 if (derived and not listed) else 0

    return (report, len(missing) + len(unclaimed) + len(stranded) + vacuous)


def main(argv):
    """Check every module named on the command line.

    Parameters:
        argv (list): the `src/pdsfile` directory followed by the modules to check.

    Returns:
        int: 1 if anything was found, 0 otherwise.
    """

    src = pathlib.Path(argv[0])
    universe = universe_names(src)
    anywhere = anywhere_names(src)

    total = 0
    for name in argv[1:]:
        report, count = check_file(pathlib.Path(name), universe, anywhere)
        total += count
        for line in report:
            print(line)

    print()
    print(f'{total} findings over {len(argv) - 1} files, '
          f'universe {len(universe)} names')

    return 1 if total else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
