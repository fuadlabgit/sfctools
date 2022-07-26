__version__ = "0.3"
__author__ = "Thomas Baldauf"
__email__ = "thomas.baldauf@dlr.de"
__license__ = "MIT"
__birthdate__ = '15.11.2021'
__status__ = 'dev' # options are: dev, test, prod


from sfctools import SingletonAgent, Settings, World, BalanceEntry
from .transactions import gov as transactions_government


class Government(SingletonAgent):
    """
    The government agent consumes 
    """

    def __init__(self):
        """
        constructor for the government
        """
        super().__init__(alias="Government") # there is only one household
        
        self.G = Settings().get_hyperparameter("G")
        self.production = None 

    def link(self):
        """
        Links the government to the production agent
        """
        self.production = World().get_agents_of_type("Production")[0]

    def reset(self):
        """
        Resets the agent for the next simulation period
        """
        self.income_statement.reset()

    def update(self):
        """
        Updates the government
        """

        with self.balance_sheet.modify:

            self.balance_sheet.change_item("Cash",BalanceEntry.ASSETS,self.G)
            # print new money
            self.balance_sheet.change_item("Equity",BalanceEntry.EQUITY,self.G)
            # print new money
        
        # transfer government expenditure to production agent 
        transactions_government(self,self.production,self.G) 
    
    def file_bankruptcy(self,event):
        # print money if bankrupt 

        cb = -self.cash_balance

        with self.balance_sheet.modify:

            self.balance_sheet.change_item("Cash",BalanceEntry.ASSETS,cb) # print new money
            self.balance_sheet.change_item("Bonds",BalanceEntry.EQUITY,cb) # print new money
        

