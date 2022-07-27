

# requires some pyqt5 modules
from PyQt5 import QtWidgets, uic,QtGui
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtWidgets import QFileDialog,QMessageBox,QTableWidgetItem,QAbstractItemView,QListWidgetItem, QSplashScreen,QShortcut
from PyQt5.QtGui import QDesktopServices, QPixmap
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtGui import QKeySequence

# sub-modules
from attune.src.qtattune import TransactionDesigner
from attune.src.pandasmodel import PandasModel
from attune.src.mamba_interpreter2 import convert_code
from attune.src.mainloop_editor import MainLoopEditor
from attune.src.output_display import OutputDisplay
from attune.src import resources

from attune.src.draw_widget import MyDrawWidget, Box
from attune.src.yaml_editor import SettingsEditor


import subprocess

import sys
import os


class Gui:
    """
    The attune-gui for usage within Python
    """

    def __init__(self):
        pass

    def run(self):
        # runs the attune gui within Python

        app = QtWidgets.QApplication(sys.argv)

        pixmap = QPixmap("./splash.png")
        splash = QSplashScreen(pixmap)
        splash.show()


        # window = ProjectDesigner()
        window = TransactionDesigner()
        splash.finish(window)
        app.exec_()


def run_gui():
    g = Gui()
    g.run()


if __name__ == "__main__":
    run_gui()
