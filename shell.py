import pandas as pd
import IPython
# load data

df = pd.read_csv('setlist_data.csv')
df['show_date'] =  pd.to_datetime(df['show_date'], format='%Y-%m-%d')

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

def song_data(title):
    song_df = df[df['title'] == title]
    prevs = {}
    nexts = {}
    for i, row in song_df.iterrows():
        n = row['next_title']
        p = row['prev_title']
        prevs[p] = (prevs[p]+1) if p in prevs else 1
        nexts[n] = (nexts[n]+1) if n in nexts else 1

    data = {}
    data['prev'] = prevs
    data['next'] = nexts
    data['plays'] = len(song_df) #total number of times in the data
    data['shows'] = song_df['show_date'].value_counts().size # total number of shows the song was played at 
    data['shows_by_year'] = song_df['show_date'].drop_duplicates().apply(lambda d: d.year).value_counts().to_dict()
    return data

# example 
carini = song_data('Carini')
more = song_data('More')
backwards = song_data('Backwards Down the Number Line')
tweeprise = song_data('Tweezer Reprise')

# shell
IPython.embed()
