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
    def test_version_found(self):
        '''
        Test that the version is parsed from common.get_version()
        and also in the locale-based version string
        '''
        self.assertIn(self.gui.settings.default_settings.get('version'), strings._('version_string').format(common.get_version()))

    @pytest.mark.run(order=3)
    def test_windowTitle_seen(self):
        '''Test that the window title is OnionShare'''
        self.assertEqual(self.gui.windowTitle(), 'OnionShare')

    @pytest.mark.run(order=4)
    def test_download_container_is_hidden(self):
        '''Test that the download container is hidden'''
        self.assertTrue(self.gui.downloads_container.isHidden())

    @pytest.mark.run(order=5)
    def test_settings_button_is_enabled(self):
        '''Test that the settings button is enabled'''
        self.assertTrue(self.gui.settings_button.isEnabled())

    @pytest.mark.run(order=6)
    def test_server_status_bar_is_visible(self):
        '''Test that the status bar is visible'''
        self.assertTrue(self.gui.status_bar.isVisible())

    @pytest.mark.run(order=7)
    def test_file_selection_widget_has_a_file(self):
        '''Test that the number of files in the list is 1'''
        self.assertEqual(self.gui.file_selection.get_num_files(), 1)

    @pytest.mark.run(order=8)
    def test_file_selection_widget_add_a_file(self):
        '''Add another file to the list'''
        self.gui.file_selection.file_list.add_file('/etc/hostname')
        self.assertEqual(self.gui.file_selection.get_num_files(), 2)

    @pytest.mark.run(order=9)
    def test_file_selection_widget_remove_a_file(self):
        '''Remove a file from the list'''
        self.gui.file_selection.file_list.item(1).setSelected(True)
        self.gui.file_selection.delete()
        self.assertEqual(self.gui.file_selection.get_num_files(), 1)

    @pytest.mark.run(order=10)
    def test_server_working_on_start_button_pressed(self):
        '''Test we can start the service'''
        QtTest.QTest.mouseClick(self.gui.server_status.server_button, QtCore.Qt.LeftButton)

        # Should be in SERVER_WORKING state
        self.assertEqual(self.gui.server_status.status, 1)

    @pytest.mark.run(order=11)
    def test_add_delete_buttons_now_disabled(self):
        '''Test that the add and delete buttons are disabled when the server starts'''
        self.assertFalse(self.gui.file_selection.add_button.isEnabled())
        self.assertFalse(self.gui.file_selection.delete_button.isEnabled())

    @pytest.mark.run(order=12)
    def test_settings_button_is_disabled(self):
        '''Test that the settings button is disabled when the server starts'''
        self.assertFalse(self.gui.settings_button.isEnabled())

    @pytest.mark.run(order=13)
    def test_a_server_is_started(self):
        '''Test that the server has started'''
        # Wait for share to start
        QtTest.QTest.qWait(60000)

        # Should now be in SERVER_STARTED state
        self.assertEqual(self.gui.server_status.status, 2)

    @pytest.mark.run(order=14)
    def test_a_web_server_is_running(self):
        '''Test that the web server has started'''
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # We should be closed by now. Fail if not!
        self.assertEqual(sock.connect_ex(('127.0.0.1',self.gui.app.port)), 0)

    @pytest.mark.run(order=15)
    def test_have_an_onion_service(self):
        '''Test that we have a valid Onion URL'''
        self.assertRegex(self.gui.app.onion_host, r'[a-z2-7].onion')
        self.assertEqual(len(self.gui.app.onion_host), 22)

    @pytest.mark.run(order=16)
    def test_have_a_slug(self):
        '''Test that we have a valid slug'''
        self.assertRegex(self.gui.server_status.web.slug, r'(\w+)-(\w+)')

    @pytest.mark.run(order=17)
    def test_url_label_shown(self):
        '''Test that the URL label is showing'''
        self.assertEquals(self.gui.server_status.url_label.text(), 'http://{0:s}/{1:s}'.format(self.gui.app.onion_host, self.gui.server_status.web.slug))

    @pytest.mark.run(order=18)
    def test_have_copy_url_button(self):
        '''Test that the Copy URL button is shown'''
        self.assertTrue(self.gui.server_status.copy_url_button.isVisible())

    @pytest.mark.run(order=19)
    def test_copy_url_button_click_shows_message(self):
        '''Test that the Copy URL button shows a status message when clicked'''
        QtTest.QTest.mouseClick(self.gui.server_status.copy_url_button, QtCore.Qt.LeftButton)
        self.assertEqual(self.gui.status_bar.currentMessage(), strings._('gui_copied_url', True))

    @pytest.mark.run(order=20)
    def test_copy_url_button_click_clears_message(self):
        '''Test that the Copy URL message disappears after 2 seconds'''
        QtTest.QTest.qWait(2500)
        self.assertEqual(self.gui.status_bar.currentMessage(), '')

    @pytest.mark.run(order=21)
    def test_server_is_stopped(self):
        '''Test that we can stop the server'''
        QtTest.QTest.mouseClick(self.gui.server_status.server_button, QtCore.Qt.LeftButton)
        QtTest.QTest.qWait(1000)
        self.assertEqual(self.gui.server_status.status, 0)

    @pytest.mark.run(order=22)
    def test_web_service_is_stopped(self):
        '''Test that the web server also stopped'''
        # Give the Flask server time to shut down
        QtTest.QTest.qWait(4000)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # We should be closed by now. Fail if not!
        self.assertNotEqual(sock.connect_ex(('127.0.0.1',self.gui.app.port)), 0)

    @pytest.mark.run(order=23)
    def test_add_button_enabled_again(self):
        # Add button should be enabled again
        self.assertTrue(self.gui.file_selection.add_button.isEnabled())


if __name__ == "__main__":
    unittest.main()
