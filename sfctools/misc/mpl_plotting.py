__version__ = "0.3"
__author__ = "Thomas Baldauf"
__email__ = "thomas.baldauf@dlr.de"
__license__ = "MIT"
__birthdate__ = '15.11.2021'
__status__ = 'prod' # options are: dev, test, prod

"""
Small plotting library for bar plots and line plots. Usage is optional / voluntary...
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pylab import rcParams
import matplotlib.patches as mpatches
import matplotlib as mpl
from functools import partial


def add_value_labels(ax, spacing=.9, fmt="{0:d}", stacked=False, legend="best"):
    """Add labels to the end of each bar in a bar chart.

    Arguments:
        ax (matplotlib.axes.Axes): The matplotlib object containing the axes
            of the plot to annotate.
        spacing (int): The distance between the labels and the bars.

    """

    # For each bar: Place a label
    for rect in ax.patches:
        # Get X and Y placement of label from rect.
        y_value = rect.get_y() + rect.get_height() * 1.01
        x_value = rect.get_x() + rect.get_width() * 0.01

        # print("yvalue",x_value,y_value)
        # Number of points between bar and label. Change to your liking.

        space = spacing
        # Vertical alignment for positive values
        va = 'bottom'

        # If value of bar is negative: Place label below bar
        if y_value < 0:
            # Invert space to place label below
            space *= -1
            # Vertically align label at top
            va = 'top'

        # Use Y value as label and format number with one decimal place
        # label = "{:.1f}".format(y_value)
        hgt = rect.get_height()
        if hgt != 0.0:
            label = fmt.format(hgt)
        else:
            label = ""

        # Create annotation
        ax.annotate(
            label,  # Use `label` as label
            (x_value, y_value),  # Place label at end of the bar
            xytext=(0, space),  # Vertically shift label by `space`
            textcoords="offset points",  # Interpret `xytext` as offset in points
            ha='left',  # Horizontally center label
            va=va)  # Vertically align label differently for
        # positive and negative values.


def matplotlib_barplot(data, xlabel, ylabel, title, color="indigo", size=(6, 5), tight_layout=True,
                       fmt="{0:f}", stacked=False, show_labels=True, legend="best", show=True):
    """
    Creates a bar plot in matplotlib. The 'macro' plotting style will be used if it is set up

    :param xlabel: x axis  label
    :param ylabeL: y axis  label
    :param title: plot title
    :param color: plot color
    :param size: figure size
    :param tight_layout: re-format plot
    :param fmt: number format, {0:d} or {0:f} for example
    :param stacked: stack column? or show side-by side (boolean)
    :paarm show_labels: show the column labels at bottom? (boolean)
    :param legend: location of legend, or 'off'
    :param show: if False, only the figure is returned. Else plot is shown
    """

    # if legend is 'off', no legend is shown

    plt.rcParams['axes.ymargin'] = .4
    rcParams['figure.figsize'] = size

    try:
        plt.style.use("macro") # if 'macro' plotting style is installed -> use it!
    except:
        pass

    plt.grid(alpha=0.0)

    if not isinstance(data, pd.DataFrame):
        if ylabel is None:
            ylabel = "Data"
        data = pd.DataFrame({ylabel: data})
        data.set_index(ylabel)
    
    # plt.figure(figsize=size)
    data.plot.bar(color=color, stacked=stacked,ax=plt.gca())
    plt.gca().set_title(title)
    # plt.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=True)
    plt.ylabel(ylabel)
    plt.xlabel(xlabel)

    if show_labels:
        add_value_labels(plt.gca(), fmt=fmt)

    if legend != "off":
        plt.legend(loc=legend)
    else:
        old_legend = plt.gca().get_legend()
        if old_legend is not None:
            old_legend.remove()
    if tight_layout:
        plt.tight_layout()

    if show:
        plt.show()
    else:
        return plt.gcf()


def matplotlib_lineplot(data, xlabel=None, ylabel=None, title="", xlim=None, ylim=None, color="indigo", legend="best",show=False):
    """
    creates a line plot in matplotlib. The 'macro' plotting style will be used if it is set up

    :param xlabel: x axis  label
    :param ylabeL: y axis  label
    :param title: plot title
    :param color: plot color
    :param xlim, ylim: tuples of plot limits
    :param legend: location of legend, or 'off', or 'outside'
    :param show: if False, only the figure is returned. Else plot is shown
    """
    try:
        plt.style.use("macro")
    except:
        pass


    if not isinstance(data, pd.DataFrame):
        if ylabel is None:
            label = "Data"
        data = pd.DataFrame({ylabel: data})
        data.set_index(ylabel)

    data.plot(color=color)
    plt.xlim(xlim)
    plt.ylim(ylim)
    plt.title(title)

    if legend != "off" and legend == "outside":
        plt.legend(loc=legend)
    elif legend == "outside":
        plt.legend(loc=(1.02,0))

    else:
        old_legend = plt.gca().get_legend()
        if old_legend is not None:
            old_legend.remove()
        if ylabel is not None:
            plt.ylabel(ylabel)

    if xlabel is not None:
        plt.gca().set_xlabel(xlabel)

    if ylabel is not None:
        plt.gca().set_ylabel(ylabel)
    plt.rcParams['axes.ymargin'] = .4

    if show:
        plt.show()
    else:
        return plt.gcf()




class Point:
    """
    a rudimentary point in 2d space
    """

    def __init__(self, x, y):
        self.x = x
        self.y = y


class Label:
    """
    a rudimentary node label
    """

    names = []

    def __init__(self,x,y,text):
        self.x = x
        self.y = y
        self.text = text
        if text in self.__class__.names:
            raise RuntimeError("Name already given")
        else:
            self.__class__.names.append(self.text)

    def shift_up(self):
        # shift the label upwards a bit
        self.y += 1.8
        self.x -= 0.2 # re-center


def casteljau(t,b0,b1,b2,b3):
    """
    casteljau bezier spline for 4 points.

    :param b0-b3: the point of the bezier curve as [x,y] array
    :param t: parameter for position on the curve, float
    """
    b = np.multiply((-b0 + 3*b1 - 3*b2 + b3),np.power(t,3))  + np.multiply((3*b0 - 6*b1 + 3*b2),np.power(t,2)) + np.multiply((-3*b0 + 3*b1),t) + b0
    return b


def bezier(pstart : Point, pend: Point ,npoints = 100, curv=None):
    """
    compute the path of a 1d bezier curve

    :param pstart: starting point of the bezier curve
    :param pend: end point of the bezier curve
    :param npoints: number of discrete points to retrun
    :param curv: optionally you can give a curvature parameter here (float) default None

    :return: x,y coordinate tuple as ndarray of shape (npoints,)
    """

    # de-casteljau b-spline
    tarr = np.linspace(0,1,npoints) # parameter of the curve position
    # define 4 points: b0, b1, b2, b3

    if pstart.x < pend.x: # pstart left of pend?
        pleft = pstart
        pright = pend
    else:
        pleft = pend
        pright = pstart

    if curv is None:
        curv = .27*(pright.x-pleft.x)

    b0 = np.array([pleft.x,pleft.y])
    b1 = np.array([pleft.x+curv,pleft.y])
    b2 = np.array([pright.x-curv,pright.y])
    b3 = np.array([pright.x,pright.y])

    spline = partial(casteljau,b0=b0,b1=b1,b2=b2,b3=b3)

    b = np.array([spline(t) for t in tarr])

    return b[:,0],b[:,1]


def band(pstart: Point, pend: Point, npoints=100,curv=None, weight=2):
    """
    computes a band of two bezier curves

    :param pstart: starting point of the bezier curve
    :param pend: end point of the bezier curve
    :param npoints: number of discrete points to retrun
    :param curv: optionally you can give a curvature parameter here (float) default None
    :param weight: width of the band

    :return: x,y1,y2 coordinate 3-tuple of the band
    """

    w = weight # width of the band
    d = 0 # horizontal shift of the bands realtive to each other
    e = 2 # distance of  '<' and '>' arc

    qstart = Point(pstart.x-d,pstart.y)
    qend  = Point(pend.x-d,pend.y)

    pstart1 = Point(pstart.x-d+.2*e,pstart.y+w)
    pend1 = Point(pend.x-d-e,pend.y+w)

    pstart2 = Point(pstart.x+d+.2*e,pstart.y-w)
    pend2 = Point(pend.x+d-e,pend.y-w)

    bezier_start1 = bezier(qstart,pstart1)
    bezier_start2 = bezier(qstart,pstart2)

    bezier_end1 = bezier(pend1,qend)
    bezier_end2 = bezier(pend2,qend)

    bezier1 = bezier(pstart1,pend1)
    bezier2 = bezier(pstart2,pend2)

    x = np.array(list(bezier_start1[0])+list(bezier1[0])+list(bezier_end1[0]))
    y1 = np.array(list(bezier_start1[1])+list(bezier1[1])+list(bezier_end1[1]))
    y2 = np.array(list(bezier_start2[1])+list(bezier2[1])+list(bezier_end2[1]))

    return x, y1, y2


def draw_band(fig,pstart:Point, pend:Point, color="blue",alpha=.8,weight=2,norm=1.0,show_label=True,label=None):
    """
    draw a band graphically

    """
    x,y1,y2 = band(pstart,pend,weight=weight)
    plt.fill_between(x,y1,y2,color=color,figure=fig,alpha=alpha)

    if show_label and label is not None:
        # draw label
        b1 = np.array([pstart.x + 3, pstart.y])
        b2 = np.array([pend.x - 3,pend.y])
        bx,by = casteljau(t=np.random.uniform(0.4,0.6),b0=np.array([pstart.x,pstart.y]),b1=b1,b2=b2,b3=np.array([pend.x,pend.y]))

        #bx2,by2 = casteljau(t=0.55,b0=np.array([pstart.x,pstart.y]),b1=b1,b2=b2,b3=np.array([pend.x,pend.y]))
        #bx3,by3 = casteljau(t=0.66,b0=np.array([pstart.x,pstart.y]),b1=b1,b2=b2,b3=np.array([pend.x,pend.y]))
        #rot = (90-.5*np.arctan2((bx3-bx2),(by3-by2))*180.0/np.pi)%360.0 # compute slope at point
        rot = 20

        bbox = {'fc': '1.0', 'pad': 2, 'facecolor':'white','edgecolor':'black','linewidth':.2}
        props = {'ha': 'center', 'va': 'center', 'bbox': bbox}

        if label is not None:
            plt.gca().text(bx,by, label, props, rotation=rot,color="black",alpha=alpha)
        else:
            plt.gca().text(bx,by, "%.2f" %(weight/norm), props, rotation=rot,color="black",alpha=alpha)
        # plt.annotate(str(weight),(bx,by),color="gray",alpha=alpha)

def plot_sankey(data,title="Sankey Diagram",show_plot=True,show_values=True):
    """
    plots a sankey diagram from data

    :param data: list of pandas dataframes, of the following format. length at least two.
    :param title: title of the plot
    :param show_plot: boolean switch to show plot window (default True). If False, figure is returned
    :param show_values: boolean switch to print numerical values of data as text label (default True)

    :return fig: None or matplotlib figure

    +----------+----------+----------+-------------+
    |  from    |   to     |  value   | color_id    |
    +----------+----------+----------+-------------+
    |    A     |  C       | 1.0      |    0        |
    +----------+----------+----------+-------------+
    |    A     |  D       | 2.0      |    1        |
    +----------+----------+----------+-------------+
    |    B     |  D       | 3.0      |    2        |
    +----------+----------+----------+-------------+

    +----------+----------+----------+-------------+
    |  from    |   to     |  value   | color_id    |
    +----------+----------+----------+-------------+
    |    C     |  E       | 5.0      |    1        |
    +----------+----------+----------+-------------+
    |    C     |  F       | 6.0      |    2        |
    +----------+----------+----------+-------------+
    |    D     |  G       | 8.0      |    3        |
    +----------+----------+----------+-------------+

    """

    if not isinstance(data,list):
        data = [data] # convert to list


    # TODO custom colors or custom color themes
    colors = [
        "black",
        "red",
        "blue",
        "gold",
        "dimgray",
    ]



    # 1. normalize the values to reasonable width of bands

    norm_factor = 1.0 #normalization factor for with

    maxval = 0.0
    maxrows = 2

    for layer in data:
        maxrows = max(maxrows,len(list(layer.iterrows())))
        for idx,row in layer.iterrows():
            val = float(row["value"])

            maxval = max(val,maxval)

    norm_factor = 1.0
    if maxval > 0.0:
        norm_factor = 1.0 /maxval

    fig = plt.figure(figsize=(4.6*len(data),1.8*maxrows))

    # 2. plot the bezier patches

    i = 10  #
    j0 = 10 # < starting position (i,j)

    dy = 8  # vertical distance of bands
    dx = 40  # horizontal distance of layers

    dx_space = 2 # white space between layers

    # define some points for the unique nodes
    my_points = {} # keys will be names, value will be Points
    my_labels = {} # keys will be names, value will be Labels
    my_values = {} # labels for values

    last_j = j0

    # iterate through the dataframes
    for indx,layer in enumerate(data):

        j = last_j
        for name in layer["from"].unique():

            if name not in my_points:
                new_point = Point(i+dx_space,j)
                my_points[name] = new_point

            if name not in my_labels:
                my_labels[name] = Label(new_point.x-2.2,new_point.y-.2,name) # plt.annotate(name,(new_point.x-1.8, new_point.y-.1))
            else:

                my_labels[name].shift_up()

            j+= dy

        j = j0
        for name in layer["to"].unique():

            if name not in my_points:
                new_point = Point(i+dx,j)
                my_points[name] = new_point #Point(i+dx,j)

            if name not in my_labels:
                my_labels[name] = Label(new_point.x+.5*dx_space,new_point.y-.2,name) # plt.annotate(name,(new_point.x+.5*dx_space,new_point.y-.1))
            else:
                my_labels[name].shift_up()
            #else:
                #if indx != len(data)-1:
                #    my_labels[name].shift_up()

            j+= dy

        last_j = j - dy

        i += dx


        # iterate through the dataframe rows
        for idx,row in layer.iterrows():

            color_idx = int(row["color_id"]) # index for color map

            fromnode = my_points[row["from"]]
            tonode = my_points[row["to"]]
            weight = max(0.1,float(row["value"])*norm_factor)

            draw_band(fig,fromnode,tonode,colors[color_idx%len(colors)],weight=weight,norm=norm_factor,show_label=show_values,label=str(row["value"]))



    for label in my_labels.values(): # draw the labels here...
        if len(label.text) <= 2:
            plt.annotate(label.text,(label.x,label.y))
        else: # rotate label for better visibility
            plt.gca().text(label.x,label.y, label.text, rotation=45)

    # 3. return the figure or show window

    plt.axis("off")


    max_x = 0
    max_y = 0

    for point in my_points.values():
        max_x = max(max_x,point.x)
        max_y = max(max_y,point.y)

    for label in my_labels.values():
        max_x = max(max_x,label.x)
        max_y = max(max_y,label.y)

    plt.xlim([3,max_x+5])
    plt.ylim([3,max_y+3])

    #plt.autoscale()

    plt.tight_layout()

    plt.title(title)

    plt.tight_layout()

    if show_plot:
        plt.show()

    return fig



if __name__ == "__main__":
    """
    basic manual testing of plot functionality
    """

    """
    data = np.random.rand(100)
    matplotlib_lineplot(data, xlabel="time", ylabel="bla", title="Test Plot", legend="off")

    other_data = {"a": 30, "b": 50, "c": 100}
    matplotlib_barplot(other_data, xlabel="category", ylabel="height", title="Test Plot", legend="off")
    """

    my_test_data = [pd.DataFrame({
        "from": ["A","A","B","A"],
        "to": ["C","U","C","D"],
        "value": [1.0,8.0,3.0,2.0],
        "color_id":[0,0,0,1] }),

        pd.DataFrame({
        "from": ["C","D","C","C"],
        "to": ["F","G","G","X"],
        "value": [6.0,8.0,.8,5.5],
        "color_id":[0,0,0,0] }),

        pd.DataFrame({
        "from": ["F","G","F","X","G","G"],
        "to": ["H","I","J","H","H","J"],
        "value": [.2,1.0,1.0,10.0,4.0,6.0],
        "color_id":[0,2,0,0,2,0] })
    ]

    plot_sankey(my_test_data,show_values=False)
