__version__ = "0.3"
__author__ = "Thomas Baldauf"
__email__ = "thomas.baldauf@dlr.de"
__license__ = "MIT"
__birthdate__ = '15.11.2021'
__status__ = 'test' # options are: dev, test, prod

from .treestruct import TreeStruct
from ..core.agent import Agent

from collections import defaultdict

import networkx as nx
import matplotlib.pyplot as plt
from networkx.drawing.layout import spring_layout


def dict_depth(d):
    """
    helper function to get the depth of a nested dict
    """
    if isinstance(d, dict):
        return 1 + (max(map(dict_depth, d.values())) if d else 0)
    return 0


def unfold_tree(tree, agent_name_dict):
    """
    iterates through production tree and 'unfolds it' by inserting the appropriate agent names
    """

    t = {}  # tree to store production chain

    # if isinstance(tree,list):
    #    strtree += "|        "*rec + str( tree) + "\n"
    #    return tree,strtree


    for key, val in tree.items():
        if val == {}: # is a leaf?

            if (not isinstance(agent_name_dict,defaultdict)) and key.split(";")[0] not in agent_name_dict:
                error =  KeyError("Error building production tree: could no find definition for leaf %s" % key.split(";")[0])
                raise error 

            name = agent_name_dict[key.split(";")[0]]  # name is split from production function definition here
            if isinstance(key, str) and len(key.split(";")) > 1:
                display_name = name + ";" + key.split(";")[1]

            else:
                if isinstance(name,list): # <- can pass a one-element list or just an instance here
                    display_name = str(name[0])
                else:
                    display_name = str(name)

            t[display_name] = {}  # str(key)  # is a leaf

        else: # is no leaf?

            if (not isinstance(agent_name_dict,defaultdict)) and key.split(";")[0] not in agent_name_dict:
                error =  KeyError("Error building production tree: could no find definition for node %s" % key.split(";")[0])
                raise error 

            for name in agent_name_dict[key.split(";")[0]]:

                if isinstance(name, str) and len(key.split(";")) > 1:
                    display_name = name + ";" + key.split(";")[1]
                else:
                    if isinstance(name,list): # <- can pass a one-element list or just an instance here
                        display_name = str(name[0])
                    else:
                        display_name = str(name)

                # print("strtree",strtree)
                t[display_name] = unfold_tree(val, agent_name_dict)

    return t

def tree_to_coords(tree, rec=0, data=None,linedata=None, style="tree"):
    """
    makes plotting data for a tree

    :param tree: a dict of dicts
    :param style: 'tree' or 'vertical' or 'horizontal'

    :param data: recursion parameter, do not change
    :param rec: recursion parameter, recursion depth, do not change

    :return strtree: str, tree in string representation

    """
    dx = 30
    
    if data is None:
        data = []

    if linedata is None:
        linedata = []
    

    if tree is not None:
        for key, val in tree.items():

            if style == "vertical":
                # strtree += "|        " * rec + str(key) + "\n"
                #x += dx*rec 
                #y  += dy 
                #data.append((str(key),x,y,False))
                raise NotImplementedError("Not implemented. try 'tree'")
            elif style == "horizontal":
                # strtree += "|" + "____________" * rec + str(key) + "\n"
                #x += dx*rec 
                #y += dy 
                #data.append((str(key),x,y,False))
                raise NotImplementedError("Not implemented. try 'tree'")

            elif style == "tree":
                if rec >= 1:
                    if val == {}: # is leaf 
                        # strtree += "'            " * (rec - 1) + "|" + "____________. " + str(key) + "\n"
                        x = dx*rec 
                        data.append((str(key),x,rec,True))
                        # linedata.append((x,rec-5,x,rec))
                        linedata.append((x-dx,rec,x,rec))
                        
                    else:
                        # strtree += "'            " * (rec - 1) + "|" + "____________ " + str(key) + "\n"
                        x = dx*rec 
                        data.append((str(key),x,rec,False))
                        #linedata.append((x,rec-5,x,rec))
                        linedata.append((x-dx,rec,x,rec))
                                         
                else:
                    # strtree += "|" + str(key) + "\n"
                    x = 0
                    # linedata.append((x,rec-5,x,rec))
                    data.append((str(key),x,rec,False))
                    
           
            tree_to_coords(val, rec + 1, data, linedata,style)
    
    return data,linedata



def tree_to_str(tree, rec=0, strtree="", style="tree"):
    """
    prints a tree structure (nested dict) as str

    :param tree: a dict of dicts
    :param style: 'tree' or 'vertical' or 'horizontal'

    :param strtree: recursion parameter, do not change
    :param rec: recursion parameter, recursion depth, do not change

    :return strtree: str, tree in string representation

    """

    if tree is not None:
        for key, val in tree.items():

            if style == "vertical":
                strtree += "|        " * rec + str(key) + "\n"

            elif style == "horizontal":
                strtree += "|" + "____________" * rec + str(key) + "\n"


            elif style == "tree":
                if rec >= 1:
                    if val == {}:
                        strtree += "'            " * (rec - 1) + "|" + "____________. " + str(key) + "\n"
                    else:
                        strtree += "'            " * (rec - 1) + "|" + "____________ " + str(key) + "\n"
                else:
                    strtree += "|" + str(key) + "\n"
            strtree = tree_to_str(val, rec + 1, strtree, style)

    return strtree


def recursive_items(dictionary):
    # yields items of a dictionary recursively
    for key, value in dictionary.items():
        if type(value) is dict:
            yield key.split(";")  # (key, value)
            yield from recursive_items(value)
        else:
            yield key.split(";")  # (key, value)


def reverse_dict_search(d, x):
    # search key x in values of dictionary d
    for k, v in d.items():
        #print("search", k, v)
        if x == v or x in v:
            return k


def extract_production_info(tree, production_dict, agent_name_dict):
    """
    extracts relevant production parameters from production_dict and agent_name_dict,
    see ProductionTree class for more information.
    """

    #print("EXTRACT")
    keys = list(recursive_items(tree))

    production_info = {}

    #p#rint("production info", keys)

    for key in keys:

        factor = key[0]
        agents = agent_name_dict[factor]

        params = None
        if len(key) > 1:
            params = production_dict[key[1]].copy() # copy ensures that product key does not change 'globally'
            params["product"] = factor

        if isinstance(agents, list):
            for agent in agents:
                if agent not in production_info:
                    production_info[agent] = params
        else:
            if agents not in production_info:
                production_info[agents] = params

        # print("agents",agents, "---->",factor)

    return production_info


def full_tree_pos(G):
    # position generator from https://stackoverflow.com/questions/33439810/preserving-the-left-and-right-child-while-printing-python-graphs-using-networkx 

    n = G.number_of_nodes()
    if n == 0 : return {}
    # Set position of root
    pos = {0:(0.5,0.9)}
    if n == 1:
        return pos
    # Calculate height of tree
    i = 1
    while(True):
        if n >= 2**i and n<2**(i+1):
            height = i 
            break
        i+=1
    # compute positions for children in a breadth first manner
    p_key = 0
    p_y = 0.9
    p_x = 0.5
    l_child = True # To indicate the next child to be drawn is a left one, if false it is the right child
    for i in range(height):
        for j in range(2**(i+1)):
            if 2**(i+1)+j-1 < n:
                # print 2**(i+1)+j-1
                if l_child == True:
                    pos[2**(i+1)+j-1] = (p_x - 0.2/(i*i+1) ,p_y - 0.1)
                    G.add_edge(2**(i+1)+j-1,p_key)
                    l_child = False
                else:
                    pos[2**(i+1)+j-1] = (p_x + 0.2/(i*i+1) ,p_y - 0.1)
                    l_child = True
                    G.add_edge(2**(i+1)+j-1,p_key)
                    p_key += 1
                    (p_x,p_y) = pos[p_key]

    return pos

class Dummy:
    def __init__(self):
        pass 


class ProductionTree:
    """
    A production tree is a set of nested dictionaries to describe a production structure (or supply chain). 

    
        
        Example: 

        .. code-block:: python
        
            from sfctools import Agent, ProductionTree

            class MyProduction():
                def __init__(self,x):
                    
                    
            my_agent_a = MyProduction("A")
            my_agent_b = MyProdution("B")
            my_agent_y = MyProduction("Y")
            
            production_dict = {
                    "CES_1": {"epsilon": 1.0, "alpha": [0.5,0.3,0.2]}, #...
                    }

            data =  {"Y;CES_1":
                        {"A": {},
                         "B": {}}

            agent_name_dict = {
                            "A": [my_agent_a],
                            "B": [my_agent_b],
                            "Y": [my_agent_y]
                        }

            my_production_tree = ProductionTree(production_dict,data,agent_name_dict)
    """

    count = 0

    def __init__(self, production_dict, data, agent_name_dict=None):
        """
        constructor for production tree
        
        :param production_dict: stores production function names (str) as keys, and dicts of productino function parameters as values
        :param data:  a nested structure of goods and their production functions, separated by ';' in the keys (see example)
        :param agent_name_dict: A dictionary where the keys are the goods and the values are lists of agents. If None (default), dummy instances will be placed here  
        """
        #TODO maybe a bit more documentation about what is going on here is required. -> provide later
        

        self.production_dict = production_dict

        self.data = data

        if agent_name_dict is None:
            # empty agent name dict -> place dummies here 

            agent_name_dict = defaultdict(lambda: [Dummy()])
            print("Default dict", agent_name_dict)
            print(agent_name_dict["Output"])

        self.detailed_data = unfold_tree(data, agent_name_dict)
        
        """
        This will create two trees: one with the aggregate production tree and one detailed (unfolded one)
        """

        self.production_info = extract_production_info(data, production_dict, agent_name_dict)
        #print("PRODUCTION INFO")
        #for k,v in self.production_info.items():
        #    print(k,v)

        self._root = next(iter(self.data.keys()))
        self._detailed_root = next(iter(self.detailed_data.keys()))

        self.depth = dict_depth(self.data)
        self.detailed_depth = dict_depth(self.detailed_data)

        self.tree = TreeStruct(data, None)
        self.detailed_tree = TreeStruct(self.detailed_data, None)

        self.__class__.count+= 1

    @property
    def root(self):
        """
        returns the root node of the (unfolded) tree structure.
        """
        return self._detailed_root

    def __repr__(self):
        return "< ProductionTree %i >"  % self.__class__.count

    def to_str(self, mode='aggregate'):
        """
        returns a string representation of the production tree
        :param mode: 'detailed' or 'aggregate'
        """
        if mode == "aggregate":
            return tree_to_str(self.data)

        elif mode == "detailed":
            return tree_to_str(self.detailed_data)

        else:
            raise (KeyError("Can not find str conversion mode. Allowed are 'detailed' or 'aggregate'"))


    def plot(self, mode="aggregate", with_labels = True, param_name="sigma", nodecolor="mediumslateblue",show_plot=True):
        """
        generates a plot of the tree structure
        :param mode: 'detailed' or 'aggregate'
        :param param_name: name of the production function parameter to search for (default 'sigma', i.e. elasticity)
        :param nodecolor: color of the nodes of the tree 
        :param show_plot: if True, window opens. if False, figure is returned only

        :return fig: matplotlib figure

        """

        t = None
        d = 0
        root = None

        if mode == "aggregate":

            t = self.tree.tree
            d = self.depth - 1
            root = self._root

        elif mode == "detailed":
            t = self.detailed_tree.tree
            d = self.detailed_depth - 1
            root = self._detailed_root

        else:
            raise (KeyError("Can not find plotting mode. Allowed are 'detailed' or 'aggregate'"))

        # t2 = nx.dfs_tree(t, source=root, depth_limit=d)

        #G = nx.Graph()
        #G.add_nodes_from(t)
        ##pos = full_tree_pos(G)
        
        #plt.show()

        #plt.figure(figsize=(7, 5))
        #pos = full_tree_pos(t) # spring_layout(t) # , prog='dot')
        #nx.draw(t, pos, node_size=25, with_labels=with_labels, arrows=True, node_color='gray')
        #nx.draw(G, pos=pos, with_labels=True)
        #plt.show()


        """
        new plotting script
        """

        #print(self.data)
        coords,linedata = tree_to_coords(self.data)
        #print(coords)

        ymin = 0
        xmax = 0

        x_vals = []
        y_vals = []

        y = 1

        dxlabel = 2
        n = 0

        old_point = None
        old_point_2 = None
        rec_old = 0

        fig = plt.figure(figsize=(3.5,4.5))
        
        for line_i in linedata:

            #print("LINE",line_i)
            
            y -= 1
        
        y = 0

        for coords_i in coords:
            #print("COORDS",coords_i)

            label, x, rec, isleaf= coords_i

            x_vals.append(x)
            y_vals.append(y)

            plt.annotate(label.split(";")[0],(x+dxlabel,y))


            if len(label.split(";")) > 1:
                params = self.production_dict[label.split(";")[1]]

                if param_name in params:
                    plt.annotate(str(params[param_name]),(x+dxlabel,y-.8),color="gray")
                else:
                    plt.annotate(str(params),(x+dxlabel,y-.8),color="gray")
                
        
            xmax = max(xmax,x)
            ymin = min(ymin,y)
            
            y -= 1
        
        plt.scatter(x_vals,y_vals,color=nodecolor)

        for i in range(len(x_vals)):
            
            a = x_vals[i]-30 

            while a >= 0:
                plt.plot([x_vals[i]-a-30,x_vals[i]-a-30],[y_vals[i],y_vals[i]+1],"--",color="gray",alpha=.5)

                a-= 30
            

            if y_vals[i] != 0:
                plt.plot([x_vals[i]-30,x_vals[i]-30],[y_vals[i],y_vals[i]+1],color="black")
                plt.plot([x_vals[i]-30,x_vals[i]],[y_vals[i],y_vals[i]],color="black")

            
            

        # plt.ylim([ymin,0])
        # plt.xlim([0,xmax])
        plt.axis("off")
        plt.tight_layout()
        
        if show_plot:
            plt.show()
        
        return fig 


        # print(root.children)



    def traverse(self, subject, direction="up"):
        """
        traverse the tree struct and execute production nodes
        on the way. -> Breadth-first search

        :param subject: the subject carried with the traversal signal
        :param direction: the direction of the trigger signal (traversal is as in nx.bfs)
        """

        for u, v in self.detailed_tree.tree.edges:  # iterate through all edges and trigger handlers

            if direction == "up":
                v.trigger(subject, u)

            elif direction == "down":
                u.trigger(subject, v)

            else:
                raise ValueError(direction)

    def init_nodes(self, subject):
        """
        send production_dict to the nodes for initialization

        :param subject: subject for initalization trigger
        """

        for agent in self.detailed_tree.tree.nodes:
            upstream_suppliers = [x[1] for x in self.detailed_tree.tree.out_edges(agent)]
            agent.trigger(subject, upstream_suppliers, self.production_info[agent])

    def traverse_nodes(self, subject):
        """
        traverse the tree struct nodes
        
        :param subject: the subject carried with the traversal signal
        """

        for agent in self.detailed_tree.tree.nodes:
            agent.trigger(subject)
