__version__ = "0.3"
__author__ = "Thomas Baldauf"
__email__ = "thomas.baldauf@dlr.de"
__license__ = "MIT"
__birthdate__ = '15.11.2021'
__status__ = 'prod' # options are: dev, test, prod

from collections import defaultdict
import pandas as pd
import warnings
from .singleton import Singleton
from enum import Enum
from .world import World
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
from ..misc.mpl_plotting import plot_sankey

class Accounts(Enum):
    """
    Enum for account type in flow matrix. Current and capital account is allowed
    """
    KA = 0 # capital account
    CA = 1 # current account


class FlowMatrix(Singleton):
    """
    The flow matrix takes care of the flows between agents and the stock-flow consistency. It has the following structure:
    

+--------------------------------------------------------------------------------------+
| Flow Matrix                                                                          |
+===============+=========================+==================================+=========+
|               |     Agent 1             |           Agent 2                |  TOTAL  |
+---------------+-----------+-------------+----------------+-----------------+---------+
|               |     CA    | KA          |           CA   | KA              |         |
+---------------+-----------+-------------+----------------+-----------------+---------+
|               |           |             |                |                 |         |
| Flows         |    -x     |             |                |  +x             |   0     |
+---------------+-----------+-------------+----------------+-----------------+---------+
|               |           |             |                |                 |         |
| d(Stocks)     |     +x    |             |                |  -x             |   0     |
+---------------+-----------+-------------+----------------+-----------------+---------+
| TOTAL         |     0     |  0          |            0   |    0            |   0     |
+---------------+-----------+-------------+----------------+-----------------+---------+

    | CA: Current Account, KA: Capital Account.

    As a consistency check, the sum of rows and columns should be zero after the end of each simulation period. 
    For more information, see

- Investopedia Article https://www.investopedia.com/ask/answers/031615/whats-difference-between-current-account-and-capital-account.asp
- A nice introduction by Gasselli (OECD) https://www.oecd.org/naec/new-economic-policymaking/grasselli_OECD_masterclass_2019.pdf
    
    """
    
    reset_count = 0

    def __init__(self):
        # constructor of the flow matrix 

        if hasattr(self, "initialized"):  # only initialize once 
            return
        
        self.initialized = True # initialized flag 
        
        # TODO replace above code with 'if self.do_init:' check? 
        # TODO Keeping it for now because it works...
        
        self._flow_data = {}  # has two keys CA and KA, see reset()...
        self.reset()  # defaultdict will take care of missing keys here
        self.linear_log = [] # linear transaction log
    
    def reset(self):
        """
        reset the data
        """
        
        self._flow_data[Accounts.CA] = defaultdict(lambda: defaultdict(float))
        self._flow_data[Accounts.KA] = defaultdict(lambda: defaultdict(float))
        
        if self.__class__.reset_count > 1:
            
            # warn the user every time this is being reset!
            warnings.warn("FlowMatrix has been reset") 
        
        else:
            self.__class__.reset_count += 1 
        
    def log_flow(self,kind,quantity,agent_from,agent_to,subject,price=None,invert=False):
        """
        Registers a flow at the flow matrix. This is no method for the user in most cases. It is automatically generated in the qattune gui.

        :param kind: tuple (from_account,to_account)
        :param quantity: weight (quantity) of the flow
        :param price: float or None (default). If not None, a price conversion factor is applied. Should not be used in most cases
        :param invert: reverse sign of the transferred quantity? Default False, should not be used in most cases
        :param agent_from: Agent instance (optionally str), sender agent
        :param agent_to: Agent instnace (optionally str), receiver agent

        Example

        .. code-block:: python

            from sfctools import FlowMatrix, Accounts
            CA = Accounts.CA
            KA = Accounts.KA

            flow = (CA,KA) # from account -> to account
            FlowMatrix().log_flow(flow, 42.0, agent1, agent2, subject="my_subject")
            # ...
            
            df = FlowMatrix().to_dataframe(group=True)
            print(FlowMatrix().to_string(group=True))
            FlowMatrix().check_consistency() # ok if no error is raised

        """

        if price is not None:
            Q = quantity * price
        else:
            Q = quantity

        if invert:
            Q = - Q

        from_account = kind[0] 
        to_account = kind[1]

        self._flow_data[from_account][subject][agent_from]-= Q
        self._flow_data[to_account][subject][agent_to] += Q

    def check_consistency(self):
        """
        Checks the consistency of the flow matrix (i.e.)

        NOTE is slow because of pandas dataframe usage. Do not call often, do not call in excessive for-loops
        TODO test this
        """

        df = self.to_dataframe(group=True)

        if df.empty:
            return

        if not df.empty:
            null_sym = "   .-   "

            # avoid numerical errors
            # so round to at max 4 orders of magntude less than max order of magnitude

            df2 = df.replace(null_sym,0.0).astype(float)
            om_max = int(np.ceil(np.log10(df2.to_numpy().max())))
            om_min = int(np.ceil(np.log10(abs(df2.to_numpy().min()))))
            order_magnitude = max(om_max,om_min)
            df2 = df2.round(-order_magnitude + 4)

            if np.array(df2["Total"]).any():
                raise RuntimeError("Inconsistent Row In Flow Sheet: \n%s" % df.to_string())

            df3 = df2.T
            if np.array(df3["Total"]).any():
                raise RuntimeError("Inconsistent Column In Flow Sheet:\n %s" % df.to_string())

    def to_string(self,group=True):
        """
        converts the flow matrix to string representation
        :return : str
        """
        return self.to_dataframe(group=group).to_string()

    def to_dataframe(self,group =True,insert_nullsym=True):
        """
        Converts the data structure to a human-readable dataframe format.
        WARNING this is slow

        :param group: boolean switch (default True), if True it will group the agents of the same class together
        :param insert_nullsym: will insert '.-' symbol instead of zero, default True
        :return: pandas dataframe object
        """

        df_credit  = pd.DataFrame(self._flow_data[Accounts.CA]).T
        df_capital = pd.DataFrame(self._flow_data[Accounts.KA]).T

        df_merge = pd.concat([df_credit, df_capital], axis=1, keys=['CA', 'KA']).swaplevel(0,1,axis=1).sort_index(axis=1)

        df = df_merge.fillna(0.0).sort_index()

        agent_types = World().get_agent_types()

        if not group:

            df.loc["Total"] = df.sum()
            df["Total"] = df.T.sum()
            return df.round(4)

        else:
            """
            Provide an overview with aggregated classes
            """

            data = {}
            renamer = {}
            for a in agent_types:
                my_group = []
                for b in df.columns:
                    # print("b",b,"a",a,b[0])
                    if isinstance(b[0],a):
                        my_group.append(b[0])

                if len(my_group) > 0:
                    my_df = df.loc[:,df.columns.get_level_values(0).isin(my_group)]
                    my_CA = my_df.loc[:,my_df.columns.get_level_values(1).isin({"CA"})].sum(axis=1)
                    my_KA = my_df.loc[:,my_df.columns.get_level_values(1).isin({"KA"})].sum(axis=1)

                    concat =  pd.concat([my_CA, my_KA], axis=1, keys=['CA', 'KA'])

                    data[a] = concat

                if len(my_group) > 1:
                    plural_suffix = ""

                    if len(World().get_agents_of_type(a.__name__))> 1:
                        plural_suffix = "s"

                    renamer[a] = a.__name__ + plural_suffix
                else:
                    renamer[a] = a.__name__

            if data == {}:
                return pd.DataFrame()

            df2 = pd.concat(data, axis=1)

            df2 = df2.rename(columns=renamer).sort_index()

            # df2 = df2.round(4)

            df2.loc["Total"] = df2.sum()
            df2["Total"] = df2.T.sum()

            df2 = df2.round(5) 
            df2 = df2.round(4) # cut one digit to obtain a 'consistently rounded table' 

            
            if insert_nullsym:
                null_sym = "   .-   "
                df2 = df2.replace(0.0,null_sym)

            df2 = df2.reindex(sorted(df2.columns), axis=1)

            cols = list(df2.columns.values) #Make a list of all of the columns in the df
            #print("COLS",cols)
            cols.pop(cols.index(("Total",""))) #Remove Total from list
            df2 = df2[cols+[("Total","")]] #Create new dataframe with columns in the order you want
            
            return df2

    def plot_colored(self,show_plot=True,group=True):
        """
        Plots the flow matrix as a nice colored heat map.
        This will open up a matplotlib window...

        :param show_plot: show the plot as window? default True. If False, figure is returned instead
        :param group: aggregated view?
        :return fig: figure object
        """

        # TODO nicer formatting
        # TODO more plotting options 

        df = self.to_dataframe(insert_nullsym=False,group=group)
        
        fig = plt.figure(figsize=(9,5))
        sns.heatmap(df, annot=True ,cmap='coolwarm',)
        ax = plt.gca()
        ax.set_ylabel('')    
        ax.set_xlabel('')

        plt.tight_layout()
        if show_plot:
            plt.show()  

        return fig 

    def plot_sankey(self,show_values=True, show_plot=True):
        """
        plots a sankey diagram of the flow matrix

        :param show_values: boolean switch to plot the values of the edge weights
        :param show_plot: show the plot as window? default True. If False, figure is returned instead.
        :return fig: figure object
        """
        df = FlowMatrix().to_dataframe(insert_nullsym=False)

        df_CA = df.iloc[:, df.columns.get_level_values(1)=='CA']
        df_CA.columns = df_CA.columns.droplevel(1) # current account

        df_KA = df.iloc[:, df.columns.get_level_values(1)=='KA'] # capital account 
        df_KA.columns = df_KA.columns.droplevel(1) 

        source  = []
        target = []
        types = []
        value = []

        source2  = []
        target2 = []
        types2 = []
        value2 = []

        subjects = {}
        for i,k in enumerate(df.index):
            subjects[str(k)] = i 
        
        for i, df_i in enumerate([df_CA,df_KA]):
                
            for index, row in df_i.iterrows():
                
                for column in df_i.columns:
                    
                    val = float(row[column])
                    if val < 0.0 and index != "Total" and (not index.startswith("Δ")): # is a source
                        source.append(str(column)+ " source")
                        target.append(str(index) )    
                        value.append(-val)
                        types.append(subjects[str(index)])

                    elif val > 0.0 and index != "Total" and (not index.startswith("Δ")): # is a sink
                        source2.append(str(column) + " sink")
                        target2.append(str(index) )    
                        value2.append(val)
                        types2.append(subjects[str(index)])
                        
        my_sankey_source = pd.DataFrame({"from":source,
                                  "to":target,
                                  "color_id":types,
                                  "value":value}).round(2)
        my_sankey_sink =  pd.DataFrame({"to":source2,
                                  "from":target2,
                                  "color_id":types2,
                                  "value":value2}).round(2)

        fig = plot_sankey([my_sankey_source,my_sankey_sink],show_values=show_values,show_plot=show_plot)
        return fig 

        
    @property
    def capital_flow_data(self):
        """'shortcut' property. only returns the data from the capital account"""
        return self._flow_data[Accounts.KA]

    @property
    def current_flow_data(self):
        """'shortcut' property. only returns the dta fromt he current flow account"""
        return self._flow_data[Accounts.CA]
