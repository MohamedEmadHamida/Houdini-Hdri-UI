# ==================================================
# EXR Browser - Header Panel
# ==================================================

from PySide6 import QtWidgets, QtCore
from ui.components.context_label import ClickableContextLabel
from ui.styles.colors import (
    ACCENT_COLOR, ACCENT_HOVER, ACCENT_PRESSED,
    BACKGROUND_MEDIUM, BACKGROUND_LIGHT, BORDER_COLOR, GRAY
)


class HeaderPanel:
    """
    Builds the header section of the EXR Browser.
    Contains: Title label, context indicator, About button.
    Methods are called from EXRBrowser._build_header().
    """

    def _build_header(self, parent):
        header_layout = QtWidgets.QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 8)
        header_layout.setSpacing(8)

        # Title
        header = QtWidgets.QLabel("HDRI Image Browser")
        header.setStyleSheet(f"""
            QLabel {{
                font-size: 18pt;
                font-weight: 600;
                color: {ACCENT_COLOR};
            }}
        """)

        # Help / About button
        about_button = QtWidgets.QPushButton("About")
        about_button.setToolTip("About / Help")
        about_button.setCursor(QtCore.Qt.PointingHandCursor)
        about_button.setFixedSize(90, 30)
        about_button.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT_COLOR};
                border: none;
                border-radius: 4px;
                color: white;
                font-weight: bold;
                font-size: 10pt;
            }}
            QPushButton:hover {{
                background: {ACCENT_HOVER};
            }}
            QPushButton:pressed {{
                background: {ACCENT_PRESSED};
            }}
        """)
        about_button.clicked.connect(self._show_about)

        # Context indicator (OBJ/STAGE) - Clickable to pin/unpin
        self.context_label = ClickableContextLabel()
        self.context_label.setStyleSheet(f"""
            QLabel {{
                font-size: 8pt;
                color: {GRAY};
                background: {BACKGROUND_MEDIUM};
                border: 1px solid {BORDER_COLOR};
                border-radius: 3px;
                padding: 2px 6px;
                min-width: 70px;
            }}
            QLabel:hover {{
                background: {BACKGROUND_LIGHT};
                border-color: {ACCENT_COLOR};
            }}
        """)
        self.context_label.setText("⚪ N/A")
        self.context_label.setAlignment(QtCore.Qt.AlignCenter)
        self.context_label.setToolTip("Click to pin/unpin current context")
        self.context_label.path_ready.connect(self._copy_context_path)

        header_layout.addWidget(header)
        header_layout.addWidget(self.context_label)
        header_layout.addStretch()
        header_layout.addWidget(about_button)

        parent.addLayout(header_layout)

    def _show_about(self):
        about_text = """
HDRI Image Browser
Version V1.2

Created by:
👤 Author
MohamedEmadHamida
Mohamed Qatary

Contact:
ArtStation / GitHub / Email
mohamedemadhamida@gmail.com
https://github.com/MohamedEmadHamida

🤍Built with passion for the Houdini community 🤍
   🙏Don't forget to keep us in your duaa 🙏
        """
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle("About")
        msg_box.setText(about_text.strip())
        msg_box.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg_box.exec()


# ==================================================
# End Of Header Panel
# ==================================================
