#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
join_episodes_and_recaps.py

Created by Austin Ogilvie on 2013-06-29.
Copyright (c) 2013. All rights reserved.

This script cleans and combines Law and Order TV data
from several sources. The script expects that the data
has already been downloaded and stored within a particular
directory structure.

Directory structure expected is as follows:

    Project/
    |-- data/
    |   |-- original/
    |   |   |-- episodes/
    |   |   |-- recaps/
    |   |-- svu/
    |   |   |-- episodes/
    |   |   |   |-- season_1.csv
    |   |   |   |-- season_2.csv
    |   |   |   |-- season_3.csv
    |   |   |-- recaps/
    |   |   |   |-- season_1.json
    |   |   |   |-- season_2.json
    |   |   |   |-- season_3.json
    |
    |-- join_episodes_and_recaps.py


Recaps are user-submitted text corpuses from tv.com.
Because these are submitted by users, not every episode will have
a recap / corpus.

Episodes describe data pulled from wikipedia. Records describe individual
episodes along with their air date, viewership, title, etc.

The script will combine the two sources into one pipe delimtied txt file here:

    Project/
    |-- data/
    |   |-- franchise/
    |   |   |   |-- episodes_and_recaps.txt
    |
    |-- join_episodes_and_recaps.py
"""


import numpy as np
import pandas as pd
import re
from string import punctuation
import ujson as json
import os

pd.options.display.line_width = 500
pd.options.display.max_columns = 15
pd.options.display.max_colwidth = 25

def snakify(txt):
    txt = txt.strip().lower()
    exclude = [ch for ch in punctuation if ch != '_']
    txt = ''.join(c for c in txt if c not in exclude)
    return txt.replace(' ', '_')

def utf8ify(txt):
    txt = ' '.join(txt.split())
    try:
        txt = u''.join(txt).encode('utf-8').strip()
    except:
        txt = ''.join(ch for ch in txt if ord(ch) < 128)
        return utf8ify(txt)
    return txt

def ls_files_by_type(p, ext='.json'):
    names = [p+'/'+f for f in os.listdir(p)
            if f.endswith(ext)]
    return names

def json_to_dataframe(f):
    data = json.loads(open(f, 'r').read())['episode_recaps']
    headers = data[0].keys()
    data = np.array([rec.values() for rec in data])
    frame = pd.DataFrame(data, columns=headers)
    return frame

def read_recaps(show):
    p = './data/{show}/{kind}'
    json_path = p.format(show=show, kind='recaps')
    for i, f in enumerate(ls_files_by_type(json_path)):
        if i == 0:
            recaps = json_to_dataframe(f)
        else:
            recaps = recaps.append(json_to_dataframe(f))
    recaps.nth_season = recaps.nth_season.astype(int)
    recaps.nth_episode = recaps.nth_episode.astype(int)
    return recaps

def read_episodes(show):

    def ensure_columns(frame):
        frame.columns = [snakify(col) for col in frame.columns]

        colnames = map(snakify,
            ['Directed by',
            'No. in season',
            'No. in series',
            'Original air date',
            'Production code',
            'Title',
            'U.S. viewers (millions)',
            'Written by',
            'nth_season'])

        swap = {
            'no': 'no_in_series',
            'ep': 'no_in_season',
            'directed_by': 'directed_by',
            'original_airdate':'original_air_date',
            'written_by': 'written_by'
        }

        frame = frame.rename(columns=swap)

        for col in colnames:
            if col not in frame.columns:
                frame[col] = None

        frame = frame.ix[:, colnames]
        return frame

    p = './data/{show}/{kind}'
    csv_path = p.format(show=show, kind='episodes')
    for i, f in enumerate(ls_files_by_type(csv_path, ext='.csv')):
        if i == 0:
            episodes = pd.read_csv(f)
            episodes = ensure_columns(episodes)
        else:
            new = pd.read_csv(f)
            new = ensure_columns(new)
            episodes = episodes.append(new)

    return episodes

for i, show in enumerate(['original', 'svu']):

    recaps = read_recaps(show)
    episodes = read_episodes(show)

    if i == 0:
        combined = pd.merge(episodes,
            recaps, how='left',
            left_on=['nth_season','no_in_season'],
            right_on=['nth_season', 'nth_episode'])
    else:
        new = pd.merge(episodes,
            recaps, how='left',
            left_on=['nth_season','no_in_season'],
            right_on=['nth_season', 'nth_episode'])

        if np.all(new.columns == combined.columns):
            combined = combined.append(new)

combined.title = combined.title.apply(utf8ify)
combined.episode_title = combined.episode_title.apply(utf8ify)

combined.corpus[combined.corpus == ''] = None

combined.original_air_date = \
    combined.original_air_date.replace('', None)

combined.original_air_date = \
    pd.to_datetime(combined.original_air_date)

combined.us_viewers_millions = \
    combined.us_viewers_millions.replace(['', 'N/A'], np.nan)

combined.us_viewers_millions = \
    combined.us_viewers_millions.astype(float) * 1000000

duped_columns = ['nth_episode', 'episode_title']
combined = combined.drop(duped_columns, axis=1)

def sanity_check(frame):
    keys = ['show', 'nth_season']
    grouped = frame.groupby(keys)
    return np.all(grouped.size() == grouped.no_in_season.max())

print pd.crosstab(
    combined.corpus.notnull(),
    combined.show,
    rownames=['Has Corpus']
)

print 'Checksum Passing => %s' % sanity_check(combined)

combined.to_csv('./data/franchise/episodes_and_recaps.txt',
    sep='|',
    index=False,
    encoding='utf-8')

