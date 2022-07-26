__version__ = "0.3"
__author__ = "Thomas Baldauf"
__email__ = "thomas.baldauf@dlr.de"
__license__ = "MIT"
__birthdate__ = '15.11.2021'
__status__ = 'prod' # options are: dev, test, prod

import numpy as np
from collections import defaultdict
import pandas as pd
import copy
from enum import Enum

class ICSEntry(Enum):
    """
    Enum for income sheet entry (ICSEntry). Explanation: see IncomeStatement class
    """
    REVENUES = 0
    GAINS = 1
    EXPENSES = 2
    LOSSES = 3
    NONTAX_PROFITS = 4
    NONTAX_LOSSES = 5
    INTEREST = 6
    TAXES = 7
    NOI = 8


class IncomeStatement:
    """
    Income statement data structure. Consist of the following entries:

+------------------------------------+------------------------------------------------------------------------------+
| Income Statement                   |  Example / Description                                                       |
+===========================+========+===========+==================================================================+
|  Revenues and Gains       |                    |   Money a company actually receives during a specific period     |
|                           |                    |                                                                  |
+---------------------------+--------------------+------------------------------------------------------------------+
|                           |   Tag  |    Value  |     interest on deposits, sales                                  |
+---------------------------+--------------------+------------------------------------------------------------------+
|                           |   Tag  |    Value  |                                                                  |
+---------------------------+--------------------+------------------------------------------------------------------+
|                           |   Tag  |    Value  |                                                                  |
+---------------------------+--------------------+------------------------------------------------------------------+
|                           |   Tag  |    Value  |                                                                  |
+---------------------------+--------------------+------------------------------------------------------------------+
|  Expenditures and Losses  |                    |      wages                                                       |
|                           |   Tag  |    Value  |                                                                  |
+---------------------------+--------------------+------------------------------------------------------------------+
|                           |   Tag  |    Value  |                                                                  |
+---------------------------+--------------------+------------------------------------------------------------------+
|  Gross (Before-Tax)       |                    |                                                                  |
|                           |   Tag  |    Value  |                                                                  |
+---------------------------+--------------------+------------------------------------------------------------------+
| ...                       |                    |                                                                  |
+---------------------------+--------------------+------------------------------------------------------------------+
|  Interest Payments        |                    |  interst on loans                                                |
|                           |   Tag  |    Value  |                                                                  |
+---------------------------+--------------------+------------------------------------------------------------------+
| ...                       |                    |                                                                  |
+---------------------------+--------------------+------------------------------------------------------------------+
|   inter                   |                    |    interest payments                                             |
|   NOI                     |                    |    non-operating income                                          |
+---------------------------+--------------------+------------------------------------------------------------------+
|   Tax                     |                    |    taxes (e.g. on income) paid                                   |
|   paid                    |                    |                                                                  |
+---------------------------+--------------------+------------------------------------------------------------------+
|                           |                    |                                                                  |
|   Non-Taxable             |                    |    untaxed profits and losses                                    |
+---------------------------+--------------------+------------------------------------------------------------------+
|   After-                  |                    |                                                                  |
|   tax income              |                    |                                                                  |
+---------------------------+--------------------+------------------------------------------------------------------+
    
    
    see also https://www.investopedia.com/terms/i/incomestatement.asp#revenues-and-gains
    
    """

    def __init__(self, owner,data=None,tot_dict=None,total_spendings=0.0):
        """
        Constructs a new income statement. 

        :param owner: Agent instance. The owner of this income statement.
        :param data: default None, can be used to pre-initialize income sheet with data. Should not be used in most cases (two-fold dict data[kind:ICSEntry][tag:str]) 
        :param tot_dict: default None, can be used to pre-initialize income sheet with data. Should not be used in most cases (two-fold dict tot_dict[kind:ICSEntry][tag:str]). Saves 'total' row of the sheet.
        :param total_spendings: depreciated, to not used
        """

        self.owner = owner
        self.data = data
        self.tot_dict = tot_dict
        self.last = self  # stores income statement of previous period
        self.total_spendings = 0.0 # TODO < logic behind this? Probably depreciated... # TODO safely delete

        self.restore()
    
    #@property
    #def taxable_income(self):
    #    """ agi + int - noi
    #     adj. gross income + interest - non-operating income
    #    """
    #    return self.gross_income - self.tot_dict[ICSEntry.INTEREST] +\
    #           self.tot_dict[ICSEntry.NOI]

    @property
    def gross_income(self):
        """agi"""
        return self.tot_dict[ICSEntry.REVENUES]\
               + self.tot_dict[ICSEntry.GAINS]\
               - self.tot_dict[ICSEntry.EXPENSES]\
               - self.tot_dict[ICSEntry.LOSSES]
    
    @property
    def noi(self):
        """ non-operational income"""
        return self.tot_dict[ICSEntry.NOI]
    
    @property
    def ebit(self):
        """earnings before interest and tax"""
        return self.gross_income\
               + self.tot_dict[ICSEntry.NONTAX_PROFITS]\
               - self.tot_dict[ICSEntry.NONTAX_LOSSES]\
               + self.noi
    
    @property
    def int(self):
        """interest expenditure (absolute value)"""
        return self.tot_dict[ICSEntry.INTEREST]

    @property
    def ebt(self):
        """earnings before tax (and after interest)"""
        return self.ebit - self.int

    @property
    def tax(self):
        """taxes"""
        return self.tot_dict[ICSEntry.TAXES]

    @property
    def net_income(self):
        """eranings after tax (and after interest)"""
        return self.ebt - self.tax

    @property
    def gross_spendings(self):
        """expenses + losses"""
        return self.tot_dict[ICSEntry.EXPENSES] + self.tot_dict[ICSEntry.LOSSES]
    
    @property
    def spendings(self):
        """expenses + losses + taxes + interest"""
        return self.tot_dict[ICSEntry.EXPENSES] + self.tot_dict[ICSEntry.LOSSES] + self.tot_dict[ICSEntry.TAXES] +\
                self.tot_dict[ICSEntry.INTEREST]

    def get_entry(self,kind,tag):
        """
        get an specific entry of the income statement

        :param kind: BalanceEntry, which entry to look up
        :param tag: str, tag of the specific row
        """
        return self.data[kind][tag]

    def new_entry(self, kind, tag, value):
        """
        Registers a new item in the income statement

        :param kind: kind of entry: Revnue, Gain, Expense, Loss or Tax
        :param tag: a name, e.g. 'interest on deposits'
        :param value: nominal value of the entry

        Example:

        .. code-block:: python

            from sfctools import Agent, ICSEntry

            a = Agent()
            ics = a.income_statement
            # ics.new_entry(kind,tag,value)
            ics.new_entry(ICSEntry.EXPENSES, "Vacation", 1000.0)
            # ...
            ics.reset()
        """ 
        
        if type(kind) == str:
            # THIS IS SLOW and should be avoided
            # introduce warning in version 0.3

            lookup = {"Revenue": ICSEntry.REVENUES,
                      "Gain": ICSEntry.GAINS,
                      "Expense": ICSEntry.EXPENSES,
                      "Loss": ICSEntry.LOSSES,
                       "Interest": ICSEntry.INTEREST,
                       "Non-Op. Income": ICSEntry.NOI,
                       "Tax": ICSEntry.TAXES,
                       "Nontax. Profit": ICSEntry.NONTAX_PROFITS,
                       "Nontax. Loss": ICSEntry.NONTAX_LOSSES
                       }

            if kind in lookup:
                kind = lookup[kind]
            else:
                error = KeyError("Passed wrong kind of income entry key. Allowed keys are %s" % str(list(lookup.values())))
                raise error

        # self.data[plural[kind]][tag] += value
        # self.tot_dict[plural[kind]] += value
        # print("NEW ENTRY", kind, tag, value, self.tot_dict)

        assert type(kind) == ICSEntry, "Passed wrong kind %s but should be %s"% (type(kind), ICSEntry)
        # ^this is indeed an error, no warning

        self.data[kind][tag] += value
        self.tot_dict[kind] += value

    def restore(self):
        """
        Restore an all-zero income statement
        """
        self.data = {ICSEntry.REVENUES: defaultdict(lambda: 0.0),
                     ICSEntry.GAINS: defaultdict(lambda: 0.0),
                     ICSEntry.EXPENSES: defaultdict(lambda: 0.0),
                     ICSEntry.LOSSES: defaultdict(lambda: 0.0),
                     ICSEntry.INTEREST: defaultdict(lambda: 0.0),
                     ICSEntry.NOI: defaultdict(lambda: 0.0),
                     ICSEntry.TAXES: defaultdict(lambda: 0.0),
                     ICSEntry.NONTAX_PROFITS: defaultdict(lambda: 0.0),
                     ICSEntry.NONTAX_LOSSES: defaultdict(lambda: 0.0)
                     }

        self.tot_dict = {
            ICSEntry.REVENUES: 0.0,
            ICSEntry.GAINS: 0.0,
            ICSEntry.EXPENSES: 0.0,
            ICSEntry.LOSSES: 0.0,
            ICSEntry.INTEREST: 0.0,
            ICSEntry.NOI:0.0,
            ICSEntry.TAXES: 0.0,
            ICSEntry.NONTAX_PROFITS: 0.0,
            ICSEntry.NONTAX_LOSSES: 0.0
        }

    def reset(self):
        """
        Reset routine. Remove data and start a new, blank income statement for the next period.
        Saves current state in "last".
        """
        self.last = IncomeStatement(owner=self.owner,data=self.data,tot_dict=self.tot_dict,total_spendings=self.total_spendings) # < TODO test this properly
        self.restore()

    def to_dataframe(self):
        """
        Converts the data structure of the income sheet to human-readable pandas dataframe format.
        :return: pandas dataframe

        """
        idx = "Value"

        keys = []

        df_revenues = pd.DataFrame(self.data[ICSEntry.REVENUES], index=[idx]).T
        df_gains  =   pd.DataFrame(self.data[ICSEntry.GAINS], index=[idx]).T
        df_expenses = pd.DataFrame(self.data[ICSEntry.EXPENSES], index=[idx]).T.multiply(-1)
        df_losses =   pd.DataFrame(self.data[ICSEntry.LOSSES], index=[idx]).T.multiply(-1)
        df_total = pd.DataFrame({"Total": self.gross_income}, index=[idx]).T
        df_interest = pd.DataFrame(self.data[ICSEntry.INTEREST], index=[idx]).T
        df_noi = pd.DataFrame(self.data[ICSEntry.NOI], index=[idx]).T
        df_taxes = pd.DataFrame(self.data[ICSEntry.TAXES], index=[idx]).T.multiply(-1)
        df_nontaxable_profits = pd.DataFrame(self.data[ICSEntry.NONTAX_PROFITS], index=[idx]).T
        df_nontaxable_losses = pd.DataFrame(self.data[ICSEntry.NONTAX_LOSSES], index=[idx]).T.multiply(-1)
        df_net = pd.DataFrame({"Total": self.net_income}, index=[idx]).T

        frames = [df_revenues,df_gains,df_expenses,df_losses,
                  df_total,df_interest,df_noi,
                  df_taxes,df_nontaxable_profits,
                  df_nontaxable_losses,df_net]

        df = pd.concat(frames,keys=["Revenues","Gains","Expenses","Losses","Gross Income",
                                     "Interest","Non-Operating Income","Taxes","Nontaxable Profits",
                                     "Nontaxable Losses","Net Income"])

        df.index.names = ["Income statement of %s" %self.owner,""]
        return df

    def to_string(self):
        """
        String representation of the income sheet. This will first convert to pandas dataframe, then to string.
        :return: str
        """
        return  "\n\n" + self.to_dataframe().to_string() + "\n\n"

