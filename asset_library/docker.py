"""Asset Library docker for Krita."""

import json
import os
import zipfile

try:
    from krita import DockWidgetFactoryBase, Krita
except ImportError:  # Allows syntax checks outside Krita.
    DockWidgetFactoryBase = object
    Krita = None

from .compat import (
    QAbstractItemView,
    QColor,
    QDialog,
    QDialogButtonBox,
    QDockWidget,
    QFileDialog,
    QFont,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPainter,
    QPixmap,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    Qt,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTimer,
    QVBoxLayout,
    QWidget,
    pyqtSignal,
)

SUPPORTED_EXTENSIONS = (".kra", ".png", ".jpg", ".jpeg")
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
        data["paths"] = [p for p in data.get("paths", []) if isinstance(p, dict)]
        data["splitter_sizes"] = self._valid_splitter_sizes(data.get("splitter_sizes"))
        data["right_panel_hidden"] = bool(data.get("right_panel_hidden", False))
        data["expanded_window_width"] = self._positive_int(
            data.get("expanded_window_width"), data["window_width"]
        )
        data["collapsed_window_width"] = self._positive_int(
            data.get("collapsed_window_width"), DEFAULT_SETTINGS["collapsed_window_width"]
        )
        return data

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
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as handle:
                json.dump(settings, handle, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def _positive_int(self, value, fallback):
        try:
            return max(80, int(value))
        except (TypeError, ValueError):
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


class AssetSettingsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Asset Library Settings")
        self._settings = dict(settings)
        self._build_ui()
        self._load_values()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget(self)
        self.tabs.addTab(self._build_paths_tab(), "Asset Paths")
        self.tabs.addTab(self._build_display_tab(), "Display")
        layout.addWidget(self.tabs, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _build_paths_tab(self):
        tab = QWidget(self)
        layout = QVBoxLayout(tab)

        path_header = QHBoxLayout()
        path_header.addStretch(1)
        self.add_button = QPushButton("Add", tab)
        self.remove_button = QPushButton("Remove", tab)
        path_header.addWidget(self.add_button)
        path_header.addWidget(self.remove_button)
        layout.addLayout(path_header)

        self.path_table = QTableWidget(0, 2, tab)
        self.path_table.setHorizontalHeaderLabels(["Alias", "Path"])
        self.path_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.path_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.path_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents
        )
        self.path_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.path_table, 1)

        self.add_button.clicked.connect(self._add_path)
        self.remove_button.clicked.connect(self._remove_path)
        return tab

    def _build_display_tab(self):
        tab = QWidget(self)
        layout = QVBoxLayout(tab)
        form = QFormLayout()
        self.width_spin = self._spin(240, 2400)
        self.height_spin = self._spin(180, 1800)
        self.columns_spin = self._spin(1, 12)
        self.thumbnail_spin = self._spin(48, 512)
        self.font_spin = self._spin(7, 32)
        form.addRow("Docker width", self.width_spin)
        form.addRow("Docker height", self.height_spin)
        form.addRow("Thumbnail columns", self.columns_spin)
        form.addRow("Thumbnail size", self.thumbnail_spin)
        form.addRow("Font size", self.font_spin)
        layout.addLayout(form)
        layout.addStretch(1)
        return tab

    def _spin(self, minimum, maximum):
        spin = QSpinBox(self)
        spin.setRange(minimum, maximum)
        return spin

    def _load_values(self):
        for item in self._settings.get("paths", []):
            self._append_path_row(item.get("alias", ""), item.get("path", ""))
        self.width_spin.setValue(
            int(self._settings.get("window_width", DEFAULT_SETTINGS["window_width"]))
        )
        self.height_spin.setValue(
            int(self._settings.get("window_height", DEFAULT_SETTINGS["window_height"]))
        )
        self.columns_spin.setValue(
            int(self._settings.get("columns", DEFAULT_SETTINGS["columns"]))
        )
        self.thumbnail_spin.setValue(
            int(
                self._settings.get("thumbnail_size", DEFAULT_SETTINGS["thumbnail_size"])
            )
        )
        self.font_spin.setValue(
            int(self._settings.get("font_size", DEFAULT_SETTINGS["font_size"]))
        )

    def _append_path_row(self, alias, path):
        row = self.path_table.rowCount()
        self.path_table.insertRow(row)
        self.path_table.setItem(row, 0, QTableWidgetItem(alias or ""))
        self.path_table.setItem(row, 1, QTableWidgetItem(path or ""))

    def _add_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Asset Folder")
        if not path:
            return
        alias, ok = QInputDialog.getText(self, "Folder Alias", "Alias (optional)")
        if ok:
            self._append_path_row(alias, path)

    def _remove_path(self):
        rows = sorted(
            {index.row() for index in self.path_table.selectedIndexes()}, reverse=True
        )
        for row in rows:
            self.path_table.removeRow(row)

    def values(self):
        paths = []
        for row in range(self.path_table.rowCount()):
            alias_item = self.path_table.item(row, 0)
            path_item = self.path_table.item(row, 1)
            alias = alias_item.text().strip() if alias_item else ""
            path = path_item.text().strip() if path_item else ""
            if path:
                paths.append({"alias": alias, "path": path})
        updated = dict(self._settings)
        updated.update(
            {
                "paths": paths,
                "window_width": self.width_spin.value(),
                "window_height": self.height_spin.value(),
                "columns": self.columns_spin.value(),
                "thumbnail_size": self.thumbnail_spin.value(),
                "font_size": self.font_spin.value(),
            }
        )
        return updated


class AssetTile(QFrame):
    opened = pyqtSignal(str)

    def __init__(self, file_path, pixmap, thumb_size, font_size, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.setFrameShape(QFrame.StyledPanel)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(file_path)
        self.setFixedSize(thumb_size + 24, thumb_size + 54)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self.image = QLabel(self)
        self.image.setAlignment(Qt.AlignCenter)
        self.image.setFixedSize(thumb_size, thumb_size)
        self.image.setPixmap(
            pixmap.scaled(
                thumb_size, thumb_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        )
        self.image.mouseDoubleClickEvent = self.mouseDoubleClickEvent
        layout.addWidget(self.image)

        self.name = QLabel(os.path.basename(file_path), self)
        self.name.setAlignment(Qt.AlignCenter)
        self.name.setWordWrap(True)
        font = QFont(self.name.font())
        font.setPointSize(font_size)
        self.name.setFont(font)
        self.name.mouseDoubleClickEvent = self.mouseDoubleClickEvent
        layout.addWidget(self.name)

    def mouseDoubleClickEvent(self, event):
        self.opened.emit(self.file_path)
        try:
            super().mouseDoubleClickEvent(event)
        except AttributeError:
            pass


class AssetLibraryDocker(QDockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Asset Library")
        self.store = SettingsStore()
        self.settings = self.store.load()
        self.current_path = ""
        self._restoring_layout = False
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._save_runtime_settings)
        self._build_ui()
        self._apply_settings()
        self._load_folders()

    def canvasChanged(self, canvas):
        pass

    def _build_ui(self):
        root = QWidget(self)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(6, 6, 6, 6)
        root_layout.setSpacing(6)

        self.splitter = QSplitter(Qt.Horizontal, root)
        self.folder_panel = QWidget(self.splitter)
        folder_layout = QVBoxLayout(self.folder_panel)
        folder_layout.setContentsMargins(0, 0, 0, 0)
        folder_layout.setSpacing(6)

        self.folder_list = QListWidget(self.folder_panel)
        self.folder_list.setMinimumWidth(120)
        self.folder_list.currentItemChanged.connect(self._folder_changed)
        folder_layout.addWidget(self.folder_list, 1)

        self.refresh_button = QPushButton("Refresh", self.folder_panel)
        self.settings_button = QPushButton("Settings", self.folder_panel)
        self.hide_button = QPushButton("Hide", self.folder_panel)
        folder_layout.addWidget(self.refresh_button)
        folder_layout.addWidget(self.settings_button)
        folder_layout.addWidget(self.hide_button)
        self.splitter.addWidget(self.folder_panel)

        self.asset_panel = QWidget(self.splitter)
        right_layout = QVBoxLayout(self.asset_panel)
        right_layout.setContentsMargins(6, 0, 0, 0)
        self.status_label = QLabel("", self.asset_panel)
        right_layout.addWidget(self.status_label)

        self.scroll = QScrollArea(self.asset_panel)
        self.scroll.setWidgetResizable(True)
        self.asset_host = QWidget(self.scroll)
        self.asset_grid = QGridLayout(self.asset_host)
        self.asset_grid.setContentsMargins(4, 4, 4, 4)
        self.asset_grid.setSpacing(10)
        self.scroll.setWidget(self.asset_host)
        right_layout.addWidget(self.scroll, 1)
        self.splitter.addWidget(self.asset_panel)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        root_layout.addWidget(self.splitter, 1)

        self.refresh_button.clicked.connect(self._refresh_assets)
        self.settings_button.clicked.connect(self._open_settings)
        self.hide_button.clicked.connect(self._toggle_asset_panel)
        self.splitter.splitterMoved.connect(self._queue_runtime_save)
        self.setWidget(root)

    def _apply_settings(self):
        width = int(self.settings.get("window_width", DEFAULT_SETTINGS["window_width"]))
        height = int(
            self.settings.get("window_height", DEFAULT_SETTINGS["window_height"])
        )
        if self.settings.get("right_panel_hidden", False):
            width = int(
                self.settings.get(
                    "collapsed_window_width", DEFAULT_SETTINGS["collapsed_window_width"]
                )
            )
        self.resize(width, height)
        font = QFont(self.font())
        font.setPointSize(
            int(self.settings.get("font_size", DEFAULT_SETTINGS["font_size"]))
        )
        self.setFont(font)
        self._restore_splitter_sizes()
        self._set_asset_panel_hidden(
            bool(self.settings.get("right_panel_hidden", False)), save=False
        )

    def _restore_splitter_sizes(self):
        self._restoring_layout = True
        self.splitter.setSizes(
            list(
                self.settings.get("splitter_sizes", DEFAULT_SETTINGS["splitter_sizes"])
            )
        )
        self._restoring_layout = False

    def _load_folders(self):
        self.folder_list.clear()
        for entry in self.settings.get("paths", []):
            path = entry.get("path", "")
            if not path:
                continue
            alias = entry.get("alias", "").strip()
            label = alias or os.path.basename(os.path.normpath(path)) or path
            item = QListWidgetItem(label)
            item.setToolTip(path)
            item.setData(Qt.UserRole, path)
            self.folder_list.addItem(item)
        if self.folder_list.count() > 0:
            self.folder_list.setCurrentRow(0)
        else:
            self._clear_assets("Add asset paths from Settings.")

    def _folder_changed(self, current, previous):
        self.current_path = current.data(Qt.UserRole) if current else ""
        self._refresh_assets()

    def _refresh_assets(self):
        if not self.current_path:
            self._clear_assets("No asset path is selected.")
            return
        if not os.path.isdir(self.current_path):
            self._clear_assets(f"Folder not found: {self.current_path}")
            return

        files = []
        try:
            for entry in os.scandir(self.current_path):
                if entry.is_file() and entry.name.lower().endswith(
                    SUPPORTED_EXTENSIONS
                ):
                    files.append(entry.path)
        except OSError as exc:
            self._clear_assets(str(exc))
            return

        files.sort(key=lambda value: os.path.basename(value).lower())
        self._populate_assets(files)

    def _clear_assets(self, message=""):
        self._remove_tiles()
        self.status_label.setText(message)

    def _remove_tiles(self):
        while self.asset_grid.count():
            item = self.asset_grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _populate_assets(self, files):
        self._remove_tiles()
        count = len(files)
        suffix = "" if count == 1 else "s"
        self.status_label.setText(f"{count} asset{suffix}")
        columns = max(1, int(self.settings.get("columns", DEFAULT_SETTINGS["columns"])))
        thumb_size = int(
            self.settings.get("thumbnail_size", DEFAULT_SETTINGS["thumbnail_size"])
        )
        font_size = int(self.settings.get("font_size", DEFAULT_SETTINGS["font_size"]))

        for index, path in enumerate(files):
            tile = AssetTile(
                path,
                make_thumbnail(path, thumb_size),
                thumb_size,
                font_size,
                self.asset_host,
            )
            tile.opened.connect(self._open_asset)
            self.asset_grid.addWidget(tile, index // columns, index % columns)
        self.asset_grid.setRowStretch((count + columns - 1) // columns, 1)
        self.asset_grid.setColumnStretch(columns, 1)

    def _open_asset(self, path):
        if not Krita:
            return
        app = Krita.instance()
        document = app.openDocument(path)
        if document and app.activeWindow():
            app.activeWindow().addView(document)

    def _open_settings(self):
        dialog = AssetSettingsDialog(self.settings, self)
        exec_dialog = dialog.exec_ if hasattr(dialog, "exec_") else dialog.exec
        if exec_dialog() == QDialog.Accepted:
            self.settings = dialog.values()
            self.store.save(self.settings)
            self._apply_settings()
            self._load_folders()
            self._refresh_assets()

    def _toggle_asset_panel(self):
        self._set_asset_panel_hidden(not self.asset_panel.isHidden(), save=True)

    def _set_asset_panel_hidden(self, hidden, save):
        height = self.size().height()
        if hidden:
            sizes = self.splitter.sizes()
            if len(sizes) == 2 and sizes[1] > 0:
                self.settings["splitter_sizes"] = sizes
            self.settings["expanded_window_width"] = max(
                self.size().width(), DEFAULT_SETTINGS["window_width"]
            )
            collapsed_width = self._collapsed_width()
            self.settings["collapsed_window_width"] = collapsed_width
            self.asset_panel.hide()
            self.hide_button.setText("Show")
            self.resize(collapsed_width, height)
        else:
            self.asset_panel.show()
            self._restore_splitter_sizes()
            self.hide_button.setText("Hide")
            expanded_width = int(
                self.settings.get(
                    "expanded_window_width", DEFAULT_SETTINGS["window_width"]
                )
            )
            self.resize(expanded_width, height)
        self.settings["right_panel_hidden"] = hidden
        if save:
            self._save_runtime_settings()

    def _collapsed_width(self):
        sizes = self.splitter.sizes()
        left_width = sizes[0] if sizes else self.folder_panel.width()
        frame_margin = max(24, self.width() - self.splitter.width() + 12)
        return max(120, int(left_width + frame_margin))

    def _queue_runtime_save(self):
        if not self._restoring_layout:
            self._save_timer.start(500)

    def _save_runtime_settings(self):
        size = self.size()
        self.settings["window_height"] = size.height()
        if self.asset_panel.isHidden():
            self.settings["collapsed_window_width"] = size.width()
        else:
            self.settings["window_width"] = size.width()
            self.settings["expanded_window_width"] = size.width()
        if not self.asset_panel.isHidden():
            sizes = self.splitter.sizes()
            if len(sizes) == 2 and sizes[1] > 0:
                self.settings["splitter_sizes"] = sizes
        self.settings["right_panel_hidden"] = self.asset_panel.isHidden()
        self.store.save(self.settings)

    def resizeEvent(self, event):
        try:
            super().resizeEvent(event)
        except AttributeError:
            pass
        self._queue_runtime_save()

    def closeEvent(self, event):
        self._save_runtime_settings()
        try:
            super().closeEvent(event)
        except AttributeError:
            pass


def make_thumbnail(path, thumb_size):
    ext = os.path.splitext(path)[1].lower()
    pixmap = QPixmap()
    if ext == ".kra":
        pixmap = _load_kra_preview(path)
    else:
        pixmap.load(path)
    if pixmap.isNull():
        pixmap = _placeholder_pixmap(path, thumb_size)
    return pixmap


def _load_kra_preview(path):
    pixmap = QPixmap()
    try:
        with zipfile.ZipFile(path, "r") as archive:
            for name in ("preview.png", "mergedimage.png"):
                try:
                    data = archive.read(name)
                except KeyError:
                    continue
                pixmap.loadFromData(data)
                if not pixmap.isNull():
                    return pixmap
    except (OSError, zipfile.BadZipFile):
        pass
    return pixmap


def _placeholder_pixmap(path, thumb_size):
    pixmap = QPixmap(thumb_size, thumb_size)
    pixmap.fill(QColor(245, 245, 245))
    painter = QPainter(pixmap)
    painter.setPen(QColor(75, 75, 75))
    painter.drawRect(0, 0, thumb_size - 1, thumb_size - 1)
    font = QFont()
    font.setPointSize(max(10, thumb_size // 7))
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(
        pixmap.rect(), Qt.AlignCenter, os.path.splitext(path)[1].upper().lstrip(".")
    )
    painter.end()
    return pixmap


class AssetLibraryDockerFactory(DockWidgetFactoryBase):
    def __init__(self):
        try:
            dock_position = DockWidgetFactoryBase.DockRight
        except AttributeError:
            dock_position = DockWidgetFactoryBase.DockPosition.DockRight
        super().__init__("AssetLibraryDocker", dock_position)

    def createDockWidget(self):
        return AssetLibraryDocker()
