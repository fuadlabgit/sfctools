__version__ = "0.3"
__author__ = "Thomas Baldauf"
__email__ = "thomas.baldauf@dlr.de"
__license__ = "MIT"
__birthdate__ = '15.11.2021'
__status__ = 'prod' # options are: dev, test, prod

import yaml
# import dill
from ..core.singleton import Singleton
from ..bottomup.stock_manager import StockManager
from ..core.custom_warnings import warning_on_one_line

import dataclasses
from typing import Sequence
import pandas as pd
from collections import deque
import warnings
from typing import Any


"""
Defines data classes for structure of settings file
NOTE this was removed as dill and cattr were unstable / unreliable in different versions. Sacrificed consistency compfort for stability here...

@dataclasses.dataclass
class CommodityDetails:
    name: str  # name of the commodity
    price: str  # name of the price index
    value: float = 1.0  # initial stock value of price index
    depreciation: float = 0.0  # depreciation rate
    description: str = "No description"  # description of this commodity
    unit: str = "unknown unit"


@dataclasses.dataclass
class MetaInfo:
    author: str = "Unknown Author"
    date: str = "Unknown Date"
    comment: str = ""


@dataclasses.dataclass
class HyperParameter:
    name: str
    value: Any = None
    description: str = "no description"


@dataclasses.dataclass
class Config:
    metainfo: MetaInfo
    params: Sequence[CommodityDetails]
    hyperparams: Sequence[HyperParameter] = deque()

"""


class Settings(Singleton):
    """
    This is a settings class that serves as a central data structure to store hyperparameters, commodity names, depreciation rates etc. 
    It also includes a section with metadata on author etc...
    """

    def __init__(self):
        """
        constructor for settings
        """
        super().__init__()  # <- has no effect (?)

        if hasattr(self, "initialized"): # <- TODO replace this with 'if self.do_init' from Singleton. 
            return
        else:
            self.initialized = False # <- Tkept this because it works


            self.config_data = None  # this stores all information about allowed asset types
            self.df = None  # this stores the same data in dataFrame format (for convenience)
            self.hyper_params = None  # this stores the hyper parameters
            self.__hyper_params_dict = {}  # dict for faster access later
            self.depr_dict = {}  # asset and depreciation rate
            
            self.allowed_commodities = []
            self.unit_dict = {}  # asset and unit
            
            warnings.formatwarning = warning_on_one_line
            
    def __str__(self):
        return self.get_hyperparams_info().to_string()
        
    def reset(self):
        """
        reset settings
        """

        self.config_data = None
        self.df = None
        self.hyper_params = None
        self.__hyper_params_dict = {}  # dict for faster access later
        self.allowed_commodities = None
        self.depr_dict = {}

        warnings.warn("Settings have been reset!")
    
    def read_from_yaml(self,data,isfile=True):
        # warnings.warn("Settings().read_from_yaml is depreciated. use 'read' instead")
        
        return self.read(data,isfile)
        
    def read(self, data, isfile=True):
        """
        read the settings from a yaml file.
        The settings of a simulation can be stored in form of a yaml file. The first block metainfo stores the author, date and other meta data. The params block stores information on the assets allowed in balance sheets and their respective depreciation rates (0 means no depreciation, 1 means that the good is fully perishable). hyperparams contains parameters of agents stored centrally (for better overview). It also helps to avoid hardcoding of parameters directly in the code of the agents.

        :param data: either str, i.e. a string containing the data, or path/str, i.e. file name to read from
        :param isfile: boolean switch. If False, a string has to be passed. 
        ** Example **
        
        "filename.yml" File:

        .. code-block:: yaml 

            metainfo :
                author: Hans Dampf
                date: Agust 1964
                info: some more info

            params:
                - name: Cash
                  depreciation: 0.0
                  price: p
                  value: 1.0
                  unit: Euro
                  description: my description 

                - name: Energy
                  ...

            hyperparams:
                - name: epsilon
                  value: 0.05
                  description: my description

                - name: 
                  ...
        
        Python code:
           
        .. code-block:: python
            
            from sfctools import Settings
            my_settings = Settings().read_from_yaml("filename.yml")    
        
        
        """
        
        if isfile:
            file = open(data)
            self.config_data = yaml.load(file, Loader=yaml.SafeLoader)
        else:
            self.config_data = yaml.safe_load(data)
        
        if "params" not in self.config_data:
            self.config_data["params"] = [] # empty list if not available
        
        self.allowed_commodities = self.config_data["params"]

        for entry in self.allowed_commodities:
            self.depr_dict[entry["name"].strip()] = float(entry["depreciation"])

        self.hyper_params = self.config_data["hyperparams"]
        for entry in self.hyper_params:
            try:
                self.__hyper_params_dict[entry["name"].strip()] = float(entry["value"])
            except:
                self.__hyper_params_dict[entry["name"].strip()] = entry["value"]

        # 3. feed stock manager with data
        self.setup_stock_manager()
        
        # 4. load world data
        # world = None
        # try:
        #    worldfile = self.config_data["worlddata"]
        #    with open(worldfile, "rb") as file:
        #        world = dill.load(file)
        # except Exception as e:
        #    print(str(e))
        #    # TODO correct error / exception handling
        # return world
        
        self.initialized = True 
        return self 
        
    def setup_stock_manager(self):
        """
        set up the stock manager from the data stored in the current settings. For more information on the stock manager, see StockManager class.
        This should not be called manually by the user. It is automatically called within 'read_from_yaml()'.
        """

        stock_mgr = StockManager()  # get instance of the stock manager

        # iterate through entries
        for k,entry in enumerate(self.config_data["params"]):
            
            try:

                # prepare the data
                name = entry["name"]

                if "price" in entry and "value" in entry and "unit" in entry:  # insert price, value and untit # TODO < how to resolve confusion between price (name of the price index) and value (current price value)?
                    price_name = entry["price"]
                    price_value = entry["value"]
                    self.unit_dict[name] = entry["unit"]

                    # write data to stock manager
                    stock_mgr.register(name, price_name, price_value)

                else:
                    if "name" in entry:
                        warnings.warn("I could not register %s at stock manager. 'price', 'value' and/or 'unit' key is missing." % entry["name"])
                    else:
                        warnings.warn("I could not register item %i at stock manager. 'name', 'price', 'value' and/or 'unit' key is missing." % k)

            except Exception as e:

                if "name" in entry:
                    warnings.warn("I could not register %s at stock manager. 'price','value' and/or 'unit' key is missing." % entry["name"])
                else:
                    warnings.warn("I could not register item %i at stock manager. Name missing" % k)

    def get_info(self):
        """
        return info about assets and their depreciation rates

        :return: df, pandas dataframe with information about allowed assets

        Example

        .. code-block:: python

            from sfctools import Settings
            dfinfo = Settings().get_info()
            print(dfinfo)
    
        """
        df = pd.DataFrame(self.config_data["params"])

        df.rename(columns={
            "name": "Name",
            "depreciation": "Depreciation",
            "unit": "Unit",
            "value": "Initial Stock Value",
            "price": "Price Index",
            "description": "Description"
        }, inplace=True)

        df.set_index("Name", inplace=True)

        self.df = df  # for convenience save this here as 'duplicate' pandas format

        return df

    def get_hyperparams_info(self):
        """
        return info about hyperparameters

        :return: df, pandas dataframe with information about allowed assets

        Example

        .. code-block:: python

            from sfctools import Settings
            dfinfo = Settings().get_hyperparams_info()
            print(dfinfo)
    
        """

        if len(self.hyper_params) == 0:
            raise TypeError("No hyperparams found.")

        df = pd.DataFrame(self.hyper_params)
        df.rename(columns={"name": "Name", "value": "Value", "description": "Description"}, inplace=True)
        df.set_index("Name", inplace=True)

        return df
    
    def __getitem__(self,key):
        return self.get_hyperparameter(key)
    
    def __setitem__(self,key,value):
        warnings.warn("Changed settings parameter %s" %key)
        self.set_hyperparameter(key,value)
        
    def get_hyperparameter(self, name):
        """
        get the value of a hyperparameter by its name. 
        WARNING this is expensive (string key lookup) -> it is recommended to look this up only once and then store it as an attribute in an agent's instance.
        #^TODO check if this is actually expensive 
        
        :param name: the name of the hyper-parameter to filter for
        """
        
        if str(name) in self.__hyper_params_dict:
            return self.__hyper_params_dict[str(name)]  # faster access in O(1)
        else:
        
            err = "Could not find parameter %s in settings yaml. Please check again!" % (str(name))
            
            if not self.initialized:
                err += " Settings have not yet been initialized. Pleas use Settings().read(...) to load the simulation settings."
            
            raise KeyError(err)
    
    def set_hyperparameter(self,name,value):
        """
        get the value of a hyperparameter by its name. 
        
        :param name: str, name of the parameter
        :param value: new value (any type but ideally same as before)
        """
        
        if str(name) in self.__hyper_params_dict:
            warnings.warn("Resetting hyperparameter value of %s" % name)
            
            self.__hyper_params_dict[str(name)] = value
        else:
        
            err = "Could not find parameter %s in settings yaml. Please check again!" % (str(name))
            
            if not self.initialized:
                err += " Settings have not yet been initialized. Pleas use Settings().read(...) to load the simulation settings."
            
            raise KeyError(err)
        