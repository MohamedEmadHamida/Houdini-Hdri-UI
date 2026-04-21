# ==================================================
# Run App
# ==================================================
import sys
from PySide6 import QtWidgets
from config.settings import ENABLE_TIME_TEST, ENABLE_HOUDINI
from ui.main_window import EXRBrowser

if ENABLE_HOUDINI:
    try:
        import hou
    except ImportError:
        ENABLE_HOUDINI = False


if ENABLE_TIME_TEST:
    print("=" * 50)
    print("⏱ TIME TEST ENABLED")
    print("=" * 50)

app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
win = EXRBrowser()
win.show()

if not ENABLE_HOUDINI:
    sys.exit(app.exec())