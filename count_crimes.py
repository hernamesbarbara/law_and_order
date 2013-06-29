import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from string import punctuation

STOP_WORDS = [word for word in
                open('./ref/stopwords.txt').read().split('\n')]

df = pd.read_csv('./svu_data/law_and_order_svu_with_recaps.txt', sep='|')
df = df[df.corpus.notnull()]

def rm_punct(txt):
    return ''.join(ch for ch in txt if ch not in punctuation)

def list_of_crimes():
    crimes = [line.lower().strip() for line in
                open('./ref/crimes.txt').read().split('\n')]

    crimes = list(set([rm_punct(word) for row in crimes
                    for word in row.split() if word not in STOP_WORDS]))
    return crimes



vec = CountVectorizer()
vec.fit(df.corpus)

crimes = list_of_crimes()
mentioned = sorted([word for word in vec.vocabulary_
                            if word in crimes ])

