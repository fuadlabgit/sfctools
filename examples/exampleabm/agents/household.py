__version__ = "0.3"
__author__ = "Thomas Baldauf"
__email__ = "thomas.baldauf@dlr.de"
__license__ = "MIT"
__birthdate__ = '15.11.2021'
__status__ = 'dev' # options are: dev, test, prod


from sfctools import SingletonAgent, Settings, World
from sfctools import BalanceEntry

from .transactions import con as transaction_consumption 


class Household(SingletonAgent):
    """
    The household agent consumes 
    """

    def __init__(self):
        """
        Constructor for the household
        """
        super().__init__(alias="Household") # there is only one household

        self.C = 0.8  # initial consumption 
        self.DI = 0.0 # initial disposable income 

        self.alpha1 = Settings().get_hyperparameter("alpha1")
        self.alpha2 = Settings().get_hyperparameter("alpha2")

        self.production = None # <- placeholder for production agent 
    

    def link(self):
        """
        Links the household agent with the production agent 
        """
        self.production = World().get_agents_of_type("Production")[0]

        # equip household with some initial net worth 
        with self.balance_sheet.modify:
            self.balance_sheet.change_item("Cash",BalanceEntry.ASSETS, 25.0, suppress_stock=True)
            self.balance_sheet.change_item("Equity",BalanceEntry.EQUITY, 25.0,suppress_stock=True)

        # equip household with some initial net worth 
        with self.balance_sheet.modify:
            self.balance_sheet.change_item("Cash",BalanceEntry.ASSETS, 25.0, suppress_stock=True)
            self.balance_sheet.change_item("Bonds",BalanceEntry.LIABILITIES, 25.0,suppress_stock=True)

    def reset(self):
        """
        Resets the agent for the next simulation period
        """
        self.income_statement.reset()
    
    def update(self):
        """
        Updates the household agent
        """
        
        #print(self.balance_sheet.to_string())

        
        # retrieve wealth and income
        wealth = self.net_worth 
        income = self.income_statement.net_income

        self.DI = wealth+ income  # disposable income 

        # consumption 
        self.C = self.alpha1 * income + self.alpha2 * wealth

        # do the actual transaction
        transaction_consumption(self,self.production,self.C)
