from __future__ import absolute_import
from six.moves import cPickle
import gzip
#from ..utils.data_utils import get_file
from six.moves import zip
import json
import numpy as np
import pandas as pd
import sys



def load_data(path='', nb_words=None, skip_top=0,
              maxlen=None, seed=113,
              start_char=1, oov_char=2, index_from=3):
    '''
    # Arguments
        path: where to store the data (in `/.keras/dataset`)
        nb_words: max number of words to include. Words are ranked
            by how often they occur (in the training set) and only
            the most frequent words are kept
        skip_top: skip the top N most frequently occuring words
            (which may not be informative).
        maxlen: truncate sequences after this length.
        seed: random seed for sample shuffling.
        start_char: The start of a sequence will be marked with this character.
            Set to 1 because 0 is usually the padding character.
        oov_char: words that were cut out because of the `nb_words`
            or `skip_top` limit will be replaced with this character.
        index_from: index actual words with this index and higher.
    Note that the 'out of vocabulary' character is only used for
    words that were present in the training set but are not included
    because they're not making the `nb_words` cut here.
    Words that were not seen in the trining set but are in the test set
    have simply been skipped.
    '''
    
    dname = '/home/j/LIMITED_USE/PROJECT_FOLDERS/DEBUT/prepped_data/'
    #fname = dname + 'codes_projected_48_regularized.csv'
    fname = dname + 'clipped_48_labeled_subject_sequences.csv'
    #patient_df = pd.read_csv(fname, index_col=0)
    patient_df = pd.DataFrame()
    for chunk in pd.read_csv(fname, index_col=0, chunksize=40000):
        patient_df = patient_df.append(chunk)


    patient_df = patient_df[patient_df.y_days >= 52*7]
    collist = patient_df.columns.tolist()
    X = patient_df[collist[:-1]].as_matrix()
    labels = np.array(patient_df.y_days <= 2*52*7, dtype=float)

    folder = '/ihme/scratch/users/cjones6/temp_data/'
    save_file = folder+'saved_eigenvectors_regularized25.txt'
    code_to_int, int_to_code, code_counts, unique_code_counts, n_codes = json.load(open(folder+'saved_dicts', 'r'))

    if start_char is not None:
        Y = []
        num_patients = len(X[:, 0])
        idx = 0
        for w in X[:, 0]:
            idx += 1
            if idx % 1000 == 0:
                print 'loading patient', idx, 'of', num_patients
            Y.append([start_char])
            w = w.split(' ')
            for i in w:
                try:
                    Y[-1] += [code_to_int[i] + index_from]  
                except:
                    pass
    X = Y

    if maxlen:
        new_X = []
        new_labels = []
        for x, y in zip(X, labels):
            if len(x) < maxlen:
                new_X.append(x)
                new_labels.append(y)
        X = new_X
        labels = new_labels
    if not X:
        raise Exception('After filtering for sequences shorter than maxlen=' +
                        str(maxlen) + ', no sequence was kept. '
                        'Increase maxlen.')
    if not nb_words:
        nb_words = max([max(x) for x in X])

    # by convention, use 2 as OOV word
    # reserve 'index_from' (=3 by default) characters: 0 (padding), 1 (start), 2 (OOV)
    if oov_char is not None:
        X = [[oov_char if (w >= nb_words or w < skip_top) else w for w in x] for x in X]
    else:
        nX = []
        for x in X:
            nx = []
            for w in x:
                if (w >= nb_words or w < skip_top):
                    nx.append(w)
            nX.append(nx)
        X = nX

    train_size = int(len(labels)*.8)
    X_train = np.array(X[:train_size])
    y_train = np.array(labels[:train_size])

    X_test = np.array(X[train_size:])
    y_test = np.array(labels[train_size:])

    return (X_train, y_train), (X_test, y_test)


if __name__ == '__main__':
    load_data()
    print 'done'
