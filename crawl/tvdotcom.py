#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
tvdotcom.py

Created by Austin Ogilvie on 2013-06-29.
Copyright (c) 2013. All rights reserved.

This script downloads Law and Order TV data from tv.com.

It visits the list of episodes page on TV.com. From there, it
finds each URL specific to a user-submitted summary page.

Although a summary / recap page exists for each episode,
not every episode actually has a recap.

This is due to the fact that users haven't written recaps for every episode.

For example:

    This page:
        http://www.tv.com/shows/law-order/season-10/

    Yields a list of URLs specific to each episode in season 1 of
    the original law and order series.

    From there, the script is able to grab each episode recap URL:

        http://www.tv.com/shows/law-order/stiff-9729/recap

You should run this script from the project root.

Results will be stored here.

    Project/
    |-- crawl/
    |   |-- tvdotcom.py
    |-- data/
    |   |-- original/
    |   |   |-- recaps/
    |   |   |   |-- season_1.json
    |   |   |   |-- season_2.json
    |   |   |   |-- season_3.json
    |   |-- svu/
    |   |   |-- recaps/
    |   |   |   |-- season_1.json
    |   |   |   |-- season_2.json
    |   |   |   |-- season_3.json

"""
import requests
from bs4 import BeautifulSoup, Tag,NavigableString
import lxml
import numpy as np
import pandas as pd
import re
from string import punctuation
import ujson as json

pd.options.display.line_width = 200
pd.options.display.max_columns = 15
pd.options.display.max_colwidth = 25

def make_url(show, season):
    base = 'http://www.tv.com/shows'
    franchise = {
        'original': '/law-order/season-{num}/',
        'svu': '/law-order-special-victims-unit/season-{num}/'
    }

    return base+franchise.get(show).format(num=season)

def get_soup(url, verbose=True):
    h = {'User-Agent': 'Mozilla/5.0'}
    if verbose:
        print "GET %s" % url

    try:
        html = requests.get(url, headers=h).text.encode('utf-8')
        soup = BeautifulSoup(html, 'lxml')

    except Exception, e:
        print 'Something went wrong'
        print e
        soup = None

    return soup

def find_episodes(soup):
    rg = re.compile('^season-\d+-eps')
    ul = soup.find('ul', id=rg)

    if ul is None:
        return []

    episodes = [ li for li in ul.children if isinstance(li, Tag)]
    return episodes

def find_links(episode):
    css = {'class': 'title'}
    title = [ a for a in episode.find_all('a', attrs=css)]

    css   = {'class': '_inline_navigation'}
    nav   = [a for tag in episode.find_all('ul', attrs=css)
                for a in tag.find_all('a')]

    nested = nav + title

    return nested

def identify_links(episode_links):
    res = []
    for ep in episode_links:
        rec = {}
        for a in ep:
            if 'class' in a.attrs and 'title' in a['class']:
                title = a.text
                rec['title'] = title
            else:
                href = a['href']
                link_type  = a.text
                rec[link_type] = href
        res.append(rec)
    return res

def get_recap(episode_url):
    return 'http://www.tv.com{overview}recap'.format(overview=episode_url)

def utf8ify(txt):
    return u''.join(txt).encode('utf-8').strip()

franchise = [
    {'name': 'svu', 'n_seasons': 14},
    {'name': 'original', 'n_seasons': 20}
]

for show in franchise:

    name = show['name']
    n_seasons = show['n_seasons']

    urls = [ make_url(name, i) for i in range(1, n_seasons+1) ]

    for i, season_url in enumerate(urls):
        nth_season = i + 1

        soup = get_soup(season_url)
        episodes = find_episodes(soup)

        if len(episodes) > 0:
            print 'Episodes for Season: %d' % nth_season

            episode_links = [find_links(ep) for ep in episodes]
            links = pd.DataFrame(identify_links(episode_links))
            total = len(links)

            links['recap'] = links['Episode Overview'].apply(get_recap)
            links['nth_season'] = nth_season

            # tv.com arranges episodes in reverse chronological order
            # this ensures proper enumeration
            links['nth_episode'] = list(reversed(range(1,total+1)))

            successful = 0


            episode_recaps = []

            for j, row in links.iterrows():
                success = True

                nth_episode = int(row['nth_episode'])
                url = utf8ify(row['recap'])
                title = utf8ify(row['title'])

                soup = get_soup(url)
                corpus = soup.find_all('div', {'class': 'text'})

                if len(corpus) == 1:
                    corpus = utf8ify(corpus[0].get_text())
                else:
                    corpus = ''

                try:

                    rec = {
                        'nth_episode': nth_episode
                        , 'nth_season': nth_season
                        , 'source': u'http://www.tv.com'
                        , 'corpus_url': url
                        , 'episode_title': title
                        , 'corpus': corpus
                        , 'show': name
                    }

                    episode_recaps.append(rec)
                    successful += 1

                except Exception, e:
                    print e
                    success = False

                print '%s: %s' % (title, ('DONE' if success else 'ERROR') )

            print 'Finished Season %d' % nth_season
            print 'Percent Success: {:.2%}'.format(float(successful)/total)

            p = './data/{show}/recaps'.format(show=name)
            fname = p+'/season_{0}.json'.format(nth_season)

            with open(fname, 'w') as f:
                json.dump({'episode_recaps': episode_recaps},f,
                    ensure_ascii=False)
