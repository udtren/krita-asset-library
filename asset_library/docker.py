"""Main Docker widget for Asset Library."""

import os

try:
    from krita import DockWidgetFactoryBase, Krita
except ImportError:  # Allows syntax checks outside Krita.
    DockWidgetFactoryBase = object
    Krita = None

from .asset_tile import AssetTile
from .compat import (
    QDockWidget,
    QFont,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTimer,
    Qt,
    QVBoxLayout,
    QWidget,
)
from .config import SettingsStore
from .constants import DEFAULT_SETTINGS, NESTED_ROLE, SUPPORTED_EXTENSIONS
from .settings_dialog import AssetSettingsDialog
from .thumbnail import make_thumbnail


class AssetLibraryDocker(QDockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Asset Library")
        self.store = SettingsStore()
        self.settings = self.store.load()
        self.current_path = ""
        self.current_nested = False
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
            item.setData(NESTED_ROLE, bool(entry.get("nested", False)))
            self.folder_list.addItem(item)
        if self.folder_list.count() > 0:
            self.folder_list.setCurrentRow(0)
        else:
            self._clear_assets("Add asset paths from Settings.")

    def _folder_changed(self, current, previous):
        self.current_path = current.data(Qt.UserRole) if current else ""
        self.current_nested = bool(current.data(NESTED_ROLE)) if current else False
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
            iterator = self._iter_asset_files(self.current_path, self.current_nested)
            files.extend(iterator)
        except OSError as exc:
            self._clear_assets(str(exc))
            return

        files.sort(key=lambda value: os.path.relpath(value, self.current_path).lower())
        self._populate_assets(files)

    def _iter_asset_files(self, root_path, nested):
        if nested:
            for folder, dirnames, filenames in os.walk(root_path):
                dirnames.sort(key=str.lower)
                for filename in sorted(filenames, key=str.lower):
                    if filename.lower().endswith(SUPPORTED_EXTENSIONS):
                        yield os.path.join(folder, filename)
        else:
            for entry in os.scandir(root_path):
                if entry.is_file() and entry.name.lower().endswith(
                    SUPPORTED_EXTENSIONS
                ):
                    yield entry.path

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
        if exec_dialog() == dialog.Accepted:
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


class AssetLibraryDockerFactory(DockWidgetFactoryBase):
    def __init__(self):
        try:
            dock_position = DockWidgetFactoryBase.DockRight
        except AttributeError:
            dock_position = DockWidgetFactoryBase.DockPosition.DockRight
        super().__init__("AssetLibraryDocker", dock_position)

    def createDockWidget(self):
        return AssetLibraryDocker()
