pds4infoshelf
=============

``pds4infoshelf`` records, for every file in a PDS4 bundle, the same five things the PDS3
program records for a volume: byte count, child count, modification time, MD5 digest and,
for a preview image, pixel width and height. It is the PDS4 half of the pair whose PDS3
half is :doc:`user_guide_pdsinfoshelf`.

The command line is the shared one, described in
:doc:`user_guide_maintenance_tools`, plus one option of its own.

.. code-block:: text

   pds4infoshelf <task> <bundle> [<bundle> ...] [--archives] [--log LOG] [--quiet]

It reads the checksum file rather than hashing
-----------------------------------------------

**The dependency on :doc:`user_guide_pds4checksums` is hard**, exactly as in the PDS3
program: the digests come out of the bundle's checksum file, and a bundle with no
checksum file gets ``Missing entry in checksum file`` for every file and then ends in
:exc:`FileNotFoundError`.

The convenience that exists on the PDS3 side does **not** exist here:
``pds4checksums --infoshelf`` chains a second ``pds4checksums`` run rather than an info
shelf run, as :doc:`user_guide_pds4checksums` describes. Run the two in sequence, and not
joined by ``&&`` -- ``pds4checksums`` exits 0 whatever it found, so ``&&`` would guard
nothing:

.. code-block:: bash

   pds4checksums --initialize "$BUNDLE"
   pds4infoshelf --initialize "$BUNDLE"

What it writes
--------------

Two files per bundle, in the ``_infoshelf-`` parallel of the category:

.. code-block:: text

   $PDS4_HOLDINGS_DIR/_infoshelf-bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023_info.pickle
   $PDS4_HOLDINGS_DIR/_infoshelf-bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023_info.py

What a path may name
--------------------

A bundle, a bundle set, or a single file inside a bundle. ``--reinitialize`` on a single
file is run as ``--update``.

``--archives``
--------------

.. list-table::
   :header-rows: 1
   :widths: 26 74

   * - Option
     - Meaning
   * - ``--archives``, ``-a``
     - Shelve the archive file of the named bundle rather than the bundle itself.
       Default: off. There is one such shelf per bundle set rather than one per bundle.

Building a shelf
----------------

.. code-block:: console

   $ pds4infoshelf --initialize $PDS4_HOLDINGS_DIR/bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023
   2026-08-09 01:42:16.838557 | pds.validation.fileinfo || HEADER | pds4infoshelf --initialize $PDS4_HOLDINGS_DIR/bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023
   2026-08-09 01:42:16.839112 | pds.validation.fileinfo |-| HEADER | Task "initialize" for: $PDS4_HOLDINGS_DIR/bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023
   2026-08-09 01:42:16.839167 | pds.validation.fileinfo |--| INFO | Log file: $PDS4_HOLDINGS_DIR/../logs/pdsinfoshelf/bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023_info_2026-08-09T01-42-16_initialize.log
   2026-08-09 01:42:16.839278 | pds.validation.fileinfo |--| HEADER | Generating file info: bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023
   2026-08-09 01:42:16.839311 | pds.validation.fileinfo |---| INFO | Loading checksums for: bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023
   2026-08-09 01:42:16.839568 | pds.validation.fileinfo |---| HEADER | Reading MD5 checksums: checksums-bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023_md5.txt
   ...
   2026-08-09 01:42:16.863753 | pds.validation.fileinfo || SUMMARY | Completed: pds4infoshelf --initialize $PDS4_HOLDINGS_DIR/bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023
   2026-08-09 01:42:16.863776 | pds.validation.fileinfo || SUMMARY | Elapsed time = 0:00:00.025186
   2026-08-09 01:42:16.863790 | pds.validation.fileinfo || SUMMARY | 184 NORMAL messages
   2026-08-09 01:42:16.863800 | pds.validation.fileinfo || SUMMARY | 8 INFO messages
   2026-08-09 01:42:16.863810 | pds.validation.fileinfo || SUMMARY | 0 DEBUG messages reported of 184 total

Note the log directory: ``logs/pdsinfoshelf/``, not ``logs/pds4infoshelf/``, and the
logger name ``pds.validation.fileinfo``, which both flavors share.

Two differences from the PDS3 program that are visible in the output
--------------------------------------------------------------------

* The per-file lines are ``NORMAL``, not ``INFO``, and the two programs report a
  validation quite differently as a result. The PDS3 program prints ``File info matches:``
  once per file. This one suppresses every ``NORMAL`` line inside the validation phase, so
  a bundle that matches prints nothing at all per file and says so when the phase closes:

  .. code-block:: text

     ... | pds.validation.fileinfo |--| SUMMARY | 0 NORMAL messages reported of 191 total

  A disagreement is logged at ``ERROR`` and is not suppressed.
* A ``WARNINGS.log`` is written in each log directory, beside the ``ERRORS.log``.

Modification times are local
----------------------------

As in the PDS3 program: **every modification time is formatted in the local time zone.**
A validation parses the two times and accepts a difference below one second, so differing
text can still agree -- but a whole-hour shift does not survive it, and a bundle shelved
under one ``TZ`` and validated under another disagrees with itself on every file.

Exit status
-----------

0 when the run logged no error, 1 when it did. This program reports the task's outcome in
its status, where :doc:`user_guide_pds4checksums`, which shares its driver, does not.

Superseded shelves are kept
---------------------------

The existing ``.pickle`` and its ``.py`` sidecar are copied into each of the run's log
directories, with ``_v001`` and upward appended, before either is replaced.
