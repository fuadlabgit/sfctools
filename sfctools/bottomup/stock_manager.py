__version__ = "0.3"
__author__ = "Thomas Baldauf"
__email__ = "thomas.baldauf@dlr.de"
__license__ = "MIT"
__birthdate__ = '15.11.2021'
__status__ = 'test' # options are: dev, test, prod

import pandas as pd
import sys 

sys.path.append("..")


from ..core.singleton import Singleton
from ..core.clock import Clock
from ..datastructs.collection import Collection
import numpy as np



class StockManager(Singleton):
    """
    The stock manager keeps track of all price trends. 
    Beta feature...
    """

    def __init__(self):
        """
        constructor of stock manager.
        """

        if hasattr(self, "initialized"):  # only initialize once
            return
        self.initialized = True

        self.hist = Collection(kind="list", maxlen=4096)  # history  logger with maximum length
        self.state = {}        # keys are price index, values are current stock values
        self.abbrev_dict = {}  # keys are commodity name, values are price index names

    def register(self, name: str, price_name: str, price_value: float) -> None:
        """
        run setup routine of stock manager for a new commodity
        
        :param name: name of the commodity  (eg. 'coal')
        :param price_name: name of the price  (e.g. 'P_c')
        :param price_value: actual value of the price, this can also point to a method
        """

        self.abbrev_dict[name] = price_name
        self.state[price_name] = price_value

        self.set_price(price_name,price_value)

    def get_index(self, name_of_commodity: str) -> str:
        """
        retrieve stock index by name of commodity

        :param name_of_commodity: name of the commodity
        """
        return self.abbrev_dict[name_of_commodity]

    def get_price(self, name, human=False):
        """
        see request_price
        """
        self.request_price(name, human)

    def get_most_recent(self, name):
        """
        get the most recent value of a price index
        if there are no values, return None
       
        :return: t, v (time stamp and value of most recent update)
        """

        entries = self.hist.get_entries()
        if name in entries:
            times, values = np.array(entries[name]).T
            return times[-1], values[-1]

        else:
            return None

    def request_price(self, name: str, human: bool = False) -> float:
        """
        Retrieve a price by the name of the index.

        :param name: the name of the commodity, e.g. 'coal'
        :param human: get price by the name of the commodity instead
        :return:  P, value of the price at the stock
        """

        # NOTE: the name of this method is request_price, not get_price because
        # in the future we want to add access rights of agents to certain price indices
        # this could also include fuzzy information propagation or just rejection to access a certain index,
        # possibly at random... so the request might be also denied in the future

        if human:
            key = self.abbrev_dict[name]
        else:
            key = name

        return self.state[key]

    def set_price(self, name: str, value: float, human: bool = False) -> None:
        """
        set a new price by name of the index commodity
        
        :param name:  name of the index to be set
        :param value: new value
        :param human: get price by the name of the commodity instead
        
        """

        # 1. log the old value

        if human:
            key = self.abbrev_dict[name]
        else:
            key = name

        assert key in self.abbrev_dict or key in self.state, "Price index %s not known" % name

        self.hist.insert(key, (Clock().get_time(), value))

        # 2. update the new value

        self.state[key] = value

    def get_info(self) -> pd.DataFrame:
        """
        get stock information in a table

        :return: df, pandas dataframe
        """

        # TODO optimize formatting for nice printing

        df_data = {"Commodity": [], "Price Index": [], "Current Stock Value": []}

        for key, val in self.abbrev_dict.items():
            p_val = self.state[val]
            df_data["Current Stock Value"].append(p_val)
            df_data["Price Index"].append(val)
            df_data["Commodity"].append(key)

        df = pd.DataFrame(df_data)

        df.set_index("Commodity", inplace=True)
        return df

    def request_price_history(self, name: str, which: str = "all", convert_df: bool = False, convert_dict: bool = False, human: bool = False):
        """
        get historical trace of a stock index 

        :param name: name of the commodity
        :param which: passing 'all' (default) will return all past values, passing 'last' will only return the two latest values. BETA works only in convert_dict mode
        :param convert_df: convert to dataframe? if False, a numpy array is returned instead (which is faster)
        :param convert_dict: convert to dictionary, where keys are time periods and values are the data values; the numpy array will be of shape [2,n] where [0,0...n-1] is the time stamp and [1,0....n-1] is the price data belonging to this  time stamp
        :param human: get price history by the name of the commodity instead
        :return: df or dict

        Example

        .. code-block:: python

            from sfctools import Clock, StockManager
            import numpy as np 

            for i in range(10):
                StockManagre().set_price("P_K",10.0 + np.random.rand())
                Clock().tick()

            times, values = StockManager().request_price_history("P_K")
            print(times)
            print(values)

        """

        if human:
            key = self.abbrev_dict[name]
        else:
            key = name

        values = np.array(self.hist.get_entries()[key])  # get data

        if not convert_df:
            if not convert_dict:
                return values.T
            else:

                if len(values) == 0:
                    return {}

                times, vals = values.T

                d = {}

                N = len(times)
                if which== "last":
                    N = min(3,len(times))
                    # get values for t, t-1, t-2 which are typically required in dynamic macro models
                    # (Bellman equation kicks out rest)

                for i in range(len(times)-N,len(times)):
                    # d[times[N-1-i]] = vals[N-1-i]
                    d[times[i]] = vals[i]

                return d
        else:

            df = pd.DataFrame(values, columns=["Time", key]).set_index("Time")
            return df
