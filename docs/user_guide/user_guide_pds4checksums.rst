pds4checksums
=============

``pds4checksums`` writes and checks the MD5 manifest of a PDS4 bundle. It is the PDS4
half of the pair whose PDS3 half is :doc:`user_guide_pdschecksums`, and it does the same
job over bundles instead of volumes: hash every file, write one line per file, and
compare a tree against what was written.

The command line is the shared one, described in
:doc:`user_guide_maintenance_tools`, plus two options of its own.

.. code-block:: text

   pds4checksums <task> <bundle> [<bundle> ...] [--archives] [--infoshelf] [--log LOG] [--quiet]

What it writes
--------------

One text file per manifest, in the ``checksums-`` parallel of the category the target
came from:

.. code-block:: text

   $PDS4_HOLDINGS_DIR/checksums-bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023_md5.txt

The coverage rule is the bundle one: one manifest per bundle in an ordinary category, one
for the whole bundle set in an ``archives-`` category, and one for each directory under a
bundle set whose name begins ``checksums_`` or ``superseded`` or ends ``_support``.

What a path may name
--------------------

A bundle, a bundle set, or a single file inside a bundle. As in the PDS3 program,
``--reinitialize`` on a single file is run as ``--update``.

Options
-------

.. list-table::
   :header-rows: 1
   :widths: 26 74

   * - Option
     - Meaning
   * - ``--archives``, ``-a``
     - Work on the archive file of the named bundle rather than on the bundle itself.
   * - ``--infoshelf``, ``-i``
     - Accepted, and has no effect. See below.

.. warning::

   **``--infoshelf`` does not chain a second run here.** The option is declared and
   accepted, and the help text describes the PDS3 behavior, but a run given it does the
   checksum task and stops; no ``pds4infoshelf`` run follows. Run the two programs in
   sequence instead:

   .. code-block:: bash

      pds4checksums --initialize "$BUNDLE" && pds4infoshelf --initialize "$BUNDLE"

Building a manifest
-------------------

.. code-block:: console

   $ pds4checksums --initialize $PDS4_HOLDINGS_DIR/bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023
   2026-08-09 01:42:15.443120 | pds.validation.checksums || HEADER | pds4checksums --initialize $PDS4_HOLDINGS_DIR/bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023
   2026-08-09 01:42:15.443708 | pds.validation.checksums |-| HEADER | Task "initialize" for: $PDS4_HOLDINGS_DIR/bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023
   2026-08-09 01:42:15.443773 | pds.validation.checksums |--| INFO | Log file: $PDS4_HOLDINGS_DIR/../logs/pdschecksums/bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023_md5_2026-08-09T01-42-15_initialize.log
   2026-08-09 01:42:15.443891 | pds.validation.checksums |--| HEADER | Generating MD5 checksums: bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023
   2026-08-09 01:42:15.443987 | pds.validation.checksums |---| NORMAL | MD5=f04bc73d543335c215c5fd0e30c2bee7: bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023/readme.txt
   2026-08-09 01:42:15.444063 | pds.validation.checksums |---| NORMAL | MD5=2fbd8665748a35efba4c97bad64dceab: bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023/bundle.xml
   ...
   2026-08-09 01:42:15.683044 | pds.validation.checksums || SUMMARY | Completed: pds4checksums --initialize $PDS4_HOLDINGS_DIR/bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023
   2026-08-09 01:42:15.683067 | pds.validation.checksums || SUMMARY | Elapsed time = 0:00:00.239915
   2026-08-09 01:42:15.683082 | pds.validation.checksums || SUMMARY | 185 NORMAL messages
   2026-08-09 01:42:15.683093 | pds.validation.checksums || SUMMARY | 2 INFO messages
   2026-08-09 01:42:15.683103 | pds.validation.checksums || SUMMARY | 184 DEBUG messages

The bundle holds 184 files. The run reports each one twice: at ``NORMAL`` while hashing
it and at ``DEBUG`` while writing its line, which with the one ``NORMAL`` line for the
directory it created is where the closing counts of 185 and 184 come from. All but two of
those lines are elided above.

**Note the log directory: ``logs/pdschecksums/``, not ``logs/pds4checksums/``.** Every
PDS4 program in this guide writes under its PDS3 counterpart's name, so the two flavors
share one log tree and are told apart by the category component beneath it --
``bundles/`` here, ``volumes/`` for the PDS3 program.
:doc:`user_guide_maintenance_tools` covers that in full.

Two differences from the PDS3 program that are visible in the output
--------------------------------------------------------------------

* **The per-file lines are ``NORMAL``, not ``INFO``.** The PDS3 program reports each
  file at ``INFO``, which is subject to a message cap of 100 per phase; this one reports
  at ``NORMAL``, which is not capped. A large bundle therefore prints one line per file
  however large it is.
* **A ``WARNINGS.log`` is written** in each log directory, beside the ``ERRORS.log`` that
  both flavors write.

Checking a bundle against its manifest
--------------------------------------

.. code-block:: console

   $ pds4checksums --validate $PDS4_HOLDINGS_DIR/bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023
   ...
   2026-08-09 01:43:25.421076 | pds.validation.checksums |--| HEADER | Reading MD5 checksums: checksums-bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023_md5.txt
   ...
   2026-08-09 01:43:25.659125 | pds.validation.checksums || SUMMARY | Elapsed time = 0:00:00.238864
   2026-08-09 01:43:25.659137 | pds.validation.checksums || SUMMARY | 368 NORMAL messages
   2026-08-09 01:43:25.659147 | pds.validation.checksums || SUMMARY | 3 INFO messages
   2026-08-09 01:43:25.659156 | pds.validation.checksums || SUMMARY | 0 DEBUG messages reported of 184 total

.. warning::

   **A run exits 0 even when the validation failed**, exactly as in
   :doc:`user_guide_pdschecksums`. Read the log or the closing ``n ERROR messages`` line,
   not the status.

Superseded manifests are kept
-----------------------------

As in the PDS3 program: the existing manifest is copied into each of the run's log
directories, under the same basename with ``_v001`` and upward appended, before it is
overwritten.
