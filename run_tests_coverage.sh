#!/bin/bash
echo "Clean up previous coverage record"
coverage erase
if [ $? -ne 0 ]; then exit -1; fi

echo "Run with use shelves on PDS3"
coverage run --parallel-mode -m pytest pdsfile/pds3file/tests/ \
    pdsfile/pds3file/rules/*.py --mode s
if [ $? -ne 0 ]; then exit -1; fi
echo "Run with no shelves on PDS3"
coverage run --parallel-mode -m pytest pdsfile/pds3file/tests/ \
    pdsfile/pds3file/rules/*.py --mode ns
if [ $? -ne 0 ]; then exit -1; fi
echo "Run with no shelves on PDS4"
coverage run --parallel-mode -m pytest pdsfile/pds4file/tests/ \
    pdsfile/pds4file/rules/*.py --mode ns
if [ $? -ne 0 ]; then exit -1; fi

echo "Combine results from all modes"
coverage combine
echo "Generate html"
coverage html
echo "Report coverage"
coverage report
