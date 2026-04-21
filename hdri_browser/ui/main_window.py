# ==================================================
# EXR Browser UI  -  main_window.py
# ==================================================
# This file now contains only:
#   - EXRBrowser class (init + core logic)
#   - _build_ui orchestration
#   - Card building + thumbnail loading
#   - Context / progress helpers
#
# Everything else lives in ui/panels/:
#   menu_bar.py       →  _build_menu
#   header.py         →  _build_header, _show_about
#   controls.py       →  _build_controls, slider handlers, random_hdri
#   settings_dialog.py→  _show_settings_dialog + helpers
# ==================================================

import os
import numpy as np
import OpenImageIO as oiio
from config import settings

from PySide6 import QtWidgets, QtCore, QtGui
from config.settings import ENABLE_HOUDINI, ENABLE_MULTITHREADING, ENABLE_TIME_TEST, ENABLE_TOOLTIPS ,Resolution
from utils.constants import MAX_THREAD_COUNT
from utils.decorators import time_test
from core.file_manager import FileManager
from core.cache_manager import CacheManager
from core.thumbnail_loader import ThumbnailWorker
from core.hdri_manager import HDRIManager
from ui.components.card import AnimatedCard
from ui.components.thumbnail import ClickableLabel
from ui.components.pulsing_label import PulsingLabel
from ui.styles.colors import *

# ── Panel mixins ─────────────────────────────────────────────────────────────
from ui.panels.menu_bar import MenuBarPanel
from ui.panels.header import HeaderPanel
from ui.panels.controls import ControlsPanel
from ui.panels.settings_dialog import SettingsDialogMixin

# Houdini import (optional)
if ENABLE_HOUDINI:
    try:
        import hou
    except ImportError:
        ENABLE_HOUDINI = False


# =============================================================================

class EXRBrowser(
    MenuBarPanel,
    HeaderPanel,
    ControlsPanel,
    SettingsDialogMixin,
    QtWidgets.QWidget,
):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("HDRI Browser")
        self.resize(Resolution.WIDTH, Resolution.HEIGHT)

        # Initialize managers
        self.file_manager = FileManager()
        self.hdri_manager = HDRIManager()

        self.last_folder    = self.file_manager.load_last_folder()
        self.hdri_folders   = self.file_manager.load_hdri_folders()
        self.cache_folder   = self.file_manager.load_cache_folder()
        if not self.cache_folder:
            self.cache_folder = os.path.join(os.path.expanduser("~"), ".hdri_browser_cache")
        os.makedirs(self.cache_folder, exist_ok=True)
        self.cache_manager = CacheManager(self.cache_folder)

        # Thread pool
        if ENABLE_MULTITHREADING:
            self.thread_pool = QtCore.QThreadPool.globalInstance()
            self.thread_pool.setMaxThreadCount(MAX_THREAD_COUNT)
        else:
            self.thread_pool = None

        # State
        self.card_data    = {}
        self.loaded_files = set()
        self.loaded_count = 0
        self.total_count  = 0

        # Context indicator timer
        self.context_label = None
        self.context_timer = QtCore.QTimer(self)
        self.context_timer.timeout.connect(self._update_context_indicator)
        self.context_timer.start(500)

        self._apply_stylesheet()
        self._build_ui()

        # Auto-load on startup
        if self.hdri_folders:
            self.path_le.setText(self.hdri_folders[0])
            self.load_exrs()
        elif self.last_folder and os.path.exists(self.last_folder):
            self.path_le.setText(self.last_folder)
            self.load_exrs(self.last_folder)

    # ── Stylesheet ────────────────────────────────────────────────────────────

    def _apply_stylesheet(self):
        self.setStyleSheet(f"""
            QWidget {{
                background: {BACKGROUND_DARK};
                color: {TEXT_COLOR};
                font-family: 'Segoe UI', Arial;
                font-size: 10pt;
            }}
            QLineEdit {{
                background: {BACKGROUND_MEDIUM};
                border: 2px solid {BORDER_COLOR};
                border-radius: 6px;
                padding: 8px 12px;
                color: {TEXT_COLOR};
            }}
            QLineEdit:focus {{
                border-color: {ACCENT_COLOR};
            }}
            QPushButton {{
                background: {ACCENT_COLOR};
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                color: white;
                font-weight: bold;
            }}
            QPushButton:hover   {{ background: {ACCENT_HOVER};    }}
            QPushButton:pressed {{ background: {ACCENT_PRESSED};  }}
            QScrollArea {{
                border: none;
                background: {BACKGROUND_DARK};
            }}
            QLabel {{ color: {TEXT_COLOR}; }}
        """)

    # ── UI assembly ───────────────────────────────────────────────────────────

    @time_test
    def _build_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        self._build_menu(main_layout)      # ← MenuBarPanel
        self._build_header(main_layout)    # ← HeaderPanel
        self._build_path_bar(main_layout)
        self._build_controls(main_layout)  # ← ControlsPanel
        self._build_scroll(main_layout)

    def _build_path_bar(self, parent):
        bar = QtWidgets.QHBoxLayout()
        bar.setSpacing(10)

        path_label = QtWidgets.QLabel("Folder:")
        path_label.setStyleSheet("font-weight: bold; min-width: 60px;")

        self.path_le = QtWidgets.QLineEdit(self.last_folder)
        self.path_le.setPlaceholderText("Select a folder containing EXR files...")
        self.path_le.returnPressed.connect(lambda: self.load_exrs(self.path_le.text()))

        browse = QtWidgets.QPushButton("Browse")
        browse.setFixedWidth(100)
        browse.clicked.connect(self.browse)

       

        self.count_label = QtWidgets.QLabel("No files loaded")
        self.count_label.setStyleSheet(f"color: {GRAY}; font-style: italic;")

        bar.addWidget(path_label)
        bar.addWidget(self.path_le)
        bar.addWidget(browse)
        bar.addWidget(self.count_label)

        parent.addLayout(bar)

    def _build_scroll(self, parent):
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        self.container = QtWidgets.QWidget()
        self.grid = QtWidgets.QGridLayout(self.container)
        self.grid.setSpacing(20)
        self.grid.setContentsMargins(10, 10, 10, 10)
        self.grid.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)

        scroll.setWidget(self.container)
        parent.addWidget(scroll)

    # ── Context helpers ───────────────────────────────────────────────────────

    def _get_current_context(self):
        return self.hdri_manager.get_current_context()

    def _update_context_indicator(self):
        if not self.context_label:
            return

        if self.hdri_manager.pinned_context:
            context = self.hdri_manager.pinned_context
            icon, color = "📌", "#ff9800"
        else:
            context, _ = self._get_current_context()
            if context == "OBJ":
                icon, color = "🟩", GREEN
            elif context == "STAGE":
                icon, color = "🟦", BLUE
            else:
                icon, color = "⚪", GRAY

        self.context_label.setText(f"{icon} {context}")
        self.context_label.setStyleSheet(f"""
            QLabel {{
                font-size: 8pt;
                color: {color};
                background: {BACKGROUND_MEDIUM};
                border: 1px solid {BORDER_COLOR};
                border-radius: 3px;
                padding: 2px 6px;
                min-width: 70px;
                font-weight: bold;
            }}
            QLabel:hover {{
                background: {BACKGROUND_LIGHT};
                border-color: {color};
            }}
        """)

    def _copy_context_path(self, path):
        """Pin / unpin the current context when context label is clicked"""
        if self.hdri_manager.pinned_context:
            self.hdri_manager.pinned_context = None
            self.hdri_manager.pinned_path    = None
            if ENABLE_TOOLTIPS:
                QtWidgets.QToolTip.showText(QtGui.QCursor.pos(), "✓ Context unpinned")
        else:
            current_context, current_path = self._get_current_context()
            self.hdri_manager.pinned_context = current_context
            self.hdri_manager.pinned_path    = current_path
            if ENABLE_TOOLTIPS:
                QtWidgets.QToolTip.showText(QtGui.QCursor.pos(), f"📌 Pinned: {current_context}")

        self._update_context_indicator()

    # ── File / folder actions ─────────────────────────────────────────────────

    @time_test
    def browse(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select Folder Containing HDRI Files", "",
            QtWidgets.QFileDialog.ShowDirsOnly
        )
        if folder:
            self.path_le.setText(folder)
            self.file_manager.save_last_folder(folder)
            self.load_exrs(folder)

    @time_test
    def clear(self):
        if self.thread_pool:
            self.thread_pool.clear()

        self.card_data.clear()
        self.loaded_files.clear()
        self.loaded_count = 0
        self.total_count  = 0

        while self.grid.count():
            w = self.grid.takeAt(0).widget()
            if w:
                w.deleteLater()

    def load_configured_folders(self):
        if not self.hdri_folders:
            QtWidgets.QMessageBox.warning(
                self, "No HDRI folders configured",
                "Please add HDRI folders in Settings first."
            )
            return
        first = self.hdri_folders[0]
        self.path_le.setText(first)
        self.file_manager.save_last_folder(first)
        self.load_exrs()

    def scan_for_new_files(self):
        check_folder = self.path_le.text().strip() if hasattr(self, 'path_le') else ''
        if check_folder and os.path.isdir(check_folder):
            self.load_exrs(folder=check_folder, incremental=True)
            return
        if self.hdri_folders:
            self.load_exrs(incremental=True)
            return
        QtWidgets.QMessageBox.warning(
            self, "No valid HDRI folder",
            "Please select or configure at least one HDRI folder to scan."
        )

    @time_test
    def load_exrs(self, folder=None, incremental=False):
        if folder:
            candidate_folders = [folder]
        elif self.hdri_folders:
            candidate_folders = self.hdri_folders
        elif self.last_folder:
            candidate_folders = [self.last_folder]
        else:
            candidate_folders = []

        candidate_folders = [f for f in candidate_folders if os.path.isdir(f)]

        if not candidate_folders:
            self.count_label.setText("Invalid folder path")
            self.count_label.setStyleSheet(f"color: {ERROR_COLOR}; font-style: italic;")
            return

        if not incremental:
            self.clear()

        existing_paths = set(self.card_data.keys())
        new_files = []
        for folder_path in candidate_folders:
            for f in os.listdir(folder_path):
                if f.lower().endswith((".exr", ".hdr")):
                    full_path = os.path.join(folder_path, f)
                    if full_path not in existing_paths:
                        new_files.append((folder_path, f))

        if not new_files and not existing_paths:
            self.count_label.setText("No HDRI files found")
            self.count_label.setStyleSheet(f"color: {WARNING_COLOR}; font-style: italic;")
            return

        if not new_files:
            self.count_label.setText("No new HDRI files found")
            self.count_label.setStyleSheet(f"color: {SUCCESS_COLOR}; font-style: italic;")
            return

        self.total_count  = len(existing_paths) + len(new_files)
        self.loaded_count = len(existing_paths)
        self.count_label.setText(f"Loading {self.loaded_count}/{self.total_count} HDRI files...")
        self.count_label.setStyleSheet("color: #ffa500; font-style: italic; font-weight: bold;")

        row = col = 0
        for folder_path, f in new_files:
            full_path = os.path.join(folder_path, f)
            card = self._build_card(full_path, f)
            self.grid.addWidget(card, row, col)
            col += 1
            if col == 4:
                col = 0
                row += 1

    # ── Card builder ──────────────────────────────────────────────────────────

    def _build_card(self, path, filename):
        box = AnimatedCard()
        box.setStyleSheet(f"""
            QWidget {{
                background: {BACKGROUND_MEDIUM};
                border-radius: 10px;
                padding: 10px;
            }}
        """)
        box.setFixedSize(280, 340)

        lay = QtWidgets.QVBoxLayout(box)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(8)
        lay.setAlignment(QtCore.Qt.AlignCenter)

        thumb = ClickableLabel(path, browser=self)
        thumb.setFixedSize(260, 220)
        thumb.setAlignment(QtCore.Qt.AlignCenter)
        thumb.setScaledContents(False)

        loading_label = PulsingLabel("⏳ Loading...")
        loading_label.setStyleSheet(f"""
            QLabel {{
                background: {BACKGROUND_MEDIUM};
                border: 2px solid {BORDER_COLOR};
                border-radius: 8px;
                color: {GRAY};
            }}
        """)
        loading_label.setAlignment(QtCore.Qt.AlignCenter)

        thumb_layout = QtWidgets.QVBoxLayout(thumb)
        thumb_layout.addWidget(loading_label)

        name = QtWidgets.QLabel(filename)
        name.setAlignment(QtCore.Qt.AlignCenter)
        name.setWordWrap(True)
        name.setStyleSheet("font-weight: bold; font-size: 9pt;")
        name.setToolTip(path)
        name.setMaximumWidth(220)

        lay.addWidget(thumb, 0, QtCore.Qt.AlignCenter)
        lay.addWidget(name,  0, QtCore.Qt.AlignCenter)

        self.card_data[path] = {
            'card': box,
            'label': thumb,
            'loading_label': loading_label,
        }
        self.loaded_files.add(path)

        # Try cache first
        cache_pixmap = self.cache_manager.load_cached_thumbnail(path)
        if cache_pixmap is not None:
            loading_label.stop_pulse()
            loading_label.deleteLater()
            thumb.setPixmap(cache_pixmap)
            thumb.setStyleSheet(self._thumb_style())
            self.loaded_count += 1
            box.start_animation()
            self._update_progress()
            return box

        if ENABLE_MULTITHREADING and self.thread_pool:
            self._load_thumbnail_async(path)
        else:
            self._load_thumbnail_sync(path, thumb, None, loading_label, box)

        return box

    def _thumb_style(self):
        return f"""
            QLabel {{
                background: {BACKGROUND_MEDIUM};
                border: 2px solid {BORDER_COLOR};
                border-radius: 8px;
            }}
            QLabel:hover {{
                border-color: {ACCENT_COLOR};
            }}
        """

    # ── Thumbnail loading ─────────────────────────────────────────────────────

    def _load_thumbnail_async(self, path):
        worker = ThumbnailWorker(path)
        worker.signals.finished.connect(self._on_thumbnail_loaded)
        worker.signals.error.connect(self._on_thumbnail_error)
        self.thread_pool.start(worker)

    @QtCore.Slot(str, object, str)
    def _on_thumbnail_loaded(self, path, pixmap, info_text):
        if path not in self.card_data:
            return
        card = self.card_data[path]
        card['loading_label'].stop_pulse()
        card['loading_label'].deleteLater()
        card['label'].setPixmap(pixmap)
        card['label'].setStyleSheet(self._thumb_style())
        self.cache_manager.cache_thumbnail(path, pixmap)
        self.loaded_count += 1
        card['card'].start_animation()
        self._update_progress()

    @QtCore.Slot(str, str)
    def _on_thumbnail_error(self, path, error_msg):
        if path not in self.card_data:
            return
        card = self.card_data[path]
        card['loading_label'].stop_pulse()
        card['loading_label'].deleteLater()
        card['label'].setText("⚠ Failed to load")
        card['label'].setStyleSheet(f"""
            QLabel {{
                background: #3d2020;
                border: 2px solid #8b0000;
                border-radius: 8px;
                color: {ERROR_LIGHT};
            }}
        """)
        self.loaded_count += 1
        card['card'].start_animation()
        self._update_progress()

    @time_test
    def _load_thumbnail_sync(self, path, label, info_label=None, loading_label=None, card=None):
        """Synchronous thumbnail loading (fallback when multithreading is off)"""
        try:
            inp  = oiio.ImageInput.open(path)
            spec = inp.spec()
            img  = inp.read_image(format=oiio.FLOAT)
            inp.close()

            img = np.nan_to_num(img)
            img = np.clip(img, 0.0, 1.0)
            img = (img * 255).astype(np.uint8)

            if spec.nchannels == 1:
                img  = img.reshape(spec.height, spec.width)
                qimg = QtGui.QImage(
                    img.data, spec.width, spec.height,
                    spec.width, QtGui.QImage.Format_Grayscale8
                ).copy()
            else:
                img = img.reshape(spec.height, spec.width, spec.nchannels)
                if spec.nchannels >= 3:
                    img = img[:, :, :3]
                img  = np.ascontiguousarray(img)
                qimg = QtGui.QImage(
                    img.data, spec.width, spec.height,
                    spec.width * 3, QtGui.QImage.Format_RGB888
                ).copy()

            pix = QtGui.QPixmap.fromImage(qimg).scaled(
                220, 220,
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation,
            )

            if loading_label is not None:
                loading_label.stop_pulse()
                loading_label.deleteLater()

            label.setPixmap(pix)
            label.setStyleSheet(self._thumb_style())
            self.cache_manager.cache_thumbnail(path, pix)
            self.loaded_count += 1

            if card is not None:
                card.start_animation()
            self._update_progress()

        except Exception as e:
            loading_label.stop_pulse()
            loading_label.deleteLater()
            label.setText("⚠ Failed to load")
            label.setStyleSheet(f"""
                QLabel {{
                    background: #3d2020;
                    border: 2px solid #8b0000;
                    border-radius: 8px;
                    color: {ERROR_LIGHT};
                }}
            """)
            self.loaded_count += 1
            card.start_animation()
            self._update_progress()

    # ── Progress ──────────────────────────────────────────────────────────────

    def _update_progress(self):
        if self.loaded_count >= self.total_count:
            self.count_label.setText(
                f"✓ Loaded {self.total_count} HDRI file{'s' if self.total_count != 1 else ''}"
            )
            self.count_label.setStyleSheet(
                f"color: {SUCCESS_COLOR}; font-style: italic; font-weight: bold;"
            )
        else:
            self.count_label.setText(
                f"Loading {self.loaded_count}/{self.total_count} HDRI files..."
            )


# ==================================================
# End Of EXR Browser UI
# ==================================================
