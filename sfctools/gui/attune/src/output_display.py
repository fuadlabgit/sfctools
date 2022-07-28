from PyQt5 import QtWidgets, uic,QtGui
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QFileDialog,QMessageBox,QTableWidgetItem,QAbstractItemView,QListWidgetItem,QShortcut
import sys
import os
import yaml
import shutil
import pyperclip

# from pandasmodel import PandasModel
from PyQt5.QtGui import QDesktopServices
import pickle as pkl
import re
import matplotlib.pyplot as plt
from PyQt5.QtCore import Qt
from PyQt5 import QtCore
from PyQt5.QtGui import QKeySequence

from .mamba_interpreter2 import convert_code

from PyQt5.QtGui import QFont, QFontDatabase, QColor #, QSyntaxHighlighter, QTextCharFormat
from PyQt5.QtGui import QKeySequence,QFontMetrics

import numpy as np
from sfctools.misc.timeseries import cross_correlate



class OutputDisplay(QtWidgets.QDialog):

    def notify(self,message,title=" "):
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.open()


    def __init__(self,parent,path=""):

        super(OutputDisplay, self).__init__(parent) # Call the inherited classes __init__ method
        ui_path = os.path.dirname(os.path.abspath(__file__))
        uic.loadUi(os.path.join(ui_path,'output_display.ui'), self) # Load the .ui file

        self.data_idx = 0
        self.data = None

        self.lock_idx = None

        self.data_range_max = None
        self.data_range_min = None

        self.Btn_copy.pressed.connect(self.copy_data)
        self.Btn_copy_2.pressed.connect(self.copy_data2)

        self.path = path
        self.path_label.setText(self.path)
        self.data_name_label.setText(" ")
        self.data_name_label2.setText(" ")

        self.Btn_update.pressed.connect(self.load_file)
        self.Btn_prev.pressed.connect(self.decrease_idx)
        self.Btn_next.pressed.connect(self.increase_idx)

        self.lock_slide.valueChanged.connect(self.toggle_lock)

        self.range_from.textChanged.connect(self.update_range)
        self.range_to.textChanged.connect(self.update_range)

        self.idx_from_edit.textChanged.connect(self.update_idx)
        self.idx_to_edit.textChanged.connect(self.update_idx)

        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.selectRow(self.data_idx)
        self.table.cellClicked.connect(self.update_idx)

        self.plot_data = {"data":None, "lock_data":None,"mydat":None} # store plot data so it does not need to be computed every iteration
        self.plot_rep = 15 # every N frames, the plots are updated
        self.plot_counter  = self.plot_rep # counts down

        # self.load_file()

        self.show()

    def copy_data(self):
        # copy current data to clipboard
        if self.data is not None:

            try:

                v = self.data[list(self.data.keys())[self.data_idx]]
                if isinstance(v,dict):
                    v = list(v.values())

                title = list(self.data.keys())[self.data_idx]

                pyperclip.copy(title + "\n" + "\n".join([str(vi) for vi in v]))
            except Exception as e:
                self.notify(str(e),title="Error")

    def copy_data2(self):
        # copy current data to clipboard
        if self.data is not None:

            try:

                if self.lock_idx is not None: # cross-correlation
                    lock_data = self.data_from_idx(self.lock_idx)
                    data = self.data_from_idx(self.data_idx)
                    ccf = cross_correlate(np.array(data[1]),np.array(lock_data[1]),lags=15)
                    mydat = {0: np.array(ccf.index), 1: np.array(ccf["Cross-Correlation"])}

                    v = mydat
                    title = "Lag\t" +list(self.data.keys())[self.data_idx] + " - " + list(self.data.keys())[self.lock_idx]
                    lag_min = -25
                    lag_max = 25

                else: # auto-correlation
                    data = self.data_from_idx(self.data_idx)
                    acf = cross_correlate(np.array(data[1]),np.array(data[1]),lags=15)
                    mydat = {0: np.array(acf.index), 1: np.array(acf["Cross-Correlation"])}

                    v = mydat
                    title = "Lag\t" + list(self.data.keys())[self.data_idx] + " - " + list(self.data.keys())[self.data_idx]
                    lag_min = 0
                    lag_max = 25

                s = ""
                for i in range(2*len(data[1])-1):
                    if int(v[0][i]) >= lag_min and int(v[0][i]) <= lag_max:
                        s += str(v[0][i]) + "\t" + str(v[1][i]) + "\n"
                        print("COPY", v[0][i])

                pyperclip.copy(title + "\n" + s)
            except Exception as e:
                self.notify(str(e),title="Error")

    def update_idx(self):
        self.plot_counter = 0
        self.update()

    def update_range(self):

        try:
            if self.range_from.text() != "":
                self.data_range_min = float(self.range_from.text())
            else:
                self.data_range_min = None

            if self.range_to.text() != "":
                self.data_range_max = float(self.range_to.text())
            else:
                self.data_range_max = None
            # print("update range", self.data_range_min, self.data_range_max)
        except:
            pass

        print("UPDATE RANGE")
        self.plot_counter = 0
        self.update()

    def toggle_lock(self):

        if self.lock_slide.value() == 1:
            self.lock_idx = self.data_idx

            try:
                self.data_name_label2.setText(str(list(self.data.keys())[self.lock_idx]))
            except:
                self.data_name_label2.setText(" ")
        else:
            self.lock_idx = None
            self.data_name_label2.setText(" ")

        self.plot_counter = 0
        self.update()

    def update_idx(self):

        if self.data is not None:

            try:
                idx = int(self.table.currentRow())
                self.data_idx = idx
                self.data_name_label.setText(str(list(self.data.keys())[self.data_idx])) # "[" + str(self.data_idx)+ "] " +
                #print(self.data[list(self.data.keys())[self.data_idx]])
                # self.update()
            except Exception as e:
                self.notify("Error while updating data index\n" + str(e))


            self.plot_counter = 0
            self.update()

    def increase_idx(self):

        try:
            if self.data is None:
                return
            max_idx = len(self.data.keys())-1
            if self.data_idx < max_idx:
                self.data_idx += 1

            self.table.selectRow(self.data_idx)
            self.data_name_label.setText(str(list(self.data.keys())[self.data_idx])) # "[" + str(self.data_idx)+ "] " +

        except Exception as e:
            self.notify("Error: %s" % str(e))

        self.plot_counter = 0
        self.update()

    def decrease_idx(self):
        try:
            if self.data is None:
                return

            min_idx = 0
            if self.data_idx > min_idx:
                self.data_idx -= 1

            self.table.selectRow(self.data_idx)
            self.data_name_label.setText(str(list(self.data.keys())[self.data_idx])) # "[" + str(self.data_idx)+ "] " +


        except Exception as e:
            self.notify("Error: %s" % str(e))

        self.plot_counter = 0
        self.update()

    def load_file(self):
        fname = self.path + self.fileEdit.text()

        try:
            # load the data file

            file = open(fname,'rb')
            data = pkl.load(file)
            file.close()

            self.data = data
            # self.data_idx = 0
            # self.decrease_idx()
            # self.update()
            # self.plot_counter = 1

        except Exception as e:
            self.notify("Could not load file %s \n %s" % (fname, str(e)))


        try:
            if self.data is not None:
                self.table.clear()
                self.table.setRowCount(len(self.data.keys()))
                # insert data rows into table
                i = 0
                for k,v in self.data.items():
                    self.table.setItem(i, 0, QTableWidgetItem(str(i)))
                    self.table.setItem(i, 1, QTableWidgetItem(str(k)))

                    idx_from = int(self.idx_from_edit.text())
                    idx_to = int(self.idx_to_edit.text())

                    if isinstance(v,dict):
                        #print("IS DICT -> converting")
                        v = list(v.values())

                    if idx_to - idx_from > 1 or (idx_to == -1 and len(v) > 1 and idx_from < len(v)-1):
                        v2 = v[idx_from:idx_to]
                    else:
                        v2 = v

                    v2 = np.array(v2,dtype=np.float32)

                    #print(v2)
                    #print("--")

                    try:
                        n_vals = "%i" % (len(v2))
                        min_val = "%.3f" % (np.min(v2))
                        max_val = "%.3f" % (np.max(v2))
                        mean_val = "%.3f" % (np.mean(v2))
                        std_val = "%.3f" % (np.std(v2))
                    except:
                        n_vals = "ERR"
                        min_val = "ERR"
                        max_val = "ERR"
                        mean_val = "ERR"
                        std_val = "ERR"

                    try:
                        self.table.setItem(i, 2, QTableWidgetItem(n_vals))
                        self.table.setItem(i, 3, QTableWidgetItem(min_val))
                        self.table.setItem(i, 4, QTableWidgetItem(max_val))
                        self.table.setItem(i, 5, QTableWidgetItem(mean_val))
                        self.table.setItem(i, 6, QTableWidgetItem(std_val))
                    except:
                        pass

                    i += 1

                self.table.setHorizontalHeaderLabels(["Index","Variable","Values", "Min", "Max", "Mean", "Std"])
        except Exception as e:
            self.notify("Could not fill table: " + str(e))

        self.plot_counter = 0
        self.update()


    def data_from_idx(self,idx):
        data = [None,None]
        N = 1000
        data[0] = np.linspace(0,100,N)
        data[1] = np.full(N,42.0)+np.sin(data[0]) # *.03*np.random.rand(N) # 30*np.sin(data[0]) #

        try:
            if self.data is not None:
                current_key = list(self.data.keys())[idx]
                data[1] = self.data[current_key]
                data[0] = np.arange(len(data[1]),dtype=float)

                if isinstance(data[1],dict):
                    # print("IS DICT -> converting")
                    data[1] = list(data[1].values())

                try:
                    idx_from = int(self.idx_from_edit.text())
                    idx_to = int(self.idx_to_edit.text())

                    if idx_to - idx_from > 1 or (idx_to == -1 and len(data[0]) > 1 and idx_from < len(data[0])-1):
                        data[0] = data[0][idx_from:idx_to]
                        data[1] = data[1][idx_from:idx_to]
                except:
                    pass

        except Exception as e:

            self.notify(str(e))
        return data


    def plot_line(self,data,color=Qt.black,offset_ylabel=0.0,offset_x=0,offset_y=0,ignore_data_range=False):


        offset_x = int(offset_x)
        offset_y = int(offset_y)
        offset_ylabel= int(offset_ylabel)

        qp = QtGui.QPainter(self)
        pen = QtGui.QPen(Qt.black ,1, Qt.SolidLine)
        brush = QtGui.QBrush(Qt.white)
        qp.setBrush(brush)
        qp.setPen(pen)

        # CANVAS

        H = 550
        offset = (50,H)

        # DATA

        x = data[0]

        if len(x) < 2:
            print("X data is too short") # self.notify("X data is too short")
            return

        x_max_label = "%i"% int(np.nanmax(x))
        x_min_label = "%i"% int(np.nanmin(x))
        x_mid_label = "%i"% int(0.5*(np.nanmax(x)+ np.nanmin(x)))


        x = x-np.nanmin(x)
        if np.nanmax(x) != 0.0:
            x /=np.nanmax(x)
        x*= 200

        scale = 3
        dx = 20

        x_max = int(np.nanmax(x))
        x_min = int(np.nanmin(x))
        x_mid = int(0.5*(np.nanmin(x) + np.nanmax(x)))

        y = data[1]

        y_max_label = "%.2f"% np.nanmax(y)
        y_min_label = "%.2f"% np.nanmin(y)
        y_mid_label = "%.2f"% (0.5*(np.nanmax(y)+ np.nanmin(y)))

        if not ignore_data_range:

            if self.data_range_min is not None:
                min_yrange = self.data_range_min
            else:
                min_yrange = np.nanmin(y)

            if self.data_range_max is not None:
                max_yrange = self.data_range_max
            else:
                max_yrange = np.nanmax(y)
        else:
            min_yrange= np.nanmin(y)
            max_yrange = np.nanmax(y)


        y = np.array(y)-min_yrange

        norm = (max_yrange-min_yrange)
        if norm != 0.0:
            y /= norm


        y*= 200
        y +=  int(offset_y)

        if np.nanmin(y) == np.nanmax(y):
            y += 100 # shift to center
            y_max_label = ""
            y_min_label = ""

        # DRAW AXIS
        y_max = int(np.nanmax(y))
        y_min = int(np.nanmin(y))
        y_mid = int(0.5*(np.nanmin(y) + np.nanmax(y)))

        if y_max == y_min:
            y_max = y_mid + 100

        points_yticks = [(x_max,y_min), (x_max,y_mid), (x_max,y_max)]
        points_xticks = [(x_min,0), (x_mid,0), (x_max,0)]

        pen = QtGui.QPen(Qt.gray ,1, Qt.SolidLine)
        qp.setPen(pen)

        for p in points_yticks:
            u = p[0]*scale
            v = p[1]
            qp.drawLine(QtCore.QPoint(int(offset[0]+u+dx),int(H-v)),QtCore.QPoint(int(offset[0]+u+10+dx),int(H-v)))

        for p in points_xticks:
            u = int(p[0]*scale +dx )
            v = p[1]- 10
            qp.drawLine(QtCore.QPoint(int(offset[0]+u),int(H-v-10)),QtCore.QPoint(int(offset[0]+u),int(H-v)))

        r1 = QtCore.QPoint(int(offset[0]+0+dx),int(H-offset_y))
        r2 = QtCore.QPoint(int(offset[0]+x_max*scale +dx) ,int(H-offset_y))
        r3 = QtCore.QPoint(int(offset[0]+x_max*scale +dx),int(H-(200)-offset_y))
        r4 = QtCore.QPoint(int(offset[0]+0+dx),int(H-(200)-offset_y))
        qp.drawLine(r1,r2)
        qp.drawLine(r2,r3)
        qp.drawLine(r3,r4)
        qp.drawLine(r4,r1)

        lx1 = QtCore.QPoint(int(offset[0]+dx+points_xticks[0][0]*scale),int(H-points_xticks[0][1]+25)-offset_y)
        lx2 = QtCore.QPoint(int(offset[0]+dx+points_xticks[1][0]*scale),int(H-points_xticks[1][1]+25)-offset_y)
        lx3 = QtCore.QPoint(int(offset[0]+dx+points_xticks[2][0]*scale),int(H-points_xticks[2][1]+25)-offset_y)

        ly1 = QtCore.QPoint(int(offset[0]+dx+points_yticks[0][0]*scale)+25+offset_ylabel,int(H-points_yticks[0][1])+5)
        ly2 = QtCore.QPoint(int(offset[0]+dx+points_yticks[1][0]*scale)+25+offset_ylabel,int(H-points_yticks[1][1])+5)
        ly3 = QtCore.QPoint(int(offset[0]+dx+points_yticks[2][0]*scale)+25+offset_ylabel,int(H-points_yticks[2][1])+5)

        qp.drawText(lx1,x_min_label)
        qp.drawText(lx2,x_mid_label)
        qp.drawText(lx3,x_max_label)

        pen = QtGui.QPen(color ,1, Qt.SolidLine)
        qp.setPen(pen)

        qp.drawText(ly1,y_min_label)
        qp.drawText(ly2,y_mid_label)
        qp.drawText(ly3,y_max_label)

        # DRAW DATA

        # pen = QtGui.QPen(color ,1.0, Qt.SolidLine)
        # qp.setPen(pen)

        qp.drawPoint(QtCore.QPoint(int(offset[0]+x[0]),int(H-y[0])))

        for i in range(1,len(x)):

            # qp.drawPoint(QtCore.QPoint(offset[0]+xi,(H-yi)))
            cond1 = not (np.isnan(x[i-1]) or np.isnan(x[i]) or np.isnan(y[i-1]) or np.isnan(y[i]))

            x1_transformed = int(dx + offset[0]+scale*x[i-1])
            y1_transformed = int(H-y[i-1])
            x2_transformed = int(dx + offset[0]+scale*x[i])
            y2_transformed = int(H-y[i])

            cond2 = (offset_y <= y[i-1] <= 200 + offset_y ) and (offset_y <= y[i] <= 200+offset_y)

            if cond1 and cond2:

                pstart = QtCore.QPoint(x1_transformed,y1_transformed)
                pend = QtCore.QPoint(x2_transformed,y2_transformed)

                qp.drawLine(pstart, pend)


    def paintEvent(self,event):

        update_data = False  # only update every N time steps
        if self.plot_counter <= 0: # or len(self.plot_data) == 0:
            self.plot_counter = self.plot_rep
            update_data = True

        self.plot_counter -= 1

        if update_data:
            data = self.data_from_idx(self.data_idx)
            self.plot_data["data"] = data
        else:
            data = self.plot_data["data"] # read from memory instead of computing again


        try:
            self.plot_line(data)

        except Exception as e:
            print("Error:", str(e))
            #self.notify(str(e))

        # OVERLAY LINE IN RED
        if self.lock_idx is not None:
            if update_data:
                lock_data = self.data_from_idx(self.lock_idx)
                self.plot_data["lock_data"] = lock_data
            else:
                lock_data = self.plot_data["lock_data"]

            try:
                self.plot_line(lock_data,color=Qt.red,offset_ylabel=50)
            except Exception as e :
                print("error",str(e))
                #self.notify(str(e))


        # CROSS-CORRELATION
        try:
            if self.lock_idx is not None: # plot cross-correlation
                if update_data:
                    ccf = cross_correlate(np.array(data[1]),np.array(lock_data[1]),lags=15)
                    mydat = {0: ccf.index, 1: ccf["Cross-Correlation"]}
                    self.plot_data["mydat"] = mydat
                else:
                    mydat = self.plot_data["mydat"]

                self.plot_line(mydat,color=Qt.blue,offset_y = -300,ignore_data_range=True)

            else: # plot auto-correlation
                if update_data:
                    acf = cross_correlate(np.array(data[1]),np.array(data[1]),lags=15)
                    mydat = {0: acf.index, 1: acf["Cross-Correlation"]}
                    self.plot_data["mydat"] = mydat
                else:
                    mydat = self.plot_data["mydat"]
                self.plot_line(mydat,color=Qt.blue,offset_y = -300,ignore_data_range=True)



        except Exception as e:
            print("Error:",str(e))
            # self.notify(str(e))

        # print("COUNT", self.plot_counter)



if __name__ == "__main__":
    """
    """

    app = QtWidgets.QApplication(sys.argv)
    # window = ProjectDesigner()
    window = OutputDisplay(None)
    app.exec_()
