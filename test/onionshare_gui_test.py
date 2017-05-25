#!/usr/bin/env python3
import os, sys, unittest, inspect, socket
from PyQt5 import QtCore, QtWidgets, QtGui, QtTest

from onionshare import onion, strings, common
from onionshare_gui import *

app = QtWidgets.QApplication(sys.argv)

class OnionShareGuiTest(unittest.TestCase):
    '''Test the OnionShare GUI'''
    @classmethod
    def setUpClass(cls):
        '''Create the GUI'''
        # Wipe settings
        try:
            os.remove(os.path.expanduser('~/.config/onionshare/onionshare.json'))
        except OSError:
            pass

        # Create our test file
        testfile = open('test/test.txt', 'w')
        testfile.write('onionshare')
        testfile.close()

        # Start the Onion
        strings.load_strings(common)

        testonion = onion.Onion()
        global qtapp
        qtapp = Application()
        app = OnionShare(testonion, 0, 0)
        cls.gui = OnionShareGui(testonion, qtapp, app, ['test/test.txt'])

    @classmethod
    def tearDownClass(cls):
        '''Clean up after tests'''
        os.remove('test/test.txt')

    def test_guiLoaded(self):
        '''Test that the GUI actually is shown'''
        self.assertTrue(self.gui.show)

    def test_version(self):
        '''
        Test that the version is parsed from common.get_version()
        and also in the locale-based version string
        '''
        self.assertIn(self.gui.settings.default_settings.get('version'), strings._('version_string').format(common.get_version()))

    def test_windowTitle(self):
        '''Test that the window title is OnionShare'''
        self.assertEqual(self.gui.windowTitle(), 'OnionShare')

    def test_downloadContainerHidden(self):
        '''Test that the download container is hidden'''
        self.assertTrue(self.gui.downloads_container.isHidden())

    def test_settingsButtonEnabled(self):
        '''Test that the settings button is enabled'''
        self.assertTrue(self.gui.settings_button.isEnabled())

    def test_server_statusBar(self):
        '''Test that the status bar is visible'''
        self.assertTrue(self.gui.status_bar.isVisible())

    def test_fileSelection_hasfile(self):
        '''Test that the number of files in the list is 1'''
        self.assertEqual(self.gui.file_selection.get_num_files(), 1)

    def test_startButtonPress(self):
        '''Test we can start the service, share a file on a valid onion HS, and stop the service again'''
        QtTest.QTest.mouseClick(self.gui.server_status.server_button, QtCore.Qt.LeftButton)
        self.assertEqual(self.gui.server_status.status, 1)
        self.assertFalse(self.gui.file_selection.add_files_button.isEnabled())
        QtTest.QTest.qWait(60000)
        self.assertEqual(self.gui.server_status.status, 2)
        self.assertRegex(self.gui.app.onion_host, r'[a-z2-7].onion')
        self.assertEqual(len(self.gui.app.onion_host), 22)
        self.assertRegex(self.gui.server_status.web.slug, r'(\w+)-(\w+)')
        self.assertTrue(self.gui.server_status.copy_url_button.isVisible())

    def test_stopButtonPress(self):
        '''Test that we can stop the server'''
        QtTest.QTest.mouseClick(self.gui.server_status.server_button, QtCore.Qt.LeftButton)
        self.assertEqual(self.gui.server_status.status, 0)

        # Give the Flask server time to shut down
        QtTest.QTest.qWait(2000)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # We should be closed by now. Fail if not!
        self.assertNotEqual(sock.connect_ex(('127.0.0.1',self.gui.app.port)), 0)


if __name__ == "__main__":
    unittest.main()
