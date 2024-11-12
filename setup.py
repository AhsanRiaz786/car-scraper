from setuptools import setup

APP = ['Scrapers.py']  # Replace with your main Python script
DATA_FILES = ['lux_official_logo.png']  # Add any data files you need
OPTIONS = {
    'argv_emulation': True,
    'packages': ['playwright', 'reportlab', 'Pillow', 'requests', 'tk'],
    'plist': {
        'CFBundleName': 'CarScraper',
        'CFBundleDisplayName': 'CarScraper',
        'CFBundleIdentifier': 'com.yourname.carscraper',
        'CFBundleVersion': '0.1.0',
    },
    'includes': ['playwright'],
    'excludes': [],  # Add any packages you want to exclude
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
