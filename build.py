import os
import sys
import PyInstaller.__main__

# Builds the app in the dist folder: python build.py
# PyInstaller can't build for another system, so run it on each one (GitHub Actions does this for you):
#   Windows: dist/CustomTkinterApp.exe    macOS: dist/CustomTkinterApp.app    Linux: dist/CustomTkinterApp

APP_NAME = "CustomTkinterApp"

def build():
    # Images are bundled inside the app, customtkinter themes and pycountry data are collected with it
    options = [
        "main.py",
        "--name", APP_NAME,
        "--windowed",  # No console window (an .app bundle on macOS)
        "--noconfirm",
        "--clean",
        "--add-data", f"images{os.pathsep}images",
        "--collect-data", "customtkinter",
        "--collect-data", "pycountry",
        "--hidden-import", "PIL._tkinter_finder",  # Needed by customtkinter images, PyInstaller misses it
    ]

    # One single file on Windows and Linux, macOS uses a normal .app bundle instead
    if sys.platform != "darwin":
        options.append("--onefile")

    # Include the PostgreSQL / MySQL driver only if it is installed
    for module in ("psycopg2", "pymysql"):
        try:
            __import__(module)
            options += ["--hidden-import", module]
        except ImportError:
            pass

    # Use images/icon.ico as the .exe icon if it exists
    if os.path.exists(os.path.join("images", "icon.ico")):
        options += ["--icon", os.path.join("images", "icon.ico")]

    PyInstaller.__main__.run(options)
    executable = APP_NAME + {"win32": ".exe", "darwin": ".app"}.get(sys.platform, "")
    print(f"\nDone: {os.path.join('dist', executable)}")

if __name__ == "__main__":
    build()
