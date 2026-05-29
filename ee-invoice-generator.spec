# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None

PROJECT_ROOT = os.path.dirname(os.path.abspath(SPEC))

# Get Python directory
python_dir = os.path.dirname(sys.executable)

a = Analysis(
    ['main.py'],
    pathex=[PROJECT_ROOT],
    binaries=[
        # Tcl/Tk DLLs
        (os.path.join(python_dir, 'DLLs', 'tcl86t.dll'), '.'),
        (os.path.join(python_dir, 'DLLs', 'tk86t.dll'), '.'),
    ],
    datas=[
        (os.path.join(PROJECT_ROOT, 'gui'), 'gui'),
        # Tcl/Tk runtime - include the entire tcl directory
        (os.path.join(python_dir, 'tcl'), 'tcl'),
        (os.path.join(python_dir, 'tk8.6'), 'tk8.6'),
    ],
    hiddenimports=[
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
    hookspath=[],
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
