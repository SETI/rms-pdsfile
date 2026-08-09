##########################################################################################
# docs/conf.py
##########################################################################################

"""Sphinx configuration for the rms-pdsfile documentation tree.

One configuration file serves the whole tree. Four of the things it does are worth
knowing before reading the settings: it puts the source root on `sys.path` so `autodoc`
imports the package from the checkout being documented; it reads the version from the
installed distribution metadata, which can therefore describe a different tree from the
one being documented; it selects the extension set, some of which the documentation rules
require rather than the pages using; and it registers a check that warns when a module
under the source root is documented by no page.

The documentation build is a gate. `scripts/run-all-checks.sh` runs two builds from this
configuration, one with `-W` and one with `-n -W`, and reads both exit statuses. `-n`
alone reports unresolved cross-references without failing, so it is never run alone, and
`-W` is what turns this file's own warning into a failure.
"""

import importlib.metadata
import pathlib
import sys

from sphinx.util import logging

logger = logging.getLogger(__name__)

# The importable source root. autodoc has to import every module it documents, and
# inserting the root at the front of sys.path documents this checkout whether or not a
# copy of the package is also installed in the environment running the build.
_SRC = pathlib.Path(__file__).resolve().parent.parent / 'src'
sys.path.insert(0, str(_SRC))

# The name to install, which is not the name to import: `pip install rms-pdsfile` gives
# `import pdsfile`.
_DISTRIBUTION = 'rms-pdsfile'

# Written by setuptools_scm at build time, absent from a source checkout, and gitignored
# (`write_to` in pyproject.toml puts it here). It holds the version in half a dozen
# spellings and nothing else, and it is not part of the documented surface, so the
# coverage check below does not ask for a page entry for it.
_GENERATED_MODULES = frozenset({'pdsfile._version'})

# -- Project information -----------------------------------------------------------------

# The distribution name, because that is what the published site is a site for; the
# importable package is `pdsfile` and is named as such throughout the API reference.
project = 'rms-pdsfile'

try:
    release = importlib.metadata.version(_DISTRIBUTION)
except importlib.metadata.PackageNotFoundError:
    # The same string the package binds to `pdsfile.__version__` when it cannot find its
    # own build metadata, so a build from an uninstalled checkout says so in one voice.
    release = 'Version unspecified'
version = release

# -- General configuration ---------------------------------------------------------------

# A diagram extension belongs here once a page draws a diagram. None does: enabling
# sphinxcontrib.mermaid with no diagram in the tree put a script tag pointing at a
# third-party CDN into 70 of the 77 built pages, because the extension skips only the
# pages whose doctree it can see has no diagram in it, and every viewcode page and every
# generated index falls outside that test.
extensions = [
    'sphinx.ext.autodoc',        # the API reference is generated from the docstrings
    'sphinx.ext.napoleon',       # the docstrings are Google style
    'sphinx.ext.viewcode',       # each documented object links to its highlighted source
    'sphinx.ext.intersphinx',    # names from the standard library resolve to python.org
    'myst_parser',               # Markdown, which is what README.md is
]

source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

exclude_patterns = ['_build']

# -- Extension configuration -------------------------------------------------------------

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_use_param = True
napoleon_use_rtype = True
# An `Attributes:` section on a dataclass otherwise collides with the field autodoc
# already emits for the same annotated class-level name, and a duplicate object
# description is a warning. Rendering the section as a field list creates no second
# target, which leaves the sections where they are and the build clean.
napoleon_use_ivar = True

autodoc_member_order = 'bysource'
# Nine classes document their constructor in `__init__`'s docstring, six of them with a
# `Parameters:` block. autodoc's default renders the class docstring alone, so all of
# that is written, maintained, and never published. 'both' concatenates the two.
autoclass_content = 'both'
# tabulate is imported by pdsfile.tools.show_opus_products and is a development
# dependency, not a runtime one, so it is absent wherever the documentation is built
# from the `docs` extra alone. Mocking it documents that module from its docstrings
# instead of dropping it from the reference.
autodoc_mock_imports = ['tabulate']

# Reaching this inventory is what makes the standard-library names in the `Parameters:`,
# `Returns:` and `Raises:` entries resolve under `-n`, so the build needs network access
# to it, and a build that cannot reach it fails: not reaching it is one warning, and the
# names it would have resolved are 34 more. The timeout bounds that failure -- without it
# a host that accepts the connection and never answers stalls the build rather than
# failing it.
intersphinx_mapping = {'python': ('https://docs.python.org/3', None)}
intersphinx_timeout = 30

# Empty, and every entry added here has to name a symbol with no resolvable target and
# carry the reason it has none. Silencing an unresolved reference to a symbol this
# package owns hides a documentation defect rather than fixing it.
nitpick_ignore = []

# -- HTML output -------------------------------------------------------------------------

# The theme the `docs` extra installs, and the one ReadTheDocs serves.
html_theme = 'sphinx_rtd_theme'

# The repository names no copyright holder: LICENSE is the Apache-2.0 text with no holder
# line and there is no NOTICE file. With `copyright` unset the theme renders a footer
# reading "(c) Copyright ." on every page, so the footer is turned off rather than filled
# in with a holder and a year this tree does not state anywhere.
html_show_copyright = False


def _module_names_under(root):
    """Return the importable name of every module in a source root, as a set.

    A directory is named by its package name and a file by its module name, so
    `src/pdsfile/tools/__init__.py` is `pdsfile.tools` and
    `src/pdsfile/tools/show_opus_products.py` is `pdsfile.tools.show_opus_products`.
    Nothing is imported: the answer describes the files on disk, which is what the API
    reference is meant to cover.

    Parameters:
        root (pathlib.Path): the directory holding the top-level package.

    Returns:
        set[str]: one dotted name per `.py` file under `root`.
    """
    names = set()
    for path in root.rglob('*.py'):
        parts = list(path.relative_to(root).parts)
        if parts[-1] == '__init__.py':
            names.add('.'.join(parts[:-1]))
        else:
            names.add('.'.join(parts)[:-len('.py')])
    return names


def _check_api_reference_coverage(app, exception):
    """Warn for every module on disk that no page in this tree documents.

    Sphinx has no opinion about a module nobody wrote an `automodule` directive for: a
    page set that has fallen behind the package builds clean and publishes an API
    reference with holes in it. This compares the source tree against the modules the
    Python domain recorded, and warns about the difference. Under `-W` that warning fails
    the build, which is what makes adding a module without adding its entry a build
    failure rather than a silent omission.

    What it establishes is that each module has a target in the Python domain, which is
    weaker than establishing that its members are published: a directive that names the
    module and documents none of its contents satisfies this, and so does one on a page
    other than the API reference.

    It runs from `build-finished` rather than from `env-check-consistency` because the
    consistency event fires only when at least one document was re-read. Adding a `.py`
    file changes no Sphinx source, so on an incremental build nothing is out of date and
    a check on that event would not run at all -- which is exactly the case it exists for.

    Parameters:
        app: the Sphinx application, whose build environment holds the documented
            modules.
        exception: the exception that ended the build, or None if it succeeded. A build
            that already failed is not asked about its coverage.
    """
    if exception is not None:
        return

    if not _SRC.is_dir():
        logger.warning('source root %s does not exist, so the API reference was not '
                       'checked for missing modules', _SRC)
        return

    on_disk = _module_names_under(_SRC) - _GENERATED_MODULES
    documented = set(app.env.domains['py'].modules)
    missing = sorted(on_disk - documented)
    for name in missing:
        logger.warning('%s is documented by no page in this tree, so it is absent from '
                       'the API reference', name)
    logger.info('API reference: %d of %d modules under %s documented',
                len(on_disk) - len(missing), len(on_disk), _SRC)


def setup(app):
    """Register this configuration's own coverage check with the build.

    Parameters:
        app: the Sphinx application to register the handler on.
    """
    app.connect('build-finished', _check_api_reference_coverage)
