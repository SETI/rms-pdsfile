# PR-31 round 4 — a second read of what rounds 1 to 3 changed

Reviewer: a fresh, no-context subagent, given the correction commit (`git diff
8840ebb..HEAD`), the seven corrections in the author's words, and one instruction: assume
that between half and three quarters of what it finds will be the first read's own
corrections gone wrong. Tree at `f7df76d`, base `8f8d825`. It copied the tree for every
experiment; `/seti/all_repos/rms-pdsfile-pr31/work` was never written to.

**Counts.** 10 defects, 9 observations, and seven corrections checked and found sound.
**Nine of the ten defects are in the corrections themselves**, which is the rate the
docstring PRs recorded and the reason this round exists.

---

## The defects, and what was done about each

**D1. The correction to the intersphinx comment made its own number wrong. FIXED.** The
same commit added `autoclass_content = 'both'`, which pulls six `Parameters:` blocks into
the pages and with them two more standard-library names. Measured with the inventory
pointed at an unreachable host: **36** unresolved references at head, 34 with the
`autoclass_content` line deleted and nothing else changed. The comment said 34. It now
says 36, and `-n -W` against a dead inventory is **37** problems, not 35. Deferred entry
329 carries the corrected enumeration.

**D2. A project path containing a space turned a clean build into a gate failure. FIXED.**
`_sphinx_coverage_line` matched the emitted path with `[^ ]+`. The reviewer copied the
tree unchanged to a directory whose name holds a space: both builds exited 0 and both
printed the coverage line, and the gate reported `✗ Sphinx warnings-as-errors build
exited 0 but reported no API-reference coverage`, exit 1. A false failure, introduced by
the correction that made the gate read its builds. The pattern is now `.+`, and the same
tree at the same spaced path passes.

**D3. `autoclass_content = 'both'` republished two constructor docstrings 33 times.
FIXED, by a different mechanism.** `autodoc_inherit_docstrings` defaults to true, so every
rules class inherits `Pds3File.__init__`'s or `Pds4File.__init__`'s docstring and `'both'`
appended it to that subclass's entry: **26** copies on the PDS3 page and **7** on the PDS4
page, +30 KB. Setting `autodoc_inherit_docstrings = False` does not help -- measured, still
26 copies. The fix is `:special-members: __init__` on the `automodule` entries instead:
without `:inherited-members:`, autodoc documents `__init__` only for a class that defines
one. Measured after: all **nine** constructor docstrings published, **0 missing**, one copy
each, twelve `__init__` entries in all (the nine plus the generated constructors of the
three dataclasses), and the PDS3 page back to 448 KB. The option is on every one of the 78
entries rather than on seven of them, so the page set has one directive vocabulary.

**D4. `docs/api/index.rst` contradicted `conf.py` in the same tree. FIXED.** The page said
the gate's failure means "no module is missing from this page set"; `conf.py`'s docstring,
rewritten in the same commit, says the check is satisfied by a directive "on a page other
than the API reference". The reviewer demonstrated it: a module documented only from
`docs/index.rst` gives `79 of 79 modules documented`, exit 0, and nothing on any API page.
The sentence now says the gate fails when a module is documented by **no page at all**.

**D5. A comment named the wrong shell option. FIXED.** `_sphinx_problem_count` contains no
pipeline, so what would abort on `grep`'s exit 1 is `errexit`, not `pipefail`. The reviewer
proved it with three one-line scripts.

**D6. "some of which the documentation rules require rather than the pages using" was not
supported by the tree. FIXED by deletion.** With mermaid gone, every remaining extension
changes the built pages: removing `viewcode` takes the build from 77 pages to 10, removing
`napoleon` produces 204 problem lines, removing `myst_parser` fails the build outright, and
an unreachable `intersphinx` produces 36.

**D7. The holdings-maintenance intro over-corrected. FIXED.** Round 1 asked for "repair" to
be added, because `crlf.py` repairs; the correction also widened the object from the
derived files to the holdings tree, and nothing in the subpackage builds a holdings tree --
its own docstring says "The tools that build and check **the derived files** a holdings
tree carries". The intro now names the derived files and gives `crlf`'s line terminators
their own clause.

**D8. The skill file's rewritten snippet was not runnable as a block. FIXED.** Three
consecutive `cd docs && ...` lines: pasted from the project root, the second and third
`cd` fail and `&&` swallows the build, so the reader gets `make clean` and one `cd` error.
It is now one `cd docs` followed by three commands.

**D9. "A build that already failed is not asked about its coverage" was false for the usual
failure. FIXED.** Sphinx 9.1.0 counts warnings under `-W` rather than raising, so
`build-finished` fires with `exception=None` on a `-W` failure; the reviewer showed the
coverage line printing under `build finished with problems, 1 warning`. The docstring now
says the guard excludes a build that died, not a build that failed.

**D10. `sphinxcontrib-mermaid` is still in the `docs` extra.** Not fixed: an installed
extension that no `extensions` list names does nothing, and the guides of PR-32 and PR-33
will want it. Deferred entry 344.

## The observations, and what was done

**O1** (two of the three published numbers cannot vary, because `-W` fails any build that
would print a non-zero count) is deferred entry 345 rather than a change: it is a property
of `-W`, and the number that does carry information -- the coverage line -- is the one the
gate requires and now compares between the two builds.

**O2** ("one page per top-level package and subpackage" counts 5 pages against 9 packages)
and **O9** (a list of modules that "includes" classes) are prose fixes, both made.

**O3** (`_GENERATED_MODULES`'s comment said "the version in half a dozen spellings"; it is
four spellings of the version and two of the commit id) is fixed.

**O4** (the correction stopped sequential mode streaming, which the workflow comment says
it does) is fixed: each build now goes through `tee`, so it streams and is captured at the
same time, and `set -o pipefail` carries `make`'s status through.

**O5** (the skill file still stated the acceptance rule as exit status alone) is fixed in
both places.

**O6** (a failing build's coverage line was dropped from the message) and **O8** (the two
builds' coverage lines were never compared) are both fixed: the failure message carries the
coverage line when the build printed one, and a disagreement between the two builds is now
itself a failure, on the grounds that the two builds document one tree.

**O7** (the mermaid comment narrated a change in the past tense, against the
current-state-only rule) is fixed to the present tense. The reviewer independently
reproduced the measurement inside it: 77 pages, exactly 70 carrying the CDN script, and the
seven without it precisely the pages that have doctrees.

## The seven corrections checked and found sound

The `build-finished` move, in its reason and in every case the reviewer could construct --
it still fires and still fails under `-E`, under the `text` builder, and runs without
failing under `linkcheck`, and `app.env` is populated in all of them. The shared-`BUILDDIR`
rationale, and non-obviously so: a second build into the same `BUILDDIR` logs `The
configuration has changed (3 options: ... 'nitpicky')` and **still** re-reads nothing,
reporting 0 of the 36 reference warnings a fresh build reports. The mermaid removal against
`doc_python.mdc` section 3. `html_show_copyright`, with `LICENSE`'s only copyright line
being the Apache-2.0 appendix placeholder. Every countable claim in the rewritten page
intros, recounted independently: 25 PDS3 dataset modules, 6 PDS4 dataset modules and
exactly 3 `*_primary_filespec` modules, 9 mixin classes which are exactly `PdsFile`'s
bases, 9 classes with an `__init__` docstring of which 6 carry `Parameters:`, and 78 unique
`automodule` entries against 78 `.py` files. The skill file's `-c` description against the
script's own flag list. And the gate mechanics in both parallel and sequential mode,
including the status-file entries and the log ordering in CI.

## What the reviewer could not verify

Whether the space-in-path failure matters in practice (GitHub Actions and ReadTheDocs both
use space-free paths, so it was latent there and bit only a developer); the exact content
of `src/pdsfile/_version.py` for this tree, since it is gitignored -- though a local full
run has since materialized it, which is deferred entry 346; behavior on Sphinx versions
other than 9.1.0, on which two findings depend; and whether `autodoc_inherit_docstrings =
False` or `:special-members:` was the author's preferred remedy for D3, which the reviewer
deliberately left open by measuring the defect rather than the fix.
