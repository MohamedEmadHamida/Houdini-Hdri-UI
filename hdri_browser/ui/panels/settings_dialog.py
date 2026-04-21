# ==================================================
# EXR Browser - Settings Dialog
# ==================================================

import os
from PySide6 import QtWidgets


class SettingsDialogMixin:
    """
    Provides the Settings dialog and all its helper slots.
    Mixed into EXRBrowser so it keeps access to self.file_manager, etc.
    """

    def _show_settings_dialog(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("HDRI Folder Settings")
        dialog.resize(600, 380)

        layout = QtWidgets.QVBoxLayout(dialog)

        info = QtWidgets.QLabel("Add or remove folders to include when loading HDRI files")
        info.setWordWrap(True)
        layout.addWidget(info)

        # ── Cache folder row ─────────────────────────────────────────────────
        cache_layout = QtWidgets.QHBoxLayout()
        self.cache_folder_line = QtWidgets.QLineEdit(dialog)
        self.cache_folder_line.setPlaceholderText("Cache folder path")
        self.cache_folder_line.setText(self.cache_folder)
        cache_layout.addWidget(self.cache_folder_line)

        cache_browse_btn = QtWidgets.QPushButton("Browse")
        cache_browse_btn.clicked.connect(self._settings_browse_cache_folder)
        cache_layout.addWidget(cache_browse_btn)
        layout.addLayout(cache_layout)

        # ── Folder list ──────────────────────────────────────────────────────
        self.folder_list_widget = QtWidgets.QListWidget(dialog)
        self.folder_list_widget.addItems(self.hdri_folders)
        layout.addWidget(self.folder_list_widget)

        # ── Add folder row ───────────────────────────────────────────────────
        add_layout = QtWidgets.QHBoxLayout()
        self.new_folder_input = QtWidgets.QLineEdit(dialog)
        self.new_folder_input.setPlaceholderText("Type folder path or browse and then click Add")
        add_layout.addWidget(self.new_folder_input)

        browse_btn = QtWidgets.QPushButton("Browse")
        browse_btn.clicked.connect(self._settings_browse_folder)
        add_layout.addWidget(browse_btn)

        add_btn = QtWidgets.QPushButton("Add")
        add_btn.clicked.connect(self._settings_add_folder)
        add_layout.addWidget(add_btn)
        layout.addLayout(add_layout)

        # ── Remove + OK/Cancel ───────────────────────────────────────────────
        remove_btn = QtWidgets.QPushButton("Remove Selected")
        remove_btn.clicked.connect(self._settings_remove_selected_folder)
        layout.addWidget(remove_btn)

        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(lambda: self._settings_apply_and_close(dialog))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.exec()

    # ── Slot helpers ──────────────────────────────────────────────────────────

    def _settings_browse_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select HDRI Folder", "", QtWidgets.QFileDialog.ShowDirsOnly
        )
        if folder:
            self.new_folder_input.setText(folder)

    def _settings_add_folder(self):
        path = self.new_folder_input.text().strip()
        if path and os.path.isdir(path) and path not in self.hdri_folders:
            self.hdri_folders.append(path)
            self.folder_list_widget.addItem(path)
            self.new_folder_input.clear()

    def _settings_browse_cache_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Cache Folder", "", QtWidgets.QFileDialog.ShowDirsOnly
        )
        if folder:
            self.cache_folder = folder
            self.cache_folder_line.setText(folder)
            os.makedirs(self.cache_folder, exist_ok=True)

    def _settings_remove_selected_folder(self):
        for item in self.folder_list_widget.selectedItems():
            path = item.text()
            self.hdri_folders = [p for p in self.hdri_folders if p != path]
            self.folder_list_widget.takeItem(self.folder_list_widget.row(item))

    def _settings_apply_and_close(self, dialog):
        self.cache_folder = self.cache_folder_line.text().strip() or self.cache_folder
        if self.cache_folder and os.path.isdir(self.cache_folder):
            self.file_manager.save_cache_folder(self.cache_folder)
            os.makedirs(self.cache_folder, exist_ok=True)
        self.file_manager.save_hdri_folders(self.hdri_folders)
        if self.hdri_folders:
            self.path_le.setText(self.hdri_folders[0])
            self.file_manager.save_last_folder(self.hdri_folders[0])
            self.load_exrs()
        dialog.accept()


# ==================================================
# End Of Settings Dialog
# ==================================================
