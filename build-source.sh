#!/bin/bash

# The script builds a source package

# The exit function after echo something
_exit() {
    echo $1 && exit 1
}

# This method will check the previous command
# and exit if it was insuccessfull
_check_prev(){
    [ $? -ne 0 ] && _exit $1
}

# Usage
[ $# -lt 1 ] && _exit "Usage: $0 [tag]"

# Input validation
TAG=$1
[ "${TAG:0:1}" != "v" ] && _exit "Tag must start with 'v' character"

VERSION=${TAG:1}

# Make sure tag exists
git tag | grep "^$TAG\$"
_check_prev "Tag does not exist"

# Clone source
mkdir -p build/source
mkdir -p dist
cd build/source
git clone https://github.com/onionshare/onionshare.git
cd onionshare

# Verify tag
git tag -v $TAG 2> ../verify.txt
_check_prev "Tag does not exist"

cat ../verify.txt | grep "using RSA key 927F419D7EC82C2F149C1BD1403C2657CD994F73"
_check_prev "Tag signed with wrong key"

cat ../verify.txt | grep "^gpg: Good signature from"
_check_prev "Tag verification missing 'Good signature from'"

# Checkout code
git checkout $TAG

# Delete .git, compress, and PGP sign
cd ..
rm -rf onionshare/.git
tar -cf onionshare-$VERSION.tar.gz onionshare/

# Move source package to dist
cd ../..
mv build/source/onionshare-$VERSION.tar.gz dist

# Clean up
rm -rf build/source/onionshare
rm build/source/verify.txt

echo "Source package complete, file in dist"
