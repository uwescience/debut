""" functions to test data methods"""

import pytest
import numpy as np, pandas as pd
import data

@pytest.fixture
def df():
    return data.load(nrows=1000)
    

def test_load():
    df = data.load(nrows=10)
    assert len(df) > 0
    assert 'out_seq' in df.columns

def test_is_included(df):
    data.is_included(df, 74901)

def test_surgery_for_cancer():
    assert data.surgery_for_cancer('icd9-153') == 1
    assert data.surgery_for_cancer('icd9-2534') == 0

def test_emergency_surgery(df):
    assert data.emergency_surgery(df, 212002) == False

def test_included_subjects(df):
    subjs = data.included_subjects(df)
    assert len(subjs) == 214

def test_seqs_dur_exposure_period(df):
    s = data.seqs_during_exposure_period(df, df.index[0], -10, 10)
    assert 'code_seq' in s.keys()
    assert 'out_seq' in s.keys()
    assert 'emrg_seq' in s.keys()
    assert 'pay_seq' in s.keys()
    

    s = data.seqs_during_exposure_period(df, df.index[0], 0, 0)
    date_list = s['date_seq'].split()
    assert len(np.unique(date_list)) == 1

def test_days_until_surgery(df):
    s = df.iloc[0]
    days = data.days_until_surgery(s)
    assert np.isinf(days)

    s = pd.Series({'code_seq':'icd9-56211 cpt-44110',
                   'date_seq':'2014-01-17 2014-01-17'})
    days = data.days_until_surgery(s)
    assert days == 0

def test_clipped_labeled_sequences(df):
    rows = df.index[::5]
    new_df = data.clipped_labeled_sequences(df, rows, -1, 1)
    assert len(new_df) == np.floor(len(df) / 5) + 1
    for col in ['code_seq', 'date_seq', 'out_seq', 'emrg_seq', 'pay_seq']:
        assert col in new_df.columns

def test_bigram_feature_vectors(df):
    X = data.bigram_feature_vectors(df)
    assert len(X.shape) == 2
