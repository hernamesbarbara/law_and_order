import numpy as np
import pandas as pd
import re
from string import punctuation
import glob
import os

pd.options.display.line_width = 200
pd.options.display.max_columns = 15
pd.options.display.max_colwidth = 25

def snakify(txt):
    txt = txt.strip().lower()
    exclude = [ch for ch in punctuation if ch != '_']
    txt = ''.join(c for c in txt if c not in exclude)
    return txt.replace(' ', '_')

def list_all_csvs(show):
    p = './data/{show}/episodes'.format(show=show)
    names = [p+'/'+f for f in os.listdir(p)
            if f.endswith('.csv')]
    return names

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


shows = ['original', 'svu']

for show in shows:

    for i, f in enumerate(list_all_csvs(show)):
        if i == 0:
            df = pd.read_csv(f)
            df = ensure_columns(df)

        else:
            new = pd.read_csv(f)
            new = ensure_columns(new)
            df = df.append(new)

    if show == 'original':
        orig = df
        orig['show'] = 'original'

    if show == 'svu':
        svu = df
        svu['show'] = 'svu'

del df

if np.all(svu.columns == orig.columns):
    df = svu.append(orig)

df.original_air_date = \
    df.original_air_date.replace('', None)

df.original_air_date = \
    pd.to_datetime(df.original_air_date)

df.us_viewers_millions = \
    df.us_viewers_millions.replace(['', 'N/A'], np.nan)

df.us_viewers_millions = \
    df.us_viewers_millions.astype(float) * 1000000


# df.to_csv('./../data/combined.csv', index=False)


