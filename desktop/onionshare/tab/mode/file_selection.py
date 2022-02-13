# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014-2022 Micah Lee, et al. <micah@micahflee.com>

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
from PySide2 import QtCore, QtWidgets, QtGui

from ... import strings
from ...widgets import Alert, AddFileDialog
from ...gui_common import GuiCommon


class DropHereWidget(QtWidgets.QWidget):
    """
    When there are no files or folders in the FileList yet, display the
    'drop files here' message and graphic.
    """

    def __init__(self, common, image_filename, header_text, w, h, parent):
        super(DropHereWidget, self).__init__(parent)
        self.common = common
        self.setAcceptDrops(True)

        self.image_label = QtWidgets.QLabel(parent=self)
        self.image_label.setPixmap(
            QtGui.QPixmap.fromImage(
                QtGui.QImage(GuiCommon.get_resource_path(image_filename))
            )
        )
        self.image_label.setAlignment(QtCore.Qt.AlignCenter)
        self.image_label.show()

        self.header_label = QtWidgets.QLabel(parent=self)
        self.header_label.setText(header_text)
        self.header_label.setStyleSheet(
            self.common.gui.css["share_file_selection_drop_here_header_label"]
        )
        self.header_label.setAlignment(QtCore.Qt.AlignCenter)
        self.header_label.show()

        self.text_label = QtWidgets.QLabel(parent=self)
        self.text_label.setText(strings._("gui_drag_and_drop"))
        self.text_label.setStyleSheet(
            self.common.gui.css["share_file_selection_drop_here_label"]
        )
        self.text_label.setAlignment(QtCore.Qt.AlignCenter)
        self.text_label.show()

        self.resize(w, h)
        self.hide()

    def dragEnterEvent(self, event):
        self.hide()
        event.accept()

    def resize(self, w, h):
        self.setGeometry(0, 0, w, h)
        self.image_label.setGeometry(0, 0, w, h - 100)
        self.header_label.setGeometry(0, 290, w, h - 360)
        self.text_label.setGeometry(0, 340, w, h - 380)


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
        self.setText(strings._("gui_drag_and_drop"))
        self.setStyleSheet(self.common.gui.css["share_file_selection_drop_count_label"])
        self.hide()

    def dragEnterEvent(self, event):
        self.hide()
        event.accept()


class FileList(QtWidgets.QListWidget):
    """
    The list of files and folders in the GUI.
    """

    files_dropped = QtCore.Signal()
    files_updated = QtCore.Signal()

    def __init__(self, common, background_image_filename, header_text, parent=None):
        super(FileList, self).__init__(parent)
        self.common = common
        self.setAcceptDrops(True)

        self.setIconSize(QtCore.QSize(32, 32))
        self.setSortingEnabled(True)
        self.setMinimumHeight(160)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.drop_here = DropHereWidget(
            self.common,
            background_image_filename,
            header_text,
            self.width(),
            self.height(),
            self,
        )
        self.drop_count = DropCountLabel(self.common, self)
        self.resizeEvent(None)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

    def update(self):
        """
        Update the GUI elements based on the current state.
        """
        # file list should have a background image if empty
        if self.count() == 0:
            self.drop_here.show()
        else:
            self.drop_here.hide()

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
        self.drop_here.resize(self.width(), self.height())

        if self.count() > 0:
            # Add and delete an empty item, to force all items to get redrawn
            # This is ugly, but the only way I could figure out how to proceed
            item = QtWidgets.QListWidgetItem("fake item")
            self.addItem(item)
            self.takeItem(self.row(item))
            self.update()

            # Extend any filenames that were truncated to fit the window
            # We use 200 as a rough guess at how wide the 'file size + delete button' widget is
            # and extend based on the overall width minus that amount.
            for index in range(self.count()):
                metrics = QtGui.QFontMetrics(self.item(index).font())
                elided = metrics.elidedText(
                    self.item(index).basename, QtCore.Qt.ElideRight, self.width() - 200
                )
                self.item(index).setText(elided)

    def dragEnterEvent(self, event):
        """
        dragEnterEvent for dragging files and directories into the widget.
        """
        # Drag and drop doesn't work in Flatpak, because of the sandbox
        if self.common.is_flatpak():
            Alert(self.common, strings._("gui_dragdrop_sandbox_flatpak").format())
            event.ignore()
            return

        if event.mimeData().hasUrls:
            self.setStyleSheet(self.common.gui.css["share_file_list_drag_enter"])
            count = len(event.mimeData().urls())
            self.drop_count.setText(f"+{count}")

            size_hint = self.drop_count.sizeHint()
            self.drop_count.setGeometry(
                self.width() - size_hint.width() - 30,
                self.height() - size_hint.height() - 10,
                size_hint.width(),
                size_hint.height(),
            )
            self.drop_count.show()
            event.accept()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        """
        dragLeaveEvent for dragging files and directories into the widget.
        """
        # Drag and drop doesn't work in Flatpak, because of the sandbox
        if self.common.is_flatpak():
            event.ignore()
            return

        self.setStyleSheet(self.common.gui.css["share_file_list_drag_leave"])
        self.drop_count.hide()
        event.accept()
        self.update()

    def dragMoveEvent(self, event):
        """
        dragMoveEvent for dragging files and directories into the widget.
        """
        # Drag and drop doesn't work in Flatpak, because of the sandbox
        if self.common.is_flatpak():
            event.ignore()
            return

        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """
        dropEvent for dragging files and directories into the widget.
        """
        # Drag and drop doesn't work in Flatpak, because of the sandbox
        if self.common.is_flatpak():
            event.ignore()
            return

        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
            for url in event.mimeData().urls():
                filename = str(url.toLocalFile())
                self.add_file(filename)
        else:
            event.ignore()

        self.setStyleSheet(self.common.gui.css["share_file_list_drag_leave"])
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
            item_size.setStyleSheet(self.common.gui.css["share_file_list_item_size"])

            item.basename = os.path.basename(filename.rstrip("/"))
            # Use the basename as the method with which to sort the list
            metrics = QtGui.QFontMetrics(item.font())
            elided = metrics.elidedText(
                item.basename, QtCore.Qt.ElideRight, self.sizeHint().width()
            )
            item.setData(QtCore.Qt.DisplayRole, elided)

            # Item's delete button
            def delete_item():
                itemrow = self.row(item)
                self.takeItem(itemrow)
                self.files_updated.emit()

            item.item_button = QtWidgets.QPushButton()
            item.item_button.setDefault(False)
            item.item_button.setFlat(True)
            item.item_button.setIcon(
                QtGui.QIcon(GuiCommon.get_resource_path("images/file_delete.png"))
            )
            item.item_button.clicked.connect(delete_item)
            item.item_button.setSizePolicy(
                QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
            )

            # Item info widget, with a white background
            item_info_layout = QtWidgets.QHBoxLayout()
            item_info_layout.setContentsMargins(0, 0, 0, 0)
            item_info_layout.addWidget(item_size)
            item_info_layout.addWidget(item.item_button)
            item_info = QtWidgets.QWidget()
            item_info.setObjectName("item-info")
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

    def __init__(self, common, background_image_filename, header_text, parent):
        super(FileSelection, self).__init__()

        self.common = common
        self.parent = parent

        self.server_on = False

        # File list
        self.file_list = FileList(self.common, background_image_filename, header_text)
        self.file_list.itemSelectionChanged.connect(self.update)
        self.file_list.files_dropped.connect(self.update)
        self.file_list.files_updated.connect(self.update)

        # Sandboxes (for masOS, Flatpak, etc.) need separate add files and folders buttons, in
        # order to use native file selection dialogs
        if self.common.platform == "Darwin" or self.common.is_flatpak():
            self.sandbox = True
        else:
            self.sandbox = False

        # Buttons
        if self.sandbox:
            # The macOS sandbox makes it so the Mac version needs separate add files
            # and folders buttons, in order to use native file selection dialogs
            self.add_files_button = QtWidgets.QPushButton(strings._("gui_add_files"))
            self.add_files_button.clicked.connect(self.add_files)
            self.add_folder_button = QtWidgets.QPushButton(strings._("gui_add_folder"))
            self.add_folder_button.clicked.connect(self.add_folder)
        else:
            self.add_button = QtWidgets.QPushButton(strings._("gui_add"))
            self.add_button.clicked.connect(self.add)
        self.remove_button = QtWidgets.QPushButton(strings._("gui_remove"))
        self.remove_button.clicked.connect(self.delete)
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        if self.sandbox:
            button_layout.addWidget(self.add_files_button)
            button_layout.addWidget(self.add_folder_button)
        else:
            button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.remove_button)

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
            if self.sandbox:
                self.add_files_button.hide()
                self.add_folder_button.hide()
            else:
                self.add_button.hide()
            self.remove_button.hide()
        else:
            if self.sandbox:
                self.add_files_button.show()
                self.add_folder_button.show()
            else:
                self.add_button.show()

            # Delete button should be hidden if item isn't selected
            if len(self.file_list.selectedItems()) == 0:
                self.remove_button.hide()
            else:
                self.remove_button.show()

        # Update the file list
        self.file_list.update()

        # Save the latest file list to mode settings
        self.save_filenames()

    def add(self):
        """
        Add button clicked.
        """
        file_dialog = AddFileDialog(self.common, caption=strings._("gui_choose_items"))
        if file_dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.common.log("FileSelection", "add", file_dialog.selectedFiles())
            for filename in file_dialog.selectedFiles():
                self.file_list.add_file(filename)

        self.file_list.setCurrentItem(None)
        self.update()

    def add_files(self):
        """
        Add Files button clicked.
        """
        files = QtWidgets.QFileDialog.getOpenFileNames(
            self.parent, caption=strings._("gui_choose_items")
        )
        self.common.log("FileSelection", "add_files", files)

        filenames = files[0]
        for filename in filenames:
            self.file_list.add_file(filename)

        self.file_list.setCurrentItem(None)
        self.update()

    def add_folder(self):
        """
        Add Folder button clicked.
        """
        filename = QtWidgets.QFileDialog.getExistingDirectory(
            self.parent,
            caption=strings._("gui_choose_items"),
            options=QtWidgets.QFileDialog.ShowDirsOnly,
        )
        self.common.log("FileSelection", "add_folder", filename)
        if filename:
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

    def get_filenames(self):
        """
        Return the list of file and folder names
        """
        filenames = []
        for index in range(self.file_list.count()):
            filenames.append(self.file_list.item(index).filename)
        return filenames

    def save_filenames(self):
        """
        Save the filenames to mode settings
        """
        filenames = self.get_filenames()
        if self.parent.tab.mode == self.common.gui.MODE_SHARE:
            self.parent.settings.set("share", "filenames", filenames)
        elif self.parent.tab.mode == self.common.gui.MODE_WEBSITE:
            self.parent.settings.set("website", "filenames", filenames)

    def setFocus(self):
        """
        Set the Qt app focus on the file selection box.
        """
        self.file_list.setFocus()
