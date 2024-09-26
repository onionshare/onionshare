#!/bin/bash
OS=$(uname -s)

if [ "$OS" == "Linux" ]; then
    # setup environment
    cd cli
    poetry install
    echo "OnionShare CLI is installed!"
    cd ../desktop
    poetry install

    # setup tor
    poetry run python ./scripts/get-tor.py linux-x86_64
    echo "Tor browser is installed"

    # compile dependencies
    ./scripts/build-pt-obfs4proxy.sh
    ./scripts/build-pt-snowflake.sh
    ./scripts/build-pt-meek.sh

    # add alias
    echo "alias onionshare='cd $(pwd) && poetry run onionshare'" >> ~/.bash_aliases
    source ~/.bash_aliases

    echo "OnionShare Desktop is now installed"
    echo "Try running 'onionshare' to start onionshare server from source tree"
    echo "Restart a new terminal if the above doesnt work"
    echo "Checkout desktop/README.md for more info"
else
    echo "This script only works in linux distros, Try cli/README.md, desktop/README.md for installation steps"
    exit 1
fi
