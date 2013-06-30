#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
extract_entities.py

Created by Austin Ogilvie on 2013-06-29.
Copyright (c) 2013. All rights reserved.

This script extracts all entities (people, names, places, etc.)
from law and order episode recaps submitted by TV.com users.

The script expects a single pipe delimited file as input here:

    Project/
    |-- data/
    |   |-- franchise/
    |   |   |   |-- episodes_and_recaps.txt
    |
    |-- extract_entities.py

The script will read in this file as a pandas DataFrame. Then it finds The
`corpus` column and extracts all entities found within each record.

Output stored here:

    Project/
    |-- ref/
    |   |-- entities.txt
    |
    |-- extract_entities.py

This takes a while to run.
"""

import nltk
import numpy as np
import pandas as pd

def read_data():
    file_name = './data/franchise/episodes_and_recaps.txt'
    df = pd.read_csv(file_name, sep='|')
    order_by = ['show', 'nth_season', 'no_in_season']
    df = df.sort_index(by=order_by)
    df = df[df.corpus.notnull()]
    return df

def parts_of_speech(corpus):
    sentences = nltk.sent_tokenize(corpus)
    tokenized = [nltk.word_tokenize(sentence) for sentence in sentences]
    pos_tags  = [nltk.pos_tag(sentence) for sentence in tokenized]
    return pos_tags

def find_entities(tree):
    entity_names = []

    if hasattr(tree, 'node') and tree.node:
        if tree.node == 'NE':
            entity_names.append(' '.join([child[0] for child in tree]))
        else:
            for child in tree:
                entity_names.extend(find_entities(child))

    return entity_names

df = read_data()
tagged_sentences = df.corpus.apply(parts_of_speech)
del df

chunked_sentences = tagged_sentences.apply(
    lambda x: nltk.batch_ne_chunk(x, binary=True)
)

entity_names = []
print 'Extracting entities...'
print 'Grab a coffee. This takes about 10 minutes.'
for cs in chunked_sentences:
    entities = sorted(list(set([word for tree in cs
                        for word in find_entities(tree)])))
    for entity in entities:
        if entity not in entity_names:
            entity_names.append(entity)

print 'Writing entities to reference folder'
with open('./ref/entities.txt', 'w') as f:
    f.write('\n'.join(word for word in sorted(entity_names)))
