import json
import os
import requests
import shutil
import socket
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


class GuiBaseTest(object):
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
        testfile = open('/tmp/testdir/test', 'w')
        testfile.write('onionshare')
        testfile.close()

        common = Common()
        common.settings = Settings(common)
        common.define_css()
        strings.load_strings(common)

        # Get all of the settings in test_settings
        test_settings['data_dir'] = '/tmp/OnionShare'
        for key, val in common.settings.default_settings.items():
            if key not in test_settings:
                test_settings[key] = val

        # Start the Onion
        testonion = Onion(common)
        global qtapp
        qtapp = Application(common)
        app = OnionShare(common, testonion, True, 0)

        web = Web(common, False, True)
        open('/tmp/settings.json', 'w').write(json.dumps(test_settings))

        gui = OnionShareGui(common, testonion, qtapp, app, ['/tmp/test.txt', '/tmp/testdir'], '/tmp/settings.json', True)
        return gui

    @staticmethod
    def tear_down():
        '''Clean up after tests'''
        try:
            os.remove('/tmp/test.txt')
            os.remove('/tmp/settings.json')
            os.remove('/tmp/large_file')
            os.remove('/tmp/download.zip')
            os.remove('/tmp/webpage')
            shutil.rmtree('/tmp/testdir')
            shutil.rmtree('/tmp/OnionShare')
        except:
            pass


    def gui_loaded(self):
        '''Test that the GUI actually is shown'''
        self.assertTrue(self.gui.show)


    def windowTitle_seen(self):
        '''Test that the window title is OnionShare'''
        self.assertEqual(self.gui.windowTitle(), 'OnionShare')


    def settings_button_is_visible(self):
        '''Test that the settings button is visible'''
        self.assertTrue(self.gui.settings_button.isVisible())


    def settings_button_is_hidden(self):
        '''Test that the settings button is hidden when the server starts'''
        self.assertFalse(self.gui.settings_button.isVisible())


    def server_status_bar_is_visible(self):
        '''Test that the status bar is visible'''
        self.assertTrue(self.gui.status_bar.isVisible())


    def click_mode(self, mode):
        '''Test that we can switch Mode by clicking the button'''
        if type(mode) == ReceiveMode:
            QtTest.QTest.mouseClick(self.gui.receive_mode_button, QtCore.Qt.LeftButton)
            self.assertTrue(self.gui.mode, self.gui.MODE_RECEIVE)
        if type(mode) == ShareMode:
            QtTest.QTest.mouseClick(self.gui.share_mode_button, QtCore.Qt.LeftButton)
            self.assertTrue(self.gui.mode, self.gui.MODE_SHARE)


    def click_toggle_history(self, mode):
        '''Test that we can toggle Download or Upload history by clicking the toggle button'''
        currently_visible = mode.history.isVisible()
        QtTest.QTest.mouseClick(mode.toggle_history, QtCore.Qt.LeftButton)
        self.assertEqual(mode.history.isVisible(), not currently_visible)


    def history_indicator(self, mode, public_mode):
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
                path = 'http://127.0.0.1:{}/{}/upload'.format(self.gui.app.port, mode.web.password)
            else:
                path = 'http://127.0.0.1:{}/upload'.format(self.gui.app.port)
            response = requests.post(path, files=files)
            QtTest.QTest.qWait(2000)

        if type(mode) == ShareMode:
            # Download files
            if public_mode:
                url = "http://127.0.0.1:{}/download".format(self.gui.app.port)
            else:
                url = "http://127.0.0.1:{}/{}/download".format(self.gui.app.port, mode.web.password)
            r = requests.get(url)
            QtTest.QTest.qWait(2000)

        # Indicator should be visible, have a value of "1"
        self.assertTrue(mode.toggle_history.indicator_label.isVisible())
        self.assertEqual(mode.toggle_history.indicator_label.text(), "1")

        # Toggle history back on, indicator should be hidden again
        QtTest.QTest.mouseClick(mode.toggle_history, QtCore.Qt.LeftButton)
        self.assertFalse(mode.toggle_history.indicator_label.isVisible())


    def history_is_not_visible(self, mode):
        '''Test that the History section is not visible'''
        self.assertFalse(mode.history.isVisible())


    def history_is_visible(self, mode):
        '''Test that the History section is visible'''
        self.assertTrue(mode.history.isVisible())


    def server_working_on_start_button_pressed(self, mode):
        '''Test we can start the service'''
        # Should be in SERVER_WORKING state
        QtTest.QTest.mouseClick(mode.server_status.server_button, QtCore.Qt.LeftButton)
        self.assertEqual(mode.server_status.status, 1)


    def server_status_indicator_says_starting(self, mode):
        '''Test that the Server Status indicator shows we are Starting'''
        self.assertEqual(mode.server_status_label.text(), strings._('gui_status_indicator_share_working'))

    def server_status_indicator_says_scheduled(self, mode):
        '''Test that the Server Status indicator shows we are Scheduled'''
        self.assertEqual(mode.server_status_label.text(), strings._('gui_status_indicator_share_scheduled'))

    def server_is_started(self, mode, startup_time=2000):
        '''Test that the server has started'''
        QtTest.QTest.qWait(startup_time)
        # Should now be in SERVER_STARTED state
        self.assertEqual(mode.server_status.status, 2)


    def web_server_is_running(self):
        '''Test that the web server has started'''
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.assertEqual(sock.connect_ex(('127.0.0.1',self.gui.app.port)), 0)


    def have_a_password(self, mode, public_mode):
        '''Test that we have a valid password'''
        if not public_mode:
            self.assertRegex(mode.server_status.web.password, r'(\w+)-(\w+)')
        else:
            self.assertIsNone(mode.server_status.web.password, r'(\w+)-(\w+)')


    def url_description_shown(self, mode):
        '''Test that the URL label is showing'''
        self.assertTrue(mode.server_status.url_description.isVisible())


    def have_copy_url_button(self, mode, public_mode):
        '''Test that the Copy URL button is shown and that the clipboard is correct'''
        self.assertTrue(mode.server_status.copy_url_button.isVisible())

        QtTest.QTest.mouseClick(mode.server_status.copy_url_button, QtCore.Qt.LeftButton)
        clipboard = self.gui.qtapp.clipboard()
        if public_mode:
            self.assertEqual(clipboard.text(), 'http://127.0.0.1:{}'.format(self.gui.app.port))
        else:
            self.assertEqual(clipboard.text(), 'http://127.0.0.1:{}/{}'.format(self.gui.app.port, mode.server_status.web.password))


    def server_status_indicator_says_started(self, mode):
        '''Test that the Server Status indicator shows we are started'''
        if type(mode) == ReceiveMode:
            self.assertEqual(mode.server_status_label.text(), strings._('gui_status_indicator_receive_started'))
        if type(mode) == ShareMode:
            self.assertEqual(mode.server_status_label.text(), strings._('gui_status_indicator_share_started'))


    def web_page(self, mode, string, public_mode):
        '''Test that the web page contains a string'''
        s = socks.socksocket()
        s.settimeout(60)
        s.connect(('127.0.0.1', self.gui.app.port))

        if not public_mode:
            path = '/{}'.format(mode.server_status.web.password)
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


    def history_widgets_present(self, mode):
        '''Test that the relevant widgets are present in the history view after activity has taken place'''
        self.assertFalse(mode.history.empty.isVisible())
        self.assertTrue(mode.history.not_empty.isVisible())


    def counter_incremented(self, mode, count):
        '''Test that the counter has incremented'''
        self.assertEqual(mode.history.completed_count, count)


    def server_is_stopped(self, mode, stay_open):
        '''Test that the server stops when we click Stop'''
        if type(mode) == ReceiveMode or (type(mode) == ShareMode and stay_open):
            QtTest.QTest.mouseClick(mode.server_status.server_button, QtCore.Qt.LeftButton)
        self.assertEqual(mode.server_status.status, 0)


    def web_server_is_stopped(self):
        '''Test that the web server also stopped'''
        QtTest.QTest.qWait(2000)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # We should be closed by now. Fail if not!
        self.assertNotEqual(sock.connect_ex(('127.0.0.1',self.gui.app.port)), 0)


    def server_status_indicator_says_closed(self, mode, stay_open):
        '''Test that the Server Status indicator shows we closed'''
        if type(mode) == ReceiveMode:
            self.assertEqual(self.gui.receive_mode.server_status_label.text(), strings._('gui_status_indicator_receive_stopped'))
        if type(mode) == ShareMode:
            if stay_open:
                self.assertEqual(self.gui.share_mode.server_status_label.text(), strings._('gui_status_indicator_share_stopped'))
            else:
                self.assertEqual(self.gui.share_mode.server_status_label.text(), strings._('closing_automatically'))


    # Auto-stop timer tests
    def set_timeout(self, mode, timeout):
        '''Test that the timeout can be set'''
        timer = QtCore.QDateTime.currentDateTime().addSecs(timeout)
        mode.server_status.autostop_timer_widget.setDateTime(timer)
        self.assertTrue(mode.server_status.autostop_timer_widget.dateTime(), timer)

    def autostop_timer_widget_hidden(self, mode):
        '''Test that the auto-stop timer widget is hidden when share has started'''
        self.assertFalse(mode.server_status.autostop_timer_container.isVisible())


    def server_timed_out(self, mode, wait):
        '''Test that the server has timed out after the timer ran out'''
        QtTest.QTest.qWait(wait)
        # We should have timed out now
        self.assertEqual(mode.server_status.status, 0)

    # Auto-start timer tests
    def set_autostart_timer(self, mode, timer):
        '''Test that the timer can be set'''
        schedule = QtCore.QDateTime.currentDateTime().addSecs(timer)
        mode.server_status.autostart_timer_widget.setDateTime(schedule)
        self.assertTrue(mode.server_status.autostart_timer_widget.dateTime(), schedule)

    def autostart_timer_widget_hidden(self, mode):
        '''Test that the auto-start timer widget is hidden when share has started'''
        self.assertFalse(mode.server_status.autostart_timer_container.isVisible())

    def scheduled_service_started(self, mode, wait):
        '''Test that the server has timed out after the timer ran out'''
        QtTest.QTest.qWait(wait)
        # We should have started now
        self.assertEqual(mode.server_status.status, 2)

    def cancel_the_share(self, mode):
        '''Test that we can cancel a share before it's started up '''
        self.server_working_on_start_button_pressed(mode)
        self.server_status_indicator_says_scheduled(mode)
        self.add_delete_buttons_hidden()
        self.settings_button_is_hidden()
        self.set_autostart_timer(mode, 10)
        QtTest.QTest.mousePress(mode.server_status.server_button, QtCore.Qt.LeftButton)
        QtTest.QTest.qWait(2000)
        QtTest.QTest.mouseRelease(mode.server_status.server_button, QtCore.Qt.LeftButton)
        self.assertEqual(mode.server_status.status, 0)
        self.server_is_stopped(mode, False)
        self.web_server_is_stopped()

    # Hack to close an Alert dialog that would otherwise block tests
    def accept_dialog(self):
        window = self.gui.qtapp.activeWindow()
        if window:
            window.close()

    # 'Grouped' tests follow from here

    def run_all_common_setup_tests(self):
        self.gui_loaded()
        self.windowTitle_seen()
        self.settings_button_is_visible()
        self.server_status_bar_is_visible()
