#!/bin/bash

for test in `ls -1 | egrep ^local_`; do
  pytest $test -vvv || exit 1
done
