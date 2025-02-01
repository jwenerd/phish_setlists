import pandas as pd


class SetlistData:
    to_numeric = ["position", "showyear", 'gap']
    to_sort = ['showdate', 'position']

    def __init__(self, data):
        self.df = self.__format(pd.DataFrame(data))

    def __format(self, df):
        df[self.to_numeric] = df[self.to_numeric].apply(pd.to_numeric)
        df = df.sort_values(self.to_sort, ascending=[True, True])

        # strip all, correct encoding from client
        def format_strings(x):
            if isinstance(x, str):
                return x.encode('latin-1').decode('utf-8').strip()
            else:
                return x

        df = df.map(format_strings)
        return df

    def save_all(self):
        self.__save(self.df, 'all')

    def save_years(self):
        for year in self.df['showyear'].unique():
            self.__save(self.df[self.df['showyear'] == year], year)

    def __save(self, df, name):
        df.to_csv(f"data/csv/{name}.csv", index=False, encoding='utf-8')
