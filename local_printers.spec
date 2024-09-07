# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['socket_app.py'],  # Main application script
    pathex=[],  # You can add paths here if needed
    binaries=[],  # No additional binaries for now
    datas=[
        ('templates', 'templates'),  # Include templates folder
        ('static', 'static')  # Include static folder for images, CSS, etc.
    ],
    hiddenimports=[],  # Add hidden imports if necessary
    hookspath=[],  # Add hooks if necessary
    hooksconfig={},  # Hooks configuration if any
    runtime_hooks=[],  # Runtime hooks if necessary
    excludes=[],  # Exclude any packages if necessary
    noarchive=False,  # Set to False to bundle files inside the archive
    optimize=0,  # No optimization
)

# Build the Python code archive
pyz = PYZ(a.pure)

# Build the EXE
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='socket_app',  # Name of the executable
    debug=False,  # Disable debug mode
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress the executable using UPX
    upx_exclude=[],  # Exclude certain binaries from UPX compression if necessary
    runtime_tmpdir=None,  # Temporary directory used during runtime
    console=True,  # Set to False for GUI apps (no console)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,  # Only needed for macOS code signing
    entitlements_file=None,  # Only needed for macOS
    icon='static/logo.ico'  # Path to the icon file (must be in .ico format)
)
