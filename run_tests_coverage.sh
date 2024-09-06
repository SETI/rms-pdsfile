#!/bin/bash
echo "Clean up previous coverage record"
coverage erase
if [ $? -ne 0 ]; then exit -1; fi

# If --update is given, we will update the opus products golden copies
if [  -n "$1"  ] && [ "$1" != "--update" ]
then
    echo "Exiting the program. Only options: None or '--update'"
    exit -1
fi

echo "Run with use shelves on PDS3"
coverage run --parallel-mode -m pytest pdsfile/pds3file/tests/ \
    pdsfile/pds3file/rules/*.py --mode s $1
if [ $? -ne 0 ]; then exit -1; fi
echo "Run with no shelves on PDS3"
coverage run --parallel-mode -m pytest pdsfile/pds3file/tests/ \
    pdsfile/pds3file/rules/*.py --mode ns $1
if [ $? -ne 0 ]; then exit -1; fi
echo "Run with no shelves on PDS4"
coverage run --parallel-mode -m pytest pdsfile/pds4file/tests/ \
    pdsfile/pds4file/rules/*.py --mode ns $1
if [ $? -ne 0 ]; then exit -1; fi

echo "Combine results from all modes"
coverage combine
echo "Generate html"
coverage html
echo "Report coverage"
coverage report
