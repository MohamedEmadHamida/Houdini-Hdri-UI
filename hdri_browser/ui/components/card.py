# ==================================================
# Animated Card Widget
# ==================================================
from PySide6 import QtWidgets, QtCore, QtGui

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