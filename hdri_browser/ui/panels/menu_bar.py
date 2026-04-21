# ==================================================
# EXR Browser - Menu Bar Panel
# ==================================================

from PySide6 import QtWidgets, QtGui


class MenuBarPanel:
    """
    Builds the top menu bar for the EXR Browser.
    Methods are called from EXRBrowser._build_menu().
    """

    def _build_menu(self, parent):
        menu_bar = QtWidgets.QMenuBar(self)

        file_menu = menu_bar.addMenu("File")

        settings_action = QtGui.QAction("Settings", self)
        settings_action.triggered.connect(self._show_settings_dialog)
        file_menu.addAction(settings_action)

        load_action = QtGui.QAction("Load Configured HDRI Folders", self)
        load_action.triggered.connect(self.load_configured_folders)
        file_menu.addAction(load_action)

        scan_action = QtGui.QAction("Scan for new HDRI files", self)
        scan_action.triggered.connect(self.scan_for_new_files)
        file_menu.addAction(scan_action)

        parent.addWidget(menu_bar)


# ==================================================
# End Of Menu Bar Panel
# ==================================================
