import nltk
import pandas as pd

file_name = './data/franchise/episodes_and_recaps.txt'
df = pd.read_csv(file_name, sep='|')
df = df.sort_index(by=['show', 'nth_season', 'no_in_season'])
corpus = df[df['show']=='svu'].head().corpus.values[0]

def parts_of_speech(corpus):
    sentences = nltk.sent_tokenize(corpus)
    tokenized = [nltk.word_tokenize(sentence) for sentence in sentences]
    pos_tags  = [nltk.pos_tag(sentence) for sentence in tokenized]
    return pos_tags

tagged_sentences = parts_of_speech(corpus)
chunked_sentences = nltk.batch_ne_chunk(tagged_sentences, binary=True)

def extract_entity_names(t):
    entity_names = []

    if hasattr(t, 'node') and t.node:
        if t.node == 'NE':
            entity_names.append(' '.join([child[0] for child in t]))
        else:
            for child in t:
                entity_names.extend(extract_entity_names(child))

    return entity_names

entity_names = []
for tree in chunked_sentences:
    entity_names.extend(extract_entity_names(tree))


entity_names = list(set(entity_names))
for name in entity_names:
    print name
