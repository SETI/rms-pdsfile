##########################################################################################
# tests/core/test_stubbed_surfaces.py
#
# Every class member a test stub in this suite stands in for, bound against the real
# class.
#
# **What already has a guard, and what does not.** `monkeypatch.setattr(module, name,
# stub)` raises if `name` is not there, so replacing a collaborator that has been renamed
# or removed already fails. Nothing checks the other half: the stub's own contents. A
# test that installs `SimpleNamespace(Pds3File=SimpleNamespace(from_abspath=...))` says
# nothing about whether `Pds3File.from_abspath` still exists or still takes one argument,
# so the code under test goes on calling a shape the real class may no longer have, and
# every such test stays green while production breaks.
#
# That is observation 2100's general form, and it has already happened twice in this
# package: the five sibling tools `re_validate` reaches by attribute (fixed by
# test_re_validate.py's own signature test) and, one level down, a tool subprocess that
# imported whichever `pdsfile` was installed rather than the tree under test
# (observation 6607). The fix in both cases is the same in kind -- one test that
# exercises the real thing, however narrowly -- and this module is that test for the
# PdsFile class members the tool tests fabricate.
#
# Each row names where the stub lives, so a stub that is removed can take its row with
# it, and a stub that is added has an obvious place to declare itself. Nothing here is
# called: the point is the member and its signature, and calling these for real would
# need a holdings tree.
#
# The tests bind signatures and need no holdings tree.
##########################################################################################

import inspect

import pytest

from pdsfile import Pds3File, Pds4File

pytestmark = pytest.mark.holdings_free

# (class, member, positional arguments, keyword arguments, the stub that stands in).
SURFACES = [
    pytest.param(Pds3File, 'from_abspath', ('/holdings/volumes/VS_0xxx/VOL_0001',), {},
                 id='pds3-from_abspath'),
    pytest.param(Pds3File, 'set_log_root', ('/logs',), {},
                 id='pds3-set_log_root'),
    pytest.param(Pds3File, 'use_shelves_only', (True,), {},
                 id='pds3-use_shelves_only'),
    pytest.param(Pds3File, 'preload', ('/holdings',), {},
                 id='pds3-preload'),
    pytest.param(Pds3File, 'from_logical_path', ('volumes/VS_0xxx/VOL_0001',), {},
                 id='pds3-from_logical_path'),
    pytest.param(Pds4File, 'from_abspath', ('/pds4-holdings/bundles/BS/B',), {},
                 id='pds4-from_abspath'),
    pytest.param(Pds4File, 'use_shelves_only', (False,), {},
                 id='pds4-use_shelves_only'),
    pytest.param(Pds4File, 'preload', ('/pds4-holdings',), {},
                 id='pds4-preload'),
    pytest.param(Pds4File, 'from_logical_path', ('bundles/BS/B',), {},
                 id='pds4-from_logical_path'),
]

# Where each stubbed member is fabricated, kept beside the table it explains rather than
# inside it, because more than one test module stubs some of them.
#
#   from_abspath, set_log_root      tests/holdings_maintenance/test_re_validate.py
#   use_shelves_only, preload,      tests/holdings_maintenance/test_show_opus_products.py
#   from_abspath, from_logical_path


@pytest.mark.parametrize(('cls', 'member', 'args', 'kwargs'), SURFACES)
def test_a_stubbed_member_still_exists_and_takes_what_the_stub_takes(cls, member, args,
                                                                     kwargs):
    """The real class carries the member, and it binds the arguments the stub accepts."""

    assert hasattr(cls, member), f'{cls.__name__}.{member}'

    function = getattr(cls, member)
    assert callable(function), function

    inspect.signature(function).bind(*args, **kwargs)
