import pandas as pd
from app import phish_net_client


def create_file():
    df = pd.DataFrame(phish_net_client.download_all())
    df[["position", "showyear", 'gap']] = df[[
        "position", "showyear", 'gap']].apply(pd.to_numeric)
    df = df.sort_values(['showdate', 'position'], ascending=[True, True])


create_file()
