
from PyQt5 import QtWidgets, uic,QtGui
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtWidgets import QFileDialog,QMessageBox,QTableWidgetItem,QAbstractItemView,QListWidgetItem, QSplashScreen,QShortcut
from PyQt5.QtGui import QDesktopServices, QPixmap
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtGui import QKeySequence

import sys
import os

import yaml
import shutil
import time

import sympy

# packages for graph
import re as regex
import matplotlib.pyplot as plt
import pydot
#import mpimg
import networkx as nx
import numpy as np
from graphviz import Source

# packages for matrix
from sympy.parsing.sympy_parser import parse_expr
from sympy import *
from sympy import simplify, init_printing, printing
import pandas as pd

import pyperclip
import pdflatex
from collections import defaultdict

import subprocess

# sub-modules
from .pandasmodel import PandasModel
from .mamba_interpreter2 import convert_code
from .mainloop_editor import MainLoopEditor
from .output_display import OutputDisplay
from . import resources

from .draw_widget import MyDrawWidget, Box
from .yaml_editor import SettingsEditor


class MatrixViewer(QtWidgets.QDialog):
    def __init__(self,parent=None):
        super(MatrixViewer, self).__init__(parent)  # Call the inherited classes __init__ method
        path = os.path.dirname(os.path.abspath(__file__))
        uic.loadUi(os.path.join(path,'matrix_viewer.ui'), self)


# Step 1: Create a worker
class StatusLED(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)

    def __init__(self,rb):
        super().__init__()
        self.rb = rb


        # self.rb = rb
        self.i = 0
        self.j = 0
        self.on = False
        # print("WORKER CREATED")

    def run(self):
        """Long-running task."""
        while(True):
            time.sleep(.1)

            if self.on:
                self.i += 1

                state = self.rb.isChecked()
                self.rb.setChecked(not state)

                if self.i == 5:
                    self.i = 0
                    self.switch_state()
            else:

                self.rb.setChecked(False)

            #print("state",self.i)

    def switch_state(self):
        self.on = not self.on
        print("switch", self.on)

        if not self.on:
            self.rb.setChecked(False)

class TransactionDesigner(QtWidgets.QMainWindow):
    def __init__(self):
        super(TransactionDesigner, self).__init__() # Call the inherited classes __init__ method
        print("load...")
        path = os.path.dirname(os.path.abspath(__file__))
        #uic.loadUi('transaction_designer.ui', self) # Load the .ui file
        uic.loadUi(os.path.join(path,'transaction_designer_mainwindow.ui'), self) # Load the .ui file
        print("done.")

        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint)
        self.setFixedSize(self.size());
        self.flipped = False

        my_widget = MyDrawWidget(self)
        my_widget.move(880,160)

        # status LED
        self.thread = QThread()

        self.worker = StatusLED(self.radioButton)
        self.worker.moveToThread(self.thread)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.started.connect(self.worker.run)
        self.thread.start()

        self.current_file = None

        # --

        self.drawcanvas = my_widget
        self.drawcanvas.mode = "drag"

        self.backup_str = ""
        #self.setMouseTracking(True)

        #self.nextButton.pressed.connect(self.goto_next)
        self.browseButton.triggered.connect(self.browse)
        #self.saveButton.triggered.connect(self.save)
        self.saveAsButton.triggered.connect(self.save_dlg)
        self.saveBuildButton.triggered.connect(self.save_and_build)
        self.FlipHeightButton.pressed.connect(self.flip_height)

        self.actionShow_Output_Log.triggered.connect(self.show_output_display)

        #self.showgraphButton.triggered.connect(self.show_graph)
        self.genMatButton.triggered.connect(self.gen_matrix)
        #self.genCodeButton.triggered.connect(self.gen_code)
        #self.genTexButton.pressed.connect(self.gen_tex_description)
        self.genICSButton.triggered.connect(self.gen_tex_ics)

        self.editMainLoopButton.triggered.connect(self.edit_mainloop)

        self.buildProjectButton.triggered.connect(lambda: self.build_project(overwrite=True))
        self.runButton.triggered.connect(self.run_project)

        self.shortcut = QShortcut(QKeySequence("Ctrl+S"),self)
        self.shortcut.activated.connect(self.save_and_build)
        self.actionAbout.triggered.connect(lambda: self.notify("attune Beta ver. 0.1, Please report bugs to thomas.baldauf@dlr.de",title="About this software"))

        self.transactionView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.transactionView.doubleClicked.connect(self.data_select)
        self.transactionView.setColumnWidth(0, 120)

        self.arrangeButton.pressed.connect(self.arrange_pretty)
        self.removeButton.pressed.connect(self.remove_item)

        self.mainloop_str = ""

        self.settings_str = """
metainfo:
	author: your name here
	date: 2022
	info: example settings

hyperparams:
       - name: example
         value: 42.0
         description: an example parameter
"""

        self.editSettingsButton.triggered.connect(self.edit_settings)

        self.addButton.pressed.connect(self.add_new) # add an agent
        self.addButton2.pressed.connect(self.add_helper) # add a helper agent (no transactions)
        self.graphDeleteButton.pressed.connect(self.remove_helper)

        #self.saveButton.pressed.connect(self.save)

        # self.graphSelectButton.pressed.connect(self.change_graphmode_select)
        # self.graphDragButton.pressed.connect(self.change_graphmode_drag)

        self.graphEditButton.pressed.connect(self.edit_graph_agent)

        #for widget in [self.AssetListLeft, self.AssetListRight,
        #               self.LiabilityListLeft, self.LiabilityListRight,
        #               self.EquityListLeft, self.EquityListRight]:
        #    widget.textChanged.connect(self.update_data)

        self.udpateButton.pressed.connect(self.update_data)

        self.filename = None    # current .yaml file
        self.entry_data = [] # store current entries
        self.selection_idx = None

        #self.matrixView = MatrixViewer(self)

        self.show() # Show the GUI

    def edit_mainloop(self):
        try:
            print("self.mainloop_str",self.mainloop_str)
            lines = self.mainloop_str

            my_edit = MainLoopEditor(parent=self, text=lines)

        except Exception as e:
            self.notify(str(e), title="Error")

    def flip_height(self):
        if self.flipped:
            self.setFixedSize(1825,990)
            self.flipped = False
        else:
            self.setFixedSize(1825,80)
            self.flipped = True


    def show_output_display(self):
        # shows the logger display for output quantities

        try:

            path = os.path.dirname(self.current_file)+"/output/"
            print("[DEBUG MESSAGE] open output display in path", path)

            output_display = OutputDisplay(self,path = path)
        except Exception as e:
            self.notify(str(e),title="Error")

    def save_and_build(self):

        # -- create new status signal

        self.worker.switch_state()
        # ---

        self.save()
        try:
            self.build_project(silent=True)
            self.statusBar().showMessage("Saved " + self.current_file)

        except Exception as e:
            # self.notify(str(e),title="Exception")
            print(str(e))

    def run_project(self):

        self.save_and_build()

        # self.show_output_display()

        self.setCursor(Qt.WaitCursor)

        try:
            # self.tabWidget.setCurrentIndex(1)

            #filename = os.path.dirname(self.current_file) + "/python_code/mainloop.py"
            filename = os.path.dirname(self.current_file) + "/runner.py"
            folder = os.path.dirname(self.current_file) + "/"

            # print("lookup", filename, "in", folder)

            old_dir = os.getcwd()
            # print("old_dir",old_dir)

            os.chdir(folder)
            cmd = "conda activate attune /k python %s" % filename
            print("COMMAND", cmd)
            os.system("start cmd     %s" % cmd)

            os.chdir(old_dir)

        except Exception as e:

            self.notify(str(e),title="")
            self.setCursor(Qt.ArrowCursor)

        self.setCursor(Qt.ArrowCursor)

    def build_project(self,silent=False,overwrite=False):

        #folder = QFileDialog.getExistingDirectory (self, 'Build Project...', os.getcwd())

        if self.current_file is None:
            self.notify(message="Cannot build project. Please save to file first.",title="Error")
            return

        folder = os.path.dirname(self.current_file)
        print("build project in ", folder)

        try:
            os.mkdir(folder + "/mamba_code/")
        except:
            pass

        try:
            os.mkdir(folder + "/python_code/")
        except:
            pass

        try:
            os.mkdir(folder + "/output/")
        except:
            pass

        try:

            for agent, code in self.drawcanvas.code_data.items():

                # write mamba code for completeness
                path = folder + "/mamba_code/%s.txt" % agent

                print("path",path)

                with open(path, "w") as file:
                    file.write(code)

                # write python code
                path = folder + "/python_code/%s.py" % agent.lower()

                print("path",path)

                with open(path, "w") as file:
                    new_code = convert_code(code.split("\n"))[0]
                    new_code = new_code.encode("utf-8").decode('cp1252')
                    file.write(new_code) # convert using the mamba interpreter

            # write settings file
            with open(folder + "/python_code/settings.yml","w") as file:
                file.write(self.settings_str)

            # write the runner file
            if self.mainloop_str == "" or overwrite:
                with open(folder+"/runner.py","w") as file:
                    file.write("from python_code.mainloop import run\n\nrun()\n")

            # write main simulation file
            with open(folder + "/python_code/mainloop.py","w") as file:
            #with open(folder + "./mainloop.py","w") as file:
                if self.mainloop_str == "" or overwrite:

                    qm = QMessageBox
                    ret = qm.question(self,'', "WARNING - You are about to overwrite the mainloop.py script. This operation cannot be reverted. Continue?", qm.Yes | qm.No)
                    if ret == qm.No:
                        return

                    if overwrite and self.mainloop_str != "":
                        with open(folder + "/python_code/mainloop_backup.py","w") as backupfile:
                        #with open(folder + "./mainloop_backup.py","w") as backupfile:
                            backupfile.write(self.mainloop_str.replace("\t","    "))

                    simu_str = """
\"\"\"
This the main ABM Simulation file
Cretaed with MAMBA GUI

@author: <Your name>
@date: <Your date>
\"\"\"

from sfctools import Agent, World, Settings, Clock, FlowMatrix
"""
                    for agent in self.drawcanvas.code_data.keys():
                        simu_str += "from python_code.%s import %s\n" % (agent.lower(),agent.capitalize())

                    simu_str += """

def iter():
    \"\"\"
    this is one iteration
    \"\"\"

    # TODO modify iteration here
"""

                    for agent in self.drawcanvas.code_data.keys():
                        a = agent.capitalize()
                        simu_str += "\tfor a in World().get_agents_of_type('%s'):\n\t\tprint('Do something with' + str(a))\n\n" % (a)
                    simu_str += """\n
def run():
    \"\"\"
    this is the main simulation loop
    \"\"\"
"""


                    simu_str += """\n

    Settings().read(\"python_code/settings.yml\") # read settings file

    \"\"\"
    Simulation parameters
    \"\"\"

    # number of agents to be created
"""

                    for agent in self.drawcanvas.code_data.keys():
                        simu_str += "\tN_%s = 1\n" % agent.capitalize()
                    simu_str += """
    # TODO^ set the correct value

    # number of simulation steps
    T = 100

    # TODO^ set the correct values

    # create Agents:
"""
                    for agent in self.drawcanvas.code_data.keys():
                        a = agent.capitalize()
                        simu_str += "\t[%s() for i in range(N_%s)]\n" % (a,a)

                    simu_str += "\n"
                    simu_str += "\t# inter-link agents \n"

                    simu_str += "\tWorld().link()\n\n"

                    # for agent in self.drawcanvas.code_data.keys():
                    #    a = agent.capitalize()
                    #    simu_str += "\t[i.link() for i in %s_pile]\n" % (a)

                    simu_str += """
    for i in range(T):
        iter()

        # TODO write outputs here ...

        Clock().tick()

    print(FlowMatrix().to_string())
"""
                    self.mainloop_str = simu_str

                else:
                    simu_str = self.mainloop_str

                print("SIMU STR", simu_str)
                file.write(simu_str.replace("\t","    "))

                if not silent:
                    self.notify("Project files built!",title="Success")

                self.gen_code() # generate transactions.py

        except Exception as e:
            self.notify("Could not build project.",title="Error on Project Build")

    def auto_backup(self):
        try:
            folder = self.current_file
            if folder is not None:
                self.saveas(folder[:-6] +"_autobackup.mamba") # makes a backup file
            else:
                # self.notify("You are working on a blank project file. Please save your changes soon.", title="Warning")
                self.statusBar().showMessage("WARNING: You are working on a blank project file. Please save your changes soon.")
        except Exception as e:
            self.notify(str(e), title="Error on AutoBackup")

    def edit_settings(self):
        if self.settings_str =="" or self.settings_str is None:
            self.notify(message="Something went wrong. Have you built the project?",title="Error")
            return

        my_edit = SettingsEditor(parent=self, text=self.settings_str)

    def edit_graph_agent(self):
        self.drawcanvas.edit_agent()

    def change_graphmode_select(self):

        self.drawcanvas.mode = "select"

    def change_graphmode_drag(self):

        self.drawcanvas.mode = "drag"

    def arrange_pretty(self):
        self.update_table()
        self.drawcanvas.arrange_pretty()


    def update_graphics_data(self, box, conn):
        pass


    def notify(self,message,title):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.open()


    def browse(self):
        try:
            filename = QFileDialog.getOpenFileName(self, 'Open file',
                                    os.path.abspath(os.path.join(os.getcwd(), '../projects/')), "MAMBA Files (*.mamba);;Transaction Files (*.trans)")[0]
        except:
            self.notify("Seems as if the projects folder does not yet exist. please create it manually in the parent directory of src", title="Projects folder")

        filename_backup = self.filename
        current_file_backup = self.current_file

        self.filename = filename
        self.current_file = filename

        try:
            print("FILENAME",filename)

            # load entries into the list
            with open(filename, 'r') as stream:
                transaction_data = yaml.safe_load(stream)

                print("transaction_data",transaction_data)
                try:

                    # new format
                    self.entry_data = transaction_data["transactions"]
                    self.drawcanvas.clear(clearall=True)
                    # add the helper agents

                    for k,v in transaction_data["agents"].items():
                        self.drawcanvas.add_agent(k)


                    # add the transactions (connectors and boxes)
                    self.update_table()

                    self.drawcanvas.code_data = transaction_data["agents"]
                    print("CODE DATA",transaction_data["agents"])
                    self.drawcanvas.reposition(transaction_data["box_positions"])
                    self.settings_str = transaction_data["settings"]
                    try:
                        self.mainloop_str = transaction_data["mainloop"]
                    except:
                        print("NO MAINLOOP FOND. SKIPPING")

                    self.statusBar().showMessage("Opened file " + filename)

                except:

                    # old format as fallback
                    self.entry_data = transaction_data
                    self.update_table()
                    print("wARNING - FALLBACK TO OLD FILE FORMAT!")

                # self.fileEdit.setText(filename)

        except Exception as e :

            # self.notify(message="Something went wrong when opening the file:\n %s"%str(e),title="Error")
            self.filename = filename_backup
            self.curent_file = current_file_backup
            if str(self.current_file) != "":
                self.statusBar().showMessage("Cancelled. Restored file '%s'" % str(self.current_file))


    def entry_to_vals(self,entry, agent,which):

        if not bool(regex.findall("([+-]+)", entry)):
            self.notify(message="Sign corrupted in entry %s (%s of %s)"%(entry,which,agent),title="Error")
            return None, None, None

        if regex.findall("([+-]+)", entry)[0] == "-":
            sign = "-"
        else:
            sign = "+"

        words = regex.findall("([\w\s]+)", entry)

        item = ""
        silent = False
        for word in words:
            if word != "s":
                item += word.strip() + " "
            elif word == "s":
                silent = True

        item = item.strip()

        return sign, item, silent


    def update_table(self):
        #self.selection_idx = None
        self.transactionView.setRowCount(0)

        #self.transactionView.model().setTorizontalHeaderItem( 0, QTableWidgetItem("Name"))
        #self.transactionView.model().setTorizontalHeaderItem( 1, QTableWidgetItem("Short Name"))
        #self.transactionView.model().setTorizontalHeaderItem( 2, QTableWidgetItem("Unidirectional"))
        #self.transactionView.model().setTorizontalHeaderItem( 3, QTableWidgetItem("Flow"))

        # insert new rows if needed
        row_count = self.transactionView.rowCount()
        if row_count < len(self.entry_data):
            for i in range(len(self.entry_data)-row_count):
                self.transactionView.insertRow(row_count)

        self.drawcanvas.clear()

        # update the data
        for i, data in enumerate(self.entry_data):
            print(data)



            self.transactionView.setItem(i, 0, QTableWidgetItem(data["subject"]))
            self.transactionView.setItem(i, 1, QTableWidgetItem(data["agent1"]))
            self.transactionView.setItem(i, 2, QTableWidgetItem(data["agent2"]))
            self.transactionView.setItem(i, 3, QTableWidgetItem(data["shortname"]))
            self.transactionView.setItem(i, 4, QTableWidgetItem(data["kind"]))
            self.transactionView.setItem(i, 5, QTableWidgetItem(str(data["uni-directional"])))
            self.transactionView.setItem(i, 6, QTableWidgetItem(str(data["quantity"])))
            # self.transactionView.selectionModel().selectedRows()

            box1 = self.drawcanvas.add_agent(data["agent1"])
            box2 = self.drawcanvas.add_agent(data["agent2"])


            self.drawcanvas.add_connection(box1,box2, name= data["shortname"])


        if self.selection_idx is not None:
            for i in range(self.transactionView.columnCount()):
                try:
                    self.transactionView.item(self.selection_idx, i).setBackground(QtGui.QColor(159, 159, 159))
                except:
                    pass
                    # avoids None pointer when a transaction is deleted

        self.drawcanvas.update()

    def data_select(self):

        #selected_rows = self.transactionView.selectionModel().selectedRows()
        selected_rows = sorted(set(index.row() for index in
                          self.transactionView.selectedIndexes()))

        if len(selected_rows) == 0:
            print("no selected rows")
            return

        selection = selected_rows[0]

        self.row_select(selection)


    def data_select_where(self,expr):
        print("data select where",expr)

        for i in range(self.transactionView.rowCount()):
                my_entry = self.transactionView.item(i, 3).text()

                print("...",i,my_entry)
                if my_entry == expr:

                    self.row_select(i)
                    return

    def row_select(self,selection):

        # color the selected row
        # gb(233, 234, 227);
        try:
            if self.selection_idx is not None:
                for i in range(self.transactionView.columnCount()):
                    self.transactionView.item(self.selection_idx, i).setBackground(QtGui.QColor(233, 234, 227))

            for i in range(self.transactionView.columnCount()):
                self.transactionView.item(selection, i).setBackground(QtGui.QColor(159, 159, 159))
        except:
            pass

        try:
            self.selection_idx = selection
            print("selection",selection)

            data = self.entry_data[selection]

            print("data", data)

            self.AssetListLeft.clear()
            self.LiabilityListLeft.clear()
            self.LiabilityListRight.clear()
            self.AssetListRight.clear()
            self.EquityListLeft.clear()
            self.EquityListRight.clear()

            self.AssetListLeft.setPlainText(data["a1"])
            self.AssetListRight.setPlainText(data["a2"])
            self.LiabilityListLeft.setPlainText(data["l1"])  # +data["e1"])
            self.LiabilityListRight.setPlainText(data["l2"]) # +data["e2"])
            self.EquityListLeft.setPlainText(data["e1"])
            self.EquityListRight.setPlainText(data["e2"])

            self.agent1Edit.setText(data["agent1"])
            self.agent2Edit.setText(data["agent2"])

            log_transaction = data["log transaction"] or "False"
            self.registerFlowBox.setCurrentIndex(self.registerFlowBox.findText(str(log_transaction)))

            cashflow1 = data["cashflow1"] or "None"
            cashflow2 = data["cashflow2"] or "None"
            self.comboCashLeft.setCurrentIndex(self.comboCashLeft.findText(str(cashflow1)))
            self.comboCashRight.setCurrentIndex(self.comboCashRight.findText(str(cashflow2)))

            trtype = data["kind"] or "KA->KA"
            self.editType.setCurrentIndex(self.editType.findText(str(trtype)))

            ics1 = data["income1"] or "None"
            ics2 = data["income2"] or "None"
            self.comboIncomeLeft.setCurrentIndex(self.comboIncomeLeft.findText(ics1))
            self.comboIncomeRight.setCurrentIndex(self.comboIncomeRight.findText(ics2))

            self.editQuantity.setText(data["quantity"])
            self.editSubject.setText(data["subject"])

            self.drawcanvas.highlight_connector(data["shortname"])

            if "description" in data:
                self.editDescription.setText(data["description"])
            else:
                self.editDescription.setText("")
            self.editShortname.setText(data["shortname"])

            unidir = str(data["uni-directional"]) or "None"
            self.comboUnidir.setCurrentIndex(self.comboUnidir.findText(unidir))
            
        except Exception as e:
            self.notify(str(e),title="Error")


    def update_data(self):
        if self.selection_idx is None:
            return


        self.entry_data[self.selection_idx]["a1"] = self.AssetListLeft.toPlainText()
        self.entry_data[self.selection_idx]["a2"] = self.AssetListRight.toPlainText()
        self.entry_data[self.selection_idx]["l1"] = self.LiabilityListLeft.toPlainText()
        self.entry_data[self.selection_idx]["l2"] = self.LiabilityListRight.toPlainText()
        self.entry_data[self.selection_idx]["e1"] = self.EquityListLeft.toPlainText()
        self.entry_data[self.selection_idx]["e2"] = self.EquityListRight.toPlainText()

        self.entry_data[self.selection_idx]["a1"]  = self.AssetListLeft.toPlainText()
        self.entry_data[self.selection_idx]["a2"] = self.AssetListRight.toPlainText()
        self.entry_data[self.selection_idx]["l1"]  = self.LiabilityListLeft.toPlainText()
        self.entry_data[self.selection_idx]["l2"]  = self.LiabilityListRight.toPlainText()
        self.entry_data[self.selection_idx]["e1"]  = self.EquityListLeft.toPlainText()
        self.entry_data[self.selection_idx]["e2"]  = self.EquityListRight.toPlainText()




        only_rename = True
        if self.entry_data[self.selection_idx]["agent1"]  != self.agent1Edit.text():
            only_rename = False
        if self.entry_data[self.selection_idx]["agent2"]  !=self.agent2Edit.text():
            only_rename = False


        if not self.drawcanvas.check_exist(self.agent1Edit.text()):
            qm = QMessageBox
            ret = qm.question(self,'', "The agent %s does not exist.\nDo you wish to continue and automatically create a new agent?"%self.agent1Edit.text(), qm.Yes | qm.No)
            if ret == qm.No:
                return

        if not self.drawcanvas.check_exist(self.agent2Edit.text()):
            qm = QMessageBox
            ret = qm.question(self,'', "The agent %s does not exist.\nDo you wish to continue and automatically create a new agent?"%self.agent2Edit.text(), qm.Yes | qm.No)
            if ret == qm.No:
                return

        self.entry_data[self.selection_idx]["agent1"]  = self.agent1Edit.text().capitalize() # upper because agents are always uppercase
        self.entry_data[self.selection_idx]["agent2"]  =self.agent2Edit.text().capitalize()

        self.agent1Edit.setText(self.agent1Edit.text().capitalize())
        self.agent2Edit.setText(self.agent2Edit.text().capitalize())

        self.entry_data[self.selection_idx]["uni-directional"] = \
            str(self.comboUnidir.currentText())

        self.entry_data[self.selection_idx]["log transaction"] =\
            str(self.registerFlowBox.currentText())

        self.entry_data[self.selection_idx]["cashflow1"] = \
            str(self.comboCashLeft.currentText())
        self.entry_data[self.selection_idx]["cashflow2"] = \
            str(self.comboCashRight.currentText())

        self.entry_data[self.selection_idx]["kind"] = \
            str(self.editType.currentText())

        self.entry_data[self.selection_idx]["income1"] = \
            str(self.comboIncomeLeft.currentText())
        self.entry_data[self.selection_idx]["income2"] = \
            str(self.comboIncomeRight.currentText())


        if only_rename:

            self.drawcanvas.rename_connection(self.entry_data[self.selection_idx]["shortname"] , str(self.editShortname.text()))

        else:
            self.drawcanvas.remove_connection(self.entry_data[self.selection_idx]["shortname"]) #, str(self.editSubject.text()))

            box1 = self.drawcanvas.add_agent(self.entry_data[self.selection_idx]["agent1"])
            box2 = self.drawcanvas.add_agent(self.entry_data[self.selection_idx]["agent2"])

            self.drawcanvas.add_connection(box1,box2, str(self.editShortname.text()))


        self.entry_data[self.selection_idx]["quantity"] = \
            str(self.editQuantity.text())


        self.entry_data[self.selection_idx]["subject"] = \
            str(self.editSubject.text())




        self.entry_data[self.selection_idx]["shortname"] = \
            str(self.editShortname.text())

        self.entry_data[self.selection_idx]["description"] = \
            str(self.editDescription.text())

        self.update_table()

        print("data changed.")

    def save(self):

        try:


            filename = self.current_file # statusBar().currentMessage()

            if filename is not None:

                self.saveas(filename)

                # TODO maybe backup(?)
                # self.notify("File saved under %s" % filename,title="Ok")
                print("FILE SAVED!")
            else:
                self.save_dlg()

        except Exception as e:
            if filename != "":
                self.notify(str(e),title="Error")



    def save_dlg(self):
        try:

            filename = QFileDialog.getSaveFileName(self, 'Save file',
                                               os.getcwd(), "MAMBA Files (*.mamba)")[0]
            self.statusBar().showMessage("Saved file " + filename)

            current_file_backup = self.current_file

            if filename is not None and filename != "":
                self.current_file = filename
                self.saveas(filename)

            # TODO maybe backup(?)

        except Exception as e:
            self.notify("Could not save project.",title="Error")
            self.current_file = current_file_backup


    def saveas(self,filename):

        # drawcanvas code_data
        code_data = {}
        for k,v in self.drawcanvas.code_data.items():
            code_data[k] = str(v.encode("utf-8").decode('cp1252'))
            # fix some potential encoding errors

        try:
            print("FILENAME", filename)

            # load entries into the list
            with open(filename, 'w') as stream:

                data = {"transactions": self.entry_data,
                "agents": code_data,
                "box_positions": self.drawcanvas.box_positions(),
                "settings": self.settings_str,
                "mainloop": self.mainloop_str}

                yaml.dump(data,stream)

        except Exception as e:
            self.notify(message=str(e), title="Error")


    def show_graph(self):
        jailbrakes = {}

        G = nx.MultiDiGraph()

        k = 0
        # select = self.parent.transaction_data.cursor_line
        for entry in self.entry_data:

            agent1 = entry["agent1"]
            agent2 = entry["agent2"]

            shortname = "T%s" % k
            if "shortname" in entry:
                shortname = entry["shortname"]

            if True: # agent1 != agent2:
                # edges.append([agent1,agent2])
                tex_subject = sympy.latex(sympy.simplify(entry["quantity"]), mode="inline")

                # print("my_flat_label",my_flat_label)

                G.add_edge(str(agent1).replace("_", " ").title(),
                           str(agent2).replace("_", " ").title(),
                           label=shortname,
                           arrowsize=1.2,
                           arrowhead="normal",
                           # style="tapered",
                           # dir="back",
                           penwidth=1.2,
                           labelfontsize=16,
                           labeldistance=0.1,
                           labelangle=-90.0,
                           overlap=0)  # str(my_label))
                # texlbl=my_label) # "\'dummy\'",texlbl=my_label)
                jailbrakes["T%s" % k] = tex_subject
                k += 1

            assets1 = entry["a1"] + "\n"
            liabs1 = entry["l1"] + "\n" + entry["e1"] + "\n"

            assets2 = entry["a2"] + "\n"
            liabs2 = entry["l2"] + "\n" + entry["e2"] + "\n"


        nx.set_node_attributes(G, "box", "shape")
        nx.set_node_attributes(G, 1.8, "width")
        nx.set_node_attributes(G, .9, "height")
        nx.set_node_attributes(G, 16, "samplepoints")
        nx.set_node_attributes(G, "gray", "color")
        nx.set_node_attributes(G, "filled", "style")

        #nx.drawing.nx_pydot.pydot_layout(G) # ,prog="dot")

        # nx.set_node_attributes(G, "test","texlbl")
        # nx.set_node_attributes(G, "    ", "label")
        np.random.seed(1234)
        path = os.path.dirname(os.path.abspath(__file__))
        nx.drawing.nx_pydot.write_dot(G, path + '/files/graph.dot')

        s = Source.from_file(os.getcwd() + "/files/graph.dot")
        print(s)
        # s.view()

        (graph,) = pydot.graph_from_dot_file(path + "/files/graph.dot")
        graph.write_pdf(path + '/files/mygraph.pdf')
        graph.write_png(path + '/files/mygraph.png')

        img = plt.imread(path + '/files/mygraph.png')
        imgplot = plt.imshow(img)
        plt.axis('off')
        plt.show()


    def gen_matrix(self):
        flow_data = {}

        flow_data["CA"] = defaultdict(lambda: defaultdict(list))  # current account
        flow_data["KA"] = defaultdict(lambda: defaultdict(list))  # capital account

        # flow_data[KA or CA][subject][agent]
        if len(self.entry_data) == 0:
            self.notify(message="Cannot generate Matrix. Have you set up any transactions yet?",title="Error")
            return

        for filedata in self.entry_data:
                            """
                            evaluate transaction entries with the flow logger
                            """
                            subject = filedata["subject"].replace("_", " ").title()
                            kind = filedata["kind"]
                            log_flow = False
                            if filedata["log transaction"] == "True":
                                log_flow= True
                            #   log_flow = bool(filedata["log transaction"])
                            print("LOG FLOW",log_flow,"raw",filedata["log transaction"])
                            quantity = filedata["quantity"]
                            agent1 = filedata["agent1"].replace("_", " ").title()
                            agent2 = filedata["agent2"].replace("_", " ").title()

                            # upper part of matrix
                            if log_flow:
                                account_from = kind.split("->")[0]
                                account_to = kind.split("->")[1]

                                flow_data[account_from][subject][agent1].append("-" + str(quantity))
                                flow_data[account_to][subject][agent2].append(str(quantity))

                            # lower part of matrix = changes in assets ans liabilities

                            a1 = filedata["a1"]  # + "\n"
                            e1 = filedata["e1"]  # + "\n"
                            l1 = filedata["l1"]  # + "\n"
                            a2 = filedata["a2"]  # + "\n"
                            e2 = filedata["e2"]  # + "\n"
                            l2 = filedata["l2"]  # + "\n"

                            # assets
                            for item_name in a1.split("\n"):  # + e1.split("\n"):
                                if item_name != "":
                                    name = item_name[1:].strip()
                                    sign = item_name[0]

                                    if sign == "+":
                                        flipped_sign = "-"
                                    else:
                                        flipped_sign = "+"

                                    if not "(s)" in name:
                                        flow_data["KA"]["Δ %s" % name][agent1].append(
                                            "(" + flipped_sign + quantity + ")")

                            for item_name in a2.split("\n"):  # + e2.split("\n"):
                                if item_name != "":
                                    name = item_name[1:].strip()
                                    sign = item_name[0]

                                    if sign == "+":
                                        flipped_sign = "-"
                                    else:
                                        flipped_sign = "+"

                                    if not "(s)" in name:
                                        flow_data["KA"]["Δ %s" % name][agent2].append(
                                            "(" + flipped_sign + quantity + ")")

                            # liabilities
                            for item_name in l1.split("\n"):
                                if item_name != "":
                                    name = item_name[1:].strip()
                                    sign = item_name[0]

                                    if not "(s)" in name:
                                        flow_data["KA"]["Δ %s" % name][agent1].append(
                                            "(" + sign + quantity + ")")

                            for item_name in l2.split("\n"):
                                if item_name != "":
                                    name = item_name[1:].strip()
                                    sign = item_name[0]

                                    if not "(s)" in name:
                                        flow_data["KA"]["Δ %s" % name][agent2].append(
                                            "(" + sign + quantity + ")")

        # print(flow_data)
        df_credit = pd.DataFrame(flow_data["CA"]).T
        df_capital = pd.DataFrame(flow_data["KA"]).T

        df_merge = pd.concat([df_credit, df_capital], axis=1, keys=['CA', 'KA']).swaplevel(0, 1,
                                                                                           axis=1).sort_index(
            axis=1)

        # append new columns
        col_dict_ca = {
        }
        for col in df_credit.columns:
            col_dict_ca[col] = col + " (CA)"

        col_dict_ka = {
        }
        for col in df_capital.columns:
            col_dict_ka[col] = col + " (KA)"

        df_credit = df_credit.rename(columns = col_dict_ca)
        df_capital = df_capital.rename(columns=col_dict_ka)

        df_merge2 = pd.concat([df_credit, df_capital], axis=1)

        df_merge2 = df_merge2.reindex(sorted(df_merge2.columns), axis=1)
        df_merge2 = df_merge2.reindex(sorted(df_merge2.index), axis=0)

        df = df_merge.fillna(0.0).sort_index()

        def join_elements(my_item):
            if isinstance(my_item, list):
                my_list = []
                for subitem in my_item:
                    if subitem != "0":
                        my_list.append(subitem)

                return "+".join(my_list)

            elif my_item == 0.0:
                return "0"
            else:
                return my_item

        df = df.applymap(join_elements)

        # sum over the columns

        def eval_sum(column):
            column = [str(c).replace("^", "**") for c in column]
            my_expr = "+".join(column)
            return parse_expr(my_expr)

        df["Total"] = df.T.agg(eval_sum)  # df.T.sum()
        df.loc["Total"] = df.agg(eval_sum)
        print("TOTAL",df.loc["Total"])
        df_merge2["Total"] = df["Total"]

        # get the new columns



        # iterate through the columns
        print(df.columns)
        for column in df.columns:
            if column[0] != "Total":
                print(column[0] + " "  + "(%s)" % column[1],df.loc["Total"][column])
                df_merge2.loc["Total",column[0] + " "  + "(%s)" % column[1]] = df.loc["Total"][column]



        def simplify_expr(my_item):
            return simplify(my_item)

        df = df.applymap(simplify_expr)

        df_for_excel = df.copy()


        def abbreviate_zeros_latex(my_item):
            if my_item == "0" or my_item == 0:
                return " .- "  # .- "
            else:
                s = printing.latex(my_item ,mode="inline") #  mode="inline")
                print(s)
                return s

        #df_backup = df.copy()
        df = df.applymap(abbreviate_zeros_latex)


        df_merge2 = df_merge2.replace(np.nan, '', regex=True)
        df_merge2 = df_merge2.replace("0", '', regex=True)
        df_merge2 = df_merge2.replace(0, '', regex=True)
        df_merge2 = df_merge2.replace(0.0, '', regex=True)

        # print(df.to_string())
        # df.iloc[0,0] = "$\\alpha$"

        pd.options.display.max_colwidth = None

        df_html = """
<html>
<head>
<title>Mathedemo</title>
<script type="text/x-mathjax-config">
  MathJax.Hub.Config({tex2jax: {inlineMath: [['$','$'], ['\\(','\\)']]}});
</script>
<script type="text/javascript"
  src="http://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.1/MathJax.js?config=TeX-AMS-MML_HTMLorMML">
</script>
<link rel="stylesheet" href="mystyle.css">
</head>

<body>
%s
</body>
</html>
"""%  df.to_html()

        pageSource = """
                     <html><head>
                     </head>
                     <body>
                     <p>asdf</p>
                     </body></html>
                     """

        # BLA

        # write page source to html
        if False:
            # DEPRECIATED
            path = os.path.dirname(os.path.abspath(__file__))
            file = open(os.path.join(path,"files/mymatrix.html"),"w",encoding='utf-8')
            file.write(df_html)
            file.close()

        # QDesktopServices.openUrl(QUrl("./files/matrix.html"))

        model = PandasModel(df_merge2)
        mview = MatrixViewer(self)
        mview.tableView.setModel(model)
        # mview.webView.setHtml(df_html)
        mview.show()


        try:
            self.convert_df_to_tex(df)
        except Exception as e:
            self.notify(str(e),title="Error during Tex Conversion")

        # print("VIEW")
        # print(df_html)

        def convert_excel(my_item):
            if my_item == "0" or my_item == 0:
                return " .- "  # .- "
            else:
                s = pretty(my_item) # printing.latex(my_item) # ,mode="inline") #  mode="inline")
                print(s)
                return s

        try:
            df_for_excel = df_for_excel.applymap(convert_excel)
            path = os.path.dirname(os.path.abspath(__file__))
            df_for_excel.to_excel(os.path.join(path,"files/FlowMatrix_formatted.xlsx"))
            df_merge2.to_excel(os.path.join(path,"files/FlowMatrix.xlsx"))
        except Exception as e:
            self.notify(str(e), title="Error during Excel conversion")


    def remove_item(self):
        selected_rows = sorted(set(index.row() for index in
                                   self.transactionView.selectedIndexes()))

        if len(selected_rows) == 0:
            self.notify("no selected rows",title="Error")
            return

        selection = selected_rows[0]


        qm = QtWidgets.QMessageBox
        ret = qm.question(self, '', "Are you sure you want to remove the entry '%s'?"%self.entry_data[selection]["subject"], qm.Yes | qm.No)
        if ret == qm.Yes:

            self.drawcanvas.remove_connection(self.entry_data[selection]["shortname"])

            self.transactionView.removeRow(selection)
            del self.entry_data[selection]


        self.update_table()


    def convert_df_to_tex(self,df):

        def wrapstring(s):
            # wraps string
            return textwrap.wrap(s, width=10)

        def abbreviate_zeros(my_item):
            if my_item == "0" or my_item == 0:
                return " .- "  # .- "
            else:
                my_item = str(my_item)
                max_len = 10
                if len(my_item) > max_len:
                    return my_item[:max_len] + "..."
                else:
                    return my_item

        df_backup = df.copy()

        df_latex = df.to_latex(longtable=False, escape=False).replace("Δ", "$\Delta$")

        df_latex = df_latex.replace("\\begin{tabular}", "\\begin{tabularx}{\\textwidth}")
        df_latex = df_latex.replace("\\end{tabular}", "\\end{tabularx}")
        df_latex = "\\begin{small}\n" + df_latex + "\n\end{small}"

        df_latex = df_latex.replace("\\left(", "(")
        df_latex = df_latex.replace("\\right)", ")")

        df_latex = df_latex.replace("{l", "{L{3cm}")

        df_latex = """
\\documentclass[a3paper,landscape]{article}
\\usepackage{booktabs}
\\usepackage{adjustbox}
\\usepackage[table]{xcolor}
\\usepackage{longtable}
\\usepackage{tabularx,ragged2e}
\\definecolor{Gray}{gray}{0.90}
\\definecolor{LightGray}{gray}{0.95}
\\definecolor{White}{rgb}{1,1,1}

\\newcolumntype{g}{>{\\columncolor{White}\\arraybackslash}L} %
\\newcolumntype{l}{>{\\columncolor{White}\\arraybackslash}p{3cm}} %centered "X" column
\\newcolumntype{L}[1]{>{\\raggedright\\arraybackslash}p{\\dimexpr#1-2\\tabcolsep-2\\arrayrulewidth+.21pt}}

\\usepackage[left=1cm,right=1.5cm]{geometry}

\\begin{document}\n""" + df_latex   + "\n\\end{document}"

        pyperclip.copy(df_latex)
        #self.notify(message="LaTeX code copied to clipboard. Have fun!", title="Have fun")
        self.statusBar().showMessage("LaTeX code copied to clipboard. Have fun!")


        # -------------
        if False: # DEPRECIATED
            try:
                from pdflatex import PDFLaTeX
                path = os.path.dirname(os.path.abspath(__file__))
                my_file = os.path.join(path,"mymatrix")

                file = open(my_file, "w")
                file.write("""
        \\documentclass[a3paper,landscape]{article}
        \\usepackage{booktabs}
        \\usepackage{adjustbox}
        \\usepackage[table]{xcolor}
        \\usepackage{longtable}
        \\usepackage{tabularx,ragged2e}
        \\definecolor{Gray}{gray}{0.90}
        \\definecolor{LightGray}{gray}{0.95}
        \\definecolor{White}{rgb}{1,1,1}

        \\newcolumntype{g}{>{\\columncolor{White}\\arraybackslash}L} %
        \\newcolumntype{l}{>{\\columncolor{White}\\arraybackslash}p{3cm}} %centered "X" column
        \\newcolumntype{L}[1]{>{\\raggedright\\arraybackslash}p{\\dimexpr#1-2\\tabcolsep-2\\arrayrulewidth+.21pt}}

        \\usepackage[left=1cm,right=1.5cm]{geometry}

        \\begin{document}""")
                file.write(df_latex)
                file.write("""
        \\end{document}""")
                file.close()
                # pdfl = PDFLaTeX.from_texfile('my_texfile.tex')
                # pdf, log, completed_process = pdfl.create_pdf(keep_pdf_file=True, keep_log_file=True)
                # os.popen("pdflatex %s" % (os.getcwd()+"/my_texfile.tex"))
                import subprocess
                path = os.path.dirname(os.path.abspath(__file__))
                subprocess.run("pdflatex %s" % (os.path.join(path,"mymatrix.tex"))).check_returncode()

                #os.startfile(os.getcwd() + "\\mymatrix.pdf")
                try:
                    # shutil.rmtree(os.getcwd()+"\\files")
                    # os.mkdir(os.getcwd()+"\\files")

                    path = os.path.dirname(os.path.abspath(__file__))
                    shutil.move(path+"\\mymatrix.tex" , path+ "\\files\\mymatrix.tex")
                    shutil.move(path + "\\mymatrix.log", path + "\\files\\mymatrix.log")
                    shutil.move(path + "\\mymatrix.aux", path + "\\files\\\mymatrix.aux")
                    shutil.move(path + "\\mymatrix.pdf", path + "\\files\\mymatrix.pdf")
                    #shutil.copy(os.getcwd() + "\\files\\mymatrix.html",os.getcwd() + "\\files\\mymatrix.html")
                    #shutil.copy(os.getcwd() + "\\files\\mystyle.css", os.getcwd() + "\\files\\mystyle.css")
                except Exception as e:
                    self.notify(message=str(e),title="An Error occurred...(ID 1308)")

            except Exception as e:
                self.notify(message=str(e),title="An Error occurred...(ID 1311)")
            # -------------

            pd.options.display.max_colwidth = 2

            df_display = df_backup.applymap(abbreviate_zeros).to_string(line_width=None).replace("\_", "_")

            # self.parent.parentApp.getForm("AGGR_FLOW").data_box.values = df_display.split("\n")
            # self.parent.parentApp.switchForm("AGGR_FLOW")


    def gen_code(self,show_notification=False):

        code = ""
        code += "from sfctools import FlowMatrix \nimport numpy as np\n"
        code += "from sfctools import BalanceEntry,Accounts\n"
        code += "from sfctools import CashFlowEntry\n"
        code += "from sfctools import ICSEntry\n"
        code += "CA = Accounts.CA\nKA = Accounts.KA\n\n"

        subjects_count = defaultdict(lambda: 0.0)

        for filedata in self.entry_data:
            agent1 = filedata["agent1"]
            agent2 = filedata["agent2"]

            if agent1 == agent2:
                agent2 = "other_" + agent2

            a1 = filedata["a1"]  # + "\n"
            e1 = filedata["e1"]  # + "\n"
            l1 = filedata["l1"]  # + "\n"
            a2 = filedata["a2"]  # + "\n"
            e2 = filedata["e2"]  # + "\n"
            l2 = filedata["l2"]  # + "\n"

            flow_check = False
            print("FLOW CHECK", filedata["shortname"],filedata["log transaction"])
            if isinstance(filedata["log transaction"],str) and filedata["log transaction"].strip() == "True":
                # bool(filedata["log transaction"])
                flow_check = True
                print(flow_check)
            elif isinstance(filedata["log transaction"],str) and filedata["log transaction"].strip() == "False":
                # bool(filedata["log transaction"])
                flow_check = False
                print(flow_check)
            else:
                flow_check = filedata["log transaction"]
                print(flow_check)
            #print("FLOW CHECK", filename, flow_check)
            print("type", type(flow_check))

            kind = filedata["kind"]

            #subject =  filedata["subject"].replace(" ","_") + "_" + filedata["shortname".replace(" ","_")].lower()
            subject =  filedata["shortname".replace(" ","_")].lower()
            subject_str =  filedata["subject".replace(" ","_")].lower().capitalize().replace("_", " ")

            subjects_count[subject] += 1
            if subjects_count[subject] > 1: # suffix for same names
                subject += "_%i" % int(subjects_count[subject])


            quantity = "q" # filedata["quantity"]

            commands = []

            if "uni-directional" in filedata:
                unidir = filedata["uni-directional"]

                commands.append("assert not np.isnan(q)")
                commands.append("assert q < +np.inf")
                commands.append("assert q > -np.inf")

                #print("uni-directional",unidir)
                if str(unidir) == "True": # do not do bool(unidir)
                    #namaaa = filedata["shortname"]
                    #self.notify( (namaaa+ str(unidir)+ "="+(str(bool(unidir)))),title="check")
                    commands.append("assert q >= 0, 'have to pass positive quantity: unidirectional transaction'")

            commands = commands + ["%s.balance_sheet.disengage()" % agent1]
            if True: # agent1 != agent2:
                commands+= ["%s.balance_sheet.disengage()" % agent2]

            for entry in e1.split("\n"):
                if entry != "" and entry != "\n":
                    sign, item, silent = self.entry_to_vals(entry, agent1, "Equity")
                    if sign is not None:
                        commands.append("%s.balance_sheet.change_item('%s', %s, %s, suppress_stock=%s)" % (
                        agent1, item, "BalanceEntry.EQUITY", sign + quantity, silent))
            for entry in a1.split("\n"):
                if entry != "" and entry != "\n":
                    sign, item, silent = self.entry_to_vals(entry, agent1, "Assets")
                    if sign is not None:
                        commands.append("%s.balance_sheet.change_item('%s', %s, %s, suppress_stock=%s)" % (
                        agent1, item, "BalanceEntry.ASSETS", sign + quantity, silent))
            for entry in l1.split("\n"):
                if entry != "" and entry != "\n":
                    sign, item, silent = self.entry_to_vals(entry, agent1, "Liabilities")
                    if sign is not None:
                        commands.append("%s.balance_sheet.change_item('%s', %s, %s, suppress_stock=%s)" % (
                        agent1, item, "BalanceEntry.LIABILITIES", sign + quantity, silent))
            for entry in e2.split("\n"):
                if entry != "" and entry != "\n":
                    sign, item, silent = self.entry_to_vals(entry, agent2, "Equity")
                    if sign is not None:
                        commands.append("%s.balance_sheet.change_item('%s', %s, %s, suppress_stock=%s)" % (
                        agent2, item, "BalanceEntry.EQUITY", sign + quantity, silent))
            for entry in a2.split("\n"):
                if entry != "" and entry != "\n":
                    sign, item, silent = self.entry_to_vals(entry, agent2, "Assets")
                    if sign is not None:
                        commands.append("%s.balance_sheet.change_item('%s', %s, %s, suppress_stock=%s)" % (
                        agent2, item, "BalanceEntry.ASSETS", sign + quantity, silent))
            for entry in l2.split("\n"):
                if entry != "" and entry != "\n":
                    sign, item, silent = self.entry_to_vals(entry, agent2, "Liabilities")
                    if sign is not None:
                        commands.append("%s.balance_sheet.change_item('%s', %s, %s, suppress_stock=%s)" % (
                        agent2, item, "BalanceEntry.LIABILITIES", sign + quantity, silent))

            commands.append("%s.balance_sheet.engage()" % agent1)
            if True: # agent1!=agent2:
                commands.append("%s.balance_sheet.engage()" % agent2)

            add_flow = flow_check
            if add_flow:
                print(subject_str,"flow check",flow_check)

                kind_enum = "(%s,%s)" % (kind.split("->")[0].strip(),kind.split("->")[1].strip())

                commands.append("FlowMatrix().log_flow(%s, %s, %s, %s, subject='%s')" % (kind_enum, quantity, agent1, agent2, subject_str))


            my_income_dict = { # #translates string into ICSEntry (for better efficiency)
                "Revenue": "ICSEntry.REVENUES",
                "Non-Op. Income": "ICSEntry.NOI",
                "Expense": "ICSEntry.EXPENSES",
                "Tax": "ICSEntry.TAXES",
                "Interest": "ICSEntry.INTEREST",
                "Gain": "ICSEntry.GAINS",
                "Nontax.Profit": "ICSEntry.NONTAX_PROFITS",
                "Nontax. Profit": "ICSEntry.NONTAX_PROFITS", # quick and dirty bugfix
                "Nontax. Loss":  "ICSEntry.NONTAX_LOSSES",
                "Loss":  "ICSEntry.LOSSES"
            }

            # income statement?
            if "income1" in filedata:
                if str(filedata["income1"]) != 'None':
                    commands.append("%s.income_statement.new_entry(%s,'%s',%s)" % (agent1,my_income_dict[filedata["income1"]],subject,quantity))

            if "income2" in filedata:
                if str(filedata["income2"]) != 'None':
                    commands.append("%s.income_statement.new_entry(%s,'%s',%s)" % (agent2, my_income_dict[filedata["income2"]], subject, quantity))

            # cash flow statement
            if "cashflow1" in filedata:
                if str(filedata["cashflow1"]) != 'None':
                    commands.append("%s.cash_flow_statement.new_entry(%s,'%s',-%s)" % (agent1,"CashFlowEntry." + filedata["cashflow1"].upper(),subject,quantity))

            if "cashflow2" in filedata:
                if str(filedata["cashflow2"]) != 'None':
                    commands.append("%s.cash_flow_statement.new_entry(%s,'%s',%s)" % (agent2,"CashFlowEntry." + filedata["cashflow2"].upper(),subject,quantity))

            if True: # agent1 != agent2:
                method = "def %s(%s, %s, %s):\n" % (subject,agent1,agent2,quantity)
            #else:
            #    method = "def %s(%s, %s):\n" % (subject, agent1, quantity)

            if "description" in filedata: # add the description in the docstring of the function definition
                method += "    #" + filedata["description"] + "\n"

            for command in commands:
                method += "    " + command + "\n"

            method += "\n\n"
            code += method

        folder = os.path.dirname(self.current_file) # statusBar().currentMessage())
        fname =  folder + "/python_code/transactions.py"

        with open(fname,"w",encoding="utf-8") as file:
            file.write(code)

        if show_notification:
            self.notify(message="Code exported to %s" % (fname),title="Success")


    def gen_tex_ics(self):
        combined_sheets = {}

        """
        {
        agent_name: {
                    "Assets": {
                                asset_name : [entries],
                                ...},

                    "Liabilities and Equity": {
                                name : [entries],
                                ...},

                    }
        }
        """

        combined_income = defaultdict(lambda: {"Gains": [], "Losses": [], "Revenues": [], "Taxes": [], "Expenses": [],
                                               "Nontaxable Losses": [], "Nontaxable Profits": [],
                                               "Non-Operational Income": [],
                                               "Interest Payments": []
                                               })

        """
        {
        agent_name: {
                "Gains":  [entries],
                "Losses":[entries],
                "Expenditures":[entries],
                "Revenues": [entries],
                "Taxes":[entries]
        }
        """

        k = 0
        texstr = ""

        try:
            for filedata in self.entry_data:
                            #   self.parent.agent1.value = filedata["agent1"]
                            # self.parent.agent2.value = filedata["agent2"]

                            # self.parent.flow_check.value = str(bool(filedata["log transaction"]))
                            # self.parent.kind.value = filedata["kind"]
                            # self.parent.subject.value = filedata["subject"]
                            # self.parent.quantity.value = filedata["quantity"]

                            agent1 = filedata["agent1"]
                            agent2 = filedata["agent2"]

                            assets1 = filedata["a1"] + "\n"
                            liabs1 = filedata["l1"] + "\n" + filedata["e1"] + "\n"

                            assets2 = filedata["a2"] + "\n"
                            liabs2 = filedata["l2"] + "\n" + filedata["e2"] + "\n"

                            my_table = pd.DataFrame.from_dict(
                                {"Assets": assets1.split("\n"), "Liabilities and Equity": liabs1.split("\n")},
                                orient='index').T
                            my_table2 = pd.DataFrame.from_dict(
                                {"Assets": assets2.split("\n"), "Liabilities and Equity": liabs2.split("\n")},
                                orient='index').T

                            tex_table1 = my_table.to_latex(index_names=False, index=False)
                            tex_table2 = my_table2.to_latex(index_names=False, index=False)

                            # merge_table = pd.concat(tex_table1,tex_table2)

                            # ============================ modify combined sheet

                            #
                            # AGENT 1
                            #

                            if agent1 not in combined_sheets:
                                combined_sheets[agent1] = {}

                            if "Assets" not in combined_sheets[agent1]:
                                combined_sheets[agent1]["Assets"] = {}
                            if "Liabilities and Equity" not in combined_sheets[agent1]:
                                combined_sheets[agent1]["Liabilities and Equity"] = {}

                            for change in assets1.split("\n"):
                                try:
                                    sign = change[0]  # first letter is sign + or -

                                    name = change[1:].strip()
                                    q = sympy.latex(sympy.simplify(sign + filedata["quantity"]), mode="inline")
                                    subject = "   (" + filedata["subject"].replace("_", " ") + ")"

                                    #print("name", name)
                                    #print("combined_sheets[agent1]", combined_sheets[agent1])
                                    if name not in combined_sheets[agent1]["Assets"]:
                                        combined_sheets[agent1]["Assets"][name] = ""

                                    combined_sheets[agent1]["Assets"][name] += q + subject + "\n"
                                except:
                                    pass
                            for change in liabs1.split("\n"):
                                try:
                                    sign = change[0]  # first letter is sign + or -

                                    name = change[1:].strip()
                                    try:
                                        q = sympy.latex(sympy.simplify(sign + filedata["quantity"]), mode="inline")
                                    except Exception as e:
                                        self.notify(
                                            "Cannot handle the symbolic expression %s" % sign + filedata[
                                                "quantity"],title="Error")

                                    subject = "   (" + filedata["subject"].replace("_", " ") + ")"

                                    if name not in combined_sheets[agent1]["Liabilities and Equity"]:
                                        combined_sheets[agent1]["Liabilities and Equity"][name] = ""

                                    combined_sheets[agent1]["Liabilities and Equity"][name] += q + subject + "\n"
                                except:
                                    pass

                            if str(filedata["income1"]) != 'None':
                                mydict = {"Gain": "Gains",
                                          "Loss": "Losses",
                                          "Expense": "Expenses",
                                          "Revenue": "Revenues",
                                          "Tax": "Taxes",
                                          "Nontax. Profit": "Nontaxable Profits",
                                          "Nontax. Loss": "Nontaxable Losses",
                                          "Non-Op. Income": "Non-Operational Income",
                                          "Interest": "Interest Payments"}

                                try:
                                    q = sympy.latex(sympy.simplify(sign + filedata["quantity"]), mode="inline")
                                    subject = "   (" + filedata["subject"].replace("_", " ") + ")"
                                    combined_income[agent1][mydict[filedata["income1"]]].append((str(q), subject))

                                except Exception as e:
                                    self.notify(
                                        "Cannot handle the symbolic expression %s" % sign + filedata["quantity"],title="Error")


                            #
                            # AGENT 2
                            #

                            if agent2 not in combined_sheets:
                                combined_sheets[agent2] = {}

                            if "Assets" not in combined_sheets[agent2]:
                                combined_sheets[agent2]["Assets"] = {}
                            if "Liabilities and Equity" not in combined_sheets[agent2]:
                                combined_sheets[agent2]["Liabilities and Equity"] = {}

                            for change in assets2.split("\n"):

                                try:
                                    sign = change[0]  # first letter is sign + or -

                                    name = change[1:].strip()
                                    try:
                                        q = sympy.latex(sympy.simplify(sign + filedata["quantity"]), mode="inline")
                                    except Exception as e:
                                        self.notify(
                                            "Cannot handle the symbolic expression %s" % sign + filedata[
                                                "quantity"],title="Error")

                                    subject = "   (" + filedata["subject"].replace("_", " ") + ")"

                                    if name not in combined_sheets[agent2]["Assets"]:
                                        combined_sheets[agent2]["Assets"][name] = ""

                                    combined_sheets[agent2]["Assets"][name] += q + subject + "\n"
                                except:
                                    pass

                            for change in liabs2.split("\n"):
                                try:
                                    sign = change[0]  # first letter is sign + or -

                                    name = change[1:].strip()
                                    try:
                                        q = sympy.latex(sympy.simplify(sign + filedata["quantity"]), mode="inline")
                                    except Exception as e:
                                        self.notify(
                                            "Cannot handle the symbolic expression %s" % sign + filedata[
                                                "quantity"],title="Error")

                                    subject = "   (" + filedata["subject"].replace("_", " ") + ")"

                                    if name not in combined_sheets[agent2]["Liabilities and Equity"]:
                                        combined_sheets[agent2]["Liabilities and Equity"][name] = ""

                                    combined_sheets[agent2]["Liabilities and Equity"][name] += q + subject + "\n"
                                except:
                                    pass

                            if str(filedata["income2"]) != 'None':
                                mydict = {"Gain": "Gains",
                                          "Loss": "Losses",
                                          "Expense": "Expenses",
                                          "Revenue": "Revenues",
                                          "Tax": "Taxes",
                                          "Nontax. Profit": "Nontaxable Profits",
                                          "Nontax. Loss": "Nontaxable Losses",
                                          "Non-Op. Income": "Non-Operational Income",
                                          "Interest": "Interest Payments"}
                                q = sympy.latex(sympy.simplify(sign + filedata["quantity"]), mode="inline")
                                subject = "   (" + filedata["subject"].replace("_", " ") + ")"
                                combined_income[agent2][mydict[filedata["income2"]]].append((str(q), subject))

                                # ============================

                            transfer_str = ""

                            if bool(filedata["log transaction"]):
                                transfer_str = "\nFlow:~" + filedata["kind"].strip().replace("->",
                                                                                             "$\\rightarrow$") + "&~\\\\" + "\n"
                                transfer_str += "Subject:~" + filedata["subject"].strip().title() + "&~\\\\" + "\n"
                                # transfer_str += "Quantity:~" + filedata["quantity"].strip() + "&~\\\\"+ "\n"

                            table_str = """\\begin{tabular}{ll}

                %s & %s \\\\
                ~ & ~ \\\\
                """ % (filedata["agent1"], filedata["agent2"])
                            table_str += tex_table1 + "&" + tex_table2 + "\\\\\\\\" + transfer_str

                            table_str += "\n\n\\end{tabular}"
                            texstr += """\\begin{table}[H]\n"""
                            texstr += table_str
                            texstr += """\caption{%s}\n\end{table}""" % (filedata["subject"] + "(%s)"%filedata["shortname"])

            texstr = texstr.replace("_", " ")
            texstr = texstr.replace("None", "")

            # ============ add combined sheets ======================
            print(combined_sheets)
            # convert the combined sheets to tex
            texstr_combined = ""
            for agent, data in combined_sheets.items():
                agent_titled = agent.replace("_", " ").title()

                assets = data["Assets"]
                liabs = data["Liabilities and Equity"]

                mys = """
            \\begin{table}[H]
            \\centering
            """
                mys += """
            \\begin{tabular}{|l|l|}
            \hline
            ~&~\\\\
            \\textbf{Assets} & \\textbf{Liabilities and Equity}\\\\
            ~&~\\\\

                        """

                mys += """
            \\begin{tabular}{ll}
                        """

                for item, entry in assets.items():

                    mys += item + "&~ \\\\\hline~&~\\\\\n"

                    for sub_entry in entry.split("\n"):
                        try:
                            lt_subentry = sub_entry
                            mys += "~&" + lt_subentry + "\\\\" + "\n"
                        except:
                            pass

                mys += """
            \end{tabular} & \\begin{tabular}{ll}""" + "\n"

                for item, entry in liabs.items():
                    if item != "Equity":
                        mys += item + "&~ \\\\\hline~&~\\\\\n"

                        for sub_entry in entry.split("\n"):
                            try:
                                lt_subentry = sub_entry
                                mys += "~&" + lt_subentry + "\\\\" + "\n"
                            except:
                                pass

                try:
                    item = "Equity"
                    entry = liabs["Equity"]
                    mys += item + "&~ \\\\\hline~&~\\\\\n"

                    for sub_entry in entry.split("\n"):
                        try:
                            lt_subentry = sub_entry
                            mys += "~&" + lt_subentry + "\\\\" + "\n"
                        except:
                            pass
                except:
                    pass

                mys += """
            \\end{tabular}
            \\\\~&~
            \\\\\hline"""
                mys += """
            \\end{tabular}"""
                mys += """
            \\caption{Balance Sheet of %s}""" % agent_titled + """
            \\end{table}
            """
                texstr_combined += mys

                # =========== add income

                if agent in combined_income:
                    income_data = combined_income[agent]
                    income_str = """
            \\begin{table}[H]\n\centering\n
            \\begin{tabular}{|ll|}\n\hline"""

                    for k in "Revenues", "Gains", "Expenses", "Losses", \
                             "Interest Payments", "Non-Operational Income", "Taxes", "Nontaxable Profits", "Nontaxable Losses":
                        v = income_data[k]

                        income_str += "~&~\\\\"
                        income_str += "\t" + k + "&~\\\\\n"

                        for sub_value in v:
                            income_str += "\t" + "~&" + sub_value[0] + sub_value[1] + "\\\\\n"
                        if len(v) == 0:
                            income_str += "\t" + "~&" + ".-" + "\\\\\n"

                        if k != "Nontaxable Losses":
                            income_str += "~&~\\\\\hline\n"

                    income_str += """\n
            ~&~\\\\\hline\n\\end{tabular}"""
                    income_str += """\n
            \\caption{Income Statement of %s}""" % agent_titled + """
            \\end{table}"""

                    texstr_combined += income_str

            # =======================================================
            pyperclip.copy(texstr_combined)
            self.notify(message="LaTeX code copied to clipboard. Have fun!", title="Have fun")

            if False: # depreciated

                path = os.path.dirname(os.path.abspath(__file__))
                with open(os.path.join(path , "files/income_statments.tex"), "w") as file:
                    file.write("""
    \documentclass{article}
    \\usepackage{tabularx}
    \\usepackage{amsmath}
    \\usepackage{float}

    \\begin{document}

    """)
                    file.write(texstr_combined)
                    file.write("""
    \\end{document}
    """)

                import subprocess
                try:

                    path = os.path.dirname(os.path.abspath(__file__))
                    subprocess.run("pdflatex %s" % (os.path.join(path, "files/income_statments.tex"))).check_returncode()

                    shutil.move(path + "income_statments.tex", path + "files\\income_statments.tex")
                    shutil.move(path + "income_statments.log", path + "files\\income_statments.log")
                    shutil.move(path + "income_statments.aux", path + "files\\\mincome_statments.aux")
                    shutil.move(path + "income_statments.pdf", path + "files\\income_statments.pdf")
                    self.notify(message="TeX File created in %s" % path + "\\files" ,title="Success")

                except Exception as e:
                    self.notify(message=str(e.__context__) + "\n" + str(e), title=e.__class__.__name__)


        except Exception as e:
            self.notify(message=str(e.__context__) + "\n" + str(e), title=e.__class__.__name__)

    def add_helper(self):
        new_name = self.HelperNameEdit.text()
        # TODO add security mechanism to avoid overwriting an agent
        if new_name == "":
            self.notify("Please enter a valid name", title="IBM Error")
        elif not new_name[0].isupper():
            self.notify("Please enter a valid name with\nuppercase first letter or camelcase, e.g. 'MyAgent'", title="IBM Error")
        else:
            self.drawcanvas.add_agent(new_name)

    def remove_helper(self):
        self.drawcanvas.remove_agent()

    def add_new(self):

        # TODO assert that quantity is not yet in any other transaction


        new_entry = {}

        new_entry["a1"] = self.AssetListLeft.toPlainText()
        new_entry["a2"] = self.AssetListRight.toPlainText()
        new_entry["l1"] = self.LiabilityListLeft.toPlainText()
        new_entry["l2"] = self.LiabilityListRight.toPlainText()
        new_entry["e1"] = self.EquityListLeft.toPlainText()
        new_entry["e2"] = self.EquityListRight.toPlainText()

        # new_entry["a1"] = self.AssetListLeft.toPlainText()
        # new_entry["l1"] = self.LiabilityListLeft.toPlainText()
        # new_entry["a2"] = self.LiabilityListRight.toPlainText()
        # new_entry["l2"] = self.AssetListRight.toPlainText()
        # new_entry["e1"] = self.EquityListLeft.toPlainText()
        # new_entry["e2"] = self.EquityListRight.toPlainText()

        new_entry["agent1"] = self.agent1Edit.text().capitalize()
        new_entry["agent2"] = self.agent2Edit.text().capitalize()

        self.agent1Edit.setText(self.agent1Edit.text().capitalize())
        self.agent2Edit.setText(self.agent2Edit.text().capitalize())

        if not self.drawcanvas.check_exist(new_entry["agent1"]):
            qm = QMessageBox
            ret = qm.question(self,'', "The agent %s does not exist.\nDo you wish to continue and automatically create a new agent?"%new_entry["agent1"], qm.Yes | qm.No)
            if ret == qm.No:
                return
        if not self.drawcanvas.check_exist(new_entry["agent2"]):
            qm = QMessageBox
            ret = qm.question(self,'', "The agent %s does not exist.\nDo you wish to continue and automatically create a new agent?"%new_entry["agent2"], qm.Yes | qm.No)
            if ret == qm.No:
                return

        box1 = self.drawcanvas.add_agent(new_entry["agent1"])
        box2 = self.drawcanvas.add_agent(new_entry["agent2"])

        self.drawcanvas.add_connection(box1, box2, name= str(self.editShortname.text()))

        new_entry["uni-directional"] = \
            str(self.comboUnidir.currentText())

        new_entry["log transaction"] = \
            bool(self.registerFlowBox.currentText())

        new_entry["cashflow1"] = \
            str(self.comboCashLeft.currentText())
        new_entry["cashflow2"] = \
            str(self.comboCashRight.currentText())

        new_entry["kind"] = \
            str(self.editType.currentText())

        new_entry["income1"] = \
            str(self.comboIncomeLeft.currentText())
        new_entry["income2"] = \
            str(self.comboIncomeRight.currentText())

        new_entry["quantity"] = \
            str(self.editQuantity.text())

        new_entry["subject"] = \
            str(self.editSubject.text())

        new_entry["shortname"] = \
            str(self.editShortname.text())

        self.entry_data.append(new_entry)
        self.update_table()

        # TODO select the new entry in the list view
        if self.selection_idx is not None:
            for i in range(self.transactionView.columnCount()):
                self.transactionView.item(self.selection_idx, i).setBackground(QtGui.QColor(233, 234, 227))

            self.selection_idx = self.transactionView.rowCount()-1
            for i in range(self.transactionView.columnCount()):
                self.transactionView.item(self.selection_idx, i).setBackground(QtGui.QColor(159, 159, 159))

    def goto_next(self):
        pass


    def udpate_display(self):
        try:

            filename = self.filename

            with open(filename, 'r') as stream:
                filedata = yaml.safe_load(stream)
                print(filedata)

                self.agent1Label.text = filedata["agent1"]
                self.agent2Label.text = filedata["agent2"]

                # self.a1.value = filedata["a1"]  # + "\n"
                # self.e1.value = filedata["e1"]  # + "\n"
                # self.l1.value = filedata["l1"]  # + "\n"
                # self.a2.value = filedata["a2"]  # + "\n"
                # self.e2.value = filedata["e2"]  # + "\n"
                # self.l2.value = filedata["l2"]  # + "\n"

                # if "shortname" in filedata:
                #    self.parent.shortname.value = filedata["shortname"]

                # if "uni-directional" in filedata:
                #    self.parent.direction_check.value = bool(str(filedata["uni-directional"]))
                # else:
                #    self.parent.direction_check.value = False

                # if "description" in filedata:
                #    self.parent.description.value = filedata["description"]

                # self.parent.flow_check.value = filedata["log transaction"]
                # self.parent.kind.value = filedata["kind"]
                # self.parent.subject.value = filedata["subject"]
                # self.parent.quantity.value = filedata["quantity"]

                try:
                    # ["None","Revenue","Expense","Gain","Loss","Tax"]

                    my_dict = {
                        "None": 0,
                        "Revenue": 1,
                        "Expense": 2,
                        "Gain": 3,
                        "Loss": 4,
                        "Interest": 5,
                        "Non-Op. Income": 6,
                        "Tax": 7,
                        "Nontax. Profit": 8,
                        "Nontax. Loss": 9
                    }

                    # self.parent.income1.value = [my_dict[filedata["income1"]]]
                    # self.parent.income2.value = [my_dict[filedata["income2"]]]

                    # self.parent.cashflow1.value = [filedata["cashflow1"]]
                    # self.parent.cashflow2.value = [filedata["cashflow2"]]

                except:
                    pass

                #self.parent.display()

        except Exception as e:
            print(str(e)) # self.notify(str(e),"Exception") < this should not throw an exception


if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)

    pixmap = QPixmap("./splash.png")
    splash = QSplashScreen(pixmap)
    splash.show()

    import sys
    import os
    import yaml
    import shutil
    import time
    from pandasmodel import PandasModel

    import resources
    from mamba_interpreter2 import convert_code
    from mainloop_editor import MainLoopEditor

    import sympy

    # packages for graph
    import re as regex
    import matplotlib.pyplot as plt
    import pydot
    #import mpimg
    import networkx as nx
    import numpy as np
    from graphviz import Source

    # packages for matrix
    from sympy.parsing.sympy_parser import parse_expr
    from sympy import *
    from sympy import simplify, init_printing, printing
    import pandas as pd


    import pyperclip
    import pdflatex
    from collections import defaultdict

    import subprocess

    from draw_widget import MyDrawWidget, Box
    from yaml_editor import SettingsEditor

    from output_display import OutputDisplay

    # window = ProjectDesigner()
    window = TransactionDesigner()
    splash.finish(window)
    app.exec_()
