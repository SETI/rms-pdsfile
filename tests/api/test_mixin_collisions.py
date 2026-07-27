##########################################################################################
# tests/api/test_mixin_collisions.py
#
# Phase 5 breaks PdsFile up by moving groups of methods into mixin classes in
# private modules, leaving the `class PdsFile` statement itself in
# pdsfile/pdsfile.py. That is only safe while the mixins stay disjoint: two mixins
# defining the same name, or a mixin defining a name PdsFile also defines, would
# silently leave one copy dead, and the API-freeze manifest could not see it --
# it records the names and signatures a class exposes, not which base supplies
# them.
#
# So these checks are the freeze's blind spot, in their own file: section 6.4 of
# plans/2026-07-25-modernization-plan.md forbids editing tests/api/test_api_freeze.py.
#
# The mixins are discovered from PdsFile's bases rather than listed, so every
# later extraction PR is covered the moment it adds one.
#
# tests/api/conftest.py marks everything collected here holdings_free, so this
# module also runs in the hosted no-holdings job. Nothing below reads a holdings
# tree.
##########################################################################################

import ast
import inspect

import pytest

from pdsfile.pdsfile import PdsFile

# Names the class machinery puts in a class body's namespace rather than the
# author: the compiler's bookkeeping, plus the __dict__ and __weakref__
# descriptors, which land on whichever class in a hierarchy first needs them --
# for PdsFile's instances that is now the first mixin base, not PdsFile. None of
# them is what "this mixin defines a name" means, and leaving them in would make
# every pair of mixins collide.
_STRUCTURAL = {'__module__', '__qualname__', '__doc__', '__dict__', '__weakref__',
               '__firstlineno__', '__static_attributes__', '__annotations__'}


def _mixins():
    """The mixin bases of PdsFile, in declaration order."""

    return [base for base in PdsFile.__bases__ if base is not object]


def _defined_names(cls):
    """The names a class body itself defines, ignoring the structural ones."""

    return {name for name in vars(cls) if name not in _STRUCTURAL}


##########################################################################################
# The discovery itself has to be sound, or every check below passes vacuously
##########################################################################################
def test_the_mixins_are_found_and_come_from_private_modules():
    mixins = _mixins()

    assert mixins, ('PdsFile has no mixin bases, so every check in this module '
                    'would pass without examining anything')
    for mixin in mixins:
        assert mixin.__module__.startswith('pdsfile._'), (
            f'{mixin.__name__} is defined in {mixin.__module__}; Phase 5 mixins '
            f'live in private pdsfile modules')
        assert _defined_names(mixin), f'{mixin.__name__} defines nothing'


def test_the_class_statement_stays_in_pdsfile_pdsfile():
    # Pickled PdsFile instances -- the memcached cache holds live ones -- record
    # this module path, so the class statement may not move into a mixin module.
    assert PdsFile.__module__ == 'pdsfile.pdsfile'
    assert PdsFile.__bases__[-1] is object


##########################################################################################
# No name is defined twice
##########################################################################################
def test_no_two_mixins_define_the_same_name():
    seen = {}
    collisions = {}
    for mixin in _mixins():
        for name in _defined_names(mixin):
            if name in seen:
                collisions.setdefault(name, [seen[name]]).append(mixin.__name__)
            else:
                seen[name] = mixin.__name__

    assert not collisions, f'names defined by more than one mixin: {collisions}'


def test_no_mixin_is_shadowed_by_pdsfile_itself():
    # PdsFile's own body wins over every base, so a name in both places would make
    # the mixin's copy unreachable -- a move that silently did nothing.
    core = _defined_names(PdsFile)
    shadowed = {mixin.__name__: sorted(_defined_names(mixin) & core)
                for mixin in _mixins()
                if _defined_names(mixin) & core}

    assert not shadowed, f'names PdsFile redefines over a mixin: {shadowed}'


def test_every_mixin_name_is_reachable_through_pdsfile():
    # The point of the move is that callers see no difference. Whatever a mixin
    # defines -- private members included -- has to arrive on PdsFile as that
    # same object.
    for mixin in _mixins():
        for name in sorted(_defined_names(mixin)):
            assert (inspect.getattr_static(PdsFile, name)
                    is inspect.getattr_static(mixin, name)), (
                f'PdsFile.{name} does not resolve to {mixin.__name__}.{name}')


##########################################################################################
# Mixins carry behavior, never state
##########################################################################################
@pytest.mark.parametrize('forbidden', ['__init__', '__new__', '__slots__',
                                       '__init_subclass__', '__getattr__',
                                       '__setattr__'])
def test_a_mixin_defines_no_construction_or_attribute_hook(forbidden):
    # The Phase 5 rule is that mixins add no state and do not participate in
    # construction; PdsFile's own __init__ and _X_filled slots stay in core.
    offenders = [m.__name__ for m in _mixins() if forbidden in vars(m)]

    assert not offenders, f'{forbidden} defined by {offenders}'


def test_a_mixin_defines_only_callables_and_properties():
    strays = {}
    for mixin in _mixins():
        for name in sorted(_defined_names(mixin)):
            value = vars(mixin)[name]
            if not isinstance(value, (staticmethod, classmethod, property)) \
                    and not inspect.isroutine(value):
                strays.setdefault(mixin.__name__, []).append(name)

    assert not strays, (f'mixins hold class-level data, which belongs on PdsFile: '
                        f'{strays}')


##########################################################################################
# No mixin module imports the class it is a base of
##########################################################################################
def _modules_named_by(node, package):
    """The absolute module names one import statement reaches for.

    Both the module a `from X import y` reads out of and each `X.y` it could be
    naming, because `from . import pdsfile` and `from .pdsfile import PdsFile`
    are the same back-import written two ways. A relative level is resolved
    against the importing module's own package; an absolute one is already
    absolute and must not be prefixed with it.
    """

    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]

    if node.level == 0:
        base = node.module
    else:
        anchor = package
        for _ in range(node.level - 1):
            anchor = anchor.rpartition('.')[0]
        base = f'{anchor}.{node.module}' if node.module else anchor
    return [base] + [f'{base}.{alias.name}' for alias in node.names]


def _is_type_checking(test):
    """True for the test of an `if TYPE_CHECKING:` / `if typing.TYPE_CHECKING:`."""

    if isinstance(test, ast.Name):
        return test.id == 'TYPE_CHECKING'
    return isinstance(test, ast.Attribute) and test.attr == 'TYPE_CHECKING'


def _imports_that_run_at_import_time(tree):
    """Every import statement in a module that executes when the module is imported.

    Not the same as the top-level body: an import nested in a module-level `try`,
    `if` or `with` still runs, and `try: import x / except ImportError:` is a
    pattern this package already uses. Three things are skipped because they do
    not run at import time, so none of them can build the cycle:

      * function and method bodies -- a deferred import inside a method is the
        pattern the Phase 5 preamble prescribes, and flagging it would forbid the
        one spelling that is allowed;
      * class bodies, which cannot reach the module under construction usefully
        anyway;
      * `if TYPE_CHECKING:` blocks, which never execute.
    """

    def is_deferred(node):
        return (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                or (isinstance(node, ast.If) and _is_type_checking(node.test)))

    found = []

    def walk(body):
        for node in body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                found.append(node)
            elif not is_deferred(node):
                for field in ('body', 'orelse', 'finalbody'):
                    walk(getattr(node, field, None) or [])
                for handler in getattr(node, 'handlers', []):
                    walk(handler.body)

    walk(tree.body)
    return found


def test_no_mixin_module_imports_pdsfile_at_import_time():
    # pdsfile/pdsfile.py imports the mixin modules to build the class, so a mixin
    # importing the core module back at import time is a cycle. A method needing
    # the class object uses a function-local deferred import instead, which is why
    # the search above deliberately does not descend into function bodies.
    #
    # Some spellings raise ImportError on their own, but only when the name being
    # imported is not yet bound on the half-initialized module -- and by the time
    # pdsfile.py imports the first mixin, most of its module-level names are. So
    # `from pdsfile.pdsfile import PdsFile` raises while
    # `from pdsfile.pdsfile import repair_case` does not, and every spelling that
    # binds the module object itself is silent. This covers all of them. Read from
    # source, because an import that raises is one of the cases being ruled out.
    offenders = []
    for mixin in _mixins():
        package = mixin.__module__.rpartition('.')[0]
        tree = ast.parse(inspect.getsource(inspect.getmodule(mixin)))
        for node in _imports_that_run_at_import_time(tree):
            if 'pdsfile.pdsfile' in _modules_named_by(node, package):
                offenders.append(f'{mixin.__module__}:{node.lineno} -> pdsfile.pdsfile')

    assert not offenders, f'import-time back-imports of the core module: {offenders}'


##########################################################################################
# The declared order
##########################################################################################
def test_the_mixin_bases_are_listed_alphabetically():
    # The mixins are disjoint (above), so the MRO order changes nothing and the
    # ordering rule is free to be the one that stays checkable as Phase 5 adds
    # more of them: alphabetical by class name, object last.
    names = [mixin.__name__ for mixin in _mixins()]

    assert names == sorted(names), (
        f'PdsFile bases are {names}; list them alphabetically so every new mixin '
        f'has one obvious place to go')

##########################################################################################
