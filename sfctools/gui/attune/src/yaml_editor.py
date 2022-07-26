from PyQt5 import QtWidgets, uic,QtGui
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QFileDialog,QMessageBox,QTableWidgetItem,QAbstractItemView,QListWidgetItem
import sys
import os
import yaml
import shutil
# from pandasmodel import PandasModel
from PyQt5.QtGui import QDesktopServices
import pickle as pkl
import re
import matplotlib.pyplot as plt
from PyQt5.QtCore import Qt

from sfctools import Settings
from PyQt5.QtGui import QFont, QFontDatabase, QColor, QSyntaxHighlighter, QTextCharFormat
import pyperclip

from PyQt5.QtWidgets import QShortcut
from PyQt5.QtGui import QKeySequence

from .pandasmodel import PandasModel
import numpy as np

class Highlighter(QSyntaxHighlighter):
    def __init__(self,parent=None):
        super().__init__(parent)
        self._mapping = {}

    def add_mapping(self, pattern, pattern_format):
        self._mapping[pattern] = pattern_format

    def highlightBlock(self, text_block):

        for pattern, fmt in self._mapping.items():
            for match in re.finditer(pattern,text_block):
                start, end = match.span()
                self.setFormat(start, end-start, fmt)

class SettingsEditor(QtWidgets.QDialog):

    def __init__(self,parent=None,text="<no text found>"):

        super(SettingsEditor, self).__init__(parent) # Call the inherited classes __init__ method
        path = os.path.dirname(os.path.abspath(__file__))
        uic.loadUi(os.path.join(path,'settings_edit.ui'), self) # Load the .ui file

        self.backup_count = 0

        self.edit_count = 0

        self.setFixedSize(self.size())
        self.fmt = self.textEdit.currentCharFormat()
        self.highlighter = Highlighter()
        self.setUpEditor()

        self.pushButton.pressed.connect(self.copy_data)

        self.shortcut = QShortcut(QKeySequence("Ctrl+S"),self)
        self.shortcut.activated.connect(self.rebuild_table)

        self.textEdit.setPlainText(text)
        self.textEdit.textChanged.connect(self.update_text)

        self.tableView.setColumnWidth(0,30)
        self.tableView.setColumnWidth(1,300)

        self.searchEdit.textChanged.connect(self.find_param)
        self.tableView.doubleClicked.connect(self.scroll_to)
        # self.okButton.pressed.connect(self.send_data)

        self.update_valid()
        self.rebuild_table()

        self.tableBtn.pressed.connect(self.rebuild_table)
        self.btnValid.pressed.connect(self.update_valid)

        self.show()

    def update_text(self):
        # if there were more than 20 difs, check if settings are still valid automatically
        # cannot do this every time because it slows down the textedit a lot
        self.edit_count += 1
        if self.edit_count >= 20:
            self.edit_count = 0
            self.update_valid()

    def find_param(self):
        # find the parameter in the search field in the table

        df = Settings().get_hyperparams_info()
        my_index = list(df.index)
        search_word = self.searchEdit.text()

        if search_word in my_index:

            scroll_idx = my_index.index(search_word)
            try:
                self.tableView.selectRow(scroll_idx)
            except Exception as e:
                print(str(e))
            self.scroll_to()

    def rebuild_table(self):
        self.update_valid()
        # self.parent().save_and_build()
        
        #scroll_pos = self.textEdit.verticalScrollBar().value()
        try:
            model = PandasModel(Settings().get_hyperparams_info())
            self.tableView.setModel(model)
        except:
            self.parent().notify(msg="Something went wrong. Is the project empty?",title="Error")
        #self.textEdit.verticalScrollBar().setValue(scroll_pos)

    def scroll_to(self):
        # scroll to selected table item in te settings editor

        selected_rows = sorted(set(index.row() for index in
                          self.tableView.selectedIndexes()))

        if len(selected_rows) == 0:
            print("no selected rows")
            return

        selection = selected_rows[0]
        df = Settings().get_hyperparams_info()

        param_name = df.index[selection]
        print("PARAM_NAME",param_name)

        # find the parameter in the settings file left
        try:
            mytext = self.textEdit.toPlainText()
            for i,line in enumerate(mytext.split("\n")):
                if line.find("name: " + param_name) > -1:
                    minimum = self.textEdit.verticalScrollBar().minimum()
                    maximum = self.textEdit.verticalScrollBar().maximum()
                    self.textEdit.verticalScrollBar().setValue(int(np.clip(i,minimum,maximum)))
                    break

        except Exception as e:
            print(str(e))

    def copy_data(self):
        data = ""

        try:
            my_teststr = self.textEdit.toPlainText().replace("\t","    ")
            Settings().read(my_teststr,isfile=False)

            print(Settings().get_hyperparams_info())
            Settings().get_hyperparams_info().to_clipboard()

        except Exception as e:
            print("Error: " + str(e))


    def update_valid(self):
        # try to read this with yaml
        valid = True

        my_teststr = self.textEdit.toPlainText().replace("\t","    ")

        try:
            Settings().read(my_teststr,isfile=False)
        except:
            valid = False


        if valid:
            self.validLabel.setText("valid")
            self.validLabel.setStyleSheet("background-color: lightgreen")
        else:
            self.validLabel.setText("invalid")
            self.validLabel.setStyleSheet("background-color: yellow")

        self.update()

        self.send_data()



    def send_data(self):
        print("yaml editor send data")
        self.parent().settings_str = self.textEdit.toPlainText().replace("\t","    ")
        # self.close()
        if self.backup_count == 10:
            self.parent().auto_backup()
            self.backup_count = 0
        self.backup_count += 1

    def setUpEditor(self):


        for keyword in ["metainfo","params","hyperparams",
                         "depreciation", "price", "unit", "description"]:
            fmt = QTextCharFormat()
            fmt.setFontWeight(QFont.Bold)
            fmt.setForeground(QtGui.QColor("#f5f5f5"))
            pattern = r'%s\:' % keyword
            self.highlighter.add_mapping(pattern,fmt)

        for keyword in ["author", "date","info", "metainfo"]:
            fmt = QTextCharFormat()
            fmt.setFontWeight(QFont.Bold)
            fmt.setForeground(QtGui.QColor("#f5f5f5"))
            pattern = r'%s\:' % keyword
            self.highlighter.add_mapping(pattern,fmt)

        for keyword in ["name", "value"]:
            fmt = QTextCharFormat()
            fmt.setFontWeight(QFont.Bold)
            fmt.setForeground(QtGui.QColor("#ff4f4f"))
            pattern = r'%s\:' % keyword
            self.highlighter.add_mapping(pattern,fmt)


        self.highlighter.setDocument(self.textEdit.document())




if __name__ == "__main__":
    """
    """

    app = QtWidgets.QApplication(sys.argv)
    # window = ProjectDesigner()
    window = SettingsEditor()
    app.exec_()
