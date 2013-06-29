import numpy as np
import pandas as pd
import re
from string import punctuation
import ujson as json

STOP_WORDS  = list(set(open('./ref/stopwords.txt', 'r').read().split('\n')))
CRIME_WORDS = list(set(open('./ref/crimes.txt', 'r').read().split('\n')))

pd.options.display.line_width = 500
pd.options.display.max_columns = 15
pd.options.display.max_colwidth = 25

def read_file(f = './svu_data/episode_recaps_by_season/recaps_season_1.json'):
    data = json.loads(open(f, 'r').read())['episode_recaps']
    headers = data[0].keys()
    data = np.array([rec.values() for rec in data])
    return data, headers

def read_all_files():
    fmt = './data/svu/episode_recaps_by_season/recaps_season_{0}.json'
    filenames = [fmt.format(i) for i in range(1, 15)]

    for i, f in enumerate(filenames):
        if i == 0:
            data, h = read_file(f)
            df = pd.DataFrame(data, columns=h)
        else:
            data, _ = read_file(f)
            df = df.append(pd.DataFrame(data, columns=h),
                ignore_index=True)

    order_by = ['nth_season', 'nth_episode']
    df[order_by] = df[order_by].astype(int)
    df = df.sort_index(by=order_by, ascending=[1,0])
    df = df.reset_index(drop=True)

    # i inadvertently reversed the order of the episodes...
    # this fixes it
    df['nth_episode'] = 1
    grouped = df.groupby('nth_season')
    df.nth_episode = grouped.nth_episode.cumsum()
    df['show'] = 'svu'

    return df


df = read_all_files()
episodes = pd.read_csv('./data/combined.csv')

combined = pd.merge(episodes,
            df, how='left',
            left_on=['show','nth_season','no_in_season'],
            right_on=['show', 'nth_season', 'nth_episode'])


duped_columns = ['nth_episode', 'episode_title']
combined = combined.drop(duped_columns, axis=1)
combined.corpus[combined.corpus == ''] = None

combined.to_csv('./data/episodes_and_recaps.txt',
    sep='|',
    index=False,
    encoding='utf-8')
