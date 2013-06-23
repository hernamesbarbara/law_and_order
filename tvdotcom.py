import requests
from bs4 import BeautifulSoup, Tag,NavigableString
import lxml
import numpy as np
import pandas as pd
import re
from string import punctuation
import ujson as json

def make_url(season):
     base = 'http://www.tv.com'
     path = '/shows/law-order-special-victims-unit/season-{num}/'
     return base+path.format(num=season)

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

urls = [ make_url(i) for i in range(1, 15) ]

for i, season_url in enumerate(urls):
    nth_season = i + 1

    soup = get_soup(season_url)
    episodes = find_episodes(soup)

    if len(episodes) > 0:

        episode_links = [find_links(ep) for ep in episodes]
        links = pd.DataFrame(identify_links(episode_links))
        links['recap'] = links['Episode Overview'].apply(get_recap)

        successful = 0
        total = len(links)

        episode_recaps = []
        for i, row in links.iterrows():
            success = True
            nth_episode = i+1
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
                    'nth_episode': int(nth_episode)
                    , 'nth_season': nth_season
                    , 'source': u'http://www.tv.com'
                    , 'corpus_url': url
                    , 'episode_title': title
                    , 'corpus': corpus
                }

                episode_recaps.append(rec)
                successful += 1

            except Exception, e:
                print e
                success = False

            print '%s: %s' % (title, ('DONE' if success else 'ERROR') )

        print 'Season %d' % nth_season
        print 'Percent Success: {:.2%}'.format(float(successful)/total)

        fname = 'recaps_season_{0}.json'.format(nth_season)
        with open(fname, 'w') as f:
            json.dump({'episode_recaps': episode_recaps},f,
                ensure_ascii=False)

# df = pd.read_csv('./law_and_order_episodes.csv')
# df = pd.merge(df,
#               links,
#               left_on='title',
#               right_on='title',
#               how='left')

# problems = ['Wanderlust', 'Stalked', 'Disrobed', 'Entitled', 'Chat Room']
# problem = 'http://www.tv.com/shows/law-order-special-victims-unit/wanderlust-12330/recap'
