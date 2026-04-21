# ==================================================
# Houdini API
# ==================================================
from config.settings import ENABLE_HOUDINI

# Houdini import (optional)
if ENABLE_HOUDINI:
    try:
        import hou
    except ImportError:
        ENABLE_HOUDINI = False

def is_houdini_available():
    """Check if Houdini is available"""
    return ENABLE_HOUDINI

def get_current_network_path():
    """Get the current network path from Houdini"""
    if not ENABLE_HOUDINI:
        return ""

    try:
        current_pane = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
        if current_pane:
            return current_pane.pwd().path()
    except:
        pass
    return ""

def create_node_at_path(path, node_type, name):
    """Create a node at the specified path"""
    if not ENABLE_HOUDINI:
        return None

    try:
        parent = hou.node(path)
        if parent:
            return parent.createNode(node_type, name)
    except:
        pass
    return None

def get_node_parameter(node_path, parm_name):
    """Get a parameter from a node"""
    if not ENABLE_HOUDINI:
        return None

    try:
        parm = hou.parm(node_path)
        if parm:
            return parm
    except:
        pass
    return None


# ==================================================
# End Of Houdini API
# ==================================================