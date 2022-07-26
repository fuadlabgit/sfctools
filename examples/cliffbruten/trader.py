from sfctools import Agent 
import numpy as np 

class Trader(Agent):
    def __init__(self,limit_price,market):
    
        super().__init__()
        self.profit_margin = np.random.uniform(0,0.2)
        self.limit_price = limit_price 
        self.learning_rate = np.random.uniform(0.02,0.05)
        self.market = market 
        self.active = True 
        
        self.e = 0.01
        self.d = 0.01
        
    @property 
    def p(self):
        return self.limit_price * (1+ self.profit_margin)
    
    def update_margin(self,q,r,a):
        tau = r *q + a 
        delta_i = self.learning_rate * (tau-self.p)
        self.profit_margin = (self.p + delta_i)/self.limit_price - 1
    
    def lower_profit_margin(self,q):
        
        # :param q: price of last shout
        r = np.random.uniform(1.0-self.e,1.0)
        a = np.random.uniform(-self.d, 0.0)
        self.update_margin(q,r,a)
        
    def raise_profit_margin(self,q):
        # :param q: price of st shout
        r = np.random.uniform(1.0, 1.0+self.e)
        a = np.random.uniform(0.0, self.d) 
        self.update_margin(q,r,a)
    
    