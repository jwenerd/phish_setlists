import pandas as pd
import IPython
# load data

df = pd.read_csv('setlist_data.csv')
df = df.drop(columns=['url','location','venue','show_rating','url','comment'])

def same_set(row1, row2):
    return row1['show_date'] == row2['show_date'] and row1['set'] == row2['set']

# setup next solenng data based set and show
next_titles = [] 
prev_titles = []

for index, row in df.iterrows():
    next = df.iloc[index + 1] if index + 1 in df.index else None
    prev = df.iloc[index - 1] if index - 1 in df.index else None
    next_title = prev_title = None
    if not next is None and same_set(next,row):
        next_title = next['title']
    if not prev is None and same_set(prev,row):
        prev_title = prev['title']
    
    next_titles.append(next_title)
    prev_titles.append(prev_title)

df['prev_title'] = prev_titles
df['next_title'] = next_titles



# shell
IPython.embed()
