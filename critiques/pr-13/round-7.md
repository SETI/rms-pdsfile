# PR-13 — adversarial review round 7 (scoped: the stdout/stderr split)

- Focus diff: `git diff c7d91b6..790a6d4` — the commit responding to the second CI
  failure.
- Reviewer: a **seventh** fresh no-context subagent, given the failure's history
  and asked to attack the stream-capture change specifically, including an
  explicit invitation to try to break the suite with hostile stderr.

## Verdict

**`goal not met`** — 2 Major, both real, both latent rather than currently
failing. CI was green on all four interpreters at the time this round ran; the
findings are about what *would* break under different stderr noise. Both fixed.

## Major findings and resolutions

### 7.1 — The widest structure parser was left on the merged stream

`ToolRun.error_lines` filters the capture by log-level marker, which is parsing
structure out of tool output — exactly what the commit's own stated rule says must
read `stdout`. It was the one parser not moved, and it is the widest consumer in
the suite: roughly forty assertions across twelve modules, fourteen of them the
exact-equality `assert run.error_lines == []`. Any stderr line containing
`| ERROR |` or `| FATAL |` would be counted as a tool error.

The reviewer did not just assert this — it injected such a line and measured **28
failures**, then applied the one-line fix through an out-of-tree plugin and got
111 passed, proving nothing in the suite depends on error lines arriving via
stderr. It corroborated that independently against the tools: `pdslogger`'s
console handler writes to stdout, its error handler is a *file* handler, and
`grep -rn stderr src/pdsfile/` is empty.

**Fixed**: `error_lines` reads `self.stdout`, with the reason in its docstring.

### 7.2 — A negative assertion on merged output that the subprocess's own cwd can trip

`assert str(tree.disk) not in run.output` means "the tool did not print an
absolute path", but evaluated against stderr it also forbids any *library* from
mentioning the working directory — and the subprocess runs with `cwd=tree.disk`.
The reviewer demonstrated the failure with a warning reading
`config not found under <cwd>`.

This also disproved the commit's blanket claim that "extra stderr noise cannot
make substring assertions wrong": it holds for positive assertions, and for
negative ones only when the string is tool-specific. The reviewer checked the
other twelve negative assertions individually and found them safe on that basis.

**Fixed**: reads `run.stdout`, with the trap named in a comment. The related
`logical.output == absolute.output` equality (raised as Minor) now compares
`stdout` too.

### The mirror-image trap, correctly avoided

Worth recording because it is the failure mode of over-applying this fix: the
three `assert 'not allowed with argument' not in run.output` assertions **must**
stay on the merged stream, since argparse writes to stderr — moving them to
`stdout` would silently make them vacuous. The reviewer confirmed they had been
left alone; they are now commented so a future reader does not "fix" them.

## Job A — the reviewer's other checks

| Point | Result |
|---|---|
| Is the capture correct? | **ok.** `capture_output=True` is exactly the two `PIPE`s; `subprocess.run` drains both through `communicate()`, so no deadlock; decoding is still explicit bytes with `errors='replace'` and no `text=True`, so no newline translation was introduced. |
| Are the deliberate stderr pins intact? | **ok.** The three pinned tracebacks read `.output`, which still contains stderr, and pass in every run. No test reads `.stderr` directly. |
| Did concatenation break anything that relied on interleaving? | **ok.** The only position-dependent parse was the "Steps required" slice, which now reads `stdout` and is immune. Concatenation is in fact more deterministic than the old real-time interleave. |

## Verification after the fixes

The harness was made maximally hostile — a stderr line in every subprocess
carrying **both** the working directory and a `| ERROR |` / `| FATAL |` marker:

| | result |
|---|---|
| suite with hostile stderr | **111 passed** |
| same, with `error_lines` reverted to the merged stream | **28 failed** |
| suite with no stderr noise | **111 passed** |

The middle row is the point: it shows the single line is load-bearing, not
defensive decoration.

## Note

Three CI-driven defects have now been found in this suite, all the same shape —
the tests pinning something about the *environment* rather than about the tool:
directory-enumeration order, then stderr contamination of a golden, then stderr
contamination of the error-line parser. The pattern is recorded in
`validation.md`; the standing rule that came out of it is in `ToolRun`'s
docstring.
