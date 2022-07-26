from sfctools import convert_quarterly_to_datetime, stretch_to_length, convert_numeric
from sfctools import Settings
import pandas as pd 
import matplotlib.pyplot as plt
import numpy as np 

"""
Small data preprocessing pipeline
"""

Settings().read_from_yaml("../settings.yml")
T = Settings().get_hyperparameter("T") # simulation length

"""
GDP data pre-process
"""
gdp_df = pd.read_csv("raw/tipsau20_gdp.csv",delimiter=";",skiprows=1) # .to_numeric()
gdp_df.index = gdp_df["Quarter"]
del gdp_df["Quarter"]
del gdp_df["GDP"]

gdp_df = gdp_df.iloc[1:,:]
gdp_df = convert_numeric(gdp_df)

# 1. convert quarterly to datetime
gdp_df = convert_quarterly_to_datetime(gdp_df) 

# 2. stretch data to simulation length
gdp_df = stretch_to_length(gdp_df,T,method="linear")

# 3. save 
arr = gdp_df["Percentage Change"].to_numpy()
np.savetxt("processed/tipsau20_gdp_processed.txt",arr)
