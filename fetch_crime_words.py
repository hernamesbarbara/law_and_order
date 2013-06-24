import requests
from bs4 import BeautifulSoup,SoupStrainer

url = 'http://en.wikipedia.org/wiki/Category:Crimes'

strain = SoupStrainer(id='mw-pages')
soup = BeautifulSoup(requests.get(url).text, parse_only=strain)
links = soup.find_all('a')

weird_shit = list(set([u'L\xe8se-majest\xe9',
              u'learn more',
              u"1788 Doctors' Riot",
              u'EAFCT',
              u'Qatl',u'TWOC',]))

crimes = sorted([ link.text for link in links if len(link.text) > 0
                    and link.text not in weird_shit ])


with open('crimes.txt', 'w') as f:
    f.write('\n'.join(crime for crime in crimes))
