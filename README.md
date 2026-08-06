# Krita Asset Library

![Asset Library screenshot](images/1.png)

Krita Docker plugin for browsing asset folders and opening `.kra`, `.png`, `.jpg`, and `.jpeg` files as new Krita documents.

## Features

- Register multiple asset folder paths from the Docker settings dialog.
- Set an optional alias for each path. When set, the alias is shown in the left folder list.
- Change registered asset path order with Up/Down buttons in Settings.
- Enable `IncludeSubFolder` per asset path to include files from child folders.
- When subfolders are included, the right panel groups thumbnails by section. The root section uses the root folder name; subfolder sections use each subfolder name.
- Displays thumbnails for PNG/JPG files and KRA previews when `preview.png` or `mergedimage.png` exists in the KRA archive.

![Right Click Menu](images/2.png)

- Right-click an asset thumbnail or filename to open the context menu: `Open`, `Insert as New Layer`, `Insert as New File Layer`, `Duplicate`, `Rename`, or `Delete`.
- Left panel contains `Refresh`, `Settings`, and `Hide` / `Show` buttons.
- `Hide` collapses the right asset thumbnail container and shrinks the Docker; `Show` restores it.
- Display settings include `Auto columns`, fixed thumbnail columns, thumbnail size, folder/button font size, header font size, and asset filename font size.
- When `Auto columns` is enabled, the asset grid column count adapts to the right panel width during Docker resize and splitter movement.

## Config

Config is saved as `config.json` under `../../krita_asset_library` relative to the plugin package.

In a normal Krita install, this resolves to:
```text
%APPDATA%/krita/krita_asset_library/config.json
```
