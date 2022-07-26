from trader import Trader
from shout import Shout 
import numpy as np 

class Buyer(Trader):
    def __init__(self,limit_price,market):
        limit_price *= np.random.uniform(0.98,1.02)
        
        super().__init__(limit_price,market)
        self.market.add_buyer(self)
        
    def update(self,last_shout):
        last_shout = self.market.last_shout
        q = last_shout.price
        
        if last_shout.accepted:
            if self.p >= q:
                self.raise_profit_margin(q)
                
            elif last_shout.kind == "offer":
                if self.active and self.p <= q:
                    self.lower_profit_margin(q)
        
        else:
            if last_shout.kind == "bid":
                if self.active and self.p <= q:
                    self.lower_profit_margin(q)
   
    def place_shout(self):
        new_shout = Shout(self,kind="bid")
        return new_shout