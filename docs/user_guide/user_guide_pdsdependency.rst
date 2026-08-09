pdsdependency
=============

``pdsdependency`` checks that every file a PDS3 volume implies actually exists and is no
older than what it is derived from. The other maintenance programs each own one kind of
derived file and check it against what it describes; this one owns the *relationships*
between them.

**It repairs nothing and creates no holdings product.** What it produces for an operator
is a list of the commands that would supply what is missing, printed under "Steps
required" at the end of a run.

.. code-block:: text

   pdsdependency <volume> [<volume> ...] [--log LOG] [--quiet]

There is no task flag: checking is the only thing this program does. The two options it
does take carry the same meanings they have for the ten programs of
:doc:`user_guide_maintenance_tools`, and the same short forms:

.. list-table::
   :header-rows: 1
   :widths: 26 74

   * - Option
     - Meaning
   * - ``--log LOG``, ``-l LOG``
     - Root directory for a duplicate of the log files. Defaults to the value of
       ``PDS_LOG_ROOT``; with neither set, no duplicate tree is written.
   * - ``--quiet``, ``-q``
     - Do not also log to the terminal. The log files are written either way.

What a path may name
--------------------

A volume, or a volume set, which is expanded into its volumes. Checksum and archive
directories are refused, because the dependencies are stated from the volume's side:

.. code-block:: text

   pdsdependency error: not a volume or volume set directory: <logical path>

What gets checked is decided by the path, not the contents
----------------------------------------------------------

Two tables decide what a volume is tested for. The first maps a path to the names of the
test suites that apply to it, so a path under ``COISS_2xxx`` picks up the Cassini imaging
suites and one under ``VGISS_7xxx`` picks up the Voyager-at-Uranus ones. It holds 49 rows
naming 41 distinct suites between them, and a volume picks up every distinct suite its
path matches -- distinct being the operative word, since a suite named by two matching
rows is still run once.

Every volume picks up ``general``, the suite of derived files every volume has whatever
is in it: checksums, archives, info shelves, link shelves, previews, diagrams, calibrated
images, metadata tables and the cumulative versions of those tables.

Each suite is a list of rules. A rule is a glob that finds the files it is about, a
regular expression that takes such a file apart, and one or more substitutions naming the
files that must exist because of it. Most rules also require the derived file to be **no
older** than its source; directory modification times are taken recursively over every
file below them.

A rule that finds nothing to test says nothing at all, so a short log means the volume
holds few of the things the suites are about, not that little was checked.

Running it
----------

.. code-block:: console

   $ pdsdependency $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:44:24.150392 | pds.validation.dependencies || HEADER | pdsdependency $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:44:24.150796 | pds.validation.dependencies |-| INFO | Log file: $PDS3_HOLDINGS_DIR/../logs/pdsdependency/volumes/COUVIS_0xxx/COUVIS_0001_dependency_2026-08-09T01-44-24.log
   2026-08-09 01:44:24.151032 | pds.validation.dependencies |-| HEADER | Dependency test suite "general": volumes/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:44:24.151118 | pds.validation.dependencies |--| HEADER | Newer checksums for volumes: volumes/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:44:24.151236 | pds.validation.dependencies |---| INFO | Confirmed: checksums-volumes/COUVIS_0xxx/COUVIS_0001_md5.txt
   2026-08-09 01:44:24.151426 | pds.validation.dependencies |--| HEADER | Newer info shelf files for volumes: volumes/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:44:24.151476 | pds.validation.dependencies |---| INFO | Confirmed: _infoshelf-volumes/COUVIS_0xxx/COUVIS_0001_info.pickle
   2026-08-09 01:44:24.151550 | pds.validation.dependencies |---| INFO | Confirmed: _infoshelf-volumes/COUVIS_0xxx/COUVIS_0001_info.py
   2026-08-09 01:44:24.151710 | pds.validation.dependencies |--| HEADER | Newer archives for volumes: volumes/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:44:24.151746 | pds.validation.dependencies |---| INFO | Confirmed: archives-volumes/COUVIS_0xxx/COUVIS_0001.tar.gz
   ...
   2026-08-09 01:44:24.158074 | pds.validation.dependencies || SUMMARY | Completed: pdsdependency $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:44:24.158095 | pds.validation.dependencies || SUMMARY | Elapsed time = 0:00:00.007675
   2026-08-09 01:44:24.158107 | pds.validation.dependencies || SUMMARY | 10 ERROR messages
   2026-08-09 01:44:24.158118 | pds.validation.dependencies || SUMMARY | 30 INFO messages

The log is organized by suite title: one level per suite, one level per rule inside it,
and ``Confirmed:`` at ``INFO`` for each file that is present and current.

"Steps required"
----------------

Everything the run found missing is turned into the command that would supply it, and the
list is printed to the terminal after the log is closed. It is in dependency order, so it
can be run top to bottom:

.. code-block:: text

   Steps required:
      pdschecksums --initialize $PDS3_HOLDINGS_DIR/archives-volumes/COUVIS_0xxx
      pdsinfoshelf --initialize $PDS3_HOLDINGS_DIR/archives-volumes/COUVIS_0xxx
      pdschecksums --initialize $PDS3_HOLDINGS_DIR/metadata/COUVIS_0xxx/COUVIS_0001
      pdsinfoshelf --initialize $PDS3_HOLDINGS_DIR/metadata/COUVIS_0xxx/COUVIS_0001
      pdsarchives --initialize $PDS3_HOLDINGS_DIR/metadata/COUVIS_0xxx/COUVIS_0001
      pdschecksums --initialize $PDS3_HOLDINGS_DIR/archives-metadata/COUVIS_0xxx
      pdsinfoshelf --initialize $PDS3_HOLDINGS_DIR/archives-metadata/COUVIS_0xxx
      pdschecksums --initialize $PDS3_HOLDINGS_DIR/previews/COUVIS_0xxx/COUVIS_0001
      pdsinfoshelf --initialize $PDS3_HOLDINGS_DIR/previews/COUVIS_0xxx/COUVIS_0001
      pdsarchives --initialize $PDS3_HOLDINGS_DIR/previews/COUVIS_0xxx/COUVIS_0001
      pdschecksums --initialize $PDS3_HOLDINGS_DIR/archives-previews/COUVIS_0xxx
      pdsinfoshelf --initialize $PDS3_HOLDINGS_DIR/archives-previews/COUVIS_0xxx
      pdslinkshelf --initialize $PDS3_HOLDINGS_DIR/metadata/COUVIS_0xxx/COUVIS_0001
      cat $PDS3_HOLDINGS_DIR/metadata/COUVIS_0xxx/COUVIS_0???/COUVIS_0???_supplemental_index.tab > $PDS3_HOLDINGS_DIR/metadata/COUVIS_0xxx/COUVIS_0999/COUVIS_0999_supplemental_index.tab
      <LABEL> $PDS3_HOLDINGS_DIR/metadata/COUVIS_0xxx/COUVIS_0999/COUVIS_0999_supplemental_index.tab

Two of the lines above are not runnable as they stand, and that is deliberate. A
cumulative metadata table is built by concatenating the per-volume tables with ``cat``,
which the run writes out in full; the ``<LABEL>`` line beneath it is a placeholder for
writing the label of the table just concatenated, which is a manual step this package does
not automate.

Where the logs go
-----------------

Under ``logs/pdsdependency/``, with ``_dependency`` as the suffix and **no task component
in the file name**, since there is no task:

.. code-block:: text

   $PDS3_HOLDINGS_DIR/../logs/pdsdependency/volumes/COUVIS_0xxx/COUVIS_0001_dependency_2026-08-09T01-44-24.log

An ``ERRORS.log`` accompanies it, and where a log root is configured a third one is
written at that root's own ``pdsdependency`` directory.

Exit status
-----------

0 when the run logged no error, 1 when it did, and 1 for a path that is not a volume or a
volume set under ``volumes/``. The run above exited 1.

Called from elsewhere
---------------------

:doc:`user_guide_re_validate` runs this program's check as the last of its five
per-volume validations, as a library call rather than as a subprocess. Running
``re_validate --timeless`` is what turns off the "no older than" half of the rules
described above; this program itself has no option for that.
