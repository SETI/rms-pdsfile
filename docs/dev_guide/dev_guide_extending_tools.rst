Extending, Part B: the Maintenance Tools and a New Dataset
==========================================================

The maintenance tools (the user guide documents each one) are generic over the
holdings tree: they walk whatever bundle sets are there, so publishing a new dataset
usually requires no tool change at all -- once the rules file of
:doc:`dev_guide_extending_rules` exists, the checksum, archive, info shelf and index
shelf tools handle the new set as they handle every other. Two pieces of
dataset-specific state are the exceptions: the link-repair table that ``pdslinkshelf``
applies to volumes published with bad internal links, and (for PDS3 dependency
checking) the rule tables in ``pdsdependency.py``, whose module docstring describes
its own ``TESTS`` registry. This chapter covers the shared tool specification a
developer meets first when reading any tool, and then the repair table, which is the
piece a new dataset most often needs.

How a tool is put together: filling a ``ToolSpec``
--------------------------------------------------

Ten of the fifteen maintenance programs -- the five PDS3/PDS4 pairs -- build no parser
and no driver of their own. Each tool module defines its task functions, declares one
:class:`~pdsfile.holdings_maintenance._common.ToolSpec`, and hands both to the shared
driver. The spec is a dataclass carrying **data only**: everything that differs
between the two halves of a pair that is a class, a string or a callable. Where the
halves differ in what they *do*, the code stays in the tool module and the spec says
nothing about it.

This is ``pdsarchives``'s spec, verbatim from
:mod:`pdsfile.holdings_maintenance.pds3.pdsarchives`:

.. code-block:: python

    SPEC = _common.ToolSpec(
        progname='pdsarchives',
        logname=LOGNAME,
        pdsfile_cls=pdsfile.Pds3File,
        unit='volume',
        holdings_sentinel='/holdings/',
        index_ext='.tab',
        file_log_level='info',
        description=_archives_common.ARCHIVE_DESCRIPTION,
        task_help=_archives_common.ARCHIVE_TASK_HELP,
        positional_help=_archives_common.ARCHIVE_POSITIONAL_HELP,
        log_path_method='log_path_for_volume',
        log_suffix='_archives',
        expand_target=archive_targets,
        handler_factories=(pdslogger.error_handler,),
        lskip_for=archive_lskip)

    TASKS = {'initialize': initialize,
             'reinitialize': reinitialize,
             'validate': validate,
             'repair': repair,
             'update': update}

    def main():
        _common.run_main(SPEC, TASKS, sys.argv)

The fields fall into three groups. The identity group (``progname``, ``logname``,
``pdsfile_cls``, ``unit``) names the tool, its logger, its
:class:`~pdsfile.pdsfile.PdsFile` class and what one command-line target is -- a
volume, a bundle or a table. Comparing ``pds4archives``'s spec against the one above
shows how much of a pair's difference is data: it differs in the identity group, the
three flavor fields, the log-path method name, and its handler tuple, which adds a
warning handler -- nine fields. The parser texts and the log suffix are shared from
``_archives_common``, and the two archive callables are each module's own function
of the same name. The flavor group (``holdings_sentinel``, ``index_ext``,
``file_log_level``) is the same for all five specs of one flavor, and each field acts
on some tools only -- the spec docstring names, for every field, exactly which shared
functions read it, because "the spec carries it" and "this tool acts on it" are
different claims. The behavior group (``expand_target``, ``lskip_for``,
``generate_links``, ``link_target_regex``, ``extra_arguments`` and the help texts) is
where a tool plugs its own callables into the shared drivers:
``_common.build_arg_parser()`` builds the parser from the spec,
``_common.run_main()`` (or the selection- and index-flavored drivers in
``_shelf_common`` and ``_indexshelf_common``) resolves targets, sets up per-target
logs and dispatches to the task functions.

To change a tool's behavior for a dataset, then: if the change is data -- a message,
an extra option, which files a target expands to -- it belongs in the spec or in the
tool's own callables; if it is logic shared by a pair, it belongs in the family's
``_*_common`` module; and if it is a published volume's own defect, it belongs in the
repair table below, not in code.

Authoring ``pdslinkshelf`` repairs
----------------------------------

A PDS3 label, catalog or text file names the files it points at, and some of those
names are wrong in the volume *as published*: a format file named without its
directory, a figure named with a dot where the file has an underscore. A published
volume is never edited, so the correction lives in the repository instead:
:mod:`pdsfile.holdings_maintenance.pds3.linkshelf_repairs` is a data table --
``REPAIRS``, a ``translator.TranslatorByRegex`` of 141 entries and nothing else --
and ``pdslinkshelf`` applies it as it scans. (``pds4linkshelf`` declares its own
``REPAIRS`` as an empty translator; there is no PDS4 counterpart table.)

Each entry is a triple:

* a regular expression matched against the **absolute path of the file being
  scanned**. The translator anchors patterns at both ends, so nearly every entry
  begins ``.*/``; scope it as tightly as the defect -- a volume set, a range of
  volumes, one file;
* the ``re`` flags for that pattern (0 in all but two entries);
* an inner translator from the link text as written to the text it was meant to
  carry: a ``TranslatorByDict`` when the bad links are a fixed list, or a nested
  ``TranslatorByRegex`` when a whole family can be rewritten by group.

For each scanned file, ``generate_links()`` collects the inner translators of every
entry whose pattern matched that file's path, and asks each in turn about each link's
text; **the first that answers wins**, so of two entries matching the same file, the
one written earlier in the table applies. What a replacement does depends on its
shape: a bare basename is resolved as though the label had been written that way; a
name carrying a slash is joined to the scanned file's directory and checked for
existence immediately, so a repair pointing at nothing surfaces as an error in the
run that first uses it; and an empty string drops the link from the shelf entirely.

**When to add an entry.** A ``pdslinkshelf --validate`` or ``--initialize`` run over
the new volumes reports a link it cannot resolve -- "Unable to locate .FMT file", a
label that does not point at the file named after it -- and inspection shows the
volume itself is wrong. Entries are grouped by mission in roughly alphabetical order
of volume set name, each group under a comment naming it; a family of near-identical
entries can be generated by a comprehension, as most of the JNOJIR group is.

A worked example, from the table as it stands. The Cassini CIRS volumes' top-level
``DATAINFO.TXT`` names its format files without the directories they sit in, so a
scan reports every one of them unlocatable. The entry:

.. code-block:: python

    (r'.*/COCIRS_[01].*/DATAINFO\.TXT', 0,
      translator.TranslatorByDict(
        {'DIAG.FMT'             : 'UNCALIBR/DIAG.FMT',
         'FRV.FMT'              : 'UNCALIBR/FRV.FMT',
         'GEO.FMT'              : 'NAV_DATA/GEO.FMT',
         'HSK.FMT'              : 'HSK_DATA/HSK.FMT',
         ...
         'TAR.FMT'              : 'NAV_DATA/TAR.FMT'})),

The outer pattern claims exactly the ``DATAINFO.TXT`` of the COCIRS_0xxx and
COCIRS_1xxx volumes, not every COCIRS volume: the 5xxx and 6xxx series carry entries
of their own in the same group, for different files with different corrections. The inner dictionary maps each bad link text to the corrected
one; every replacement carries a slash, so each is joined to the scanned file's
directory and existence-checked the first time the entry fires, which is the check
that catches a typo in the repair itself. After adding an entry, rerun
``pdslinkshelf --reinitialize`` (or ``--repair``) on the affected volumes and confirm
the run no longer reports the link; the tool-test suite of :doc:`dev_guide_testing`
then pins the tool's behavior generally, and the repair table needs no test of its
own per entry.

Two behaviors of the scanner bound what a repair can do, and both are documented at
length in the module docstring of
:mod:`pdsfile.holdings_maintenance.pds3.linkshelf_repairs`: only files whose
upper-cased extension is ``.LBL``, ``.CAT``, ``.TXT``, ``.FMT`` or ``.SFD`` are read
for links at all, and a link written with a directory prefix that resolves nowhere is
cut back to its basename only for files that matched at least one ``REPAIRS`` entry.
