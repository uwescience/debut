""" functions to test model (ML) methods"""

import pytest
import numpy as np, pandas as pd, sklearn.naive_bayes
import data, model

@pytest.fixture
def df():
    df = data.load(nrows=1000)
    return data.clipped_labeled_sequences(df, df.index, 104, 104)

@pytest.fixture
def X(df):
    return data.ngram_feature_vectors(df, (1,1))

@pytest.fixture
def y(df):
    return np.array(df.y_days > 52*7, dtype=float)
    

def test_auc_est(X, y):
    clf = sklearn.naive_bayes.BernoulliNB()
    results = model.auc_est(clf, X, y, [0], [0])
    assert len(results) == 1
