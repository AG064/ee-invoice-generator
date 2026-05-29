# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import glob

block_cipher = None

# Project root directory
PROJECT_ROOT = os.path.dirname(os.path.abspath(SPEC))

# Find Python directory
python_dir = os.path.dirname(sys.executable)

# Find tcl/tk DLLs and PIL binaries
def find_dll(dll_name):
    """Find a DLL in Python directory or system"""
    search_paths = [
        os.path.join(python_dir, 'DLLs'),
        os.path.join(python_dir, 'Lib', 'site-packages', 'PIL'),
        os.path.join(python_dir, 'Lib', 'site-packages'),
    ]
    for path in search_paths:
        full_path = os.path.join(path, dll_name)
        if os.path.exists(full_path):
            return (full_path, dll_name)
    return None

# Collect binaries
binaries = []
dll_files = ['tcl86t.dll', 'tk86t.dll', '_imaging.pyd', '_imagingcms.pyd', '_tkinter_finder.pyd']
for dll in dll_files:
    result = find_dll(dll)
    if result:
        binaries.append(result)

a = Analysis(
    ['main.py'],
    pathex=[PROJECT_ROOT],
    binaries=binaries,
    datas=[
        (os.path.join(PROJECT_ROOT, 'gui'), 'gui'),
        # Tcl/Tk runtime from Python directory
        (os.path.join(python_dir, 'tcl'), 'tcl'),
        (os.path.join(python_dir, 'tk8.6'), 'tk'),
    ],
    hiddenimports=[
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'PIL._imaging',
        'PIL._imagingcms',
        'PIL._tkinter_finder',
        'PySimpleGUI',
        'reportlab',
        'reportlab.lib.pagesizes',
        'reportlab.platypus',
        'reportlab.lib.styles',
        'reportlab.lib.colors',
        'reportlab.pdfgen',
        'reportlab.lib.units',
        'reportlab.lib.enums',
        'xml.etree.ElementTree',
        'gui',
        'gui.main',
        'gui.accounting_tab',
        'gui.invoice_history_tab',
        'einvoice',
        'einvoice.generator',
        'einvoice.accounting',
        'einvoice.accounting.accounts',
        'einvoice.accounting.journal',
        'einvoice.accounting.vat',
        'einvoice.accounting.reports',
        'einvoice.accounting.database',
    ],
    hookspath=[os.path.join(PROJECT_ROOT, 'hooks')],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ee-invoice-generator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
