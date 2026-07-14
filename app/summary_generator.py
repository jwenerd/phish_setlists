import pandas as pd
from datetime import datetime, timedelta

SIX_MONTHS = 182
ONE_YEAR = 365
TWO_YEARS = 730
FIVE_YEARS = 1825
TEN_YEARS = 3650

class SummaryGenerator:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        
        # 1. Consolidate Data Cleaning
        self.df['showdate'] = pd.to_datetime(self.df['showdate'])
        self.df['gap'] = pd.to_numeric(self.df['gap'], errors='coerce').fillna(0)
        self.df['isjam'] = pd.to_numeric(self.df['isjam'], errors='coerce').fillna(0)
        
        self.now = datetime.now()
        
        # Determine most recent tour
        latest_date = self.df['showdate'].max()
        latest_shows = self.df[self.df['showdate'] == latest_date]
        if not latest_shows.empty:
            self.most_recent_tour = latest_shows['tourname'].iloc[0]
        else:
            self.most_recent_tour = None
        
        # 2. Cache Filtered DataFrames
        self.df_6_months = self._filter_past_days(SIX_MONTHS)
        self.df_1_year = self._filter_past_days(ONE_YEAR)
        self.df_2_years = self._filter_past_days(TWO_YEARS)
        self.df_5_years = self._filter_past_days(FIVE_YEARS)
        self.df_10_years = self._filter_past_days(TEN_YEARS)
        if self.most_recent_tour:
            self.df_most_recent_tour = self.df[self.df['tourname'] == self.most_recent_tour]
        else:
            self.df_most_recent_tour = self.df.iloc[0:0]

    def _filter_past_days(self, days: int):
        cutoff_date = self.now - timedelta(days=days)
        return self.df[self.df['showdate'] >= cutoff_date]
        
    def _format_date(self, series: pd.Series):
        # 3. Date Formatting Helper
        return series.dt.strftime('%Y-%m-%d')
        
    def _get_df_by_timeframe(self, timeframe):
        if timeframe == SIX_MONTHS:
            return self.df_6_months
        elif timeframe == ONE_YEAR:
            return self.df_1_year
        elif timeframe == TWO_YEARS:
            return self.df_2_years
        elif timeframe == FIVE_YEARS:
            return self.df_5_years
        elif timeframe == TEN_YEARS:
            return self.df_10_years
        elif timeframe == 'most_recent_tour':
            return self.df_most_recent_tour
        
        if isinstance(timeframe, int):
            return self._filter_past_days(timeframe)
        return self.df

    def get_show_count(self, timeframe) -> int:
        return self._get_df_by_timeframe(timeframe)['showdate'].nunique()

    def get_most_common_songs(self, timeframe, top_n: int = 10):
        recent_df = self._get_df_by_timeframe(timeframe)
        counts = recent_df['song'].value_counts().head(top_n).reset_index()
        counts.columns = ['Song', 'Times Played']
        return counts

    def get_newest_songs(self, timeframe):
        first_played = self.df.groupby('song')['showdate'].min().reset_index()
        if timeframe == 'most_recent_tour':
            tour_df = self._get_df_by_timeframe(timeframe)
            if tour_df.empty:
                return pd.DataFrame(columns=['Song', 'Debut Date', 'Times Played'])
            tour_songs = tour_df['song'].unique()
            new_songs = first_played[first_played['song'].isin(tour_songs)].copy()
            min_tour_date = tour_df['showdate'].min()
            new_songs = new_songs[new_songs['showdate'] >= min_tour_date]
        else:
            if isinstance(timeframe, int):
                cutoff_date = self.now - timedelta(days=timeframe)
            else:
                cutoff_date = self.now - timedelta(days=TWO_YEARS)
            new_songs = first_played[first_played['showdate'] >= cutoff_date].copy()
        
        new_songs.columns = ['Song', 'Debut Date']
        
        if new_songs.empty:
            return pd.DataFrame(columns=['Song', 'Debut Date', 'Times Played'])
            
        recent_df = self._get_df_by_timeframe(timeframe)
        play_counts = recent_df[recent_df['song'].isin(new_songs['Song'])]['song'].value_counts().reset_index()
        play_counts.columns = ['Song', 'Times Played']
        
        merged = pd.merge(new_songs, play_counts, on='Song', how='left')
        merged['Times Played'] = merged['Times Played'].fillna(0).astype(int)
        
        merged = merged.sort_values(by='Debut Date', ascending=False)
        merged['Debut Date'] = self._format_date(merged['Debut Date'])
        return merged

    def get_bustout_shows(self, timeframe, top_n: int = 5):
        recent_df = self._get_df_by_timeframe(timeframe).copy()
        
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

    def get_marathon_shows(self, timeframe, top_n: int = 5):
        recent_df = self._get_df_by_timeframe(timeframe).copy()
        show_counts = recent_df.groupby(['showdate', 'venue', 'city', 'state']).agg(
            unique_songs=('song', 'nunique')
        ).reset_index()
        show_counts = show_counts.sort_values(by='unique_songs', ascending=False).head(top_n)
        
        show_counts['showdate'] = self._format_date(show_counts['showdate'])
        show_counts = show_counts[['showdate', 'venue', 'city', 'state', 'unique_songs']]
        show_counts.columns = ['Date', 'Venue', 'City', 'State', 'Unique Songs']
        return show_counts
        
    def get_rarest_songs(self, timeframe, top_n: int = 10):
        recent_df = self._get_df_by_timeframe(timeframe).copy()
        
        idx = recent_df.groupby('song')['gap'].idxmax()
        rarest = recent_df.loc[idx].sort_values(by='gap', ascending=False).head(top_n)
        rarest['showdate'] = self._format_date(rarest['showdate'])
        rarest = rarest[['song', 'showdate', 'gap']]
        rarest.columns = ['Song', 'Date Played', 'Gap']
        return rarest

    def get_fun_stats(self, timeframe) -> str:
        df = self._get_df_by_timeframe(timeframe).copy()
        if df.empty:
            return "No data for this timeframe.\n"
            
        shows = df['showdate'].nunique()
        venues = df['venue'].nunique()
        total_songs = len(df)
        unique_songs = df['song'].nunique()
        
        song_counts = df['song'].value_counts()
        one_timers = (song_counts == 1).sum()
        
        # Bust-outs (gap > 50)
        bustouts = len(df[df['gap'] > 50])
        
        # Most common opener
        df['set_str'] = df['set'].astype(str)
        set1_openers = df[(df['set_str'] == '1') & (df['position'] == 1)]
        if not set1_openers.empty:
            top_opener = set1_openers['song'].value_counts().index[0]
            top_opener_count = set1_openers['song'].value_counts().iloc[0]
        else:
            top_opener = "N/A"
            top_opener_count = 0
            
        # Most common encore
        encores = df[df['set_str'] == 'e']
        if not encores.empty:
            encore_first_songs = encores.loc[encores.groupby('showdate')['position'].idxmin()]
            if not encore_first_songs.empty:
                top_encore = encore_first_songs['song'].value_counts().index[0]
                top_encore_count = encore_first_songs['song'].value_counts().iloc[0]
            else:
                top_encore = "N/A"
                top_encore_count = 0
        else:
            top_encore = "N/A"
            top_encore_count = 0
            
        stats_lines = [
            f"{shows} shows across {venues} venues",
            f"{total_songs} total songs played",
            f"Number of unique songs played: {unique_songs}",
            f"{one_timers} songs were played exactly once",
            f"Bust-outs (Gap > 50): {bustouts}"
        ]
        
        if top_opener_count > 1:
            stats_lines.append(f"Most common show opener: {top_opener} ({top_opener_count} times)")
            
        if top_encore_count > 1:
            stats_lines.append(f"Most common encore: {top_encore} ({top_encore_count} times)")
            
        return "\n\n".join(stats_lines) + "\n"

    def generate_markdown(self) -> str:
        shows_6_mo = self.get_show_count(SIX_MONTHS)
        shows_1_yr = self.get_show_count(ONE_YEAR)
        shows_2_yr = self.get_show_count(TWO_YEARS)
        shows_5_yr = self.get_show_count(FIVE_YEARS)
        shows_10_yr = self.get_show_count(TEN_YEARS)
        
        tour_fun_stats = ""
        tour_common_songs = ""
        if self.most_recent_tour:
            shows_recent_tour = self.get_show_count('most_recent_tour')
            tour_fun_stats = f"""
### Most Recent Tour: {self.most_recent_tour} ({shows_recent_tour} Shows)
{self.get_fun_stats('most_recent_tour')}"""
            tour_common_songs = f"""
### Most Recent Tour: {self.most_recent_tour} ({shows_recent_tour} Shows)

{self.get_most_common_songs('most_recent_tour').to_markdown(index=False)}
"""
        
        # 4. Markdown Generation Boilerplate
        template = f"""# Phish Setlist Summary
 
*Generated on {self.now.strftime('%Y-%m-%d')}*
 
## Fun with Stats
{tour_fun_stats}
### Past 6 Months ({shows_6_mo} Shows)
{self.get_fun_stats(SIX_MONTHS)}
 
### Past 1 Year ({shows_1_yr} Shows)
{self.get_fun_stats(ONE_YEAR)}
 
### Past 2 Years ({shows_2_yr} Shows)
{self.get_fun_stats(TWO_YEARS)}
 
### Past 5 Years ({shows_5_yr} Shows)
{self.get_fun_stats(FIVE_YEARS)}
 
### Past 10 Years ({shows_10_yr} Shows)
{self.get_fun_stats(TEN_YEARS)}
 
## Most Common Songs
{tour_common_songs}
### Past 6 Months ({shows_6_mo} Shows)
 
{self.get_most_common_songs(SIX_MONTHS).to_markdown(index=False)}
 
### Past 1 Year ({shows_1_yr} Shows)
 
{self.get_most_common_songs(ONE_YEAR).to_markdown(index=False)}
 
### Past 2 Years ({shows_2_yr} Shows)
 
{self.get_most_common_songs(TWO_YEARS).to_markdown(index=False)}
 
### Past 5 Years ({shows_5_yr} Shows)
 
{self.get_most_common_songs(FIVE_YEARS).to_markdown(index=False)}
 
### Past 10 Years ({shows_10_yr} Shows)
 
{self.get_most_common_songs(TEN_YEARS).to_markdown(index=False)}
 
## Newest Songs (Debuts Past 2 Years - {shows_2_yr} Shows)
 
{self.get_newest_songs(TWO_YEARS).to_markdown(index=False)}
 
## Notable Shows with Variety (Past 5 Years - {shows_5_yr} Shows)
 
### The 'Bust-Out' Shows (Highest Avg Gap - Past 5 Years)
 
{self.get_bustout_shows(FIVE_YEARS).to_markdown(index=False)}
 
### The 'Bust-Out' Shows (Highest Avg Gap - Past 10 Years)
 
{self.get_bustout_shows(TEN_YEARS).to_markdown(index=False)}
 
### The Marathons (Most Unique Songs - Past 5 Years)
 
{self.get_marathon_shows(FIVE_YEARS).to_markdown(index=False)}
 
### The Marathons (Most Unique Songs - Past 10 Years)
 
{self.get_marathon_shows(TEN_YEARS).to_markdown(index=False)}
 
## Rarest Songs Played (Past 1 Year - {shows_1_yr} Shows)
 
{self.get_rarest_songs(ONE_YEAR).to_markdown(index=False)}
"""
        return template

    def write_to_file(self, filename: str):
        with open(filename, 'w') as f:
            f.write(self.generate_markdown())

