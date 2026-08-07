# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for book2pdf Windows standalone .exe (onedir mode)"""

import os
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

block_cipher = None

base_dir = os.path.abspath(SPECPATH)


# ローカルパッケージ（ui, core）を再帰収集するための隠しインポートを列挙
def collect_local_imports():
    imports = []
    for pkg in ("ui", "core"):
        pkg_path = os.path.join(base_dir, pkg)
        if not os.path.isdir(pkg_path):
            continue
        imports.append(pkg)
        for root, _dirs, files in os.walk(pkg_path):
            if "__pycache__" in root:
                continue
            rel = os.path.relpath(root, base_dir).replace(os.sep, ".")
            for f in files:
                if f.endswith(".py") and f != "__init__.py":
                    mod = rel + "." + f[:-3]
                    imports.append(mod)
    return imports


local_imports = collect_local_imports()

a = Analysis(
    ["app.py"],
    pathex=[base_dir],
    binaries=[],
    datas=[
        ("config.example.json", "."),
        ("replacements.json", "."),
        ("README.md", "."),
        # NDLOCR-Lite is NOT bundled (size consideration)
    ],
    hiddenimports=[
        "customtkinter",
        "darkdetect",
        "PIL._tkinter_finder",
        "cv2",
        "numpy.core._dtype_ctypes",
    ] + local_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib",
        "pytest",
        "unittest",
        "pdb",
        "doctest",
        # macOS 専用フレームワークは Windows ビルドでは不要
        "Quartz",
        "Cocoa",
        "ApplicationServices",
        "objc",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="book2pdf",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="book2pdf",
)

print("[build-win.spec] Windows build configured")
