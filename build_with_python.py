import os
import shutil
import subprocess
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files

# -------------------------
# CONFIG
# -------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
VENV_PYTHON = PROJECT_ROOT / "venv" / "Scripts" / "python.exe"
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
SPEC_FILE = PROJECT_ROOT / "main.spec"

SOCKS_PROXY = "socks5://localhost:1080"

PIP_INSTALL = f'"{VENV_PYTHON}" -m pip install --no-cache-dir --proxy="{SOCKS_PROXY}"'

# Only pip-installable dependencies
REQUIRED_PACKAGES = [
    "pyinstaller",
    "pyside6",
    "openai-whisper",
    "soundfile",
    "pydub",
    "numpy",
    "torch",
]

# -------------------------
# UTILITY FUNCTIONS
# -------------------------

def run(cmd):
    print(f"\n>>>> RUNNING: {cmd}\n")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"ERROR! Command failed: {cmd}")
        sys.exit(1)


def clean_previous_build():
    print("\n=== Cleaning old build folders ===")
    for target in [DIST_DIR, BUILD_DIR, SPEC_FILE]:
        if Path(target).exists():
            if Path(target).is_dir():
                shutil.rmtree(target)
            else:
                Path(target).unlink()
    print("✔ Cleaned\n")


def install_dependencies():
    print("\n=== Installing dependencies via SOCKS proxy ===\n")

    run(f"{PIP_INSTALL} --upgrade pip setuptools wheel")

    for package in REQUIRED_PACKAGES:
        run(f"{PIP_INSTALL} {package}")

    print("\n✔ Dependencies installed!\n")


# -------------------------
# CREATE SPEC FILE
# -------------------------

def write_spec_file():
    print("\n=== Writing PyInstaller spec file ===")

    # Include all data files (Qt .ui files, models, etc.)
    datas = collect_data_files("ui") + collect_data_files("transcribe")

    spec_content = f"""
# -*- mode: python -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['{PROJECT_ROOT}'],
    binaries=[],
    datas={datas},
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True
)
"""
    with open(SPEC_FILE, "w", encoding="utf-8") as f:
        f.write(spec_content)

    print("✔ spec file written!\n")


# -------------------------
# RUN PYINSTALLER
# -------------------------

def run_pyinstaller():
    print("\n=== Running PyInstaller ===\n")
    run(f'"{VENV_PYTHON}" -m PyInstaller "{SPEC_FILE}"')
    print("\n✔ PyInstaller build completed!\n")


# -------------------------
# MAIN BUILD PIPELINE
# -------------------------

if __name__ == "__main__":
    print("===================================")
    print("🚀 PYTRANSCRIBER BUILD SCRIPT START")
    print("===================================\n")

    clean_previous_build()
    install_dependencies()
    write_spec_file()
    run_pyinstaller()

    print("\n===================================")
    print("🎉 BUILD COMPLETE!")
    print(f"📦 Executable available in: {DIST_DIR}")
    print("===================================\n")
