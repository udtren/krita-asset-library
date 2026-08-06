"""Thumbnail loading helpers for Asset Library."""

import os
import zipfile

from .compat import QColor, QFont, QPainter, QPixmap, Qt


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
