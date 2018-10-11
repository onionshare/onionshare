import os
import requests
import socket
import socks
import zipfile
import json
import shutil

from PyQt5 import QtCore, QtTest

from onionshare import strings
from onionshare.common import Common
from onionshare.settings import Settings
from onionshare.onion import Onion
from onionshare.web import Web
from onionshare_gui import Application, OnionShare, OnionShareGui
from onionshare_gui.mode.share_mode import ShareMode
from onionshare_gui.mode.receive_mode import ReceiveMode


class CommonTests(object):
    @staticmethod
    def set_up(test_settings):
        '''Create GUI with given settings'''
        # Create our test file
        testfile = open('/tmp/test.txt', 'w')
        testfile.write('onionshare')
        testfile.close()

        common = Common()
        common.settings = Settings(common)
        common.define_css()
        strings.load_strings(common)

        # Get all of the settings in test_settings
        test_settings['downloads_dir'] = '/tmp/OnionShare'
        for key, val in common.settings.default_settings.items():
            if key not in test_settings:
                test_settings[key] = val

        # Start the Onion
        testonion = Onion(common)
        global qtapp
        qtapp = Application(common)
        app = OnionShare(common, testonion, True, 0)

        web = Web(common, False, True)
        settings_filename = '/tmp/testsettings.json'
        open(settings_filename, 'w').write(json.dumps(test_settings))

        gui = OnionShareGui(common, testonion, qtapp, app, ['/tmp/test.txt'], settings_filename, True)
        return gui

    @staticmethod
    def tear_down():
        try:
            os.remove('/tmp/test.txt')
            shutil.rmtree('/tmp/OnionShare')
        except:
            pass

    def test_gui_loaded(self):
        '''Test that the GUI actually is shown'''
        self.assertTrue(self.gui.show)

    def test_windowTitle_seen(self):
        '''Test that the window title is OnionShare'''
        self.assertEqual(self.gui.windowTitle(), 'OnionShare')

    def test_settings_button_is_visible(self):
        '''Test that the settings button is visible'''
        self.assertTrue(self.gui.settings_button.isVisible())

    def test_server_status_bar_is_visible(self):
        '''Test that the status bar is visible'''
        self.assertTrue(self.gui.status_bar.isVisible())

    def test_click_mode(self, mode):
        '''Test that we can switch Mode by clicking the button'''
        if type(mode) == ReceiveMode:
            QtTest.QTest.mouseClick(self.gui.receive_mode_button, QtCore.Qt.LeftButton)
            self.assertTrue(self.gui.mode, self.gui.MODE_RECEIVE)
        if type(mode) == ShareMode:
            QtTest.QTest.mouseClick(self.gui.share_mode_button, QtCore.Qt.LeftButton)
            self.assertTrue(self.gui.mode, self.gui.MODE_SHARE)

    def test_click_toggle_history(self, mode):
        '''Test that we can toggle Download or Upload history by clicking the toggle button'''
        currently_visible = mode.history.isVisible()
        QtTest.QTest.mouseClick(mode.toggle_history, QtCore.Qt.LeftButton)
        self.assertEqual(mode.history.isVisible(), not currently_visible)

    def test_history_indicator(self, mode, public_mode):
        '''Test that we can make sure the history is toggled off, do an action, and the indiciator works'''
        # Make sure history is toggled off
        if mode.history.isVisible():
            QtTest.QTest.mouseClick(mode.toggle_history, QtCore.Qt.LeftButton)
            self.assertFalse(mode.history.isVisible())

        # Indicator should not be visible yet
        self.assertFalse(mode.toggle_history.indicator_label.isVisible())

        if type(mode) == ReceiveMode:
            # Upload a file
            files = {'file[]': open('/tmp/test.txt', 'rb')}
            if not public_mode:
                path = 'http://127.0.0.1:{}/{}/upload'.format(self.gui.app.port, mode.web.slug)
            else:
                path = 'http://127.0.0.1:{}/upload'.format(self.gui.app.port)
            response = requests.post(path, files=files)
            QtTest.QTest.qWait(2000)

        if type(mode) == ShareMode:
            # Download files
            if public_mode:
                url = "http://127.0.0.1:{}/download".format(self.gui.app.port)
            else:
                url = "http://127.0.0.1:{}/{}/download".format(self.gui.app.port, self.gui.share_mode.web.slug)
            r = requests.get(url)
            QtTest.QTest.qWait(2000)

        # Indicator should be visible, have a value of "1"
        self.assertTrue(mode.toggle_history.indicator_label.isVisible())
        self.assertEqual(mode.toggle_history.indicator_label.text(), "1")

        # Toggle history back on, indicator should be hidden again
        QtTest.QTest.mouseClick(mode.toggle_history, QtCore.Qt.LeftButton)
        self.assertFalse(mode.toggle_history.indicator_label.isVisible())

    def test_history_is_not_visible(self, mode):
        '''Test that the History section is not visible'''
        self.assertFalse(mode.history.isVisible())

    def test_history_is_visible(self, mode):
        '''Test that the History section is visible'''
        self.assertTrue(mode.history.isVisible())

    def test_server_working_on_start_button_pressed(self, mode):
        '''Test we can start the service'''
        # Should be in SERVER_WORKING state
        QtTest.QTest.mouseClick(mode.server_status.server_button, QtCore.Qt.LeftButton)
        self.assertEqual(mode.server_status.status, 1)

    def test_server_status_indicator_says_starting(self, mode):
        '''Test that the Server Status indicator shows we are Starting'''
        self.assertEquals(mode.server_status_label.text(), strings._('gui_status_indicator_share_working'))

    def test_settings_button_is_hidden(self):
        '''Test that the settings button is hidden when the server starts'''
        self.assertFalse(self.gui.settings_button.isVisible())

    def test_a_server_is_started(self, mode):
        '''Test that the server has started'''
        QtTest.QTest.qWait(2000)
        # Should now be in SERVER_STARTED state
        self.assertEqual(mode.server_status.status, 2)

    def test_a_web_server_is_running(self):
        '''Test that the web server has started'''
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.assertEqual(sock.connect_ex(('127.0.0.1',self.gui.app.port)), 0)

    def test_have_a_slug(self, mode, public_mode):
        '''Test that we have a valid slug'''
        if not public_mode:
            self.assertRegex(mode.server_status.web.slug, r'(\w+)-(\w+)')
        else:
            self.assertIsNone(mode.server_status.web.slug, r'(\w+)-(\w+)')


    def test_url_description_shown(self, mode):
        '''Test that the URL label is showing'''
        self.assertTrue(mode.server_status.url_description.isVisible())

    def test_have_copy_url_button(self, mode):
        '''Test that the Copy URL button is shown'''
        self.assertTrue(mode.server_status.copy_url_button.isVisible())

    def test_server_status_indicator_says_started(self, mode):
        '''Test that the Server Status indicator shows we are started'''
        if type(mode) == ReceiveMode:
            self.assertEquals(mode.server_status_label.text(), strings._('gui_status_indicator_receive_started'))
        if type(mode) == ShareMode:
            self.assertEquals(mode.server_status_label.text(), strings._('gui_status_indicator_share_started'))

    def test_web_page(self, mode, string, public_mode):
        '''Test that the web page contains a string'''
        s = socks.socksocket()
        s.settimeout(60)
        s.connect(('127.0.0.1', self.gui.app.port))

        if not public_mode:
            path = '/{}'.format(mode.server_status.web.slug)
        else:
            path = '/'

        http_request = 'GET {} HTTP/1.0\r\n'.format(path)
        http_request += 'Host: 127.0.0.1\r\n'
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

    def test_history_widgets_present(self, mode):
        '''Test that the relevant widgets are present in the history view after activity has taken place'''
        self.assertFalse(mode.history.empty.isVisible())
        self.assertTrue(mode.history.not_empty.isVisible())

    def test_counter_incremented(self, mode, count):
        '''Test that the counter has incremented'''
        self.assertEquals(mode.history.completed_count, count)

    def test_server_is_stopped(self, mode, stay_open):
        '''Test that the server stops when we click Stop'''
        if type(mode) == ReceiveMode or (type(mode) == ShareMode and stay_open):
            QtTest.QTest.mouseClick(mode.server_status.server_button, QtCore.Qt.LeftButton)
        self.assertEquals(mode.server_status.status, 0)

    def test_web_service_is_stopped(self):
        '''Test that the web server also stopped'''
        QtTest.QTest.qWait(2000)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # We should be closed by now. Fail if not!
        self.assertNotEqual(sock.connect_ex(('127.0.0.1',self.gui.app.port)), 0)

    def test_server_status_indicator_says_closed(self, mode, stay_open):
        '''Test that the Server Status indicator shows we closed'''
        if type(mode) == ReceiveMode:
            self.assertEquals(self.gui.receive_mode.server_status_label.text(), strings._('gui_status_indicator_receive_stopped'))
        if type(mode) == ShareMode:
            if stay_open:
                self.assertEquals(self.gui.share_mode.server_status_label.text(), strings._('gui_status_indicator_share_stopped'))
            else:
                self.assertEquals(self.gui.share_mode.server_status_label.text(), strings._('closing_automatically'))

    # Auto-stop timer tests
    def test_set_timeout(self, mode, timeout):
        '''Test that the timeout can be set'''
        timer = QtCore.QDateTime.currentDateTime().addSecs(timeout)
        mode.server_status.shutdown_timeout.setDateTime(timer)
        self.assertTrue(mode.server_status.shutdown_timeout.dateTime(), timer)

    def test_timeout_widget_hidden(self, mode):
        '''Test that the timeout widget is hidden when share has started'''
        self.assertFalse(mode.server_status.shutdown_timeout_container.isVisible())

    def test_server_timed_out(self, mode, wait):
        '''Test that the server has timed out after the timer ran out'''
        QtTest.QTest.qWait(wait)
        # We should have timed out now
        self.assertEqual(mode.server_status.status, 0)

    # Receive-specific tests
    def test_upload_file(self, public_mode, expected_file):
        '''Test that we can upload the file'''
        files = {'file[]': open('/tmp/test.txt', 'rb')}
        if not public_mode:
            path = 'http://127.0.0.1:{}/{}/upload'.format(self.gui.app.port, self.gui.receive_mode.web.slug)
        else:
            path = 'http://127.0.0.1:{}/upload'.format(self.gui.app.port)
        response = requests.post(path, files=files)
        QtTest.QTest.qWait(2000)
        self.assertTrue(os.path.isfile(expected_file))

    # Share-specific tests
    def test_file_selection_widget_has_a_file(self):
        '''Test that the number of files in the list is 1'''
        self.assertEqual(self.gui.share_mode.server_status.file_selection.get_num_files(), 1)

    def test_deleting_only_file_hides_delete_button(self):
        '''Test that clicking on the file item shows the delete button. Test that deleting the only item in the list hides the delete button'''
        rect = self.gui.share_mode.server_status.file_selection.file_list.visualItemRect(self.gui.share_mode.server_status.file_selection.file_list.item(0))
        QtTest.QTest.mouseClick(self.gui.share_mode.server_status.file_selection.file_list.viewport(), QtCore.Qt.LeftButton, pos=rect.center())
        # Delete button should be visible
        self.assertTrue(self.gui.share_mode.server_status.file_selection.delete_button.isVisible())
        # Click delete, and since there's no more files, the delete button should be hidden
        QtTest.QTest.mouseClick(self.gui.share_mode.server_status.file_selection.delete_button, QtCore.Qt.LeftButton)
        self.assertFalse(self.gui.share_mode.server_status.file_selection.delete_button.isVisible())

    def test_add_a_file_and_delete_using_its_delete_widget(self):
        '''Test that we can also delete a file by clicking on its [X] widget'''
        self.gui.share_mode.server_status.file_selection.file_list.add_file('/etc/hosts')
        QtTest.QTest.mouseClick(self.gui.share_mode.server_status.file_selection.file_list.item(0).item_button, QtCore.Qt.LeftButton)
        self.assertEqual(self.gui.share_mode.server_status.file_selection.get_num_files(), 0)

    def test_file_selection_widget_readd_files(self):
        '''Re-add some files to the list so we can share'''
        self.gui.share_mode.server_status.file_selection.file_list.add_file('/etc/hosts')
        self.gui.share_mode.server_status.file_selection.file_list.add_file('/tmp/test.txt')
        self.assertEqual(self.gui.share_mode.server_status.file_selection.get_num_files(), 2)

    def test_add_delete_buttons_hidden(self):
        '''Test that the add and delete buttons are hidden when the server starts'''
        self.assertFalse(self.gui.share_mode.server_status.file_selection.add_button.isVisible())
        self.assertFalse(self.gui.share_mode.server_status.file_selection.delete_button.isVisible())

    def test_download_share(self, public_mode):
        '''Test that we can download the share'''
        s = socks.socksocket()
        s.settimeout(60)
        s.connect(('127.0.0.1', self.gui.app.port))

        if public_mode:
            path = '/download'
        else:
            path = '{}/download'.format(self.gui.share_mode.web.slug)

        http_request = 'GET {} HTTP/1.0\r\n'.format(path)
        http_request += 'Host: 127.0.0.1\r\n'
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
        QtTest.QTest.qWait(2000)
        self.assertEqual('onionshare', zip.read('test.txt').decode('utf-8'))

    def test_add_button_visible(self):
        '''Test that the add button should be visible'''
        self.assertTrue(self.gui.share_mode.server_status.file_selection.add_button.isVisible())
