#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
crawl_wikipedia.py

Created by Austin Ogilvie on 2013-06-29.
Copyright (c) 2013. All rights reserved.

This script downloads Law and Order TV data from wikipedia.

It visits the list of episodes page on wikipedia
and grabs each of the tables for each season of the show.

For example:
http://en.wikipedia.org/wiki/List_of_Law_%26_Order_episodes
http://en.wikipedia.org/wiki/List_of_Law_%26_Order:_Special_Victims_Unit_episodes

You should run this script from the project root.

Results will be stored here.

    Project/
    |-- crawl/
    |   |-- crawl_wikipedia.py
    |-- data/
    |   |-- original/
    |   |   |-- episodes/
    |   |   |   |-- season_1.csv
    |   |   |   |-- season_2.csv
    |   |   |   |-- season_3.csv
    |   |-- svu/
    |   |   |-- episodes/
    |   |   |   |-- season_1.csv
    |   |   |   |-- season_2.csv
    |   |   |   |-- season_3.csv

"""
import requests
from bs4 import BeautifulSoup, Tag,NavigableString
import lxml
import numpy as np
import pandas as pd
import re
from string import punctuation
from collections import defaultdict

pd.options.display.line_width = 200
pd.options.display.max_columns = 15
pd.options.display.max_colwidth = 25

ISO_DATE_PAT = re.compile('(\d{4}-\d{2}-\d{2})', re.DOTALL|re.IGNORECASE)
FLOAT_PAT    = re.compile( '(\d{1,2}\.\d{1,2})', re.DOTALL|re.IGNORECASE)

def get_tables(soup):
    css = {'class': 'wikitable plainrowheaders'}
    tables = [table for table in soup.find_all('table', css)]
    print tables[0].get_text()
    return tables

def find_rows(table):
    return [row for row in table.find_all('tr')]

def find_columns(row):
    return list(row.find_all('th'))

def clean_txt(tag):
    txt = tag.get_text().split('\n')
    return u' '.join(txt).encode('utf-8').strip()

def find_headers(table):
    rows = find_rows(table)
    rows = [find_columns(row) for row in rows]
    rows = [ row for row in rows if len(row) >= 6 ]
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

    if len(rows) == 1:
        return

    episode_numbers = [row.find('th').get_text() for row in rows
                        if row is not None and isinstance(row, Tag)]

    rows = [[clean_txt(td) for td in row.find_all('td')]
                for row in rows]

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

        # only some have
        # `U.S. Viewers (millions)`
        if len(row) == 7:
            row[6] = parse_text(row[6], rg=FLOAT_PAT)

        row.insert(0, ep)

    return rows

base = 'http://en.wikipedia.org/wiki'

franchise = {
    'original': base+'/List_of_Law_%26_Order_episodes'
    , 'svu': base+'/List_of_Law_%26_Order:_Special_Victims_Unit_episodes'
}

for show in franchise:

    url = franchise.get(show)

    html = requests.get(url).text.encode('utf-8')
    soup = BeautifulSoup(html, 'lxml')

    tables = get_tables(soup)

    if show == 'original':
        tables.pop(0)

    tables = [ t for t in tables if 'Law & Order Movie' not in t.get_text() ]

    for i, table in enumerate(tables):
        nth_season = i + 1
        rows = find_data(table)
        h = find_headers(table)

        if rows is None or len(rows) == 0:
            continue

        data = defaultdict(list)

        for j in range(len(h)):
            data[h[j]] = [row[j] for row in rows]

        df = pd.DataFrame(data)
        df['nth_season'] = nth_season
        f = './data/{show}/episodes/season_{num}.csv'
        f = f.format(show=show, num=nth_season)
        df.to_csv(f, index=False)
