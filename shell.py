import pandas as pd
import IPython
# load data

df = pd.read_csv('setlist_data.csv')
df['next_title'] = None

len = len(df)

# setup next song data based set and show
for row in df.itertuples():
    j = row.Index+1
    if j >= len:
        break        
    next = df.iloc[j]

    next_title =  None
    if next['show_date'] == row.show_date and next['set'] == row.set:
        next_title = next['title']
    df.loc[row.Index, 'next_title'] = next_title

# shell 
IPython.embed()
