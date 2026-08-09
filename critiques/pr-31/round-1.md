# PR-31 round 1 — `docs/conf.py`, the API pages, the Makefile and the README marker

Reviewer: a fresh, no-context subagent, given the tree path, the rule files to read
(`doc_python.mdc` all seven sections, `doc_dev_guide.mdc` sections 6 and 7) and the scope,
and nothing about how the change was arrived at. Tree
`/seti/all_repos/rms-pdsfile-pr31/work` at `8840ebb`, base `8f8d825`. Interpreter
`/seti/all_repos/rms-pdsfile/venv/bin/python` (3.12.3, Sphinx 9.1.0). The reviewer was
told to copy the tree before changing anything; `git status --porcelain` was empty when
the round started and empty when it ended.

**Counts.** 12 defects, 9 observations, and an explicit list of eleven things checked and
found sound.

---

## The defects, and what was done about each

**D1. The coverage check did not run on an incremental build — the one case it exists
for. FIXED.** `env.check_consistency()`, which emits `env-check-consistency`, is guarded
by `if updated_docnames:` in `sphinx/builders/__init__.py`. The check reads the source
tree, not the docs tree, so adding a `.py` file changes no Sphinx source, nothing is
re-read, and the handler never ran. Measured by the reviewer: a clean build printed the
coverage line and exited 0; `echo '"""A brand new public module."""' >
src/pdsfile/newthing.py` followed by the same build printed `no targets are out of date`,
**no coverage line at all**, and exited 0; touching `docs/index.rst` and rebuilding
produced the warning and exit 1.

The wired gate was safe because it runs `make clean` first. A developer's `make html`
loop was not. **The handler now runs from `build-finished`**, which fires on every build.
Re-measured after the fix: the same incremental build prints `no targets are out of
date.`, then `WARNING: pdsfile._probe_new_module2 is documented by no page in this tree`,
then `API reference: 78 of 79 modules ... documented`, and exits **2**.

**D2. The check establishes a domain entry, not published content. DOCUMENTED, not
fixed.** `.. automodule:: pdsfile.newthing` with none of the `:members:` options gives
`79 of 79 modules ... documented`, exit 0, and nothing rendered; so does a bare
`.. py:module::`. The check's docstring said it "compares the modules the build actually
documented", which is stronger than what it does. The docstring now says what it
establishes and what it does not, and `docs/api/index.rst` no longer claims the page set
covers members. Hardening it further would mean asserting a member count, which is a
golden-file gate and not this PR's.

**D3. The warning named a directory the code never looks at. FIXED.** The message read
`%s has no automodule entry under docs/api/`, but the check reads the Python domain,
which is directive- and location-agnostic: appending an `automodule` to `docs/index.rst`
satisfied it. The message now reads `%s is documented by no page in this tree`.

**D4. The intersphinx comment had the count right and the reason wrong. FIXED.** It said
the 34 names come from `Parameters:` entries. At least 13 do not: six are `py:exc` from
`Raises:` blocks, five `argparse.ArgumentParser` are all `Returns:` type lines, and
`datetime.datetime` and one `collections.abc.Callable` are `Returns:` lines. The comment
now names all three sections. The arithmetic -- one warning, plus 34 -- reproduced
exactly.

**D5. `_GENERATED_MODULES`'s comment mis-described the generated file. FIXED.** It said
"It holds one string"; the `_version.py` that `setuptools_scm` writes under this
`write_to` defines six names with an `__all__` block. The comment now says the version in
half a dozen spellings.

**D6/D7. Two page intros were false. FIXED.** "one rule module per PDS3 volume set" is
contradicted by the rule modules' own docstrings -- `HSTxx_xxxx.py` "serves five volume
sets", `COCIRS_xxxx.py`, `COISS_xxxx.py` and `VGISS_xxxx.py` each "serves four",
`NHxxxx_xxxx.py` "serves two". And the PDS4 page's enumeration omitted a third of its own
entries: three of the nine modules under `pds4file.rules` are `*_primary_filespec`
modules, which are not rule modules. Both intros now count what is there.

**D8. The README include leaves an empty section on the landing page. NOT fixed, and
recorded.** `README.md`'s last line is the H1 `# PDS Ring-Moon Systems Node, SETI
Institute`, so the rendered `index.html` ends with that heading and nothing under it. The
alternative -- moving the marker past it -- costs the page its only substantive line
(round 3 measured that). The README rewrite is a later PR and this is its to fix.

**D9. Every page footer read "(c) Copyright ." FIXED.** `conf.py` set `project` and no
`copyright`. The repository names no holder anywhere -- `LICENSE` is the stock Apache-2.0
text with no holder line and there is no `NOTICE` -- so `html_show_copyright = False`
turns the footer off rather than inventing one. Measured after: zero `Copyright` matches
in `index.html`.

**D10. `sphinxcontrib.mermaid` put a third-party CDN script on 70 of 77 built pages, with
no diagram anywhere in the tree. FIXED by removing it.** The extension's `install_js`
skips pages whose doctree shows no mermaid node, but pages built with `doctree is None` --
every `_modules/*` viewcode page, plus `search`, `genindex` and `py-modindex` -- fall
through and get `<script type="module">import mermaid from
"https://cdn.jsdelivr.net/npm/mermaid@11.12.1/..."`. The reviewer also found that
`mermaid_output_format = 'raw'` restated the extension's own default and changed nothing.
`doc_python.mdc` section 3 asks for a diagram extension "**when the guides use
diagrams**"; no guide exists yet. Measured after removal: **0 of 77** pages reference the
CDN, and the build is still clean under both gates.

**D11. `_module_names_under` treats any `.py` file as a module. RECORDED.** A file named
`template-example.py` produces `pdsfile.pds3file.rules.template-example`, a name no
`automodule` can document, and the only escape hatch is `_GENERATED_MODULES`. Latent: no
such file exists.

**D12. `docs/api/index.rst` inherited D1, D2 and D3. FIXED** -- the page now says the
gate fails when a module has no entry, and says plainly that this is a claim about
modules and not about their contents.

## The observations worth keeping

**O1 is the most valuable part of the round: eleven things checked and found sound.** The
page set is complete and has no duplicates and no phantoms (`on_disk - documented` and
`documented - on_disk` both empty, `uniq -d` empty); `napoleon_use_ivar` prevents exactly
the 27 collisions claimed, and flipping it off reproduced them (21 `ToolSpec`, 3
`RunResult`, 3 `VersionedFile`); `-n` alone exits 0 with 35 warnings; the `sys.path`
insertion beats the installed copy, tested with a marker in a scratch docstring; all nine
`:private-members:` names exist and are exactly `PdsFile`'s bases; the three documented
`Makefile` invocations work and `make clean` empties `_build` including
`_build/nitpicky`; the shared-`BUILDDIR` claim reproduced exactly; `tabulate` is the only
import needing a mock, and no `MagicMock` leaked into a page; `nitpick_ignore` is empty;
and every code-object mention in the `.rst` prose carries a role.

**O3 (the module docstring's "four things" undercounts, and "the extension set the pages
rely on" is not true of an unused extension) is fixed** -- the docstring no longer counts,
and the mermaid half of the problem went with the extension.

**O4 (the holdings-maintenance intro did not describe `crlf`, which repairs the published
PDS3 text files rather than derived files) is fixed** -- the intro now says "build, check
and repair a holdings tree and the files derived from it".

**O6 (`core` is not a subpackage; "the rule tables **it** starts from" attributes to
`Pds3File` what the rules package describes as what every subclass starts from) is
fixed** in both places.

**O2, O5, O7, O8, O9 are left as they are.** `docs/` copied away from `src/` warns rather
than silently documenting the installed copy, which is the honest outcome under `-W`;
`holdings_maintenance.rst` orders packages before their modules, which is the ordering
every page uses and which nothing claims to be alphabetical; the editable-install caveat
is real but only for a PEP 660 meta-path finder, which this layout does not produce; the
Napoleon settings that restate defaults are required to be explicit by `doc_python.mdc`
section 3; and the version coming from installed metadata while the code comes from the
checkout is what that same section asks for.

## What the reviewer could not verify

Whether ReadTheDocs enforces any of this (it sets no `fail_on_warning`); whether a PEP 660
editable install defeats the `sys.path` insertion; the docstring section of origin for 21
of the 34 intersphinx-dependent references, which report at `<unknown>:1`; whether every
PDS4 bundle set has a rule module; whether `_version.py` really materializes during a
ReadTheDocs build; and the symlinked-subpackage case, which `pathlib.rglob` skips.
