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
#   --stubtest             Run the public-API stub validation (stubtest) only
#   --bandit               Run bandit only
#   --vulture              Run vulture only
#   --sphinx               Run Sphinx build only
#   --pymarkdown           Run PyMarkdown scan only
#   --coverage             Run the pytest gate under coverage; report and write
#                            htmlcov/
#   --coverage-subprocess  As --coverage, and measure the maintenance tools too
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
#   shelves-only behavior, and its coverage total is over both passes where the
#   --coverage total below is over one.
#
#   Coverage (--coverage, --coverage-subprocess) is OFF unless asked for: it is a
#   mode of the pytest gate, not a check of its own, so it has no RUN_*/ENABLE_*
#   pair -- a no-scope run turns every RUN_* on, and that is the day-to-day run
#   coverage must stay out of. Both modes use `coverage run`, as the data gate
#   does, and take what is measured from [tool.coverage.*] in pyproject.toml: the
#   script names no source, omit or exclude, and reaches `branch` and `parallel`
#   through the environment variables that section substitutes. Two settings it
#   does name outright, both of them coverage's own environment variables and
#   neither of them about what is measured: COVERAGE_CORE, which selects the
#   tracer, and COVERAGE_FILE, which puts the data in the project root whatever
#   directory a measured child happens to run in.
#
#     --coverage             Branch coverage of the pytest process, which is what
#                            pyproject.toml configures and what the data gate
#                            produces. The eleven console-script tools and
#                            show_opus_products run as subprocesses, so this
#                            measures their test files' imports, not the tools.
#     --coverage-subprocess  Adds the tool subprocesses, through
#                            COVERAGE_PROCESS_START, which coverage's own
#                            a1_coverage.pth acts on from 7.10 and the hook in
#                            tests/holdings_maintenance/_subprocess_guard/
#                            sitecustomize.py acts on at any version (and fails
#                            closed, which the .pth does not). That costs two
#                            settings for the whole run, because a run cannot be
#                            half of each:
#                            data files are per-process (combined afterwards),
#                            and coverage is LINE-ONLY under COVERAGE_CORE=sysmon
#                            -- coverage cannot measure branches with sys.monitoring
#                            below Python 3.14, and `coverage combine` refuses to
#                            mix branch data with statement data. The run says so in
#                            its own output, and writes htmlcov/ as well. Measured on
#                            tests/holdings_maintenance/test_pds3_archives.py
#                            (13 ids, Python 3.12.3, coverage 7.13.3): 10.60s
#                            uninstrumented, 12.49s this mode, 79.68s with branch
#                            coverage and the C tracer -- 1.2x against 7.5x. On a
#                            Python without sys.monitoring the sysmon request
#                            falls back to the C tracer and this mode costs the
#                            7.5x; the run prints that too.
#
#   Either mode runs pytest with -n 0 (in this process) whatever -w asked for:
#   xdist workers are subprocesses `coverage run` does not follow, measured on
#   tests/core (73 ids) as 15% under -n 1 against 24% under -n 0.
#
#   Pytest coverage minimum: configure fail_under in coverage config (e.g.
#   pyproject.toml [tool.coverage.report] or .coveragerc [report]).
#
#   RUN_* (set by this script from CLI or full-run defaults): RUN_RUFF_CHECK,
#   RUN_RUFF_FORMAT, RUN_MYPY, RUN_PYTEST, RUN_PYROMA, RUN_API_FREEZE,
#   RUN_CLEAN_INSTALL, RUN_STUBTEST, RUN_BANDIT, RUN_VULTURE, RUN_SPHINX,
#   RUN_PYMARKDOWN
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
#     ENABLE_STUBTEST     public-API stub validation via mypy.stubtest
#                         (default: true). Distinct from ENABLE_MYPY: stubtest
#                         checks the .pyi stubs against the runtime surface;
#                         it never type-checks the implementation
#     ENABLE_BANDIT       (default: false — never)
#     ENABLE_VULTURE      (default: false — never)
#     ENABLE_SPHINX       Sphinx documentation build (default: true)
#     ENABLE_PYMARKDOWN   PyMarkdown scan (default: true)
#
# Checks (each run separately; -d runs both Sphinx and Markdown):
#   Code:     optional: ruff check, ruff format --check, mypy, pytest, pyroma,
#             api-freeze, clean-install, stubtest, bandit, vulture (see
#             ENABLE_* above)
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
RUN_STUBTEST=false
RUN_BANDIT=false
RUN_VULTURE=false
RUN_SPHINX=false
RUN_PYMARKDOWN=false
SCOPE_SPECIFIED=false
# Coverage is a mode of the pytest gate rather than a check of its own; see the
# Environment section above for why it carries no RUN_*/ENABLE_* pair.
COVERAGE=false
COVERAGE_SUBPROCESS=false

# Per-check defaults (override by exporting before invoking this script, or
# permanently change here).
#
# Gates are enabled as they become able to pass. Currently enabled: ruff-check
# (which runs the configured rules and then a second, indentation-only pass over
# the preview E1 rules), pytest, pyroma, api-freeze, the clean-install gate,
# stubtest, the Sphinx build, and pymarkdown. Not enabled: ruff-format (owner
# decision, pdsfile_overrides.mdc (11)). Never enabled: mypy, bandit, vulture
# (ground rules / pdsfile_overrides.mdc).
: "${ENABLE_RUFF_CHECK:=true}"
: "${ENABLE_RUFF_FORMAT:=false}"
: "${ENABLE_MYPY:=false}"
: "${ENABLE_PYTEST:=true}"
: "${ENABLE_PYROMA:=true}"
: "${ENABLE_API_FREEZE:=true}"
: "${ENABLE_CLEAN_INSTALL:=true}"
: "${ENABLE_STUBTEST:=true}"
: "${ENABLE_BANDIT:=false}"
: "${ENABLE_VULTURE:=false}"
: "${ENABLE_SPHINX:=true}"
: "${ENABLE_PYMARKDOWN:=true}"

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
            RUN_STUBTEST=true
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
        --stubtest)
            RUN_STUBTEST=true
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
        # Neither coverage flag sets SCOPE_SPECIFIED: they select nothing, they
        # change how the pytest gate runs, the way -p/-s/-w do.
        --coverage)
            COVERAGE=true
            shift
            ;;
        --coverage-subprocess)
            COVERAGE=true
            COVERAGE_SUBPROCESS=true
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
    RUN_STUBTEST=true
    RUN_BANDIT=true
    RUN_VULTURE=true
    RUN_SPHINX=true
    RUN_PYMARKDOWN=true
fi

# Coverage rides on the pytest gate's own two flags, so asking for it with that
# gate unselected or disabled is a request to measure nothing. That fails here
# rather than printing a 0% report, for the same reason the PyMarkdown gate fails
# on an empty file selection.
if [ "$COVERAGE" = true ] \
        && { [ "$RUN_PYTEST" != true ] || [ "$ENABLE_PYTEST" != true ]; }; then
    echo -e "${RED}Error: --coverage measures the pytest gate, which this run does not"\
            "schedule (RUN_PYTEST=$RUN_PYTEST, ENABLE_PYTEST=$ENABLE_PYTEST)${RESET}" >&2
    exit 1
fi

# Where the data lands: coverage's own default name in the project root, which is
# what `coverage report` and the data gate both expect, and which .gitignore
# already covers. Where the HTML lands is coverage's choice, not this script's.
COVERAGE_DATA_FILE="$PROJECT_ROOT/.coverage"

# The environment every coverage command in this run is prefixed with. It is
# passed per command rather than exported, so that the total describes the pytest
# gate and nothing else. An exported COVERAGE_PROCESS_START would reach every
# other check too -- in either mode, since a backgrounded subshell inherits the
# exported environment exactly as a sequential one does -- and the Sphinx build is
# the one that matters: its autodoc imports the package. Measured by running the
# docs gate alone with these variables in its environment: three data files, 77
# pdsfile modules, 6,851 lines recorded, none of it executed by a test.
COVERAGE_ENV=()
if [ "$COVERAGE" = true ]; then
    COVERAGE_ENV=("COVERAGE_FILE=$COVERAGE_DATA_FILE")
fi
if [ "$COVERAGE_SUBPROCESS" = true ]; then
    # COVERAGE_PROCESS_START is read by two things in a tool subprocess: the
    # coverage hook in the tests' sitecustomize, and (on a coverage new enough to
    # ship it) coverage's own a1_coverage.pth. Both call the same
    # coverage.process_startup(); the hook is what makes the measurement fail
    # closed and what works on a coverage that ships no .pth.
    #
    # PDSFILE_COVERAGE_PARALLEL and PDSFILE_COVERAGE_BRANCH are read by
    # pyproject.toml itself (coverage substitutes environment variables into
    # config values), which is how a setting reaches a child that has no command
    # line. Unset, they leave the repository default: branch coverage, one data
    # file.
    COVERAGE_ENV+=("COVERAGE_PROCESS_START=$PROJECT_ROOT/pyproject.toml"
                   "PDSFILE_COVERAGE_PARALLEL=true"
                   "PDSFILE_COVERAGE_BRANCH=false"
                   "COVERAGE_CORE=sysmon")
fi

START_TIME=$(date +%s)

print_header "rms-pdsfile - Running All Checks"

if [ "$PARALLEL" = true ]; then
    print_info "Running checks in PARALLEL mode"
else
    print_info "Running checks in SEQUENTIAL mode"
fi
if [ "$RUN_PYTEST" = true ] && [ "$ENABLE_PYTEST" = true ]; then
    if [ "$COVERAGE" = true ]; then
        # Said here as well as at the invocation, so that -w and what runs cannot
        # appear to disagree: coverage mode overrides the worker count outright.
        print_info "Pytest workers: 0 (coverage mode; -w ${PYTEST_WORKERS} is overridden)"
    else
        print_info "Pytest workers: $PYTEST_WORKERS"
    fi
fi
if [ "$COVERAGE" = true ]; then
    if [ "$COVERAGE_SUBPROCESS" = true ]; then
        print_info "Coverage: pytest process and the maintenance-tool subprocesses"
    else
        print_info "Coverage: pytest process only (--coverage-subprocess adds the tools)"
    fi
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
    [ "$RUN_STUBTEST" = true ] && [ "$ENABLE_STUBTEST" = true ] && return 0
    [ "$RUN_BANDIT" = true ] && [ "$ENABLE_BANDIT" = true ] && return 0
    [ "$RUN_VULTURE" = true ] && [ "$ENABLE_VULTURE" = true ] && return 0
    return 1
}

# ---- Coverage, as a mode of the pytest gate ----
#
# Every one of these runs `python -m coverage` with COVERAGE_ENV in front, and
# nothing here names a source, an omit or an exclude: what is measured is
# [tool.coverage.*] in pyproject.toml, and these functions only choose when.
# They are called from run_code_checks, so the venv is already active.

# What kind of coverage this run will produce. Asked of coverage rather than
# stated, so the line cannot outlive a change to the configuration it describes.
_coverage_kind() {
    local branch monitoring=false
    branch=$(env "${COVERAGE_ENV[@]}" python -m coverage debug config 2>/dev/null \
        | sed -n 's/^ *branch: *//p' || true)
    case "$branch" in
        True)  printf 'branch coverage' ;;
        False) printf 'line-only coverage' ;;
        *)     printf "coverage of an unreadable kind (branch: '%s')" "$branch" ;;
    esac
    [ "$COVERAGE_SUBPROCESS" = false ] && return 0

    # COVERAGE_CORE=sysmon is a request, and coverage answers a request it cannot
    # meet with a warning to stderr and a silent fall back to the C tracer -- which
    # is the whole cost of this mode, so the two conditions it needs are checked
    # here rather than left to a reader of a log. They are BOTH needed, and the
    # branch value read above is one of them: sys.monitoring cannot measure
    # branches on Python 3.12, so `branch coverage, core sysmon` is a combination
    # that cannot exist, and printing it would be the exact misreport this line is
    # for.
    if python -c 'import sys; raise SystemExit(0 if hasattr(sys, "monitoring") else 1)'
    then
        monitoring=true
    fi
    if [ "$monitoring" = true ] && [ "$branch" = False ]; then
        printf ', core sysmon, subprocesses measured'
    elif [ "$monitoring" = true ]; then
        printf ', so coverage CANNOT use core sysmon and the C tracer runs'
        printf ' (~7.5x, not ~1.2x), subprocesses measured'
    else
        printf ', core sysmon UNAVAILABLE on this Python so the C tracer runs'
        printf ' (~7.5x, not ~1.2x), subprocesses measured'
    fi
}

# Discard the previous run's data. A report that silently included a run from an
# hour ago would be worse than no report, and with per-process data files the
# suffixed ones accumulate rather than overwrite, so this is also what keeps the
# count below honest.
_coverage_erase() {
    env "${COVERAGE_ENV[@]}" python -m coverage erase
}

# Combine, report, and say what the numbers are made of. Returns non-zero if
# coverage produced no data or could not report: a coverage mode that measured
# nothing has failed, exactly as an empty PyMarkdown selection has.
_coverage_report() {
    local report_text='' data_files=0 tool_files=0 subprocess_note='' total_line=''
    local statements branches percent arcs kind measured

    if [ "$COVERAGE_SUBPROCESS" = true ]; then
        # Every measured process writes its own suffixed data file, so counting
        # them is what turns "the tools were measured" from a claim into a number:
        # one file is the pytest process and the rest are children it started.
        # Most are tool runs, but not all -- COVERAGE_PROCESS_START reaches every
        # child, including the freeze, mixin-isolation and docstring checks'
        # subprocesses -- so the count is of measured children, not of tool runs.
        data_files=$(find "$PROJECT_ROOT" -maxdepth 1 -type f \
                          -name "$(basename "$COVERAGE_DATA_FILE").*" | wc -l)
        if [ "$data_files" -eq 0 ]; then
            print_error "Coverage: no data file at all; not even the pytest process was measured"
            return 1
        fi
        tool_files=$((data_files - 1))
        print_info "Coverage data files: ${data_files} (1 pytest process + ${tool_files} measured children)"
        if [ "$tool_files" -eq 0 ]; then
            # Legitimate, and the reason this is reported rather than failed: the
            # tool tests skip when the holdings root lacks the source subset they
            # declare, and a skipped test starts no subprocess. The total is still
            # not --coverage's, because this run is line-only and that one is not.
            print_info "Coverage: no child was measured, so this total covers the pytest process alone -- still line-only, so not comparable with --coverage's branch total"
        fi
        subprocess_note=", ${tool_files} measured children"
        # -q because combine names every file it merges, and three hundred of
        # those would bury the verdicts in a log this project's rule is to read
        # rather than tail. The count above is the number that carries the
        # information those lines would.
        if ! env "${COVERAGE_ENV[@]}" python -m coverage combine -q; then
            print_error "Coverage: combining the ${data_files} data files failed"
            return 1
        fi
    fi

    # Captured rather than piped through tee: with `set -o pipefail` a tee that
    # could not write its file would make a successful report look like a failed
    # one, and this function's whole job is to not misreport.
    if ! report_text=$(env "${COVERAGE_ENV[@]}" python -m coverage report 2>&1); then
        printf '%s\n' "$report_text"
        print_error "Coverage: report failed"
        return 1
    fi
    printf '%s\n' "$report_text"

    total_line=$(printf '%s\n' "$report_text" | grep -E '^TOTAL ' | tail -1 || true)
    if [ -z "$total_line" ]; then
        print_error "Coverage: the report carried no TOTAL line, so it measured nothing"
        return 1
    fi

    # Whether these numbers are branch or line-only is read out of the data file
    # that produced them, not out of the flags that were meant to. This one is not
    # given COVERAGE_ENV: it needs only the data file, and a plain `python -c`
    # carrying COVERAGE_PROCESS_START would start measuring itself and leave an
    # uncombined data file behind. (`python -m coverage <verb>` does not, which is
    # why the other three commands here can take the whole environment.)
    arcs=$(env "COVERAGE_FILE=$COVERAGE_DATA_FILE" python -c 'import os
import coverage
data = coverage.CoverageData(os.environ["COVERAGE_FILE"])
data.read()
print(data.has_arcs())' || true)

    # The two report shapes carry different columns, and the percentage means a
    # different thing in each: line-only is `Stmts Miss Cover`, where Cover is a
    # fraction of statements, while branch is `Stmts Miss Branch BrPart Cover`,
    # where Cover counts executed statements AND taken branches over statements
    # plus branches. Calling the branch figure a percentage of statements would
    # misstate it by several points -- the same execution measured both ways here
    # reports 56% branch and 60% line-only -- so each shape is named for what it is.
    statements=$(printf '%s\n' "$total_line" | awk '{print $2}')
    percent=$(printf '%s\n' "$total_line" | awk '{print $NF}')
    case "$arcs" in
        True)  kind='branch coverage'
               branches=$(printf '%s\n' "$total_line" | awk '{print $4}')
               measured="${percent} of ${statements} statements and ${branches} branches together" ;;
        False) kind='line-only coverage'
               measured="${percent} of ${statements} statements" ;;
        *)     print_error "Coverage: could not read back the data file to say which kind it holds"
               return 1 ;;
    esac

    # "measured", not "passed": no fail_under is configured, so this number
    # cleared no bar and a summary line saying it had would be a lie. Printed
    # before the HTML is written, so that an unwritable htmlcov/ costs the run its
    # HTML and not its number.
    print_success "Coverage measured: ${measured}, ${kind}${subprocess_note}"

    # coverage prints where it wrote the HTML; that line is printed rather than a
    # path this script derived, because the directory is coverage's to choose.
    if ! env "${COVERAGE_ENV[@]}" python -m coverage html; then
        print_error "Coverage: HTML report failed"
        return 1
    fi
    return 0
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

        # One command line, built here, so that what runs and what is printed
        # cannot disagree. Under coverage the workers drop to 0 -- pytest runs the
        # tests in this process, where `coverage run` can see them -- which also
        # makes --dist meaningless, so it goes.
        local pytest_argv=(python -m pytest -q -n "$PYTEST_WORKERS"
                           --dist loadscope tests --mode ns)
        local pytest_note="-n ${PYTEST_WORKERS}"
        local coverage_ok=true
        if [ "$COVERAGE" = true ]; then
            pytest_argv=(env "${COVERAGE_ENV[@]}"
                         python -m coverage run -m pytest -q -n 0 tests --mode ns)
            pytest_note="-n 0 under coverage, $(_coverage_kind)"
            # An unerased data file would leave the report describing this run and
            # an older one at once, which no reader could unpick, so the report is
            # not attempted at all if the erase failed.
            if ! _coverage_erase; then
                print_error "Coverage: could not erase the previous run's data"
                coverage_ok=false
                failed=true
                failed_checks="${failed_checks}Code - Coverage report"$'\n'
            fi
        fi

        case "$holdings_flavor" in
            none)
                print_info "Running pytest (${pytest_note}; no holdings: holdings-free subset only)..."
                ;;
            unresolved)
                print_info "Running pytest (${pytest_note}; holdings selection is invalid, pytest will report it)..."
                ;;
            *)
                print_info "Running pytest (${pytest_note}; holdings: ${holdings_flavor})..."
                ;;
        esac
        if "${pytest_argv[@]}"; then
            print_success "Pytest passed"
        else
            print_error "Pytest failed"
            failed=true
            failed_checks="${failed_checks}Code - Pytest"$'\n'
        fi

        # The report runs whether or not the suite passed: a failing suite still
        # measured something, and the numbers are why the run was asked for.
        if [ "$COVERAGE" = true ] && [ "$coverage_ok" = true ]; then
            if ! _coverage_report; then
                print_error "Coverage report failed"
                failed=true
                failed_checks="${failed_checks}Code - Coverage report"$'\n'
            fi
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

    # Public-API stub validation. `mypy.stubtest` compares the .pyi stubs
    # against the imported runtime package: names, kinds, signatures and
    # defaults. It does NOT type-check the implementation (that is ENABLE_MYPY,
    # permanently false under ground rule 5), and it cannot check that the
    # annotated types are TRUE — the runtime carries no annotations to compare
    # against. The mypy config section in pyproject.toml exists solely for this
    # gate; the allowlist carries the unstubable private-module dynamics, and
    # --ignore-unused-allowlist keeps its host-dependent pylibmc entry from
    # failing on machines where pylibmc is installed.
    if [ "$RUN_STUBTEST" = true ] && [ "$ENABLE_STUBTEST" = true ]; then
        print_info "Running stubtest (public-API stub validation)..."
        if MYPYPATH=src python -m mypy.stubtest \
                --mypy-config-file pyproject.toml \
                --allowlist scripts/stubtest_allowlist.txt \
                --ignore-unused-allowlist \
                pdsfile; then
            print_success "Stubtest passed"
        else
            print_error "Stubtest failed"
            failed=true
            failed_checks="${failed_checks}Code - Stubtest"$'\n'
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

    # Each build streams to the log and is captured at the same time, then read: it is
    # accepted only if it exited 0, wrote the HTML it was asked for, and printed the line
    # docs/conf.py emits when it has compared the source tree against the modules the
    # build documented. Exit status alone would accept a `make` that resolved to nothing
    # at all. `set -o pipefail` is what carries make's status through the tee, and each
    # verdict is printed directly under the build it judges.
    print_info "Building documentation (warnings as errors)..."
    (cd docs && make html SPHINXOPTS="-W") 2>&1 | tee "$warnings_log" || warnings_status=$?
    _sphinx_build_verdict "warnings-as-errors" "$warnings_status" "$warnings_log" \
        docs/_build/html/index.html "$status_file" || warnings_status=1

    print_info "Building documentation (nitpicky, warnings as errors)..."
    (cd docs && make html BUILDDIR=_build/nitpicky SPHINXOPTS="-n -W") 2>&1 \
        | tee "$nitpicky_log" || nitpicky_status=$?
    _sphinx_build_verdict "nitpicky" "$nitpicky_status" "$nitpicky_log" \
        docs/_build/nitpicky/html/index.html "$status_file" || nitpicky_status=1

    deactivate 2>/dev/null || true

    if [ "$warnings_status" -eq 0 ] && [ "$nitpicky_status" -eq 0 ]; then
        local warn_problems nitpick_problems coverage nitpicky_coverage
        warn_problems=$(_sphinx_problem_count "$warnings_log")
        nitpick_problems=$(_sphinx_problem_count "$nitpicky_log")
        coverage=$(_sphinx_coverage_line "$warnings_log")
        nitpicky_coverage=$(_sphinx_coverage_line "$nitpicky_log")
        # The two builds document one tree, so a disagreement means one of them was not
        # the build it claimed to be.
        if [ "$coverage" != "$nitpicky_coverage" ]; then
            print_error "Sphinx builds disagree about coverage: '$coverage' against '$nitpicky_coverage'"
            if [ -n "$status_file" ]; then
                echo "Sphinx - builds disagree about coverage" >> "$status_file"
            fi
            return 1
        fi
        print_success "Sphinx build passed: $warn_problems problem lines under -W and $nitpick_problems under -n -W, and both builds report $coverage"
        return 0
    fi
    return 1
}

# Number of WARNING/ERROR lines a Sphinx build printed. grep reports none by exiting 1,
# which under `set -e` would otherwise take the caller down with it.
_sphinx_problem_count() {
    grep -cE 'WARNING:|ERROR:' "$1" || true
}

# The coverage line docs/conf.py prints once per build, or the empty string if it did not.
_sphinx_coverage_line() {
    { grep -oE 'API reference: [0-9]+ of [0-9]+ modules under .+ documented' "$1" \
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
        print_error "Sphinx $label build failed (exit $status, problem lines: $problems)${coverage:+, $coverage}"
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

    local scan_paths=()
    [ -d "docs/" ] && scan_paths+=("docs/")
    [ -d ".cursor/" ] && scan_paths+=(".cursor/")
    [ -f "README.md" ] && scan_paths+=("README.md")
    [ -f "CONTRIBUTING.md" ] && scan_paths+=("CONTRIBUTING.md")

    # The scan is only as good as its file selection, so the selection is printed
    # and an empty one fails rather than passing over nothing. Two properties of
    # pymarkdown's selection decide what the list holds: it selects by the .md
    # extension, so no .rst page under docs/ and no .mdc rule file is ever read;
    # and a directory argument is NOT recursed into, so a nested Markdown file
    # (such as the .cursor skills') is not read either. Today that leaves
    # README.md and CONTRIBUTING.md.
    print_info "Running PyMarkdown scan (docs/, .cursor/, root *.md)..."
    local file_list file_count
    if ! file_list=$(python -m pymarkdown scan --list-files "${scan_paths[@]}" 2>&1); then
        # Nonzero covers both an empty selection and a scan/config error; either
        # way the gate has measured nothing, so print what pymarkdown said and fail.
        print_error "PyMarkdown file listing failed (empty selection or scan error):"
        printf '%s\n' "$file_list"
        [ -n "$status_file" ] && echo "Markdown - PyMarkdown file listing" >> "$status_file"
        deactivate 2>/dev/null || true
        return 1
    fi
    file_count=$(printf '%s\n' "$file_list" | grep -c .)
    # The empty selection is checked here as well, so the gate does not depend
    # on pymarkdown's return-code scheme (the default scheme exits nonzero on
    # "no files", but that is the tool's choice, and configurable): a selection
    # of zero files means the gate would measure nothing, which is a failure.
    if [ "$file_count" -eq 0 ]; then
        print_error "PyMarkdown selected no files to scan"
        [ -n "$status_file" ] && echo "Markdown - PyMarkdown empty selection" >> "$status_file"
        deactivate 2>/dev/null || true
        return 1
    fi
    print_info "PyMarkdown will scan $file_count file(s):"
    printf '%s\n' "$file_list"

    if python -m pymarkdown scan "${scan_paths[@]}"; then
        print_success "PyMarkdown scan passed ($file_count file(s) scanned)"
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
