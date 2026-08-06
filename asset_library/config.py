"""Config file loading and saving for Asset Library."""

import json
import os

try:
    from krita import Krita
except ImportError:  # Allows syntax checks outside Krita.
    Krita = None

from .constants import (
    CONFIG_DIR_NAME,
    CONFIG_FILE_NAME,
    DEFAULT_SETTINGS,
    LEGACY_SETTINGS_GROUP,
    LEGACY_SETTINGS_KEY,
)


class SettingsStore:
    def __init__(self):
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_dir = os.path.normpath(
            os.path.join(plugin_dir, "..", "..", CONFIG_DIR_NAME)
        )
        self.config_path = os.path.join(self.config_dir, CONFIG_FILE_NAME)

    def load(self):
        data = dict(DEFAULT_SETTINGS)
        saved = self._load_file_settings()
        if saved is None:
            saved = self._load_legacy_krita_settings()
        if isinstance(saved, dict):
            data.update(saved)
        return self._valid_settings(data)

    def _load_file_settings(self):
        if not os.path.exists(self.config_path):
            return None
        try:
            with open(self.config_path, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except (OSError, ValueError):
            return None

    def _load_legacy_krita_settings(self):
        if Krita is None:
            return None
        try:
            raw = Krita.instance().readSetting(
                LEGACY_SETTINGS_GROUP, LEGACY_SETTINGS_KEY, ""
            )
        except Exception:
            return None
        if not raw:
            return None
        try:
            return json.loads(raw)
        except ValueError:
            return None

    def save(self, settings):
        settings = self._valid_settings(settings)
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as handle:
                json.dump(settings, handle, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def _valid_settings(self, settings):
        data = dict(DEFAULT_SETTINGS)
        if isinstance(settings, dict):
            data.update(settings)
        data["paths"] = [
            self._valid_path_entry(p)
            for p in data.get("paths", [])
            if isinstance(p, dict)
        ]
        data["splitter_sizes"] = self._valid_splitter_sizes(data.get("splitter_sizes"))
        data["right_panel_hidden"] = bool(data.get("right_panel_hidden", False))
        data["auto_columns"] = bool(data.get("auto_columns", True))
        data["columns"] = self._bounded_int(
            data.get("columns"), DEFAULT_SETTINGS["columns"], 1, 12
        )
        data["ui_font_size"] = self._font_size(
            data.get("ui_font_size", data.get("font_size")),
            DEFAULT_SETTINGS["ui_font_size"],
        )
        data["header_font_size"] = self._font_size(
            data.get(
                "header_font_size",
                data.get("ui_font_size", data.get("font_size")),
            ),
            DEFAULT_SETTINGS["header_font_size"],
        )
        data["asset_name_font_size"] = self._font_size(
            data.get("asset_name_font_size", data.get("font_size")),
            DEFAULT_SETTINGS["asset_name_font_size"],
        )
        data.pop("font_size", None)
        data["expanded_window_width"] = self._positive_int(
            data.get("expanded_window_width"), data["window_width"]
        )
        data["collapsed_window_width"] = self._positive_int(
            data.get("collapsed_window_width"),
            DEFAULT_SETTINGS["collapsed_window_width"],
        )
        return data

    def _valid_path_entry(self, entry):
        return {
            "alias": str(entry.get("alias", "")),
            "path": str(entry.get("path", "")),
            "include_subfolders": bool(
                entry.get("include_subfolders", entry.get("nested", False))
            ),
        }

    def _positive_int(self, value, fallback):
        try:
            return max(80, int(value))
        except (TypeError, ValueError):
            return int(fallback)

    def _bounded_int(self, value, fallback, minimum, maximum):
        try:
            number = int(value)
        except (TypeError, ValueError):
            return int(fallback)
        if minimum <= number <= maximum:
            return number
        return int(fallback)

    def _font_size(self, value, fallback):
        try:
            font_size = int(value)
        except (TypeError, ValueError):
            return int(fallback)
        if 7 <= font_size <= 32:
            return font_size
        return int(fallback)

    def _valid_splitter_sizes(self, sizes):
        if not isinstance(sizes, list) or len(sizes) != 2:
            return list(DEFAULT_SETTINGS["splitter_sizes"])
        try:
            left = max(80, int(sizes[0]))
            right = max(0, int(sizes[1]))
        except (TypeError, ValueError):
            return list(DEFAULT_SETTINGS["splitter_sizes"])
        return [left, right]
