from PyInstaller.utils.hooks import collect_all, collect_submodules

# Collect all PIL data files and binaries
datas, binaries, hiddenimports = collect_all('PIL')

# Also collect tcl/tk
hiddenimports += ['tkinter', '_tkinter']
