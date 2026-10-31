import os
import sys
import PyInstaller.__main__

# Builds one .exe file in the dist folder: python build.py
# Run it on Windows to get a Windows .exe (PyInstaller can't build for another system).

APP_NAME = "TitlePlacement"

def build():
    # Images are bundled inside the .exe, customtkinter themes and pycountry data are collected with it
    options = [
        "main.py",
        "--name", APP_NAME,
        "--onefile",  # One single .exe file
        "--windowed",  # No console window
        "--noconfirm",
        "--clean",
        "--add-data", f"images{os.pathsep}images",
        "--collect-data", "customtkinter",
        "--collect-data", "pycountry",
        "--hidden-import", "PIL._tkinter_finder",  # Needed by customtkinter images, PyInstaller misses it
    ]

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
    executable = APP_NAME + (".exe" if sys.platform == "win32" else "")
    print(f"\nDone: {os.path.join('dist', executable)}")

if __name__ == "__main__":
    build()
