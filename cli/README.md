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

First, make sure you have `tor` and `python3` installed. In Linux, install it through your package manager. In macOS, install it with [Homebrew](https://brew.sh): `brew install tor`. Second, OnionShare is written in python, and you can install the command line version use python's package manager `pip`.

### Requirements

Debian/Ubuntu (APT):
```sh
sudo apt-get install tor python3-pip
```

Arch (Pacman):
```sh
sudo pacman -S tor python-pip
```

CentOS, Red Hat, and Fedora (Yum):
```sh
sudo yum install tor python3 python3-wheel
```

macOS (Homebrew):
```sh
brew install tor python
sudo easy_install pip
```

### Main

#### Installation

Install OnionShare CLI:

```sh
pip install --user onionshare-cli
```

#### Set path

When you install programs with pip and use the --user flag, it installs them into ~/.local/bin, which isn't in your path by default. To add ~/.local/bin to your path automatically for the next time you reopen the terminal or source your shell configuration file, do the following:

First, discover what shell you are using:

```sh
echo $SHELL
```

Then apply the path to your shell file:

bash:

```sh
echo "PATH=\$PATH:~/.local/bin" >> ~/.bashrc
source ~/.bashrc
```

zsh:

```sh
echo "PATH=\$PATH:~/.local/bin" >> ~/.zshrc
source ~/.zshrc
```

#### Usage

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
