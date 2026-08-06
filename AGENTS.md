# AGENTS.md

## Project Overview

This repository contains a Krita Python Docker plugin named `asset_library`. It lets users register asset folders, browse supported asset files as thumbnails, and open files as new Krita documents.

## Repository Layout

- `asset_library.desktop`: Krita plugin desktop metadata.
- `asset_library/__init__.py`: Krita extension registration entrypoint.
- `asset_library/docker.py`: Main Docker widget and asset actions.
- `asset_library/settings_dialog.py`: Settings dialog UI.
- `asset_library/config.py`: Config loading, validation, and saving.
- `asset_library/constants.py`: Shared constants and default settings.
- `asset_library/compat.py`: PyQt5/PyQt6 compatibility imports and aliases.
- `asset_library/asset_tile.py`: Thumbnail tile widget and context menu signals.
- `asset_library/thumbnail.py`: Thumbnail generation for image files and KRA archives.

## Development Notes

- Keep the plugin compatible with both PyQt5 and PyQt6 by importing Qt classes through `asset_library/compat.py`.
- Config is stored at `../../krita_asset_library/config.json` relative to the plugin package. In a normal Krita install this resolves to `%APPDATA%/krita/krita_asset_library/config.json`.
- Preserve backward compatibility for older config keys where practical, especially renamed keys such as `nested` to `include_subfolders` and `font_size` to split font-size settings.
- Supported asset extensions are defined in `asset_library/constants.py`.
- The right-click asset context menu lives in `asset_library/asset_tile.py`; filesystem operations are handled in `asset_library/docker.py`.
- Avoid writing Krita-specific imports in modules that should be syntax-checkable outside Krita unless guarded with `try/except ImportError`.

## Verification

Run a syntax check from the repository root:

```powershell
Get-ChildItem asset_library -Filter *.py | ForEach-Object { python -m py_compile $_.FullName }
```

After running `py_compile`, remove generated caches before committing:

```powershell
if (Test-Path asset_library\__pycache__) { Remove-Item -LiteralPath asset_library\__pycache__ -Recurse -Force }
```

Manual verification should be done inside Krita because Docker registration, document opening, and Qt menu behavior depend on Krita's runtime.
