import pandas as pd
from datetime import datetime
from typing import List, Union


class PersonalSummaryGenerator:
    DAYS_ORDER = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    MONTHS_ORDER = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]

    def __init__(self, full_df: pd.DataFrame, shows_input: Union[str, List[str]] = 'data/input/shows.txt'):
        self.now = datetime.now()
        self.full_df = full_df.copy()

        # Clean full dataset
        self.full_df['showdate'] = pd.to_datetime(self.full_df['showdate'])
        self.full_df['gap'] = pd.to_numeric(self.full_df['gap'], errors='coerce').fillna(0)
        self.full_df['exclude'] = pd.to_numeric(self.full_df['exclude'], errors='coerce').fillna(0)
        self.full_df['position'] = pd.to_numeric(self.full_df['position'], errors='coerce').fillna(0)
        self.full_df['is_original'] = pd.to_numeric(self.full_df['is_original'], errors='coerce').fillna(0)
        self.full_df['set_str'] = self.full_df['set'].astype(str).str.strip().str.lower()

        # Load personal show dates
        if isinstance(shows_input, str):
            with open(shows_input, 'r', encoding='utf-8') as f:
                raw_dates = [line.strip() for line in f if line.strip()]
        else:
            raw_dates = list(shows_input)

        self.personal_dates = pd.to_datetime(raw_dates)
        self.personal_dates_set = set(self.personal_dates.strftime('%Y-%m-%d'))

        # Filter full dataset for regular (non-excluded) shows
        self.catalog_df = self.full_df[self.full_df['exclude'] == 0].copy()

        # Calculate all-time first play date for each song in catalog
        self.first_plays = self.catalog_df.groupby('song')['showdate'].min().to_dict()

        # Filter personal dataset
        self.my_df = self.catalog_df[self.catalog_df['showdate'].isin(self.personal_dates)].copy()
        self.my_df['is_debut'] = self.my_df.apply(lambda r: r['showdate'] == self.first_plays.get(r['song']), axis=1)

        # Distinct show-level data
        self.shows_df = self.my_df.drop_duplicates(subset=['showdate']).sort_values(by='showdate').copy()
        self.total_shows = len(self.shows_df)

    def _format_date(self, series: pd.Series) -> pd.Series:
        return series.dt.strftime('%Y-%m-%d')

    def get_fun_stats(self) -> str:
        if self.my_df.empty:
            return "No show data found for the provided dates.\n"

        total_songs_heard = len(self.my_df)
        unique_songs_heard = self.my_df['song'].nunique()
        total_catalog_songs = self.catalog_df['song'].nunique()
        catalog_pct = (unique_songs_heard / total_catalog_songs * 100) if total_catalog_songs else 0

        unique_venues = self.shows_df['venue'].nunique()
        unique_cities = self.shows_df['city'].nunique()
        unique_states = self.shows_df['state'].nunique()

        first_show = self.shows_df.iloc[0]
        first_date_str = first_show['showdate'].strftime('%Y-%m-%d')
        first_show_info = f"{first_date_str} ({first_show['venue']}, {first_show['city']}, {first_show['state']})"

        latest_show = self.shows_df.iloc[-1]
        latest_date_str = latest_show['showdate'].strftime('%Y-%m-%d')
        latest_show_info = f"{latest_date_str} ({latest_show['venue']}, {latest_show['city']}, {latest_show['state']})"

        # Originals vs covers
        originals = len(self.my_df[self.my_df['is_original'] == 1])
        covers = len(self.my_df[self.my_df['is_original'] == 0])
        orig_pct = (originals / total_songs_heard * 100) if total_songs_heard else 0
        cover_pct = (covers / total_songs_heard * 100) if total_songs_heard else 0

        song_counts = self.my_df['song'].value_counts()
        one_timers = (song_counts == 1).sum()

        avg_songs_per_show = (total_songs_heard / self.total_shows) if self.total_shows else 0

        stats_lines = [
            f"- **Total Shows Attended:** {self.total_shows}",
            f"- **First Show:** {first_show_info}",
            f"- **Latest Show:** {latest_show_info}",
            f"- **Total Song Performances Heard:** {total_songs_heard} (~{avg_songs_per_show:.1f} songs/show)",
            f"- **Unique Songs Heard:** {unique_songs_heard} ({catalog_pct:.1f}% of Phish's lifetime catalog of {total_catalog_songs} songs)",
            f"- **Songs Seen Only Once:** {one_timers}",
            f"- **Originals vs Covers:** {originals} originals ({orig_pct:.1f}%) / {covers} covers ({cover_pct:.1f}%)",
            f"- **Geographic Footprint:** {unique_venues} venues across {unique_cities} cities and {unique_states} US states/regions"
        ]

        return "\n".join(stats_lines)

    def get_most_common_songs(self, top_n: int = 25) -> pd.DataFrame:
        my_counts = self.my_df['song'].value_counts().head(top_n).reset_index()
        my_counts.columns = ['Song', 'Times Seen']
        my_counts['% of Shows'] = ((my_counts['Times Seen'] / self.total_shows) * 100).map(lambda x: f"{x:.1f}%")

        catalog_counts = self.catalog_df['song'].value_counts()
        my_counts['All-Time Plays'] = my_counts['Song'].map(catalog_counts).fillna(0).astype(int)
        my_counts.insert(0, 'Rank', range(1, len(my_counts) + 1))
        return my_counts

    def get_most_common_by_set(self, set_name: str, top_n: int = 15) -> pd.DataFrame:
        set_df = self.my_df[self.my_df['set_str'] == str(set_name).lower()]
        counts = set_df['song'].value_counts().head(top_n).reset_index()
        counts.columns = ['Song', 'Times Seen']
        counts['% of Shows'] = ((counts['Times Seen'] / self.total_shows) * 100).map(lambda x: f"{x:.1f}%")
        counts.insert(0, 'Rank', range(1, len(counts) + 1))
        return counts

    def get_most_common_show_openers(self, top_n: int = 10) -> pd.DataFrame:
        openers = self.my_df[(self.my_df['set_str'] == '1') & (self.my_df['position'] == 1)]
        counts = openers['song'].value_counts().head(top_n).reset_index()
        counts.columns = ['Song', 'Times Opened']
        counts['% of Shows'] = ((counts['Times Opened'] / self.total_shows) * 100).map(lambda x: f"{x:.1f}%")
        counts.insert(0, 'Rank', range(1, len(counts) + 1))
        return counts

    def get_most_common_set2_openers(self, top_n: int = 10) -> pd.DataFrame:
        set2 = self.my_df[self.my_df['set_str'] == '2']
        if set2.empty:
            return pd.DataFrame(columns=['Rank', 'Song', 'Times Opened', '% of Shows'])
        min_pos = set2.groupby('showdate')['position'].min().reset_index()
        openers = self.my_df.merge(min_pos, on=['showdate', 'position'])
        counts = openers['song'].value_counts().head(top_n).reset_index()
        counts.columns = ['Song', 'Times Opened']
        counts['% of Shows'] = ((counts['Times Opened'] / self.total_shows) * 100).map(lambda x: f"{x:.1f}%")
        counts.insert(0, 'Rank', range(1, len(counts) + 1))
        return counts

    def get_most_common_encores(self, top_n: int = 15) -> pd.DataFrame:
        encores = self.my_df[self.my_df['set_str'].str.startswith('e')]
        counts = encores['song'].value_counts().head(top_n).reset_index()
        counts.columns = ['Song', 'Times Heard']
        counts['% of Shows'] = ((counts['Times Heard'] / self.total_shows) * 100).map(lambda x: f"{x:.1f}%")
        counts.insert(0, 'Rank', range(1, len(counts) + 1))
        return counts

    def get_one_time_songs(self) -> pd.DataFrame:
        song_counts = self.my_df['song'].value_counts()
        one_time_songs = song_counts[song_counts == 1].index

        one_df = self.my_df[self.my_df['song'].isin(one_time_songs)].copy()
        one_df = one_df.sort_values(by='song')
        one_df['Date'] = self._format_date(one_df['showdate'])
        one_df = one_df[['song', 'Date', 'venue', 'city', 'state']]
        one_df.columns = ['Song', 'Date', 'Venue', 'City', 'State']
        return one_df

    def get_shows_by_year(self) -> pd.DataFrame:
        shows = self.shows_df.copy()
        shows['Year'] = shows['showdate'].dt.year
        year_counts = shows['Year'].value_counts().sort_index().reset_index()
        year_counts.columns = ['Year', 'Shows']

        # Unique songs per year
        my_with_year = self.my_df.copy()
        my_with_year['Year'] = my_with_year['showdate'].dt.year
        unique_songs = my_with_year.groupby('Year')['song'].nunique().reset_index()
        unique_songs.columns = ['Year', 'Unique Songs']

        merged = pd.merge(year_counts, unique_songs, on='Year')
        merged['% of Total'] = ((merged['Shows'] / self.total_shows) * 100).map(lambda x: f"{x:.1f}%")
        merged = merged[['Year', 'Shows', '% of Total', 'Unique Songs']]
        return merged

    def get_shows_by_month(self) -> pd.DataFrame:
        shows = self.shows_df.copy()
        shows['Month'] = shows['showdate'].dt.month_name()
        month_counts = shows['Month'].value_counts().reindex(self.MONTHS_ORDER).fillna(0).astype(int).reset_index()
        month_counts.columns = ['Month', 'Shows']
        month_counts['% of Total'] = ((month_counts['Shows'] / self.total_shows) * 100).map(lambda x: f"{x:.1f}%")
        return month_counts[month_counts['Shows'] > 0]

    def get_shows_by_day_of_week(self) -> pd.DataFrame:
        shows = self.shows_df.copy()
        shows['Day'] = shows['showdate'].dt.day_name()
        day_counts = shows['Day'].value_counts().reindex(self.DAYS_ORDER).fillna(0).astype(int).reset_index()
        day_counts.columns = ['Day of Week', 'Shows']
        day_counts['% of Total'] = ((day_counts['Shows'] / self.total_shows) * 100).map(lambda x: f"{x:.1f}%")
        return day_counts

    def get_shows_by_state(self) -> pd.DataFrame:
        shows = self.shows_df.copy()
        state_counts = shows.groupby('state').agg(
            Shows=('showdate', 'count'),
            Venues=('venue', 'nunique'),
            Cities=('city', 'nunique')
        ).sort_values(by='Shows', ascending=False).reset_index()
        state_counts.columns = ['State', 'Shows', 'Venues', 'Cities']
        state_counts['% of Total'] = ((state_counts['Shows'] / self.total_shows) * 100).map(lambda x: f"{x:.1f}%")
        state_counts = state_counts[['State', 'Shows', '% of Total', 'Venues', 'Cities']]
        return state_counts

    def get_top_venues(self, top_n: int = 15) -> pd.DataFrame:
        shows = self.shows_df.copy()
        venues = shows.groupby(['venue', 'city', 'state']).agg(
            Shows=('showdate', 'count'),
            First_Seen=('showdate', 'min'),
            Last_Seen=('showdate', 'max')
        ).sort_values(by='Shows', ascending=False).head(top_n).reset_index()

        venues['First Seen'] = self._format_date(venues['First_Seen'])
        venues['Last Seen'] = self._format_date(venues['Last_Seen'])
        venues.insert(0, 'Rank', range(1, len(venues) + 1))
        venues = venues[['Rank', 'venue', 'city', 'state', 'Shows', 'First Seen', 'Last Seen']]
        venues.columns = ['Rank', 'Venue', 'City', 'State', 'Shows', 'First Seen', 'Last Seen']
        return venues

    def get_biggest_bustouts_seen(self, top_n: int = 15) -> pd.DataFrame:
        # Exclude song debuts from bustout calculation
        bustouts_df = self.my_df[~self.my_df['is_debut']].sort_values(by='gap', ascending=False).drop_duplicates(subset=['song', 'showdate']).head(top_n).copy()
        bustouts_df['Date'] = self._format_date(bustouts_df['showdate'])
        bustouts_df['Gap'] = bustouts_df['gap'].astype(int)
        bustouts_df.insert(0, 'Rank', range(1, len(bustouts_df) + 1))
        result = bustouts_df[['Rank', 'song', 'Gap', 'Date', 'venue', 'city', 'state']]
        result.columns = ['Rank', 'Song', 'Gap (Shows)', 'Date Played', 'Venue', 'City', 'State']
        return result

    def get_debuts_seen(self) -> pd.DataFrame:
        debuts = self.my_df[self.my_df['is_debut']].sort_values(by='showdate', ascending=False).copy()
        debuts['Date'] = self._format_date(debuts['showdate'])
        result = debuts[['song', 'Date', 'venue', 'city', 'state']]
        result.columns = ['Song', 'Debut Date', 'Venue', 'City', 'State']
        return result

    def get_white_whales(self, top_n: int = 15) -> pd.DataFrame:
        all_song_counts = self.catalog_df['song'].value_counts()
        my_songs = set(self.my_df['song'].unique())
        unseen_counts = all_song_counts[~all_song_counts.index.isin(my_songs)].head(top_n).reset_index()
        unseen_counts.columns = ['Song', 'All-Time Phish Plays']
        unseen_counts.insert(0, 'Rank', range(1, len(unseen_counts) + 1))
        return unseen_counts

    def get_personal_bustout_shows(self, top_n: int = 10) -> pd.DataFrame:
        # Calculate show-level gap metrics excluding debuts
        non_debuts = self.my_df[~self.my_df['is_debut']].copy()
        show_gaps = non_debuts.groupby(['showdate', 'venue', 'city', 'state']).agg(
            avg_gap=('gap', 'mean'),
            max_gap=('gap', 'max'),
            song_count=('song', 'count')
        ).reset_index()

        show_gaps = show_gaps[show_gaps['song_count'] > 10]
        show_gaps = show_gaps.sort_values(by='avg_gap', ascending=False).head(top_n).copy()
        show_gaps['Date'] = self._format_date(show_gaps['showdate'])
        show_gaps['Avg Gap'] = show_gaps['avg_gap'].round(1)
        show_gaps['Max Gap'] = show_gaps['max_gap'].astype(int)
        show_gaps.insert(0, 'Rank', range(1, len(show_gaps) + 1))
        result = show_gaps[['Rank', 'Date', 'venue', 'city', 'state', 'Avg Gap', 'Max Gap']]
        result.columns = ['Rank', 'Date', 'Venue', 'City', 'State', 'Avg Gap', 'Max Gap']
        return result

    def generate_markdown(self) -> str:
        overview = self.get_fun_stats()
        common_songs = self.get_most_common_songs(25).to_markdown(index=False)
        set1_songs = self.get_most_common_by_set('1', 15).to_markdown(index=False)
        set2_songs = self.get_most_common_by_set('2', 15).to_markdown(index=False)
        show_openers = self.get_most_common_show_openers(10).to_markdown(index=False)
        set2_openers = self.get_most_common_set2_openers(10).to_markdown(index=False)
        encores = self.get_most_common_encores(15).to_markdown(index=False)
        one_timers_df = self.get_one_time_songs()
        one_timers_table = one_timers_df.to_markdown(index=False)
        shows_by_year = self.get_shows_by_year().to_markdown(index=False)
        shows_by_month = self.get_shows_by_month().to_markdown(index=False)
        shows_by_dow = self.get_shows_by_day_of_week().to_markdown(index=False)
        shows_by_state = self.get_shows_by_state().to_markdown(index=False)
        top_venues = self.get_top_venues(15).to_markdown(index=False)
        bustouts = self.get_biggest_bustouts_seen(15).to_markdown(index=False)
        debuts_df = self.get_debuts_seen()
        debuts_table = debuts_df.to_markdown(index=False) if not debuts_df.empty else "No song debuts attended."
        white_whales = self.get_white_whales(15).to_markdown(index=False)
        bustout_shows = self.get_personal_bustout_shows(10).to_markdown(index=False)

        md = f"""# Personal Phish Stats Summary

*Generated on {self.now.strftime('%Y-%m-%d')} based on `{self.total_shows}` attended shows.*

---

## 🎸 Overview & Highlights

{overview}

---

## 🏆 Most Common Songs Seen

### Top 25 Songs Overall
{common_songs}

### Top 15 Set 1 Songs
{set1_songs}

### Top 15 Set 2 Songs
{set2_songs}

---

## 🚪 Openers & Encores

### Top 10 Show Openers (Set 1 Opener)
{show_openers}

### Top 10 Set 2 Openers
{set2_openers}

### Top 15 Encores
{encores}

---

## 📅 Chronological & Geographic Breakdown

### Shows by Year
{shows_by_year}

### Shows by Month
{shows_by_month}

### Shows by Day of Week
{shows_by_dow}

### Shows by State / Region
{shows_by_state}

### Top Venues Visited
{top_venues}

---

## ⚡ Bust-Outs, Debuts & Rarities

### Biggest Bust-Outs Witnessed (Largest Show Gaps)
{bustouts}

### Song Debuts Witnessed ({len(debuts_df)} Total)
{debuts_table}

### Personal 'Bust-Out' Shows (Highest Average Song Gap)
{bustout_shows}

### Top 15 "White Whales" (Most Played Songs Never Seen Live)
{white_whales}

---

## 🦄 Songs Seen Only Once ({len(one_timers_df)} Songs)

{one_timers_table}
"""
        return md

    def write_to_file(self, filename: str = 'MY-SUMMARY.md'):
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(self.generate_markdown())
