"""Asset thumbnail tile widget."""

import os

from .compat import QFont, QFrame, QLabel, Qt, QVBoxLayout, pyqtSignal


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
