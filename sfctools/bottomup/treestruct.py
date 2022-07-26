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
from networkx.algorithms.traversal.beamsearch import bfs_beam_edges
from collections.abc import Mapping
from networkx.drawing.nx_agraph import graphviz_layout

def graph_from_dict(graph_data):
    """
    take a nested dict and convert it to a networkx graph
    """

    G = nx.DiGraph()  # empty directed graph

    q = list(graph_data.items())
    while q: # iterate through the layers
        v, d = q.pop()
        for nv, nd in d.items():
            G.add_edge(v, nv)
            if isinstance(nd, Mapping):
                q.append((nv, nd))
    return G


class TreeStruct:
    """
    wrapper for a special networkx graph

    tree structure (for supply chain processing)
    """

    def __init__(self, data, handler):
        """
        inits a static production tree from nested dict.

        :param data: data in form of a nested dict
        :param handler: handler to be called at each node

        example data

        data = {
            A: {
                B: {},
                C:
                {
                    D: {},
                    E: {}
                }
            }
        }

        for a tree like

                     A
                    / \
                   B   C
                      / \
                     D   E
        """

        self.tree = graph_from_dict(data)
        self.handler = handler

    def traverse(self):
        """
        traverse the tree struct and execute production nodes
        on the way. -> Breadth-first search
        """

        if self.handler is not None:

            for u, v in self.tree.edges:  # iterate through all edges and trigger handlers
                v.trigger(self.handler, u)

    def plot(self):
        """
        plots the production tree with networkx
        """

        plt.figure(figsize=(7, 5))
        pos = graphviz_layout(self.tree, prog='dot')
        nx.draw(self.tree, pos, with_labels=True, arrows=True, node_color='#d1ffdf')
        plt.show()


if __name__ == "__main__":
    """
    test for plotting
    """

    data = {
            "A": {
                "B": {},
                "C":
                {
                    "D": {},
                    "E": {}
                }
            }
        }

    ts = TreeStruct(data, "Produce")

    ts.plot()
