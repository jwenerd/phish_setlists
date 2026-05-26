import pandas as pd
from datetime import datetime, timedelta

ONE_YEAR = 365
TWO_YEARS = 730
FIVE_YEARS = 1825

class SummaryGenerator:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        
        # 1. Consolidate Data Cleaning
        self.df['showdate'] = pd.to_datetime(self.df['showdate'])
        self.df['gap'] = pd.to_numeric(self.df['gap'], errors='coerce').fillna(0)
        self.df['isjam'] = pd.to_numeric(self.df['isjam'], errors='coerce').fillna(0)
        
        self.now = datetime.now()
        
        # 2. Cache Filtered DataFrames
        self.df_1_year = self._filter_past_days(ONE_YEAR)
        self.df_2_years = self._filter_past_days(TWO_YEARS)
        self.df_5_years = self._filter_past_days(FIVE_YEARS)

    def _filter_past_days(self, days: int):
        cutoff_date = self.now - timedelta(days=days)
        return self.df[self.df['showdate'] >= cutoff_date]
        
    def _format_date(self, series: pd.Series):
        # 3. Date Formatting Helper
        return series.dt.strftime('%Y-%m-%d')
        
    def _get_df_by_days(self, days: int):
        if days == ONE_YEAR:
            return self.df_1_year
        elif days == TWO_YEARS:
            return self.df_2_years
        elif days == FIVE_YEARS:
            return self.df_5_years
        return self._filter_past_days(days)

    def get_show_count(self, days: int) -> int:
        return self._get_df_by_days(days)['showdate'].nunique()

    def get_most_common_songs(self, days: int, top_n: int = 10):
        recent_df = self._get_df_by_days(days)
        counts = recent_df['song'].value_counts().head(top_n).reset_index()
        counts.columns = ['Song', 'Times Played']
        return counts

    def get_newest_songs(self, days: int):
        first_played = self.df.groupby('song')['showdate'].min().reset_index()
        cutoff_date = self.now - timedelta(days=days)
        
        new_songs = first_played[first_played['showdate'] >= cutoff_date].copy()
        new_songs.columns = ['Song', 'Debut Date']
        
        if new_songs.empty:
            return pd.DataFrame(columns=['Song', 'Debut Date', 'Times Played'])
            
        recent_df = self._get_df_by_days(days)
        play_counts = recent_df[recent_df['song'].isin(new_songs['Song'])]['song'].value_counts().reset_index()
        play_counts.columns = ['Song', 'Times Played']
        
        merged = pd.merge(new_songs, play_counts, on='Song', how='left')
        merged['Times Played'] = merged['Times Played'].fillna(0).astype(int)
        
        merged = merged.sort_values(by='Debut Date', ascending=False)
        merged['Debut Date'] = self._format_date(merged['Debut Date'])
        return merged

    def get_bustout_shows(self, days: int, top_n: int = 5):
        recent_df = self._get_df_by_days(days).copy()
        
        show_gaps = recent_df.groupby(['showdate', 'venue', 'city', 'state']).agg(
            avg_gap=('gap', 'mean'),
            song_count=('song', 'count')
        ).reset_index()
        
        show_gaps = show_gaps[show_gaps['song_count'] > 10]
        show_gaps = show_gaps.sort_values(by='avg_gap', ascending=False).head(top_n)
        
        show_gaps['showdate'] = self._format_date(show_gaps['showdate'])
        show_gaps['avg_gap'] = show_gaps['avg_gap'].round(1)
        show_gaps = show_gaps[['showdate', 'venue', 'city', 'state', 'avg_gap']]
        show_gaps.columns = ['Date', 'Venue', 'City', 'State', 'Avg Gap']
        return show_gaps

    def get_marathon_shows(self, days: int, top_n: int = 5):
        recent_df = self._get_df_by_days(days).copy()
        show_counts = recent_df.groupby(['showdate', 'venue', 'city', 'state']).agg(
            unique_songs=('song', 'nunique')
        ).reset_index()
        show_counts = show_counts.sort_values(by='unique_songs', ascending=False).head(top_n)
        
        show_counts['showdate'] = self._format_date(show_counts['showdate'])
        show_counts = show_counts[['showdate', 'venue', 'city', 'state', 'unique_songs']]
        show_counts.columns = ['Date', 'Venue', 'City', 'State', 'Unique Songs']
        return show_counts
        
    def get_rarest_songs(self, days: int, top_n: int = 10):
        recent_df = self._get_df_by_days(days).copy()
        
        idx = recent_df.groupby('song')['gap'].idxmax()
        rarest = recent_df.loc[idx].sort_values(by='gap', ascending=False).head(top_n)
        rarest['showdate'] = self._format_date(rarest['showdate'])
        rarest = rarest[['song', 'showdate', 'gap']]
        rarest.columns = ['Song', 'Date Played', 'Gap']
        return rarest

    def generate_markdown(self) -> str:
        shows_1_yr = self.get_show_count(ONE_YEAR)
        shows_2_yr = self.get_show_count(TWO_YEARS)
        shows_5_yr = self.get_show_count(FIVE_YEARS)
        
        # 4. Markdown Generation Boilerplate
        template = f"""# Phish Setlist Summary

*Generated on {self.now.strftime('%Y-%m-%d')}*

## Most Common Songs

### Past 1 Year ({shows_1_yr} Shows)

{self.get_most_common_songs(ONE_YEAR).to_markdown(index=False)}

### Past 2 Years ({shows_2_yr} Shows)

{self.get_most_common_songs(TWO_YEARS).to_markdown(index=False)}

### Past 5 Years ({shows_5_yr} Shows)

{self.get_most_common_songs(FIVE_YEARS).to_markdown(index=False)}

## Newest Songs (Debuts Past 2 Years - {shows_2_yr} Shows)

{self.get_newest_songs(TWO_YEARS).to_markdown(index=False)}

## Notable Shows with Variety (Past 5 Years - {shows_5_yr} Shows)

### The 'Bust-Out' Shows (Highest Avg Gap)

{self.get_bustout_shows(FIVE_YEARS).to_markdown(index=False)}

### The Marathons (Most Unique Songs)

{self.get_marathon_shows(FIVE_YEARS).to_markdown(index=False)}

## Rarest Songs Played (Past 1 Year - {shows_1_yr} Shows)

{self.get_rarest_songs(ONE_YEAR).to_markdown(index=False)}
"""
        return template

    def write_to_file(self, filename: str):
        with open(filename, 'w') as f:
            f.write(self.generate_markdown())

