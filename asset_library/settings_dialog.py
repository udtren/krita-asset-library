"""Settings dialog for Asset Library."""

from .compat import (
    QAbstractItemView,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    Qt,
    QVBoxLayout,
    QWidget,
)
from .constants import DEFAULT_SETTINGS


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
        self.up_button = QPushButton("Up", tab)
        self.down_button = QPushButton("Down", tab)
        path_header.addWidget(self.add_button)
        path_header.addWidget(self.remove_button)
        path_header.addWidget(self.up_button)
        path_header.addWidget(self.down_button)
        layout.addLayout(path_header)

        self.path_table = QTableWidget(0, 3, tab)
        self.path_table.setHorizontalHeaderLabels(
            ["Alias", "Path", "IncludeSubFolder"]
        )
        self.path_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.path_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.path_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents
        )
        self.path_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.path_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeToContents
        )
        layout.addWidget(self.path_table, 1)

        self.add_button.clicked.connect(self._add_path)
        self.remove_button.clicked.connect(self._remove_path)
        self.up_button.clicked.connect(lambda: self._move_selected_path(-1))
        self.down_button.clicked.connect(lambda: self._move_selected_path(1))
        return tab

    def _build_display_tab(self):
        tab = QWidget(self)
        layout = QVBoxLayout(tab)
        form = QFormLayout()
        self.auto_columns_check = QCheckBox("Auto columns", tab)
        self.columns_spin = self._spin(1, 12)
        self.thumbnail_spin = self._spin(48, 512)
        self.ui_font_spin = self._spin(7, 32)
        self.header_font_spin = self._spin(7, 32)
        self.asset_name_font_spin = self._spin(7, 32)
        form.addRow("Thumbnail columns", self.auto_columns_check)
        form.addRow("Fixed thumbnail columns", self.columns_spin)
        form.addRow("Thumbnail size", self.thumbnail_spin)
        form.addRow("Folder/Button font size", self.ui_font_spin)
        form.addRow("Header font size", self.header_font_spin)
        form.addRow("Asset filename font size", self.asset_name_font_spin)
        layout.addLayout(form)
        self.auto_columns_check.toggled.connect(self.columns_spin.setDisabled)
        layout.addStretch(1)
        return tab

    def _spin(self, minimum, maximum):
        spin = QSpinBox(self)
        spin.setRange(minimum, maximum)
        return spin

    def _load_values(self):
        for item in self._settings.get("paths", []):
            self._append_path_row(
                item.get("alias", ""),
                item.get("path", ""),
                item.get("include_subfolders", item.get("nested", False)),
            )
        self.auto_columns_check.setChecked(
            bool(self._settings.get("auto_columns", DEFAULT_SETTINGS["auto_columns"]))
        )
        self.columns_spin.setValue(
            int(self._settings.get("columns", DEFAULT_SETTINGS["columns"]))
        )
        self.columns_spin.setDisabled(self.auto_columns_check.isChecked())
        self.thumbnail_spin.setValue(
            int(
                self._settings.get("thumbnail_size", DEFAULT_SETTINGS["thumbnail_size"])
            )
        )
        self.ui_font_spin.setValue(
            int(self._settings.get("ui_font_size", DEFAULT_SETTINGS["ui_font_size"]))
        )
        self.header_font_spin.setValue(
            int(
                self._settings.get(
                    "header_font_size",
                    DEFAULT_SETTINGS["header_font_size"],
                )
            )
        )
        self.asset_name_font_spin.setValue(
            int(
                self._settings.get(
                    "asset_name_font_size",
                    DEFAULT_SETTINGS["asset_name_font_size"],
                )
            )
        )

    def _append_path_row(self, alias, path, include_subfolders=False):
        row = self.path_table.rowCount()
        self.path_table.insertRow(row)
        self._set_path_row(
            row,
            {
                "alias": alias or "",
                "path": path or "",
                "include_subfolders": include_subfolders,
            },
        )

    def _add_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Asset Folder")
        if not path:
            return
        alias, ok = QInputDialog.getText(self, "Folder Alias", "Alias (optional)")
        if ok:
            self._append_path_row(alias, path, False)

    def _remove_path(self):
        rows = sorted(
            {index.row() for index in self.path_table.selectedIndexes()}, reverse=True
        )
        for row in rows:
            self.path_table.removeRow(row)

    def _move_selected_path(self, direction):
        selected_rows = sorted(
            {index.row() for index in self.path_table.selectedIndexes()}
        )
        if not selected_rows:
            return
        row = selected_rows[0]
        target = row + direction
        if target < 0 or target >= self.path_table.rowCount():
            return
        row_data = self._path_row_values(row)
        self.path_table.removeRow(row)
        self.path_table.insertRow(target)
        self._set_path_row(target, row_data)
        self.path_table.selectRow(target)

    def _path_row_values(self, row):
        alias_item = self.path_table.item(row, 0)
        path_item = self.path_table.item(row, 1)
        include_item = self.path_table.item(row, 2)
        return {
            "alias": alias_item.text() if alias_item else "",
            "path": path_item.text() if path_item else "",
            "include_subfolders": (
                include_item.checkState() == Qt.Checked if include_item else False
            ),
        }

    def _set_path_row(self, row, data):
        self.path_table.setItem(row, 0, QTableWidgetItem(data.get("alias", "")))
        self.path_table.setItem(row, 1, QTableWidgetItem(data.get("path", "")))
        include_item = QTableWidgetItem()
        include_item.setFlags(include_item.flags() | Qt.ItemIsUserCheckable)
        include_item.setCheckState(
            Qt.Checked if data.get("include_subfolders", False) else Qt.Unchecked
        )
        self.path_table.setItem(row, 2, include_item)

    def values(self):
        paths = []
        for row in range(self.path_table.rowCount()):
            row_data = self._path_row_values(row)
            alias = row_data["alias"].strip()
            path = row_data["path"].strip()
            if path:
                paths.append(
                    {
                        "alias": alias,
                        "path": path,
                        "include_subfolders": row_data["include_subfolders"],
                    }
                )
        updated = dict(self._settings)
        updated.update(
            {
                "paths": paths,
                "auto_columns": self.auto_columns_check.isChecked(),
                "columns": self.columns_spin.value(),
                "thumbnail_size": self.thumbnail_spin.value(),
                "ui_font_size": self.ui_font_spin.value(),
                "header_font_size": self.header_font_spin.value(),
                "asset_name_font_size": self.asset_name_font_spin.value(),
            }
        )
        return updated
