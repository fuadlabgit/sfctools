__version__ = "0.3"
__author__ = "Thomas Baldauf"
__email__ = "thomas.baldauf@dlr.de"
__license__ = "MIT"
__birthdate__ = '15.11.2021'
__status__ = 'prod' # options are: dev, test, prod

from .world import World
from ..datastructs.balance import BalanceSheet, BalanceEntry
from ..datastructs.income_statement import IncomeStatement
from ..datastructs.cash_flow_statement import CashFlowStatement
from ..datastructs.signalslot import Signal,Slot
from .flow_matrix import FlowMatrix
import numpy as np
import warnings
from collections import defaultdict
from functools import wraps


class Agent:
    """
    This is the base class for any agent. It takes care of the bookkeeping system
    and other low-level operations of the agent.

    """

    def __init__(self, alias=None, verbose=False, signals:list = None, slots:list = None ):
        """
        Instantiation of agents is done here.
        Note: Each agent will be given a name and an alias name. The name will be set automatically and
        the alias name will be a (possibly non-unique) name, for example 'name' could be 'Firm_0001' and
        alias_name could be 'MyEnergyProducer'.

        :param alias: (optional) alias or None(default)
        :param verbose: boolean switch to enable console output. Default is False
        :param signals: list of str or None(default), signal names connected to this node
        :param slots: list of str or None(default), slot names connected to this node.
        """ 

        self.name = "New Agent" # set dummy name for registering agent

        world = World()  # get singleton world
        world.register_agent(self) # register agent at world registry

        # set name
        self.name = str(self.__class__.__name__) + "__%05i" % world.agent_registry.get_count(self.__class__.__name__)

        if alias is None: # set the alias if desired
            self.alias = self.name
        else:
            self.alias = alias

        self._balance_sheet = BalanceSheet(self) # agent gets a blank balance sheet
        self.income_statement = IncomeStatement(self) # blank income statement
        self.cash_flow_statement = CashFlowStatement(self)  # blank cash flow statement

        # triggers for tree struct to enable event-based approach
        self.trigger_dict = {} # <- this is meant for automation and therefore cannot be set by the user. TODO re-think implementation

        # bankruptcy flag
        self.bankrupt = False

        # print notification in verbose mode
        if verbose:
            if self.name != self.alias:
                print("New Agent %s" % self.name, "alias", self.alias)
            else:
                print("New Agent %s" % self.name)

        # triggers for signals and slots
        if signals is not None or slots is not None:
            self.signals = {}  # agent only has attribute "signals" if given 
            self.slots = {}    # agent only has attribute "slots" if given 

            # fill signals and slots dictionaries...
            assert isinstance(signals,list) or signals is None, "signal must be a list of str or None"
            if signals is not None:
                for signal_name in signals:
                    self.signals[signal_name] = Signal.retrieve(signal_name)

            assert isinstance(slots, list) or slots is None, "signal must be a list of str or None"
            if slots is not None:
                for slot_name in slots:
                    self.slots[slot_name] = Slot.retrieve(slot_name)

    def trigger(self, event_key,*args,**kwargs):
        """
        trigger a certain default method of this agent
        :param event_key str: a key for the event
        """
        method = self.trigger_dict[event_key]
        method()

    @property
    def balance_sheet(self):
        """
        This will return the (private) BalanceSheet object of the agent.
        """
        return self._balance_sheet

    def __repr__(self):
            s = ""
            if hasattr(self, "alias") and self.name != self.alias:
                s = " alias " + self.alias

            return "<Agent: " + self.name + s + ">"

    def __str__(self):
        if hasattr(self, "alias") and self.alias is not None and self.name != self.alias:
            return self.name + "(" + self.alias + ")" # + " [ %i ]"%id(self)
        else:
            return self.name # + " [ %i ]"%id(self)

    def __lt__(self, other): # required for pandas
        return self.name < other.name

    @property
    def leverage(self) -> float:
        """
        leverage of own balance sheet
        """
        return self.balance_sheet.leverage

    @property
    def net_worth(self) -> float:
        """
        net worth at own balance sheet
        """
        return self.balance_sheet.net_worth

    @property
    def total_assets(self):
        """
        sum of assets column of balance sheet
        """
        return self.balance_sheet.total_assets

    @property
    def total_liabilities(self):
        """
        sum of liabilities column of balance sheet
        """
        return  self.balance_sheet.total_liabilities

    @property
    def cash_balance(self) -> float:
        """
        'Shortcut' property for balance of 'Cash' stored in 'Assets' of the agent
        """
        return self.balance_sheet.get_balance("Cash", BalanceEntry.ASSETS)
    
    def file_bankruptcy(self, event=None):
        """ file agent for bankrupcy

        :param event: preferrably str, can be None for manual trigger but should be something like 'negative cash' or 'negative equity' (default). 
        
        NOTE This should be called by a sub-module rather than manually by the user
        """
        self.bankrupt = True
        raise RuntimeError("%s went bankrupt (reason: %s) ! %s" %(self,event,self.balance_sheet.to_string()))

    def get_balance(self, key,kind) -> float:
        """
        Gets the nominal balance of a certain entry in the balance sheet.
        :param key: str, which item is requested (e.g. 'Cash', 'Apples',...)
        :param kind: BalanceEntry 
        """
        # get balance sheet asset balance
        return self.balance_sheet.get_balance(key,kind=kind)



class SingletonAgent(Agent):
    """
    SingletonAgent is an agent which is singleton, meaning that only one instance creation of this Agent will be allowed.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self,alias=None, verbose=False):
        super().__init__(alias=alias, verbose=verbose)


def block_on_bankrupt(method):
    """
    This is a decorator you can use when building an agent. 
    It will block this action whenever the agent is bankrupt. 

    Usage:

    .. code-block:: python
    
        from sfctools import block_on_bankrupt

        class MyAgent(Agent):
            ...

        @block_on_bankrupt
        def my_fun(self,...):
            ...

    """
    @wraps(method)
    def _impl(self,*args,**kwargs):
        if not self.bankrupt:
            method_output = method(self,*args,**kwargs)
            return method_output
        else:
            warnings.warn("%s: tried to call forbidden method in bankruptcy: %s"%(self,method)) # <- TODO test this
            return None
    return _impl

