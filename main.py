#!/usr/bin/env python3
"""ee-invoice-generator - Estonian e-invoice generator with GUI"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.main import main

if __name__ == "__main__":
    main()