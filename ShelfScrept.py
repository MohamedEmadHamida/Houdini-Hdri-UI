import sys
# Change the path to the directory where your main.py is located
path = r"D:\Python\012 Houdini Hdri APP\Houdini Hdri UI\hdri_browser"
file = path + r"\main.py"

if path not in sys.path:
    sys.path.append(path)

exec(open(file).read())