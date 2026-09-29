"""The Sphinx configuration PR-29 built its five-module API pages with.

This is a record of a build that succeeded, not a live configuration: `docs/` does not
exist yet, and PR-31 owns creating it. The tree this configured lived in the scratchpad,
which is why the source root arrives through an environment variable rather than as a
path relative to this file.

Under both `sphinx-build -W` and `sphinx-build -n`, with `nitpick_ignore` empty and
nothing mocked, this produced zero warnings over autodoc pages for `pdsfile`,
`pdsfile.pdsfile`, `pdsfile.pdscache`, `pdsfile.pdsviewable` and
`pdsfile.preload_and_cache`.

`doc_python.mdc` section 3 asks for three things this does not have, because a build with
five API pages and no narrative pages has nothing to use them for: `myst_parser`, a
diagram extension, and a version read from installed package metadata.

The intersphinx inventory is what makes the builtin type names in `Parameters:` entries
resolve under `-n`, so the build needs network access.
"""

import os
import sys

sys.path.insert(0, os.environ['PDSFILE_SRC'])

project = 'pdsfile'
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.napoleon', 'sphinx.ext.viewcode',
              'sphinx.ext.intersphinx']
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_use_param = True
napoleon_use_rtype = True
intersphinx_mapping = {'python': ('https://docs.python.org/3', None)}
nitpick_ignore = []
autodoc_member_order = 'bysource'
