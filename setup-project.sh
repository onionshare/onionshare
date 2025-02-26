#!/bin/bash
OS=$(uname -s)

if [ "$OS" == "Linux" ]; then
    # Check poetry installation and exit if no installation found.
    if ! command -v poetry 2>&1 >/dev/null
    then
        echo "Could not detect Poetry installation. Please make sure you install Poetry first.
        See https://python-poetry.org/docs/#installation or run pip3 install poetry"
        exit 1
    fi

    # setup environment
    cd cli
    poetry install
    echo "OnionShare CLI is installed!"
    cd ../desktop
    poetry install

    # setup tor
    poetry run python ./scripts/get-tor.py linux-x86_64
    echo "Tor is installed"

    # compile dependencies
    ./scripts/build-pt-obfs4proxy.sh
    ./scripts/build-pt-snowflake.sh
    ./scripts/build-pt-meek.sh

    # add alias
    echo "alias onionshare='cd $(pwd) && poetry run onionshare'" >> ~/.bash_aliases
    echo "alias onionshare-cli='cd $(pwd) && poetry run onionshare-cli'" >> ~/.bash_aliases
    source ~/.bash_aliases

    echo "OnionShare Desktop is now installed"
    echo "Try running 'onionshare' to start onionshare server from source tree"
    echo "Restart a new terminal if the above doesnt work"
    echo "Checkout desktop/README.md for more info"
else
    echo "This script only works in linux distros, Try cli/README.md, desktop/README.md for installation steps"
    exit 1
fi
