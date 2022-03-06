import sys
import os
from datetime import datetime, timedelta

from PySide2 import QtTest


# Force tests to look for resources in the source code tree
sys.onionshare_dev_mode = True

# Let OnionShare know the tests are running, to avoid colliding with settings files
sys.onionshare_test_mode = True


@staticmethod
def qWait(t, qtapp):
    end = datetime.now() + timedelta(milliseconds=t)
    while datetime.now() < end:
        qtapp.processEvents()


# Monkeypatch qWait, because PySide2 doesn't have it
# https://stackoverflow.com/questions/17960159/qwait-analogue-in-pyside
QtTest.QTest.qWait = qWait

# Allow importing onionshare_cli from the source tree
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "cli",
    ),
)

# Create common and qtapp singletons
from onionshare_cli.common import Common
from onionshare import Application

common = Common(verbose=True)
qtapp = Application(common)

# Attach them to sys, so GuiBaseTest can retrieve them
sys.onionshare_common = common
sys.onionshare_qtapp = qtapp
