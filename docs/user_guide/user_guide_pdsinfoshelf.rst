pdsinfoshelf
============

``pdsinfoshelf`` records, for every file in a PDS3 volume, the five things
:class:`~pdsfile.pdsfile.PdsFile` is asked about often enough that reading them off the
filesystem each time is too slow: how many bytes the file holds, how many children a
directory has, when it was last modified, what its MD5 digest is, and, for a preview
image, its width and height in pixels.

The command line is the shared one, described in
:doc:`user_guide_maintenance_tools`, plus one option of its own.

.. code-block:: text

   pdsinfoshelf <task> <volume> [<volume> ...] [--archives] [--log LOG] [--quiet]

It reads the checksum file rather than hashing
-----------------------------------------------

**This program does not compute digests.** It reads them out of the volume's checksum
file, so every entry it writes is only as current as :doc:`user_guide_pdschecksums` left
it, and a volume with no checksum file cannot be shelved at all: the run reports
``Missing entry in checksum file`` for every file and then ends in
``FileNotFoundError``, because it dates the volume partly by the checksum file's own
modification time.

So ``pdschecksums`` runs first, always. ``pdschecksums --infoshelf`` does both in one
command.

What it writes
--------------

Two files per volume, in the ``_infoshelf-`` parallel of the category:

.. code-block:: text

   $PDS3_HOLDINGS_DIR/_infoshelf-volumes/COUVIS_0xxx/COUVIS_0001_info.pickle
   $PDS3_HOLDINGS_DIR/_infoshelf-volumes/COUVIS_0xxx/COUVIS_0001_info.py

The ``.pickle`` is what the package reads. The ``.py`` beside it is the same mapping
written as readable Python, one line per entry, and it travels with the pickle: a task
that versions one versions the other.
:doc:`user_guide_appendix_file_formats` gives the format of both.

What a path may name
--------------------

A volume, a volume set, or **a single file inside a volume**. Naming one file narrows the
task to that file's entry and leaves the rest of the shelf alone; as in
:doc:`user_guide_pdschecksums`, ``--reinitialize`` on a single file is run as
``--update``.

``--archives``
--------------

.. list-table::
   :header-rows: 1
   :widths: 26 74

   * - Option
     - Meaning
   * - ``--archives``, ``-a``
     - Shelve the archive file of the named volume rather than the volume itself. The
       shelf lands under ``_infoshelf-archives-<category>/``.

Building a shelf
----------------

.. code-block:: console

   $ pdsinfoshelf --initialize $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:40:05.882962 | pds.validation.fileinfo || HEADER | pdsinfoshelf --initialize $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:40:05.883482 | pds.validation.fileinfo |-| HEADER | Task "initialize" for: $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:40:05.883535 | pds.validation.fileinfo |--| INFO | Log file: $PDS3_HOLDINGS_DIR/../logs/pdsinfoshelf/volumes/COUVIS_0xxx/COUVIS_0001_info_2026-08-09T01-40-05_initialize.log
   2026-08-09 01:40:05.883646 | pds.validation.fileinfo |--| HEADER | Generating file info: volumes/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:40:05.883677 | pds.validation.fileinfo |---| INFO | Loading checksums for: volumes/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:40:05.883923 | pds.validation.fileinfo |---| HEADER | Reading MD5 checksums: checksums-volumes/COUVIS_0xxx/COUVIS_0001_md5.txt
   2026-08-09 01:40:05.884160 | pds.validation.fileinfo |---| INFO | Checksum load completed: volumes/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:40:05.884246 | pds.validation.fileinfo |---| INFO | File info generated: volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/HDAC1999_007_16_31.DAT
   ...
   2026-08-09 01:40:05.885629 | pds.validation.fileinfo || SUMMARY | Completed: pdsinfoshelf --initialize $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:40:05.885649 | pds.validation.fileinfo || SUMMARY | Elapsed time = 0:00:00.002658
   2026-08-09 01:40:05.885662 | pds.validation.fileinfo || SUMMARY | 17 INFO messages
   2026-08-09 01:40:05.885672 | pds.validation.fileinfo || SUMMARY | 0 DEBUG messages reported of 9 total

The nested ``Reading MD5 checksums`` level is the checksum file being loaded, inside this
run rather than as a separate one. The remaining ``File info generated:`` lines and the
per-phase summaries are elided.

.. note::

   **The logger name is ``pds.validation.fileinfo``**, not anything containing
   "infoshelf". Both flavors of this program share it, which is how a chained
   ``pdschecksums --infoshelf`` run is recognizable in a combined log.

Modification times are local
----------------------------

**Every modification time in the shelf is formatted in the local time zone**, and the
comparison a validation makes is a string comparison. A volume shelved under one setting
of ``TZ`` and validated under another therefore disagrees with itself, on every file. Set
``TZ`` the same way for every run against one tree.

Checking a shelf
----------------

``--validate`` compares each of the five fields against the tree, and reports a
disagreement per file. The comparison on the third field allows a shelf that is merely
older than the file it describes to be reported separately from one that is wrong, which
is why ``--repair`` can update a shelf's own modification date without rewriting it.

Exit status
-----------

0 when the run logged no error, 1 when it did. Unlike :doc:`user_guide_pdschecksums`,
which shares this program's driver, **this program does report the task's outcome in its
exit status**: a failed validation exits 1.

Superseded shelves are kept
---------------------------

Before a task replaces a shelf, the existing ``.pickle`` and its ``.py`` sidecar are
copied into each of the run's log directories with ``_v001`` and upward appended to the
basename.
