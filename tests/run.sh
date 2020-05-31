#!/bin/bash

# The script runs python tests
# Firstly, all CLI tests are run
# Then, all the GUI tests are run individually
# to avoid segmentation fault

PARAMS=""

while [ ! $# -eq 0 ]
do
	case "$1" in
		--rungui)
			PARAMS="$PARAMS --rungui"
			;;
		--runtor)
			PARAMS="$PARAMS --runtor"
			;;
	esac
	shift
done

pytest $PARAMS -vvv ./tests/test_cli*.py || exit 1
for filename in ./tests/test_gui_*.py; do
	pytest $PARAMS -vvv --no-qt-log $filename || exit 1
done
