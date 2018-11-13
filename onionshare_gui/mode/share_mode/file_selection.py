# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014-2018 Micah Lee <micah@micahflee.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import os
from PyQt5 import QtCore, QtWidgets, QtGui

from onionshare import strings

from ...widgets import Alert, AddFileDialog

class DropHereLabel(QtWidgets.QLabel):
    """
    When there are no files or folders in the FileList yet, display the
    'drop files here' message and graphic.
    """
    def __init__(self, common, parent, image=False):
        self.parent = parent
        super(DropHereLabel, self).__init__(parent=parent)

        self.common = common

        self.setAcceptDrops(True)
        self.setAlignment(QtCore.Qt.AlignCenter)

        if image:
            self.setPixmap(QtGui.QPixmap.fromImage(QtGui.QImage(self.common.get_resource_path('images/logo_transparent.png'))))
        else:
            self.setText(strings._('gui_drag_and_drop'))
            self.setStyleSheet(self.common.css['share_file_selection_drop_here_label'])

        self.hide()

    def dragEnterEvent(self, event):
        self.parent.drop_here_image.hide()
        self.parent.drop_here_text.hide()
        event.accept()


class DropCountLabel(QtWidgets.QLabel):
    """
    While dragging files over the FileList, this counter displays the
    number of files you're dragging.
    """
    def __init__(self, common, parent):
        self.parent = parent
        super(DropCountLabel, self).__init__(parent=parent)

        self.common = common

        self.setAcceptDrops(True)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setText(strings._('gui_drag_and_drop'))
        self.setStyleSheet(self.common.css['share_file_selection_drop_count_label'])
        self.hide()

    def dragEnterEvent(self, event):
        self.hide()
        event.accept()


class FileList(QtWidgets.QListWidget):
    """
    The list of files and folders in the GUI.
    """
    files_dropped = QtCore.pyqtSignal()
    files_updated = QtCore.pyqtSignal()

    def __init__(self, common, parent=None):
        super(FileList, self).__init__(parent)

        self.common = common

        self.setAcceptDrops(True)
        self.setIconSize(QtCore.QSize(32, 32))
        self.setSortingEnabled(True)
        self.setMinimumHeight(160)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.drop_here_image = DropHereLabel(self.common, self, True)
        self.drop_here_text = DropHereLabel(self.common, self, False)
        self.drop_count = DropCountLabel(self.common, self)
        self.resizeEvent(None)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

    def update(self):
        """
        Update the GUI elements based on the current state.
        """
        # file list should have a background image if empty
        if self.count() == 0:
            self.drop_here_image.show()
            self.drop_here_text.show()
        else:
            self.drop_here_image.hide()
            self.drop_here_text.hide()

    def server_started(self):
        """
        Update the GUI when the server starts, by hiding delete buttons.
        """
        self.setAcceptDrops(False)
        self.setCurrentItem(None)
        self.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        for index in range(self.count()):
            self.item(index).item_button.hide()

    def server_stopped(self):
        """
        Update the GUI when the server stops, by showing delete buttons.
        """
        self.setAcceptDrops(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        for index in range(self.count()):
            self.item(index).item_button.show()

    def resizeEvent(self, event):
        """
        When the widget is resized, resize the drop files image and text.
        """
        offset = 70
        self.drop_here_image.setGeometry(0, 0, self.width(), self.height() - offset)
        self.drop_here_text.setGeometry(0, offset, self.width(), self.height() - offset)

        if self.count() > 0:
            # Add and delete an empty item, to force all items to get redrawn
            # This is ugly, but the only way I could figure out how to proceed
            item = QtWidgets.QListWidgetItem('fake item')
            self.addItem(item)
            self.takeItem(self.row(item))
            self.update()

            # Extend any filenames that were truncated to fit the window
            # We use 200 as a rough guess at how wide the 'file size + delete button' widget is
            # and extend based on the overall width minus that amount.
            for index in range(self.count()):
                metrics = QtGui.QFontMetrics(self.item(index).font())
                elided = metrics.elidedText(self.item(index).basename, QtCore.Qt.ElideRight, self.width() - 200)
                self.item(index).setText(elided)


    def dragEnterEvent(self, event):
        """
        dragEnterEvent for dragging files and directories into the widget.
        """
        if event.mimeData().hasUrls:
            self.setStyleSheet(self.common.css['share_file_list_drag_enter'])
            count = len(event.mimeData().urls())
            self.drop_count.setText('+{}'.format(count))

            size_hint = self.drop_count.sizeHint()
            self.drop_count.setGeometry(self.width() - size_hint.width() - 10, self.height() - size_hint.height() - 10, size_hint.width(), size_hint.height())
            self.drop_count.show()
            event.accept()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        """
        dragLeaveEvent for dragging files and directories into the widget.
        """
        self.setStyleSheet(self.common.css['share_file_list_drag_leave'])
        self.drop_count.hide()
        event.accept()
        self.update()

    def dragMoveEvent(self, event):
        """
        dragMoveEvent for dragging files and directories into the widget.
        """
        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """
        dropEvent for dragging files and directories into the widget.
        """
        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
            for url in event.mimeData().urls():
                filename = str(url.toLocalFile())
                self.add_file(filename)
        else:
            event.ignore()

        self.setStyleSheet(self.common.css['share_file_list_drag_leave'])
        self.drop_count.hide()

        self.files_dropped.emit()

    def add_file(self, filename):
        """
        Add a file or directory to this widget.
        """
        filenames = []
        for index in range(self.count()):
            filenames.append(self.item(index).filename)

        if filename not in filenames:
            if not os.access(filename, os.R_OK):
                Alert(self.common, strings._("not_a_readable_file").format(filename))
                return

            fileinfo = QtCore.QFileInfo(filename)
            ip = QtWidgets.QFileIconProvider()
            icon = ip.icon(fileinfo)

            if os.path.isfile(filename):
                size_bytes = fileinfo.size()
                size_readable = self.common.human_readable_filesize(size_bytes)
            else:
                size_bytes = self.common.dir_size(filename)
                size_readable = self.common.human_readable_filesize(size_bytes)

            # Create a new item
            item = QtWidgets.QListWidgetItem()
            item.setIcon(icon)
            item.size_bytes = size_bytes

            # Item's filename attribute and size labels
            item.filename = filename
            item_size = QtWidgets.QLabel(size_readable)
            item_size.setStyleSheet(self.common.css['share_file_list_item_size'])

            item.basename = os.path.basename(filename.rstrip('/'))
            # Use the basename as the method with which to sort the list
            metrics = QtGui.QFontMetrics(item.font())
            elided = metrics.elidedText(item.basename, QtCore.Qt.ElideRight, self.sizeHint().width())
            item.setData(QtCore.Qt.DisplayRole, elided)

            # Item's delete button
            def delete_item():
                itemrow = self.row(item)
                self.takeItem(itemrow)
                self.files_updated.emit()

            item.item_button = QtWidgets.QPushButton()
            item.item_button.setDefault(False)
            item.item_button.setFlat(True)
            item.item_button.setIcon( QtGui.QIcon(self.common.get_resource_path('images/file_delete.png')) )
            item.item_button.clicked.connect(delete_item)
            item.item_button.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

            # Item info widget, with a white background
            item_info_layout = QtWidgets.QHBoxLayout()
            item_info_layout.setContentsMargins(0, 0, 0, 0)
            item_info_layout.addWidget(item_size)
            item_info_layout.addWidget(item.item_button)
            item_info = QtWidgets.QWidget()
            item_info.setObjectName('item-info')
            item_info.setLayout(item_info_layout)

            # Create the item's widget and layouts
            item_hlayout = QtWidgets.QHBoxLayout()
            item_hlayout.addStretch()
            item_hlayout.addWidget(item_info)
            widget = QtWidgets.QWidget()
            widget.setLayout(item_hlayout)

            item.setSizeHint(widget.sizeHint())

            self.addItem(item)
            self.setItemWidget(item, widget)

            self.files_updated.emit()


class FileSelection(QtWidgets.QVBoxLayout):
    """
    The list of files and folders in the GUI, as well as buttons to add and
    delete the files and folders.
    """
    def __init__(self, common):
        super(FileSelection, self).__init__()

        self.common = common

        self.server_on = False

        # File list
        self.file_list = FileList(self.common)
        self.file_list.itemSelectionChanged.connect(self.update)
        self.file_list.files_dropped.connect(self.update)
        self.file_list.files_updated.connect(self.update)

        # Buttons
        self.add_button = QtWidgets.QPushButton(strings._('gui_add'))
        self.add_button.clicked.connect(self.add)
        self.delete_button = QtWidgets.QPushButton(strings._('gui_delete'))
        self.delete_button.clicked.connect(self.delete)
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.delete_button)

        # Add the widgets
        self.addWidget(self.file_list)
        self.addLayout(button_layout)

        self.update()

    def update(self):
        """
        Update the GUI elements based on the current state.
        """
        # All buttons should be hidden if the server is on
        if self.server_on:
            self.add_button.hide()
            self.delete_button.hide()
        else:
            self.add_button.show()

            # Delete button should be hidden if item isn't selected
            if len(self.file_list.selectedItems()) == 0:
                self.delete_button.hide()
            else:
                self.delete_button.show()

        # Update the file list
        self.file_list.update()

    def add(self):
        """
        Add button clicked.
        """
        file_dialog = AddFileDialog(self.common, caption=strings._('gui_choose_items'))
        if file_dialog.exec_() == QtWidgets.QDialog.Accepted:
            for filename in file_dialog.selectedFiles():
                self.file_list.add_file(filename)

        self.file_list.setCurrentItem(None)
        self.update()

    def delete(self):
        """
        Delete button clicked
        """
        selected = self.file_list.selectedItems()
        for item in selected:
            itemrow = self.file_list.row(item)
            self.file_list.takeItem(itemrow)
        self.file_list.files_updated.emit()

        self.file_list.setCurrentItem(None)
        self.update()

    def server_started(self):
        """
        Gets called when the server starts.
        """
        self.server_on = True
        self.file_list.server_started()
        self.update()

    def server_stopped(self):
        """
        Gets called when the server stops.
        """
        self.server_on = False
        self.file_list.server_stopped()
        self.update()

    def get_num_files(self):
        """
        Returns the total number of files and folders in the list.
        """
        return len(range(self.file_list.count()))

    def setFocus(self):
        """
        Set the Qt app focus on the file selection box.
        """
        self.file_list.setFocus()
