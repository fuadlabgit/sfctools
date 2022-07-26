__version__ = "0.3"
__author__ = "Thomas Baldauf"
__email__ = "thomas.baldauf@dlr.de"
__license__ = "MIT"
__birthdate__ = '15.11.2021'
__status__ = 'dev' # options are: dev, test, prod

from sfctools import FlowMatrix as FlowLogger
import numpy as np
from sfctools import BalanceEntry,Accounts
from sfctools import ICSEntry
CA = Accounts.CA
KA = Accounts.KA


def con(household, production, q):
    #
    assert not np.isnan(q)
    assert q < +np.inf
    assert q > -np.inf
    assert q >= 0, print('have to pass positive quantity: unidirectional transaction')
    household.balance_sheet.disengage()
    production.balance_sheet.disengage()
    household.balance_sheet.change_item('Equity', BalanceEntry.EQUITY, -q, suppress_stock=False)
    household.balance_sheet.change_item('Cash', BalanceEntry.ASSETS, -q, suppress_stock=False)
    production.balance_sheet.change_item('Equity', BalanceEntry.EQUITY, +q, suppress_stock=False)
    production.balance_sheet.change_item('Cash', BalanceEntry.ASSETS, +q, suppress_stock=False)
    household.balance_sheet.engage()
    production.balance_sheet.engage()
    FlowLogger().log_flow((KA,KA), q, household, production, subject='Consumption')
    household.income_statement.new_entry(ICSEntry.EXPENSES,'con',q)
    production.income_statement.new_entry(ICSEntry.REVENUES,'con',q)


def gov(government, production, q):
    #government consumption
    assert not np.isnan(q)
    assert q < +np.inf
    assert q > -np.inf
    assert q >= 0, print('have to pass positive quantity: unidirectional transaction')
    government.balance_sheet.disengage()
    production.balance_sheet.disengage()
    government.balance_sheet.change_item('Equity', BalanceEntry.EQUITY, -q, suppress_stock=False)
    government.balance_sheet.change_item('Cash', BalanceEntry.ASSETS, -q, suppress_stock=False)
    production.balance_sheet.change_item('Equity', BalanceEntry.EQUITY, +q, suppress_stock=False)
    production.balance_sheet.change_item('Cash', BalanceEntry.ASSETS, +q, suppress_stock=False)
    government.balance_sheet.engage()
    production.balance_sheet.engage()
    FlowLogger().log_flow((KA,KA), q, government, production, subject='Gov. Expenditure')
    government.income_statement.new_entry(ICSEntry.EXPENSES,'gov',q)
    production.income_statement.new_entry(ICSEntry.NONTAX_PROFITS,'gov',q)


def wag(production, household, q):
    #
    assert not np.isnan(q)
    assert q < +np.inf
    assert q > -np.inf
    assert q >= 0, print('have to pass positive quantity: unidirectional transaction')
    production.balance_sheet.disengage()
    household.balance_sheet.disengage()
    production.balance_sheet.change_item('Equity', BalanceEntry.EQUITY, -q, suppress_stock=False)
    production.balance_sheet.change_item('Cash', BalanceEntry.ASSETS, -q, suppress_stock=False)
    household.balance_sheet.change_item('Equity', BalanceEntry.EQUITY, +q, suppress_stock=False)
    household.balance_sheet.change_item('Cash', BalanceEntry.ASSETS, +q, suppress_stock=False)
    production.balance_sheet.engage()
    household.balance_sheet.engage()
    FlowLogger().log_flow((KA,KA), q, production, household, subject='Wages')
    production.income_statement.new_entry(ICSEntry.EXPENSES,'wag',q)
    household.income_statement.new_entry(ICSEntry.REVENUES,'wag',q)


def tax(production, government, q):
    # taxes on firm profits
    assert not np.isnan(q)
    assert q < +np.inf
    assert q > -np.inf
    assert q >= 0, print('have to pass positive quantity: unidirectional transaction')
    production.balance_sheet.disengage()
    government.balance_sheet.disengage()
    production.balance_sheet.change_item('Equity', BalanceEntry.EQUITY, -q, suppress_stock=False)
    production.balance_sheet.change_item('Cash', BalanceEntry.ASSETS, -q, suppress_stock=False)
    government.balance_sheet.change_item('Equity', BalanceEntry.EQUITY, +q, suppress_stock=False)
    government.balance_sheet.change_item('Cash', BalanceEntry.ASSETS, +q, suppress_stock=False)
    production.balance_sheet.engage()
    government.balance_sheet.engage()
    FlowLogger().log_flow((KA,KA), q, production, government, subject='Taxes')
    production.income_statement.new_entry(ICSEntry.TAXES,'tax',q)
    government.income_statement.new_entry(ICSEntry.REVENUES,'tax',q)
