import pandas as pd
from app import phish_net_client


def create_file():
    """ This creates the CSV file by downloading all """
    df = pd.DataFrame(phish_net_client.download_all())
    df[["position", "showyear", 'gap']] = df[[
        "position", "showyear", 'gap']].apply(pd.to_numeric)
    df = df.sort_values(['showdate', 'position'], ascending=[True, True])

    # strip all
    def trim_strings(x): return x.strip() if isinstance(x, str) else x
    df = df.map(trim_strings)

    df.to_csv("data/csv/setlist_data.csv", index=False, encoding='utf-8')
