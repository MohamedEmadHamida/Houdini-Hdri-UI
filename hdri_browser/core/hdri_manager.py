# ==================================================
# HDRI Manager
# ==================================================
from PySide6 import QtWidgets, QtGui
from config.settings import ENABLE_HOUDINI, ENABLE_TOOLTIPS

# Houdini import (optional)
if ENABLE_HOUDINI:
    try:
        import hou
    except ImportError:
        ENABLE_HOUDINI = False

class HDRIManager:
    """Manages HDRI operations in Houdini"""

    def __init__(self):
        self.pinned_context = None
        self.pinned_path = None

    def get_current_context(self):
        """Get current Houdini context (OBJ or STAGE) using NetworkEditor"""
        if not ENABLE_HOUDINI:
            return "N/A", ""

        try:
            # Get the active Network Editor pane
            current_pane = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)

            if current_pane is None:
                return "No Editor", ""

            # Get the current path from the active pane
            current_path = current_pane.pwd().path()

            # Store the path in the label for copying
            if hasattr(self, 'context_label'):
                self.context_label.set_path(current_path)

            if current_path.startswith("/stage"):
                return "STAGE", current_path
            elif current_path.startswith("/obj"):
                return "OBJ", current_path
            else:
                context_name = current_path.split("/")[1].upper() if current_path != "/" else "Root"
                return context_name, current_path

        except Exception as e:
            return "Error", ""

    def apply_env_light(self, path, context=None):
        """Apply HDRI as environment light in Houdini"""
        if not ENABLE_HOUDINI:
            return

        # Determine current context (pinned or actual)
        if context is None:
            context = self.pinned_context if self.pinned_context else self.get_current_context()[0]

        try:
            if context == "STAGE":
                # Solaris STAGE - use domelight
                dome = hou.node('/stage/domelight1')
                if dome is None:
                    dome = hou.node('/stage').createNode('domelight', 'domelight1')

                # Set texture file path
                texture_parm = hou.parm('/stage/domelight1/xn__inputstexturefile_r3ah')
                if texture_parm:
                    texture_parm.set(path)

                if ENABLE_TOOLTIPS:
                    QtWidgets.QToolTip.showText(
                        QtGui.QCursor.pos(),
                        "✓ STAGE Dome Light Updated"
                    )

            else:  # OBJ context
                # Object level - use envlight (original code)
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
                    parm.set(path)

                if ENABLE_TOOLTIPS:
                    QtWidgets.QToolTip.showText(
                        QtGui.QCursor.pos(),
                        "✓ Environment Light Updated"
                    )
        except Exception as e:
            if ENABLE_TOOLTIPS:
                QtWidgets.QToolTip.showText(
                    QtGui.QCursor.pos(),
                    f"⚠ Error: {str(e)[:30]}"
                )
            print(f"Error applying env light: {e}")

    def set_light_intensity(self, value, context=None):
        """Set light intensity"""
        if not ENABLE_HOUDINI:
            return

        # Determine current context (pinned or actual)
        if context is None:
            context = self.pinned_context if self.pinned_context else self.get_current_context()[0]

        try:
            if context == "STAGE":
                # Solaris STAGE - use domelight intensity parameter
                intensity_parm = hou.parm('/stage/domelight1/xn__inputsintensity_i0a')
                if intensity_parm:
                    intensity_value = value / 5.0  # Convert to 0.0-2.0 range
                    intensity_parm.set(intensity_value)

            else:  # OBJ context
                # Object level envlight
                obj = hou.node("/obj")
                if obj:
                    env = next(
                        (n for n in obj.children() if n.type().name() == "envlight"),
                        None
                    )

                    if env:
                        intensity_value = value / 5.0  # 1 = 0.2, 5 = 1.0, 10 = 2.0
                        intensity_parm = env.parm("light_intensity")
                        if intensity_parm:
                            intensity_parm.set(intensity_value)
        except Exception as e:
            print(f"Error setting light intensity: {e}")

    def set_light_exposure(self, value, context=None):
        """Set light exposure"""
        if not ENABLE_HOUDINI:
            return

        # Convert slider value to exposure value (-100 to 100 -> -2.0 to 2.0)
        exposure_value = value / 50.0

        # Determine current context (pinned or actual)
        if context is None:
            context = self.pinned_context if self.pinned_context else self.get_current_context()[0]

        try:
            if context == "STAGE":
                # Solaris STAGE - use domelight exposure parameter
                exposure_parm = hou.parm('/stage/domelight1/xn__inputsexposure_vya')
                if exposure_parm:
                    exposure_parm.set(exposure_value)

            else:  # OBJ context
                # Object level envlight
                obj = hou.node("/obj")
                if obj:
                    env = next(
                        (n for n in obj.children() if n.type().name() == "envlight"),
                        None
                    )

                    if env:
                        exposure_parm = env.parm("light_exposure")
                        if exposure_parm:
                            exposure_parm.set(exposure_value)
        except Exception as e:
            print(f"Error setting light exposure: {e}")

    def set_light_rotation(self, value, context=None):
        """Set light rotation"""
        if not ENABLE_HOUDINI:
            return

        # Determine current context (pinned or actual)
        if context is None:
            context = self.pinned_context if self.pinned_context else self.get_current_context()[0]

        try:
            if context == "STAGE":
                # Solaris STAGE - use domelight rotation parameter (r tuple)
                rot_parm = hou.parmTuple('/stage/domelight1/r')
                if rot_parm:
                    # Set rotation around Y axis (index 1)
                    current_rot = rot_parm.eval()
                    new_rot = (current_rot[0], value, current_rot[2])
                    rot_parm.set(new_rot)

            else:  # OBJ context
                # Object level envlight
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
# End Of HDRI Manager
# ==================================================