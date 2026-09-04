pds4indexshelf
==============

``pds4indexshelf`` records where each product's rows are in a PDS4 metadata index table.
It is the PDS4 half of the pair whose PDS3 half is :doc:`user_guide_pdsindexshelf`, and
of the five pairs it is the one whose two halves differ least: nothing about shelving an
index table depends on the PDS version, so both halves are a few lines naming which
flavor to be.

The command line is the shared one, described in
:doc:`user_guide_maintenance_tools`, with no options of its own. The target is a
**table** rather than a bundle.

.. code-block:: text

   pds4indexshelf <task> <table> [<table> ...] [--log LOG] [--quiet]

What differs from the PDS3 program
----------------------------------

Three things, and only one of them is visible on the command line:

* The index extension is ``.csv``, not ``.tab``. A metadata directory is globbed for
  ``.csv`` files and a file named on the command line is checked against that extension.
* Paths resolve through the PDS4 rules, so the tree is ``$PDS4_HOLDINGS_DIR``.
* A ``WARNINGS.log`` is written, which the PDS3 program does not write. As in the PDS3
  program, it and the ``ERRORS.log`` go in this program's own log directory rather than
  beside each table's log file, so a run produces one of each however many tables it
  shelves.

What it writes
--------------

Two files per table, in ``_indexshelf-metadata/``, in a directory named for the bundle:

.. code-block:: text

   $PDS4_HOLDINGS_DIR/_indexshelf-metadata/<bundle set>/<bundle>/<table>.pickle
   $PDS4_HOLDINGS_DIR/_indexshelf-metadata/<bundle set>/<bundle>/<table>.py

Where the logs go
-----------------

Under ``logs/pds4indexshelf/`` -- this program's own name, as for all five PDS4 programs.
As in the PDS3 program, the path is built from the table's own path, so it carries the
bundle as a directory component and the table's basename as the file name, with no
separate suffix.

.. warning::

   **Neither of the two PDS4 bundle sets available for testing can be shelved by this
   program.** The package's rules cover six bundle sets; these are the two with holdings
   to run against, and both fail, for two different reasons, neither about the command
   line:

   * A bundle set whose metadata ``.csv`` files carry **no label at all** fails when the
     table is read, because the reader is given an empty label path.
   * A bundle set whose ``.csv`` has a label fails when the label and the file disagree
     about the row count:

     .. code-block:: console

        $ pds4indexshelf --initialize "$PDS4_HOLDINGS_DIR/metadata/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023"
        ...
        2026-08-09 01:42:18.295265 | pds.validation.indexshelf |---| ERROR | row count mismatch in $PDS4_HOLDINGS_DIR/metadata/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023_index.xml: 42 rows in file; label says 41 rows
        ...
        ValueError: row count mismatch in ...: 42 rows in file; label says 41 rows

   The second is a disagreement between a published table and its published label, and
   the program is reporting it correctly; correcting it means correcting the label. The
   first needs a decision about what a PDS4 index shelf is built from when there is no
   label. Until then, PDS4 metadata tables have no index shelves, and nothing else in this
   package depends on their existing.

Nothing versions an index shelf
-------------------------------

As in the PDS3 program: no log directories are recorded and no superseded shelf is copied
anywhere. A task that replaces a shelf replaces it.

Exit status
-----------

0 when the run logged no error, 1 when it did, and 1 for a path this program refuses. 2
for a command line the parser cannot read. A task that raises -- which is what the two
failures above do -- ends the process through the traceback.
