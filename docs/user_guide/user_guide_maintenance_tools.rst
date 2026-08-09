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
first two also accept a shorter spelling.

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
  and one more thing: **a single file inside a unit**. A run given one narrows its work
  to that file and leaves every other entry in the product alone.
* ``pdsindexshelf`` and ``pds4indexshelf`` take an index table or a metadata directory,
  which is expanded into the tables inside it.

**Relative paths are accepted** and resolved against the working directory before
anything else happens. A path that does not exist ends the run before any log file is
created:

.. code-block:: console

   $ pdsarchives --validate /no/such/volume
   No such file or directory: /no/such/volume

A path that exists but lies outside any holdings tree, or that names checksum or archive
files where the program does not work on them, is also rejected before the first task
starts.

``--log`` and ``--quiet``
-------------------------

.. list-table::
   :header-rows: 1
   :widths: 26 74

   * - Option
     - Meaning
   * - ``--log LOG``, ``-l LOG``
     - Root directory for a *duplicate* of the log files. Defaults to the value of
       ``PDS_LOG_ROOT``; with neither set, no duplicate tree is written.
   * - ``--quiet``, ``-q``
     - Do not also log to the terminal. The log files are written either way.

``--quiet`` suppresses the per-file detail but not the run's own opening and closing
lines, which still reach the terminal:

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

**The default place** is a ``logs`` directory beside the holdings root -- not inside it:

.. code-block:: text

   $PDS3_HOLDINGS_DIR/../logs/<program>/<category>/<unit set>/<unit>_<suffix>_<timestamp>_<task>.log

**The parallel place** is the same shape under the log root, when ``--log`` or
``PDS_LOG_ROOT`` supplies one. The two are the same file when no log root is configured,
and the program writes it once.

A run also appends to an ``ERRORS.log`` in each directory it writes a log file in, and
the PDS4 programs add a ``WARNINGS.log`` beside it that the PDS3 programs do not. Both
accumulate across runs. Where a log root is configured, one more ``ERRORS.log`` is
created directly under ``<log root>/<program>/``, covering the run as a whole.

A ``--log`` run, showing both trees after one validation:

.. code-block:: text

   $PDS3_HOLDINGS_DIR/../logs/pdschecksums/volumes/COUVIS_0xxx/COUVIS_0001_md5_2026-08-09T01-44-21_validate.log
   $PDS3_HOLDINGS_DIR/../logs/pdschecksums/volumes/COUVIS_0xxx/ERRORS.log
   $PDS3_HOLDINGS_DIR/../logroot/pdschecksums/volumes/COUVIS_0xxx/COUVIS_0001_md5_2026-08-09T01-44-21_validate.log
   $PDS3_HOLDINGS_DIR/../logroot/pdschecksums/volumes/COUVIS_0xxx/ERRORS.log
   $PDS3_HOLDINGS_DIR/../logroot/pdschecksums/ERRORS.log

The timestamp has one-second resolution and both copies of one run's log carry the same
one, so the two trees can be compared file for file.

Two things about the program directory are worth knowing before looking for a log.

**The five PDS4 programs write under their PDS3 counterpart's name.** ``pds4checksums``
logs into ``logs/pdschecksums/``, ``pds4archives`` into ``logs/pdsarchives/``, and so on
for all five. The two flavors' logs are therefore mixed in one directory tree, separated
only by the category component below it: a PDS3 run lands under ``volumes/`` and a PDS4
run under ``bundles/``. The same name appears in each PDS4 program's ``--help``
description and in its "Missing task" error, so ``pds4archives --help`` describes itself
as ``pdsarchives``.

**The suffix in a log file's name is not always the program's own.** ``pdsarchives``
writes ``<volume>_links_<timestamp>_<task>.log``, which is the same suffix
``pdslinkshelf`` uses; the two do not collide because the program directory above them
differs. ``pds4archives`` writes ``_archives``. The other suffixes are ``_md5`` for the
checksum programs, ``_info`` for the info shelf programs and ``_index`` for the index
shelf programs, and the index shelf log path is built from the table's own path, so it
carries one more directory level than the rest.

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
     - The command line could not be parsed. ``argparse`` prints the usage and the
       reason.

.. code-block:: console

   $ pdsarchives --nosuchflag $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001
   usage: pdsarchives [-h] [--initialize] [--reinitialize] [--validate]
                      [--repair] [--update] [--log LOG] [--quiet]
                      volume [volume ...]
   pdsarchives: error: unrecognized arguments: --nosuchflag

**The two checksum programs are the exception, and it matters.** ``pdschecksums`` and
``pds4checksums`` exit **0 whatever a task found**. A ``--validate`` that reported every
file in a volume as a mismatch still exits 0, so a script must read the log or the
run's own summary line rather than the status. The other eight programs exit 1 when the
run logged an error. Measured on one volume with one file deliberately altered:

.. code-block:: console

   $ pdschecksums --validate --quiet <volume> ; echo "exit=$?"
   exit=0
   $ pdsinfoshelf --validate --quiet <volume> ; echo "exit=$?"
   exit=1
   $ pdsarchives --validate --quiet <volume> ; echo "exit=$?"
   exit=1

A task that raises an exception ends the process through the traceback rather than
through any of the statuses above; the exception is logged first.

Reading the log
---------------

Every line of a run's output has the same shape:

.. code-block:: text

   <timestamp> | <logger name> |<depth>| <level> | <message>

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

The levels these programs emit, from least to most serious, are ``DEBUG``, ``INFO``,
``NORMAL``, ``WARNING``, ``ERROR``, ``CRITICAL`` and ``EXCEPTION``; ``FATAL`` is another
name for ``CRITICAL``. ``HEADER`` and ``SUMMARY`` are not severities: they are the lines
that open and close a level. Some phases cap how many messages of a level they will
print and say so when they close, which is what a summary line like this reports:

.. code-block:: text

   ... | SUMMARY | 0 DEBUG messages reported of 9 total
