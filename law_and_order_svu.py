import numpy as np
import pandas as pd
import re
from string import punctuation
import ujson as json

episodes = pd.read_csv('./law_and_order_episodes.csv')


def read_file(f = './episode_recaps_by_season/recaps_season_1.json'):
    data = json.loads(open(f, 'r').read())
    data = data['episode_recaps']
    headers = data[0].keys()
    data = np.array([rec.values() for rec in data])
    return data, headers


def read_all_files():
    fmt = './episode_recaps_by_season/recaps_season_{0}.json'
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
    df = df.sort_index(by=order_by, ascending=[1,1])
    df = df.reset_index()

    return df


df = read_all_files()


df = pd.merge(episodes,
              df,
              left_on=['season','season_num'],
              right_on=['nth_season', 'nth_episode'],
              how='left')

print df[['nth_season', 'season_num', 'nth_episode', 'episode_title']].head(50)

