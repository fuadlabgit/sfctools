
import sys
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QPainter
from PyQt5 import QtGui
from PyQt5.QtCore import Qt

import numpy as np
# from transaction_editor import TransactionEditor
# from agent_editor import AgentEditor

from .agent_editor import CodeEditor


class Box:

    def __init__(self,x,y, name,ishelper=False,parent=None,parent_widget=None):

        self.x = x
        self.y = y

        self.x0 = x
        self.y0 = y

        self.name = name
        self.ishelper = ishelper
        self.parent = parent
        self.n_connections = 0

        self.parent_widget = parent_widget


    def edit_agent(self):
        if not self.ishelper:
            print("EDIT AGENT CODE", self.name)

            start = ""
            if self.name in self.parent_widget.code_data:
                start = self.parent_widget.code_data[self.name]

            if self.name not in CodeEditor.instances:
                CodeEditor(self.parent_widget,self,start)

        else:
            print("CANNOT EDIT HELPER")

    def overlaps(self,boxes):
        if self.ishelper:
            e = 8
        else:
            return False

        for box in boxes:

            if self.x - box.x < e:
                return True
            if self.y - box.y < e:
                return True

        return False

    def adjust_position(self,boxes):
        k = 0
        while self.overlaps(boxes) and k < 100:

            self.x = self.x0 + np.random.uniform(-45,45)
            self.y = self.y0 + np.random.uniform(-45,45)

            try:
                self.x = np.clip(self.x ,1,self.parent_widget.W - 45) # 799)
                self.y = np.clip(self.y ,1,self.parent_widget.H -45) # 699)
                # TODO fix parent_widget is None sometimes
            except:
                pass

            k+= 1


class Connector:
    def __init__(self,a,b,name="Connector"):
        self.a = a
        self.b = b

        #self.a.n_connections += 1
        #if self.a != self.b:
        #    self.b.n_connections += 1
        # ^moved to add_connection

        dx = self.b.x +25 - self.a.x #+ 25
        dy = self.b.y +25 - self.a.y #+ 25

        u = np.random.uniform(-1,1)
        v = np.random.uniform(-1,1)

        if a != b:

            self.c = Box(self.a.x + 0.5*dx + u, self.a.y + 0.5*dy + v,name,ishelper=True,parent=self)
            # self.d = Box(self.a.x + 0.75*dx, self.a.y + 0.75*dy,None,ishelper=True,parent=self)
        else:
            self.c = Box(self.a.x + 5*u, self.a.y + 5*u ,name,ishelper=True,parent=self)


class MyDrawWidget(QtWidgets.QWidget):

    def __init__(self,parent):

        super().__init__(parent)
        self.W = 920 # 850
        self.H = 750
        self.setGeometry(0,0,self.W,self.H)


        self.boxes = []
        self.connectors = []

        self.old_positions = {}

        self.code_data = {}

        self.selected = None
        self.connected1 = None
        self.connected2 = None
        self._highlighted = None

        self.parent().graphEditButton.setEnabled(False)

        self.setMouseTracking(True)

        self.offx = 0
        self.offy = 0

        self.maxx = self.W-50 # 800
        self.maxy = self.H- 50 # 700

        self.mousex = 0
        self.mousey = 0

        self.mode = "drag"


        self.show()


    @property
    def highlighted(self):
        return self._highlighted

    @highlighted.setter
    def highlighted(self,val):
        if val is None:
            self.parent().graphEditButton.setEnabled(False)
            self.parent().graphDeleteButton.setEnabled(False)

            self._highlighted = val
        else:
            if not val.ishelper: # is not a helper node (connection node)
                self.parent().graphEditButton.setEnabled(True)
                # self.parent().graphDeleteButton.setEnabled(True)
                if val.n_connections == 0:
                    self.parent().graphDeleteButton.setEnabled(True)
                else:
                    self.parent().graphDeleteButton.setEnabled(False)
            else:
                self.parent().graphEditButton.setEnabled(False)
                self.parent().graphDeleteButton.setEnabled(False)

            self._highlighted = val

    def box_positions(self):
        pos_data = {}

        for box in self.boxes:
            pos_data[box.name] = {"x": int(box.x), "y": int(box.y)}

        return pos_data

    def reposition(self,pos_data):
        # reposition all the boxes
        print("reposition <-> ", pos_data)
        for box in self.boxes:
            if box.name in pos_data:

                print("reposition",box.name,pos_data[box.name])
                box.x = pos_data[box.name]["x"]
                box.y = pos_data[box.name]["y"]
                box.x0 = box.x
                box.y0 = box.y

    def edit_agent(self):
        if self.highlighted is not None:
            self.highlighted.edit_agent()

    def remove_agent(self):
        # remove currently selected agent if it has no connections
        box = self.highlighted
        if box is not None and box.n_connections <= 0:
            if box in self.boxes:
                self.boxes.remove(box)
            if box.name in self.code_data:
                del self.code_data[box.name]
            self.update()
        else:
            self.parent().notify("Box has still %i connection(s)! Cannot remove"%box.n_connections, title="Error")

    def check_exist(self,name):
        for box in self.boxes:
            # TODO more efficient search for large number of boxes?
            if box.name == name:
                return True
        return False

    def add_agent(self, name):

        # mechanism to avoid overwriting...
        for box in self.boxes:
            if not box.ishelper and box.name == name:
                return box

        # actually a new agent?
        if name not in self.old_positions:
            u = np.random.uniform(40,self.W-40)
            v = np.random.uniform(40,self.H-40)
        else:
            u,v = self.old_positions[name]

        new_box = Box(u,v,name,ishelper=False,parent_widget=self)
        self.boxes.append(new_box)
        self.update()

        return new_box

    def arrange_pretty(self):
        for box in self.boxes:
            box.adjust_position(self.boxes)

        self.update()

    def highlight_connector(self,name):
        for box in self.boxes:
            if box.ishelper and box.name == name:
                self.highlighted = box

        self.update()

    def add_connection(self,box1, box2, name):

        #for box in self.boxes:
        #    if box.ishelper and box.name == name:
        #        return

        new_conn = Connector(box1,box2,name)

        if name not in self.old_positions:
            self.old_positions[name] = new_conn.c.x, new_conn.c.y
        else:
            new_conn.c.x = self.old_positions[name][0]
            new_conn.c.y = self.old_positions[name][1]
            box1.n_connections += 1
            box2.n_connections += 1

        self.connectors.append(new_conn)
        self.boxes.append(new_conn.c)

        return new_conn

    def clear(self,clearall=False):

        if clearall:
            boxes = [b for b in self.boxes]

        else:
            boxes = [b for b in self.boxes if b.ishelper]

        while len(boxes) > 0:
            b = boxes.pop()
            self.boxes.remove(b)
            self.old_positions[b.name] = (b.x, b.y)

        while len(self.connectors) > 0:
            self.connectors.pop()


    def rename_connection(self,name,new_name):
        for box in self.boxes:
            if box.ishelper and box.name == name:
                box.name = new_name
                self.update()
                self.old_positions[box.name] = (box.x,box.y)


    def remove_connection(self,name):
        self.update()

        self.highlighted = None
        self.selected = None
        print("remove connection",name)

        for box in self.boxes:
            if box.ishelper and box.name == name:
                print("*BOX a", box.parent.a.n_connections)
                print("*BOX b", box.parent.b.n_connections)

                box.parent.a.n_connections -= 1
                box.parent.b.n_connections -= 1

                print("remove box", box, box.name)
                print("BOX a", box.parent.a.n_connections)
                print("BOX b", box.parent.b.n_connections)

                self.boxes.remove(box)
                self.connectors.remove(box.parent)

                if False:
                    # TODO ask dialog if boxes are to be deleted if they have no longer any connection to other boxes...
                    if box.parent.a.n_connections == 0:
                        self.boxes.remove(box.parent.a)
                    if box.parent.b.n_connections == 0:
                        self.boxes.remove(box.parent.b)

                # print("self.boxes",[b.name for b in self.boxes])

                self.old_positions[box.name] = (box.x, box.y)
                self.old_positions[box.parent.a.name] = (box.parent.a.x,box.parent.a.y)
                self.old_positions[box.parent.b.name] = (box.parent.b.x,box.parent.b.y)

                self.update()
                return


    def draw_bezier(self,qp,x0,y0,xf,yf,xi,yi):
        """
        draws a bezier line between x0,y0,xf and yf via xi,yi
        """

        # add offset
        dx = 0
        dy = 0

        # first quadrant (bottom right)
        if xf >= x0 and yf >= y0:
            x0 += 10
            xf -= 10

        # second quadrant (bottom left)
        if xf < x0 and yf >= y0:
            pass

        # third quadrant (top left)
        if xf < x0 and yf < y0:
            pass

        # fourth quadrant (top right)
        if xf >= x0 and yf < y0:
            pass




        t_vals = [0,0.2,0.4,0.6,0.8,1.0,1.1]
        points = []
        for t in t_vals:
            x_temp = (1-t)*((1-t)*x0+t*xi) + t*((1-t)*xi + t*xf)
            y_temp = (1-t)*((1-t)*y0+t*yi) + t*((1-t)*yi + t*yf)

            points.append((x_temp,y_temp))

        for i in range(len(points)-2):
            qp.drawLine(points[i][0],points[i][1],points[i+1][0],points[i+1][1])



    def curved_connector(self,qp,x0,y0,xf,yf,xi,yi):
        """
        draws a curved connector
        """

        # construct helper box_positions
        xi2 = 0.5*(xi-x0) + x0
        xi3 = 0.5*(xf-xi) + xi
        yi2 = 0.5*(yi-y0) + y0
        yi3 = 0.5*(yf-yi) + yi

        #qp.drawRect(xi2-5,yi2-5,10,10)
        #qp.drawRect(xi3-5,yi3-5,10,10)

        xi4 = xi
        yi4 = yi
        xi5 = xf
        yi5 = yf

        # first quadrant (bottom right)
        if xf >= xi and yf >= yi and abs(xi-xf) >30:
            xi4 = xi+30
            yi4 = yi
            xi5 = xf-30
            yi5 = yf

        # second quadrant (bottom left)
        if xf < xi and yf >= yi and abs(xi-xf) >30:
            xi4 = xi-30
            yi4 = yi
            xi5 = xf+30
            yi5 = yf

        # third quadrant (top left)
        if xf < xi and yf < yi and abs(xi-xf) >30:
            xi4 = xi-30
            yi4 = yi
            xi5 = xf+30
            yi5 = yf

        # fourth quadrant (top right)
        if xf >= xi and yf < yi and abs(xi-xf) >30:
            xi4 = xi+30
            yi4 = yi
            xi5 = xf-30
            yi5 = yf

        xi6 = x0
        yi6 = y0
        xi7 = xi
        yi7 = yi


        # first quadrant (bottom right)
        if xi >= x0 and yi >= y0 and abs(xi-x0) >30:
            xi6 = x0+30
            yi6 = y0
            xi7 = xi-30
            yi7 = yi

        # second quadrant (bottom left)
        if xi < x0 and yi >= y0 and abs(xi-x0) >30:
            xi6 = x0-30
            yi6 = y0
            xi7 = xi+30
            yi7 = yi

        # third quadrant (top left)
        if xi < x0 and yi < y0 and abs(xi-x0) >30:
            xi6 = x0-30
            yi6 = y0
            xi7 = xi+30
            yi7 = yi

        # fourth quadrant (top right)
        if xi >= x0 and yi < y0 and abs(xi-x0) >30:
            xi6 = x0+30
            yi6 = y0
            xi7 = xi-30
            yi7 = yi


        #qp.drawRect(xi4-5,yi4-5,10,10)
        #qp.drawRect(xi5-5,yi5-5,10,10)
        #qp.drawRect(xi6-5,yi6-5,10,10)
        #qp.drawRect(xi7-5,yi7-5,10,10)

        xi62 = 0.5*(xi6+xi2)
        yi62 = 0.5*(yi6+yi2)

        qp.drawLine(x0,y0,xi6,yi6)
        qp.drawLine(xi6,yi6,xi62,yi62)
        qp.drawLine(xi62,yi62,xi2,yi2)
        qp.drawLine(xi2,yi2,xi,yi)
        qp.drawLine(xi,yi,xi3,yi3)

        xi35 = 0.5*(xi3+xi5)
        yi35 = 0.5*(yi3+yi5)

        qp.drawLine(xi3,yi3,xi3,yi3)
        qp.drawLine(xi3,yi3,xi35,yi35)
        qp.drawLine(xi35,yi35,xi5,yi5)
        qp.drawLine(xi5,yi5,xf,yf)

        # points are [y0,xi6,xi2,xi3,xi5,xf]

        # qp.drawLine(xi2,yi2,xi5,yi5)

        #qp.drawLine(xi2,yi2,xi7,yi7)
        #qp.drawLine(xi7,yi7,xf,yf)

        #qp.drawLine(xi2,yi2,xf,yf)

        #self.draw_bezier(qp,xi4,yi4,xi5,yi5,xi3,yi3) # starting point
        #self.draw_bezier(qp,xi7,yi7,xi6,yi6,xi2,yi2) # starting point
        #self.draw_bezier(qp,xi,yi,xi3,yi3,xi7,yi7) # starting point
        #self.draw_bezier(qp,xi3,yi3,xf,yf,xi5,yi5) # starting point


    def paintEvent(self, event):

        qp = QtGui.QPainter(self)
        pen = QtGui.QPen(QtGui.QColor(0, 0, 0, 255),1) # ,2, Qt.SolidLine)
        qp.setPen(pen)
        qp.drawRect(0,0,self.W-2,self.H-2)


        for conn in self.connectors:

            if conn.c == self.highlighted:
                pen = QtGui.QPen(QtGui.QColor(255, 2, 2, 255),3) # ,2, Qt.SolidLine)
            else:
                pen = QtGui.QPen(QtGui.QColor(0, 0, 0, 200),1) # ,2, Qt.SolidLine)

            qp.setPen(pen)

            # qp.drawLine(int(conn.a.x+25), int(conn.a.y+25), int(conn.c.x+5), int(conn.c.y+5))
            # qp.drawLine(int(conn.c.x+5), int(conn.c.y+5), int(conn.b.x+25), int(conn.b.y+25))
            self.curved_connector(qp,int(conn.a.x+25), int(conn.a.y+25),int(conn.b.x+25), int(conn.b.y+25),int(conn.c.x+5), int(conn.c.y+5))
            # self.curved_connector(qp,int(conn.a.x), int(conn.a.y),int(conn.b.x), int(conn.b.y),int(conn.c.x), int(conn.c.y))

        pen = QtGui.QPen(QtGui.QColor(0, 0,0 , 200),1) # ,2, Qt.SolidLine)
        qp.setPen(pen)

        # print("self.boxes",[b.name for b in self.boxes])
        for box in self.boxes:

            if box != self.selected: # and box != self.connected2:

                x = box.x
                y = box.y
            elif box == self.selected:

                x = self.mousex + self.offx
                y = self.mousey + self.offx


            if box == self.selected:
                br = QtGui.QBrush(QtGui.QColor(34, 34, 230, 255))
            elif box == self.connected1:
                br = QtGui.QBrush(QtGui.QColor(100, 10, 10, 255))
            elif box.ishelper and box != self.highlighted:
                br = QtGui.QBrush(QtGui.QColor(0, 0, 100, 255))
            elif box == self.highlighted:
                br = QtGui.QBrush(QtGui.QColor(255, 44, 47, 255))
            else:
                br = QtGui.QBrush(QtGui.QColor(200, 200, 200, 255))

            x = int(x)
            y = int(y)

            if box.ishelper:
                qp.drawText(x,y-3,box.name)
            else:
                #qp.drawText(x,y-3,box.name.capitalize())
                qp.drawText(x,y-3,box.name)

            qp.setBrush(br)

            if box.ishelper:

                x2 = x + 8
                y2 = y + 8

                qp.drawRect(QtCore.QRect(QtCore.QPoint(x,y),QtCore.QPoint(x2,y2)))

            else:

                x2 = x + 50
                y2 = y + 50

                qp.drawRect(QtCore.QRect(QtCore.QPoint(x,y),QtCore.QPoint(x2,y2)))

    def mousePressEvent(self, event):

        self.parent().update_graphics_data(self.boxes,self.connectors)

        if event.buttons() & QtCore.Qt.RightButton:
            self.mode = "select"

        x,y = event.pos().x(), event.pos().y()

        x = int(x)
        y = int(y)

        # check if any box was selected
        self.selected = None
        for box in self.boxes:
            if box.ishelper:
                w = 10
            else:
                w = 50
            if box.x < x < box.x + w and box.y < y < box.y + w:

                if self.mode == "drag":
                    self.selected = box
                    self.offx = box.x - x
                    self.offy = box.y - y

                elif self.mode == "select":
                    if self.highlighted == box:
                        self.highlighted = None
                        print("unhighlight", box)
                    else:
                        print("highlight",box)
                        self.highlighted = box


                    self.mode = "drag"

                    if box.ishelper:
                        self.parent().data_select_where(box.name)

                    self.update()

                elif self.mode == "edit":
                    print("EDIT", box)

                    if box.ishelper:
                        print("EDIT CONNECTOR")
                        new_editor = TransactionEditor(self,box)

                    else:
                        print("EDIT AGENT")
                        new_editor = AgentEditor(self,box)

                    self.mode = "select"

                elif self.mode == "delete":
                    raise RuntimeError("Delete mode not supported")
                    self.selected = None
                    self.connected1 = None
                    self.connected2 = None

                    if box.ishelper and box.parent is not None:
                        self.boxes.remove(box.parent.c)
                        # self.boxes.remove(box.parent.d)
                        self.connectors.remove(box.parent)
                        self.update()
                        self.mode = "drag"
                    else:


                        for conn in self.connectors:
                            if conn.a == box or conn.b == box:
                                self.connectors.remove(conn)
                                self.boxes.remove(conn.a)
                                self.boxes.remove(conn.b)
                                self.boxes.remove(conn.c)

                        if box in self.boxes:
                            self.boxes.remove(box)

                        self.update()
                        self.mode= "drag"


                elif self.mode == "connect":
                    self.selected = None

                    if self.connected1 is None:
                        self.connected1 = box
                        self.update()

                    elif self.connected2 is None and not box.ishelper:
                        self.connected2 = box

                        con = Connector(self.connected1,self.connected2)
                        self.connectors.append(con)
                        self.boxes.append(con.c)
                        # self.boxes.append(con.d)

                        self.connected1 = None
                        self.connected2 = None
                        self.mode = "drag"


    def mouseMoveEvent(self,event):

        x,y = event.pos().x(), event.pos().y()

        self.mousex = x
        self.mousey = y

        # print("move",x,y)

        hovering = False
        for box in self.boxes:
            if box.ishelper:
                w = 10
            else:
                w = 50
            if box.x < x < box.x + w and box.y < y < box.y + w:

                if event.buttons() & QtCore.Qt.LeftButton:
                    self.mode = "drag"


                self.setCursor(Qt.OpenHandCursor)
                hovering = True

        if not hovering:
            self.setCursor(Qt.ArrowCursor)
            #self.parent().setCursor(Qt.OpenHandCursor)


        self.update()

    def mouseReleaseEvent(self, event):


        if self.mode == "drag":
            x,y = event.pos().x(), event.pos().y()

            if self.selected is not None:
                self.selected.x = np.clip(self.mousex + self.offx ,1,self.maxx)
                self.selected.y = np.clip(self.mousey + self.offy, 1, self.maxy)
                self.selected.x0 = self.selected.x
                self.selected.y0 = self.selected.y

                self.selected = None
            self.update()
