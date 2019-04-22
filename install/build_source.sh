#!/bin/bash

# The script builds a source package
# See https://github.com/micahflee/onionshare/blob/develop/BUILD.md#source-package

# Usage
display_usage() {
	echo "Usage: $0 [tag]"
}

if [ $# -lt 1 ]
then
  display_usage
  exit 1
fi

# Input validation
TAG=$1

if [ "${TAG:0:1}" != "v" ]
then
  echo "Tag must start with 'v' character"
  exit 1
fi

VERSION=${TAG:1}

# Make sure tag exists
git tag | grep "^$TAG\$"
if [ $? -ne 0 ]
then
  echo "Tag does not exist"
  exit 1
fi

# Clone source
mkdir -p build/source
mkdir -p dist
cd build/source
git clone https://github.com/micahflee/onionshare.git
cd onionshare

# Verify tag
git tag -v $TAG 2> ../verify.txt
if [ $? -ne 0 ]
then
  echo "Tag does not verify"
  exit 1
fi
cat ../verify.txt |grep "using RSA key 927F419D7EC82C2F149C1BD1403C2657CD994F73"
if [ $? -ne 0 ]
then
  echo "Tag signed with wrong key"
  exit 1
fi
cat ../verify.txt |grep "^gpg: Good signature from"
if [ $? -ne 0 ]
then
  echo "Tag verification missing 'Good signature from'"
  exit 1
fi

# Checkout code
git checkout $TAG

# Delete .git, compress, and PGP sign
cd ..
rm -rf onionshare/.git
tar -cf onionshare-$VERSION.tar.gz onionshare/
gpg -a --detach-sign onionshare-$VERSION.tar.gz

# Move source package to dist
cd ../..
mv build/source/onionshare-$VERSION.tar.gz dist
mv build/source/onionshare-$VERSION.tar.gz.asc dist

# Clean up
rm -rf build/source/onionshare
rm build/source/verify.txt

echo "Source package complete, files are in dist"
