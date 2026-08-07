# PR-29 adversarial review, round 1 — `pdscache.py`

Reviewer: a fresh subagent with no context from the executor's session, given the head
and base copies of `src/pdsfile/pdscache.py` and told to hunt for docstrings that are
wrong about the code. Slice: that one file, 3 classes and 60 functions.

Fifteen findings. Every one was re-verified by the executor before acting on it, and
every re-verification agreed with the reviewer except where noted below.

## What was fixed in the docstrings

| # | finding | fix |
|---:|---|---|
| 1 | `MemcachedCache.delete_multi` — the `AttributeError` was attributed to `self._del_local`, but the call dies one statement earlier on `self.mc.del_multi`, which pylibmc does not have. So *every* call fails, an empty one included, and the server-side deletion the docstring said had "already happened" never happens. | rewritten; entry 157 rewritten |
| 2 | `DictionaryCache` — deleting an entry, or reading one that has expired, leaves its key in the trim bookkeeping, and the next trim raises `KeyError`. Nothing in the file mentioned it, and `get()`'s "as though it had never been there" pointed the other way. | class docstring, `_trim`, `get`, `delete`, `__delitem__`, `delete_multi`, `clear`; entry 170 |
| 3 | `_wait_for_ok` — "raises AttributeError at that point rather than breaking the block" is inverted. The block is written to the server first and logged second, so it is broken, sometimes claimed, and *then* the call raises. | rewritten |
| 4 | `DictionaryCache.set_multi` — the `Returns:` rationale said "the shared cache returns the keys it failed to store". It does not; `MemcachedCache.set_multi` returns `[]` unconditionally and its own docstring says so. The two docstrings contradicted each other. | rewritten |
| 5 | module docstring — "share one interface, so a caller can be handed either" overclaims. The two `set_multi` signatures differ in arity *and* default. | qualified, with the two divergences named |
| 6 | `MemcachedCache.set_local` — "in seconds, rounded up to a whole second" on the parameter. Rounding is applied only to the lifetime function's result; a lifetime passed in goes through as it stands, fraction and all. | rewritten |
| 7 | `DictionaryCache` class docstring — "never counts against the size limit" is false for an expiring entry re-stored as permanent: the key stays in the counted set while the entry becomes exempt from trimming. | rewritten; entry 171 |
| 8 | `MemcachedCache.get_multi` — restores a lost permanent value and then does not return it, so it disagrees with `get()` for the same key. `Returns:` said a key is absent only when no source has it. | rewritten; entry 172 |
| 9 | `MemcachedCache.clear` — "the cache is blocked for the duration whether or not `block` was asked for" is false. With `block=False` the wipe runs with no block held. | rewritten; entry 174 |
| 10 | `MemcachedCache.clear` — undocumented `TypeError` when the server has lost the clear counter, which the two sibling methods facing the same key already document. | added; entry 174 |
| 11 | `MemcachedCache` class docstring — "a caller gets back an equal object rather than the one it stored" is false for all three local paths, and for an oversized value permanently so. | rewritten |
| 12 | `MemcachedCache.delete` — `Returns:` said "the server or this process". The permanent copy is removed and not counted, so a key held only there is removed and reported absent. | rewritten; entry 173 |
| 13 | `MemcachedCache.flush` — stated the order as wait-then-copy; the permanent copy happens first. | rewritten |
| 14 | `MAX_BLOCK_SECONDS` — described as a block's age in two places. It is one waiter's patience, measured from when that waiter arrived, and it restarts whenever the blocking process changes. | both rewritten; entry 175 |
| 15 | five wording imprecisions: nested pauses log only the outermost; `flush`'s no-logger path loses only the failing batch onward; `replicate_clear_if_necessary` is called by three methods, not by "the read and write paths"; `_trim` also removes expired entries; `preload_eligible` was undocumented. | all rewritten; entry 176 |

## Where the executor's re-verification differed from the reviewer

**Finding 7.** The reviewer's reproduction stored 40 entries and re-stored all 40, and
reported the key set at 40. Re-run, it is 19: trimming had already fired during the first
loop. The claim itself holds and is cleaner at one key — `set('k', 1, lifetime=3600)`
then `set('k', 1, lifetime=0)` leaves `keys == {'k'}` with the entry permanent — so that
is what entry 171 records.

**Finding 1.** The reviewer inspected the pylibmc 1.6.3 source to establish that
`del_multi` does not exist. The executor repeated it from a fresh download rather than
taking it: `src/_pylibmcmodule.h` registers `delete_multi` in the method table, there is
no attribute fallback in `src/pylibmc/client.py`, and `del_multi` occurs in the package
only as a substring of `delete_multi`.

## What the reviewer checked and found sound

- No `Raises:` entry names something the code cannot produce. Every one was traced to a
  reachable statement.
- The bugs this PR deliberately documents rather than fixes are documented accurately —
  the constant-zero-lifetime trap, `set_multi` collapsing to one lifetime, `unblock`'s
  logger-conditioned refusals, `flush`'s `dict_keys.sort()`, `replicate_clear` writing
  `None` back, `len_mc`'s first-server undercount, and the conflation of a stored `None`
  with a miss. Findings 1, 3 and 6 are the three that had the details wrong.
- `DictionaryCache`'s nine no-op methods and its ignored parameters are all described
  correctly.
- `get_local`, `get_now` and `set_local` name the right sources on both classes.

## Gates after the fixes

The AST hash is unchanged at `eccdfbc6d19a526d`, the docstring checker reports 0
findings, `ruff check .` passes, and the Sphinx build is still clean under `-W -n`.
