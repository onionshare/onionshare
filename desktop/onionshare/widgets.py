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
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

from PySide6 import QtCore, QtWidgets, QtGui
import qrcode

from . import strings
from .gui_common import GuiCommon


class Alert(QtWidgets.QMessageBox):
    """
    A class to display an alert box dialog.

    Args:
        common: Reference to the common GUI object for logging.
        message: The message to display in the alert dialog.
        icon: The icon to display alongside the alert message (default: NoIcon).
        buttons: Buttons to display in the alert (default: Ok).
        autostart: If True, the dialog automatically opens (default: True).
        title: Title of the dialog window (default: "OnionShare").
    """
    
    def __init__(self, common, message, icon=QtWidgets.QMessageBox.NoIcon, buttons=QtWidgets.QMessageBox.Ok, autostart=True, title="OnionShare"):
        super().__init__(None)
        self.common = common
        self.common.log("Alert", "__init__")

        self.setWindowTitle(title)
        self.setWindowIcon(QtGui.QIcon(GuiCommon.get_resource_path("images/logo.png")))
        self.setText(message)
        self.setIcon(icon)
        self.setStandardButtons(buttons)

        if autostart:
            self.exec()


class AddFileDialog(QtWidgets.QFileDialog):
    """
    Customized version of QFileDialog to allow selecting both files and folders.

    Note: Not compatible with macOS due to the sandbox requiring native dialogs.
          Only usable on Windows, Linux, and BSD.

    Args:
        common: Reference to the common GUI object for logging.
    """
    
    def __init__(self, common, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.common = common
        self.common.log("AddFileDialog", "__init__")

        self.setOption(self.Option.DontUseNativeDialog, True)
        self.setOption(self.Option.ReadOnly, True)
        self.setOption(self.Option.ShowDirsOnly, False)
        self.setFileMode(self.FileMode.ExistingFiles)

        # Allow multi-selection in both tree view and list view
        tree_view = self.findChild(QtWidgets.QTreeView)
        tree_view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        
        list_view = self.findChild(QtWidgets.QListView, "listView")
        list_view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

    def accept(self):
        """
        Override accept to log the action before closing the dialog.
        """
        self.common.log("AddFileDialog", "accept")
        super().accept()


class MinimumSizeWidget(QtWidgets.QWidget):
    """
    A widget with a specified minimum width and height to force layouts to behave.

    Args:
        width: Minimum width of the widget.
        height: Minimum height of the widget.
    """
    
    def __init__(self, width, height):
        super().__init__()
        self.setMinimumWidth(width)
        self.setMinimumHeight(height)


class Image(qrcode.image.base.BaseImage):
    """
    Custom QR Code image class for use with PyQt pixmaps.

    Args:
        border: Size of the border around the QR code.
        width: Width of the QR code in pixels.
        box_size: Size of each box in the QR code.
    """
    
    def __init__(self, border, width, box_size, *args, **kwargs):
        self.border = border
        self.width = width
        self.box_size = box_size
        size = (width + border * 2) * box_size
        self._image = QtGui.QImage(size, size, QtGui.QImage.Format_RGB16)
        self._image.fill(QtCore.Qt.white)

    def pixmap(self):
        """
        Convert the QR code image to a QPixmap for display in the GUI.
        """
        return QtGui.QPixmap.fromImage(self._image)

    def drawrect(self, row, col):
        """
        Draw a single black rectangle (QR code module) at the specified row and column.
        
        Args:
            row: The row of the QR code matrix.
            col: The column of the QR code matrix.
        """
        painter = QtGui.QPainter(self._image)
        painter.fillRect(
            (col + self.border) * self.box_size,
            (row + self.border) * self.box_size,
            self.box_size,
            self.box_size,
            QtCore.Qt.black,
        )

    def save(self, stream, kind=None):
        """
        Empty method for compatibility with the base class.
        """
        pass


class QRCodeDialog(QtWidgets.QDialog):
    """
    A dialog window to display a QR code.

    Args:
        common: Reference to the common GUI object for logging.
        title: Title of the QR code dialog.
        text: The text to encode in the QR code.
    """
    
    def __init__(self, common, title, text):
        super().__init__()

        self.common = common
        self.common.log("QRCodeDialog", "__init__")

        # QR code title label
        self.qr_label_title = QtWidgets.QLabel(self)
        self.qr_label_title.setText(title)
        self.qr_label_title.setAlignment(QtCore.Qt.AlignCenter)

        # QR code image display
        self.qr_label = QtWidgets.QLabel(self)
        self.qr_label.setPixmap(qrcode.make(text, image_factory=Image).pixmap())
        self.qr_label.setScaledContents(True)
        self.qr_label.setFixedSize(350, 350)

        self.setWindowTitle(strings._("gui_qr_code_dialog_title"))
        self.setWindowIcon(QtGui.QIcon(GuiCommon.get_resource_path("images/logo.png")))

        # Layout for the dialog
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.qr_label_title)
        layout.addWidget(self.qr_label)

        self.exec()
