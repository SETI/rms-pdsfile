pdsindexshelf
=============

``pdsindexshelf`` records where each product's rows are in a PDS3 metadata index table. A
metadata table lists one row per product, or several rows for a product observed in more
than one way, and looking a product up in it otherwise means reading the whole table.
This program reads it once and writes down which row numbers belong to which product.

The command line is the shared one, described in
:doc:`user_guide_maintenance_tools`, with no options of its own -- but the target is a
**table** rather than a volume, and that changes what a path may name and where the log
goes.

.. code-block:: text

   pdsindexshelf <task> <table> [<table> ...] [--log LOG] [--quiet]

What a path may name
--------------------

An index table, or a metadata directory, which is expanded into the ``.tab`` files inside
it. A directory holding none directly is searched one level deeper instead, which is how
a whole volume set's metadata directory expands into its volumes' tables. A metadata
directory holding three tables is three targets, each with its own log level and its own
log file:

.. code-block:: console

   $ pdsindexshelf --initialize "$PDS3_HOLDINGS_DIR/metadata/COUVIS_0xxx/COUVIS_0001"
   2026-08-09 01:41:18.077222 | pds.validation.indexshelf || HEADER | pdsindexshelf --initialize $PDS3_HOLDINGS_DIR/metadata/COUVIS_0xxx/COUVIS_0001

   2026-08-09 01:41:18.077749 | pds.validation.indexshelf |-| HEADER | Task "initialize" for: $PDS3_HOLDINGS_DIR/metadata/COUVIS_0xxx/COUVIS_0001/COUVIS_0001_supplemental_index.tab
   2026-08-09 01:41:18.077789 | pds.validation.indexshelf |--| INFO | Log file: $PDS3_HOLDINGS_DIR/../logs/pdsindexshelf/metadata/COUVIS_0xxx/COUVIS_0001/COUVIS_0001_supplemental_index_2026-08-09T01-41-18_initialize.log
   2026-08-09 01:41:18.077883 | pds.validation.indexshelf |--| HEADER | Tabulating index rows for: metadata/COUVIS_0xxx/COUVIS_0001/COUVIS_0001_supplemental_index.tab
   2026-08-09 01:41:18.237519 | pds.validation.indexshelf |---| INFO | Rows tabulated: 2930
   2026-08-09 01:41:18.237735 | pds.validation.indexshelf |---| INFO | Latest index file modification date: 2022-01-04T18-39-59
   ...
   2026-08-09 01:41:18.367344 | pds.validation.indexshelf || SUMMARY | Completed: pdsindexshelf --initialize $PDS3_HOLDINGS_DIR/metadata/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:41:18.367378 | pds.validation.indexshelf || SUMMARY | Elapsed time = 0:00:00.290108
   2026-08-09 01:41:18.367404 | pds.validation.indexshelf || SUMMARY | 19 INFO messages

Two of the three tables' levels are elided. The directory named on the command line held
``COUVIS_0001_index.tab``, ``COUVIS_0001_supplemental_index.tab`` and
``COUVIS_0001_versions.tab``, and the run shelved all three.

A backup copy of a table is skipped rather than shelved, and two separate rules decide
what counts as one:

* a **basename** whose last component before the extension is a timestamp of the form
  ``2026-08-09T01-41-18``, or the word ``backup`` or ``original``, separated from the
  rest by a hyphen or an underscore; or
* an **absolute path** containing the text ``" copy"`` anywhere in it -- so a table under
  a directory called ``metadata copy`` is skipped as a backup however it is named.

The skip is reported at ``ERROR``, not as a note, so a run that skips one exits 1:

.. code-block:: text

   ... | pds.validation.indexshelf |-| ERROR | Backup file skipped: metadata/COUVIS_0xxx/COUVIS_0001/COUVIS_0001_index_backup.tab

The path in that line is written relative to the holdings root only because an earlier
table in the same run has already been shelved: the skip is decided before the work that
registers the holdings root with the logger. Name the backup table by itself, so that it
is the run's first target, and the same line carries the absolute path instead.

What it writes
--------------

Two files per **table**, in ``_indexshelf-metadata/``, in a directory named for the
volume:

.. code-block:: text

   $PDS3_HOLDINGS_DIR/_indexshelf-metadata/COUVIS_0xxx/COUVIS_0001/COUVIS_0001_index.pickle
   $PDS3_HOLDINGS_DIR/_indexshelf-metadata/COUVIS_0xxx/COUVIS_0001/COUVIS_0001_index.py

The mapping is from a row selection key to the row number, or to the list of row numbers
where a product has more than one:

.. code-block:: python

   COUVIS_0001_index = {
       "HSP1999_007_16_53"   : 0,
       "HDAC1999_007_16_31"  : 1,
       "HDAC1999_007_16_33"  : 2,
   }

This is the one product of the ten programs that is per table rather than per unit, so a
volume has as many index shelves as it has metadata tables, and they sit one directory
deeper than the other shelves.

The log path is one level deeper too
------------------------------------

Because the target is a table, the log path is built from the table's own path rather
than from a volume's, so it carries the volume as a directory component and the table's
basename as the file name -- and there is no separate suffix in the file name, where the
other eight programs insert one. ``pds4indexshelf`` behaves exactly as this one does:

.. code-block:: text

   $PDS3_HOLDINGS_DIR/../logs/pdsindexshelf/metadata/COUVIS_0xxx/COUVIS_0001/COUVIS_0001_supplemental_index_2026-08-09T01-41-18_initialize.log

Checking a shelf
----------------

``--validate`` re-reads the table and compares the row numbers it derives with the ones
the shelf holds:

.. code-block:: console

   $ pdsindexshelf --validate "$PDS3_HOLDINGS_DIR/metadata/COUVIS_0xxx/COUVIS_0001"
   ...
   2026-08-09 01:43:24.604501 | pds.validation.indexshelf |--| HEADER | Tabulating index rows for: metadata/COUVIS_0xxx/COUVIS_0001/COUVIS_0001_supplemental_index.tab
   2026-08-09 01:43:24.748927 | pds.validation.indexshelf |---| INFO | Rows tabulated: 2930
   2026-08-09 01:43:24.749101 | pds.validation.indexshelf |---| INFO | Latest index file modification date: 2022-01-04T18-39-59
   ...
   2026-08-09 01:43:24.833406 | pds.validation.indexshelf || SUMMARY | Completed: pdsindexshelf --validate $PDS3_HOLDINGS_DIR/metadata/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:43:24.833425 | pds.validation.indexshelf || SUMMARY | Elapsed time = 0:00:00.229490
   2026-08-09 01:43:24.833437 | pds.validation.indexshelf || SUMMARY | 21 INFO messages

The table is read in full on every task, including ``--validate``, so a validation costs
about what an initialization costs.

Nothing versions an index shelf
-------------------------------

Unlike the checksum, info shelf and link shelf programs, this one records no log
directories and copies no superseded file into them. A ``--reinitialize`` or a
``--repair`` that replaces an index shelf simply replaces it.

.. note::

   :doc:`user_guide_re_validate`, which re-runs five of the maintenance validations over
   whole volumes, does **not** run this one. Index shelves have to be validated by
   invoking this program directly.

Exit status
-----------

0 when the run logged no error, 1 when it did, and 1 for a path this program refuses. 2
for a command line the parser cannot read.
