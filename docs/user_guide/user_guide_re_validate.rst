re_validate
===========

``re_validate`` re-runs five of the PDS3 maintenance validations over whole volumes and
writes one log per volume covering all five. It fixes nothing: every task it calls is a
validation, and a failure is logged rather than repaired.

It is not a console script. Run it as a module:

.. code-block:: text

   python -m pdsfile.holdings_maintenance.pds3.re_validate <path> [<path> ...] [options]

What it runs, and what it does not
----------------------------------

The five are the checksum, archive, info shelf, link shelf and dependency validations --
that is, the validation task of :doc:`user_guide_pdschecksums`,
:doc:`user_guide_pdsarchives`, :doc:`user_guide_pdsinfoshelf` and
:doc:`user_guide_pdslinkshelf`, plus the whole of :doc:`user_guide_pdsdependency`. They
are called as library functions rather than as subprocesses, so what each of them
validates is whatever that program validates.

**Five is not all of them.** Three checks in this package are never reached from here:

* :doc:`user_guide_pdsindexshelf` offers a validation task under the same name as the
  four that are called, and this program neither imports nor runs it. **The index shelves
  of a volume's metadata tables are not re-validated here.**
* :doc:`user_guide_shelf_consistency_check`, which looks for shelves with nothing left to
  describe, has no task to call.
* :doc:`user_guide_crlf`, which checks line terminators, has none either.

There is no PDS4 counterpart to this program.

Two modes
---------

**Interactive mode** is the default. Each path names a volume, or a volume set that is
expanded into its volumes, and every volume named is validated before the run exits.

**Batch mode**, selected by ``--batch`` *or* by ``--batch-status``, takes **holdings
roots** rather than volumes. It
works out which volumes have changed since they were last validated and which have gone
longest without one, validates them in that order until ``--minutes`` is up, and mails a
report.

The positional argument therefore means two different things depending on whether the
run is in batch mode. It is not the only flag in the guide that changes what a path
means: ``--archives`` does the same for the four checksum and info shelf programs.

Options
-------

Twenty options, in four groups.

Logging
~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 26 74

   * - Option
     - Meaning
   * - ``--log LOG``, ``-l LOG``
     - Root directory for a duplicate of the log files. Defaults to ``PDS_LOG_ROOT``.
       Logs are written into the ``re-validate`` subdirectory of each log root.
   * - ``--quiet``, ``-q``
     - Do not also log to the terminal.

Which tests to run
~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 26 74

   * - Option
     - Meaning
   * - ``--checksums``, ``-C``
     - Validate MD5 checksums.
   * - ``--archives``, ``-A``
     - Validate archive files.
   * - ``--info``, ``-I``
     - Validate info shelves.
   * - ``--links``, ``-L``
     - Validate link shelves.
   * - ``--dependencies``, ``-D``
     - Validate dependencies.
   * - ``--full``, ``-F``
     - All five. This is also what naming none of them means.
   * - ``--timeless``, ``-T``
     - Suppress the "newer modification date" tests in the dependency validation.

Which trees to examine
~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 26 74

   * - Option
     - Meaning
   * - ``--volumes``, ``-v``
     - Check ``volumes/`` directories.
   * - ``--calibrated``, ``-c``
     - Check ``calibrated/`` directories.
   * - ``--diagrams``, ``-d``
     - Check ``diagrams/`` directories.
   * - ``--metadata``, ``-m``
     - Check ``metadata/`` directories.
   * - ``--previews``, ``-p``
     - Check ``previews/`` directories.
   * - ``--all``, ``-a``
     - All five of the trees above. This is also what naming none of them means. The
       help text adds "plus their checksums and archives", which describes what the
       tests then cover for those trees rather than a sixth and seventh selection.

**Naming none of a group selects all of it**, and so does the group's own ``--all`` or
``--full``. Two tests are then narrowed to the trees they can run against: link shelves
exist only for ``volumes``, ``calibrated`` and ``metadata``, and the dependency test only
makes sense over ``volumes``.

Batch mode
~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 26 74

   * - Option
     - Meaning
   * - ``--batch``, ``-b``
     - Operate in batch mode. The positional paths become holdings roots. Default: off.
   * - ``--minutes MINUTES``
     - Rough upper limit on the run, in minutes. Default **60**. A volume already started
       when the limit passes is finished; no new one is begun.
   * - ``--batch-status``
     - Print the schedule batch mode would follow, and validate nothing. This also puts
       the run in batch mode, so the positional paths are holdings roots. Default: off.
   * - ``--email ADDR``
     - Address to mail a report to when a batch job completes. Repeat for more than one.
   * - ``--error-email ADDR``
     - Address to mail an error-only report to. Nothing is sent if no errors were found.
       Repeat for more than one.

``--email`` and ``--error-email`` accumulate, and ``--minutes`` takes a whole number of
minutes; every other option in this group is a plain switch.
Mail is sent through a fixed relay host on port 25, unauthenticated, from a fixed sender
address. There is no option for either.

Option names may be abbreviated to any unambiguous prefix, which is not true of
:doc:`user_guide_crlf` or :doc:`user_guide_shelf_consistency_check`.

An interactive run
------------------

.. code-block:: console

   $ python -m pdsfile.holdings_maintenance.pds3.re_validate --log $PDS3_HOLDINGS_DIR/../logroot $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:44:58.231134 | pds.validation || HEADER | <source root>/pdsfile/holdings_maintenance/pds3/re_validate.py --log $PDS3_HOLDINGS_DIR/../logroot $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001

   2026-08-09 01:44:58.231652 | pds.validation |-| HEADER | Re-validate $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:44:58.231783 | pds.validation |--| INFO | Last modification: 2020-05-13 00:30:45
   2026-08-09 01:44:58.231853 | pds.validation |--| INFO | Volume types: volumes, calibrated, diagrams, metadata, previews
   2026-08-09 01:44:58.231907 | pds.validation |--| INFO | Tests: checksums, archives, infoshelves, linkshelves, dependencies

   2026-08-09 01:44:58.232008 | pds.validation |--| HEADER | Checksum re-validation for: volumes/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:44:58.232268 | pds.validation.checksums || HEADER | Reading MD5 checksums: checksums-volumes/COUVIS_0xxx/COUVIS_0001_md5.txt
   ...
   2026-08-09 01:44:58.258094 | pds.validation || SUMMARY | Completed: <source root>/pdsfile/holdings_maintenance/pds3/re_validate.py --log $PDS3_HOLDINGS_DIR/../logroot $PDS3_HOLDINGS_DIR/volumes/COUVIS_0xxx/COUVIS_0001
   2026-08-09 01:44:58.258117 | pds.validation || SUMMARY | Elapsed time = 0:00:00.026954
   2026-08-09 01:44:58.258131 | pds.validation || SUMMARY | 2 CRITICAL messages
   2026-08-09 01:44:58.258143 | pds.validation || SUMMARY | 63 ERROR messages
   2026-08-09 01:44:58.258153 | pds.validation || SUMMARY | 159 INFO messages reported of 174 total
   2026-08-09 01:44:58.258163 | pds.validation || SUMMARY | 19 DEBUG messages reported of 33 total

The two ``INFO`` lines after the volume's own header are the run stating what it settled
on: the volume types and the tests, both defaulted here because the command line named
neither.

The nested logger names are the individual validations' own --
``pds.validation.checksums`` here, and ``pds.validation.archives``,
``pds.validation.fileinfo``,
``pds.validation.links`` and ``pds.validation.dependencies`` further down, one per
section -- so one log carries all five and each section is identifiable by its logger.

Batch mode's schedule
---------------------

``--batch-status`` prints the order without validating anything:

.. code-block:: console

   $ python -m pdsfile.holdings_maintenance.pds3.re_validate --batch-status --log $PDS3_HOLDINGS_DIR/../logroot $PDS3_HOLDINGS_DIR
      1         COUVIS_0xxx/COUVIS_0009  modified , not previously validated
      2         COUVIS_0xxx/COUVIS_0058  modified , not previously validated
      3          COUVIS_0xxx/COUVIS_0001  modified 2020-05-13, last validated 2026-08-09, duration 0:00:00, error logged

**The schedule comes from two places and no third.** It walks the log root -- the one
under ``--log`` or ``PDS_LOG_ROOT``, not the ``logs`` directory beside the holdings tree
-- for the record of what has been validated, and it globs each holdings tree for the
volumes that exist and the date each carries. A volume whose current date is not one the
logs recorded goes first; the rest follow oldest validation first. There is no state file
and no database.

Two consequences follow directly:

* A batch run against a log root holding no logs treats **every** volume as never
  validated.
* A batch run with **no log root at all** has nothing to walk and ends in a
  :exc:`TypeError`. ``--log`` or ``PDS_LOG_ROOT`` is required in batch mode, and nothing
  checks for it up front.

Where the logs go
-----------------

In the ``re-validate`` subdirectory of a ``logs`` directory beside the holdings tree,
and, where a log root is configured, in the same subdirectory under that root. **The
volume's category component is dropped from the path**, so a volume's logs sit directly
under a directory named for its volume set:

.. code-block:: text

   $PDS3_HOLDINGS_DIR/../logroot/re-validate/COUVIS_0xxx/COUVIS_0001_re-validate_2026-08-09T01-44-58.log
   $PDS3_HOLDINGS_DIR/../logroot/re-validate/ERRORS.log

That shape is not incidental: it is what batch mode reads a volume set and a volume name
back out of.

Exit status
-----------

**Interactive mode**: 1 if a path is unusable or the run logged a fatal or an error, 0
otherwise.

**Batch mode**: **0 even when the run logged errors.** A nonzero status would cancel the
launch daemon that schedules it, so the status deliberately says nothing about what the
validations found -- the mailed report does. That covers anything a validation finds and
not everything: the mail is sent from the same block that would exit 0, so a mail relay
that cannot be reached ends the run in the exception instead.

Three things still exit 1 in batch mode, all of them decided from the command line
before any validation starts: naming no path at all (``No holdings path identified``),
naming one that does not exist (``Holdings path not found:``), and naming one that does
exist but whose resolved path does not end in ``/holdings`` (``Not a holdings
directory:``) -- the test is on the last path component, so a directory named
``pdsholdings`` is rejected too. The guarantee is about what the validations found, not
about the command line being usable.
