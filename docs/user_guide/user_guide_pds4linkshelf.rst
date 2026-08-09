pds4linkshelf
=============

``pds4linkshelf`` finds the links inside a PDS4 bundle's files and records them. It is
the PDS4 half of the pair whose PDS3 half is :doc:`user_guide_pdslinkshelf`, and the scan
itself is the largest thing the two do differently, because a PDS4 label names the file
it describes in a ``<file_name>`` element rather than in ``KEYWORD = FILENAME`` syntax.

The command line is the shared one, described in
:doc:`user_guide_maintenance_tools`, with no options of its own.

.. code-block:: text

   pds4linkshelf <task> <bundle> [<bundle> ...] [--log LOG] [--quiet]

What it writes
--------------

Two files per bundle, in the ``_linkshelf-`` parallel of the category:

.. code-block:: text

   $PDS4_HOLDINGS_DIR/_linkshelf-bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023_links.pickle
   $PDS4_HOLDINGS_DIR/_linkshelf-bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023_links.py

What counts as a link
---------------------

The ``<file_name>`` element, matched case-insensitively, over five extensions: ``.XML``,
``.LBLX``, ``.CAT``, ``.FMT`` and ``.SFD``. Those five are also the extensions a file is
not required to have a label of its own for.

Two of the tables the PDS3 program relies on are **empty** here, and the difference is
visible in what a run reports:

* There is no repair table, so no PDS4 link is ever rewritten before it is resolved.
* There is no list of files excused from the label search, so nothing is passed over on
  the strength of being known to have no label.

What takes their place is the **collection inventory**. A PDS4 collection lists its
members in a ``collection*.csv`` file, and the scan reads every one it walks past:

.. code-block:: text

   ... | DEBUG | Construct collection basename dictionary from: bundles/.../data/collection_data.csv

Before reporting that a file has no label, or an ambiguous one, the scan asks whether a
collection whose path begins with that file's own directory, or the one above it, lists
the file. **A file no collection lists is passed over** -- an errata file or a checksum
manifest is not part of the archive and is not expected to be labeled. It is not passed
over silently: the question is logged for every file that reaches it.

One further difference: this scan will credit a label by what it says rather than by what
it is called. A file is shelved as described by a label in the same directory when its
basename exactly equals one of the link values that label yielded -- the values the scan
parsed out of the label, not any occurrence of the name in the label's text. It is a
fallback rather than a first resort, applied only to files that the earlier
name-matching pass left uncredited.

What a path may name
--------------------

A bundle, or a bundle set. A bundle set is expanded into its bundles and each is shelved
separately.

Checking a shelf
----------------

.. code-block:: console

   $ pds4linkshelf --validate $PDS4_HOLDINGS_DIR/bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023
   ...
   2026-08-09 01:43:27.994288 | pds.validation.links |---| INFO | *** Get link info and review: bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023/data/collection_data.xml
   2026-08-09 01:43:27.994838 | pds.validation.links |---| INFO | Label identified (by name) for collection_data.csv: bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023/data/collection_data.xml
   2026-08-09 01:43:28.033869 | pds.validation.links |---| INFO | Label already found for $PDS4_HOLDINGS_DIR/bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023/data/collection_data.csv
   ...
   2026-08-09 01:43:28.054296 | pds.validation.links || SUMMARY | Completed: pds4linkshelf --validate $PDS4_HOLDINGS_DIR/bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023
   2026-08-09 01:43:28.054319 | pds.validation.links || SUMMARY | Elapsed time = 0:00:00.232136
   2026-08-09 01:43:28.054333 | pds.validation.links || SUMMARY | 1 ERROR message
   2026-08-09 01:43:28.054344 | pds.validation.links || SUMMARY | 278 INFO messages
   2026-08-09 01:43:28.054353 | pds.validation.links || SUMMARY | 200 DEBUG messages reported of 1972 total

The ``200 ... reported of 1972`` line is the ``DEBUG`` cap: the scan narrates every string
it considered, which for a bundle of this size is nearly two thousand lines, and only the
first two hundred reach the log.

The single error is the bundle's own, and it recurs on every run:

.. code-block:: text

   ... | ERROR | Label Cassini_UVIS_Users_Guide_20180706.xml does not point to file: bundles/.../document/Cassini_UVIS_Users_Guide_20180706.pdf

Log file naming
---------------

Under ``logs/pdslinkshelf/`` -- the PDS3 program's name, as for all five PDS4 programs --
with ``_links`` as the suffix, and a ``WARNINGS.log`` beside the ``ERRORS.log`` that the
PDS3 program writes alone.

Exit status
-----------

0 when the run logged no error, 1 when it did -- including when the errors are the
bundle's own link problems rather than anything about the shelf.

Superseded shelves are kept
---------------------------

The existing ``.pickle`` and its ``.py`` sidecar are copied into each of the run's log
directories, with ``_v001`` and upward appended, before either is replaced.
