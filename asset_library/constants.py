"""Shared constants for Asset Library."""

from .compat import PYQT6, Qt

SUPPORTED_EXTENSIONS = (".kra", ".png", ".jpg", ".jpeg")
NESTED_ROLE = Qt.UserRole + 1 if not PYQT6 else Qt.ItemDataRole(Qt.UserRole.value + 1)
CONFIG_DIR_NAME = "krita_asset_library"
CONFIG_FILE_NAME = "config.json"
LEGACY_SETTINGS_GROUP = "asset_library"
LEGACY_SETTINGS_KEY = "settings_json"

DEFAULT_SETTINGS = {
    "paths": [],
    "window_width": 720,
    "window_height": 520,
    "splitter_sizes": [150, 570],
    "right_panel_hidden": False,
    "expanded_window_width": 720,
    "collapsed_window_width": 170,
    "columns": 3,
    "thumbnail_size": 140,
    "font_size": 10,
}
