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
    def test_enable_autostop_timer(self):
        '''Test that the Use Auto-stop Timer checkbox can be checked'''
        self.assertTrue(self.gui.server_status.server_shutdown_timeout_checkbox.isVisible())
        self.assertFalse(self.gui.server_status.server_shutdown_timeout_checkbox.isChecked())
        QtTest.QTest.mouseClick(self.gui.server_status.server_shutdown_timeout_checkbox, QtCore.Qt.LeftButton, pos=QtCore.QPoint(2,self.gui.server_status.server_shutdown_timeout_checkbox.height()/2))
        self.assertTrue(self.gui.server_status.server_shutdown_timeout_checkbox.isChecked())

    @pytest.mark.run(order=3)
    def test_set_timeout(self):
        '''Test that the timeout can be set'''
        timer = QtCore.QDateTime.currentDateTime().addSecs(120)
        self.gui.server_status.server_shutdown_timeout.setDateTime(timer)
        self.assertTrue(self.gui.server_status.server_shutdown_timeout.dateTime(), timer)

    @pytest.mark.run(order=4)
    def test_server_working_on_start_button_pressed(self):
        '''Test we can start the service'''
        QtTest.QTest.mouseClick(self.gui.server_status.server_button, QtCore.Qt.LeftButton)
        # Should be in SERVER_WORKING state
        self.assertEqual(self.gui.server_status.status, 1)

    @pytest.mark.run(order=5)
    def test_server_is_started(self):
        '''Test that the server has started'''
        # Wait for share to start
        QtTest.QTest.qWait(60000)

        # Should now be in SERVER_STARTED state
        self.assertEqual(self.gui.server_status.status, 2)

    @pytest.mark.run(order=6)
    def test_server_timed_out(self):
        '''Test that the server has timed out after the timer ran out'''
        QtTest.QTest.qWait(65000)
        # We should have timed out now
        self.assertEqual(self.gui.server_status.status, 0)

    @pytest.mark.run(order=7)
    def test_web_service_is_stopped(self):
        '''Test that the web server also stopped'''
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # We should be closed by now. Fail if not!
        self.assertNotEqual(sock.connect_ex(('127.0.0.1',self.gui.app.port)), 0)

    @pytest.mark.run(order=8)
    def test_status_bar_shows_timeout_message(self):
        '''Test that the GUI's status bar shows the timeout message as the reason for stopping'''
        self.assertEqual(self.gui.status_bar.currentMessage(), strings._('close_on_timeout', True))

if __name__ == "__main__":
    unittest.main()
