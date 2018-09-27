#!/bin/bash

for test in `ls -1 | egrep ^onionshare_`; do
  py.test-3 $test -vvv || exit 1
done
