#!/bin/bash

# Run OnionShare desktop, allowing you to use command-line arguments

SCRIPTS_DIR="$( cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd )"
cd $SCRIPTS_DIR

cd ../src
python -c "import onionshare; onionshare.main()" $@