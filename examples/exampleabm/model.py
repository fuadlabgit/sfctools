__version__ = "0.3"
__author__ = "Thomas Baldauf"
__email__ = "thomas.baldauf@dlr.de"
__license__ = "MIT"
__birthdate__ = '15.11.2021'
__status__ = 'dev' # options are: dev, test, prod


from agents.household import Household 
from agents.production import Production 
from agents.government import Government 

from sfctools import Clock, FlowMatrix, Settings
from sfctools import matplotlib_lineplot, matplotlib_barplot 
from sfctools import IndicatorReport, ReportingSheet, BalanceSheet

import pandas as pd 
import matplotlib.pyplot as plt 
import numpy as np 

# read settings
Settings().read_from_yaml("settings.yml")

# generate agents 
my_household  = Household()
my_production = Production()
my_government = Government()

# link the agents 
my_household.link()
my_production.link()
my_government.link()

# simulation duration 
T = int(Settings().get_hyperparameter("T")) # simulation length
T_burn_in = int(Settings().get_hyperparameter("T_burn")) # simulation length

# prepare output data 
rs = ReportingSheet([
    IndicatorReport("Time","C"),
    IndicatorReport("Time","G"),
    IndicatorReport("Time","Y"),
    IndicatorReport("Time","T"),
    IndicatorReport("Time","DI")])

household_balance_data = []  # logs the household balance sheets
governmnt_balance_data = []  # logs the government balance sheets

# simulation loop
for i in range(T):

   
    # reset flow matrix 
    FlowMatrix().reset() 
    
    
    # update all agents individually
    my_household.update()
    my_government.update()
    my_production.update()

    Clock().tick() # increase clock by one tick 
    
    # output data 
    if i > T_burn_in: # after burn-in
        
        IndicatorReport.getitem("C").add_data(my_household.C)
        IndicatorReport.getitem("G").add_data(my_government.G)
        IndicatorReport.getitem("Y").add_data(my_production.Y)
        IndicatorReport.getitem("T").add_data(my_production.T)
        IndicatorReport.getitem("DI").add_data(my_household.DI)
        
        # plot agent's balance sheets
        household_balance_data.append(my_household.balance_sheet.raw_data)
        governmnt_balance_data.append(my_government.balance_sheet.raw_data)

    # reset agents
    my_household.reset()
    my_production.reset()
    my_government.reset()
    

# print flow matrix
print(FlowMatrix().to_string())

fig = FlowMatrix().plot_sankey(show_values=True,show_plot=False)
plt.savefig("figures/sankey.png")
plt.close()

fig = FlowMatrix().plot_colored(show_plot=False)
plt.savefig("figures/matrix.png")
plt.close()

# plot output indicators
fig = rs.plot(show_plot=False)
plt.savefig("figures/outputs.png")
plt.close()

# plot the stocks of government and household
# BalanceSheet.plot_list(household_balance_data, dt=5, xlabel="Time", title="Household",  show_liabilities=False)
BalanceSheet.plot_list(governmnt_balance_data, dt=5, xlabel="Time", title="Example", show_liabilities=True)
