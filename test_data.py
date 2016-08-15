""" functions to test data methods"""

import data

def test_load():
    df = data.load(nrows=10)
    assert len(df) > 0
