import json
import os
import requests
import socks

from PyQt5 import QtCore, QtTest

from onionshare import strings
from onionshare.common import Common
from onionshare.settings import Settings
from onionshare.onion import Onion
from onionshare.web import Web
from onionshare_gui import Application, OnionShare, OnionShareGui
from onionshare_gui.mode.share_mode import ShareMode
from onionshare_gui.mode.receive_mode import ReceiveMode

from .GuiBaseTest import GuiBaseTest

class TorGuiBaseTest(GuiBaseTest):
    @staticmethod
    def set_up(test_settings):
        '''Create GUI with given settings'''
        # Create our test file
        testfile = open('/tmp/test.txt', 'w')
        testfile.write('onionshare')
        testfile.close()

        # Create a test dir and files
        if not os.path.exists('/tmp/testdir'):
            testdir = os.mkdir('/tmp/testdir')
        testfile = open('/tmp/testdir/test.txt', 'w')
        testfile.write('onionshare')
        testfile.close()

        common = Common()
        common.settings = Settings(common)
        common.define_css()
        strings.load_strings(common)

        # Get all of the settings in test_settings
        test_settings['connection_type'] = 'automatic'
        test_settings['data_dir'] = '/tmp/OnionShare'
        for key, val in common.settings.default_settings.items():
            if key not in test_settings:
                test_settings[key] = val

        # Start the Onion
        testonion = Onion(common)
        global qtapp
        qtapp = Application(common)
        app = OnionShare(common, testonion, False, 0)

        web = Web(common, False, False)
        open('/tmp/settings.json', 'w').write(json.dumps(test_settings))

        gui = OnionShareGui(common, testonion, qtapp, app, ['/tmp/test.txt', '/tmp/testdir'], '/tmp/settings.json', False)
        return gui

    def history_indicator(self, mode, public_mode):
        '''Test that we can make sure the history is toggled off, do an action, and the indiciator works'''
        # Make sure history is toggled off
        if mode.history.isVisible():
            QtTest.QTest.mouseClick(mode.toggle_history, QtCore.Qt.LeftButton)
            self.assertFalse(mode.history.isVisible())

        # Indicator should not be visible yet
        self.assertFalse(mode.toggle_history.indicator_label.isVisible())

        # Set up connecting to the onion
        (socks_address, socks_port) = self.gui.app.onion.get_tor_socks_port()
        session = requests.session()
        session.proxies = {}
        session.proxies['http'] = 'socks5h://{}:{}'.format(socks_address, socks_port)

        if type(mode) == ReceiveMode:
            # Upload a file
            files = {'file[]': open('/tmp/test.txt', 'rb')}
            if not public_mode:
                path = 'http://{}/{}/upload'.format(self.gui.app.onion_host, mode.web.slug)
            else:
                path = 'http://{}/upload'.format(self.gui.app.onion_host)
            response = session.post(path, files=files)
            QtTest.QTest.qWait(4000)

        if type(mode) == ShareMode:
            # Download files
            if public_mode:
                path = "http://{}/download".format(self.gui.app.onion_host)
            else:
                path = "http://{}/{}/download".format(self.gui.app.onion_host, mode.web.slug)
            response = session.get(path)
            QtTest.QTest.qWait(4000)

        # Indicator should be visible, have a value of "1"
        self.assertTrue(mode.toggle_history.indicator_label.isVisible())
        self.assertEqual(mode.toggle_history.indicator_label.text(), "1")

        # Toggle history back on, indicator should be hidden again
        QtTest.QTest.mouseClick(mode.toggle_history, QtCore.Qt.LeftButton)
        self.assertFalse(mode.toggle_history.indicator_label.isVisible())

    def have_an_onion_service(self):
        '''Test that we have a valid Onion URL'''
        self.assertRegex(self.gui.app.onion_host, r'[a-z2-7].onion')

    def web_page(self, mode, string, public_mode):
        '''Test that the web page contains a string'''
        (socks_address, socks_port) = self.gui.app.onion.get_tor_socks_port()
        socks.set_default_proxy(socks.SOCKS5, socks_address, socks_port)
        s = socks.socksocket()
        s.settimeout(60)
        s.connect((self.gui.app.onion_host, 80))
        if not public_mode:
            path = '/{}'.format(mode.server_status.web.slug)
        else:
            path = '/'
        http_request = 'GET {} HTTP/1.0\r\n'.format(path)
        http_request += 'Host: {}\r\n'.format(self.gui.app.onion_host)
        http_request += '\r\n'
        s.sendall(http_request.encode('utf-8'))
        with open('/tmp/webpage', 'wb') as file_to_write:
            while True:
               data = s.recv(1024)
               if not data:
                   break
               file_to_write.write(data)
            file_to_write.close()
        f = open('/tmp/webpage')
        self.assertTrue(string in f.read())
        f.close()

    def have_copy_url_button(self, mode, public_mode):
        '''Test that the Copy URL button is shown and that the clipboard is correct'''
        self.assertTrue(mode.server_status.copy_url_button.isVisible())

        QtTest.QTest.mouseClick(mode.server_status.copy_url_button, QtCore.Qt.LeftButton)
        clipboard = self.gui.qtapp.clipboard()
        if public_mode:
            self.assertEqual(clipboard.text(), 'http://{}'.format(self.gui.app.onion_host))
        else:
            self.assertEqual(clipboard.text(), 'http://{}/{}'.format(self.gui.app.onion_host, mode.server_status.web.slug))


    # Stealth tests
    def copy_have_hidserv_auth_button(self, mode):
        '''Test that the Copy HidservAuth button is shown'''
        self.assertTrue(mode.server_status.copy_hidservauth_button.isVisible())

    def hidserv_auth_string(self):
        '''Test the validity of the HidservAuth string'''
        self.assertRegex(self.gui.app.auth_string, r'HidServAuth {} [a-zA-Z1-9]'.format(self.gui.app.onion_host))



    # Miscellaneous tests
    def tor_killed_statusbar_message_shown(self, mode):
        '''Test that the status bar message shows Tor was disconnected'''
        self.gui.app.onion.c = None
        QtTest.QTest.qWait(1000)
        self.assertTrue(mode.status_bar.currentMessage(), strings._('gui_tor_connection_lost'))
