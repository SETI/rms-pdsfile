"""Build a throwaway Sphinx tree over the documented modules and run both gates.

`docs/` does not exist in this repository yet, so there is nowhere to run
`doc_python.mdc` section 6's two builds. This writes a minimal tree somewhere else,
points it at a source root, and runs `sphinx-build -n` and `sphinx-build -W` over
autodoc pages for the modules named below.

The configuration is `critiques/pr-29/sphinx-conf.py` unchanged. What is extended is the
page list: the nine private modules join the four public ones. `pdsfile.pdsfile` has to
be among them or the `PdsFile` written in a `Parameters:` type slot resolves to nothing
and fails `-n`, which is a property of a partial page set rather than of the prose.

`_properties.py` is deliberately absent. Its docstrings have not been revised, and
including it adds warnings that belong to the module rather than to this build.

Usage:
    python build_docs_probe.py SRC_DIR BUILD_DIR

`SRC_DIR` is the importable source root, the `src` of the tree being measured.
`BUILD_DIR` is created or emptied. Exit status is 1 if either build reports anything.
"""

import pathlib
import re
import shutil
import subprocess
import sys

MODULES = ('pdsfile', 'pdscache', 'pdsviewable', 'preload_and_cache',
           '_associations', '_derived_paths', '_index_rows', '_local_fs', '_opus',
           '_path_utils', '_preload', '_shelves', '_sorting')

INDEX = 'pdsfile\n=======\n\n.. toctree::\n   :maxdepth: 2\n\n   api\n'

PAGE = ('.. automodule:: pdsfile.{name}\n'
        '   :members:\n'
        '   :undoc-members:\n'
        '   :private-members:\n'
        '   :special-members: __init__\n\n')

PROBLEM_RE = re.compile(r'WARNING|ERROR')


def write_tree(build, conf):
    """Write the conf, the index page and the API page into an empty directory.

    Parameters:
        build (pathlib.Path): the directory to write, emptied first if it exists.
        conf (pathlib.Path): the `conf.py` to copy in.
    """

    if build.exists():
        shutil.rmtree(build)
    build.mkdir(parents=True)

    shutil.copy(conf, build / 'conf.py')
    (build / 'index.rst').write_text(INDEX, encoding='utf-8')

    pages = ['API', '===', '', '.. automodule:: pdsfile', '   :members:', '']
    pages += [PAGE.format(name=name) for name in MODULES]
    (build / 'api.rst').write_text('\n'.join(pages), encoding='utf-8')


def run(build, src, flag, out):
    """Run one Sphinx build and return its problem lines.

    Parameters:
        build (pathlib.Path): the source tree written by `write_tree`.
        src (str): the importable source root, passed through `PDSFILE_SRC`.
        flag (str): `-n` or `-W`.
        out (str): the output subdirectory name.

    Returns:
        list: the lines of output that name a warning or an error.
    """

    result = subprocess.run(
        [sys.executable, '-m', 'sphinx', flag, '-E', '-b', 'html', '.', out],
        cwd=build, env={'PDSFILE_SRC': src, 'PATH': '/usr/bin:/bin', 'HOME': '/tmp'},
        capture_output=True, text=True, check=False)

    text = result.stdout + result.stderr

    return [line for line in text.split('\n') if PROBLEM_RE.search(line)]


def main(argv):
    """Build the probe tree and run both gates over it.

    Parameters:
        argv (list): the source root and the build directory.

    Returns:
        int: 1 if either build reported a problem, 0 otherwise.
    """

    src = str(pathlib.Path(argv[0]).resolve())
    build = pathlib.Path(argv[1]).resolve()
    conf = pathlib.Path(__file__).resolve().parent.parent / 'pr-29' / 'sphinx-conf.py'

    write_tree(build, conf)

    total = 0
    for flag, out in (('-n', '_build_n'), ('-W', '_build_w')):
        problems = run(build, src, flag, out)
        total += len(problems)
        print(f'{flag}: {len(problems)} problems')
        for line in problems:
            print('  ' + line)

    return 1 if total else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
