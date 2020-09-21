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
