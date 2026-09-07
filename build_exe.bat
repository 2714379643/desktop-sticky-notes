@echo off
setlocal
pushd "%~dp0"
if errorlevel 1 goto bad_path

echo ========================================
echo Building DesktopStickyNotes.exe
echo ========================================

if exist ".venv\Scripts\python.exe" goto install

echo [1/3] Creating the virtual environment...
where py >nul 2>nul
if errorlevel 1 goto use_python
py -3 -m venv .venv
goto check_python

:use_python
where python >nul 2>nul
if errorlevel 1 goto no_python
python -m venv .venv

:check_python
if not exist ".venv\Scripts\python.exe" goto no_python

:install
set "PYTHON_EXE=%CD%\.venv\Scripts\python.exe"

echo [2/3] Installing dependencies. Keep the network connected...
"%PYTHON_EXE%" -m pip install --upgrade pip
if errorlevel 1 goto failed
"%PYTHON_EXE%" -m pip install -r requirements-build.txt
if errorlevel 1 goto failed

echo [3/3] Packaging the application. This may take a few minutes...
"%PYTHON_EXE%" -m PyInstaller --noconfirm --clean --onefile --windowed --name DesktopStickyNotes main.py
if errorlevel 1 goto failed

echo.
echo Build succeeded. The EXE is here:
echo %CD%\dist\DesktopStickyNotes.exe
echo.
start "" "%CD%\dist"
goto finish

:bad_path
echo.
echo ERROR: The project folder could not be opened.
goto finish_error

:no_python
echo.
echo ERROR: Python 3 was not found, or the virtual environment could not be created.
echo Check that Python is installed, then try again.
goto finish_error

:failed
echo.
echo ERROR: The build failed. Send me a screenshot of the last error lines.

:finish_error
pause
exit /b 1

:finish
popd
pause
exit /b 0
