# Create virtual environment
Write-Host "Creating virtual environment..."
python -m venv build_env

# Install required packages (minimal footprint)
Write-Host "Installing dependencies..."
.\build_env\Scripts\python.exe -m pip install flask pandas openpyxl werkzeug pyinstaller

# Run PyInstaller
Write-Host "Compiling executable..."
.\build_env\Scripts\pyinstaller.exe --onefile --noconfirm --noconsole --add-data "templates;templates" --add-data "static;static" app.py --name ReportGenerator

# Create the final distribution folder
Write-Host "Preparing Release folder..."
if (Test-Path -Path "Release") { Remove-Item -Recurse -Force "Release" }
New-Item -ItemType Directory -Force -Path "Release"

# Copy the executable
Copy-Item "dist\ReportGenerator.exe" -Destination "Release\"

# Copy the data folder (contains your CSVs and rules)
Copy-Item -Recurse "data" -Destination "Release\"

# Pre-create the working directories so everything is organized on the pendrive
New-Item -ItemType Directory -Force -Path "Release\uploads"
New-Item -ItemType Directory -Force -Path "Release\reports"
New-Item -ItemType Directory -Force -Path "Release\intermediate"

Write-Host "========================================="
Write-Host "Build Complete! You can copy the 'Release' folder directly to your pendrive."
Write-Host "========================================="
