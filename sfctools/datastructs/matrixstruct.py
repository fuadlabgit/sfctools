__version__ = "0.3"
__author__ = "Thomas Baldauf"
__email__ = "thomas.baldauf@dlr.de"
__license__ = "MIT"
__birthdate__ = '15.11.2021'
__status__ = 'dev' # options are: dev, test, prod

import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from networkx.convert_matrix import to_pandas_adjacency,to_pandas_edgelist
from sfctools.src.agent import Agent
from networkx.algorithms.traversal.beamsearch import bfs_beam_edges


class MatrixStruct:
    """
    wrapper for a special networkx graph

    Special data structure for a 'matrix' filled with agents. Will be
    used for aggregate flow matrices. The idea behind this is to have
    a sparse and flexible data structure where agents and their relations can be stored.
    This ensures stock-stock consistency of a macro economic model.
    """

    def __init__(self,handler,name=None):
        """
        set up a new matrixstruct.
        handler will be called when traversing the network for connections
        """

        self.graph = nx.DiGraph()

        self.name = name

        self.handler = handler

    def establish_connection(self, agent1, agent2):
        self.graph.add_edge(agent1, agent2)

    def remove_connection(self, agent1, agent2):
        self.graph.remove_edge(agent1, agent2)

    def plot(self,with_labels=False):
        plt.figure(figsize=(5,5))

        if self.name is None:
            plt.title("My Agent Network")
        else:
            plt.title(self.name)

        nx.draw(self.graph, with_labels=with_labels,node_size=20,node_color='#686f82')
        plt.show()

    def to_dataframe(self, option="adjacency"):
        """
        convert the current graph to a dataframe

        :param option: 'adjacency' or 'edge'
        """

        if option == "adjacency":
            return to_pandas_adjacency(self.graph)
        elif option == "edge":
            return to_pandas_edgelist(self.graph)

    def traverse(self):
        """
        traverses the network and executes the handler for every connection
        """
        for u,v in self.graph.edges:
            u.trigger(self.handler, v)

