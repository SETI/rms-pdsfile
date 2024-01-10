#!/bin/bash

source ~/pdsfile_runner_secrets
if [ $? -ne 0 ]; then exit -1; fi

if [[ ! -v PDS_HOLDINGS_DIR ]]; then
    echo "PDS_HOLDINGS_DIR is not set"
    exit -1
fi
if [[ ! -v PDS4_HOLDINGS_DIR ]]; then
    echo "PDS_HOLDINGS_DIR is not set"
    exit -1
fi

pip3 install --upgrade pip
pip3 install -r requirements.txt
echo

echo "================================================================"
echo "PDSFILE NOT-SHELVES-ONLY TESTS"
echo "================================================================"
echo
echo "Test start:" `date`
echo
coverage run -m pytest pdsfile/pds3file/tests/ pdsfile/pds3file/rules/*.py pdsfile/pds4file/tests/ pdsfile/pds4file/rules/*.py --mode ns
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
coverage run -a -m pytest pdsfile/pds3file/tests/ pdsfile/pds3file/rules/*.py pdsfile/pds4file/tests/ pdsfile/pds4file/rules/*.py --mode s
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

coverage report
if [ $? -ne 0 ]; then exit -1; fi
coverage xml
if [ $? -ne 0 ]; then exit -1; fi

exit 0
