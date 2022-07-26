# sfctools - A toolbox for stock-flow consistent, agent-based models

Sfctools is a lightweight and easy-to-use Python framework for agent-based macroeconomic, stock-flow consistent (ABM-SFC) modeling. It concentrates on agents in economics and helps you to construct agents, helps you to manage and document your model parameters, assures stock-flow consistency, and facilitates basic economic data structures (such as the balance sheet).


## Installation 

In a terminal of your choice, type: 

    pip install sfctools 

see https://pypi.org/project/sfctools/


## Usage

```console
from sfctools import Agent,World
class MyAgent(Agent):
    def __init__(self, a):
        super().__init__(self)
        self. = a 
my_agent = MyAgent()
print(my_agent)
print(World().get_agents_of_type("MyAgent"))
```


| Author Thomas Baldauf, German Aerospace Center (DLR), Curiestr. 4 70563 Stuttgart | thomas.baldauf@dlr.de | version: 0.5 (Beta) | date: February 2022
