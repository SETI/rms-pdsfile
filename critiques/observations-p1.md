# Observations — blocking (P1)

Open observations that block the merge to `main`: the ones where leaving them undone makes a claim this branch makes about itself untrue.

The module-length breaches that used to sit here are waived, with one issue per file recording the split (#141, #142, #143, #144), and the API-freeze gate's environment dependence is ruled unimportant because the gate exists only for the duration of this refactor and is removed with the rest of the scaffolding. What is left is the one entry that says the test suite passed green over a real break.

## Test coverage

### 2100. A stubbed collaborator hid a real break, for the second time in this subsystem

**A stubbed collaborator hid a real break, for the second time in this
subsystem.** The migration left the four thin tool modules with a task *table*
and no task *names*, and `re_validate.validate_one_volume()` reaches
`pdslinkshelf.validate()` by attribute. The full `--mode ns` data suite ran
green in that state — 1,047 passed, 34 skipped — and so did
`run-all-checks -c -s`. Nothing could have caught it: every test that drives
`validate_one_volume` replaces all five sibling tools with `SimpleNamespace`
stubs, which is what lets those tests run without holdings and is also what
makes them silent about whether the real functions exist.

Fixed here — each module binds its five tasks under the names it carries them
as a library, and `test_re_validate.py` gains
`test_the_sibling_tools_really_accept_what_this_module_calls_them_with`, which
binds each of the seven calls against the real modules. The general shape is
what is left open: `re_validate` is not the only module in this tree that
stubs a collaborator wholesale, and a stub that outlives its subject is
invisible to every gate. observation 6607 is the same failure mode one level down —
a subprocess importing a different tree — and the fix is the same in kind: one
test that exercises the real thing, however narrowly.
**Owner: open.**
