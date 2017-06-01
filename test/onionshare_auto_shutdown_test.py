#!/usr/bin/env python3
import os, sys, unittest, inspect, socket
from PyQt5 import QtCore, QtWidgets, QtGui, QtTest

sys.path.append('../onionshare')
sys.path.append('../onionshare_gui')

setattr(sys, 'onionshare_dev_mode', True)

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

    def test_downloadShare(self):
        '''
        Test the following:
        1. we can start the service by clicking on the start button,
        2. the server status is now in mode 'working'
        3. we can't add files to the dialog while working/running
        4. the server finally completes starting up and is in mode 'running'
        5. we have a valid onion address in terms of regex and length
        6. we have a valid web slug
        7. we can download the zip
        8. the server stops as soon as we download the zip (assuming config stay_open = False)
        '''
        QtTest.QTest.mouseClick(self.gui.server_status.server_button, QtCore.Qt.LeftButton)
        self.assertEqual(self.gui.server_status.status, 1)
        self.assertFalse(self.gui.file_selection.add_files_button.isEnabled())
        QtTest.QTest.qWait(60000)
        self.assertEqual(self.gui.server_status.status, 2)
        self.assertRegex(self.gui.app.onion_host, r'[a-z2-7].onion')
        self.assertEqual(len(self.gui.app.onion_host), 22)
        self.assertRegex(self.gui.server_status.web.slug, r'(\w+)-(\w+)')

        url = 'http://{0:s}/{1:s}/download'.format(self.gui.app.onion_host, self.gui.server_status.web.slug)
        # Cheap and nasty request to the .onion to save messing with SOCKS proxies and the like
        self.assertEqual(os.system('torify curl {0:s}'.format(url)), 0)

        QtTest.QTest.qWait(3000)

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # We should be closed by now. Fail if not!
        self.assertNotEqual(sock.connect_ex(('127.0.0.1',self.gui.app.port)), 0)


if __name__ == "__main__":
    unittest.main()
