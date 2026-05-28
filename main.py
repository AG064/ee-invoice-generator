#!/usr/bin/env python3
"""ee-invoice-generator - Estonian e-invoice generator with GUI"""
import sys
import os

# Add project root to path - works both in development and when bundled
if getattr(sys, 'frozen', False):
    # When bundled by PyInstaller
    application_path = sys._MEIPASS
    project_root = os.path.dirname(application_path)
else:
    # When running from source
    project_root = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, project_root)

# Import GUI as absolute imports
from gui.main import main

if __name__ == "__main__":
    main()