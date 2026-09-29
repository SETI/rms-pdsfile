# PR-31 round 3 — one job: prove the gate is vacuous

Reviewer: a fresh, no-context subagent, given a single instruction -- find a documentation
defect this gate does not catch, and demonstrate it by making the change and running the
gate. It copied the whole repository into its own scratch tree and ran **20 gate
invocations against 17 mutations**, measuring the published HTML in every case. Tree at
`8840ebb`, base `8f8d825`; `git status --porcelain` empty at both ends of the round.

Baseline on the unmutated copy: gate exit **0**, `Sphinx build passed: 0 warnings under
-W and under -n -W, over 78 automodule entries in 6 files under docs/api`.

**This round is the most valuable output of this PR**, because everything downstream leans
on this gate, and what follows is the list of what it does not hold up.

---

## What the gate does not catch

**1. Docstring and signature drift, in every shape, producing a page that contradicts
itself.** With `selected_path_from_path(path, cls, abspaths=True)` untouched, the reviewer
deleted the `cls` entry, invented a `verbose` entry, and inverted the stated default; and
added a `Returns:` to a function whose body is a bare `return`. **Gate exit 0, zero
warnings.** The published page renders the real signature immediately above a parameter
list that omits a required argument, documents one that does not exist, and states the
opposite default. A renamed parameter behaves the same way.

`critiques/pr-29/check_docstrings.py` catches four of the five shapes (P1, P2, R1) and
does not catch the wrong default. **And it is not a gate**: `grep -rI check_docstrings`
outside `critiques/` and `.git/` returns nothing -- not in `run-all-checks.sh`, not in any
workflow. It is a tool this project runs by hand. Deferred entry 337.

**2. Cross-references inside the docstrings of unpublished members are never checked.** A
`:meth:` naming a method that does not exist, placed in `_clean_join`'s docstring (a
private function), passes: the docstring is never rendered, so its references are never
resolved. The same two lines in a published function fail the gate. Measured scope: **52
objects carry a docstring in the source and are absent from the published reference** --
25 private and 27 dunder, zero public.

**Nine of those 27 were `__init__` docstrings, six carrying a `Parameters:` block**:
constructor documentation written, maintained, and never published, because
`autoclass_content` defaults to `'class'`. **Fixed** -- `autoclass_content = 'both'`, and
all nine now appear on the pages, verified by matching each `__init__` docstring's first
line against the built HTML (9 published, 0 missing). The remaining 43 are private
members and dunders whose docstrings stay unpublished and therefore unchecked. Deferred
entry 333.

**3. A dev-only or undeclared import in a module no dependency gate imports.** `import
pytest` added to `pdsarchives.py`: gate exit 0, ruff clean, the new function published.
The same tree with `pytest` unavailable -- the documentation builder's environment --
loses **two** modules (the one with the import and one that imports it), publishes 76 of
78, and `.readthedocs.yaml` sets no `fail_on_warning`, so that build succeeds and
publishes. `scripts/check_runtime_imports.py::_module_set()` returns 43 names, and
neither `pdsfile.holdings_maintenance.*` nor `pdsfile.tools.*` is among them: **35 of the
78 documented modules are imported by no dependency gate.** The reviewer ran the
clean-install gate on the mutated tree with `pytest` blocked and it passed, exit 0.
Deferred entry 334; entry 330 is the live instance of the same mechanism.

**4. `__all__` deletes members from a page silently.** `__all__ = ['construct_category_list']`
in `_path_utils.py` takes that module's published objects from 6 to 1. Gate exit 0, "78
automodule entries".

**5. Dropping `:members:` from one `automodule` entry.** `pdscache`'s published objects go
from **46 to 0** -- three classes and 43 methods -- and the gate's success line is
byte-identical to the baseline's.

**6. A decorator without `functools.wraps`** replaces the published signature with
`(*args, **kwargs)` and deletes the whole docstring from the page. Gate exit 0.

**7. `.. note:` with one colon** turns the directive into an RST comment and deletes the
entire indented block from the page, with no diagnostic anywhere. Gate exit 0,
`check_docstrings.py` clean. The easiest typo in the whole surface.

**8. Two pages documenting the same module, with `:no-index:`.** Without it the duplicate
fails the gate with 47 `duplicate object description` warnings; with it the gate passes,
`tools.html` grows from 14,641 to 95,871 bytes, and the search index points at the other
copy.

**9. A module dropped from a page *and* added to `_GENERATED_MODULES`.** Two lines, gate
exit 0, "77 automodule entries" -- nothing compares that number to anything. Nothing
asserts that a name in that set is actually generated. The asymmetry is instructive:
dropping `pdsviewable` the same way *does* fail, but only because five other docstrings
cross-reference `PdsViewSet`.

**10. Moving the README marker** past `Supported versions: Python >= 3.10` removes the
front page's only substantive line. `:start-after:` swallowing content is not a warning.
This is why the marker was left where it is despite the empty trailing section round 1
found.

**11. An empty page in the `toctree`** is published, appears in the sidebar, and raises the
"files under docs/api" figure the old pass line quoted.

**12. Prose that is simply false**, including the gate's own. Two injected examples passed
(a page claiming every constructor is published; a docstring claiming binary units over
code that divides by 1000). **And one that was not injected: the comment defending two
builds claimed "the two flags catch different defects and neither implies the other",
which is false.** `-n` only adds warnings; in every defect the gate caught, the nitpicky
build caught it too. The reviewer found no defect the first build catches that the second
does not. **Fixed** -- the comment now says what the first build is actually for: the
`docs/_build/html` a reader opens, and a failure attributable to something other than a
cross-reference.

## What the gate did catch

A broken `:meth:`/`:mod:` in a **published** docstring (nitpicky build only -- the
warnings build passed it); a plain duplicate `automodule` (both builds, 47 warnings); a
new module with no entry; a module removed from its page and exempted in `conf.py`, when
other docstrings reference it (five `py:class reference target not found`); and an
unreachable intersphinx inventory (1 warning under `-W`, 35 under `-n -W`, exactly the
count `conf.py` claims).

**No incremental-build hole inside the gate.** The reviewer planted a known-caught defect
in a tree with a warm `_build` and ran the gate: exit 1. `make clean` plus the separate
`BUILDDIR` hold. (Round 1 found the hole one level out, in a developer's bare `make
html`; that is D1 there, and it is fixed.)

## What the reviewer could not verify

That ReadTheDocs actually publishes the finding-3 build (inferred from the config plus a
local reproduction, not observed); that `-n -W` is a strict superset of `-W` in every case
rather than in the four measured; whether any test asserts anything about `docs/`;
whether the local venv's package set matches CI's on 3.10; the full set of undeclared
third-party imports at HEAD; and whether any of the 52 unpublished docstrings currently
contains a broken reference.
