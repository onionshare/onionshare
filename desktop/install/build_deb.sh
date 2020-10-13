#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"
cd $DIR

VERSION=`cat share/version.txt`

# clean up from last build
rm -r deb_dist >/dev/null 2>&1

# build binary package
python3 setup.py --command-packages=stdeb.command bdist_deb

# return install instructions if onionshare builds properly
if [[ $? -eq 0 ]]; then
	# The build process in stdeb's util.py renames .dev to ~dev
	# Adjust it here for the purposes of displaying the right filename
	VERSION="${VERSION/.dev/~dev}"
	echo ""
	echo "To install, run:"
	echo "sudo dpkg -i deb_dist/onionshare_$VERSION-1_all.deb"
else
	echo "OnionShare failed to build!"
	exit 1
fi
