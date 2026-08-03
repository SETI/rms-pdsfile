##########################################################################################
# tests/api/test_mixin_collisions.py
#
# Phase 5 breaks PdsFile up by moving groups of methods into mixin classes in
# private modules, leaving the `class PdsFile` statement itself in
# pdsfile/pdsfile.py. That is only safe while the mixins stay disjoint: two mixins
# defining the same name, or a mixin defining a name PdsFile or one of its direct
# subclasses also defines, would silently leave one copy dead, and the API-freeze
# manifest could not see it -- it records the names and signatures a class
# exposes, not which base supplies them.
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

import inspect

import pytest

from pdsfile.pds3file import Pds3File
from pdsfile.pds4file import Pds4File
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
    # The base list carries mixins only. A trailing `object` predated Phase 5 and
    # is gone; in Python 3 it is implicit, and the MRO is the same with or without
    # it (plans/2026-07-27-addendum-phase5-mixin-base-order.md).
    assert object not in PdsFile.__bases__
    assert all(base.__module__.startswith('pdsfile._')
               for base in PdsFile.__bases__), (
        f'PdsFile bases are '
        f'{[(b.__module__, b.__name__) for b in PdsFile.__bases__]}; the base '
        f'list carries Phase-5 mixins and nothing else')


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


@pytest.mark.parametrize('subclass', [Pds3File, Pds4File],
                         ids=['Pds3File', 'Pds4File'])
def test_no_mixin_is_shadowed_by_a_pdsfile_subclass(subclass):
    # The check above stops at PdsFile, but the subclasses are where PdsFile's
    # method surface is actually extended -- pdsfile/pds3file/__init__.py defines
    # the volume/volset aliases there -- and they are what the tools, OPUS and the
    # rule modules instantiate. A name a subclass defines wins over every base, so
    # a mixin name a subclass also defines is dead on the class callers use, and
    # the manifest cannot see that any more than it can see the PdsFile case.
    #
    # What this asserts is a name-discipline rule, not a defect a move introduces:
    # such a name was already shadowed before the extraction, when the copy lived
    # on PdsFile itself. It is worth pinning because the surfaces are now in
    # separate files, and because the shadowing would be silent either way.
    #
    # The rule is strict, so it can in principle reject a legitimate future move.
    # It does not today: the 34 (Pds3File) and 35 (Pds4File) names that override a
    # PdsFile name are class attributes and translator tables, which the Phase 5
    # mechanics keep on PdsFile, plus __init__, __repr__ and the four
    # use_shelves_only/require_shelves/set_logger/set_easylogger classmethods,
    # every one of which is on PR-22's explicit stay-list. None of them can reach
    # a mixin, so nothing this phase does can trip this check by accident.
    assert subclass in PdsFile.__subclasses__(), (
        f'{subclass.__name__} is not a direct subclass of PdsFile, so this check '
        f'is not looking where it thinks it is')

    own = _defined_names(subclass)
    shadowed = {mixin.__name__: sorted(_defined_names(mixin) & own)
                for mixin in _mixins()
                if _defined_names(mixin) & own}

    assert not shadowed, (f'names {subclass.__name__} redefines over a mixin: '
                          f'{shadowed}')


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
# The declared order
##########################################################################################
def test_the_mixin_bases_are_listed_alphabetically():
    # The mixins are disjoint (above), so the MRO order changes nothing and the
    # ordering rule is free to be the one that stays checkable as Phase 5 adds
    # more of them: alphabetical by class name. (The rule was written as
    # "alphabetical, object last"; the trailing object base is gone, and the
    # bases are mixins only.)
    names = [mixin.__name__ for mixin in _mixins()]

    assert names == sorted(names), (
        f'PdsFile bases are {names}; list them alphabetically so every new mixin '
        f'has one obvious place to go')

##########################################################################################
