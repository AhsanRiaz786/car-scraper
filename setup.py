from cx_Freeze import setup, Executable
import os

# Set environment variable to prevent Playwright from bundling the browser binaries
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "0"

# Include any additional files
include_files = ["lux_official_logo.png"]

# Define build options
build_exe_options = {
    "packages": ["playwright", "requests", "reportlab", "tkinter"],  # Include necessary libraries
    "include_files": include_files,  # Additional files to include
}

# Define the executable
executables = [
    Executable("Scrapers.py", base="Win32GUI" if os.name == "nt" else None)
]

setup(
    name="CarScraper",
    version="1.0",
    description="Car Scraper Application",
    options={"build_exe": build_exe_options},
    executables=executables,
)
