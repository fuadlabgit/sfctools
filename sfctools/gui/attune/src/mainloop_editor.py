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
from PyQt5 import QtCore
from PyQt5.QtGui import QFont, QFontDatabase, QColor, QSyntaxHighlighter, QTextCharFormat


from PyQt5.QtWidgets import QShortcut
from PyQt5.QtGui import QKeySequence


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


class MainLoopEditor(QtWidgets.QDialog):

    def __init__(self,parent,text=""):

        super(MainLoopEditor, self).__init__(parent) # Call the inherited classes __init__ method
        path = os.path.dirname(os.path.abspath(__file__))
        uic.loadUi(os.path.join(path,'simulation_edit.ui'), self) # Load the .ui file

        self.setFixedSize(self.size());

        self.backup_count = 0

        self.textEdit.textChanged.connect(self.text_changed)
        self.textEdit.cursorPositionChanged.connect(self.update_line_label)

        self.textEdit.installEventFilter(self)

        self.highlighter = Highlighter()

        self.setUpEditor()


        self.shortcut = QShortcut(QKeySequence("Ctrl+S"),self)
        self.shortcut.activated.connect(self.parent().save_and_build)


        self.shortcut2 = QShortcut(QKeySequence("Ctrl+Tab"),self)
        self.shortcut2.activated.connect(self.indent)

        self.shortcut2 = QShortcut(QKeySequence("Shift+Tab"),self)
        self.shortcut2.activated.connect(self.unindent)

        text = text.replace("    ","\t")
        self.textEdit.setPlainText(text)

        self.searchEdit.textChanged.connect(self.update_search)

        self.show()


    def update_search(self):
        self.setUpEditor()
        self.update()

    def eventFilter(self, obj, event):
        self.update()
        if event.type() == QtCore.QEvent.KeyPress and obj is self.textEdit:
            if event.key() == QtCore.Qt.Key_Tab: # and self.text_box.hasFocus():
                print('Tab pressed')
                self.indent()
                return True
        return False

    def indent(self):
        # inert tab for whole selection

        scroll_pos = self.textEdit.verticalScrollBar().value()

        cursor = self.textEdit.textCursor()
        old_position= cursor.position()

        start = cursor.selectionStart()
        end = cursor.selectionEnd()

        text = self.textEdit.toPlainText()

        mystr = text[:start]
        my_lines = []

        for line in text[start:end].split("\n"):
            my_lines.append("\t" + line)

        new_str =  "\n".join(my_lines)
        new_end = start + len(new_str)
        mystr += new_str

        mystr += text[end:]

        self.textEdit.setPlainText(mystr)

        cursor = self.textEdit.textCursor()
        if new_end - start > 1:

            cursor.setPosition(start)
            cursor.setPosition(new_end, QtGui.QTextCursor.KeepAnchor)
        else:
            cursor.setPosition(new_end)

        self.textEdit.setTextCursor(cursor)
        self.textEdit.verticalScrollBar().setValue(scroll_pos)

    def unindent(self):
        # inert tab for whole selection

        scroll_pos = self.textEdit.verticalScrollBar().value()

        cursor = self.textEdit.textCursor()
        old_position= cursor.position()

        start = cursor.selectionStart()
        end = cursor.selectionEnd()

        text = self.textEdit.toPlainText()

        mystr = text[:start]
        my_lines = []

        for line in text[start:end].split("\n"):
            if line.startswith("\t"):
                my_lines.append(line[1:])
            else:
                my_lines.append(line)

        new_str =  "\n".join(my_lines)
        new_end = start + len(new_str)
        mystr += new_str

        mystr += text[end:]

        self.textEdit.setPlainText(mystr)

        cursor = self.textEdit.textCursor()

        if new_end - start > 1:

            cursor.setPosition(start)
            cursor.setPosition(new_end, QtGui.QTextCursor.KeepAnchor)
        else:
            cursor.setPosition(new_end)

        self.textEdit.setTextCursor(cursor)
        self.textEdit.verticalScrollBar().setValue(scroll_pos)

    def text_changed(self):
        self.send_data()
        self.update_line_label()
        self.update()

    def update_line_label(self):
        cursor = self.textEdit.textCursor()
        x = cursor.blockNumber() + 1
        y = cursor.columnNumber() + 1
        self.lineLabel.setText('{0:d}, {1:d}'.format(x,y))

    def send_data(self):
        self.parent().mainloop_str = self.textEdit.toPlainText()
        if self.backup_count == 10:
            self.parent().auto_backup()
            self.backup_count = 0
        self.backup_count += 1

    def paintEvent(self,event):
        qp = QtGui.QPainter(self)
        pen = QtGui.QPen(Qt.black ,1, Qt.SolidLine)
        brush = QtGui.QBrush(Qt.black)
        qp.setBrush(brush)
        qp.setPen(pen)

        for block_number in range(self.textEdit.document().lineCount()):

            offset = self.textEdit.contentOffset()

            block= self.textEdit.document().findBlockByNumber(block_number)
            brect = self.textEdit.blockBoundingGeometry(block)
            # print("brect", brect)
            y = int(brect.y()+ offset.y()) + 53 #  53
            x = int(brect.x() + 6)
            w = brect.width()
            h = brect.height()

            if(y >= 50 and y <= 820):
                try:
                    qp.drawText(x,y+20,"%04i" % int(block_number))
                except:
                    pass

    def setUpEditor(self):
        self.highlighter = Highlighter()
        # python stuff
        fmt = QTextCharFormat()
        fmt.setForeground(QtGui.QColor("#b80000"))
        for pattern in ['def ','for ', 'if ', 'else:', "while ", ' in ', ' not ', 'elif ', "True", "False", "class "]:
            self.highlighter.add_mapping(pattern,fmt)

        # return statement
        fmt = QTextCharFormat()
        fmt.setForeground(QtGui.QColor("#dae0dc"))
        for pattern in ['return']:
            self.highlighter.add_mapping(pattern,fmt)

        #print
        fmt = QTextCharFormat()
        fmt.setForeground(QtGui.QColor("#3f88e8"))
        for pattern in ['print']:
            self.highlighter.add_mapping(pattern,fmt)

        # python stuff
        fmt = QTextCharFormat()
        fmt.setForeground(QtGui.QColor("#59de85"))
        for pattern in ['from ','import ']:
            self.highlighter.add_mapping(pattern,fmt)

        # comments
        fmt = QTextCharFormat()
        fmt.setForeground(QtGui.QColor("#121212"))
        self.highlighter.add_mapping(r'\"{3}[A-Za-z0-9_\n\t\wx^^    ]+\"{3}',fmt)

        fmt = QTextCharFormat()
        # fmt.setFontWeight(QFont.Bold)
        fmt.setForeground(QtGui.QColor("#6a6a6a"))
        pattern = r'\#\s.+'
        self.highlighter.add_mapping(pattern,fmt)

        searchtext = self.searchEdit.text()

        if searchtext != "":
            try:
                fmt = QTextCharFormat()
                # fmt.setFontItalic(True)
                fmt.setFontWeight(QFont.Bold)
                fmt.setForeground(QtGui.QColor("#fcf75b"))
                fmt.setBackground(QtGui.QColor("#000000"))
                self.highlighter.add_mapping(searchtext,fmt)
            except Exception as e:
                print(str(e))

        self.highlighter.setDocument(self.textEdit.document())
