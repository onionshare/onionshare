# OnionShare Documentation

All these commands must be run from the `docs` folder.

You must have the python dependencies installed to build the docs:

```sh
pip3 install --user requirements.txt
```

To build HTML docs:

```sh
make html
```

Then open `docs/build/html/index.html` in a browser to see it.

To prepare translations:

```sh
# Generate .po files in build/gettext 
make gettext

# Create a new blank German locale in source/locale, based on .po files
sphinx-intl update -p build/gettext -l de

# Build German translated document
make -e SPHINXOPTS="-D language='de'" html
```
