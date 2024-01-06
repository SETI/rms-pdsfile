#!/bin/bash
echo "Clean up previous coverage record"
coverage erase
count=1
numOfModes=2
declare -a mode_arr
mode_arr=( [1]="s" [2]="ns" )
declare -a mode_desc
mode_desc=( [1]="use shelves" [2]="no shelves" )

while [ $count -le $numOfModes ]
do
    echo "Run with ${mode_desc[$count]}"
    coverage run --parallel-mode -m --source=pdsfile pytest pdsfile/pds3file/tests/ \
    pdsfile/pds3file/rules/*.py pdsfile/pds4file/tests/ pdsfile/pds4file/rules/*.py --mode ${mode_arr[$count]}

    count=`expr $count + 1`
done
echo "Combine results from all modes"
coverage combine
echo "Generate html"
coverage html
echo "Report coverage"
coverage report
