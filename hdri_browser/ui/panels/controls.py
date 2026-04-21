# ==================================================
# EXR Browser - Controls Panel (Sliders)
# ==================================================

import random
from PySide6 import QtWidgets, QtCore, QtGui
from config.settings import ENABLE_HOUDINI, ENABLE_TOOLTIPS
from ui.styles.colors import ACCENT_COLOR, ACCENT_HOVER

# Houdini import (optional)
if ENABLE_HOUDINI:
    try:
        import hou
    except ImportError:
        ENABLE_HOUDINI = False

# ── Shared slider stylesheet ─────────────────────────────────────────────────

def _slider_style():
    return f"""
        QSlider::groove:horizontal {{
            border: 1px solid #555;
            height: 6px;
            background: #333;
            margin: 2px 0;
            border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            background: {ACCENT_COLOR};
            border: 2px solid #005a9e;
            width: 16px;
            margin: -3px 0;
            border-radius: 8px;
        }}
        QSlider::handle:horizontal:hover {{
            background: {ACCENT_HOVER};
        }}
        QSlider::sub-page:horizontal {{
            background: {ACCENT_COLOR};
            border-radius: 3px;
        }}
        QSlider::add-page:horizontal {{
            background: #333;
            border-radius: 3px;
        }}
    """

def _value_label_style():
    return """
        color: #ccc;
        font-size: 9pt;
        background: #222;
        border: 1px solid #555;
        border-radius: 3px;
        padding: 1px 6px;
        min-width: 35px;
    """

def _section_label_style():
    return f"""
        font-weight: bold;
        color: {ACCENT_COLOR};
        font-size: 10pt;
    """


class ControlsPanel:
    """
    Builds the controls bar: Random button + Rotation / Intensity / Exposure sliders.
    Methods are called from EXRBrowser._build_controls().
    """

    def _build_controls(self, parent):
        controls_layout = QtWidgets.QHBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 15)
        controls_layout.setSpacing(15)

        # Random HDRI Button
        random_button = QtWidgets.QPushButton("🎲")
        random_button.setStyleSheet("""
            QPushButton {
                background: #ff6b35;
                border: none;
                border-radius: 6px;
                padding: 5px 10px;
                color: white;
                font-weight: bold;
                font-size: 10pt;
            }
            QPushButton:hover { background: #ff8555; }
            QPushButton:pressed { background: #e55a2b; }
        """)
        random_button.setFixedHeight(30)
        random_button.setFixedWidth(35)
        random_button.clicked.connect(self.random_hdri)

        controls_layout.addWidget(random_button)
        controls_layout.addSpacing(10)
        controls_layout.addLayout(self._build_rotation_slider())
        controls_layout.addLayout(self._build_intensity_slider())
        controls_layout.addLayout(self._build_exposure_slider())
        controls_layout.addStretch()

        parent.addLayout(controls_layout)

    # ── Rotation ─────────────────────────────────────────────────────────────

    def _build_rotation_slider(self):
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(6)

        label = QtWidgets.QLabel("HDRI Rotation")
        label.setStyleSheet(_section_label_style())

        self.location_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.location_slider.setRange(-360, 360)
        self.location_slider.setValue(0)
        self.location_slider.setMinimumHeight(20)
        self.location_slider.setStyleSheet(_slider_style())

        self.location_value_label = QtWidgets.QLabel("0°")
        self.location_value_label.setStyleSheet(_value_label_style())
        self.location_value_label.setAlignment(QtCore.Qt.AlignCenter)
        self.location_slider.valueChanged.connect(self.on_location_changed)

        layout.addWidget(label)
        layout.addWidget(self.location_slider)
        layout.addWidget(self.location_value_label, alignment=QtCore.Qt.AlignCenter)
        return layout

    # ── Intensity ─────────────────────────────────────────────────────────────

    def _build_intensity_slider(self):
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(6)

        label = QtWidgets.QLabel("HDRI Intensity")
        label.setStyleSheet(_section_label_style())

        self.intensity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.intensity_slider.setRange(0, 100)
        self.intensity_slider.setValue(10)   # 10 → 1.0
        self.intensity_slider.setSingleStep(1)
        self.intensity_slider.setMinimumHeight(20)
        self.intensity_slider.setStyleSheet(_slider_style())

        self.intensity_value_label = QtWidgets.QLabel("1.0")
        self.intensity_value_label.setStyleSheet(_value_label_style())
        self.intensity_value_label.setAlignment(QtCore.Qt.AlignCenter)
        self.intensity_slider.valueChanged.connect(self.on_intensity_changed)

        layout.addWidget(label)
        layout.addWidget(self.intensity_slider)
        layout.addWidget(self.intensity_value_label, alignment=QtCore.Qt.AlignCenter)
        return layout

    # ── Exposure ──────────────────────────────────────────────────────────────

    def _build_exposure_slider(self):
        layout = QtWidgets.QVBoxLayout()
        layout.setSpacing(6)

        label = QtWidgets.QLabel("HDRI Exposure")
        label.setStyleSheet(_section_label_style())

        self.exposure_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.exposure_slider.setRange(-100, 100)
        self.exposure_slider.setValue(0)
        self.exposure_slider.setSingleStep(1)
        self.exposure_slider.setMinimumHeight(20)
        self.exposure_slider.setStyleSheet(_slider_style())

        self.exposure_value_label = QtWidgets.QLabel("0.0")
        self.exposure_value_label.setStyleSheet(_value_label_style())
        self.exposure_value_label.setAlignment(QtCore.Qt.AlignCenter)
        self.exposure_slider.valueChanged.connect(self.on_exposure_changed)

        layout.addWidget(label)
        layout.addWidget(self.exposure_slider)
        layout.addWidget(self.exposure_value_label, alignment=QtCore.Qt.AlignCenter)
        return layout

    # ── Slider event handlers ─────────────────────────────────────────────────

    def on_intensity_changed(self, value):
        """Handle intensity slider value changes"""
        self.intensity_value_label.setText(f"{value}.0")

        if ENABLE_HOUDINI:
            context = (self.hdri_manager.pinned_context
                       or self.hdri_manager.get_current_context()[0])
            try:
                intensity_value = value / 5.0
                if context == "STAGE":
                    parm = hou.parm('/stage/domelight1/xn__inputsintensity_i0a')
                    if parm:
                        parm.set(intensity_value)
                else:
                    obj = hou.node("/obj")
                    if obj:
                        env = next(
                            (n for n in obj.children() if n.type().name() == "envlight"),
                            None
                        )
                        if env:
                            parm = env.parm("light_intensity")
                            if parm:
                                parm.set(intensity_value)
            except Exception as e:
                print(f"Error setting light intensity: {e}")

    def on_exposure_changed(self, value):
        """Handle exposure slider value changes"""
        exposure_value = value / 50.0
        self.exposure_value_label.setText(f"{exposure_value:.1f}")

        if ENABLE_HOUDINI:
            context = (self.hdri_manager.pinned_context
                       or self.hdri_manager.get_current_context()[0])
            try:
                if context == "STAGE":
                    parm = hou.parm('/stage/domelight1/xn__inputsexposure_vya')
                    if parm:
                        parm.set(exposure_value)
                else:
                    obj = hou.node("/obj")
                    if obj:
                        env = next(
                            (n for n in obj.children() if n.type().name() == "envlight"),
                            None
                        )
                        if env:
                            parm = env.parm("light_exposure")
                            if parm:
                                parm.set(exposure_value)
            except Exception as e:
                print(f"Error setting light exposure: {e}")

    def on_location_changed(self, value):
        """Handle rotation slider value changes"""
        self.location_value_label.setText(f"{value}°")

        if ENABLE_HOUDINI:
            context = (self.hdri_manager.pinned_context
                       or self.hdri_manager.get_current_context()[0])
            try:
                if context == "STAGE":
                    rot = hou.parmTuple('/stage/domelight1/r')
                    if rot:
                        current = rot.eval()
                        rot.set((current[0], value, current[2]))
                else:
                    obj = hou.node("/obj")
                    if obj:
                        env = next(
                            (n for n in obj.children() if n.type().name() == "envlight"),
                            None
                        )
                        if env:
                            ry = env.parm("ry")
                            if ry:
                                ry.set(value)
            except Exception as e:
                print(f"Error setting light rotation: {e}")

    def random_hdri(self):
        """Select a random HDRI and apply it with random rotation"""
        if not self.card_data:
            if ENABLE_TOOLTIPS:
                QtWidgets.QToolTip.showText(
                    QtGui.QCursor.pos(),
                    "⚠ No HDRI files loaded"
                )
            return

        random_path = random.choice(list(self.card_data.keys()))
        random_rotation = random.randint(-360, 360)
        self.location_slider.setValue(random_rotation)

        if ENABLE_HOUDINI:
            context = (self.hdri_manager.pinned_context
                       or self.hdri_manager.get_current_context()[0])
            try:
                if context == "STAGE":
                    dome = hou.node('/stage/domelight1')
                    if dome is None:
                        dome = hou.node('/stage').createNode('domelight', 'domelight1')

                    tex = hou.parm('/stage/domelight1/xn__inputstexturefile_r3ah')
                    if tex:
                        tex.set(random_path)

                    rot = hou.parmTuple('/stage/domelight1/r')
                    if rot:
                        current = rot.eval()
                        rot.set((current[0], random_rotation, current[2]))
                else:
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
                        parm.set(random_path)

                    ry = env.parm("ry")
                    if ry:
                        ry.set(random_rotation)

                if ENABLE_TOOLTIPS:
                    QtWidgets.QToolTip.showText(
                        QtGui.QCursor.pos(),
                        f"✓ Random HDRI applied with {random_rotation}° rotation"
                    )
            except Exception as e:
                if ENABLE_TOOLTIPS:
                    QtWidgets.QToolTip.showText(
                        QtGui.QCursor.pos(),
                        f"⚠ Error: {str(e)[:30]}"
                    )
                print(f"Error applying random HDRI: {e}")


# ==================================================
# End Of Controls Panel
# ==================================================
