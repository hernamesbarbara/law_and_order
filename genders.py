import nltk
import numpy as np
import pandas as pd

from sklearn.feature_extraction.text \
    import (CountVectorizer, TfidfVectorizer)

from sklearn.decomposition import NMF

pd.options.display.width = 500
pd.options.display.max_columns = 6
pd.options.display.max_colwidth = 100

def read_data(f='./data/franchise/episodes_and_recaps.txt'):
    df = pd.read_csv(f, sep='|')
    order_by = ['show', 'nth_season', 'no_in_season']
    df = df.sort_index(by=order_by)
    df = df.dropna(subset=['corpus'])
    return df

def read_entities(f='./ref/entities.txt'):
    return pd.Series(row for row in open(f).read().split('\n'))

def read_corpuses():
    corpuses = read_data()['corpus']
    corpuses = corpuses.reset_index()
    corpuses = corpuses.rename(columns={'index':'row_id'})
    return corpuses

def names_by_gender():
    names = nltk.corpus.names
    male_names = pd.DataFrame(
        {'name': names.words('male.txt'),
        'sex': 'male'}
    )
    female_names = pd.DataFrame(
        {'name': names.words('female.txt'),
        'sex': 'female'}
    )
    names = male_names.append(female_names,ignore_index=True)
    names = names.join(pd.get_dummies(names.sex))
    names = names.groupby('name')[['female','male']].max()
    names = names.sort_index()
    names = names.reset_index()
    return names

entities = read_entities()
names = names_by_gender().reset_index()
entities = entities.reset_index(name='entity')
entities.columns = ['row_id', 'entity']

def lookup(word):
    return names[names.name==word]

def find_sex(entity):
    is_name = lambda x: len(lookup(x)) > 0
    words = entity.split()
    male, female = '', ''
    for word in words:
        if is_name(word):
            male   = lookup(word)['male'].values[0]
            female = lookup(word)['female'].values[0]
    return pd.Series([male,female], index=['male','female'])

entities[['male', 'female']] = entities.entity.apply(find_sex)

entities[['male', 'female']] = \
    entities[['male','female']].replace('', np.nan)

entities['is_name'] = \
    entities[['male', 'female']].apply(lambda row: row.sum()>0, axis=1)

people = entities[entities['is_name']==True]
people[['male', 'female']] = people[['male','female']].fillna(0)
people = people.ix[:, ['row_id','entity','male','female']]
people = people.reset_index(drop=True)
people = people.rename(columns={'entity':'character_name'})
people.to_csv('./ref/list_of_characters.txt', index=False, sep='|')
