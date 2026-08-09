pdschecksums
============

``pdschecksums`` writes and checks the MD5 manifest of a PDS3 volume. Every other
derived product in a holdings tree can be rebuilt from the data, but the manifest is what
says the data has not changed since it was published, so this is the first program to run
against a new volume and the one an info shelf depends on.

The command line is the shared one, described in
:doc:`user_guide_maintenance_tools`, plus two options of its own.

.. code-block:: text

   pdschecksums <task> <volume> [<volume> ...] [--archives] [--infoshelf] [--log LOG] [--quiet]

What it writes
--------------

One text file per manifest, in the ``checksums-`` parallel of the category the target
came from:

.. code-block:: text

   $PDS3_HOLDINGS_DIR/checksums-volumes/COUVIS_0xxx/COUVIS_0001_md5.txt

Each line holds a 32-character MD5 digest, two spaces and the file's path below the
volume set. :doc:`user_guide_appendix_file_formats` gives the format in full.

**What one manifest covers is not always one volume.** In an ordinary category there is
one file per volume. In an ``archives-`` category there is one for the whole volume set,
because an archive file is one file per volume and grouping them is what makes the
manifest worth having. And each of the three kinds of directory that sit under a volume
set without being a volume -- a name beginning ``checksums_``, a name beginning
``superseded``, or a name ending ``_support`` -- gets a manifest of its own.

What a path may name
--------------------

A volume, a volume set, or **a single file inside a volume**. Naming one file narrows the
task to that file's entry and leaves the rest of the manifest untouched. One combination
is changed rather than obeyed: ``--reinitialize`` on a single file is run as ``--update``,
because rebuilding a whole manifest from one named file would erase every other entry.

Options
-------

.. list-table::
   :header-rows: 1
   :widths: 26 74

   * - Option
     - Meaning
   * - ``--archives``, ``-a``
     - Work on the archive file of the named volume rather than on the volume itself.
       The path given stays a ``volumes/`` path; the program redirects it.
   * - ``--infoshelf``, ``-i``
     - After a successful run, also run the equivalent ``pdsinfoshelf`` command.

``--infoshelf`` is the answer to the ordering rule in :doc:`user_guide_concepts`: an info
shelf reads the checksum file, so the two always run in that order, and this does both in
one command. The second run is a full ``pdsinfoshelf`` run with its own log file and its
own logger name:

.. code-block:: console

   $ pdschecksums --validate --infoshelf $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001
   ...
   2026-08-09 01:44:56.051771 | pds.validation.fileinfo || HEADER | pdsinfoshelf --validate $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:44:56.052227 | pds.validation.fileinfo |--| INFO | Log file: $PDS3_HOLDINGS_DIR/../logs/pdsinfoshelf/volumes/COUVIS_0xxx/COUVIS_0001_info_2026-08-09T01-44-56_validate.log
   ...

Building a manifest
-------------------

.. code-block:: console

   $ pdschecksums --initialize $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:40:04.716654 | pds.validation.checksums || HEADER | pdschecksums --initialize $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:40:04.717147 | pds.validation.checksums |-| HEADER | Task "initialize" for: $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:40:04.717202 | pds.validation.checksums |--| INFO | Log file: $PDS3_HOLDINGS_DIR/../logs/pdschecksums/volumes/COUVIS_0xxx/COUVIS_0001_md5_2026-08-09T01-40-04_initialize.log
   2026-08-09 01:40:04.717317 | pds.validation.checksums |--| HEADER | Generating MD5 checksums: volumes/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:40:04.717423 | pds.validation.checksums |---| INFO | MD5=de39b402ff1fd89e709d3d87e7f9464e: volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/HDAC1999_007_16_31.DAT
   2026-08-09 01:40:04.717513 | pds.validation.checksums |---| INFO | MD5=7e7a9fea32d2f26898bb2a630b21862f: volumes/COUVIS_0xxx/COUVIS_0001/DATA/D1999_007/FUV1999_007_16_57.LBL
   2026-08-09 01:40:04.718159 | pds.validation.checksums |---| INFO | Lastest holdings file modification date: 2020-05-13T00-30-45
   2026-08-09 01:40:04.718504 | pds.validation.checksums |--| HEADER | Writing MD5 checksums: checksums-volumes/COUVIS_0xxx/COUVIS_0001_md5.txt
   2026-08-09 01:40:04.718540 | pds.validation.checksums |---| INFO | Creating directory: checksums-volumes/COUVIS_0xxx
   2026-08-09 01:40:04.719379 | pds.validation.checksums || SUMMARY | Completed: pdschecksums --initialize $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:40:04.719400 | pds.validation.checksums || SUMMARY | Elapsed time = 0:00:00.002717
   2026-08-09 01:40:04.719414 | pds.validation.checksums || SUMMARY | 12 INFO messages
   2026-08-09 01:40:04.719425 | pds.validation.checksums || SUMMARY | 9 DEBUG messages reported of 9 total

Seven of this volume's nine files, and the per-phase summary lines, are elided above. The
run reports one ``MD5=`` line per file as it hashes it, then one ``Written:`` line per
file as it writes the manifest, and the closing summary counts both.

Checking a volume against its manifest
--------------------------------------

.. code-block:: console

   $ pdschecksums --validate $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001
   ...
   2026-08-09 01:43:22.218196 | pds.validation.checksums |--| HEADER | Reading MD5 checksums: checksums-volumes/COUVIS_0xxx/COUVIS_0001_md5.txt
   2026-08-09 01:43:22.218226 | pds.validation.checksums |---| INFO | MD5 checksum file: checksums-volumes/COUVIS_0xxx/COUVIS_0001_md5.txt
   ...
   2026-08-09 01:43:22.218492 | pds.validation.checksums |--| HEADER | Generating MD5 checksums: volumes/COUVIS_0xxx/COUVIS_0001
   ...

A file whose digest disagrees is reported at ``ERROR``, one line per file:

.. code-block:: text

   ... | pds.validation.checksums |---| ERROR | Checksum mismatch: volumes/COUVIS_0xxx/COUVIS_0001/INDEX/INDEX.TAB

.. warning::

   **A run exits 0 even when the validation failed.** The exit status of this program
   reports whether the command line and the paths were usable, not what the task found.
   The mismatch above was reported by a run that exited 0. A script that has to know
   whether a volume is intact must read the log, or the run's closing ``n ERROR
   messages`` summary line, rather than the status. Every other program in this guide
   except ``pds4checksums`` exits 1 in that situation.

Superseded manifests are kept
-----------------------------

A task that replaces an existing manifest does not lose the old one. Before the write,
the existing file is **copied** into each of the run's log directories -- the original
stays where it is and is then overwritten -- under the same basename with a version
number added:

.. code-block:: text

   COUVIS_0001_md5_v001.txt

The number is one past the highest already in that directory, starting at ``001``.
:doc:`user_guide_maintenance_tools` says where the log directories are.
