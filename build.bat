@echo off
REM Build CustomTkinterApp.exe in the dist folder (double-click or run from cmd)
cd /d "%~dp0"
python -m pip install -r requirements.txt pyinstaller || goto :error
python build.py || goto :error
echo.
echo The release is dist\CustomTkinterApp.exe
pause
exit /b 0

:error
echo.
echo Build failed, see the messages above.
pause
exit /b 1
