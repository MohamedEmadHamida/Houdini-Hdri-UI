''' 
This is the main UI script for the EXR Browser application.
It provides a modern dark-themed interface for browsing EXR images,
loading thumbnails in parallel, and applying them as environment lights in Houdini.

version: 1.3
main features:
- Modern dark theme with custom styles
- Path bar for selecting folders
- Scrollable grid layout for thumbnails
- Parallel loading of thumbnails using QThreadPool
- Clickable thumbnails to set environment light in Houdini
- Clickable labels for applying EXR images as environment lights
- Hover zoom preview for thumbnails ** not working yet **
- Time test decorator for performance measurement
- Config flags for enabling/disabling features
- Rotation and intensity sliders for HDRI adjustment in Houdini
Dependencies:

- PySide6
- OpenImageIO
- Numpy



ideas (Todo list):
rotation slider for hdri
slider for intensity

get Hdri from open images api
Sheard Foulders for hdri collections
download hdri collections when use 
Smart Filters
karma hdri preview
premade light setups
multiple hdri selection for lighting and render image in each one
random hdri rotation and render 


'''



# ==================================================
# CONFIG FLAGS
# ==================================================

ENABLE_HOUDINI = 1       
ENABLE_ENV_LIGHT_CLICK = 1 
ENABLE_TOOLTIPS = 1
ENABLE_TIME_TEST = 0
ENABLE_MULTITHREADING = True
# ==================================================

import os
import sys
import time
import subprocess

MAX_THREAD_COUNT = max(1, os.cpu_count() // 2)
##MAX_THREAD_COUNT = 4

# ==================================================
# Safe Imports
# ==================================================

import numpy as np
from PySide6 import QtWidgets, QtGui, QtCore

# Install OpenImageIO if not present
try:
    import OpenImageIO as oiio
except ImportError:
    print("OpenImageIO not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "OpenImageIO"])
    import OpenImageIO as oiio

# Houdini import (optional)
if ENABLE_HOUDINI:
    try:
        import hou
    except ImportError:
        ENABLE_HOUDINI = False


# ==================================================
# End Of Safe Imports
# ==================================================


# ==================================================
# Time Test Decorator
# ==================================================
def time_test(func):
    """Decorator to measure function execution time"""
    if not ENABLE_TIME_TEST:
        return func
    
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"⏱ {func.__name__}: {end - start:.4f}s")
        return result
    return wrapper


# ==================================================
# End Of Time Test Decorator
# ==================================================


# ==================================================
# Thumbnail Loading Worker
# ==================================================
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
        start_time = time.time()
        
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


# ==================================================
# Animated Card Widget
# ==================================================
class AnimatedCard(QtWidgets.QWidget):
    """Card widget with fade-in animation"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Simple fade-in without graphics effect to avoid rendering issues
        self.current_opacity = 0.0
        self.target_opacity = 1.0
        self.animation_active = False
        
        # Animation timer
        self.animation_timer = QtCore.QTimer(self)
        self.animation_timer.timeout.connect(self._animate_step)
        
    def start_animation(self, delay=0):
        """Start the entrance animation with optional delay"""
        if delay > 0:
            QtCore.QTimer.singleShot(delay, self._start_fade)
        else:
            self._start_fade()
    
    def _start_fade(self):
        """Begin fade animation"""
        self.animation_active = True
        self.animation_timer.start(16)  # ~60fps
    
    def _animate_step(self):
        """Animate one step"""
        if self.current_opacity < self.target_opacity:
            self.current_opacity += 0.05
            if self.current_opacity >= self.target_opacity:
                self.current_opacity = self.target_opacity
                self.animation_active = False
                self.animation_timer.stop()
            self.update()
    
    def paintEvent(self, event):
        """Paint with opacity"""
        if self.animation_active or self.current_opacity < 1.0:
            painter = QtGui.QPainter(self)
            painter.setOpacity(self.current_opacity)
            painter.fillRect(self.rect(), self.palette().window())
        super().paintEvent(event)


# ==================================================
# End Of Animated Card Widget
# ==================================================


# ==================================================
# Clickable Thumbnail with Hover Zoom
# ==================================================
class ClickableLabel(QtWidgets.QLabel):

    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.path = path
        self.zoomed = False
        self.original_pixmap = None

        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setStyleSheet("""
            QLabel {
                background: #2b2b2b;
                border: 2px solid #3d3d3d;
                border-radius: 8px;
            }
            QLabel:hover {
                border-color: #0078d4;
            }
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
            self.zoom_label.setStyleSheet("""
                QLabel {
                    background: #1e1e1e;
                    border: 3px solid #0078d4;
                    border-radius: 12px;
                    padding: 10px;
                }
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
        obj = hou.node("/obj")
        if not obj:
            return

        env = next(
            (n for n in obj.children() if n.type().name() == "envlight"),
            None
        )

        if env is None:
            env = obj.createNode("envlight", "HDRI_Environment_Light")
            env.moveToGoodPosition()

        parm = env.parm("env_map")
        if parm:
            parm.set(self.path)

        if ENABLE_TOOLTIPS:
            QtWidgets.QToolTip.showText(
                QtGui.QCursor.pos(),
                "✓ Environment Light Updated"
            )


# ==================================================
# End Of Clickable Thumbnail
# ==================================================


# ==================================================
# Pulse Animation for Loading Label
# ==================================================
class PulsingLabel(QtWidgets.QLabel):
    """Label with pulsing opacity animation for loading state"""
    
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        
        self.opacity_effect = QtWidgets.QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        
        self.pulse_animation = QtCore.QPropertyAnimation(self.opacity_effect, b"opacity")
        self.pulse_animation.setDuration(1000)
        self.pulse_animation.setStartValue(0.3)
        self.pulse_animation.setEndValue(1.0)
        self.pulse_animation.setEasingCurve(QtCore.QEasingCurve.InOutSine)
        self.pulse_animation.setLoopCount(-1)  # Infinite loop
        
    def start_pulse(self):
        """Start the pulsing animation"""
        self.pulse_animation.start()
    
    def stop_pulse(self):
        """Stop the pulsing animation"""
        self.pulse_animation.stop()
        self.opacity_effect.setOpacity(1.0)


# ==================================================
# End Of Pulse Animation
# ==================================================


# ==================================================
# EXR Browser UI
# ==================================================
class EXRBrowser(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("HDRI Browser")
        self.resize(1300, 700)

        self.last_folder_file = os.path.join(
            os.path.expanduser("~"), "last_folder.txt"
        )
        self.last_folder = self._load_last_folder()

        # Thread pool for parallel thumbnail loading
        if ENABLE_MULTITHREADING:
            self.thread_pool = QtCore.QThreadPool.globalInstance()
            self.thread_pool.setMaxThreadCount(MAX_THREAD_COUNT)
            #print(f"🚀 Multithreading enabled with {MAX_THREAD_COUNT} threads")
        else:
            self.thread_pool = None

        # Store references to cards for thread-safe updates
        self.card_data = {}
        self.loaded_count = 0
        self.total_count = 0

        self.setStyleSheet("""
            QWidget {
                background: #1e1e1e;
                color: #e0e0e0;
                font-family: 'Segoe UI', Arial;
                font-size: 10pt;
            }
            QLineEdit {
                background: #2d2d2d;
                border: 2px solid #3d3d3d;
                border-radius: 6px;
                padding: 8px 12px;
                color: #e0e0e0;
            }
            QLineEdit:focus {
                border-color: #0078d4;
            }
            QPushButton {
                background: #0078d4;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #1084d8;
            }
            QPushButton:pressed {
                background: #006cc1;
            }
            QScrollArea {
                border: none;
                background: #1e1e1e;
            }
            QLabel {
                color: #e0e0e0;
            }
        """)

        self._build_ui()

        if self.last_folder and os.path.exists(self.last_folder):
            self.load_exrs(self.last_folder)

    @time_test
    def _build_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        self._build_header(main_layout)
        self._build_path_bar(main_layout)
        self._build_controls(main_layout)
        self._build_scroll(main_layout)


# ==================================================
# End Of EXR Browser UI
# ==================================================


# ==================================================
# Header UI
# ==================================================

    def _build_header(self, parent):
        header_layout = QtWidgets.QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 8)
        header_layout.setSpacing(8)

        # Title
        header = QtWidgets.QLabel("HDRI Image Browser")
        header.setStyleSheet("""
         QLabel {
                font-size: 18pt;
            font-weight: 600;
            color: #0078d4;
        }
         """)

    # Help / About button
        about_button = QtWidgets.QPushButton("About")
        about_button.setToolTip("About / Help")
        about_button.setCursor(QtCore.Qt.PointingHandCursor)
        about_button.setFixedSize(90, 30)

        about_button.setStyleSheet("""
            QPushButton {
                background: #0078d4;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #1084d8;
            }
            QPushButton:pressed {
                background: #006cc1;
            }
            """)

        about_button.clicked.connect(self._show_about)

        header_layout.addWidget(header)
        header_layout.addStretch()
        header_layout.addWidget(about_button)

        parent.addLayout(header_layout)


# ==================================================
# End Of Header UI
# ==================================================


# ==================================================
# About Dialog
# ==================================================

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

Built with passion for the Houdini community 🤍
   🙏Don't forget to keep us in your duaa 🙏
        """
        
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle("About")
        msg_box.setText(about_text.strip())
        msg_box.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg_box.exec()


# ==================================================
# End Of About Dialog
# ==================================================


# ==================================================
# Path Bar UI
# ==================================================

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
        self.count_label.setStyleSheet("color: #888; font-style: italic;")

        bar.addWidget(path_label)
        bar.addWidget(self.path_le)
        bar.addWidget(browse)
        bar.addWidget(self.count_label)

        parent.addLayout(bar)


# ==================================================
# End Of Path Bar UI
# ==================================================


# ==================================================
# Controls UI
# ==================================================

    def _build_controls(self, parent):
        controls_layout = QtWidgets.QHBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 15)
        controls_layout.setSpacing(40)

        # HDRI Rotation Slider (Left)
        location_layout = QtWidgets.QVBoxLayout()
        location_layout.setSpacing(6)

        location_label = QtWidgets.QLabel("HDRI Rotation")
        location_label.setStyleSheet("""
            font-weight: bold; 
            color: #0078d4;
            font-size: 10pt;
        """)

        self.location_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.location_slider.setRange(-360, 360)
        self.location_slider.setValue(0)
        self.location_slider.setMinimumHeight(20)
        self.location_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #555;
                height: 6px;
                background: #333;
                margin: 2px 0;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #0078d4;
                border: 2px solid #005a9e;
                width: 16px;
                margin: -3px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #1084d8;
            }
            QSlider::sub-page:horizontal {
                background: #0078d4;
                border-radius: 3px;
            }
            QSlider::add-page:horizontal {
                background: #333;
                border-radius: 3px;
            }
        """)

        self.location_value_label = QtWidgets.QLabel("0°")
        self.location_value_label.setStyleSheet("""
            color: #ccc; 
            font-size: 9pt;
            background: #222;
            border: 1px solid #555;
            border-radius: 3px;
            padding: 1px 6px;
            min-width: 35px;
        """)
        self.location_value_label.setAlignment(QtCore.Qt.AlignCenter)

        self.location_slider.valueChanged.connect(self.on_location_changed)

        location_layout.addWidget(location_label)
        location_layout.addWidget(self.location_slider)
        location_layout.addWidget(self.location_value_label, alignment=QtCore.Qt.AlignCenter)

        # HDRI Intensity Slider (Right)
        intensity_layout = QtWidgets.QVBoxLayout()
        intensity_layout.setSpacing(6)

        intensity_label = QtWidgets.QLabel("HDRI Intensity")
        intensity_label.setStyleSheet("""
            font-weight: bold; 
            color: #0078d4;
            font-size: 10pt;
        """)

        self.intensity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal) 
        self.intensity_slider.setRange(0, 100)
        self.intensity_slider.setValue(10)  # 10 = 1.0
        self.intensity_slider.setSingleStep(1)
        self.intensity_slider.setMinimumHeight(20)
        self.intensity_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #555;
                height: 6px;
                background: #333;
                margin: 2px 0;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #0078d4;
                border: 2px solid #005a9e;
                width: 16px;
                margin: -3px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #1084d8;
            }
            QSlider::sub-page:horizontal {
                background: #0078d4;
                border-radius: 3px;
            }
            QSlider::add-page:horizontal {
                background: #333;
                border-radius: 3px;
            }
        """)

        self.intensity_value_label = QtWidgets.QLabel("1.0")
        self.intensity_value_label.setStyleSheet("""
            color: #ccc; 
            font-size: 9pt;
            background: #222;
            border: 1px solid #555;
            border-radius: 3px;
            padding: 1px 6px;
            min-width: 35px;
        """)
        self.intensity_value_label.setAlignment(QtCore.Qt.AlignCenter)

        self.intensity_slider.valueChanged.connect(self.on_intensity_changed)

        intensity_layout.addWidget(intensity_label)
        intensity_layout.addWidget(self.intensity_slider)
        intensity_layout.addWidget(self.intensity_value_label, alignment=QtCore.Qt.AlignCenter)

        # Add to layout: Rotation on left, Intensity on right
        controls_layout.addLayout(location_layout)
        controls_layout.addStretch()
        controls_layout.addLayout(intensity_layout)

        parent.addLayout(controls_layout)


# ==================================================
# End Of Controls UI
# ==================================================


# ==================================================
# Scroll Area UI
# ==================================================

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


# ==================================================
# Slider Logic Methods
# ==================================================

    def on_intensity_changed(self, value):
        """Handle intensity slider value changes"""
        # Update the value label
        self.intensity_value_label.setText(f"{value}.0")
        
        # Apply intensity to Houdini environment light
        if ENABLE_HOUDINI:
            try:
                obj = hou.node("/obj")
                if obj:
                    env = next(
                        (n for n in obj.children() if n.type().name() == "envlight"),
                        None
                    )
                    
                    if env:
                        # Convert slider value (0-10) to intensity multiplier (0.0-2.0)
                        intensity_value = value / 5.0  # 1 = 0.2, 5 = 1.0, 10 = 2.0
                        intensity_parm = env.parm("light_intensity")
                        if intensity_parm:
                            intensity_parm.set(intensity_value)
            except Exception as e:
                print(f"Error setting light intensity: {e}")

    def on_location_changed(self, value):
        """Handle location slider value changes"""
        # Update the value label
        self.location_value_label.setText(f"{value}°")
        
        # Apply rotation to Houdini environment light
        if ENABLE_HOUDINI:
            try:
                obj = hou.node("/obj")
                if obj:
                    env = next(
                        (n for n in obj.children() if n.type().name() == "envlight"),
                        None
                    )
                    
                    if env:
                        # Set rotation around Y axis (common for HDRI positioning)
                        ry_parm = env.parm("ry")
                        if ry_parm:
                            ry_parm.set(value)
            except Exception as e:
                print(f"Error setting light rotation: {e}")


# ==================================================
# End Of Slider Logic Methods
# ==================================================


# ==================================================
# End Of Scroll Area UI
# ==================================================


# ==================================================
# Logic Methods
# ==================================================

    @time_test
    def browse(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Select Folder Containing HDRI Files",
            "",
            QtWidgets.QFileDialog.ShowDirsOnly
        )
        if folder:
            self.path_le.setText(folder)
            self._save_last_folder(folder)
            self.load_exrs(folder)

    @time_test
    def clear(self):
        # Cancel all pending threads
        if self.thread_pool:
            self.thread_pool.clear()
        
        self.card_data.clear()
        self.loaded_count = 0
        self.total_count = 0
        
        while self.grid.count():
            w = self.grid.takeAt(0).widget()
            if w:
                w.deleteLater()

    def _load_last_folder(self):
        if os.path.exists(self.last_folder_file):
            try:
                with open(self.last_folder_file, 'r') as f:
                    return f.read().strip()
            except Exception as e:
                print("Failed to load last folder:", e)
                return ""
        return ""

    def _save_last_folder(self, folder):
        try:
            with open(self.last_folder_file, 'w') as f:
                f.write(folder)
        except Exception as e:
            print("Failed to save last folder:", e)

    @time_test
    def load_exrs(self, folder):
        if not os.path.isdir(folder):
            self.count_label.setText("Invalid folder path")
            self.count_label.setStyleSheet("color: #ff4444; font-style: italic;")
            return

        self.clear()
        files = [f for f in os.listdir(folder) if f.lower().endswith((".exr", ".hdr"))]

        if not files:
            self.count_label.setText("No HDRI files found")
            self.count_label.setStyleSheet("color: #ff9800; font-style: italic;")
            return

        self.total_count = len(files)
        self.loaded_count = 0
        
        self.count_label.setText(
            f"Loading 0/{self.total_count} HDRI files..."
        )
        self.count_label.setStyleSheet(
            "color: #ffa500; font-style: italic; font-weight: bold;"
        )

        row = col = 0
        for f in files:
            full_path = os.path.join(folder, f)
            card = self._build_card(full_path, f)
            self.grid.addWidget(card, row, col)

            col += 1
            if col == 4:
                col = 0
                row += 1


# ==================================================
# End Of Logic Methods
# ==================================================


# ==================================================
# Card Builder
# ==================================================

    def _build_card(self, path, filename):
        # Create animated card container
        box = AnimatedCard()
        box.setStyleSheet("""
            QWidget {
                background: #252525;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        box.setFixedSize(280, 340)  # Fixed card size
        
        lay = QtWidgets.QVBoxLayout(box)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(8)
        lay.setAlignment(QtCore.Qt.AlignCenter)

        thumb = ClickableLabel(path)
        thumb.setFixedSize(260, 220)  # Full width of card minus padding
        thumb.setAlignment(QtCore.Qt.AlignCenter)
        thumb.setScaledContents(False)  # Keep aspect ratio
        
        # Use pulsing label for loading state
        loading_label = PulsingLabel("⏳ Loading...")
        loading_label.setStyleSheet("""
            QLabel {
                background: #2b2b2b;
                border: 2px solid #3d3d3d;
                border-radius: 8px;
                color: #888;
            }
        """)
        loading_label.setAlignment(QtCore.Qt.AlignCenter)
        loading_label.start_pulse()
        
        # Add loading label to thumbnail
        thumb_layout = QtWidgets.QVBoxLayout(thumb)
        thumb_layout.addWidget(loading_label)

        name = QtWidgets.QLabel(filename)
        name.setAlignment(QtCore.Qt.AlignCenter)
        name.setWordWrap(True)
        name.setStyleSheet("font-weight: bold; font-size: 9pt;")
        name.setToolTip(path)
        name.setMaximumWidth(220)

        info = QtWidgets.QLabel("Loading...")
        info.setAlignment(QtCore.Qt.AlignCenter)
        info.setStyleSheet("color: #888; font-size: 9pt;")

        lay.addWidget(thumb, 0, QtCore.Qt.AlignCenter)
        lay.addWidget(name, 0, QtCore.Qt.AlignCenter)
        lay.addWidget(info, 0, QtCore.Qt.AlignCenter)

        # Store references including the animated card and loading label
        self.card_data[path] = {
            'card': box,
            'label': thumb,
            'info': info,
            'loading_label': loading_label
        }

        # Load thumbnail using threading or sync
        if ENABLE_MULTITHREADING and self.thread_pool:
            self._load_thumbnail_async(path)
        else:
            self._load_thumbnail_sync(path, thumb, info, loading_label, box)

        return box


# ==================================================
# End Of Card Builder
# ==================================================


# ==================================================
# Thumbnail Loader
# ==================================================

    def _load_thumbnail_async(self, path):
        """Load thumbnail asynchronously using thread pool"""
        worker = ThumbnailWorker(path)
        worker.signals.finished.connect(self._on_thumbnail_loaded)
        worker.signals.error.connect(self._on_thumbnail_error)
        self.thread_pool.start(worker)

    @QtCore.Slot(str, object, str)
    def _on_thumbnail_loaded(self, path, pixmap, info_text):
        """Handle successful thumbnail load (runs in main thread)"""
        if path in self.card_data:
            card = self.card_data[path]
            
            # Stop pulsing and remove loading label
            card['loading_label'].stop_pulse()
            card['loading_label'].deleteLater()
            
            # Set pixmap
            card['label'].setPixmap(pixmap)
            card['label'].setStyleSheet("""
                QLabel {
                    background: #2b2b2b;
                    border: 2px solid #3d3d3d;
                    border-radius: 8px;
                }
                QLabel:hover {
                    border-color: #0078d4;
                }
            """)
            card['info'].setText(info_text)
            card['info'].setStyleSheet("color: #4caf50; font-size: 9pt; font-weight: bold;")
            
            self.loaded_count += 1
            
            # Start card animation immediately (no delay)
            card['card'].start_animation()
            
            self._update_progress()

    @QtCore.Slot(str, str)
    def _on_thumbnail_error(self, path, error_msg):
        """Handle thumbnail loading error (runs in main thread)"""
        if path in self.card_data:
            card = self.card_data[path]
            
            # Stop pulsing and remove loading label
            card['loading_label'].stop_pulse()
            card['loading_label'].deleteLater()
            
            card['label'].setText("⚠ Failed to load")
            card['label'].setStyleSheet("""
                QLabel {
                    background: #3d2020;
                    border: 2px solid #8b0000;
                    border-radius: 8px;
                    color: #ff6b6b;
                }
            """)
            card['info'].setText(error_msg)
            card['info'].setStyleSheet("color: #ff6b6b; font-size: 8pt;")
            
            self.loaded_count += 1
            
            # Start card animation immediately (no delay)
            card['card'].start_animation()
            
            self._update_progress()

    def _update_progress(self):
        """Update loading progress in count label"""
        if self.loaded_count >= self.total_count:
            self.count_label.setText(
                f"✓ Loaded {self.total_count} HDRI file{'s' if self.total_count != 1 else ''}"
            )
            self.count_label.setStyleSheet(
                "color: #4caf50; font-style: italic; font-weight: bold;"
            )
        else:
            self.count_label.setText(
                f"Loading {self.loaded_count}/{self.total_count} HDRI files..."
            )

    @time_test
    def _load_thumbnail_sync(self, path, label, info_label, loading_label, card):
        """Synchronous thumbnail loading (fallback)"""
        try:
            inp = oiio.ImageInput.open(path)
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
            
            # Stop pulsing and remove loading label
            loading_label.stop_pulse()
            loading_label.deleteLater()
            
            label.setPixmap(pix)
            label.setStyleSheet("""
                QLabel {
                    background: #2b2b2b;
                    border: 2px solid #3d3d3d;
                    border-radius: 8px;
                }
                QLabel:hover {
                    border-color: #0078d4;
                }
            """)

            info_label.setText(f"{spec.width}×{spec.height} · {spec.nchannels}ch")
            info_label.setStyleSheet("color: #4caf50; font-size: 9pt; font-weight: bold;")
            
            self.loaded_count += 1
            
            # Start card animation immediately
            card.start_animation()
            
            self._update_progress()

        except Exception as e:
            # Stop pulsing and remove loading label
            loading_label.stop_pulse()
            loading_label.deleteLater()
            
            label.setText("⚠ Failed to load")
            label.setStyleSheet("""
                QLabel {
                    background: #3d2020;
                    border: 2px solid #8b0000;
                    border-radius: 8px;
                    color: #ff6b6b;
                }
            """)
            info_label.setText(str(e)[:30])
            info_label.setStyleSheet("color: #ff6b6b; font-size: 8pt;")
            
            self.loaded_count += 1
            
            # Start card animation immediately
            card.start_animation()
            
            self._update_progress()


# ==================================================
# End Of Thumbnail Loader
# ==================================================


# ==================================================
# Run App
# ==================================================
if ENABLE_TIME_TEST:
    print("=" * 50)
    print("⏱ TIME TEST ENABLED")
    print("=" * 50)

app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
win = EXRBrowser()
win.show()

if not ENABLE_HOUDINI:
    sys.exit(app.exec())