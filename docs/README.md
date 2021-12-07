# OnionShare Documentation

All these commands must be run from the `docs` folder.

You must have the python dependencies installed to build the docs:

```sh
poetry install
```

To build HTML docs:

```sh
poetry run make html
```

Then open `docs/build/html/index.html` in a browser to see it.

To update all of the translations and build all the html, run:

```sh
poetry run ./build.sh
```

You will end up with the documentation in all supported locales in `docs/localized_html`.

Here's how preparing translations works:

```sh
# Generate .po files in build/gettext
make gettext

# Create a new blank German locale in source/locale, based on .po files
sphinx-intl update -p build/gettext -l de

# Build German translated document
make -e SPHINXOPTS="-D language='de'" html
```

## Discoving which translations are >90% complete

Each OnionShare release should only include a language if >90% of the strings have been translated into it. The script `check-weblate.py` script can be used to make a few hundreds weblate API requests to determine this for you automatically. It requires using your weblate API key, which you can find in your [user profile](https://hosted.weblate.org/accounts/profile/#api).

```
$ poetry run ./check-weblate.py $WEBLATE_API_KEY
GET https://hosted.weblate.org/api/projects/onionshare/languages/
GET https://hosted.weblate.org/api/translations/onionshare/translations/hr/
GET https://hosted.weblate.org/api/translations/onionshare/translations/eo/
GET https://hosted.weblate.org/api/translations/onionshare/translations/ja/
<...snip...>
GET https://hosted.weblate.org/api/translations/onionshare/doc-tor/wo/ | error 404
GET https://hosted.weblate.org/api/translations/onionshare/doc-tor/ar/
GET https://hosted.weblate.org/api/translations/onionshare/doc-tor/it/

App translations >= 100%
=======================
English (en), 100.0%

App translations >= 90%
=======================
Arabic (ar), 95.0%
Bengali (bn), 95.0%
Catalan (ca), 93.5%
Chinese (Simplified) (zh_Hans), 98.0%
Chinese (Traditional) (zh_Hant), 95.0%
Croatian (hr), 95.0%
Danish (da), 94.5%
Dutch (nl), 92.6%
French (fr), 98.0%
Galician (gl), 97.5%
German (de), 95.0%
Greek (el), 98.0%
Icelandic (is), 98.0%
Indonesian (id), 98.0%
Italian (it), 94.5%
Japanese (ja), 94.5%
Kurdish (Central) (ckb), 94.5%
Norwegian Bokmål (nb_NO), 98.0%
Polish (pl), 95.0%
Portuguese (Brazil) (pt_BR), 95.0%
Portuguese (Portugal) (pt_PT), 92.6%
Russian (ru), 95.0%
Serbian (latin) (sr_Latn), 95.0%
Slovak (sk), 94.5%
Spanish (es), 98.0%
Swedish (sv), 94.5%
Turkish (tr), 98.0%
Ukrainian (uk), 98.0%

App translations >= 80%
=======================
Finnish (fi), 88.1%

Docs translations >= 100%
========================
English (en), 100.0%, 100.0%, 100.0%, 100.0%, 100.0%, 100.0%, 100.0%, 100.0%, 100.0%
Turkish (tr), 100.0%, 100.0%, 100.0%, 100.0%, 100.0%, 100.0%, 100.0%, 100.0%, 100.0%
Ukrainian (uk), 100.0%, 100.0%, 100.0%, 100.0%, 100.0%, 100.0%, 100.0%, 100.0%, 100.0%

Docs translations >= 90%
========================


Docs translations >= 80%
========================
German (de), 90.6%, 100.0%, 82.1%, 100.0%, 100.0%, 100.0%, 100.0%, 100.0%, 100.0%
Greek (el), 90.6%, 100.0%, 82.1%, 100.0%, 100.0%, 100.0%, 100.0%, 100.0%, 100.0%
Russian (ru), 90.6%, 100.0%, 82.1%, 100.0%, 100.0%, 100.0%, 100.0%, 100.0%, 100.0%
Spanish (es), 90.6%, 100.0%, 82.1%, 100.0%, 100.0%, 100.0%, 100.0%, 100.0%, 100.0%
```
