# PR-29b review rounds

Five rounds, each run by a fresh reviewer subagent with no context from this session or
from any other round. Two slices, read twice each; the fifth round exists because the
slice grew after round 1 had run.

| round | slice | surface | read |
|---|---|---|---|
| 1 | `_properties.py` | the ten members of the line-count sample | first |
| 2 | `pdsfile.py` + `pdsviewable.py` | 63 functions, 3 classes, 2 module docstrings | first of this PR, second of the prose |
| 3 | `_properties.py` | the other 58 members and the module docstring | first |
| 4 | `_properties.py` | all 68 members re-read | second |
| 5 | `pdsfile.py` + `pdsviewable.py` | the same 63 re-read | second |

Rounds 1 and 2 were run against a surface of ten and sixty-three. The owner's waiver on
2026-08-08 enlarged this PR's scope by the 58 members round 1 had not covered, so round 3
reads those and round 4 is the second read of the whole file. Splitting it that way keeps
the property the rounds exist for -- every docstring read twice, by two reviewers who share
no context -- rather than reading 58 once because a round budget said four.

Rounds 3, 4 and 5 carry, by name, the sentences the earlier round rewrote. That is the
lesson `critiques/pr-29a-validation.md` section 10a records: eleven of PR-29a's round-4
findings were correcting sentences round 2 had itself written, and a corrected sentence has
been written once and verified zero times.
