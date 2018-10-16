import json
import os
import sys
from PyQt5 import QtWidgets

from onionshare import strings
from onionshare.common import Common
from onionshare.settings import Settings
from onionshare.onion import Onion
from onionshare.web import Web
from onionshare_gui import Application, OnionShare
from onionshare_gui.settings_dialog import SettingsDialog

class SettingsGuiBaseTest(object):
    @staticmethod
    def set_up(test_settings, settings_filename):
        '''Create the GUI'''
        # Create our test file
        testfile = open('/tmp/test.txt', 'w')
        testfile.write('onionshare')
        testfile.close()

        common = Common()
        common.settings = Settings(common)
        common.define_css()
        strings.load_strings(common)

        # Start the Onion
        testonion = Onion(common)
        global qtapp
        qtapp = Application(common)
        app = OnionShare(common, testonion, True, 0)

        web = Web(common, False, True)

        for key, val in common.settings.default_settings.items():
            if key not in test_settings:
                test_settings[key] = val

        open('/tmp/{}.json'.format(settings_filename), 'w').write(json.dumps(test_settings))

        gui = SettingsDialog(common, testonion, qtapp, '/tmp/{}.json'.format(settings_filename), True)
        return gui


    @staticmethod
    def tear_down():
        '''Clean up after tests'''
        os.remove('/tmp/settings.json')
