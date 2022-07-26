# sfctools - A toolbox for stock-flow consistent, agent-based models

Sfctools is a lightweight and easy-to-use Python framework for agent-based macroeconomic, stock-flow consistent (ABM-SFC) modeling. It concentrates on agents in economics and helps you to construct agents, helps you to manage and document your model parameters, assures stock-flow consistency, and facilitates basic economic data structures (such as the balance sheet).


## Installation of the Framework

(**Lazy version**) In a terminal of your choice, type: 

    pip install sfctools 

see https://pypi.org/project/sfctools/

this will install the version available on pypi.

(**Latest version**) To get the version stored in this repository, you need poetry (see https://python-poetry.org/). Once you have poetry installed, run poetry build. 
In the dist folder, you will find the wheel file necessary to install the framework. 


## Installation of the GUI

(**Recommended way**) The gui is already shipped with the framework. Just open Python and type the following commands

    from sfctools.gui import Gui
    g = GUi()
    g.run()

this will open the gui for you. 

(**Alternative way**) If you like to start the gui from another environment directly, you can also copy the gui/attune folder to an arbitrary folder and just navigate to src/. In src, run python on qtattune.py. 


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

## Bug reports

Bug reports, feature requests etc. are warmly welcome! Just open a new issue in git!



| Author Thomas Baldauf, German Aerospace Center (DLR), Curiestr. 4 70563 Stuttgart | thomas.baldauf@dlr.de | version: 0.5 (Beta) | date: February 2022
