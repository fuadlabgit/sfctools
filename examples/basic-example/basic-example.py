from sfctools import Settings, Agent, FlowMatrix, BalanceEntry
from sfctools import Accounts

Settings().read_from_yaml("my_settings.yml") # <- defines parameter 'beta'

print(Settings())


class MyAgent(Agent):
  def __init__(self):
    super().__init__()

    self.my_parameter = Settings().get_hyperparameter("beta") # or Settings()["beta"]

  # def more_here(self,*args):
  #  ...

my_agent = MyAgent() # <- create an agent
my_second_agent = MyAgent()  # <- create a second agent

with my_agent.balance_sheet.modify:
  my_agent.balance_sheet.change_item("Cash", BalanceEntry.ASSETS, 10.0)
  my_agent.balance_sheet.change_item("Equity", BalanceEntry.EQUITY, 10.0)  # enlarge my_agent's balance by 10

def my_test_transaction(agent1,agent2,quantity):
  FlowMatrix().log_flow((Accounts.CA, Accounts.CA), quantity, agent1,agent2,subject="test")

my_test_transaction(my_agent,my_second_agent,9.0) # transfer 9 units between the agents

print(my_agent.balance_sheet.to_string())
print(my_second_agent.balance_sheet.to_string())

print(FlowMatrix().to_string())