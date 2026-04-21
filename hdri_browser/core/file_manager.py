# ==================================================
# File Manager
# ==================================================
import os

class FileManager:
    """Manages file operations for the HDRI browser"""

    def __init__(self):
        self.last_folder_file = os.path.join(
            os.path.expanduser("~"), "last_folder.txt"
        )
        self.hdri_folders_file = os.path.join(
            os.path.expanduser("~"), "hdri_folders.txt"
        )
        self.cache_folder_file = os.path.join(
            os.path.expanduser("~"), "hdri_cache_folder.txt"
        )

    def load_last_folder(self):
        """Load the last used folder"""
        if os.path.exists(self.last_folder_file):
            try:
                with open(self.last_folder_file, 'r') as f:
                    return f.read().strip()
            except Exception as e:
                print("Failed to load last folder:", e)
                return ""
        return ""

    def save_last_folder(self, folder):
        """Save the last used folder"""
        try:
            with open(self.last_folder_file, 'w') as f:
                f.write(folder)
        except Exception as e:
            print("Failed to save last folder:", e)

    def load_hdri_folders(self):
        """Load configured HDRI folders"""
        if os.path.exists(self.hdri_folders_file):
            try:
                with open(self.hdri_folders_file, 'r', encoding='utf-8') as f:
                    paths = [line.strip() for line in f if line.strip()]
                return [p for p in paths if os.path.isdir(p)]
            except Exception as e:
                print("Failed to load HDRI folders:", e)
                return []
        return []

    def save_hdri_folders(self, folders):
        """Save configured HDRI folders"""
        try:
            with open(self.hdri_folders_file, 'w', encoding='utf-8') as f:
                for path in folders:
                    f.write(path + "\n")
        except Exception as e:
            print("Failed to save HDRI folders:", e)

    def load_cache_folder(self):
        """Load cache folder path"""
        if os.path.exists(self.cache_folder_file):
            try:
                with open(self.cache_folder_file, 'r', encoding='utf-8') as f:
                    path = f.read().strip()
                return path if os.path.isdir(path) else ''
            except Exception as e:
                print("Failed to load cache folder:", e)
                return ''
        return ''

    def save_cache_folder(self, cache_folder):
        """Save cache folder path"""
        try:
            with open(self.cache_folder_file, 'w', encoding='utf-8') as f:
                f.write(cache_folder)
        except Exception as e:
            print("Failed to save cache folder:", e)


# ==================================================
# End Of File Manager
# ==================================================