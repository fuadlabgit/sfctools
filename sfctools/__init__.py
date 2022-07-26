"""
SFCTOOLS
========

Thomas Baldauf
thomas.baldauf@dlr.de
November 2021, German Aerospace Center

Licensed under MIT license

Contents

    1. CORE FEATURES
    2. DATA STRUCTURES
    3. AUTOMATION AND PARAMETER-IO
    4. BOTTOM-UP FEATURES
    5. MISC
    6. GRAPHICAL USER INTERFACE

"""

"""
CORE FEATURES
"""
from .core.agent import Agent, SingletonAgent
from .core.agent import block_on_bankrupt
from .core.singleton import Singleton
from .core.clock import Clock
from .core.settings import Settings
from .core.world import World
from .core.flow_matrix import FlowMatrix, Accounts

"""
DATA STRUCTURES
"""
from .datastructs.balance import BalanceSheet, BalanceEntry
from .datastructs.income_statement import IncomeStatement,ICSEntry
from .datastructs.cash_flow_statement import CashFlowStatement, CashFlowEntry
from .datastructs.bank_order_book import BankOrderBook
from .datastructs.inventory import Inventory
from .datastructs.market_registry import MarketRegistry
from .datastructs.worker_registry import WorkerRegistry
from .datastructs.signalslot import Signal,Slot,SignalSlot

"""
AUTOMATION AND PARAMETER-IO
"""
from .automation.runner import ModelRunner
from .automation.calibration import CalibrationRoutine, DistanceMeasure

"""
BOTTOM-UP FEATURES
"""
from .bottomup.stock_manager import StockManager
from .bottomup.matching import MarketMatching
from .bottomup.productiontree import ProductionTree

"""
MISCELLANEOUS
"""
from .misc.timeseries import stretch_pandas, stretch_datetime, convert_quarterly_to_datetime, stretch_to_length, convert_numeric
from .misc.mpl_plotting import matplotlib_barplot,matplotlib_lineplot, plot_sankey
from .misc.reporting_sheet import ReportingSheet, DistributionReport, IndicatorReport

"""
GUI
"""
from . import gui
