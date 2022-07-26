__version__ = "0.3"
__author__ = "Thomas Baldauf"
__email__ = "thomas.baldauf@dlr.de"
__license__ = "MIT"
__birthdate__ = '15.11.2021'
__status__ = 'test' # options are: dev, test, prod

from collections import defaultdict
from ..core.clock import Clock
import pandas as pd
from ..core.settings import Settings
from ..datastructs.balance import BalanceEntry


class Inventory:
    """
    Inventory data structure.
    An Inventory consists of a collection of current assets.

    +-----------------+--------------------------------+-------------------------+
    |   Name of asset | inventory (in physical quant.) | costs ( = worth in €)   |
    +=================+================================+=========================+
    |   Apples        | 10                             | 2.0                     |
    +-----------------+--------------------------------+-------------------------+
    |   Oranges       | 9                              | 2.1                     |
    +-----------------+--------------------------------+-------------------------+

    Usage: The inventory is a non-standard feature of an agent and has to be added manually

    .. code-block:: python
    
        class InventoryAgent(Agent):
            def __init__(self):
                super().__init__()
                self.inventory = Inventory(self)
            
        my_agent = InventoryAgent()
        my_agent.inventory.add_item(name,quantity,costs)
        my_agent.inventory.remove_item(name, quantity)
        my_agent.inventory.get_inventory(name)
        
    """

    def __init__(self, owner,depreciation_dict=None):
        """
        Instantiates a new inventory data structure.

        :param owner: instance who owns this data structure
        :param depreciation_dict: a dict with the depreciation values for the goods stored in the
        """

        self.owner = owner
        self.data = defaultdict(lambda: {"inventory": 0.0, "costs": 0.0})

        if depreciation_dict is not None:
            self.depreciation_dict = depreciation_dict
        else:
            self.depreciation_dict = Settings().depr_dict

    def to_dataframe(self):
        """
        converts the inventory data to pandas dataframe format
        """

        data = {"Asset":[],"Inventory":[], "Worth":[]}

        for asset,line in self.data.items():

            data["Asset"].append(asset)
            data["Inventory"].append(line["inventory"])
            data["Worth"].append(line["costs"])

        return pd.DataFrame(data)

    def to_string(self):
        """
        converts the inventory data to string format
        """

        return "\n\n" + self.to_dataframe().to_string() + "\n\n"

    def depreciate(self, method="linear"):
        """
        Depreciates the values in the balance sheet. This requires a sfctools.Settings object to be instantiated.
        
        :param method: 'linear' (other options not yet implemented)
        """
        if method != "linear":
            raise NotImplementedError("Not yet implemented")

        for asset, line in self.data.items():

            # print("DEPRECIATE",self.depreciation_dict)
            quantity = max(0, self.data[asset]["inventory"]*self.depreciation_dict[asset.strip()])

            if quantity > 0:
                self.remove_item(asset, quantity)

            else:
                error = NotImplementedError("Something went wrong. Tried to depreciate negative quantity.")
                raise error 


    def add_item(self, name, quantity, costs):
        """
        adds an item to the inventory

        :param name: name of the item
        :param quantity: quantity of the item (float or int)
        :param costs: the nominal value of the items being added (= quantity x price)
        """

        assert quantity >= 0

        self.data[name]["inventory"] += quantity
        self.data[name]["costs"] += costs

        self.owner.balance_sheet.disengage()
        self.owner.balance_sheet.change_item(name, BalanceEntry.ASSETS, costs, suppress_stock=True)
        self.owner.balance_sheet.change_item("Equity", BalanceEntry.EQUITY, costs, suppress_stock=True)
        self.owner.balance_sheet.engage()

    def remove_item(self, name, quantity):
        """
        Takes a certain quantity of an item out of inventory

        :param name: name of the item from which you want to remove
        :param quantity: physical quantity to remove
        """

        eps = 1e-10
        assert quantity <= self.data[name]["inventory"] + eps, "Exceeded inventory by" \
                                                         " removing a quantity (%.2f) more than on stock (%.2f)"%(quantity,self.data[name]["inventory"])

        avg_cost = self.data[name]["costs"]/self.data[name]["inventory"]

        """
        €/pieces * pieces = €
        """
        self.data[name]["inventory"] -= quantity
        self.data[name]["costs"] -= avg_cost * quantity

        self.owner.balance_sheet.disengage()
        self.owner.balance_sheet.change_item(name, BalanceEntry.ASSETS, -avg_cost * quantity, suppress_stock=True)
        self.owner.balance_sheet.change_item("Equity", BalanceEntry.EQUITY, -avg_cost * quantity, suppress_stock=True)

        # income statement: costs, e.g. costs for labor have already been subtracted
        # so there is no redundant income statement needed here

        self.owner.balance_sheet.engage()

        return avg_cost * quantity


    def get_inventory(self, name):
        """
        gets the current inventory of a certain item type

        :param: name of the item 
        """

        return self.data[name]["inventory"]

    @property
    def worth(self):
        """
        computes total nominal worth of the inventory.
        """

        s = 0
        for k, v in self.data.items():
            s += v["costs"]

        return s