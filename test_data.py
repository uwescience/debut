""" functions to test data methods"""

import pytest
import data

@pytest.fixture
def df():
    return data.load(nrows=1000)
    

def test_load():
    df = data.load(nrows=10)
    assert len(df) > 0

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
