# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
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
        'einvoice',
        'einvoice.generator',
        'einvoice.pdf',
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
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # True for debugging, False for GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)