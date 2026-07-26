#!/bin/bash

source ~/pdsfile_runner_secrets
if [ $? -ne 0 ]; then exit -1; fi

if [[ -z ${PDS3_HOLDINGS_DIR+x} ]]; then
    echo "PDS3_HOLDINGS_DIR is not set"
    exit -1
fi
if [[ -z ${PDS4_HOLDINGS_DIR+x} ]]; then
    echo "PDS4_HOLDINGS_DIR is not set"
    exit -1
fi

# Run against the complete real holdings. The suite defaults to the mini fixtures
# (skipping everything when they are absent), so the full-data run selects the
# full flavor explicitly; PDS3_HOLDINGS_DIR / PDS4_HOLDINGS_DIR supply the roots.
export PDSFILE_TEST_HOLDINGS=full

pip3 install --upgrade pip
# requirements.txt is now just "-e ."; the self-hosted suite also needs the dev
# tools (coverage, pytest plugins) so install the dev extra.
pip3 install -e ".[dev]"
echo

echo "================================================================"
echo "CLEAN-INSTALL GATE (runtime-dependency leak)"
echo "================================================================"
echo
# Verify the full pdsfile module surface imports from a bare `pip install .` (no
# extras). Catches a runtime module still importing a dev-only dependency (e.g.
# pytest). Holdings-independent; runs before the data tests so a leak fails fast.
# Builds its own throwaway venv.
bash scripts/clean_install_check.sh
if [ $? -ne 0 ]; then
    echo "**************************************"
    echo "*** CLEAN-INSTALL GATE FAILED      ***"
    echo "**************************************"
    exit -1
fi
echo

echo "================================================================"
echo "PDSFILE NOT-SHELVES-ONLY TESTS"
echo "================================================================"
echo
echo "Test start:" `date`
echo
python -m coverage run -m pytest tests/api/ tests/holdings_maintenance/ tests/pds3file/ tests/rules/pds3/ tests/pds4file/ tests/rules/pds4/ --mode ns
if [ $? -ne 0 ]; then
    echo "**************************************************"
    echo "*** PDSFILE NOT-SHELVES-ONLY FAILED UNIT TESTS ***"
    echo "**************************************************"
    echo
    echo "Test end:" `date`
    exit -1
fi
echo
echo "Test end:" `date`
echo

echo "================================================================"
echo "PDSFILE SHELVES-ONLY TESTS"
echo "================================================================"
echo
echo "Test start:" `date`
echo
# tests/holdings_maintenance/ is deliberately absent here and runs only in the
# not-shelves-only pass above. Those tests drive each tool in its own subprocess,
# so --mode (which only flips use_shelves_only inside *this* pytest process) makes
# no difference to them; running them twice would just double their cost.
python -m coverage run -a -m pytest tests/pds3file/ tests/rules/pds3/ --mode s
if [ $? -ne 0 ]; then
    echo "********************************************"
    echo "*** PDSFILE SHELVES-ONLY FAILED UNIT TESTS ***"
    echo "********************************************"
    echo
    echo "Test end:" `date`
    exit -1
fi
echo
echo "Test end:" `date`
echo

python -m coverage report
if [ $? -ne 0 ]; then exit -1; fi
python -m coverage xml
if [ $? -ne 0 ]; then exit -1; fi

exit 0
