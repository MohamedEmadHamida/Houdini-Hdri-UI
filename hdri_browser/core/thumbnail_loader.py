# ==================================================
# Thumbnail Loading Worker
# ==================================================
import os
import time
import numpy as np
from PySide6 import QtCore, QtGui
import OpenImageIO as oiio
from utils.decorators import time_test
from config.settings import ENABLE_TIME_TEST

class ThumbnailWorker(QtCore.QRunnable):
    """Worker thread for loading thumbnails in parallel"""

    class Signals(QtCore.QObject):
        finished = QtCore.Signal(str, object, str)  # path, pixmap, info_text
        error = QtCore.Signal(str, str)  # path, error_msg

    def __init__(self, path):
        super().__init__()
        self.path = path
        self.signals = self.Signals()
        self.setAutoDelete(True)

    def run(self):
        """Execute thumbnail loading in background thread"""
        start_time = time.time() if ENABLE_TIME_TEST else 0

        try:
            inp = oiio.ImageInput.open(self.path)
            spec = inp.spec()
            img = inp.read_image(format=oiio.FLOAT)
            inp.close()

            img = np.nan_to_num(img)
            img = np.clip(img, 0.0, 1.0)
            img = (img * 255).astype(np.uint8)

            if spec.nchannels == 1:
                img = img.reshape(spec.height, spec.width)
                qimg = QtGui.QImage(
                    img.data,
                    spec.width,
                    spec.height,
                    spec.width,
                    QtGui.QImage.Format_Grayscale8
                ).copy()
            else:
                img = img.reshape(spec.height, spec.width, spec.nchannels)
                if spec.nchannels >= 3:
                    img = img[:, :, :3]
                img = np.ascontiguousarray(img)
                qimg = QtGui.QImage(
                    img.data,
                    spec.width,
                    spec.height,
                    spec.width * 3,
                    QtGui.QImage.Format_RGB888
                ).copy()

            pix = QtGui.QPixmap.fromImage(qimg).scaled(
                220, 220,
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation
            )

            info_text = f"{spec.width}×{spec.height} · {spec.nchannels}ch"

            if ENABLE_TIME_TEST:
                elapsed = time.time() - start_time
                print(f"⏱ _load_thumbnail [{os.path.basename(self.path)}]: {elapsed:.4f}s")

            self.signals.finished.emit(self.path, pix, info_text)

        except Exception as e:
            if ENABLE_TIME_TEST:
                elapsed = time.time() - start_time
                print(f"⏱ _load_thumbnail [{os.path.basename(self.path)}] FAILED: {elapsed:.4f}s")

            self.signals.error.emit(self.path, str(e)[:30])


# ==================================================
# End Of Thumbnail Loading Worker
# ==================================================