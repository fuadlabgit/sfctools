# attune - A gui for stock-flow consistent, agent-based modeling

Attune (agent-based transaction and accounting gui) is a graphical user interface (GUI) for generating accounting and cash flow patterns for the usage in sfctools. This is a complementary tool to the sfctools framework.


![screenshot](title.png)

## Installation 


1. Get your copy of this repo. See https://git-scm.com/book/en/v2/Git-Basics-Getting-a-Git-Repository for help on git.

2. Create a new environment from the yaml provided. This will automatically get you a copy of sfctools

        conda env create -f environment.yml --name "attune"
        conda activate attune

3. Install some dependencies manually (just in case step 2 fails)
        
        pip install --no-dependencies sfctools pyqt5 sympy pydot pyperclip pdflatex openpyxl

4. Run the gui via

        cd src && python qtattune.py

5. Read the docs at ``docs/build/index.html``


| Author Thomas Baldauf, German Aerospace Center (DLR), Curiestr. 4 70563 Stuttgart | thomas.baldauf@dlr.de | version: 0.7 (Alpha) | date: February 2022
