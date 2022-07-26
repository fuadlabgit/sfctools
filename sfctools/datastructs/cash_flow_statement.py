__version__ = "0.3"
__author__ = "Thomas Baldauf"
__email__ = "thomas.baldauf@dlr.de"
__license__ = "MIT"
__birthdate__ = '15.11.2021'
__status__ = 'dev' # options are: dev, test, prod

import numpy as np
from collections import defaultdict
import pandas as pd

from enum import Enum

class CashFlowEntry(Enum):
    """
    these are the different entry types
    """
    OPERATING = 0
    FINANCING = 1
    INVESTING = 2


class CashFlowStatement:
    """
    Cash flow statement data structure.
    See also https://www.investopedia.com/investing/what-is-a-cash-flow-statement/

    WARNING beta state

    +------------------------------------+
    |    Cash Flow Statement             |
    +===============+====================+
    |  Operating    |                    |
    |  Activities   |                    |
    +---------------+--------------------+
    |               | Net Income | Value |
    +---------------+--------------------+
    |               |   Tag      | Value |
    +---------------+--------------------+
    |               |   Tag      | Value |
    +---------------+--------------------+
    |   TOTAL       |               ...  |
    +---------------+--------------------+
    |  Investing    |                    |
    |  Activities   |                    |
    +---------------+--------------------+
    |               |   Tag  |    Value  |
    +---------------+--------------------+
    |               |   Tag  |    Value  |
    +---------------+--------------------+
    |   TOTAL       |               ...  |
    +---------------+--------------------+
    |  Financing    |                    |
    |  Activities   |                    |
    |               |   Tag  |    Value  |
    +---------------+--------------------+
    |               |   Tag  |    Value  |
    +---------------+--------------------+
    |   TOTAL       |               ...  |
    +---------------+--------------------+


    """

    def __init__(self, owner):
        """
        instaniates a new cash flow statement

        :param owner: owner instance this cash flow statement belongs to.
        """

        self.owner = owner
        self.data = None
        self.tot_dict = None
        self.reset()

    @property
    def total_cash_flow(self):
        """
        returns total cashflow, i.e. operating plus financing plus investing
        """
        return self.tot_dict[CashFlowEntry.OPERATING]  + self.tot_dict[CashFlowEntry.FINANCING] + self.tot_dict[CashFlowEntry.INVESTING]

    @property
    def operating_cash_flow(self):
        """
        returns only operating part of the cash flow
        """
        return self.tot_dict[CashFlowEntry.OPERATING]

    @property
    def financing_cash_flow(self):
        """
        returns only financing part of the cash flow
        """
        return self.tot_dict[CashFlowEntry.FINANCING]

    @property
    def investing_cash_flow(self):
        """
        returns only investing part of the cash flow
        """
        return self.tot_dict[CashFlowEntry.INVESTING]

    def new_entry(self, kind, tag, value):
        """
        registers a new item in the income statement

        :param kind: kind of entry: Financing, Operating or Investing
        :param tag: a name, e.g. 'interest on deposits'
        :param value: nominal value of the entry

        Example


        .. code-block:: python

            from sfctools import Agent, CashFlowEntry
            a = Agent()
            cfs = a.cash_flow_statement

            kind = CashFlowEntry.FINANCING
            tag = "My Subject"
            value = 10.0

            cfs.new_entry(kind,tag,value)
            print(cfs.to_dataframe())


        """

        self.data[kind][tag] += value
        self.tot_dict[kind] += value

    def reset(self):
        """
        Removes data and starts a new, blank income statement for the next period
        """

        self.data = {CashFlowEntry.OPERATING: defaultdict(lambda: 0.0),
                     CashFlowEntry.FINANCING: defaultdict(lambda: 0.0),
                     CashFlowEntry.INVESTING: defaultdict(lambda: 0.0),
                     }

        self.tot_dict = {
            CashFlowEntry.OPERATING: 0.0,
            CashFlowEntry.FINANCING: 0.0,
            CashFlowEntry.INVESTING: 0.0}

    def to_dataframe(self):
        """
        Converts the data structure to a human-readable pandas dataframe.
        """

        idx = "Value"

        keys = []

        df_operating = pd.DataFrame(self.data[CashFlowEntry.OPERATING], index=[idx]).T
        df_total_op = pd.DataFrame({"Tot. Operating": self.operating_cash_flow}, index=[idx]).T

        df_financing = pd.DataFrame(self.data[CashFlowEntry.FINANCING], index=[idx]).T
        df_total_fin = pd.DataFrame({"Tot. Financing": self.financing_cash_flow}, index=[idx]).T

        df_investing = pd.DataFrame(self.data[CashFlowEntry.INVESTING], index=[idx]).T
        df_total_inv = pd.DataFrame({"Tot. Operating": self.investing_cash_flow}, index=[idx]).T

        df_total = pd.DataFrame({"Total Cash Flow": self.total_cash_flow}, index=[idx]).T

        frames = [df_operating,df_total_op,df_financing,df_total_fin,df_investing,df_total_inv,df_total]

        df = pd.concat(frames,keys=["Operating","Tot. Operating", "Finacing","Tot. Financing","Investing","Tot. Investing","Tot."])

        df.index.names = ["Cash flow statement of %s" %self.owner,""]
        return df

    def to_string(self):
        """
        Converts the cash-flow statement to dataframe and then to string.
        """
        return self.to_dataframe().to_string()
