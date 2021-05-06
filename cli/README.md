```
╭───────────────────────────────────────────╮
│    *            ▄▄█████▄▄            *    │
│               ▄████▀▀▀████▄     *         │
│              ▀▀█▀       ▀██▄              │
│      *      ▄█▄          ▀██▄             │
│           ▄█████▄         ███        -+-  │
│             ███         ▀█████▀           │
│             ▀██▄          ▀█▀             │
│         *    ▀██▄       ▄█▄▄     *        │
│ *             ▀████▄▄▄████▀               │
│                 ▀▀█████▀▀                 │
│             -+-                     *     │
│   ▄▀▄               ▄▀▀ █                 │
│   █ █     ▀         ▀▄  █                 │
│   █ █ █▀▄ █ ▄▀▄ █▀▄  ▀▄ █▀▄ ▄▀▄ █▄▀ ▄█▄   │
│   ▀▄▀ █ █ █ ▀▄▀ █ █ ▄▄▀ █ █ ▀▄█ █   ▀▄▄   │
│                                           │
│          https://onionshare.org/          │
╰───────────────────────────────────────────╯
```

## Installing OnionShare CLI

First, make sure you have `tor` installed. In Linux, install it through your package manager. In macOS, install it with [Homebrew](https://brew.sh): `brew install tor`.

Then install OnionShare CLI:

```sh
pip install onionshare-cli
```

Then run it with:

```sh
onionshare-cli --help
```

## Developing OnionShare CLI

You must have python3 and [poetry](https://python-poetry.org/) installed.

Install dependencies with poetry:

```sh
poetry install
```

To run from the source tree:

```sh
poetry run onionshare-cli
```

To run tests:

```sh
poetry run pytest -v ./tests
```

## Build a wheel package

```sh
poetry build
```

This will create `dist/onionshare_cli-$VERSION-py3-none-any.whl`.
