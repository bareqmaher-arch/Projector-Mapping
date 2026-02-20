@echo off
echo Building Projector Mapping Studio...

pip install pyinstaller

if not exist dist mkdir dist

pyinstaller --noconfirm --onedir --windowed --name "ProjectorMappingStudio" ^
    --add-data "src;src" ^
    --add-data "assets;assets" ^
    src/main.py

echo Build complete! Check dist/ProjectorMappingStudio folder.
pause
