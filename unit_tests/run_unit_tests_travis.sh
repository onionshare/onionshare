#!/bin/bash

for test in `ls -1 | egrep ^onionshare_`; do
  xvfb-run pytest $test -vvv || exit 1
done
