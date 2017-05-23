#!/usr/bin/env python3
import os, sys, unittest, inspect, time
from PyQt5 import QtCore, QtWidgets, QtGui, QtTest

sys.path.append('../onionshare')
sys.path.append('../onionshare_gui')

from onionshare import onion, strings, common
from onionshare_gui import *

app = QtWidgets.QApplication(sys.argv)

class OnionShareGuiTest(unittest.TestCase):
    '''Test the OnionShare GUI'''
    @classmethod
    def setUpClass(cls):
        '''Create the GUI'''

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
        '''
        Test that we can start the service by clicking on the start button,
        the add_files button is now disabled while the service starts up,
        and that we can get a valid .onion address and slug returned once 
        it's ready
        '''
        QtTest.QTest.mouseClick(self.gui.server_status.server_button, QtCore.Qt.LeftButton)
        self.assertEqual(self.gui.server_status.status, 1)
        self.assertFalse(self.gui.file_selection.add_files_button.isEnabled())
        time.sleep(60)
        self.assertRegex(self.gui.app.onion_host, r'[a-z0-9].onion')
        self.assertRegex(self.gui.server_status.web.slug, r'(\w+)-(\w+)')

if __name__ == "__main__":
    unittest.main()
