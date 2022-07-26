__version__ = "0.3"
__author__ = "Thomas Baldauf"
__email__ = "thomas.baldauf@dlr.de"
__license__ = "MIT"
__birthdate__ = '15.11.2021'
__status__ = 'dev' # options are: dev, test, prod


from sfctools import SingletonAgent, Settings, World,Clock
from .transactions import wag as transaction_wages 
from .transactions import tax as transaction_taxes 
import pandas as pd 
import numpy as np


class Production(SingletonAgent):
    """
    The production agent produces a single good Y
    """

    def __init__(self):
        """
        constructor for the production agent
        """
        super().__init__(alias="Production") # there is only one production

        self.Y = 1.0 # initial production level 
        self.W = 1.0 # initial wages
        self.T = 1.0 # initial taxes

        gdp_file = Settings().get_hyperparameter("gdp_change")
        self.Y_change = np.loadtxt(gdp_file) # percentage change of GDP , in percent

        self.theta = Settings().get_hyperparameter("theta")

    def link(self):
        """
        Links the production agent with the household agent and the government agent
        """

        self.household = World().get_agents_of_type("Household")[0]
        self.government = World().get_agents_of_type("Government")[0]

    def reset(self):
        """
        Resets the agent for the next simulation period
        """
        self.income_statement.reset()

    def update(self):
        """
        updates production 
        """       
        # set the wage level for this period
        
        t = Clock().get_time()
        C = self.household.C
        G = self.government.G

        self.W = C + G # update wage level 

        # pay wages 
        wages = (1-self.theta) * self.W
        transaction_wages(self,self.household,wages)

        # pay taxes
        taxes = self.theta * self.W
        self.T = taxes 
        transaction_taxes(self,self.government,taxes) # production pays income taxes of households directly to household

        self.Y = self.W - self.T
        self.Y *= (1+0.01*self.Y_change[t]) 


    def file_bankruptcy(self,event):
        pass