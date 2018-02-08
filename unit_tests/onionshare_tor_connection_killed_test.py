#!/usr/bin/env python3
import os, sys, unittest, socket, pytest
from PyQt5 import QtCore, QtWidgets, QtTest

from onionshare import onion, strings, common
from onionshare_gui import *

app = QtWidgets.QApplication(sys.argv)

class OnionShareGuiTest(unittest.TestCase):
    '''Test the OnionShare GUI'''
    @classmethod
    def setUpClass(cls):
        '''Create the GUI'''
        # Create our test file
        testfile = open('/tmp/test.txt', 'w')
        testfile.write('onionshare')
        testfile.close()

        # Start the Onion
        strings.load_strings(common)

        testonion = onion.Onion()
        global qtapp
        qtapp = Application()
        app = OnionShare(testonion, 0, 0)
        cls.gui = OnionShareGui(testonion, qtapp, app, ['/tmp/test.txt'])

    @classmethod
    def tearDownClass(cls):
        '''Clean up after tests'''
        os.remove('/tmp/test.txt')

    @pytest.mark.run(order=1)
    def test_gui_loaded_and_tor_bootstrapped(self):
        '''Test that the GUI actually is shown'''
        self.assertTrue(self.gui.show)

    @pytest.mark.run(order=2)
    def test_server_working_on_start_button_pressed(self):
        '''Test we can start the service'''
        QtTest.QTest.mouseClick(self.gui.server_status.server_button, QtCore.Qt.LeftButton)

        # Should be in SERVER_WORKING state
        self.assertEqual(self.gui.server_status.status, 1)

    @pytest.mark.run(order=3)
    def test_server_is_started(self):
        '''Test that the server has started'''
        # Wait for share to start
        QtTest.QTest.qWait(60000)

        # Should now be in SERVER_STARTED state
        self.assertEqual(self.gui.server_status.status, 2)

    @pytest.mark.run(order=4)
    def test_settings_button_is_disabled(self):
        '''Test that the settings button is disabled'''
        self.assertFalse(self.gui.settings_button.isEnabled())

    @pytest.mark.run(order=5)
    def test_tor_killed_statusbar_message_shown(self):
        '''Test that the status bar message shows Tor was disconnected''' 
        self.gui.app.onion.cleanup(stop_tor=True)
        QtTest.QTest.qWait(2500)
        self.assertTrue(self.gui.status_bar.currentMessage(), strings._('gui_tor_connection_lost', True))

    @pytest.mark.run(order=6)
    def test_server_is_stopped(self):
        '''Test that the server has stopped'''

        # Should now be in SERVER_STOPPED state
        self.assertEqual(self.gui.server_status.status, 0)

    @pytest.mark.run(order=7)
    def test_server_button_is_disabled(self):
        '''Test that the server button is disabled'''
        self.assertFalse(self.gui.server_status.server_button.isEnabled())

    @pytest.mark.run(order=8)
    def test_settings_button_is_enabled(self):
        '''Test that the settings button is enabled'''
        self.assertTrue(self.gui.settings_button.isEnabled())


if __name__ == "__main__":
    unittest.main()
