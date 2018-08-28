import numpy as np
import pandas as pd
from time import sleep
from setlist import get_setlist, parse_setlist

dfl = pd.read_csv('set_dates.csv')
set_dates =  list(map( lambda x: x[0], dfl.values.tolist() ) )
output = []

for idx, set_date in enumerate(set_dates):    
    print((idx,set_date))
    
    setlist = get_setlist(set_date)
    setlist = parse_setlist(setlist)
    if setlist is None:
        pass
    else:
        output.extend(setlist)

df = pd.DataFrame(output)
df['show_date'] = pd.to_datetime(df['show_date'])
df = df.loc[:, ['show_date', 'venue', 'location', 'show_rating', 'set', 'title', 'url', 'comment']]
df.to_csv("data.csv", index=False)
