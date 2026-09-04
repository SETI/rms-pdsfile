Extending, Part A: a Rules File for a New Volume or Bundle Set
==============================================================

When the Node publishes a new volume set or bundle set, the package learns about it
through one new module: a *rules file* under :mod:`pdsfile.pds3file.rules` or
:mod:`pdsfile.pds4file.rules`. The module defines a subclass of
:class:`~pdsfile.pds3file.Pds3File` or :class:`~pdsfile.pds4file.Pds4File`, installs
dataset-specific translator tables on it, and registers it so that every path inside
the new set resolves to it (the machinery is drawn at the end of
:doc:`dev_guide_architecture`). Registration is a side effect of importing the module,
so beyond the module itself the package changes only where the wiring section below
points -- the import list that triggers that side effect, the rules package's
``__all__``, and the regenerated API manifest. No dispatch code changes anywhere.

A rules file is mostly data. Its tables are ``translator`` objects -- ordered lists of
``(regular expression, flags, result)`` rows -- matched against logical paths, and the
craft in writing one is describing the dataset's layout in those rows. This chapter
gives the skeleton and the wiring; the tables' meanings are catalogued in the
docstring of :mod:`pdsfile.pds3file.rules` (the shared defaults every subclass starts
from), and the 25 existing PDS3 modules are the corpus of worked examples.

The skeleton
------------

.. code-block:: python

    ##########################################################################################
    # pds3file/rules/NEWSET_xxxx.py
    ##########################################################################################

    """Rules for the NEWSET_xxxx volume set: one line saying what the data is.

    Say which volumes exist, what instrument or campaign produced them, and what
    each rule table below contributes. The module docstrings of the existing rule
    modules are the pattern to follow.
    """

    import re

    import translator

    import pdsfile.pds3file as pds3file

    ##########################################################################################
    # DESCRIPTION_AND_ICON
    ##########################################################################################

    description_and_icon_by_regex = translator.TranslatorByRegex([
        (r'volumes/NEWSET_xxxx/NEWSET_00../DATA(|/.*)', re.I,
         ('Data files by orbit', 'IMAGEDIR')),
    ])

    ##########################################################################################
    # Subclass definition
    ##########################################################################################

    class NEWSET_xxxx(pds3file.Pds3File):
        """The Pds3File subclass for NEWSET_xxxx."""

        pds3file.Pds3File.VOLSET_TRANSLATOR = \
            translator.TranslatorByRegex([('NEWSET_xxxx', re.I, 'NEWSET_xxxx')]) + \
            pds3file.Pds3File.VOLSET_TRANSLATOR

        DESCRIPTION_AND_ICON = description_and_icon_by_regex + \
                               pds3file.Pds3File.DESCRIPTION_AND_ICON

    ##########################################################################################
    # Update the global dictionary of subclasses
    ##########################################################################################

    pds3file.Pds3File.SUBCLASSES['NEWSET_xxxx'] = NEWSET_xxxx

Three statements do the registering, and each matters:

* **The translator prepend** onto ``VOLSET_TRANSLATOR``, inside the class body, maps the family of
  bundle set names to the registry key. It is written as *new entry plus old table*,
  which puts the new row in front: lookups try it before everything already
  registered, and the base catch-all mapping everything to ``default`` stays at the
  end. The pattern should cover every volume-set spelling the family uses (compare
  ``COISS_[0123x]xxx``, which claims four related volume sets for one class).
* **The rule-table assignments** install the dataset's behavior. There are four
  routes, and they differ in precedence -- ``table + inherited`` puts the module's
  rows in front, ``ASSOCIATIONS[key] += table`` puts them behind, outright assignment
  replaces the default, and ``FILESPEC_TO_BUNDLESET`` is extended at module level --
  and the docstring of :mod:`pdsfile.pds3file.rules` measures which route each table
  conventionally takes. Start from the tables the dataset actually needs; a module
  can be as small as no tables at all.
* **The registry assignment** into ``SUBCLASSES`` at the module tail binds the registry key to the
  class. The key must be what the translator produces; a mismatch leaves paths
  raising ``KeyError`` out of ``new_pdsfile``.

The smallest real example, and a full one
-----------------------------------------

:mod:`pdsfile.pds3file.rules.RES_xxxx` is the minimal case in the tree: no tables at
all, just the docstring, the class with its translator prepend, and the tail
registration -- every rule it uses is the inherited default. Read it first; it is 47
lines. Then read :mod:`pdsfile.pds3file.rules.COISS_xxxx` for the full spread: tables
installed by every route, an ``OPUS_ID_TO_SUBCLASS`` prepend at module level so OPUS
IDs resolve to the class, and a ``FILENAME_KEYLEN`` method (the number of leading
basename characters that group an observation's files together, 11 for Cassini ISS
images).

On the PDS4 side the shape is the same with different spellings: registry keys are
lower-case bundle set names (``uranus_occs_earthbased``), and the convention there
splits the file-specification tables into a sibling ``*_primary_filespec`` module.

Wiring the module in
--------------------

Creating the file is not enough; the module must be imported for its registration
side effects to run. Two lists name it:

1. The ``from .rules import (...)`` block at the tail of
   ``src/pdsfile/pds3file/__init__.py`` (``src/pdsfile/pds4file/__init__.py`` for a
   PDS4 module) -- this is the import that actually registers the subclass, and it
   must stay after the class body, because the rule module subclasses
   :class:`~pdsfile.pds3file.Pds3File` (or :class:`~pdsfile.pds4file.Pds4File`).
2. ``__all__`` in ``src/pdsfile/pds3file/rules/__init__.py`` (or
   ``src/pdsfile/pds4file/rules/__init__.py``), the package's public-name list.
   Only the import registers: in both generations the recorded ``__all__``
   currently trails the import block (``JNOSRU_xxxx`` on the PDS3 side, two
   modules on the PDS4 side), a gap each package's docstring measures as harmless
   because nothing imports through ``__all__`` -- name a new module in both lists
   anyway.

Adding a rule module **extends the frozen public surface**: the new class and module
are reachable via ``import pdsfile``, so ``tests/api/test_api_freeze.py`` will fail
against the recorded manifest until the manifest is regenerated. That is the gate
working as designed -- the surface change is deliberate, so regenerate the manifest
with ``scripts/dump_public_api.py`` and present the diff (which should be exactly the
new dataset's names) for review in the same change. Never edit the manifest by hand.

A description for the volume set also belongs in the holdings tree itself: the
``_volinfo/`` tables (see the file-format appendix of the user guide) are where
:meth:`~pdsfile._preload._PreloadMixin.load_volume_info` reads the text that
:attr:`~pdsfile._properties._PropertiesMixin.description` returns for the set and its
volumes. That is a holdings-tree edit, not a repository edit.

The standard test set
---------------------

A rule module's tests live in ``tests/rules/pds3/test_<name>.py`` (lower-cased module
name), built from the shared helpers in ``tests/rules/support.py``; thirteen of the
PDS3 modules currently have one, and a new dataset should. The standard set, taken
from the existing test modules:

.. code-block:: python

    import pytest

    import pdsfile.pds3file as pds3file
    from tests.rules.support import (
        PDS3_TEST_RESULTS_DIR as TEST_RESULTS_DIR,
    )
    from tests.rules.support import (
        associated_abspaths_test,
        opus_products_test,
    )


    @pytest.mark.parametrize(
        ('input_path', 'expected'),
        [
            ('volumes/NEWSET_xxxx/NEWSET_0001/DATA/FILE01.DAT',
             'NEWSET_xxxx/opus_products/FILE01.txt'),
        ]
    )
    def test_opus_products(request, input_path, expected):
        update = request.config.option.update
        opus_products_test(pds3file.Pds3File, input_path,
                           TEST_RESULTS_DIR + expected, update)


    @pytest.mark.parametrize(
        ('input_path', 'category', 'expected'),
        [
            ('volumes/NEWSET_xxxx/NEWSET_0001/DATA/FILE01.DAT',
             'volumes',
             'NEWSET_xxxx/associated_abspaths/FILE01.txt'),
        ]
    )
    def test_associated_abspaths(request, input_path, category, expected):
        update = request.config.option.update
        associated_abspaths_test(pds3file.Pds3File, input_path, category,
                                 TEST_RESULTS_DIR + expected, update)

The two golden tests compare :meth:`~pdsfile._opus._OpusMixin.opus_products` and
:meth:`~pdsfile._associations._AssociationsMixin.associated_abspaths` output for a
representative data file against a committed golden copy under
``tests/golden/full/pds3/<NEWSET_xxxx>/``; a run with ``--update`` -- or a first run,
since a missing golden is written rather than failed -- creates them against real
holdings, and they are then reviewed and committed (:doc:`dev_guide_goldens`). Modules whose rules define OPUS identifiers add
a round-trip test over a list of real paths, asserting that each path's
:attr:`~pdsfile._properties._PropertiesMixin.opus_id` leads back to the same logical
path through :meth:`~pdsfile._opus._OpusMixin.from_opus_id`;
several also assert ``VERSIONS`` behavior or translator coverage directly. Pick from
the existing test modules whichever assertions the new dataset's rules make
meaningful, and run the suite as :doc:`dev_guide_testing` describes.
