from seller import Seller
from buyer import Buyer
from market import Market 
import numpy as np 
from sfctools import matplotlib_lineplot 
import matplotlib.pyplot as plt 

"""
Market model from http://shiftleft.com/mirrors/www.hpl.hp.com/techreports/97/HPL-97-141.pdf
"""

# set up the agents
market = Market()
margins = np.linspace(0.1,0.5,20)

sellers = []
buyers = []

for i,m in enumerate(margins):
    for j in range(i):
        sellers.append(Seller(m,market))
    for j in range(i):
        buyers.append(Buyer(m,market))

# iterate the market process 
prices = []

for i in range(20):
    print(i)
    p = market.process()
    prices += p 

market.plot_weighted()

# plot the output 
plt.figure()
plt.plot(prices)
plt.show()
