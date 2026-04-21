# ==================================================
# Clickable Thumbnail with Hover Zoom
# ==================================================
import os
from PySide6 import QtWidgets, QtCore, QtGui
from utils.decorators import time_test
from core.hdri_manager import HDRIManager
from ui.styles.colors import BACKGROUND_MEDIUM, BORDER_COLOR, ACCENT_COLOR, BACKGROUND_DARK
from config.settings import ENABLE_HOUDINI, ENABLE_ENV_LIGHT_CLICK, ENABLE_TOOLTIPS

# Houdini import (optional)
if ENABLE_HOUDINI:
    try:
        import hou
    except ImportError:
        ENABLE_HOUDINI = False

class ClickableLabel(QtWidgets.QLabel):

    def __init__(self, path, parent=None, browser=None):
        super().__init__(parent)
        self.path = path
        self.zoomed = False
        self.original_pixmap = None
        self.browser = browser  # Reference to EXRBrowser
        self.hdri_manager = HDRIManager()

        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QLabel {{
                background: {BACKGROUND_MEDIUM};
                border: 2px solid {BORDER_COLOR};
                border-radius: 8px;
            }}
            QLabel:hover {{
                border-color: {ACCENT_COLOR};
            }}
        """)

    def enterEvent(self, event):
        """Show zoomed preview on hover"""
        if self.original_pixmap and not self.zoomed:
            self.zoomed = True
            self._show_zoom_preview()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Hide zoomed preview"""
        if self.zoomed:
            self.zoomed = False
            self._hide_zoom_preview()
        super().leaveEvent(event)

    def _show_zoom_preview(self):
        """Display large zoom preview"""
        if not hasattr(self, 'zoom_label'):
            self.zoom_label = QtWidgets.QLabel(self.window())
            self.zoom_label.setStyleSheet(f"""
                QLabel {{
                    background: {BACKGROUND_DARK};
                    border: 3px solid {ACCENT_COLOR};
                    border-radius: 12px;
                    padding: 10px;
                }}
            """)
            self.zoom_label.setAlignment(QtCore.Qt.AlignCenter)

        # Scale pixmap to 400x400
        scaled = self.original_pixmap.scaled(
            400, 400,
            QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation
        )
        self.zoom_label.setPixmap(scaled)
        self.zoom_label.adjustSize()

        # Position near cursor
        cursor_pos = QtGui.QCursor.pos()
        widget_pos = self.window().mapFromGlobal(cursor_pos)
        self.zoom_label.move(widget_pos.x() + 20, widget_pos.y() + 20)
        self.zoom_label.raise_()
        self.zoom_label.show()

    def _hide_zoom_preview(self):
        """Hide zoom preview"""
        if hasattr(self, 'zoom_label'):
            self.zoom_label.hide()

    def mousePressEvent(self, event):
        if not (
            ENABLE_HOUDINI and
            ENABLE_ENV_LIGHT_CLICK and
            event.button() == QtCore.Qt.LeftButton
        ):
            return

        self._apply_env_light()

    @time_test
    def _apply_env_light(self):
        if not self.browser:
            return

        # Determine current context (pinned or actual)
        context = self.hdri_manager.pinned_context if self.hdri_manager.pinned_context else self.hdri_manager.get_current_context()[0]

        self.hdri_manager.apply_env_light(self.path, context)


# ==================================================
# End Of Clickable Thumbnail
# ==================================================