#!/usr/bin/env python3
import os, sys, unittest, socket, pytest, zipfile
from PyQt5 import QtCore, QtWidgets, QtTest

from onionshare import onion, strings, common, socks
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
        os.remove('/tmp/download.zip')

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
    def test_a_server_is_started(self):
        '''Test that the server has started'''
        # Wait for share to start
        QtTest.QTest.qWait(60000)

        # Should now be in SERVER_STARTED state
        self.assertEqual(self.gui.server_status.status, 2)

    @pytest.mark.run(order=4)
    def test_a_web_server_is_running(self):
        '''Test that the web server has started'''
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # We should be closed by now. Fail if not!
        self.assertEqual(sock.connect_ex(('127.0.0.1',self.gui.app.port)), 0)

    @pytest.mark.run(order=5)
    def test_have_an_onion_service(self):
        '''Test that we have a valid Onion URL'''
        self.assertRegex(self.gui.app.onion_host, r'[a-z2-7].onion')
        self.assertEqual(len(self.gui.app.onion_host), 22)

    @pytest.mark.run(order=6)
    def test_have_a_slug(self):
        '''Test that we have a valid slug'''
        self.assertRegex(self.gui.server_status.web.slug, r'(\w+)-(\w+)')

    @pytest.mark.run(order=7)
    def test_download_share(self):
        '''Test that we can download the share'''
        (socks_address, socks_port) = self.gui.app.onion.get_tor_socks_port()
        socks.set_default_proxy(socks.SOCKS5, socks_address, socks_port)

        s = socks.socksocket()
        s.settimeout(15) # 15 second timeout
        s.connect((self.gui.app.onion_host, 80))

        http_request = 'GET {}/download HTTP/1.0\r\n'.format(self.gui.server_status.web.slug)
        http_request += 'Host: {}\r\n'.format(self.gui.app.onion_host)
        http_request += '\r\n'
        s.sendall(http_request.encode('utf-8'))

        with open('/tmp/download.zip', 'wb') as file_to_write:
            while True:
               data = s.recv(1024)
               if not data:
                   break
               file_to_write.write(data)
            file_to_write.close()

        zip = zipfile.ZipFile('/tmp/download.zip')
        self.assertEquals('onionshare', zip.read('test.txt').decode('utf-8'))

    @pytest.mark.run(order=8)
    def test_server_is_stopped(self):
        '''Test that the server stopped automatically when we downloaded the share'''
        QtTest.QTest.qWait(1000)
        self.assertEqual(self.gui.server_status.status, 0)

    @pytest.mark.run(order=9)
    def test_web_service_is_stopped(self):
        '''Test that the web server also stopped'''
        # Give the Flask server time to shut down
        QtTest.QTest.qWait(4000)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # We should be closed by now. Fail if not!
        self.assertNotEqual(sock.connect_ex(('127.0.0.1',self.gui.app.port)), 0)

if __name__ == "__main__":
    unittest.main()
