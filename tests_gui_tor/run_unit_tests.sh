#!/bin/bash

for test in `ls -1 | egrep ^onionshare_`; do
  pytest $test -vvv || exit 1
done
