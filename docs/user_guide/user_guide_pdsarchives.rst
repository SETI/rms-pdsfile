pdsarchives
===========

``pdsarchives`` packs a PDS3 volume into one ``.tar.gz`` file and checks that the two
still agree. The archive is what a user downloads or a mirror copies when it wants a
whole volume as a single object.

The command line is the shared one, described in
:doc:`user_guide_maintenance_tools`, with no options of its own.

.. code-block:: text

   pdsarchives <task> <volume> [<volume> ...] [--log LOG] [--quiet]

What it writes
--------------

**One archive per volume**, in the ``archives-`` parallel of the category the volume came
from:

.. code-block:: text

   $PDS3_HOLDINGS_DIR/archives-volumes/COUVIS_0xxx/COUVIS_0001.tar.gz

The member names inside the archive begin at the volume name, so unpacking one gives a
``COUVIS_0001/`` directory.

What a path may name
--------------------

A volume, or a volume set. A volume set is expanded into the volumes inside it and each
is archived separately, one target and one log file each. A path naming checksum or
archive files is refused, because an archive is made of published data rather than of
another derived product.

Validation compares metadata, not contents
------------------------------------------

**``--validate`` and ``--repair`` never read a file's bytes.** They compare, for each
entry, the absolute path, the byte count and the modification time recorded in the
archive against the same three taken from the directory tree. A file whose contents
changed without its size or its timestamp changing is reported as matching.

That is what the ``--help`` text means by "Files match if they have identical byte counts
and modification dates; file contents are not compared", and it is deliberate: comparing
contents means decompressing every archive of a volume set, which would make checking a
whole tree impractical. The check that a file's *bytes* are what they were is
:doc:`user_guide_pdschecksums`.

Writing an archive
------------------

.. code-block:: console

   $ pdsarchives --initialize $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:40:05.267486 | pds.validation.archives || HEADER | pdsarchives --initialize $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:40:05.267999 | pds.validation.archives |-| HEADER | Task initialize for: $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:40:05.268051 | pds.validation.archives |--| INFO | Log file: $PDS3_HOLDINGS_DIR/../logs/pdsarchives/volumes/COUVIS_0xxx/COUVIS_0001_links_2026-08-09T01-40-05_initialize.log
   2026-08-09 01:40:05.268156 | pds.validation.archives |--| HEADER | Writing .tar.gz file for: volumes/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:40:05.268191 | pds.validation.archives |---| INFO | Creating directory: archives-volumes/COUVIS_0xxx
   2026-08-09 01:40:05.268432 | pds.validation.archives |---| INFO | File archived: COUVIS_0001
   2026-08-09 01:40:05.268613 | pds.validation.archives |---| INFO | File archived: COUVIS_0001/CALIB
   2026-08-09 01:40:05.269386 | pds.validation.archives |---| INFO | File archived: COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57.DAT
   2026-08-09 01:40:05.311310 | pds.validation.archives |---| INFO | Written: archives-volumes/COUVIS_0xxx/COUVIS_0001.tar.gz
   2026-08-09 01:40:05.311890 | pds.validation.archives || SUMMARY | Completed: pdsarchives --initialize $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:40:05.311910 | pds.validation.archives || SUMMARY | Elapsed time = 0:00:00.044396
   2026-08-09 01:40:05.311923 | pds.validation.archives || SUMMARY | 19 INFO messages

Thirteen of the sixteen ``File archived:`` lines and the per-phase summaries are elided.
Directories are archived as members in their own right, which is why the sixteen exceeds
the volume's nine files.

.. note::

   **The log file is named ``COUVIS_0001_links_...``, not ``..._archives_...``.** This
   program writes its logs with the same ``_links`` suffix that
   :doc:`user_guide_pdslinkshelf` uses. The two do not overwrite each other, because the
   program's own directory sits above them: ``logs/pdsarchives/`` here and
   ``logs/pdslinkshelf/`` there. :doc:`user_guide_pds4archives` uses ``_archives``.

Checking an archive
-------------------

.. code-block:: console

   $ pdsarchives --validate $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001
   ...
   2026-08-09 01:43:22.799465 | pds.validation.archives |--| HEADER | Generating file info: volumes/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:43:22.799513 | pds.validation.archives |---| INFO | Directory info generated: volumes/COUVIS_0xxx/COUVIS_0001/DATA
   2026-08-09 01:43:22.799728 | pds.validation.archives |---| INFO | File info generated: volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/HDAC1999_007_16_31.DAT
   ...
   2026-08-09 01:43:22.803465 | pds.validation.archives || SUMMARY | Completed: pdsarchives --validate $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:43:22.803484 | pds.validation.archives || SUMMARY | Elapsed time = 0:00:00.004615
   2026-08-09 01:43:22.803497 | pds.validation.archives || SUMMARY | 48 INFO messages

A run that finds a disagreement reports it one line per entry and exits 1. A path in the
directory tree that the archive does not hold is ``Missing from tar file``; a path in the
archive that the directory tree does not hold is ``Missing from directory``; and where
both hold it, a differing byte count or modification time is its own error line. **A
modification time is allowed to differ by up to one second**, because the archive records
whole seconds and the filesystem does not.

An archive that cannot be read at all -- an empty or truncated ``.tar.gz`` -- is not one
of those reports. The exception is logged and re-raised, so the run ends in a traceback
naming ``tarfile.ReadError`` and the process exits 1.

Task by task
------------

.. list-table::
   :header-rows: 1
   :widths: 24 76

   * - Task
     - What it does here
   * - ``--initialize``
     - Write the archive. Report an error and leave the existing file alone if there is
       one.
   * - ``--reinitialize``
     - Write the archive, replacing any existing file.
   * - ``--validate``
     - Compare the directory tree with the archive. Write nothing.
   * - ``--repair``
     - Compare; write a new archive only if they disagree.
   * - ``--update``
     - Given a volume set, write an archive for each volume that has none. Leave existing
       archives alone.

Exit status
-----------

0 when the run logged no error, 1 when it did, and 1 for a command line naming no task or
a path that does not exist. 2 for a command line the parser cannot read.
