@echo off

echo Building Binary...

:: Build executable
echo Starting PyInstaller...
call pyinstaller --onefile --noconsole --icon="assets\icon.ico" --add-data="assets\icon.ico;assets" --name helping-hand main.py
echo PyInstaller finished

:: Verify output
echo Verifying output...
if exist "dist\helping-hand.exe" (
    echo SUCCESS: Build completed
    if not exist "test" mkdir test
    move /y dist\helping-hand.exe test\
    echo Moved to test\helping-hand.exe
) else (
    echo ERROR: Build failed - executable not found
)

:: Clean build artifacts
echo Cleaning build artifacts...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del /f /q helping-hand.spec 2>nul

echo Done.
