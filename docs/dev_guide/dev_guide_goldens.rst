How-To: Regenerating Goldens
============================

The goldens under ``tests/golden/full/`` are recorded answers: what
:meth:`~pdsfile._opus._OpusMixin.opus_products` and
:meth:`~pdsfile._associations._AssociationsMixin.associated_abspaths` returned for
named inputs, and what the maintenance tools wrote and logged over the declared
source subsets. They exist so that a change in output is a *visible decision* rather
than a silent drift. Everything in this chapter follows from that: a golden is never
edited by hand, and a regeneration is reviewed like code.

When ``--update`` is legitimate
-------------------------------

Three situations, and only these:

1. **A new test.** A new rule-module test or tool test needs its golden created
   once. (For the rule tests this happens even without ``--update``: a missing
   golden is written from current output on first run. Treat that written file
   exactly like an ``--update`` product -- read it before committing it, because the
   test passed vacuously the run that created it.)
2. **An intended behavior change.** A rule-table fix, a tool bug fix with a pinned
   regression test, or new data in the reference tree changes what the correct
   answer *is*. Regenerate, and the golden diff **is** the statement of the
   behavior change; the pull request must call it out and justify every changed
   line.
3. **A deliberately changed reference tree.** New volumes added to the reference
   root, a corrected file in the published data. The diff should touch exactly the
   datasets that changed and nothing else.

Never to make a red test green. A golden diff you cannot explain line by line is a
bug report, not a fixture update -- either in the change under test or in the tree
being run against.

Which holdings root to use
--------------------------

Goldens are regenerated **only against real holdings** -- the tree resolved from
``PDS3_HOLDINGS_DIR``/``PDS4_HOLDINGS_DIR`` with ``PDSFILE_TEST_HOLDINGS=full``,
exactly as CI runs (:doc:`dev_guide_testing`). The committed goldens record the
answers of one *reference* root -- the real tree the routine runs use, which both the
per-PR self-hosted runs and the nightly complete-set runs must agree with, since one
set of goldens serves them all. Regenerating against a different tree than
the one the goldens were made from produces diffs that are about the trees, not
about the code -- the tool-test modules defend themselves against exactly that by
fingerprinting their sources (size and md5) and skipping when the root disagrees,
and the rule-test goldens rely on the diff review to catch it instead. If a
regeneration touches goldens for datasets your change did not touch, stop: you are
running against the wrong root, or the root has changed underneath you.

The two mechanisms differ in one behavior worth rechecking here: a *missing* rule
golden is created silently on any run, while a missing tool-test golden **fails**
unless the run was started with ``--update``. The tool-test failure message names
the exact command to run.

How to regenerate and present the diff
--------------------------------------

::

    export PDS3_HOLDINGS_DIR=/path/to/pdsdata/holdings
    export PDS4_HOLDINGS_DIR=/path/to/pdsdata/pds4-holdings
    export PDSFILE_TEST_HOLDINGS=full

    # Rule-module goldens (scope the run to what you changed):
    pytest tests/rules/pds3/test_newset_xxxx.py --update

    # Maintenance-tool goldens:
    pytest tests/holdings_maintenance --update

    git diff tests/golden/

Then, in order:

1. **Re-run, without the update flag,** and confirm the suite passes against the
   files just written; the ``--update`` run itself asserted nothing.
2. **Read the diff.** For every changed line, know which change of yours (or of the
   reference tree) produced it. ``git diff`` is readable here by design: the rule
   goldens are sorted logical-path text, and the tool goldens are normalized
   sidecar and log text, so the diff is the behavior change.
3. **Scope the commit.** Commit golden changes with the code change that caused
   them, never batched with unrelated regenerations, and never via a blanket
   ``git add`` over ``tests/golden/``.
4. **Present it.** The pull request description states why the goldens moved and
   quotes or summarizes the diff shape (which datasets, which products, how many
   lines). A reviewer should be able to accept the behavior change from the golden
   diff alone.
