Installation
============================

Installation with pip
---------------------

Sfctools runs in any python >3.6 environment. The installation is as simple as

.. code-block:: python

    pip install sfctools


Before the installation, please upgrade your current version of pip (22 or higher required) and install the latest version of pyyaml (we require 5.0 or higher). The following commands could be helpful for troubleshooting

.. code-block:: python 

    pip install --ignore-installed PyYAML
    pip install --upgrade pip --user

If you are having trouble please contact the development team or open up an issue. 

Check your working installation with 

.. code-block:: python

    pip show sfctools

For advanced users, it is recommended to create a new python environment for sfctools.

.. warning::

  This is still an experimental release (v0.4 beta). Bug reports and feature requests are welcome!

Basic Example
-------------------
The framework can be included in any python project. Agents are constructed by inheriting from the Agent class:

.. code-block:: python

  from sfctools import Settings, Agent, FlowMatrix, BalanceEntry
  from sfctools import Accounts

  Settings().read_from_yaml("my_settings.yml") # <- defines parameter 'beta'

  class MyAgent(Agent):
    def __init__(self):
      super().__init__()

      self.my_parameter = Settings().get_hyperparameter("beta")

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

And the my_settings.yml:

.. code-block:: yaml

            metainfo :
                author: Example Author
                date: November 2021
                info: settings for example project

            hyperparams:
                - name: beta
                  value: 0.05
                  description: just an example parameter
