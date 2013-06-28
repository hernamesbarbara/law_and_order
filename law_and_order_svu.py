import numpy as np
import pandas as pd
import re
from string import punctuation
import ujson as json

STOP_WORDS  = list(set(open('./ref/stopwords.txt', 'r').read().split('\n')))
CRIME_WORDS = list(set(open('./ref/crimes.txt', 'r').read().split('\n')))

def read_file(f = './svu_data/episode_recaps_by_season/recaps_season_1.json'):
    data = json.loads(open(f, 'r').read())['episode_recaps']
    headers = data[0].keys()
    data = np.array([rec.values() for rec in data])
    return data, headers

def read_all_files():
    fmt = './svu_data/episode_recaps_by_season/recaps_season_{0}.json'
    filenames = [fmt.format(i) for i in range(1, 15)]

    for i, f in enumerate(filenames):
        if i == 0:
            data, h = read_file(f)
            df = pd.DataFrame(data, columns=h)
        else:
            data, _ = read_file(f)
            df = df.append(pd.DataFrame(data, columns=h),ignore_index=True)

    order_by = ['nth_season', 'nth_episode']
    df[order_by] = df[order_by].astype(int)
    df = df.sort_index(by=order_by, ascending=[1,0])
    df = df.reset_index()

    # i inadvertently reversed the order of the episodes...
    # this fixes it
    df['nth_episode'] = 1
    grouped = df.groupby('nth_season')
    df.nth_episode = grouped.nth_episode.cumsum()

    return df


df = read_all_files()
episodes = pd.read_csv('./svu_data/law_and_order_episodes.csv')

df = pd.merge(episodes, df, how='left',
              left_on=['season','season_num'],
              right_on=['nth_season', 'nth_episode'])

df = df.drop(['season', 'index', 'season_num', 'episode_title'], axis=1)
df = df.rename(columns={'series_num':'nth_episode_in_series'})

reordered = ['nth_season'
            , 'nth_episode'
            , 'nth_episode_in_series'
            , 'title'
            , 'director'
            , 'writer'
            , 'code'
            , 'viewership'
            , 'source'
            , 'corpus_url'
            , 'corpus']

df = df.ix[:, reordered]

# df.to_csv('./svu_data/law_and_order_svu_with_recaps.txt',
#     sep='|',
#     index=False,
#     encoding='utf-8')

