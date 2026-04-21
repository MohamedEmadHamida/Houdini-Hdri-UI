# ==================================================
# Pulse Animation for Loading Label
# ==================================================
from PySide6 import QtWidgets, QtCore

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