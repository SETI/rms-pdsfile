# Observations — blocking (P1)

Open observations that block the merge to `main`: the ones where leaving them undone makes a claim this branch makes about itself untrue.

**None are open.** The module-length breaches that used to sit here are waived, with one issue per file recording the split (#141, #142, #143, #144), and the API-freeze gate's environment dependence is ruled unimportant because the gate exists only for the duration of this refactor and is removed with the rest of the scaffolding.

The last entry, 2100, said the suite had run green over a real break because every test that drives `re_validate.validate_one_volume` replaces its five sibling tools with stubs. Both halves are now closed. The instance was fixed when each tool module bound its five tasks under the names it carries them as a library and `test_re_validate.py` gained a test that binds all seven calls against the real modules. The general shape — a stub that outlives its subject is invisible to every gate — is answered by `tests/core/test_stubbed_surfaces.py`, which binds every PdsFile class member the suite's stubs stand in for against the real class. `monkeypatch.setattr` already refuses to replace an attribute that is not there; what had no guard was the shape of the replacement, and that is what the new module checks.
