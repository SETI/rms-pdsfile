# Contributing to rms-pdsfile

Thank you for your interest in contributing to rms-pdsfile! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

We expect all contributors to follow our Code of Conduct, which ensures a welcoming and inclusive environment for everyone.
See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:

   ```bash
   git clone https://github.com/your-username/rms-pdsfile.git
   cd rms-pdsfile
   ```

3. Create a virtual environment and install the package with dev dependencies:

   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -e ".[dev]"
   ```

   Linux and macOS are the supported platforms; Windows is not.

## Development Workflow

1. Create a new branch for your feature or bugfix:

   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b bugfix/issue-number
   ```

2. Make your changes, following our coding standards
3. Write or update tests as necessary
4. Run the tests and lint to ensure they pass:

   ```bash
   scripts/run-all-checks.sh
   ```

5. Commit your changes with a descriptive message:

   ```bash
   git commit -m "Add feature: description of your changes"
   ```

6. Push your branch to your fork:

   ```bash
   git push origin feature/your-feature-name
   ```

7. Open a Pull Request on GitHub

## Coding Standards

We follow these standards for all code contributions:

* **Python Style**: `ruff check` is the style gate, run by `scripts/run-all-checks.sh`
  with the rule set configured in `pyproject.toml`; its per-file-ignores list may
  shrink but never grow
* **Type Hints**: This codebase does not use inline type annotations; do not add them
* **Docstrings**: Document all modules, classes and functions with docstrings
  following the Google style
* **Testing**: Include unit tests for new functionality
* **Compatibility**: Ensure compatibility with Python 3.11+

Example of a well-formatted function:

```python
def calculate_offset(image, model):
    """Calculate the offset between an image and a model.

    Parameters:
        image: The observed image as a NumPy array.
        model: The theoretical model as a NumPy array.

    Returns:
        A tuple containing the (u, v) offset in pixels.
    """
    # Implementation here
    return u_offset, v_offset
```

## Pull Request Process

1. Ensure all tests pass
2. Update documentation if necessary
3. Make sure your code passes every check `scripts/run-all-checks.sh` runs
4. Request a review from a maintainer
5. Address any feedback from reviewers

The maintainers will merge your PR once it meets all requirements.

## Testing

We use pytest, and the suite is holdings-aware: nearly every test runs against a
real PDS holdings tree, and on a machine without one the data-dependent tests are
collected and skipped with a clear reason rather than failing. A bare `pytest`
run with no holdings is therefore green but mostly skips; it proves imports and
the holdings-free subset, nothing more.

To run the suite against a holdings tree (complete, or a limited real copy),
name its roots and select them first — the selector is what makes a bare
`pytest` run use the roots at all:

```bash
export PDS3_HOLDINGS_DIR="/path/to/pdsdata/holdings"
export PDS4_HOLDINGS_DIR="/path/to/pdsdata/pds4-holdings"
export PDSFILE_TEST_HOLDINGS=full

pytest tests --mode ns
```

The `--mode` option (default `ns`) selects how the classes answer file-system
questions: `ns` reads the file system, `s` answers from the info shelf files
alone. The whole tree passes under `ns`; a shelves-specific failure is visible
only under `s`, so a change that touches data handling is checked with both:

```bash
pytest tests --mode ns
pytest tests/pds3file tests/rules/pds3 --mode s
pytest tests/pds4file tests/rules/pds4 --mode s
```

To run a specific test file:

```bash
pytest tests/pds3file/test_pds3file_blackbox.py --mode ns
```

`scripts/run-all-checks.sh` wraps the `ns` pass together with every other check
and fills in the holdings selection from the environment variables. The
[test-suite chapter of the developer guide](docs/dev_guide/dev_guide_testing.rst)
covers the selection machinery, the markers, and the golden-file mechanisms.

## Documentation

We use Sphinx for documentation. To build the docs:

```bash
cd docs
make html
```

The generated documentation will be in `docs/_build/html`.

When adding new features, please update the relevant documentation:

* Update docstrings for new functions and classes
* Add examples if appropriate
* Update the user guide or developer guide if necessary

## Reporting Issues

If you find a bug or have a suggestion for improvement:

1. Check if the issue already exists in the GitHub issue tracker
2. If not, create a new issue with:
   * A clear, descriptive title
   * A detailed description of the issue
   * Steps to reproduce (for bugs)
   * Your environment information (Python version, OS, etc.)
   * Any relevant logs or screenshots

Thank you for contributing to rms-pdsfile!
