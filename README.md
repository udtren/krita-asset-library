# Krita Asset Library

Krita Docker plugin for browsing asset folders and opening `.kra`, `.png`, `.jpg`, and `.jpeg` files as new Krita documents.

## Features

- Register multiple asset folder paths from the Docker settings dialog.
- Optional alias per path. When set, the alias is shown in the left folder list.
- Settings dialog is split into tabs: `Asset Paths` and `Display`.
- Shows only files in the selected folder root; nested folders are not traversed.
- Displays thumbnails for PNG/JPG files and KRA previews when `preview.png` or `mergedimage.png` exists in the KRA archive.
- Double-click a thumbnail to open it with `Krita.instance().openDocument()` and add a new view.
- Left panel contains `Refresh`, `Settings`, and `Hide` / `Show` buttons.
- `Hide` collapses the right asset thumbnail container; `Show` restores it.
- Settings include Docker window size, left/right container sizes, thumbnail columns, thumbnail size, font size, and right-panel hidden state.
- Config is saved as `config.json` under `../../krita_asset_library` relative to the plugin folder. In the normal Krita install this resolves to `%APPDATA%/krita/krita_asset_library/config.json`.
- Uses `asset_library/compat.py` for PyQt5/PyQt6 import compatibility.

## Install

Copy both of these into Krita's `pykrita` folder:

- `asset_library/`
- `asset_library.desktop`

Restart Krita, enable **Asset Library** in Python Plugin Manager, then open the Docker from Krita's Docker menu.