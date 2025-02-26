from app import BookmarkManager
import sys
from PyQt6.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BookmarkManager()
    window.show()
    sys.exit(app.exec())
