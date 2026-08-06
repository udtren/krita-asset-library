"""Asset thumbnail tile widget."""

import os

from .compat import QFont, QFrame, QLabel, QMenu, Qt, QVBoxLayout, pyqtSignal


class AssetTile(QFrame):
    open_requested = pyqtSignal(str)
    insert_layer_requested = pyqtSignal(str)
    insert_file_layer_requested = pyqtSignal(str)
    rename_requested = pyqtSignal(str)
    remove_requested = pyqtSignal(str)
    duplicate_requested = pyqtSignal(str)

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
        self.image.contextMenuEvent = self.contextMenuEvent
        layout.addWidget(self.image)

        self.name = QLabel(os.path.basename(file_path), self)
        self.name.setAlignment(Qt.AlignCenter)
        self.name.setWordWrap(True)
        font = QFont(self.name.font())
        font.setPointSize(font_size)
        self.name.setFont(font)
        self.name.contextMenuEvent = self.contextMenuEvent
        layout.addWidget(self.name)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        open_action = menu.addAction("Open")
        insert_layer_action = menu.addAction("Insert as New Layer")
        insert_file_layer_action = menu.addAction("Insert as New File Layer")
        duplicate_action = menu.addAction("Duplicate")
        rename_action = menu.addAction("Rename")
        remove_action = menu.addAction("Delete")
        exec_menu = menu.exec_ if hasattr(menu, "exec_") else menu.exec
        selected = exec_menu(event.globalPos())
        if selected == open_action:
            self.open_requested.emit(self.file_path)
        elif selected == insert_layer_action:
            self.insert_layer_requested.emit(self.file_path)
        elif selected == insert_file_layer_action:
            self.insert_file_layer_requested.emit(self.file_path)
        elif selected == duplicate_action:
            self.duplicate_requested.emit(self.file_path)
        elif selected == rename_action:
            self.rename_requested.emit(self.file_path)
        elif selected == remove_action:
            self.remove_requested.emit(self.file_path)
