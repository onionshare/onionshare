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

from PySide2 import QtCore, QtWidgets, QtGui
import qrcode

from . import strings
from .gui_common import GuiCommon


class Alert(QtWidgets.QMessageBox):
    """
    An alert box dialog.
    """

    def __init__(
        self,
        common,
        message,
        icon=QtWidgets.QMessageBox.NoIcon,
        buttons=QtWidgets.QMessageBox.Ok,
        autostart=True,
        title="OnionShare",
    ):
        super(Alert, self).__init__(None)

        self.common = common

        self.common.log("Alert", "__init__")

        self.setWindowTitle(title)
        self.setWindowIcon(QtGui.QIcon(GuiCommon.get_resource_path("images/logo.png")))
        self.setText(message)
        self.setIcon(icon)
        self.setStandardButtons(buttons)

        if autostart:
            self.exec_()


class AddFileDialog(QtWidgets.QFileDialog):
    """
    Overridden version of QFileDialog which allows us to select folders as well
    as, or instead of, files. For adding files/folders to share.

    Note that this dialog can't be used in macOS, only in Windows, Linux, and BSD.
    This is because the macOS sandbox requires native dialogs, and this is a Qt5
    dialog.
    """

    def __init__(self, common, *args, **kwargs):
        QtWidgets.QFileDialog.__init__(self, *args, **kwargs)

        self.common = common
        self.common.log("AddFileDialog", "__init__")

        self.setOption(self.DontUseNativeDialog, True)
        self.setOption(self.ReadOnly, True)
        self.setOption(self.ShowDirsOnly, False)
        self.setFileMode(self.ExistingFiles)
        tree_view = self.findChild(QtWidgets.QTreeView)
        tree_view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        list_view = self.findChild(QtWidgets.QListView, "listView")
        list_view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

    def accept(self):
        self.common.log("AddFileDialog", "accept")
        QtWidgets.QDialog.accept(self)


class MinimumSizeWidget(QtWidgets.QWidget):
    """
    An empty widget with a minimum width and height, just to force layouts to behave
    """

    def __init__(self, width, height):
        super(MinimumSizeWidget, self).__init__()
        self.setMinimumWidth(width)
        self.setMinimumHeight(height)


class Image(qrcode.image.base.BaseImage):
    """
    A custom Image class, for use with the QR Code pixmap.
    """

    def __init__(self, border, width, box_size):
        self.border = border
        self.width = width
        self.box_size = box_size
        size = (width + border * 2) * box_size
        self._image = QtGui.QImage(size, size, QtGui.QImage.Format_RGB16)
        self._image.fill(QtCore.Qt.white)

    def pixmap(self):
        return QtGui.QPixmap.fromImage(self._image)

    def drawrect(self, row, col):
        painter = QtGui.QPainter(self._image)
        painter.fillRect(
            (col + self.border) * self.box_size,
            (row + self.border) * self.box_size,
            self.box_size,
            self.box_size,
            QtCore.Qt.black,
        )

    def save(self, stream, kind=None):
        pass


class QRCodeDialog(QtWidgets.QDialog):
    """
    A dialog showing a QR code.
    """

    def __init__(self, common, title, text):
        super(QRCodeDialog, self).__init__()

        self.common = common

        self.common.log("QrCode", "__init__")

        self.qr_label_title = QtWidgets.QLabel(self)
        self.qr_label_title.setText(title)
        self.qr_label_title.setAlignment(QtCore.Qt.AlignCenter)

        self.qr_label = QtWidgets.QLabel(self)
        self.qr_label.setPixmap(qrcode.make(text, image_factory=Image).pixmap())
        self.qr_label.setScaledContents(True)
        self.qr_label.setFixedSize(350, 350)

        self.setWindowTitle(strings._("gui_qr_code_dialog_title"))
        self.setWindowIcon(QtGui.QIcon(GuiCommon.get_resource_path("images/logo.png")))
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.qr_label_title)
        layout.addWidget(self.qr_label)

        self.exec_()
