#!/usr/bin/env bash
#
# rms-pdsfile - Run All Checks Script
#
# This script runs linting, type checking, tests, Sphinx build, and
# Markdown lint as separate checks. In parallel mode all requested
# checks run concurrently.
#
# Usage:
#   ./scripts/run-all-checks.sh [options]
#
# Options:
#   -p, --parallel         Run all requested checks in parallel (default)
#   -s, --sequential       Run all requested checks sequentially
#   -w, --pytest-workers N Pytest workers: 1 (serial, default), auto, or N
#   -c, --code             Run all code checks (sets each RUN_* code flag true)
#   -d, --docs             Run Sphinx and PyMarkdown (RUN_SPHINX, RUN_PYMARKDOWN)
#   -m, --markdown         Run only PyMarkdown (RUN_PYMARKDOWN)
#   --ruff-check           Run ruff check only (may combine with other --* flags)
#   --ruff-format          Run ruff format --check only
#   --mypy                 Run mypy only
#   --pytest               Run pytest only
#   --pyroma               Run pyroma only
#   --api-freeze           Run the public-API freeze check only
#   --clean-install        Run the clean-install (runtime-dep leak) gate only
#   --bandit               Run bandit only
#   --vulture              Run vulture only
#   --sphinx               Run Sphinx build only
#   --pymarkdown           Run PyMarkdown scan only
#   -h, --help             Show this help message
#
# Environment:
#   VENV or VENV_PATH        Path to virtualenv (default: $PROJECT_ROOT/venv)
#   CLEANUP_GRACE_PERIOD     Seconds to wait for graceful shutdown (default: 5)
#
#   PDS3_HOLDINGS_DIR        Roots of the real holdings trees. Export both to run
#   PDS4_HOLDINGS_DIR          the pytest gate as a full data suite; with neither
#                              it runs the holdings-free subset and skips the
#                              rest. Exporting only one is an error: the gate
#                              fails and names the missing variable rather than
#                              running the subset. Which run happened is printed.
#   PDSFILE_TEST_HOLDINGS    Explicit tree selector (full|mini). Set to full when
#                              either root above is exported and this is not.
#
#   The pytest gate here is ONE --mode ns pass over tests/. The self-hosted data
#   gate (scripts/automated_tests/pdsfile_main_test.sh) runs that pass under
#   coverage plus a second, pds3-only --mode s pass, so it is the authority on
#   shelves-only behavior.
#
#   Pytest coverage minimum: configure fail_under in coverage config (e.g.
#   pyproject.toml [tool.coverage.report] or .coveragerc [report]).
#
#   RUN_* (set by this script from CLI or full-run defaults): RUN_RUFF_CHECK,
#   RUN_RUFF_FORMAT, RUN_MYPY, RUN_PYTEST, RUN_PYROMA, RUN_API_FREEZE,
#   RUN_CLEAN_INSTALL, RUN_BANDIT, RUN_VULTURE, RUN_SPHINX, RUN_PYMARKDOWN
#
#   Per-check toggles (true/false). Each check runs only if both RUN_* and
#   ENABLE_* are true (RUN_* from CLI or defaults below; ENABLE_* from env; see
#   pdsfile_overrides.mdc for which checks are permanently off):
#     ENABLE_RUFF_CHECK   (default: true)
#     ENABLE_RUFF_FORMAT  (default: false — never; owner dropped the one-time
#                          reformat 2026-08-03, see pdsfile_overrides.mdc (11))
#     ENABLE_MYPY         (default: false — never; no inline typing)
#     ENABLE_PYTEST       (default: true)
#     ENABLE_PYROMA       (default: true)
#     ENABLE_API_FREEZE   public-API freeze (default: true)
#     ENABLE_CLEAN_INSTALL clean-install runtime-dep leak gate (default: true)
#     ENABLE_BANDIT       (default: false — never)
#     ENABLE_VULTURE      (default: false — never)
#     ENABLE_SPHINX       Sphinx documentation build (default: true)
#     ENABLE_PYMARKDOWN   PyMarkdown scan (default: false — not enabled yet)
#
# Checks (each run separately; -d runs both Sphinx and Markdown):
#   Code:     optional: ruff check, ruff format --check, mypy, pytest, pyroma,
#             api-freeze, clean-install, bandit, vulture (see ENABLE_* above)
#   Sphinx:   make clean, then two builds whose statuses, output and HTML are all
#             read: make html SPHINXOPTS="-W", then the same with SPHINXOPTS="-n -W"
#             into its own BUILDDIR (all three run from docs/)
#   Markdown: pymarkdown scan docs/ .cursor/ README.md CONTRIBUTING.md
#
# Exit codes:
#   0 - All requested checks passed
#   1 - One or more checks failed
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
RESET='\033[0m'

# Default options
PARALLEL=true
# Serial by default: with holdings present this gate is a full-data run, and each
# xdist worker preloads its own copy of the holdings cache. Pass -w auto to
# parallelize on a machine that can afford it.
PYTEST_WORKERS=1
RUN_RUFF_CHECK=false
RUN_RUFF_FORMAT=false
RUN_MYPY=false
RUN_PYTEST=false
RUN_PYROMA=false
RUN_API_FREEZE=false
RUN_CLEAN_INSTALL=false
RUN_BANDIT=false
RUN_VULTURE=false
RUN_SPHINX=false
RUN_PYMARKDOWN=false
SCOPE_SPECIFIED=false

# Per-check defaults (override by exporting before invoking this script, or
# permanently change here).
#
# Gates are enabled as they become able to pass. Currently enabled: ruff-check
# (which runs the configured rules and then a second, indentation-only pass over
# the preview E1 rules), pytest, pyroma, api-freeze, the clean-install gate, and
# the Sphinx build. Not enabled yet: ruff-format and pymarkdown. Never enabled:
# mypy, bandit, vulture (ground rules / pdsfile_overrides.mdc).
: "${ENABLE_RUFF_CHECK:=true}"
: "${ENABLE_RUFF_FORMAT:=false}"
: "${ENABLE_MYPY:=false}"
: "${ENABLE_PYTEST:=true}"
: "${ENABLE_PYROMA:=true}"
: "${ENABLE_API_FREEZE:=true}"
: "${ENABLE_CLEAN_INSTALL:=true}"
: "${ENABLE_BANDIT:=false}"
: "${ENABLE_VULTURE:=false}"
: "${ENABLE_SPHINX:=true}"
: "${ENABLE_PYMARKDOWN:=false}"

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV="${VENV:-${VENV_PATH:-$PROJECT_ROOT/venv}}"

# Track failures and final exit code
FAILED_CHECKS=()
EXIT_CODE=0

# Temp directory for parallel output and status files
TEMP_DIR=$(mktemp -d)

# Grace period (seconds) before SIGKILL after SIGTERM
CLEANUP_GRACE_PERIOD=${CLEANUP_GRACE_PERIOD:-5}
if ! echo "$CLEANUP_GRACE_PERIOD" | grep -qE '^[0-9]+$'; then
    echo "Error: CLEANUP_GRACE_PERIOD must be a non-negative integer (got: $CLEANUP_GRACE_PERIOD)" >&2
    exit 1
fi

_wait_or_kill() {
    local pid=$1
    [ -z "$pid" ] && return 0
    kill -TERM "$pid" 2>/dev/null || true
    local waited=0
    while [ "$waited" -lt "$CLEANUP_GRACE_PERIOD" ]; do
        kill -0 "$pid" 2>/dev/null || break
        sleep 1
        waited=$((waited + 1))
    done
    if kill -0 "$pid" 2>/dev/null; then
        kill -KILL "$pid" 2>/dev/null || true
    fi
    wait "$pid" 2>/dev/null || true
    return 0
}

_cleanup() {
    rm -rf "$TEMP_DIR"
}

# On INT/TERM: kill all background check jobs with grace period, then exit
_cleanup_and_exit() {
    local sig_code=$1
    local pids
    pids=$(jobs -p)
    if [ -n "$pids" ]; then
        for pid in $pids; do
            _wait_or_kill "$pid"
        done
    fi
    _cleanup
    exit "$sig_code"
}
trap '_cleanup_and_exit 130' SIGINT
trap '_cleanup_and_exit 143' SIGTERM
trap _cleanup EXIT

print_header() {
    echo -e "\n${BOLD}${BLUE}===================================================${RESET}"
    echo -e "${BOLD}${BLUE}  $1${RESET}"
    echo -e "${BOLD}${BLUE}===================================================${RESET}\n"
}

print_section() {
    echo -e "\n${BOLD}${YELLOW}>>> $1${RESET}\n"
}

print_success() {
    echo -e "${GREEN}✓${RESET} $1"
}

print_error() {
    echo -e "${RED}✗${RESET} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${RESET} $1"
}

show_usage() {
    sed -n '/^# Usage:/,/^# Exit codes:/p' "$0" | sed 's/^# //g' | sed 's/^#//g'
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--parallel)
            PARALLEL=true
            shift
            ;;
        -s|--sequential)
            PARALLEL=false
            shift
            ;;
        -w|--pytest-workers)
            if [[ -z "${2:-}" || "$2" =~ ^- ]]; then
                echo -e "${RED}Error: -w/--pytest-workers requires a value (auto, 1, 2, ...)${RESET}" >&2
                show_usage
                exit 1
            fi
            PYTEST_WORKERS="$2"
            shift 2
            ;;
        --pytest-workers=*)
            PYTEST_WORKERS="${1#*=}"
            shift
            ;;
        -c|--code)
            RUN_RUFF_CHECK=true
            RUN_RUFF_FORMAT=true
            RUN_MYPY=true
            RUN_PYTEST=true
            RUN_PYROMA=true
            RUN_API_FREEZE=true
            RUN_CLEAN_INSTALL=true
            RUN_BANDIT=true
            RUN_VULTURE=true
            SCOPE_SPECIFIED=true
            shift
            ;;
        -d|--docs)
            RUN_SPHINX=true
            RUN_PYMARKDOWN=true
            SCOPE_SPECIFIED=true
            shift
            ;;
        -m|--markdown)
            RUN_PYMARKDOWN=true
            SCOPE_SPECIFIED=true
            shift
            ;;
        --ruff-check)
            RUN_RUFF_CHECK=true
            SCOPE_SPECIFIED=true
            shift
            ;;
        --ruff-format)
            RUN_RUFF_FORMAT=true
            SCOPE_SPECIFIED=true
            shift
            ;;
        --mypy)
            RUN_MYPY=true
            SCOPE_SPECIFIED=true
            shift
            ;;
        --pytest)
            RUN_PYTEST=true
            SCOPE_SPECIFIED=true
            shift
            ;;
        --pyroma)
            RUN_PYROMA=true
            SCOPE_SPECIFIED=true
            shift
            ;;
        --api-freeze)
            RUN_API_FREEZE=true
            SCOPE_SPECIFIED=true
            shift
            ;;
        --clean-install)
            RUN_CLEAN_INSTALL=true
            SCOPE_SPECIFIED=true
            shift
            ;;
        --bandit)
            RUN_BANDIT=true
            SCOPE_SPECIFIED=true
            shift
            ;;
        --vulture)
            RUN_VULTURE=true
            SCOPE_SPECIFIED=true
            shift
            ;;
        --sphinx)
            RUN_SPHINX=true
            SCOPE_SPECIFIED=true
            shift
            ;;
        --pymarkdown)
            RUN_PYMARKDOWN=true
            SCOPE_SPECIFIED=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Error: Unknown option: $1${RESET}" >&2
            show_usage
            exit 1
            ;;
    esac
done

# Default: run all checks (each RUN_* true; ENABLE_* still filters per repo)
if [ "$SCOPE_SPECIFIED" = false ]; then
    RUN_RUFF_CHECK=true
    RUN_RUFF_FORMAT=true
    RUN_MYPY=true
    RUN_PYTEST=true
    RUN_PYROMA=true
    RUN_API_FREEZE=true
    RUN_CLEAN_INSTALL=true
    RUN_BANDIT=true
    RUN_VULTURE=true
    RUN_SPHINX=true
    RUN_PYMARKDOWN=true
fi

START_TIME=$(date +%s)

print_header "rms-pdsfile - Running All Checks"

if [ "$PARALLEL" = true ]; then
    print_info "Running checks in PARALLEL mode"
else
    print_info "Running checks in SEQUENTIAL mode"
fi
if [ "$RUN_PYTEST" = true ] && [ "$ENABLE_PYTEST" = true ]; then
    print_info "Pytest workers: $PYTEST_WORKERS"
fi

# True if at least one code check is both selected (RUN_*) and enabled (ENABLE_*).
_code_checks_any_scheduled() {
    [ "$RUN_RUFF_CHECK" = true ] && [ "$ENABLE_RUFF_CHECK" = true ] && return 0
    [ "$RUN_RUFF_FORMAT" = true ] && [ "$ENABLE_RUFF_FORMAT" = true ] && return 0
    [ "$RUN_MYPY" = true ] && [ "$ENABLE_MYPY" = true ] && return 0
    [ "$RUN_PYTEST" = true ] && [ "$ENABLE_PYTEST" = true ] && return 0
    [ "$RUN_PYROMA" = true ] && [ "$ENABLE_PYROMA" = true ] && return 0
    [ "$RUN_API_FREEZE" = true ] && [ "$ENABLE_API_FREEZE" = true ] && return 0
    [ "$RUN_CLEAN_INSTALL" = true ] && [ "$ENABLE_CLEAN_INSTALL" = true ] && return 0
    [ "$RUN_BANDIT" = true ] && [ "$ENABLE_BANDIT" = true ] && return 0
    [ "$RUN_VULTURE" = true ] && [ "$ENABLE_VULTURE" = true ] && return 0
    return 1
}

# ---- Code checks (ruff, mypy, pytest, pyroma, bandit, vulture) ----
run_code_checks() {
    local output_file="${1:-}"
    local status_file="${2:-}"

    if [ -n "$output_file" ]; then
        exec > "$output_file" 2>&1
    fi

    print_section "Code Checks"

    cd "$PROJECT_ROOT" || exit 1

    if ! _code_checks_any_scheduled; then
        print_info "No code checks scheduled (RUN_* and ENABLE_*); skipping code checks"
        return 0
    fi

    if [ ! -f "$VENV/bin/activate" ]; then
        print_error "Virtual environment not found at $VENV"
        [ -n "$status_file" ] && echo "Code - Virtual environment not found" >> "$status_file"
        return 1
    fi

    # shellcheck source=/dev/null
    source "$VENV/bin/activate"

    local failed=false
    local failed_checks=""

    # Lint the package under src/pdsfile, the top-level tests/ tree (which
    # includes tests/conftest.py), the standalone scripts, and docs/ for its
    # conf.py, which is the one Python file the documentation tree carries.
    RUFF_TARGETS="src/pdsfile tests scripts docs"

    if [ "$RUN_RUFF_CHECK" = true ] && [ "$ENABLE_RUFF_CHECK" = true ]; then
        print_info "Running ruff check..."
        if python -m ruff check $RUFF_TARGETS; then
            print_success "Ruff check passed"
        else
            print_error "Ruff check failed"
            failed=true
            failed_checks="${failed_checks}Code - Ruff check"$'\n'
        fi

        # Indentation of code. The E1 rules are preview-gated, so they need
        # their own invocation: turning preview on in pyproject.toml would also
        # change the behaviour of the stable rules and raise thousands of new
        # findings. Naming the codes explicitly keeps the surface narrow.
        #
        # Only the three rules that fire on code are selected. E114, E115 and
        # E116 are their comment-line counterparts, and E117 fires on both.
        # Where a comment sits is the author's decision here: a trailing comment
        # continued under the column it started in, an annotation that follows
        # the statement it describes, and commented-out code parked at column 0
        # are all deliberate, and all three read worse pulled to the code grid.
        print_info "Running ruff check (indentation)..."
        if python -m ruff check --preview \
                --select E111,E112,E113 $RUFF_TARGETS; then
            print_success "Ruff indentation check passed"
        else
            print_error "Ruff indentation check failed"
            failed=true
            failed_checks="${failed_checks}Code - Ruff indentation"$'\n'
        fi
    fi

    if [ "$RUN_RUFF_FORMAT" = true ] && [ "$ENABLE_RUFF_FORMAT" = true ]; then
        print_info "Running ruff format --check..."
        if python -m ruff format --check $RUFF_TARGETS; then
            print_success "Ruff format check passed"
        else
            print_error "Ruff format check failed"
            failed=true
            failed_checks="${failed_checks}Code - Ruff format"$'\n'
        fi
    fi

    if [ "$RUN_MYPY" = true ] && [ "$ENABLE_MYPY" = true ]; then
        print_info "Running mypy..."
        if MYPYPATH=src python -m mypy src tests; then
            print_success "Mypy passed"
        else
            print_error "Mypy failed"
            failed=true
            failed_checks="${failed_checks}Code - Mypy"$'\n'
        fi
    fi

    # -n controls parallelism; --dist loadscope keeps each test module on one
    # worker to avoid cross-test interference. No -n/--cov live in pyproject
    # addopts (chosen per invocation), so they are passed here. This branch runs
    # only when the pytest gate is enabled (ENABLE_PYTEST) and targets the whole
    # top-level tests/ tree.
    #
    # --mode ns is the mode in which the whole tree passes; it is passed
    # explicitly so this invocation does not depend on the option's default. Note
    # this is one pass over everything, whereas the self-hosted data gate
    # (scripts/automated_tests/pdsfile_main_test.sh) runs two: the same ns pass
    # under coverage, then a pds3-only --mode s pass. A shelves-only-specific
    # failure is therefore visible to that driver and not to this script.
    if [ "$RUN_PYTEST" = true ] && [ "$ENABLE_PYTEST" = true ]; then
        # Which tree the suite runs against is chosen by PDSFILE_TEST_HOLDINGS
        # (see tests/support/holdings.py); exporting the roots is not by itself
        # enough. Either root present and no selector means someone meant to run
        # against data, so select the full tree rather than quietly running the
        # holdings-free subset and reporting success. With only one of the two
        # exported the resolver then fails the session and names the missing
        # variable, which is the point: half-configured is a mistake, not a
        # 3%-of-the-suite pass. An explicit selector always wins.
        if [ -z "${PDSFILE_TEST_HOLDINGS:-}" ] \
                && { [ -n "${PDS3_HOLDINGS_DIR:-}" ] || [ -n "${PDS4_HOLDINGS_DIR:-}" ]; }; then
            export PDSFILE_TEST_HOLDINGS=full
        fi
        # Report what the resolver actually resolved rather than re-deriving it
        # here, so the log cannot disagree with the session.
        holdings_flavor=$(python -c 'import sys; sys.path.insert(0, ".")
from tests.support.holdings import resolve_holdings
print(resolve_holdings().flavor or "none")' 2>/dev/null || echo 'unresolved')
        case "$holdings_flavor" in
            none)
                print_info "Running pytest (-n ${PYTEST_WORKERS}; no holdings: holdings-free subset only)..."
                ;;
            unresolved)
                print_info "Running pytest (-n ${PYTEST_WORKERS}; holdings selection is invalid, pytest will report it)..."
                ;;
            *)
                print_info "Running pytest (-n ${PYTEST_WORKERS}; holdings: ${holdings_flavor})..."
                ;;
        esac
        if python -m pytest -q -n "$PYTEST_WORKERS" --dist loadscope tests --mode ns; then
            print_success "Pytest passed"
        else
            print_error "Pytest failed"
            failed=true
            failed_checks="${failed_checks}Code - Pytest"$'\n'
        fi
    fi

    if [ "$RUN_PYROMA" = true ] && [ "$ENABLE_PYROMA" = true ]; then
        print_info "Running pyroma (packaging metadata)..."
        if python -m pyroma .; then
            print_success "Pyroma passed"
        else
            print_error "Pyroma failed"
            failed=true
            failed_checks="${failed_checks}Code - Pyroma"$'\n'
        fi
    fi

    # Public-API freeze. --confcutdir=tests/api collects the test without
    # tests/conftest.py, so this check pulls in no session options, no holdings
    # resolution and no preload. The freeze test regenerates the manifest in a
    # clean subprocess and needs no holdings itself.
    if [ "$RUN_API_FREEZE" = true ] && [ "$ENABLE_API_FREEZE" = true ]; then
        print_info "Running API-freeze check..."
        if python -m pytest tests/api/test_api_freeze.py --confcutdir=tests/api -p no:cacheprovider -q; then
            print_success "API-freeze check passed"
        else
            print_error "API-freeze check failed"
            failed=true
            failed_checks="${failed_checks}Code - API freeze"$'\n'
        fi
    fi

    # Clean-install gate (permanent). Builds a throwaway venv, installs the
    # project with NO extras, and imports the whole public module surface. The
    # only check that catches a runtime-dependency leak (every other run has the
    # dev extra present). Runs its own subprocess venv, independent of the
    # activated dev venv here.
    if [ "$RUN_CLEAN_INSTALL" = true ] && [ "$ENABLE_CLEAN_INSTALL" = true ]; then
        print_info "Running clean-install gate (runtime-dep leak)..."
        if bash "$PROJECT_ROOT/scripts/clean_install_check.sh"; then
            print_success "Clean-install gate passed"
        else
            print_error "Clean-install gate failed"
            failed=true
            failed_checks="${failed_checks}Code - Clean install"$'\n'
        fi
    fi

    if [ "$RUN_BANDIT" = true ] && [ "$ENABLE_BANDIT" = true ]; then
        print_info "Running bandit..."
        if python -m bandit -c pyproject.toml -r src -q; then
            print_success "Bandit passed"
        else
            print_error "Bandit failed"
            failed=true
            failed_checks="${failed_checks}Code - Bandit"$'\n'
        fi
    fi

    if [ "$RUN_VULTURE" = true ] && [ "$ENABLE_VULTURE" = true ]; then
        print_info "Running vulture..."
        if python -m vulture src tests; then
            print_success "Vulture passed"
        else
            print_error "Vulture failed"
            failed=true
            failed_checks="${failed_checks}Code - Vulture"$'\n'
        fi
    fi

    deactivate 2>/dev/null || true

    if [ "$failed" = true ]; then
        [ -n "$status_file" ] && printf '%s' "$failed_checks" >> "$status_file"
        return 1
    fi
    return 0
}

# ---- Sphinx build only ----
run_sphinx_build() {
    local output_file="${1:-}"
    local status_file="${2:-}"

    if [ -n "$output_file" ]; then
        exec > "$output_file" 2>&1
    fi

    print_section "Sphinx Build"

    cd "$PROJECT_ROOT" || exit 1

    if [ ! -f "$VENV/bin/activate" ]; then
        print_error "Virtual environment not found at $VENV"
        [ -n "$status_file" ] && echo "Sphinx - Virtual environment not found" >> "$status_file"
        return 1
    fi

    # shellcheck source=/dev/null
    source "$VENV/bin/activate"

    # Two builds, and the reason is not that each catches something the other misses:
    # -n only adds the unresolved-cross-reference warnings to what -W already fails on,
    # so the second build's findings are a superset of the first's. What the first build
    # supplies is docs/_build/html, which is the tree a reader opens, and a failure
    # attributable to something other than a cross-reference. The documentation rules ask
    # for both builds; running -n without -W would be the mistake, because on its own it
    # reports every unresolved reference and still exits 0.
    #
    # The second build gets its own BUILDDIR. Two builds that share one share its
    # doctree cache, Sphinx then re-reads only what changed, and a build that re-reads
    # nothing re-reports nothing.
    local clean_status=0
    local warnings_status=0
    local nitpicky_status=0
    local warnings_log="$TEMP_DIR/sphinx-warnings-build.log"
    local nitpicky_log="$TEMP_DIR/sphinx-nitpicky-build.log"

    print_info "Emptying docs/_build..."
    (cd docs && make clean) || clean_status=$?
    if [ "$clean_status" -ne 0 ]; then
        print_error "Sphinx: make clean failed (exit $clean_status); neither build ran"
        if [ -n "$status_file" ]; then
            echo "Sphinx - make clean" >> "$status_file"
        fi
        deactivate 2>/dev/null || true
        return 1
    fi

    print_info "Building documentation (warnings as errors)..."
    (cd docs && make html SPHINXOPTS="-W") > "$warnings_log" 2>&1 || warnings_status=$?
    cat "$warnings_log"

    print_info "Building documentation (nitpicky, warnings as errors)..."
    (cd docs && make html BUILDDIR=_build/nitpicky SPHINXOPTS="-n -W") \
        > "$nitpicky_log" 2>&1 || nitpicky_status=$?
    cat "$nitpicky_log"

    deactivate 2>/dev/null || true

    # Read the builds rather than restating them. A build is accepted only if it exited
    # 0, wrote the HTML it was asked for, and printed the line docs/conf.py emits when it
    # has compared the source tree against the modules the build documented. Exit status
    # alone would accept a `make` that resolved to nothing at all.
    _sphinx_build_verdict "warnings-as-errors" "$warnings_status" "$warnings_log" \
        docs/_build/html/index.html "$status_file" || warnings_status=1
    _sphinx_build_verdict "nitpicky" "$nitpicky_status" "$nitpicky_log" \
        docs/_build/nitpicky/html/index.html "$status_file" || nitpicky_status=1

    if [ "$warnings_status" -eq 0 ] && [ "$nitpicky_status" -eq 0 ]; then
        local warn_problems nitpick_problems coverage
        warn_problems=$(_sphinx_problem_count "$warnings_log")
        nitpick_problems=$(_sphinx_problem_count "$nitpicky_log")
        coverage=$(_sphinx_coverage_line "$warnings_log")
        print_success "Sphinx build passed: $warn_problems problem lines under -W and $nitpick_problems under -n -W, and the build reports $coverage"
        return 0
    fi
    return 1
}

# Number of WARNING/ERROR lines a Sphinx build printed. grep reports none by exiting 1,
# which under `set -o pipefail` would otherwise take the caller down with it.
_sphinx_problem_count() {
    grep -cE 'WARNING:|ERROR:' "$1" || true
}

# The coverage line docs/conf.py prints once per build, or the empty string if it did not.
_sphinx_coverage_line() {
    { grep -oE 'API reference: [0-9]+ of [0-9]+ modules under [^ ]+ documented' "$1" \
        || true; } | tail -1
}

# Accept one Sphinx build. Prints its verdict and returns non-zero unless the build
# exited 0, produced its HTML, and reported its module coverage.
_sphinx_build_verdict() {
    local label=$1 status=$2 log=$3 html=$4 status_file=$5
    local problems coverage
    problems=$(_sphinx_problem_count "$log")
    coverage=$(_sphinx_coverage_line "$log")

    if [ "$status" -ne 0 ]; then
        print_error "Sphinx $label build failed (exit $status, problem lines: $problems)"
    elif [ ! -f "$html" ]; then
        print_error "Sphinx $label build exited 0 but wrote no $html"
    elif [ -z "$coverage" ]; then
        print_error "Sphinx $label build exited 0 but reported no API-reference coverage"
    else
        print_success "Sphinx $label build passed (exit 0, problem lines: $problems, $coverage)"
        return 0
    fi

    if [ -n "$status_file" ]; then
        echo "Sphinx - $label build" >> "$status_file"
    fi
    return 1
}

# ---- Markdown lint only (PyMarkdown) ----
run_markdown_checks() {
    local output_file="${1:-}"
    local status_file="${2:-}"

    if [ -n "$output_file" ]; then
        exec > "$output_file" 2>&1
    fi

    print_section "Markdown Lint (PyMarkdown)"

    cd "$PROJECT_ROOT" || exit 1

    if [ ! -f "$VENV/bin/activate" ]; then
        print_error "Virtual environment not found at $VENV"
        [ -n "$status_file" ] && echo "Markdown - Virtual environment not found" >> "$status_file"
        return 1
    fi

    # shellcheck source=/dev/null
    source "$VENV/bin/activate"

    print_info "Running PyMarkdown scan (docs/, .cursor/, root *.md)..."
    local scan_paths=()
    [ -d "docs/" ] && scan_paths+=("docs/")
    [ -d ".cursor/" ] && scan_paths+=(".cursor/")
    [ -f "README.md" ] && scan_paths+=("README.md")
    [ -f "CONTRIBUTING.md" ] && scan_paths+=("CONTRIBUTING.md")
    if [ ${#scan_paths[@]} -eq 0 ]; then
        print_info "No Markdown files/directories found to scan"
        deactivate 2>/dev/null || true
        return 0
    fi
    if python -m pymarkdown scan "${scan_paths[@]}"; then
        print_success "PyMarkdown scan passed"
        deactivate 2>/dev/null || true
        return 0
    else
        print_error "PyMarkdown scan failed"
        [ -n "$status_file" ] && echo "Markdown - PyMarkdown scan" >> "$status_file"
        deactivate 2>/dev/null || true
        return 1
    fi
}

# ---- Collect status from a status file into FAILED_CHECKS ----
_collect_status() {
    local status_file=$1
    if [ -f "$status_file" ]; then
        while IFS= read -r line; do
            [ -n "$line" ] && FAILED_CHECKS+=("$line")
        done < "$status_file"
    fi
}

# ---- Run requested checks ----
if [ "$PARALLEL" = true ]; then
    print_info "Running requested checks in parallel, please wait..."

    pids=()
    temp_files=()
    status_files=()

    if _code_checks_any_scheduled; then
        code_output="$TEMP_DIR/code.log"
        code_status="$TEMP_DIR/code.status"
        temp_files+=("$code_output")
        status_files+=("$code_status")
        run_code_checks "$code_output" "$code_status" &
        pids+=($!)
    fi

    if [ "$RUN_SPHINX" = true ] && [ "$ENABLE_SPHINX" = true ]; then
        sphinx_output="$TEMP_DIR/sphinx.log"
        sphinx_status="$TEMP_DIR/sphinx.status"
        temp_files+=("$sphinx_output")
        status_files+=("$sphinx_status")
        run_sphinx_build "$sphinx_output" "$sphinx_status" &
        pids+=($!)
    fi

    if [ "$RUN_PYMARKDOWN" = true ] && [ "$ENABLE_PYMARKDOWN" = true ]; then
        markdown_output="$TEMP_DIR/markdown.log"
        markdown_status="$TEMP_DIR/markdown.status"
        temp_files+=("$markdown_output")
        status_files+=("$markdown_status")
        run_markdown_checks "$markdown_output" "$markdown_status" &
        pids+=($!)
    fi

    # Wait for all jobs; any non-zero exit sets EXIT_CODE=1
    for pid in "${pids[@]}"; do
        if ! wait "$pid"; then
            EXIT_CODE=1
        fi
    done

    # Collect named failures from status files
    for status_file in "${status_files[@]}"; do
        _collect_status "$status_file"
    done

    # Safety net: if any status file had content, ensure EXIT_CODE reflects it
    [ ${#FAILED_CHECKS[@]} -gt 0 ] && EXIT_CODE=1

    # Print all outputs in a fixed order
    echo ""
    for log_file in "${temp_files[@]}"; do
        [ -f "$log_file" ] && cat "$log_file"
    done
else
    # Sequential — pass a status file so FAILED_CHECKS is populated
    if _code_checks_any_scheduled; then
        code_status="$TEMP_DIR/code.status"
        if ! run_code_checks "" "$code_status"; then
            EXIT_CODE=1
        fi
        _collect_status "$code_status"
    fi

    if [ "$RUN_SPHINX" = true ] && [ "$ENABLE_SPHINX" = true ]; then
        sphinx_status="$TEMP_DIR/sphinx.status"
        if ! run_sphinx_build "" "$sphinx_status"; then
            EXIT_CODE=1
        fi
        _collect_status "$sphinx_status"
    fi

    if [ "$RUN_PYMARKDOWN" = true ] && [ "$ENABLE_PYMARKDOWN" = true ]; then
        markdown_status="$TEMP_DIR/markdown.status"
        if ! run_markdown_checks "" "$markdown_status"; then
            EXIT_CODE=1
        fi
        _collect_status "$markdown_status"
    fi
fi

# ---- Summary ----
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
MINUTES=$((ELAPSED / 60))
ELAPSED_SECONDS=$((ELAPSED % 60))

print_header "Summary"

if [ "$EXIT_CODE" -eq 0 ]; then
    print_success "All checks passed!"
    echo -e "${GREEN}${BOLD}✓ SUCCESS${RESET} - All checks completed successfully"
else
    print_error "Some checks failed:"
    if [ ${#FAILED_CHECKS[@]} -eq 0 ]; then
        echo -e "  ${RED}✗${RESET} One or more checks failed (see output above)"
    else
        for check in "${FAILED_CHECKS[@]}"; do
            echo -e "  ${RED}✗${RESET} $check"
        done
        echo -e "${RED}${BOLD}✗ FAILURE${RESET} - ${#FAILED_CHECKS[@]} check(s) failed"
    fi
fi

echo ""
print_info "Total time: ${MINUTES}m ${ELAPSED_SECONDS}s"
echo ""

exit "$EXIT_CODE"
