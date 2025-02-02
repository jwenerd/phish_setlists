import pysh
import os
import itertools
import concurrent.futures

if "PHISH_API_KEY" in os.environ:
    apikey = os.environ["PHISH_API_KEY"]
else:
    raise ValueError(
        "Must set PHISH_API_KEY enviromental variable with api.phish.net key!")


SONG_KEYS = ['showdate', 'showyear', 'exclude', 'position', 'transition', 'set', 'isjam',
                         'isreprise', 'gap', 'tourname', 'tourwhen', 'song', 'nickname', 'is_original',
                         'venue', 'city', 'state', 'country', 'trans_mark']


class PhishNetClient():
    def __init__(self):
        self.client = pysh.Client()
        self._all_shows = None

    def get_all_shows(self):
        if self._all_shows:
            return self._all_shows
        all_shows = self.client.get_shows(parameters=pysh.Parameters(order_by='showdate'))
        self._all_shows = [show for show in all_shows if str(show.get('artist_name')).lower() == 'phish']
        return self._all_shows

    def get_setlist_by_date(self, date):
        return self.client.get_setlists(column="showdate", value=date)

    def get_setlist_data(self, year=None):
        shows = self.get_all_shows()
        if year:
            shows = [show for show in shows if show['showyear'] == str(year)]

        print(f"  downloading: year={year}, {len(shows)} shows")

        with concurrent.futures.ThreadPoolExecutor() as executor:
            setlists = list(executor.map(lambda show: self.get_setlist_by_date(show['showdate']), shows))

        setlist_data = []
        for setlist in setlists:
            for index, setlist_song in enumerate(setlist.copy()):
                setlist[index] = {key: setlist_song[key] for key in SONG_KEYS if key in setlist_song}
            setlist_data.append(setlist)

        return list(itertools.chain(*setlist_data))  # flatten

    def download_all(self):
        years = set([show['showyear'] for show in self.get_all_shows()])
        year_data = [self.get_setlist_data(year) for year in sorted(years)]
        return list(itertools.chain(*year_data))  # flatten


phish_net_client = PhishNetClient()
