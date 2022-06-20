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
import shutil
from pkg_resources import resource_filename
from PySide2 import QtCore, QtWidgets, QtGui

from . import strings
from onionshare_cli.onion import (
    Onion,
    TorErrorInvalidSetting,
    TorErrorAutomatic,
    TorErrorSocketPort,
    TorErrorSocketFile,
    TorErrorMissingPassword,
    TorErrorUnreadableCookieFile,
    TorErrorAuthError,
    TorErrorProtocolError,
    BundledTorTimeout,
    BundledTorBroken,
    TorTooOldEphemeral,
    TorTooOldStealth,
    PortNotAvailable,
)
from onionshare_cli.meek import Meek


class GuiCommon:
    """
    The shared code for all of the OnionShare GUI.
    """

    MODE_SHARE = "share"
    MODE_RECEIVE = "receive"
    MODE_WEBSITE = "website"
    MODE_CHAT = "chat"

    def __init__(self, common, qtapp, local_only):
        self.common = common
        self.qtapp = qtapp
        self.local_only = local_only

        # Are we running in a flatpak package?
        self.is_flatpak = os.path.exists("/.flatpak-info")

        # Load settings
        self.common.load_settings()

        # Load strings
        strings.load_strings(self.common, self.get_resource_path("locale"))

        # Start the Onion
        self.onion = Onion(common, get_tor_paths=self.get_tor_paths)

        # Lock filename
        self.lock_filename = os.path.join(self.common.build_data_dir(), "lock")

        # Events filenames
        self.events_dir = os.path.join(self.common.build_data_dir(), "events")
        if not os.path.exists(self.events_dir):
            os.makedirs(self.events_dir, 0o700, True)
        self.events_filename = os.path.join(self.events_dir, "events")

        # Instantiate Meek, which is used to bypass censorship
        self.meek = Meek(self.common, get_tor_paths=self.get_tor_paths)

        self.css = self.get_css(qtapp.color_mode)
        self.color_mode = qtapp.color_mode

    def get_css(self, color_mode):
        header_color = "#4E064F"  # purple in light
        title_color = "#333333"  # dark gray color in main window
        stop_button_color = "#d0011b"  # red button color for stopping server
        new_tab_button_background = "#ffffff"
        new_tab_button_border = "#efeff0"
        new_tab_button_text_color = "#4e0d4e"
        downloads_uploads_progress_bar_border_color = "#4E064F"
        downloads_uploads_progress_bar_chunk_color = "#4E064F"
        share_zip_progess_bar_border_color = "#4E064F"
        share_zip_progess_bar_chunk_color = "#4E064F"
        history_background_color = "#ffffff"
        history_label_color = "#000000"
        settings_error_color = "#FF0000"
        if color_mode == "dark":
            header_color = "#F2F2F2"
            title_color = "#F2F2F2"
            stop_button_color = "#C32F2F"
            new_tab_button_background = "#5F5F5F"
            new_tab_button_border = "#878787"
            new_tab_button_text_color = "#FFFFFF"
            share_zip_progess_bar_border_color = "#F2F2F2"
            history_background_color = "#191919"
            history_label_color = "#ffffff"
            settings_error_color = "#FF9999"

        return {
            # OnionShareGui styles
            "tab_widget": """
                QTabBar::tab { width: 170px; height: 30px; }
                """,
            "tab_widget_new_tab_button": """
                QPushButton {
                    font-weight: bold;
                    font-size: 20px;
                }""",
            "settings_subtab_bar": """
                QTabBar::tab {
                    background: transparent;
                }
                QTabBar::tab:selected {
                    border-bottom: 3px solid;
                    border-color: #4E064F;
                    padding: 3px
                }""",
            "mode_new_tab_button": """
                QPushButton {
                    font-weight: bold;
                    font-size: 30px;
                    color: #601f61;
                }""",
            "mode_header_label": """
                QLabel {
                    color: """
            + header_color
            + """;
                    font-size: 48px;
                    margin-bottom: 16px;
                }""",
            "settings_button": """
                QPushButton {
                    border: 0;
                    border-radius: 0;
                }""",
            "server_status_indicator_label": """
                QLabel {
                    font-style: italic;
                    color: #666666;
                    padding: 2px;
                }""",
            "status_bar": """
                QStatusBar {
                    font-style: italic;
                    color: #666666;
                }
                QStatusBar::item {
                    border: 0px;
                }""",
            "autoconnect_start_button": """
                QPushButton {
                    background-color: #5fa416;
                    color: #ffffff;
                    padding: 10px;
                    border: 0;
                    border-radius: 5px;
                }""",
            "autoconnect_configure_button": """
                QPushButton {
                    padding: 9px 29px;
                    color: #3f7fcf;
                    text-align: left;
                }""",
            "enable_autoconnect": """
                QCheckBox {
                    margin-top: 30px;
                    background: #FCFCFC;
                    color: #000000;
                    border: 1px solid #DDDBDA;
                    border-radius: 8px;
                    padding: 24px 16px;
                }
                QCheckBox::indicator {
                    width: 0;
                    height: 0;
                }""",
            "autoconnect_countries_combobox": """
                QComboBox {
                    padding: 10px;
                    font-size: 16px;
                    margin-left: 32px;
                }
                QComboBox:disabled {
                    color: #666666;
                }
                """,
            "autoconnect_task_label": """
                QLabel {
                    font-weight: bold;
                }
                """,
            "autoconnect_failed_to_connect_label": """
                QLabel {
                    font-size: 18px;
                    font-weight: bold;
                }""",
            "autoconnect_bridge_setting_options": """
                QGroupBox {
                    border: 0;
                    border-color: transparent;
                    background-color: transparent;
                    font-weight: bold;
                    margin-top: 16px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                }""",
            # Common styles between modes and their child widgets
            "mode_settings_toggle_advanced": """
                QPushButton {
                    color: #3f7fcf;
                    text-align: left;
                }
                """,
            "mode_info_label": """
                QLabel {
                    font-size: 12px;
                    color: #666666;
                }
                """,
            "server_status_url": """
                QLabel {
                    background-color: #ffffff;
                    color: #000000;
                    padding: 10px;
                    border: 1px solid #666666;
                    font-size: 12px;
                }
                """,
            "server_status_url_buttons": """
                QPushButton {
                    padding: 4px 8px;
                    text-align: center;
                }
                """,
            "server_status_button_stopped": """
                QPushButton {
                    background-color: #5fa416;
                    color: #ffffff;
                    padding: 10px 30px 10px 30px;
                    border: 0;
                    border-radius: 5px;
                }""",
            "server_status_button_working": """
                QPushButton {
                    background-color: #4c8211;
                    color: #ffffff;
                    padding: 10px 30px 10px 30px;
                    border: 0;
                    border-radius: 5px;
                    font-style: italic;
                }""",
            "server_status_button_started": """
                QPushButton {
                    background-color: """
            + stop_button_color
            + """;
                    color: #ffffff;
                    padding: 10px 30px 10px 30px;
                    border: 0;
                    border-radius: 5px;
                }""",
            "downloads_uploads_not_empty": """
                QWidget{
                    background-color: """
            + history_background_color
            + """;
                }""",
            "downloads_uploads_empty": """
                QWidget {
                    background-color: """
            + history_background_color
            + """;
                    border: 1px solid #999999;
                }
                QWidget QLabel {
                    background-color: none;
                    border: 0px;
                }
                """,
            "downloads_uploads_empty_text": """
                QLabel {
                    color: #999999;
                }""",
            "downloads_uploads_label": """
                QLabel {
                    font-weight: bold;
                    font-size 14px;
                    text-align: center;
                    background-color: none;
                    border: none;
                }""",
            "downloads_uploads_clear": """
                QPushButton {
                    color: #3f7fcf;
                }
                """,
            "download_uploads_indicator": """
                QLabel {
                    color: #ffffff;
                    background-color: #f44449;
                    font-weight: bold;
                    font-size: 10px;
                    padding: 2px;
                    border-radius: 7px;
                    text-align: center;
                }""",
            "downloads_uploads_progress_bar": """
                QProgressBar {
                    border: 1px solid """
            + downloads_uploads_progress_bar_border_color
            + """;
                    background-color: #ffffff !important;
                    text-align: center;
                    color: #9b9b9b;
                    font-size: 14px;
                }
                QProgressBar::chunk {
                    background-color: """
            + downloads_uploads_progress_bar_chunk_color
            + """;
                    width: 10px;
                }""",
            "history_default_label": """
                QLabel {
                    color: """
            + history_label_color
            + """;
                }""",
            "history_individual_file_timestamp_label": """
                QLabel {
                    color: #666666;
                }""",
            "history_individual_file_status_code_label_2xx": """
                QLabel {
                    color: #008800;
                }""",
            "history_individual_file_status_code_label_4xx": """
                QLabel {
                    color: #cc0000;
                }""",
            "tor_not_connected_label": """
                QLabel {
                    font-size: 16px;
                    font-style: italic;
                }""",
            # New tab
            "new_tab_button_image": """
                QLabel {
                    padding: 30px;
                    text-align: center;
                }
                """,
            "new_tab_button_text": """
                QLabel {
                    border: 1px solid """
            + new_tab_button_border
            + """;
                    border-radius: 4px;
                    background-color: """
            + new_tab_button_background
            + """;
                    text-align: center;
                    color: """
            + new_tab_button_text_color
            + """;
                }
                """,
            "new_tab_title_text": """
                QLabel {
                    text-align: center;
                    color: """
            + title_color
            + """;
                    font-size: 25px;
                }
                """,
            # Share mode and child widget styles
            "share_delete_all_files_button": """
                QPushButton {
                    color: #3f7fcf;
                }
                """,
            "share_zip_progess_bar": """
                QProgressBar {
                    border: 1px solid """
            + share_zip_progess_bar_border_color
            + """;
                    background-color: #ffffff !important;
                    text-align: center;
                    color: #9b9b9b;
                }
                QProgressBar::chunk {
                    border: 0px;
                    background-color: """
            + share_zip_progess_bar_chunk_color
            + """;
                    width: 10px;
                }""",
            "share_filesize_warning": """
                QLabel {
                    padding: 10px 0;
                    font-weight: bold;
                    color: """
            + title_color
            + """;
                }
                """,
            "share_file_selection_drop_here_header_label": """
                QLabel {
                    color: """
            + header_color
            + """;
                    font-size: 48px;
                }""",
            "share_file_selection_drop_here_label": """
                QLabel {
                    color: #666666;
                }""",
            "share_file_selection_drop_count_label": """
                QLabel {
                    color: #ffffff;
                    background-color: #f44449;
                    font-weight: bold;
                    padding: 5px 10px;
                    border-radius: 10px;
                }""",
            "share_file_list_drag_enter": """
                FileList {
                    border: 3px solid #538ad0;
                }
                """,
            "share_file_list_drag_leave": """
                FileList {
                    border: none;
                }
                """,
            "share_file_list_item_size": """
                QLabel {
                    color: #666666;
                    font-size: 11px;
                }""",
            # Receive mode and child widget styles
            "receive_file": """
                QWidget {
                    background-color: #ffffff;
                }
                """,
            "receive_file_size": """
                QLabel {
                    color: #666666;
                    font-size: 11px;
                }""",
            "receive_message_button": """
                QPushButton {
                    padding: 5px 10px;
                }""",
            # Tor Settings dialogs
            "tor_settings_error": """
                QLabel {
                    color: """
            + settings_error_color
            + """;
                }
                """,
        }

    def get_tor_paths(self):
        if self.common.platform == "Linux":
            base_path = self.get_resource_path("tor")
            if base_path and os.path.isdir(base_path):
                self.common.log(
                    "GuiCommon", "get_tor_paths", "using paths in resources"
                )
                tor_path = os.path.join(base_path, "tor")
                tor_geo_ip_file_path = os.path.join(base_path, "geoip")
                tor_geo_ipv6_file_path = os.path.join(base_path, "geoip6")
                obfs4proxy_file_path = os.path.join(base_path, "obfs4proxy")
                snowflake_file_path = os.path.join(base_path, "snowflake-client")
                meek_client_file_path = os.path.join(base_path, "meek-client")
            else:
                # Fallback to looking in the path
                self.common.log("GuiCommon", "get_tor_paths", "using paths from PATH")
                tor_path = shutil.which("tor")
                obfs4proxy_file_path = shutil.which("obfs4proxy")
                snowflake_file_path = shutil.which("snowflake-client")
                meek_client_file_path = shutil.which("meek-client")
                prefix = os.path.dirname(os.path.dirname(tor_path))
                tor_geo_ip_file_path = os.path.join(prefix, "share/tor/geoip")
                tor_geo_ipv6_file_path = os.path.join(prefix, "share/tor/geoip6")

        if self.common.platform == "Windows":
            base_path = self.get_resource_path("tor")
            tor_path = os.path.join(base_path, "tor.exe")
            obfs4proxy_file_path = os.path.join(base_path, "obfs4proxy.exe")
            snowflake_file_path = os.path.join(base_path, "snowflake-client.exe")
            meek_client_file_path = os.path.join(base_path, "meek-client.exe")
            tor_geo_ip_file_path = os.path.join(base_path, "geoip")
            tor_geo_ipv6_file_path = os.path.join(base_path, "geoip6")
        elif self.common.platform == "Darwin":
            base_path = self.get_resource_path("tor")
            tor_path = os.path.join(base_path, "tor")
            obfs4proxy_file_path = os.path.join(base_path, "obfs4proxy")
            snowflake_file_path = os.path.join(base_path, "snowflake-client")
            meek_client_file_path = os.path.join(base_path, "meek-client")
            tor_geo_ip_file_path = os.path.join(base_path, "geoip")
            tor_geo_ipv6_file_path = os.path.join(base_path, "geoip6")
        elif self.common.platform == "BSD":
            tor_path = "/usr/local/bin/tor"
            tor_geo_ip_file_path = "/usr/local/share/tor/geoip"
            tor_geo_ipv6_file_path = "/usr/local/share/tor/geoip6"
            obfs4proxy_file_path = "/usr/local/bin/obfs4proxy"
            meek_client_file_path = "/usr/local/bin/meek-client"
            snowflake_file_path = "/usr/local/bin/snowflake-client"

        return (
            tor_path,
            tor_geo_ip_file_path,
            tor_geo_ipv6_file_path,
            obfs4proxy_file_path,
            snowflake_file_path,
            meek_client_file_path,
        )

    @staticmethod
    def get_resource_path(filename):
        """
        Returns the absolute path of a resource
        """
        try:
            return resource_filename("onionshare", os.path.join("resources", filename))
        except KeyError:
            return None

    @staticmethod
    def get_translated_tor_error(e):
        """
        Takes an exception defined in onion.py and returns a translated error message
        """
        if type(e) is TorErrorInvalidSetting:
            return strings._("settings_error_unknown")
        elif type(e) is TorErrorAutomatic:
            return strings._("settings_error_automatic")
        elif type(e) is TorErrorSocketPort:
            return strings._("settings_error_socket_port").format(e.args[0], e.args[1])
        elif type(e) is TorErrorSocketFile:
            return strings._("settings_error_socket_file").format(e.args[0])
        elif type(e) is TorErrorMissingPassword:
            return strings._("settings_error_missing_password")
        elif type(e) is TorErrorUnreadableCookieFile:
            return strings._("settings_error_unreadable_cookie_file")
        elif type(e) is TorErrorAuthError:
            return strings._("settings_error_auth").format(e.args[0], e.args[1])
        elif type(e) is TorErrorProtocolError:
            return strings._("error_tor_protocol_error").format(e.args[0])
        elif type(e) is BundledTorTimeout:
            return strings._("settings_error_bundled_tor_timeout")
        elif type(e) is BundledTorBroken:
            return strings._("settings_error_bundled_tor_broken").format(e.args[0])
        elif type(e) is TorTooOldEphemeral:
            return strings._("error_ephemeral_not_supported")
        elif type(e) is TorTooOldStealth:
            return strings._("error_stealth_not_supported")
        elif type(e) is PortNotAvailable:
            return strings._("error_port_not_available")
        return None


class ToggleCheckbox(QtWidgets.QCheckBox):
    def __init__(self, text):
        super(ToggleCheckbox, self).__init__(text)
        # Set default parameters
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.w = 50
        self.h = 24
        self.bg_color = "#D4D4D4"
        self.circle_color = "#BDBDBD"
        self.active_color = "#4E0D4E"
        self.inactive_color = ""

    def hitButton(self, pos):
        return self.toggleRect.contains(pos)

    def paintEvent(self, e):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(QtCore.Qt.NoPen)
        opt = QtWidgets.QStyleOptionButton()
        opt.init(self)
        self.initStyleOption(opt)
        s = self.style()
        s.drawControl(QtWidgets.QStyle.CE_CheckBox, opt, painter, self)

        rect = QtCore.QRect(
            s.subElementRect(QtWidgets.QStyle.SE_CheckBoxContents, opt, self)
        )
        x = (
            rect.width() - rect.x() - self.w + 20
        )  # 20 is the padding between text and toggle
        y = (
            self.height() / 2 - self.h / 2 + 16
        )  # 16 is the padding top for the checkbox
        self.toggleRect = QtCore.QRect(x, y, self.w, self.h)
        painter.setBrush(QtGui.QColor(self.bg_color))
        painter.drawRoundedRect(x, y, self.w, self.h, self.h / 2, self.h / 2)
        if not self.isChecked():
            painter.setBrush(QtGui.QColor(self.circle_color))
            painter.drawEllipse(x, y - 3, self.h + 6, self.h + 6)
        else:
            painter.setBrush(QtGui.QColor(self.active_color))
            painter.drawEllipse(
                x + self.w - (self.h + 6), y - 3, self.h + 6, self.h + 6
            )

        painter.end()
