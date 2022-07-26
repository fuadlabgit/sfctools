__version__ = "0.3"
__author__ = "Thomas Baldauf"
__email__ = "thomas.baldauf@dlr.de"
__license__ = "MIT"
__birthdate__ = '15.11.2021'
__status__ = 'test' # options are: dev, test, prod


from collections import defaultdict
import pandas as pd

class RegistryEntry:
    """
    A helper data structure for MarketRegistry
    """

    def __init__(self):
        self.data = {"total": 0.0, "fulfilled": 0.0}

    def __str__(self):
        return str((self["total"],self["fulfilled"],self["remaining"]))

    def __getitem__(self, item):
        if item == "total" or item == "fulfilled":

            if callable(self.data[item]):
                call = self.data[item]
                return call()
            else:
                return self.data[item]

        if item == "remaining":
            return self["total"] - self["fulfilled"]

    def __setitem__(self, key, value):
        if key== "total" or key=="fulfilled":
            self.data[key] = value
        else:   
            raise KeyError("Cannot set key %s",key)


class MarketRegistry:
    """
    Data structure to store remaining and fulfilled demand of an agent at a market


    DEMAND:

    +---------+--------------------+-------------------+------------------------+
    |         |       total        |    fulfilled      |    remaining           |
    +---------+--------------------+-------------------+------------------------+
    | good1   |                    |                   |    =total-fulfilled    |
    +---------+--------------------+-------------------+------------------------+
    | good2   |                    |                   |                        |
    +---------+--------------------+-------------------+------------------------+
    | good3   |                    |                   |                        |
    +---------+--------------------+-------------------+------------------------+
    

    SUPPLY:

    +---------+--------------------+-------------------+------------------------+
    |         |       total        |    fulfilled      |    remaining           |
    +---------+--------------------+-------------------+------------------------+
    | good1   |                    |                   |    =total-fulfilled    |
    +---------+--------------------+-------------------+------------------------+
    | good2   |                    |                   |                        |
    +---------+--------------------+-------------------+------------------------+
    | good3   |                    |                   |                        |
    +---------+--------------------+-------------------+------------------------+

    """
    
    def __init__(self,owner):
        """
        :param owner: agent instance who owns this data structure
        """
        self.data = {"demand":defaultdict(lambda: RegistryEntry()),
                     "supply":defaultdict(lambda: RegistryEntry())}

        self.owner = owner

    def to_string(self):
        """
        converts data structure to human-readable string format
        """
        df = pd.DataFrame.from_dict(self.data)
        df.index.name = str(self.owner)   # .set_caption(self.owner)
        return "\n\n" +  df.to_string()

    def __getitem__(self, item):
        return self.data[item]

    def set_target_update(self, kind, good, new_value):
        """
        set up the toftal demand/supply for a certain good
        
        :param kind: 'demand' or 'supply'
        :param good: name of good
        :param q: new entry value
        """
        self.data[kind][good]["total"] = new_value

    def set_current_update(self, kind, good, q):
        """"
        update fulfillment of demand or supply

        :param kind: 'demand' or 'supply'
        :param good: name of good
        :param q: new entry value
        """
        self.data[kind][good]["fulfilled"] = q

    def reset(self,kind,good):
        """
        reset all entries to zero
        
        :param kind: 'demand' or 'supply'
        :param good: name of good
        """
        self.data[kind][good]["total"] = 0
        self.data[kind][good]["fulfilled"] = 0


