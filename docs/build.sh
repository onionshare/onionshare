#!/bin/bash

# Supported locales
LOCALES="ar ca zh_CN zh_TW da nl en fr de el is ga it ja nb fa pl pt_BR pt_PT ro ru sr@latin es sv te tr uk"

# Generate English .po files
make gettext

# Update all .po files for all locales
for LOCALE in $LOCALES; do
    sphinx-intl update -p build/gettext -l $LOCALE
done

# Build all locales
rm -rf build/html build/localized_html > /dev/null
mkdir -p build/localized_html

make html
mv build/html build/localized_html/en

for LOCALE in $LOCALES; do
    make -e SPHINXOPTS="-D language='$LOCALE'" html
    mv build/html build/localized_html/$LOCALE
done

# Redirect to English by default
echo '<html><head><meta http-equiv="refresh" content="0; url=en/" /><script>document.location="en/"</script></head></html>' > build/localized_html/index.html