import sys

from PyQt5 import QtWidgets

try:
    import slb
except ImportError:
    import os

    package_dir = os.path.abspath(os.path.dirname(__file__))
    sys.path.insert(0, package_dir)

from slb.custom_logging import setup_system
from slb.main_window import GUIWindow


def main():
    setup_system()

    app = QtWidgets.QApplication([])
    win = GUIWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
