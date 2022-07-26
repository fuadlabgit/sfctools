from sfctools import Agent
from seller import Seller
from buyer import Buyer 
import numpy as np 
from shout import Shout 

from sfctools import MarketMatching


class Market(MarketMatching):
    
    def __init__(self):
        # :param marketmatching: an sfctools MarketMatching object 
        super().__init__()
        self._seller_list = []
        self._buyer_list = []
        self.shouts = []
        
    def add_seller(self,seller):
        self._seller_list.append(seller)
        self.add_supplier(seller)
        
    def add_buyer(self,buyer):
        self._buyer_list.append(buyer)
        self.add_demander(buyer)
    
    def rematch(self,buyer,seller,trader):
        # required for MarketMatching 
        success = False 
        if trader.active and buyer.p >= seller.p:
                    
            print("    -> SUCCESS")
            
            
            success = True 
        return success 
        
    def process(self):
        # process one iteration
        prices = []
        
        # get a random seller 
        np.random.shuffle(self._seller_list)
        np.random.shuffle(self._buyer_list)
        
        sellers = self._seller_list.copy()
        buyers = self._buyer_list.copy()
        
        k_max = 10
        k = 0
        
        while len(sellers) > 0 and len(buyers) > 0 and k < k_max:
            
            k+= 1
            
            trader = np.random.choice(sellers + buyers)
            
            shout = trader.place_shout()
            
            print("new shout", shout)
            kk = 0
            
            success = False 
            
            while kk < 10 and len(buyers) > 0 and len(sellers) > 0 and not success:
                kk += 1 
                
                if isinstance(trader,Seller):
                    seller = trader
                    buyer = np.random.choice(buyers)
                else:
                    buyer = trader 
                    seller = np.random.choice(sellers)
                    
                # print("seller", seller, "p" , seller.p, "    <->     " , "buyer", buyer, "p", buyer.p)
                
                success = self.rematch(buyer,seller,trader)
                
                if success:
                    shout.accepted = True 
                    prices.append(shout.price)
                    
                    sellers.remove(seller)
                    buyers.remove(buyer)
                    
                    buyer.active = False 
                    seller.active = False 
                    
                    val = self.get_value(seller, buyer)
                    if val is None:
                        val = 0
                    else:
                        self.unlink_agent(seller,buyer)
                    
                    self.link_agents(seller, buyer, val+1)
                    
                
                self.last_shout = shout 
                
                for trader in self._seller_list + self._buyer_list:
                    trader.update(shout)
        
        for trader in self._seller_list + self._buyer_list:
            trader.active = True 
            
        return prices 