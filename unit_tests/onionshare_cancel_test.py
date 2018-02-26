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
    def test_file_selection_widget_has_a_file(self):
        '''Test that the number of files in the list is 1'''
        self.assertEqual(self.gui.file_selection.get_num_files(), 1)

    @pytest.mark.run(order=3)
    def test_info_widget_is_visible(self):
        '''Test that the info widget along top of screen is shown because we have a file'''
        self.assertTrue(self.gui.info_widget.isVisible())

    @pytest.mark.run(order=4)
    def test_add_button_is_visible(self):
        '''Test that the Add button is visible'''
        self.assertTrue(self.gui.file_selection.add_button.isVisible())

    @pytest.mark.run(order=5)
    def test_server_working_on_start_button_pressed(self):
        '''Test we can start the service'''
        QtTest.QTest.mouseClick(self.gui.server_status.server_button, QtCore.Qt.LeftButton)

        # Should be in SERVER_WORKING state
        self.assertEqual(self.gui.server_status.status, 1)

        self.assertEqual(self.gui.server_status.server_button.text(), strings._('gui_please_wait', True))

    @pytest.mark.run(order=6)
    def test_add_delete_buttons_now_hidden(self):
        '''Test that the add and delete buttons are hidden when the server starts'''
        self.assertFalse(self.gui.file_selection.add_button.isVisible())
        self.assertFalse(self.gui.file_selection.delete_button.isVisible())

    @pytest.mark.run(order=7)
    def test_settings_button_is_hidden(self):
        '''Test that the settings button is hidden when the server starts'''
        self.assertFalse(self.gui.settings_button.isVisible())

    @pytest.mark.run(order=8)
    def test_cancel_the_share(self):
        '''Test that we can cancel this share before it's started up '''
        QtTest.QTest.mousePress(self.gui.server_status.server_button, QtCore.Qt.LeftButton)
        QtTest.QTest.qWait(1000)
        QtTest.QTest.mouseRelease(self.gui.server_status.server_button, QtCore.Qt.LeftButton)
        self.assertEqual(self.gui.server_status.status, 0)

    @pytest.mark.run(order=9)
    def test_server_status_indicator_says_ready_to_share(self):
        '''Test that the Server Status indicator shows we are Ready To Share'''
        self.assertEquals(self.gui.server_status_label.text(), strings._('gui_status_indicator_stopped', True))

    @pytest.mark.run(order=10)
    def test_web_service_is_stopped(self):
        '''Test that the web server also stopped'''
        # Give the Flask server time to shut down
        QtTest.QTest.qWait(4000)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # We should be closed by now. Fail if not!
        self.assertNotEqual(sock.connect_ex(('127.0.0.1',self.gui.app.port)), 0)

    @pytest.mark.run(order=11)
    def test_add_button_visible_again(self):
        # Add button should be visible again
        self.assertTrue(self.gui.file_selection.add_button.isVisible())


if __name__ == "__main__":
    unittest.main()
