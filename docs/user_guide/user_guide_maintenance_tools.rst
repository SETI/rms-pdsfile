The Maintenance Tools: the Command Line They Share
==================================================

Ten of the fifteen programs in this guide take **the same command line**. They are the
five kinds of derived product described in :doc:`user_guide_concepts`, each in a PDS3 and
a PDS4 flavor:

.. list-table::
   :header-rows: 1
   :widths: 24 24 16 36

   * - PDS3 program
     - PDS4 program
     - Unit
     - Options beyond the shared set
   * - ``pdschecksums``
     - ``pds4checksums``
     - volume / bundle
     - ``--archives``, ``--infoshelf``
   * - ``pdsarchives``
     - ``pds4archives``
     - volume / bundle
     - none
   * - ``pdsinfoshelf``
     - ``pds4infoshelf``
     - volume / bundle
     - ``--archives``
   * - ``pdslinkshelf``
     - ``pds4linkshelf``
     - volume / bundle
     - none
   * - ``pdsindexshelf``
     - ``pds4indexshelf``
     - table
     - none

This chapter is the reference for everything they share. Each program's own chapter
covers only what it builds, where it puts it, and the options in the last column.

The five remaining programs -- :doc:`user_guide_pdsdependency`,
:doc:`user_guide_re_validate`, :doc:`user_guide_crlf`,
:doc:`user_guide_shelf_consistency_check` and :doc:`user_guide_show_opus_products` --
have command lines of their own and none of what follows applies to them, except that
``pdsdependency`` and ``re_validate`` take ``--log`` and ``--quiet`` with the meanings
given below.

Invocation
----------

.. code-block:: text

   <program> <task> <unit> [<unit> ...] [--log LOG] [--quiet]

The task and at least one unit path are both required. Everything else is optional.

The task flags
--------------

Exactly one task is performed per run. Each flag is spelled out in full below, and the
first two also accept a shorter spelling. **None of the five has a default**: all five
write into one destination whose default is empty, which is what makes a command line
naming no task an error rather than a run of some assumed task.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Flag
     - What it does
   * - ``--initialize``, ``--init``
     - Build the product for each target. Report an error if it already exists.
   * - ``--reinitialize``, ``--reinit``
     - Build the product, replacing one that already exists.
   * - ``--validate``
     - Compare the product against what it describes and report the differences. Write
       nothing.
   * - ``--repair``
     - Compare, and rewrite the product only if it disagrees.
   * - ``--update``
     - Add entries for anything the product does not yet cover. Leave existing entries
       alone.

**A command line naming no task is rejected**, with the program's own name in the
message and status 1:

.. code-block:: console

   $ pdsarchives $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001
   pdsarchives error: Missing task

**A command line naming more than one task is accepted, and the last one wins.** The five
flags all write into a single destination, so nothing rejects the combination. The run
below performed ``validate``, not ``repair``:

.. code-block:: console

   $ pdsarchives --repair --validate $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001
   ... | pds.validation.archives |-| HEADER | Task validate for: ...

The unit argument
-----------------

The positional argument is one or more paths, and its name in the help text is the
program's unit: ``volume``, ``bundle`` or ``table``. It is repeatable, and each path is
handled in turn.

What a path may name depends on the program, and the three groups differ:

* ``pdsarchives``, ``pds4archives``, ``pdslinkshelf`` and ``pds4linkshelf`` take a unit
  or a unit set directory. A unit set is expanded into its units and each is handled
  separately -- except for ``pds4archives``, where what one archive covers is decided by
  the bundle set's own rules and a path is not expanded at all.
* ``pdschecksums``, ``pds4checksums``, ``pdsinfoshelf`` and ``pds4infoshelf`` take those
  and one more thing: **a single top-level file of a unit**, or a unit's own archive
  file. A run given one narrows its work to that file and leaves every other entry in
  the product alone. A file deeper inside the unit is refused with status 1, under
  ``Invalid file for checksumming:`` from the two checksum programs and ``Invalid file
  for an infoshelf:`` from the two info shelf programs. A path under a
  ``checksums-`` category is refused before that, under ``No checksums for checksum
  files:`` or ``No infoshelves for checksum files:``, also with status 1.
  ``--reinitialize`` on a selection is run as ``--update`` instead, because rebuilding a
  whole product from one named file would erase the rest.

  ``--initialize`` does not accept a selection either, but it is not refused up front:
  path resolution succeeds and the log files open before anything checks. If the product
  already exists the run stops on that instead, since ``--initialize`` refuses to replace
  one. Otherwise all four report ``File selection is disallowed for task "initialize"``,
  in one of two ways: the two checksum programs raise :exc:`ValueError` carrying that
  text, and the two info shelf programs log it as an error and exit 1.
* ``pdsindexshelf`` and ``pds4indexshelf`` take an index table or a metadata directory,
  which is expanded into the tables inside it.

**Relative paths are accepted** and resolved against the working directory before
anything else happens. An unusable path then ends the run before any log file is created,
always with status 1, but what the ten programs say about it depends on two things: which
of two families the program belongs to, and **where the path is**, not whether it exists.

The families are the four checksum and info shelf programs on one side, and the two
archive, two link shelf and two index shelf programs on the other. The first thing the
first family does is look for ``/holdings/`` or ``/pds4-holdings/`` in the path, so for
that family the question is location; the second family resolves the path first, so for
it the question is existence.

.. list-table::
   :header-rows: 1
   :widths: 34 33 33

   * - The path
     - Checksum and info shelf
     - Archive, link shelf and index shelf
   * - is outside any holdings tree, whether or not it exists
     - ``Not a holdings subdirectory:`` and the absolute path
     - an unhandled :exc:`ValueError` traceback, ``Not compatible with a logical path:``
   * - is inside a holdings tree but does not exist
     - an unhandled :exc:`OSError` traceback, ``File not found:``, naming the path as it
       looks from the holdings root
     - ``No such file or directory:`` and the absolute path

So the tidy message and the traceback swap sides according to where the bad path is:

.. code-block:: console

   $ pdsarchives --validate /no/such/volume
   No such file or directory: /no/such/volume

   $ pdschecksums --validate /no/such/volume
   Not a holdings subdirectory: /no/such/volume

A path naming checksum or archive files where the program does not work on them is
rejected with a message.

``--log`` and ``--quiet``
-------------------------

.. list-table::
   :header-rows: 1
   :widths: 26 74

   * - Option
     - Meaning
   * - ``--log LOG``, ``-l LOG``
     - Root directory for a *duplicate* of the log files. Defaults to the value of
       ``PDS_LOG_ROOT``; with neither set, no duplicate tree is written. Default: empty,
       which means "consult the environment variable".
   * - ``--quiet``, ``-q``
     - Do not also log to the terminal. The log files are written either way. Default:
       off.

Every program in this guide also takes ``--help``, ``-h``, which prints the usage and
exits 0 without doing anything else. It is not repeated in the option tables.

``--quiet`` silences every level of the log below the run's own. The per-target header,
the ``Log file:`` lines and all the per-file detail go with it. What survives depends on
whether a log root is configured. **With none, the run's own opening and closing lines
still reach the terminal** -- its ``HEADER`` and its ``SUMMARY`` lines, counts and all --
because with no handler attached anywhere the outermost level falls back to printing. Add
``--log`` or ``PDS_LOG_ROOT`` and a handler exists, so ``--quiet`` leaves **nothing** on
the terminal at all. The run below had no log root:

.. code-block:: console

   $ pdschecksums --validate --quiet $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:44:22.453034 | pds.validation.checksums || HEADER | pdschecksums --validate --quiet $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:44:22.455568 | pds.validation.checksums || SUMMARY | Completed: pdschecksums --validate --quiet $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:44:22.455577 | pds.validation.checksums || SUMMARY | Elapsed time = 0:00:00.002523
   2026-08-09 01:44:22.455583 | pds.validation.checksums || SUMMARY | 21 INFO messages
   2026-08-09 01:44:22.455586 | pds.validation.checksums || SUMMARY | 0 DEBUG messages reported of 9 total

.. _where-logs-go:

Where the logs go
-----------------

Each target of each run gets its own log file, and a run writes it in one place or two.

A ``logs`` directory beside the holdings root -- not inside it -- always gets a copy:

.. code-block:: text

   $PDS3_HOLDINGS_DIR/../logs/<program>/<category>/<unit set>/<unit>_<suffix>_<timestamp>_<task>.log

A configured log root, from ``--log`` or ``PDS_LOG_ROOT``, gets a second copy in the same
shape below it. With no log root the two collapse to one path and the program writes it
once. When both exist the program reports the log-root copy **first**:

.. code-block:: text

   ... | INFO | Log file: <log root>/pdsarchives/volumes/COUVIS_0xxx/COUVIS_0001_archives_..._initialize.log
   ... | INFO | Log file: $PDS3_HOLDINGS_DIR/../logs/pdsarchives/volumes/COUVIS_0xxx/COUVIS_0001_archives_..._initialize.log

Eight of the ten programs also append to an ``ERRORS.log`` in each directory they write a
log file in, and the PDS4 programs add a ``WARNINGS.log`` beside it that the PDS3
programs do not. Both accumulate across runs rather than being replaced.

``pdsindexshelf`` and ``pds4indexshelf`` are the exception. They attach those files to
the program's own directory instead, so a run produces one of each however many tables it
shelves, and the directory holding a table's log file holds no ``ERRORS.log`` at all.

Where a log root is configured, one more set is created directly under
``<log root>/<program>/``, covering the run as a whole: an ``ERRORS.log`` for a PDS3
program, and an ``ERRORS.log`` and a ``WARNINGS.log`` for a PDS4 one.

A ``pdschecksums --log`` run, showing both trees after one validation:

.. code-block:: text

   $PDS3_HOLDINGS_DIR/../logs/pdschecksums/volumes/COUVIS_0xxx/COUVIS_0001_md5_2026-08-09T01-44-21_validate.log
   $PDS3_HOLDINGS_DIR/../logs/pdschecksums/volumes/COUVIS_0xxx/ERRORS.log
   <log root>/pdschecksums/volumes/COUVIS_0xxx/COUVIS_0001_md5_2026-08-09T01-44-21_validate.log
   <log root>/pdschecksums/volumes/COUVIS_0xxx/ERRORS.log
   <log root>/pdschecksums/ERRORS.log

The timestamp has one-second resolution and both copies of one run's log carry the same
one, so the two trees can be compared file for file.

**Every program writes under its own name**, so ``pds4checksums`` logs into
``logs/pds4checksums/`` and ``pdschecksums`` into ``logs/pdschecksums/``, and the two
flavors of one program never share a directory. That name is also what each program's
``--help`` description and "Missing task" error call it.

.. note::

   An existing log tree carries an older layout, and so does any script written against
   it. The five PDS4 programs wrote under their PDS3 counterpart's name --
   ``pds4archives`` into ``logs/pdsarchives/`` -- so the two flavors' logs were mixed in
   one tree, separated only by the category component below. ``pdsarchives`` wrote its
   suffix as ``_links`` rather than ``_archives``.

**The suffix in a log file's name is the program's kind.** The archive programs write
``<unit>_archives_<timestamp>_<task>.log``, and the link shelf programs ``_links``. The
others are ``_md5`` for the checksum programs and ``_info`` for the info shelf programs.
The two index shelf programs insert **no suffix at all**: their log path is built from the
table's own path, so it carries one more directory level than the rest and the file is
named for the table. A table named ``COUVIS_0001_versions.tab`` therefore produces a log
with no ``_index`` anywhere in it.

Exit statuses
-------------

.. list-table::
   :header-rows: 1
   :widths: 12 88

   * - Status
     - Meaning
   * - ``0``
     - The run finished. For most programs this also means nothing was logged as an
       error; see below for the two where it does not.
   * - ``1``
     - The command line named no task, or named a path that does not exist or that the
       program refuses, or the run logged an error or a fatal.
   * - ``2``
     - The command line could not be parsed. :mod:`argparse` prints the usage and the
       reason.

.. code-block:: console

   $ pdsarchives --nosuchflag $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001
   usage: pdsarchives [-h] [--initialize] [--reinitialize] [--validate]
                      [--repair] [--update] [--log LOG] [--quiet]
                      volume [volume ...]
   pdsarchives: error: unrecognized arguments: --nosuchflag

**Every program reports a logged fatal or error the same way**: 0 when the run logged
neither, and 1 when it logged either. A ``--validate`` that reports a mismatch exits 1,
so a script can branch on the status rather than parsing the log. Measured on one volume
whose checksum file was written first and one of whose files was then altered:

.. code-block:: console

   $ pdschecksums --initialize --quiet <volume> ; echo "exit=$?"
   exit=0
   $ printf 'CORRUPTED\r\n' >> <volume>/INDEX/INDEX.TAB
   $ pdschecksums --validate --quiet <volume> ; echo "exit=$?"
   exit=1

A task that raises an exception ends the process through the traceback rather than
through any of the statuses above; the exception is logged first.

Reading the log
---------------

Every line of a run's output has the same shape:

.. code-block:: text

   <timestamp> | <logger name> |<depth>| <level> | <message>

**The order of the per-file lines is the order the filesystem lists a directory in**, so
two runs over one unit can report the same files in a different order; only the counts in
the closing ``SUMMARY`` lines are stable. Each example in this guide shows one run's
order.

The depth marker is a run of hyphens between two vertical bars, one per open level, so
``||`` is the run itself, ``|-|`` one target within it, and ``|--|`` a phase of that
target's work. ``HEADER`` opens a level and ``SUMMARY`` closes it, reporting the elapsed
time and a count of every level of message the closed level saw.

The logger name identifies the kind of work rather than the program, so both flavors of
a program share one: ``pds.validation.checksums``, ``pds.validation.archives``,
``pds.validation.fileinfo``, ``pds.validation.links`` and ``pds.validation.indexshelf``.
One consequence is visible from a script: the two flavors of one program cannot be
driven from a single Python process, because the second attempt to register the shared
logger name raises.

The level names are not a ladder of distinct rungs. Several share one severity, and the
name in the log is the one the message was written with rather than the severity it
carries:

.. list-table::
   :header-rows: 1
   :widths: 16 44 40

   * - Severity
     - Names at that severity
     - What the extra names are for
   * - 1
     - ``HIDDEN``
     - a message the default configuration does not print at all
   * - 10
     - ``DEBUG``, ``DS_STORE``
     - a skipped ``.DS_Store``
   * - 20
     - ``INFO``, ``NORMAL``, ``HEADER``
     - ``NORMAL`` is the per-file line of a PDS4 program; ``HEADER`` opens a level
   * - 30
     - ``WARNING``, ``INVISIBLE``
     - a file whose name begins with a dot
   * - 40
     - ``ERROR``, ``DOT_``
     - a skipped dot-underscore file
   * - 50
     - ``CRITICAL``, ``EXCEPTION``
     - ``EXCEPTION`` is what a logged traceback carries

Those twelve names are every registered level. Two more names work but are aliases
rather than levels of their own: ``FATAL`` for ``CRITICAL`` and ``WARN`` for
``WARNING``.

``DOT_`` is the one worth knowing. It carries **ERROR's severity**, so a stray
``._something`` file inside a unit is enough on its own to make one of the eight programs
that report their outcome exit 1, under a level name that does not look like an error.

``SUMMARY`` is the exception to the table: it is the only thing appearing in the level
field that is not a registered level. The logger writes it as a literal tag when it
closes a level, and emits those lines at ``HEADER``'s severity of 20. **A summary line
counting errors therefore carries severity 20 itself**, which matters to anything
filtering a log by severity: ``ERRORS.log`` holds the individual errors, not the summary
line that counts them.

Some phases cap how many messages of a level they will print and say so when they close,
which is what a summary line like this reports:

.. code-block:: text

   ... | SUMMARY | 0 DEBUG messages reported of 9 total
