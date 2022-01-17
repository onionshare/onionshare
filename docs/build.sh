#!/bin/bash

VERSION=$(cat ../cli/onionshare_cli/resources/version.txt)

# Supported locales
LOCALES="en fr de el it nb_NO pl pt_BR ru es tr uk"

# Generate English .po files
make gettext
rm -rf gettext > /dev/null
cp -r build/gettext gettext

# Update all .po files for all locales
for LOCALE in $LOCALES; do
    sphinx-intl update -p build/gettext -l $LOCALE
done

# Build all locales
rm -rf build/html build/docs > /dev/null
mkdir -p build/docs/$VERSION

make html
mv build/html build/docs/$VERSION/en

for LOCALE in $LOCALES; do
    make -e SPHINXOPTS="-D language='$LOCALE'" html
    mv build/html build/docs/$VERSION/$LOCALE
done

# Redirect to English by default
echo '<html><head><meta http-equiv="refresh" content="0; url=en/" /><script>document.location="en/"</script></head></html>' > build/docs/$VERSION/index.html

# Redirect to latest version
echo '<html><head><meta http-equiv="refresh" content="0; url='$VERSION'/en/" /><script>document.location="'$VERSION'/en/"</script></head></html>' > build/docs/index.html
