from PySide2 import QtCore, QtWidgets, QtGui

from onionshare_cli.mode_settings import ModeSettings

from . import strings
from .tab import Tab
from .threads import EventHandlerThread
from .gui_common import GuiCommon
from .tor_settings_tab import TorSettingsTab
from .settings_tab import SettingsTab
from .connection_tab import AutoConnectTab


class SettingsParentTab(QtWidgets.QTabWidget):
    """
    The settings tab widget containing the tor settings
    and app settings subtabs
    """

    bring_to_front = QtCore.Signal()
    close_this_tab = QtCore.Signal()

    def __init__(
        self, common, tab_id, parent=None, active_tab="general", from_autoconnect=False
    ):
        super(SettingsParentTab, self).__init__()
        self.parent = parent
        self.common = common
        self.common.log("SettingsParentTab", "__init__")

        # Keep track of tabs in a dictionary that maps tab_id to tab.
        # Each tab has a unique, auto-incremented id (tab_id). This is different than the
        # tab's index, which changes as tabs are re-arranged.
        self.tabs = {
            "general": 0,
            "tor": 1,
        }
        self.tab_id = tab_id
        self.current_tab_id = self.tabs[active_tab]

        # Use a custom tab bar
        tab_bar = TabBar(self.common)
        self.setTabBar(tab_bar)
        settings_tab = SettingsTab(self.common, self.tabs["general"], parent=self)
        self.tor_settings_tab = TorSettingsTab(
            self.common,
            self.tabs["tor"],
            self.parent.are_tabs_active(),
            self.parent.status_bar,
            parent=self,
            from_autoconnect=from_autoconnect,
        )
        self.addTab(settings_tab, strings._("gui_general_settings_window_title"))
        self.addTab(self.tor_settings_tab, strings._("gui_tor_settings_window_title"))

        # Set up the tab widget
        self.setMovable(False)
        self.setTabsClosable(False)
        self.setUsesScrollButtons(False)
        self.setCurrentIndex(self.current_tab_id)


class TabBar(QtWidgets.QTabBar):
    """
    A custom tab bar
    """

    move_new_tab_button = QtCore.Signal()

    def __init__(self, common):
        super(TabBar, self).__init__()
        self.setStyleSheet(common.gui.css["settings_subtab_bar"])
