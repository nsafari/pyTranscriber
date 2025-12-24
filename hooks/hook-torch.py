from PyInstaller.utils.hooks import (
    collect_submodules,
    collect_dynamic_libs,
)

hiddenimports = collect_submodules("torch")
binaries = collect_dynamic_libs("torch")
