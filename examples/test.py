__version__ = "0.3"
__author__ = "Thomas Baldauf"
__email__ = "thomas.baldauf@dlr.de"
__license__ = "MIT"
__birthdate__ = '15.11.2021'
__status__ = 'dev' # options are: dev, test, prod


from sfctools import Agent , BalanceEntry

class MyAgent(Agent):


    def __init__(self):

        super().__init__()

        with self.balance_sheet.modify:
            self.balance_sheet.change_item("Cash", BalanceEntry.ASSETS, 10.0)
            self.balance_sheet.change_item("Equity", BalanceEntry.EQUITY, 10.0)


my_agent = MyAgent()

print(my_agent.balance_sheet.to_string())