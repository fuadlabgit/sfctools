from sfctools import plot_sankey
import pandas as pd

my_test_data = [pd.DataFrame({
    "from": ["A","A","B","A"],
    "to": ["C","U","C","D"],
    "value": [1.0,8.0,3.0,2.0],
    "color_id":[0,0,0,1] }),

    pd.DataFrame({
    "from": ["C","D","C","C"],
    "to": ["F","G","G","X"],
    "value": [6.0,8.0,.8,5.5],
    "color_id":[0,0,0,0] }),

    pd.DataFrame({
    "from": ["F","G","F","X","G","G"],
    "to": ["H","I","J","H","H","J"],
    "value": [.2,1.0,1.0,10.0,4.0,6.0],
    "color_id":[0,2,0,0,2,0] })
]

plot_sankey(my_test_data,show_values=False)
