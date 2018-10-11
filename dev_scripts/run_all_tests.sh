#!/bin/bash
ROOT="$( dirname $(cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd ))"

# CLI tests
cd $ROOT
pytest tests/

# Local GUI tests
cd $ROOT/tests_gui_local
./run_unit_tests.sh

# Tor GUI tests
cd $ROOT/tests_gui_tor
./run_unit_tests.sh
