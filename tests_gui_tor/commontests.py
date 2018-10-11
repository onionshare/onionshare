import os
import requests
import socket
import socks
import zipfile

from PyQt5 import QtCore, QtTest
from onionshare import strings

from tests_gui_local import CommonTests as LocalCommonTests

class CommonTests(LocalCommonTests):
    def test_a_server_is_started(self, mode):
        '''Test that the server has started (overriding from local tests to wait for longer)'''
        QtTest.QTest.qWait(45000)
        # Should now be in SERVER_STARTED state
        if mode == 'receive':
            self.assertEqual(self.gui.receive_mode.server_status.status, 2)
        if mode == 'share':
            self.assertEqual(self.gui.share_mode.server_status.status, 2)

    def test_have_an_onion_service(self):
        '''Test that we have a valid Onion URL'''
        self.assertRegex(self.gui.app.onion_host, r'[a-z2-7].onion')

    def test_cancel_the_share(self, mode):
        '''Test that we can cancel this share before it's started up '''
        if mode == 'share':
            QtTest.QTest.mousePress(self.gui.share_mode.server_status.server_button, QtCore.Qt.LeftButton)
            QtTest.QTest.qWait(1000)
            QtTest.QTest.mouseRelease(self.gui.share_mode.server_status.server_button, QtCore.Qt.LeftButton)
            self.assertEqual(self.gui.share_mode.server_status.status, 0)

        if mode == 'receive':
            QtTest.QTest.mousePress(self.gui.receive_mode.server_status.server_button, QtCore.Qt.LeftButton)
            QtTest.QTest.qWait(1000)
            QtTest.QTest.mouseRelease(self.gui.receive_mode.server_status.server_button, QtCore.Qt.LeftButton)
            self.assertEqual(self.gui.receive_mode.server_status.status, 0)

    # Stealth tests
    def test_copy_have_hidserv_auth_button(self, mode):
        '''Test that the Copy HidservAuth button is shown'''
        if mode == 'share':
            self.assertTrue(self.gui.share_mode.server_status.copy_hidservauth_button.isVisible())
        if mode == 'receive':
            self.assertTrue(self.gui.receive_mode.server_status.copy_hidservauth_button.isVisible())

    def test_hidserv_auth_string(self):
        '''Test the validity of the HidservAuth string'''
        self.assertRegex(self.gui.app.auth_string, r'HidServAuth %s [a-zA-Z1-9]' % self.gui.app.onion_host)


    # Miscellaneous tests
    def test_tor_killed_statusbar_message_shown(self, mode):
        '''Test that the status bar message shows Tor was disconnected'''
        self.gui.app.onion.cleanup(stop_tor=True)
        QtTest.QTest.qWait(2500)
        if mode == 'share':
            self.assertTrue(self.gui.share_mode.status_bar.currentMessage(), strings._('gui_tor_connection_lost', True))
        if mode == 'receive':
            self.assertTrue(self.gui.receive_mode.status_bar.currentMessage(), strings._('gui_tor_connection_lost', True))
