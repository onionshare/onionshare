# -*- coding: utf-8 -*-
"""
OnionShare | https://onionshare.org/

Copyright (C) 2014-2021 Micah Lee, et al. <micah@micahflee.com>

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

import json
import os
from PySide2 import QtCore, QtWidgets, QtGui

from onionshare_cli.censorship import (
    CensorshipCircumvention,
    CensorshipCircumventionError,
)
from onionshare_cli.meek import (
    MeekNotRunning,
    MeekNotFound,
)
from onionshare_cli.settings import Settings

from . import strings
from .gui_common import GuiCommon, ToggleCheckbox
from .tor_connection import TorConnectionWidget
from .update_checker import UpdateThread
from .widgets import Alert


class AutoConnectTab(QtWidgets.QWidget):
    """
    Initial Tab that appears in the very beginning to ask user if
    should auto connect.
    """

    close_this_tab = QtCore.Signal()
    tor_is_connected = QtCore.Signal()
    tor_is_disconnected = QtCore.Signal()

    def __init__(self, common, tab_id, status_bar, window, parent=None):
        super(AutoConnectTab, self).__init__()
        self.common = common
        self.common.log("AutoConnectTab", "__init__")

        self.status_bar = status_bar
        self.tab_id = tab_id
        self.window = window
        self.parent = parent

        # Was auto connected?
        self.curr_settings = Settings(common)
        self.curr_settings.load()
        self.auto_connect_enabled = self.curr_settings.get("auto_connect")

        # Rocket ship animation images
        self.anim_stars = AnimStars(self, self.window)
        self.anim_ship = AnimShip(self, self.window)
        self.anim_smoke = AnimSmoke(self, self.window)

        # Onionshare logo
        self.image_label = QtWidgets.QLabel()
        self.image_label.setPixmap(
            QtGui.QPixmap.fromImage(
                QtGui.QImage(
                    GuiCommon.get_resource_path(
                        os.path.join(
                            "images", f"{common.gui.color_mode}_logo_text_bg.png"
                        )
                    )
                )
            )
        )
        self.image_label.setFixedSize(322, 65)
        image_layout = QtWidgets.QVBoxLayout()
        image_layout.addWidget(self.image_label)
        self.image = QtWidgets.QWidget()
        self.image.setLayout(image_layout)

        # First launch widget
        self.first_launch_widget = AutoConnectFirstLaunchWidget(
            self.common, self.curr_settings
        )
        self.first_launch_widget.toggle_auto_connect.connect(self.toggle_auto_connect)
        self.first_launch_widget.connect_clicked.connect(
            self.first_launch_widget_connect_clicked
        )
        self.first_launch_widget.open_tor_settings.connect(self.open_tor_settings)
        self.first_launch_widget.show()

        # Use bridge widget
        self.use_bridge_widget = AutoConnectUseBridgeWidget(self.common)
        self.use_bridge_widget.connect_clicked.connect(self.use_bridge_connect_clicked)
        self.use_bridge_widget.try_again_clicked.connect(
            self.first_launch_widget_connect_clicked
        )
        self.use_bridge_widget.open_tor_settings.connect(self.open_tor_settings)
        self.use_bridge_widget.hide()

        # Tor connection widget
        self.tor_con = TorConnectionWidget(self.common, self.status_bar)
        self.tor_con.success.connect(self.tor_con_success)
        self.tor_con.fail.connect(self.tor_con_fail)
        self.tor_con.update_progress.connect(self.anim_stars.update)
        self.tor_con.update_progress.connect(self.anim_ship.update)
        self.tor_con.update_progress.connect(self.anim_smoke.update)
        self.tor_con.hide()

        # Layout
        content_layout = QtWidgets.QVBoxLayout()
        content_layout.addStretch()
        content_layout.addWidget(self.image)
        content_layout.addWidget(self.first_launch_widget)
        content_layout.addWidget(self.use_bridge_widget)
        content_layout.addWidget(self.tor_con)
        content_layout.addStretch()
        content_layout.setAlignment(QtCore.Qt.AlignCenter)
        content_widget = QtWidgets.QWidget()
        content_widget.setLayout(content_layout)

        self.layout = QtWidgets.QHBoxLayout()
        self.layout.addWidget(content_widget)
        self.layout.addStretch()

        self.setLayout(self.layout)

    def check_autoconnect(self):
        """
        After rendering, check if autoconnect was clicked, then start connecting
        """
        self.common.log("AutoConnectTab", "autoconnect_checking")
        if self.auto_connect_enabled:
            self.first_launch_widget.enable_autoconnect_checkbox.setChecked(True)
            self.first_launch_widget_connect_clicked()

    def toggle_auto_connect(self):
        """
        Auto connect checkbox clicked
        """
        self.common.log("AutoConnectTab", "autoconnect_checkbox_clicked")
        self.curr_settings.set(
            "auto_connect",
            self.first_launch_widget.enable_autoconnect_checkbox.isChecked(),
        )
        self.curr_settings.save()

    def open_tor_settings(self):
        self.parent.open_settings_tab(from_autoconnect=True, active_tab="tor")

    def first_launch_widget_connect_clicked(self):
        """
        Connect button in first launch widget clicked. Try to connect to tor.
        """
        self.common.log("AutoConnectTab", "first_launch_widget_connect_clicked")
        self.first_launch_widget.hide_buttons()

        self.tor_con.show()
        self.tor_con.start(self.curr_settings)

    def _got_bridges(self):
        self.use_bridge_widget.progress.hide()
        self.use_bridge_widget.progress_label.hide()
        # Try and connect again
        self.common.log(
            "AutoConnectTab",
            "_got_bridges",
            "Got bridges. Trying to reconnect to Tor",
        )
        self.tor_con.show()
        self.tor_con.start(self.curr_settings)

    def _got_no_bridges(self):
        # If we got no bridges, even after trying the default bridges
        # provided by the Censorship API, try connecting again using
        # our built-in obfs4 bridges
        self.curr_settings.set("bridges_type", "built-in")
        self.curr_settings.set("bridges_builtin_pt", "obfs4")
        self.curr_settings.set("bridges_enabled", True)
        self.curr_settings.save()

        self._got_bridges()

    def _censorship_progress_update(self, progress, summary):
        self.use_bridge_widget.progress.setValue(int(progress))
        self.use_bridge_widget.progress_label.setText(
            f"<strong>{strings._('gui_autoconnect_circumventing_censorship')}</strong><br>{summary}"
        )

    def network_connection_error(self):
        """
        Display an error if there simply seems no network connection.
        """
        self.use_bridge_widget.connection_status_label.setText(
            strings._("gui_autoconnect_failed_to_connect_to_tor")
        )
        self.use_bridge_widget.progress.hide()
        self.use_bridge_widget.progress_label.hide()
        self.use_bridge_widget.error_label.show()
        self.use_bridge_widget.country_combobox.setEnabled(True)
        self.use_bridge_widget.show_buttons()
        self.use_bridge_widget.show()

    def use_bridge_connect_clicked(self):
        """
        Connect button in use bridge widget clicked.
        """
        self.common.log(
            "AutoConnectTab",
            "use_bridge_connect_clicked",
            "Trying to automatically obtain bridges",
        )
        self.use_bridge_widget.hide_buttons()
        self.use_bridge_widget.progress.show()
        self.use_bridge_widget.progress_label.show()

        if self.use_bridge_widget.detect_automatic_radio.isChecked():
            country = False
        else:
            country = self.use_bridge_widget.country_combobox.currentData().lower()

        self._censorship_progress_update(
            50, strings._("gui_autoconnect_circumventing_censorship_starting_meek")
        )
        try:
            self.common.gui.meek.start()
            self.censorship_circumvention = CensorshipCircumvention(
                self.common, self.common.gui.meek
            )
            self._censorship_progress_update(
                75,
                strings._(
                    "gui_autoconnect_circumventing_censorship_requesting_bridges"
                ),
            )
            bridge_settings = self.censorship_circumvention.request_settings(
                country=country
            )

            if not bridge_settings:
                # Fall back to trying the default bridges from the API
                self.common.log(
                    "AutoConnectTab",
                    "use_bridge_connect_clicked",
                    "Falling back to trying default bridges provided by the Censorship Circumvention API",
                )
                bridge_settings = (
                    self.censorship_circumvention.request_default_bridges()
                )

            self.common.gui.meek.cleanup()

            if bridge_settings and self.censorship_circumvention.save_settings(
                self.curr_settings, bridge_settings
            ):
                self._censorship_progress_update(
                    100,
                    strings._("gui_autoconnect_circumventing_censorship_got_bridges"),
                )
                self._got_bridges()
            else:
                self._got_no_bridges()
        except (
            MeekNotRunning,
            MeekNotFound,
        ) as e:
            self._got_no_bridges()
        except CensorshipCircumventionError as e:
            self.common.log(
                "AutoConnectTab",
                "use_bridge_connect_clicked",
                "Request to the Tor Censorship Circumvention API failed. No network connection?",
            )
            self.network_connection_error()

    def check_for_updates(self):
        """
        Check for OnionShare updates in a new thread, if enabled.
        """
        if self.common.platform == "Windows" or self.common.platform == "Darwin":
            if self.common.settings.get("use_autoupdate"):

                def update_available(update_url, installed_version, latest_version):
                    Alert(
                        self.common,
                        strings._("update_available").format(
                            update_url, installed_version, latest_version
                        ),
                    )

                self.update_thread = UpdateThread(self.common, self.common.gui.onion)
                self.update_thread.update_available.connect(update_available)
                self.update_thread.start()

    def tor_con_success(self):
        """
        Finished testing tor connection.
        """
        self.tor_con.hide()
        self.first_launch_widget.show_buttons()
        self.use_bridge_widget.show_buttons()
        self.use_bridge_widget.progress.hide()
        self.use_bridge_widget.progress_label.hide()

        if self.common.gui.onion.is_authenticated() and not self.tor_con.wasCanceled():
            # Tell the tabs that Tor is connected
            self.tor_is_connected.emit()
            # After connecting to Tor, check for updates
            self.check_for_updates()
            # Close the tab
            self.close_this_tab.emit()

    def tor_con_fail(self, msg):
        """
        Finished testing tor connection.
        """
        self.tor_con.hide()

        # If there is a message, update the text of the bridge widget
        if msg:
            self.use_bridge_widget.connection_error_message.setText(msg)

        # If we're on first launch, check if wasCanceled
        # If cancelled, stay in first launch widget and show buttons
        # Else, switch to use bridge
        if self.first_launch_widget.isVisible():
            if self.tor_con.wasCanceled():
                self.first_launch_widget.show_buttons()
            else:
                self.first_launch_widget.show_buttons()
                self.first_launch_widget.hide()
                self.use_bridge_widget.show()
        else:
            self.use_bridge_widget.show_buttons()

    def reload_settings(self):
        """
        Reload the latest Tor settings, and reset to show the
        first-launch widget if it had been hidden.
        """
        self.curr_settings.load()
        self.auto_connect_enabled = self.curr_settings.get("auto_connect")
        self.first_launch_widget.enable_autoconnect_checkbox.setChecked(
            self.auto_connect_enabled
        )
        self.use_bridge_widget.hide()
        self.first_launch_widget.show_buttons()
        self.first_launch_widget.show()


class Anim(QtWidgets.QLabel):
    """
    Rocket ship animation base class
    """

    force_update = QtCore.Signal(int)

    def __init__(self, parent, window, w, h, filename):
        super(Anim, self).__init__(parent=parent)

        self.window = window
        self.window.window_resized.connect(self.update_same_percent)

        self.w = w
        self.h = h
        self.percent = 0
        self.used_percentages = []

        self.setPixmap(
            QtGui.QPixmap.fromImage(
                QtGui.QImage(
                    GuiCommon.get_resource_path(os.path.join("images", filename))
                )
            )
        )
        self.setFixedSize(self.w, self.h)
        self.update(0)

        self.force_update.connect(self.update)

    def update_same_percent(self):
        self.update(self.percent)

    def update(self, percent):
        self.percent = percent
        self.move()
        self.setGeometry(int(self.x), int(self.y), int(self.w), int(self.h))

    def move(self):
        # Implement in child
        pass


class AnimStars(Anim):
    """
    Rocket ship animation part: stars
    """

    def __init__(self, parent, window):
        super(AnimStars, self).__init__(
            parent, window, 740, 629, "tor-connect-stars.png"
        )

    def move(self):
        self.x = self.window.width() - self.w
        self.y = 0
        # Stars don't move until 10%, then move down
        if self.percent >= 10:
            self.y += self.percent * 6.6


class AnimShip(Anim):
    """
    Rocket ship animation part: ship
    """

    def __init__(self, parent, window):
        super(AnimShip, self).__init__(parent, window, 239, 545, "tor-connect-ship.png")

    def move(self):
        self.x = self.window.width() - self.w - 150
        self.y = self.window.height() - self.h - 40
        # Ship moves up
        self.y -= self.percent * 6.6


class AnimSmoke(Anim):
    """
    Rocket ship animation part: smoke
    """

    def __init__(self, parent, window):
        super(AnimSmoke, self).__init__(
            parent, window, 522, 158, "tor-connect-smoke.png"
        )

    def move(self):
        self.x = self.window.width() - self.w
        self.y = self.window.height() - self.h + 50
        # Smoke moves up until 50%, then moves down
        self.y -= self.percent * 6.6
        if self.percent >= 50:
            self.y += self.percent * 6.7


class AutoConnectFirstLaunchWidget(QtWidgets.QWidget):
    """
    When you first launch OnionShare, this is the widget that is displayed
    """

    toggle_auto_connect = QtCore.Signal()
    connect_clicked = QtCore.Signal()
    open_tor_settings = QtCore.Signal()

    def __init__(self, common, settings):
        super(AutoConnectFirstLaunchWidget, self).__init__()
        self.common = common
        self.common.log("AutoConnectFirstLaunchWidget", "__init__")

        self.settings = settings

        # Description and checkbox
        description_label = QtWidgets.QLabel(strings._("gui_autoconnect_description"))
        self.enable_autoconnect_checkbox = ToggleCheckbox(
            strings._("gui_enable_autoconnect_checkbox")
        )
        self.enable_autoconnect_checkbox.setChecked(self.settings.get("auto_connect"))
        self.enable_autoconnect_checkbox.clicked.connect(self._toggle_auto_connect)
        self.enable_autoconnect_checkbox.setFixedWidth(400)
        self.enable_autoconnect_checkbox.setStyleSheet(
            common.gui.css["enable_autoconnect"]
        )
        description_layout = QtWidgets.QVBoxLayout()
        description_layout.addWidget(description_label)
        description_layout.addWidget(self.enable_autoconnect_checkbox)
        description_widget = QtWidgets.QWidget()
        description_widget.setLayout(description_layout)

        # Buttons
        self.connect_button = QtWidgets.QPushButton(strings._("gui_autoconnect_start"))
        self.connect_button.clicked.connect(self._connect_clicked)
        self.connect_button.setFixedWidth(150)
        self.connect_button.setStyleSheet(common.gui.css["autoconnect_start_button"])
        self.configure_button = QtWidgets.QPushButton(
            strings._("gui_autoconnect_configure")
        )
        self.configure_button.clicked.connect(self._open_tor_settings)
        self.configure_button.setFlat(True)
        self.configure_button.setStyleSheet(
            common.gui.css["autoconnect_configure_button"]
        )
        cta_layout = QtWidgets.QHBoxLayout()
        cta_layout.addWidget(self.connect_button)
        cta_layout.addWidget(self.configure_button)
        cta_widget = QtWidgets.QWidget()
        cta_widget.setLayout(cta_layout)

        # Layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(description_widget)
        layout.addWidget(cta_widget)
        self.setLayout(layout)

    def hide_buttons(self):
        self.connect_button.hide()
        self.configure_button.hide()

    def show_buttons(self):
        self.connect_button.show()
        self.configure_button.show()

    def _toggle_auto_connect(self):
        self.toggle_auto_connect.emit()

    def _connect_clicked(self):
        self.connect_clicked.emit()

    def _open_tor_settings(self):
        self.open_tor_settings.emit()


class AutoConnectUseBridgeWidget(QtWidgets.QWidget):
    """
    If connecting fails, this is the widget that helps the user bypass censorship
    """

    connect_clicked = QtCore.Signal()
    try_again_clicked = QtCore.Signal()
    open_tor_settings = QtCore.Signal()

    def __init__(self, common):
        super(AutoConnectUseBridgeWidget, self).__init__()
        self.common = common
        self.common.log("AutoConnectUseBridgeWidget", "__init__")

        # Heading label when we fail to connect to Tor.
        self.connection_status_label = QtWidgets.QLabel(
            strings._("gui_autoconnect_failed_to_connect_to_tor")
        )
        self.connection_status_label.setTextFormat(QtCore.Qt.RichText)
        self.connection_status_label.setStyleSheet(
            common.gui.css["autoconnect_failed_to_connect_label"]
        )

        # Tor connection error message
        self.connection_error_message = QtWidgets.QLabel(
            strings._("gui_autoconnect_connection_error_msg")
        )
        self.connection_error_message.setTextFormat(QtCore.Qt.RichText)
        self.connection_error_message.setWordWrap(True)
        self.connection_error_message.setContentsMargins(0, 0, 0, 10)

        # Description
        self.description_label = QtWidgets.QLabel(
            strings._("gui_autoconnect_bridge_description")
        )
        self.description_label.setTextFormat(QtCore.Qt.RichText)
        self.description_label.setWordWrap(True)
        self.description_label.setContentsMargins(0, 0, 0, 20)

        # Detection preference
        self.use_bridge = True
        self.no_bridge = QtWidgets.QRadioButton(
            strings._("gui_autoconnect_no_bridge")
        )
        self.no_bridge.toggled.connect(self._toggle_no_bridge)
        self.detect_automatic_radio = QtWidgets.QRadioButton(
            strings._("gui_autoconnect_bridge_detect_automatic")
        )
        self.detect_automatic_radio.toggled.connect(self._detect_automatic_toggled)
        self.detect_manual_radio = QtWidgets.QRadioButton(
            strings._("gui_autoconnect_bridge_detect_manual")
        )
        self.detect_manual_radio.toggled.connect(self._detect_manual_toggled)
        detect_layout = QtWidgets.QVBoxLayout()
        detect_layout.addWidget(self.no_bridge)
        detect_layout.addWidget(self.detect_automatic_radio)
        detect_layout.addWidget(self.detect_manual_radio)
        bridge_setting_options = QtWidgets.QGroupBox(
            strings._("gui_autoconnect_bridge_setting_options")
        )
        bridge_setting_options.setLayout(detect_layout)
        bridge_setting_options.setFlat(True)
        bridge_setting_options.setStyleSheet(
            common.gui.css["autoconnect_bridge_setting_options"]
        )

        # Country list
        locale = self.common.settings.get("locale")
        if not locale:
            locale = "en"

        with open(
            GuiCommon.get_resource_path(os.path.join("countries", f"{locale}.json"))
        ) as f:
            countries = json.loads(f.read())

        self.country_combobox = QtWidgets.QComboBox()
        self.country_combobox.setStyleSheet(
            common.gui.css["autoconnect_countries_combobox"]
        )
        self.country_combobox.setIconSize(QtCore.QSize(26, 20))
        for country_code in countries:
            icon = QtGui.QIcon(
                GuiCommon.get_resource_path(os.path.join("images", "countries", f"{country_code.lower()}.png"))
            )
            self.country_combobox.addItem(icon, countries[country_code], country_code)

        # Task label
        self.task_label = QtWidgets.QLabel()
        self.task_label.setStyleSheet(common.gui.css["autoconnect_task_label"])
        self.task_label.setAlignment(QtCore.Qt.AlignCenter)
        self.task_label.hide()

        # Buttons
        self.connect_button = QtWidgets.QPushButton(
            strings._("gui_autoconnect_start")
        )
        self.connect_button.clicked.connect(self._connect_clicked)
        self.connect_button.setFixedWidth(150)
        self.connect_button.setStyleSheet(common.gui.css["autoconnect_start_button"])

        self.configure_button = QtWidgets.QPushButton(
            strings._("gui_autoconnect_configure")
        )
        self.configure_button.clicked.connect(self._open_tor_settings)
        self.configure_button.setFlat(True)
        self.configure_button.setStyleSheet(
            common.gui.css["autoconnect_configure_button"]
        )

        # Error label
        self.error_label = QtWidgets.QLabel(
            strings._("gui_autoconnect_could_not_connect_to_tor_api")
        )
        self.error_label.setStyleSheet(self.common.gui.css["tor_settings_error"])
        self.error_label.setWordWrap(True)
        self.error_label.hide()

        self.progress = QtWidgets.QProgressBar()
        self.progress.setRange(0, 100)
        self.progress_label = QtWidgets.QLabel(
            strings._("gui_autoconnect_circumventing_censorship")
        )
        self.progress_label.setAlignment(QtCore.Qt.AlignHCenter)
        self.progress.hide()
        self.progress_label.hide()

        cta_layout = QtWidgets.QHBoxLayout()
        cta_layout.addWidget(self.connect_button)
        cta_layout.addWidget(self.configure_button)
        cta_layout.addStretch()
        cta_widget = QtWidgets.QWidget()
        cta_widget.setLayout(cta_layout)

        # Layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.connection_status_label)
        layout.addWidget(self.connection_error_message)
        layout.addWidget(self.description_label)
        layout.addWidget(bridge_setting_options)
        layout.addWidget(self.country_combobox)
        layout.addWidget(self.task_label)
        layout.addWidget(cta_widget)
        layout.addWidget(self.progress)
        layout.addWidget(self.progress_label)
        layout.addWidget(self.error_label)
        self.setLayout(layout)

        self.detect_automatic_radio.setChecked(True)

    def hide_buttons(self):
        self.connect_button.hide()
        self.configure_button.hide()
        self.connection_error_message.hide()
        self.description_label.hide()
        self.error_label.hide()
        self.no_bridge.hide()
        self.detect_automatic_radio.hide()
        self.detect_manual_radio.hide()

    def show_buttons(self):
        self.connect_button.show()
        self.connection_error_message.show()
        self.description_label.show()
        self.configure_button.show()
        self.no_bridge.show()
        self.detect_automatic_radio.show()
        self.detect_manual_radio.show()

    def _toggle_no_bridge(self):
        self.use_bridge = not self.use_bridge

    def _detect_automatic_toggled(self):
        self.country_combobox.setEnabled(False)
        self.country_combobox.hide()

    def _detect_manual_toggled(self):
        self.country_combobox.setEnabled(True)
        self.country_combobox.show()

    def _connect_clicked(self):
        self.country_combobox.setEnabled(False)
        self.hide_buttons()
        self.connection_status_label.setText(
            strings._("gui_autoconnect_trying_to_connect_to_tor")
        )
        print(self.use_bridge)
        if not self.use_bridge:
            self.try_again_clicked.emit()
        else:
            self.connect_clicked.emit()

    def _open_tor_settings(self):
        self.open_tor_settings.emit()
