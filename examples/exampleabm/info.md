# Dxample Project 'Macro-ABM'

This model is a simple stock-flow consistent macro-economic example model, simmilar but not equal to the one developed in Godley and Lavoie https://link.springer.com/book/10.1007/978-1-137-08599-3. 
This project serves as a sandbox to get familiar with the functionalities of sfctools and is NOT meant to be a ready-to-apply macroeconomic model (e.g. for a policy study).


There are some relevant agents included (see ./agents folder):

- Household
- Government
- Production

Settings: see ./settings.yml

Main script: just run python on model.py results will be written to ./figures

Transactions: The transactions are noted down separately in ./agents/transactions.py

Data sources: Eurostat API. See ./data folder

- tec00023 total general government expenditure (annual) 2015-2019 was 44.1-44.3% of GDP (2020: 50.8%)
- tipsau20 growth rate of gross domestic product at market price (quarterly) 2015-2019 
- gov_10a_taxag national accounts tax aggregate (annual) 2015-2020 government sector (S13): approx. 12.5% of GDP
- teina500 (quarterly) Gross household saving rate: between 17 and 22% (peak 27% during Corona crisis)
- literature: Drescher et al. (2020) find a marginal propensity to consume of 51%
