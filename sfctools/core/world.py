__version__ = "0.3"
__author__ = "Thomas Baldauf"
__email__ = "thomas.baldauf@dlr.de"
__license__ = "MIT"
__birthdate__ = '15.11.2021'
__status__ = 'prod' # options are: dev, test, prod

from ..datastructs.collection import Collection
from .clock import Clock
from .singleton import Singleton
import warnings
import pandas as pd
import matplotlib.pyplot as plt
# from ..misc.mpl_plotting import matplotlib_barplot,matplotlib_lineplot
from ..core.custom_warnings import warning_on_one_line
import sys
import gc

class World(Singleton):
    """
    This is the world where agents live in. There can only be one world at a time.
    """

    """
    # TODO for the future
    # TODO employ a world.plot() method to get a graph view (or multiple graph views) of the world with networkx(?)
    # TODO world info printer (number of agents, current time (clock status), stocks,...)

    """

    def __init__(self):
        """
        The world constructor.
        """

        if hasattr(self, "initialized"):  # only initialize once
            return
        self.initialized = True

        self.agent_registry = Collection(kind="list")  # register the agents in a data structure
        self.helper_registry = Collection(kind="list") # register the helper structures here

        self.globals = {} # globally accessible data here
        self.agent_types = []

        warnings.formatwarning = warning_on_one_line


    def get_agent_types(self):
        """
        Constructs a list of all agent types registered so far (i.e. keys of agent registry dict).

        :return list: list of agents
        """
        return list(set(self.agent_types))

    def link(self):
        """
        Calls the 'link' fun in all the agents to inter-link them in the world
        """
        pool_a = list(self.helper_registry.values())
        pool_b = list(self.agent_registry.values())

        for agent_list in pool_a + pool_b:
            for agent in list(set(agent_list)):
                if hasattr(agent,"link"):
                    if callable(getattr(agent, "link")):
                        agent.link()
                    else:
                        warnings.warn("WORLD LINK: Link attr of %s is not callable. Skipping..." % str(agent))
                else:
                    pass # NOTE it is ok if it has no link attr

    def reset(self):
        """
        resets the registry
        """

        warnings.warn("WORLD RESET - deleting all agents.")

        for agent_list in self.agent_registry.values():
            for agent in agent_list:
                try:
                    self.remove_agent(agent)
                    del agent
                except Exception as e:
                    warnings.warn(str(e))


        for elements in self.helper_registry.values():
            for element in elements:
                try:
                    self.remove_helper(element)
                    del element
                except Exception as e:
                    warnings.warn(str(e))

        self.agent_registry = Collection(kind="list")   # register the agents in a data structure
        self.helper_registry = Collection(kind="list")  # register the helpers in a data structure

        clock = Clock()
        if clock is not None:
            clock.reset()

        gc.collect()

    def register_agent(self, agent, verbose=False):
        """
        inserts a new agent under the tag of its class

        :param agent: an agent object to be registered
        """
        if verbose:
            print("[WORLD] Reigster Agent %s of class %s " % (agent,agent.__class__))
        self.agent_types.append(agent.__class__)  # append new key if doesnt exist yet
        self.agent_registry.insert(agent.__class__.__name__, agent)  # write new agent to data structure

    def register_helper(self, object):
        """
        inserts a new helper object under the tag of its class

        :param object: instance to store
        """
        self.helper_registry.insert(object.__class__.__name__, object) # write new object

    def find_agent(self,name):
        """
        search for agent by name and alias

        :return: agent instance
        """

        for agent_list in self.agent_registry.values():
            for agent in agent_list:
                if agent.name == name or agent.alias == name:
                    return agent

        return None

    def remove_agent(self, agent, verbose=False):
        """
        removes an agent from the tag of its class (i.e. from the world)

        :param agent: instance to be removed
        """
        if verbose:
            print("[WORLD] Remove Agent %s of class %s " % (agent, agent.__class__))
        self.agent_types.remove(agent.__class__)
        self.agent_registry.remove(agent.__class__.__name__, agent)  # remove the agent from the tag
        del agent  # delete the instance to assure proper removal of the agent

    def remove_helper(self, agent):
        """
        removes an agent from the tag of its class (i.e. from the world)

        :param agent: instance to be removed
        """
        #self.agent_types.remove(agent.__class__)
        self.helper_registry.remove(agent.__class__.__name__, agent)  # remove the agent from the tag
        del agent  # delete the instance to assure proper removal of the agent

    def write_global(self,key,data):
        """
        write globally accessible data here

        :param key: key for the data (generic)
        :param data: value of the data (generic)
        """
        self.globals[key] = data

    def read_global(self,key):
        """
        reads global variable by key
        """
        return self.globals[key]

    def get_agents_of_type(self,agent_type):
        """
        gets all agents belonging to a certain tpe

        :param agent_type: key to search for in self.agent_registry
        :return: list of instances or empty list

        Example

        .. code-block:: python

            from sfctools import Agent,World

            class MyAgent(Agent):
                def __init__(self):
                    super().init()
                    # ...

            [MyAgent() for i in range(10)] # create 10 agents

            mylist = World().get_agents_of_type("MyAgent")
            print(mylist)

        """

        return self.agent_registry[agent_type]

    # DEPRECIATED - MOVED TO plotting and reporting ...
    #def plot_statistics(self,agents,attribute):
    #    """
    #    plots distributions of agents (BETA)#
    #
    #    :param agents: a list of agents
    #    :param attribute: attribute to plot
    #    """#
    #
    #    warnigns.warn("Warning: Beta feature 'plot_statistics' was called")#
    #
    #    data = {"i": range(len(agents)), "w": [getattr(a,attribute) for a in agents]}
    #    df = pd.DataFrame(data).set_index("i")
    #    matplotlib_lineplot(df, "Agent index", attribute, "",legend="off")
    #    plt.show()
