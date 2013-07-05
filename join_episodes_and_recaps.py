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
from datetime import date, datetime

pd.options.display.width = 500
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
    files = ls_files_by_type(json_path)
    if len(files) == 0:
        return []

    for i, f in enumerate(files):
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
        frame['show_name'] = show

        colnames = map(snakify,
            ['show_name',
            'Directed by',
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
            'us_viewers_millions29': 'us_viewers_millions',
            'season_no': 'no_in_season',
            'series_no': 'no_in_series',
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

def parse_title(txt, rg = re.compile('(.*)\\[\\d+\\]$')):
    m = rg.findall(txt)
    if len(m):
        txt = m[0].strip()
        txt = txt.replace('"', '')
    return txt

def parse_date(txt, rg=re.compile('.*?(\\(.*\\))')):
    try:
        d = pd.to_datetime(txt)
        if isinstance(d, (date, datetime)):
            return d

        elif len(d) >= 25:
            matches = rg.search(txt)
            if matches:
                d = matches.group(1)
                d = d.strip("()")
                return pd.to_datetime(d)

    except Exception, e:
        print 'Unable to parse date'
        print e
        return txt

BRACKETS = re.compile('([+-]?\\d*\\.\\d+)(?![-+0-9\\.])',
        re.IGNORECASE|re.DOTALL)

show_names = ['criminal_intent','trial_by_jury', 'svu', 'original']

combined=None
for i, show in enumerate(show_names):
    print 'Processing %s' % show

    episodes = read_episodes(show)
    print 'Found %d episodes' % len(episodes)
    if len(episodes) > 0:
        episodes.original_air_date = episodes.original_air_date.apply(parse_date)
        episodes.title = episodes.title.apply(parse_title)
        episodes.title = episodes.title.str.strip('"')
        episodes.title = episodes.title.apply(utf8ify)
        episodes.title = episodes.title.str.title()

        episodes.original_air_date = \
            episodes.original_air_date.replace('', None)

        episodes.original_air_date = \
            pd.to_datetime(episodes.original_air_date)

        # this deals with rows where
        # us_viewers_millions has a value like
        # 0     17.29[2]
        # 1     14.52[2]
        episodes.us_viewers_millions = \
            episodes.us_viewers_millions.astype(str).str.match(BRACKETS)

        episodes.us_viewers_millions = \
        episodes.us_viewers_millions.apply(lambda x: x[0] if len(x) else None)

        episodes.us_viewers_millions = \
            episodes.us_viewers_millions.replace(['', 'N/A',None], np.nan)

        episodes.us_viewers_millions = \
            episodes.us_viewers_millions.astype(float) * 1000000

        if show == 'trial_by_jury':
            episodes.no_in_season = episodes.no_in_series

    recaps = read_recaps(show)
    print 'Found %d recaps' % len(recaps)
    if len(recaps) > 0:
        recaps.corpus[recaps.corpus == ''] = None
        recaps.episode_title = recaps.episode_title.apply(parse_title)
        recaps.episode_title = recaps.episode_title.apply(utf8ify)
        recaps.episode_title = recaps.episode_title.str.title()

        if show == 'trial_by_jury':
            rm = recaps.episode_title.isin(['Day (Part 2)', 'Skeleton (Part 2)'])
            recaps = recaps.drop(recaps.index[rm])
            recaps = recaps.reset_index(drop=True)
            recaps['nth_episode'] = recaps.groupby('show').nth_season.cumsum()
            recaps = recaps.sort_index(by=['nth_episode'], ascending=False)
            recaps['nth_episode'] = recaps.groupby('show').nth_season.cumsum()

        if show == 'criminal_intent':
            recaps = recaps.drop_duplicates(cols=['episode_title'])
            recaps = recaps.reset_index(drop=True)
            # recaps.nth_episode = \
            #     recaps.groupby('nth_season').nth_episode.cumsum()

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
            else:
                print 'NOT EQL'

duped_columns = ['nth_episode', 'episode_title', 'show']
combined = combined.drop(duped_columns, axis=1)
combined = combined.rename(columns={'show_name': 'show'})
colorder = ['directed_by','no_in_season','no_in_series','original_air_date',
            'production_code','title','us_viewers_millions','written_by',
            'nth_season','show','corpus_url','source','corpus']

print
print "n_shows:    %d" % (len(combined.show.unique()))
print "n_episodes: %d" % len(combined)
print

grouped    = combined.groupby(['show'])
n_corpuses = grouped.corpus.apply(lambda x: x.notnull().sum())
print "non-null corpuses\n"
print n_corpuses
print ("Total"+ "%d".rjust(16) % np.sum(n_corpuses))
print

save_to_file = False
if save_to_file:
    combined = combined.ix[:, colorder]
    combined.to_csv('./data/franchise/episodes_and_recaps.txt',
        sep='|',
        index=False,
        encoding='utf-8')

