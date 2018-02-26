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
    def test_add_delete_buttons(self):
        '''Test that the add button is visiblem and that the delete button is not visible (we don't have focus on the item)'''
        self.assertTrue(self.gui.file_selection.add_button.isVisible())
        self.assertFalse(self.gui.file_selection.delete_button.isVisible())

    @pytest.mark.run(order=4)
    def test_deleting_only_file_hides_delete_button(self):
        '''Test that clicking on the file item shows the delete button. Test that deleting the only item in the list hides the delete button'''
        rect = self.gui.file_selection.file_list.visualItemRect(self.gui.file_selection.file_list.item(0))
        QtTest.QTest.mouseClick(self.gui.file_selection.file_list.viewport(), QtCore.Qt.LeftButton, pos=rect.center())
        self.assertTrue(self.gui.file_selection.delete_button.isVisible())
        QtTest.QTest.mouseClick(self.gui.file_selection.delete_button, QtCore.Qt.LeftButton)
        self.assertFalse(self.gui.file_selection.delete_button.isVisible())

    @pytest.mark.run(order=5)
    def test_add_a_file_and_delete_using_its_delete_widget(self):
        self.gui.file_selection.file_list.add_file('/etc/hostname')
        QtTest.QTest.mouseClick(self.gui.file_selection.file_list.item(0).item_button, QtCore.Qt.LeftButton)
        self.assertEquals(self.gui.file_selection.get_num_files(), 0)

