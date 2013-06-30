import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from string import punctuation

STOP_WORDS = [word for word in
                open('./ref/stopwords.txt').read().split('\n')]


file_name = './data/franchise/episodes_and_recaps.txt'
df = pd.read_csv(file_name, sep='|')
df = df[df.corpus.notnull()]

def rm_punct(txt):
    return ''.join(ch for ch in txt if ch not in punctuation)

def list_of_crimes():
    crimes = [line.lower().strip() for line in
                open('./ref/crimes.txt').read().split('\n')]

    crimes = list(set([rm_punct(word) for row in crimes
                    for word in row.split() if word not in STOP_WORDS]))
    return sorted(crimes)

crimes = list_of_crimes()

vec = CountVectorizer(
    stop_words='english',
    vocabulary=crimes
)

vec.fit(df.corpus)

print np.all([word in vec.vocabulary_ for word in crimes])



