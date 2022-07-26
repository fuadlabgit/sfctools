from PyQt5 import QtWidgets, uic,QtGui
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QFileDialog,QMessageBox,QTableWidgetItem,QAbstractItemView,QListWidgetItem,QShortcut
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
from PyQt5.QtGui import QKeySequence

from .mamba_interpreter2 import convert_code

from PyQt5.QtGui import QFont, QFontDatabase, QColor, QSyntaxHighlighter, QTextCharFormat
from PyQt5.QtGui import QKeySequence,QFontMetrics


class Highlighter(QSyntaxHighlighter):
    def __init__(self,parent=None):
        super().__init__(parent)
        self._mapping = {}

    def add_mapping(self, pattern, pattern_format):
        self._mapping[pattern] = pattern_format


    def highlightBlock(self, text_block):
        # print("highligth block", text_block, )

        try:

            for pattern, fmt in self._mapping.items():
                for match in re.finditer(pattern,text_block):
                    start, end = match.span()
                    self.setFormat(start, end-start, fmt)
        except:
            pass


class CodeEditor(QtWidgets.QDialog):

    instances = {}

    def closeEvent(self, event):
        del self.__class__.instances[self.box.name]
        event.accept() # let the window close

    def __init__(self,parent,box,text=""):

        super(CodeEditor, self).__init__(parent) # Call the inherited classes __init__ method

        self.__class__.instances[box.name] = self
        path = os.path.dirname(os.path.abspath(__file__))
        uic.loadUi(os.path.join(path,'code_editor.ui'), self) # Load the .ui file

        self.backup_count = 0

        self.large_size = QtCore.QSize(1569,874)
        self.small_size = QtCore.QSize(800,874)
        self.size = "small"
        self.pushButton.pressed.connect(self.switch_size)

        self.search_idx = -1
        self.matched_lines = []
        self.matched_lines_idx = 0

        self.shortcut = QShortcut(QKeySequence("Ctrl+S"),self)
        self.shortcut.activated.connect(self.parent().parent().save_and_build)
        # self.shortcut.activated.connect(lambda: print("ACTIVATED"))

        self.textEdit.installEventFilter(self)
        self.textEdit.cursorPositionChanged.connect(self.update_line_label)

        self.linedict = {}

        self.shortcut3 = QShortcut(QKeySequence("Shift+Tab"),self)
        self.shortcut3.activated.connect(self.unindent)

        self.setFixedSize(self.small_size)
        self.highlighter = Highlighter(self)
        self.setUpEditor()

        if text == "":
            text = "$[AGENT] %s\n\n\n$[END]\n" % (box.name)

        self.textEdit.setPlainText(text)
        self.textEdit.textChanged.connect(self.update_interpreter)
        self.searchEdit.textChanged.connect(self.update_search)

        self.box = box
        try:
            self.setWindowTitle("Edit Agent " + str(self.box.name).capitalize())
        except Exception as e:
            print(str(e))

        self.highlighter_rects = []


        self.count_interpr_max = 5
        self.count_update_max = 5
        self.count_interpr = self.count_interpr_max
        self.count_update = self.count_update_max
        # self.okButton.pressed.connect(self.send_data)
        self.show()

        self.nextButton.pressed.connect(self.update_matched_line)

    def update_matched_line(self):

        # update matched lines
        searchstr = self.searchEdit.text()
        mystring = self.textEdit.toPlainText()
        self.matched_lines = []
        for i,line in enumerate(mystring.split('\n')):
            if searchstr in line:
                self.matched_lines.append(i)

        # update scrolling

        if len(self.matched_lines) <= 0:
            return

        self.matched_lines_idx += 1
        if self.matched_lines_idx >= len(self.matched_lines):
            self.matched_lines_idx = 0
        #print("matched_lines",self.matched_lines)

        #print("IDX",self.matched_lines_idx)
        matchline = self.matched_lines[self.matched_lines_idx]
        self.textEdit.verticalScrollBar().setValue(max(0,matchline - 1))

        self.update_line_highlight()


    def paintEvent(self,event):

        qp = QtGui.QPainter(self)
        pen = QtGui.QPen(Qt.black ,1, Qt.SolidLine)
        brush = QtGui.QBrush(Qt.black)
        qp.setBrush(brush)
        qp.setPen(pen)

        font = self.textEdit.document().defaultFont()
        metrics = QFontMetrics(font)

        for block_number in self.highlighter_rects:
            offset = self.textEdit.contentOffset()

            block= self.textEdit.document().findBlockByNumber(block_number)
            brect = self.textEdit.blockBoundingGeometry(block)
            # print("brect", brect)
            y = int(brect.y()+ offset.y()) + 53
            x = int(brect.x() + 6)
            w = brect.width()
            h = brect.height()

            qp.drawRect(x,y+3,7,7)


    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.KeyPress and obj is self.textEdit:
            if event.key() == QtCore.Qt.Key_Tab: # and self.text_box.hasFocus():
                # print('Tab pressed')
                self.indent()
                return True

        elif event.type() == QtCore.QEvent.Wheel:

            self.update_line_highlight()
            self.count_interpr = 0
            self.update_interpreter()
            self.repaint()

        self.count_update -=1
        if self.count_update <= 0:
            self.update()
            self.count_update = self.count_update_max

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


    def switch_size(self):

        if self.size == "large":
            self.size = "small"
            self.setFixedSize(self.small_size)

        elif self.size == "small":
            self.size = "large"
            self.setFixedSize(self.large_size)

        self.count_interpr = 0
        self.update_interpreter()


    def update_interpreter(self):
        """
        interpret each line of code here
        """

        # old_text = self.textEdit.toPlainText()
        # self.textEdit.setPlainText(str(old_text.encode("utf-8").decode('cp1252')))

        scroll_pos = self.textEdit2.verticalScrollBar().value()

        if self.count_interpr <= 0 or self.size=="large":
            self.count_interpr = self.count_interpr_max

            code_lines = self.textEdit.toPlainText().split("\n")
            translated_code,mydict = convert_code(code_lines)
            self.textEdit2.setPlainText(translated_code)
            self.linedict = mydict

        self.count_interpr -= 1

        self.textEdit2.verticalScrollBar().setValue(scroll_pos)

        self.update_line_highlight()
        self.send_data()

    def update_line_highlight(self):
        code_lines = self.textEdit.toPlainText().split("\n")

        self.highlighter_rects = []
        for i,line in enumerate(code_lines):
            if line.startswith("+[FUN]"):
                self.highlighter_rects.append(i)
        # print("highlighter_rects", self.highlighter_rects)

    def update_line_label(self):
        cursor = self.textEdit.textCursor()
        x = cursor.blockNumber() + 1
        y = cursor.columnNumber() + 1
        z = -1

        # print("linedict",self.linedict)

        if int(x) in self.linedict:
            z = int(self.linedict[int(x)]) - 2
            # print("z = ", z)

        if z < 0:
            z = -1

        #self.lineLabel.setText('Row {0:d}, Col {1:d} Python {2:d}'.format(x,y,z))
        self.lineLabel.setText('Line {0:d}, Python: {1:d}'.format(x,z))


    def update_search(self):
        self.setUpEditor()
        self.update_interpreter()

    def send_data(self):
        self.box.parent_widget.code_data[self.box.name] = str(self.textEdit.toPlainText())
        # self.close()
        if self.backup_count == 50:
            self.parent().parent().auto_backup()
            self.backup_count = 0
        self.backup_count += 1

    def setUpEditor(self):
        self.highlighter = Highlighter(self)

        # Agent
        agent_format = QTextCharFormat()
        #agent_format.setFontWeight(QFont.Bold)
        agent_format.setForeground(QtGui.QColor("#36ad97"))
        pattern = r'\$\[[A-Za-z0-9]+\]'
        self.highlighter.add_mapping(pattern,agent_format)

        import_format = QTextCharFormat()
        #import_format.setFontWeight(QFont.Bold)
        import_format.setForeground(QtGui.QColor("#635b5a"))
        pattern = r'\+\[IMPORT\]'
        self.highlighter.add_mapping(pattern,import_format)

        fmt = QTextCharFormat()
        #fmt.setFontWeight(QFont.Bold)
        fmt.setForeground(QtGui.QColor("#d42408"))
        pattern = r'\+\[KNOWS\]'

        self.highlighter.add_mapping(pattern,fmt)

        fmt = QTextCharFormat()
        #fmt.setFontWeight(QFont.Bold)
        fmt.setForeground(QtGui.QColor("#d42408"))
        pattern = r'\+\[PARAM\]'
        self.highlighter.add_mapping(pattern,fmt)

        fmt = QTextCharFormat()
        # fmt.setFontWeight(QFont.Bold)
        fmt.setForeground(QtGui.QColor("#8874a3"))
        pattern = r'\+\[FUN\]'
        self.highlighter.add_mapping(pattern,fmt)

        fmt = QTextCharFormat()
        # fmt.setFontWeight(QFont.Bold)
        fmt.setForeground(QtGui.QColor("#8874a3"))
        pattern = r'\+\[ENDFUN\]'
        self.highlighter.add_mapping(pattern,fmt)


        fmt = QTextCharFormat()
        #fmt.setFontWeight(QFont.Bold)
        fmt.setForeground(QtGui.QColor("#3148cc"))
        pattern = r'\$\.[A-Za-z0-9_]+'
        self.highlighter.add_mapping(pattern,fmt)


        fmt = QTextCharFormat()
        # mt.setFontWeight(QFont.It)
        fmt.setForeground(QtGui.QColor("#a69819"))
        pattern = r'\<\~\~\>\s+[A-Za-z0-9,\@\s\_]+'
        self.highlighter.add_mapping(pattern,fmt)

        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Bold)
        fmt.setForeground(QtGui.QColor("#5a5e5e"))
        pattern = r'\@[A-Za-z0-9_]+'
        self.highlighter.add_mapping(pattern,fmt)

        fmt = QTextCharFormat()
        # fmt.setFontItalic(True)
        fmt.setFontWeight(QFont.Bold)
        fmt.setForeground(QtGui.QColor("#03318c"))
        self.highlighter.add_mapping(r'balance\_sheet',fmt)
        self.highlighter.add_mapping(r'income\_statement',fmt)

        fmt = QTextCharFormat()
        # fmt.setFontItalic(True)
        fmt.setFontWeight(QFont.Bold)
        fmt.setForeground(QtGui.QColor("#614d70"))
        self.highlighter.add_mapping(r'update',fmt)
        self.highlighter.add_mapping(r'file_bankruptcy',fmt)

        fmt = QTextCharFormat()
        # fmt.setFontItalic(True)
        # fmt.setFontWeight(QFont.Bold)
        fmt.setForeground(QtGui.QColor("#d42408"))
        self.highlighter.add_mapping(r'\+\[INIT\]',fmt)
        self.highlighter.add_mapping(r'\+\[ENDINIT\]',fmt)

        fmt = QTextCharFormat()
        # fmt.setFontItalic(True)
        # fmt.setFontWeight(QFont.Bold)
        fmt.setForeground(QtGui.QColor("#366630"))
        self.highlighter.add_mapping(r'\+\[ACCOUNTING\]',fmt)
        self.highlighter.add_mapping(r'\+\[ENDACCOUNTING\]',fmt)


        fmt = QTextCharFormat()
        fmt.setForeground(QtGui.QColor("#044bd6"))
        for element in ["gross_income","gross_spendings","ebit","net_income","noi","get_entry","get_balance","net_worth",
                        "total_assets","total_liabilities"]:
        #["REVENUES","GAINS","EXPENSES","LOSSES", "NONTAX_PROFITS", "NONTAX_LOSSES","INTEREST", "TAXES", "NOI",

            self.highlighter.add_mapping(element,fmt)

        fmt = QTextCharFormat()
        # fmt.setFontItalic(True)
        # fmt.setFontWeight(QFont.Bold)
        fmt.setForeground(QtGui.QColor("#4bd16f"))
        for i in ["ASSETS", "EQUITY", "LIABILITIES"]+["REVENUES", "GAINS", "EXPENSES", "LOSSES", "NONTAX_PROFITS", "NONTAX_LOSSES", "INTEREST", "TAXES", "NOI"]:
            self.highlighter.add_mapping(i,fmt)

        fmt = QTextCharFormat()
        # fmt.setFontItalic(True)
        # fmt.setFontWeight(QFont.Bold)
        fmt.setForeground(QtGui.QColor("#4bd16f"))
        self.highlighter.add_mapping("BALANCE?.",fmt)
        self.highlighter.add_mapping("INCOME?.",fmt)

        fmt = QTextCharFormat()
        # fmt.setFontItalic(True)
        # fmt.setFontWeight(QFont.Bold)
        fmt.setForeground(QtGui.QColor("#888f8a"))
        self.highlighter.add_mapping("<>",fmt)
        self.highlighter.add_mapping("<.>",fmt)


        fmt = QTextCharFormat()
        # fmt.setFontItalic(True)
        # fmt.setFontWeight(QFont.Bold)
        fmt.setForeground(QtGui.QColor("#bd1a91"))
        self.highlighter.add_mapping("\$URAND",fmt)


        fmt = QTextCharFormat()
        # fmt.setFontItalic(True)
        # fmt.setFontWeight(QFont.Bold)
        fmt.setForeground(QtGui.QColor("#bd1a91"))
        self.highlighter.add_mapping("\$NRAND",fmt) # <- TODO add to mamba interpreter


        fmt = QTextCharFormat()
        # fmt.setFontItalic(True)
        # fmt.setFontWeight(QFont.Bold)
        fmt.setForeground(QtGui.QColor("#b3a834"))
        self.highlighter.add_mapping("\!LOG",fmt)  # <- TODO add to mamba interpreter

        fmt = QTextCharFormat()
        # fmt.setFontItalic(True)
        fmt.setFontWeight(QFont.Bold)
        fmt.setForeground(QtGui.QColor("#334f7a"))
        self.highlighter.add_mapping("print",fmt)


        fmt = QTextCharFormat()
        # fmt.setFontItalic(True)
        fmt.setFontWeight(QFont.Bold)
        #fmt.setForeground(QtGui.QColor("#bd1a91"))
        self.highlighter.add_mapping("return",fmt)
        self.highlighter.add_mapping("pass",fmt)
        self.highlighter.add_mapping("rematch",fmt)


        # pythonic syntax
        fmt = QTextCharFormat()
        # fmt.setFontItalic(True)
        fmt.setFontWeight(QFont.Bold)
        # fmt.setForeground(QtGui.QColor("#d42408"))
        for i in ["self","if ","elif ", "else", "for ","while ", " in ", " not ", "True", "False"]: #, "\(", "\)"]:
            self.highlighter.add_mapping(i,fmt)
            # TODO hide this in comments

        fmt = QTextCharFormat()
        # fmt.setFontWeight(QFont.Bold)
        fmt.setForeground(QtGui.QColor("#ababab"))
        pattern = r'\#.+'
        self.highlighter.add_mapping(pattern,fmt)


        searchtext = self.searchEdit.text()

        if searchtext != "":
            try:
                fmt = QTextCharFormat()
                # fmt.setFontItalic(True)
                fmt.setFontWeight(QFont.Bold)
                fmt.setForeground(QtGui.QColor("#ffff2e"))
                fmt.setBackground(QtGui.QColor("#000000"))
                self.highlighter.add_mapping(searchtext,fmt)
            except Exception as e:
                print(str(e))

        #self.textEdit.setPlainText(self.textEdit.toPlainText())

        fmt = QTextCharFormat()
        # fmt.setFontItalic(True)
        fmt.setForeground(QtGui.QColor("#5a14ff"))
        fmt.setBackground(QtGui.QColor("#dbdbdb"))
        self.highlighter.add_mapping("NOTE",fmt)


        fmt = QTextCharFormat()
        # fmt.setFontItalic(True)
        fmt.setForeground(QtGui.QColor("#ff4f14"))
        fmt.setBackground(QtGui.QColor("#dbdbdb"))
        self.highlighter.add_mapping("TODO",fmt)



        self.highlighter.setDocument(self.textEdit.document())




if __name__ == "__main__":
    """
    """

    app = QtWidgets.QApplication(sys.argv)
    # window = ProjectDesigner()
    window = CodeEditor()
    app.exec_()
