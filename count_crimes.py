import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from string import punctuation

STOP_WORDS = [word for word in open('./stopwords.txt').read().split('\n')]

df = pd.read_csv('./law_and_order_svu_with_recaps.txt', sep='|')
df = df[df.corpus.notnull()]

def rm_punct(txt):
    return ''.join(ch for ch in txt if ch not in punctuation)

def list_of_crimes():
    crimes = [word.lower() for word in open('./crimes.txt').read().split('\n')]
    crimes = list(set([rm_punct(token) for word in CRIMES
                    for token in word.split() if token not in STOP_WORDS]))
    return crimes

crimes = list_of_crimes()

vec = CountVectorizer()
vec.fit(df.corpus)

crimes_mentioned = sorted([word for word in vec.vocabulary_ if word in crimes])
