pds4archives
============

``pds4archives`` packs PDS4 bundle directories into ``.tar.gz`` files and checks that the
two agree. It is the PDS4 half of the pair whose PDS3 half is
:doc:`user_guide_pdsarchives`, but it differs from it more than the other four pairs
differ from each other, and the difference is on the command line rather than inside.

The command line is the shared one, described in
:doc:`user_guide_maintenance_tools`, with no options of its own.

.. code-block:: text

   pds4archives <task> <bundle> [<bundle> ...] [--log LOG] [--quiet]

How many archives cover a target is looked up, not derived
----------------------------------------------------------

The PDS3 program archives one volume into one file, always. **Here, what a path resolves
to is decided by the bundle set's own rules**: a table installed by the bundle set says
which archive files cover a given path, and a second table says which directories each of
those archives packages. A target may therefore resolve to one archive, several, or none,
and a run loops over whatever the tables answer.

Two consequences matter when choosing what to put on the command line.

* **A path is not expanded.** Whatever level it names becomes one target. A bundle set
  path does not become one target per bundle.
* **The level a path must name is the level the rules describe.** For a bundle set whose
  rules place one archive over the whole set, the bundle set path is the one that works,
  and a bundle path inside it resolves to no archives at all.

A target that resolves to no archives is not a quiet no-op, and the five tasks do not
agree on what it is. ``--update`` reports nothing and moves on. ``--validate`` and
``--repair`` walk the whole directory tree first and only then find there is nothing to
compare it with. ``--initialize`` and ``--reinitialize`` log an error and then end the
run in an exception:

.. code-block:: console

   $ pds4archives --initialize $PDS4_HOLDINGS_DIR/bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023
   ...
   2026-08-09 01:42:16.282938 | pds.validation.archives |---| ERROR | No archive paths resolved for: bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023
   2026-08-09 01:42:16.283004 | pds.validation.archives |---| EXCEPTION | **** RuntimeError No active exception to reraise
   ...
   RuntimeError: No active exception to reraise

The ``ERROR`` line above is the one to read; the ``RuntimeError`` that follows carries no
further information about what went wrong. Naming the bundle **set** instead is what this
bundle set's rules describe:

.. code-block:: console

   $ pds4archives --initialize $PDS4_HOLDINGS_DIR/bundles/cassini_uvis_solarocc_beckerjarmak2023
   ...
   2026-08-09 01:42:52.282574 | pds.validation.archives |--| INFO | Log file: $PDS4_HOLDINGS_DIR/../logs/pdsarchives/bundles/cassini_uvis_solarocc_beckerjarmak2023/_archives_2026-08-09T01-42-52_initialize.log
   2026-08-09 01:42:52.282678 | pds.validation.archives |--| HEADER | Writing .tar.gz file for: bundles/cassini_uvis_solarocc_beckerjarmak2023
   2026-08-09 01:42:52.282759 | pds.validation.archives |---| NORMAL | Creating directory: archives-bundles/cassini_uvis_solarocc_beckerjarmak2023
   ...
   2026-08-09 01:42:58.872248 | pds.validation.archives |---| NORMAL | File archived: cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023/xml_schema/collection_xml_schema.xml
   2026-08-09 01:42:58.873330 | pds.validation.archives |--| SUMMARY | Completed: Writing .tar.gz file for: bundles/cassini_uvis_solarocc_beckerjarmak2023
   2026-08-09 01:42:58.873361 | pds.validation.archives |--| SUMMARY | Elapsed time = 0:00:06.590632
   2026-08-09 01:42:58.873379 | pds.validation.archives |--| SUMMARY | 194 NORMAL messages

Unlike the PDS3 program, this one logs no line naming the archive it wrote: the last
``File archived:`` line is the last thing the write phase reports. The archive's path is
the ``archives-`` parallel of the target, as in the next section.

What it writes
--------------

One or more archives in the ``archives-`` parallel of the category the target came from:

.. code-block:: text

   $PDS4_HOLDINGS_DIR/archives-bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023.tar.gz

Validation compares metadata, not contents
------------------------------------------

As in the PDS3 program: absolute path, byte count and modification time, with a
one-second tolerance on the time, and no file's contents are ever read.

.. warning::

   **A freshly written archive does not pass this program's own ``--validate``.** The
   two halves of the round trip disagree about how much of the path a member name
   carries: an archive is written with member names beginning at the bundle set, and
   validation rebuilds an absolute path by putting the bundle set's own prefix back in
   front of the member name, which produces the bundle set component twice. Every entry
   is then reported as ``Missing from tar file``:

   .. code-block:: console

      $ pds4archives --validate $PDS4_HOLDINGS_DIR/bundles/cassini_uvis_solarocc_beckerjarmak2023
      ...
      2026-08-09 01:43:26.647554 | pds.validation.archives |---| ERROR | Missing from tar file: bundles/cassini_uvis_solarocc_beckerjarmak2023
      2026-08-09 01:43:26.647663 | pds.validation.archives |---| ERROR | Missing from tar file: bundles/cassini_uvis_solarocc_beckerjarmak2023/cassini_uvis_solarocc_beckerjarmak2023/readme.txt
      ...

   The run above closed with ``382 ERROR messages`` over an archive it had written itself
   minutes earlier, and exited 1: 191 ``Missing from tar file`` for the paths the walk
   found, and 191 ``Missing from directory`` for the same paths as the archive names
   them. **The archives are written correctly** -- ``tar tzf`` lists every file -- so the
   finding is about the comparison rather than about the archive.
   To check a PDS4 archive today, unpack it and compare, or use
   :doc:`user_guide_pds4checksums` on the archive file itself.

Two differences from the PDS3 program that are visible in the output
--------------------------------------------------------------------

* **The per-file lines are ``NORMAL``, not ``INFO``**, so nothing caps them: where the
  PDS3 program stops after 100 lines in the walk and the comparison, this one prints one
  per file however large the target is.
* **A ``WARNINGS.log`` is written** in each log directory, beside the ``ERRORS.log`` that
  both flavors write.

Where the logs go
-----------------

Under ``logs/pdsarchives/`` -- the PDS3 program's name, as for all five PDS4 programs --
with ``_archives`` as the suffix in the file name. That is one of the few places where a
PDS4 program's naming is the more predictable of the two: the PDS3 program writes
``_links``.

A target that is a bundle set produces a log file whose name begins with the suffix and
nothing else, because the name is built from the target's own basename and the bundle
set's is already the directory above:

.. code-block:: text

   $PDS4_HOLDINGS_DIR/../logs/pdsarchives/bundles/cassini_uvis_solarocc_beckerjarmak2023/_archives_2026-08-09T01-42-52_initialize.log

Exit status
-----------

0 when the run logged no error, 1 when it did, and 1 for a command line naming no task or
a path that does not exist. 2 for a command line the parser cannot read. A task that
raises, which ``--initialize`` on a target with no archives does, ends the process
through the traceback.
