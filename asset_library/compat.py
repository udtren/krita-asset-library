"""PyQt5 / PyQt6 compatibility shim for Asset Library."""

try:
    from PyQt5.QtCore import Qt, QTimer, pyqtSignal
    from PyQt5.QtGui import QColor, QFont, QPainter, QPixmap
    from PyQt5.QtWidgets import (
        QAbstractItemView,
        QCheckBox,
        QDialog,
        QDialogButtonBox,
        QDockWidget,
        QFileDialog,
        QFormLayout,
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QHeaderView,
        QInputDialog,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QMenu,
        QMessageBox,
        QPushButton,
        QScrollArea,
        QSpinBox,
        QSplitter,
        QTableWidget,
        QTableWidgetItem,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )

    PYQT6 = False

except ImportError:
    from PyQt6.QtCore import Qt, QTimer, pyqtSignal
    from PyQt6.QtGui import QColor, QFont, QPainter, QPixmap
    from PyQt6.QtWidgets import (
        QAbstractItemView,
        QCheckBox,
        QDialog,
        QDialogButtonBox,
        QDockWidget,
        QFileDialog,
        QFormLayout,
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QHeaderView,
        QInputDialog,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QMenu,
        QMessageBox,
        QPushButton,
        QScrollArea,
        QSpinBox,
        QSplitter,
        QTableWidget,
        QTableWidgetItem,
        QTabWidget,
        QVBoxLayout,
        QWidget,
    )

    PYQT6 = True

    Qt.AlignCenter = Qt.AlignmentFlag.AlignCenter
    Qt.PointingHandCursor = Qt.CursorShape.PointingHandCursor
    Qt.KeepAspectRatio = Qt.AspectRatioMode.KeepAspectRatio
    Qt.SmoothTransformation = Qt.TransformationMode.SmoothTransformation
    Qt.UserRole = Qt.ItemDataRole.UserRole
    Qt.ItemIsUserCheckable = Qt.ItemFlag.ItemIsUserCheckable
    Qt.Checked = Qt.CheckState.Checked
    Qt.Unchecked = Qt.CheckState.Unchecked
    Qt.Horizontal = Qt.Orientation.Horizontal

    QFrame.StyledPanel = QFrame.Shape.StyledPanel

    QDialog.Accepted = QDialog.DialogCode.Accepted
    QDialog.Rejected = QDialog.DialogCode.Rejected

    QDialogButtonBox.Ok = QDialogButtonBox.StandardButton.Ok
    QDialogButtonBox.Cancel = QDialogButtonBox.StandardButton.Cancel

    QMessageBox.Yes = QMessageBox.StandardButton.Yes
    QMessageBox.No = QMessageBox.StandardButton.No

    QHeaderView.Stretch = QHeaderView.ResizeMode.Stretch
    QHeaderView.ResizeToContents = QHeaderView.ResizeMode.ResizeToContents

    QAbstractItemView.SelectRows = QAbstractItemView.SelectionBehavior.SelectRows
    QAbstractItemView.SingleSelection = QAbstractItemView.SelectionMode.SingleSelection
