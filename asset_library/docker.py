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
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTimer,
    Qt,
    QVBoxLayout,
    QWidget,
)
from .config import SettingsStore
from .constants import (
    DEFAULT_SETTINGS,
    INCLUDE_SUBFOLDERS_ROLE,
    SUPPORTED_EXTENSIONS,
)
from .settings_dialog import AssetSettingsDialog
from .thumbnail import make_thumbnail


class AssetLibraryDocker(QDockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Asset Library")
        self.store = SettingsStore()
        self.settings = self.store.load()
        self.current_path = ""
        self.current_include_subfolders = False
        self._asset_sections = []
        self._restoring_layout = False
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._save_runtime_settings)
        self._layout_timer = QTimer(self)
        self._layout_timer.setSingleShot(True)
        self._layout_timer.timeout.connect(self._relayout_assets)
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
        self.asset_layout = QVBoxLayout(self.asset_host)
        self.asset_layout.setContentsMargins(4, 4, 4, 4)
        self.asset_layout.setSpacing(14)
        self.scroll.setWidget(self.asset_host)
        right_layout.addWidget(self.scroll, 1)
        self.splitter.addWidget(self.asset_panel)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        root_layout.addWidget(self.splitter, 1)

        self.refresh_button.clicked.connect(self._refresh_assets)
        self.settings_button.clicked.connect(self._open_settings)
        self.hide_button.clicked.connect(self._toggle_asset_panel)
        self.splitter.splitterMoved.connect(self._splitter_moved)
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
            int(self.settings.get("ui_font_size", DEFAULT_SETTINGS["ui_font_size"]))
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
            item.setData(
                INCLUDE_SUBFOLDERS_ROLE,
                bool(entry.get("include_subfolders", entry.get("nested", False))),
            )
            self.folder_list.addItem(item)
        if self.folder_list.count() > 0:
            self.folder_list.setCurrentRow(0)
        else:
            self._clear_assets("Add asset paths from Settings.")

    def _folder_changed(self, current, previous):
        self.current_path = current.data(Qt.UserRole) if current else ""
        self.current_include_subfolders = (
            bool(current.data(INCLUDE_SUBFOLDERS_ROLE)) if current else False
        )
        self._refresh_assets()

    def _refresh_assets(self):
        if not self.current_path:
            self._clear_assets("No asset path is selected.")
            return
        if not os.path.isdir(self.current_path):
            self._clear_assets(f"Folder not found: {self.current_path}")
            return

        try:
            if self.current_include_subfolders:
                sections = self._collect_asset_sections(self.current_path)
            else:
                sections = [
                    (
                        self._folder_header(self.current_path),
                        list(self._iter_root_asset_files(self.current_path)),
                    )
                ]
            self._asset_sections = sections
            self._populate_asset_sections(sections)
        except OSError as exc:
            self._clear_assets(str(exc))

    def _collect_asset_sections(self, root_path):
        sections = [
            (self._folder_header(root_path), list(self._iter_root_asset_files(root_path)))
        ]
        for folder, dirnames, filenames in os.walk(root_path):
            dirnames.sort(key=str.lower)
            if folder == root_path:
                continue
            files = [
                os.path.join(folder, filename)
                for filename in sorted(filenames, key=str.lower)
                if filename.lower().endswith(SUPPORTED_EXTENSIONS)
            ]
            if files:
                sections.append((os.path.basename(os.path.normpath(folder)), files))
        return sections

    def _folder_header(self, path):
        return os.path.basename(os.path.normpath(path)) or path

    def _iter_root_asset_files(self, root_path):
        for entry in os.scandir(root_path):
            if entry.is_file() and entry.name.lower().endswith(SUPPORTED_EXTENSIONS):
                yield entry.path

    def _clear_assets(self, message=""):
        self._asset_sections = []
        self._remove_tiles()
        self.status_label.setText(message)

    def _remove_tiles(self):
        while self.asset_layout.count():
            item = self.asset_layout.takeAt(0)
            widget = item.widget()
            layout = item.layout()
            if widget is not None:
                widget.deleteLater()
            elif layout is not None:
                self._clear_layout(layout)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget is not None:
                widget.deleteLater()
            elif child_layout is not None:
                self._clear_layout(child_layout)

    def _populate_asset_sections(self, sections):
        self._remove_tiles()
        count = sum(len(files) for _, files in sections)
        suffix = "" if count == 1 else "s"
        self.status_label.setText(f"{count} asset{suffix}")
        thumb_size = int(
            self.settings.get("thumbnail_size", DEFAULT_SETTINGS["thumbnail_size"])
        )
        columns = self._thumbnail_columns(thumb_size)
        font_size = int(
            self.settings.get(
                "asset_name_font_size", DEFAULT_SETTINGS["asset_name_font_size"]
            )
        )

        for title, files in sections:
            if files:
                self._add_asset_section(title, files, columns, thumb_size, font_size)
        self.asset_layout.addStretch(1)

    def _thumbnail_columns(self, thumb_size):
        if not self.settings.get("auto_columns", DEFAULT_SETTINGS["auto_columns"]):
            return max(
                1, int(self.settings.get("columns", DEFAULT_SETTINGS["columns"]))
            )
        tile_width = thumb_size + 24
        spacing = 10
        available_width = max(1, self.scroll.viewport().width() - 8)
        return max(1, int((available_width + spacing) / (tile_width + spacing)))

    def _add_asset_section(self, title, files, columns, thumb_size, font_size):
        title_label = QLabel(title, self.asset_host)
        section_font = QFont(self.font())
        section_font.setBold(True)
        section_font.setPointSize(
            int(
                self.settings.get(
                    "header_font_size", DEFAULT_SETTINGS["header_font_size"]
                )
            )
        )
        title_label.setFont(section_font)
        title_label.setToolTip(title)
        title_label.setWordWrap(True)
        self.asset_layout.addWidget(title_label)

        grid_host = QWidget(self.asset_host)
        grid = QGridLayout(grid_host)
        grid.setContentsMargins(0, 0, 0, 10)
        grid.setSpacing(10)
        for index, path in enumerate(files):
            tile = AssetTile(
                path,
                make_thumbnail(path, thumb_size),
                thumb_size,
                font_size,
                grid_host,
            )
            tile.open_requested.connect(self._open_asset)
            tile.rename_requested.connect(self._rename_asset)
            tile.remove_requested.connect(self._remove_asset_file)
            grid.addWidget(tile, index // columns, index % columns)
        grid.setColumnStretch(columns, 1)
        self.asset_layout.addWidget(grid_host)

    def _open_asset(self, path):
        if not Krita:
            return
        app = Krita.instance()
        document = app.openDocument(path)
        if document and app.activeWindow():
            app.activeWindow().addView(document)

    def _rename_asset(self, path):
        current_name = os.path.basename(path)
        new_name, ok = QInputDialog.getText(
            self, "Rename Asset", "New file name", text=current_name
        )
        if not ok:
            return
        new_name = new_name.strip()
        if not new_name or new_name == current_name:
            return
        if os.path.basename(new_name) != new_name:
            QMessageBox.warning(self, "Rename Asset", "File name cannot contain a path.")
            return
        root, ext = os.path.splitext(new_name)
        if not ext:
            new_name = root + os.path.splitext(current_name)[1]
        target = os.path.join(os.path.dirname(path), new_name)
        if os.path.exists(target):
            QMessageBox.warning(
                self, "Rename Asset", "A file with that name already exists."
            )
            return
        try:
            os.rename(path, target)
        except OSError as exc:
            QMessageBox.warning(self, "Rename Asset", str(exc))
            return
        self._refresh_assets()

    def _remove_asset_file(self, path):
        answer = QMessageBox.question(
            self,
            "Remove Asset",
            f"Delete this file?\n{path}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        try:
            os.remove(path)
        except OSError as exc:
            QMessageBox.warning(self, "Remove Asset", str(exc))
            return
        self._refresh_assets()

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

    def _splitter_moved(self, *_args):
        self._queue_runtime_save()
        self._queue_asset_relayout()

    def _queue_runtime_save(self):
        if not self._restoring_layout:
            self._save_timer.start(500)

    def _queue_asset_relayout(self):
        if (
            self.settings.get("auto_columns", DEFAULT_SETTINGS["auto_columns"])
            and self._asset_sections
            and not self.asset_panel.isHidden()
        ):
            self._layout_timer.start(150)

    def _relayout_assets(self):
        if self._asset_sections and not self.asset_panel.isHidden():
            self._populate_asset_sections(self._asset_sections)

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
        self._queue_asset_relayout()

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
