import requests
from bs4 import BeautifulSoup, Tag,NavigableString
import lxml
import numpy as np
import pandas as pd
import re
from string import punctuation


url = 'http://en.wikipedia.org/wiki/List_of_Law_%26_Order:\
    _Special_Victims_Unit_episodes'

ISO_DATE_PAT = re.compile('(\d{4}-\d{2}-\d{2})', re.DOTALL|re.IGNORECASE)
FLOAT_PAT    = re.compile( '(\d{1,2}\.\d{1,2})', re.DOTALL|re.IGNORECASE)

HTML = requests.get(url).text.encode('utf-8')
SOUP = BeautifulSoup(HTML, 'lxml')

def snakify(txt):
    txt = txt.strip()
    txt = ''.join(c for c in txt if c not in punctuation)
    return txt.replace(' ', '_').lower()

def get_tables(soup=SOUP):
    css = {'class': 'wikitable plainrowheaders'}
    return [table for table in soup.find_all('table', css)]

def find_rows(table):
    return [row for row in table.find_all('tr')]

def find_columns(row):
    return list(row.find_all('th'))

def tags_only(row):
    return [th for th in row if isinstance(th, Tag)]

def is_header(row):
    return len(row) == 8

def clean_txt(tag):
    txt = tag.get_text().split('\n')
    return u' '.join(txt).encode('utf-8').strip()

def find_headers(table):
    rows = find_rows(table)
    rows = [find_columns(row) for row in rows]
    rows = [ row for row in rows if len(row) == 8 ]
    headers = rows[0] if len(rows) == 1 else []
    headers = [clean_txt(h) for h in headers]
    return headers

def parse_text(txt, rg):
    txt = txt.strip()
    matches = rg.findall(txt)
    res = matches[0] if len(matches) else txt
    return res

def rm_quotes(txt):
    return txt.strip('"') if len(txt) else ''

def find_data(table):
    css = {'class': 'vevent'}
    rows = table.find_all('tr', css)
    episode_numbers = [row.find('th').get_text() for row in rows]
    rows = [ [clean_txt(td) for td in row.find_all('td')] for row in rows]

    for (ep, row) in zip(episode_numbers, rows):
        ep = int(ep) if ep.isdigit() else ep

        row[0] = int(row[0]) if row[0].isdigit() else row[0]
        row[1] = rm_quotes(row[1])
        row[4] = parse_text(row[4], rg=ISO_DATE_PAT)
        if len(row[4]) != 10:
            try:
                row[4] = pd.datetime.strptime(row[4], '%B %d, %Y')
            except:
                pass

        row[6] = parse_text(row[6], rg=FLOAT_PAT)
        row.insert(0, ep)

    return rows


tables = get_tables()
df = None
for i, table in enumerate(tables):
    rows = find_data(table)
    if df is None:
        df = pd.DataFrame(rows)
        df['season'] = i + 1
    else:
        new = pd.DataFrame(rows)
        new['season'] = i + 1
        df = df.append(new)

columns = find_headers(tables[0])
columns.append('season')
columns = [snakify(col) for col in columns]
df.columns = columns
df = df.reset_index(drop=True)

colnames = {
    'no_in_season': 'season_num'
    , 'no_in_series': 'series_num'
    , 'directed_by': 'director'
    , 'written_by': 'writer'
    , 'original_air_date': 'aired'
    , 'production_code': 'code'
    , 'us_viewers_millions': 'viewership'
}

df = df.rename(columns=colnames)

reordered = ['season',
             'season_num',
             'series_num',
             'title',
             'director',
             'writer',
             'aired',
             'code',
             'viewership']

df = df.ix[:, reordered]

df.aired = df.aired.replace('', None)
df.aired = pd.to_datetime(df.aired)

df.viewership = df.viewership.replace(['', 'N/A'], np.nan)
df.viewership = df.viewership.astype(float) * 1000000

df = df.set_index(['aired'])
keys = [df.index.year, df.index.month]
df.groupby(keys).viewership.mean().plot()

