import os, sys

# Load onionshare module and resources from the source code tree
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.onionshare_dev_mode = True
