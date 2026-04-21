# ==================================================
# Cache Manager
# ==================================================
import os
import hashlib
from PySide6 import QtGui

class CacheManager:
    """Manages thumbnail caching"""

    def __init__(self, cache_folder):
        self.cache_folder = cache_folder
        if cache_folder:
            os.makedirs(cache_folder, exist_ok=True)

    def cache_thumbnail(self, path, pixmap):
        """Cache a thumbnail pixmap"""
        if not self.cache_folder:
            return

        os.makedirs(self.cache_folder, exist_ok=True)
        hash_name = hashlib.md5(path.encode('utf-8')).hexdigest()
        cache_file = os.path.join(self.cache_folder, f"{hash_name}.png")
        try:
            pixmap.save(cache_file, "PNG")
        except Exception as e:
            print("Failed to save cached thumbnail:", e)

    def load_cached_thumbnail(self, path):
        """Load a cached thumbnail if available"""
        if not self.cache_folder:
            return None

        hash_name = hashlib.md5(path.encode('utf-8')).hexdigest()
        cache_file = os.path.join(self.cache_folder, f"{hash_name}.png")
        if os.path.exists(cache_file):
            pixmap = QtGui.QPixmap(cache_file)
            if not pixmap.isNull():
                return pixmap
        return None


# ==================================================
# End Of Cache Manager
# ==================================================