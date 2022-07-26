__version__ = "0.3"
__author__ = "Thomas Baldauf"
__email__ = "thomas.baldauf@dlr.de"
__license__ = "MIT"
__birthdate__ = '15.11.2021'
__status__ = 'dev' # options are: dev, test, prod

import numpy as np
import matplotlib.pyplot as plt
import warnings

"""
This file embraces the following features

IndicatorReport
DistributionReport
ReportingSheet

WARNING BETA, under development, use at own risk!
"""

class IndicatorReport:
    """
    A generic class for logging scalar values ('indicators').
    """

    _instances = {}

    def __init__(self,xlabel,ylabel):
        """

        :param xlabel: x axis label, str
        :param ylabel: y axis label, str
        """
        self.data = []
        self.xlabel = xlabel
        self.ylabel = ylabel

        if not self.ylabel in self.__class__._instances:
            self.__class__._instances[self.ylabel] = self
        else:
            warnings.warn("Tried to add a report with a variable that is already registered. Skipping...")

    @classmethod
    def getitem(cls,key):
        """
        retrieves a certain report from the instances created.

        :param key: the ylabel of the respective report 
        """
        return cls._instances[key]

    def add_data(self,x):
        """ 
        inserts some data into the data structure

        :param x: a scalar value 
        """
        self.data.append(x)

    def plot_data(self,ax):
        """
        plots the data onto a matplotlib axis

        :param ax: a matplotlib axis
        """

        data = self.data
        x = np.arange(len(data)) + 1
        y = data # np.random.rand(len(x))

        if len(data) > 1 and data[1] is not None:
            has_labels = True

        if len(y) < 100: 
            ax.scatter(x, y, color="gray", s=4.0)  # <- manually optimized
        else:
            ax.plot(x, y, "-", color="black") # <- manually optimized

        ax.set_xlabel(self.xlabel)
        ax.set_ylabel(self.ylabel)

        # ax.set_title(self.title)


class DistributionReport:
    """
    A generic class for a logger of a distribution (i.e. )
    """

    def __init__(self,title):
        """
        :param title: title of the report
        """

        self.data = []
        self.title = title

    def add_data(self, x, label=None):
        """
        adds data into the data structure. (stores a sorted version of x).

        :param x: list or numpy array to store
        :param label: some additional tag
        """

        y = np.sort(x.copy())

        # store distribution
        self.data.append((y,label))

    def plot_data(self, ax,colors=None):
        """
        plot the data onto a matplotlib axis
        
        :param ax: a matplotlib axis
        :param colors: list of colors to use (default None)
        """

        colors = ["gray", "indianred", "mediumblue"]

        has_labels = False

        for i,data in enumerate(self.data):
            x = np.arange(len(data[0]))+1
            y = data[0] # np.random.rand(len(x))
            label = data[1] or ""
            if data[1] is not None:
                has_labels = True
            ax.plot(x, y,color=colors[i%len(colors)], alpha=1-0.8*i/len(self.data[0]),label=label)
            ax.scatter(x, y, color=colors[i % len(colors)], s=.5)

        ax.set_ylabel(self.title)
        ax.set_xlabel("Rank")

        if has_labels:
            ax.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)


class ReportingSheet:
    """
    Reporting sheet is an overview sheet for reporting model results in form of a grid plot.
    """

    def __init__(self,instances=None):
        """
        :param instances: default None, if not None: list of Report instances can be passed here
        """
        if instances is None:
            self.items = []
        else:
            self.items = instances
    
    def add_report(self,report):
        """
        Adds a report item to this sheet.

        :param report: any IndicatorReport or DistributionReport
        """
        self.items.append(report)

    def plot(self, show_plot=True):
        """
        Generates a plot grid using matplotlib

        :param show_plot: show the figure in a window? default True. If False, figure is returned
        :return fig: matplotlib figure
        """
        
        plt.rcParams.update({'font.size': 8})

        # layout is 2 plots per column...
        n_cols = 2
        n_rows = max(1,int(np.ceil(len(self.items)/n_cols)))

        print("n_rows","n_cols",n_rows,n_cols)
        cm = 1 / 2.54  # centimeters in inches
        fig = plt.figure(figsize=(0.5*3.1415*10.5*cm,14.8*cm)) # DIN A6

        try:
            plt.style.use("macro")
        except:
            pass

        for i,item in enumerate(self.items):
            ax = fig.add_subplot(n_rows,n_cols,i+1)
            item.plot_data(ax)

        plt.tight_layout()
        fig.subplots_adjust(hspace=.67)

        if show_plot:
            plt.show()
        
        return fig 

    def to_latex(self):
        """
        Generates latex code NOT YET IMPLEMENTED
        """
        raise NotImplementedError("Not yet implemented. Wait for beta release.")


if __name__ == "__main__":

    rep_sheet = ReportingSheet()

    for i in range(3):
        my_dist = DistributionReport(title="Distribution 1")
        my_dist.add_data(np.random.rand(10),label="t=1")
        my_dist.add_data(np.random.rand(10),label="t=2")
        my_dist.add_data(np.random.rand(10), label="t=3")
        rep_sheet.add_report(my_dist)

    for i in range(3):
        my_ind = IndicatorReport(xlabel="Time", ylabel="Some Indicator")
        my_ind.add_data(np.random.rand(10), label="t=1")
        my_ind.add_data(np.random.rand(10), label="t=2")
        my_ind.add_data(np.random.rand(10), label="t=3")
        rep_sheet.add_report(my_ind)

    rep_sheet.plot()

