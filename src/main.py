from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    
    # Define icon path with fallback support (development and PyInstaller build)
    if hasattr(sys, "_MEIPASS"):
        icon_path = Path(sys._MEIPASS) / "icone.ico"
    else:
        icon_path = Path(__file__).parent / "icone.ico"
        
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
        
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())