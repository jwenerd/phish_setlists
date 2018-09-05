import pandas as pd

def same_set(row1, row2):
    return row1['show_date'] == row2['show_date'] and row1['set'] == row2['set']

def offset_from(df, i, offset):
    return df.iloc[i + offset] if i + offset in df.index else None

class SongDataset:
    def __init__(self, file):
        self.df = pd.read_csv(file)
        # self.df = self.df.drop(columns=['url','location','venue','show_rating','url','comment'])
        self.df['show_date'] =  pd.to_datetime(self.df['show_date'], format='%Y-%m-%d')

        next_titles = [] 
        prev_titles = []

        for index, row in self.df.iterrows():
            next = offset_from(self.df, index, 1)
            prev = offset_from(self.df, index, -1)
            next_title = prev_title = None
            if not next is None and same_set(next,row):
                next_title = next['title']
            if not prev is None and same_set(prev,row):
                prev_title = prev['title']
            
            next_titles.append(next_title)
            prev_titles.append(prev_title)

        self.df['prev_title'] = prev_titles
        self.df['next_title'] = next_titles

    def song_data(self,title):
        song_df = self.df[self.df['title'] == title]
        prevs = {}
        nexts = {}
        for i, row in song_df.iterrows():
            n = 'None' if row['next_title'] == None else row['next_title']
            p = 'None' if row['prev_title'] == None else row['prev_title']
            
            prevs[p] = (prevs[p]+1) if p in prevs else 1
            nexts[n] = (nexts[n]+1) if n in nexts else 1

        data = {
            'prev': prevs,
            'next': nexts,
            'plays': len(song_df),
            'shows': song_df['show_date'].value_counts().size,
            'shows_by_year': song_df['show_date'].drop_duplicates().apply(lambda d: d.year).value_counts().to_dict()
        }
        return data

song_dataset = SongDataset('./data/csv/setlist_data.csv')