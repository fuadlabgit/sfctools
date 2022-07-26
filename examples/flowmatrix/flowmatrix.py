from sfctools import Agent, FlowMatrix, Accounts, BalanceEntry

# create some agent classes
class MyAgent(Agent):
 def __init__(self):
     super().__init__()
     with self.balance_sheet.modify:

         self.balance_sheet.change_item("Cash",BalanceEntry.ASSETS,+100.0,suppress_stock=True)
         self.balance_sheet.change_item("Equity",BalanceEntry.EQUITY,+100.0,suppress_stock=True)


class TypeA(MyAgent):
 def __init__(self):
     super().__init__()

class TypeB(MyAgent):
 def __init__(self):
     super().__init__()

class TypeC(MyAgent):
 def __init__(self):
     super().__init__()

class TypeD(MyAgent):
 def __init__(self):
     super().__init__()

class TypeE(MyAgent):
 def __init__(self):
     super().__init__()


my_a = TypeA() # create agents
my_b = TypeB()
my_c = TypeC()
my_d = TypeD()
my_e = TypeE()
my_e2 = TypeE()

def transfer(t,agent1,agent2,subject,quantity): # define a generic transaction
 with agent1.balance_sheet.modify:
     with agent2.balance_sheet.modify:

         agent1.balance_sheet.change_item("Cash",BalanceEntry.ASSETS,-quantity)
         agent1.balance_sheet.change_it em("Equity",BalanceEntry.EQUITY,-quantity)

         agent2.balance_sheet.change_item("Cash",BalanceEntry.ASSETS,+quantity)
         agent2.balance_sheet.change_item("Equity",BalanceEntry.EQUITY,+quantity)


         FlowMatrix().log_flow(t, quantity, agent1, agent2 ,subject=subject)

# do some transactions
transfer((Accounts.CA, Accounts.CA),my_a,my_b,"my subject",quantity=42)
transfer((Accounts.CA, Accounts.CA),my_a,my_c,"other subject",quantity=3.1415)
transfer((Accounts.CA, Accounts.KA),my_c,my_d,"different subject",quantity=10.0)
transfer((Accounts.KA, Accounts.KA),my_a,my_e,"no subject",quantity=3.1415)
transfer((Accounts.KA, Accounts.KA),my_a,my_e2,"no subject",quantity=3.1415)

# output flow matrix as table and Sankey chart
print(FlowMatrix().to_dataframe())
FlowMatrix().plot_colored(group=False)
FlowMatrix().plot_colored(group=True)
FlowMatrix().plot_sankey()