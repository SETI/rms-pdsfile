"""Build a throwaway Sphinx tree over the documented modules and run both gates.

`docs/` does not exist in this repository yet, so there is nowhere to run
`doc_python.mdc` section 6's two builds. This writes a minimal tree somewhere else,
points it at a source root, and runs `sphinx-build -n` and `sphinx-build -W` over
autodoc pages for the modules named below.

The configuration is `critiques/pr-29/sphinx-conf.py` unchanged. What is extended is the
page list: the nine private modules join the four public ones. `pdsfile.pdsfile` has to
be among them or the `PdsFile` written in a `Parameters:` type slot resolves to nothing
and fails `-n`, which is a property of a partial page set rather than of the prose.

`_properties.py` is absent from the default list, because a module whose docstrings have
not been revised adds warnings that belong to the module rather than to this build. Any
module can be added back by naming it, which is how a later change brings its own file
into the page set without disturbing the default.

Usage:
    python build_docs_probe.py SRC_DIR BUILD_DIR [MODULE ...]

`SRC_DIR` is the importable source root, the `src` of the tree being measured.
`BUILD_DIR` is created or emptied. Each `MODULE` is added to the default page list, in
the order given; a name already in that list, and a name given twice, are each written
once, because a duplicated `automodule` directive is a duplicate-target warning and would
fail the very build this runs. Exit status is 1 if either build reports anything.
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


def write_tree(build, conf, modules):
    """Write the conf, the index page and the API page into an empty directory.

    Parameters:
        build (pathlib.Path): the directory to write, emptied first if it exists.
        conf (pathlib.Path): the `conf.py` to copy in.
        modules (tuple): the module names to write an autodoc page for, in order.
    """

    if build.exists():
        shutil.rmtree(build)
    build.mkdir(parents=True)

    shutil.copy(conf, build / 'conf.py')
    (build / 'index.rst').write_text(INDEX, encoding='utf-8')

    pages = ['API', '===', '', '.. automodule:: pdsfile', '   :members:', '']
    pages += [PAGE.format(name=name) for name in modules]
    (build / 'api.rst').write_text('\n'.join(pages), encoding='utf-8')


def run(build, src, flag, out):
    """Run one Sphinx build and return its problem lines.

    Parameters:
        build (pathlib.Path): the source tree written by `write_tree`.
        src (str): the importable source root, passed through `PDSFILE_SRC`.
        flag (str): `-n` or `-W`.
        out (str): the output subdirectory name.

    Returns:
        list: the lines of output that name a warning or an error, plus one line
        recording a nonzero exit status.
    """

    result = subprocess.run(
        [sys.executable, '-m', 'sphinx', flag, '-E', '-b', 'html', '.', out],
        cwd=build, env={'PDSFILE_SRC': src, 'PATH': '/usr/bin:/bin', 'HOME': '/tmp'},
        capture_output=True, text=True, check=False)

    text = result.stdout + result.stderr
    problems = [line for line in text.split('\n') if PROBLEM_RE.search(line)]

    # A build that fails to start prints no warning line at all -- an absent sphinx says
    # only "No module named sphinx" -- so a filter alone would report a clean build.
    if result.returncode:
        problems.append(f'sphinx-build exited with status {result.returncode}')

    return problems


def main(argv):
    """Build the probe tree and run both gates over it.

    Parameters:
        argv (list): the source root, the build directory, and any module names to add
            to the default page list.

    Returns:
        int: 1 if either build reported a problem, 0 otherwise.
    """

    src = str(pathlib.Path(argv[0]).resolve())
    build = pathlib.Path(argv[1]).resolve()
    conf = pathlib.Path(__file__).resolve().parent.parent / 'pr-29' / 'sphinx-conf.py'

    extra = dict.fromkeys(name for name in argv[2:] if name not in MODULES)
    modules = MODULES + tuple(extra)

    write_tree(build, conf, modules)

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
