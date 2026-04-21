# ==================================================
# Clickable Context Label
# ==================================================
from PySide6 import QtWidgets, QtCore

class ClickableContextLabel(QtWidgets.QLabel):
    """Clickable label for copying current context path"""

    path_ready = QtCore.Signal(str)  # Emits the path to copy

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_path = ""
        self.setCursor(QtCore.Qt.PointingHandCursor)

    def set_path(self, path):
        """Set the path that will be copied when clicked"""
        self.current_path = path

    def mousePressEvent(self, event):
        """Copy path to clipboard on click"""
        if event.button() == QtCore.Qt.LeftButton and self.current_path:
            self.path_ready.emit(self.current_path)
        super().mousePressEvent(event)


# ==================================================
# End Of Clickable Context Label
# ==================================================