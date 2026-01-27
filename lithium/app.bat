@echo off
REM Build Python Viewer/Editor app with PyInstaller

REM Paths
SET PYTHON_EXE="C:\Users\Maddo\AppData\Local\Programs\Python\Python313\python.exe"
SET SCRIPT_PATH="C:\Users\Maddo\Desktop\Python.pyw"
SET ICON_PATH="C:\Users\Maddo\Desktop\python.ico"
SET APP_NAME="PythonViewerEditor"

REM Ensure PyInstaller is installed
%PYTHON_EXE% -m pip install --upgrade pip
%PYTHON_EXE% -m pip install pyinstaller

REM Build the app
%PYTHON_EXE% -m PyInstaller ^
    --onefile ^
    --noconsole ^
    --name %APP_NAME% ^
    --icon %ICON_PATH% ^
    %SCRIPT_PATH%

echo.
echo Build finished! Check the 'dist' folder for your app.
pause
